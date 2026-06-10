# MSA Routing Cross-Check — 종합 판정 (2026-05-12)

- **팀**: `sod-2026-05-12-msa-routing-crosscheck` (4/4 closed)
- **사용자 질문**: "api.colabfold.com으로 directing 하는 게 옳은가?"
- **결과**: 4 레이어 분리 분석 → **layer별 판정 분리** 필요

---

## 1. 입력 산출

- T1 researcher → `_workspace/release/msa-routing-research-2026-05-12.md`
- T2 backend → `_workspace/release/msa-code-trace-2026-05-12.md`
- T3 science → `_workspace/release/msa-quality-2026-05-12.md`
- T4 biology → `_workspace/release/sstr-gpcr-msa-suitability-2026-05-12.md`

---

## 2. 사용자 질문 해체

질문은 *3 레이어*에 걸쳐 있음:

| 레이어 | 질문 | 담당 |
|--------|------|------|
| L1: routing 기술 | 어디로 가는가? alphafold.ebi.ac.uk가 옳은가? | T1+T2 |
| L2: 데이터 품질 | 다운로드 MSA가 충분한가? | T3 |
| L3: 응용 정당성 | 그 MSA + Boltz 결과를 *어떻게* 쓰는가? | T4 |

---

## 3. 레이어별 판정

### L1 — Routing 기술 ✅ **CORRECT**

- PR #14는 **api.colabfold.com을 호출하지 않음** (T2: cmd에 `--use_msa_server` 부재)
- alphafold.ebi.ac.uk가 **유일 외부 source** (직접 URL → API 동적 조회 fallback)
- PR 본문 표현 "차단 우회"는 *예방 조치*. 실제로는 처음부터 alphafold.ebi.ac.uk 단독 사용
- ColabFold ≈ AlphaFoldDB MSA: 등가 신뢰 (Mirdita 2022, HIGH 신뢰, T1)
- 형식 호환: `.a3m`은 Boltz YAML `msa:` 필드 직접 입력 (T2 확인)

### L2 — MSA 데이터 품질 ✅ **HIGH**

5개 SSTR MSA 정량 (T3):
| 지표 | 측정값 | 권장 | 판정 |
|------|--------|------|------|
| Depth | 19,116~19,490 seqs (unique 99.99%) | AF2: ≥1000 | ✅ 19× 초과 |
| Neff 추정 | ≈19,000+ | Boltz-2: 1000+ | ✅ |
| Paralog (라벨 기반) | 2.24% (436/19,444) | <5% 권장 | ✅ |
| TM2-TM7 coverage | 72~84% | binding pocket 핵심 | ✅ |
| TM1 coverage | 32.4% | (N-term truncation, 알려진 패턴) | ⚠️ 경미 |

**판정**: HIGH — Boltz-2 cross-validation 신뢰 가능. 단, Boltz 자동 8192 subsample (T1) 적용됨 → 실 사용 depth는 ~8192.

### L3 — 응용 정당성 ⚠️ **HEURISTIC-PARTIAL** (selectivity 정량 부적합)

T4 biology 검증:
- **iPTM 0.946 geometry 신뢰**: ✅ 최상위 (>0.8 구간, Evans 2022)
- **iPTM → Ki/Kd 추론**: ❌ **불가** (VR-cycle-09 H-06 가드)
- **iPTM → SSTR subtype 선택성 순위**: ❌ **모순 확인**

| 수용체 | 실측 Ki (nM) | Boltz iPTM | Ki 순위 | iPTM 순위 |
|--------|-------------|-----------|---------|-----------|
| SSTR1 | 0.4 | 0.975 | 3 | **1** |
| SSTR2 | **0.2 (최강)** | 0.946 | **1** | 4 |
| SSTR3 | 0.8 | 0.958 | 4 | 2 |
| SSTR4 | 1.6 (최약) | 0.956 | 5 | 3 |
| SSTR5 | 0.3 | 0.913 | 2 | 5 |

**순위 일치율 = 0/5** (Spearman ρ ≈ -0.3 추정). → iPTM은 *selectivity ranker 부적합*.

**Paralog 구조적 contamination** (T4): SSTR1-5 identity 39-70%, ECL2 선택성 신호가 family-공통 신호에 희석될 가능성. MED-HIGH 위험.

---

## 4. 사용자 직접 질문 답변

> **"api.colabfold.com으로 directing 하는 게 옳은가?"**

### 명확히
- PR #14는 *애초에 api.colabfold.com을 사용하지 않음*. **alphafold.ebi.ac.uk가 단독 source**.
- 따라서 "api.colabfold.com으로 directing"이 발생하지 않음.

### 더 정확한 질문 ("alphafold.ebi.ac.uk routing이 옳은가?")
- **기술적 routing: ✅ CORRECT** (등가 source, 형식 호환, 품질 HIGH)
- **응용 (iPTM → selectivity): ⚠️ epistemic gap** (routing 문제 아님, *상위 가정* 문제)

---

## 5. PR #14에 대한 권고

PR 본문에 다음 *2건 명시* 권고:

1. **iPTM의 한계 표기 의무**:
   > ⚠️ Boltz-2 iPTM은 *구조 geometry 신뢰도*이며 결합 친화도 또는 selectivity 순위의 *비례 proxy 아님*. 정량 선택성 평가 시 FEP/MM-GBSA 또는 실측 Ki binding assay (cand03 wetlab 계획 활용)로 확정 의무.

2. **Tier 분류 임계의 보정** (현재 `DEFAULT_TIER_THRESHOLDS`):
   - iPTM 절대값으로 T0~T3 분류하는 로직 → "iPTM Δ(SSTR2 vs off-target)"의 *상대값* 기반으로 재설계 검토
   - 또는 iPTM tier는 "geometry 신뢰성 필터"로만 사용하고 selectivity 판정은 별도 메트릭

---

## 6. 새 §검증 필요 등록

T1/T3/T4가 제기:
- **V-01** (MED): AlphaFoldDB v6 MSA 생성 방법 정확 확인 (FAQ 접근 불가)
- **V-04** (MED): a3m 내 MGnify/BFD 서열 포함 여부 (현재 UniRef90 헤더만 확인)
- **VB-02** (MED): SSTR2 MSA의 *binding pocket 잔기 (TM2/5/6/7)* 보존성 직접 측정
- **VB-04** (HIGH): SSTR1-5 paralog hit를 row 단위로 제거 → Boltz cross-validation 재실행 A/B 비교
- **VB-05** (HIGH): Boltz `msa: empty` (single-sequence) vs 본 MSA 결과 비교 — *deep MSA → inactive state bias* (Perez-Benito 2023) 영향 측정

---

## 7. 메타 관찰 — VR-cycle-08/09 가드 작동

- **VR-cycle-08 (echo 가드)**: 4 팀원이 모두 다른 수치 source를 *직접 read* — T2가 코드, T3가 a3m 파일, T4가 iPTM 표, T1이 외부 docs
- **VR-cycle-09 (H-06 가드)**: T4가 "iPTM은 affinity proxy 아님" 명시적 검증 — 단순 회피 아닌 *명시적 반증*

이 가드들이 routing 질문에서 *3 레이어 분리*를 가능케 함. T1 단독이라면 "ColabFold ≈ AlphaFoldDB → OK 종료"로 끝났을 것. T4가 *상위 가정*까지 의문화하여 epistemic gap 발견.

---

## 8. 종합 한 줄

**Routing은 옳다. 하지만 PR #14가 selectivity 정량을 iPTM에 위탁한 *상위 가정*에 epistemic gap 있음 — 별도 후속 PR 또는 README disclaimer 필요.**
