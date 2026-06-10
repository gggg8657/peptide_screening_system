# Peptide Binder Design: FastDesign vs Independent Mutation + Ab Initio Dock

## 1. 실험 개요

SSTR2(Somatostatin Receptor 2) + SST14(Somatostatin-14) 복합체를 대상으로,
펩타이드 바인더 설계에서 **두 가지 접근법**의 품질과 리소스 효율을 정량 비교한다.
두 접근법 모두 **extended 펩타이드에서 FlexPepDock Ab Initio 도킹**부터 시작한다.

### 대상 시스템

| 구성 요소 | 세부 정보 |
|-----------|----------|
| Receptor  | SSTR2, 369 residues (Chain A after standardization) |
| Peptide   | SST14, 14 residues: `AGCKNFFWKTFTSC` (Chain B after standardization) |
| Disulfide | Cys3 — Cys14 (고정, 변이 불가) |
| Design positions | 서열에서 Cys 자동 탐지하여 제외 (`scripts/peptide_design_utils.py`) |

> **참고**: 원본 AlphaFold3 출력에서는 Chain A = Peptide(14 res), Chain B = Receptor(369 res)이나,
> `SSTR2_SST14_demo.ipynb`의 표준화 단계에서 **A = Receptor, B = Peptide**로 통일된다.
> 비교 노트북은 표준화된 `standardized_relaxed.pdb`를 입력으로 사용한다.

---

## 2. 비교 설계 원칙

### 공정한 비교를 위한 핵심 설계

| 원칙 | 설명 |
|------|------|
| **동일 출발점** | 두 접근법 모두 **분리된 receptor PDB + extended peptide**에서 시작 |
| **동일 도킹** | FlexPepDock Ab Initio (folding + docking from scratch) |
| **동일 후보 수** | 각 3개 (빠른 검증, 평균 시간으로 20개 추정치 계산) |
| **동일 스코어링** | InterfaceAnalyzerMover (dG, dSASA) + stability/PK proxy |
| **동일 모니터링** | ResourceMonitor (CPU, Memory, GPU, Wall-clock time) |

기존 `SSTR2_SST14_demo.ipynb`에서는 Approach A가 AlphaFold3로 이미 결합된 복합체를
"무료"로 사용하여 도킹 비용이 0이었다.
이번 비교에서는 **두 접근법 모두 Ab Initio 도킹 단계를 포함**하여 비교의 공정성을 확보한다.

---

## 3. 두 접근법 상세

### Approach A: Dock-then-Design (결합 후 변이)

```
receptor PDB + 원본 peptide seq (extended 구조)
       │
       ▼
  make_complex_pose()         ← extended peptide → binding site COM 근처 배치
       │
       ▼
  FlexPepDock Ab Initio       ← folding + docking from scratch
       │
       ▼
  FastDesign                  ← 결합 상태에서 펩타이드 서열 변이
  (TaskFactory 제어:             - Receptor: 완전 고정
   receptor 고정,                - Peptide Cys: 고정 (이황화결합 보존)
   Cys 고정,                     - Design positions: 변이 허용
   design pos만 변이)            - 나머지: repack만
       │
       ▼
  InterfaceAnalyzerMover      ← 스코어링 (dG, dSASA)
```

**특징**:
- Ab Initio 도킹으로 진짜 from-scratch binding pose 확보
- FastDesign이 receptor-peptide 상호작용을 **직접 고려**하며 서열 최적화
- 각 후보 생성 시 에너지 최소화 + Monte Carlo 사이클 반복 → **느림**
- 동일 시작점 근처의 local minimum으로 수렴하는 경향 → 서열 다양성 제한

### Approach B: Mutate-then-Dock (변이 후 결합)

```
receptor PDB + 랜덤 변이 peptide seq (extended 구조)
       │
       ▼
  generate_random_mutant()    ← 문자열 수준에서 랜덤 변이 생성
       │                         (design positions에서 Cys 제외 18종 AA 중 선택)
       ▼
  make_complex_pose()         ← extended peptide → binding site COM 근처 배치
       │
       ▼
  FlexPepDock Ab Initio       ← folding + docking from scratch
       │
       ▼
  InterfaceAnalyzerMover      ← 스코어링 (dG, dSASA)
```

**특징**:
- 변이 서열이 receptor context 없이 **순수 랜덤** 생성 (독립적)
- 펩타이드는 **extended 구조**에서 시작 (backbone 정보 없음)
- Ab Initio가 folding + docking을 **from scratch**로 수행
- FastDesign 없이 도킹만으로 결합 평가
- 서열 다양성이 높음 (랜덤 변이이므로 중복 가능성 낮음)

---

## 4. 스코어링 지표

### 결합 품질 (Quality)

| 지표 | 도구 | 해석 |
|------|------|------|
| **dG (REU)** | InterfaceAnalyzerMover | 인터페이스 결합 에너지. **낮을수록** 좋음 |
| **dSASA (Å²)** | InterfaceAnalyzerMover | 매몰 표면적. **높을수록** 좋음 |
| **rank_score** | 계산식 | `(-dG) - 0.5 * cleavage_risk - 1.0 * pk_penalty` |

### 안정성/PK Proxy

| 지표 | 계산 | 해석 |
|------|------|------|
| cleavage_risk | 2.0 * (K+R) + 1.0 * (F+Y+W) | 프로테아제 절단 위험 |
| hydrophobic_fraction | hydrophobic AA / length | 소수성 비율 |
| net_charge_proxy | (K+R+H) - (D+E) | 순 전하 |
| pk_penalty | 5.0 * max(0, hyd_frac - 0.5) + 0.5 * |net_charge| | PK 패널티 |

### 리소스 사용량 (Performance)

| 지표 | 도구 | 설명 |
|------|------|------|
| Wall-clock time | `time.perf_counter()` | 실제 경과 시간 |
| CPU % | `psutil.Process.cpu_percent()` | 프로세스 CPU 사용률 |
| RSS Memory (MB) | `psutil.Process.memory_info().rss` | 물리 메모리 사용량 |
| GPU Utilization % | `pynvml` | GPU 코어 사용률 (해당 시) |
| GPU Memory (MB) | `pynvml` | GPU VRAM 사용량 (해당 시) |

---

## 5. 시각화 출력

노트북 실행 시 `comparison_results/` 디렉토리에 다음 파일이 생성된다:

| 파일명 | 내용 |
|--------|------|
| `comparison_all_candidates.csv` | 전체 후보 데이터 (A + B) |
| `resource_timeseries.csv` | 0.5초 간격 리소스 샘플링 시계열 |
| `quality_comparison.png` | dG / dSASA / Time box plot (3패널) |
| `resource_timeseries.png` | CPU / Memory / GPU 시계열 (4패널) |
| `efficiency_frontier.png` | dG vs Wall Time scatter plot |
| `per_candidate_resources.png` | 후보별 Time / CPU / Memory bar chart |
| `diversity_analysis.png` | Hamming distance 분포 + Unique sequences |

---

## 6. 코드 출처 및 재활용

| 함수/클래스 | 출처 | 비고 |
|------------|------|------|
| `build_task_factory()` | `SSTR2_SST14_demo.ipynb` | Approach A용 |
| `make_complex_pose()` | 신규 구현 (extended peptide + COM positioning) | 양쪽 공유 |
| `flexpepdock_ab_initio()` | 신규 구현 (RosettaScripts XML) | 양쪽 공유 |
| `analyze_interface()` | `SSTR2_SST14_demo.ipynb` | 양쪽 공유 |
| `stability_pk_proxy_scores()` | `SSTR2_SST14_demo.ipynb` | 양쪽 공유 |
| `ResourceMonitor` | 신규 구현 | `psutil` + `pynvml` 기반 context manager |
| `generate_random_mutant()` | 신규 구현 | Approach B용 랜덤 변이 생성 |
| `mutate_and_dock_single()` | 신규 구현 | Approach B 전체 파이프라인 |

---

## 7. 실행 환경

```bash
# 환경 활성화
conda activate bio-tools

# 추가 패키지 설치 (최초 1회)
pip install psutil pynvml

# 또는 environment 파일로 일괄 업데이트
conda env update -f environment-bio-tools.yml

# 실행
cd notebooks/
jupyter notebook comparison_fastdesign_vs_dock.ipynb
```

### 전제 조건
- `standardized_relaxed.pdb`가 `notebooks/` 디렉토리에 존재해야 함
  (→ `SSTR2_SST14_demo.ipynb`의 Section 1-6 실행 결과물)
- PyRosetta 라이선스가 유효해야 함

---

## 8. 검증 체크리스트

### Ab Initio 도킹 방식

- **FlexPepDock Ab Initio**: 펩타이드의 backbone folding + receptor 위의 도킹을 동시에 수행
- `lowres_abinitio=1`: centroid-level fragment insertion으로 펩타이드 backbone 탐색
- `pep_refine=1`: high-resolution refinement로 sidechain + interface 최적화
- Extended peptide의 COM을 원본 binding site COM 근처로 이동 → 탐색 공간 제한

### Approach A 검증

- [x] Ab Initio 도킹 후 docked pose에서 FastDesign 수행
- [x] FastDesign에 TaskFactory 적용: receptor 고정, Cys 고정, design positions만 변이 허용
- [x] 각 후보별 고유 Rosetta random seed (SEED_BASE + k * 100)
- [x] ResourceMonitor로 전체 + 후보별 리소스 측정
- [x] Ab Initio 도킹 시간이 total time에 포함됨

### Approach B 검증

- [x] `generate_random_mutant()`: Cys 위치(3, 13)는 design positions에 없으므로 변이 불가
- [x] `AA_NO_CYS`: 19종 (Cys 제외) — Cys로의 변이 자체를 차단
- [x] `mutate_and_dock_single()`: extended peptide 조립 → Ab Initio Dock → Score
- [x] 중복 서열 방지: `seen_seqs_b` set으로 최대 10회 재시도
- [x] ResourceMonitor로 전체 + 후보별 리소스 측정

### 공통 검증

- [x] Baseline 측정: 원본 서열로 extended assemble + Ab Initio Dock → 기준 dG/dSASA
- [x] 양쪽 모두 동일한 `InterfaceAnalyzerMover` 설정 (jump=1, pack_separated=True)
- [x] 양쪽 모두 동일한 `stability_pk_proxy_scores()` 적용
- [x] 양쪽 모두 동일한 `rank_score` 공식: `(-dG) - 0.5 * cleavage_risk - 1.0 * pk_penalty`

---

## 9. 예상 결과 및 가설

| 차원 | Approach A (Dock→Design) | Approach B (Mutate→Dock) |
|------|--------------------------|--------------------------|
| **속도** | 매우 느림 (Ab Initio + FastDesign) | 느림 (Ab Initio per candidate) |
| **dG 품질** | 우수 (receptor context 고려 설계) | 불확실 (blind mutation) |
| **서열 다양성** | 낮음 (local minimum 수렴) | 높음 (랜덤 변이) |
| **메모리** | 높음 (FastDesign 내부 상태) | 중간 |
| **확장성** | Ab Initio 1회 + FastDesign N회 | Ab Initio N회 |

### 핵심 가설
> 두 접근법 모두 Ab Initio 도킹을 사용하므로 도킹 비용은 동일하다.
> Approach A는 추가로 FastDesign이 필요하므로 **항상 더 느리다**.
> 핵심 질문: FastDesign의 추가 시간이 **dG 품질 향상으로 정당화**되는가?
> 만약 Approach B의 Top-N 후보 중 Approach A의 평균 dG 이하인 후보가 존재한다면,
> **B로 대량 탐색 → A로 정밀 최적화**하는 2단계 전략이 유효하다.
