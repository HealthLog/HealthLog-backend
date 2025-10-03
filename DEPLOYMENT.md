# Oracle VM 배포 가이드

## 🏗️ 아키텍처

```
Oracle VM (138.2.122.234)
├─ Supabase (기존) - Port 54321
│   └─ supabase_network_fitness_database
└─ Embedding API (신규) - Port 8000
    ├─ embedding-api (Supabase 네트워크 연결)
    └─ redis (내부 네트워크만)

Mobile App
├─ Supabase Auth (138.2.122.234:54321) → JWT 토큰 받기
└─ Embedding API (138.2.122.234:8000) → JWT + 임베딩 요청
```

**네트워크 통신:**
- Embedding API ↔ Supabase: `http://supabase_kong_fitness_database:8000` (내부)
- Mobile App → Embedding API: `http://138.2.122.234:8000` (외부)

---

## 📋 배포 전 체크리스트

### 1. 로컬 환경
- [x] Docker 이미지 빌드 완료
- [x] `.env` 파일 프로덕션 설정 완료
- [x] `docker-compose.yml` 네트워크 설정 완료

### 2. Oracle VM
```bash
# SSH 접속 테스트
ssh oracle-instance

# Docker 상태 확인
docker ps
docker network ls | grep supabase

# 디렉토리 준비
mkdir -p ~/embedding-api
```

### 3. Oracle Cloud 방화벽
- [ ] Port 8000 인바운드 규칙 추가 필요

---

## 🚀 배포 단계

### Step 1: 프로젝트 파일 전송

```bash
# 로컬에서 실행
cd /Users/hong-yun-yeong/workspace/fitness_database/embedding-api

# 필수 파일만 전송
scp docker-compose.yml .env prometheus.yml Dockerfile requirements.txt oracle-instance:~/embedding-api/
scp -r app oracle-instance:~/embedding-api/
```

### Step 2: Docker 이미지 빌드

**Option A: 로컬에서 빌드 후 전송 (권장)**
```bash
# 로컬에서 ARM64 이미지 빌드
docker build --platform linux/arm64 -t embedding-api:latest .

# 이미지 저장 및 압축
docker save embedding-api:latest | gzip > embedding-api.tar.gz

# VM으로 전송
scp embedding-api.tar.gz oracle-instance:~/

# VM에서 이미지 로드
ssh oracle-instance
cd ~
gunzip -c embedding-api.tar.gz | docker load
rm embedding-api.tar.gz
```

**Option B: VM에서 직접 빌드**
```bash
# VM에서 실행
ssh oracle-instance
cd ~/embedding-api
docker build -t embedding-api:latest .
```

### Step 3: Oracle Cloud 방화벽 설정

Oracle Cloud Console에서:
1. **Compute → Instances → Your Instance**
2. **Subnet → Security Lists → Default Security List**
3. **Add Ingress Rule**:
   - Source CIDR: `0.0.0.0/0`
   - IP Protocol: `TCP`
   - Destination Port: `8000`
   - Description: `Embedding API`

또는 CLI로:
```bash
# Oracle Cloud CLI 사용 시
oci network security-list-rule add \
  --security-list-id <your-security-list-id> \
  --protocol 6 \
  --source 0.0.0.0/0 \
  --destination-port-range-min 8000 \
  --destination-port-range-max 8000
```

### Step 4: Docker Compose 실행

```bash
# VM에서 실행
ssh oracle-instance
cd ~/embedding-api

# 백그라운드로 실행
docker-compose up -d

# 로그 확인 (모델 로딩 대기 - 1-2분 소요)
docker-compose logs -f embedding-api

# "model_loaded_successfully" 메시지 대기
```

### Step 5: 헬스체크

```bash
# VM 내부에서
curl http://localhost:8000/health

# 로컬에서 (방화벽 열린 후)
curl http://138.2.122.234:8000/health

# 예상 응답
{
  "status": "healthy",
  "model_loaded": true,
  "redis_connected": true
}
```

---

## 🧪 테스트

### 1. JWT 토큰 발급
```bash
# 로컬에서 실행
cd ../embedding-api-tests
./get_token.sh

# 이메일: test@example.com
# 비밀번호: (입력)
# → JWT 토큰 복사
```

### 2. API 테스트
```bash
export JWT_TOKEN='eyJhbG...'

# 단일 임베딩
curl -X POST http://138.2.122.234:8000/embed \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"text": "안녕하세요"}'

# 배치 임베딩
curl -X POST http://138.2.122.234:8000/batch-embed \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["첫 번째", "두 번째"]}'
```

### 3. 자동화 테스트
```bash
cd ../embedding-api-tests
python test_with_token.py
```

---

## 📊 모니터링

### 리소스 사용량
```bash
# 실시간 모니터링
docker stats embedding-api

# 로그 스트리밍
docker-compose logs -f embedding-api

# Prometheus (선택)
open http://138.2.122.234:9090
```

### 주요 메트릭
```bash
# Prometheus 메트릭 확인
curl http://138.2.122.234:8000/metrics

# 주요 지표
# - embed_requests_total: 총 요청 수
# - embed_request_duration_seconds: 요청 처리 시간
# - embed_errors_total: 에러 발생 수
```

---

## 🔧 트러블슈팅

### 모델 로딩 실패
```bash
# HuggingFace 토큰 확인
docker-compose exec embedding-api env | grep HF_TOKEN

# 디스크 공간 확인
df -h
docker system df

# 필요시 정리
docker system prune -a --volumes -f
```

### Supabase 통신 실패
```bash
# 네트워크 연결 확인
docker network inspect supabase_network_fitness_database

# embedding-api가 supabase-network에 연결되어 있는지 확인
docker inspect embedding-api | grep -A 10 Networks

# Supabase Kong 접근 테스트
docker-compose exec embedding-api curl http://supabase_kong_fitness_database:8000/auth/v1/health
```

### Port 8000 접근 불가
```bash
# VM 방화벽 확인 (iptables)
sudo iptables -L -n | grep 8000

# 포트 리스닝 확인
netstat -tlnp | grep 8000

# Oracle Cloud 방화벽 규칙 확인 필요
```

### 컨테이너 재시작
```bash
# 전체 재시작
docker-compose restart

# embedding-api만 재시작
docker-compose restart embedding-api

# 완전 재배포
docker-compose down
docker-compose up -d
```

---

## 🔄 업데이트 절차

### 코드 변경 시
```bash
# 로컬에서 이미지 재빌드
docker build --platform linux/arm64 -t embedding-api:latest .
docker save embedding-api:latest | gzip > embedding-api.tar.gz
scp embedding-api.tar.gz oracle-instance:~/

# VM에서 이미지 교체
ssh oracle-instance
gunzip -c ~/embedding-api.tar.gz | docker load
cd ~/embedding-api
docker-compose up -d --force-recreate embedding-api
```

### 환경 변수 변경 시
```bash
# .env 파일만 전송
scp .env oracle-instance:~/embedding-api/

# 컨테이너 재시작
ssh oracle-instance
cd ~/embedding-api
docker-compose restart embedding-api
```

---

## 🛑 서비스 중지

```bash
ssh oracle-instance
cd ~/embedding-api

# 컨테이너 중지 (볼륨 유지)
docker-compose stop

# 완전 삭제 (볼륨 유지)
docker-compose down

# 볼륨까지 삭제
docker-compose down -v
```

---

## 📱 모바일 앱 연동

### API Endpoint
```
Base URL: http://138.2.122.234:8000
Auth URL: http://138.2.122.234:54321
```

### 인증 흐름
```
1. POST http://138.2.122.234:54321/auth/v1/token?grant_type=password
   → JWT 토큰 받기

2. POST http://138.2.122.234:8000/embed
   Headers: Authorization: Bearer {JWT_TOKEN}
   → 임베딩 결과 받기
```

### 보안 고려사항
- **HTTPS 미적용**: JWT 토큰이 평문 전송됨 (추후 Nginx + Let's Encrypt 권장)
- **Rate Limiting**: 10 req/min (필요시 조정)
- **CORS**: 모바일 앱은 영향 없음

---

## 🔐 보안 강화 (추후)

### HTTPS 설정 (Nginx + Let's Encrypt)
```bash
# Nginx 리버스 프록시 추가
# Certbot으로 SSL 인증서 발급
# 도메인 연결 필요
```

### 모니터링 강화
```bash
# Grafana 추가
# Alertmanager 설정
# 로그 집계 (ELK Stack)
```
