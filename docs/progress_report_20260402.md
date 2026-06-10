# 2026-04-02 진행 보고서

## 1. 오늘 완료된 작업

### A-03 해결: SSTR1/3/4/5 실험 구조 CIF 경로 등록 ✅

**커밋**: `ec4982f` — "feat: SSTR1/3/4/5 실험 구조 CIF 경로 등록 (A-03 해결)"

**변경 내용** (`AG_src/config/pipeline_config.yaml`):
- `off_target_receptors` pdb_source: `"alphafold"` → `"local"`
- local_path 등록 (실험 구조 CIF, `data/somatostatin_receptor/`):

| 서브타입 | UniProt | PDB ID | 파일 |
|---------|---------|--------|------|
| SSTR1 | P30872 | 9IK8 | SSTR1_9IK8.cif |
| SSTR3 | P32745 | 8XIR | SSTR3_8XIR.cif |
| SSTR4 | P31391 | 7XMT | SSTR4_7XMT.cif |
| SSTR5 | P35346 | 8ZBJ | SSTR5_8ZBJ.cif |

**의미**: AlphaFold API 동적 다운로드 불필요 → 네트워크 의존성 제거. 즉시 selectivity 도킹 실행 가능 상태.

---

### 문서 최신화 ✅

A-03 완료 반영, 4개 파일 업데이트:

| 파일 | 변경 내용 |
|------|---------|
| `meet_log.md` | A-03 ⚠️→✅, 대응 요약 ✅7/⚠️1/⏸️2 갱신 |
| `docs/action_items_tracker.md` | M1-5·M2-11 ✅, 회의록 완료율 52%→58% |
| `docs/reports/action_response_report.md` | A-03 요약·현재단계·한줄요약 ✅ 반영 |
| `ai4sci-kaeri/docs/reports/system_overview_for_biologists.md` | A-03 아이콘 ⏸️→✅, Appendix C 현황 업데이트 |

---

## 2. 현재 액션 아이템 상태 (2026-04-02 기준)

```
✅ 완료/대체  7건  A-01, A-03, A-04, A-05, A-08, A-09, A-10
⚠️ 진행 중   1건  A-02 (pepADMET 연동 중)
⏸️ RI팀 담당  2건  A-06, A-07
```

---

## 3. 미완료 항목 (다음 세션)

### Selectivity 파이프라인 실행 테스트
- SSTR1/3/4/5 CIF 로드 확인 후 `step05b_selectivity.py` 실행
- selectivity margin > 3 kcal/mol 후보 → Cluster B 분류 검증

### pepADMET 추론 파이프라인 완성
- subprocess 호출 수정
- 21개 후보 binary toxicity + 6-class 분류 실행

### UI 점검 + 개선
- 전 패널 동작 확인

---

## 4. Git 커밋 이력 (오늘)

| 커밋 | 내용 |
|------|------|
| `ec4982f` | feat: SSTR1/3/4/5 실험 구조 CIF 경로 등록 (A-03 해결) |

---

## 5. 다음 세션 시작 시 할 일

1. `source ~/.zshrc` (환경변수 로드)
2. Backend 시작: `conda activate bio-tools && python -m pipeline_local.backend.main &`
3. Frontend 시작: `cd .../frontend && npm run dev &`
4. Selectivity 파이프라인 실행 테스트 (Task #2)
5. pepADMET subprocess 수정 (Task #4)
