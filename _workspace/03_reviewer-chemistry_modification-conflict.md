# Chemistry Review — modification_conflict

리뷰어: reviewer-chemistry (임시 역할)
날짜: 2026-05-11
대상: `pipeline_local/scripts/modification_conflict.py` (Phase 1 산출물)
참고: Phase 1 셀프-노트 `_workspace/01_engineer-backend_modification-conflict-v1.md`

---

## 요약

- **판정: CONDITIONAL PASS**
- **신뢰 등급: MED (HIGH로 끌어올리려면 아래 §검증 필요 해소 + 추가 규칙 C-07 ~ C-10 채택 필요)**

C-01 ~ C-06 여섯 규칙 모두 화학적으로 타당한 근거를 갖고 있으며, 출처도 1차 문헌으로 적절히 인용되어 있다. 다만 C-04의 severity 선택(WARNING)이 SST-14의 핵심 약리 구조를 다루는 점에서 **너무 관대**하며, SPPS/NCL 관점에서 누락된 충돌 4건(C-07 ~ C-10 제안)이 존재한다. step08_stability.py의 modification 제안 출력이 0~2개 Lys 가정에 묶여 있어, 본 체커가 그 가정을 깨는 다중 fatty_acid 경우를 검출하지 못하는 점도 보완 대상이다.

---

## 각 규칙 화학 정확성 평가

| Rule | PASS? | 화학 근거 | 출처 |
|------|-------|---------|------|
| C-01 | PASS | Lys 측쇄 ε-NH2는 1차 친핵성 부위 1개뿐. NHS-ester 활성화된 C18 지방산과 PEG-NHS 링커가 같은 ε-NH2에 동시 결합하면 amide bond formation이 경쟁(둘 다 동일한 nucleophile-electrophile 화학)하며 모노-아실화만 허용. ERROR 등급이 적절. 다만 description의 "PEG는 N-말단(position 1)이나 다른 Lys에 이동 권장" 부분은 SST-14의 N-term이 비-Lys일 때만 유효 — 사용자 시퀀스 일반화 시 부정확할 수 있어 문구 수정 권장. | Knudsen & Lau 2019 Front Endocrinol 10:155; Lau et al. 2015 J Med Chem 58:7370 (세마글루타이드 단일 K26 아실화 입증) |
| C-02 | PASS | C18-NHS 또는 γ-Glu-spacer 활성화 지방산은 ε-NH2(Lys)와 α-NH2(N-term)에만 선택적으로 amide 결합. Ser/Thr OH는 pKa~13으로 생리적 pH에서 deprotonation 비율이 ~10^-6, 비교 가능한 nucleophilicity 부족(Hermanson, Bioconjugate Techniques 3rd ed. Ch.2). N-term α-NH2 예외 처리는 라이라글루타이드/세마글루타이드 양쪽 모두 Lys ε에 가져갔으나, lipidation 일반론에서 N-term α-NH2도 표준 부위이므로 허용은 정확. | Knudsen & Lau 2019; Hermanson 2013 Bioconjugate Techniques 3rd ed. Ch.2 (NHS-ester 부위선택성) |
| C-03 | PASS | Glycine은 α-탄소가 R = -H 라 키랄 중심이 없으며 D-Gly과 L-Gly은 동일 화합물(Cahn-Ingold-Prelog 규칙). 따라서 안정성 boost 0 → no-op WARNING이 적절. | Merrifield 1963 J Am Chem Soc 85:2149; IUPAC-IUB JCBN 1984 Eur J Biochem 138:9 (아미노산 입체화학 nomenclature) |
| C-04 | **CONDITIONAL** | D-Cys 치환 시 측쇄 χ1/χ2 이면각이 변하여 SS bond geometry(S-S 거리 ~2.05 Å, Cα-Cβ-S-S-Cβ-Cα dihedral) 형성에 필요한 conformational restraint가 깨지며 — SSTR2 결합에 필수인 FWKT pharmacophore β-turn(Cys3-Cys14 핵심)이 손상될 수 있음. 다만 **WARNING이 너무 관대하다**. SST-14의 SS bond는 binding affinity의 핵심이며(Veber 1978 PNAS 75:2636에서 D-Cys 치환은 활성 ~10x 감소), Phase 1 셀프-노트에 명시된 "DOTATATE Cys3-Cys14 토폴로지"가 *기능적으로 critical*이라면 **ERROR로 격상** 권장. 단, fatty acid-conjugated linear analog 같은 의도적 SS 제거 케이스를 막지 않으려면 WARNING 유지 + suggestion에 "SS bond 제거 의도라면 두 Cys 모두 substitution 필요" 명시. | Reubi 2000 Eur J Nucl Med 28:836; Veber DF et al. 1978 PNAS 75:2636 (Cys D/L 치환 활성 비교); Pellegrini & Mierke 1999 Biopolymers 51:208 (somatostatin β-turn) |
| C-05 | PASS | DOTATATE 류처럼 Cys-Cys 쌍이 시퀀스 내 존재하면 SPPS 후 산화(공기/I₂/DMSO) 단계에서 intramolecular SS bond가 자발 형성. 이 상태에서 별도 cyclization(head-to-tail amide, lactam side-chain, click chemistry 등) 추가는 (1) 합성 단계 비용 중복, (2) lactam 시도가 SS-인접 잔기와 부피 충돌, (3) 잠재적 SS-scrambling 위험. WARNING 등급이 적절(완전 금지가 아닌 bicyclic 의도일 수도 있음). | Reubi 2000 Eur J Nucl Med 28:836; Andreu et al. 1994 Methods Mol Biol 35:91 (SPPS SS 산화 프로토콜) |
| C-06 | PASS | 화학적 의미 없음. 코드 안전성/조기 실패(fail-fast) 측면에서 ERROR가 적절. position이 정수가 아닌 경우(예: 4.5, "K4")까지 잡아내는 isinstance 체크가 견고. **단**, `bool`이 `int`의 서브클래스라 `isinstance(True, int) == True`로 통과하는 파이썬 함정 존재 → `isinstance(pos, int) and not isinstance(pos, bool)` 권장. | (코드 안전성 사항, 화학 출처 무관) |

---

## 놓친 규칙 (추가 제안)

| 제안 ID | 설명 | 출처 | severity |
|--------|------|------|---------|
| **C-07** | **DOTA(또는 NOTA/HBED-CC) chelator 이중 결합 금지** — chelator는 분자당 1개여야 라벨링 stoichiometry가 정의됨. 두 개의 DOTA가 있으면 ⁶⁸Ga/¹⁷⁷Lu 정량적 충진이 깨지고 라디오케미컬 순도(RCP) 검증이 불가. step08_stability.py에 DOTA modification 타입은 아직 없으나, theranostic 라벨링이 reviewer-chemistry.md 필수 영역이므로 modification 어휘 확장과 함께 도입 권장. | Velikyan 2014 Theranostics 4:47 (⁶⁸Ga-DOTATATE 라벨링 화학); Price & Orvig 2014 Chem Soc Rev 43:260 | ERROR |
| **C-08** | **인접 Cys 쌍 양쪽에 동시 d_amino_acid 적용 → SS bond 형성 불가** — SS pair의 한쪽만 D-Cys면 geometry 왜곡(C-04), 둘 다 D-Cys면 D,D-cystine은 형성 가능하지만 SST-14의 β-turn topology와 incompatible(거울상). 한쪽만 D-치환은 더 심각하나, 두 쪽 모두 D-치환 케이스는 별도 명시적 검증이 필요. | Mosberg et al. 1983 PNAS 80:5871 (D,D-cystine peptide bicyclic 구조 비교) | WARNING |
| **C-09** | **N-term cyclized peptide(head-to-tail lactam) + N-terminus modification 충돌** — head-to-tail cyclization은 N-term α-NH2를 C-term α-COOH와 amide bond로 소비. 이 상태에서 N-term에 fatty_acid 또는 DOTA를 시도하면 결합할 1차 아민이 없음. C-05가 자연 SS만 다루므로 lactam/head-to-tail cyclization과 N-term acylation의 조합을 별도로 잡아야 함. | Davies 2003 J Pept Sci 9:471 (head-to-tail cyclic peptide N-term 비가용성) | ERROR |
| **C-10** | **동일 position에 substitution + d_amino_acid 동시 지정** — substitution은 잔기 자체를 다른 아미노산으로 교체(예: K→Orn), d_amino_acid는 키랄성만 D로 바꿈. 같은 position에 둘 다 지정되면 (1) 의미적 ambiguous(substituted 결과 잔기의 D form인가?), (2) 합성 SOP 작성 시 어느 Fmoc 빌딩블록을 발주할지 결정 불가. step08_stability.py의 fatty_acid_pos와 substitution_candidates는 분리되지만 외부 입력 시 충돌 가능. | (의미적 충돌 — pipeline schema 무결성 측면) | ERROR |
| **C-11(옵션)** | **N-methylation + Pro 직전 위치 또는 Pro 자체** — Pro는 이미 secondary amine, NMe-Pro 합성 시 매우 비효율. Pro 직전 잔기의 NMe는 SPPS 결합 효율 <50%로 폐기율 급증. modification 어휘에 NMe가 들어가면 도입 필요. | Chatterjee et al. 2008 Acc Chem Res 41:1331 (NMe SPPS 효율) | WARNING |
| **C-12(옵션)** | **Met/Trp 잔기에 산화-민감 modification 부가** — Met S-oxide, Trp kynurenine 산화는 long-term 보관 시 발생. SS 산화 단계(I₂/DMSO)에서 Met/Trp 보호 필요. SST-14에는 W8이 있어 적용 대상. | Stadtman 2006 Free Radic Biol Med 41:1378 (Met/Trp 산화) | WARNING |

C-07~C-10은 본 체커의 적용 도메인(SST-14 theranostic 라벨링 + 안정성 최적화)에 직접 관련되므로 차기 iteration에서 채택을 강력 권고. C-11/C-12는 modification 어휘 확장 시 후속.

---

## 의도 vs 구현 갭

- **`_find_cys_pairs`의 4잔기 간격 임계값**: 코드는 `j - i >= 4` 인데 SST-14는 `13 - 2 = 11`로 통과. 일반론에서 SS bond 최소 loop size는 2~3 잔기(예: 옥시토신 Cys1-Cys6, loop=4)이므로 임계값 `>= 4`는 *지나치게 보수적*. 짧은 hairpin cystine knot peptide(예: 일부 conotoxin Cys-Cys-X-Cys)는 누락될 수 있음 — SST-14 한정 사용이면 무관하나 일반 어셈블리에 쓰일 거면 `>= 3` 또는 `>= 2` 검토 필요. 출처: Pallaghy et al. 1994 Protein Sci 3:1833 (CSK motif loop size 통계).
- **C-04의 SS 쌍 추정 휴리스틱**: 시퀀스 내 모든 가능 Cys 쌍을 SS로 가정. SST-14처럼 Cys 2개면 안전하나 Cys ≥3 (예: ICK conotoxin)이면 잘못된 페어링을 SS로 가정해 false-positive WARNING 발생 가능. step08_stability.py와 일치한다고 명시되어 있으나, 실측 SS connectivity가 PDB로 알려진 경우 명시 인자(`ss_pairs` 옵션 인자) 제공 권장.
- **mods_involved 중복 인덱스**: C-01에서 한 position에 fatty_acid 2개 + pegylation 1개 같은 비정상 케이스 시 list 컴프리헨션이 중복을 만들 수 있음(현재 `sorted(...)`로만 정렬, dedup 안 됨). 합성 의도상 거의 발생 안 하나 schema 검증 측면에서 `sorted(set(...))` 권장.
- **N-terminal 정의의 모호성**: C-02에서 `pos == 1`을 N-terminal로 간주. fatty_acid가 spacer(γ-Glu, OEG) 없이 직접 N-term α-NH2에 붙는 것과 spacer를 통해 붙는 것은 다르나 코드는 둘을 구분하지 않음. semaglutide는 γ-Glu-γ-Glu-C18-diacid spacer 필수(Knudsen 2019 Fig.2). 현 체커는 *위치*만 검증하므로 spacer 누락은 별도 단계의 책임 → 본 PR 범위 밖이나 §검증 필요 항목으로 기록.

---

## §검증 필요 (확인 못한 점)

1. **C-04 severity 결정**: WARNING vs ERROR는 프로젝트 정책 결정 사항. SST-14 fatty acid analog의 SS bond 제거를 의도적 설계 옵션으로 두는지(예: linear semaglutide-style analog) 확인 필요 → reviewer-pharma 또는 PI 결정.
2. **DOTA/chelator modification 어휘**: 현 `mod_type` 열거에 `dota_conjugation`, `chelator`가 부재. theranostic 라벨링이 프로젝트 핵심이라면 step08_stability.py와 본 체커 모두 어휘 확장 필요 — 별도 이슈로 등록 권장.
3. **세마글루타이드 spacer 화학(γ-Glu, OEG)**: fatty_acid modification이 단순 C18인지 C18-diacid + γ-Glu spacer인지 schema가 침묵. spacer 없는 직접 acylation은 albumin binding이 약함(Lau 2015) — modification dict에 `spacer` 필드 도입 필요 가능성.
4. **Aib(α-aminoisobutyric acid) 같은 비표준 잔기**: substitution 후보에 Aib, Orn, Nle 등이 도입되면 substitution → d_amino_acid C-03 검사가 무력화(Aib는 비키랄). 비표준 잔기 어휘 확장 시 C-03 로직 보강 필요.
5. **테스트 커버리지 갭**: 현재 20개 테스트는 단일/이중 규칙 위주. 한 mod에 여러 규칙이 동시 트리거되는 케이스(예: C-02 + C-06 동시 — Lys 아닌 position 0)나 same-rule 다중 인스턴스(같은 K4에 fatty 2개)는 미검증. 무해할 가능성 높으나 명시 권장.
6. **소문자→대문자 자동 변환**: `sequence.upper()`는 정상. 다만 modification dict의 키(`"mod_type"`)에 대소문자 변형(`"Mod_Type"`, `"fatty_Acid"`)이 들어오는 케이스는 검증 안 됨 → 스키마 정규화 책임이 본 체커인지 별도 validator인지 명시 필요.

---

## 결론

C-01 ~ C-06 화학 근거는 모두 1차 문헌으로 뒷받침되며 SST-14 도메인에서 기능적으로 의미 있음. 단, **C-04 severity 재검토**와 **C-07 ~ C-10 추가 도입**이 다음 iteration의 우선순위. 본 Phase 1 산출물은 *CONDITIONAL PASS*로 통과시키되, Phase 3에 위 사항 반영 권장.
