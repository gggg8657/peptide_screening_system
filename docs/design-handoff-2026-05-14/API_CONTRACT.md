# API Contract · SSTR2 Dashboard

> 본 prototype의 화면이 호출하는 endpoint 와 응답 shape. 기존 router는 응답 형식 조정 필요, 신규 router는 새로 구현.

Base URL: `http://127.0.0.1:8787/api`

## 1. 기존 Endpoint (응답 shape 조정 필요)

### `GET /api/status` — 현재 실행 상태

화면: A (Run Console) 상단 status pill.

```json
{
  "run_id": "local_20260512_1430_iter02",
  "started_at": "2026-05-12T14:30:12+09:00",
  "duration_seconds": 2358,
  "iteration": 2,
  "max_iterations": 5,
  "silo": "B",
  "llm_model": "qwen3-32b",
  "gpus": "H100 NVL × 4",
  "seed": 42,
  "current_step": "05c",
  "progress": 0.78,
  "state": "running"
}
```

### `GET /api/experiment/{run_id}/candidates` — 후보 리스트

화면: A (table), B (heatmap).

```json
{
  "run_id": "local_20260512_1430_iter02",
  "wild_type": "AGCKNFFWKTFTSC",
  "candidates": [
    {
      "id": "cand03",
      "seq": "AICKNFFWKTFTSC",
      "tier": "T2",
      "margin": 0.008,
      "best_receptor": "SSTR2",
      "iptm": {
        "SSTR1": 0.900, "SSTR2": 0.952, "SSTR3": 0.838,
        "SSTR4": 0.944, "SSTR5": 0.818
      },
      "ddg": -48.529,
      "source": "sst14_mutdock_42",
      "mutations": ["G2->I"],
      "recommended": true,
      "wildtype": false,
      "notes": "유일 SSTR2-selective T2..."
    }
  ]
}
```

`prototype/data.js → candidates` 배열 구조와 동일. 기존 `selectivity_summary.json`/`boltz_summary.json` 변환 함수만 추가.

### `GET /api/selectivity/{run_id}` — Selectivity 매트릭스

화면: B (Selectivity Explorer).

기존 `boltz_summary.json` 형식 그대로:

```json
{
  "cand03_AICKNFFWKTFTSC": {
    "seq": "AICKNFFWKTFTSC",
    "tier": "T2",
    "margin": 0.008,
    "best_receptor": "SSTR2",
    "iptms": { "SSTR1": 0.900, "SSTR2": 0.952, ... }
  }
}
```

### `POST /api/selectivity/run` — 단일 후보 재실행

```json
// Request
{ "candidate_id": "cand03", "receptor": "SSTR1", "n_struct": 1 }

// Response
{ "task_id": "boltz_20260512_1530", "eta_seconds": 30 }
```

### `GET /api/cluster/{run_id}` — FoldMason 클러스터

화면: C (variant 카탈로그). 기존 응답 유지.

### `GET /api/admet/{seq_id}` — ADMET 점수

화면: C (Candidate Review · stability 패널).

```json
{
  "seq_id": "cand03",
  "half_life_minutes": 5,
  "instability": 30.65,
  "boman_kcal": 0.18,
  "aggregation_score": 0.42,
  "gravy": 0.379,
  "vulnerabilities": [
    { "site": "F6-F7", "protease": "chymotrypsin", "severity": "high" },
    { "site": "K9-T10", "protease": "trypsin", "severity": "medium" }
  ],
  "confidence": "HEURISTIC / LOW"
}
```

### `GET /api/settings` / `PATCH /api/settings` — Gate 임계값

화면: D (Run Launcher).

```json
{
  "gates": {
    "plddt_mean": 60,
    "plddt_interface": 45,
    "disulfide_max_angstrom": 2.5,
    "docking_top_percent": 20,
    "diffdock_confidence_max": -1.0,
    "boltz_affinity_max": -8.0,
    "rosetta_ddg_max": -1.0,
    "rosetta_clash_max": 10,
    "selectivity_margin_max": -10.0,
    "off_target_max": -15.0,
    "boltz_iptm_margin_min": 0.0,
    "stability_half_life_min": 50.0,
    "foldmason_lddt_min": 0.6
  },
  "off_target_receptors": [
    { "name": "SSTR1", "uniprot": "P30872", "pdb": "9IK8", "enabled": true },
    { "name": "SSTR3", "uniprot": "P32745", "pdb": "8XIR", "enabled": true }
  ],
  "boltz_cross_enabled": false
}
```

---

## 2. 신규 Endpoint (구현 필요)

### `GET /api/agents/{run_id}/log` — 5-agent 로그 (REST)

화면: A (Agent rail · 첫 로드).

```json
{
  "agents": [
    { "id": "planner", "name": "Planner", "role": "실험 설계", "color": "violet" },
    { "id": "builder", "name": "Builder", "role": "코드 실행", "color": "blue" },
    { "id": "qcranker", "name": "QCRanker", "role": "Gate 평가 + 랭킹", "color": "cyan" },
    { "id": "diversity", "name": "DiversityManager", "role": "foldmason 클러스터링", "color": "teal" },
    { "id": "critic", "name": "Critic", "role": "실패 진단 + 게이트 조정", "color": "amber" },
    { "id": "reporter", "name": "Reporter", "role": "요약 + 결정 기록", "color": "stone" }
  ],
  "entries": [
    {
      "ts": "2026-05-12T14:30:12+09:00",
      "agent": "planner",
      "level": "info",
      "text": "iter02 변이 전략 결정: pos2 G→I/V/L 친수성 변이 확장..."
    }
  ]
}
```

### `GET /api/agents/{run_id}/stream` — SSE live stream

화면: A (Agent rail · live).

```
event: agent
data: {"ts":"2026-05-12T15:08:45+09:00","agent":"critic","text":"T2 후보 cand03..."}

event: status
data: {"current_step":"05c","progress":0.78}
```

`text/event-stream` content-type, Last-Event-ID 헤더로 재연결 지원.

### `GET /api/pipelines/{silo}` — Silo별 파이프라인 구조

화면: A (PipelineFlow 컴포넌트).

`silo`: `A` | `B` | `Combined`

```json
{
  "name": "Silo A · De Novo",
  "description": "RFdiffusion 백본부터 새로 디자인",
  "stages": [
    {
      "id": "02",
      "name": "Backbone",
      "group": "gen",
      "tool": "RFdiffusion",
      "env": "rfdiffusion",
      "status": "done",
      "in_count": 1,
      "out_count": 10,
      "in_unit": "receptor",
      "out_unit": "bb·pdb",
      "time": "4:12",
      "gpu": "H100×1",
      "gate": null,
      "pass": null,
      "fail": null,
      "progress": null
    }
  ]
}
```

Combined일 경우:
```json
{
  "name": "Dual Silo · A + B",
  "input": { "id": "01", "name": "Receptor", ... },
  "tracks": [
    { "silo": "A", "label": "de novo", "stages": [...] },
    { "silo": "B", "label": "mutation", "stages": [...] }
  ],
  "converge": [...]
}
```

### `GET /api/cand03_variants/list` — 변이체 카탈로그

화면: C (Candidate Review · 변이체 테이블).

데이터 소스: `runs_local/cand03_variants/cand03_variants.json` (이미 존재, 20종).

```json
{
  "baseline": "cand03",
  "variants": [
    {
      "id": "var12",
      "name": "var12 (T12 → D-Thr)",
      "seq": "AICKNFFWKTF*SC",
      "modifications": ["D-Thr12"],
      "hl_score": 16.72,
      "chymotrypsin_sites": 4,
      "trypsin_sites": 2,
      "nep_sites": 5,
      "priority": "★ 1순위",
      "rationale": "stability 보강, Boltz iPTM 0.952 유지"
    }
  ]
}
```

### `POST /api/runs/start` — 새 실행 시작

화면: D (Run Launcher).

```json
// Request
{
  "name": "local_20260512_iter03",
  "silo": "B",
  "iterations": 3,
  "seed": 42,
  "n_backbone": 10,
  "k_seq_per_backbone": 8,
  "top_m_rosetta": 10,
  "llm_model": "qwen3-32b",
  "mutation_strategy": "ga_bo",
  "off_targets": ["SSTR1", "SSTR3", "SSTR4", "SSTR5"],
  "boltz_cross_enabled": true,
  "gates": { "plddt_mean": 60, ... }
}

// Response
{
  "run_id": "local_20260512_2030_iter01",
  "started_at": "2026-05-12T20:30:01+09:00",
  "estimated_eta_minutes": 28,
  "monitor_url": "/runs/local_20260512_2030_iter01"
}
```

### `GET /api/runs/{run_id}/predicted_pass_rates` — Gate 예상 통과율

화면: D (Run Launcher · 우측 패널).

```json
{
  "based_on": "iter02 + 4 historical runs",
  "predicted": [
    { "gate_id": "G1", "name": "pLDDT", "rate": 0.91 },
    { "gate_id": "G2", "name": "Docking", "rate": 0.22 },
    { "gate_id": "G3", "name": "Selectivity", "rate": 0.50 },
    { "gate_id": "G3b", "name": "Boltz iPTM margin", "rate": 0.12, "warn": true }
  ]
}
```

### `GET /api/benchmark/results` — LLM benchmark

화면: E (LLM Benchmark Dashboard).

Query: `?phase=V2&metric=pass_rate`

데이터 소스: `llm_benchmark/analysis/*.json` (이미 존재).

```json
{
  "phase": "V2",
  "total_runs": 199,
  "llms": [
    { "id": "qwen3-32b", "short": "q32", "vram_gb": 80 },
    { "id": "qwen3-14b", "short": "q14", "vram_gb": 40 }
  ],
  "flows": [
    { "id": "sequential", "name": "Sequential", "desc": "P→B→Q→C→R 단방향" }
  ],
  "matrix": {
    "qwen3-32b": {
      "sequential":    { "pass_rate": 87, "time_min": 38, "candidates": 12, "t2": 1, "cost": 1.0 },
      "collaborative": { "pass_rate": 82, "time_min": 51, "candidates": 14, "t2": 1, "cost": 1.4 }
    }
  }
}
```

### `GET /api/wetlab/orders` — 발주서 리스트

화면: F (Wetlab Order).

```json
{
  "orders": [
    {
      "id": "WO-2026-005",
      "candidate_id": "cand03",
      "stage": "approval",
      "total_krw": 13400000,
      "lead_weeks": 8,
      "requested_by": "dongjukim@kaeri.re.kr",
      "created_at": "2026-05-12T09:00:00+09:00"
    }
  ]
}
```

### `GET /api/wetlab/orders/{id}` — 발주서 상세

```json
{
  "id": "WO-2026-005",
  "candidate_id": "cand03",
  "candidate_seq": "AICKNFFWKTFTSC",
  "stage": "approval",
  "hypothesis": {
    "h1": "cand03은 SSTR2에 대해 SST-14 대비 향상된 선택성을 보이며 Ki(SSTR2) < 10 nM",
    "h0": "cand03의 Ki 프로파일이 SST-14와 유의미한 차이가 없다"
  },
  "predicted_ki": [
    { "receptor": "SSTR1", "iptm": 0.900, "sst14_ki_nm": 0.4, "predicted_ki": "≥ 5 nM" },
    { "receptor": "SSTR2", "iptm": 0.952, "sst14_ki_nm": 0.2, "predicted_ki": "0.5–5 nM", "target": true }
  ],
  "reagents": [
    {
      "name": "cand03",
      "spec": "14aa · Cys SS bond · ≥95% (HPLC) · 5 mg",
      "vendor": "Peptron",
      "unit_price_krw": 2500000,
      "qty": 1,
      "lead_days": "10-14"
    }
  ],
  "protocol": {
    "format": "96-well competition binding",
    "tracer": "¹²⁵I-Tyr¹¹ SS-14 · 0.05 nM final",
    "membrane": "SSTR1–5 stable cell, 2 µg/well",
    "concentration_range": "10⁻¹² – 10⁻⁵ M · 11-point",
    "replicates": "n = 3 technical × 3 biological",
    "negative_control": "Scrambled cand03 @ 1 µM",
    "readout": "γ-counter, 1 min/well",
    "analysis": "GraphPad Prism · log Ki + Welch t-test"
  },
  "acceptance_criteria": [
    { "criterion": "cand03 Ki(SSTR2) < 10 nM", "passed": null },
    { "criterion": "log SI(SSTR1/SSTR2) > 1.0", "passed": null }
  ],
  "timeline": [
    { "week": "1주", "task": "PO 발주 · 시약 입하 추적", "actor": "연구원" }
  ]
}
```

### `POST /api/wetlab/orders` — 발주서 생성

```json
// Request
{ "candidate_id": "cand03" }

// Response: full order object
```

### `POST /api/wetlab/orders/{id}/transition` — 상태 변경

```json
// Request
{ "to_stage": "approval", "note": "PI 검토 요청" }

// Response
{ "id": "WO-2026-005", "stage": "approval", "updated_at": "..." }
```

---

## 3. Error Format (전역)

```json
{
  "error": {
    "code": "candidate_not_found",
    "message": "후보 cand99를 찾을 수 없음",
    "hint": "GET /api/experiment/{run_id}/candidates 로 유효한 ID 조회"
  }
}
```

HTTP status: 4xx (client), 5xx (server).
