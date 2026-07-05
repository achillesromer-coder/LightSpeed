# Launcher/services/presets.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

APP_ROOT = Path(__file__).resolve().parents[1]          # .../Launcher
CFG_DIR = APP_ROOT / "config"
GLOBAL_TOKENS = CFG_DIR / "design_tokens.json"
UI_STRINGS = CFG_DIR / "ui_strings.yaml"

DATA_DIR = APP_ROOT.parent / "data"
COMPANIES_DIR = DATA_DIR / "companies"

def load_tokens(company: str | None = None) -> Dict[str, Any]:
    base = {}
    if GLOBAL_TOKENS.exists():
        try:
            base = json.loads(GLOBAL_TOKENS.read_text(encoding="utf-8"))
        except Exception:
            base = {}
    if company:
        brand = COMPANIES_DIR / company / "brand.json"
        if brand.exists():
            try:
                user = json.loads(brand.read_text(encoding="utf-8"))
                base = {**base, **user}
            except Exception:
                pass
    return base

def save_company_tokens(company: str, tokens: Dict[str, Any]) -> None:
    d = COMPANIES_DIR / company
    d.mkdir(parents=True, exist_ok=True)
    (d / "brand.json").write_text(json.dumps(tokens, indent=2), encoding="utf-8")
