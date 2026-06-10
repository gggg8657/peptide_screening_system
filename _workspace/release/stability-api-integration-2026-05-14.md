# T3 — stability_predictor BE API 통합 검증 (2026-05-14)

> **수행**: orchestrator 직접 (cursor-agent wrapper args parsing 실패 fallback)
> **대상**: PR #20 머지 후 BE 가동 상태에서 5 endpoint 가동성 + schema 일관성 검증

---

## §0 메타

- BE: `http://localhost:8787` (uvicorn, run_id `local_20260514_0240_iter01`)
- 모듈: `pipeline_local/scripts/stability_predictor/` (Plugin 패턴 패키지, 1735 LOC)
- 라우터: `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/routers/stability.py`

---

## §1 5 Endpoint 응답 표

| Endpoint | Method | Status | Schema | `is_unstable` | HEURISTIC disclaimer |
|----------|--------|--------|--------|---------------|---------------------|
| `/api/stability/predict?seq=` | GET | ✅ 200 | ⚠️ 중첩 + 다른 키명 (legacy?) | ❌ **MISSING** | ⚠️ `warnings` 키로만 |
| `/api/stability/cand03` | GET | ✅ 200 | ✅ flat (18 키) | ✅ 노출 | ✅ `hl_warnings` |
| `/api/stability/batch` | POST | ✅ 200 | ✅ flat (18 키) | ✅ True (ILCKK II=55.14) | ✅ `hl_warnings` |
| `/api/stability/batch/async` | POST | (미테스트 — 비동기) | — | — | — |
| `/api/stability/result/{job_id}` | GET | (미테스트 — async 의존) | — | — | — |

### 1.1 `/batch` 응답 (정상 schema, 18 키)
```
['admet_score', 'aliphatic_index', 'boman', 'canonical_sequence', 'charge_ph74',
 'gravy', 'hl_score_heuristic', 'hl_warnings', 'instability_index', 'is_unstable',
 'mw', 'ncaa_warnings', 'nephrotox_risk', 'pi', 'protease_cleavage_sites',
 'seq_id', 'sequence', 'stability_class']
```

### 1.2 `/predict` 응답 (legacy schema, 다른 키)
```
['admet', 'aliphatic_index', 'biophysical', 'boman', 'canonical_sequence',
 'engine', 'hl_score', 'nephrotox_risk', 'protease_predictions', 'seq_id',
 'sequence', 'warnings']
```

---

## §2 결함 등록 — F-15: stability API schema inconsistency

### F-15 (Medium)

**위치**: `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/routers/stability.py` (정확한 라인은 후속 확인)

**증상**:
- `/predict` endpoint와 `/batch`+`/cand03` endpoint가 *다른 schema*를 반환
- predict의 top-level 키:
  - `biophysical: {mw, gravy, instability_index, pi}` (중첩) vs batch는 flat
  - `protease_predictions` vs `protease_cleavage_sites`
  - `hl_score` vs `hl_score_heuristic`
  - `admet` vs `admet_score`
  - `warnings` vs `hl_warnings`
- predict 응답에 **`is_unstable` / `stability_class` 누락**
- batch/cand03은 `StabilityResult` dataclass 그대로 직렬화, predict는 *별도 wrapper transform*

**원인 추정**: predict가 *별도 함수* 또는 *legacy response builder*를 사용 (Plugin 패턴 패키지 전환 시 predict 핸들러만 갱신 누락 가능성)

**영향**:
- FE 클라이언트가 predict와 batch를 *다른 데이터 형식*으로 처리해야 함
- `is_unstable` flag를 predict 단일 호출로 얻을 수 없음 → 사용자가 batch만 호출하도록 우회 필요

**권장 fix**:
- predict가 `StabilityResult.to_dict()`를 *직접* 반환하도록 통일
- 또는 batch가 predict와 동일 schema를 따르도록 변경
- 회귀 테스트: predict와 batch 응답이 동일 키 set을 갖도록 명시적 검증

---

## §3 step05c ↔ step08 ↔ stability_predictor 통합 흐름

### 분석 결과 (코드 read)
- `pipeline_local/steps/step08_stability.py` — 기존 모듈 (HL ranking score 계산)
- `pipeline_local/scripts/stability_predictor/` — 새 패키지 (U1+U5, 종합 평가)
- 호출 관계:
  - **stability_predictor → step08**: `hl_score_heuristic` 산출 시 step08의 `predict_half_life`와 *동일 한계* (응답 HEURISTIC disclaimer에 명시)
  - **step05c → stability_predictor**: 직접 호출 없음 (선택성 측정과 안정성 평가는 *직교*)

### DRY 평가
- step08의 `predict_half_life` 와 stability_predictor의 `hl_score_heuristic` 가 *유사 책임*이나 *분리 정당*:
  - step08: 파이프라인 흐름 내 step (8번째 단계, gate 평가)
  - stability_predictor: 독립 모듈 + BE API 제공 (외부 호출용)
- 두 함수가 같은 HEURISTIC 한계를 *공유*함을 disclaimer로 명시 (적절)

---

## §4 HEURISTIC disclaimer 자동 부착 검증

batch 응답에서 ILCKKFFWKTFTSC의 `hl_warnings`:
```
[HEURISTIC] 시퀀스 기반 physicochemical 속성 + heuristic HL ranking score.
한계: hl_score_heuristic: step08_stability.predict_half_life 와 동일 한계 (in-vitro assay X, PK 모델 X). ...
```

→ `pharmacology_guards.HEURISTIC_FUNCTION_DISCLAIMERS["pipeline_local.scripts.stability_predictor.compute_stability"]` entry가 *자동* 부착됨. **VR-cycle-09 (H-06) 가드 준수 확인**.

단, predict의 `warnings` 키도 동일 disclaimer를 포함하는지는 *별도 확인 필요*.

---

## §5 ILCKKFFWKTFTSC 검증 (II=55.14 → is_unstable=True)

```json
{
  "instability_index": 55.14,
  "is_unstable": true,
  "stability_class": "unstable",
  "hl_warnings": ["[HEURISTIC] ..."]
}
```

✅ Guruprasad 1990 threshold (II>40 → unstable) 정상 작동. 어제 추가된 `__post_init__` 자동 도출 검증됨.

---

## §6 종합 판정

| 차원 | 판정 |
|------|------|
| BE 5 endpoint 가동 | ✅ 3/5 직접 확인 (predict/batch/cand03), 2/5 미테스트 (async) |
| schema 일관성 | ⚠️ **F-15 (Medium) 등록** — predict가 다른 schema |
| `is_unstable`/`stability_class` 작동 | ✅ batch/cand03에서 정상 (Guruprasad 1990) |
| HEURISTIC disclaimer 부착 | ✅ batch/cand03 정상, predict는 미확인 |
| step05c/step08 통합 | ✅ 직교 책임 분리 명확 |

**결과**: T3 통합 검증 SUCCESS — schema 일관성 결함 1건(F-15) 등록 필요 후속 PR.

---

## §7 워크플로우 메타 관찰

- **cursor-agent CLI 위임 실패**: wrapper의 `ARGS="$*"` 처리가 prompt 내 `-s` 옵션 글자를 cursor-agent의 자체 옵션으로 잘못 해석 (`error: unknown option '-s'`)
- **Fallback 패턴**: orchestrator가 즉시 직접 검증으로 전환 — 워크플로우 *유연성* 확보
- **토큰 절약 실패**: 본 작업은 본 세션 토큰을 소모함. wrapper 개선 또는 cursor-agent 호출 방식 재정의 필요 (별도 hotfix 후보)

---

**작성**: orchestrator (Claude Opus 4.7 1M)
**소요**: ~5분 (직접 검증)
