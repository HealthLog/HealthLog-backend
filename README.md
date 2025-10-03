# Embedding API

Google EmbeddingGemma-300m 모델을 사용한 텍스트 임베딩 API 서비스

## 🚀 특징

- **경량 모델**: 300M 파라미터 (INT8 양자화 시 ~300MB)
- **ARM 최적화**: Oracle A1 Flex 인스턴스 최적화
- **JWT 인증**: Supabase 기반 사용자 인증
- **Rate Limiting**: Redis 기반 요청 제한
- **모니터링**: Prometheus 메트릭
- **Docker 기반**: 간편한 배포

## 📋 요구사항

- Docker & Docker Compose
- 최소 3GB RAM
- 1.5+ CPU 코어
- HuggingFace 계정 (gated model 접근용)
- Supabase (JWT 인증용)

## 🛠️ 빠른 시작

### 1. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가:

```bash
# 모델 설정
MODEL_NAME=google/embeddinggemma-300m
MODEL_QUANTIZATION=int8
MAX_BATCH_SIZE=8
MAX_SEQ_LENGTH=2048

# HuggingFace 인증 (https://huggingface.co/settings/tokens)
HF_TOKEN=your_huggingface_token_here

# Supabase JWT 인증
SUPABASE_JWT_SECRET=your_supabase_jwt_secret
SUPABASE_URL=http://your-supabase-url:54321
SUPABASE_ANON_KEY=your_supabase_anon_key

# Redis (Docker Compose 사용 시 자동 설정)
REDIS_URL=redis://redis:6379

# Rate Limiting
RATE_LIMIT_PER_MIN=10

# 개발 모드
DEBUG=true
```

### 2. Docker Compose 실행

```bash
# 빌드 및 실행
docker-compose up --build -d

# 로그 확인
docker-compose logs -f embedding-api

# 정상 작동 확인 (model_loaded_successfully 메시지 대기)
```

### 3. JWT 토큰 발급

테스트 스크립트를 사용하여 JWT 토큰 발급:

```bash
cd ../embedding-api-tests
./get_token.sh
# 이메일과 비밀번호 입력 후 토큰 복사
```

### 4. API 테스트

```bash
# 환경 변수에 토큰 설정
export JWT_TOKEN='발급받은_토큰_붙여넣기'

# Health check
curl http://localhost:8000/health

# 단일 텍스트 임베딩
curl -X POST http://localhost:8000/embed \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"text": "안녕하세요, 반갑습니다!"}'

# 배치 임베딩
curl -X POST http://localhost:8000/batch-embed \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["첫 번째", "두 번째", "세 번째"]}'

# 자동화된 테스트 (../embedding-api-tests 디렉토리에서)
cd ../embedding-api-tests
python test_with_token.py
```

## 📊 모니터링

### Prometheus 메트릭

```bash
# 메트릭 확인
curl http://localhost:8000/metrics

# Prometheus UI
open http://localhost:9090
```

**주요 메트릭:**
- `embed_requests_total`: 총 임베딩 요청 수
- `embed_request_duration_seconds`: 요청 처리 시간
- `embed_errors_total`: 오류 발생 수

### Docker 리소스 모니터링

```bash
# 실시간 리소스 사용량
docker stats embedding-api

# 로그 스트리밍
docker-compose logs -f embedding-api
```

## 🚢 프로덕션 배포

### Oracle Cloud (ARM64)

```bash
# 1. ARM64 이미지 빌드
docker build --platform linux/arm64 -t embedding-api:latest .

# 2. 이미지 저장 및 전송
docker save embedding-api:latest | gzip > embedding-api.tar.gz
scp embedding-api.tar.gz user@server:/home/user/

# 3. 서버에서 이미지 로드
ssh user@server
docker load < embedding-api.tar.gz

# 4. 필요한 파일 업로드
scp docker-compose.yml .env prometheus.yml user@server:/app/

# 5. 서버에서 실행
ssh user@server
cd /app
docker-compose up -d
```

### Docker Hub 사용

```bash
# 이미지 푸시
docker tag embedding-api:latest your-username/embedding-api:latest
docker push your-username/embedding-api:latest

# 서버에서 pull
docker pull your-username/embedding-api:latest
docker-compose up -d
```

## 🔒 보안 설정

### JWT 인증

이 API는 Supabase JWT 기반 인증이 **필수**입니다:

1. Supabase Auth API로 사용자 등록/로그인
2. 발급받은 JWT 토큰을 `Authorization: Bearer {token}` 헤더에 포함
3. 모든 `/embed`, `/batch-embed` 엔드포인트는 유효한 토큰 필요

**인증 흐름:**
```
Client → Supabase Auth (로그인) → JWT 토큰 발급
Client → Embedding API (JWT 포함) → 토큰 검증 → 임베딩 처리
```

### HTTPS 설정

Nginx 또는 Caddy 리버스 프록시 사용 권장:

```bash
# Caddy 예시
caddy reverse-proxy --from https://api.yourdomain.com --to localhost:8000
```

## 📈 성능 튜닝

### 메모리 최적화

```yaml
# docker-compose.yml
services:
  embedding-api:
    deploy:
      resources:
        limits:
          cpus: '2.0'      # CPU 코어 수
          memory: 4G       # RAM 크기
```

### 배치 크기 조정

```bash
# .env
MAX_BATCH_SIZE=16  # 메모리 여유가 있다면 증가
```

### 양자화 설정

```bash
# .env
MODEL_QUANTIZATION=int8   # 메모리 최소 (권장)
# MODEL_QUANTIZATION=fp16  # 성능 중시
# MODEL_QUANTIZATION=fp32  # 정확도 최우선
```

## 🐛 트러블슈팅

### 1. 모델 다운로드 실패

**원인:** HF_TOKEN 미설정 또는 디스크 공간 부족

```bash
# HuggingFace 토큰 확인
echo $HF_TOKEN  # .env 파일 확인

# 디스크 공간 확보
docker system prune -a --volumes -f
```

### 2. JWT 인증 실패

**원인:** SUPABASE_JWT_SECRET 불일치

```bash
# Supabase JWT Secret 확인
# Supabase 대시보드 → Settings → API → JWT Secret
```

### 3. OOM (Out of Memory)

**해결 방법:**
1. `MODEL_QUANTIZATION=int8` 사용
2. `MAX_BATCH_SIZE` 감소 (4 이하)
3. Docker 메모리 제한 증가 (`memory: 4G`)

### 4. Redis 연결 실패

```bash
# Redis 컨테이너 상태 확인
docker-compose ps redis
docker-compose logs redis

# Redis 재시작
docker-compose restart redis
```

### 5. SlowAPI 오류

**에러:** `parameter 'request' must be an instance of starlette.requests.Request`

**원인:** SlowAPI rate limiter는 첫 번째 매개변수가 `Request` 객체여야 함
**해결:** 코드에서 이미 수정됨 (CLAUDE.md 참조)

## 📝 API 문서

서버 실행 후 자동 생성된 문서 확인:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 테스트

테스트 스크립트는 `../embedding-api-tests` 디렉토리에 있습니다:

```bash
cd ../embedding-api-tests

# JWT 토큰 발급
./get_token.sh

# 간단한 API 테스트
./test_api.sh

# 전체 통합 테스트
export JWT_TOKEN='your_token'
python test_with_token.py
```

## 🔧 로컬 개발

### Python 직접 실행 (Docker 없이)

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Redis 실행 (Docker)
docker run -d -p 6379:6379 redis:7-alpine

# .env 파일 설정 후 개발 서버 실행
python -m app.main
```

### 코드 수정 후

```bash
# 컨테이너 재시작
docker-compose restart embedding-api

# 또는 재빌드
docker-compose up --build -d
```

## 📁 프로젝트 구조

```
embedding-api/
├── app/
│   ├── __init__.py
│   ├── config.py       # 환경 변수 설정
│   ├── main.py         # FastAPI 애플리케이션
│   └── models.py       # Pydantic 모델
├── .dockerignore
├── .env                # 환경 변수 (gitignore)
├── .gitignore
├── CLAUDE.md           # 개발 가이드
├── docker-compose.yml  # 서비스 정의
├── Dockerfile          # 이미지 빌드
├── prometheus.yml      # 모니터링 설정
├── README.md
└── requirements.txt    # Python 의존성

../embedding-api-tests/  # 테스트 스크립트
├── get_token.sh
├── test_api.sh
└── test_with_token.py
```

## 📄 라이센스

MIT License

## 🤝 기여

Issue 및 PR 환영합니다!
