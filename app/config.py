"""애플리케이션 설정"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os


class Settings(BaseSettings):
    """애플리케이션 설정 클래스

    .env 파일 또는 환경 변수에서 설정을 로드합니다.
    민감한 정보는 반드시 .env 파일에서 관리하세요.
    """

    # 애플리케이션
    app_name: str = "Embedding API"
    app_version: str = "0.1.0"
    debug: bool = False

    # 모델 설정
    model_name: str = "google/embeddinggemma-300m"
    model_quantization: str = "int8"  # int8, fp16, fp32
    max_batch_size: int = 8
    max_seq_length: int = 2048

    # HuggingFace 인증 (Gated Model 접근용)
    hf_token: Optional[str] = None

    # Redis (Docker Compose 사용 시: redis://redis:6379)
    redis_url: str = "redis://localhost:6379"

    # Rate Limiting
    rate_limit_per_min: int = 10

    # Supabase JWT 검증용 (필수 설정)
    # Self-hosted Supabase의 경우 docker-compose.yml에서 JWT_SECRET 확인
    supabase_jwt_secret: str = ""  # 필수: JWT 검증용 시크릿

    # 선택 설정 (필요시)
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None

    # CORS (프로덕션에서는 특정 도메인만 허용)
    cors_origins: list[str] = ["*"]

    # 로깅
    log_level: str = "INFO"

    model_config = {
        # .env 파일에서 설정 로드
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        # Pydantic v2: model_ 네임스페이스 충돌 방지
        "protected_namespaces": (),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # JWT Secret 필수 체크 (프로덕션 모드)
        if not self.debug and not self.supabase_jwt_secret:
            raise ValueError(
                "SUPABASE_JWT_SECRET is required in production mode. "
                "Please set it in .env file or environment variable."
            )


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글톤 반환

    .env 파일이 없으면 환경 변수에서 로드됩니다.
    """
    return Settings()
