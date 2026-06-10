# Publications & Reference Documentation

> PRST_N_FM 프로젝트의 논문, 참고 문서, 기술 보고서 종합 인덱스

---

## 1. Paper Drafts (논문 초안)

### 1.1 최종 제출본 (Published)

| 파일 | 상태 | 비고 |
|------|------|------|
| `paper/KNS_v2.pdf` | **제출 완료** | KNS 2026 춘계학술대회 (제주, 2026-05-07~08) |
| `paper/Design and Operational Verification of an Agentic AI System for SSTR2-Binding Peptide Candidate Screening.pdf` | **제출 완료** | KNS_v2와 동일 내용 (영문 파일명) |
| `paper/Design and Operational Verification of an Agentic AI System for SSTR2-Binding Peptide Candidate Screening.docx` | 편집본 | Word 편집용 |

- **학회**: Transactions of the Korean Nuclear Society Spring Meeting
- **제목**: Design and Operational Verification of an Agentic AI System for SSTR2-Binding Peptide Candidate Screening
- **저자**: Dongju Kim, Soyeon Kim, Yonggyun Yu, Min-Kyu Kim, Ki-Bum Ahn, Ho-Seong Seo*, Yujong Kim*
- **소속**: KAERI (Applied AI Section, Cyclotron Application Research Section)
- **키워드**: Agentic AI, Multi-agent, AI Scientist, Peptide Screening, SSTR2, SST14, Workflow Automation
- **핵심 내용**: 5-Agent 시스템 (Planner, QCRanker, DiversityManager, Critic, Reporter), mutate-dock-QC-critique-report 루프, directional-consistency check, top-3 mean dG 메트릭

### 1.2 초안 이력 (Draft History)

| 파일 | 버전 | 방향 | 상태 |
|------|------|------|------|
| `paper/draft/outline.md` | 초기 아웃라인 | 6-Agent Hybrid + Multi-MCP 개발방법론 | 대체됨 (v1 기반) |
| `paper/draft/paper_v1.md` | v1 | Multi-Agent AI Co-Scientist 전체 (6-Agent, Competing Hypotheses, Multi-MCP) | 대체됨 |
| `paper/draft/paper_v2_ai_scientist_focus_draft.md` | v2 | AI Scientist 수행 성능 중심 (Plan-Critique-Explore 프레임) | 대체됨 |
| `paper/draft/paper_v3_structure_only.md` | v3 | 구조만 확정, 수치 추후 입력 | 대체됨 |
| `paper/draft/outline_for_review_EN.md` | 리뷰용 | 영문 방향성 검토 요청서 | 참고용 |
| `paper/draft/outline_for_review_KR.md` | 리뷰용 | 한국어 방향성 검토 요청서 | 참고용 |

**초안 진화 경로**: outline -> v1 (6-Agent 풀스펙) -> v2 (AI Scientist 성능 중심) -> v3 (구조 확정) -> KNS_v2 (최종 5-Agent 간결화)

---

## 2. Internal Reports (내부 기술 보고서)

### 2.1 Markdown 보고서

| 파일 | 작성일 | 내용 |
|------|--------|------|
| `paper/materials/comprehensive_report.md` | 2026-02-18 | 종합 기술 보고서 - 아키텍처 검증, LLM 선정 (Qwen 2.5 7B), P0/P1 버그 수정 6건, 프론트엔드 대시보드 |
| `paper/materials/pipeline_validation_report.md` | 2026-02-18 | AG_src 아키텍처 검증 보고서 - Competing Hypotheses Pattern, 4-Agent 팀 분석, Option C (6-Agent Hybrid) 채택 근거 |

### 2.2 프레젠테이션 자료 (NotebookLM 생성)

| 파일 | 내용 |
|------|------|
| `paper/materials/SSTR2_AI_Pipeline_and_LLM_Selection.pdf` | AI 파이프라인 최적화 및 LLM 선정 보고서 슬라이드 (아키텍처, 벤치마크, P0/P1 수정) |
| `paper/materials/SSTR2_Hybrid_Agentic_Design.pdf` | Hybrid Agentic System 설계 슬라이드 (Self-Design Loop, 6-Agent 구조, Option C 검증) |

---

## 3. Reference Documentation (참고 문서)

### 3.1 Tool References (도구 레퍼런스)

| 파일 | 도구 | 설명 |
|------|------|------|
| `docs/BIONEMO_REFERENCE.md` | NVIDIA BioNeMo / NIM API | MolMIM, DiffDock, RFdiffusion, ProteinMPNN, ESMFold, OpenFold3, Boltz-2 등 16개 모델 API 가이드 |
| `docs/PYROSETTA_REFERENCE.md` | PyRosetta | Scoring, Relax, Docking, Design, ddG, Loop Modeling, Cyclic Peptide 등 17개 섹션 |
| `docs/PYMOL_REFERENCE.md` | PyMOL 3.1.0 | Representations, Selections, Scripting, 렌더링 등 14개 섹션 |
| `docs/FOLDMASON_REFERENCE.md` | FoldMason | 대규모 다중 구조 정렬(MSA), easy-msa 워크플로우, lDDT 품질 지표 |
| `docs/PDB_VISUALIZATION_TOOLS.md` | 시각화 도구 비교 | Mol*, PyMOL, NGL Viewer, 3Dmol.js, Jmol/JSmol 비교 분석 |

### 3.2 Architecture & Environment (아키텍처/환경)

| 파일 | 설명 |
|------|------|
| `docs/SYSTEM_ARCHITECTURE.md` | Dual-Silo (A+B) 전체 아키텍처, BioNeMo 클라이언트 추상화, YAML 기반 오케스트레이션 |
| `docs/ENV_COMPATIBILITY.md` | PyRosetta + Biopython + AutoDock-GPU 환경 호환성, AlphaFold3 분리, MCP 서버 구성 |
| `ENVIRONMENT.md` (루트) | bio-tools conda 환경 스펙, Python 3.10~3.12, NVIDIA NIM API 설정, 실행/테스트 커맨드 |
| `pipeline_orchestration.mermaid` (루트) | 파이프라인 오케스트레이션 플로우차트 (PDB 입력 -> MCP -> FoldMason -> LLM 의사결정 -> Evidence Package) |

---

## 4. Scientific Comparisons (과학적 비교 분석)

| 파일 | 비교 대상 | 핵심 내용 |
|------|----------|----------|
| `docs/pipeline_comparison.md` | 4개 파이프라인 비교 | FastDesign vs RFdiffusion+MPNN vs MolMIM+DiffDock vs FlexPepDock 변이체 분석 |
| `docs/comparison_fastdesign_vs_dock.md` | FastDesign vs Independent Mutation + Ab Initio Dock | 동일 출발점(extended peptide) 기반 공정 비교, 리소스 효율 분석 |
| `docs/sstr2_demo_version_comparison.md` | 데모 노트북 v1 vs v2 | SSTR2_SST14_demo (생성) vs presentation_sstr2_pipeline (시각화) 비교 |
| `docs/sstr2_scientific_comparison.md` | v1 vs v2 (과학적 관점) | SSTR2 타겟 생물학, 약효단 분석, 방사성의약품 적합성 관점 비교 |

---

## 5. Diagram Assets (다이어그램)

| 파일 | 형식 | 내용 |
|------|------|------|
| `docs/pipeline_orchestration.svg` | SVG | 파이프라인 오케스트레이션 다이어그램 |
| `pipeline_orchestration.mermaid` | Mermaid | 동일 다이어그램 소스 (flowchart TD) |

---

## 6. 논문 핵심 참고문헌 (Key References)

KNS_v2 논문에서 인용된 주요 문헌:

1. Watson et al. "De novo design of protein structure and function with RFdiffusion" - *Nature*, 2023
2. Dauparas et al. "Robust deep learning-based protein sequence design" - *Science*, 2022
3. Corso et al. "DiffDock: Diffusion Steps, Twists, and Turns for Molecular Docking" - *ICLR*, 2023
4. Lin et al. "Evolutionary-scale prediction of atomic-level protein structure with a language model" - *Science*, 2023
5. Leaver-Fay et al. "Rosetta3: An Object-Oriented Software Suite" - *Methods in Enzymology*, 2011
6. Gottwalt et al. "AI Co-Scientist" - Google DeepMind, 2024
7. Qwen Team. "Qwen 2.5 Technical Report" - 2024
8. Gilchrist et al. "FoldMason: Multiple Protein Structure Alignment at Scale" - *Science*, 2026
