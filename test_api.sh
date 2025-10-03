#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL=${API_URL:-http://localhost:8000}

echo -e "${YELLOW}=== Embedding API 테스트 ===${NC}\n"

# 1. 헬스체크
echo -e "${YELLOW}1. 헬스체크${NC}"
response=$(curl -s -w "\n%{http_code}" ${API_URL}/health)
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✓ 헬스체크 성공${NC}"
    echo "$body" | jq .
else
    echo -e "${RED}✗ 헬스체크 실패 (HTTP $http_code)${NC}"
    echo "$body"
fi

echo ""

# 2. 단일 텍스트 임베딩
echo -e "${YELLOW}2. 단일 텍스트 임베딩${NC}"
response=$(curl -s -w "\n%{http_code}" -X POST ${API_URL}/embed \
    -H "Content-Type: application/json" \
    -d '{"text": "안녕하세요, 임베딩 테스트입니다."}')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✓ 임베딩 성공${NC}"
    echo "$body" | jq '{dimension: .dimension, model: .model, embeddings_sample: .embeddings[:5]}'
else
    echo -e "${RED}✗ 임베딩 실패 (HTTP $http_code)${NC}"
    echo "$body"
fi

echo ""

# 3. 배치 임베딩
echo -e "${YELLOW}3. 배치 텍스트 임베딩${NC}"
response=$(curl -s -w "\n%{http_code}" -X POST ${API_URL}/batch-embed \
    -H "Content-Type: application/json" \
    -d '{
        "texts": [
            "첫 번째 문장입니다.",
            "두 번째 문장입니다.",
            "세 번째 문장입니다."
        ]
    }')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✓ 배치 임베딩 성공${NC}"
    echo "$body" | jq '{dimension: .dimension, model: .model, count: .count}'
else
    echo -e "${RED}✗ 배치 임베딩 실패 (HTTP $http_code)${NC}"
    echo "$body"
fi

echo ""

# 4. Prometheus 메트릭
echo -e "${YELLOW}4. Prometheus 메트릭 확인${NC}"
response=$(curl -s -w "\n%{http_code}" ${API_URL}/metrics)
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✓ 메트릭 엔드포인트 정상${NC}"
    echo "메트릭 샘플:"
    echo "$response" | sed '$d' | grep "embed_requests_total\|embed_request_duration_seconds" | head -5
else
    echo -e "${RED}✗ 메트릭 조회 실패 (HTTP $http_code)${NC}"
fi

echo ""
echo -e "${YELLOW}=== 테스트 완료 ===${NC}"
