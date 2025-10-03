#!/usr/bin/env python3
"""
Embedding API 통합 테스트 스크립트

사용법:
    1. Supabase에서 JWT 토큰 발급
    2. 환경 변수 설정: export JWT_TOKEN="your_token_here"
    3. 스크립트 실행: python3 test_with_token.py
"""

import os
import sys
import json
import requests
from typing import List, Dict, Any

# API 설정
API_URL = "http://localhost:8000"

# JWT 토큰 (환경 변수에서 가져오기)
JWT_TOKEN = os.getenv("JWT_TOKEN")

if not JWT_TOKEN:
    print("❌ JWT_TOKEN 환경 변수가 설정되지 않았습니다.")
    print("\n토큰 발급 방법:")
    print("1. Supabase 대시보드: http://138.2.122.234:54321")
    print("2. 사용자 등록/로그인 후 토큰 복사")
    print("3. 환경 변수 설정: export JWT_TOKEN='your_token_here'")
    print("4. 다시 실행: python3 test_with_token.py")
    sys.exit(1)

# HTTP 헤더
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {JWT_TOKEN}"
}


def test_health_check():
    """Health check 테스트"""
    print("\n[1/3] Health Check 테스트...")
    response = requests.get(f"{API_URL}/health")
    data = response.json()

    print(json.dumps(data, indent=2, ensure_ascii=False))

    if data["status"] == "healthy":
        print("✅ Health check 성공")
        return True
    else:
        print("❌ Health check 실패")
        return False


def test_single_embed():
    """단일 텍스트 임베딩 테스트"""
    print("\n[2/3] 단일 텍스트 임베딩 테스트...")

    payload = {
        "text": "안녕하세요, 이것은 테스트 문장입니다.",
        "normalize": True
    }

    try:
        response = requests.post(
            f"{API_URL}/embed",
            headers=HEADERS,
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ 임베딩 성공!")
            print(f"   - 모델: {data['model']}")
            print(f"   - 차원: {data['dimension']}")
            print(f"   - 벡터 샘플: {data['embeddings'][:5]}...")
            return True
        else:
            print(f"❌ 임베딩 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False


def test_batch_embed():
    """배치 임베딩 테스트"""
    print("\n[3/3] 배치 임베딩 테스트...")

    payload = {
        "texts": [
            "첫 번째 문장입니다.",
            "두 번째 문장입니다.",
            "세 번째 문장입니다."
        ],
        "normalize": True
    }

    try:
        response = requests.post(
            f"{API_URL}/batch-embed",
            headers=HEADERS,
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ 배치 임베딩 성공!")
            print(f"   - 모델: {data['model']}")
            print(f"   - 차원: {data['dimension']}")
            print(f"   - 처리 개수: {data['count']}")
            print(f"   - 첫 번째 벡터 샘플: {data['embeddings'][0][:5]}...")
            return True
        else:
            print(f"❌ 배치 임베딩 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False


def main():
    print("=" * 50)
    print("Embedding API 통합 테스트")
    print("=" * 50)

    results = []

    # 테스트 실행
    results.append(("Health Check", test_health_check()))
    results.append(("단일 임베딩", test_single_embed()))
    results.append(("배치 임베딩", test_batch_embed()))

    # 결과 요약
    print("\n" + "=" * 50)
    print("테스트 결과 요약")
    print("=" * 50)

    for name, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{name}: {status}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 모든 테스트 통과!")
        sys.exit(0)
    else:
        print("\n⚠️ 일부 테스트 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
