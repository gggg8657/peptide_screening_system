# Git / GitHub 추적 정책 (최대 보존)

레포: `https://github.com/AI-scientist4BIO/SST14-M_scr`

## 목표

- **올린다**: 실험·문서·런 산출물·`_workspace` 작업물·`runs_local` (재현·감사용)
- **올리지 않는다**: 비밀, 캐시, `node_modules`, conda env 복제본, **git worktree 복제본**(`.worktrees/`)

## 용량 참고 (로컬 기준, 변동 가능)

| 경로 | 대략 | Git |
|------|------|-----|
| `runs_local/` | ~6GB, 3만+ 파일 | 추적 (단일 76MB CSV는 LFS) |
| `_workspace/` | 대부분 env/캐시 제외 후 추적 | 선택적 제외만 |
| `.worktrees/` | ~24GB | **절대 커밋 금지** |
| `local_models/` | 대형 가중치 | 제외 (스크립트로 재다운로드) |

## 사전 준비 (최초 1회)

```bash
# Git LFS (PDB·대형 CSV)
git lfs install
git lfs track "*.pdb" "*.cif" "runs_local/gpu_monitor_silob.csv"
git add .gitattributes
```

## 단계별 스테이징 (한 번에 add 하지 말 것)

```bash
cd /path/to/SST14-M_scr
git fetch origin

# 1) 문서·릴리즈 노트
git add _workspace/release/*.md docs/ _workspace/README.md

# 2) 로컬 파이프라인 런 (가장 큼)
git add runs_local/

# 3) _workspace (node_modules / .conda_env 는 ignore)
git add _workspace/

# 4) 루트 runs (있다면)
git add runs/ 2>/dev/null || true

# 5) 그 외 추적 대상
git add AgenticAI4SCIENCE_pyrosetta_track/ pipeline_local/ tools/harness-adaptation/

git status
```

커밋·푸시는 본인 확인 후:

```bash
git commit -m "chore: broaden tracked artifacts (runs_local, workspace, LFS)"
git push -u origin HEAD
```

## 여전히 제외 (보안·재현 불가)

- `.env`, `*.key`, `config/secret_key`, `molmim.key`, `ngc.key`
- `.cursor/`, `config/codex.sqlite3*`, `config/cache/`
- `**/node_modules/`, `**/.conda_env/`, `local_models/`
- `.worktrees/`, `.codex/`

## GitHub 한도

- 단일 파일 **100MB 초과** → push 거부 → LFS 또는 제외
- **50MB~100MB** → 경고; `runs_local/gpu_monitor_silob.csv`는 LFS 대상

## Obsidian

- `.obsidian/`은 기본 제외(머신별). 팀 공유 설정까지 올리려면 `.gitignore`에서 해당 줄 제거 후 커밋.
