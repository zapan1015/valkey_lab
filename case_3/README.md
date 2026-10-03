# 사례 3. 레이트 리미팅

Lua로 묶은 `INCR`+`EXPIRE` 고정 윈도우와, 정렬된 셋 기반 슬라이딩 윈도우의 허용/거절 판정을 검증합니다.

## 실행

```bash
docker compose up -d --wait
python test.py
docker compose down -v
```

직접 실습하려면 `docker exec -it valkey-case3 valkey-cli`로 접속합니다.

## 검증 항목

- 고정 윈도우 7회 호출: 카운터 1~7, 5회까지 허용
- 카운터에 TTL(1~60초) 설정
- 2초 윈도우가 지난 뒤 카운터가 1로 초기화
- 슬라이딩 윈도우(60초 3회): 시각 100/130/155 허용, 156 거절, 170에 오래된 기록 1건 제거 후 허용, 171 거절

마지막 실행 결과는 `output.txt`에 있습니다.
