# 멀티스테이지 빌드 - ARM64 최적화
FROM python:3.11-slim as builder

# 빌드 의존성
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 런타임 스테이지
FROM python:3.11-slim

# 런타임 의존성만 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 비root 사용자 생성 (보안)
RUN useradd -m -u 1000 appuser

# 빌드 스테이지에서 Python 패키지 복사
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# 작업 디렉토리 설정
WORKDIR /app

# 애플리케이션 코드 복사
COPY --chown=appuser:appuser ./app ./app

# 모델 캐시 디렉토리 (선택적)
RUN mkdir -p /home/appuser/.cache/huggingface && \
    chown -R appuser:appuser /home/appuser/.cache

# 비root 사용자로 전환
USER appuser

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 포트 노출
EXPOSE 8000

# Uvicorn 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
