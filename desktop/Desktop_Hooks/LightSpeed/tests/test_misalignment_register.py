from __future__ import annotations

import json
from pathlib import Path

from lightspeed_runtime.misalignment_register import (
    MISALIGNMENT_ITEMS,
    build_misalignment_register,
    write_misalignment_register,
)


def test_misalignment_register_has_25_actionable_items() -> None:
    payload = build_misalignment_register(Path.cwd())

    assert payload["item_count"] == 25
    assert len(MISALIGNMENT_ITEMS) == 25
    assert all(item["id"].startswith("UX-MIS-") for item in payload["items"])
    assert all(item["miss"] and item["change"] and item["owner_floor"] for item in payload["items"])


def test_misalignment_register_writes_json(tmp_path: Path) -> None:
    out = tmp_path / "misalignment_register.json"
    payload = write_misalignment_register(tmp_path, out)
    stored = json.loads(out.read_text(encoding="utf-8"))

    assert stored["item_count"] == 25
    assert payload["path"] == str(out)
