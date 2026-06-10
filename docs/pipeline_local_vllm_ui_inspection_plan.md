# pipeline_local · vLLM · UI 점검 계획서

**목적**: 로컬 파이프라인(`pipeline_local`)과 LLM 백엔드(vLLM/Ollama), 모니터링 UI(프론트 + FastAPI) 간 **설정·경로·헬스체크 정합성**을 검증하고, 발견 항목을 추적한다.

**범위**: `SST14-M_scr/pipeline_local/`, `AG_src/llm/`, `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/frontend/` (백엔드 프록시 기준), 환경 변수 `PIPELINE_*`, `OLLAMA_HOST`.

**비범위**: 논문/실험 과학적 결론, GPU 드라이버 하위 튜닝(별도 인프라 문서 참고).

---

## 우선순위 정의

| 우선순위 | 라벨 | 기준 |
|----------|------|------|
| **P0** | 차단 | 잘못된 LLM 헬스 판정, 아카이브 미표시, 실행기가 잘못된 서버를 검사함 |
| **P1** | 기능 완성 | API/CLI가 provider를 일관 반영, 최소 자동 테스트, vLLM 스모크 |
| **P2** | UX·운영 | Settings/라벨, mockData 구분, 문서·런북 정리 |

---

## P0 — 정합성 (차단 수준)

### P0-1. `run_pipeline_local.py` 사전 점검과 `llm.provider` 일치

**배경**: 설정이 `vllm`인데도 Ollama `/api/tags`만 검사하면, `base_url`이 vLLM 포트(예: `8001`)일 때 **잘못된 엔드포인트**를 두드리거나, 실패를 **Ollama 미설치**로 오해하게 된다.

| # | 점검 항목 | 방법 | 기대 결과 | 불합격 시 증상 |
|---|-----------|------|-----------|----------------|
| P0-1a | YAML `llm.provider: vllm`일 때 Ollama 호출 여부 | 코드 리뷰 또는 로그/패킷 캡처 | **Ollama `/api/tags` 호출 없음** (또는 명시적 no-op) | vLLM 포트에 `/api/tags` 요청 |
| P0-1b | `llm.provider: ollama`일 때 기존 동작 | `base_url`을 Ollama 호스트로 파싱해 태그 조회 | 모델 존재 시 OK | 회귀 |
| P0-1c | 배너/stdout의 LLM 한 줄 | 실행 직후 콘솔 | **실제 provider 이름 + 엔드포인트** (vLLM이면 base URL) | 항상 "Ollama"만 표시 |
| P0-1d | vLLM 헬스 (구현 시) | 선택: `GET {base_url}/v1/models` 또는 최소 `chat` 1토큰 | HTTP 200, 모델 목록에 YAML `model`과 호환되는 이름 | 타임아웃/404 시 경고 문구가 Ollama 안내로만 끝남 |

**완료 조건 (Acceptance)**:

- [ ] `provider: vllm` 실행 시 사전 점검이 **vLLM 호환 검사**를 수행하거나, 검사를 건너뛰고 문서화된 수동 확인만 안내한다(둘 중 하나는 필수).
- [ ] `provider: ollama`일 때 기존 `_check_ollama` 경로가 깨지지 않는다.

**관련 파일**: `pipeline_local/run_pipeline_local.py`, `pipeline_local/config/pipeline_config_local.yaml`

---

### P0-2. 아카이브 디렉터리: `PIPELINE_ARCHIVE_DIR` vs PyRosetta 런

**배경**: `pipeline_local/backend/state.py` 기본 `ARCHIVE_DIR`은 `runs_local/archives`. `ai4sci-kaeri`의 `status_emitter` 기본은 `runs/pyrosetta_flow/archives`일 수 있어, **같은 UI라도 백엔드 바이너리에 따라 과거 런이 안 보일 수 있다.**

| # | 점검 항목 | 방법 | 기대 결과 |
|---|-----------|------|-----------|
| P0-2a | 현재 백엔드 프로세스의 실제 `ARCHIVE_DIR` | 실행 중인 uvicorn 환경에서 `echo $PIPELINE_ARCHIVE_DIR` 또는 로그 | 의도한 경로 |
| P0-2b | `GET /api/runs` 응답에 기대 run_id 포함 | 브라우저 또는 `curl` | PyRosetta 전용 런이 목록에 있음 |
| P0-2c | `GET /api/runs/{run_id}` | 아카이브 JSON 로드 | 200 + 대시보드 필드 |
| P0-2d | 운영 규약 문서화 | 이 문서 + README 한 줄 | 신규 런은 **한 디렉터리로 통일** 또는 **심링크/복사 규칙** 명시 |

**완료 조건**:

- [ ] 단일 “정답” 아카이브 경로가 팀 합의로 정해지고, 로컬 실행 커맨드에 반영된다.
- [ ] 프론트에서 과거 런을 열었을 때 **404가 아니다** (해당 JSON이 존재하는 경우).

**관련 파일**: `pipeline_local/backend/state.py`, `pipeline_local/backend/routers/status.py`, `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/status_emitter.py`

---

## P1 — 기능 완성

### P1-1. `GET /api/experiment/models` 및 Settings와 LLM 설정 일치

**배경**: UI/실험 API가 Ollama 전용이면, vLLM 전환 후에도 **모델 목록·에러 메시지**가 사용자를 잘못 유도한다.

| # | 점검 항목 | 방법 | 기대 결과 |
|---|-----------|------|-----------|
| P1-1a | `GET /api/experiment/models` | vLLM 사용 시 | `v1/models` 기반 목록 또는 명시적 `"provider": "vllm"` + 폴백 메시지 |
| P1-1b | Settings 스키마 | `GET/PUT /api/settings` | `ollama_host`만이 아니라 **base_url / provider** 확장 여부 합의 |
| P1-1c | 실험 실행 서브프로세스 | `POST /api/experiment/run` 후 CLI 인자 | `pipeline_config`와 모순 없이 전달 |

**완료 조건**:

- [ ] vLLM 모드에서 UI가 “Ollama만 설치하세요”로 단정하지 않는다.

**관련 파일**: `pipeline_local/backend/routers/experiment.py`, `pipeline_local/backend/routers/settings.py`, `pipeline_local/backend/state.py`

---

### P1-2. `AG_src` LLM provider — vLLM 스모크

| # | 점검 항목 | 방법 | 기대 결과 |
|---|-----------|------|-----------|
| P1-2a | 인스턴스 생성 | `create_provider` + 실제 YAML | `VLLMProvider` |
| P1-2b | 평문 생성 | `generate("ping")` | 비어 있지 않은 문자열 |
| P1-2c | JSON 모드 | `generate_json` (Planner/Critic이 쓰는 경로와 동일 옵션) | dict 파싱 성공 또는 문서화된 폴백 |
| P1-2d | 모델명 | vLLM 서버 `--served-model-name` | YAML `llm.model`과 일치 |

**완료 조건**:

- [ ] 위 스모크가 **한 스크립트 또는 pytest**로 재실행 가능하다.

**관련 파일**: `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/AG_src/llm/provider.py`

---

### P1-3. `pipeline_local` 최소 자동 테스트

| # | 점검 항목 | 내용 |
|---|-----------|------|
| P1-3a | 설정 로드 | `pipeline_config_local.yaml` 파싱, 필수 키 존재 |
| P1-3b | `create_provider` | provider별 기대 타입 |
| P1-3c | (선택) `dual_silo` CLI 병합 | `--dual` 시 `enabled: true` 반영 |

**완료 조건**:

- [ ] CI 또는 로컬 `pytest` 한 디렉터리에서 **초록** (외부 GPU/서버 없이 가능한 범위).

---

## P2 — UX·운영

### P2-1. 프론트 `mockData` vs 라이브

| # | 점검 항목 | 방법 | 기대 결과 |
|---|-----------|------|-----------|
| P2-1a | 백엔드 미연결 시 Silo B | `/api/status` 끊김 | 샘플 데이터 표시 여부가 **한눈에 구분** (배지/카피) |
| P2-1b | `pyrosettaOnly` 모드 | `run_id` 패턴 + step 필터 | Step06 중심 UI가 의도대로인지 확인 |

**관련 파일**: `frontend/src/pages/SiloBPage.tsx`, `frontend/src/hooks/usePipelineStatus.ts`

---

### P2-2. 폴링·부하

| # | 점검 항목 | 비고 |
|---|-----------|------|
| P2-2a | `usePipelineStatus` 2s + `useExperiment` 3s | 동시 폴링이 백엔드/브라우저에 무리 없는지 |
| P2-2b | (선택) 단일 엔드포인트 병합 | 주석에 이미 “향후 통합” 언급 |

---

### P2-3. CORS·포트

| # | 점검 항목 | 기대 |
|---|-----------|------|
| P2-3a | Vite dev 서버 포트 | `main.py` `allow_origins`와 일치 |
| P2-3b | 프로덕션 빌드 | 동일 출처 또는 프록시 규칙 |

---

## 실행 순서 (권장)

1. **환경 변수 고정**: `PIPELINE_ARCHIVE_DIR`, `PIPELINE_STATUS_FILE`, `API_PORT`를 점검 시트에 기록.
2. **P0-2**: 아카이브 경로부터 맞춘 뒤 UI에서 과거 런 로드 확인.
3. **P0-1 / P1-1**: CLI·API를 provider-aware로 맞춤.
4. **P1-2**: vLLM 서버 가동 후 스모크.
5. **P1-3**: 테스트 추가 후 회귀 방지.
6. **P2**: UX 라벨·폴링·CORS.

---

## 점검 기록표 (복사용)

| 날짜 | 담당 | P0-1 | P0-2 | P1-1 | P1-2 | P1-3 | P2 | 비고 |
|------|------|------|------|------|------|------|-----|------|
| | | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | |

---

## 부록: 참고 커맨드 (로컬)

아래는 **환경에 맞게 수정** 후 사용한다.

```bash
# 백엔드 헬스
curl -s http://127.0.0.1:8787/api/health

# 라이브 상태 (STATUS_FILE 필요)
curl -s http://127.0.0.1:8787/api/status | head

# 아카이브 목록
curl -s http://127.0.0.1:8787/api/runs

# vLLM OpenAI 호환 (예시)
curl -s http://127.0.0.1:8001/v1/models

# Ollama 태그 (Ollama 모드일 때만)
curl -s http://127.0.0.1:11435/api/tags
```

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| 1.0 | 2026-04-02 | 최초 작성 (P0–P2 점검 계획·완료 조건·관련 파일) |
| 1.1 | 2026-04-02 | 코드 반영: P0-1 `run_pipeline_local` vLLM `/v1/models` 점검·배너·`--llm-base-url`; P0-2 기본 `ARCHIVE_DIRS` 병합 (`runs/pyrosetta_flow/archives` + `runs_local/archives`); P1-1 `GET /api/experiment/models`·`get_config` provider 분기; `PUT /api/settings` 에 `llm_provider`·`llm_base_url`; `tests/pipeline_local/test_config_smoke.py` 추가 |

### 구현 요약 (v1.1)

- **`PIPELINE_ARCHIVE_DIR` 미설정 시**: 두 기본 경로 모두에서 `*_dashboard.json` 을 찾는다. 단일 경로만 쓰려면 환경 변수로 고정.
- **CLI**: `provider=vllm` 일 때 `--ollama-host` 는 `base_url` 을 덮어쓰지 않는다. vLLM URL 은 `--llm-base-url` 또는 YAML `llm.base_url`.
- **런타임 설정**: `runtime_settings` 의 `llm_model` / `llm_provider` / `llm_base_url` 기본은 `None` — `GET /api/experiment/config` 가 YAML 을 우선 표시한다.
