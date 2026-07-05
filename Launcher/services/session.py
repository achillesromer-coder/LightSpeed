# Launcher/services/session.py
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional


APP_ROOT = Path(__file__).resolve().parents[1]          # .../Launcher
DATA_DIR = APP_ROOT.parent / "data"                     # .../data
SESSIONS_DIR = DATA_DIR / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Session:
    user_id: str
    company: Optional[str] = None
    project_id: Optional[str] = None
    ui_prefs: Dict[str, Any] = None  # e.g., {"theme":"dark","ui_scale":1.0}

    def save(self) -> Path:
        path = SESSIONS_DIR / f"{self.user_id}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)
        return path

    @staticmethod
    def load(user_id: str) -> Optional["Session"]:
        path = SESSIONS_DIR / f"{user_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return Session(
            user_id=data.get("user_id", user_id),
            company=data.get("company"),
            project_id=data.get("project_id"),
            ui_prefs=data.get("ui_prefs") or {},
        )
