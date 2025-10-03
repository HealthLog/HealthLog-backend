"""FastAPI 임베딩 API 메인 애플리케이션"""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import Counter, Histogram, make_asgi_app
import redis.asyncio as redis
from typing import Optional
import torch
from transformers import AutoTokenizer, AutoModel
from jose import jwt, JWTError

from .config import get_settings
from .models import (
    EmbedRequest,
    EmbedResponse,
    BatchEmbedRequest,
    BatchEmbedResponse,
    HealthResponse,
    ErrorResponse,
)

# 설정 로드
settings = get_settings()

# 로거 설정
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

# Prometheus 메트릭
REQUEST_COUNT = Counter("embed_requests_total", "Total embedding requests")
REQUEST_DURATION = Histogram("embed_request_duration_seconds", "Request duration")
ERROR_COUNT = Counter("embed_errors_total", "Total errors", ["error_type"])

# 전역 변수
model: Optional[AutoModel] = None
tokenizer: Optional[AutoTokenizer] = None
redis_client: Optional[redis.Redis] = None

# Security
security = HTTPBearer(auto_error=False)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global model, tokenizer, redis_client

    logger.info("starting_application", model=settings.model_name)

    try:
        # 모델 로드
        logger.info("loading_model", model=settings.model_name)
        tokenizer = AutoTokenizer.from_pretrained(
            settings.model_name,
            token=settings.hf_token  # HuggingFace 인증 토큰
        )
        model = AutoModel.from_pretrained(
            settings.model_name,
            torch_dtype=torch.float16 if settings.model_quantization == "fp16" else torch.float32,
            token=settings.hf_token  # HuggingFace 인증 토큰
        )
        model.eval()

        # INT8 양자화 (선택적)
        if settings.model_quantization == "int8":
            logger.info("applying_int8_quantization")
            # 실제로는 torch.quantization 사용
            # model = torch.quantization.quantize_dynamic(
            #     model, {torch.nn.Linear}, dtype=torch.qint8
            # )

        logger.info("model_loaded_successfully", model=settings.model_name)

        # Redis 연결
        logger.info("connecting_to_redis", url=settings.redis_url)
        redis_client = redis.from_url(settings.redis_url, decode_responses=False)
        await redis_client.ping()
        logger.info("redis_connected_successfully")

    except Exception as e:
        logger.error("startup_failed", error=str(e))
        raise

    yield

    # 종료 시 정리
    logger.info("shutting_down")
    if redis_client:
        await redis_client.close()
    logger.info("shutdown_complete")


# FastAPI 앱 생성
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiter 예외 처리
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Prometheus 메트릭 엔드포인트
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> str:
    """JWT 토큰 검증 (Supabase) - 인증 필수

    Args:
        credentials: HTTP Bearer 토큰

    Returns:
        str: 사용자 ID (sub claim)

    Raises:
        HTTPException: 토큰이 없거나 유효하지 않은 경우 (401)
    """
    # 토큰이 없으면 거부
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide a valid JWT token in Authorization header."
        )

    try:
        # JWT 디코딩 및 검증
        payload = jwt.decode(
            credentials.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": False,  # audience 검증 스킵 (필요시 True로 변경)
            }
        )

        # 사용자 ID 추출 (sub claim)
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("jwt_missing_sub", payload=payload)
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user ID"
            )

        # 추가 검증: role 확인 (선택적)
        role = payload.get("role")
        logger.info("jwt_verified", user_id=user_id, role=role)

        return user_id

    except jwt.ExpiredSignatureError:
        logger.warning("jwt_expired")
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except JWTError as e:
        logger.warning("jwt_invalid", error=str(e))
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        logger.error("jwt_verification_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Token verification failed"
        )


@app.get("/", response_model=dict)
async def root():
    """루트 엔드포인트"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "endpoints": {
            "embed": "/embed",
            "batch_embed": "/batch-embed",
            "health": "/health",
            "metrics": "/metrics",
        },
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크 엔드포인트"""
    model_loaded = model is not None
    redis_connected = False

    try:
        if redis_client:
            await redis_client.ping()
            redis_connected = True
    except Exception:
        pass

    status = "healthy" if (model_loaded and redis_connected) else "unhealthy"

    return HealthResponse(
        status=status,
        model_loaded=model_loaded,
        redis_connected=redis_connected,
    )


@app.post("/embed", response_model=EmbedResponse)
@limiter.limit(f"{settings.rate_limit_per_min}/minute")
async def embed_text(
    request: Request,
    embed_request: EmbedRequest,
    user_id: str = Depends(verify_token),
):
    """단일 텍스트 임베딩 (인증 필수)"""
    REQUEST_COUNT.inc()

    try:
        with REQUEST_DURATION.time():
            # 토크나이징
            inputs = tokenizer(
                embed_request.text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=settings.max_seq_length,
            )

            # 추론
            with torch.no_grad():
                outputs = model(**inputs)
                # 평균 풀링
                embeddings = outputs.last_hidden_state.mean(dim=1).squeeze()

                # 정규화
                if embed_request.normalize:
                    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=0)

                embeddings_list = embeddings.tolist()

            logger.info(
                "embed_success",
                user_id=user_id,
                text_length=len(embed_request.text),
                dimension=len(embeddings_list),
            )

            return EmbedResponse(
                embeddings=embeddings_list,
                dimension=len(embeddings_list),
                model=settings.model_name,
            )

    except Exception as e:
        ERROR_COUNT.labels(error_type=type(e).__name__).inc()
        logger.error("embed_failed", error=str(e), user_id=user_id)
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")


@app.post("/batch-embed", response_model=BatchEmbedResponse)
@limiter.limit(f"{settings.rate_limit_per_min}/minute")
async def batch_embed_text(
    request: Request,
    batch_request: BatchEmbedRequest,
    user_id: str = Depends(verify_token),
):
    """배치 텍스트 임베딩 (인증 필수)"""
    REQUEST_COUNT.inc()

    if len(batch_request.texts) > settings.max_batch_size:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size exceeds maximum: {settings.max_batch_size}",
        )

    try:
        with REQUEST_DURATION.time():
            # 토크나이징
            inputs = tokenizer(
                batch_request.texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=settings.max_seq_length,
            )

            # 추론
            with torch.no_grad():
                outputs = model(**inputs)
                # 평균 풀링
                embeddings = outputs.last_hidden_state.mean(dim=1)

                # 정규화
                if batch_request.normalize:
                    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

                embeddings_list = embeddings.tolist()

            logger.info(
                "batch_embed_success",
                user_id=user_id,
                batch_size=len(batch_request.texts),
                dimension=len(embeddings_list[0]),
            )

            return BatchEmbedResponse(
                embeddings=embeddings_list,
                dimension=len(embeddings_list[0]),
                model=settings.model_name,
                count=len(embeddings_list),
            )

    except Exception as e:
        ERROR_COUNT.labels(error_type=type(e).__name__).inc()
        logger.error("batch_embed_failed", error=str(e), user_id=user_id)
        raise HTTPException(status_code=500, detail=f"Batch embedding failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
