"""사례 1~8 전체 검증 실행기.

각 사례 폴더에서 docker compose 를 기동하고 test.py(사례 5는 vector_demo.py)를 실행한 뒤,
출력을 case_N/output.txt 에 저장하고 종료합니다. 모든 사례가 통과하면 종료 코드 0을 반환합니다.

사용법: python verify_all.py [사례번호 ...]
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.stdout.reconfigure(encoding="utf-8")


def run(cmd, cwd, **kw):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", **kw)


def verify(n):
    d = ROOT / f"case_{n}"
    up = run(["docker", "compose", "up", "-d", "--wait"], d)
    if up.returncode != 0:
        return False, f"[compose up 실패]\n{up.stdout}\n{up.stderr}"
    try:
        if n == 5:
            cmd = ["docker", "compose", "run", "--rm", "pyclient", "sh", "-c",
                   "pip install -q --disable-pip-version-check valkey && python vector_demo.py"]
        else:
            cmd = [sys.executable, "test.py"]
        t = run(cmd, d)
        out = t.stdout + (f"\n[stderr]\n{t.stderr}" if t.returncode and t.stderr else "")
        return t.returncode == 0, out
    finally:
        run(["docker", "compose", "down", "-v"], d)


if __name__ == "__main__":
    targets = [int(a) for a in sys.argv[1:]] or list(range(1, 9))
    summary = {}
    for n in targets:
        print(f"\n######## case_{n} ########")
        ok, out = verify(n)
        (ROOT / f"case_{n}" / "output.txt").write_text(out, encoding="utf-8")
        print(out)
        summary[n] = ok
    print("\n==== 요약 ====")
    for n, ok in summary.items():
        print(f"case_{n}: {'PASS' if ok else 'FAIL'}")
    sys.exit(0 if all(summary.values()) else 1)
