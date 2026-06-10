# Claude Code 실행 프롬프트 — A-07

## 사용 방법

이 프롬프트는 **견적 수집·비교 자료 정리 자동화**용이다.  
실제 구매·결재는 사용자(서호성/안기범)가 수행한다.  
인프라 점검 및 문서 자동화에만 Claude Code / engineer-infra 를 활용한다.

```
# Claude Code에서 실행 시
@docs/meet_log/2026-04-06_action_items/prompts/A-07_prompt.md
```

---

## 컨텍스트

- @CLAUDE.md
- @docs/meet_log/2026-04-06_action_items/A-07_GPU_infra_quote.md
- 회의록: `docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf` (§2.3, §2.4)

---

## 작업 정의

### 작업 1. 기존 인프라 점검 보고서 작성

**담당**: engineer-infra

사용자 로컬 및 외부망 서버의 현재 GPU 상태를 점검하고 결과를 
`A-07_GPU_infra_quote.md`의 "기존 H100 ×8 서버 VRAM 점검" 섹션에 반영한다.

**실행 명령 (사용자 환경에서 직접 실행)**:
```bash
# 사용자 로컬 (H100 NVL ×4)
nvidia-smi --query-gpu=index,name,memory.total,memory.free,memory.used \
  --format=csv,noheader,nounits
nvidia-smi topo -m

# 외부망 서버 접속 후 (사용자 제공 시)
nvidia-smi --query-gpu=index,name,memory.total,memory.free,memory.used \
  --format=csv,noheader,nounits
nvidia-smi topo -m
```

### 작업 2. 디퓨전 모델 PoC VRAM 측정 (A-06 연동)

**담당**: engineer-infra (측정 자동화) + AI팀 (A-06 PoC 실행)  
**선행 조건**: A-06 디퓨전 모델 도킹 PoC 실행

A-06 PoC 실행 중 아래 수치를 기록하여 본 문서 "비교 매트릭스"의 판단 기준 입력:
- 모델 로딩 시 peak VRAM (GB)
- 배치 추론 시 peak VRAM (GB)
- 단일 GPU 충분 여부 vs. multi-GPU 필요 여부 결론

### 작업 3. DGX H100 / B200 / 자체 빌드 비교 매트릭스 작성

**담당**: 사용자 (서호성/안기범) — 벤더 견적 수집  
**담당**: engineer-infra — 수집된 데이터를 매트릭스에 반영

벤더 견적 수집 후 `A-07_GPU_infra_quote.md` 비교 매트릭스의 `TBD` 항목을 채운다.

---

## 입력 (Input Spec)

| 입력 | 제공자 | 필수 여부 |
|------|--------|----------|
| 사용자 로컬 `nvidia-smi` 출력 | 자동 (engineer-infra 실행) | 필수 |
| 외부망 서버 접근 정보 (hostname/SSH key) | 사용자 제공 | 선택 (접근 가능 시) |
| A-06 PoC 결과 (peak VRAM 수치) | A-06 담당자 | 필수 (판단 기준) |
| 벤더 견적 (DGX H100, DGX B200, 자체 빌드) | 서호성 / 안기범 | 필수 (의사결정) |

---

## 출력 (Output Spec)

| 출력 | 파일 위치 | 형식 |
|------|-----------|------|
| 인프라 점검 보고 | `A-07_GPU_infra_quote.md` 갱신 | Markdown 표 |
| 견적 비교 매트릭스 (완성) | `A-07_GPU_infra_quote.md` 갱신 | Markdown 표 |
| 추가 구매 필요성 결론 | `A-07_GPU_infra_quote.md` 말미 추가 | 한국어 서술 |

---

## 검증 기준 (Acceptance Criteria)

- [ ] 사용자 로컬 H100 NVL ×4 점검 결과 기록됨
- [ ] 외부망 H100 ×8 NVLink topology 확인 결과 기록됨 (접근 가능 시)
- [ ] A-06 PoC peak VRAM 수치 기록됨
- [ ] 최소 **2개 벤더** 견적 입력란 채워짐 (TBD → 실수치)
- [ ] "기존 H100 ×8 활용 가능 여부" 결론이 명시됨
- [ ] 추가 구매 필요 여부 의사결정 결론이 명시됨

---

## 추천 위임 경로

```
engineer-infra
├── 인프라 점검 (nvidia-smi, NVLink topology)
├── VRAM 측정 스크립트 작성/실행
└── 비교 매트릭스 Markdown 갱신

사용자 (서호성 / 안기범)
└── 벤더 견적 수집 (외부 액션, 자동화 불가)
```

---

## 에러 처리

| 에러 상황 | 처리 방법 |
|-----------|----------|
| 외부망 서버 접근 불가 | 사용자에게 `nvidia-smi` 출력 데이터 직접 요청; 해당 셀은 "사용자 제공 필요" 표기 |
| A-06 미완료 | VRAM 란 "A-06 완료 후 기입" 표기; 판단 보류 |
| 벤더 견적 미수집 | TBD 유지; 5월 회의 전 업데이트 요청 알림 |
| GPU 점유 상태 (테스트 불가) | `nvidia-smi` 스냅샷만 기록; 실측은 여유 시간대 재시도 |

---

## 참고 자료

- [NVIDIA DGX H100 Product Page](https://www.nvidia.com/en-us/data-center/dgx-h100/)
- [NVIDIA DGX B200 Product Page](https://www.nvidia.com/en-us/data-center/dgx-b200/)
- [DGX H100 System Architecture](https://resources.nvidia.com/en-us-dgx-systems/dgx-h100-datasheet)
- 사용자 로컬 H100 NVL spec: 96GB/GPU × 4 = 384GB (`infra_gpu_settings.md` 참조)
- 외부망 서버: H100 SXM 80GB × 8 = 640GB (회의록 §2.3)
