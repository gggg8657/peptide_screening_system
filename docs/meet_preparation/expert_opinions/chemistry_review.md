# 화학 전문가 견해 — 합성·Modification·킬레이션
**작성**: reviewer-chemistry | **날짜**: 2026-06-01
**대상 회의**: KAERI-AIRL-MOM-2026-003 후속 6월 회의
**원칙**: 검증된 출처만 인용. 미검증 항목은 `[추정]` 명시. 약리학적 PK/효능 해석은 [다른 전문가 의견 권장].

---

## 1. A-04 Modification 전략 — 회의록 p.8 변형 후보 표 화학적 평가

### 1.1 잔기 치환

| 변형 | 난이도 | 예상 수율 | 판정 |
|-----|--------|----------|------|
| **Met→Nle** | 낮음 — Fmoc-Nle-OH 표준 시약 | 영향 없음 | PASS |
| **Lys→Orn** | 낮음 — Fmoc-Orn(Boc)-OH 표준 시약 | 영향 없음 | PASS |
| **Trp→5-F-Trp** | 중간 — 비천연 AA 빌딩블록 특주·국내 조달 확인 필요 | 결합 효율 ≥95% 가능 `[추정]` | CONDITIONAL |
| **Tyr→3-F-Tyr** | 중간 — Fmoc-3-F-Tyr(tBu)-OH 특주 필요 | 표준 `[추정]` | CONDITIONAL |

불소화 비천연 AA(5-F-Trp, 3-F-Tyr)의 방사분해 저항성 증가 효과는 불소 치환 방향족의 라디칼 안정화 화학에 기반한 `[추정]`이며 펩타이드 문맥 실측은 미확인 — §검증 필요.

### 1.2 환형화 전략 (Cys-Cys 브릿지 변형)

현재 SST-14 Cys3-Cys14 이황화결합(SS bond) 기준으로 대안 비교:

| 브릿지 | 합성 단계 | 환원 안정성 | 복잡도 | 판정 |
|-------|---------|-----------|--------|------|
| SS bond (현재) | SPPS 표준 + 공기 산화 | GSH 환경에서 분해 가능 | 낮음 | PASS (기준) |
| Thioether | SPPS 후 별도 반응 1단계 추가 | SS보다 ↑ | 높음 | CONDITIONAL |
| Lactam (Lys/Asp 또는 Lys/Glu) | SPPS 후 PyBOP/HOBt 고리화, 직교 보호기 필수 | 가수분해 저항↑ | 높음 | CONDITIONAL |
| Dicarba (RCM) | Grubbs 2세대 촉매 필요 — 비용↑ | 매우 높음 (C-C bond) | 매우 높음 | CONDITIONAL |

**D-Cys 치환 주의**: modification_conflict.py C-04 규칙 근거 — Veber 1978 (PNAS 75:2636) 실측 D-Cys 치환 시 활성 ~10× 감소. SS bond 내 Cys에 D-AA 적용은 ERROR.

SS bond를 대안 브릿지로 교체 시, 시퀀스 내 Cys를 Ala 등으로 선치환 후 cyclization modification을 지정해야 C-05(SS + cyclization 중복) 충돌이 발생하지 않는다.

### 1.3 D-아미노산 치환 (A-02 연계)

Fmoc-D-Phe-OH, Fmoc-D-Trp-OH, Fmoc-D-Nal-OH (D-2-naphthylalanine) 등은 Bachem, AAPPTec, Sigma-Aldrich에서 공급. Fmoc SPPS 완전 호환, 라세미화 위험 낮음(피페리딘 탈보호). 합성 가능성 자체는 PASS.

단, D-AA 도입 후 serum stability 예측 도구가 현재 부재(A-02 HIGH-BLOCKER, PEPlife2-GAT R²=0.022). 합성 후 in vitro serum stability 실측이 필수. [다른 전문가 의견 권장: PK 예측·반감기 해석은 reviewer-pharma]

---

## 2. A-09 ¹⁷⁷Lu DOTA 라벨링 — 프로토콜 화학적 타당성

### 2.1 DOTA 결합 위치

PRST-001~004 서열 내 Lys는 K4, K10 두 위치 존재. 선택지:
- **N-terminal α-NH2**: DOTA-NHS-ester amide 결합 — modification_conflict.py C-09 주의 필요(head-to-tail cyclization과 충돌). SST-14 계열은 SS bond 환형이므로 C-09 해당 없음.
- **Lys 측쇄 ε-NH2**: K4 또는 K10 단일 지정 필수. C-01 규칙 — 동일 Lys에 DOTA + fatty_acid 동시 불가. C-07 규칙 — DOTA는 펩타이드당 1개 (stoichiometry 원칙, Wadas 2010 Chem Rev 110:2858).

합성 의뢰서에 DOTA 결합 위치(N-term vs K4 vs K10)를 명시해야 한다.

### 2.2 ¹⁷⁷Lu 라벨링 프로토콜 (Lutathera NDA 208700 [R19] 기반)

1. DOTA-펩타이드 + [¹⁷⁷Lu]LuCl₃ + 0.4 M ammonium acetate buffer, pH 4.0~4.5
2. 가열: 95°C, 15~30분
3. 품질관리: RP-HPLC 또는 ITLC — RCP ≥95% 기준
4. Lab-scale RCY 80~95% 범위 `[추정 — 최적화 전 수율 확정 불가]`

회의록 기준 72시간 RCP ≥90% 달성 여부는 quencher 포함 제형에서 결정됨.

---

## 3. Radiolysis Quencher DOE 화학적 합리성

| Quencher | 기전 | 검증 수준 |
|---------|-----|---------|
| **Gentisic acid** 0.63 mg/mL | •OH 라디칼 scavenging (phenol OH기) | Lutathera NDA 208700 직접 확인 [R19] |
| **Ascorbic acid** 2.8 mg/mL | 환원제 — •OH 및 산화종 환원 (electron donor) | Lutathera NDA 208700 직접 확인 [R19] |
| **Methionine** | Met 황 원자의 라디칼 포획 → methionine sulfoxide | `[추정]` — 일부 항체 제형 사례, Lutathera 직접 성분 아님 |
| **Cysteine** | -SH 라디칼 scavenger | `[추정]` — **주의: 유리 Cys는 PRST SS bond와 thiol-disulfide exchange 반응 위험** |
| **Ethanol** | •OH → acetaldehyde 간접 전환 | `[추정]` — 주사제 잔류 에탄올 농도 규격 확인 필요 |

**핵심 화학적 주의**: PRST-001~004는 Cys3-Cys14 SS bond 함유 펩타이드. 유리 Cys를 quencher로 사용하면 thiol-disulfide exchange 반응이 발생해 SS bond 구조가 손상될 수 있다. **DOE에서 Cys 단독 조합 적용 시 이 위험을 명시적으로 제어하거나 제외를 검토** 권장.

Gentisic acid + Ascorbic acid 조합은 Lutathera에서 검증된 유일한 조합 [R19] — DOE 베이스라인으로 타당.

---

## 4. modification_conflict.py 화학적 일관성

C-01~C-10 규칙 전체 화학적 타당성 PASS (상세 근거: 코드 내 docstring 및 Knudsen 2019, Veber 1978, Davies 2003 인용).

**식별된 갭 3건**:

1. **C-07 mod_type 어휘 미연동**: step08_stability.py의 `suggest_modifications`가 "dota_conjugation" mod_type을 직접 생성하지 않아 C-07이 파이프라인 내 자동 트리거되지 않음. engineer-backend에 mod_type 어휘 확장 요청 권장.
2. **Thioether/lactam/dicarba 전용 규칙 부재**: 현재 단일 "cyclization" mod_type만 존재 — 복합 브릿지 전략 충돌 검출 불완전.
3. **불소화 AA 위치 경고 부재**: 5-F-Trp(W8), 3-F-Tyr 등 결합 핵심 잔기 변형에 대한 WARNING이 없음. [다른 전문가 의견 권장: 결합 핵심 잔기 영향은 reviewer-biology]

---

## 5. §검증 필요

- 5-F-Trp, 3-F-Tyr의 방사분해 저항성 실측 문헌 — 현재 `[추정]`
- Free Met quencher의 ¹⁷⁷Lu-DOTA 라벨링 조건 내 농도·효과 문헌
- 국내 Fmoc-D-Nal-OH, Fmoc-5-F-Trp-OH, Fmoc-3-F-Tyr(tBu)-OH 조달 벤더·납기
- PRST-001~004 합성 수율 사전 추정 (벤더 협의 전 확정 불가)
- C-07과 step08_stability.py 어휘 연동 — engineer-backend RFC

---

*화학 도메인: 합성 가능성·modification 화학·SPPS·DOTA 킬레이션·radiolysis quencher 화학*
*PK/ADMET → reviewer-pharma | 구조·결합 → reviewer-biology*
