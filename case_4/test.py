"""사례 4. 실시간 리더보드 검증 스크립트.

검증 항목
  1) 점수 기록, 점수 증가, 상위 N명 조회, 순위/점수 조회
  2) 점수 증가에 따른 순위 즉시 변경
  3) 동점 정렬 규칙(사전순, REV 조회 시 역순)
  4) 기간 만료(EXPIRE)
"""
import re
import subprocess
import sys

CONTAINER = "valkey-case4"
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


def members(out):
    """배열 응답에서 따옴표로 감싼 문자열만 순서대로 추출합니다."""
    return re.findall(r'"([^"]*)"', out)


lb = "leaderboard:weekly"

print("=== 1. 점수 기록과 조회 ===")
out = cli("ZADD", lb, "120", "alice", "95", "bob", "150", "carol")
show(f"ZADD {lb} 120 alice 95 bob 150 carol", out)
check("멤버 3명 추가", out == "(integer) 3")

out = cli("ZINCRBY", lb, "100", "bob")
show(f"ZINCRBY {lb} 100 bob", out)
check("bob 점수가 195로 증가", out == '"195"')

out = cli("ZRANGE", lb, "0", "2", "REV", "WITHSCORES")
show(f"ZRANGE {lb} 0 2 REV WITHSCORES", out)
check("상위 3명이 bob(195), carol(150), alice(120) 순서",
      members(out) == ["bob", "195", "carol", "150", "alice", "120"])

out = cli("ZREVRANK", lb, "alice")
show(f"ZREVRANK {lb} alice", out)
check("alice는 0부터 센 순위 2 (3위)", out == "(integer) 2")

out = cli("ZSCORE", lb, "bob")
show(f"ZSCORE {lb} bob", out)
check("bob 점수 195", out == '"195"')

out = cli("ZREVRANK", lb, "nobody")
show(f"ZREVRANK {lb} nobody", out)
check("없는 멤버는 nil", out == "(nil)")

print("=== 2. 순위 즉시 변경 ===")
out = cli("ZINCRBY", lb, "100", "alice")
show(f"ZINCRBY {lb} 100 alice", out)
out = cli("ZREVRANK", lb, "alice")
show(f"ZREVRANK {lb} alice", out)
check("alice(220)가 1위(순위 0)로 상승", out == "(integer) 0")

print("=== 3. 동점 정렬 규칙 ===")
tie = "leaderboard:tie"
cli("ZADD", tie, "100", "b", "100", "a")
asc = members(cli("ZRANGE", tie, "0", "-1"))
rev = members(cli("ZRANGE", tie, "0", "-1", "REV"))
print(f"ZRANGE {tie} 0 -1      -> {asc}")
print(f"ZRANGE {tie} 0 -1 REV  -> {rev}\n")
check("동점은 사전순(a, b)", asc == ["a", "b"])
check("REV 조회 시 역순(b, a)", rev == ["b", "a"])

print("=== 4. 기간 만료 ===")
out = cli("EXPIRE", lb, "604800")
show(f"EXPIRE {lb} 604800", out)
check("EXPIRE 성공", out == "(integer) 1")
ttl = int(re.search(r"\d+", cli("TTL", lb)).group())
check("TTL이 7일(604,800초) 이내", 0 < ttl <= 604800)

print(f"결과: {sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
