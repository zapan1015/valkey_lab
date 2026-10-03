# 사례 7. Pub/Sub

구독자가 있을 때의 수신과, 구독자가 없을 때의 메시지 유실을 검증합니다.

## 실행

```bash
docker compose up -d --wait
python test.py
docker compose down -v
```

직접 실습하려면 터미널 두 개에서 `docker exec -it valkey-case7 valkey-cli`로 접속해 한쪽에서 `SUBSCRIBE alerts`, 다른 쪽에서 `PUBLISH alerts "hello"`를 실행합니다.

## 검증 항목

- 구독 중 `PUBSUB NUMSUB alerts`가 1, `PUBLISH`가 `1` 반환, 구독자가 메시지 수신
- 구독 종료 후 `PUBSUB NUMSUB alerts`가 0, `PUBLISH`가 `0` 반환
- 늦게 구독한 클라이언트는 구독 응답만 받고 과거 메시지를 받지 못함

구독자는 컨테이너 안에서 `timeout` 명령으로 실행해 정해진 시간에 스스로 종료합니다. 호스트의 `docker exec` 프로세스만 종료하면 컨테이너 안의 구독자가 남을 수 있기 때문입니다.

마지막 실행 결과는 `output.txt`에 있습니다.
