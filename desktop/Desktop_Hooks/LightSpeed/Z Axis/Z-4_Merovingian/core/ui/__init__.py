"""
LightSpeed core UI compatibility namespace.

Merovingian owns the stable `core.ui` import path. Active UI implementations
live in Trinity (`Z+3_Trinity/ui`) and Construct (`Z0_TheConstruct/ui`), so this
package extends its search path to those floor-owned modules and only imports
surfaces that still exist after the Z-axis cleanup.
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any


def _find_lightspeed_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
            return candidate
    return Path.cwd()


_LIGHTSPEED_ROOT = _find_lightspeed_root()
_TRINITY_UI = _LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "ui"
_CONSTRUCT_UI = _LIGHTSPEED_ROOT / "Z Axis" / "Z0_TheConstruct" / "ui"

for _path in (_TRINITY_UI, _CONSTRUCT_UI):
    try:
        if _path.exists():
            __path__.append(str(_path))  # type: ignore[name-defined]
    except Exception:
        pass


def _optional(module_name: str, names: tuple[str, ...]) -> bool:
    try:
        module = import_module(f"{__name__}.{module_name}")
    except Exception:
        return False
    for name in names:
        if hasattr(module, name):
            globals()[name] = getattr(module, name)
    return True


HAS_GLASS_UI = _optional(
    "glass_ui",
    (
        "GlassUIManager",
        "GlassMaterial",
        "GlassPanel",
        "GlassButton",
        "GlassFrame",
        "GLASS_MATERIALS",
        "ROMER_GLASS_COLORS",
        "apply_romer_theme",
        "create_glass_ui_manager",
        "tk_safe_color",
    ),
)

HAS_ICON_LIBRARY = _optional(
    "icon_library_glass",
    ("IconLibraryManager", "IconDefinition", "IconCategory", "IconMaterial", "create_icon_library"),
)

HAS_SPHERICAL_GLASS = _optional(
    "enhanced_spherical_glass_ui",
    ("EnhancedSphericalGlassUI", "AchillesBubble", "GlassWidget3D"),
)
HAS_SPHERICAL_UI = _optional("spherical_ui", ("EquirectangularUI", "Widget3D"))

HAS_BASE_PORTAL = _optional(
    "base_portal_glass",
    ("PortalTheme", "BentoConstraints", "SpecForm", "find_lightspeed_root"),
)

HAS_SETTINGS_PANEL = _optional("settings_panel", ("SettingsPanel",))
HAS_BENTO_HUB = _optional("unified_bento_hub", ("UnifiedBentoHub",))

HAS_TEMPLATE_MANAGER = _optional("template_manager", ("TemplateManagerDialog", "show_template_manager"))
HAS_SETTINGS_MANAGER = _optional(
    "settings_manager",
    ("SettingsManager", "LightSpeedSettings", "get_settings_manager", "get_settings"),
)
HAS_THEMES = _optional(
    "themes",
    ("ThemeManager", "create_theme_toggle_button", "get_light_colors", "get_dark_colors"),
)
HAS_SMART_THEME = _optional(
    "smart_theme",
    ("SmartThemeExtractor", "get_smart_theme_extractor", "create_theme_from_image"),
)
HAS_TOWER_3D = _optional(
    "tower_3d_view",
    ("Tower3DVisualization", "Floor3DView", "Floor3DObject", "show_tower_3d_view"),
)
HAS_CONSTRUCT_3D = _optional(
    "immersive_3d_engine",
    ("Immersive3DEngine", "Camera", "Vector3D", "Interactive3DObject"),
)


__version__ = "5.1.2"
__author__ = "LightSpeed Team / ACHILLES"

__all__ = sorted(
    name
    for name, value in globals().items()
    if not name.startswith("_")
    and name not in {"Any", "Path", "import_module"}
    and (name.startswith("HAS_") or isinstance(value, (type, str)) or callable(value))
)
