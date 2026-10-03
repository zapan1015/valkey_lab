# 사례 4. 실시간 리더보드

정렬된 셋으로 점수 기록, 순위 조회, 순위 변동, 동점 정렬 규칙을 검증합니다.

## 실행

```bash
docker compose up -d --wait
python test.py
docker compose down -v
```

직접 실습하려면 `docker exec -it valkey-case4 valkey-cli`로 접속합니다.

## 검증 항목

- 점수 증가 후 상위 3명이 bob(195), carol(150), alice(120)
- `ZREVRANK`는 0부터 시작, 없는 멤버는 `(nil)`
- 점수 증가 시 순위 즉시 변경
- 동점은 사전순, `REV` 조회 시 역순
- `EXPIRE 604800` 적용

마지막 실행 결과는 `output.txt`에 있습니다.
