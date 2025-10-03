"""Pydantic 모델 정의"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class EmbedRequest(BaseModel):
    """임베딩 요청 모델"""

    text: str = Field(
        ...,
        min_length=1,
        max_length=8192,
        description="임베딩할 텍스트",
        examples=["안녕하세요, 반갑습니다!"]
    )

    normalize: bool = Field(
        default=True,
        description="임베딩 벡터 정규화 여부"
    )

    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """텍스트 검증"""
        if not v.strip():
            raise ValueError('텍스트가 비어있습니다')
        return v.strip()


class EmbedResponse(BaseModel):
    """임베딩 응답 모델"""

    model_config = {"protected_namespaces": ()}  # Pydantic v2: model_ 네임스페이스 충돌 방지

    embeddings: List[float] = Field(
        ...,
        description="임베딩 벡터"
    )

    dimension: int = Field(
        ...,
        description="임베딩 차원"
    )

    model: str = Field(
        ...,
        description="사용된 모델 이름"
    )


class BatchEmbedRequest(BaseModel):
    """배치 임베딩 요청 모델"""

    texts: List[str] = Field(
        ...,
        min_length=1,
        max_length=32,
        description="임베딩할 텍스트 목록"
    )

    normalize: bool = Field(
        default=True,
        description="임베딩 벡터 정규화 여부"
    )

    @field_validator('texts')
    @classmethod
    def validate_texts(cls, v: List[str]) -> List[str]:
        """텍스트 목록 검증"""
        if not v:
            raise ValueError('텍스트 목록이 비어있습니다')

        # 각 텍스트 검증
        cleaned = []
        for text in v:
            if not text.strip():
                raise ValueError('빈 텍스트가 포함되어 있습니다')
            if len(text) > 8192:
                raise ValueError('텍스트가 너무 깁니다 (최대 8192자)')
            cleaned.append(text.strip())

        return cleaned


class BatchEmbedResponse(BaseModel):
    """배치 임베딩 응답 모델"""

    model_config = {"protected_namespaces": ()}  # Pydantic v2: model_ 네임스페이스 충돌 방지

    embeddings: List[List[float]] = Field(
        ...,
        description="임베딩 벡터 목록"
    )

    dimension: int = Field(
        ...,
        description="임베딩 차원"
    )

    model: str = Field(
        ...,
        description="사용된 모델 이름"
    )

    count: int = Field(
        ...,
        description="처리된 텍스트 개수"
    )


class HealthResponse(BaseModel):
    """헬스체크 응답 모델"""

    model_config = {"protected_namespaces": ()}  # Pydantic v2: model_ 네임스페이스 충돌 방지

    status: str = Field(
        ...,
        description="서비스 상태",
        examples=["healthy"]
    )

    model_loaded: bool = Field(
        ...,
        description="모델 로드 상태"
    )

    redis_connected: bool = Field(
        ...,
        description="Redis 연결 상태"
    )


class ErrorResponse(BaseModel):
    """에러 응답 모델"""

    error: str = Field(
        ...,
        description="에러 메시지"
    )

    detail: Optional[str] = Field(
        None,
        description="상세 에러 정보"
    )
