"""사례 1. 캐싱 검증 스크립트.

검증 항목
  1) 캐시 미스 -> 저장 -> 캐시 적중 흐름과 keyspace_hits/misses 통계
  2) SET ... EX 로 지정한 TTL
  3) maxmemory 초과 시 allkeys-lru 정책에 의한 키 제거(evicted_keys > 0)
"""
import re
import subprocess
import sys

CONTAINER = "valkey-case1"
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


def info(section, key):
    m = re.search(rf"^{key}:(\S+)", cli("INFO", section), re.M)
    return m.group(1) if m else None


print("=== 1. 캐시 어사이드: 미스 -> 저장 -> 적중 ===")
cli("CONFIG", "RESETSTAT")
value = '{"name":"keyboard","price":59000}'
out = cli("GET", "product:123")
show("GET product:123", out)
check("처음 조회는 캐시 미스(nil)", out == "(nil)")

out = cli("SET", "product:123", value, "EX", "600")
show('SET product:123 "{...}" EX 600', out)
check("SET 성공(OK)", out == "OK")

out = cli("GET", "product:123")
show("GET product:123", out)
check("두 번째 조회는 캐시 적중", "keyboard" in out)

hits, misses = info("stats", "keyspace_hits"), info("stats", "keyspace_misses")
show("INFO stats (발췌)", f"keyspace_hits:{hits}\nkeyspace_misses:{misses}")
check("hits=1, misses=1", (hits, misses) == ("1", "1"))

out = cli("TTL", "product:123")
show("TTL product:123", out)
ttl = int(re.search(r"-?\d+", out).group())
check("TTL이 590~600초 범위", 590 <= ttl <= 600)

out = cli("DEL", "product:123")
show("DEL product:123", out)
check("DEL은 1건 삭제", out == "(integer) 1")

print("=== 2. maxmemory 초과 시 키 제거 ===")
used = int(info("memory", "used_memory"))
print(f"기준 used_memory: {used} bytes (모듈 포함 빈 서버)")
check("기준 사용량이 2MB를 넘으므로 2mb 제한은 부적합", used > 2 * 1024 * 1024)

show("CONFIG SET maxmemory 8mb", cli("CONFIG", "SET", "maxmemory", "8mb"))
show("CONFIG SET maxmemory-policy allkeys-lru",
     cli("CONFIG", "SET", "maxmemory-policy", "allkeys-lru"))
show("CONFIG GET maxmemory-policy", cli("CONFIG", "GET", "maxmemory-policy"))
cli("CONFIG", "RESETSTAT")

# 1KB 값을 가진 키 8,000개(약 8MB)를 기록해 한도를 넘깁니다.
subprocess.run(
    ["docker", "exec", CONTAINER, "valkey-benchmark", "-t", "set",
     "-n", "8000", "-d", "1024", "-r", "8000", "-q"],
    capture_output=True, text=True,
)
evicted = int(info("stats", "evicted_keys"))
dbsize = int(re.search(r"\d+", cli("DBSIZE")).group())
used_after = int(info("memory", "used_memory"))
show("INFO stats (발췌)", f"evicted_keys:{evicted}")
show("DBSIZE", f"{dbsize}")
check("evicted_keys > 0 (키가 실제로 제거됨)", evicted > 0)
check("남은 키 수가 기록 시도(8,000)보다 적음", dbsize < 8000)
check("used_memory가 maxmemory(8MB) 부근에서 유지됨",
      used_after <= 8 * 1024 * 1024 * 1.05)

print(f"결과: {sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
