# 실험 02: FoldMason 구조 기반 MSA

## 목적

AlphaFold3에서 예측한 다중 모델(model 0, 1, 2)을 FoldMason으로 구조 정렬하여:
1. 모델 간 구조적 일관성(lDDT) 평가
2. 구조 기반 MSA 생성
3. 가이드 트리(Newick) 생성

## 환경

- **conda env**: `bio-tools`
- **FoldMason**: v4.dd3c235 (conda-forge / bioconda)
- **OS**: Ubuntu 22.04 (WSL2)

## 실행 명령어

```bash
conda activate bio-tools

foldmason easy-msa \
  "data/fold_test1/fold_test1_model_0.pdb" \
  "data/fold_test1/fold_test1_model_1.pdb" \
  "data/fold_test1/fold_test1_model_2.pdb" \
  results/foldmason/result_foldmason \
  /tmp/foldmason_test \
  --report-mode 1
```

### 파라미터 설명

| 파라미터 | 값 | 설명 |
|----------|-----|------|
| 입력 | model_0.pdb, model_1.pdb, model_2.pdb | AlphaFold 예측 모델 3개 |
| 출력 prefix | `results/foldmason/result_foldmason` | 결과 파일 prefix |
| tmpDir | `/tmp/foldmason_test` | 임시 디렉토리 |
| `--report-mode` | `1` | HTML 리포트 생성 |

## 결과

### 요약 지표

- **Average MSA lDDT**: **0.664**

### 출력 파일

| 파일 | 크기 | 설명 |
|------|------|------|
| `result_foldmason_aa.fa` | 2.3 KB | 아미노산 기반 MSA (FASTA) |
| `result_foldmason_3di.fa` | 2.3 KB | 3Di 알파벳 기반 MSA (FASTA) |
| `result_foldmason.nw` | 136 B | 가이드 트리 (Newick 형식) |
| `result_foldmason.html` | 5.0 MB | 대화형 MSA 시각화 (브라우저로 열기) |

### lDDT 해석

- 0.664는 세 모델 간 구조가 어느 정도 일관성이 있으나, 일부 영역에서 차이가 있음을 의미한다.
- lDDT > 0.7: 높은 신뢰도 / 0.5~0.7: 중간 / < 0.5: 낮은 신뢰도
- 후속으로 `foldmason msa2lddt`를 사용하면 잔기별 lDDT를 추출할 수 있다.

## HTML 리포트 확인 방법

```bash
# WSL에서 브라우저 열기
wslview results/foldmason/result_foldmason.html

# 또는 Windows에서 직접 열기
start results/foldmason/result_foldmason.html
```

## 특수 사항

- FoldMason은 입력으로 PDB 또는 mmCIF를 지원. 여기서는 PDB 사용.
- `--report-mode 1`이 아닌 `0`(기본)이면 HTML을 생성하지 않음.
- 5개 모델 전체를 넣어도 되지만, 테스트 목적으로 3개만 사용.
- 대규모(수천 구조) 실행 시 `--threads` 옵션으로 병렬화 가능.
