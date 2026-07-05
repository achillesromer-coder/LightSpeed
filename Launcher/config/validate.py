"""
config/validate.py — Load & validate config packs with ranges and friendly errors.
Usage:
    from config.validate import AppConfig
    cfg = AppConfig.load_all(base_dir=Path(__file__).resolve().parent)
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional, List
import json, yaml
from pydantic import BaseModel, Field, validator

class Defaults(BaseModel):
    grid_size_px: int = Field(24, ge=8, le=64, description="Snap grid size (8–64).")
    opacity: float = Field(1.0, ge=0.05, le=1.0, description="Default opacity (0.05–1.0).")
    blur_radius_px: int = Field(8, ge=0, le=64, description="Blur/softness radius (0–64px).")

class AppConfig(BaseModel):
    theme: str = Field(..., description="Insert 'light' or 'dark'.")
    ui_scale: float = Field(1.0, ge=0.85, le=1.25, description="UI scale 0.85–1.25.")
    autosave_interval_sec: int = Field(300, ge=60, le=1800)
    visible_tabs: List[str]
    hidden_layers: List[str] = []
    defaults: Defaults = Defaults()

    # loaded companions
    design_tokens: Dict[str, Any] = {}
    permissions: Dict[str, Any] = {}
    ui_strings: Dict[str, Any] = {}
    node_presets: Dict[str, Any] = {}

    @validator("theme")
    def _theme_ok(cls, v):
        if v not in ("light", "dark", "_____"):
            # allow placeholder during setup
            raise ValueError("theme must be 'light' or 'dark' (temporary '_____' allowed only in wizard).")
        return v

    @classmethod
    def load_all(cls, base_dir: Path) -> "AppConfig":
        # main config.json (user-edited)
        config_path = base_dir / "config.json"
        if not config_path.exists():
            # bootstrap a placeholder
            config_path.write_text(json.dumps({
                "theme": "_____",
                "ui_scale": 1.00,
                "autosave_interval_sec": 300,
                "visible_tabs": ["Layer N","Graph","Z Map"],
                "hidden_layers": []
            }, indent=2), encoding="utf-8")

        cfg = json.loads(config_path.read_text(encoding="utf-8"))

        # companions
        tokens = json.loads((base_dir / "design_tokens.json").read_text(encoding="utf-8"))
        perms  = yaml.safe_load((base_dir / "permissions.yaml").read_text(encoding="utf-8"))
        i18n   = yaml.safe_load((base_dir / "ui_strings.yaml").read_text(encoding="utf-8"))
        presets= json.loads((base_dir / "node_presets.json").read_text(encoding="utf-8"))

        obj = cls(**cfg)
        obj.design_tokens = tokens
        obj.permissions   = perms
        obj.ui_strings    = i18n
        obj.node_presets  = presets
        return obj
