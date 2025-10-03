#!/usr/bin/env python3
"""Supabase JWT 테스트 토큰 생성 스크립트"""

import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# JWT Secret (Supabase에서 사용하는 것과 동일)
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

if not JWT_SECRET:
    print("❌ Error: SUPABASE_JWT_SECRET not found in .env file")
    exit(1)

# 테스트용 페이로드
payload = {
    "sub": "test-user-12345",  # 사용자 ID
    "email": "test@example.com",
    "role": "authenticated",
    "aud": "authenticated",
    "exp": datetime.utcnow() + timedelta(hours=1),  # 1시간 후 만료
    "iat": datetime.utcnow(),
}

# JWT 토큰 생성
token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

print("=" * 60)
print("✅ Supabase JWT 테스트 토큰 생성 완료")
print("=" * 60)
print(f"\n📋 토큰:\n{token}\n")
print("=" * 60)
print("📝 페이로드:")
print(f"  - 사용자 ID: {payload['sub']}")
print(f"  - 이메일: {payload['email']}")
print(f"  - 역할: {payload['role']}")
print(f"  - 만료 시간: {payload['exp']}")
print("=" * 60)
print("\n🧪 테스트 방법:")
print(f"""
curl -X POST http://localhost:8000/embed \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer {token}" \\
  -d '{{"text": "테스트 텍스트입니다."}}'
""")
print("=" * 60)
