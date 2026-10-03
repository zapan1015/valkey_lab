"""사례 8. 분산 락 검증 스크립트.

검증 항목
  1) SET NX PX 로 락 획득, 경쟁자 실패
  2) 동시 경쟁 시 정확히 1개 클라이언트만 락 획득
  3) 소유자 토큰 검증 후 해제(Lua): 잘못된 토큰은 해제 불가
  4) TTL 만료로 락 자동 해제(작업자 중단 시나리오)
  5) 소유자 검증 없이 DEL 하면 남의 락을 지울 수 있음(위험 시연)
"""
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

CONTAINER = "valkey-case8"
sys.stdout.reconfigure(encoding="utf-8")
results = []

RELEASE = ("if server.call('get',KEYS[1]) == ARGV[1] "
           "then return server.call('del',KEYS[1]) else return 0 end")


def cli(*args):
    r = subprocess.run(
        ["docker", "exec", CONTAINER, "valkey-cli", "--no-raw", *args],
        capture_output=True, text=True, encoding="utf-8",
    )
    return r.stdout.strip()


def show(cmd, out):
    print(f"> {cmd}\n{out}")


def check(name, ok):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}\n")


lock = "lock:daily-settlement"

print("=== 1. 락 획득과 경쟁 ===")
out = cli("SET", lock, "token-A", "NX", "PX", "30000")
show(f"SET {lock} token-A NX PX 30000   (A)", out)
check("A가 락 획득(OK)", out == "OK")

out = cli("SET", lock, "token-B", "NX", "PX", "30000")
show(f"SET {lock} token-B NX PX 30000   (B)", out)
check("B는 획득 실패(nil)", out == "(nil)")

print("=== 2. 소유자 검증 후 해제 ===")
out = cli("EVAL", RELEASE, "1", lock, "token-B")
show(f"EVAL <release> 1 {lock} token-B   (B)", out)
check("B의 잘못된 토큰은 해제 불가(0)", out == "(integer) 0")
check("락은 여전히 token-A 소유", cli("GET", lock) == '"token-A"')

out = cli("EVAL", RELEASE, "1", lock, "token-A")
show(f"EVAL <release> 1 {lock} token-A   (A)", out)
check("A가 해제(1)", out == "(integer) 1")

out = cli("SET", lock, "token-B", "NX", "PX", "30000")
show(f"SET {lock} token-B NX PX 30000   (B, 재시도)", out)
check("해제 후 B가 락 획득", out == "OK")
cli("DEL", lock)

print("=== 3. 동시 경쟁: 20개 클라이언트가 동시에 시도 ===")
race = "lock:race"
with ThreadPoolExecutor(max_workers=20) as pool:
    outs = list(pool.map(
        lambda i: cli("SET", race, f"client-{i}", "NX", "PX", "10000"), range(20)))
winners = outs.count("OK")
print(f"획득 성공 {winners}명, 실패 {outs.count('(nil)')}명\n")
check("정확히 1명만 락 획득", winners == 1 and outs.count("(nil)") == 19)
cli("DEL", race)

print("=== 4. TTL 만료로 자동 해제 ===")
out = cli("SET", "lock:test", "token-A", "NX", "PX", "3000")
show("SET lock:test token-A NX PX 3000", out)
out = cli("PTTL", "lock:test")
show("PTTL lock:test", out)
pttl = int(re.search(r"-?\d+", out).group())
check("PTTL이 1~3000ms", 1 <= pttl <= 3000)
time.sleep(3.5)
out = cli("GET", "lock:test")
show("GET lock:test (3.5초 경과)", out)
check("만료 후 락이 사라짐(nil)", out == "(nil)")

print("=== 5. [위험 시연] 소유자 검증 없는 DEL ===")
cli("SET", "lock:unsafe", "token-A", "NX", "PX", "30000")
print("A가 락을 쥔 상태에서, 락을 갖지 못한 B가 단순 DEL을 실행하면:")
out = cli("DEL", "lock:unsafe")
show("DEL lock:unsafe   (B)", out)
check("남의 락이 삭제됨(1) -> 반드시 토큰 검증이 필요", out == "(integer) 1")

print(f"결과: {sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
