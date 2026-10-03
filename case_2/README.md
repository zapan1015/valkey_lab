# 사례 2. 세션 저장소

해시로 세션을 저장하고, `EXPIRE`로 만료와 활동 시 갱신을 구현하는 과정을 검증합니다.

## 실행

```bash
docker compose up -d --wait
python test.py
docker compose down -v
```

직접 실습하려면 `docker exec -it valkey-case2 valkey-cli`로 접속합니다.

## 검증 항목

- 필드 3개 저장 후 `HGETALL`로 모두 조회
- `EXPIRE 1800` 직후 `TTL`이 1795~1800
- 2초 경과 후 `TTL` 감소, `EXPIRE` 재호출 후 복구
- 기존 필드 `HSET`은 `0` 반환, 값 변경, TTL 유지
- TTL 2초 세션이 3초 뒤 자동 삭제
- `DEL` 후 세션 없음

마지막 실행 결과는 `output.txt`에 있습니다.
