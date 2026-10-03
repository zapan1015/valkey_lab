# 사례 5. 벡터 검색과 시맨틱 캐싱

Valkey-Search 모듈의 HNSW 벡터 인덱스, KNN 검색, 임계값 기반 캐시 판정, 테넌트 분리를 검증합니다.
`valkey/valkey-bundle` 이미지가 필요합니다.

## 실행

```bash
docker compose up -d --wait
docker compose run --rm pyclient sh -c "pip install -q valkey && python vector_demo.py"
docker compose down -v
```

`pyclient`는 `tools` 프로필에 속하므로 `up` 명령으로는 시작되지 않고 `run`으로만 실행됩니다.

## 검증 항목

- `search` 모듈 로드 확인
- userA 범위 KNN 검색에서 `qa:1` 선택
- 서버의 `score`가 코드로 직접 계산한 코사인 거리와 일치(오차 1e-4 이내)
- 유사한 질문은 거리 ≤ 0.1(적중), 무관한 질문은 거리 > 0.1(미스)
- userA/userB 필터 검색이 각자의 항목만 반환, 필터가 없으면 다른 테넌트 항목도 후보

마지막 실행 결과는 `output.txt`에 있습니다.
