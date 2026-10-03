# 사례 8. 분산 락

`SET ... NX PX`로 락을 얻고, Lua 스크립트로 소유자 확인 후 해제하며, 동시 경쟁과 TTL 만료를 검증합니다.

## 실행

```bash
docker compose up -d --wait
python test.py
docker compose down -v
```

직접 실습하려면 터미널 두 개에서 `docker exec -it valkey-case8 valkey-cli`로 접속합니다.

## 검증 항목

- A 획득 `OK`, B 획득 시도 `(nil)`
- B의 잘못된 토큰으로 해제하면 `0`, A의 올바른 토큰으로 해제하면 `1`
- 20개 클라이언트가 동시에 시도하면 정확히 1명만 성공
- `PX 3000` 락이 3.5초 뒤 사라짐
- 토큰 검증 없이 `DEL`하면 남의 락이 지워짐(위험 시연)

이 사례는 단일 인스턴스를 전제로 합니다. 프라이머리 장애 시 락 유실 가능성은 본문 사례 8의 운영 시 주의점을 참고하십시오.

마지막 실행 결과는 `output.txt`에 있습니다.
