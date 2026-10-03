# 사례 6. 큐와 스트림

스트림과 컨슈머 그룹으로 메시지 분배, ACK, 워커 중단 후 재처리, 길이 관리를 검증합니다.

## 실행

```bash
docker compose up -d --wait
python test.py
docker compose down -v
```

직접 실습하려면 `docker exec -it valkey-case6 valkey-cli`로 접속합니다.

## 검증 항목

- `XGROUP CREATE ... MKSTREAM` 성공, 메시지 ID가 `밀리초-순번` 형식
- 두 워커가 서로 다른 메시지를 받음
- ACK 전 대기 2건, worker-2 ACK 후 1건
- `XAUTOCLAIM`으로 worker-2가 worker-1의 미처리 메시지를 인계받고 ACK 후 대기 0건
- `XTRIM MAXLEN 1` 후 스트림 길이 1

마지막 실행 결과는 `output.txt`에 있습니다.
