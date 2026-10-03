# 사례 1. 캐싱

Valkey에 결과를 TTL과 함께 저장하는 캐시 어사이드 패턴과, 메모리 한도 초과 시 `allkeys-lru` 정책에 의한 키 제거를 검증합니다.

## 실행

```bash
docker compose up -d --wait
python test.py
docker compose down -v
```

직접 실습하려면 `docker exec -it valkey-case1 valkey-cli`로 접속합니다.

## 검증 항목

- 저장 전 `GET`은 `(nil)`, 저장 후 `GET`은 저장한 값
- 통계 초기화 후 `keyspace_hits:1`, `keyspace_misses:1`
- `TTL`이 590~600초
- `valkey-bundle`의 기준 `used_memory`가 2MB를 넘는지 확인
- `maxmemory 8mb`에서 1KB 값 8,000건을 기록하면 `evicted_keys > 0`

모든 항목은 `PASS`/`FAIL`로 판정하며, 하나라도 실패하면 종료 코드 1을 반환합니다. 마지막 실행 결과는 `output.txt`에 있습니다.
