"""사례 2. 세션 저장소 검증 스크립트.

검증 항목
  1) 해시로 세션 저장, 필드 단위 조회/수정
  2) EXPIRE 로 지정한 TTL과 활동 시 갱신(슬라이딩 만료)
  3) 유휴 세션의 자동 만료
  4) 로그아웃(DEL)
"""
import re
import subprocess
import sys
import time

CONTAINER = "valkey-case2"
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


key = "session:8f2a"

print("=== 1. 세션 생성과 조회 ===")
out = cli("HSET", key, "user_id", "42", "role", "user", "cart_id", "c-1001")
show(f"HSET {key} user_id 42 role user cart_id c-1001", out)
check("필드 3개 생성", out == "(integer) 3")

out = cli("EXPIRE", key, "1800")
show(f"EXPIRE {key} 1800", out)
check("EXPIRE 성공", out == "(integer) 1")

out = cli("HGETALL", key)
show(f"HGETALL {key}", out)
check("세 필드가 모두 조회됨", all(v in out for v in ('"42"', '"user"', '"c-1001"')))

out = cli("TTL", key)
show(f"TTL {key}", out)
check("TTL이 1795~1800초", 1795 <= num(out) <= 1800)

print("=== 2. 활동 시 만료 시간 갱신 ===")
time.sleep(2)
out = cli("TTL", key)
show(f"TTL {key} (2초 경과)", out)
check("2초 경과 후 TTL이 감소", num(out) <= 1798)

out = cli("EXPIRE", key, "1800")
show(f"EXPIRE {key} 1800", out)
out = cli("TTL", key)
show(f"TTL {key} (갱신 직후)", out)
check("갱신 후 TTL이 다시 1799 이상", num(out) >= 1799)

print("=== 3. 필드 단위 수정 ===")
out = cli("HSET", key, "role", "admin")
show(f"HSET {key} role admin", out)
check("기존 필드 수정은 0 반환", out == "(integer) 0")
out = cli("HGET", key, "role")
show(f"HGET {key} role", out)
check("role이 admin으로 변경", out == '"admin"')
check("수정 후에도 TTL 유지", num(cli("TTL", key)) > 0)

print("=== 4. 유휴 세션 자동 만료 ===")
idle = "session:idle"
cli("HSET", idle, "user_id", "7")
cli("EXPIRE", idle, "2")
time.sleep(3)
out = cli("EXISTS", idle)
show(f"EXISTS {idle} (3초 경과)", out)
check("TTL 2초 세션이 자동 삭제됨", out == "(integer) 0")

print("=== 5. 로그아웃 ===")
out = cli("DEL", key)
show(f"DEL {key}", out)
check("DEL은 1건 삭제", out == "(integer) 1")
out = cli("EXISTS", key)
show(f"EXISTS {key}", out)
check("삭제 후 세션 없음", out == "(integer) 0")

print(f"결과: {sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
