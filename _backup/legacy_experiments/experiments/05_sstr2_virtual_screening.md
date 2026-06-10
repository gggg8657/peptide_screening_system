# Experiment 05: SSTR2 Virtual Screening Pipeline

## 목적
Somatostatin Receptor Type 2 (SSTR2)에 대해 Somatostatin보다 더 잘 결합하거나 오래 결합하는 분자를 탐색한다.

## 입력 데이터
- **SSTR2 + Somatostatin 복합체**: AlphaFold3 예측 (`data/fold_test1/fold_test1_model_0.pdb`)
  - Chain A: Somatostatin-14 (`AGCKNFFWKTFTSC`, 14잔기 고리 펩타이드)
  - Chain B: SSTR2 (369잔기, GPCR)
  - ipTM: 0.71, ranking score: 0.83

## Step 0: 바인딩 포켓 분석

Somatostatin(Chain A) 기준 5Å 이내 SSTR2 잔기 **35개** 추출:
- 핵심 접촉 잔기: B122(ASP), B127(PHE), B184(ARG), B197(TRP), B205(TYR), B272(PHE), B294(PHE)
- Trp8(A)이 가장 깊이 삽입 (min 2.91Å, 13개 잔기 접촉)
- Lys9(A)이 가장 가까운 접촉 (min 2.58Å, 9개 잔기 접촉)

## Arm 1: 소분자 스크리닝 (MolMIM + DiffDock)

### 방법
1. 4개 시드 분자(SSTR2 관련 scaffold)에서 MolMIM CMA-ES QED 최적화 → 40개 후보
2. QED 상위 15개 → DiffDock blind docking

### 결과
- MolMIM 후보: 40개 생성
- DiffDock 도킹: **15/15 성공**
- DiffDock confidence 범위: -3.0 ~ -5.5 (높을수록 좋음)

### 최고 QED 후보 (시드별 top)
| 시드 | SMILES | QED |
|------|--------|-----|
| SSTR2_agonist_1 | `Cn1c(=O)c(C(=O)O)c(CC(=O)C(C)(C)C)c2ccccc21` | 0.944 |
| Paltusotine_core | `O=C(COc1cc2ccccc2cc(=O)n1)NC1CCCCC1` | 0.941 |
| Indole_scaffold | `CNC(=O)Cc1c(OC(F)(F)F)ccc2ccccc12` | 0.940 |
| Benzimidazole_hit | `Cc1cccc(C2(NC(=O)c3ccccc3)CCC2)c1` | 0.898 |

## Arm 2: 펩타이드 변이체 분석

### 방법
Somatostatin-14 (`AGCKNFFWKTFTSC`)에 대한 13개 변이체 설계:
- Alanine scanning: F6A, F7A, W8A, K9A, T10A, F11A
- 알려진 유사체: Octreotide core (`FCFWKTCT`)
- 강화 변이체: A1S, K4R, F6Y, K9R, F11Y

### 결과
- 변이체 서열 분석 완료 (13개)
- PyRosetta FlexPepDock은 DB 초기화 이슈로 미수행 → 추후 환경 정비 후 진행

## Arm 3: De Novo 펩타이드 바인더 설계

### 방법 (Baker Lab Pipeline)
1. **RFdiffusion**: SSTR2 바인딩 포켓에 새 펩타이드 백본 설계 (5회 시도)
2. **ProteinMPNN**: 백본 → 최적 아미노산 서열 (4서열/백본)
3. **ESMFold**: 설계 서열의 폴딩 품질 검증 (pLDDT)

### 결과
- RFdiffusion 백본: **4/5 성공** (11-22잔기)
- ProteinMPNN 서열: **16개** 설계
- ESMFold 검증: **16/16 통과** (전체 구조 생성)

### Top De Novo 펩타이드 (pLDDT 순)
| 순위 | 서열 | 길이 | pLDDT | 백본 |
|------|------|------|-------|------|
| 1 | `AALARTIAARFRKELEA` | 17 | 81.4 | bb03 |
| 2 | `AALARTIRADFRAQQQA` | 17 | 81.2 | bb03 |
| 3 | `SGLTGGLLALRRYAELARRYLE` | 22 | 80.4 | bb00 |
| 4 | `AAALGLLLFEAAEQ` | 14 | 79.9 | bb01 |
| 5 | `AGLTGGLAAYREYCRLARRLLE` | 22 | 76.9 | bb00 |
| 6 | `AALWQTILTRFRRQQEE` | 17 | 74.7 | bb03 |
| 7 | `MAALGLLLFEYAEQ` | 14 | 73.6 | bb01 |
| 8 | `TPLTGGEAQLVRYASLARRYLE` | 22 | 73.3 | bb00 |

## 사용 도구 (NVIDIA NIM API)

| 도구 | 엔드포인트 | 용도 |
|------|-----------|------|
| MolMIM | `health.api.nvidia.com/v1/biology/nvidia/molmim` | 소분자 생성/최적화 |
| DiffDock | `health.api.nvidia.com/v1/biology/mit/diffdock` | 분자 도킹 |
| RFdiffusion | `health.api.nvidia.com/v1/biology/ipd/rfdiffusion` | 단백질 바인더 설계 |
| ProteinMPNN | `health.api.nvidia.com/v1/biology/ipd/proteinmpnn` | 역접힘 서열 설계 |
| ESMFold | `health.api.nvidia.com/v1/biology/nvidia/esmfold` | 구조 예측/검증 |

모든 API는 동일한 `nvapi-` 키로 접근. GPU 불필요.

## 다음 단계

1. **AlphaFold3 복합체 검증**: Top de novo 펩타이드 + SSTR2 서열 → AlphaFold3 Server 제출 → ipTM 기준 Somatostatin(0.71) 대비 비교
2. **PyRosetta FlexPepDock**: 환경 정비 후 Arm 2 변이체 도킹 에너지 비교
3. **MD 시뮬레이션**: Residence time 예측을 위한 GROMACS 파이프라인 (추후)
4. **Hit 확장**: 최고 de novo 서열을 시드로 추가 RFdiffusion 라운드

## 파일 구조
```
results/sstr2_docking/
├── binding_pocket.json        # Step 0: 바인딩 포켓 잔기
├── sstr2_receptor.pdb         # Step 0: SSTR2 단독 PDB
├── arm1_smallmol/             # Arm 1: DiffDock 결과
├── arm2_flexpep/              # Arm 2: 변이체 분석
└── arm3_denovo/               # Arm 3: RFdiffusion + ProteinMPNN + ESMFold
    ├── backbone_0X.pdb        # RFdiffusion 백본
    ├── esmfold_bbXX_seqX.pdb  # ESMFold 검증 구조
    └── arm3_final_*.json      # 최종 결과
```
