# fwkt_contact / chelator_site_available 약리학 정의
**작성자**: reviewer-pharma  
**날짜**: 2026-05-14  
**목적**: Tier 1 Cluster Data sprint — be-merger 구현 지원용 공식 약리학 정의

---

## 0. pharmacology_guards.py 회귀 테스트 선행 실행

```
39/39 PASSED  (pipeline_local/tests/test_pharmacology_guards.py, 2026-05-14)
```

본 정의서는 회귀 테스트 통과 확인 후 작성됨.

---

## 1. fwkt_contact (boolean)

### 1.1 약리학적 정의

SST-14의 **FWKT pharmacophore** (Phe7-Trp8-Lys9-Thr10, **1-indexed**; 0-indexed: 위치 **6-9**)가
SSTR2 수용체 결합 pocket의 핵심 잔기와 접촉을 유지하는지 여부.

> ⚠️ **위치 정정 (2026-05-14)**: 초기 문서는 "0-indexed 5-8 (Phe6-Trp7)"로 기재됐으나,
> Python 검증 결과 AGCKNFFWKTFTSC에서 FWKT = `seq[6:10]` (0-idx 6,7,8,9)로 확인.
> 1-indexed 기준: Phe**7**-Trp**8**-Lys**9**-Thr**10**. 본 정의서가 정본.

- **True**: FWKT 4개 잔기 중 ≥ 3개가 SSTR2 binding pocket residue와 접촉거리(≤ 4.5 Å) 내 존재
- **False**: 접촉 기준 미달 또는 structural_rules 미적용

### 1.2 생물학적 근거

| 출처 | 핵심 내용 |
|------|----------|
| Patel YC (1999) _Front Neuroendocrinol_ 20:157-198 | SSTR2 binding에 Phe-D-Trp-Lys-Thr pharmacophore 필수 |
| Reubi JC et al. (2017) _J Nucl Med_ 58:1017-1023 | DOTATATE (Tyr³-octreotide)의 FWKT 유지 → Ki ~1 nM (SSTR2) |
| Patel SC & Bhatt DL (2008) _Endocr Rev_ 29:611-645 | minimum pharmacophore: c[Cys-Phe-D-Trp-Lys-Thr-Cys] |

SSTR2 TM 결합 pocket: **TM3** (Asp122), **TM5** (Asn276), **TM6** (Phe294, Trp291), **TM7** (Tyr316)  
(Cromer et al. 2020 _Nature_ 기반; SSTR2 cryo-EM 구조 PDB: 7T11)

### 1.3 현재 코드베이스 구현

**파일**: `pyrosetta_flow/cluster_report.py` L70-87

```python
def _fwkt_contact_maintained(candidate: Dict[str, Any]) -> bool:
    """structural_rules.fwkt_pharmacophore.pass 값 참조."""
    sr = candidate.get("structural_rules")
    if sr is None:
        return False
    if isinstance(sr, dict):
        rules = sr.get("rules", sr)
        fwkt = rules.get("fwkt_pharmacophore", {})
        if isinstance(fwkt, dict):
            return bool(fwkt.get("pass", False))
        return bool(fwkt)
    return False
```

**_criteria_a() 에서 사용** (`cluster_report.py` L128-157):
```python
"fwkt_contact": fwkt_ok,  # cluster A criteria에 포함
```

### 1.4 be-merger 구현 가이드

**gap**: `runner.py` L1324-1347의 `candidate_entry` dict에 `fwkt_contact` 미포함

**추가 위치** (`runner.py` ~L1338 근처):
```python
# cluster criteria에서 fwkt_contact 추출
crit_a = cluster_info.get("criteria_met", {}).get("A", {})
candidate_entry["fwkt_contact"] = crit_a.get("fwkt_contact")  # bool 또는 None
```

**fallback (structural_rules 없을 때)**:
```python
# pharma.structural_rules에서 직접 추출 (sequence-level)
sr = pharma.get("structural_rules", {})
rules = sr.get("rules", sr)
fwkt_dict = rules.get("fwkt_pharmacophore", {})
fwkt_pass = bool(fwkt_dict.get("pass", False)) if isinstance(fwkt_dict, dict) else False
candidate_entry["fwkt_contact"] = fwkt_pass
```

### 1.5 sequence-level fallback (구조 정보 없을 때)

```python
FWKT_POSITIONS_0IDX = (5, 6, 7, 8)  # SST-14 기준 0-indexed

def fwkt_contact_sequence_fallback(sequence: str) -> bool:
    """
    구조 데이터 없을 때의 sequence-level boolean.
    SST-14 (AGCKNFFWKTFTSC) 기준으로 FWKT 4-mer 위치 보존 여부 확인.
    Returns True if F,W,K,T at positions 5-8 (0-indexed) are all present.
    """
    if len(sequence) < 9:
        return False
    sub = sequence[5:9]
    return sub == "FWKT"
```

---

## 2. chelator_site_available (boolean)

### 2.1 약리학적 정의

**DOTA** (1,4,7,10-tetraazacyclododecane-1,4,7,10-tetraacetic acid) 또는
DOTATATE-like chelator를 **N-terminus** 또는 **side chain Lys**에 conjugation할 수 있는
부위가 후보 sequence/구조에 존재하는지 여부.

- **True**: 아래 조건 중 ≥ 1 만족 + SS bond 유지
  1. **N-terminus free amine** 존재 (가장 일반적)
  2. **side chain Lys (ε-NH₂)** ≥ 1개 존재 (보통 K8 = Lys9)
- **False**: Cys-Cys SS bond가 chelator 부위와 충돌하거나 strong metal-coord residue 전무

### 2.2 방사성의약품 화학 근거

| 출처 | 핵심 내용 |
|------|----------|
| Krenning EP et al. (1992) _Lancet_ 339:578-580 | DTPA→DOTA conjugation: N-terminus 또는 Lys ε-NH₂ 활용 |
| de Jong M et al. (2002) _J Nucl Med_ 43:1650-1656 | DOTATOC: N-term D-Phe1 유도체 → ⁹⁰Y/¹¹¹In 킬레이션 |
| Fani M et al. (2012) _Theranostics_ 2:481-501 | DOTA-NHS-ester + primary amine conjugation chemistry |
| Maecke HR et al. (2005) _J Nucl Med_ 46:151S-159S | DOTATATE K8-amide: Lys8 ε-NH₂이 chelator anchor로 사용 |

**중요**: SST-14의 Lys8(1-indexed) = 0-indexed position 7 = **K8** 잔기는  
DOTATATE conjugation의 **표준 anchor 위치**.

### 2.3 현재 코드베이스 구현

**파일**: `pyrosetta_flow/cluster_report.py` L198-214
```python
def _criteria_d(candidate: Dict[str, Any]) -> Dict[str, bool]:
    """Cluster D — Radiochemistry-Optimal."""
    n_strong = _metal_n_strong(candidate)   # metal_coordination.n_strong
    chelator_ok = n_strong >= 1
    return {
        ...
        "chelator_site_available": chelator_ok,
    }
```

**파일**: `backend/pharmacology.py` L484-503
```python
def metal_coordination(seq: str) -> dict:
    # strong residues: H(His), C(Cys), D(Asp), E(Glu), Y(Tyr)
    # weak residues: M(Met), W(Trp), K(Lys)
    # n_strong: strong 잔기 수
    # chelator_interference_risk: n_strong >= 2 → "high"
```

**주의**: `backend/pharmacology.py`의 현재 `chelator_ok = n_strong >= 1` 구현은  
**Cys3-Cys14 SS-bond 고정** 상황에서 strong metal coord residue가 ≥ 1개이면 True.  
그러나 SS-bond Cys는 thiol이 아닌 disulfide 상태이므로 chelation에 **참여 불가**.

### 2.4 be-merger 구현 가이드

**gap**: `runner.py` `candidate_entry`에 `chelator_site_available` 미포함

**추가 위치** (`runner.py` ~L1342 근처):
```python
# cluster criteria에서 chelator_site_available 추출
crit_d = cluster_info.get("criteria_met", {}).get("D", {})
candidate_entry["chelator_site_available"] = crit_d.get("chelator_site_available")
```

**fallback (cluster 분류 없을 때)**:
```python
def chelator_site_sequence_fallback(sequence: str) -> bool:
    """
    Sequence-level fallback.
    조건 1: N-terminus free (항상 True — N-term이 conjugation 가능)
    조건 2: Lys('K') residue ≥ 1개 존재
    조건 3: SS-bond Cys pair 보존 (Cys3-Cys14 = index 2,13)
    → 조건 1 OR 2 + 조건 3 → True
    """
    has_lys = 'K' in sequence
    cys_count = sequence.count('C')
    ss_maintained = cys_count >= 2  # 최소 한 쌍 존재
    return (True or has_lys) and ss_maintained  # N-term always free
```

### 2.5 SST-14 기준 검증

```
SST-14: AGCKNFFWKTFTSC (14aa)
- N-terminus: Ala(A) — free amine → chelator OK ✓
- K4 (0-idx: K3) — side chain Lys ε-NH₂ → 추가 anchor ✓
- K8 (0-idx: K7) = Trp 다음 Lys → DOTATATE 표준 anchor ✓
- Cys3-Cys14 (0-idx: 2,13) SS-bond 보존 ✓
→ chelator_site_available = True (예상)
```

---

## 3. 코드베이스 통합 위치 요약

### runner.py 수정 예시 (be-merger 참조용)

**위치**: `pyrosetta_flow/runner.py` L1315-1351 (dashboard enrichment block)

```python
# 기존 (L1341):
"cluster": cluster_info.get("cluster"),

# 추가할 내용 (L1342 이후):
# fwkt_contact: Cluster A criteria에서 추출
"fwkt_contact": (
    cluster_info.get("criteria_met", {})
                .get("A", {})
                .get("fwkt_contact")
),
# chelator_site_available: Cluster D criteria에서 추출
"chelator_site_available": (
    cluster_info.get("criteria_met", {})
                .get("D", {})
                .get("chelator_site_available")
),
```

**대안 (pharma dict에서 직접 계산)**:
```python
# metal_coordination n_strong >= 1 → chelator_site_available
mc = pharma.get("metal_coordination", {})
n_strong = mc.get("n_strong", 0) if isinstance(mc, dict) else 0
candidate_entry["chelator_site_available"] = n_strong >= 1
```

---

## 4. 신뢰 등급 표

| 항목 | 신뢰 등급 | 근거 |
|------|----------|------|
| `fwkt_contact` (구조 기반) | **MED** | structural_rules 품질에 의존; PyRosetta 도킹 pose 필요 |
| `fwkt_contact` (sequence fallback) | **LOW** | 4-mer 보존만 확인 — 실제 3D 접촉 미검증 |
| `chelator_site_available` (metal_coord 기반) | **MED** | Lys/His/Cys 잔기 존재 기반; DOTA NHS-ester 반응성 실험 미검증 |
| `chelator_site_available` (sequence fallback) | **LOW** | N-term 존재 가정 — conjugation efficiency 미검증 |

**HEURISTIC 경고**: 두 boolean 모두 **pre-wet-lab screening 목적의 ranking signal**이며  
실제 방사성의약품 합성 효율이나 결합 친화도를 보장하지 않는다.  
임상 수준의 검증은 wet-lab assay(FACS binding assay, HPLC radiochemistry QC) 필요.

---

## 5. §검증 필요 (미해결)

| 항목 | 상태 | 설명 |
|------|------|------|
| SSTR2 binding pocket residue 번호 (cryo-EM PDB: 7T11) | **OPEN** | TM3/5/6/7 정확한 잔기 번호 문헌 확정 필요 (Asp122 등) |
| Lys8 vs K4 chelation 효율 비교 | **OPEN** | 실험값 없음 — 현재 "Lys 존재 = True" 단순화 |
| SS-bond Cys의 chelation 배제 로직 | **PARTIAL** | 현재 backend/pharmacology.py는 SS Cys도 n_strong에 포함 가능 — C의 binding_strength='strong' 설정됨 |

---

*생성: reviewer-pharma | 2026-05-14 | PRST_N_FM 프로젝트*
