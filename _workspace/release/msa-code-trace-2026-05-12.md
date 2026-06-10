# MSA 데이터 흐름 코드 추적 — step05c_boltz_cross.py
**날짜**: 2026-05-12  
**담당**: engineer-backend (Task #2)  
**대상**: `pipeline_local/steps/step05c_boltz_cross.py` (PR #14 머지 후 버전)

---

## §1 `download_alphafold_msa()` 분석

**함수 정의** — L568~618

```python
def download_alphafold_msa(
    uniprot_id: str,
    dest_dir: Path,
    timeout: int = 120,
) -> Optional[Path]:
```

### 입력 / 출력

| 항목 | 상세 |
|------|------|
| 입력 | `uniprot_id` (e.g. "P30874"), `dest_dir` (Path), `timeout=120` (초) |
| 출력 | 다운로드된 `.a3m` 파일의 `Path`; 실패 시 `None` |
| 저장 파일명 | `dest_dir / f"AF-{uniprot_id}-F1-msa.a3m"` (L589) |

### 캐시 로직

L592~594: **이미 존재하고 크기 > 1000 bytes**이면 즉시 재사용, 네트워크 요청 없음.

```python
if dest.exists() and dest.stat().st_size > 1000:
    logger.debug("[Step05c] MSA 캐시 사용: %s", dest)
    return dest
```

### 다운로드 시도 순서 (Fallback 체계)

**시도 1 — 직접 URL** (L596~599):
- URL 패턴 (`_AF_MSA_URL_TEMPLATE`, L121~123):  
  `https://alphafold.ebi.ac.uk/files/msa/AF-{uniprot}-F1-msa_v6.a3m`
- `_download_url(direct_url, dest, timeout)` 호출 → 성공 시 `dest` 반환

**시도 2 — API endpoint 동적 조회** (L602~615):
- URL: `https://alphafold.ebi.ac.uk/api/prediction/{uniprot}` (L124~126)
- `urllib.request.urlopen(api_url, timeout=timeout)` → JSON 파싱
- `api_data[0].get("msaUrl", "")` 에서 실제 MSA URL 추출 (L608)
- 추출된 URL로 다시 `_download_url()` 호출

**Fallback 없음**: 시도 2 실패 시 `logger.error()` 후 `None` 반환 (L617).  
ColabFold MSA 서버 / 로컬 모델 / 다른 DB 경로 없음 — **alphafold.ebi.ac.uk 단일 소스**.

### `_download_url()` 내부 (L621~632)

```python
def _download_url(url: str, dest: Path, timeout: int) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            content = resp.read()
        if len(content) < 100:   # 최소 크기 가드
            return False
        dest.write_bytes(content)
        return True
    except Exception as e:
        logger.debug("[Step05c] download failed %s: %s", url, e)
        return False
```

- `urllib.request` 사용 (표준 라이브러리, requests/httpx 미사용)
- 응답 전체를 메모리에 적재 후 `write_bytes()` (9~10 MB 파일 1회 로드)
- 100 bytes 미만이면 실패 처리 (HTML 오류 페이지 방어)

---

## §2 `predict_pair()` 시그니처 + Boltz CLI 명령 재구성

**함수 정의** — L342~454

```python
def predict_pair(
    seq_id: str,
    sequence: str,
    receptor_name: str,
    receptor_seq: str,
    receptor_msa_path: Path,   # 수용체 a3m 절대 경로
    work_dir: Path,
    boltz_env: str = "boltz",
    cuda_device: int = 3,
    pair_timeout: int = 600,
) -> Optional[float]:
```

### Boltz CLI 명령 (L399~410) — 실제 cmd 리스트

```python
cmd = [
    "conda", "run", "--no-capture-output", "-n", boltz_env,
    "boltz", "predict", str(yaml_path),
    "--out_dir", str(out_dir),
    "--recycling_steps", "1",
    "--sampling_steps", "50",
    "--diffusion_samples", "1",
    "--output_format", "pdb",
    "--override",
    "--num_workers", "0",
    "--no_kernels",
]
```

**실제 확장 예시** (`boltz_env="boltz"`, `cuda_device=3`):
```
conda run --no-capture-output -n boltz \
  boltz predict /path/to/step05c/{pair_id}/{pair_id}.yaml \
  --out_dir /path/to/step05c/{pair_id}/boltz_out \
  --recycling_steps 1 \
  --sampling_steps 50 \
  --diffusion_samples 1 \
  --output_format pdb \
  --override \
  --num_workers 0 \
  --no_kernels
```

**환경 변수** (L412):
```python
env = {**os.environ, "CUDA_VISIBLE_DEVICES": str(cuda_device)}
```
→ `CUDA_VISIBLE_DEVICES=3` (기본값)

---

## §3 MSA가 Boltz에 도달하는 정확한 경로

### a3m → YAML `msa:` 필드

MSA 파일은 **`--msa_dir` 인자로 전달되지 않는다.**  
대신 **Boltz input YAML 파일 내 `msa:` 필드에 절대 경로**로 삽입된다.

#### 펩타이드 self-only a3m 생성 (L377~378)

```python
pep_msa_path = pair_dir / f"{seq_id}_pepmsa.a3m"
pep_msa_path.write_text(f">query\n{sequence}\n", encoding="utf-8")
```
- 내용: 단 2줄 — `>query` + 아미노산 시퀀스
- 이 파일은 on-the-fly 생성, 외부 MSA 검색 없음

#### 생성되는 YAML 구조 (L381~394)

```yaml
version: 1
sequences:
  - protein:
      id: A
      sequence: {candidate_sequence}
      msa: /absolute/path/to/{seq_id}_pepmsa.a3m   # 펩타이드 self-only
  - protein:
      id: B
      sequence: {receptor_sequence}
      msa: /absolute/path/to/AF-{uniprot}-F1-msa.a3m  # AlphaFoldDB MSA
```

코드 (L388, L392):
```python
f"      msa: {pep_msa_path.resolve()}\n"   # L388
f"      msa: {receptor_msa_path.resolve()}\n"  # L392
```

### 전체 데이터 흐름 요약

```
AlphaFoldDB (alphafold.ebi.ac.uk)
    │  download_alphafold_msa()  [L568]
    │  → _download_url()  [L621]
    ▼
af_msa_dir / "AF-{uniprot}-F1-msa.a3m"   (9~10 MB, ~19000 seq)
    │  _ensure_receptor_msa()  [L635]
    │  receptor_msa_paths[rec_name] = msa_path
    │
    └─→  predict_pair(receptor_msa_path=...)  [L264~274]
              │  pair_dir / f"{pair_id}.yaml" 작성 [L381]
              │    protein A (펩타이드): msa: pep_msa_path (self-only)
              │    protein B (수용체):   msa: receptor_msa_path  ← AlphaFoldDB a3m
              ▼
         boltz predict {yaml_path} --out_dir {out_dir} ...
              ▼
         confidence_{pair_id}_model_0.json → iPTM 파싱 [L457]
```

---

## §4 `--no_kernels` 및 `--num_workers 0` 옵션 실제 동작

### `--no_kernels` (L409)

Boltz는 기본적으로 triton 기반 custom CUDA 커널(Flash Attention, custom attention masking 등)을 사용한다.  
`--no_kernels` 플래그를 전달하면 이 커스텀 커널을 비활성화하고 **표준 PyTorch 연산**으로 대체한다.

**효과**:
- **안정성 향상**: triton 커널 컴파일 실패 / GPU 아키텍처 호환 문제 회피
- **속도**: 약간 느릴 수 있으나 subprocess 격리 환경에서 커널 캐시가 없으므로 첫 실행 오버헤드 제거
- **KAERI 내부망 맥락**: JIT 컴파일 환경 불확실성 회피 목적으로 사용 (docstring L12 설명)

### `--num_workers 0` (L408)

PyTorch DataLoader의 worker process 수를 0으로 설정.

**효과**:
- DataLoader가 별도 subprocess를 생성하지 않음 → **메인 프로세스(= 이미 conda subprocess) 내에서 단일 스레드 처리**
- 이미 `subprocess.run()`으로 격리된 환경에서 다시 child process fork 시 발생하는 CUDA context 충돌 방지
- 메모리 공유 문제 및 "daemonic process" 제한 회피

두 옵션 모두 PR #14 docstring(L12~13)의 "우회 전략" 항목에 명시됨:
```
CLI 옵션: --no_kernels --num_workers 0
```

---

## §5 alphafold.ebi.ac.uk URL이 *유일* MSA source인지 확인

### 수용체 MSA — 단일 소스 확인

`download_alphafold_msa()` (L568) 의 fallback 전체를 추적한 결과:

| 시도 | Source | 코드 위치 |
|------|--------|-----------|
| 1 | `https://alphafold.ebi.ac.uk/files/msa/AF-{UP}-F1-msa_v6.a3m` (직접 URL) | L597~599 |
| 2 | `https://alphafold.ebi.ac.uk/api/prediction/{UP}` → `msaUrl` 필드 (동적 URL) | L602~615 |
| 실패 | `None` 반환, 해당 수용체 예측 스킵 | L617 |

**ColabFold MSA 서버(`api.colabfold.com`) 호출 없음** — `--use_msa_server` 플래그가 Boltz CLI 명령에 포함되지 않음 (L399~410 전체 확인).

### 펩타이드 MSA — self-only (외부 의존 없음)

L377~378: `f">query\n{sequence}\n"` — 단일 서열만 포함한 최소 a3m 파일을 코드에서 직접 생성.  
어떤 외부 MSA source도 사용하지 않음.

### `--use_msa_server` 비활성화 확인

Boltz CLI 명령 (L399~410)에 `--use_msa_server` 인자 **없음** → Boltz 내부에서 ColabFold API 호출이 발생하지 않음.  
KAERI 내부망 차단 환경에서 네트워크 오류 없이 동작 가능.

### 결론

| MSA 종류 | Source | 비고 |
|----------|--------|------|
| 수용체 (SSTR1~5) | AlphaFoldDB (alphafold.ebi.ac.uk) — 2-step fallback | 유일 소스 |
| 펩타이드 후보 | 코드 생성 self-only a3m | 외부 의존 없음 |
| ColabFold 서버 | **미사용** | `--use_msa_server` 없음 |
| `--msa_dir` 인자 | **미사용** | YAML msa 필드로 대체 |

alphafold.ebi.ac.uk가 완전히 차단되면 수용체 MSA 준비 실패 → 해당 수용체 예측 스킵 (로그: `"MSA 준비 실패 — 해당 수용체 스킵"`, L209).  
현재 코드에는 로컬 fallback 경로(사전 다운로드 캐시 제외) 없음.
