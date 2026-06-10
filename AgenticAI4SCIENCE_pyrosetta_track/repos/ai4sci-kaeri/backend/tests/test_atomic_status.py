"""D2 (F04) 원자적 상태 쓰기 회귀 테스트.

atomic_write_json 이 동시 쓰기/읽기에서 torn-write(부분 JSON) 없이 항상 유효한 JSON 을
남기는지 검증.
"""
import json
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.state import atomic_write_json


def test_atomic_write_readback(tmp_path):
    p = tmp_path / "status.json"
    atomic_write_json(p, {"run_id": "r1", "candidates": [1, 2, 3]})
    assert json.loads(p.read_text()) == {"run_id": "r1", "candidates": [1, 2, 3]}
    # temp 잔여 없음
    assert not (p.with_suffix(".json.tmp")).exists()


def test_concurrent_writes_never_corrupt(tmp_path):
    """여러 스레드가 동시에 쓰고 읽어도 항상 완전한 JSON 이어야 한다."""
    p = tmp_path / "status.json"
    atomic_write_json(p, {"i": 0, "payload": "x" * 1000})
    errors = []

    def writer(n):
        try:
            for i in range(20):
                atomic_write_json(p, {"i": n * 100 + i, "payload": "y" * 2000})
        except Exception as e:  # noqa
            errors.append(e)

    def reader():
        try:
            for _ in range(50):
                txt = p.read_text()
                json.loads(txt)  # 부분 JSON 이면 여기서 예외
        except Exception as e:  # noqa
            errors.append(e)

    threads = [threading.Thread(target=writer, args=(n,)) for n in range(4)]
    threads += [threading.Thread(target=reader) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"동시 접근 중 손상/예외 발생: {errors[:3]}"
    # 최종 파일은 유효한 JSON
    final = json.loads(p.read_text())
    assert "i" in final
