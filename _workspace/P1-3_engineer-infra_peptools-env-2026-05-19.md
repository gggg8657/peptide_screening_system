# 환경 변경 메모 — peptools env 신설 + 반감기·ADMET wrapper

**작성**: engineer-infra  
**일시**: 2026-05-19  
**작업 ID**: p1-action-items task #3  

---

## 변경 내용

### 1. 신규 conda 환경: `peptools`

```bash
conda create -n peptools python=3.11 -y
conda run -n peptools pip install plifepred2 rdkit biopython requests
```

| 패키지 | 버전 | 비고 |
|--------|------|------|
| Python | 3.11 | |
| plifepred2 | 1.0 | PyPI, peer-review 미검증 |
| scikit-learn | 1.4.2 | bio-tools(1.8.0)와 충돌 → 별도 env |
| rdkit | 2026.3.2 | SMILES 변환 |
| biopython | 1.87 | |
| requests | 2.34.2 | |

**영향 범위**: 없음 (신규 env, 기존 env 미수정)

### 2. 기존 환경 상태

| env | 변경 | 비고 |
|-----|------|------|
| bio-tools | 변경 없음 | scikit-learn 1.8.0 유지 |
| pepadmet | 변경 없음 | modlamp v0.4.3 (Python 3.7) 기존 |
| 기타 모든 env | 변경 없음 | |

---

## 신규 파일

| 파일 | 설명 |
|------|------|
| `pipeline_local/scripts/predict_halflife_pepmsnd.py` | PlifePred2 wrapper (PepMSND stub 포함) |
| `pipeline_local/scripts/predict_admet_pepadmet.py` | modlamp wrapper (pepADMET stub 포함) |
| `pipeline_local/scripts/sequence_to_smiles.py` | D-AA + DOTA SMILES 변환 유틸 |
| `pipeline_local/requirements_peptools.txt` | peptools env 재현 requirements |
| `docs/environments/pepmsnd_pepadmet.md` | 도구별 사용 가이드 |

---

## 웹 도구 접근 상태 확인 결과

| 도구 | URL | HTTP 상태 | 로컬 대안 |
|------|-----|---------|---------|
| PepMSND | http://model.highslab.com/pepmsnd | **403** | plifepred2 (P4) |
| pepADMET | https://pepadmet.ddai.tech/ | **403** | modlamp (P3 디스크립터) |

> **결론**: PepMSND와 pepADMET 모두 이 서버에서 자동화 통합 불가.  
> 수동 브라우저 접속은 가능할 수 있음 (네트워크 정책 차이).

---

## SST14 벤치마크 결과

```
서열: AGCKNFFWKTFTSC (14aa, t½_실측=3분)
```

| 도구 | 출력 | 상태 |
|------|------|------|
| PlifePred2 model_1 | score=3.38 (단위 미명시) | ✅ 성공 |
| pepADMET 웹 | — | ❌ 403 |
| PepMSND 웹 | — | ❌ 403 |
| modlamp MW | 1638.92 Da | ✅ 성공 |
| modlamp Charge pH7 | +2.68 | ✅ 성공 |
| modlamp InstabilityIdx | 30.65 (<40 안정) | ✅ 성공 |

**벤치마크 파일**:
- `runs_local/pepmsnd_benchmark/sst14.json`
- `runs_local/pepadmet_benchmark/sst14.json`

---

## pharmacology_guards.py 업데이트

ENDPOINT_CONFIDENCE에 5개 항목 추가:

| 키 | 등급 | 비고 |
|----|------|------|
| `halflife_plifepred2` | P4 | 설치 확인, 스코어 단위 미명시 |
| `halflife_pepmsnd` | P3 | 웹 403, 이진 분류 |
| `halflife_plifepred` | P2 | 웹 전용 |
| `admet_pepadmet` | P2 | 웹 403, modlamp fallback 명시 |
| `admet_modlamp` | P3 | 물리화학 디스크립터 |

---

## 검증 명령

```bash
# peptools env 설치 확인
conda run -n peptools python -c "import plifepred2, rdkit, Bio; print('OK')"

# SST14 반감기 예측
conda run -n peptools python pipeline_local/scripts/predict_halflife_pepmsnd.py \
    --sequence AGCKNFFWKTFTSC --seq-id SST14

# ADMET 디스크립터
conda run -n pepadmet python pipeline_local/scripts/predict_admet_pepadmet.py \
    --sequence AGCKNFFWKTFTSC --seq-id SST14

# SMILES 변환
conda run -n peptools python pipeline_local/scripts/sequence_to_smiles.py \
    --sequence AGCKNFFWKTFTSC

# pharmacology_guards ENDPOINT_CONFIDENCE 검증
conda run -n bio-tools python -c "
import importlib.util
spec = importlib.util.spec_from_file_location('pg', 'pipeline_local/scripts/pharmacology_guards.py')
mod = importlib.util.module_from_spec(spec)
import sys; sys.modules['pg'] = mod
spec.loader.exec_module(mod)
print('halflife_plifepred2:', mod.ENDPOINT_CONFIDENCE['halflife_plifepred2']['grade'])
print('admet_pepadmet:', mod.ENDPOINT_CONFIDENCE['admet_pepadmet']['grade'])
"
```

---

## 팀원 영향

| 팀원 | 영향 | 내용 |
|------|------|------|
| engineer-backend (be-a04) | 영향 있음 | wrapper 인터페이스 확인 필요 |
| reviewer-pharma | 영향 있음 | ENDPOINT_CONFIDENCE 추가 5건 확인 |
| 기타 | 없음 | 기존 env 미수정 |

---

## 주요 이슈 및 한계

1. **PepMSND 이진 분류**: 연속 t½ 아님 — TPP KPI 직접 적용 불가
2. **PlifePred2 스코어 단위**: 0~1 아닌 3.38 출력 — 로그 변환 추정, 변환 방법 미확인
3. **D-AA 지원 없음**: 모든 로컬 도구 D-AA 미지원 — wet-lab 필수
4. **Octreotide 길이 제한**: 8aa → PlifePred2 12aa 최소 요구로 제외
5. **웹 서비스 403**: 네트워크 정책 또는 User-Agent 필터링 가능 — 브라우저 수동 시도 권장
