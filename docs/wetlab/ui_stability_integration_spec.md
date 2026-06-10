# UI Integration Spec — Stability Predictor (U5)

> 작성: 2026-05-12  
> 담당: engineer-backend (백엔드 API 완성), reviewer-uiux (프론트엔드 구현)  
> API 문서: `GET /api/stability/predict`, `POST /api/stability/batch`, `GET /api/stability/cand03`

---

## 1. 페이지 설계

### 옵션 A (권장): SelectivityPage에 Stability 탭 추가

기존 `/selectivity` 라우트에 Tab 구조 추가:
```
SelectivityPage
├── [Tab 1] Boltz-2 iPTM Matrix (기존)
└── [Tab 2] Stability Predictor  ← 신규 추가
```

장점:
- 후보 선택(Selectivity) → 안정성 확인(Stability) 워크플로우 자연스러움
- 별도 라우트 추가 불필요

### 옵션 B: 독립 `/stability` 페이지

```
/stability
├── SinglePredict    — 단일 서열 입력 + 즉시 평가
└── BatchMatrix      — 8 후보 매트릭스 시각화
```

장점: 기존 SelectivityPage 수정 최소화

**권장: 옵션 A** (팀 표준 Tab 패턴 재사용)

---

## 2. 후보 매트릭스 시각화

### 2.1 컴포넌트: StabilityMatrix

8 후보 × 6 컬럼 테이블:

| seq_id | MW (Da) | GRAVY | Instab. Index | HL score* | Protease sites | Nephrotox |
|--------|---------|-------|---------------|-----------|----------------|-----------|

API: `GET /api/stability/cand03`  
응답 `results[]` 배열을 행으로 렌더링.

### 2.2 컬럼 설명

| 컬럼 | API 필드 | 설명 |
|------|---------|------|
| MW (Da) | `biophysical.mw` | 분자량. 범위 표시 (1200-2000 Da 권장) |
| GRAVY | `biophysical.gravy` | Kyte-Doolittle mean. <0 = 친수성 |
| Instab. Index | `biophysical.instability_index` | >40 = 불안정 (Biopython Guruprasad 1990) |
| HL score* | `hl_score` | **HEURISTIC** ranking score. 임상 반감기 아님 |
| Protease sites | `protease_predictions` | Trypsin/Chymotrypsin/NEP 절단 취약 잔기 수 |
| Nephrotox | `nephrotox_risk` | Low/Moderate/High |

### 2.3 색상 코딩

```typescript
const STABILITY_COLORS = {
  instability: {
    stable:   "bg-green-100",   // instability_index < 40
    unstable: "bg-red-100",     // instability_index >= 40
    na:       "bg-gray-100",    // NaN (Biopython 없음)
  },
  gravy: {
    hydrophilic: "text-blue-600",   // gravy < 0
    hydrophobic: "text-orange-600", // gravy >= 0.5
  },
  nephrotox: {
    Low:      "bg-green-100 text-green-700",
    Moderate: "bg-yellow-100 text-yellow-700",
    High:     "bg-red-100 text-red-700",
    Unknown:  "bg-gray-100 text-gray-500",
  },
};
```

### 2.4 SST-14 baseline 비교 row

`SST14_ref` 행을 항상 첫 번째에 고정 + 회색 배경으로 baseline 구분:

```typescript
const isBaseline = (row: StabilityRow) => row.seq_id === "SST14_ref";
// → className={cn(row className, isBaseline && "bg-gray-50 font-medium border-b-2")}
```

---

## 3. Modification Before/After Diff 표시

### 3.1 NCAA 치환 경고 렌더링

`warnings[]` 배열에 NCAA 관련 경고 포함 시:

```tsx
{result.warnings.filter(w => w.includes("→")).map((w, i) => (
  <Badge key={i} variant="outline" className="text-xs text-orange-600 border-orange-300">
    {w}
  </Badge>
))}
```

### 3.2 D-Thr (var12_dThr) Before/After 표시

`var12_dThr` 행에 `ncaa_warnings` 존재 시 diff 표시:
- Before: `AICKNFFWKTFTSC` (T12 = L-Thr)
- After: `AICKNFFWKTFT[dT]C` (T12 = D-Thr)
- 효과: 장 프로테아제 내성 향상 예상 (HEURISTIC)

```tsx
const DiffBadge = ({ before, after }: { before: string; after: string }) => (
  <div className="text-xs flex gap-1 items-center">
    <span className="line-through text-gray-400">{before}</span>
    <span>→</span>
    <span className="font-medium text-blue-600">{after}</span>
  </div>
);
```

---

## 4. HEURISTIC 경고 표시

**필수 — HEURISTIC_FUNCTION_DISCLAIMERS 준수**

모든 HL score 표시 영역에:

```tsx
const HeuristicBanner = () => (
  <div className="flex items-start gap-2 rounded border border-yellow-300 bg-yellow-50 p-3 text-sm">
    <AlertTriangle className="h-4 w-4 text-yellow-600 flex-shrink-0 mt-0.5" />
    <div>
      <span className="font-medium text-yellow-800">HEURISTIC ranking score</span>
      <p className="text-yellow-700 mt-0.5">
        HL score는 후보 <em>상대 순위</em> 부여용 heuristic score입니다.
        임상 반감기 절대값이 아닙니다. in-vitro serum stability assay 미수행.
      </p>
    </div>
  </div>
);
```

위치: StabilityMatrix 상단 고정.

---

## 5. 단일 서열 입력 UI

### 5.1 SinglePredict 컴포넌트

```tsx
// API: GET /api/stability/predict?seq=<sequence>
const [seq, setSeq] = useState("");
const [result, setResult] = useState<StabilityResponse | null>(null);

const handlePredict = async () => {
  const res = await fetch(`/api/stability/predict?seq=${encodeURIComponent(seq)}`);
  if (!res.ok) throw new Error(await res.text());
  setResult(await res.json());
};
```

입력 필드:
- `<input type="text" placeholder="AGCKNFFWKTFTSC" />`
- NCAA 표기 허용 안내: "[dT], [Cha], [2Nal] 허용"
- 최대 50자 검증

---

## 6. 로딩 & 에러 상태

| 상태 | UI |
|------|-----|
| 로딩 중 | Skeleton rows (6컬럼, 8행) |
| 에러 | `ErrorBanner` + `/api/stability/cand03` 재시도 버튼 |
| Biopython 없음 | instability_index 컬럼에 "N/A" + tooltip "bio-tools conda env 필요" |
| peptides.py 없음 | boman 컬럼에 "N/A" + tooltip "pip install peptides" |

---

## 7. API 연동 타입 (TypeScript)

```typescript
export interface StabilityResponse {
  seq_id: string;
  sequence: string;
  canonical_sequence: string;
  biophysical: {
    mw: number;
    gravy: number;
    instability_index: number | null;
    pi: number | null;
  };
  aliphatic_index: number;
  boman: number | null;
  protease_predictions: {
    trypsin: number[];
    chymotrypsin: number[];
    nep: number[];
  };
  admet: Record<string, unknown>;
  nephrotox_risk: "Low" | "Moderate" | "High" | "Unknown";
  hl_score: number;           // HEURISTIC — 임상 반감기 아님
  warnings: string[];
  engine: string;
}

export interface BatchResponse {
  n_total: number;
  results: StabilityResponse[];
  summary: {
    n_stable_biopython: number;
    mean_mw: number;
    mean_gravy: number;
    mean_instability: number | null;
    mean_hl_score: number | null;
    heuristic_disclaimer: string;
  };
}
```

---

## 8. 구현 우선순위

| 우선순위 | 컴포넌트 | 소요 예상 |
|----------|---------|---------|
| P0 | `GET /api/stability/cand03` 호출 + 테이블 렌더 | 2h |
| P0 | HEURISTIC 배너 (필수 — 가드 준수) | 0.5h |
| P1 | 색상 코딩 (instability/nephrotox) | 1h |
| P1 | SST-14 baseline row 고정 | 0.5h |
| P2 | SinglePredict 입력 UI | 1.5h |
| P2 | NCAA diff 배지 | 1h |
| P3 | 비동기 배치 (job polling) | 2h |

---

## 9. 관련 파일

| 파일 | 용도 |
|------|------|
| `pipeline_local/scripts/stability_predictor.py` | 백엔드 계산 모듈 |
| `backend/routers/stability.py` | API 엔드포인트 |
| `pipeline_local/tests/test_stability_predictor.py` | 단위 테스트 |
| `docs/wetlab/stability_predictor_tools.md` | 도구 인벤토리 (researcher S6) |
| `runs_local/stability/batch_8_candidates.json` | 사전 계산 결과 캐시 |
