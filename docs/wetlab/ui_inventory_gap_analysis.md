# UI 기능 인벤토리 + 누락 식별 갭 분석

> **작성일**: 2026-05-12  
> **작성자**: reviewer-uiux (U3 task #18)  
> **대상 브랜치**: `fix/f06-step05c-sequence-passing`  
> **스택**: React 19 + Vite 7 + TypeScript + Tailwind CSS v4 + Recharts + Mol*  
> **기준 커밋**: `595896a` (fix(step05c): F-06 config.sequence_map fallback)

---

## 요약 판정

| 판정 | 항목 수 |
|------|---------|
| ✅ PASS (노출 완료) | 10개 backend 라우터 중 7개 |
| ❌ MISSING (노출 없음) | 4개 신규 기능 (볼트 cross-val, archives 랭킹, cand03 변이체, stability) |
| ⚠️ PARTIAL (부분 노출) | 3개 (cluster, rcsb, pharmacology — SiloB에 컴포넌트 있으나 전용 훅 없음) |
| 🔲 N/A | static 파일 서빙 (직접 노출 불필요) |

---

## 1. Backend API 라우터 인벤토리 (현재 main.py 기준 10개)

### 1.1 `status` 라우터

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/status` | 현재 파이프라인 상태 (단일 run) |
| POST | `/api/status` | 상태 업데이트 수신 (emitter) |
| GET | `/api/health` | 서버 헬스체크 |
| GET | `/api/runs` | 아카이브된 run 목록 |
| GET | `/api/runs/{run_id}` | 특정 run 상세 |

### 1.2 `analysis` 라우터

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/analysis/convergence` | 수렴 데이터 (이터레이션별 ΔG) |
| GET | `/api/analysis/rank-stability` | 후보 랭크 안정성 |
| GET | `/api/analysis/gate-distribution` | QC 게이트 분포 |
| GET | `/api/analysis/candidate-evidence` | 후보 증거 수집 |
| GET | `/api/analysis/cross-run-variance` | 런 간 분산 |
| GET | `/api/analysis/summary` | 분석 요약 |
| GET | `/api/analysis/sar-pssm` | SAR/PSSM 분석 |
| POST | `/api/analysis/refresh` | 분석 새로고침 |

### 1.3 `validation` 라우터

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/validation/criteria` | 검증 기준 목록 |
| GET | `/api/validation/results` | 검증 결과 조회 |
| POST | `/api/validation/run` | 검증 실행 |
| POST | `/api/validate/selected` | 선택된 후보 검증 |
| POST | `/api/validate/unified` | 통합 검증 |

### 1.4 `experiment` 라우터

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/experiment/config` | 실험 설정 조회 |
| GET | `/api/experiment/models` | 사용 가능 모델 목록 |
| GET | `/api/experiment/status` | 실험 실행 상태 |
| POST | `/api/experiment/run` | 실험 시작 |
| POST | `/api/experiment/stop` | 실험 중단 |
| GET | `/api/experiment/history` | 실험 이력 |

### 1.5 `admet` 라우터

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/admet/{sequence}` | 단일 시퀀스 ADMET 예측 |
| POST | `/api/admet/batch` | 배치 ADMET 예측 |
| POST | `/api/pharmacology/batch` | 배치 약리학 프로퍼티 |

### 1.6 `static` 라우터

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/structures/{rel_path}` | PDB 구조 파일 서빙 |
| GET | `/api/images/{rel_path}` | 시각화 이미지 서빙 |

### 1.7 `settings` 라우터

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/settings` | 파이프라인 설정 조회 |
| PUT | `/api/settings` | 파이프라인 설정 저장 |

### 1.8 `rcsb` 라우터

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/rcsb-search` | RCSB PDB 유사도 검색 |

### 1.9 `cluster` 라우터

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/cluster/classify` | 후보 클러스터 분류 |

### 1.10 `selectivity` 라우터

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/selectivity/receptors` | 수용체 목록 (loaded 상태 포함) |
| POST | `/api/selectivity/upload` | 수용체 PDB 업로드 |
| GET | `/api/selectivity/structure/{receptor_name}` | 수용체 구조 조회 |
| POST | `/api/selectivity/run` | 선택성 분석 실행 |
| GET | `/api/selectivity/status/{job_id}` | 작업 상태 폴링 |
| GET | `/api/selectivity/results/{job_id}` | 작업 결과 조회 |
| GET | `/api/selectivity/jobs` | 전체 작업 목록 |

### 미등록 (신규 필요) 라우터

| 라우터 | 경로 | 데이터 파일 | 상태 |
|--------|------|------------|------|
| stability | `/api/stability/*` | `pipelines/silo_b/src/stability.py` | U5 진행 중 |
| boltz_cross | `/api/boltz_cross/*` | `runs_local/step05c_boltz_cross/partial_results.json` (현재 비어 있음) | 미구현 |
| archives | `/api/archives/*` | `runs_local/archives_boltz_eval/all_results.json` (1,615 레코드 완비) | 미구현 |
| cand03_variants | `/api/cand03_variants/*` | `runs_local/cand03_variants/cand03_variants.json` (20종 완비) | 미구현 |

---

## 2. Frontend 페이지 인벤토리 (6 pages)

### 2.1 페이지 라우트 구조 (`App.tsx`)

```
/ → redirect → /silo-b
/silo-b      → SiloBPage.tsx       (메인: PyRosetta Silo B)
/silo-a      → SiloAPage.tsx       (Silo A: 3-ARM NIM)
/combined    → CombinedPage.tsx    (교차 비교 대시보드)
/selectivity → SelectivityPage.tsx (GPCR 선택성 분석)
/settings    → SettingsPage.tsx    (파이프라인 설정)
/about       → AboutPage.tsx       (프로젝트 소개)
```

### 2.2 SiloBPage (`/silo-b`) — 메인 대시보드

사용 컴포넌트 (21개):

| 컴포넌트 | 기능 | API 의존 |
|---------|------|---------|
| `PipelineStatus` | 파이프라인 단계 상태 표시 | `usePipelineContext` → `/api/status` |
| `AgentMonitor` | 에이전트 활동 모니터 | `usePipelineContext` |
| `CandidateTable` | 후보 목록 (가상 스크롤) | `usePipelineContext` |
| `PharmacologyPanel` | 약리학 메트릭 카드 | `usePipelineContext` |
| `ValidationPanel` | 검증 결과 패널 | `useValidation` → `/api/validate/selected` |
| `QCGateChart` | QC 게이트 통과율 차트 | `usePipelineContext` |
| `ConvergenceGraph` | ΔG 수렴 그래프 | `usePipelineContext` |
| `RiskMatrix` | 리스크 매트릭스 | `usePipelineContext` |
| `VisualizationPanel` | 3D 구조 이미지 갤러리 | `/api/images/*` (static) |
| `MoleculeViewer` | Mol* 3D 인터랙티브 뷰어 | `/api/structures/*` (static) |
| `AgentFlowDiagram` | 에이전트 흐름 다이어그램 | (정적) |
| `SequenceLogo` | 시퀀스 로고 시각화 | `usePipelineContext` |
| `MutationAnalysis` | 변이 빈도 분석 | `usePipelineContext` |
| `PositionEnrichment` | 위치별 잔기 빈도 | `usePipelineContext` |
| `ExperimentControl` | 실험 시작/중단 컨트롤 | `useExperiment` → `/api/experiment/*` |
| `LoopTimeline` | 이터레이션 타임라인 | `usePipelineContext` |
| `DdGDistribution` | ΔG 분포 히스토그램 | `usePipelineContext` |
| `SARHeatmap` | SAR 히트맵 | `usePipelineContext` |
| `RCSBMatchPanel` | RCSB PDB 유사도 | 인라인 fetch → `/api/rcsb-search` |
| `RunComparisonPanel` | 런 간 비교 | `usePipelineContext` |
| `ClusterPanel` | 클러스터 시각화 | 인라인 fetch → `/api/cluster/classify` |
| `ADMETPanel` | ADMET 예측 패널 | `useAdmetBatch` → `/api/admet/batch` |

### 2.3 SiloAPage (`/silo-a`) — 3-ARM NIM 파이프라인

사용 컴포넌트:

| 컴포넌트 | 기능 |
|---------|------|
| `PipelineStatus` | Silo A 단계별 상태 |
| `AgentMonitor` | 에이전트 모니터 |
| `CandidateTable` | 후보 테이블 |
| `QCGateChart` | QC 게이트 |
| `ConvergenceGraph` | 수렴 그래프 |
| `ExperimentControl` | 실험 시작/중단 |

> 참고: SiloA는 주로 정적 폴백 데이터 사용 (파이프라인 미실행 상태). 실시간 데이터 연결 약함.

### 2.4 CombinedPage (`/combined`) — 교차 비교

- Recharts `ScatterChart`, `BarChart` (Silo A vs Silo B 후보 산포도/막대)
- `PipelineStatus`, `AgentMonitor` 임베드
- **주의**: 현재 Silo A 데이터가 없으므로 SiloB 단일 데이터만 시각화됨

### 2.5 SelectivityPage (`/selectivity`) — 선택성 분석

| 컴포넌트 | 기능 | API |
|---------|------|-----|
| `ReceptorUpload` | PDB 업로드 | `/api/selectivity/upload` |
| `SelectivityTable` | 결과 테이블 | `/api/selectivity/results/*` |
| `SelectivityChart` | Recharts 선택성 차트 | `/api/selectivity/results/*` |

### 2.6 SettingsPage (`/settings`)

- 파이프라인 설정 폼 (실행 전략, 이터레이션 수, 모델 선택 등)
- API: `/api/settings` GET/PUT

### 2.7 AboutPage (`/about`)

- 프로젝트 소개 정적 페이지
- ADMET, RCSB 검색 결과 일부 표시 가능 (분석 확인 필요)

---

## 3. Backend ↔ Frontend 매핑 매트릭스

| Backend 라우터 | 주요 엔드포인트 | Frontend 연결 지점 | 연결 Hook | 상태 |
|---------------|--------------|-------------------|----------|------|
| `status` | `/api/status`, `/api/runs` | SiloBPage, SiloAPage, CombinedPage (헤더 포함) | `usePipelineStatus` | ✅ **완료** |
| `analysis` | `/api/analysis/*` | SiloBPage (ConvergenceGraph, DdGDistribution, SARHeatmap, RunComparisonPanel) | `usePipelineContext` (간접) | ⚠️ **부분** — 전용 hook 없음, 컨텍스트 통해 주입 |
| `validation` | `/api/validate/selected`, `/api/validation/results` | SiloBPage (ValidationPanel) | `useValidation` | ⚠️ **부분** — `/api/validation/run`, `/api/validate/unified` 미사용 |
| `experiment` | `/api/experiment/*` | SiloBPage, SiloAPage (ExperimentControl) | `useExperiment` | ✅ **완료** |
| `admet` | `/api/admet/batch` | SiloBPage (ADMETPanel) | `useAdmetBatch` | ⚠️ **부분** — `/api/pharmacology/batch` 미사용 |
| `static` | `/api/structures/*`, `/api/images/*` | SiloBPage (VisualizationPanel, MoleculeViewer) | 직접 URL | ✅ **완료** |
| `settings` | `/api/settings` | SettingsPage | 인라인 fetch | ✅ **완료** |
| `rcsb` | `/api/rcsb-search` | SiloBPage (RCSBMatchPanel) | 인라인 fetch | ✅ **완료** |
| `cluster` | `/api/cluster/classify` | SiloBPage (ClusterPanel) | 인라인 fetch | ✅ **완료** |
| `selectivity` | `/api/selectivity/*` | SelectivityPage | `useSelectivity` | ✅ **완료** |
| **(신규)** `stability` | `/api/stability/*` | ❌ 없음 | ❌ 없음 | **❌ MISSING** (U5 진행 중) |
| **(신규)** `boltz_cross` | `/api/boltz_cross/*` | ❌ 없음 | ❌ 없음 | **❌ MISSING** (데이터 미완) |
| **(신규)** `archives` | `/api/archives/*` | ❌ 없음 | ❌ 없음 | **❌ MISSING** (데이터 완비) |
| **(신규)** `cand03_variants` | `/api/cand03_variants/*` | ❌ 없음 | ❌ 없음 | **❌ MISSING** (데이터 완비) |

---

## 4. 신규 기능 UI 노출 평가

### 4.1 step05c Boltz cross-validation 결과

**데이터 상태**: `runs_local/step05c_boltz_cross/partial_results.json` — **현재 비어 있음 `{}`**

```json
// partial_results.json 현재 내용
{}
```

- 완전한 iptm_matrix.json 생성 필요 (F-06 fix 머지 후 재실행 필요)
- **UI 통합 위치 (권장)**: SelectivityPage에 **"Boltz Cross-Val" 탭** 추가
  - 열: receptor, sequence, iptm, ptm, confidence
  - 현재 SelectivityPage가 단일 run job 중심 → cross-val 결과는 별도 섹션으로 추가
- **데이터 완전성 검증 필요**: 백엔드 라우터 없음, partial_results 비어 있음

### 4.2 Archives 1,615 페어 평가 결과

**데이터 상태**: `runs_local/archives_boltz_eval/all_results.json` — **완비 (1,615 레코드)**

```
스키마: sequence, receptor, iptm, ptm, confidence, complex_plddt, complex_iplddt,
        pair_chains_iptm, status, elapsed_sec, gpu_id, timestamp
수용체: SSTR1/2/3/4/5 × 323 후보 = 1,615 페어
SSTR2 Top-3:
  1위: AVCKNRFWKTFTSC  iptm=0.9757
  2위: AGCKNFFWKTFNSR  iptm=0.9751
  3위: PQCKNFFWKTFTSC  iptm=0.9708
T3 기준(iptm≥0.92): SSTR2에서 상위 ~6개, T2 기준(iptm≥0.85): ~38개
```

- **UI 통합 위치 (권장)**: `/selectivity` 또는 새 `/archives` 페이지
  - 옵션 A (권장): SelectivityPage에 **"Archive Eval" 탭** 추가
  - 옵션 B: 독립 페이지 `/archives` — NavItem 추가 필요
- **필요 컴포넌트**: 
  - `ArchivesRankingTable` — SSTR2 선택성 점수 컬럼 포함 정렬 가능 테이블
  - `ReceptorScatterMatrix` — 5개 SSTR 대비 산포도 (Recharts)
  - 컬러 코딩: iptm≥0.92 → `text-green-400`, 0.85~0.92 → `text-amber-400`, <0.85 → `text-slate-400`

### 4.3 cand03 변이체 20종 (Chemistry T4)

**데이터 상태**: `runs_local/cand03_variants/cand03_variants.json` — **완비 (20종)**

```
스키마 (variants[]):
  id, sequence, modification, rationale, synthesizability, spps_compatibility,
  blosum62_score, gravy, gravy_delta, net_charge_ph74, cluster_d_gravy,
  cluster_d_charge, dota_sites, expected_iptm_change, selectivity_hypothesis,
  chemical_risk, priority
```

- **UI 통합 위치 (권장)**: SiloBPage 또는 새 `/candidates` 서브 페이지
  - 옵션 A: SiloBPage CandidateTable에 "Variants" 필터 탭 추가
  - 옵션 B (권장): SelectivityPage에 **"cand03 Variants" 서브 탭** 추가
    - SAR rationale 팝업 (Tooltip on hover)
    - DOTA site 표시 (방사성 라벨링 위치)
    - Priority 배지 (high/medium/low)
    - synthesizability 스코어 표시

### 4.4 Wetlab 6도메인 보고서 (3,033 LOC)

**데이터 상태**: `docs/wetlab/*.md` 8개 파일

```
파일 목록:
  cand03_binding_assay_design.md  ← in-vitro 발주 권장 후보 목록 포함
  cand_stability_analysis.md
  halflife_methodology.md
  META_stability_halflife_integrated.md
  protease_mechanisms_sst14.md
  sst_analog_stability_literature.md
  stability_modifications_review.md
  stability_predictor_tools.md
```

- 정적 문서는 UI 직접 노출 불필요 (개발자용)
- **단, in-vitro 발주 권장 후보 표는 UI에 필요**
  - `cand03_binding_assay_design.md`의 발주 후보 추출 → AboutPage 또는 별도 섹션

### 4.5 Stability 평가 결과 (U1 진행 중)

**데이터 상태**: `pipelines/silo_b/src/stability.py` 구현됨, `batch_8_candidates.json` 미생성 (U1 완료 후 생성)

- **UI 통합 위치 (권장)**: SelectivityPage에 **"Stability" 탭** 추가
  - Biopython + peptides.py 결과 시각화:
    - Instability Index (< 40 = stable) → 색상 배지
    - GRAVY score → 수평 바 차트
    - Net charge at pH 7.4 → 수치
    - Half-life estimate → 표 컬럼
  - `useStability` hook 신규 생성 필요 (U5 의존)

---

## 5. UI 누락 기능 우선순위 매트릭스

### Critical (즉시 추가 필요)

| 기능 | 데이터 준비 | Backend | Frontend | 담당 |
|------|------------|---------|---------|------|
| Archives Top-K SSTR2 선택성 랭킹 | ✅ 완비 | ❌ 없음 | ❌ 없음 | U5 + engineer-backend |
| cand03 변이체 20종 카탈로그 | ✅ 완비 | ❌ 없음 | ❌ 없음 | U5 + engineer-backend |
| Stability 예측 결과 패널 | ⏳ U1 완료 후 | ❌ (U5) | ❌ 없음 | U5 완료 후 |

### Medium

| 기능 | 데이터 준비 | Backend | Frontend | 담당 |
|------|------------|---------|---------|------|
| Boltz cross-val iptm 매트릭스 | ❌ partial 비어 있음 | ❌ 없음 | ❌ 없음 | F-06 재실행 필요 |
| in-vitro 발주 권장 후보 + 비용 | ✅ 문서 내 | N/A (정적) | ❌ 없음 | reviewer-uiux |
| pharmacology/batch 결과 시각화 | 기존 backend 있음 | ✅ 있음 | ❌ 없음 | 별도 작업 |

### Low

| 기능 | 데이터 준비 | 우선순위 이유 |
|------|------------|-------------|
| wetlab 보고서 markdown 렌더링 | ✅ | 개발자/연구자용, 일반 사용자 비필수 |
| `/api/validate/unified` 연동 | 기존 backend 있음 | ValidationPanel 개선 |
| experiment history 페이지 | 기존 backend 있음 | `useExperiment` 훅 확장 필요 |

---

## 6. 신규 페이지/탭 설계 권장안

### 6.1 SelectivityPage 탭 구조 재편 (권장)

현재 SelectivityPage는 단일 뷰. 탭 구조로 확장:

```
/selectivity
├── [Tab 1] Live Screening   ← 현재 기능 유지
│   ├── ReceptorUpload
│   ├── SelectivityTable
│   └── SelectivityChart
│
├── [Tab 2] Archive Eval     ← 신규 (4.2)
│   ├── ArchivesRankingTable (1,615 페어, 필터: SSTR 선택, Top-K 슬라이더)
│   └── ReceptorScatterMatrix (5 SSTR × N candidates)
│
├── [Tab 3] cand03 Variants  ← 신규 (4.3)
│   ├── VariantsTable (20종, SAR rationale hover)
│   └── PropertiesHeatmap (GRAVY, charge, priority)
│
└── [Tab 4] Stability        ← 신규 (4.5, U5 완료 후)
    ├── StabilityTable
    └── StabilityBarChart
```

탭 컴포넌트 구현 패턴 (기존 SiloBPage `useState` 방식 참고):

```tsx
// 기존 코드 패턴과 일관성 유지
const [activeTab, setActiveTab] = useState<
  'live' | 'archive' | 'variants' | 'stability'
>('live')
```

### 6.2 Archives 랭킹 테이블 컴포넌트 스펙

```tsx
// ArchivesRankingTable.tsx
interface ArchivesEntry {
  sequence: string
  receptor: string   // 'SSTR1' | 'SSTR2' | 'SSTR3' | 'SSTR4' | 'SSTR5'
  iptm: number
  ptm: number
  confidence: number
  tier: 'T3' | 'T2' | 'T1'  // ≥0.92 / ≥0.85 / <0.85
}

// 색상 코딩 (디자인 표준 준수)
// tier T3 → text-green-400  (iptm ≥ 0.92)
// tier T2 → text-amber-400  (0.85 ≤ iptm < 0.92)
// tier T1 → text-slate-400  (iptm < 0.85)
```

### 6.3 Boltz cross-val 결과 통합 (데이터 준비 후)

step05c `iptm_matrix.json` 생성 완료 후:

```
/selectivity → [Tab 5] Boltz Cross-Val (선택적 추가)
├── 후보 × 수용체 iptm 히트맵 (Recharts)
└── 교차 검증 요약 카드 (vs selectivity Tab 1 비교)
```

---

## 7. 색상 코딩 / 색맹 친화성 / 접근성

### 7.1 현재 색상 체계 적합성

| 색상 역할 | 현재 클래스 | WCAG 2.1 AA (4.5:1) | 색맹 친화성 |
|----------|------------|---------------------|------------|
| 성공/고 iptm | `text-green-400` on `bg-slate-900` | ✅ 통과 (~7:1) | ⚠️ 적녹색맹 주의 |
| 경고/중간 | `text-amber-400` on `bg-slate-900` | ✅ 통과 (~8:1) | ✅ 안전 |
| 위험/낮음 | `text-red-400` on `bg-slate-900` | ✅ 통과 (~5.5:1) | ⚠️ 적녹색맹 주의 |
| 정보 | `text-blue-400` on `bg-slate-900` | ✅ 통과 (~6:1) | ✅ 안전 |
| 비활성 | `text-slate-500` on `bg-slate-900` | ⚠️ 경계 (~3.5:1) | ✅ 안전 |

**권장**: iptm 등급 표시 시 색상 + 아이콘/텍스트 배지 병행 사용  
예: `T3 ✓` (그린 배지) vs `T2` (앰버 배지) — 색상만 의존 않도록

### 7.2 Archives/Variants 테이블 색맹 대응 방안

```tsx
// 색맹 친화적 tier 배지 (색상 + 문자 조합)
function TierBadge({ tier }: { tier: 'T3' | 'T2' | 'T1' }) {
  const styles = {
    T3: 'bg-green-500/20 text-green-300 border-green-500/30',
    T2: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    T1: 'bg-slate-700/30 text-slate-400 border-slate-600/30',
  }
  return (
    <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-semibold border ${styles[tier]}`}>
      {tier}
    </span>
  )
}
```

### 7.3 접근성 (WCAG 2.1 AA)

신규 탭 컴포넌트 적용 시 필수 체크리스트:

- [ ] `role="tablist"` / `role="tab"` / `role="tabpanel"` 시맨틱 구조
- [ ] `aria-selected`, `aria-controls`, `aria-labelledby` 속성
- [ ] 키보드 네비게이션: Left/Right 화살표로 탭 이동, Enter/Space로 선택
- [ ] 테이블 `th`에 `scope="col"` 속성
- [ ] 정렬 가능 컬럼에 `aria-sort="ascending|descending|none"` 표시
- [ ] 로딩 상태에 `aria-live="polite"` 영역 사용

---

## 8. 모바일 반응형 검토

### 8.1 현재 반응형 현황

| 페이지 | 모바일 (< 768px) | 태블릿 (768px~) | 데스크톱 (1440px+) |
|--------|----------------|---------------|-----------------|
| SiloBPage | ⚠️ 그리드 깨짐 가능 (다중 패널) | ✅ 적절 | ✅ 최적화 |
| SelectivityPage | ✅ 단순 레이아웃 | ✅ | ✅ |
| SettingsPage | ✅ | ✅ | ✅ |
| CombinedPage | ⚠️ 차트 overflow 가능 | ✅ | ✅ |

### 8.2 Mol* Viewer 모바일 대응

**현재 구현** (`MoleculeViewer.tsx`): `fullscreen` 상태 있음, 모달 기반.  
**모바일 제한사항**:
- Mol* 렌더링 자체는 canvas 기반으로 모바일 지원 가능
- 터치 인터랙션 (rotate/zoom) 기본 지원
- **문제**: 모달이 `fixed` 배치로 모바일 viewport 고려 필요

```tsx
// 현재 fullscreen 토글 — 모바일 최적화 권장
// dialogRef.current에 max-h-[100dvh] 추가 권장
className={cn(
  "fixed inset-0 z-50 bg-slate-950/80",
  fullscreen ? "p-0" : "p-4 md:p-8"  // 모바일: 패딩 없애기
)}
```

### 8.3 신규 Archives 테이블 모바일 권장

1,615 레코드 테이블은 모바일에서 가로 스크롤 불가피:
```tsx
// 권장: 모바일 카드 뷰 + 데스크톱 테이블 뷰 전환
<div className="hidden md:block">  {/* 데스크톱 테이블 */}
  <ArchivesTable ... />
</div>
<div className="md:hidden">        {/* 모바일 카드 */}
  <ArchivesCardList ... />
</div>
```

---

## 9. §검증 필요 항목

1. **boltz_cross 데이터 완전성**: `partial_results.json` 현재 비어 있음 → F-06 fix 머지 + 재실행 후 확인 필요 (engineer-backend)
2. **archives API 경로**: `runs_local/archives_boltz_eval/` 파일이 backend static 서빙 범위 밖 → 신규 라우터 또는 파일 이동 필요 (engineer-backend)
3. **Mol* PDB 로드 경로**: 신규 후보 PDB 파일은 `/api/structures/{rel_path}` 경로로 서빙 → `rel_path` 규칙 확인 필요
4. **React Router 새 route**: `/selectivity`에 탭 추가 vs `/archives` 신규 route 추가 시 `NavItem` 배열 수정 필요 (`App.tsx:54-61`)
5. **CombinedPage Silo A 데이터 공백**: 현재 Silo A 실행 이력 없어 Combined 차트가 SiloB 단독 표시됨 — 명시적 안내 메시지 추가 권장

---

## 10. 권장 작업 순서 (내일 우선순위)

```
1. [U5, engineer-backend]  archives API 라우터 구현
   → /api/archives/top-k?receptor=SSTR2&k=20
   → /api/archives/matrix (전체 1615 페어 필터링)

2. [U5, engineer-backend]  cand03_variants API 라우터 구현
   → /api/cand03_variants/list

3. [reviewer-uiux]         SelectivityPage 탭 구조 구현
   → Tab 2 (Archive Eval) + Tab 3 (cand03 Variants)
   → useArchives, useCand03Variants 훅 신규 작성

4. [U5 완료 후]            Tab 4 (Stability) 추가
   → /api/stability/* 의존

5. [F-06 재실행 후]        Tab 5 (Boltz Cross-Val) 추가
```

---

*reviewer-uiux 작성 — 2026-05-12 / U3 task #18*
