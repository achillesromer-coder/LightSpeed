"""
UNIVERSAL BENTO UI SYSTEM v5.1.2
1.5m Radius Curved Interface Available Across All Z-Floors

This is the UNIVERSAL Bento UI system that provides a consistent curved
interface experience across all Z-floors. Each floor can contribute its
own widgets, functions, and settings to the Bento grid.

Updated: April 8, 2026
Purpose: Universal curved UI for all Z-floors with per-floor customization
"""

import tkinter as tk
from tkinter import ttk
import math
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

# Tk-safe color sanitizer (handles rgba() + #RRGGBBAA). Keep optional to avoid hard import coupling.
try:
    from core.ui.glass_ui import tk_safe_color as _tk_safe_color
except Exception:  # pragma: no cover
    _tk_safe_color = None
# CODEX NOTE (2026-01-30):
# - `UniversalBentoSystem` is the canonical widget registry used by the Construct's CurvedUIOverlay.
# - Config is read from `config/unified_config.json` (optional `bento` section) and styled by
#   `config/premium_theme_config.json` (Romer Premium palette).
# - Runtime should not write config files; persistence belongs in Trinity settings/trinity storage.


def _find_lightspeed_root(start: Path) -> Path:
    start = start.resolve()
    for cand in (start, *start.parents):
        try:
            if (cand / "N.py").exists() and (cand / "Z Axis").exists():
                return cand
        except Exception:
            continue
    return start.parent


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def _load_romer_palette(mode: str = "dark_mode") -> Dict[str, str]:
    """
    Load the Romer Premium palette from config/premium_theme_config.json.

    Note: The platform commonly expects dark-mode keys like `accent_deep_gold`.
    For light mode we map `accent_gold` -> `accent_deep_gold` for compatibility.
    """
    root = _find_lightspeed_root(Path(__file__))
    cfg = root / "config" / "premium_theme_config.json"
    payload = _load_json(cfg) if cfg.exists() else {}
    palettes = payload.get("color_palettes") if isinstance(payload, dict) else {}
    selected = palettes.get(mode) if isinstance(palettes, dict) else {}

    # Stable subset with safe fallbacks (dark defaults).
    base: Dict[str, str] = {
        "primary": "#0A4D4D",
        "secondary": "#1A5F5F",
        "accent_phthalo_green": "#123524",
        "accent_deep_gold": "#B8860B",
        "accent_velvet_blue": "#191970",
        "matrix_green": "#00FF41",
        "tortoise_eggshell": "#F0EAD6",
        "charcoal_text": "#36454F",
        "text_primary": "#F5F5DC",
        "text_secondary": "#D3D3D3",
        "border": "#2F4F4F",
        "button_hover": "#1A5F5F",
    }

    if isinstance(selected, dict):
        for k, v in selected.items():
            if isinstance(v, str) and v.strip():
                base[k] = v.strip()

        # Compatibility mapping for light mode key names.
        if mode == "light_mode":
            gold = selected.get("accent_gold")
            if isinstance(gold, str) and gold.strip():
                base["accent_deep_gold"] = gold.strip()

            # Provide sensible light-mode defaults for keys not present in config.
            base.setdefault("accent_velvet_blue", "#191970")
            base.setdefault("matrix_green", "#00FF41")
            base.setdefault("tortoise_eggshell", "#F0EAD6")
            base.setdefault("charcoal_text", "#36454F")

    # Final pass: ensure every palette entry is Tk-safe. This prevents "unknown color name"
    # errors if config contains rgba() or alpha-hex strings.
    if _tk_safe_color:
        bg = base.get("primary", "#000000")
        for k, v in list(base.items()):
            if isinstance(v, str) and v.strip():
                base[k] = _tk_safe_color(v.strip(), bg=bg)
    else:
        # Best-effort: drop CSS rgba() values to defaults.
        for k, v in list(base.items()):
            if isinstance(v, str) and v.strip().lower().startswith("rgba"):
                # Keep existing default for this key if present, else fall back to a safe black.
                base[k] = base.get(k) or "#000000"

    return base


def _load_bento_config() -> Dict[str, Any]:
    root = _find_lightspeed_root(Path(__file__))
    cfg = root / "config" / "unified_config.json"
    payload = _load_json(cfg) if cfg.exists() else {}
    bento = payload.get("bento") if isinstance(payload, dict) else None
    return bento if isinstance(bento, dict) else {}

def _load_ui_theme_config() -> Dict[str, Any]:
    root = _find_lightspeed_root(Path(__file__))
    cfg = root / "config" / "unified_config.json"
    payload = _load_json(cfg) if cfg.exists() else {}
    ui_theme = payload.get("ui_theme") if isinstance(payload, dict) else None
    return ui_theme if isinstance(ui_theme, dict) else {}


def _trinity_smart_settings_path() -> Path:
    root = _find_lightspeed_root(Path(__file__))
    return root / "Z Axis" / "Z+3_Trinity" / "settings" / "smart_settings.json"


def _read_trinity_smart_settings() -> Dict[str, Any]:
    path = _trinity_smart_settings_path()
    return _load_json(path) if path.exists() else {}


def _write_trinity_smart_settings(payload: Dict[str, Any]) -> bool:
    path = _trinity_smart_settings_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
        return True
    except Exception:
        return False


class BentoWidgetType(Enum):
    """Types of widgets that can appear in Bento UI"""
    BUTTON = "button"
    SLIDER = "slider"
    TOGGLE = "toggle"
    DISPLAY = "display"
    INPUT = "input"
    GRAPH = "graph"
    CALCULATOR = "calculator"
    MONITOR = "monitor"


@dataclass
class BentoWidget:
    """
    A widget in the Bento UI grid
    """
    id: str
    title: str
    widget_type: BentoWidgetType
    floor: str  # Which Z-floor owns this widget
    callback: Optional[Callable] = None
    value: Any = None
    config: Dict[str, Any] = field(default_factory=dict)
    position: Optional[tuple] = None  # (row, col) in grid


@dataclass
class FloorBentoConfig:
    """
    Configuration for a Z-floor's Bento UI contributions
    """
    floor_id: str
    floor_name: str
    color: str
    widgets: List[BentoWidget] = field(default_factory=list)
    priority: int = 0  # Higher priority = appears first in UI


class UniversalBentoSystem:
    """
    Universal Bento UI System - 1.5m curved interface

    This system manages the curved Bento grid that wraps around the user
    at a 1.5m radius. It aggregates widgets from all Z-floors and presents
    them in an organized, physics-based curved interface.
    """

    def __init__(self, parent: Optional[tk.Misc] = None):
        self.parent = parent

        self.palette = _load_romer_palette()
        bento_cfg = _load_bento_config()
        self.ui_theme = _load_ui_theme_config()

        # Optional per-user context (wired by N.py after login). When set, we prefer
        # user-owned persistence (`user_preferences.widget_layout`) over Trinity's
        # global `smart_settings.json` layout.
        self.user_id: Optional[str] = None
        self.user_prefs: Any = None
        self._layout_source: str = "trinity_settings"

        self.radius = float(bento_cfg.get("radius_m", 1.5))  # meters
        self.visible = False

        # Bento grid configuration
        self.grid_cols = int(bento_cfg.get("grid_cols", 4))
        self.grid_rows = int(bento_cfg.get("grid_rows", 12))
        self.cell_width = float(bento_cfg.get("cell_width_m", 0.25))  # meters
        self.cell_height = float(bento_cfg.get("cell_height_m", 0.30))  # meters

        # Floor configurations
        self.floor_configs: Dict[str, FloorBentoConfig] = {}
        self.active_floor: Optional[str] = None

        # Widget registry
        self.widgets: List[BentoWidget] = []

        # UI state
        self.selected_widget: Optional[str] = None
        self.scroll_offset = 0

        # Persistent Bento layout (Trinity-owned, stored in smart_settings.json).
        self.saved_layout: Dict[str, Dict[str, int]] = self._load_saved_layout()

        # Initialize default floor configurations
        self._initialize_default_floors()

    def _initialize_default_floors(self):
        """Initialize default Bento configurations for each Z-floor"""

        # Z+3 Trinity - UI & Dashboard
        trinity_config = FloorBentoConfig(
            floor_id="Z+3_Trinity",
            floor_name="Trinity",
            color=self.palette.get("accent_deep_gold", "#B8860B"),
            priority=10
        )
        trinity_config.widgets = [
            BentoWidget(
                id="trinity_dashboard",
                title="Dashboard",
                widget_type=BentoWidgetType.DISPLAY,
                floor="Z+3_Trinity",
                config={
                    "icon": "DASH",
                    "description": "System dashboard",
                    "span_cols": 3,
                    "span_rows": 2,
                }
            ),
            BentoWidget(
                id="trinity_layout",
                title="Workspace Layout",
                widget_type=BentoWidgetType.BUTTON,
                floor="Z+3_Trinity",
                config={"icon": "LAY", "description": "Arrange workspace (spatial)"},
            ),
            BentoWidget(
                id="trinity_save_layout",
                title="Save Layout",
                widget_type=BentoWidgetType.BUTTON,
                floor="Z+3_Trinity",
                config={"icon": "SAVE", "description": "Save Bento layout (per-user when available)"},
            ),
            BentoWidget(
                id="trinity_reset_layout",
                title="Reset Layout",
                widget_type=BentoWidgetType.BUTTON,
                floor="Z+3_Trinity",
                config={"icon": "RESET", "description": "Clear saved layout (per-user when available)"},
            ),
            BentoWidget(
                id="trinity_edit_layout",
                title="Edit Layout",
                widget_type=BentoWidgetType.BUTTON,
                floor="Z+3_Trinity",
                config={"icon": "EDIT", "description": "Edit Bento layout grid"},
            ),
            BentoWidget(
                id="trinity_widgets",
                title="Widget Library",
                widget_type=BentoWidgetType.BUTTON,
                floor="Z+3_Trinity",
                config={"icon": "WID", "description": "Browse widgets"}
            ),
            BentoWidget(
                id="trinity_themes",
                title="Theme Selector",
                widget_type=BentoWidgetType.TOGGLE,
                floor="Z+3_Trinity",
                config={"icon": "THEME", "options": ["Light", "Dark", "Auto"]}
            )
        ]
        self.floor_configs["Z+3_Trinity"] = trinity_config

        # Z+2 Neo - AI Integration
        neo_config = FloorBentoConfig(
            floor_id="Z+2_Neo",
            floor_name="Neo",
            color=self.palette.get("accent_velvet_blue", "#191970"),
            priority=9
        )
        neo_config.widgets = [
            BentoWidget(
                id="neo_achilles",
                title="Achilles AI",
                widget_type=BentoWidgetType.BUTTON,
                floor="Z+2_Neo",
                config={"icon": "AI", "description": "Talk to Achilles"}
            ),
            BentoWidget(
                id="neo_learning",
                title="Learning Engine",
                widget_type=BentoWidgetType.MONITOR,
                floor="Z+2_Neo",
                config={"icon": "LEARN", "metric": "correlations"}
            ),
            BentoWidget(
                id="neo_models",
                title="Model Selector",
                widget_type=BentoWidgetType.TOGGLE,
                floor="Z+2_Neo",
                config={"icon": "MODEL", "options": ["GPT-4", "Ollama", "Claude"]}
            )
        ]
        self.floor_configs["Z+2_Neo"] = neo_config

        # Z+1 Architect - Mission Planning
        architect_config = FloorBentoConfig(
            floor_id="Z+1_Architect",
            floor_name="Architect",
            color=self.palette.get("accent_phthalo_green", "#123524"),
            priority=8
        )
        architect_config.widgets = [
            BentoWidget(
                id="architect_projects",
                title="Projects",
                widget_type=BentoWidgetType.DISPLAY,
                floor="Z+1_Architect",
                config={"icon": "PROJ", "count": 0}
            ),
            BentoWidget(
                id="architect_timeline",
                title="Timeline",
                widget_type=BentoWidgetType.GRAPH,
                floor="Z+1_Architect",
                config={"icon": "TIME", "type": "gantt"}
            ),
            BentoWidget(
                id="architect_tasks",
                title="Task Queue",
                widget_type=BentoWidgetType.DISPLAY,
                floor="Z+1_Architect",
                config={"icon": "TASK", "count": 0}
            )
        ]
        self.floor_configs["Z+1_Architect"] = architect_config

        # Z0 TheConstruct - Physics & Simulations
        construct_config = FloorBentoConfig(
            floor_id="Z0_TheConstruct",
            floor_name="TheConstruct",
            color=self.palette.get("secondary", "#1A5F5F"),
            priority=7
        )
        construct_config.widgets = [
            BentoWidget(
                id="construct_raphael",
                title="Raphael Physics",
                widget_type=BentoWidgetType.BUTTON,
                floor="Z0_TheConstruct",
                config={
                    "icon": "RAPH",
                    "description": "Physics engine",
                    "span_cols": 2,
                    "span_rows": 2,
                }
            ),
            BentoWidget(
                id="construct_schwarzschild",
                title="Black Hole Calc",
                widget_type=BentoWidgetType.CALCULATOR,
                floor="Z0_TheConstruct",
                config={"icon": "SCHW", "formula": "Schwarzschild Radius"}
            ),
            BentoWidget(
                id="construct_quantum",
                title="Quantum Sim",
                widget_type=BentoWidgetType.CALCULATOR,
                floor="Z0_TheConstruct",
                config={"icon": "QUANT", "formula": "Quantum Energy"}
            ),
            BentoWidget(
                id="construct_gravity",
                title="Gravity Sim",
                widget_type=BentoWidgetType.SLIDER,
                floor="Z0_TheConstruct",
                config={"icon": "GRAV", "min": 0, "max": 50, "default": 9.8}
            )
        ]
        self.floor_configs["Z0_TheConstruct"] = construct_config

        # Z-1 Morpheus - Knowledge Base
        morpheus_config = FloorBentoConfig(
            floor_id="Z-1_Morpheus",
            floor_name="Morpheus",
            color=self.palette.get("accent_velvet_blue", "#191970"),
            priority=6
        )
        morpheus_config.widgets = [
            BentoWidget(
                id="morpheus_search",
                title="Knowledge Search",
                widget_type=BentoWidgetType.INPUT,
                floor="Z-1_Morpheus",
                config={
                    "icon": "SRCH",
                    "placeholder": "Search...",
                    "span_cols": 3,
                    "span_rows": 1,
                }
            ),
            BentoWidget(
                id="morpheus_docs",
                title="Documentation",
                widget_type=BentoWidgetType.DISPLAY,
                floor="Z-1_Morpheus",
                config={"icon": "DOCS", "count": 0}
            ),
            BentoWidget(
                id="morpheus_analyze",
                title="Code Analysis",
                widget_type=BentoWidgetType.BUTTON,
                floor="Z-1_Morpheus",
                config={"icon": "ANALY", "description": "Analyze code"}
            )
        ]
        self.floor_configs["Z-1_Morpheus"] = morpheus_config

        # Z-2 Oracle - Archives
        oracle_config = FloorBentoConfig(
            floor_id="Z-2_Oracle",
            floor_name="Oracle",
            color=self.palette.get("primary", "#0A4D4D"),
            priority=5
        )
        oracle_config.widgets = [
            BentoWidget(
                id="oracle_encyclopedia",
                title="Encyclopedia",
                widget_type=BentoWidgetType.BUTTON,
                floor="Z-2_Oracle",
                config={"icon": "ENC", "volumes": 3}
            ),
            BentoWidget(
                id="oracle_dictionary",
                title="Dictionary",
                widget_type=BentoWidgetType.BUTTON,
                floor="Z-2_Oracle",
                config={"icon": "DICT", "languages": 5}
            ),
            BentoWidget(
                id="oracle_z_direct",
                title="Z Direct",
                widget_type=BentoWidgetType.BUTTON,
                floor="Z-2_Oracle",
                config={"icon": "ZDIR", "description": "Committed objects + schemas (read-only)"}
            ),
            BentoWidget(
                id="oracle_vault",
                title="IP Vault",
                widget_type=BentoWidgetType.DISPLAY,
                floor="Z-2_Oracle",
                config={
                    "icon": "VAULT",
                    "secure": True,
                    "span_cols": 2,
                    "span_rows": 1,
                }
            )
        ]
        self.floor_configs["Z-2_Oracle"] = oracle_config

        # Z-3 Smith - Automation
        smith_config = FloorBentoConfig(
            floor_id="Z-3_Smith",
            floor_name="Smith",
            color=self.palette.get("matrix_green", "#00FF41"),
            priority=4
        )
        smith_config.widgets = [
            BentoWidget(
                id="smith_jobs",
                title="Background Jobs",
                widget_type=BentoWidgetType.MONITOR,
                floor="Z-3_Smith",
                config={"icon": "JOBS", "active": 0}
            ),
            BentoWidget(
                id="smith_sops",
                title="SOPs",
                widget_type=BentoWidgetType.DISPLAY,
                floor="Z-3_Smith",
                config={"icon": "SOPS", "count": 0}
            ),
            BentoWidget(
                id="smith_scheduler",
                title="Task Scheduler",
                widget_type=BentoWidgetType.BUTTON,
                floor="Z-3_Smith",
                config={"icon": "SCHED", "description": "Schedule tasks"}
            )
        ]
        self.floor_configs["Z-3_Smith"] = smith_config

        # Z-4 Merovingian - Diagnostics
        merovingian_config = FloorBentoConfig(
            floor_id="Z-4_Merovingian",
            floor_name="Merovingian",
            color=self.palette.get("charcoal_text", "#36454F"),
            priority=3
        )
        merovingian_config.widgets = [
            BentoWidget(
                id="mero_health",
                title="System Health",
                widget_type=BentoWidgetType.MONITOR,
                floor="Z-4_Merovingian",
                config={"icon": "HEALTH", "status": "healthy"}
            ),
            BentoWidget(
                id="mero_logs",
                title="Log Viewer",
                widget_type=BentoWidgetType.BUTTON,
                floor="Z-4_Merovingian",
                config={
                    "icon": "LOG",
                    "description": "View logs",
                    "span_cols": 2,
                    "span_rows": 1,
                }
            ),
            BentoWidget(
                id="mero_metrics",
                title="Performance",
                widget_type=BentoWidgetType.GRAPH,
                floor="Z-4_Merovingian",
                config={"icon": "METR", "metric": "fps"}
            )
        ]
        self.floor_configs["Z-4_Merovingian"] = merovingian_config

        # Load committed "bento_widget" definitions (data-defined UI tiles) then compile.
        # This keeps the default curated widgets in code while allowing operator-approved
        # extensions via Z Direct durable registries.
        try:
            self._load_committed_bento_widget_definitions()
        except Exception:
            pass

        # Compile all widgets
        self._compile_widgets()

    def _coerce_widget_type(self, raw: Any) -> "BentoWidgetType":
        """Convert a string-like widget_type into a BentoWidgetType enum (best-effort)."""
        try:
            if isinstance(raw, BentoWidgetType):
                return raw
            if not isinstance(raw, str):
                return BentoWidgetType.BUTTON
            key = raw.strip().upper()
            if not key:
                return BentoWidgetType.BUTTON
            return BentoWidgetType[key]
        except Exception:
            return BentoWidgetType.BUTTON

    def _ensure_floor_config(self, floor_id: str, *, color: Optional[str] = None, priority: int = 0) -> FloorBentoConfig:
        """Ensure a FloorBentoConfig exists for a floor_id (best-effort; does not override existing)."""
        existing = self.floor_configs.get(floor_id)
        if existing is not None:
            return existing

        # Best-effort naming: "Z+3_Trinity" -> "Trinity"
        floor_name = floor_id
        try:
            if "_" in floor_id:
                floor_name = floor_id.split("_", 1)[1]
        except Exception:
            floor_name = floor_id

        cfg = FloorBentoConfig(
            floor_id=floor_id,
            floor_name=floor_name,
            color=(color or self.palette.get("secondary", "#1A5F5F")),
            priority=int(priority or 0),
        )
        self.floor_configs[floor_id] = cfg
        return cfg

    def _load_committed_bento_widget_definitions(self) -> None:
        """
        Load committed Bento widget definitions from Trinity's durable Z Direct registry.

        Convention:
        - Stored in `Z+3` registry `objects.json` as `kind="bento_widget"` items.
        - These are operator-approved definitions (staging stream is not used here).
        """
        try:
            from core.services import get_z_direct  # type: ignore

            z_direct = get_z_direct()
        except Exception:
            return

        try:
            items = z_direct.read_registry("Z+3", name="objects") or []
        except Exception:
            items = []

        for it in items:
            if not isinstance(it, dict):
                continue
            if it.get("kind") != "bento_widget":
                continue

            # Default enabled=True when omitted.
            enabled = it.get("enabled")
            if enabled is False:
                continue

            wid = str(it.get("id") or "").strip()
            if not wid:
                continue

            title = str(it.get("title") or "").strip() or wid
            floor = str(it.get("floor") or "").strip() or "Z+3_Trinity"
            wtype = self._coerce_widget_type(it.get("widget_type"))
            cfg = it.get("config") if isinstance(it.get("config"), dict) else {}

            # Optional per-floor hints (do not override existing config colors/priorities).
            floor_color = it.get("color") if isinstance(it.get("color"), str) and str(it.get("color")).strip() else None
            floor_pri = it.get("floor_priority")
            try:
                floor_pri_i = int(floor_pri) if floor_pri is not None else 0
            except Exception:
                floor_pri_i = 0

            floor_cfg = self._ensure_floor_config(floor, color=floor_color, priority=floor_pri_i)

            # Avoid duplicates when the curated code set already defines this id.
            try:
                if any(getattr(w, "id", None) == wid for w in (floor_cfg.widgets or [])):
                    continue
            except Exception:
                pass

            floor_cfg.widgets.append(
                BentoWidget(
                    id=wid,
                    title=title,
                    widget_type=wtype,
                    floor=floor,
                    config=cfg,
                )
            )

    def _compile_widgets(self):
        """Compile widgets from all floors into master list"""
        self.widgets.clear()

        # Sort floors by priority
        sorted_floors = sorted(
            self.floor_configs.values(),
            key=lambda f: f.priority,
            reverse=True
        )

        # Add widgets from each floor
        for floor_config in sorted_floors:
            self.widgets.extend(floor_config.widgets)

    def register_floor_widgets(self, floor_id: str, widgets: List[BentoWidget]):
        """
        Register additional widgets for a floor

        This allows Z-floors to dynamically add their widgets to the Bento UI
        """
        if floor_id not in self.floor_configs:
            print(f"[Bento] Warning: Floor {floor_id} not found")
            return

        config = self.floor_configs[floor_id]
        config.widgets.extend(widgets)
        self._compile_widgets()

        print(f"[Bento] Registered {len(widgets)} widgets for {floor_id}")

    def get_widgets_for_floor(self, floor_id: str) -> List[BentoWidget]:
        """Get all widgets belonging to a specific floor"""
        return [w for w in self.widgets if w.floor == floor_id]

    def get_all_widgets(self) -> List[BentoWidget]:
        """Get all widgets across all floors"""
        return self.widgets

    def toggle_visibility(self):
        """Toggle Bento UI visibility"""
        self.visible = not self.visible
        return self.visible

    def set_active_floor(self, floor_id: str):
        """Set the currently active floor (filters widgets)"""
        self.active_floor = floor_id

    def _sanitize_layout(self, layout: Any) -> Dict[str, Dict[str, int]]:
        """Best-effort validation/coercion of a packed Bento layout dict."""
        if not isinstance(layout, dict):
            return {}

        cols = max(1, int(self.grid_cols))
        rows = max(1, int(self.grid_rows))
        cleaned: Dict[str, Dict[str, int]] = {}

        for wid, item in layout.items():
            if not isinstance(wid, str) or not wid:
                continue
            if not isinstance(item, dict):
                continue
            try:
                r = int(item.get("row", 0))
                c = int(item.get("col", 0))
                sc = int(item.get("span_cols", 1))
                sr = int(item.get("span_rows", 1))
            except Exception:
                continue

            r = max(0, min(r, rows - 1))
            c = max(0, min(c, cols - 1))
            sc = max(1, min(sc, cols))
            sr = max(1, min(sr, rows))
            if r + sr > rows:
                sr = max(1, rows - r)
            if c + sc > cols:
                sc = max(1, cols - c)

            cleaned[wid] = {"row": r, "col": c, "span_cols": sc, "span_rows": sr}

        return cleaned

    def _apply_palette_to_floor_configs(self) -> None:
        """Update per-floor accent colors when the palette changes."""
        try:
            mapping = {
                "Z+3_Trinity": self.palette.get("accent_deep_gold", "#B8860B"),
                "Z+2_Neo": self.palette.get("accent_velvet_blue", "#191970"),
                "Z+1_Architect": self.palette.get("accent_phthalo_green", "#123524"),
                "Z0_TheConstruct": self.palette.get("secondary", "#1A5F5F"),
                "Z-1_Morpheus": self.palette.get("accent_velvet_blue", "#191970"),
                "Z-2_Oracle": self.palette.get("primary", "#0A4D4D"),
                "Z-3_Smith": self.palette.get("matrix_green", "#00FF41"),
                "Z-4_Merovingian": self.palette.get("charcoal_text", "#36454F"),
            }
            for floor_id, color in mapping.items():
                cfg = self.floor_configs.get(floor_id)
                if cfg and isinstance(color, str) and color:
                    cfg.color = color
        except Exception:
            return

    def set_user_context(self, user_id: Optional[str]) -> bool:
        """
        Set the active user context for per-user layout/theme overrides.

        When available, this prefers `user_preferences.widget_layout` over the
        Trinity-global `smart_settings.json` stored layout.
        """
        if not user_id:
            return False

        user_id = str(user_id).strip()
        if not user_id or user_id.lower() in ("guest", "anonymous"):
            return False

        if self.user_id == user_id:
            return True

        self.user_id = user_id

        # Best-effort: load per-user preferences from core services (Merovingian-owned).
        prefs = None
        try:
            from core.services import get_user_preferences  # type: ignore

            prefs = get_user_preferences(user_id)
            self.user_prefs = prefs
        except Exception:
            prefs = None
            self.user_prefs = None

        # Theme -> palette selection (defaults to dark if unknown).
        mode = "dark_mode"
        try:
            theme = prefs.get_theme() if prefs is not None else None
            if isinstance(theme, str) and theme.strip().lower().startswith("light"):
                mode = "light_mode"
        except Exception:
            mode = "dark_mode"

        try:
            self.palette = _load_romer_palette(mode)
            self._apply_palette_to_floor_configs()
        except Exception:
            pass

        # Per-user Bento layout.
        user_layout: Dict[str, Dict[str, int]] = {}
        try:
            layout = prefs.get_widget_layout() if prefs is not None else None
            user_layout = self._sanitize_layout(layout)
        except Exception:
            user_layout = {}

        if user_layout:
            self.saved_layout = user_layout
            self._layout_source = "user_preferences"
        else:
            self._layout_source = "trinity_settings"

        return True

    # ----------------------------------------------------------------------
    # Bento menu affordances (Favorites / Recents)
    # ----------------------------------------------------------------------

    def _get_user_list_preference(self, key: str, default: Optional[List[str]] = None) -> List[str]:
        default = list(default or [])
        prefs = getattr(self, "user_prefs", None)
        if prefs is None:
            return default
        try:
            getter = getattr(prefs, "get_preference", None)
            if not callable(getter):
                return default
            raw = getter(key, default)
        except Exception:
            return default

        if isinstance(raw, list):
            out: List[str] = []
            for item in raw:
                try:
                    s = str(item).strip()
                except Exception:
                    continue
                if s:
                    out.append(s)
            return out
        return default

    def _set_user_list_preference(self, key: str, values: List[str]) -> bool:
        prefs = getattr(self, "user_prefs", None)
        if prefs is None:
            return False
        try:
            setter = getattr(prefs, "set_preference", None)
            if not callable(setter):
                return False
            cleaned: List[str] = []
            for v in (values or []):
                try:
                    s = str(v).strip()
                except Exception:
                    continue
                if s and s not in cleaned:
                    cleaned.append(s)
            setter(key, cleaned)
            return True
        except Exception:
            return False

    def get_favorite_widget_ids(self) -> List[str]:
        return self._get_user_list_preference("bento.favorites", default=[])

    def is_favorite_widget(self, widget_id: str) -> bool:
        try:
            wid = str(widget_id or "").strip()
        except Exception:
            return False
        if not wid:
            return False
        return wid in set(self.get_favorite_widget_ids())

    def toggle_favorite_widget(self, widget_id: str) -> bool:
        """
        Toggle a widget favorite state (per-user).

        Returns: True if now favorited, False if unfavorited / not persisted.
        """
        try:
            wid = str(widget_id or "").strip()
        except Exception:
            wid = ""
        if not wid:
            return False

        favs = self.get_favorite_widget_ids()
        now_fav = True
        if wid in favs:
            favs = [x for x in favs if x != wid]
            now_fav = False
        else:
            favs = [wid, *favs]
            now_fav = True

        ok = self._set_user_list_preference("bento.favorites", favs[:64])
        return now_fav if ok else False

    def clear_favorite_widgets(self) -> bool:
        """Clear all favorites for the active user (best-effort)."""
        return bool(self._set_user_list_preference("bento.favorites", []))

    def get_recent_widget_ids(self, *, limit: int = 8) -> List[str]:
        ids = self._get_user_list_preference("bento.recents", default=[])
        out: List[str] = []
        for wid in ids:
            if wid and wid not in out:
                out.append(wid)
            if len(out) >= int(limit):
                break
        return out

    def clear_recent_widgets(self) -> bool:
        """Clear all recents for the active user (best-effort)."""
        return bool(self._set_user_list_preference("bento.recents", []))

    def _note_recent_widget(self, widget_id: str) -> None:
        try:
            wid = str(widget_id or "").strip()
        except Exception:
            wid = ""
        if not wid:
            return

        recents = self.get_recent_widget_ids(limit=32)
        recents = [x for x in recents if x != wid]
        recents = [wid, *recents]
        self._set_user_list_preference("bento.recents", recents[:24])

    def save_layout_to_user_preferences(self) -> bool:
        """Persist the current (packed) layout to the active user's preferences."""
        if not self.user_id:
            return False

        # Pack a deterministic layout and persist it.
        try:
            widgets = self.get_all_widgets() or []
            layout = self.layout_for_widgets(widgets, prefer_saved=True)
            layout = self._sanitize_layout(layout)
        except Exception:
            layout = {}

        try:
            prefs = self.user_prefs
            if prefs is None:
                from core.services import get_user_preferences  # type: ignore

                prefs = get_user_preferences(self.user_id)
                self.user_prefs = prefs

            setter = getattr(prefs, "set_widget_layout", None)
            if callable(setter):
                setter(layout)
                self.saved_layout = layout
                self._layout_source = "user_preferences"
                return True
        except Exception:
            return False

        return False

    def reset_layout_in_user_preferences(self) -> bool:
        """Clear any user-saved Bento layout and fall back to Trinity global/default layout."""
        if not self.user_id:
            return False

        try:
            prefs = self.user_prefs
            if prefs is None:
                from core.services import get_user_preferences  # type: ignore

                prefs = get_user_preferences(self.user_id)
                self.user_prefs = prefs

            clearer = getattr(prefs, "clear_widget_layout", None)
            if callable(clearer):
                clearer()
            else:
                setter = getattr(prefs, "set_widget_layout", None)
                if callable(setter):
                    setter({})

            self.saved_layout = self._load_saved_layout()
            self._layout_source = "trinity_settings"
            return True
        except Exception:
            return False

    def _load_saved_layout(self) -> Dict[str, Dict[str, int]]:
        """
        Load a saved Bento layout from Trinity settings (best-effort).

        Stored under the key `bento.layout` in `smart_settings.json`.
        """
        try:
            settings = _read_trinity_smart_settings()
            layout = settings.get("bento.layout")
            if isinstance(layout, dict):
                cleaned: Dict[str, Dict[str, int]] = {}
                for wid, item in layout.items():
                    if not isinstance(wid, str) or not wid:
                        continue
                    if not isinstance(item, dict):
                        continue
                    try:
                        cleaned[wid] = {
                            "row": int(item.get("row", 0)),
                            "col": int(item.get("col", 0)),
                            "span_cols": int(item.get("span_cols", 1)),
                            "span_rows": int(item.get("span_rows", 1)),
                        }
                    except Exception:
                        continue
                return cleaned
        except Exception:
            pass
        return {}

    def save_layout_to_settings(self) -> bool:
        """
        Persist the current layout into Trinity settings.

        This saves a packed layout (ignores any existing saved layout) so it can be
        deterministic on next start.
        """
        try:
            widgets = self.get_all_widgets() or []
            layout = self.layout_for_widgets(widgets, prefer_saved=False)
            settings = _read_trinity_smart_settings()
            settings["bento.layout"] = layout
            settings["bento.layout_saved_at"] = __import__("datetime").datetime.now().isoformat()
            ok = _write_trinity_smart_settings(settings)
            if ok:
                self.saved_layout = layout
                self._layout_source = "trinity_settings"
            return bool(ok)
        except Exception:
            return False

    def reset_layout_in_settings(self) -> bool:
        """Clear any saved Bento layout (reverts to auto packing)."""
        try:
            settings = _read_trinity_smart_settings()
            if "bento.layout" in settings:
                settings.pop("bento.layout", None)
            settings["bento.layout_saved_at"] = __import__("datetime").datetime.now().isoformat()
            ok = _write_trinity_smart_settings(settings)
            if ok:
                self.saved_layout = {}
                self._layout_source = "trinity_settings"
            return bool(ok)
        except Exception:
            return False

    def _widget_span(self, widget: BentoWidget) -> tuple[int, int]:
        """
        Return (span_cols, span_rows) for a widget.

        Spans are optional and used by the 3D overlay to scale panel size.
        """
        try:
            sc = int(widget.config.get("span_cols", 1))
        except Exception:
            sc = 1
        try:
            sr = int(widget.config.get("span_rows", 1))
        except Exception:
            sr = 1
        sc = max(1, min(sc, max(1, int(self.grid_cols))))
        sr = max(1, min(sr, max(1, int(self.grid_rows))))
        return sc, sr

    def layout_for_widgets(self, widgets: List[BentoWidget], *, prefer_saved: bool = True) -> Dict[str, Dict[str, int]]:
        """
        Compute a simple first-fit packing layout for a widget list.

        Returns a dict keyed by widget.id:
        - row, col, span_cols, span_rows
        """
        cols = max(1, int(self.grid_cols))
        rows = max(1, int(self.grid_rows))
        occ = [[False for _ in range(cols)] for _ in range(rows)]
        layout: Dict[str, Dict[str, int]] = {}

        def _fits(r: int, c: int, sc: int, sr: int) -> bool:
            if r + sr > rows or c + sc > cols:
                return False
            for rr in range(r, r + sr):
                for cc in range(c, c + sc):
                    if occ[rr][cc]:
                        return False
            return True

        def _mark(r: int, c: int, sc: int, sr: int) -> None:
            for rr in range(r, r + sr):
                for cc in range(c, c + sc):
                    occ[rr][cc] = True

        placed_ids: set[str] = set()
        if prefer_saved and isinstance(getattr(self, "saved_layout", None), dict) and self.saved_layout:
            # First, try to place widgets at their saved coordinates (if they fit).
            for widget in (widgets or []):
                wid = getattr(widget, "id", None)
                if not isinstance(wid, str) or not wid:
                    continue
                entry = self.saved_layout.get(wid)
                if not isinstance(entry, dict):
                    continue
                try:
                    r = int(entry.get("row", 0))
                    c = int(entry.get("col", 0))
                except Exception:
                    continue
                sc, sr = self._widget_span(widget)
                try:
                    sc = int(entry.get("span_cols", sc))
                    sr = int(entry.get("span_rows", sr))
                except Exception:
                    pass
                sc = max(1, min(sc, cols))
                sr = max(1, min(sr, rows))
                if r < 0 or c < 0:
                    continue
                if _fits(r, c, sc, sr):
                    layout[wid] = {"row": r, "col": c, "span_cols": sc, "span_rows": sr}
                    _mark(r, c, sc, sr)
                    placed_ids.add(wid)

        for idx, widget in enumerate(widgets or []):
            wid = getattr(widget, "id", None)
            if not isinstance(wid, str) or not wid:
                continue
            if wid in placed_ids:
                continue
            sc, sr = self._widget_span(widget)

            placed = False
            for r in range(rows):
                for c in range(cols):
                    if _fits(r, c, sc, sr):
                        layout[wid] = {"row": r, "col": c, "span_cols": sc, "span_rows": sr}
                        _mark(r, c, sc, sr)
                        placed = True
                        break
                if placed:
                    break

            if not placed:
                # Fallback: index-based position (may overlap if grid is full).
                r = idx // cols
                c = idx % cols
                layout[wid] = {"row": r, "col": c, "span_cols": sc, "span_rows": sr}

        return layout

    def get_widget_position_3d(self, index: int) -> Dict[str, float]:
        """
        Calculate 3D position for a widget in the curved array

        Returns: {x, y, z} coordinates for positioning in 3D space
        """
        # Calculate grid position
        row = index // self.grid_cols
        col = index % self.grid_cols

        # Calculate angle around cylinder
        angle_per_col = (2 * math.pi) / self.grid_cols
        angle = col * angle_per_col - math.pi  # Center at front

        # Calculate position
        x = math.sin(angle) * self.radius
        z = math.cos(angle) * self.radius
        y = 1.5 - (row * self.cell_height)  # Start at eye level, go down

        return {"x": x, "y": y, "z": z, "angle": angle}

    def get_widget_position_3d_for(
        self,
        widget: BentoWidget,
        index: int,
        *,
        layout: Optional[Dict[str, Dict[str, int]]] = None,
    ) -> Dict[str, float]:
        """
        Calculate 3D placement for a specific widget, optionally using a packed layout.
        """
        cols = max(1, int(self.grid_cols))

        row = index // cols
        col = index % cols
        sc, sr = self._widget_span(widget)

        try:
            wid = getattr(widget, "id", "")
            if layout and isinstance(wid, str) and wid in layout:
                row = int(layout[wid].get("row", row))
                col = int(layout[wid].get("col", col))
                sc = int(layout[wid].get("span_cols", sc))
                sr = int(layout[wid].get("span_rows", sr))
        except Exception:
            pass

        angle_per_col = (2 * math.pi) / cols
        # Center the widget across its span so wide panels sit correctly.
        angle = (col + (sc / 2.0)) * angle_per_col - math.pi

        x = math.sin(angle) * self.radius
        z = math.cos(angle) * self.radius
        y = 1.5 - (row * self.cell_height) - ((sr - 1) * self.cell_height / 2.0)

        width_m = float(self.cell_width) * float(max(1, sc))
        height_m = float(self.cell_height) * float(max(1, sr))

        return {
            "x": float(x),
            "y": float(y),
            "z": float(z),
            "angle": float(angle),
            "width_m": float(width_m),
            "height_m": float(height_m),
            "span_cols": int(sc),
            "span_rows": int(sr),
        }

    def handle_widget_click(self, widget_id: str):
        """Handle clicking on a widget"""
        widget = next((w for w in self.widgets if w.id == widget_id), None)

        if not widget:
            print(f"[Bento] Widget not found: {widget_id}")
            return

        # Persist recents (best-effort, per-user).
        try:
            self._note_recent_widget(widget_id)
        except Exception:
            pass

        print(f"[Bento] Widget clicked: {widget.title} ({widget.floor})")

        # Built-in actions (work even when the host does not inject callbacks).
        if widget_id == "trinity_save_layout" and not callable(widget.callback):
            ok = self.save_layout_to_user_preferences()
            if not ok:
                ok = self.save_layout_to_settings()
            print(f"[Bento] Save layout -> {'OK' if ok else 'FAILED'} ({self._layout_source})")
            return widget

        if widget_id == "trinity_reset_layout" and not callable(widget.callback):
            ok = self.reset_layout_in_user_preferences()
            if not ok:
                ok = self.reset_layout_in_settings()
            print(f"[Bento] Reset layout -> {'OK' if ok else 'FAILED'} ({self._layout_source})")
            return widget

        if widget_id == "trinity_edit_layout" and not callable(widget.callback):
            try:
                self.open_layout_editor()
            except Exception as e:
                print(f"[Bento] Layout editor failed: {e}")
            return widget

        if widget_id == "trinity_themes" and not callable(widget.callback):
            ok = False
            try:
                ok = self.toggle_theme_preference()
            except Exception:
                ok = False
            print(f"[Bento] Toggle theme -> {'OK' if ok else 'FAILED'}")
            return widget

        # Execute callback if available. If the callback was not injected, use
        # the widget's data-defined host action or floor owner as a fallback.
        callback_ok = False
        if callable(widget.callback):
            try:
                widget.callback(widget)
                callback_ok = True
            except Exception as e:
                print(f"[Bento] Widget callback error: {e}")

        if not callback_ok and self._run_host_action_for_widget(widget):
            return widget

        if not callback_ok:
            print(f"[Bento] No action mapped for widget: {widget.id}")

        return widget

    def _floor_name_for_host(self, floor: str) -> Optional[str]:
        """Map canonical floor ids and display labels to N.py floor names."""
        raw = str(floor or "").strip()
        if not raw:
            return None
        lookup = {
            "Z+3_Trinity": "Trinity",
            "Z+2_Neo": "Neo",
            "Z+1_Architect": "Architect",
            "Z0_TheConstruct": "TheConstruct",
            "Z-1_Morpheus": "Morpheus",
            "Z-2_Oracle": "Oracle",
            "Z-3_Smith": "Smith",
            "Z-4_Merovingian": "Merovingian",
            "Trinity": "Trinity",
            "Neo": "Neo",
            "Architect": "Architect",
            "TheConstruct": "TheConstruct",
            "Construct": "TheConstruct",
            "Morpheus": "Morpheus",
            "Oracle": "Oracle",
            "Smith": "Smith",
            "Merovingian": "Merovingian",
        }
        return lookup.get(raw, raw)

    def _run_host_action_for_widget(self, widget: BentoWidget) -> bool:
        """Run the host action declared by a widget config, if available."""
        host = getattr(self, "parent", None) or getattr(self, "host", None)
        config = widget.config if isinstance(widget.config, dict) else {}
        action_name = str(config.get("host_action") or "").strip()

        if host is not None and action_name:
            action = getattr(host, action_name, None)
            if callable(action):
                try:
                    args = config.get("host_action_args", {})
                    if isinstance(args, dict):
                        action(**args)
                    elif isinstance(args, (list, tuple)):
                        action(*args)
                    elif args:
                        action(args)
                    else:
                        action()
                    print(f"[Bento] Host action -> {action_name}")
                    return True
                except Exception as e:
                    print(f"[Bento] Host action failed ({action_name}): {e}")

        if host is not None and hasattr(host, "open_z_floor"):
            floor_name = self._floor_name_for_host(widget.floor)
            if floor_name:
                try:
                    host.open_z_floor(floor_name)
                    print(f"[Bento] Opened floor -> {floor_name}")
                    return True
                except Exception as e:
                    print(f"[Bento] Floor fallback failed ({floor_name}): {e}")

        return False

    def toggle_theme_preference(self) -> bool:
        """
        Toggle the active theme between dark/light and persist per-user when possible.

        This primarily updates the Bento palette/floor accent colors; host shells may
        apply additional theming separately.
        """
        # Prefer per-user persistence when a user session is present.
        prefs = getattr(self, "user_prefs", None)
        if prefs is None and getattr(self, "user_id", None):
            try:
                from core.services import get_user_preferences  # type: ignore

                prefs = get_user_preferences(self.user_id)
                self.user_prefs = prefs
            except Exception:
                prefs = None

        current = "dark"
        try:
            if prefs is not None and hasattr(prefs, "get_theme"):
                t = prefs.get_theme()
                if isinstance(t, str) and t.strip():
                    current = t.strip().lower()
        except Exception:
            current = "dark"

        new_theme = "light" if not current.startswith("light") else "dark"
        mode = "light_mode" if new_theme.startswith("light") else "dark_mode"

        # Persist (best-effort) then apply palette.
        try:
            if prefs is not None and hasattr(prefs, "set_theme"):
                prefs.set_theme(new_theme)
        except Exception:
            pass

        try:
            self.palette = _load_romer_palette(mode)
            self._apply_palette_to_floor_configs()
        except Exception:
            return False

        return True

    def _layout_target_label(self) -> str:
        try:
            u = getattr(self, "user_id", None)
            if isinstance(u, str) and u.strip():
                return f"user:{u.strip()}"
        except Exception:
            pass
        return "global"

    def _persist_layout_to_settings(self, layout: Dict[str, Dict[str, int]]) -> bool:
        """Persist a provided packed layout into Trinity smart_settings.json (global default)."""
        try:
            layout = self._sanitize_layout(layout)
            settings = _read_trinity_smart_settings()
            settings["bento.layout"] = layout
            settings["bento.layout_saved_at"] = __import__("datetime").datetime.now().isoformat()
            ok = _write_trinity_smart_settings(settings)
            if ok:
                self.saved_layout = layout
                self._layout_source = "trinity_settings"
            return bool(ok)
        except Exception:
            return False

    def _persist_layout_to_user_preferences(self, layout: Dict[str, Dict[str, int]]) -> bool:
        """Persist a provided packed layout into the active user's preferences."""
        if not getattr(self, "user_id", None):
            return False

        try:
            layout = self._sanitize_layout(layout)
        except Exception:
            pass

        try:
            prefs = getattr(self, "user_prefs", None)
            if prefs is None:
                from core.services import get_user_preferences  # type: ignore

                prefs = get_user_preferences(self.user_id)
                self.user_prefs = prefs

            setter = getattr(prefs, "set_widget_layout", None)
            if callable(setter):
                setter(layout)
                self.saved_layout = layout
                self._layout_source = "user_preferences"
                return True
        except Exception:
            return False

        return False

    def open_layout_editor(self, parent: Optional[tk.Misc] = None):
        """
        Open a lightweight Bento layout editor.

        This is intentionally simple: it edits the packed layout mapping used by
        the 3D overlay (row/col/span per widget) and saves it per-user or globally.
        """
        host = parent or self.parent or getattr(tk, "_default_root", None)
        created_root = False
        if host is None:
            host = tk.Tk()
            created_root = True

        win = tk.Toplevel(host) if not created_root else host
        win.title(f"Bento Layout Editor ({self._layout_target_label()})")
        win.geometry("1100x820")
        win.configure(bg="#0a1628")

        cols = max(1, int(getattr(self, "grid_cols", 4)))
        rows = max(1, int(getattr(self, "grid_rows", 12)))

        widgets = self.get_all_widgets() or []
        widget_by_id = {getattr(w, "id", ""): w for w in widgets if isinstance(getattr(w, "id", None), str)}

        # Start with a concrete packed layout.
        working_layout: Dict[str, Dict[str, int]] = self.layout_for_widgets(widgets, prefer_saved=True)
        working_layout = self._sanitize_layout(working_layout)

        # Layout: left controls, right grid canvas.
        outer = tk.Frame(win, bg="#0a1628")
        outer.pack(fill="both", expand=True)

        left = tk.Frame(outer, bg="#0a1628", width=340)
        left.pack(side="left", fill="y", padx=12, pady=12)
        left.pack_propagate(False)

        right = tk.Frame(outer, bg="#0a1628")
        right.pack(side="right", fill="both", expand=True, padx=12, pady=12)

        status_var = tk.StringVar(value=f"Layout source: {getattr(self, '_layout_source', 'unknown')}")
        tk.Label(left, text="Bento Layout Editor", bg="#0a1628", fg="#00FFFF", font=("Segoe UI", 14, "bold")).pack(
            anchor="w", pady=(0, 8)
        )
        tk.Label(left, textvariable=status_var, bg="#0a1628", fg="#AAAAAA", font=("Segoe UI", 9)).pack(
            anchor="w", pady=(0, 12)
        )

        tk.Label(left, text="Widgets", bg="#0a1628", fg="#FFFFFF", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        listbox = tk.Listbox(left, height=18, bg="#111a2a", fg="#FFFFFF", selectbackground="#1a5f5f")
        listbox.pack(fill="x", pady=(6, 10))

        wid_list = sorted([wid for wid in widget_by_id.keys() if wid])
        for wid in wid_list:
            listbox.insert("end", wid)

        sel_var = tk.StringVar(value=wid_list[0] if wid_list else "")

        def _current_entry(wid: str) -> Dict[str, int]:
            e = working_layout.get(wid)
            if isinstance(e, dict):
                try:
                    return {
                        "row": int(e.get("row", 0)),
                        "col": int(e.get("col", 0)),
                        "span_cols": int(e.get("span_cols", 1)),
                        "span_rows": int(e.get("span_rows", 1)),
                    }
                except Exception:
                    pass
            return {"row": 0, "col": 0, "span_cols": 1, "span_rows": 1}

        row_var = tk.IntVar(value=0)
        col_var = tk.IntVar(value=0)
        sc_var = tk.IntVar(value=1)
        sr_var = tk.IntVar(value=1)

        def _sync_fields_from_selection() -> None:
            wid = sel_var.get()
            e = _current_entry(wid)
            row_var.set(int(e["row"]))
            col_var.set(int(e["col"]))
            sc_var.set(int(e["span_cols"]))
            sr_var.set(int(e["span_rows"]))

        def _set_selected(wid: str) -> None:
            if not wid:
                return
            sel_var.set(wid)
            try:
                idx = wid_list.index(wid)
                listbox.selection_clear(0, "end")
                listbox.selection_set(idx)
                listbox.see(idx)
            except Exception:
                pass
            _sync_fields_from_selection()
            _redraw()

        def _on_select(_event=None):
            try:
                idx = int(listbox.curselection()[0])
                sel_var.set(wid_list[idx])
            except Exception:
                return
            _sync_fields_from_selection()
            _redraw()

        listbox.bind("<<ListboxSelect>>", _on_select)
        _sync_fields_from_selection()

        controls = tk.LabelFrame(left, text="Placement", bg="#0a1628", fg="#FFFFFF", bd=1, relief="groove")
        controls.pack(fill="x", pady=(0, 10))

        def _spin(parent, label, var, frm, to):
            rowf = tk.Frame(parent, bg="#0a1628")
            rowf.pack(fill="x", pady=3)
            tk.Label(rowf, text=label, bg="#0a1628", fg="#D3D3D3", width=10, anchor="w").pack(side="left")
            sp = tk.Spinbox(rowf, from_=frm, to=to, textvariable=var, width=6)
            sp.pack(side="left")

        _spin(controls, "Row", row_var, 0, rows - 1)
        _spin(controls, "Col", col_var, 0, cols - 1)
        _spin(controls, "Span C", sc_var, 1, cols)
        _spin(controls, "Span R", sr_var, 1, rows)

        def _apply_selected():
            wid = sel_var.get()
            if not wid:
                return
            working_layout[wid] = {
                "row": int(row_var.get()),
                "col": int(col_var.get()),
                "span_cols": int(sc_var.get()),
                "span_rows": int(sr_var.get()),
            }
            # Sanitize clamps values to grid and avoids overflows.
            nonlocal_working = self._sanitize_layout(working_layout)
            working_layout.clear()
            working_layout.update(nonlocal_working)
            status_var.set(f"Updated {wid}")
            _redraw()

        tk.Button(left, text="Apply Placement", command=_apply_selected, bg="#1A5F5F", fg="#FFFFFF").pack(
            fill="x", pady=(0, 8)
        )

        actions = tk.LabelFrame(left, text="Persistence", bg="#0a1628", fg="#FFFFFF", bd=1, relief="groove")
        actions.pack(fill="x", pady=(0, 10))

        def _load_from_user():
            prefs = getattr(self, "user_prefs", None)
            if prefs is None:
                status_var.set("No user context; cannot load user layout")
                return
            try:
                layout = prefs.get_widget_layout() or {}
                cleaned = self._sanitize_layout(layout)
                working_layout.clear()
                working_layout.update(cleaned)
                status_var.set("Loaded layout from user preferences")
                _redraw()
            except Exception as e:
                status_var.set(f"Load user failed: {e}")

        def _load_from_global():
            try:
                layout = self._load_saved_layout() or {}
                cleaned = self._sanitize_layout(layout)
                working_layout.clear()
                working_layout.update(cleaned)
                status_var.set("Loaded layout from Trinity settings")
                _redraw()
            except Exception as e:
                status_var.set(f"Load global failed: {e}")

        def _save_to_user():
            ok = self._persist_layout_to_user_preferences(working_layout)
            status_var.set(f"Save user: {'OK' if ok else 'FAILED'}")

        def _save_to_global():
            ok = self._persist_layout_to_settings(working_layout)
            status_var.set(f"Save global: {'OK' if ok else 'FAILED'}")

        def _reset_user():
            ok = self.reset_layout_in_user_preferences()
            if ok:
                working_layout.clear()
                working_layout.update(self.layout_for_widgets(widgets, prefer_saved=False))
                working_layout.update(self._sanitize_layout(working_layout))
            status_var.set(f"Reset user: {'OK' if ok else 'FAILED'}")
            _redraw()

        def _reset_global():
            ok = self.reset_layout_in_settings()
            if ok:
                working_layout.clear()
                working_layout.update(self.layout_for_widgets(widgets, prefer_saved=False))
                working_layout.update(self._sanitize_layout(working_layout))
            status_var.set(f"Reset global: {'OK' if ok else 'FAILED'}")
            _redraw()

        tk.Button(actions, text="Load (User)", command=_load_from_user, bg="#111a2a", fg="#FFFFFF").pack(fill="x", pady=2)
        tk.Button(actions, text="Load (Global)", command=_load_from_global, bg="#111a2a", fg="#FFFFFF").pack(fill="x", pady=2)
        tk.Button(actions, text="Save (User)", command=_save_to_user, bg="#123524", fg="#FFFFFF").pack(fill="x", pady=2)
        tk.Button(actions, text="Save (Global)", command=_save_to_global, bg="#123524", fg="#FFFFFF").pack(fill="x", pady=2)
        tk.Button(actions, text="Reset (User)", command=_reset_user, bg="#2a1a11", fg="#FFFFFF").pack(fill="x", pady=2)
        tk.Button(actions, text="Reset (Global)", command=_reset_global, bg="#2a1a11", fg="#FFFFFF").pack(fill="x", pady=2)

        # Grid canvas
        cell_w = 120
        cell_h = 52
        canvas_w = cols * cell_w
        canvas_h = rows * cell_h
        grid = tk.Canvas(right, width=canvas_w, height=canvas_h, bg="#06101a", highlightthickness=1, highlightbackground="#2F4F4F")
        grid.pack(fill="both", expand=True)

        def _cell_color_for(wid: str) -> str:
            try:
                w = widget_by_id.get(wid)
                if w is not None:
                    cfg = self.floor_configs.get(w.floor)
                    if cfg and isinstance(cfg.color, str) and cfg.color:
                        return cfg.color
            except Exception:
                pass
            return "#1A5F5F"

        def _occupancy():
            occ = {}
            for wid, e in (working_layout or {}).items():
                if not isinstance(wid, str) or not isinstance(e, dict):
                    continue
                try:
                    r = int(e.get("row", 0))
                    c = int(e.get("col", 0))
                    sc = int(e.get("span_cols", 1))
                    sr = int(e.get("span_rows", 1))
                except Exception:
                    continue
                for rr in range(r, min(rows, r + sr)):
                    for cc in range(c, min(cols, c + sc)):
                        key = (rr, cc)
                        if key in occ:
                            occ[key] = "!"  # collision marker
                        else:
                            occ[key] = wid
            return occ

        def _redraw():
            grid.delete("all")
            occ = _occupancy()
            selected = sel_var.get()

            for r in range(rows):
                for c in range(cols):
                    x1 = c * cell_w
                    y1 = r * cell_h
                    x2 = x1 + cell_w
                    y2 = y1 + cell_h
                    key = (r, c)
                    wid = occ.get(key)
                    fill = "#0b1a2a"
                    label = ""
                    if wid == "!":
                        fill = "#7a1f2b"
                        label = "COLLIDE"
                    elif isinstance(wid, str) and wid:
                        fill = _cell_color_for(wid)
                        label = wid[:12]
                        if wid == selected:
                            fill = "#B8860B"
                    grid.create_rectangle(x1 + 1, y1 + 1, x2 - 1, y2 - 1, fill=fill, outline="#0f2235")
                    grid.create_text(x1 + 6, y1 + 6, text=f"{r},{c}", anchor="nw", fill="#D3D3D3", font=("Consolas", 8))
                    if label:
                        grid.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=label, fill="#000000", font=("Consolas", 9, "bold"))

            # Selected outline for its top-left cell if present.
            if selected and selected in working_layout:
                e = working_layout[selected]
                try:
                    r = int(e.get("row", 0))
                    c = int(e.get("col", 0))
                    x1 = c * cell_w
                    y1 = r * cell_h
                    x2 = x1 + cell_w
                    y2 = y1 + cell_h
                    grid.create_rectangle(x1 + 3, y1 + 3, x2 - 3, y2 - 3, outline="#FFFFFF", width=2)
                except Exception:
                    pass

        def _on_grid_click(ev):
            c = int(ev.x // cell_w)
            r = int(ev.y // cell_h)
            if r < 0 or c < 0 or r >= rows or c >= cols:
                return
            selected = sel_var.get()
            occ = _occupancy()
            wid = occ.get((r, c))

            if selected:
                row_var.set(r)
                col_var.set(c)
                _apply_selected()
                return

            if isinstance(wid, str) and wid and wid != "!":
                _set_selected(wid)

        grid.bind("<Button-1>", _on_grid_click)

        _redraw()
        if wid_list:
            _set_selected(wid_list[0])

        if created_root:
            win.mainloop()

        return win

    def create_2d_window(self):
        """Create a 2D window representation of the Bento UI (for debugging/fallback)."""
        if not self.parent:
            root = tk.Tk()
        else:
            root = tk.Toplevel(self.parent)

        root.title("LightSpeed Bento UI")
        root.geometry("800x900")
        # Keep this consistent with the embeddable 2D frame (search/scope/recents/favs).
        try:
            palette = getattr(self, "palette", {}) or {}
            root.configure(bg=palette.get("accent_phthalo_green", "#0a1628"))
        except Exception:
            pass
        frame = self.create_2d_frame(root)
        frame.pack(fill="both", expand=True)

        return root

    def create_2d_frame(self, parent: tk.Misc) -> tk.Frame:
        """
        Create an embeddable 2D Bento UI frame.

        This is the same content as `create_2d_window()` but returns a Frame so it can be
        overlaid on top of a background canvas (e.g., the Construct/venv scene).
        """
        palette = getattr(self, "palette", {}) or {}
        ui_theme = getattr(self, "ui_theme", {}) or {}
        parent_bg = None
        try:
            parent_bg = parent.cget("bg")
        except Exception:
            parent_bg = None
        bg = parent_bg or palette.get("accent_phthalo_green", "#0a1628")
        btn_bg = palette.get("secondary", "#1a2332")
        btn_hover = palette.get("button_hover", btn_bg)
        text = palette.get("text_primary", "white")
        border = palette.get("border", "#2F4F4F")
        input_bg = palette.get("primary", "#0A4D4D")
        input_fg = palette.get("tortoise_eggshell", text)
        button_style = ui_theme.get("button_style", {}) if isinstance(ui_theme, dict) else {}
        if not isinstance(button_style, dict):
            button_style = {}
        btn_bg = str(button_style.get("fill_color", btn_bg) or btn_bg)
        btn_hover = str(button_style.get("hover_color", btn_hover) or btn_hover)
        button_shape = str(button_style.get("shape", "rounded")).strip().lower()
        button_radius_px = int(button_style.get("corner_radius_px", 12) or 12)
        button_border = str(button_style.get("border_color", border) or border)
        button_border_width = max(0, int(button_style.get("border_width_px", 1) or 1))
        button_relief = "flat" if button_shape in {"rounded", "pill", "smooth"} else "raised"
        button_highlight = max(0, min(2, button_border_width))

        font_body = ui_theme.get("font_body") if isinstance(ui_theme, dict) else None
        font_body = str(font_body).strip() if font_body else "Arial"
        font_title = ui_theme.get("font_title") if isinstance(ui_theme, dict) else None
        font_title = str(font_title).strip() if font_title else font_body
        font_code = ui_theme.get("font_code") if isinstance(ui_theme, dict) else None
        font_code = str(font_code).strip() if font_code else "Consolas"

        container = tk.Frame(parent, bg=bg)

        # Per-user UI preferences (best-effort). These are intentionally soft-fail so the
        # Bento menu still works when running without a user context.
        prefs = getattr(self, "user_prefs", None)

        def _get_pref(key: str, default: Any = None) -> Any:
            try:
                if prefs is not None and hasattr(prefs, "get_preference"):
                    return prefs.get_preference(key, default)
            except Exception:
                pass
            return default

        def _set_pref(key: str, value: Any) -> None:
            try:
                if prefs is not None and hasattr(prefs, "set_preference"):
                    prefs.set_preference(key, value)
            except Exception:
                pass

        # Tooltips (shared convention across Trinity UIs).
        show_tooltips = bool(_get_pref("ui.show_tooltips", _get_pref("show_tooltips", True)))
        try:
            tooltip_delay_ms = int(_get_pref("ui.tooltip_delay", _get_pref("tooltip_delay", 500)) or 500)
        except Exception:
            tooltip_delay_ms = 500

        def _attach_tooltip(widget: tk.Widget, tip_text: str) -> None:
            """Lightweight tooltip helper (no dependency imports)."""
            if (not show_tooltips) or (not tip_text) or (not hasattr(widget, "bind")):
                return

            state: Dict[str, Any] = {"after_id": None, "tip": None}

            def _hide(_e=None):
                try:
                    if state.get("after_id") is not None:
                        container.after_cancel(state["after_id"])
                except Exception:
                    pass
                state["after_id"] = None
                try:
                    tip = state.get("tip")
                    if tip is not None:
                        tip.destroy()
                except Exception:
                    pass
                state["tip"] = None

            def _show(ev):
                _hide()
                try:
                    tip = tk.Toplevel(container)
                    tip.wm_overrideredirect(True)
                    tip.attributes("-topmost", True)
                    tip.wm_geometry(f"+{int(ev.x_root) + 12}+{int(ev.y_root) + 12}")

                    tk.Label(
                        tip,
                        text=str(tip_text),
                        bg=btn_bg,
                        fg=text,
                        font=(font_body, 9),
                        relief="solid",
                        borderwidth=1,
                        padx=8,
                        pady=5,
                        wraplength=340,
                        justify="left",
                    ).pack()
                    state["tip"] = tip
                except Exception:
                    state["tip"] = None

            def _schedule_show(ev):
                _hide()
                try:
                    state["after_id"] = container.after(max(0, int(tooltip_delay_ms)), lambda: _show(ev))
                except Exception:
                    state["after_id"] = None

            widget.bind("<Enter>", _schedule_show)
            widget.bind("<Leave>", _hide)
            try:
                widget.bind("<ButtonPress>", _hide)
            except Exception:
                pass

        # Header: menu affordances (search) so this reads like an actual menu, not a distant overlay.
        header = tk.Frame(container, bg=bg)
        header.pack(side="top", fill="x", padx=10, pady=(10, 6))

        title = tk.Label(
            header,
            text="Menu",
            bg=bg,
            fg=text,
            font=(font_title, 14, "bold"),
        )
        title.pack(side="left")

        filter_var = tk.StringVar()

        filter_entry = tk.Entry(
            header,
            textvariable=filter_var,
            bg=input_bg,
            fg=input_fg,
            insertbackground=input_fg,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=border,
            highlightcolor=border,
            font=(font_body, 11),
        )
        filter_entry.pack(side="left", fill="x", expand=True, padx=10)
        filter_entry.insert(0, "Search...")

        def _filter_entry_focus_in(_e=None):
            try:
                if filter_entry.get().strip() == "Search...":
                    filter_entry.delete(0, "end")
            except Exception:
                pass

        def _filter_entry_focus_out(_e=None):
            try:
                if not filter_entry.get().strip():
                    filter_entry.insert(0, "Search...")
            except Exception:
                pass

        filter_entry.bind("<FocusIn>", _filter_entry_focus_in)
        filter_entry.bind("<FocusOut>", _filter_entry_focus_out)

        def _focus_search() -> None:
            try:
                filter_entry.focus_set()
                filter_entry.selection_range(0, "end")
            except Exception:
                return

        # Expose focus/search hook for host shells (N.py shortcuts).
        try:
            setattr(container, "_bento_focus_search", _focus_search)
        except Exception:
            pass

        # Scope + recents (open-world menu affordances).
        meta = tk.Frame(container, bg=bg)
        meta.pack(side="top", fill="x", padx=10, pady=(0, 6))

        scope_var = tk.StringVar(value="all")
        try:
            raw_scope = _get_pref("bento.scope", "all")
            if isinstance(raw_scope, str) and raw_scope.strip():
                scope_var.set(raw_scope.strip().lower())
        except Exception:
            pass

        tk.Label(
            meta,
            text="Scope:",
            bg=bg,
            fg=text,
            font=(font_body, 10, "bold"),
        ).pack(side="left")

        def _set_scope(value: str):
            value = (value or "all").strip().lower()
            if value not in {"all", "active", "fav", "recent"}:
                value = "all"
            scope_var.set(value)
            _set_pref("bento.scope", value)
            _render_widgets(filter_var.get())

        def _pill(parent: tk.Misc, label: str, value: str, var: tk.StringVar, on_set: Callable[[str], None]) -> tk.Button:
            def _refresh():
                cur = (var.get() or "").strip().lower()
                active = (cur == str(value).strip().lower())
                try:
                    b.configure(
                        relief=("sunken" if active else "raised"),
                        bg=(btn_hover if active else btn_bg),
                    )
                except Exception:
                    pass

            b = tk.Button(
                parent,
                text=label,
                command=lambda: on_set(value),
                bg=btn_bg,
                activebackground=btn_hover,
                fg=text,
                activeforeground=text,
                font=(font_body, 9, "bold"),
                relief=button_relief,
                bd=button_border_width,
                highlightbackground=button_border,
                highlightthickness=button_highlight,
                padx=10,
                pady=3,
            )
            # Local hover binding so this header section doesn't depend on later helpers.
            try:
                b.bind("<Enter>", lambda _e: b.configure(bg=btn_hover))
                b.bind("<Leave>", lambda _e: _refresh())
            except Exception:
                pass
            _refresh()
            try:
                var.trace_add("write", lambda *_a: _refresh())
            except Exception:
                pass
            return b

        s_all = _pill(meta, "All", "all", scope_var, _set_scope)
        s_active = _pill(meta, "Active", "active", scope_var, _set_scope)
        s_fav = _pill(meta, "Fav", "fav", scope_var, _set_scope)
        s_recent = _pill(meta, "Recent", "recent", scope_var, _set_scope)
        _attach_tooltip(s_all, "Show the full widget library.")
        _attach_tooltip(s_active, "Only show widgets for the active Z-floor.")
        _attach_tooltip(s_fav, "Only show your favorited widgets.")
        _attach_tooltip(s_recent, "Only show your most recently used widgets.")
        s_all.pack(side="left", padx=(8, 0))
        s_active.pack(side="left", padx=(6, 0))
        s_fav.pack(side="left", padx=(6, 0))
        s_recent.pack(side="left", padx=(6, 0))

        # Density affects readability vs information density in the 2D menu.
        density_var = tk.StringVar(value="comfortable")
        try:
            raw_density = _get_pref("bento.density", "comfortable")
            if isinstance(raw_density, str) and raw_density.strip():
                density_var.set(raw_density.strip().lower())
        except Exception:
            pass

        tk.Label(
            meta,
            text="  Density:",
            bg=bg,
            fg=text,
            font=(font_body, 10, "bold"),
        ).pack(side="left", padx=(12, 0))

        def _set_density(value: str) -> None:
            value = (value or "comfortable").strip().lower()
            if value not in {"comfortable", "compact"}:
                value = "comfortable"
            density_var.set(value)
            _set_pref("bento.density", value)
            _render_widgets(filter_var.get())

        d1 = _pill(meta, "Comfort", "comfortable", density_var, _set_density)
        d2 = _pill(meta, "Compact", "compact", density_var, _set_density)
        _attach_tooltip(d1, "Comfort: larger tiles, more readable.")
        _attach_tooltip(d2, "Compact: smaller tiles, more items per screen.")
        d1.pack(side="left", padx=(6, 0))
        d2.pack(side="left", padx=(6, 0))

        recents_row = tk.Frame(container, bg=bg)
        recents_row.pack(side="top", fill="x", padx=10, pady=(0, 8))
        tk.Label(
            recents_row,
            text="Recent:",
            bg=bg,
            fg=text,
            font=(font_body, 10, "bold"),
        ).pack(side="left")
        recents_strip = tk.Frame(recents_row, bg=bg)
        recents_strip.pack(side="left", fill="x", expand=True, padx=(8, 0))

        # Body wrapper
        body = tk.Frame(container, bg=bg)
        body.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))

        preview_panel = tk.Frame(body, bg=bg, width=280, highlightbackground=border, highlightthickness=1)
        preview_panel.pack(side="right", fill="y", padx=(10, 0))
        preview_panel.pack_propagate(False)

        preview_title_var = tk.StringVar(value="Select a widget")
        preview_meta_var = tk.StringVar(value="Click once to preview. Double-click or press Enter to open.")
        preview_desc_var = tk.StringVar(value="Right-click a tile to see all available actions.")
        selected_widget_id: Dict[str, str] = {"value": ""}

        tk.Label(
            preview_panel,
            textvariable=preview_title_var,
            bg=bg,
            fg=text,
            font=(font_title, 12, "bold"),
            wraplength=245,
            justify="left",
        ).pack(anchor="w", padx=12, pady=(12, 4))
        tk.Label(
            preview_panel,
            textvariable=preview_meta_var,
            bg=bg,
            fg=palette.get("muted_text", "#9aa5b1"),
            font=(font_body, 9),
            wraplength=245,
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 10))
        tk.Label(
            preview_panel,
            textvariable=preview_desc_var,
            bg=bg,
            fg=text,
            font=(font_body, 10),
            wraplength=245,
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 12))

        preview_actions = tk.Frame(preview_panel, bg=bg)
        preview_actions.pack(anchor="w", fill="x", padx=12, pady=(0, 12))

        # Create scrollable frame
        canvas = tk.Canvas(body, bg=bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=bg)

        scrollable_frame.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _safe_icon(value: Any) -> str:
            try:
                s = str(value)
            except Exception:
                return "?"
            # Common mojibake sequences from UTF-8 emojis in cp1252/latin-1.
            if "ðŸ" in s or "â" in s:
                return "?"
            if not s.strip():
                return "?"
            return s

        def _bind_hover(btn: tk.Button):
            try:
                btn.bind("<Enter>", lambda _e: btn.configure(bg=btn_hover))
                btn.bind("<Leave>", lambda _e: btn.configure(bg=btn_bg))
            except Exception:
                pass

        def _widget_by_id() -> Dict[str, BentoWidget]:
            out: Dict[str, BentoWidget] = {}
            for w in self.widgets:
                try:
                    if isinstance(getattr(w, "id", None), str) and w.id:
                        out[w.id] = w
                except Exception:
                    continue
            return out

        def _copy_to_clipboard(value: str) -> None:
            try:
                container.clipboard_clear()
                container.clipboard_append(str(value))
            except Exception:
                pass

        def _preview_widget(widget: BentoWidget) -> None:
            """Select a widget without executing it."""
            try:
                selected_widget_id["value"] = widget.id
            except Exception:
                selected_widget_id["value"] = ""

            cfg = widget.config if isinstance(widget.config, dict) else {}
            desc = str(cfg.get("description") or cfg.get("summary") or "No description registered yet.").strip()
            action_name = str(cfg.get("host_action") or "").strip()
            floor_name = self._floor_name_for_host(widget.floor) or str(widget.floor or "")

            preview_title_var.set(str(widget.title or widget.id))
            meta = f"{floor_name} / {widget.id}"
            if action_name:
                meta += f"\nAction: {action_name}"
            preview_meta_var.set(meta)
            preview_desc_var.set(desc)

            try:
                for child in list(preview_actions.winfo_children()):
                    child.destroy()
            except Exception:
                pass

            def _small_button(label: str, command: Callable[[], None]) -> None:
                b = tk.Button(
                    preview_actions,
                    text=label,
                    command=command,
                    bg=btn_bg,
                    activebackground=btn_hover,
                    fg=text,
                    activeforeground=text,
                    font=(font_body, 9, "bold"),
                    relief=button_relief,
                    bd=button_border_width,
                    highlightbackground=button_border,
                    highlightthickness=button_highlight,
                    padx=8,
                    pady=3,
                )
                _bind_hover(b)
                b.pack(fill="x", pady=(0, 6))

            _small_button("Open / Run", lambda _w=widget: _on_widget_click(_w))
            _small_button("Set Active Floor", lambda _w=widget: _set_active_floor_from_widget(_w))
            _small_button("Copy Widget ID", lambda _w=widget: _copy_to_clipboard(_w.id))

        def _refresh_recents_row() -> None:
            try:
                for child in list(recents_strip.winfo_children()):
                    child.destroy()
            except Exception:
                pass

            by_id = _widget_by_id()
            recent_ids = []
            try:
                recent_ids = self.get_recent_widget_ids(limit=6)
            except Exception:
                recent_ids = []

            for wid in recent_ids:
                w = by_id.get(wid)
                if w is None:
                    continue
                title = str(getattr(w, "title", wid))
                max_len = 18 if (density_var.get() or "").strip().lower() != "compact" else 14
                if len(title) > max_len:
                    title = title[: max(1, max_len - 2)].rstrip() + ".."
                chip = tk.Button(
                    recents_strip,
                    text=title,
                    bg=btn_bg,
                    activebackground=btn_hover,
                    fg=text,
                    activeforeground=text,
                    font=(font_body, 9, "bold"),
                    relief="raised",
                    bd=1,
                    padx=8,
                    pady=3,
                    command=lambda _w=w: _on_widget_click(_w),
                )
                _bind_hover(chip)
                try:
                    desc = str((w.config or {}).get("description", "") or "")
                except Exception:
                    desc = ""
                _attach_tooltip(chip, f"{w.title}\n{w.floor}\n{desc}".strip())
                chip.pack(side="left", padx=(0, 6), pady=2)

            if not recent_ids:
                empty = tk.Label(
                    recents_strip,
                    text="No recent items yet.",
                    bg=bg,
                    fg=palette.get("muted_text", "#9aa5b1"),
                    font=(font_body, 9, "italic"),
                )
                empty.pack(side="left", padx=(0, 6), pady=2)

        def _on_widget_click(widget: BentoWidget) -> None:
            try:
                self.handle_widget_click(widget.id)
            finally:
                # Recents/favs UI should update immediately.
                try:
                    _refresh_recents_row()
                except Exception:
                    pass
                try:
                    _render_widgets(filter_var.get())
                except Exception:
                    pass

        def _show_widget_menu(ev, widget: BentoWidget) -> None:
            try:
                menu = tk.Menu(container, tearoff=0, bg=btn_bg, fg=text)
                is_fav = False
                try:
                    is_fav = bool(self.is_favorite_widget(widget.id))
                except Exception:
                    is_fav = False

                menu.add_command(label="Preview", command=lambda _w=widget: _preview_widget(_w))
                menu.add_command(label="Open / Run", command=lambda _w=widget: _on_widget_click(_w))
                menu.add_separator()
                menu.add_command(
                    label=("Unfavorite" if is_fav else "Favorite"),
                    command=lambda _w=widget: _toggle_fav(_w),
                )
                menu.add_separator()
                menu.add_command(
                    label="Set Active Floor",
                    command=lambda _w=widget: _set_active_floor_from_widget(_w),
                )
                menu.add_command(
                    label="Open Owning Floor",
                    command=lambda _w=widget: _open_owning_floor(_w),
                )
                menu.add_separator()
                menu.add_command(label="Copy Widget ID", command=lambda _w=widget: _copy_to_clipboard(_w.id))
                menu.add_command(label="Copy Title", command=lambda _w=widget: _copy_to_clipboard(_w.title))
                try:
                    menu.tk_popup(int(ev.x_root), int(ev.y_root))
                finally:
                    try:
                        menu.grab_release()
                    except Exception:
                        pass
            except Exception:
                return

        def _toggle_fav(widget: BentoWidget) -> None:
            try:
                self.toggle_favorite_widget(widget.id)
            except Exception:
                pass
            try:
                _render_widgets(filter_var.get())
            except Exception:
                pass
            try:
                _refresh_recents_row()
            except Exception:
                pass

        def _set_active_floor_from_widget(widget: BentoWidget) -> None:
            try:
                self.set_active_floor(widget.floor)
            except Exception:
                pass
            try:
                _set_scope("active")
            except Exception:
                pass

        def _open_owning_floor(widget: BentoWidget) -> None:
            host = getattr(self, "parent", None) or getattr(self, "host", None)
            floor_name = self._floor_name_for_host(widget.floor)
            if host is not None and floor_name and hasattr(host, "open_z_floor"):
                try:
                    host.open_z_floor(floor_name)
                except Exception:
                    pass

        def _render_widgets(filter_text: str):
            # Clear existing widgets
            for child in list(scrollable_frame.winfo_children()):
                try:
                    child.destroy()
                except Exception:
                    pass

            needle = (filter_text or "").strip().lower()
            if needle == "search...":
                needle = ""

            def _matches(w: BentoWidget) -> bool:
                if not needle:
                    return True
                try:
                    desc = str((w.config or {}).get("description", "") or "")
                except Exception:
                    desc = ""
                hay = " ".join([str(getattr(w, "title", "")), str(getattr(w, "floor", "")), desc]).lower()
                return needle in hay

            # Grid layout for widgets
            current_floor = None
            row = 0
            col = 0

            visible_widgets = [w for w in self.widgets if _matches(w)]

            scope = (scope_var.get() or "all").strip().lower()
            if scope == "active":
                try:
                    af = getattr(self, "active_floor", None)
                    if isinstance(af, str) and af.strip():
                        visible_widgets = [w for w in visible_widgets if w.floor == af]
                except Exception:
                    pass
            elif scope == "fav":
                favs = set()
                try:
                    favs = set(self.get_favorite_widget_ids())
                except Exception:
                    favs = set()
                if favs:
                    visible_widgets = [w for w in visible_widgets if w.id in favs]
                else:
                    visible_widgets = []
            elif scope == "recent":
                # Keep recent order, but still honor the text filter.
                try:
                    by_id = _widget_by_id()
                except Exception:
                    by_id = {}
                ids = []
                try:
                    ids = self.get_recent_widget_ids(limit=50)
                except Exception:
                    ids = []
                ordered = []
                for wid in ids:
                    w = by_id.get(wid)
                    if w is not None and _matches(w):
                        ordered.append(w)
                visible_widgets = ordered

            tile_buttons: List[tk.Button] = []

            def _bind_grid_keyboard(btn: tk.Button, index: int, widget: BentoWidget) -> None:
                def _focus(target: int) -> str:
                    try:
                        if 0 <= target < len(tile_buttons):
                            tile_buttons[target].focus_set()
                    except Exception:
                        pass
                    return "break"

                try:
                    btn.bind("<Return>", lambda _e, w=widget: (_on_widget_click(w), "break")[1])
                    btn.bind("<space>", lambda _e, w=widget: (_on_widget_click(w), "break")[1])
                    btn.bind("<Right>", lambda _e, i=index: _focus(i + 1))
                    btn.bind("<Left>", lambda _e, i=index: _focus(i - 1))
                    btn.bind("<Down>", lambda _e, i=index: _focus(i + max(1, int(self.grid_cols))))
                    btn.bind("<Up>", lambda _e, i=index: _focus(i - max(1, int(self.grid_cols))))
                except Exception:
                    pass

            for widget in visible_widgets:
                # Add floor separator
                if widget.floor != current_floor:
                    floor_color = "#00DDFF"
                    try:
                        floor_color = self.floor_configs[widget.floor].color
                    except Exception:
                        pass
                    floor_label = tk.Label(
                        scrollable_frame,
                        text=f"=== {widget.floor} ===",
                        bg=bg,
                        fg=floor_color,
                        font=(font_code, 12, "bold"),
                    )
                    floor_label.grid(row=row, column=0, columnspan=self.grid_cols, pady=(12, 8), sticky="ew")
                    row += 1
                    col = 0
                    current_floor = widget.floor

                # Create widget button
                icon = _safe_icon((widget.config or {}).get("icon", "?"))
                fav_mark = ""
                try:
                    fav_mark = " *" if self.is_favorite_widget(widget.id) else ""
                except Exception:
                    fav_mark = ""
                density = (density_var.get() or "comfortable").strip().lower()
                if density == "compact":
                    tile_font = (font_body, 11, "bold")
                    tile_w, tile_h, tile_wrap = 16, 3, 120
                    tile_padx, tile_pady = 5, 5
                else:
                    tile_font = (font_body, 12, "bold")
                    tile_w, tile_h, tile_wrap = 18, 4, 140
                    tile_padx, tile_pady = 6, 6

                btn = tk.Button(
                    scrollable_frame,
                    text=f"{icon}{fav_mark}\n{widget.title}",
                    bg=btn_bg,
                    activebackground=btn_hover,
                    fg=text,
                    activeforeground=text,
                    font=tile_font,
                    width=tile_w,
                    height=tile_h,
                    wraplength=tile_wrap,
                    justify="center",
                    relief=button_relief,
                    bd=max(1, button_border_width),
                    highlightbackground=button_border,
                    highlightthickness=button_highlight,
                    command=lambda w=widget: _preview_widget(w),
                )
                try:
                    btn._lightspeed_corner_radius_px = button_radius_px
                except Exception:
                    pass
                _bind_hover(btn)
                btn.grid(row=row, column=col, padx=tile_padx, pady=tile_pady, sticky="nsew")
                try:
                    btn.bind("<Button-3>", lambda e, w=widget: _show_widget_menu(e, w))
                except Exception:
                    pass
                try:
                    btn.bind("<Double-Button-1>", lambda _e, w=widget: (_on_widget_click(w), "break")[1])
                except Exception:
                    pass
                tile_buttons.append(btn)
                _bind_grid_keyboard(btn, len(tile_buttons) - 1, widget)
                try:
                    desc = str((widget.config or {}).get("description", "") or "")
                except Exception:
                    desc = ""
                _attach_tooltip(btn, f"{widget.title}\n{widget.floor}\n{desc}".strip())

                col += 1
                if col >= self.grid_cols:
                    col = 0
                    row += 1

            for c in range(max(1, int(self.grid_cols))):
                try:
                    scrollable_frame.grid_columnconfigure(c, weight=1)
                except Exception:
                    pass

            if visible_widgets and not selected_widget_id.get("value"):
                try:
                    _preview_widget(visible_widgets[0])
                except Exception:
                    pass

        def _apply_filter(_e=None):
            try:
                _render_widgets(filter_var.get())
            except Exception:
                pass

        def _clear_filter():
            try:
                filter_var.set("")
                filter_entry.delete(0, "end")
                filter_entry.insert(0, "Search...")
                _render_widgets("")
            except Exception:
                pass

        clear_btn = tk.Button(
            header,
            text="Clear",
            command=_clear_filter,
            bg=btn_bg,
            activebackground=btn_hover,
            fg=text,
            activeforeground=text,
            font=(font_body, 10, "bold"),
            relief=button_relief,
            bd=button_border_width,
            highlightbackground=button_border,
            highlightthickness=button_highlight,
            padx=10,
            pady=4,
        )
        _bind_hover(clear_btn)
        clear_btn.pack(side="right")

        filter_entry.bind("<KeyRelease>", _apply_filter)

        # Mouse wheel scrolling for the menu (more game-like).
        def _on_wheel(ev):
            try:
                delta = int(getattr(ev, "delta", 0))
                if delta:
                    canvas.yview_scroll(int(-1 * (delta / 120)), "units")
            except Exception:
                pass

        for w in (canvas, scrollable_frame, body, container):
            try:
                w.bind("<MouseWheel>", _on_wheel)
            except Exception:
                pass

        _refresh_recents_row()
        _render_widgets("")

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return container


# Global instance
_bento_system: Optional[UniversalBentoSystem] = None


def get_bento_system() -> UniversalBentoSystem:
    """Get the global Bento system instance"""
    global _bento_system
    if _bento_system is None:
        _bento_system = UniversalBentoSystem()
    return _bento_system


def register_floor_widgets(floor_id: str, widgets: List[BentoWidget]):
    """Convenience function to register widgets for a floor"""
    return get_bento_system().register_floor_widgets(floor_id, widgets)


# Export key items
__all__ = [
    'UniversalBentoSystem',
    'BentoWidget',
    'BentoWidgetType',
    'FloorBentoConfig',
    'get_bento_system',
    'register_floor_widgets'
]
