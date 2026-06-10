---
marp: true
theme: default
paginate: true
style: |
  section {
    background: #ffffff;
    color: #1a1a2e;
    font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
    padding: 38px 48px 56px 48px;
    box-sizing: border-box;
  }
  section::after {
    content: attr(data-marpit-pagination) ' / ' attr(data-marpit-pagination-total);
    position: absolute;
    left: 50%;
    right: auto;
    transform: translateX(-50%);
    bottom: 10px;
    padding: 2px 10px;
    background: rgba(255, 255, 255, 0.35);
    border-radius: 999px;
    box-shadow: 0 0 0 1px rgba(100, 116, 139, 0.1);
    font-size: 0.58em;
    font-weight: 500;
    color: rgba(71, 85, 105, 0.48);
    letter-spacing: 0.05em;
    line-height: 1.1;
  }
  h1 { color: #0f3460; font-size: 1.6em; border-bottom: 2px solid #0f3460; padding-bottom: 8px; }
  h2 { color: #16213e; font-size: 1.2em; }
  table {
    font-size: 0.84em;
    border-collapse: collapse;
    width: 100%;
    margin: 0.45em 0;
    border: 1px solid #cbd5e1;
  }
  th {
    background: #dfe7f2;
    color: #0f172a;
    font-weight: 700;
    padding: 0.48em 0.7em;
    border-bottom: 2px solid #0f3460;
    text-align: left;
    vertical-align: top;
  }
  td {
    padding: 0.42em 0.7em;
    border-bottom: 1px solid #e2e8f0;
    vertical-align: top;
    line-height: 1.35;
  }
  tbody tr:nth-child(even) td { background: #f8fafc; }
  tbody tr:last-child td { border-bottom: none; }
  .ref { position: absolute; bottom: 20px; right: 30px; font-size: 0.45em; color: #666; }
  .badge-ok { color: #22c55e; font-weight: bold; }
  .badge-wip { color: #f59e0b; font-weight: bold; }
  .badge-wait { color: #94a3b8; font-weight: bold; }
  img { border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  .small { font-size: 0.65em; color: #444; }
  .metric { font-size: 2em; font-weight: bold; color: #0f3460; }
  .big { font-size: 1.5em; font-weight: bold; color: #0f3460; line-height: 1.6; }
  .done { color: #22c55e; }
  .warn { color: #f59e0b; }
  .next { color: #ef4444; }
---

# SSTR2 방사성의약품 AI 파이프라인
## Version D — 5분 압축 보고

<br>

> **10개 액션 중 7개 완료, 파이프라인 검증 완료, 대규모 실행 대기**

<br>

2026-04-05 내부 보고 &nbsp;|&nbsp; 5-min compact

<div class="ref">전체 보고서: 01_ACTION_ITEMS_RESPONSE_REPORT.md</div>

---

# 완료된 것

<br>

<div class="big">

**1.** &nbsp; Pharma 메서드 — GT <span class="done">8/8 일치</span>, 15개 구현 완료

**2.** &nbsp; 후보 분류 — Cluster <span class="done">A ~ E</span> 5단계 체계 확립

**3.** &nbsp; Selectivity — SSTR 5종 CIF + FlexPepDock <span class="done">연결 완료</span>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 시스템 구축 완료, 대규모 시뮬레이션 즉시 가능

</div>

<br>

<div class="small">테스트 265 passed · UI 패널 8개 정상 · ddG 단위: REU</div>

<div class="ref">→ 부록 §1 pharma 검증 상세</div>

---

# pepADMET 전환

<br>

### ADMETlab 3.0 ❌ &nbsp;→&nbsp; pepADMET ✅

<br>

| 항목 | 상태 | 비고 |
|:-----|:----:|:-----|
| 코드 공개 (재학습 가능) | ✅ | GitHub 확보, 커스텀 학습 가능 |
| 모델 공개 (추론 성공) | ✅ | MGA 기반 추론 검증 완료 |
| Descriptor 파이프라인 | ⚠️ | pepADMET 전환 진행중 |

<br>

<div class="small">†HC50 R²=0.474, 보조 지표로만 활용 &nbsp;|&nbsp; II&lt;30 (보수적)</div>

<div class="ref">→ 부록 §3 pepADMET 환경 상세</div>

---

# UI 데모

<br>

### 멀티패널 대시보드 — 후보 테이블 + 차트 + Selectivity

![Silo B Dashboard](../screenshots/20260403/01_silo_b_light.png)

<div class="small">Streamlit 기반 · 후보 테이블 / ddG 산점도 / Selectivity 레이더 / 필터 등 8개 패널</div>

<div class="ref">→ 부록 §5 UI 기능 목록</div>

---

# 안 된 것 + 다음 스텝

<br>

| 구분 | 항목 | 액션 |
|:----:|:-----|:-----|
| <span class="next">Gap</span> | Cluster A 후보 공백 | **대규모 실행 필요** — GPU 자원 확보 후 착수 |
| <span class="warn">WIP</span> | pepADMET descriptor 전환 | **즉시 착수** — 1~2주 소요 예상 |

<br>

<div class="small">
우선순위: ① pepADMET descriptor 완료 → ② Cluster A 대규모 실행
</div>

<div class="ref">→ 부록 §7 잔여 이슈 상세</div>

---

# 논의 안건

<br>

### 1. Cluster A 대규모 실행 — GPU 자원 일정 확정

### 2. pepADMET descriptor — 전환 범위 및 우선 지표 합의

<br><br><br>

## 질문 부탁드립니다

<div class="ref">Version D compact · 2026-04-05</div>
