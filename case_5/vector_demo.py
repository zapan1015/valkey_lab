"""사례 5. 벡터 검색과 시맨틱 캐싱 검증 스크립트.

검증 항목
  1) Valkey-Search 모듈 로드, HNSW 벡터 인덱스 생성
  2) KNN 검색 결과가 독립 계산한 코사인 거리와 일치
  3) 임계값 기반 시맨틱 캐시 판정(적중/미스)
  4) 테넌트(TAG) 필터로 다른 사용자의 캐시가 검색되지 않음
"""
import math
import struct
import sys
import time

import valkey

sys.stdout.reconfigure(encoding="utf-8")
results = []
THRESHOLD = 0.1

r = valkey.Valkey(host="valkey", port=6379, decode_responses=False)


def check(name, ok):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}\n")


def vec(*values):
    """FLOAT32 little-endian 바이트열로 변환합니다."""
    return struct.pack(f"<{len(values)}f", *values)


def cosine_distance(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return 1 - dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def search(query_vector, tenant=None):
    """가장 가까운 항목 1개를 {key, score, answer} 로 반환합니다. 없으면 None."""
    base = f"(@tenant:{{{tenant}}})" if tenant else "*"
    res = r.execute_command(
        "FT.SEARCH", "qa_idx", f"{base}=>[KNN 1 @embedding $vec AS score]",
        "PARAMS", "2", "vec", query_vector,
        "RETURN", "2", "score", "answer",
    )
    if res[0] == 0:
        return None
    fields = {res[2][i].decode(): res[2][i + 1].decode() for i in range(0, len(res[2]), 2)}
    return {"key": res[1].decode(), "score": float(fields["score"]), "answer": fields["answer"]}


r.flushall()

print("=== 1. 모듈과 인덱스 ===")
modules = [m[1].decode() if isinstance(m, list) else str(m) for m in r.execute_command("MODULE", "LIST")]
print("로드된 모듈:", modules)
check("search 모듈 로드됨", "search" in modules)

print("> FT.CREATE qa_idx ON HASH PREFIX 1 qa: SCHEMA tenant TAG embedding VECTOR HNSW 6 ...")
print(r.execute_command(
    "FT.CREATE", "qa_idx", "ON", "HASH", "PREFIX", "1", "qa:", "SCHEMA",
    "tenant", "TAG",
    "embedding", "VECTOR", "HNSW", "6",
    "TYPE", "FLOAT32", "DIM", "4", "DISTANCE_METRIC", "COSINE",
).decode(), "\n")

v_card = (0.9, 0.1, 0.0, 0.1)
v_weather = (0.0, 0.1, 0.9, 0.2)
v_card_other = (0.88, 0.12, 0.02, 0.1)
r.hset("qa:1", mapping={"tenant": "userA", "question": "이번 달 카드 사용 내역을 요약해줘",
                        "answer": "A 사용자의 카드 사용 요약", "embedding": vec(*v_card)})
r.hset("qa:2", mapping={"tenant": "userA", "question": "내일 서울 날씨는?",
                        "answer": "내일 서울 날씨 안내", "embedding": vec(*v_weather)})
r.hset("qa:3", mapping={"tenant": "userB", "question": "이번 달 카드 사용 내역 알려줘",
                        "answer": "B 사용자의 카드 사용 요약", "embedding": vec(*v_card_other)})
time.sleep(1)  # 색인은 백그라운드 스레드에서 갱신됩니다.

print("=== 2. KNN 검색과 거리 검증 ===")
query = (0.85, 0.15, 0.05, 0.1)
hit = search(vec(*query), tenant="userA")
print("검색 결과:", hit)
expected = cosine_distance(v_card, query)
print(f"독립 계산한 코사인 거리: {expected:.12f}\n")
check("userA 범위에서 qa:1(카드 질문)이 선택됨", hit and hit["key"] == "qa:1")
check("서버 score가 독립 계산값과 일치(오차 1e-4 이내)",
      hit and abs(hit["score"] - expected) < 1e-4)

print("=== 3. 시맨틱 캐시 판정 (임계값 %.2f) ===" % THRESHOLD)
check("유사한 질문 -> 거리가 임계값 이하 -> 캐시 적중", hit["score"] <= THRESHOLD)

unrelated = (0.1, 0.9, 0.1, 0.9)
miss = search(vec(*unrelated), tenant="userA")
print("무관한 질문 검색 결과:", miss, "\n")
check("무관한 질문 -> 거리가 임계값 초과 -> 캐시 미스(LLM 호출 필요)", miss["score"] > THRESHOLD)

print("=== 4. 테넌트 분리 ===")
for tenant, expect_key in (("userA", "qa:1"), ("userB", "qa:3")):
    res = search(vec(*query), tenant=tenant)
    print(f"{tenant} 검색:", res)
    check(f"{tenant}는 자기 캐시({expect_key})만 검색", res["key"] == expect_key)

no_filter = search(vec(*query))
print("필터 없이 검색:", no_filter)
check("필터가 없으면 다른 테넌트 항목도 후보가 됨(필터 필수)", no_filter["key"] in ("qa:1", "qa:3"))

print(f"결과: {sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
