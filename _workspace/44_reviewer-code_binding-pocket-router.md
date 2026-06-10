# 코드 리뷰 보고서 — binding_pocket CRUD Router (task #1)

**파일**: `backend/routers/binding_pocket.py` + `backend/tests/test_binding_pocket_router.py`  
**리뷰어**: reviewer-code  
**날짜**: 2026-05-19  
**트리거**: team-lead 요청 (uvicorn 재기동 대기 중 선행 가능 작업)

---

## 1. 요약

| 항목 | 결과 |
|------|------|
| 전체 판정 | **CONDITIONAL PASS** |
| 12개 신규 테스트 | 12/12 PASS ✅ |
| 기능 완성도 | CRUD 4 endpoint 정상 구현 |
| Critical 이슈 | 없음 |
| High 이슈 | 2건 (race condition, box_size 유효성) |
| Medium 이슈 | 4건 |
| Low 이슈 | 3건 |

**조건**: High #1 (race condition) 은 현재 단일 사용자·단일 프로세스 운영 환경에서는 실질 위험이 낮으나, 향후 multi-worker uvicorn 전환 전 반드시 수정 필요.

---

## 2. Critical 이슈

없음. 기본 CRUD 동작 정상, 테스트 격리 완전.

---

## 3. High 이슈

### H-1. `_default.json` 백업의 TOCTOU Race Condition
**[HIGH] — 신뢰등급: HIGH (코드 직접 확인)**  
**파일**: `binding_pocket.py:159-165`

```python
# 현재 코드 (비원자적)
if main_path.exists() and not default_path.exists():       # ← check
    existing = json.loads(main_path.read_text(encoding="utf-8"))
    if existing.get("source") != "user_override":
        default_path.write_text(...)                        # ← use (write)
```

**위험**: 두 개의 동시 PUT 요청이 모두 `not default_path.exists()`를 통과하면, 두 번째 write가 첫 번째 백업을 덮어씀. 두 번째 요청 시점에서 `main_path`는 이미 첫 번째 PUT의 `user_override` 데이터이므로, 실제 원본(original) 대신 `user_override`가 `_default.json`으로 저장됨 → **원본 데이터 유실**.

**현재 위험도**: 단일 워커 uvicorn이고 사용자가 1명이므로 실질 발생 가능성 낮음.  
**미래 위험도**: multi-worker (`--workers 4`) 전환 시 즉시 발현.

**권장 수정**:
```python
# 원자적 백업 — 파일이 없을 때만 생성 (O_EXCL 의미)
import os

if main_path.exists() and not default_path.exists():
    existing = json.loads(main_path.read_text(encoding="utf-8"))
    if existing.get("source") != "user_override":
        try:
            # O_CREAT|O_EXCL: 파일이 없을 때만 생성, 이미 있으면 FileExistsError
            fd = os.open(str(default_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(json.dumps(existing, ensure_ascii=False, indent=2))
        except FileExistsError:
            pass  # 다른 요청이 이미 백업 생성 완료
```

---

### H-2. `box_size` 검증 미흡 — 잘못된 키 허용
**[HIGH] — 신뢰등급: HIGH (실험으로 확인)**  
**파일**: `binding_pocket.py:60`

```python
box_size: Optional[Dict[str, Any]] = None  # 현재: 임의 Dict 허용
```

**실험 결과**:
```bash
# 잘못된 키 {"wrong_key": 99} → 200 OK (저장됨)
box_size bad keys -> 200
```

`size_x/size_y/size_z` 없이 임의 딕셔너리가 그대로 저장됨. 이 데이터가 GNINA/Boltz 도킹 파라미터로 사용될 경우 KeyError 또는 묵시적 0-box로 도킹 실패.

**권장 수정**:
```python
from pydantic import BaseModel, Field as PydanticField, model_validator

class BoxSize(BaseModel):
    size_x: float = PydanticField(..., gt=0)
    size_y: float = PydanticField(..., gt=0)
    size_z: float = PydanticField(..., gt=0)

class BindingPocketConfig(BaseModel):
    ...
    box_size: Optional[BoxSize] = None
```

---

## 4. Medium 이슈

### M-1. `residue_ids` 음수/0 값 허용 (PUT 경로)
**[MEDIUM] — 신뢰등급: HIGH**  
**파일**: `binding_pocket.py:59`

```python
residue_ids: List[int] = Field(default_factory=list)  # 음수 허용됨
```

PUT에서는 `extract_pocket_center`가 호출되지 않으므로 음수 residue_id가 검증 없이 저장됨. 다운스트림 도킹 단계에서 조용히 오류 발생 가능.

**권장**:
```python
residue_ids: List[int] = Field(default_factory=list)

@field_validator("residue_ids")
@classmethod
def validate_residue_ids(cls, v: List[int]) -> List[int]:
    if any(rid <= 0 for rid in v):
        raise ValueError("residue_ids must be positive integers")
    return v
```

---

### M-2. TC12 mock 전략 복잡성 + 죽은 코드
**[MEDIUM] — 신뢰등급: HIGH**  
**파일**: `test_binding_pocket_router.py:309-332`

```python
mock_fn = MagicMock(return_value=MOCK_EXTRACT_RESULT)

with patch(
    "backend.routers.binding_pocket.extract_pocket_center",
    mock_fn,
    create=True,          # ← create=True: 모듈에 속성 없음을 시인
):
    import backend.routers.binding_pocket as bp_mod
    original_import = bp_mod.__builtins__  # ← 완전한 죽은 코드, noqa F841

    with patch.dict(
        "sys.modules",
        {"pipeline_local.scripts.extract_binding_pocket": MagicMock(...)},
    ):
        resp = client.post(...)
```

**문제**:
1. 외부 `patch(..., create=True)` — router의 lazy import (`from ... import` inside function)에는 작용하지 않음. 실제로 동작하는 것은 내부 `patch.dict(sys.modules, ...)`
2. `original_import = bp_mod.__builtins__` — 완전한 dead code. `__builtins__` 는 mock과 무관하며, 변수도 사용되지 않음 (`# noqa: F841`)

**권장**: 외부 `patch()` 블록 제거, `patch.dict(sys.modules, ...)` 단독 사용으로 단순화:
```python
def test_extract_pocket_200_mock(client, tmp_data_dir):
    fake_pdb = tmp_data_dir / "SSTR2_7XNA.pdb"
    fake_pdb.write_text("FAKE PDB CONTENT\n", encoding="utf-8")
    mock_module = MagicMock(extract_pocket_center=MagicMock(return_value=MOCK_EXTRACT_RESULT))

    with patch.dict("sys.modules", {"pipeline_local.scripts.extract_binding_pocket": mock_module}):
        resp = client.post("/api/binding_pocket/sstr2/extract", json={"residue_ids": [208, 209, 272]})

    assert resp.status_code == 200
    ...
```

---

### M-3. 두 번째 PUT 시 `_default.json` 불덮어쓰기 — 미검증
**[MEDIUM] — 신뢰등급: MED (코드 로직 추론)**  
**파일**: `test_binding_pocket_router.py` (TC07 부재)

현재 TC07은 "첫 번째 PUT이 `_default.json`을 생성"만 검증. 두 번째 PUT 시 기존 `_default.json`을 덮어쓰지 않는 코드 경로 (`not default_path.exists()` 조건)가 테스트되지 않음.

**권장**: TC07-b 추가:
```python
def test_put_second_override_preserves_default(client, tmp_data_dir, populated_sstr2):
    """두 번째 PUT은 _default.json을 덮어쓰지 않아야 한다."""
    # 1차 PUT → _default.json 생성
    client.put("/api/binding_pocket/sstr2", json=VALID_PUT_BODY)
    default_path = tmp_data_dir / "binding_pocket_SSTR2_default.json"
    first_backup = default_path.read_text()

    # 2차 PUT → _default.json 불변 확인
    body2 = dict(VALID_PUT_BODY, center_x=99.0)
    client.put("/api/binding_pocket/sstr2", json=body2)
    assert default_path.read_text() == first_backup  # 원본 보존
```

---

### M-4. `radius_angstrom` 하한 경계값(4.9) 미테스트
**[MEDIUM] — 신뢰등급: HIGH**  
**파일**: `test_binding_pocket_router.py` (TC06)

TC06은 `radius=50 > 30`만 검증. `radius=4.9 < 5.0` (하한 초과), `radius=30.1 > 30` 상한 경계 테스트 없음.

**실험 결과**: `radius=4.9 → 422` 정상 동작하나, 회귀 방지를 위해 테스트 추가 권장.

---

## 5. Low 이슈

### L-1. `source` 필드 제약 없음
**[LOW] — 신뢰등급: HIGH**  
**파일**: `binding_pocket.py:61`

`source: str = "user_override"` — 임의 문자열 허용. 권장: `Literal["user_override"]`

---

### L-2. sstr1/4/5 수용체 테스트 없음
**[LOW] — 신뢰등급: HIGH**  
**파일**: `test_binding_pocket_router.py`

5개 수용체 중 sstr2(주), sstr3(404 fixture), sstr9(invalid) 만 사용. 수용체명 정규화·파일명 매핑은 공통 로직이므로 parametrize 적용 권장.

---

### L-3. `sys.path.insert` 모듈 레벨 부작용
**[LOW] — 신뢰등급: HIGH**  
**파일**: `binding_pocket.py:32-33`

모듈 임포트 시 `sys.path` 수정. 현재 환경에서 문제 없으나 pytest-xdist 병렬 실행 시 경합 가능. 향후 `importlib` 기반 lazy-import 패턴으로 교체 권장.

---

## 6. 누락된 테스트 케이스 (우선순위 순)

| 우선순위 | 케이스 | 기대 동작 |
|---------|--------|---------|
| **High** | PUT 두 번째 override (TC07-b) | `_default.json` 불변 |
| **High** | PUT `box_size` 잘못된 키 | 422 (현재 200 — 버그) |
| **Medium** | PUT `radius=4.9` | 422 |
| **Medium** | PUT `radius=30.1` | 422 |
| **Medium** | PUT `residue_ids=[-1]` | 422 |
| **Medium** | GET `SSTR2` (대문자) | 200 (정규화 확인) |
| **Low** | GET/PUT sstr1, sstr4, sstr5 | 정상 동작 |
| **Low** | POST /extract `ValueError` 처리 | 422 |

---

## 7. 긍정 평가

- **완성도**: 4 endpoint + Pydantic 검증 + `_default.json` 백업/복원 메커니즘 모두 구현
- **테스트 격리**: `monkeypatch`로 실제 `data/` 디렉토리 접근 없는 완전 격리
- **에러 코드 일관성**: 400/404/422/503 상황별 명확히 구분
- **타입 힌팅**: 전 함수 일관 적용
- **문서화**: docstring + 커버리지 항목 목록 상세

---

## 8. E2E 관련 차단 정리 (uvicorn 재기동 후)

```bash
# 재기동 후 즉시 확인 커맨드
curl http://127.0.0.1:8787/api/binding_pocket/sstr2
# 예상: 200 (binding_pocket_SSTR2.json 존재 시) 또는 404 (파일 없을 시, 정상)

curl -X PUT http://127.0.0.1:8787/api/binding_pocket/sstr2 \
  -H "Content-Type: application/json" \
  -d '{"receptor":"sstr2","center_x":-5.595,"center_y":-28.626,"center_z":52.21,"radius_angstrom":13.0,"residue_ids":[208,209,272,273,276]}'
# 예상: 200 {"ok": true, "path": "..."}
```

---

*생성: reviewer-code | 2026-05-19*
