"""사례 3. 레이트 리미팅 검증 스크립트.

검증 항목
  A) 고정 윈도우: INCR + EXPIRE 를 Lua로 묶어 원자적으로 처리, 한도 초과 판정, 윈도우 경과 후 초기화
  B) 슬라이딩 윈도우: 정렬된 셋으로 오래된 기록 제거 후 허용/거절 판정
"""
import re
import subprocess
import sys
import time

CONTAINER = "valkey-case3"
sys.stdout.reconfigure(encoding="utf-8")
results = []


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


def num(out):
    return int(re.search(r"-?\d+", out).group())


# 카운터 증가와 최초 TTL 설정을 한 번에 실행합니다.
FIXED_LUA = (
    "local c = server.call('INCR', KEYS[1]) "
    "if c == 1 then server.call('EXPIRE', KEYS[1], ARGV[1]) end "
    "return c"
)
LIMIT = 5

print("=== A. 고정 윈도우 (1분 5회) ===")
key = "ratelimit:user:42:202610032100"
counts = []
for i in range(1, 8):
    c = num(cli("EVAL", FIXED_LUA, "1", key, "60"))
    counts.append(c)
    print(f"요청 {i}: 카운터={c} -> {'허용' if c <= LIMIT else '거절'}")
print()
check("카운터가 1부터 7까지 순서대로 증가", counts == [1, 2, 3, 4, 5, 6, 7])
check("5회까지 허용, 6회부터 거절", [c <= LIMIT for c in counts] == [True] * 5 + [False] * 2)

out = cli("TTL", key)
show(f"TTL {key}", out)
check("카운터에 TTL(1~60초)이 설정됨", 1 <= num(out) <= 60)

print("--- 윈도우 경과 후 초기화 (2초 윈도우) ---")
short = "ratelimit:user:43:short"
for _ in range(3):
    cli("EVAL", FIXED_LUA, "1", short, "2")
time.sleep(3)
c = num(cli("EVAL", FIXED_LUA, "1", short, "2"))
print(f"3초 경과 후 첫 요청의 카운터: {c}\n")
check("윈도우 경과 후 카운터가 1로 초기화", c == 1)

print("=== B. 슬라이딩 윈도우 (60초 3회) ===")
sk, WINDOW, SLIDE_LIMIT = "sliding:user:42", 60, 3


def request(now, member):
    """오래된 기록을 지운 뒤, 한도 미만이면 기록하고 허용합니다."""
    removed = num(cli("ZREMRANGEBYSCORE", sk, "-inf", str(now - WINDOW)))
    count = num(cli("ZCARD", sk))
    allowed = count < SLIDE_LIMIT
    if allowed:
        cli("ZADD", sk, str(now), member)
    print(f"t={now}s: 제거={removed}, 기존 건수={count} -> {'허용' if allowed else '거절'}")
    return removed, count, allowed


r1 = request(100, "req-1")
r2 = request(130, "req-2")
r3 = request(155, "req-3")
r4 = request(156, "req-4")
r5 = request(170, "req-5")
r6 = request(171, "req-6")
print()
check("t=100,130,155 요청은 허용", r1[2] and r2[2] and r3[2])
check("t=156 요청은 3건이 창 안에 있어 거절", r4[2] is False and r4[1] == 3)
check("t=170에 req-1(t=100)이 창 밖으로 밀려 제거되고 허용", r5[0] == 1 and r5[2])
check("t=171 요청은 다시 3건이 되어 거절", r6[2] is False and r6[1] == 3)

print(f"결과: {sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
