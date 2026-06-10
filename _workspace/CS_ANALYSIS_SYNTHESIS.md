# CS 관점 통합 분석 + 의사결정 (2026-06-09)

오케스트레이터(최종 결정권자)가 codex(read-only 코드분석) + 내장 아키텍처 에이전트(cursor-agent 대체)의 보고를 통합.
원본: `_workspace/codex_cs_analysis.md`(+codex_run.log 풀 테이블 F01-F18), `_workspace/arch_cs_analysis.md`.
**cursor-agent 자체는 미인증(로그인 필요)으로 직접 실행 불가 → 내장 에이전트로 대체.**

## 수렴된 핵심 발견 (두 분석 공통, HIGH)
1. **runner.py god-object (~1720 LOC)** [codex F01] — agents+mutation+docking+ranking+report+status+history+viz+validation 전부 소유.
2. **파일 기반 상태 경쟁** [codex F04 / arch] — /tmp flock-JSON이 단일 진실원, 리더는 락 안 함, 다중 라이터가 비원자적 덮어쓰기. 백엔드 재시작 시 도킹 subprocess orphan [codex F05/arch].
3. **실패한 계산이 stub/random 점수로 랭킹에 진입** [codex F08] — 가장 위험. 실패한 PyRosetta가 진짜처럼 보이는 가짜 점수 반환 → 거짓 신뢰. **과학적 타당성 직결.**
4. **API 인증 전무** [codex F11] — run-control/upload 전부 개방.
5. **임계 경로 대부분 mock, 실 통합 스모크 테스트 없음** [codex F16].

## 아키텍처 수준
6. **GPU/CPU 비대칭** [arch] — H100 4장이 LLM에만, 도킹은 CPU-bound(~4min/cand)가 진짜 병목. 100s 후보엔 job-queue/분산 도킹 필요.
7. **단일 실험 글로벌 락** [arch/F05] — 멀티유저·uvicorn workers>1 불가.
8. **sys.path 이름충돌 취약성** [arch/F14] — 최상위·중첩 동명패키지(pyrosetta_flow/scripts), append 순서 의존(주석에만 문서화). editable install로 견고화 권장.
9. **스키마 3중 수기 미러링** [arch] — emitter dict / pydantic / TS, codegen 없어 drift 위험.

## 중간 (codex)
- F03 fail-open vs fail-closed 정책 부재(silent pass), F10 재현성(hash() 시드), F12/F13 입력검증·경로 traversal, F15 deps 락파일, F17 O(n²) clash 루프(check_receptor_structure.py)·과병렬 기본값, F18 LLM provider None이 "no LLM"과 "LLM 실패" 혼동.
- arch quick win: **pyproject.toml testpaths가 archived된 pipelines/ 가리킴**(stale), vLLM 모델 revision 미고정, seq→ddG dedup 캐시.

## 오케스트레이터 의사결정 (FIX vs PEND)

### ✅ FIX 권장 (고가치·저~중위험, 작동 시스템 보존)
- **D1 (F08) 가짜점수 차단 [최우선·과학 타당성]**: 실패한 도킹/스코어는 fail-closed(후보/런 실패 처리), stub는 dev 명시 opt-in + 랭킹 제외 태그. 저위험.
- **D2 (F04) StatusStore 단일화**: 원자적 write(temp+rename)+읽기 락+스키마 검증을 한 모듈로. 모든 상태 쓰기 경유. 중위험.
- **D3 (F10) 재현성**: hash() 시드→sha256 안정 시드, 후보/trial별 시드 로깅. 저위험.
- **D4 (quick wins)**: pyproject.toml testpaths 수정(archived 경로 제거), vLLM 모델 revision 고정, F18 LLM 타입드 결과+재시도. 저위험.

### ⏸️ PEND 권장 (고비용·구조적·사용자 동의 필요)
- **P1 (F01) runner.py 서비스 분해**: 큰 리팩토링, 작동 시스템 회귀 위험. 전용 작업 권장.
- **P2 (F05) 영속 run store(DB)+stateless API**: 아키텍처 변경. 멀티유저 필요 시.
- **P3 (F11) API 인증**: 로컬 연구도구엔 과잉, 외부노출/멀티유저 시 필요.
- **P4 분산 도킹/job-queue**: 대규모 스크리닝 시 전략적 투자.
- **P5 (F16) 실 통합 스모크 테스트 스위트**: 가치 높으나 공수.
- **P6 스키마 codegen, editable install 패키징**: 중공수.

## 다음
사용자에게 FIX 묶음(D1-D4) 진행 여부 확인 후 진행/pend. 코드 수정은 사용자 확인 전까지 보류.
