"""
Lightweight state store for Trinity UI prefs.
- Stores window geometry, last tool/workspace, and split ratios.
- Persisted in config/trinity_ui.json relative to repo root.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def get_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
            return candidate
    return start


def load_state(start: Path) -> Dict[str, Any]:
    root = get_root(start)
    path = root / "config" / "trinity_ui.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(start: Path, data: Dict[str, Any]) -> None:
    root = get_root(start)
    path = root / "config" / "trinity_ui.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
