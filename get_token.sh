#!/bin/bash
# Supabase JWT 토큰 발급 스크립트

SUPABASE_URL="http://138.2.122.234:54321"

echo "=========================================="
echo "Supabase JWT 토큰 발급"
echo "=========================================="
echo ""

# 사용자 입력
read -p "이메일: " EMAIL
read -sp "비밀번호: " PASSWORD
echo ""
echo ""

# 1. 회원가입 시도
echo "[1/2] 회원가입 시도..."
SIGNUP_RESPONSE=$(curl -s -X POST "${SUPABASE_URL}/auth/v1/signup" \
  -H "apikey: sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}")

if echo "$SIGNUP_RESPONSE" | grep -q "access_token"; then
    echo "✅ 회원가입 성공!"
    ACCESS_TOKEN=$(echo "$SIGNUP_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

    echo ""
    echo "=========================================="
    echo "✅ JWT 토큰 발급 완료!"
    echo "=========================================="
    echo ""
    echo "토큰:"
    echo "$ACCESS_TOKEN"
    echo ""
    echo "환경 변수 설정:"
    echo "export JWT_TOKEN='${ACCESS_TOKEN}'"
    echo ""
    exit 0
fi

# 2. 이미 가입된 경우 로그인
echo "이미 가입된 사용자입니다. 로그인 시도..."
LOGIN_RESPONSE=$(curl -s -X POST "${SUPABASE_URL}/auth/v1/token?grant_type=password" \
  -H "apikey: sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ 로그인 성공!"
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

    echo ""
    echo "=========================================="
    echo "✅ JWT 토큰 발급 완료!"
    echo "=========================================="
    echo ""
    echo "토큰:"
    echo "$ACCESS_TOKEN"
    echo ""
    echo "환경 변수 설정:"
    echo "export JWT_TOKEN='${ACCESS_TOKEN}'"
    echo ""
else
    echo "❌ 로그인 실패"
    echo "응답: $LOGIN_RESPONSE"
    exit 1
fi
