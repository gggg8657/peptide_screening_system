# Pharmacology Review — modification_conflict

**리뷰어**: reviewer-pharma (임시 역할)
**리뷰 대상**:
- `pipeline_local/scripts/modification_conflict.py`
- `pipeline_local/steps/step08_stability.py` (`_MODIFICATION_BONUS`, `predict_half_life`)
**날짜**: 2026-05-11

---

## 사전 검증

- `pipeline_local/tests/test_pharmacology_guards.py` pytest: **33/33 PASS** (0.13s, Python 3.13.12)
- 회귀 테스트는 Kyte-Doolittle / Boman / N-end rule(Pro=30h) / Lehninger pKa 무결성 모두 통과.
- step08 stability 출력 범위 테스트(`TestStep08StabilityOutputRange`) 4건도 모두 통과 — 후속 PK 평가 진행에 차단 요소 없음.

## 요약

- **판정: CONDITIONAL PASS** — 6개 규칙 모두 PK·반감기 정합성 측면에서 정당화 가능. 단, step08 보너스 누적 모델(단순 합산)이 conflict checker가 차단하지 않는 케이스에서 *over-prediction* 위험을 내포하므로 `§검증 필요` 항목 부착.
- **신뢰 등급: 中(보통)** — 화학적 차단 논리 자체는 일차 문헌(Knudsen 2019, Reubi 2000, Merrifield 1963)과 정합. 단, "차단되지 않은 조합"이 실제 PK에서 얼마나 가산적인지에 대한 정량 출처가 step08 측에 누락.

## 각 규칙 PK 영향 평가

| Rule | 차단 정당성 (PK 측면) | 반감기 효과 (시간) | 출처 |
|------|------------------|----------------|------|
| **C-01** | fatty_acid와 pegylation 둘 다 *반감기 연장* 전략. 동일 Lys ε-NH2에 둘 다 적용은 화학적으로 모노-치환만 가능 → 실제로는 한쪽만 부착되므로 "둘 다 +120+96=216h" 라는 step08 가산은 *물리적으로 불가능*. 차단이 정확 (over-prediction 방지). | fatty_acid 단독: +120h (세마글루타이드 168h 근사). pegylation 단독: +96h (PEG-exenatide 류 신장 청소율 감소). | Knudsen & Lau 2019 Front Endocrinol 10:155 (세마글루타이드 168h, K26 단일 결합); §검증 필요 (PEG-exenatide 96h 정확 수치) |
| **C-02** | fatty_acid를 Lys/N-term 외 위치(예: Ser, Thr)에 지정 시, NHS-ester 아실화는 생리적 pH에서 실효 반응성이 없어 실제로는 **부착 실패**. 만약 차단 없이 통과되면 step08가 `+120h`를 가산 → 알부민 결합 없이 반감기 168h 예측 = *심각한 over-prediction*. 차단 필수. | "잘못 적용" 시 실제 반감기는 base ~3h 수준으로 유지 (~120h 오차 발생). | Knudsen & Lau 2019 — 세마글루타이드 K26 ε-NH2 선택성. Merrifield 1963 J Am Chem Soc 85:2149 (선택적 acylation 화학) |
| **C-03** | Gly에 d_amino_acid 적용은 *no-op*. 키랄성 없으므로 D-Gly = L-Gly = 동일 화합물. step08가 `+48h` 보너스를 가산하면 **0h 실제값 대비 +48h over-prediction**. WARNING 차단 정당. | 실제 효과: 0h (no-op). 잘못 적용 시 step08 over-prediction: +48h. | Merrifield 1963 J Am Chem Soc 85:2149 (Gly 비키랄성). IUPAC 기본 입체화학. |
| **C-04** | SS bond 참여 Cys를 D-Cys로 치환 시 χ1 각 변화로 이황화결합 기하 왜곡 → β-turn 손상 → SSTR2 결합력 저하 가능. PK 측면에서 D-아미노산 보너스(+48h)는 *프로테아제 저항*에서 오는데, SS bond가 깨지면 환형 펩타이드의 **엔도펩티다제 차단 효과(+24h cyclization 보너스)**도 동시 상실. 즉, "+48h 얻고 -24h 잃고 + 결합력 손실"의 **net negative** 가능. WARNING 차단 정당. | D-Cys 치환 단독 효과 ≤ +48h. 단, cyclization 손실 -24h + SSTR2 affinity 손실로 net 음의 PK/PD 영향 우려. | Reubi JC 2000 Eur J Nucl Med 28:836 (DOTATATE SS topology). Veber DF et al. 1978 PNAS 75:2636 (somatostatin Cys D/L 치환). |
| **C-05** | 자연 Cys-Cys SS bond가 이미 환형 구조를 형성하는데 별도 `cyclization` modification을 추가하면 step08의 보너스 가산 로직에서 **이중 계산** 위험. 실제로 `predict_half_life` L217-225는 Cys 쌍 존재 시 `cyclization_bonus`(+24h)를 자동 적용. 외부에서 cyclization을 또 명시하면 ext_mod_bonus에 또 +24h 누적되어 **+48h 중복**. WARNING 차단 정당. | 실제 cyclization 효과: +24h (1회). 차단 실패 시 over-prediction: +24h. | Reubi 2000 (DOTATATE). step08_stability.py L222 자체 자동 가산 로직이 증거. |
| **C-06** | position 범위 밖이면 modification이 실체적으로 적용 불가. step08가 그래도 보너스를 가산하면 **존재하지 않는 잔기에 +120h 부여** = 환각. ERROR 차단 정당. | 실제 효과: 0h. step08 over-prediction 위험: 해당 mod_type 보너스 전액. | 기본 배열 인덱스 유효성. |

## step08_stability 정합성

### `_MODIFICATION_BONUS` (L89-95) vs conflict checker 차단 케이스

| step08 보너스 키 | 값 (h) | 출처 주석 | conflict checker 가드 | 정합성 |
|----------|------|----------|-----------------|------|
| `fatty_acid` | 120.0 | "세마글루타이드 168h 달성" | C-01(중복), C-02(위치) | **일치** — over-prediction 차단 |
| `pegylation` | 96.0 | "PEGylated exenatide 기준" | C-01(중복) | **부분 일치** — 위치 제약(Lys/N-term)이 conflict checker에 **누락** |
| `d_amino_acid` | 48.0 | "프로테아제 저항성" | C-03(Gly), C-04(SS Cys) | **일치** — no-op/구조 손상 케이스 차단 |
| `cyclization` | 24.0 | "엑소/엔도펩티다제 차단" | C-05(자연 SS 중복) | **일치** — 이중 계산 방지 |
| `substitution` | 12.0 | "Arg→Aib, Lys→Orn" | (가드 없음) | **불일치** — substitution mod에 대한 위치/잔기 적합성 검사 부재 |

### 일치/불일치 사례 정리

**일치 (PK 측면 보호 효과):**
1. C-01은 step08가 fatty_acid+pegylation 동시 적용 시 단순 `+120+96=216h` 가산하는 것을 사전 차단 — 물리적 모노-치환 한계 반영.
2. C-03/C-04는 d_amino_acid `+48h` 가산이 *적용 불가능한 잔기*에 들어가는 것을 차단.
3. C-05는 step08 L217-225의 자동 cyclization 보너스(+24h)와 명시적 cyclization 보너스(+24h)의 이중 계산을 방지.

**불일치 / 갭:**
1. **pegylation 위치 제약 부재** — step08은 PEG를 N-term에 배치(L350 `position=1`)하지만, conflict checker에는 "PEG가 N-term 외 위치에 적용 시" 차단 규칙이 없음. NHS-PEG도 화학적으로 Lys/N-term 선택적이므로 C-02와 대칭적인 규칙(가칭 C-07)이 필요할 수 있음. → §검증 필요.
2. **substitution 가드 부재** — step08은 R/K 잔기를 substitution 대상으로 권장(L391-401)하지만, conflict checker는 substitution mod_type에 대한 가드 없음. 예: substitution을 Cys SS bond 위치에 적용 시 C-04와 유사한 구조 손상 가능 — 가드 추가 검토 필요. → §검증 필요.
3. **반감기 가산 모델의 *상호작용 부재*** — `predict_half_life` L255-265는 ext_mod_bonus를 단순 합산하나, 실제 PK에서 fatty_acid(알부민 결합)와 d_amino_acid(프로테아제 저항)는 *부분적으로 독립*이지만 cyclization과는 효과 중첩 가능성 존재. conflict checker가 차단하지 않는 조합(예: fatty_acid + d_amino_acid 3개 = +120+48×3 = +264h)은 step08에서 통과되지만 임상 데이터로는 **세마글루타이드 168h를 초과한 사례가 거의 없음** → 상한 캡(`min(final_hl, 240h)`) 도입 검토. → §검증 필요.

## §검증 필요

1. **PEG20kDa exenatide 반감기 정확 수치** — step08 주석은 `+96h`이라 명시했으나 출처 미인용. *PEG-exenatide Exendin-4 conjugate* 임상 PK 데이터 1차 문헌 보강 필요. (예: Cirincione et al. 2017 Clin Pharmacokinet 등)
2. **PEGylation 위치 선택성 규칙(C-07 후보)** — NHS-PEG의 부위 선택성을 conflict checker에 추가할 것인가에 대한 화학자 판단 필요. linker 종류(NHS vs maleimide vs click chemistry)에 따라 위치 선택성이 다름.
3. **반감기 합산 상한 캡** — fatty_acid + cyclization + d_amino_acid 다중 적용 시 `predict_half_life`가 240h를 초과하는 경우, step08의 `min_half_life` 검증 외에 **상한 cap**이 필요한가? GLP-1 계열 임상 사례 검토 필요 (세마글루타이드 168h가 사실상 상한).
4. **C-04 D-Cys의 net PK 효과** — 본 보고서는 "+48h 보너스 vs -24h cyclization 손실"로 net 음의 영향을 추정했으나, 정량 문헌 데이터로 확정 필요. Veber 1978 외 추가 출처 권장.
5. **substitution mod_type 가드 부재** — engineer-backend에 C-08 또는 C-04 확장 형태로 substitution-on-SS-Cys 차단 규칙 추가 검토 요청 권장.

---

**결론**: 6개 충돌 규칙은 모두 step08의 단순 가산 모델이 만들 수 있는 over-prediction을 사전 차단하는 정합성 있는 가드. 화학적·구조적 근거는 일차 문헌과 일치. 단, pegylation 위치 가드 누락, substitution 가드 부재, 반감기 가산 상한 캡 부재 3가지는 후속 보강 권장. 회귀 테스트 33/33 통과로 lookup table 무결성 확보됨.
