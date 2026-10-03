"""사례 7. Pub/Sub 검증 스크립트.

검증 항목
  1) 구독자가 있을 때: 메시지 수신, PUBLISH 반환값 1
  2) 구독자가 없을 때: PUBLISH 반환값 0, 메시지 유실
  3) 늦게 구독한 클라이언트는 과거 메시지를 받지 못함

구독자는 컨테이너 안에서 timeout 명령으로 스스로 종료하게 합니다.
(docker exec 클라이언트만 종료하면 컨테이너 안의 구독자가 남을 수 있기 때문입니다.)
"""
import re
import subprocess
import sys
import time

CONTAINER = "valkey-case7"
sys.stdout.reconfigure(encoding="utf-8")
results = []


def cli(*args):
    r = subprocess.run(
        ["docker", "exec", CONTAINER, "valkey-cli", "--no-raw", *args],
        capture_output=True, text=True, encoding="utf-8",
    )
    return r.stdout.strip()


def check(name, ok):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}\n")


def start_subscriber(seconds):
    return subprocess.Popen(
        ["docker", "exec", CONTAINER, "timeout", str(seconds),
         "valkey-cli", "--no-raw", "SUBSCRIBE", "alerts"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8",
    )


def subscribers():
    out = cli("PUBSUB", "NUMSUB", "alerts")
    return int(re.findall(r"\d+", out)[-1])


print("=== 1. 구독자가 있을 때 ===")
sub = start_subscriber(4)
time.sleep(1.5)
print(f"> PUBSUB NUMSUB alerts -> 구독자 {subscribers()}명")
check("구독자 1명 확인", subscribers() == 1)

out = cli("PUBLISH", "alerts", "price changed: 59000")
print(f"> PUBLISH alerts \"price changed: 59000\"\n{out}")
check("PUBLISH 반환값 1 (수신자 1명)", out == "(integer) 1")

sub_out, _ = sub.communicate()
print("구독자 터미널 출력:\n" + sub_out.strip() + "\n")
check("구독자가 메시지를 수신",
      '"message"' in sub_out and "price changed: 59000" in sub_out)

print("=== 2. 구독자가 없을 때 ===")
print(f"> PUBSUB NUMSUB alerts -> 구독자 {subscribers()}명")
check("구독자 0명 확인(이전 구독자가 남아 있지 않음)", subscribers() == 0)
out = cli("PUBLISH", "alerts", "missed message")
print(f"> PUBLISH alerts \"missed message\"\n{out}")
check("PUBLISH 반환값 0 (수신자 없음)", out == "(integer) 0")

print("=== 3. 늦게 구독한 클라이언트 ===")
late = start_subscriber(3)
time.sleep(3.5)
late_out, _ = late.communicate()
print("늦은 구독자 출력:\n" + late_out.strip() + "\n")
check("구독 확인 응답만 있고 'missed message'는 없음",
      '"subscribe"' in late_out and "missed message" not in late_out)

print(f"결과: {sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
