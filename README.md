# Valkey Laboratory (`valkey_lab`)

[![Valkey Compatible](https://img.shields.io/badge/Valkey-9.1.2-red.svg)](https://valkey.io)
[![Docker Engine](https://img.shields.io/badge/Docker-Compose_v2-blue.svg)](https://www.docker.com/)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](LICENSE)

**Valkey Laboratory**는 오픈소스 인메모리 저장소 **Valkey**의 핵심 자료구조와 확장 모듈(Valkey-Search 등)을 활용한 **8가지 실무 활용 사례**의 Docker 기반 실습 및 자동화 검증 스위트를 제공합니다.

---

## 📌 8가지 주요 활용 사례

| 번호 | 사례 (Use Case) | 핵심 기능 & 자료구조 | 실습 및 검증 스크립트 |
| :--- | :--- | :--- | :--- |
| **1** | **캐싱 (Caching)** | `SET ... EX`, `maxmemory`, LRU 제거 정책 (`INFO stats`) | [`case_1/test.py`](case_1/test.py) |
| **2** | **세션 저장소 (Session Store)** | Hash (`HSET`, `HGETALL`), `EXPIRE`, `TTL` | [`case_2/test.py`](case_2/test.py) |
| **3** | **레이트 리미팅 (Rate Limiting)** | 고정 윈도우(Lua `INCR`+`EXPIRE`) & 슬라이딩 윈도우(`Sorted Set`) | [`case_3/test.py`](case_3/test.py) |
| **4** | **실시간 리더보드 (Leaderboard)** | Sorted Set (`ZADD`, `ZINCRBY`, `ZRANGE ... REV`, `ZREVRANK`) | [`case_4/test.py`](case_4/test.py) |
| **5** | **벡터 검색 & 시맨틱 캐싱** | Valkey-Search 모듈 (`FT.CREATE`, `FT.SEARCH` HNSW KNN) | [`case_5/vector_demo.py`](case_5/vector_demo.py) |
| **6** | **큐와 스트림 (Queue & Streams)** | Stream & Consumer Group (`XGROUP`, `XREADGROUP`, `XPENDING`, `XACK`) | [`case_6/test.py`](case_6/test.py) |
| **7** | **Pub/Sub** | `SUBSCRIBE`, `PUBLISH` (실시간 메시지 수신 및 유실 특성 검증) | [`case_7/test.py`](case_7/test.py) |
| **8** | **분산 락 (Distributed Lock)** | `SET ... NX PX` 락 획득, 원자적 Lua 스크립트 해제, `PTTL` 만료 | [`case_8/test.py`](case_8/test.py) |

---

## 🚀 사전 준비 (Prerequisites)

- **Docker Desktop** 또는 **Docker Engine** (Compose v2 지원)
- **Python 3.10** 이상
- *(선택 사항)* [direnv](https://direnv.net/) (환경변수 자동 로드용)

---

## 🛠️ 빠른 시작 (Quick Start)

### 1. 전체 사례 일괄 자동 검증
모든 사례(`case_1` ~ `case_8`)의 Docker 환경을 순차적으로 띄우고 자동 검증 스크립트를 수행합니다.

```bash
# repository clone
git clone https://github.com/zapan1015/valkey_lab.git
cd valkey_lab

# 전체 8가지 사례 자동 실행 검증
python verify_all.py
```

### 2. 개별 사례 실행 및 검증
특정 사례 디렉토리로 이동하여 독립적으로 실행할 수 있습니다.

```bash
cd case_1

# Valkey 컨테이너 구동
docker compose up -d --wait

# 직접 CLI 접속 실습
docker exec -it valkey-case1 valkey-cli

# 자동 검증 스크립트 실행
python test.py

# 환경 종료
docker compose down -v
```

> **Note (사례 5 벡터 검색)**: 사례 5의 경우 `docker compose run --rm pyclient sh -c "pip install -q valkey && python vector_demo.py"` 명령으로 수행할 수 있습니다.

---

## 📁 프로젝트 구조 (Directory Structure)

```text
valkey_lab/
├── Docs/
│   └── valkey_usecases_chapter.md   # Valkey 8가지 사례 상세 가이드 및 검증 보고서
├── case_1/                          # 사례 1: 캐싱
│   ├── compose.yaml
│   ├── test.py
│   └── README.md
├── ...
├── case_8/                          # 사례 8: 분산 락
│   ├── compose.yaml
│   ├── test.py
│   └── README.md
├── .env.example                     # 환경변수 템플릿
├── .envrc                           # direnv 환경 자동 로드 설정
├── .gitignore                       # 보안 및 시스템 파일 커밋 방지
├── verify_all.py                    # 전체 사례 일괄 검증 실행기
├── LICENSE                          # BSD 3-Clause License
└── README.md                        # 프로젝트 메인 안내서
```

---

## 🔒 보안 및 환경 설정 (Security & Environment)

- `.env` 및 `Docs/valkey_production_notes.md` 등 민감 정보 및 비공개 노트는 `.gitignore`에 의해 커밋에서 제외됩니다.
- 환경변수 추가 시 `.env.example` 템플릿을 참고하여 작성합니다.

---

## 📄 라이선스 (License)

이 프로젝트는 [BSD 3-Clause License](LICENSE)에 따라 자유롭게 이용 및 수정할 수 있습니다.
