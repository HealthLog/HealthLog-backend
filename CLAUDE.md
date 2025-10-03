# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EmbeddingGemma-300m 기반 텍스트 임베딩 API 서비스. FastAPI로 구현되었으며, Supabase JWT 인증과 Redis 기반 rate limiting을 제공합니다.

## Essential Commands

### Development
```bash
# Docker로 개발 환경 시작
docker-compose up --build

# 백그라운드 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f embedding-api

# 컨테이너 재시작 (코드 변경 후)
docker-compose restart embedding-api

# 로컬 Python 개발 (Docker 없이)
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
docker run -d -p 6379:6379 redis:7-alpine
python -m app.main
```

### Testing
```bash
# API 테스트 스크립트
./test_api.sh

# JWT 토큰 발급
./get_token.sh

# Python 통합 테스트
export JWT_TOKEN='your_token_here'
python test_with_token.py

# Health check
curl http://localhost:8000/health

# 임베딩 테스트 (JWT 필요)
curl -X POST http://localhost:8000/embed \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"text": "테스트 문장"}'
```

### Production Deployment
```bash
# ARM64 이미지 빌드
docker build --platform linux/arm64 -t embedding-api:latest .

# 이미지 저장 및 전송
docker save embedding-api:latest | gzip > embedding-api.tar.gz
scp embedding-api.tar.gz user@server:/home/user/
```

## Architecture

### Core Components

**FastAPI Application (`app/main.py`)**
- Lifespan context: 모델과 Redis 초기화를 startup/shutdown에서 관리
- Global singletons: `model`, `tokenizer`, `redis_client`를 전역으로 관리
- Rate limiting: SlowAPI를 사용하며 **반드시 `Request` 객체를 첫 번째 매개변수로 받아야 함**
- Authentication: `verify_token()` dependency가 JWT를 검증하고 user_id 반환

**Configuration (`app/config.py`)**
- Pydantic v2 Settings로 .env 파일 자동 로드
- Production mode에서는 `SUPABASE_JWT_SECRET` 필수
- `model_config`에서 `protected_namespaces = ()`로 Pydantic 경고 방지

**Models (`app/models.py`)**
- Request/Response 모델은 `model_config = {"protected_namespaces": ()}`로 설정
- `EmbedRequest`, `BatchEmbedRequest`: 입력 검증
- `EmbedResponse`, `BatchEmbedResponse`: 출력 포맷

### Critical Integration Points

**SlowAPI Rate Limiter**
```python
# ❌ 잘못된 패턴 - SlowAPI 오류 발생
@app.post("/embed")
@limiter.limit("10/minute")
async def embed_text(
    request: EmbedRequest,  # Pydantic 모델
    user_id: str = Depends(verify_token)
):
    pass

# ✅ 올바른 패턴
@app.post("/embed")
@limiter.limit("10/minute")
async def embed_text(
    request: Request,  # Starlette Request 객체 필수!
    embed_request: EmbedRequest,  # Pydantic 모델은 별도 매개변수
    user_id: str = Depends(verify_token)
):
    pass
```

**JWT Authentication Flow**
1. Supabase Auth가 JWT 토큰 발급 (HS256 알고리즘)
2. 클라이언트가 `Authorization: Bearer {token}` 헤더로 전송
3. `verify_token()`이 `SUPABASE_JWT_SECRET`으로 서명 검증
4. Payload에서 `sub` (user_id) 추출하여 반환

**Model Loading**
- HuggingFace gated model이므로 `HF_TOKEN` 환경변수 필수
- `from_pretrained()`에 `token=settings.hf_token` 전달
- 모델은 lifespan context에서 로드되어 전역 변수로 관리

### Package Dependencies

**Critical Version Constraints**
- `transformers>=4.56.0`: EmbeddingGemma 지원
- `torch>=2.3.0,<2.6.0`: transformers 4.56+ 호환
- `numpy<2`: NumPy 2.x 호환성 문제 방지
- `pydantic==2.11.9`: v2 스타일 사용
- `fastapi==0.118.0`, `uvicorn==0.37.0`: 최신 안정 버전

### Environment Variables

**필수 변수 (.env)**
```bash
# 모델 설정
MODEL_NAME=google/embeddinggemma-300m
HF_TOKEN=your_huggingface_token  # Gated model 접근용

# Supabase 인증
SUPABASE_JWT_SECRET=your_jwt_secret  # Production 필수
DEBUG=true  # false일 때 JWT_SECRET 검증

# Redis (Docker Compose 사용 시 자동 설정)
REDIS_URL=redis://redis:6379
```

### Docker Architecture

**서비스 구성**
- `embedding-api`: FastAPI 애플리케이션
- `redis`: Rate limiting용 캐시
- `prometheus`: 메트릭 수집 (선택)

**볼륨 관리**
- `model-cache`: HuggingFace 모델 캐시 영구 저장 (~1.2GB)
- `prometheus-data`: 메트릭 데이터

**환경변수 주입**
- `.env` 파일을 `env_file`로 자동 로드
- `REDIS_URL`은 Docker 네트워크용으로 오버라이드

### API Endpoints

- `GET /health`: 모델 로드 및 Redis 연결 상태
- `POST /embed`: 단일 텍스트 임베딩 (JWT 필수)
- `POST /batch-embed`: 배치 임베딩 (JWT 필수)
- `GET /metrics`: Prometheus 메트릭
- `GET /docs`: Swagger UI

### Monitoring

**Prometheus Metrics**
- `embed_requests_total`: 총 요청 수
- `embed_request_duration_seconds`: 요청 처리 시간
- `embed_errors_total{error_type}`: 에러 타입별 카운트

**Logging**
- structlog JSON 로깅 (타임스탬프, 레벨 포함)
- 주요 이벤트: `starting_application`, `model_loaded_successfully`, `embed_success`, `embed_failed`
