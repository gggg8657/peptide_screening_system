# Step 0 모듈 검증 — 통합 보고서

> **세션명**: `module-verification-2026-05-13`
> **작성**: team-lead orchestrator
> **일시**: 2026-05-13 오후
> **목적**: 11 모듈 (step01~08 + step03b + step05b + step05c) 정상 동작 여부 + UI 연동 분석 + 백본 신규 기능 제안

---

## 0. 한눈에 보기

5 task 병렬 검증 결과 **시스템 전반의 통합 부재 패턴** 확인:
- **모듈 자체는 대부분 정상 작동** (PyRosetta, FoldMason, ESMFold, Boltz, 환경 8/10 healthy)
- 그러나 **STATUS_FILE 갱신 부재 + save 함수 미호출 + schema 불일치 + 부호 충돌** 등 통합 결함 다수
- **CLI ad-hoc만 UI 미반영이 아니라, 정식 orchestrator 실행조차도 일부 데이터 저장 안 함**
- Critical 3건, High 12건, Medium 12건 식별

---

## 1. 5 task 산출물

| Task | 팀원 | 산출물 | LOC |
|------|------|--------|-----|
| **M1** | backend | `_workspace/M1_engineer-backend_step01-03b-verify-2026-05-13.md` | ~400 |
| **M2** | code | `_workspace/M2_reviewer-code_step04-05c-verify-2026-05-13.md` | ~400 |
| **M3** | infra | `_workspace/M3_engineer-infra_step06-08-env-verify-2026-05-13.md` | ~500 |
| **M4** | uiux | `_workspace/M4_reviewer-uiux_ui-integration-2026-05-13.md` | 1,384 |
| **M5** | pharma | `_workspace/M5_reviewer-pharma_module-spec-2026-05-13.md` | 504 |
| **본 통합 보고서** | team-lead | (자체) | ~600 |

**총 산출**: ~3,800 LOC

---

## 2. 결함 통합 매트릭스

### 🔴 Critical (3건) — 즉시 수정

| ID | 모듈 | 결함 | 영향 | 출처 |
|----|------|------|------|------|
| **C-M1-1** | step01_receptor | OpenFold3 키 불일치 (`mmcif` vs `output_pdb`) | OpenFold3 항상 실패 → data/ fallback만 동작 | M1 |
| **C-M1-2** | step02_backbone | 백본 0개 silent 전파 (n_generated=0 무방어) | Step03이 빈 list 받고 조용히 진행 | M1 |
| **C-M2-1** | step05b_selectivity | `save_selectivity_results` orchestrator 미호출 | **모든 정식 run의 05b_selectivity/ 디렉토리 비어있음** (검증: 0건) | M2 |

### 🟠 High (12건) — 1주 내 수정

| ID | 모듈/영역 | 결함 |
|----|----------|------|
| H-M1-1 | step01 | `analyze_binding_pocket()` 미호출, config 그대로 복사 |
| H-M1-2 | step03b | 변이체 수백 개 메모리에만, 결과 파일 미저장 |
| H-M2-1 | step04_qc | `apply_plddt_gate` 결과 미사용 (dead code) |
| H-M2-2 | step05_docking | DiffPepBuilder 비활성 함수 3개 잔존 |
| **H-M2-3** | step05b/c | **affinity = -10 × iPTM 임의 선형 스케일** → selectivity margin 신뢰도 ↓ |
| **H-M2-4** | step05c | `work_dir` 이터레이션 미격리 (`runs_local/step05c_boltz_cross` 고정) → checkpoint 오염 |
| **H-M3-1** | step06 | **`rosetta_ddg_max -1.0` 운영** (코드 기본 -5.0 보다 완화) |
| H-M3-2 | step08 vs U1.5 | 병렬 구현체, 미통합 (수치 동등성 검증 필요) |
| H-M3-3 | env | diffpepbuilder GPU 없음 (CPU-only PyTorch) |
| H-M3-4 | env | pepadmet 구 CUDA (1.13.1+cu117, sm_89 최적 없음) |
| **H-M5-P1** | step08 | D-AA 도입 후 Instability 재계산 (pepADMET 필요) |
| **H-M5-P2** | step05 | Boltz affinity_kcal ↔ Ki/Kd 상관 부재 |

### 🟡 Medium (12건)

(상세는 각 M1-M5 보고서 참조. 주요)
- M-M1-1: PyRosetta `pose_to_pdbstring` API 경로 불확실
- M-M1-3: `diffusion_steps` config → wrapper 전달 안 됨 (항상 T=50)
- M-M2-1: step05c `save_step05c_results` 미호출 (C-M2-1 동일 패턴)
- M-M2-2: step05b/c STATUS_FILE 미갱신
- **M-M5-P3**: compute_admet DLscore 100/100 포화 — 규칙 재정의 필요
- M-M5-P5: pLDDT↔iPTM 상관 데이터 수집

---

## 3. **🔴 시스템 전반 패턴 — 결함 군집**

### 3-1. STATUS_FILE 갱신 부재 (전체 step)
| 모듈 | 갱신 여부 |
|------|----------|
| step01~03b | ❌ M1 보고 |
| step05b/c | ❌ M2 보고 |
| step06~08 | ✅ orchestrator만 (CLI 직접 호출 시 ❌) M3 보고 |

→ **모든 step 내부에서 STATUS_FILE 갱신 함수 호출 없음**. orchestrator의 `_write_status()`만 큰 단계별 호출.

### 3-2. **STATUS_FILE 경로 불일치** (Critical)
| 경로 | 용도 | 누가 갱신 |
|------|------|----------|
| `/tmp/pipeline_local_status.json` | pipeline_local orchestrator | orchestrator만 |
| `/tmp/ag_pipeline_status.json` | AG_src (레거시) | (현재 미사용 추정) |

→ **UI 가 보는 곳과 다른 파일** 가능성. 두 파일 병존 + UI hooks(`usePipelineStatus`)가 어느 쪽을 polling 하는지 확인 필요 (현재 코드 기준 `/tmp/ag_pipeline_status.json`로 추정).

### 3-3. `save_*_results` 함수 미호출 패턴
| 모듈 | save 함수 | orchestrator 호출 |
|------|----------|-------------------|
| step03b_blosum | `save_mutants()` (있다면) | 미호출 (H-M1-2) |
| step05b_selectivity | `save_selectivity_results()` | **미호출** (C-M2-1) |
| step05c_boltz_cross | `save_step05c_results()` | **미호출** (M-M2-1) |

→ **save 함수 정의는 있지만 orchestrator에서 호출 안 함** = 정식 run에서 결과 디스크 미저장.

### 3-4. **schema/스케일/부호 불일치** (Critical 위험)
| 비교 | 충돌 |
|------|------|
| **selectivity_margin 부호** | step05b: 낮을수록 selective vs step05c: 높을수록 selective (P4) |
| **ad-hoc vs 정식 schema** | seq_id 식별자, Tier 분류, iPTM 추가 지표 모두 다름 (M2) |
| **affinity 공식** | -10 × iPTM 임의 선형 (H-M2-3) |

→ **UI 통합 시 부호 반대 해석 위험**. 모든 selectivity 보고서 일관성 검토 필요.

### 3-5. 신뢰도 표시 부재
- pharmacology_guards.is_heuristic_function() API 준비됨 (M5)
- **그러나 API 응답 JSON에 `confidence_grade: HEURISTIC` 자동 주입 미확인**
- Frontend `⚠️ in-silico 추정값` 배지 부재
- iPTM ≠ Ki (Spearman -0.3, 순위 일치 0/5)인데 UI에 경고 없으면 환각 위험

---

## 4. UI 통합 spec (M4 권장)

### 4-1. **Phase 1 (즉시, 30분)** — STATUS_FILE 일관성
- `scripts/run_with_status.sh` wrapper 신규
- `pipeline_local/scripts/status_updater.py` 신규
- 모든 CLI ad-hoc 도 STATUS_FILE 자동 갱신
- 경로 통일 (`/tmp/pipeline_local_status.json` 단일화)

### 4-2. **Phase 2 (1주)** — 실시간 SSE
- `GET /api/events` (FastAPI SSE)
- `watchfiles` 백엔드
- `useEventSource` React hook
- 파일 변경 → 즉시 push

### 4-3. **5탭 확장 (어제 U3 + M4 보강)**
| Tab | 데이터 | 의존 |
|-----|--------|------|
| **Live Screening** | 기존 | - |
| **Archive Eval** | 1,615 페어 (Top-K 슬라이더) | Phase 1 라우터 |
| **cand03 Variants** | 20종 + DOTA 사이트 hover | Phase 1 라우터 |
| **Stability** | 8 후보 매트릭스 + HeuristicBanner | API 이미 작동 ✅ |
| **Boltz Cross-Val** | iPTM 매트릭스 (placeholder) | F-06 재실행 후 |

### 4-4. 백본 신규 기능 12개 (P0/P1/P2)
| Priority | 기능 |
|---------|------|
| **P0** | 후보 비교 모달, Archives Top-K 슬라이더, CombinedPage 공백 안내 |
| **P1** | Modification 시뮬레이터, Mol* 통합 확장, SAR 드릴다운, 타임라인 간트, Candidate Diff |
| **P2** | 실시간 알림, Export PDF (합성 발주서), 임계값 슬라이더, 실험 이력 |

### 4-5. 접근성
- `text-slate-500 → 400` (대비율 AA 미달 해결)
- aria-tablist/tab/tabpanel + 키보드 네비
- 색맹 친화 TierBadge
- HEURISTIC 배너 위치 (GATE-F 준수)

---

## 5. 신뢰도 매트릭스 (M5)

### 5-1. 출력값 분류
| 등급 | 갯수 | 예시 | 의미 |
|------|------|------|------|
| **A 실측 기반** | 14 | MW, pI, GRAVY, SG-SG 거리, clash | 표준 lookup table 검증됨 |
| **B in-silico** | 14 | pLDDT, Instability Index, ddG, lDDT | 상대 순위 의미 있음 |
| **🔴 C 의심** | **9** | **Boltz iPTM, selectivity_margin, affinity_kcal, DLscore** | 검증 부족 / 본 환경 calibration 안 됨 |
| HEURISTIC 등록 | 5 | step08 predict_half_life 외 | disclaimer 준비 완료 |

### 5-2. 약리학 cross-check 검증
- **iPTM ≠ Ki**: Spearman ρ≈-0.3 → iPTM을 Ki proxy 사용 **금지**
- **HL 64.72 (var12)**: ranking score만, "임상 t½ 64h" 환각
- **ILCKKFFWKTFTSC**: 두 독립 모델 (step08 + Biopython) 일관 불안정 → modification 필수
- **cand03 G2I**: 목적 타당, 결합력 손상 낮음 (pharmacophore 외부)

### 5-3. 시스템 빈 칸 4 도메인
- PK (plasma t½, Vd, CLr, HSA Kd) — 모두 없음
- 독성 (LD50, hERG, 간독성) — 없음
- 면역원성 — 없음
- 방사성의약품 (¹⁷⁷Lu RCP, biodistribution) — 없음

---

## 6. 환경 health (M3)

| 상태 | 환경 | 비고 |
|------|------|------|
| ✅ HEALTHY (8) | bio-tools, boltz, rfdiffusion, esmfold, genmol, openfold3, proteinmpnn, vllm-server | 핵심 모두 정상 |
| ⚠️ GPU 없음 | diffpepbuilder | CPU-only PyTorch |
| ⚠️ 구 CUDA | pepadmet | 1.13.1+cu117, sm_89 최적 없음 |

**bio-tools 핵심**: pyrosetta ✅ biopython 1.79 ✅ peptides 0.5.0 ✅ pymol ✅ torch 2.10.0+cu128 ✅

---

## 7. 우선순위별 수정 권장

### 🔥 Phase 1 (오늘~내일, 즉시 수정)
1. **C-M2-1**: orchestrator 에 `save_selectivity_results` + `save_step05c_results` 호출 추가 (~10분)
2. **C-M1-1**: step01 OpenFold3 키 정정 (`output_pdb` → `mmcif`) (~10분)
3. **C-M1-2**: step02 백본 0개 silent fail 차단 (raise + STATUS) (~15분)
4. **Phase 1 STATUS wrapper**: `run_with_status.sh` + `status_updater.py` (~30분)
5. **state.py 확장**: `runs_local/` ARCHIVE_DIR 추가 1줄 (~5분)
6. **selectivity_margin 부호 통일** (P4, ~30분 + 어제 보고서 수정)

→ **총 ~2시간**, 시스템 통합 핵심 결함 해결

### 🚀 Phase 2 (1주)
- **H-M2-3**: affinity 공식 재정의 (단순 선형 X → empirical fit)
- **H-M2-4**: step05c work_dir 이터레이션 격리
- **H-M3-1**: rosetta_ddg_max 운영값 재검토
- **SSE endpoint**: GET /api/events + useEventSource
- **5탭 UI 구현**: M4 spec 적용
- **HEURISTIC API 응답 자동 부착**: confidence_grade JSON 키
- **HeuristicBanner** 컴포넌트 추가

### 📊 Phase 3 (2-3주)
- step08 → U1.5 통합 (수치 동등성 검증 후)
- 백본 신규 기능 P1 (Modification 시뮬레이터, SAR 드릴다운 등)
- pharmacology_guards 확장 (33 → 39 문서 갱신)
- 빈 칸 4 도메인 — wet lab 실험 plan

### 🔮 Phase 4 (장기)
- 백본 신규 기능 P2 (Export PDF, 실험 이력)
- PK / 독성 / 면역원성 / 방사성의약품 데이터 축적
- ML predictor 학습 (실측 데이터 100+ pair 후)

---

## 8. §검증 필요 항목 종합 (M1~M5)

총 **24건** 신규 §검증:

### M1 (4건)
- M1-V1: PyRosetta pose_to_pdbstring API 경로
- M1-V2: 백본 silent fail시 정확한 raise 패턴
- M1-V3: diffusion_steps wrapper 전달 검증
- M1-V4: ProteinMPNN logit 추출 가능성

### M2 (3건)
- M2-V1: H-3 affinity 선형 스케일 → empirical fit
- M2-V2: H-4 work_dir 격리 후 회귀 테스트
- M2-V3: ad-hoc → 정식 schema ETL 구현

### M3 (6건)
- M3-V1: gate_thresholds.yaml `rosetta_ddg_max -1.0` 운영 판정
- M3-V2: step08 → U1.5 수치 동등성
- M3-V3: STATUS_FILE 두 경로 통일 (pipeline_local vs ag_pipeline)
- M3-V4: pepadmet 구 CUDA sm_89 호환
- M3-V5: diffpepbuilder GPU 환경 도입
- M3-V6: SSE endpoint 부하 평가

### M4 (6건)
- M4-V1: watchfiles 환경 설치 + 의존성
- M4-V2: archives API 파일 경로 결정
- M4-V3: Recharts HeatmapChart 구현 방식
- M4-V4: PDF 내보내기 방식 (react-pdf vs html2canvas)
- M4-V5: SSE Nginx 설정
- M4-V6: 탭 키보드 네비 자동화 테스트

### M5 (5건, P1-P5는 어제 작성)
- M5-V1: pharmacology_guards 33 → 39 문서 갱신
- M5-V2: iPTM ↔ Ki 상관관계 in-vitro 실측
- M5-V3: HEURISTIC API 자동 주입 검증
- M5-V4: selectivity_margin 부호 통일 후 회귀
- M5-V5: DLscore 포화 규칙 재정의 (예: 50/50 분할 + bonus)

---

## 9. 결론

### 9-1. **시스템은 모듈 단위로 대부분 작동**
- step06~08 PASS (104s + 4.4s)
- 환경 8/10 HEALTHY
- 핵심 모듈 (PyRosetta, FoldMason, Boltz, ESMFold) 정상

### 9-2. **그러나 통합 결함이 시스템 전반**
- STATUS_FILE 갱신 부재 (모든 step 내부)
- save 함수 미호출 (step03b, 05b, 05c)
- schema/스케일/부호 불일치 (selectivity margin)
- 신뢰도 표시 부재 (HEURISTIC banner)

### 9-3. **"CLI ad-hoc UI 미반영"은 빙산의 일각**
- 정식 orchestrator 실행 조차도:
  - selectivity 결과 디스크 미저장
  - step별 progress STATUS_FILE 부재
  - 두 STATUS_FILE 경로 병존
- → **시스템 전반의 통합 layer 미흡**

### 9-4. **2시간 작업으로 핵심 6건 해결 가능** (Phase 1)
- C-M1-1, C-M1-2, C-M2-1 fix
- STATUS_FILE wrapper + 경로 통일
- state.py archive 확장
- selectivity margin 부호 통일

### 9-5. **신뢰도 분류는 약리학적으로 합리적**
- A 14 / B 14 / C 9 / HEURISTIC 5
- C 9개가 selectivity 핵심 지표라 UI 경고 의무
- 빈 칸 4 도메인 명시

---

## 10. 다음 사용자 결정 요청

| 결정 | 옵션 |
|------|------|
| **Phase 1 즉시 수정** | 진행 (~2시간) / 보류 |
| **Phase 2 SSE/UI 구현** | 다음 세션 / 별도 PR / 보류 |
| **selectivity_margin 부호** | step05c 기준 통일 (높을수록 selective) / step05b 기준 / 둘 다 명시 |
| **백본 신규 기능** | P0 즉시 / P1 단기 / 보류 |
| **§검증 24건** | 분기 회고 안건 / Action Item으로 등록 |
| **팀 shutdown** | 즉시 / 다음 작업 후 |

---

## 11. 산출물 인덱스

```
_workspace/
├── M1_engineer-backend_step01-03b-verify-2026-05-13.md  (~400 LOC)
├── M2_reviewer-code_step04-05c-verify-2026-05-13.md      (~400 LOC)
├── M3_engineer-infra_step06-08-env-verify-2026-05-13.md  (~500 LOC)
├── M4_reviewer-uiux_ui-integration-2026-05-13.md         (1,384 LOC)
├── M5_reviewer-pharma_module-spec-2026-05-13.md          (504 LOC)
└── release/
    └── module-verification-2026-05-13-integrated.md      (본 문서, ~600 LOC)
```

**총 산출**: ~3,800 LOC (5 모듈별 + 통합)

---

*Generated by team-lead orchestrator · 2026-05-13 오후*
*세션: module-verification-2026-05-13*
*5 task / 5 완료 / Critical 3 + High 12 + Medium 12 발견*
