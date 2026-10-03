"""사례 6. 큐와 스트림 검증 스크립트.

검증 항목
  1) 컨슈머 그룹 생성, 이벤트 추가, 그룹 내 메시지 분배
  2) ACK 전 대기(PEL) 상태와 ACK 후 해소
  3) 워커 중단 시 XAUTOCLAIM으로 다른 워커가 재처리
  4) XTRIM으로 스트림 길이 관리
"""
import re
import subprocess
import sys

CONTAINER = "valkey-case6"
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


def first_id(out):
    return re.search(r'"(\d+-\d+)"', out).group(1)


def pending_count():
    return int(re.search(r"\(integer\) (\d+)", cli("XPENDING", "orders", "billing")).group(1))


print("=== 1. 그룹 생성과 이벤트 추가 ===")
out = cli("XGROUP", "CREATE", "orders", "billing", "$", "MKSTREAM")
show("XGROUP CREATE orders billing $ MKSTREAM", out)
check("그룹 생성 OK", out == "OK")

out1 = cli("XADD", "orders", "*", "order_id", "1001", "status", "paid")
out2 = cli("XADD", "orders", "*", "order_id", "1002", "status", "paid")
show("XADD orders * order_id 1001 status paid", out1)
show("XADD orders * order_id 1002 status paid", out2)
id1, id2 = out1.strip('"'), out2.strip('"')
check("메시지 ID가 '밀리초-순번' 형식",
      all(re.fullmatch(r"\d+-\d+", i) for i in (id1, id2)))
check("두 번째 ID가 첫 번째보다 큼", int(id2.split("-")[0]) >= int(id1.split("-")[0]))

print("=== 2. 워커 분배와 대기 상태 ===")
out = cli("XREADGROUP", "GROUP", "billing", "worker-1", "COUNT", "1", "STREAMS", "orders", ">")
show("XREADGROUP GROUP billing worker-1 COUNT 1 STREAMS orders >", out)
check("worker-1이 첫 번째 메시지를 받음", first_id(out) == id1 and '"1001"' in out)

out = cli("XREADGROUP", "GROUP", "billing", "worker-2", "COUNT", "1", "STREAMS", "orders", ">")
show("XREADGROUP GROUP billing worker-2 COUNT 1 STREAMS orders >", out)
check("worker-2는 중복 없이 두 번째 메시지를 받음", first_id(out) == id2 and '"1002"' in out)

out = cli("XPENDING", "orders", "billing")
show("XPENDING orders billing", out)
check("ACK 전 대기 건수 2", pending_count() == 2)

print("=== 3. ACK 처리 ===")
out = cli("XACK", "orders", "billing", id2)
show(f"XACK orders billing {id2}", out)
check("worker-2의 메시지 ACK 성공", out == "(integer) 1")
check("대기 건수 2 -> 1", pending_count() == 1)

print("=== 4. 워커 중단 후 재처리 (worker-1이 ACK 없이 중단했다고 가정) ===")
out = cli("XPENDING", "orders", "billing", "-", "+", "10")
show("XPENDING orders billing - + 10", out)
check("남은 대기 메시지의 소유자는 worker-1", id1 in out and "worker-1" in out)

out = cli("XAUTOCLAIM", "orders", "billing", "worker-2", "0", "0", "COUNT", "10")
show("XAUTOCLAIM orders billing worker-2 0 0 COUNT 10", out)
check("worker-2가 미처리 메시지를 인계받음", id1 in out and '"1001"' in out)

out = cli("XACK", "orders", "billing", id1)
show(f"XACK orders billing {id1}", out)
check("재처리 후 ACK 성공, 대기 건수 0", out == "(integer) 1" and pending_count() == 0)

print("=== 5. 스트림 길이 관리 ===")
show("XLEN orders", cli("XLEN", "orders"))
out = cli("XTRIM", "orders", "MAXLEN", "1")
show("XTRIM orders MAXLEN 1", out)
check("오래된 1건 삭제", out == "(integer) 1")
out = cli("XLEN", "orders")
show("XLEN orders", out)
check("스트림 길이 1", out == "(integer) 1")

print(f"결과: {sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
