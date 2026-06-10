# Sanity Check v3 결과 — toxicity_retrained_2026-05-21.pth
## A.A5Pd — 2026-05-21 08:30

**상태**: ✅ PASS (모든 조건 충족)

---

## 예측 결과

| 후보 | binary_toxicity_pred | 기준 | 결과 |
|------|----------------------|------|------|
| Octreotide | **0.1322** | < 0.5 | ✅ PASS |
| SST-14 native | **0.4022** | < 0.5 | ✅ PASS |
| PRST-001 | 0.4022 | — | — |
| PRST-002 | 0.2681 | — | — |
| PRST-003 | **0.4854** | — | — |
| PRST-004 | 0.4022 | — | — |
| PRST max−min | **0.2174** | ≥ 0.2 | ✅ PASS |

---

## 알려진 약점 (team-lead 명시 요구)

- PRST-001 = PRST-004 = 0.4022 (정확 동일) → 변이 구별력 매우 약함
- SST-14 (0.40220) ≈ PRST-001 (0.40220) → SST-14 family 미세 구별 어려움
- test fold에 SS-bond 분자 0개 → cyclic peptide 일반화 미검증
- val score 0.25 (4-task 복합) → 절대 신뢰도 낮음

---

## Raw JSON

```json
{
  "model_path": "pepADMET/model/toxicity_retrained_2026-05-21.pth",
  "predictions": {
    "Octreotide": 0.1322096437215805,
    "SST-14": 0.4021983742713928,
    "PRST-001": 0.4021984040737152,
    "PRST-002": 0.26809483766555786,
    "PRST-003": 0.48544982075691223,
    "PRST-004": 0.4021984040737152
  },
  "status": "PASS",
  "timestamp": "2026-05-21T08:30:29.788364"
}
```

---

*생성: engineer-backend 2026-05-21 (A.A5Pd)*
