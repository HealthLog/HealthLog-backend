# Embedding API

Google embedding-gemma-300m 모델을 사용한 텍스트 임베딩 API 서비스

## 🚀 특징

- **경량 모델**: 300M 파라미터 (INT8 양자화 시 ~300MB)
- **ARM 최적화**: Oracle A1 Flex 인스턴스 최적화
- **보안**: JWT 인증, Rate Limiting
- **모니터링**: Prometheus 메트릭
- **Docker 기반**: 간편한 배포

## 📋 요구사항

- Docker & Docker Compose
- 최소 3GB RAM
- 1.5+ CPU 코어

## 🛠️ 로컬 개발 시작

### 1. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일 편집
```

### 2. Docker Compose 실행

```bash
# 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f embedding-api
```

### 3. API 테스트

```bash
# 헬스체크
curl http://localhost:8000/health

# 단일 텍스트 임베딩
curl -X POST http://localhost:8000/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "안녕하세요, 반갑습니다!"}'

# 배치 임베딩
curl -X POST http://localhost:8000/batch-embed \
  -H "Content-Type: application/json" \
  -d '{"texts": ["첫번째 텍스트", "두번째 텍스트"]}'
```

## 📊 모니터링

### Prometheus 메트릭

```bash
# 메트릭 확인
curl http://localhost:8000/metrics

# Prometheus UI
open http://localhost:9090
```

### Docker 리소스 모니터링

```bash
# 실시간 리소스 사용량
docker stats

# 컨테이너 로그
docker logs -f embedding-api
```

## 🚢 프로덕션 배포 (Oracle Cloud)

### 1. 이미지 빌드

```bash
# ARM64 이미지 빌드
docker build --platform linux/arm64 -t embedding-api:latest .
```

### 2. 이미지 전송 (옵션 A: Docker Hub)

```bash
# Docker Hub에 푸시
docker tag embedding-api:latest your-username/embedding-api:latest
docker push your-username/embedding-api:latest
```

### 3. 이미지 전송 (옵션 B: 직접 전송)

```bash
# 이미지 저장
docker save embedding-api:latest | gzip > embedding-api.tar.gz

# Oracle 인스턴스로 전송
scp embedding-api.tar.gz user@your-instance:/home/user/

# 인스턴스에서 로드
ssh user@your-instance
docker load < embedding-api.tar.gz
```

### 4. 인스턴스에서 실행

```bash
# docker-compose.yml 업로드
scp docker-compose.yml prometheus.yml user@your-instance:/app/

# SSH 접속
ssh user@your-instance
cd /app

# 환경 변수 설정
nano .env

# 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

## 📈 성능 튜닝

### 메모리 제한 조정

```yaml
# docker-compose.yml
services:
  embedding-api:
    deploy:
      resources:
        limits:
          memory: 3G  # 필요에 따라 조정
```

### Worker 수 조정

```bash
# Dockerfile 또는 docker-compose.yml
CMD ["uvicorn", "app.main:app", "--workers", "2"]  # CPU에 맞게 조정
```

## 🔒 보안 설정

### JWT 인증 활성화

1. `.env` 파일에서 Supabase 설정
2. `app/main.py`의 `verify_token` 함수 주석 해제

### HTTPS 설정

Nginx 또는 Caddy 리버스 프록시 사용 권장

```bash
# Caddy 예시
caddy reverse-proxy --from https://api.yourdomain.com --to localhost:8000
```

## 🐛 트러블슈팅

### 모델 다운로드 실패

```bash
# 모델 수동 다운로드
docker-compose run embedding-api python -c "from transformers import AutoModel; AutoModel.from_pretrained('google/embedding-gemma-300m')"
```

### OOM (Out of Memory)

1. INT8 양자화 확인: `MODEL_QUANTIZATION=int8`
2. 배치 크기 감소: `MAX_BATCH_SIZE=4`
3. 메모리 제한 증가: `memory: 4G`

### Redis 연결 실패

```bash
# Redis 상태 확인
docker-compose ps redis
docker-compose logs redis

# Redis 재시작
docker-compose restart redis
```

## 📝 API 문서

서버 실행 후 자동 생성된 문서 확인:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 개발

### 로컬에서 Python 직접 실행

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Redis 실행 (Docker)
docker run -d -p 6379:6379 redis:7-alpine

# 개발 서버 실행
python -m app.main
```

### 테스트

```bash
# pytest 설치
pip install pytest pytest-asyncio httpx

# 테스트 실행
pytest tests/
```

## 📄 라이센스

MIT License

## 🤝 기여

Issue 및 PR 환영합니다!
