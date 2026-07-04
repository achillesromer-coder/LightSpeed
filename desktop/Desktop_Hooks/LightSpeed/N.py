#!/usr/bin/env python
"""
N.py - LightSpeed Unified Orchestrator
Complete 200% Implementation - All systems integrated

This is THE ONE entry point for LightSpeed platform.
Consolidates:
- lightspeed_complete_gui.py (navigation, screens, database)
- lightspeed_immersive_complete.py (TTK styling, event queue, enhanced DB)
- N.py CLI (service integration, floor navigation, tests)
- Framework layer (themes, settings, widgets, API manager)

Features:
- Dual-mode: Client (guided) vs IT/Founder (god mode)
- Login system: UI-only; users are stored in DB via Setup Wizard
- All 14 PDF screens implemented
- 8 Z-floors fully integrated
- Framework layer: themes, settings, widgets, API management
- Unified database (core.services)
- First-run wizard integration
- Event queue for real-time updates
- TTK styled components
- Keyboard shortcuts
- Achilles AI interface (ready for Ollama)
- Document viewer + Project tree
- NO stub code - all features functional

Author: Romer Industries / EMASSC / LightSpeed Team
Version: 0.9.7 - ENHANCED RELEASE
Date: January 13, 2026

New in V0.9.7 (January 2026):
- DOME PROJECTION ENGINE: Full FPS mouse-look controls (360-degree horizontal, 180-degree vertical)
- UI ANCHORING: Widgets stay 1.5m from player viewpoint (billboard effect)
- BENTO SYSTEM: 3-step widget management (Select -> Configure -> Confirm)
- ROLLING HILLS: Windows 97-style immersive environment
- SMART MENUS: Simplified configuration approach (no complex nested menus)
- Trinity Collaboration Hub (3-way AI collaboration with M1-2/2-3 methodology)
- Weighted voting system (User 51%, Claude 24.5%, Codex 24.5%)
- Smart Floor template system (Merovingian-based, Z Direct deployment)
- Template Engine with automated component generation
- Comprehensive library analysis (331 libraries across 1,128 files)
- Library enhancement plan with cross-platform optimization
- Complete Z Direct inter-floor communication (63 files, 9 floors)
- Standardized directory structures across all floors
- File upload and code drop collaboration features
- Real-time proposal tracking and vote aggregation
- 17 templates deployed across all Z-Axis floors

New in V1.0.0:
- Oracle Smart Floor Integrator (automatic file ingestion & distribution)
- Smith Inter-Floor Coordinator (9-floor task coordination)
- Smith Task Queue with intelligent prioritization
- Encyclopedia System (3 volumes: Empirical, Economic, Applied)
- Multilingual Dictionary (30+ terms, 5 languages)
- Spherical 360-degree UI Projection (immersive Z-floor navigation)
- Neo AI Sign-Off System (intelligent task approval)
- Database schema enhancements (encyclopedia_entries, interfloor_tasks)
- Complete inter-floor communication via Event Bus
- 34 foundation constants and SI units pre-loaded
"""

# CODEX NOTE (2026-02-06):
# - Canonical spec/tracking: `dataindex/02_MASTER_BUILD_SPEC_SHEET.md`
# - Working log: `ai_logs/open_dialogue/OPEN_DIALOGUE_CODEX.md` (0111+)
# - Direction lock: UI-first (Bento is the primary readable/clickable UI); 3D is ambient background; immersive is opt-in.

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import threading
import queue
import argparse
import json
import re
import base64
import hashlib
import hmac
import secrets

# Add paths
LIGHTSPEED_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(LIGHTSPEED_ROOT))
sys.path.insert(0, str(LIGHTSPEED_ROOT / "Z Axis"))

# Transitional package roots (until everything is fully floor-native).
_Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"
_TRINITY_ROOT = _Z_AXIS_ROOT / "Z+3_Trinity"
_MEROVINGIAN_ROOT = _Z_AXIS_ROOT / "Z-4_Merovingian"

def _syspath_ensure(path: Path, *, front: bool = False) -> None:
    """Ensure a path is on sys.path; optionally move it to the front."""
    try:
        p = str(path)
        if front:
            while p in sys.path:
                sys.path.remove(p)
            sys.path.insert(0, p)
        else:
            if p not in sys.path:
                sys.path.append(p)
    except Exception:
        return


# Canonical package roots:
# - `ui.*` lives under Trinity (must win the `ui` namespace)
# - `core.*` lives under Merovingian (must not shadow `ui.*`)
_syspath_ensure(_TRINITY_ROOT, front=True)
_syspath_ensure(_MEROVINGIAN_ROOT, front=False)

_CANONICAL_RUNTIME_CANDIDATES = [
    LIGHTSPEED_ROOT / "canonical_runtime",
    LIGHTSPEED_ROOT.parent.parent / "LightSpeed_Runtime",
]


def _resolve_canonical_runtime_root() -> Optional[Path]:
    for candidate in _CANONICAL_RUNTIME_CANDIDATES:
        try:
            if candidate.exists():
                return candidate.resolve()
        except Exception:
            continue
    return None


CANONICAL_RUNTIME_ROOT = _resolve_canonical_runtime_root()
if CANONICAL_RUNTIME_ROOT is not None:
    # Canonical runtime must win the `lightspeed_runtime` package namespace.
    # The desktop shell also has a compatibility package with the same name,
    # but it does not contain the generated agent-home bridge.
    _syspath_ensure(CANONICAL_RUNTIME_ROOT, front=True)


def _force_canonical_runtime_package() -> None:
    """Purge cached desktop-runtime modules when the generated runtime exists."""
    if CANONICAL_RUNTIME_ROOT is None:
        return

    try:
        canonical_marker = str(CANONICAL_RUNTIME_ROOT).replace("\\", "/").lower()
    except Exception:
        return

    mod = sys.modules.get("lightspeed_runtime")
    if not mod:
        return

    mod_file = (getattr(mod, "__file__", "") or "").replace("\\", "/").lower()
    mod_path = (getattr(mod, "__path__", [""]) or [""])[0]
    mod_path = str(mod_path).replace("\\", "/").lower()
    if canonical_marker in mod_file or canonical_marker in mod_path:
        return

    # `__main__.py` can import the compatibility package before this module
    # loads. Remove it so generated modules such as agent_home_bridge resolve.
    for key in list(sys.modules.keys()):
        if key == "lightspeed_runtime" or key.startswith("lightspeed_runtime."):
            sys.modules.pop(key, None)


_force_canonical_runtime_package()


def _force_trinity_ui_package() -> None:
    """
    Ensure the top-level `ui` package resolves to Trinity.

    Some floor folders may also contain a top-level `ui` directory. If `ui` is
    imported from a non-Trinity location first (e.g., when launching via
    `python -m LightSpeed`), `ui.*` imports will later fail. This guard keeps
    the canonical Trinity UI package authoritative.
    """
    try:
        if _TRINITY_ROOT.exists():
            _syspath_ensure(_TRINITY_ROOT, front=True)
    except Exception:
        return

    mod = sys.modules.get("ui")
    if not mod:
        return

    mod_file = (getattr(mod, "__file__", "") or "").replace("\\", "/")
    if "Z+3_Trinity" in mod_file:
        return

    # Purge cached non-canonical `ui` modules so re-import binds to Trinity.
    for key in list(sys.modules.keys()):
        if key == "ui" or key.startswith("ui."):
            sys.modules.pop(key, None)


def _bootstrap_canonical_runtime(index_limit_per_source: int = 20) -> Optional[Dict[str, Any]]:
    if CANONICAL_RUNTIME_ROOT is None:
        return None
    try:
        from lightspeed_runtime.agent_home_bridge import AgentHomeBridge
        from lightspeed_runtime.floor_bridges import NeoAchillesBridge, OracleMorpheusBridge, TrinityShellBridge
        from lightspeed_runtime.runtime import LightSpeedRuntime

        runtime = LightSpeedRuntime(root=CANONICAL_RUNTIME_ROOT)
        runtime.bootstrap(index_limit_per_source=index_limit_per_source)
        knowledge_bridge = OracleMorpheusBridge(runtime)
        shell_bridge = TrinityShellBridge(runtime)
        neo_bridge = NeoAchillesBridge(runtime, knowledge_bridge)
        agent_home_bridge = None
        try:
            candidate = AgentHomeBridge.from_runtime_root(runtime.root)
            candidate.agent_environment()
            agent_home_bridge = candidate
        except Exception as exc:
            print(f"[WARNING] Agent home bridge unavailable: {exc}")
        return {
            "runtime": runtime,
            "oracle_morpheus_bridge": knowledge_bridge,
            "trinity_shell_bridge": shell_bridge,
            "neo_achilles_bridge": neo_bridge,
            "agent_home_bridge": agent_home_bridge,
        }
    except Exception as exc:
        print(f"[WARNING] Canonical runtime unavailable: {exc}")
        return None

# Optional immersive modules (may live in archived oracle tree)
IMMERSIVE_MODULES_PATHS = [
    LIGHTSPEED_ROOT / "Z Axis" / "Z-2_Oracle" / "immersive_modules",
    LIGHTSPEED_ROOT / "Z Axis" / "Z-2_Oracle" / "legacy" / "Z-1_Oracle" / "immersive_modules",
]
for _p in IMMERSIVE_MODULES_PATHS:
    try:
        if _p.exists():
            sys.path.insert(0, str(_p))
    except Exception:
        pass

# Tkinter
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext

# Premium Theme Engine (Trinity Z+3)
try:
    _force_trinity_ui_package()
    from ui.premium_theme_engine import get_theme_engine, ThemeMode
    HAS_PREMIUM_THEME = True
except ImportError as e:
    print(f"[INFO] Premium theme engine not available: {e}")
    HAS_PREMIUM_THEME = False

# ---------------------------------------------------------------------------
# Floor-native dynamic imports (avoid invalid package names like Z+2_Neo)
# ---------------------------------------------------------------------------
from importlib.util import module_from_spec, spec_from_file_location


def _load_symbol_from_file(rel_path: str, symbol: str):
    """
    Load a symbol (class/function/const) from a file by relative path.

    This is the canonical way to reference floor-owned modules because folders
    like `Z+2_Neo` are not valid Python package names.
    """
    path = (LIGHTSPEED_ROOT / rel_path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    mod_name = f"lightspeed_dynamic_{path.stem}_{abs(hash(str(path)))%1_000_000}"
    spec = spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    mod = module_from_spec(spec)
    # Ensure dataclasses/type evaluation can resolve __module__ via sys.modules.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    if not hasattr(mod, symbol):
        raise AttributeError(f"{symbol} not found in {path}")
    return getattr(mod, symbol)

# PIL for enhanced graphics
try:
    from PIL import Image, ImageTk, ImageDraw, ImageFilter
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Core services (MUST be available)
try:
    from core.services import (
        initialize_services, shutdown_services,
        get_db, get_event_bus, get_storage,
        get_user_preferences  # User preferences support
    )
    HAS_SERVICES = True
except ImportError as e:
    print(f"[CRITICAL] Cannot import core services: {e}")
    print("Run: pip install -r \"Z Axis/Z+3_Trinity/requirements/requirements.txt\"")
    _CORE_SERVICE_ERROR = str(e)
    HAS_SERVICES = False

    def initialize_services():
        raise RuntimeError(f"Core services unavailable: {_CORE_SERVICE_ERROR}")

    def shutdown_services():
        return None

    def get_db():
        raise RuntimeError(f"Core services unavailable: {_CORE_SERVICE_ERROR}")

    def get_event_bus():
        raise RuntimeError(f"Core services unavailable: {_CORE_SERVICE_ERROR}")

    def get_storage():
        raise RuntimeError(f"Core services unavailable: {_CORE_SERVICE_ERROR}")

    def get_user_preferences():
        return {}

# Floor Loader (Dynamic Z-floor component loading)
try:
    from core.services.floor_loader import FloorLoader
    HAS_FLOOR_LOADER = True
except ImportError as e:
    print(f"[WARNING] FloorLoader not available: {e}")
    HAS_FLOOR_LOADER = False

# Data Accumulation (Objectification layer)
try:
    from core.services.data_accumulation_engine import DataAccumulationEngine
    HAS_DATA_ACCUMULATION = True
except ImportError as e:
    print(f"[WARNING] DataAccumulationEngine not available: {e}")
    HAS_DATA_ACCUMULATION = False

# Framework layer
try:
    from core.ui.themes import ThemeManager
    from core.ui.settings_manager import SettingsManager
    from core.ui.dashboard_widgets import (
        OKRWidget, NotesWidget, TaskListWidget, CalendarWidget,
        NoticesWidget, QuickLinksWidget,
        BackgroundJobsWidget, APITogglesWidget, DependencyMapWidget
    )
    from core.api.api_manager import APIManager
    from core.project_manager import (
        ProjectManager, FileHandler, ProjectEnvironment,
        ToolRegistry, create_project_manager
    )
    HAS_PROJECT_MANAGER = True
    HAS_FRAMEWORK = True
except ImportError as e:
    print(f"[WARNING] Framework layer not fully available: {e}")
    HAS_FRAMEWORK = False
    HAS_PROJECT_MANAGER = False

# Wizards (floor-native under Trinity; loaded by file to avoid package naming issues)
StartupWizard = None
launch_setup_wizard_ui = None
launch_cognigrex_setup_wizard = None
HAS_WIZARDS = False
try:
    StartupWizard = _load_symbol_from_file("Z Axis/Z+3_Trinity/wizards/startup_wizard.py", "StartupWizard")
    HAS_WIZARDS = True
except Exception as _e:
    print(f"[!] Startup wizard not available: {_e}")
try:
    launch_setup_wizard_ui = _load_symbol_from_file(
        "Z Axis/Z+3_Trinity/wizards/setup_wizard.py",
        "launch_setup_wizard_ui",
    )
    HAS_WIZARDS = True
except Exception as _e:
    print(f"[!] Setup wizard (legacy) not available: {_e}")
try:
    launch_cognigrex_setup_wizard = _load_symbol_from_file(
        "Z Axis/Z+3_Trinity/wizards/cognigrex_setup_wizard.py",
        "launch_setup_wizard",
    )
    HAS_WIZARDS = True
except Exception as _e:
    print(f"[!] Cognigrex setup wizard not available: {_e}")

# Open Dialogue Board (Codex / Claude / User message board; Trinity-owned tool)
try:
    launch_dialogue_board = _load_symbol_from_file(
        "Z Axis/Z+3_Trinity/tools/open_dialogue_board.py",
        "launch_dialogue_board",
    )
    HAS_OPEN_DIALOGUE_BOARD = True
except Exception as _e:
    HAS_OPEN_DIALOGUE_BOARD = False
    print(f"[!] Open Dialogue Board not available: {_e}")

# IT Portal
try:
    ITPortal = _load_symbol_from_file("Z Axis/Z+3_Trinity/ui/it_portal.py", "ITPortal")
    HAS_IT_PORTAL = True
except Exception as _e:
    HAS_IT_PORTAL = False
    print(f"[!] IT Portal not available: {_e}")

# Trinity Immersive UI (360/portal shell)
try:
    ImmersiveInterface = _load_symbol_from_file("Z Axis/Z+3_Trinity/ui/immersive_interface.py", "ImmersiveInterface")
    HAS_TRINITY_IMMERSIVE_UI = True
except Exception:
    HAS_TRINITY_IMMERSIVE_UI = False

# Immersive modules
try:
    # Preferred: packaged under `immersive_modules/`
    from immersive_modules import DocumentViewer, ProjectTreeViewer
    HAS_MODULES = True
except ImportError:
    try:
        # Legacy layout (direct modules on sys.path)
        from document_viewer import DocumentViewer
        from project_tree import ProjectTreeViewer
        HAS_MODULES = True
    except ImportError:
        HAS_MODULES = False
        print("[!] Immersive modules not available")

# Z-floor modules - Using new standardized entry points
Z_FLOORS_AVAILABLE: Dict[str, Any] = {}

# Map floor names to their directory locations
FLOOR_LOCATIONS = {
    'Merovingian': 'Z Axis/Z-4_Merovingian',  # Core services (always available)
    # Canonical floor entrypoints live in `Z Axis/<Floor>.py` (manifest-owned).
    'Smith': 'Z Axis/Smith.py',
    'Oracle': 'Z Axis/Oracle.py',
    'Morpheus': 'Z Axis/Morpheus.py',
    'TheConstruct': 'Z Axis/TheConstruct.py',
    'Architect': 'Z Axis/Architect.py',
    'Neo': 'Z Axis/Neo.py',
    'Trinity': 'Z Axis/Trinity.py',
}


def _resolve_floor_entry_path(floor_name: str) -> Optional[Path]:
    if floor_name == "Merovingian":
        return None
    floor_path = FLOOR_LOCATIONS.get(floor_name)
    if not floor_path:
        return None
    return (LIGHTSPEED_ROOT / floor_path).resolve()


def _is_floor_entry_available(floor_name: str) -> bool:
    path = _resolve_floor_entry_path(floor_name)
    return bool(path and path.exists())


def _build_shell_startup_audit() -> dict[str, Any]:
    optional_targets = {
        "premium_theme_engine": LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "ui" / "premium_theme_engine.py",
        "smart_settings_hub": LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "ui" / "smart_settings_hub.py",
        "it_portal": LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "ui" / "it_portal.py",
        "startup_wizard": LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "wizards" / "startup_wizard.py",
        "open_dialogue_board": LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "tools" / "open_dialogue_board.py",
        "core_services": LIGHTSPEED_ROOT / "Z Axis" / "Z-4_Merovingian" / "core" / "services" / "__init__.py",
    }
    missing_targets = {
        name: str(path)
        for name, path in optional_targets.items()
        if not path.exists()
    }
    floor_status = {
        floor_name: _is_floor_entry_available(floor_name)
        for floor_name in FLOOR_LOCATIONS
        if floor_name != "Merovingian"
    }
    return {
        "missing_targets": missing_targets,
        "available_floors": sorted([name for name, available in floor_status.items() if available]),
        "missing_floors": sorted([name for name, available in floor_status.items() if not available]),
    }


def _resolve_launch_boot_policy(
    root: Path,
    *,
    requested_profile: str,
    enabled_floor_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    enabled = [str(name).strip() for name in (enabled_floor_names or []) if str(name).strip()]
    policy: Dict[str, Any] = {
        "requested_profile": requested_profile,
        "boot_floor_names": enabled or None,
        "deferred_floor_names": [],
        "manual_only_floor_names": [],
        "details": None,
    }
    if requested_profile != "resident":
        return policy

    try:
        from lightspeed_runtime.startup_options import read_launch_control_profile

        details = read_launch_control_profile(root)
        boot_floor_names = [str(name) for name in (details.get("boot_floors") or []) if str(name).strip()]
        deferred_floor_names = [str(name) for name in (details.get("deferred_floors") or []) if str(name).strip()]
        manual_only_floor_names = [str(name) for name in (details.get("manual_heavy_floors") or []) if str(name).strip()]

        if enabled:
            allow = set(enabled)
            boot_floor_names = [name for name in boot_floor_names if name in allow]
            deferred_floor_names = [name for name in deferred_floor_names if name in allow]
            manual_only_floor_names = [name for name in manual_only_floor_names if name in allow]

        policy.update(
            {
                "boot_floor_names": boot_floor_names or enabled or None,
                "deferred_floor_names": deferred_floor_names,
                "manual_only_floor_names": manual_only_floor_names,
                "details": details,
            }
        )
    except Exception as exc:
        policy["error"] = str(exc)
    return policy


def _trinity_ui_surface_available() -> bool:
    """Return True only when the Trinity UI stack is present in this checkout."""
    required_paths = (
        LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "ui" / "premium_theme_engine.py",
        LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "ui" / "smart_settings_hub.py",
        LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "ui" / "it_portal.py",
        LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "wizards" / "startup_wizard.py",
        LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "tools" / "open_dialogue_board.py",
        LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "core" / "services" / "__init__.py",
    )
    return all(path.exists() for path in required_paths)


def _shell_action_catalog() -> list[dict[str, Any]]:
    """Compact, function-first shell surface inventory used by help and launcher hints."""
    trinity_ready = _trinity_ui_surface_available()
    return [
        {"label": "Home", "shortcut": "Ctrl+H", "surface": "shell", "available": True},
        {"label": "Command Palette", "shortcut": "Ctrl+K", "surface": "shell", "available": True},
        {"label": "Settings", "shortcut": "Ctrl+,", "surface": "Trinity", "available": trinity_ready},
        {"label": "Projects", "shortcut": "Ctrl+P", "surface": "shell", "available": True},
        {"label": "Documents", "shortcut": "Ctrl+D", "surface": "shell", "available": True},
        {"label": "Project Tree", "shortcut": "Ctrl+T", "surface": "shell", "available": True},
        {"label": "Templates", "shortcut": "Ctrl+M", "surface": "Trinity", "available": trinity_ready},
        {"label": "Immersive Overlay", "shortcut": "F1 / Immersive toggle", "surface": "Construct", "available": True},
    ]

def _get_z_floor_module(floor_name: str) -> Optional[Any]:
    """
    Lazily load a canonical Z-floor entrypoint module.

    We intentionally avoid importing all floors at module import time to prevent
    noisy warnings and heavyweight side-effects (e.g. Tk initialization) during
    simple operations like `python N.py --smoke`.
    """
    if floor_name == "Merovingian":
        return None

    cached = Z_FLOORS_AVAILABLE.get(floor_name)
    if cached is not None:
        return cached

    floor_path = FLOOR_LOCATIONS.get(floor_name)
    if not floor_path:
        Z_FLOORS_AVAILABLE[floor_name] = None
        return None

    try:
        full_path = (LIGHTSPEED_ROOT / floor_path).resolve()
        if not full_path.exists():
            Z_FLOORS_AVAILABLE[floor_name] = None
            return None

        # Load the entire module from file using dynamic import.
        mod_name = f"lightspeed_floor_{floor_name.lower()}"
        spec = spec_from_file_location(mod_name, full_path)
        if spec is None or spec.loader is None:
            Z_FLOORS_AVAILABLE[floor_name] = None
            return None

        mod = module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        Z_FLOORS_AVAILABLE[floor_name] = mod
        return mod
    except Exception as exc:
        # Keep console output clean; floor loading is primarily managed by FloorLoader.
        print(f"[WARNING] Failed to load {floor_name} entrypoint: {exc}")
        Z_FLOORS_AVAILABLE[floor_name] = None
        return None


# Seed cache keys so downstream UIs can list floors without importing them.
for _floor_name in FLOOR_LOCATIONS.keys():
    if _floor_name == "Merovingian":
        Z_FLOORS_AVAILABLE[_floor_name] = None
    else:
        Z_FLOORS_AVAILABLE.setdefault(_floor_name, None)


# ============================================================================
# LOGIN (DB-backed; no embedded credentials)
# ============================================================================

# This project intentionally does not embed passwords/credentials in code.
# Users (including IT/Founder clearance) are created/updated by the Setup Wizard
# and stored in the unified database.


# ============================================================================
# COLOR SCHEMES (Cyberpunk theme from lightspeed_complete_gui.py)
# ============================================================================

COLORS = {
    'bg_dark': '#000B1F',
    'bg_blue': '#001B3F',
    'bg_panel': '#002855',
    # Common aliases used across older UIs
    'accent': '#00FFFF',
    'accent_cyan': '#00FFFF',
    'accent_magenta': '#FF00FF',
    'accent_pink': '#FF0088',
    'text_green': '#00FF88',
    'text_cyan': '#00DDFF',
    'text_white': '#FFFFFF',
    'border_blue': '#0055FF',
    'button_green': '#00AA00',
    'button_hover': '#00DD00',
    'button_orange': '#FF9900',
    'error_red': '#FF3333',
    'warning_orange': '#FF9900',
    'success_green': '#00FF00',
}


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class LightSpeedUnified(tk.Tk):
    """
    Unified LightSpeed Orchestrator
    200% Implementation - ALL systems integrated

    Dual-mode operation:
    - Client mode: Guided, simplified UI, ACHILLES-style assistance
    - IT/Founder mode: Full control, Z-floor tabs, orchestrator AI
    """

    def __init__(
        self,
        cli_mode=False,
        *,
        auto_trinity_login: bool = False,
        requested_it_portal: bool = False,
        launch_profile: str = "resident",
    ):
        super().__init__()

        # Initialize Premium Theme Engine
        if HAS_PREMIUM_THEME:
            self.theme = get_theme_engine(ThemeMode.LIGHT)
            self.use_premium_theme = True
        else:
            self.theme = None
            self.use_premium_theme = False

        # Window setup
        self.title("LightSpeed Unified Orchestrator v1.0.0")
        self.geometry("1600x1000")
        try:
            self.state('zoomed')
        except:
            pass

        # Apply premium theme or fallback to classic colors
        if self.use_premium_theme:
            self.theme.apply_to_root(self)
            self.configure(bg=self.theme.palette.primary)
        else:
            self.configure(bg=COLORS['bg_dark'])

        # CLI mode flag
        self.cli_mode = cli_mode

        # Trinity-first login consolidation flags (launcher-driven).
        self._auto_trinity_login = bool(auto_trinity_login)
        self._requested_it_portal = bool(requested_it_portal)
        self.launch_profile_name = str(launch_profile or "resident")

        # Initialize services (MUST succeed)
        print("[INIT] Initializing core services...")
        self.services = initialize_services()
        self.db = get_db()
        self.event_bus = get_event_bus()
        self.storage = get_storage()
        self.data_accumulator = None
        if HAS_DATA_ACCUMULATION:
            try:
                self.data_accumulator = DataAccumulationEngine(LIGHTSPEED_ROOT)
            except Exception as e:
                print(f"[WARNING] Data accumulation disabled: {e}")
        print("[OK] Core services initialized")

        self.canonical_runtime = None
        self.oracle_morpheus_bridge = None
        self.trinity_shell_bridge = None
        self.neo_achilles_bridge = None
        self.agent_home_bridge = None
        self.canonical_runtime_root = CANONICAL_RUNTIME_ROOT
        runtime_bundle = _bootstrap_canonical_runtime(index_limit_per_source=20)
        if runtime_bundle:
            self.canonical_runtime = runtime_bundle.get("runtime")
            self.oracle_morpheus_bridge = runtime_bundle.get("oracle_morpheus_bridge")
            self.trinity_shell_bridge = runtime_bundle.get("trinity_shell_bridge")
            self.neo_achilles_bridge = runtime_bundle.get("neo_achilles_bridge")
            self.agent_home_bridge = runtime_bundle.get("agent_home_bridge")
            print("[OK] Canonical runtime connected")
            if self.agent_home_bridge is not None:
                print("[OK] Agent home bridge connected")
            else:
                print("[WARNING] Agent home bridge not connected")
        else:
            print("[WARNING] Canonical runtime not connected")

        # Service registry (optional): drives floor/service enablement and GUI status
        self.service_registry_status = None
        self.enabled_floor_names = None
        try:
            from core.services.function_registry import validate_service_registry
            self.service_registry_status = validate_service_registry(LIGHTSPEED_ROOT, include_disabled=True)
            self.enabled_floor_names = self.service_registry_status.get("enabled_floors") or None
        except Exception as e:
            print(f"[WARNING] Service registry unavailable: {e}")

        self.launch_boot_policy = _resolve_launch_boot_policy(
            LIGHTSPEED_ROOT,
            requested_profile=self.launch_profile_name,
            enabled_floor_names=self.enabled_floor_names,
        )
        if self.launch_boot_policy.get("error"):
            print(f"[WARNING] Launch control profile unavailable: {self.launch_boot_policy.get('error')}")
        elif self.launch_profile_name == "resident":
            boot_preview = self.launch_boot_policy.get("boot_floor_names") or []
            deferred_preview = self.launch_boot_policy.get("deferred_floor_names") or []
            manual_preview = self.launch_boot_policy.get("manual_only_floor_names") or []
            print(
                "[INIT] Launch control profile: "
                f"boot={', '.join(boot_preview) if boot_preview else 'none'} | "
                f"deferred={', '.join(deferred_preview) if deferred_preview else 'none'} | "
                f"manual={', '.join(manual_preview) if manual_preview else 'none'}"
            )

        # Initialize Floor Loader for dynamic Z-floor component loading
        self.floor_loader = None
        if HAS_FLOOR_LOADER:
            print("[INIT] Initializing Floor Loader...")
            self.floor_loader = FloorLoader(lightspeed_root=LIGHTSPEED_ROOT)

            # Load all manifests
            self.floor_loader.load_all_manifests()

            # Prepare dependencies for floors
            floor_dependencies = {
                'db': self.db,
                'event_bus': self.event_bus,
                'storage': self.storage,
                'accumulator': self.data_accumulator,
                'app': self,
                'canonical_runtime': self.canonical_runtime,
                'oracle_morpheus_bridge': self.oracle_morpheus_bridge,
                'trinity_shell_bridge': self.trinity_shell_bridge,
                'neo_achilles_bridge': self.neo_achilles_bridge,
                'agent_home_bridge': self.agent_home_bridge,
            }

            # Initialize floors in inside-out order (canonical runtime: Z-4 to Z+3; Z+4_FirstRun is legacy-only)
            print("[INIT] Initializing Z-floors (inside-out)...")
            try:
                floor_init = self.floor_loader.initialize_all_floors_inside_out(
                    floor_dependencies,
                    enabled_floor_names=self.enabled_floor_names,
                    boot_floor_names=self.launch_boot_policy.get("boot_floor_names"),
                    deferred_floor_names=self.launch_boot_policy.get("deferred_floor_names"),
                    manual_only_floor_names=self.launch_boot_policy.get("manual_only_floor_names"),
                    return_details=True,
                )
                ok = bool((floor_init or {}).get("success"))
                if ok:
                    print("[OK] Z-floors initialized successfully")
                else:
                    print("[WARNING] One or more enabled Z-floors failed to initialize")
                if isinstance(floor_init, dict):
                    if floor_init.get("skipped_deferred"):
                        print(f"[INIT] Deferred floors: {', '.join(floor_init.get('skipped_deferred') or [])}")
                    if floor_init.get("skipped_manual"):
                        print(f"[INIT] Manual-heavy floors: {', '.join(floor_init.get('skipped_manual') or [])}")
            except Exception as e:
                print(f"[WARNING] Floor initialization encountered errors: {e}")
        else:
            print("[!] Floor Loader not available - using legacy Z-floor imports")

        # Surface Smith automation runtime on the host so floor UIs can enqueue background work
        # without needing to import floor runner modules directly.
        self.smith_queue = None
        self.smith_coordinator = None
        try:
            if self.floor_loader is not None and hasattr(self.floor_loader, "floor_instances"):
                smith_mod = getattr(self.floor_loader, "floor_instances", {}).get("Z-3_Smith")
                runtime = getattr(smith_mod, "SMITH_RUNTIME", None)
                if isinstance(runtime, dict):
                    self.smith_queue = runtime.get("queue")
                    self.smith_coordinator = runtime.get("coordinator")
        except Exception:
            self.smith_queue = None
            self.smith_coordinator = None

        # Initialize framework layer
        if HAS_FRAMEWORK:
            self.settings_manager = SettingsManager("config/settings.json")
            self.api_manager = APIManager("config/apis.json")
            print("[OK] Framework layer initialized")
        else:
            self.settings_manager = None
            self.api_manager = None

        # Initialize ProjectManager
        if HAS_PROJECT_MANAGER:
            try:
                from core.config.paths import CONSTRUCT_ROOT  # type: ignore
                projects_dir = Path(CONSTRUCT_ROOT) / "projects"
            except Exception:
                projects_dir = LIGHTSPEED_ROOT / "projects"
            try:
                projects_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            self.project_manager = create_project_manager(str(projects_dir))
            print("[OK] Project Manager initialized")
        else:
            self.project_manager = None

        # Application state
        self.current_screen = "login"
        self.current_user = None
        self.current_company = None
        self.current_project = None
        self.screens_history = []
        self.user_mode = None  # "client" or "it_founder"

        # Z-Floor integration
        self.z_floor_windows = {}  # For Client mode (Toplevel windows)
        self.z_floor_tabs = {}     # For IT/Founder mode (Notebook tabs)
        self.z_floor_instances = {}  # Floor module instances
        self.z_floor_status = {}   # Initialization status
        # Track live floor UI widgets (for deep-linking to specific tabs within a floor window).
        self._floor_ui_widgets = {}  # floor_name -> ttk.Frame/tk.Widget (usually the floor UI root)

        # Event queue for real-time updates
        self.event_queue = queue.Queue()
        self._event_bus_subscription_id = None
        self._event_bus_handler = None
        self._register_event_bus_bridge()

        # Initialize floors in inside-out order (Core -> Surface)
        if self.floor_loader is None:
            self._initialize_floors_inside_out()

        # Web server (for 3D visualization)
        self.web_server = None
        self.web_server_thread = None
        self._start_web_server()

        # Theme manager
        if HAS_FRAMEWORK:
            theme = self.settings_manager.get("system.theme", "light")
            self.theme_manager = ThemeManager(self, theme)
        else:
            self.theme_manager = None

        # Create UI
        self.setup_styles()
        self.create_top_bar()
        self.create_main_container()
        self.create_status_bar()

        # Show login screen
        self.show_login()

        # Trinity-first: when requested by launcher flags, open Trinity login immediately.
        if getattr(self, "_auto_trinity_login", False):
            try:
                self.after(250, self._open_trinity_login)
            except Exception:
                pass

        # Bind shortcuts
        self.bind_shortcuts()

        # Start event processing
        self.process_events()

        # Center window
        self.center_window()

    def center_window(self):
        """Center window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _initialize_floors_inside_out(self):
        """
        Initialize Z-floors in inside-out order (Core -> Surface)
        Each floor depends on floors below it (inner layers)
        """
        print("\n[Z-Axis] Initializing floors (Inside-Out)...")

        # Initialization order: Core to Surface
        initialization_order = [
            ("Merovingian", -4, "System Core - Health & Diagnostics"),
            ("Smith", -3, "Background Jobs - Automation"),
            ("Oracle", -2, "IP Vault - Archiving"),
            ("Morpheus", -1, "Knowledge Base - Documentation"),
            ("TheConstruct", 0, "Training Ground - Simulations"),
            ("Architect", 1, "Mission Planning - Goals"),
            ("Neo", 2, "AI Assistant - Ollama"),
            ("Trinity", 3, "UI Layer - Customization"),
        ]

        for floor_name, z_level, description in initialization_order:
            self._init_floor(floor_name, z_level, description)

        print("[Z-Axis] All floors initialized successfully!\n")

    def _init_floor(self, floor_name: str, z_level: int, description: str):
        """
        Initialize a single Z-floor using new standardized entry points

        Args:
            floor_name: Floor module name
            z_level: Z-axis position
            description: Floor description
        """
        try:
            # Skip Merovingian - it's the core services layer, already initialized
            if floor_name == "Merovingian":
                self.z_floor_status[floor_name] = {
                    "status": "CORE",
                    "z_level": z_level,
                    "description": description
                }
                print(f"  [CORE] Z{z_level:+d}: {floor_name} - {description} (Core Services)")
                return

            # Lazily resolve floor entrypoint (fallback path; primary path is FloorLoader)
            module = _get_z_floor_module(floor_name)
            if module:

                # Prepare dependencies for this floor (all previously initialized floors)
                dependencies = {
                    'db': self.db,
                    'event_bus': self.event_bus,
                    'storage': self.storage,
                    'app': self,
                    'canonical_runtime': self.canonical_runtime,
                    'oracle_morpheus_bridge': self.oracle_morpheus_bridge,
                    'trinity_shell_bridge': self.trinity_shell_bridge,
                    'neo_achilles_bridge': self.neo_achilles_bridge,
                    'agent_home_bridge': self.agent_home_bridge,
                }

                # Add previously initialized floor instances as dependencies
                for prev_floor_name, prev_floor in self.z_floor_instances.items():
                    dependencies[prev_floor_name.lower()] = prev_floor

                # Initialize floor using standardized initialize() function
                if hasattr(module, 'initialize'):
                    try:
                        result = module.initialize(
                            dependencies=dependencies,
                            components=None  # Load all components by default
                        )
                        status = "OK" if result else "PARTIAL"

                        # Store runtime for cross-floor access
                        if hasattr(module, 'get_runtime'):
                            runtime = module.get_runtime()
                            if runtime:
                                dependencies[f'{floor_name.lower()}_runtime'] = runtime

                    except TypeError:
                        # Fallback for old-style initialize without parameters
                        result = module.initialize()
                        status = "OK" if result else "PARTIAL"
                else:
                    status = "LOADED"

                self.z_floor_instances[floor_name] = module
                self.z_floor_status[floor_name] = {
                    "status": status,
                    "z_level": z_level,
                    "description": description
                }

                print(f"  [{status}] Z{z_level:+d}: {floor_name} - {description}")

            else:
                self.z_floor_status[floor_name] = {
                    "status": "NOT_AVAILABLE",
                    "z_level": z_level,
                    "description": description
                }
                print(f"  [SKIP] Z{z_level:+d}: {floor_name} - Not available")

        except Exception as e:
            self.z_floor_status[floor_name] = {
                "status": "ERROR",
                "z_level": z_level,
                "description": description,
                "error": str(e)
            }
            print(f"  [ERROR] Z{z_level:+d}: {floor_name} - {e}")

    def _start_web_server(self):
        """Start FastAPI web server for 3D visualization in background thread"""
        try:
            import socket
            # Canonical FastAPI server lives under TheConstruct (Z0). Avoid importing
            # a non-existent top-level `server` package (keeps console clean).
            create_app = _load_symbol_from_file(
                "Z Axis/Z0_TheConstruct/server/web_server.py",
                "create_app",
            )
            import uvicorn
            import webbrowser

            # Create FastAPI app
            app = create_app(self)

            def _port_available(port: int) -> bool:
                """Best-effort port availability check to avoid noisy uvicorn bind errors."""
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind(("127.0.0.1", int(port)))
                    s.close()
                    return True
                except Exception:
                    try:
                        s.close()
                    except Exception:
                        pass
                    return False

            preferred = 8080
            candidates = [preferred] + list(range(8081, 8091))
            port = None
            for p in candidates:
                if _port_available(p):
                    port = p
                    break

            if port is None:
                print("[Web Server] Disabled: no free port available in 8080-8090")
                return

            # Start server in daemon thread
            def run_server():
                try:
                    # Keep logs quiet; errors are still surfaced via print.
                    uvicorn.run(app, host="127.0.0.1", port=int(port), log_level="critical")
                except Exception as e:
                    print(f"[Web Server] Error: {e}")

            self.web_server_thread = threading.Thread(target=run_server, daemon=True)
            self.web_server_thread.start()

            self.web_server_port = int(port)
            print(f"[Web Server] Started on http://127.0.0.1:{port}")
            print("[Web Server] Click '3D View' button to open visualization")

        except ImportError as e:
            print(f"[Web Server] Not available: {e}")
            # Silently fail - web server is optional
        except Exception as e:
            print(f"[Web Server] Failed to start: {e}")

    def open_3d_view(self):
        """Open UI-first 3D Tower background host (interactive controls are pinned by default)."""
        # Prefer embedded UI-first world (part of N.py experience).
        try:
            self.show_immersive_world(interactive=False)
            return
        except Exception:
            pass

        # Fallback: open the UI-first environment host in a Toplevel (no second Tk root).
        try:
            launch_cognigrex_3d = _load_symbol_from_file(
                "Z Axis/Z0_TheConstruct/ui/cognigrex_3d_environment.py",
                "launch_cognigrex_3d",
            )
            self.update_status("Launching 3D environment host...")
            launch_cognigrex_3d(parent=self)
            return
        except Exception:
            pass

        # Final fallback: browser-based 3D server
        try:
            import webbrowser
            port = int(getattr(self, "web_server_port", 8080) or 8080)
            webbrowser.open(f"http://localhost:{port}")
            self.update_status("Opening 3D visualization in browser...")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open 3D view:\n{e}", parent=self)

    def open_immersive_wasd(self):
        """Open immersive 3D with interactive controls (requires explicit unpin for the active user)."""
        try:
            self.show_immersive_world(interactive=True)
        except Exception:
            # Best-effort: fall back to the pinned host.
            try:
                self.show_immersive_world(interactive=False)
            except Exception:
                pass

    def open_dome_interface(self):
        """
        Open enhanced dome projection interface with FPS mouse-look controls.

        Features:
        - Full FPS-style mouse-look (360-degree horizontal, 180-degree vertical)
        - UI widgets anchored at 1.5m from player
        - 3-step Bento widget management
        - Rolling hills environment (Windows 97 style)
        """
        try:
            # Launch dome interface as subprocess (cleaner separation)
            import subprocess
            dome_launcher = (
                LIGHTSPEED_ROOT / "Z Axis" / "Z0_TheConstruct" / "ui" / "launch_immersive_dome.py"
            )

            if dome_launcher.exists():
                self.update_status("Launching Dome Projection Interface (FPS Controls)...")
                subprocess.Popen([sys.executable, str(dome_launcher)])
                messagebox.showinfo(
                    "Dome Interface",
                    "Dome Projection Interface launched!\n\n"
                    "Features:\n"
                    "- FPS Mouse-Look Controls\n"
                    "- UI at 1.5m from player\n"
                    "- 3-Step Bento System\n"
                    "- Rolling Hills Environment\n\n"
                    "Click canvas to capture mouse, ESC to release.",
                    parent=self
                )
            else:
                raise FileNotFoundError(f"Dome launcher not found: {dome_launcher}")

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to open Dome Interface:\n{e}\n\n"
                "Please ensure Trinity floor UI modules are present.",
                parent=self
            )

    def _current_user_id_for_bento(self) -> Optional[str]:
        """Best-effort stable user id for Bento persistence/callback wiring."""
        try:
            if isinstance(self.current_user, dict):
                return (
                    self.current_user.get("username")
                    or self.current_user.get("id")
                    or self.current_user.get("fullname")
                )
            if isinstance(self.current_user, str):
                return self.current_user
        except Exception:
            return None
        return None

    def _load_unified_config(self) -> Dict[str, Any]:
        """Best-effort load of config/unified_config.json (no side effects)."""
        try:
            cfg_path = (LIGHTSPEED_ROOT / "config" / "unified_config.json").resolve()
            if cfg_path.exists():
                data = json.loads(cfg_path.read_text(encoding="utf-8", errors="replace"))
                return data if isinstance(data, dict) else {}
        except Exception:
            pass
        return {}

    def _allow_guest_mode(self) -> bool:
        """
        Guest mode is ON by default (requested).

        Controlled by `features.allow_guest_mode` in unified_config.json.
        """
        try:
            cfg = self._load_unified_config()
            features = cfg.get("features") if isinstance(cfg.get("features"), dict) else {}
            # If `features` is absent, default to True so the app remains approachable on first run.
            return bool((features or {}).get("allow_guest_mode", True))
        except Exception:
            return True

    def _show_trinity_login_portal_button(self) -> bool:
        """
        Whether to show the "Open Trinity Login Portal" button on the local login screen.

        Default: False (local login is canonical).
        Controlled by `features.show_trinity_login_portal` in unified_config.json.
        """
        try:
            cfg = self._load_unified_config()
            features = cfg.get("features") if isinstance(cfg.get("features"), dict) else {}
            return bool((features or {}).get("show_trinity_login_portal", False))
        except Exception:
            return False

    def _require_password_login(self) -> bool:
        """
        Whether local login requires a password.

        Default: True (can be disabled for dev/demo via unified_config.json).
        Controlled by `features.require_password_login`.
        """
        try:
            cfg = self._load_unified_config()
            features = cfg.get("features") if isinstance(cfg.get("features"), dict) else {}
            return bool((features or {}).get("require_password_login", True))
        except Exception:
            return True

    def _hash_password_record(self, password: str) -> Dict[str, Any]:
        """Create a PBKDF2 password record for storage in user_preferences.preferences_json."""
        pwd = (password or "").encode("utf-8")
        salt = secrets.token_bytes(16)
        iterations = 200_000
        digest = hashlib.pbkdf2_hmac("sha256", pwd, salt, iterations)
        return {
            "alg": "pbkdf2_sha256",
            "iter": iterations,
            "salt_b64": base64.b64encode(salt).decode("ascii"),
            "hash_b64": base64.b64encode(digest).decode("ascii"),
        }

    def _verify_password_record(self, record: Dict[str, Any], password: str) -> bool:
        """Verify a PBKDF2 password record."""
        try:
            if not isinstance(record, dict):
                return False
            if str(record.get("alg") or "") != "pbkdf2_sha256":
                return False
            iterations = int(record.get("iter") or 0)
            salt = base64.b64decode(str(record.get("salt_b64") or ""), validate=False)
            expected = base64.b64decode(str(record.get("hash_b64") or ""), validate=False)
            if iterations <= 0 or (not salt) or (not expected):
                return False
            got = hashlib.pbkdf2_hmac("sha256", (password or "").encode("utf-8"), salt, iterations)
            return hmac.compare_digest(got, expected)
        except Exception:
            return False

    def _immersive_unpinned(self) -> bool:
        """Interactive immersive controls are pinned off unless the active user explicitly unpins."""
        try:
            prefs = getattr(self, "user_prefs", None)
            getter = getattr(prefs, "get_preference", None)
            if callable(getter):
                return bool(getter("immersive.unpinned", default=False))
        except Exception:
            pass
        return False

    def set_immersive_unpinned(self, enabled: bool = False) -> bool:
        """Set the per-user immersive unpinned flag (tailoring only; does not touch durable registries)."""
        try:
            prefs = getattr(self, "user_prefs", None)
            setter = getattr(prefs, "set_preference", None)
            if callable(setter):
                setter("immersive.unpinned", bool(enabled))
                return True
        except Exception:
            pass
        return False

    def reset_tailoring(self, *, user_id: Optional[str] = None, confirm: bool = True) -> bool:
        """
        Reset per-user tailoring (preferences, Bento recents/favorites/layout, OKRs/Notes, etc).

        This must NOT delete Oracle vault files or floor durable registries; it only clears the
        user's `user_preferences` row (best-effort).
        """
        target = (user_id or self._current_user_id_for_bento() or "").strip()
        if not target:
            return False

        if confirm:
            ok = messagebox.askyesno(
                "Reset Tailoring",
                f"Reset tailoring for user '{target}'?\n\n"
                "This clears UI preferences, Bento layout/recents/favorites, OKRs, and Notes.\n"
                "It does not delete vault contents or durable registries.",
                parent=self,
            )
            if not ok:
                return False

        try:
            prefs = get_user_preferences(target)
            prefs.reset_to_defaults()
            # Reload into runtime state (best-effort).
            try:
                self.user_prefs = get_user_preferences(target)
                self.user_prefs.apply_to_ui(self)
            except Exception:
                pass
            messagebox.showinfo("Reset Tailoring", "Tailoring has been reset.", parent=self)
            return True
        except Exception as e:
            messagebox.showerror("Reset Tailoring", f"Failed to reset tailoring:\n{e}", parent=self)
            return False

    def reset_first_run_state(self, *, confirm: bool = True, remove_user_config: bool = False) -> bool:
        """
        Reset first-run / setup markers (launcher-level state).

        This is intended for "true first run" replays without deleting durable registries:
        - Removes `config/.initialized` and `config/cognigrex_setup_state.json` (resume state).
        - Optionally removes `config/user_config.json` (profiles/preferences scaffold).

        Does NOT delete:
        - Oracle vault/library contents
        - Z Direct durable registries (`objects.json` committed)
        - Database file itself (projects/tasks/telemetry)
        """
        cfg_root = (LIGHTSPEED_ROOT / "config").resolve()
        targets = [
            cfg_root / ".initialized",
            cfg_root / "cognigrex_setup_state.json",
        ]
        if remove_user_config:
            targets.append(cfg_root / "user_config.json")

        if confirm:
            msg = (
                "Reset first-run state?\n\n"
                "This will remove setup markers so the next launch behaves like a fresh first-run.\n\n"
                "Files:\n"
                + "\n".join([f"- {p}" for p in targets])
                + "\n\nPreserved:\n"
                "- Database (projects/tasks/telemetry)\n"
                "- Oracle vault/library\n"
                "- Committed Z Direct registries\n"
            )
            if not messagebox.askyesno("Reset First-Run State", msg, parent=self):
                return False

        removed = 0
        errors = []
        for p in targets:
            try:
                if p.exists():
                    p.unlink()
                    removed += 1
            except Exception as e:
                errors.append(f"{p.name}: {e}")

        if errors:
            messagebox.showwarning(
                "Reset First-Run State",
                f"Removed {removed} file(s), but some items failed:\n\n" + "\n".join(errors),
                parent=self,
            )
            return False

        messagebox.showinfo(
            "Reset First-Run State",
            f"Reset complete. Removed {removed} file(s).\n\nYou can re-run the Setup Wizard now (Wizards / Setup), or restart the launcher.",
            parent=self,
        )
        return True

    def open_unified_search(self, *, initial_query: str = "", initial_category: str = "all") -> None:
        """Open Trinity's unified search / command palette UI with host wiring enabled."""
        try:
            wizard_path = (Path(__file__).resolve().parent / "Z Axis" / "Z+3_Trinity" / "wizards" / "unified_search_system.py").resolve()
            if not wizard_path.exists():
                raise FileNotFoundError(wizard_path)
            spec = spec_from_file_location("lightspeed_unified_search_system", wizard_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load UnifiedSearchSystem from {wizard_path}")
            mod = module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            SearchUI = getattr(mod, "SearchUI")

            win = tk.Toplevel(self)
            try:
                win.title("LightSpeed Unified Search")
                win.geometry("1000x600")
            except Exception:
                pass
            SearchUI(win, initial_query=initial_query, initial_category=initial_category, host=self)
            return
        except Exception as e:
            messagebox.showwarning("Unified Search", f"Unified Search is unavailable:\n{e}", parent=self)

    def open_object_catalog(
        self,
        *,
        scope: str = "trinity",
        kind: str = "all",
        query: str = "",
    ) -> None:
        """
        Read-only object browser for committed Z Direct registries (menu-first, non-destructive).

        This is a non-IT surface for exploring committed objects by kind/id/title and inspecting payload JSON.
        Governance stays the same: staging happens in JSONL streams; commits require IT Portal approval.
        """
        root = Path(__file__).resolve().parent

        def _registry_path(s: str) -> Path:
            s = (s or "trinity").strip().lower()
            if s in {"oracle", "z-2", "z-2_oracle"}:
                return (root / "Z Axis" / "Z-2_Oracle" / "Z Direct" / "objects.json").resolve()
            return (root / "Z Axis" / "Z+3_Trinity" / "Z Direct" / "objects.json").resolve()

        win = tk.Toplevel(self)
        try:
            win.title("Object Catalog")
            win.geometry("1200x760")
        except Exception:
            pass
        try:
            win.configure(bg=COLORS["bg_dark"])
            win.transient(self)
        except Exception:
            pass

        header = tk.Frame(win, bg=COLORS["bg_panel"])
        header.pack(fill="x")
        tk.Label(
            header,
            text="Object Catalog (Committed Registries)",
            bg=COLORS["bg_panel"],
            fg=COLORS["accent_cyan"],
            font=("Arial", 14, "bold"),
        ).pack(side="left", padx=12, pady=10)
        tk.Button(
            header,
            text="Close",
            command=win.destroy,
            bg=COLORS["bg_blue"],
            fg=COLORS["text_white"],
            relief="flat",
            padx=12,
            pady=6,
        ).pack(side="right", padx=12, pady=10)

        controls = tk.Frame(win, bg=COLORS["bg_dark"])
        controls.pack(fill="x", padx=12, pady=(10, 8))

        scope_var = tk.StringVar(value=(scope or "trinity"))
        kind_var = tk.StringVar(value=(kind or "all"))
        query_var = tk.StringVar(value=(query or ""))

        tk.Label(controls, text="Registry:", bg=COLORS["bg_dark"], fg=COLORS["text_white"], font=("Arial", 10, "bold")).pack(side="left")
        scope_combo = ttk.Combobox(
            controls,
            textvariable=scope_var,
            state="readonly",
            width=12,
            values=["trinity", "oracle"],
        )
        scope_combo.pack(side="left", padx=(8, 16))

        tk.Label(controls, text="Kind:", bg=COLORS["bg_dark"], fg=COLORS["text_white"], font=("Arial", 10, "bold")).pack(side="left")
        kind_combo = ttk.Combobox(controls, textvariable=kind_var, state="readonly", width=18, values=["all"])
        kind_combo.pack(side="left", padx=(8, 16))

        tk.Label(controls, text="Search:", bg=COLORS["bg_dark"], fg=COLORS["text_white"], font=("Arial", 10, "bold")).pack(side="left")
        q_entry = ttk.Entry(controls, textvariable=query_var, width=40)
        q_entry.pack(side="left", padx=(8, 16), fill="x", expand=True)

        body = tk.Frame(win, bg=COLORS["bg_dark"])
        body.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        left = ttk.LabelFrame(body, text="Objects")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right = ttk.LabelFrame(body, text="Details")
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        cols = ("kind", "id", "title", "tags")
        tree = ttk.Treeview(left, columns=cols, show="headings", height=22)
        for c in cols:
            tree.heading(c, text=c.upper())
        tree.column("kind", width=140, anchor="w")
        tree.column("id", width=160, anchor="w")
        tree.column("title", width=480, anchor="w")
        tree.column("tags", width=260, anchor="w")
        tree.pack(side="left", fill="both", expand=True, padx=6, pady=6)

        sb = ttk.Scrollbar(left, orient="vertical", command=tree.yview)
        sb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=sb.set)

        details = scrolledtext.ScrolledText(
            right,
            bg="#001122",
            fg=COLORS["text_green"],
            font=("Consolas", 10),
            wrap="word",
        )
        details.pack(fill="both", expand=True, padx=6, pady=6)
        try:
            details.configure(state="disabled")
        except Exception:
            pass

        state: dict = {"rows": [], "all_rows": [], "vault_paths": {}}

        def _title_for(obj: dict) -> str:
            k = str(obj.get("kind") or "")
            if k == "vault_file":
                return str(obj.get("source_name") or obj.get("name") or "")
            if k == "knowledge_node":
                return str(obj.get("concept") or "")
            if k == "citation":
                return str(obj.get("note") or "")
            if k == "dataset":
                return str(obj.get("name") or obj.get("id") or "")
            if k == "research_query":
                return str(obj.get("query_text") or obj.get("query") or obj.get("id") or "")
            return str(obj.get("title") or obj.get("name") or obj.get("id") or k)

        def _tags_for(obj: dict) -> str:
            try:
                tags = obj.get("tags")
                if isinstance(tags, list):
                    cleaned = [str(t).strip() for t in tags if str(t).strip()]
                    if not cleaned:
                        return ""
                    # Keep the table readable; full list is visible in JSON details.
                    if len(cleaned) > 8:
                        return ", ".join(cleaned[:8]) + ", ..."
                    return ", ".join(cleaned)
                if isinstance(tags, str) and tags.strip():
                    return tags.strip()
            except Exception:
                return ""
            return ""

        def _load_objects() -> list:
            p = _registry_path(scope_var.get())
            if not p.exists():
                return []
            try:
                data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
                return data if isinstance(data, list) else []
            except Exception:
                return []

        def _render_details(obj: dict | None) -> None:
            try:
                details.configure(state="normal")
                details.delete("1.0", tk.END)
                details.insert("1.0", json.dumps(obj or {}, indent=2, ensure_ascii=False))
                details.configure(state="disabled")
            except Exception:
                pass

        def _selected_obj() -> dict | None:
            try:
                sel = tree.selection()
                if not sel:
                    return None
                idx = tree.index(sel[0])
                rows = state.get("rows") or []
                if 0 <= idx < len(rows):
                    return rows[idx]
            except Exception:
                return None
            return None

        def refresh() -> None:
            rows = _load_objects()
            state["all_rows"] = rows
            vault_paths = {}
            for it in rows:
                if isinstance(it, dict) and it.get("kind") == "vault_file":
                    vid = str(it.get("id") or "").strip()
                    pth = str(it.get("path") or "").strip()
                    if vid and pth:
                        vault_paths[vid] = pth
            state["vault_paths"] = vault_paths

            kinds = sorted({str(it.get("kind") or "").strip() for it in rows if isinstance(it, dict) and str(it.get("kind") or "").strip()})
            try:
                kind_combo.configure(values=["all", *kinds])
            except Exception:
                pass
            if kind_var.get() not in (["all"] + kinds):
                kind_var.set("all")

            ksel = (kind_var.get() or "all").strip()
            q = (query_var.get() or "").strip().lower()
            q_terms = [t for t in q.split() if t.strip()]
            view = []
            try:
                for it in tree.get_children():
                    tree.delete(it)
            except Exception:
                pass

            for it in rows:
                if not isinstance(it, dict):
                    continue
                k = str(it.get("kind") or "")
                if ksel != "all" and k != ksel:
                    continue
                rid = str(it.get("id") or "")
                title = _title_for(it)
                tags_s = _tags_for(it)
                # Search blob includes common fields (id/title/tags/path-ish) for menu-first discovery.
                hay = " ".join(
                    [
                        k,
                        rid,
                        title,
                        tags_s,
                        str(it.get("description") or ""),
                        str(it.get("name") or ""),
                        str(it.get("query_text") or it.get("query") or ""),
                        str(it.get("concept") or ""),
                        str(it.get("note") or ""),
                        str(it.get("path") or ""),
                    ]
                ).lower()
                if q_terms and not all(term in hay for term in q_terms):
                    continue
                view.append(it)
                try:
                    tree.insert(
                        "",
                        tk.END,
                        values=(
                            k,
                            rid,
                            (title[:160] + "...") if len(title) > 160 else title,
                            (tags_s[:90] + "...") if len(tags_s) > 90 else tags_s,
                        ),
                    )
                except Exception:
                    continue

            state["rows"] = view
            _render_details(_selected_obj())

        def _resolve_path(obj: dict | None) -> str:
            if not isinstance(obj, dict):
                return ""
            k = str(obj.get("kind") or "")
            if k == "vault_file":
                return str(obj.get("path") or "")
            if k == "citation":
                vid = str(obj.get("vault_file_id") or "").strip()
                return str((state.get("vault_paths") or {}).get(vid, ""))
            if k == "knowledge_node":
                sources = obj.get("sources") or []
                if isinstance(sources, list):
                    for s in sources:
                        if isinstance(s, dict):
                            vid = str(s.get("vault_file_id") or s.get("vault_id") or "").strip()
                            if vid:
                                p = str((state.get("vault_paths") or {}).get(vid, ""))
                                if p:
                                    return p
            # Generic best-effort path keys
            for key in ("path", "source_path", "vault_path", "file_location"):
                v = obj.get(key)
                if isinstance(v, str) and v.strip():
                    return v.strip()
            return ""

        def copy_id() -> None:
            obj = _selected_obj()
            if not obj:
                return
            rid = str(obj.get("id") or "").strip()
            if not rid:
                return
            try:
                self.clipboard_clear()
                self.clipboard_append(rid)
            except Exception:
                pass

        def copy_json() -> None:
            obj = _selected_obj()
            if not obj:
                return
            try:
                txt = json.dumps(obj, indent=2, ensure_ascii=False)
                self.clipboard_clear()
                self.clipboard_append(txt)
            except Exception:
                pass

        def open_path() -> None:
            obj = _selected_obj()
            p = _resolve_path(obj)
            if not p:
                return
            try:
                if os.path.exists(p):
                    os.startfile(p)  # type: ignore[attr-defined]
            except Exception:
                pass

        def open_folder() -> None:
            obj = _selected_obj()
            p = _resolve_path(obj)
            if not p:
                return
            try:
                pp = Path(p)
                if pp.exists():
                    os.startfile(str(pp.parent if pp.is_file() else pp))  # type: ignore[attr-defined]
            except Exception:
                pass

        def _vault_id_for_related(obj: dict | None) -> str:
            if not isinstance(obj, dict):
                return ""
            k = str(obj.get("kind") or "").strip()
            if k == "vault_file":
                return str(obj.get("id") or "").strip()
            if k == "citation":
                return str(obj.get("vault_file_id") or "").strip()
            if k == "knowledge_node":
                sources = obj.get("sources") or []
                if isinstance(sources, list):
                    for s in sources:
                        if isinstance(s, dict):
                            vid = str(s.get("vault_file_id") or s.get("vault_id") or "").strip()
                            if vid:
                                return vid
                        elif isinstance(s, str) and s.strip():
                            return s.strip()
            return ""

        def _citation_ids_for_related(obj: dict | None) -> list[str]:
            if not isinstance(obj, dict):
                return []
            k = str(obj.get("kind") or "").strip()
            if k == "citation":
                cid = str(obj.get("id") or "").strip()
                return [cid] if cid else []
            if k == "knowledge_node":
                out: list[str] = []
                sources = obj.get("sources") or []
                if isinstance(sources, list):
                    for s in sources:
                        if isinstance(s, dict):
                            cid = str(s.get("citation_id") or "").strip()
                            if cid:
                                out.append(cid)
                # De-dupe but keep order
                seen: set[str] = set()
                uniq: list[str] = []
                for cid in out:
                    if cid in seen:
                        continue
                    seen.add(cid)
                    uniq.append(cid)
                return uniq
            return []

        def _open_related_window(title: str, items: list[dict], *, kind_hint: str = "") -> None:
            win2 = tk.Toplevel(self)
            try:
                win2.title(title)
                win2.geometry("1100x720")
                win2.transient(win)
            except Exception:
                pass

            frame2 = tk.Frame(win2, bg=COLORS["bg_dark"])
            frame2.pack(fill="both", expand=True, padx=12, pady=12)

            left2 = ttk.LabelFrame(frame2, text="Related")
            left2.pack(side="left", fill="both", expand=True, padx=(0, 10))

            right2 = ttk.LabelFrame(frame2, text="Details")
            right2.pack(side="right", fill="both", expand=True, padx=(10, 0))

            cols2 = ("kind", "id", "title")
            tree2 = ttk.Treeview(left2, columns=cols2, show="headings", height=20)
            for c in cols2:
                tree2.heading(c, text=c.upper())
            tree2.column("kind", width=140, anchor="w")
            tree2.column("id", width=200, anchor="w")
            tree2.column("title", width=520, anchor="w")
            tree2.pack(side="left", fill="both", expand=True, padx=6, pady=6)

            sb2 = ttk.Scrollbar(left2, orient="vertical", command=tree2.yview)
            sb2.pack(side="right", fill="y")
            tree2.configure(yscrollcommand=sb2.set)

            details2 = scrolledtext.ScrolledText(
                right2,
                bg="#001122",
                fg=COLORS["text_green"],
                font=("Consolas", 10),
                wrap="word",
            )
            details2.pack(fill="both", expand=True, padx=6, pady=6)
            try:
                details2.configure(state="disabled")
            except Exception:
                pass

            def _sel2() -> dict | None:
                try:
                    sel = tree2.selection()
                    if not sel:
                        return None
                    idx = tree2.index(sel[0])
                    if 0 <= idx < len(items):
                        return items[idx]
                except Exception:
                    return None
                return None

            def _render2() -> None:
                obj2 = _sel2()
                try:
                    details2.configure(state="normal")
                    details2.delete("1.0", tk.END)
                    details2.insert("1.0", json.dumps(obj2 or {}, indent=2, ensure_ascii=False))
                    details2.configure(state="disabled")
                except Exception:
                    pass

            for it in items:
                try:
                    k2 = str(it.get("kind") or "")
                    rid2 = str(it.get("id") or "")
                    title2 = _title_for(it)
                    tree2.insert("", tk.END, values=(k2, rid2, (title2[:160] + "...") if len(title2) > 160 else title2))
                except Exception:
                    continue

            try:
                tree2.bind("<<TreeviewSelect>>", lambda _e: _render2())
            except Exception:
                pass
            _render2()

            btn2 = tk.Frame(win2, bg=COLORS["bg_dark"])
            btn2.pack(fill="x", padx=12, pady=(0, 12))

            def _copy_ids() -> None:
                try:
                    ids = [str(it.get("id") or "") for it in items if isinstance(it, dict)]
                    txt = "\n".join([i for i in ids if i.strip()]).strip()
                    if not txt:
                        return
                    self.clipboard_clear()
                    self.clipboard_append(txt)
                except Exception:
                    pass

            tk.Button(btn2, text="Copy IDs", command=_copy_ids, bg=COLORS["button_green"], fg="white", font=("Arial", 10, "bold")).pack(side="left")
            if kind_hint:
                tk.Label(btn2, text=f"hint: {kind_hint}", bg=COLORS["bg_dark"], fg=COLORS["text_white"], font=("Arial", 10)).pack(side="left", padx=(10, 0))

        def show_related_citations() -> None:
            obj = _selected_obj()
            vault_id = _vault_id_for_related(obj)
            if not vault_id:
                messagebox.showwarning("Object Catalog", "Select a vault-linked item first (vault_file/citation/knowledge_node).", parent=win)
                return
            rows_all = state.get("all_rows") or []
            items = [
                it
                for it in rows_all
                if isinstance(it, dict)
                and str(it.get("kind") or "") == "citation"
                and str(it.get("vault_file_id") or "").strip() == vault_id
            ]
            _open_related_window(f"Related Citations (vault_file_id={vault_id})", items, kind_hint="citation")

        def show_related_knowledge() -> None:
            obj = _selected_obj()
            vault_id = _vault_id_for_related(obj)
            if not vault_id:
                messagebox.showwarning("Object Catalog", "Select a vault-linked item first (vault_file/citation/knowledge_node).", parent=win)
                return
            rows_all = state.get("all_rows") or []
            items: list[dict] = []
            for it in rows_all:
                if not isinstance(it, dict) or str(it.get("kind") or "") != "knowledge_node":
                    continue
                sources = it.get("sources") or []
                found = False
                if isinstance(sources, list):
                    for s in sources:
                        if isinstance(s, dict):
                            vid = str(s.get("vault_file_id") or s.get("vault_id") or "").strip()
                            if vid and vid == vault_id:
                                found = True
                                break
                        elif isinstance(s, str) and s.strip() == vault_id:
                            found = True
                            break
                if found:
                    items.append(it)
            _open_related_window(f"Related Knowledge Nodes (vault_file_id={vault_id})", items, kind_hint="knowledge_node")

        def show_related_via_citation() -> None:
            obj = _selected_obj()
            if not isinstance(obj, dict):
                messagebox.showwarning("Object Catalog", "Select an item first.", parent=win)
                return
            k = str(obj.get("kind") or "").strip()
            rows_all = state.get("all_rows") or []
            if k == "citation":
                cid = str(obj.get("id") or "").strip()
                if not cid:
                    return
                items: list[dict] = []
                for it in rows_all:
                    if not isinstance(it, dict) or str(it.get("kind") or "") != "knowledge_node":
                        continue
                    sources = it.get("sources") or []
                    found = False
                    if isinstance(sources, list):
                        for s in sources:
                            if isinstance(s, dict) and str(s.get("citation_id") or "").strip() == cid:
                                found = True
                                break
                    if found:
                        items.append(it)
                _open_related_window(f"Knowledge Nodes referencing citation_id={cid}", items, kind_hint="knowledge_node")
                return
            if k == "knowledge_node":
                cids = _citation_ids_for_related(obj)
                if not cids:
                    messagebox.showwarning("Object Catalog", "No citation_id found on this knowledge_node sources.", parent=win)
                    return
                want = set(cids)
                items = [
                    it
                    for it in rows_all
                    if isinstance(it, dict) and str(it.get("kind") or "") == "citation" and str(it.get("id") or "").strip() in want
                ]
                _open_related_window("Citations referenced by knowledge_node (citation_id in sources)", items, kind_hint="citation")
                return
            messagebox.showwarning("Object Catalog", "Select a citation or knowledge_node for citation-based linking.", parent=win)

        def open_z_direct_it() -> None:
            obj = _selected_obj()
            if not isinstance(obj, dict):
                return
            channel = "Z+3" if (scope_var.get() or "").strip().lower() != "oracle" else "Z-2"
            kind2 = str(obj.get("kind") or "").strip() or None
            rid2 = str(obj.get("id") or "").strip() or None
            try:
                self.open_it_portal_z_direct(channel=channel, peer="All", kind=kind2, tags=None, search=rid2)
            except Exception:
                return

        footer = tk.Frame(win, bg=COLORS["bg_dark"])
        footer.pack(fill="x", padx=12, pady=(0, 12))
        tk.Button(footer, text="Refresh", command=refresh, bg=COLORS["bg_panel"], fg="white", font=("Arial", 10, "bold")).pack(side="left")
        tk.Button(footer, text="Copy ID", command=copy_id, bg=COLORS["button_green"], fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=(8, 0))
        tk.Button(footer, text="Copy JSON", command=copy_json, bg=COLORS["bg_blue"], fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=(8, 0))
        tk.Button(footer, text="Open", command=open_path, bg=COLORS["bg_panel"], fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=(8, 0))
        tk.Button(footer, text="Open Folder", command=open_folder, bg=COLORS["bg_panel"], fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=(8, 0))
        rel_mb = tk.Menubutton(footer, text="Related", bg=COLORS["bg_panel"], fg="white", font=("Arial", 10, "bold"), relief="flat")
        rel_menu = tk.Menu(rel_mb, tearoff=0)
        rel_menu.add_command(label="Citations (vault_file_id)", command=show_related_citations)
        rel_menu.add_command(label="Knowledge (vault_file_id)", command=show_related_knowledge)
        rel_menu.add_separator()
        rel_menu.add_command(label="Related via Citation (citation_id)", command=show_related_via_citation)
        rel_mb.configure(menu=rel_menu)
        rel_mb.pack(side="left", padx=(8, 0))

        it_state = "normal"
        try:
            if getattr(self, "user_mode", "") != "it_founder":
                it_state = "disabled"
        except Exception:
            it_state = "disabled"
        tk.Button(
            footer,
            text="Open Z Direct (IT)",
            command=open_z_direct_it,
            bg=COLORS["bg_panel"],
            fg="white",
            font=("Arial", 10, "bold"),
            state=it_state,
        ).pack(side="left", padx=(8, 0))

        try:
            tree.bind("<<TreeviewSelect>>", lambda _e: _render_details(_selected_obj()))
            scope_combo.bind("<<ComboboxSelected>>", lambda _e: refresh())
            kind_combo.bind("<<ComboboxSelected>>", lambda _e: refresh())
            q_entry.bind("<Return>", lambda _e: refresh())
        except Exception:
            pass

        refresh()

    def stage_v1r_definitions(self, *, confirm: bool = True) -> bool:
        """
        Stage a baseline set of V1R definitions into Trinity's Z Direct stream (append-only).

        This does NOT commit anything into durable registries; operators must review/commit via IT Portal.
        """
        if confirm:
            ok = messagebox.askyesno(
                "Stage V1R Definitions",
                "Stage baseline V1R definitions into Trinity Z Direct (append-only)?\n\n"
                "This will NOT commit to durable registries automatically.",
                parent=self,
            )
            if not ok:
                return False

        try:
            from core.services import get_z_direct  # type: ignore

            zd = get_z_direct()
        except Exception as e:
            messagebox.showerror("Stage V1R", f"Z Direct service unavailable:\n{e}", parent=self)
            return False

        staged = 0

        def _stage(payload: Dict[str, Any], tags: List[str]) -> None:
            nonlocal staged
            env = zd.make_envelope(
                kind="object",
                channel="Z+3",
                payload=payload,
                z_context="Trinity",
                source="N.stage_v1r_definitions",
                tags=tags,
            )
            zd.append_object("Z+3", env)
            staged += 1

        # Built-in schemas (bootstrap; evolve/commit via IT Portal).
        try:
            want = {
                "task",
                "vault_file",
                "citation",
                "simulation_result",
                "bento_widget",
                "action_def",
                "simulation_def",
                "workflow_def",
                "knowledge_node",
                "project",
                "workspace",
                "research_query",
                "dataset",
                "experiment_run",
                "learning_module",
            }
            for s in zd.builtin_schema_payloads() or []:
                if not isinstance(s, dict):
                    continue
                if str(s.get("id") or "").strip() in want:
                    _stage(s, ["v1r", "bootstrap", "schema"])
        except Exception:
            pass

        # Simulation definitions (SpecForm typed params).
        raphael_def = {
            "kind": "simulation_def",
            "id": "raphael",
            "title": "Raphael Equations",
            "description": "Compute simplified forces for an element (protons/neutrons/electrons).",
            "sim_type": "raphael",
            "output_kind": "simulation_result",
            "enabled": True,
            "tags": ["simulation", "physics"],
            "params": [
                {"name": "protons", "type": "int", "required": True, "default": 1, "ui": {"control": "spinbox", "min": 0, "max": 200, "step": 1, "label": "Protons", "units": "count"}},
                {"name": "neutrons", "type": "int", "required": True, "default": 1, "ui": {"control": "spinbox", "min": 0, "max": 300, "step": 1, "label": "Neutrons", "units": "count"}},
                {"name": "electrons", "type": "int", "required": True, "default": 1, "ui": {"control": "spinbox", "min": 0, "max": 300, "step": 1, "label": "Electrons", "units": "count"}},
            ],
        }
        bigbang_def = {
            "kind": "simulation_def",
            "id": "bigbang",
            "title": "Big Bang Simulation",
            "description": "Simulate expansion with fractal refinement (time_steps/fractal_iterations/scale).",
            "sim_type": "bigbang",
            "output_kind": "simulation_result",
            "enabled": True,
            "tags": ["simulation", "cosmology"],
            "params": [
                {"name": "time_steps", "type": "int", "required": False, "default": 500, "ui": {"control": "spinbox", "min": 10, "max": 5000, "step": 10, "label": "Time Steps", "units": "steps"}},
                {"name": "fractal_iterations", "type": "int", "required": False, "default": 3, "ui": {"control": "spinbox", "min": 0, "max": 10, "step": 1, "label": "Fractal Iterations", "units": "iters"}},
                {"name": "scale", "type": "number", "required": False, "default": 1e-30, "ui": {"control": "entry", "label": "Initial Scale", "units": "m", "help": "Typical: 1e-30"}},
            ],
        }
        _stage(raphael_def, ["v1r", "bootstrap", "simulation_def"])
        _stage(bigbang_def, ["v1r", "bootstrap", "simulation_def"])

        # Action definitions (host-aware; runnable from Unified Search when committed).
        action_defs = [
            {
                "kind": "action_def",
                "id": "open_it_portal",
                "title": "Open IT Portal",
                "description": "Open the Trinity IT Portal (IT/Founder only).",
                "category": "trinity",
                "host_action": "open_it_portal",
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "open_oracle_registry",
                "title": "Open Oracle Registry (Z Direct)",
                "description": "Open Oracle's Z Direct registry view.",
                "category": "oracle",
                "host_action": "open_oracle_registry",
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "open_unified_search",
                "title": "Open Unified Search",
                "description": "Open the unified search / command palette surface.",
                "category": "trinity",
                "host_action": "open_unified_search",
                "host_action_args": {"initial_category": "all"},
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "open_object_catalog",
                "title": "Open Object Catalog",
                "description": "Browse committed Z Direct registries (read-only object catalog).",
                "category": "trinity",
                "host_action": "open_object_catalog",
                "host_action_args": {"scope": "trinity"},
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "stage_v1r_definitions",
                "title": "Stage V1R Definitions",
                "description": "Stage baseline V1R defs into Trinity Z Direct (append-only; commit via IT Portal).",
                "category": "trinity",
                "host_action": "stage_v1r_definitions",
                "host_action_args": {"confirm": True},
                "safety": {"requires_confirm": True},
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "reset_tailoring",
                "title": "Reset Tailoring",
                "description": "Reset per-user tailoring (preferences, Bento layout/recents/favorites, OKRs, Notes).",
                "category": "settings",
                "host_action": "reset_tailoring",
                "host_action_args": {"confirm": True},
                "safety": {"requires_confirm": True},
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "arise_protocol",
                "title": "Arise Protocol",
                "description": "Guided onboarding: stage baseline definitions, seed a minimal review task, then open key floors. No auto-commit.",
                "category": "architect",
                "host_action": "arise_protocol",
                "host_action_args": {"confirm": True},
                "safety": {"requires_confirm": True},
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "sweep_legacy_packs",
                "title": "Sweep Legacy Packs (Oracle -> Smith)",
                "description": (
                    "Ingest archived legacy packs into Oracle (dedupe-only) and stage a single reconciliation task into Smith "
                    "for Trinity approval. No auto-commit."
                ),
                "category": "oracle",
                "host_action": "sweep_legacy_packs",
                "host_action_args": {"confirm": True, "max_files": 200},
                "safety": {"requires_confirm": True},
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "sweep_legacy_packs_deep",
                "title": "Sweep Legacy Packs (Deep)",
                "description": (
                    "Deeper legacy packs sweep (more files + broader allowlist). "
                    "Still non-destructive: Oracle dedupes; Smith stages a single reconciliation task."
                ),
                "category": "oracle",
                "host_action": "sweep_legacy_packs",
                "host_action_args": {
                    "confirm": True,
                    "max_files": 2500,
                    "include_extensions": [".py", ".md", ".json", ".txt", ".yaml", ".yml", ".csv"],
                },
                "safety": {"requires_confirm": True},
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "set_immersive_unpinned",
                "title": "Set Immersive Unpinned (This User)",
                "description": "Toggle whether interactive immersive controls are allowed for the active user.",
                "category": "environment",
                "host_action": "set_immersive_unpinned",
                "params": [
                    {"name": "enabled", "type": "bool", "required": True, "default": False, "ui": {"control": "toggle", "label": "Enable immersive controls"}},
                ],
                "enabled": True,
            },
            # Floor tool deep-links (single dynamic menu: Command Palette).
            {
                "kind": "action_def",
                "id": "open_architect_project_manager",
                "title": "Open Architect: Project Manager",
                "description": "Open the Architect floor and select the Project Manager tab.",
                "category": "architect",
                "host_action": "open_z_floor_tab",
                "host_action_args": {"floor_name": "Architect", "subtab_title": "Project Manager"},
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "open_oracle_library",
                "title": "Open Oracle: Library",
                "description": "Open the Oracle floor and select the Library tab.",
                "category": "oracle",
                "host_action": "open_z_floor_tab",
                "host_action_args": {"floor_name": "Oracle", "subtab_title": "Library"},
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "open_oracle_backup_restore",
                "title": "Open Oracle: Backup & Restore (Request Only)",
                "description": "Open the Oracle floor and select Backup & Restore (request-only staging).",
                "category": "oracle",
                "host_action": "open_z_floor_tab",
                "host_action_args": {"floor_name": "Oracle", "subtab_title": "Backup & Restore"},
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "open_smith_jobs_artifacts",
                "title": "Open Smith: Jobs & Artifacts",
                "description": "Open the Smith floor and select Jobs & Artifacts (immutable ledger).",
                "category": "smith",
                "host_action": "open_z_floor_tab",
                "host_action_args": {"floor_name": "Smith", "subtab_title": "Jobs & Artifacts"},
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "open_merovingian_logs",
                "title": "Open Merovingian: Logs",
                "description": "Open the Merovingian floor and select Logs (file viewer).",
                "category": "merovingian",
                "host_action": "open_z_floor_tab",
                "host_action_args": {"floor_name": "Merovingian", "subtab_title": "Logs"},
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "open_merovingian_database_browser",
                "title": "Open Merovingian: Database Browser",
                "description": "Open the Merovingian floor and select Database Browser.",
                "category": "merovingian",
                "host_action": "open_z_floor_tab",
                "host_action_args": {"floor_name": "Merovingian", "subtab_title": "Database Browser"},
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "open_merovingian_profiler",
                "title": "Open Merovingian: Performance Profiler",
                "description": "Open the Merovingian floor and select Performance Profiler.",
                "category": "merovingian",
                "host_action": "open_z_floor_tab",
                "host_action_args": {"floor_name": "Merovingian", "subtab_title": "Performance Profiler"},
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "open_neo_planner",
                "title": "Open Neo: Planner",
                "description": "Open the Neo floor and select Planner (Plan A/B/C staging).",
                "category": "neo",
                "host_action": "open_z_floor_tab",
                "host_action_args": {"floor_name": "Neo", "subtab_title": "Planner"},
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "open_morpheus_dependency_map",
                "title": "Open Morpheus: Dependency Map",
                "description": "Open the Morpheus floor and select Dependency Map.",
                "category": "morpheus",
                "host_action": "open_z_floor_tab",
                "host_action_args": {"floor_name": "Morpheus", "subtab_title": "Dependency Map"},
                "enabled": True,
            },
            {
                "kind": "action_def",
                "id": "open_trinity_settings_hub",
                "title": "Open Trinity: Settings Hub",
                "description": "Open the Trinity floor and select Settings Hub.",
                "category": "trinity",
                "host_action": "open_z_floor_tab",
                "host_action_args": {"floor_name": "Trinity", "subtab_title": "Settings Hub"},
                "enabled": True,
            },
        ]
        for a in action_defs:
            _stage(a, ["v1r", "bootstrap", "action_def"])

        # Bento widget definitions (optional UI extensions; enable/disable post-commit).
        bento_widgets = [
            {
                "kind": "bento_widget",
                "id": "v1r_unified_search",
                "title": "Unified Search",
                "floor": "Trinity",
                "widget_type": "action",
                "enabled": True,
                "config": {"host_action": "open_unified_search", "host_action_args": {"initial_category": "all"}},
                "tags": ["v1r", "bootstrap"],
            },
            {
                "kind": "bento_widget",
                "id": "v1r_object_catalog",
                "title": "Object Catalog",
                "floor": "Trinity",
                "widget_type": "action",
                "enabled": True,
                "config": {"icon": "OBJ", "host_action": "open_object_catalog", "host_action_args": {"scope": "trinity"}},
                "tags": ["v1r", "bootstrap"],
            },
            {
                "kind": "bento_widget",
                "id": "v1r_oracle_object_catalog",
                "title": "Oracle: Object Catalog",
                "floor": "Oracle",
                "widget_type": "action",
                "enabled": True,
                "config": {"icon": "VAULT", "host_action": "open_object_catalog", "host_action_args": {"scope": "oracle"}},
                "tags": ["v1r", "bootstrap"],
            },
            {
                "kind": "bento_widget",
                "id": "v1r_it_portal_z_direct",
                "title": "IT Portal: Z Direct",
                "floor": "Trinity",
                "widget_type": "action",
                "enabled": True,
                "config": {
                    "icon": "ZDIR",
                    "host_action": "open_it_portal_z_direct",
                    "host_action_args": {"channel": "Z+3", "peer": "All", "kind": "all", "tags": "any"},
                },
                "tags": ["v1r", "bootstrap"],
            },
            {
                "kind": "bento_widget",
                "id": "v1r_stage_v1r",
                "title": "Stage V1R",
                "floor": "Trinity",
                "widget_type": "action",
                "enabled": False,
                "config": {"host_action": "stage_v1r_definitions", "host_action_args": {"confirm": True}},
                "tags": ["v1r", "bootstrap"],
            },
            {
                "kind": "bento_widget",
                "id": "v1r_sweep_legacy_packs",
                "title": "Sweep Legacy Packs",
                "floor": "Trinity",
                "widget_type": "action",
                "enabled": False,
                "config": {"host_action": "sweep_legacy_packs", "host_action_args": {"confirm": True, "max_files": 200}},
                "tags": ["v1r", "bootstrap", "legacy_packs"],
            },
            {
                "kind": "bento_widget",
                "id": "v1r_sweep_legacy_packs_deep",
                "title": "Sweep Legacy Packs (Deep)",
                "floor": "Trinity",
                "widget_type": "action",
                "enabled": False,
                "config": {
                    "host_action": "sweep_legacy_packs",
                    "host_action_args": {
                        "confirm": True,
                        "max_files": 2500,
                        "include_extensions": [".py", ".md", ".json", ".txt", ".yaml", ".yml", ".csv"],
                    },
                },
                "tags": ["v1r", "bootstrap", "legacy_packs"],
            },
            {
                "kind": "bento_widget",
                "id": "v1r_reset_tailoring",
                "title": "Reset Tailoring",
                "floor": "Trinity",
                "widget_type": "action",
                "enabled": False,
                "config": {"host_action": "reset_tailoring", "host_action_args": {"confirm": True}},
                "tags": ["v1r", "bootstrap"],
            },
        ]
        for w in bento_widgets:
            _stage(w, ["v1r", "bootstrap", "bento_widget"])

        try:
            fp = (Path(__file__).resolve().parent / "Z Axis" / "Z+3_Trinity" / "Z Direct" / "objects.jsonl").resolve()
        except Exception:
            fp = None

        messagebox.showinfo(
            "Stage V1R",
            f"Staged {staged} definition(s) to Trinity Z Direct (append-only)."
            + (f"\n\n{fp}" if fp else ""),
            parent=self,
        )
        return True

    def arise_protocol(self, *, confirm: bool = True) -> bool:
        """
        Guided onboarding (UI-first, no auto-commit).

        Intended behavior:
        - Stage baseline V1R definitions (append-only to Trinity Z Direct).
        - Seed a minimal review task into Smith via directed Z Direct (Z+3 -> Z-3).
        - Open the primary surfaces a new operator typically needs next.

        This function is designed to be safe to run repeatedly; it does not write to
        durable registries directly (IT Portal remains the commit gate).
        """
        if confirm:
            ok = messagebox.askyesno(
                "Arise Protocol",
                "Run Arise Protocol?\n\n"
                "- Stages baseline definitions into Trinity Z Direct (append-only)\n"
                "- Stages one onboarding task into Smith via directed Z Direct\n"
                "- Opens Architect / Oracle / Trinity settings surfaces\n\n"
                "No durable registry commits will be made automatically.",
                parent=self,
            )
            if not ok:
                return False

        # 1) Stage baseline definitions (best-effort).
        try:
            self.stage_v1r_definitions(confirm=False)
        except Exception:
            pass

        # 2) Seed a minimal onboarding task to Smith (directed queue).
        try:
            from core.services import get_z_direct  # type: ignore

            zd = get_z_direct()
            import uuid

            task_id = f"arise_{uuid.uuid4().hex[:10]}"
            task = {
                "kind": "task",
                "id": task_id,
                "title": "Arise Protocol: Review staged definitions + configure first project",
                "description": (
                    "Review staged definitions in Trinity IT Portal (Z Direct), commit what you want, then "
                    "use Architect to set initial OKRs and Oracle to ingest project docs."
                ),
                "status": "todo",
                "priority": 0,
            }
            env = zd.make_envelope(
                kind="object",
                channel="Z+3",
                payload=task,
                z_context="Trinity",
                source="N.arise_protocol",
                tags=["v1r", "arise", "task"],
            )
            zd.append_channel_outbox(from_channel="Z+3", to_channel="Z-3", payload=env)
            zd.append_channel_inbox(to_channel="Z-3", from_channel="Z+3", payload=env)
        except Exception as e:
            # Keep the flow usable even if directed staging fails.
            try:
                messagebox.showwarning(
                    "Arise Protocol",
                    f"Baseline definitions staged, but failed to seed the Smith review task:\n{e}",
                    parent=self,
                )
            except Exception:
                pass

        # 3) Open key surfaces (best-effort order).
        try:
            self.open_z_floor_tab("Architect", "Project Manager")
        except Exception:
            pass
        try:
            self.open_oracle_registry()
        except Exception:
            pass
        try:
            self.open_z_floor_tab("Trinity", "Settings Hub")
        except Exception:
            pass

        # If we're IT/Founder, jump straight into the review queue for the new task.
        try:
            if getattr(self, "user_mode", "") == "it_founder":
                self.open_it_portal_z_direct(channel="Z-3", peer="Z+3", kind="task", tags="any", search="arise_")
        except Exception:
            pass

        return True

    def sweep_legacy_packs(
        self,
        *,
        confirm: bool = True,
        max_files: int = 200,
        include_extensions: Optional[List[str]] = None,
    ) -> bool:
        """
        Ingest archived legacy packs into Oracle (dedupe-only) and stage a reconciliation task (approval-gated).

        This is designed to be non-destructive:
        - Oracle dedupes against the vault; no overwrites of canonical runtime sources.
        - Smith will stage a single summary task into Trinity's review queue via Z Direct.
        """
        if confirm:
            ok = messagebox.askyesno(
                "Sweep Legacy Packs",
                "Run a legacy packs sweep?\n\n"
                "- Oracle ingests `Z Axis/archive/legacy_packs` (allowlist .py/.md/.json/.txt)\n"
                "- Dedupes against the Oracle vault (no file mutation)\n"
                "- Smith stages one reconciliation task into Trinity (approval-gated)\n\n"
                "This may take a while on first run.",
                parent=self,
            )
            if not ok:
                return False

        try:
            root = Path(__file__).resolve().parent
            legacy_root = (root / "Z Axis" / "archive" / "legacy_packs").resolve()
        except Exception as e:
            messagebox.showerror("Sweep Legacy Packs", f"Could not resolve legacy packs path:\n{e}", parent=self)
            return False

        if not legacy_root.exists():
            messagebox.showwarning(
                "Sweep Legacy Packs",
                f"Legacy packs folder not found:\n{legacy_root}",
                parent=self,
            )
            return False

        try:
            self.update_status(f"Sweeping legacy packs (max_files={max_files})...")
        except Exception:
            pass

        allowlist = include_extensions or [".py", ".md", ".json", ".txt"]

        def _run():
            # Load Oracle integrator via file-loader (floors are not always importable packages).
            try:
                OracleSmartFloorIntegrator = _load_symbol_from_file(
                    "Z Axis/Z-2_Oracle/components/oracle_smart_floor_integrator.py",
                    "OracleSmartFloorIntegrator",
                )
            except Exception as e:
                self._run_ui_action(
                    "Sweep Legacy Packs",
                    lambda: messagebox.showerror(
                        "Sweep Legacy Packs",
                        f"Oracle integrator unavailable:\n{e}",
                        parent=self,
                    ),
                    parent=self,
                )
                return

            try:
                oracle = OracleSmartFloorIntegrator()
                summary = oracle.ingest_directory(
                    str(legacy_root),
                    include_extensions=list(allowlist),
                    max_files=int(max_files) if max_files is not None else None,
                    recursive=True,
                    metadata={"ingest_source": "legacy_packs_sweep", "tags": ["legacy_packs"]},
                )
            except Exception as e:
                self._run_ui_action(
                    "Sweep Legacy Packs",
                    lambda: messagebox.showerror(
                        "Sweep Legacy Packs",
                        f"Sweep failed:\n{e}",
                        parent=self,
                    ),
                    parent=self,
                )
                return

            def _done():
                try:
                    try:
                        self.update_status("Legacy packs sweep completed (review via IT Portal -> Z Direct).")
                    except Exception:
                        pass
                    messagebox.showinfo(
                        "Sweep Legacy Packs",
                        "Sweep completed.\n\n"
                        f"Folder: {legacy_root}\n"
                        f"Files scanned: {summary.get('files_total')}\n"
                        f"Deduped: {summary.get('files_deduped')}\n"
                        f"New ingested: {summary.get('files_ingested')}\n"
                        f"Failed: {summary.get('files_failed')}\n\n"
                        "Next: Trinity IT Portal -> Z Direct -> filter tags `legacy_packs` to review/commit.",
                        parent=self,
                    )
                except Exception:
                    pass

                try:
                    if getattr(self, "user_mode", "") == "it_founder":
                        self.open_it_portal_z_direct(channel="Z-3", peer="All", kind="task", tags="legacy_packs", search="legacy_packs")
                except Exception:
                    pass

            try:
                self.after(0, _done)
            except Exception:
                _done()

        try:
            t = threading.Thread(target=_run, name="SweepLegacyPacks", daemon=True)
            t.start()
        except Exception as e:
            messagebox.showerror("Sweep Legacy Packs", f"Failed to start background sweep:\n{e}", parent=self)
            return False

        return True

    def _run_ui_action(self, name: str, fn, *, parent: Optional[tk.Misc] = None):
        """
        Execute a UI callback with consistent error surfacing + logging.

        This prevents silent failures where a button appears to do nothing.
        """
        try:
            return fn()
        except Exception as e:
            msg = f"{name} failed: {e}"
            try:
                self.update_status(msg)
            except Exception:
                pass
            # Publish to the inter-floor bus when available (diagnostics + audit trail).
            try:
                from core.services import get_event_bus  # type: ignore

                bus = get_event_bus()
                if bus is not None:
                    bus.publish(
                        "ui.action.error",
                        {
                            "action": name,
                            "error": str(e),
                            "user": self._current_user_id_for_bento(),
                            "mode": getattr(self, "user_mode", None),
                        },
                    )
            except Exception:
                pass
            try:
                messagebox.showerror("Action Failed", msg, parent=(parent or self))
            except Exception:
                pass
            return None

    def _wire_bento_widget_callbacks(self, bento: Any) -> None:
        """
        Attach meaningful callbacks to UniversalBentoSystem widgets.

        This is used for both immersive overlay mode and the 2D Bento panel in the main menu.
        """
        if bento is None or not hasattr(bento, "get_all_widgets"):
            return

        def _safe(name: str, fn):
            def _cb(_widget=None):
                self._run_ui_action(name, fn, parent=self)
            return _cb

        def _open_trinity():
            self.open_z_floor("Trinity")

        def _open_oracle():
            self.open_z_floor("Oracle")

        def _open_morpheus():
            self.open_z_floor("Morpheus")

        def _open_smith():
            self.open_z_floor("Smith")

        def _open_merovingian():
            self.open_z_floor("Merovingian")

        def _open_neo():
            self.open_z_floor("Neo")

        def _open_construct():
            self.open_z_floor("TheConstruct")

        def _open_knowledge_search(*, initial_query: str = "", initial_category: str = "all"):
            # Unified Search is the primary library surface; fallback to Morpheus if unavailable.
            try:
                self.open_unified_search(initial_query=initial_query, initial_category=initial_category)
                return
            except Exception:
                try:
                    _open_morpheus()
                except Exception:
                    pass

        widget_actions = {
            # Trinity
            "trinity_dashboard": _safe("open_it_portal", self.open_it_portal) if self.user_mode == "it_founder" else _safe("open_trinity", _open_trinity),
            "trinity_layout": _safe("open_workspace_layout", self.open_workspace_layout),
            "trinity_widgets": _safe("open_trinity", _open_trinity),
            # Prefer per-user theme toggle when available; fallback to settings hub.
            "trinity_themes": _safe("toggle_theme_or_settings", lambda: getattr(bento, "toggle_theme_preference", lambda: False)() or self.show_settings()),

            # Neo
            "neo_achilles": _safe("open_neo", _open_neo),
            "neo_learning": _safe("open_neo", _open_neo),
            "neo_models": _safe("open_neo", _open_neo),

            # Architect (workspace + projects)
            "architect_projects": _safe("show_projects", self.show_projects),
            "architect_tasks": _safe("open_smith", _open_smith),
            "architect_timeline": _safe("open_trinity", _open_trinity),

            # Construct
            "construct_raphael": _safe("open_construct", _open_construct),
            "construct_schwarzschild": _safe("open_construct", _open_construct),
            "construct_quantum": _safe("open_construct", _open_construct),
            "construct_gravity": _safe("open_construct", _open_construct),

            # Oracle
            "oracle_vault": _safe("open_oracle_panel", self.open_oracle_panel),
            "oracle_encyclopedia": _safe("open_knowledge_search", lambda: _open_knowledge_search(initial_category="knowledge")),
            "oracle_dictionary": _safe("open_knowledge_search", lambda: _open_knowledge_search(initial_category="knowledge")),
            "oracle_z_direct": _safe("open_oracle_registry", self.open_oracle_registry),

            # Smith
            "smith_jobs": _safe("open_smith", _open_smith),
            "smith_sops": _safe("open_smith", _open_smith),
            "smith_scheduler": _safe("open_smith", _open_smith),

            # Merovingian
            "mero_health": _safe("open_merovingian", _open_merovingian),
            "mero_metrics": _safe("open_merovingian", _open_merovingian),
            "mero_alerts": _safe("open_merovingian", _open_merovingian),

            # Morpheus
            "morpheus_search": _safe("open_unified_search", lambda: _open_knowledge_search(initial_category="all")),
            "morpheus_docs": _safe("open_morpheus", _open_morpheus),
            "morpheus_analyze": _safe("open_morpheus", _open_morpheus),
        }

        for w in bento.get_all_widgets() or []:
            try:
                wid = getattr(w, "id", "")
                if wid in widget_actions:
                    w.callback = widget_actions[wid]
                    continue

                # Data-defined widgets can specify a host action to invoke without adding new code.
                cfg = getattr(w, "config", None)
                if isinstance(cfg, dict):
                    host_action = cfg.get("host_action")
                    host_action_args = cfg.get("host_action_args")
                    if isinstance(host_action, str) and host_action.strip():
                        fn = getattr(self, host_action.strip(), None)
                        if callable(fn):
                            if isinstance(host_action_args, dict) and host_action_args:
                                w.callback = _safe(host_action.strip(), lambda fn=fn, a=host_action_args: fn(**a))
                            else:
                                w.callback = _safe(host_action.strip(), fn)
            except Exception:
                continue

    def _register_bento_frame_shortcuts(self, bento_frame: Any) -> None:
        """Expose Bento menu focus hooks to global shortcuts (best-effort)."""
        try:
            hook = getattr(bento_frame, "_bento_focus_search", None)
        except Exception:
            hook = None
        self._bento_focus_search = hook if callable(hook) else None

    def focus_bento_search(self) -> None:
        """Focus the Bento search box if a Bento panel is currently active."""
        hook = getattr(self, "_bento_focus_search", None)
        if callable(hook):
            try:
                hook()
            except Exception:
                pass

    def toggle_bento_panel(self) -> None:
        """
        Toggle the current Bento panel visibility (best-effort).

        This is intentionally implemented as a hook so multiple shells (main menu,
        Construct host, etc.) can expose a consistent action without duplicating UI logic.
        """
        hook = getattr(self, "_toggle_bento_panel_hook", None)
        if callable(hook):
            try:
                hook()
            except Exception:
                pass

    def _get_bento_for_actions(self):
        """Return the global Bento system with the current user context set (best-effort)."""
        try:
            _force_trinity_ui_package()
            from ui.universal_bento_system import get_bento_system  # type: ignore

            bento = get_bento_system()
            setter = getattr(bento, "set_user_context", None)
            if callable(setter):
                setter(self._current_user_id_for_bento())
            return bento
        except Exception:
            return None

    def bento_clear_recents(self) -> bool:
        """Clear Bento recent items for the active user (best-effort)."""
        b = self._get_bento_for_actions()
        if b is None:
            return False
        try:
            fn = getattr(b, "clear_recent_widgets", None)
            if callable(fn):
                ok = bool(fn())
                if ok:
                    self.update_status("Bento recents cleared")
                return ok
        except Exception:
            return False
        return False

    def bento_clear_favorites(self) -> bool:
        """Clear Bento favorites for the active user (best-effort)."""
        b = self._get_bento_for_actions()
        if b is None:
            return False
        try:
            fn = getattr(b, "clear_favorite_widgets", None)
            if callable(fn):
                ok = bool(fn())
                if ok:
                    self.update_status("Bento favorites cleared")
                return ok
        except Exception:
            return False
        return False

    def run_simulation(self, sim_type: str = "", **params):
        """
        Host hook for data-defined actions/simulations (simulation_def/action_def).

        Invokes TheConstruct's floor API (which stages outputs into Z Direct) and
        returns the raw result.
        """
        sim_type = str(sim_type or "").strip()
        if not sim_type:
            raise ValueError("sim_type is required")

        try:
            from importlib.util import spec_from_file_location, module_from_spec

            tc_path = (Path(__file__).resolve().parent / "Z Axis" / "Z0_TheConstruct" / "TheConstruct.py").resolve()
            if not tc_path.exists():
                raise FileNotFoundError(tc_path)
            spec = spec_from_file_location("lightspeed_construct_floor", str(tc_path))
            if spec is None or spec.loader is None:
                raise ImportError("Cannot load TheConstruct floor module")
            mod = module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore
            fn = getattr(mod, "run_simulation", None)
            if not callable(fn):
                raise AttributeError("TheConstruct.run_simulation not found")
            return fn(sim_type, **params)
        except Exception:
            # Minimal fallback (no staging) for basic sims.
            try:
                from core.services.physics_tools import calculate_raphael_equations, generate_big_bang_simulation  # type: ignore

                if sim_type == "raphael":
                    return calculate_raphael_equations(**params)
                if sim_type == "bigbang":
                    return generate_big_bang_simulation(**params)
            except Exception:
                pass
            raise

    def show_immersive_world(self, interactive: bool = False):
        """
        TheConstruct environment surface.

        Default (interactive=False): UI-first host mode.
        - 3D is a passive background (fixed camera)
        - 2D Bento panel is the primary readable/clickable UI

        Optional (interactive=True): immersive mode.
        - WASD + mouse look via the immersive engine
        - curved overlay remains available (CapsLock x2)
        """
        if interactive and not self._immersive_unpinned():
            # Prevent "immersive-first creep": interactive controls are opt-in per user.
            ok = messagebox.askyesno(
                "Immersive Controls (Pinned)",
                "Interactive immersive controls (WASD + mouse-look) are pinned OFF by default.\n\n"
                "Unpin immersive controls for this user and continue?",
                parent=self,
            )
            if not ok:
                interactive = False
            else:
                try:
                    self.set_immersive_unpinned(True)
                except Exception:
                    pass
        self.push_history("dashboard")
        self.clear_screen()
        self.update_breadcrumb("Home > Immersive World" if interactive else "Home > Environment Host")

        # Overlay state shared by header buttons.
        bento_panel = None
        def _compute_bento_place() -> Dict[str, Any]:
            try:
                w = int(scene.winfo_width() or 0)
            except Exception:
                w = 0
            width_px = 520
            if w > 0:
                width_px = max(560, min(860, int(w * 0.42)))
            return {"relx": 0.985, "rely": 0.05, "anchor": "ne", "width": width_px, "relheight": 0.90}

        def _toggle_bento_panel():
            nonlocal bento_panel
            if bento_panel is None:
                return
            try:
                if bento_panel.winfo_ismapped():
                    bento_panel.place_forget()
                    try:
                        setattr(canvas, "_lightspeed_dim", 0.0)
                    except Exception:
                        pass
                else:
                    bento_panel.place(**_compute_bento_place())
                    bento_panel.lift()
                    try:
                        setattr(canvas, "_lightspeed_dim", 0.35)
                    except Exception:
                        pass
                    # Focus search when the menu is explicitly opened.
                    try:
                        self.focus_bento_search()
                    except Exception:
                        pass
            except Exception:
                pass

        # Expose the current shell's Bento toggle to global actions (command palette, hotkeys).
        try:
            self._toggle_bento_panel_hook = _toggle_bento_panel
        except Exception:
            pass

        # Expose the current shell's Bento toggle to global actions (command palette, hotkeys).
        try:
            self._toggle_bento_panel_hook = _toggle_bento_panel
        except Exception:
            pass

        def _toggle_mode():
            try:
                self.show_immersive_world(interactive=not interactive)
            except Exception:
                pass

        header = tk.Frame(self.main_container, bg=COLORS["bg_panel"])
        header.pack(fill="x")

        title = (
            "Immersive World (TheConstruct) - WASD / Shift Run / Space Jump"
            if interactive
            else "Environment Host (TheConstruct) - UI-first (Bento is primary; 3D is ambient)"
        )
        tk.Label(
            header,
            text=title,
            bg=COLORS["bg_panel"],
            fg=COLORS["accent_cyan"],
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=12, pady=10)

        tk.Button(
            header,
            text="Bento Panel",
            bg=COLORS["bg_dark"],
            fg=COLORS["text_green"],
            command=_toggle_bento_panel,
        ).pack(side="right", padx=(6, 6), pady=8)

        tk.Button(
            header,
            text=("UI-first" if interactive else "Enable WASD"),
            bg=COLORS["bg_dark"],
            fg=COLORS["text_green"],
            command=_toggle_mode,
        ).pack(side="right", padx=(6, 6), pady=8)

        tk.Button(
            header,
            text="Exit",
            bg=COLORS["bg_blue"],
            fg=COLORS["text_green"],
            command=self.go_back,
        ).pack(side="right", padx=(6, 12), pady=8)

        scene = tk.Frame(self.main_container, bg=COLORS["bg_dark"])
        scene.pack(fill="both", expand=True)

        canvas = tk.Canvas(scene, bg="#000000", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        self.update_idletasks()
        try:
            setattr(canvas, "_lightspeed_dim", 0.0)
        except Exception:
            pass

        hint = tk.Label(
            scene,
            text=(
                "UI-first: use the Bento panel for readable navigation."
                if not interactive
                else "Immersive: click canvas to focus; Esc toggles menu; CapsLock x2 also toggles overlay."
            ),
            bg=COLORS["bg_panel"],
            fg=COLORS["text_green"],
            font=("Arial", 10, "bold"),
            padx=10,
            pady=6,
        )
        hint.place(relx=0.01, rely=0.01, anchor="nw")

        # Build Bento overlay (best-effort).
        try:
            _force_trinity_ui_package()
            from ui.universal_bento_system import get_bento_system  # type: ignore

            bento = get_bento_system()
            try:
                bento.parent = self
            except Exception:
                pass
            try:
                setter = getattr(bento, "set_user_context", None)
                if callable(setter):
                    setter(self._current_user_id_for_bento())
            except Exception:
                pass
            try:
                self._wire_bento_widget_callbacks(bento)
            except Exception:
                pass

            panel_bg = COLORS["bg_panel"]
            try:
                panel_bg = (getattr(bento, "palette", {}) or {}).get("accent_phthalo_green", panel_bg)
            except Exception:
                pass
            bento_panel = tk.Frame(scene, bg=panel_bg)
            # UI-first: visible by default. Immersive: start hidden (curved overlay is the default UI).
            if not interactive:
                bento_panel.place(**_compute_bento_place())
                try:
                    setattr(canvas, "_lightspeed_dim", 0.35)
                except Exception:
                    pass
            try:
                bento_panel.lift()
            except Exception:
                pass
            bento_frame = bento.create_2d_frame(bento_panel)
            bento_frame.pack(fill="both", expand=True)
            try:
                self._register_bento_frame_shortcuts(bento_frame)
            except Exception:
                pass

            def _on_scene_resize(_e=None):
                nonlocal bento_panel
                if bento_panel is None:
                    return
                try:
                    if bento_panel.winfo_ismapped():
                        bento_panel.place_configure(**_compute_bento_place())
                except Exception:
                    pass

            try:
                scene.bind("<Configure>", _on_scene_resize)
            except Exception:
                pass
        except Exception:
            bento_panel = None
            try:
                setattr(canvas, "_lightspeed_dim", 0.0)
            except Exception:
                pass

        # Shared physics tuning.
        cfg = self._load_unified_config()
        physics = (cfg.get("physics") or {}) if isinstance(cfg, dict) else {}

        if interactive:
            # Full immersive engine (WASD + mouse look).
            try:
                attach = _load_symbol_from_file(
                    "Z Axis/Z0_TheConstruct/ui/immersive_3d_engine.py",
                    "attach_immersive_3d_environment",
                )

                def on_action(obj):
                    data = obj.data or {}
                    if data.get("type") == "physics_simulation_launcher":
                        self.open_z_floor("TheConstruct")
                        return
                    if data.get("type") == "bento_ui_launcher":
                        self.open_z_floor("Trinity")
                        return
                    if data.get("type") == "neo_library_launcher":
                        self.open_z_floor("Neo")
                        return
                    if data.get("type") == "settings_hub":
                        self.open_z_floor("Trinity")
                        return
                    if obj.id == "achilles_sphere":
                        self.open_z_floor("Neo")
                        return
                    if data.get("builtin") and data.get("widget_id") == "tower_view":
                        try:
                            show_tower_3d_view = _load_symbol_from_file(
                                "Z Axis/Z0_TheConstruct/ui/tower_3d_view.py",
                                "show_tower_3d_view",
                            )
                            show_tower_3d_view(parent=self)
                        except Exception:
                            pass
                        return

                engine = attach(self, canvas, on_action=on_action, physics=physics, capture_mouse=True, enable_input=True)
                try:
                    bento_overlay = getattr(getattr(engine, "ui_overlay", None), "bento_system", None)
                    if bento_overlay is not None:
                        try:
                            setter = getattr(bento_overlay, "set_user_context", None)
                            if callable(setter):
                                setter(self._current_user_id_for_bento())
                        except Exception:
                            pass
                        self._wire_bento_widget_callbacks(bento_overlay)
                except Exception:
                    pass

                self.update_status("Immersive world ready (click canvas to focus)")
                return
            except Exception:
                self.update_status("Immersive world failed; falling back to UI-first")
                try:
                    self.show_immersive_world(interactive=False)
                except Exception:
                    pass
                return

        # UI-first host (passive fixed-camera environment).
        try:
            attach = _load_symbol_from_file(
                "Z Axis/Z0_TheConstruct/ui/cognigrex_3d_environment.py",
                "attach_cognigrex_3d",
            )

            def _on_floor_select(floor):
                try:
                    floor_name = getattr(floor, "name", "") or ""
                    if not floor_name and hasattr(floor, "value"):
                        v = getattr(floor, "value", None)
                        if isinstance(v, (list, tuple)) and len(v) > 1:
                            floor_name = str(v[1])
                    if floor_name:
                        self.open_z_floor(str(floor_name))
                except Exception:
                    pass

            self._immersive_host_engine = attach(self, canvas, on_floor_select=_on_floor_select)
            self.update_status("Environment host ready (Bento is primary UI)")
        except Exception:
            # Fallback: immersive engine in passive preview mode (no input capture).
            try:
                attach = _load_symbol_from_file(
                    "Z Axis/Z0_TheConstruct/ui/immersive_3d_engine.py",
                    "attach_immersive_3d_environment",
                )
                self._immersive_host_engine = attach(
                    self,
                    canvas,
                    on_action=None,
                    physics=physics,
                    capture_mouse=False,
                    enable_input=False,
                )
                self.update_status("Environment host ready (fallback renderer)")
            except Exception:
                self._immersive_host_engine = None
                self.update_status("Environment host unavailable (renderer attach failed)")


    def setup_styles(self):
        """Configure TTK styles"""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass

        # Portal styles (from lightspeed_immersive_complete.py)
        style.configure('Portal.TButton',
                       background=COLORS['bg_blue'],
                       foreground=COLORS['text_green'],
                       borderwidth=2,
                       font=('Arial', 11, 'bold'))

        style.configure('Portal.TLabel',
                       background=COLORS['bg_dark'],
                       foreground=COLORS['text_green'],
                       font=('Arial', 10))

        style.configure('Header.TLabel',
                       background=COLORS['bg_dark'],
                       foreground=COLORS['accent_cyan'],
                       font=('Arial', 16, 'bold'))

    def create_top_bar(self):
        """Top navigation bar"""
        self.top_bar = tk.Frame(self, bg=COLORS['bg_panel'], height=60)
        self.top_bar.pack(side='top', fill='x')
        self.top_bar.pack_propagate(False)

        # Logo: the PDF shell treats the title/path as navigation, not decoration.
        self.logo_button = tk.Button(
            self.top_bar,
            text="LIGHTSPEED",
            command=self.show_home,
            font=('Arial', 18, 'bold'),
            bg=COLORS['bg_panel'],
            fg=COLORS['accent_cyan'],
            activebackground=COLORS['bg_blue'],
            activeforeground=COLORS['text_white'],
            relief="flat",
            bd=0,
            cursor="hand2",
        )
        self.logo_button.pack(side='left', padx=(16, 8))

        # Breadcrumb
        self.breadcrumb_frame = tk.Frame(self.top_bar, bg=COLORS['bg_panel'])
        self.breadcrumb_frame.pack(side='left', expand=True, padx=30)

        # Controls
        self.controls = tk.Frame(self.top_bar, bg=COLORS['bg_panel'])
        self.controls.pack(side='right', padx=20)

        # User label (will be populated after login)
        self.user_label = tk.Label(self.controls, text="Not logged in",
                                   bg=COLORS['bg_panel'],
                                   fg=COLORS['text_green'],
                                   font=('Arial', 10))
        self.user_label.pack(side='left', padx=10)

        tk.Button(
            self.controls,
            text="Home",
            command=self.show_home,
            bg=COLORS['bg_dark'],
            fg=COLORS['text_white'],
            activebackground=COLORS['accent_cyan'],
            activeforeground=COLORS['bg_dark'],
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
        ).pack(side='left', padx=(0, 6))

    def create_main_container(self):
        """Main content area"""
        self.main_container = tk.Frame(self, bg=COLORS['bg_dark'])
        self.main_container.pack(side='top', fill='both', expand=True)

    def create_status_bar(self):
        """Bottom status bar"""
        self.status_bar = tk.Frame(self, bg=COLORS['bg_panel'], height=30)
        self.status_bar.pack(side='bottom', fill='x')
        self.status_bar.pack_propagate(False)

        self.status_label = tk.Label(self.status_bar, text="Ready",
                                     bg=COLORS['bg_panel'],
                                     fg=COLORS['text_green'],
                                     font=('Arial', 9), anchor='w')
        self.status_label.pack(side='left', padx=10)

        # Database indicator
        tk.Label(self.status_bar, text="DB Connected",
                bg=COLORS['bg_panel'],
                fg=COLORS['success_green'],
                font=('Arial', 8)).pack(side='right', padx=10)

    def bind_shortcuts(self):
        """Keyboard shortcuts"""
        self.bind('<Control-h>', lambda e: self.show_main_menu() if self.current_user else None)
        self.bind('<Control-k>', lambda e: self.open_command_palette() if self.current_user else None)
        self.bind('<Control-comma>', lambda e: self.show_settings() if self.current_user else None)
        self.bind('<Control-f>', lambda e: self.focus_bento_search() if self.current_user else None)
        self.bind('<Control-p>', lambda e: self.show_projects() if self.current_user else None)
        self.bind('<Control-d>', lambda e: self.show_document_viewer() if self.current_user else None)
        self.bind('<Control-t>', lambda e: self.show_project_tree() if self.current_user else None)
        self.bind('<Control-m>', lambda e: self.show_template_manager() if self.current_user else None)
        self.bind('<Control-q>', lambda e: self.quit())
        self.bind('<Escape>', lambda e: self.go_back())
        self.bind('<F1>', lambda e: self.show_help())

    def process_events(self):
        """Process event queue (real-time updates)"""
        try:
            while not self.event_queue.empty():
                event = self.event_queue.get_nowait()
                self._handle_event(event)
        except queue.Empty:
            pass

        # Schedule next check
        self.after(100, self.process_events)

    # ========================================================================
    # NAVIGATION
    # ========================================================================

    def clear_screen(self):
        """Clear main container"""
        # If an embedded immersive canvas is active, removing widgets naturally
        # ends the render loop (scheduled via Tk `after`). This flag prevents
        # future enhancements from leaking state across screens.
        try:
            self._immersive_active = False
        except Exception:
            pass
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def go_back(self):
        """Navigate back"""
        if self.screens_history:
            prev = self.screens_history.pop()
            if hasattr(self, f"show_{prev}"):
                getattr(self, f"show_{prev}")()

    def show_home(self):
        """Return to the main lobby, or login when no user session exists."""
        if self.current_user:
            self.show_main_menu()
        else:
            self.show_login()

    def push_history(self, screen):
        """Save to history"""
        if self.current_screen and self.current_screen != screen:
            self.screens_history.append(self.current_screen)
        self.current_screen = screen

    def _breadcrumb_command(self, part: str, index: int, parts: List[str]):
        key = part.strip().lower()
        if key == "home":
            return self.show_home
        if key in {"functions", "z functions", "smart floors"}:
            return self.show_floors_hub
        if key == "dashboard":
            return self.show_user_dashboard
        if key == "documents":
            return self.show_document_viewer
        if key == "project tree":
            return self.show_project_tree
        if key == "projects":
            return self.show_projects
        if key == "settings":
            return self.show_settings
        if key == "first-run setup":
            return self.show_setup
        if key == "login":
            return self.show_login
        return None

    def update_breadcrumb(self, path: str):
        """Update breadcrumb with clickable path segments."""
        for w in self.breadcrumb_frame.winfo_children():
            w.destroy()

        parts = path.split(" > ")
        for i, part in enumerate(parts):
            if i > 0:
                tk.Label(self.breadcrumb_frame, text=">",
                        bg=COLORS['bg_panel'],
                        fg=COLORS['text_green']).pack(side='left', padx=3)

            command = self._breadcrumb_command(part, i, parts)
            if command:
                tk.Button(
                    self.breadcrumb_frame,
                    text=part,
                    command=command,
                    bg=COLORS['bg_panel'],
                    fg=COLORS['accent_cyan'],
                    activebackground=COLORS['bg_blue'],
                    activeforeground=COLORS['text_white'],
                    font=('Arial', 10, 'bold'),
                    relief="flat",
                    bd=0,
                    cursor="hand2",
                ).pack(side='left')
            else:
                tk.Label(self.breadcrumb_frame, text=part,
                        bg=COLORS['bg_panel'],
                        fg=COLORS['accent_cyan'],
                        font=('Arial', 10, 'bold')).pack(side='left')

    def update_status(self, msg: str):
        """Update status message"""
        self.status_label.config(text=msg)

    def _register_event_bus_bridge(self):
        """
        Subscribe to the core EventBus and bridge async events into the Tk-safe UI queue.

        The EventBus may invoke handlers from background threads; all UI updates
        happen via `process_events()` on the Tk main thread.
        """
        if not self.event_bus:
            return

        def handler(event):
            try:
                self.event_queue.put(event)
            except Exception:
                return

        self._event_bus_handler = handler
        try:
            self._event_bus_subscription_id = self.event_bus.subscribe('*', handler, floor='N')
        except Exception as e:
            print(f"[WARNING] Could not subscribe to event bus: {e}")
            self._event_bus_subscription_id = None

    def _handle_event(self, event):
        """Handle a single event from the event queue."""
        try:
            event_type = getattr(event, 'type', None) or (event.get('type') if isinstance(event, dict) else None)
            source = getattr(event, 'source', None) or (event.get('source') if isinstance(event, dict) else None)
            priority = getattr(event, 'priority', None)
            if priority is None and isinstance(event, dict):
                priority = event.get('priority', 3)
            if priority is None:
                priority = 3
            data = getattr(event, 'data', None) or (event.get('data') if isinstance(event, dict) else None) or {}
        except Exception:
            self.update_status("Event received")
            return

        summary = f"{event_type or 'event'}"
        if source:
            summary += f" [{source}]"
        self.update_status(summary)

        # Surface critical alerts as modal popups.
        if event_type in ("system.alert.triggered", "system.health.changed") and int(priority) <= 2:
            try:
                message = data.get('message') if isinstance(data, dict) else None
                details = data.get('details') if isinstance(data, dict) else None
                body = message or summary
                if details:
                    body = f"{body}\n\n{details}"
                messagebox.showwarning("System Alert", body, parent=self)
            except Exception:
                return

    def _publish_event(self, event_type: str, data: Dict[str, Any], priority: int = 3):
        """Publish an event to the core EventBus (best-effort)."""
        if not self.event_bus:
            return
        try:
            from core.services.event_bus import Event
            self.event_bus.publish(
                Event(type=event_type, source="N", data=data, priority=priority),
                async_mode=True
            )
        except Exception:
            return

    def update_top_bar_controls(self):
        """Update top bar controls based on user mode"""
        # Clear existing controls
        for widget in self.controls.winfo_children():
            if widget != self.user_label:
                widget.destroy()

        # Achilles button
        tk.Button(self.controls, text="Ask Achilles",
                 command=self.ask_achilles,
                 bg=COLORS['accent_magenta'], fg='white',
                 font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        # Immersive world (TheConstruct) embedded into N.py
        tk.Button(self.controls, text="Immersive World",
                 command=self.open_3d_view,
                 bg='#9B59B6', fg='white',
                 font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        # Z-function selector (All users)
        self._create_z_floors_dropdown()

        if self.user_mode == "it_founder":
            operator_btn = tk.Menubutton(
                self.controls,
                text="Operator OS",
                bg=COLORS['bg_blue'],
                fg='white',
                font=('Arial', 10, 'bold'),
                relief='raised',
            )
            operator_menu = tk.Menu(
                operator_btn,
                tearoff=0,
                bg='#1e1e1e',
                fg='#ffffff',
                activebackground=COLORS['accent_cyan'],
                activeforeground='#000000',
                font=('Arial', 10),
            )
            operator_menu.add_command(
                label="Governance Hub",
                command=self.open_it_portal,
                state=("normal" if HAS_IT_PORTAL else "disabled"),
            )
            operator_menu.add_command(
                label="Trinity Functions",
                command=lambda: self.open_z_floor("Trinity"),
                state=("normal" if _is_floor_entry_available("Trinity") else "disabled"),
            )
            operator_menu.add_command(label="Settings Hub", command=self.show_settings)
            operator_menu.add_command(label="Template Outputs", command=self.show_template_manager)
            operator_menu.add_command(
                label="Open Dialogue",
                command=self.open_open_dialogue_board,
                state=("normal" if HAS_OPEN_DIALOGUE_BOARD else "disabled"),
            )

            try:
                import webbrowser

                web_menu = tk.Menu(
                    operator_menu,
                    tearoff=0,
                    bg='#1e1e1e',
                    fg='#ffffff',
                    activebackground=COLORS['accent_cyan'],
                    activeforeground='#000000',
                    font=('Arial', 10),
                )
                web_menu.add_command(label="Romer Operations", command=lambda: webbrowser.open("https://romer.industries/operations", new=2))
                web_menu.add_command(label="Achilles Desktop", command=lambda: webbrowser.open("https://romer.industries/achilles", new=2))
                web_menu.add_command(label="LightSpeed Home", command=lambda: webbrowser.open("https://romer.industries/lightspeedhome", new=2))
                web_menu.add_command(label="Achilles Data", command=lambda: webbrowser.open("https://romer.industries/data/achilles", new=2))
                operator_menu.add_cascade(label="Web Links", menu=web_menu)
            except Exception:
                pass

            operator_btn.config(menu=operator_menu)
            operator_btn.pack(side='left', padx=5)

        # User label (already packed, just update)
        self.user_label.pack(side='left', padx=10)

        # Logout button
        tk.Button(self.controls, text="Logout",
                 command=self.logout,
                 bg=COLORS['error_red'], fg='white',
                 font=('Arial', 9, 'bold'), width=8).pack(side='left', padx=5)

    def open_open_dialogue_board(self):
        """Launch the Open Dialogue Board (Tk message board for Codex/Claude/User)."""
        if not HAS_OPEN_DIALOGUE_BOARD:
            try:
                self.open_z_floor("Trinity")
                self.update_status("Trinity functions opened (Dialogue unavailable)")
                return
            except Exception:
                messagebox.showerror(
                    "Open Dialogue Unavailable",
                    "Open Dialogue Board is not available.\n"
                    "Check: Z Axis/Z+3_Trinity/tools/open_dialogue_board.py",
                    parent=self,
                )
            return
        try:
            board = launch_dialogue_board(parent=self)
            try:
                board.lift()
            except Exception:
                pass
            self.update_status("Open Dialogue Board opened")
        except Exception as exc:
            try:
                self.open_z_floor("Trinity")
                self.update_status("Trinity functions opened (Dialogue unavailable)")
                return
            except Exception:
                messagebox.showerror(
                    "Open Dialogue Error",
                    f"Failed to launch Open Dialogue Board:\n{exc}",
                    parent=self,
                )

    # ========================================================================
    # LOGIN SCREEN
    # ========================================================================

    def show_login(self):
        """Login screen with credential check - Premium UI"""
        self.clear_screen()
        self.push_history("login")
        self.update_breadcrumb("Login")

        # Main frame with premium background
        if self.use_premium_theme:
            frame = self.theme.create_glass_frame(self.main_container)
        else:
            frame = tk.Frame(self.main_container, bg=COLORS['bg_dark'])
        frame.pack(fill='both', expand=True)

        # LightSpeed logo/title (premium Garamond font)
        if self.use_premium_theme:
            title_label = self.theme.create_title_label(
                frame,
                text="LIGHTSPEED",
                font=(self.theme.config.get("typography", {}).get("font_primary", "Garamond"), 48, 'bold')
            )
            title_label.pack(pady=(100, 10))

            subtitle_label = self.theme.create_body_label(
                frame,
                text="Type I Civilization Platform",
                font=(self.theme.config.get("typography", {}).get("font_secondary", "Arial"), 16)
            )
            subtitle_label.pack(pady=(0, 50))
        else:
            tk.Label(frame, text="LIGHTSPEED",
                    font=('Arial', 48, 'bold'),
                    bg=COLORS['bg_dark'],
                    fg=COLORS['accent_cyan']).pack(pady=(100, 10))

            tk.Label(frame, text="Type I Civilization Platform",
                    font=('Arial', 16),
                    bg=COLORS['bg_dark'],
                    fg=COLORS['text_green']).pack(pady=(0, 50))

        # Login form (glass card)
        if self.use_premium_theme:
            login_frame = self.theme.create_card_frame(frame)
        else:
            login_frame = tk.Frame(frame, bg=COLORS['bg_blue'], relief='solid', bd=2)
        login_frame.pack(pady=30)

        # Username field
        if self.use_premium_theme:
            username_label = self.theme.create_body_label(
                login_frame,
                text="Username:",
                font=(self.theme.config.get("typography", {}).get("font_secondary", "Arial"), 12, 'bold')
            )
            username_label.grid(row=0, column=0, sticky='w', padx=20, pady=(30, 10))

            username_entry = self.theme.create_premium_entry(login_frame, width=25)
        else:
            tk.Label(login_frame, text="Username:",
                    bg=COLORS['bg_blue'], fg=COLORS['text_green'],
                    font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky='w', padx=20, pady=(30, 10))
            username_entry = tk.Entry(login_frame, font=('Arial', 14), width=25)

        username_entry.grid(row=0, column=1, padx=20, pady=(30, 10))

        # Password field
        if self.use_premium_theme:
            password_label = self.theme.create_body_label(
                login_frame,
                text="Password:",
                font=(self.theme.config.get("typography", {}).get("font_secondary", "Arial"), 12, 'bold')
            )
            password_label.grid(row=1, column=0, sticky='w', padx=20, pady=(0, 10))
            password_entry = self.theme.create_premium_entry(login_frame, width=25, show="*")
        else:
            tk.Label(login_frame, text="Password:",
                    bg=COLORS['bg_blue'], fg=COLORS['text_green'],
                    font=('Arial', 12, 'bold')).grid(row=1, column=0, sticky='w', padx=20, pady=(0, 10))
            password_entry = tk.Entry(login_frame, font=('Arial', 14), width=25, show="*")

        password_entry.grid(row=1, column=1, padx=20, pady=(0, 10))

        def attempt_login():
            username = username_entry.get().strip()
            password = password_entry.get()
            if not username:
                messagebox.showerror("Login Failed", "Please enter a username.", parent=self)
                return

            require_pw = bool(self._require_password_login())

            # DB-backed login (password-less by design for now; Setup Wizard manages users/clearance).
            try:
                user_row = self.db.fetchone("SELECT * FROM users WHERE username = ?", (username,))
            except Exception:
                user_row = None

            if user_row:
                user = dict(user_row)

                # Enforce/enroll a local password (stored under user_preferences.preferences_json).
                try:
                    prefs = get_user_preferences(username)
                except Exception:
                    prefs = None

                if require_pw and getattr(prefs, "table_available", False):
                    try:
                        record = prefs.get_preference("auth.password", default=None) if prefs else None
                    except Exception:
                        record = None

                    if record:
                        if not self._verify_password_record(record, password or ""):
                            messagebox.showerror("Login Failed", "Incorrect password.", parent=self)
                            return
                    else:
                        if not (password or "").strip():
                            messagebox.showerror(
                                "Login Failed",
                                "Password required.\n\n"
                                "This user has no password set yet. Enter a password to enroll it on this device.",
                                parent=self,
                            )
                            return
                        try:
                            prefs.set_preference("auth.password", self._hash_password_record(password))
                            # Reduce the chance of accidental disclosure.
                            try:
                                password_entry.delete(0, "end")
                            except Exception:
                                pass
                            messagebox.showinfo(
                                "Password Set",
                                "Password enrolled for this user.\n\n"
                                "You can reset it later from Settings Hub -> Tailoring.",
                                parent=self,
                            )
                        except Exception:
                            # If we cannot persist, do not block login (but warn).
                            messagebox.showwarning(
                                "Password Warning",
                                "Could not persist password enrollment. Continuing without password persistence.",
                                parent=self,
                            )

                elif require_pw and not getattr(prefs, "table_available", True):
                    # If the preferences table is missing, we cannot persist the password record.
                    # Do not block login; direct IT to run migrations.
                    try:
                        self.update_status("Password enforcement skipped (user_preferences table missing).")
                    except Exception:
                        pass

                clearance = int(user.get("clearance") or 1)
                # IT/Founder clearance is >=4 (setup wizard seeds IT and Achilles with clearance 4).
                self.user_mode = "it_founder" if clearance >= 4 else "client"
                self.current_user = user
                self.user_label.config(text=f"{username} ({'IT/Founder' if self.user_mode=='it_founder' else 'Client'})")
                self.update_top_bar_controls()

                # Load and apply user preferences
                self.load_user_preferences(username)
                self.check_first_run()

                # If launcher requested IT Portal mode, open it after login routing.
                if getattr(self, "_requested_it_portal", False) and self.user_mode == "it_founder":
                    try:
                        self.after(250, self.open_it_portal)
                    except Exception:
                        pass
                return

            # Not found: offer setup wizard (UI-only) or guest.
            if HAS_WIZARDS:
                ok = messagebox.askyesno(
                    "User Not Found",
                    "No user with that username exists yet.\n\nOpen Setup Wizard to create one?",
                    parent=self,
                )
                if ok:
                    try:
                        def _on_complete(config: Optional[Dict[str, Any]] = None):
                            try:
                                new_user = (config or {}).get("user") if isinstance(config, dict) else None
                                new_username = (new_user or {}).get("username") if isinstance(new_user, dict) else None
                                if new_username:
                                    try:
                                        username_entry.delete(0, "end")
                                        username_entry.insert(0, str(new_username))
                                    except Exception:
                                        pass
                            finally:
                                self.update_status("Setup complete. Please log in.")

                        if callable(launch_cognigrex_setup_wizard):
                            launch_cognigrex_setup_wizard(parent=self, on_complete=_on_complete)
                        elif callable(launch_setup_wizard_ui):
                            launch_setup_wizard_ui(parent=self, on_complete=_on_complete)
                        else:
                            raise RuntimeError("No setup wizard entrypoint is available")
                    except Exception as e:
                        messagebox.showerror("Setup Wizard", f"Failed to open Setup Wizard:\n{e}", parent=self)
                return

            messagebox.showerror(
                "Login Failed",
                "User not found. Run the Setup Wizard to create a user.",
                parent=self,
            )

        # Login button (premium gold style)
        if self.use_premium_theme:
            login_btn = self.theme.create_premium_button(
                login_frame,
                text="Login",
                command=attempt_login,
                style="gold"
            )
            login_btn.config(width=20, height=2)
        else:
            login_btn = tk.Button(login_frame, text="Login",
                                 command=attempt_login,
                                 bg=COLORS['button_green'], fg='white',
                                 font=('Arial', 14, 'bold'),
                                 width=20, height=2)
        login_btn.grid(row=2, column=0, columnspan=2, pady=(20, 30))

        # Bind Enter key
        username_entry.bind('<Return>', lambda e: attempt_login())
        try:
            password_entry.bind('<Return>', lambda e: attempt_login())
        except Exception:
            pass

        # Guest mode option (premium secondary style)
        # Optional: Trinity login portal (hidden by default; local login is canonical).
        if self._show_trinity_login_portal_button():
            if self.use_premium_theme:
                trinity_btn = self.theme.create_premium_button(
                    frame,
                    text="Open Trinity Login Portal",
                    command=self._open_trinity_login,
                    style="secondary",
                )
            else:
                trinity_btn = tk.Button(
                    frame,
                    text="Open Trinity Login Portal",
                    command=self._open_trinity_login,
                    bg=COLORS['bg_panel'],
                    fg=COLORS['text_cyan'],
                    font=('Arial', 10),
                )
            trinity_btn.pack(pady=(10, 0))

        if self._allow_guest_mode():
            if self.use_premium_theme:
                guest_btn = self.theme.create_premium_button(
                    frame,
                    text="Continue as Guest",
                    command=self.guest_login,
                    style="secondary"
                )
            else:
                guest_btn = tk.Button(frame, text="Continue as Guest",
                                      command=self.guest_login,
                                      bg=COLORS['bg_panel'], fg=COLORS['text_cyan'],
                                      font=('Arial', 10))
            guest_btn.pack(pady=10)

    def _open_trinity_login(self):
        """Launch Trinity's consolidated login portal and map the session back into N runtime."""
        try:
            launch_login = _load_symbol_from_file(
                "Z Axis/Z+3_Trinity/components/cognigrex_login.py",
                "launch_login",
            )
        except Exception as e:
            messagebox.showerror(
                "Trinity Login Unavailable",
                f"Failed to load Trinity login portal:\n{e}",
                parent=self,
            )
            return

        def _on_login(session: Optional[Dict[str, Any]] = None):
            try:
                sess = session or {}
                user = sess.get("user_data") if isinstance(sess, dict) else None
                if not isinstance(user, dict):
                    user = {}

                username = str(user.get("username") or sess.get("user") or "user")

                # Prefer DB-backed users when available (canonical source of clearance + profile fields).
                try:
                    row = self.db.fetchone("SELECT * FROM users WHERE username = ?", (username,))
                    if row:
                        user = dict(row)
                except Exception:
                    pass

                clearance = int(user.get("clearance") or 1) if isinstance(user, dict) else 1
                mode = str(sess.get("mode") or "")

                if mode == "it_portal":
                    self.user_mode = "it_founder"
                else:
                    # IT/Founder clearance is >=4 (setup wizard seeds IT and Achilles with clearance 4).
                    self.user_mode = "it_founder" if clearance >= 4 else "client"

                self.current_user = user if isinstance(user, dict) else {"username": username, "clearance": clearance}
                try:
                    display_name = self.current_user.get("username") or self.current_user.get("fullname") or username
                    self.user_label.config(
                        text=f"{display_name} ({'IT/Founder' if self.user_mode=='it_founder' else 'Client'})"
                    )
                except Exception:
                    pass

                try:
                    self.update_top_bar_controls()
                except Exception:
                    pass

                try:
                    self.load_user_preferences(username)
                except Exception:
                    pass

                # Continue into the canonical post-login flow.
                try:
                    self.check_first_run()
                except Exception:
                    self.show_main_menu()

                # If Trinity login requested IT Portal, open it after first-run routing.
                if mode == "it_portal":
                    try:
                        self.open_it_portal()
                    except Exception:
                        pass

                # If launcher requested IT Portal mode, open it after login routing.
                if getattr(self, "_requested_it_portal", False) and self.user_mode == "it_founder":
                    try:
                        self.open_it_portal()
                    except Exception:
                        pass
            except Exception as exc:
                messagebox.showerror("Trinity Login Error", f"Login mapping failed:\n{exc}", parent=self)

        try:
            # Do not call a nested mainloop; N is already running one.
            launch_login(parent=self, on_login=_on_login)
        except Exception as e:
            messagebox.showerror("Trinity Login", f"Failed to launch Trinity login:\n{e}", parent=self)

    def load_user_preferences(self, username: str):
        """Load and apply user preferences after login"""
        try:
            self.user_prefs = get_user_preferences(username)
            # Apply theme and fonts to UI
            self.user_prefs.apply_to_ui(self)
            self.status_label.config(text=f"Loaded preferences for {username}")
        except Exception as e:
            print(f"[WARNING] Could not load user preferences: {e}")
            self.user_prefs = None

    def guest_login(self):
        """Guest login (Client mode, no persistence)"""
        self.user_mode = "client"
        self.current_user = {
            'username': 'guest',
            'fullname': 'Guest User',
            'position': 'Visitor',
            'company': 'Guest',
            'clearance': 1
        }
        self.user_label.config(text="Guest (Client)")
        self.update_top_bar_controls()
        self.show_main_menu()

    def logout(self):
        """Logout current user and return to login screen"""
        confirm = messagebox.askyesno(
            "Confirm Logout",
            "Are you sure you want to logout?",
            parent=self
        )

        if confirm:
            # Close any open Z-floor windows
            for window in list(self.z_floor_windows.values()):
                if window and window.winfo_exists():
                    window.destroy()
            self.z_floor_windows.clear()

            # Reset user state
            self.current_user = None
            self.current_company = None
            self.current_project = None
            self.user_mode = None
            self.screens_history.clear()

            # Update UI
            self.user_label.config(text="Not logged in")

            # Show login screen
            self.show_login()

    def check_first_run(self):
        """Check if first-run setup needed"""
        # Run startup checks with error handling (UI-only; no terminal interaction)
        if HAS_WIZARDS and self.user_mode == "it_founder":
            try:
                import io
                from contextlib import redirect_stdout, redirect_stderr

                startup_wizard = StartupWizard()
                buf = io.StringIO()
                with redirect_stdout(buf), redirect_stderr(buf):
                    checks_passed = startup_wizard.run()
                report = (buf.getvalue() or "").strip()

                if not checks_passed:
                    def show_report():
                        win = tk.Toplevel(self)
                        win.title("LightSpeed Startup Check Report")
                        win.geometry("900x600")
                        win.configure(bg=COLORS["bg_dark"])
                        win.transient(self)

                        header = tk.Frame(win, bg=COLORS["bg_panel"])
                        header.pack(fill="x")
                        tk.Label(
                            header,
                            text="Startup Checks (Report)",
                            bg=COLORS["bg_panel"],
                            fg=COLORS["accent_cyan"],
                            font=("Arial", 14, "bold"),
                        ).pack(side="left", padx=12, pady=10)
                        tk.Button(
                            header,
                            text="Close",
                            command=win.destroy,
                            bg=COLORS["bg_blue"],
                            fg=COLORS["text_white"],
                            relief="flat",
                            padx=12,
                            pady=6,
                        ).pack(side="right", padx=12, pady=10)

                        text = scrolledtext.ScrolledText(
                            win,
                            bg="#001122",
                            fg=COLORS["text_green"],
                            font=("Consolas", 10),
                            wrap="word",
                        )
                        text.pack(fill="both", expand=True, padx=12, pady=12)
                        text.insert("1.0", report or "(No report output captured)")
                        text.configure(state="disabled")

                    if messagebox.askyesno(
                        "System Check",
                        "Some system checks failed.\n\nOpen report?",
                        parent=self,
                    ):
                        show_report()
            except Exception as e:
                print(f"[ERROR] StartupWizard failed: {e}")
                messagebox.showerror("Startup Error",
                                    f"Startup wizard encountered an error:\n{e}\n\n"
                                    "Platform will continue with default configuration.")

        # Check if user needs setup (with error handling)
        try:
            # Canonical: runtime must NOT silently mutate schema.
            # If schema is invalid, route IT/Founder to IT Portal to run explicit migration (Trinity setup flow).
            try:
                schema_ok = getattr(self.db, "schema_ok", None)
            except Exception:
                schema_ok = None

            if schema_ok is False:
                if self.user_mode == "it_founder":
                    messagebox.showwarning(
                        "Database Needs Migration",
                        "The database schema is not in a V1-ready state.\n\n"
                        "Open IT Portal -> Database -> Run DB Migration.",
                        parent=self,
                    )
                    try:
                        self.open_it_portal()
                    except Exception:
                        pass
                    return
                messagebox.showerror(
                    "Database Error",
                    "Database schema is not initialized. Please contact IT/Founder to run Setup/Migration in the IT Portal.",
                    parent=self,
                )
                return

            companies = self.db.fetchall("SELECT * FROM companies LIMIT 1")

            if not companies and self.user_mode == "it_founder":
                # First run - show setup
                self.show_setup()
            else:
                # Load company if exists
                if self.current_user.get('company'):
                    try:
                        company_row = self.db.fetchone("SELECT * FROM companies WHERE name = ?",
                                                      (self.current_user['company'],))
                        if company_row:
                            self.current_company = dict(company_row)
                    except Exception as e:
                        print(f"[WARNING] Failed to load company: {e}")

                self.show_main_menu()

        except Exception as e:
            print(f"[ERROR] Database check failed: {e}")
            # Continue anyway - show immersive shell (canonical home)
            self.show_main_menu()

    # ========================================================================
    # FIRST-RUN SETUP (UNIFIED WIZARD)
    # ========================================================================

    def show_setup(self):
        """Unified setup wizard (company + user)"""
        self.clear_screen()
        self.push_history("setup")
        self.update_breadcrumb("First-Run Setup")

        if HAS_WIZARDS and self.user_mode == "it_founder":
            # UI-only wizard (no terminal prompts)
            try:
                def on_complete(config: Optional[Dict[str, Any]] = None):
                    try:
                        if config and isinstance(config, dict):
                            company = (config.get("company") or {})
                            if isinstance(company, dict) and company.get("name"):
                                self.current_company = dict(company)
                    except Exception:
                        pass
                    self.show_main_menu()

                # Provide a minimal on-screen context while the wizard window is open
                frame = tk.Frame(self.main_container, bg=COLORS['bg_dark'])
                frame.pack(fill='both', expand=True)
                tk.Label(
                    frame,
                    text="Setup Wizard",
                    font=('Arial', 28, 'bold'),
                    bg=COLORS['bg_dark'],
                    fg=COLORS['accent_cyan']
                ).pack(pady=(60, 10))
                tk.Label(
                    frame,
                    text="The Setup Wizard window is open.\nComplete it to continue into the main portal.",
                    font=('Arial', 12),
                    bg=COLORS['bg_dark'],
                    fg=COLORS['text_green'],
                    justify='center'
                ).pack(pady=10)
                tk.Button(
                    frame,
                    text="Re-open Setup Wizard",
                    command=lambda: (launch_cognigrex_setup_wizard(parent=self, on_complete=on_complete) if callable(launch_cognigrex_setup_wizard) else launch_setup_wizard_ui(parent=self, on_complete=on_complete)),
                    bg=COLORS['button_green'],
                    fg='white',
                    font=('Arial', 12, 'bold'),
                    width=24,
                    height=2
                ).pack(pady=20)

                if callable(launch_cognigrex_setup_wizard):
                    launch_cognigrex_setup_wizard(parent=self, on_complete=on_complete)
                elif callable(launch_setup_wizard_ui):
                    launch_setup_wizard_ui(parent=self, on_complete=on_complete)
                else:
                    raise RuntimeError("No setup wizard entrypoint is available")
                return
            except Exception as e:
                print(f"[WARNING] SetupWizard UI unavailable: {e}")

        # Fallback simple setup
        self.show_simple_setup()

    def show_simple_setup(self):
        """Simple fallback setup (when wizards unavailable)"""
        frame = tk.Frame(self.main_container, bg=COLORS['bg_dark'])
        frame.pack(fill='both', expand=True)

        tk.Label(frame, text="Welcome to LightSpeed",
                font=('Arial', 32, 'bold'),
                bg=COLORS['bg_dark'],
                fg=COLORS['accent_cyan']).pack(pady=(40, 20))

        tk.Label(frame, text="First-Time Setup",
                font=('Arial', 16),
                bg=COLORS['bg_dark'],
                fg=COLORS['text_green']).pack(pady=10)

        # Setup form
        form_frame = tk.Frame(frame, bg=COLORS['bg_blue'], relief='solid', bd=2)
        form_frame.pack(pady=30, padx=100)

        # Company name
        tk.Label(form_frame, text="Company Name:",
                bg=COLORS['bg_blue'], fg=COLORS['text_green'],
                font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky='w', padx=20, pady=(20, 10))

        company_entry = tk.Entry(form_frame, font=('Arial', 14), width=30)
        company_entry.grid(row=0, column=1, padx=20, pady=(20, 10))
        company_entry.insert(0, self.current_user.get('company', 'My Company'))

        # Industry
        tk.Label(form_frame, text="Industry:",
                bg=COLORS['bg_blue'], fg=COLORS['text_green'],
                font=('Arial', 12, 'bold')).grid(row=1, column=0, sticky='w', padx=20, pady=10)

        industry_var = tk.StringVar(value="Technology")
        industry_combo = ttk.Combobox(form_frame, textvariable=industry_var, width=28,
                                      values=["Technology", "Manufacturing", "Services",
                                              "Healthcare", "Education", "Finance", "Other"])
        industry_combo.grid(row=1, column=1, padx=20, pady=10)

        def save_setup():
            company_name = company_entry.get().strip()
            industry = industry_var.get()

            if not company_name:
                messagebox.showerror("Error", "Company name required", parent=self)
                return

            # Save to database
            try:
                self.db.execute(
                    "INSERT INTO companies (name, industry, created_at) VALUES (?, ?, ?)",
                    (company_name, industry, datetime.now().isoformat())
                )
                self.current_company = {'name': company_name, 'industry': industry}
                messagebox.showinfo("Setup Complete", f"Welcome to {company_name}!", parent=self)
                self.show_main_menu()
            except Exception as e:
                print(f"[ERROR] Failed to save company: {e}")
                messagebox.showerror("Error", f"Failed to save setup:\n{e}", parent=self)

        tk.Button(form_frame, text="Complete Setup",
                 command=save_setup,
                 bg=COLORS['button_green'], fg='white',
                 font=('Arial', 12, 'bold'),
                 width=20, height=2).grid(row=2, column=0, columnspan=2, pady=(20, 30))

        # Skip option (guest is off-by-default; avoids accidental non-persistent sessions).
        if self._allow_guest_mode():
            tk.Button(frame, text="Skip Setup (Continue as Guest)",
                     command=self.guest_login,
                     bg=COLORS['bg_panel'], fg=COLORS['text_cyan'],
                     font=('Arial', 10)).pack(pady=10)

    # ========================================================================
    # MAIN MENU (RADIAL LAYOUT)
    # ========================================================================

    def show_main_menu(self):
        """Main menu with radial navigation (PDF Page 13)"""
        self.clear_screen()
        self.push_history("main_menu")
        self.update_breadcrumb("Home")

        # Use premium glass frame if theme engine available
        if self.use_premium_theme:
            frame = self.theme.create_glass_frame(self.main_container)
        else:
            frame = tk.Frame(self.main_container, bg=COLORS['bg_dark'])
        frame.pack(fill='both', expand=True)

        # Welcome message
        if self.current_user:
            welcome_text = self.current_user.get('fullname', 'User')
            mode_text = " (IT/Founder Mode)" if self.user_mode == "it_founder" else " (Client Mode)"
            if self.use_premium_theme:
                welcome_label = self.theme.create_title_label(frame, text=f"Welcome, {welcome_text}{mode_text}")
                welcome_label.pack(pady=(40, 20))
            else:
                tk.Label(frame, text=f"Welcome, {welcome_text}{mode_text}",
                        font=('Arial', 24, 'bold'),
                        bg=COLORS['bg_dark'],
                        fg=COLORS['accent_cyan']).pack(pady=(40, 20))

        # Company lobby (multi-company support)
        company_name = None
        try:
            company_name = (self.current_company or {}).get("name")
        except Exception:
            company_name = None
        if not company_name:
            company_name = (self.current_user or {}).get("company") or "No company selected"

        if self.use_premium_theme:
            company_row = self.theme.create_glass_frame(frame)
        else:
            company_row = tk.Frame(frame, bg=COLORS['bg_dark'])
        company_row.pack(pady=(0, 10))

        if self.use_premium_theme:
            company_label = self.theme.create_header_label(company_row, text=f"Lobby: {company_name}")
            company_label.pack(side="left", padx=(0, 12))
            switch_btn = self.theme.create_premium_button(company_row, text="Switch Company",
                                                         command=self.open_company_selector, style="secondary")
            switch_btn.pack(side="left")
        else:
            tk.Label(
                company_row,
                text=f"Lobby: {company_name}",
                font=('Arial', 12, 'bold'),
                bg=COLORS['bg_dark'],
                fg=COLORS['text_green'],
            ).pack(side="left", padx=(0, 12))
            tk.Button(
                company_row,
                text="Switch Company",
                command=self.open_company_selector,
                bg=COLORS['bg_panel'],
                fg=COLORS['text_cyan'],
                font=('Arial', 10, 'bold'),
                relief="flat",
                padx=10,
                pady=4,
            ).pack(side="left")

        # Center experience: N (external ground) with the Z-stack tower centered (Z0 aligned to ground).
        scene = tk.Frame(frame, bg=COLORS['bg_dark'])
        scene.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        canvas = tk.Canvas(scene, bg="#000000", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        hint = tk.Label(
            scene,
            text="N Lobby: fixed-camera world - Click tower slabs/doors to trigger floor functions - Use Bento panel for readable UI (Immersive optional)",
            bg=COLORS["bg_panel"],
            fg=COLORS["text_green"],
            font=("Arial", 10, "bold"),
            padx=10,
            pady=6,
        )
        hint.place(relx=0.01, rely=0.01, anchor="nw")

        # Bottom HUD (minimal; immersive UI overlay lives inside the 3D engine).
        if self.use_premium_theme:
            hud = self.theme.create_glass_frame(scene)
        else:
            hud = tk.Frame(scene, bg=COLORS["bg_panel"])
        hud.place(relx=0.5, rely=0.98, anchor="s")

        def hud_btn(label, cmd, color=None, style="gold"):
            if self.use_premium_theme:
                return self.theme.create_premium_button(hud, text=label, command=cmd, style=style)
            else:
                return tk.Button(
                    hud,
                    text=label,
                    command=cmd,
                    bg=(color or COLORS["bg_blue"]),
                    fg="white",
                    font=("Arial", 10, "bold"),
                    relief="flat",
                    padx=10,
                    pady=6,
                )

        try:
            # UI shells request dimming via `canvas._lightspeed_dim`; renderers apply it (stipple overlay).
            setattr(canvas, "_lightspeed_dim", 0.0)
        except Exception:
            pass

        # Bento overlay panel (primary, readable UI for the lobby).
        bento_panel = None
        # Keep this responsive so it reads like a real menu (not a distant HUD panel).
        def _compute_bento_place() -> Dict[str, Any]:
            try:
                w = int(scene.winfo_width() or 0)
            except Exception:
                w = 0
            # Prefer ~40% of the viewport, clamped.
            width_px = 520
            if w > 0:
                width_px = max(560, min(860, int(w * 0.42)))
            return {"relx": 0.985, "rely": 0.05, "anchor": "ne", "width": width_px, "relheight": 0.90}

        bento_place = _compute_bento_place()
        try:
            _force_trinity_ui_package()
            from ui.universal_bento_system import get_bento_system  # type: ignore

            bento = get_bento_system()
            try:
                bento.parent = self
            except Exception:
                pass
            try:
                setter = getattr(bento, "set_user_context", None)
                if callable(setter):
                    setter(self._current_user_id_for_bento())
            except Exception:
                pass
            try:
                self._wire_bento_widget_callbacks(bento)
            except Exception:
                pass

            # Prefer Romer palette when available.
            panel_bg = COLORS["bg_panel"]
            try:
                panel_bg = (getattr(bento, "palette", {}) or {}).get("accent_phthalo_green", panel_bg)
            except Exception:
                pass

            bento_panel = tk.Frame(scene, bg=panel_bg)
            bento_panel.place(**_compute_bento_place())
            try:
                setattr(canvas, "_lightspeed_dim", 0.35)
            except Exception:
                pass
            try:
                bento_panel.lift()
            except Exception:
                pass

            bento_frame = bento.create_2d_frame(bento_panel)
            bento_frame.pack(fill="both", expand=True)
            try:
                self._register_bento_frame_shortcuts(bento_frame)
            except Exception:
                pass

            # Live-resize the menu when the window changes (keeps it readable).
            def _on_scene_resize(_e=None):
                nonlocal bento_panel
                if bento_panel is None:
                    return
                try:
                    if bento_panel.winfo_ismapped():
                        bento_panel.place_configure(**_compute_bento_place())
                except Exception:
                    pass

            try:
                scene.bind("<Configure>", _on_scene_resize)
            except Exception:
                pass
        except Exception:
            bento_panel = None
            try:
                setattr(canvas, "_lightspeed_dim", 0.0)
            except Exception:
                pass

        def _toggle_bento_panel():
            nonlocal bento_panel
            if bento_panel is None:
                return
            try:
                if bento_panel.winfo_ismapped():
                    bento_panel.place_forget()
                    try:
                        setattr(canvas, "_lightspeed_dim", 0.0)
                    except Exception:
                        pass
                else:
                    bento_panel.place(**_compute_bento_place())
                    bento_panel.lift()
                    try:
                        setattr(canvas, "_lightspeed_dim", 0.35)
                    except Exception:
                        pass
                    # Focus search when the menu is explicitly opened.
                    try:
                        self.focus_bento_search()
                    except Exception:
                        pass
            except Exception:
                pass

        hud_btn("Ask Achilles", self.ask_achilles, COLORS["accent_magenta"], "gold").pack(side="left", padx=4, pady=6)
        # Condense project management into the Architect floor for IT/Founder mode.
        # Client mode keeps the simplified list view.
        proj_cmd = (lambda: self.open_z_floor_tab("Architect", "Project Manager")) if self.user_mode == "it_founder" else self.show_projects
        hud_btn("Projects", proj_cmd, COLORS["button_green"], "gold").pack(side="left", padx=4, pady=6)
        hud_btn("Documents", self.show_document_viewer, COLORS["button_green"], "gold").pack(side="left", padx=4, pady=6)
        hud_btn("Tree", self.show_project_tree, COLORS["button_green"], "gold").pack(side="left", padx=4, pady=6)
        hud_btn("Dashboard", self.show_user_dashboard, COLORS["button_green"], "gold").pack(side="left", padx=4, pady=6)
        if _trinity_ui_surface_available():
            hud_btn("Templates", self.show_template_manager, COLORS["accent_magenta"], "gold").pack(side="left", padx=4, pady=6)
        hud_btn("Bento Panel", _toggle_bento_panel, COLORS["accent_cyan"], "secondary").pack(side="left", padx=4, pady=6)
        hud_btn("Immersive (WASD)", self.open_immersive_wasd, COLORS["accent_cyan"], "gold").pack(side="left", padx=4, pady=6)
        hud_btn("Dome (FPS)", self.open_dome_interface, "#ff6b35", "gold").pack(side="left", padx=4, pady=6)

        cfg = self._load_unified_config()
        physics = (cfg.get("physics") or {}) if isinstance(cfg, dict) else {}

        # Attach a passive background host environment; main interactions happen in the Bento panel.
        try:
            attach = _load_symbol_from_file(
                "Z Axis/Z0_TheConstruct/ui/cognigrex_3d_environment.py",
                "attach_cognigrex_3d",
            )

            def _on_floor_select(floor):
                try:
                    floor_name = getattr(floor, "name", "") or ""
                    if not floor_name and hasattr(floor, "value"):
                        v = getattr(floor, "value", None)
                        if isinstance(v, (list, tuple)) and len(v) > 1:
                            floor_name = str(v[1])
                    if floor_name:
                        self.open_z_floor(str(floor_name))
                except Exception:
                    pass

            self._main_menu_engine = attach(self, canvas, on_floor_select=_on_floor_select)
        except Exception:
            # Fallback: immersive engine in passive preview mode (no input capture).
            try:
                attach = _load_symbol_from_file(
                    "Z Axis/Z0_TheConstruct/ui/immersive_3d_engine.py",
                    "attach_immersive_3d_environment",
                )
                self._main_menu_engine = attach(
                    self,
                    canvas,
                    on_action=None,
                    physics=physics,
                    capture_mouse=False,
                    enable_input=False,
                )
            except Exception:
                self._main_menu_engine = None

        self.update_status("Ready")

    # ========================================================================
    # COMPANY LOBBY (MULTI-COMPANY)
    # ========================================================================

    @staticmethod
    def _slugify_company(name: str) -> str:
        name = (name or "").strip().lower()
        name = re.sub(r"[^a-z0-9]+", "_", name)
        name = re.sub(r"_+", "_", name).strip("_")
        return name or "company"

    def _canonical_company_name(self, name: str) -> str:
        n = (name or "").strip()
        low = n.lower()
        if "emassc" in low and ("romer" in low or "rÃ¶mer" in low):
            return "Romer Industries / EMASSC"
        if "emassc" in low:
            return "EMASSC"
        if "rÃ¶mer" in low or "romer" in low:
            return "Romer Industries"
        return n or "Company"

    def open_company_selector(self):
        """Popup to switch active company lobby (affects project root + filtering surfaces)."""
        if not self.db:
            messagebox.showerror("Company", "Database not available.", parent=self)
            return
        try:
            rows = self.db.fetchall("SELECT id, name, industry FROM companies ORDER BY name")
        except Exception as e:
            messagebox.showerror("Company", f"Failed to load companies:\n{e}", parent=self)
            return

        win = tk.Toplevel(self)
        win.title("Select Company Lobby")
        win.geometry("520x420")

        if self.use_premium_theme:
            win.configure(bg=self.theme.palette.primary)
            try:
                self.theme.apply_to_root(win)
            except:
                win.configure(bg=COLORS["bg_dark"])
        else:
            win.configure(bg=COLORS["bg_dark"])

        if self.use_premium_theme:
            title_label = self.theme.create_title_label(win, text="Select Company")
            title_label.pack(pady=(16, 8))
            desc_label = self.theme.create_body_label(win, text="Switching lobby scopes projects and knowledge views to this company.")
            desc_label.pack(pady=(0, 10))
        else:
            tk.Label(
                win,
                text="Select Company",
                font=("Arial", 18, "bold"),
                bg=COLORS["bg_dark"],
                fg=COLORS["accent_cyan"],
            ).pack(pady=(16, 8))

            tk.Label(
                win,
                text="Switching lobby scopes projects and knowledge views to this company.",
                font=("Arial", 10),
                bg=COLORS["bg_dark"],
                fg=COLORS["text_green"],
            ).pack(pady=(0, 10))

        listbox = tk.Listbox(
            win,
            bg=COLORS["bg_panel"],
            fg=COLORS["text_white"],
            selectbackground=COLORS["accent_cyan"],
            activestyle="dotbox",
        )
        listbox.pack(fill="both", expand=True, padx=14, pady=10)

        companies: List[Dict[str, Any]] = []
        for r in rows or []:
            try:
                rid = r.get("id") if isinstance(r, dict) else r[0]
                nm = r.get("name") if isinstance(r, dict) else r[1]
                ind = r.get("industry") if isinstance(r, dict) else (r[2] if len(r) > 2 else "")
            except Exception:
                continue
            canonical = self._canonical_company_name(str(nm or ""))
            companies.append({"id": int(rid), "name": canonical, "industry": str(ind or "")})
            label = canonical + (f"  -  {ind}" if ind else "")
            listbox.insert(tk.END, label)

        cur_name = None
        try:
            cur_name = (self.current_company or {}).get("name")
        except Exception:
            cur_name = None
        if cur_name:
            cur_name = self._canonical_company_name(cur_name)
            for i, c in enumerate(companies):
                if c["name"] == cur_name:
                    listbox.selection_set(i)
                    listbox.see(i)
                    break

        def set_selected():
            sel = listbox.curselection()
            if not sel:
                return
            idx = int(sel[0])
            if idx < 0 or idx >= len(companies):
                return
            self.set_active_company(companies[idx])
            win.destroy()
            try:
                self.show_main_menu()
            except Exception:
                pass

        if self.use_premium_theme:
            btns = self.theme.create_glass_frame(win)
        else:
            btns = tk.Frame(win, bg=COLORS["bg_dark"])
        btns.pack(fill="x", padx=14, pady=(0, 14))

        if self.use_premium_theme:
            select_btn = self.theme.create_premium_button(btns, text="Select", command=set_selected, style="gold")
            select_btn.pack(side="left")
            cancel_btn = self.theme.create_premium_button(btns, text="Cancel", command=win.destroy, style="secondary")
            cancel_btn.pack(side="right")
        else:
            tk.Button(btns, text="Select", command=set_selected, bg=COLORS["button_green"], fg="white", padx=12, pady=6).pack(side="left")
            tk.Button(btns, text="Cancel", command=win.destroy, bg=COLORS["bg_panel"], fg=COLORS["text_cyan"], padx=12, pady=6).pack(side="right")
        listbox.bind("<Double-Button-1>", lambda _e: set_selected())

    def set_active_company(self, company: Dict[str, Any]):
        """Set active company lobby and re-root ProjectManager under a company folder."""
        try:
            self.current_company = {"id": int(company.get("id")), "name": company.get("name")}
            if company.get("industry"):
                self.current_company["industry"] = company.get("industry")
        except Exception:
            self.current_company = {"name": str(company.get("name") or "Company")}

        if self.project_manager is not None:
            try:
                base = Path(self.project_manager.base_path)
                # Ensure base is the projects root (not already a company directory).
                if base.name.lower() != "projects":
                    proj_root = None
                    for parent in [base, *base.parents]:
                        if parent.name.lower() == "projects":
                            proj_root = parent
                            break
                    base = proj_root or (base.parent / "projects")
                slug = self._slugify_company(self.current_company.get("name", "company"))
                company_root = base / slug
                company_root.mkdir(parents=True, exist_ok=True)
                self.project_manager.base_path = company_root
            except Exception:
                pass

    # ========================================================================
    # SETTINGS (Framework Integration)
    # ========================================================================

    def show_settings(self):
        """Open the operator settings function (IT/Founder only)."""
        if self.user_mode != "it_founder":
            messagebox.showwarning("Access Denied",
                                  "Settings are only available in IT/Founder mode")
            return

        if not _trinity_ui_surface_available():
            messagebox.showinfo(
                "Settings",
                "Trinity UI modules are not present in this checkout.\n"
                "Use the compact shell controls here, or restore the Trinity UI tree before reopening Settings Hub.",
                parent=self,
            )
            return

        # Prefer the condensed 3-tab hub (Trinity floor-owned UI).
        try:
            SmartSettingsHub = _load_symbol_from_file(
                "Z Axis/Z+3_Trinity/ui/smart_settings_hub.py",
                "SmartSettingsHub",
            )
            hub = SmartSettingsHub(parent=self)
            hub.open_dialog()
            return
        except Exception:
            pass

        try:
            if self.open_z_floor_tab("Trinity", "Settings Hub"):
                self.update_status("Trinity: Settings Hub")
                return
        except Exception:
            pass

        if HAS_FRAMEWORK and self.settings_manager:
            try:
                self.settings_manager.create_settings_window(self)
                return
            except Exception:
                pass

        messagebox.showinfo(
            "Settings",
            "Settings Hub is not available right now.\n"
            "Try Trinity Functions once the Trinity UI modules are ready.",
            parent=self,
        )

    def open_workspace_layout(self):
        """Open the workspace layout surface (Trinity spatial tooling, parented to N.py)."""
        if not _trinity_ui_surface_available():
            messagebox.showinfo(
                "Workspace Layout",
                "Trinity spatial tooling is not present in this checkout.",
                parent=self,
            )
            return
        try:
            SpatialUIManager = _load_symbol_from_file(
                "Z Axis/Z+3_Trinity/ui/spatial/spatial_ui_integration.py",
                "SpatialUIManager",
            )
            win = tk.Toplevel(self)
            SpatialUIManager(win)
        except Exception as e:
            messagebox.showerror("Workspace Layout", f"Failed to open workspace layout:\n{e}", parent=self)

    def show_template_manager(self):
        """Show Template Manager - Create professional outputs from templates"""
        if not self.current_user:
            messagebox.showwarning("Access Denied",
                                  "Please login to access Template Manager")
            return

        if not _trinity_ui_surface_available():
            messagebox.showinfo(
                "Template Manager",
                "Template Manager is not available in this checkout because the Trinity UI stack is missing.",
                parent=self,
            )
            return

        try:
            show_template_manager = _load_symbol_from_file(
                "Z Axis/Z+3_Trinity/ui/template_manager.py",
                "show_template_manager",
            )
            show_template_manager(self)
        except Exception as e:
            try:
                if self.open_z_floor_tab("Trinity", "Templates"):
                    self.update_status("Trinity: Templates")
                    return
            except Exception:
                pass
            messagebox.showerror("Template Manager Error",
                               f"Could not open Template Manager:\n{str(e)}")

    # ========================================================================
    # DOCUMENT VIEWER
    # ========================================================================

    def show_document_viewer(self):
        """Document viewer (PDF Pages 1, 6, 11)"""
        self.clear_screen()
        self.push_history("document_viewer")
        self.update_breadcrumb("Home > Documents")

        if HAS_MODULES:
            viewer = DocumentViewer(self.main_container, COLORS, self.db)
            viewer_frame = viewer.create_viewer()
            viewer_frame.pack(fill='both', expand=True)
        else:
            # Fallback viewer
            if self.use_premium_theme:
                frame = self.theme.create_glass_frame(self.main_container)
            else:
                frame = tk.Frame(self.main_container, bg=COLORS['bg_dark'])
            frame.pack(fill='both', expand=True, padx=20, pady=20)

            if self.use_premium_theme:
                toolbar = self.theme.create_glass_frame(frame)
            else:
                toolbar = tk.Frame(frame, bg=COLORS['bg_panel'])
            toolbar.pack(side='top', fill='x', pady=(0, 10))

            if self.use_premium_theme:
                title_label = self.theme.create_title_label(toolbar, text="Document Viewer")
                title_label.pack(side='left', padx=10)
            else:
                tk.Label(toolbar, text="Document Viewer",
                        bg=COLORS['bg_panel'], fg=COLORS['accent_cyan'],
                        font=('Arial', 14, 'bold')).pack(side='left', padx=10)

            text_widget = scrolledtext.ScrolledText(frame,
                                                    bg='#001122',
                                                    fg=COLORS['text_green'],
                                                    font=('Consolas', 10),
                                                    wrap='word')
            text_widget.pack(fill='both', expand=True)

            tk.Button(toolbar, text="Open File",
                     command=lambda: self.open_any_file(text_widget),
                     bg=COLORS['button_green'], fg='white',
                     font=('Arial', 10, 'bold')).pack(side='right', padx=5)

        self.update_status("Document Viewer ready")

    def open_any_file(self, text_widget):
        """Universal file opener"""
        filepath = filedialog.askopenfilename(title="Open File",
                                             filetypes=[("All Files", "*.*")])
        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            text_widget.delete('1.0', 'end')
            text_widget.insert('1.0', content)
            self.update_status(f"Loaded: {Path(filepath).name}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")

    # ========================================================================
    # PROJECT TREE
    # ========================================================================

    def show_project_tree(self):
        """Project tree viewer (PDF Page 14)"""
        self.clear_screen()
        self.push_history("project_tree")
        self.update_breadcrumb("Home > Project Tree")

        if HAS_MODULES:
            tree_viewer = ProjectTreeViewer(self.main_container, COLORS, self.db)
            tree_frame = tree_viewer.create_tree_view()
            tree_frame.pack(fill='both', expand=True)
        else:
            tk.Label(self.main_container,
                    text="Project Tree Viewer\n(Module not loaded)",
                    font=('Arial', 20),
                    bg=COLORS['bg_dark'],
                    fg=COLORS['text_green']).pack(expand=True)

        self.update_status("Project Tree ready")

    # ========================================================================
    # PROJECTS
    # ========================================================================

    def show_projects(self):
        """Projects list"""
        self.clear_screen()
        self.push_history("projects")
        self.update_breadcrumb("Home > Projects")

        frame = tk.Frame(self.main_container, bg=COLORS['bg_dark'])
        frame.pack(fill='both', expand=True, padx=20, pady=20)

        tk.Label(frame, text="Projects",
                font=('Arial', 24, 'bold'),
                bg=COLORS['bg_dark'],
                fg=COLORS['accent_cyan']).pack(pady=20)

        tk.Button(frame, text="+ New Project",
                 command=self.create_project,
                 bg=COLORS['button_green'], fg='white',
                 font=('Arial', 12, 'bold')).pack(pady=10)

        company_id = None
        try:
            if isinstance(self.current_company, dict):
                company_id = self.current_company.get("id")
        except Exception:
            company_id = None

        # Company-scoped view (shared projects use NULL company_id)
        if company_id is not None:
            try:
                projects = self.db.fetchall(
                    "SELECT * FROM projects WHERE (company_id=? OR company_id IS NULL) ORDER BY COALESCE(updated_at, created_at) DESC, id DESC",
                    (int(company_id),),
                )
            except TypeError:
                projects = self.db.fetchall(
                    f"SELECT * FROM projects WHERE (company_id={int(company_id)} OR company_id IS NULL) ORDER BY COALESCE(updated_at, created_at) DESC, id DESC"
                )
        else:
            projects = self.db.fetchall(
                "SELECT * FROM projects ORDER BY COALESCE(updated_at, created_at) DESC, id DESC"
            )

        if projects:
            for project in projects:
                p_frame = tk.Frame(frame, bg=COLORS['bg_panel'], relief='solid', bd=2)
                p_frame.pack(fill='x', pady=5)

                # Project info (left side)
                info_frame = tk.Frame(p_frame, bg=COLORS['bg_panel'])
                info_frame.pack(side='left', fill='both', expand=True)

                tk.Label(info_frame, text=project['name'],
                        bg=COLORS['bg_panel'], fg=COLORS['text_cyan'],
                        font=('Arial', 14, 'bold')).pack(side='left', padx=15, pady=10)

                tk.Label(info_frame, text=f"Status: {project.get('status', 'active')}",
                        bg=COLORS['bg_panel'], fg=COLORS['text_green'],
                        font=('Arial', 10)).pack(side='left', padx=15)

                # Avoid expensive filesystem scans in the list view (keeps UI responsive).
                # File details are available via the "Files" action.
                if HAS_PROJECT_MANAGER and self.project_manager:
                    tk.Label(
                        info_frame,
                        text="files: open Files",
                        bg=COLORS['bg_panel'],
                        fg=COLORS['warning_orange'],
                        font=('Arial', 10),
                    ).pack(side='left', padx=15)

                # Action buttons (right side)
                btn_frame = tk.Frame(p_frame, bg=COLORS['bg_panel'])
                btn_frame.pack(side='right', padx=10)

                if HAS_PROJECT_MANAGER and self.project_manager:
                    tk.Button(btn_frame, text="Files",
                             command=lambda p=project: self.manage_project_files(p),
                             bg=COLORS['warning_orange'], fg='white',
                             font=('Arial', 9, 'bold'), width=8).pack(side='left', padx=2, pady=5)

                    tk.Button(btn_frame, text="Archive",
                             command=lambda p=project: self.archive_project_to_oracle(p),
                             bg='#9B59B6', fg='white',
                             font=('Arial', 9, 'bold'), width=8).pack(side='left', padx=2, pady=5)

                tk.Button(btn_frame, text="Edit",
                         command=lambda p=project: self.edit_project(p),
                         bg=COLORS['accent_cyan'], fg='white',
                         font=('Arial', 9, 'bold'), width=8).pack(side='left', padx=2, pady=5)

                tk.Button(btn_frame, text="Delete",
                         command=lambda p=project: self.delete_project(p),
                         bg=COLORS['error_red'], fg='white',
                         font=('Arial', 9, 'bold'), width=8).pack(side='left', padx=2, pady=5)

        self.update_status(f"Projects: {len(projects) if projects else 0}")

    def create_project(self):
        """Enhanced project creation dialog with ProjectManager integration"""
        dialog = tk.Toplevel(self)
        dialog.title("New Project")
        dialog.geometry("550x650")
        dialog.configure(bg=COLORS['bg_blue'])

        # Form container
        form = tk.Frame(dialog, bg=COLORS['bg_blue'])
        form.pack(fill='both', expand=True, padx=30, pady=20)

        # Project Name
        tk.Label(form, text="Project Name:",
                bg=COLORS['bg_blue'], fg=COLORS['text_green'],
                font=('Arial', 12, 'bold')).pack(anchor='w', pady=(10, 5))

        name_entry = tk.Entry(form, font=('Arial', 14), width=40)
        name_entry.pack(fill='x', pady=5)

        # Project Type (for database)
        tk.Label(form, text="Project Category:",
                bg=COLORS['bg_blue'], fg=COLORS['text_green'],
                font=('Arial', 12, 'bold')).pack(anchor='w', pady=(15, 5))

        type_var = tk.StringVar(value="Development")
        type_combo = ttk.Combobox(form, textvariable=type_var, width=38,
                                  values=["Development", "Research", "Operations",
                                          "Marketing", "Design", "Infrastructure", "Other"])
        type_combo.pack(fill='x', pady=5)

        # Template Type (for ProjectManager)
        if HAS_PROJECT_MANAGER and self.project_manager:
            tk.Label(form, text="Project Template:",
                    bg=COLORS['bg_blue'], fg=COLORS['text_green'],
                    font=('Arial', 12, 'bold')).pack(anchor='w', pady=(15, 5))

            template_var = tk.StringVar(value="general")
            template_combo = ttk.Combobox(form, textvariable=template_var, width=38,
                                          values=["general", "python", "web", "data"])
            template_combo.pack(fill='x', pady=5)

            # Create venv checkbox
            venv_var = tk.BooleanVar(value=False)
            venv_check = tk.Checkbutton(form, text="Create Python virtual environment (.venv)",
                                       variable=venv_var,
                                       bg=COLORS['bg_blue'], fg=COLORS['text_green'],
                                       selectcolor=COLORS['bg_dark'],
                                       font=('Arial', 10))
            venv_check.pack(anchor='w', pady=10)

        # Project Status
        tk.Label(form, text="Status:",
                bg=COLORS['bg_blue'], fg=COLORS['text_green'],
                font=('Arial', 12, 'bold')).pack(anchor='w', pady=(15, 5))

        status_var = tk.StringVar(value="active")
        status_combo = ttk.Combobox(form, textvariable=status_var, width=38,
                                    values=["active", "planning", "on-hold", "completed", "archived"])
        status_combo.pack(fill='x', pady=5)

        # Description
        tk.Label(form, text="Description:",
                bg=COLORS['bg_blue'], fg=COLORS['text_green'],
                font=('Arial', 12, 'bold')).pack(anchor='w', pady=(15, 5))

        desc_text = tk.Text(form, height=4, width=40, font=('Arial', 11))
        desc_text.pack(fill='x', pady=5)

        def save():
            name = name_entry.get().strip()
            desc = desc_text.get('1.0', 'end-1c').strip()
            proj_type = type_var.get()
            status = status_var.get()
            company_id = None
            try:
                if isinstance(self.current_company, dict):
                    company_id = self.current_company.get("id")
            except Exception:
                company_id = None

            if not name:
                messagebox.showerror("Error", "Project name required", parent=dialog)
                return

            try:
                # Create filesystem project structure with ProjectManager
                if HAS_PROJECT_MANAGER and self.project_manager:
                    template = template_var.get()
                    result = self.project_manager.create_project(
                        name=name,
                        project_type=template,
                        template=template,
                        description=desc or None,
                        owner_id=self.current_user.get('id', 1),
                        company_id=int(company_id) if company_id is not None else None,
                        floor="Architect",
                        status=status,
                        persist_db=True,
                    )

                    if not result.get('success'):
                        messagebox.showerror("Error", f"Failed to create project structure:\n{result.get('error')}", parent=dialog)
                        return

                    # Create venv if requested
                    if venv_var.get() and template == "python":
                        project_path = Path(result['path'])
                        env = ProjectEnvironment(project_path)
                        venv_result = env.create_venv()

                        if not venv_result.get('success'):
                            messagebox.showwarning("Warning", f"Project created but venv failed:\n{venv_result.get('error')}", parent=dialog)

                # Save to database when ProjectManager isn't available. When it *is*
                # available, it is the single source of truth for project persistence
                # (prevents duplicate project rows).
                if not (HAS_PROJECT_MANAGER and self.project_manager):
                    # Save to database (prefer company-scoped projects)
                    now = datetime.now().isoformat()
                    try:
                        self.db.execute(
                            "INSERT INTO projects (name, description, type, status, owner_id, company_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (
                                name,
                                desc,
                                proj_type,
                                status,
                                self.current_user.get('id', 1),
                                int(company_id) if company_id is not None else None,
                                now,
                                now,
                            ),
                        )
                    except Exception:
                        # Back-compat for older schemas
                        self.db.execute(
                            "INSERT INTO projects (name, description, type, status, owner_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (name, desc, proj_type, status, self.current_user.get('id', 1), now, now),
                        )

                dialog.destroy()
                messagebox.showinfo("Success", f"Project '{name}' created with full structure!", parent=self)
                self.show_projects()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create project:\n{e}", parent=dialog)

        tk.Button(form, text="Create Project",
                 command=save,
                 bg=COLORS['button_green'], fg='white',
                 font=('Arial', 12, 'bold'), width=20, height=2).pack(pady=20)

    def edit_project(self, project):
        """Edit existing project"""
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Project: {project['name']}")
        dialog.geometry("500x450")
        dialog.configure(bg=COLORS['bg_blue'])

        # Form container
        form = tk.Frame(dialog, bg=COLORS['bg_blue'])
        form.pack(fill='both', expand=True, padx=30, pady=20)

        # Project Name
        tk.Label(form, text="Project Name:",
                bg=COLORS['bg_blue'], fg=COLORS['text_green'],
                font=('Arial', 12, 'bold')).pack(anchor='w', pady=(10, 5))

        name_entry = tk.Entry(form, font=('Arial', 14), width=40)
        name_entry.pack(fill='x', pady=5)
        name_entry.insert(0, project['name'])

        # Project Type
        tk.Label(form, text="Project Type:",
                bg=COLORS['bg_blue'], fg=COLORS['text_green'],
                font=('Arial', 12, 'bold')).pack(anchor='w', pady=(15, 5))

        type_var = tk.StringVar(value=project.get('type', 'Development'))
        type_combo = ttk.Combobox(form, textvariable=type_var, width=38,
                                  values=["Development", "Research", "Operations",
                                          "Marketing", "Design", "Infrastructure", "Other"])
        type_combo.pack(fill='x', pady=5)

        # Project Status
        tk.Label(form, text="Status:",
                bg=COLORS['bg_blue'], fg=COLORS['text_green'],
                font=('Arial', 12, 'bold')).pack(anchor='w', pady=(15, 5))

        status_var = tk.StringVar(value=project.get('status', 'active'))
        status_combo = ttk.Combobox(form, textvariable=status_var, width=38,
                                    values=["active", "planning", "on-hold", "completed", "archived"])
        status_combo.pack(fill='x', pady=5)

        # Description
        tk.Label(form, text="Description:",
                bg=COLORS['bg_blue'], fg=COLORS['text_green'],
                font=('Arial', 12, 'bold')).pack(anchor='w', pady=(15, 5))

        desc_text = tk.Text(form, height=4, width=40, font=('Arial', 11))
        desc_text.pack(fill='x', pady=5)
        desc_text.insert('1.0', project.get('description', ''))

        def save():
            name = name_entry.get().strip()
            desc = desc_text.get('1.0', 'end-1c').strip()
            proj_type = type_var.get()
            status = status_var.get()

            if not name:
                messagebox.showerror("Error", "Project name required", parent=dialog)
                return

            try:
                now = datetime.now().isoformat()
                company_id = None
                try:
                    company_id = (self.current_company or {}).get("id") if isinstance(self.current_company, dict) else None
                except Exception:
                    company_id = None

                has_company_col = False
                try:
                    cols = self.db.get_table_info("projects") or []
                    has_company_col = any((c.get("name") == "company_id") for c in cols if isinstance(c, dict))
                except Exception:
                    has_company_col = False

                if has_company_col and company_id is not None:
                    existing = self.db.fetchone("SELECT company_id FROM projects WHERE id=?", (project["id"],))
                    existing_company = (existing.get("company_id") if isinstance(existing, dict) else None) if existing else None
                    if existing_company is None:
                        messagebox.showwarning(
                            "Shared Project",
                            "This project is shared (no company).\n\nSwitch to the Global lobby to edit shared projects.",
                            parent=dialog,
                        )
                        return
                    if int(existing_company) != int(company_id):
                        messagebox.showerror(
                            "Company Mismatch",
                            "This project belongs to a different company context.",
                            parent=dialog,
                        )
                        return

                    self.db.execute(
                        "UPDATE projects SET name=?, description=?, type=?, status=?, updated_at=? WHERE id=? AND company_id=?",
                        (name, desc, proj_type, status, now, project["id"], int(company_id)),
                    )
                else:
                    self.db.execute(
                        "UPDATE projects SET name=?, description=?, type=?, status=?, updated_at=? WHERE id=?",
                        (name, desc, proj_type, status, now, project["id"]),
                    )

                dialog.destroy()
                messagebox.showinfo("Success", f"Project '{name}' updated!", parent=self)
                self.show_projects()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update project:\n{e}", parent=dialog)

        tk.Button(form, text="Save Changes",
                 command=save,
                 bg=COLORS['button_green'], fg='white',
                 font=('Arial', 12, 'bold'), width=20, height=2).pack(pady=20)

    def manage_project_files(self, project):
        """Project file management dialog with compact wall search/preview."""
        dialog = tk.Toplevel(self)
        dialog.title(f"Project Files: {project['name']}")
        dialog.geometry("1140x780")
        dialog.configure(bg=COLORS['bg_dark'])

        ui_state = {"project": project, "cancel_import": False, "records": {}, "selection": None}

        header_frame = tk.Frame(dialog, bg=COLORS['bg_panel'])
        header_frame.pack(fill='x', padx=10, pady=10)
        tk.Label(header_frame, text=f"Files in {project['name']}", bg=COLORS['bg_panel'], fg=COLORS['text_cyan'], font=('Arial', 16, 'bold')).pack(side='left', padx=10)
        btn_frame = tk.Frame(header_frame, bg=COLORS['bg_panel'])
        btn_frame.pack(side='right', padx=10)
        tk.Button(btn_frame, text="+ Add Files", command=lambda: self.add_files_to_project(project, dialog), bg=COLORS['button_green'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Refresh", command=lambda: render_files(), bg=COLORS['accent_cyan'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Close", command=dialog.destroy, bg=COLORS['error_red'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        filter_frame = tk.Frame(dialog, bg=COLORS['bg_dark'])
        filter_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(filter_frame, text="Category:", bg=COLORS['bg_dark'], fg=COLORS['text_green'], font=('Arial', 10)).pack(side='left', padx=(0, 5))
        category_var = tk.StringVar(value="all")
        search_var = tk.StringVar(value="")
        categories = ["all", "text", "code", "web", "data", "document", "image", "audio", "video", "archive", "other"]
        category_combo = ttk.Combobox(filter_frame, textvariable=category_var, values=categories, width=15, state='readonly')
        category_combo.pack(side='left', padx=5)
        tk.Label(filter_frame, text="Search:", bg=COLORS['bg_dark'], fg=COLORS['text_green'], font=('Arial', 10)).pack(side='left', padx=(14, 5))
        search_entry = tk.Entry(filter_frame, textvariable=search_var, width=40, font=('Arial', 10))
        search_entry.pack(side='left', padx=5, fill='x', expand=True)
        tk.Button(filter_frame, text="Clear", command=lambda: (search_var.set(""), render_files()), bg=COLORS['bg_panel'], fg=COLORS['text_green'], font=('Arial', 9, 'bold')).pack(side='left', padx=5)

        body_frame = tk.Frame(dialog, bg=COLORS['bg_dark'])
        body_frame.pack(fill='both', expand=True, padx=16, pady=(4, 10))
        body_frame.columnconfigure(0, weight=3)
        body_frame.columnconfigure(1, weight=2)
        body_frame.rowconfigure(0, weight=1)

        tree_container = tk.Frame(body_frame, bg=COLORS['bg_dark'])
        tree_container.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        preview_container = tk.Frame(body_frame, bg=COLORS['bg_dark'])
        preview_container.grid(row=0, column=1, sticky='nsew')

        tree_header = tk.Frame(tree_container, bg=COLORS['bg_panel'])
        tree_header.pack(fill='x', pady=(0, 8))
        tk.Label(tree_header, text="Component Set", bg=COLORS['bg_panel'], fg=COLORS['accent_cyan'], font=('Arial', 12, 'bold')).pack(side='left', padx=10, pady=6)
        tk.Label(tree_header, text="Double-click folders, right-click files", bg=COLORS['bg_panel'], fg=COLORS['text_green'], font=('Arial', 9)).pack(side='right', padx=10)

        tree_frame = tk.Frame(tree_container, bg=COLORS['bg_dark'])
        tree_frame.pack(fill='both', expand=True)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side='right', fill='y')
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.pack(side='bottom', fill='x')
        file_tree = ttk.Treeview(tree_frame, columns=('Category', 'Size', 'Modified'), show='tree headings', yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        file_tree.pack(fill='both', expand=True)
        vsb.config(command=file_tree.yview)
        hsb.config(command=file_tree.xview)
        file_tree.heading('#0', text='File Name')
        file_tree.heading('Category', text='Category')
        file_tree.heading('Size', text='Size')
        file_tree.heading('Modified', text='Modified')
        file_tree.column('#0', width=380)
        file_tree.column('Category', width=110)
        file_tree.column('Size', width=100)
        file_tree.column('Modified', width=180)
        empty_label = tk.Label(tree_frame, text="", bg=COLORS['bg_dark'], fg=COLORS['warning_orange'], font=('Arial', 12, 'bold'), wraplength=340, justify='center')
        empty_label.place(relx=0.5, rely=0.5, anchor='center')

        preview_header = tk.Frame(preview_container, bg=COLORS['bg_panel'])
        preview_header.pack(fill='x')
        preview_title_var = tk.StringVar(value=project['name'])
        tk.Label(preview_header, textvariable=preview_title_var, bg=COLORS['bg_panel'], fg=COLORS['accent_cyan'], font=('Arial', 13, 'bold')).pack(side='left', padx=10, pady=6)
        tk.Button(preview_header, text="Clear", command=lambda: clear_preview(), bg=COLORS['bg_panel'], fg=COLORS['text_green'], font=('Arial', 9, 'bold')).pack(side='right', padx=6, pady=4)
        tk.Button(preview_header, text="Open", command=lambda: open_selected(), bg=COLORS['button_green'], fg='white', font=('Arial', 9, 'bold')).pack(side='right', padx=4, pady=4)
        tk.Button(preview_header, text="Edit", command=lambda: edit_selected(), bg=COLORS['accent_cyan'], fg='white', font=('Arial', 9, 'bold')).pack(side='right', padx=4, pady=4)
        preview_chip_row = tk.Frame(preview_container, bg=COLORS['bg_dark'])
        preview_chip_row.pack(fill='x', pady=(8, 4))
        preview_mode_var = tk.StringVar(value="Mode: inspector")
        preview_renderer_var = tk.StringVar(value="Renderer: none")
        preview_fallback_var = tk.StringVar(value="Fallback: none")
        preview_actions_var = tk.StringVar(value="Actions: open, edit, replace")
        preview_meta_var = tk.StringVar(value="Meta: folder / file / target / floor")
        preview_body = scrolledtext.ScrolledText(preview_container, bg='#001122', fg=COLORS['text_green'], font=('Consolas', 10), wrap='word')
        preview_body.pack(fill='both', expand=True)
        preview_body.insert('1.0', "Select a file to inspect its metadata, preview text, and actions.")
        tk.Label(preview_container, textvariable=preview_meta_var, bg=COLORS['bg_dark'], fg=COLORS['text_green'], font=('Arial', 9), anchor='w').pack(fill='x', padx=4, pady=(0, 4))
        tk.Label(preview_container, textvariable=preview_actions_var, bg=COLORS['bg_dark'], fg=COLORS['warning_orange'], font=('Arial', 9), anchor='w').pack(fill='x', padx=4, pady=(0, 4))
        preview_actions = tk.Frame(preview_container, bg=COLORS['bg_panel'])
        preview_actions.pack(fill='x', pady=(8, 0))
        tk.Button(preview_actions, text="Import", command=lambda: self.add_files_to_project(project, dialog), bg=COLORS['button_green'], fg='white', font=('Arial', 9, 'bold')).pack(side='left', padx=4, pady=4)
        tk.Button(preview_actions, text="Replace", command=lambda: self.add_files_to_project(project, dialog), bg=COLORS['warning_orange'], fg='white', font=('Arial', 9, 'bold')).pack(side='left', padx=4, pady=4)
        tk.Button(preview_actions, text="Close Preview", command=lambda: clear_preview(), bg=COLORS['error_red'], fg='white', font=('Arial', 9, 'bold')).pack(side='right', padx=4, pady=4)

        status_bar = tk.Frame(dialog, bg=COLORS['bg_panel'])
        status_bar.pack(fill='x', side='bottom')
        status_var = tk.StringVar(value="Ready")
        tk.Label(status_bar, textvariable=status_var, bg=COLORS['bg_panel'], fg=COLORS['text_green'], font=('Arial', 9), anchor='w').pack(side='left', padx=10, pady=6)
        progress_bar = ttk.Progressbar(status_bar, mode='determinate', length=220)
        progress_bar.pack_forget()
        cancel_btn = tk.Button(status_bar, text="Cancel Import", command=lambda: ui_state.__setitem__("cancel_import", True), bg=COLORS['error_red'], fg='white', font=('Arial', 9, 'bold'))
        cancel_btn.pack(side='right', padx=6, pady=4)

        def set_status(text, busy=False, progress=None):
            status_var.set(text)
            try:
                if busy:
                    if not progress_bar.winfo_ismapped():
                        progress_bar.pack(side='right', padx=10, pady=6)
                    if progress is None:
                        progress_bar.config(mode='indeterminate')
                        progress_bar.start(10)
                    else:
                        progress_bar.stop()
                        progress_bar.config(mode='determinate', maximum=100)
                        progress_bar['value'] = max(0, min(100, progress))
                else:
                    progress_bar.stop()
                    progress_bar['value'] = 0
                    progress_bar.pack_forget()
            except Exception:
                pass
            try:
                dialog.update_idletasks()
            except Exception:
                pass

        def clear_preview(message="Select a file to inspect its metadata, preview text, and actions."):
            ui_state["selection"] = None
            preview_title_var.set(project['name'])
            preview_mode_var.set("Mode: inspector")
            preview_renderer_var.set("Renderer: none")
            preview_fallback_var.set("Fallback: none")
            preview_actions_var.set("Actions: open, edit, replace")
            preview_meta_var.set("Meta: folder / file / target / floor")
            preview_body.delete('1.0', 'end')
            preview_body.insert('1.0', message)
            set_status("Ready", busy=False)

        def file_path(file_record):
            for key in ("path", "filepath", "file_path", "source_path", "full_path"):
                value = file_record.get(key)
                if value:
                    return Path(str(value))
            return None

        def preview_descriptor(file_record):
            return {
                "title": str(file_record.get("name") or file_record.get("title") or file_record.get("label") or "Untitled"),
                "mode": str(file_record.get("mode") or file_record.get("category") or "file"),
                "renderer": str(file_record.get("renderer") or file_record.get("preview_mode") or "native"),
                "fallback": str(file_record.get("fallback") or file_record.get("preview_fallback") or "text"),
                "actions": file_record.get("actions") or ["open", "edit", "replace"],
                "metadata": [
                    f"{key}:{value}" for key, value in (
                        ("folder", file_record.get("folder") or file_record.get("component_set")),
                        ("floor", file_record.get("floor")),
                        ("target", file_record.get("target")),
                        ("label", file_record.get("label")),
                        ("category", file_record.get("category")),
                        ("status", file_record.get("status")),
                    ) if value
                ],
            }

        def load_preview(file_record):
            desc = preview_descriptor(file_record)
            ui_state["selection"] = file_record
            preview_title_var.set(desc["title"])
            preview_mode_var.set(f"Mode: {desc['mode']}")
            preview_renderer_var.set(f"Renderer: {desc['renderer']}")
            preview_fallback_var.set(f"Fallback: {desc['fallback']}")
            preview_actions_var.set("Actions: " + ", ".join(str(a) for a in desc["actions"]))
            preview_meta_var.set("Meta: " + (" | ".join(desc["metadata"]) if desc["metadata"] else "none"))
            set_status(f"Previewing {desc['title']}", busy=True)
            preview_body.delete('1.0', 'end')
            preview_body.insert('1.0', "Loading preview...")
            try:
                dialog.update_idletasks()
                dialog.update()
            except Exception:
                pass
            path = file_path(file_record)
            if path is None or not path.exists():
                preview_body.delete('1.0', 'end')
                preview_body.insert('1.0', "Preview target is missing.")
                set_status("Preview target missing", busy=False)
                return
            try:
                if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".pdf"}:
                    preview_body.delete('1.0', 'end')
                    preview_body.insert('1.0', f"Descriptor-only preview.\nPath: {path}")
                    set_status(f"{desc['title']} preview is descriptor-only", busy=False)
                    return
                with open(path, 'r', encoding='utf-8', errors='ignore') as handle:
                    content = handle.read(24_000)
                preview_body.delete('1.0', 'end')
                preview_body.insert('1.0', content)
                set_status(f"Loaded preview for {desc['title']}", busy=False)
            except Exception as exc:
                preview_body.delete('1.0', 'end')
                preview_body.insert('1.0', f"Preview unavailable: {exc}")
                set_status("Preview load failed", busy=False)

        def open_selected():
            record = ui_state.get("selection")
            if not record:
                return
            path = file_path(record)
            if path and path.exists():
                try:
                    os.startfile(str(path))
                    set_status(f"Opened {path.name}", busy=False)
                except Exception as exc:
                    messagebox.showerror("Open Failed", f"Could not open file:\n{exc}", parent=dialog)
            else:
                messagebox.showwarning("Missing Target", "The selected file target is missing or unavailable.", parent=dialog)

        def edit_selected():
            record = ui_state.get("selection")
            if not record:
                return
            path = file_path(record)
            title = preview_descriptor(record)["title"]
            editor = tk.Toplevel(dialog)
            editor.title(f"Artifact Editor: {title}")
            editor.geometry("980x720")
            editor.configure(bg=COLORS['bg_dark'])
            editor.transient(dialog)
            editor_header = tk.Frame(editor, bg=COLORS['bg_panel'])
            editor_header.pack(fill='x', padx=12, pady=12)
            tk.Label(editor_header, text=title, bg=COLORS['bg_panel'], fg=COLORS['accent_cyan'], font=('Arial', 15, 'bold')).pack(side='left', padx=8)
            tk.Button(editor_header, text="Close", command=editor.destroy, bg=COLORS['error_red'], fg='white', font=('Arial', 10, 'bold')).pack(side='right', padx=6)
            editor_chip_row = tk.Frame(editor, bg=COLORS['bg_dark'])
            editor_chip_row.pack(fill='x', padx=12, pady=(0, 8))
            desc = preview_descriptor(record)
            for chip in (f"Title: {desc['title']}", f"Mode: {desc['mode']}", f"Renderer: {desc['renderer']}", f"Fallback: {desc['fallback']}"):
                tk.Label(editor_chip_row, text=chip, bg=COLORS['bg_panel'], fg=COLORS['accent_cyan'], font=('Arial', 9, 'bold'), padx=8, pady=2, relief='groove', bd=1).pack(side='left', padx=4, pady=2)
            actions_frame = tk.Frame(editor, bg=COLORS['bg_dark'])
            actions_frame.pack(fill='x', padx=12, pady=(0, 8))
            tk.Button(actions_frame, text="Open", command=open_selected, bg=COLORS['button_green'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=4)
            tk.Button(actions_frame, text="Refresh Preview", command=lambda: load_preview(record), bg=COLORS['accent_cyan'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=4)
            tk.Button(actions_frame, text="Replace", command=lambda: self.add_files_to_project(project, dialog), bg=COLORS['warning_orange'], fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=4)
            editor_text = scrolledtext.ScrolledText(editor, bg='#001122', fg=COLORS['text_green'], font=('Consolas', 10), wrap='word')
            editor_text.pack(fill='both', expand=True, padx=12, pady=8)
            try:
                if path and path.exists():
                    with open(path, 'r', encoding='utf-8', errors='ignore') as handle:
                        editor_text.insert('1.0', handle.read(24_000))
                else:
                    editor_text.insert('1.0', preview_body.get('1.0', 'end-1c'))
            except Exception as exc:
                editor_text.insert('1.0', f"Could not load editor content:\n{exc}")

        def render_files(*_):
            for item in file_tree.get_children():
                file_tree.delete(item)
            ui_state["records"].clear()
            files = self.refresh_project_files(
                project,
                file_tree,
                category=category_var.get(),
                search_text=search_var.get(),
                empty_label=empty_label,
            )
            records = getattr(file_tree, "_project_file_records", {}) or {}
            ui_state["records"].update(records)
            if files:
                try:
                    first_leaf = next((iid for iid, record in records.items() if isinstance(record, dict) and record.get("kind") != "category"), None)
                except Exception:
                    first_leaf = None
                if first_leaf:
                    file_tree.selection_set(first_leaf)
                    file_tree.focus(first_leaf)
                    file_tree.see(first_leaf)
                    load_preview(records[first_leaf])
                else:
                    clear_preview()
            else:
                clear_preview()
            return files

        def on_select(_event=None):
            selection = file_tree.selection()
            if not selection:
                clear_preview()
                return
            record = ui_state["records"].get(selection[0])
            if not record or record.get("kind") == "category":
                clear_preview(f"{file_tree.item(selection[0], 'text')} contains grouped files.")
                return
            load_preview(record)

        file_tree.bind("<<TreeviewSelect>>", on_select)
        file_tree.bind("<Double-1>", lambda _e: open_selected())
        file_tree.bind("<Return>", lambda _e: open_selected())
        search_var.trace_add("write", lambda *_: render_files())
        category_var.trace_add("write", lambda *_: render_files())

        status_bar = tk.Frame(dialog, bg=COLORS['bg_panel'])
        status_bar.pack(fill='x', side='bottom')
        status_var = tk.StringVar(value="Ready")
        tk.Label(status_bar, textvariable=status_var, bg=COLORS['bg_panel'], fg=COLORS['text_green'], font=('Arial', 9), anchor='w').pack(side='left', padx=10, pady=6)
        progress_bar = ttk.Progressbar(status_bar, mode='determinate', length=220)
        progress_bar.pack(side='right', padx=10, pady=6)
        progress_bar.grid_remove()
        cancel_btn = tk.Button(status_bar, text="Cancel Import", command=lambda: ui_state.__setitem__("cancel_import", True), bg=COLORS['error_red'], fg='white', font=('Arial', 9, 'bold'))
        cancel_btn.pack(side='right', padx=6, pady=4)

        def set_status(text, busy=False, progress=None):
            status_var.set(text)
            try:
                if busy:
                    progress_bar.grid()
                    if progress is None:
                        progress_bar.config(mode='indeterminate')
                        progress_bar.start(10)
                    else:
                        progress_bar.stop()
                        progress_bar.config(mode='determinate', maximum=100)
                        progress_bar['value'] = max(0, min(100, progress))
                else:
                    progress_bar.stop()
                    progress_bar['value'] = 0
                    progress_bar.grid_remove()
            except Exception:
                pass
            try:
                dialog.update_idletasks()
            except Exception:
                pass

        dialog._project_files_ui = {
            "cancel_import": False,
            "cancel_btn": cancel_btn,
            "set_status": set_status,
            "render_files": render_files,
            "tree": file_tree,
            "records": ui_state["records"],
            "status_var": status_var,
            "progress_bar": progress_bar,
            "search_var": search_var,
            "category_var": category_var,
            "preview_body": preview_body,
        }

        render_files()

    def _project_file_blob(self, file_record):
        """Build a safe searchable blob for project-wall filtering."""
        if not isinstance(file_record, dict):
            return str(file_record or "").lower()
        parts = []
        for key in (
            "name", "title", "label", "target", "floor", "folder", "component_set", "parent_folder", "category", "description",
            "preview", "preview_text", "mode", "renderer", "fallback", "path",
            "filepath", "status", "tags", "metadata",
        ):
            value = file_record.get(key)
            if not value:
                continue
            if isinstance(value, (list, tuple, set)):
                parts.extend(str(item) for item in value if item)
            else:
                parts.append(str(value))
        return " ".join(parts).lower()

    def _project_file_collect(self, project, category=None, search_text=None):
        """Fetch project files with helper-backed search when available."""
        if not HAS_PROJECT_MANAGER or not self.project_manager:
            return []

        filter_cat = None if category in (None, "", "all") else str(category).lower()
        search_value = (search_text or "").strip().lower()

        helper = getattr(self.project_manager, "search_project_files", None)
        files = None
        if callable(helper) and search_value:
            for args in (
                (project['name'], search_value),
                (project['name'], search_value, filter_cat),
            ):
                try:
                    result = helper(*args)
                except TypeError:
                    continue
                except Exception:
                    result = None
                if result is not None:
                    try:
                        files = list(result)
                    except TypeError:
                        files = result if isinstance(result, list) else []
                    break

        if files is None:
            try:
                files = self.project_manager.get_project_files(project['name'], category=filter_cat)
            except TypeError:
                files = self.project_manager.get_project_files(project['name'], category=filter_cat)
            except Exception:
                files = []

        if filter_cat is not None:
            files = [file for file in files if str((file or {}).get('category', '')).lower() == filter_cat]

        if search_value:
            files = [file for file in files if search_value in self._project_file_blob(file)]

        return files

    def refresh_project_files(self, project, tree, category=None, search_text=None, empty_label=None):
        """Refresh file list in TreeView"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)

        try:
            tree._project_file_records = {}
        except Exception:
            pass

        if not HAS_PROJECT_MANAGER or not self.project_manager:
            if empty_label is not None:
                empty_label.config(text="ProjectManager not available.")
                empty_label.lift()
            else:
                tree.insert('', 'end', text="ProjectManager not available", values=('', '', ''))
            return []

        files = self._project_file_collect(project, category=category, search_text=search_text)

        if not files:
            if empty_label is not None:
                query = (search_text or "").strip()
                if query:
                    empty_label.config(text=f"No results for '{query}'. Clear the search or widen filters.")
                else:
                    empty_label.config(text="Blank component set. Add files to populate this wall.")
                empty_label.lift()
            else:
                tree.insert('', 'end', text="No files in project", values=('', '', ''))
            return []

        # Organize by category
        by_category = {}
        for file in files:
            cat = str((file or {}).get('category', 'other')).lower()
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(file)

        # Insert into tree
        record_map = {}
        for cat, cat_files in sorted(by_category.items()):
            # Category parent
            cat_item = tree.insert('', 'end', text=f"{cat.title()} ({len(cat_files)})",
                                  values=(cat, '', ''))
            record_map[cat_item] = {"kind": "category", "name": cat.title(), "category": cat}

            # Files in category
            for index, file in enumerate(cat_files):
                size_value = file.get('size') or file.get('bytes') or 0
                try:
                    size_kb = float(size_value) / 1024.0
                    size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb / 1024.0:.1f} MB"
                except Exception:
                    size_str = str(size_value) if size_value else ""

                modified = file.get('modified') or file.get('updated_at') or file.get('created_at')
                try:
                    modified = datetime.fromisoformat(str(modified)).strftime('%Y-%m-%d %H:%M') if modified else ""
                except Exception:
                    modified = str(modified) if modified else ""

                iid = f"file::{cat}:{index}:{len(record_map)}"
                tree.insert(cat_item, 'end', iid=iid, text=str(file.get('name') or file.get('title') or 'Untitled'),
                           values=(str(file.get('category', cat)), size_str, modified))
                record_map[iid] = file

        try:
            tree._project_file_records = record_map
        except Exception:
            pass
        return files

    def add_files_to_project(self, project, parent_dialog):
        """Add files to project via file picker with status/progress feedback."""
        filepaths = filedialog.askopenfilenames(
            title="Add Files to Project",
            parent=parent_dialog
        )

        if not filepaths:
            return

        if not HAS_PROJECT_MANAGER or not self.project_manager:
            messagebox.showerror("Error", "ProjectManager not available", parent=parent_dialog)
            return

        ui_state = getattr(parent_dialog, "_project_files_ui", {}) if parent_dialog else {}
        set_status = ui_state.get("set_status")
        render_files = ui_state.get("render_files")
        cancel_btn = ui_state.get("cancel_btn")

        if callable(set_status):
            try:
                ui_state["cancel_import"] = False
                if isinstance(cancel_btn, tk.Button):
                    cancel_btn.config(state='normal', text="Cancel Import")
                set_status(f"Importing {len(filepaths)} file(s)...", busy=True)
            except Exception:
                pass

        added = 0
        errors = []
        total = max(1, len(filepaths))

        for index, filepath in enumerate(filepaths, start=1):
            if ui_state.get("cancel_import"):
                errors.append("Import cancelled by user.")
                break
            try:
                result = self.project_manager.add_file_to_project(
                    project['name'],
                    Path(filepath),
                    destination_dir="data"
                )

                if result.get('success'):
                    added += 1
                else:
                    errors.append(f"{Path(filepath).name}: {result.get('error')}")

            except Exception as e:
                errors.append(f"{Path(filepath).name}: {str(e)}")

            if callable(set_status):
                try:
                    percent = (index / total) * 100.0
                    set_status(f"Importing {index}/{total}: {Path(filepath).name}", busy=True, progress=percent)
                except Exception:
                    pass
            try:
                parent_dialog.update_idletasks()
                parent_dialog.update()
            except Exception:
                pass

        if callable(set_status):
            try:
                set_status("Import complete" if added else "Import finished with warnings", busy=False)
                if isinstance(cancel_btn, tk.Button):
                    cancel_btn.config(state='normal', text="Cancel Import")
            except Exception:
                pass

        # Show results
        if added > 0:
            messagebox.showinfo("Success", f"Added {added} file(s) to project!", parent=parent_dialog)
            if callable(render_files):
                try:
                    render_files()
                except Exception:
                    pass
            else:
                for child in parent_dialog.winfo_children():
                    if isinstance(child, tk.Frame):
                        for widget in child.winfo_children():
                            if isinstance(widget, ttk.Treeview):
                                self.refresh_project_files(project, widget)
                                break

        if errors:
            error_msg = "\n".join(errors[:5])
            if len(errors) > 5:
                error_msg += f"\n... and {len(errors) - 5} more"
            messagebox.showwarning("Some Errors", f"Could not add {len(errors)} file(s):\n{error_msg}",
                                  parent=parent_dialog)

    def archive_project_to_oracle(self, project):
        """Archive project to Oracle IP Vault"""
        if not HAS_PROJECT_MANAGER or not self.project_manager:
            messagebox.showerror("Error", "ProjectManager not available", parent=self)
            return

        confirm = messagebox.askyesno(
            "Archive to Oracle",
            f"Archive project '{project['name']}' to Oracle IP Vault?\n\n"
            "This will create a permanent copy in the Oracle archives.",
            parent=self
        )

        if confirm:
            try:
                # Get company and workspace
                company = self.current_company.get('name', 'default_company') if self.current_company else 'default_company'
                workspace = project.get('name', 'default_workspace')

                # Archive to Oracle (floor-native; never create a legacy root `Data/` folder)
                try:
                    from core.config.paths import ORACLE_ROOT as _ORACLE_ROOT  # type: ignore
                    oracle_root = Path(_ORACLE_ROOT) / "Data"
                except Exception:
                    oracle_root = LIGHTSPEED_ROOT / "Z Axis" / "Z-2_Oracle" / "Data"
                result = self.project_manager.archive_to_oracle(
                    project['name'],
                    oracle_root,
                    company=company,
                    workspace=workspace
                )

                if result['success']:
                    msg = f"Successfully archived {result['archived_files']} file(s) to Oracle!\n\n"
                    msg += f"Archive location: {result['archive_path']}\n"
                    msg += f"Manifest: {result['manifest']}"

                    if result.get('errors'):
                        msg += f"\n\nWarnings: {len(result['errors'])} file(s) had issues"

                    messagebox.showinfo("Archive Complete", msg, parent=self)
                else:
                    messagebox.showerror("Archive Failed", f"Could not archive project:\n{result.get('error')}", parent=self)

            except Exception as e:
                messagebox.showerror("Error", f"Archive operation failed:\n{e}", parent=self)

    def delete_project(self, project):
        """Delete project with confirmation"""
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete project '{project['name']}'?\n\n"
            "This action cannot be undone.",
            parent=self
        )

        if confirm:
            try:
                company_id = None
                try:
                    company_id = (self.current_company or {}).get("id") if isinstance(self.current_company, dict) else None
                except Exception:
                    company_id = None

                has_company_col = False
                try:
                    cols = self.db.get_table_info("projects") or []
                    has_company_col = any((c.get("name") == "company_id") for c in cols if isinstance(c, dict))
                except Exception:
                    has_company_col = False

                if has_company_col and company_id is not None:
                    existing = self.db.fetchone("SELECT company_id FROM projects WHERE id=?", (project["id"],))
                    existing_company = (existing.get("company_id") if isinstance(existing, dict) else None) if existing else None
                    if existing_company is None:
                        messagebox.showwarning(
                            "Shared Project",
                            "This project is shared (no company).\n\nSwitch to the Global lobby to delete shared projects.",
                            parent=self,
                        )
                        return
                    if int(existing_company) != int(company_id):
                        messagebox.showerror(
                            "Company Mismatch",
                            "This project belongs to a different company context.",
                            parent=self,
                        )
                        return
                    self.db.execute("DELETE FROM projects WHERE id=? AND company_id=?", (project["id"], int(company_id)))
                else:
                    self.db.execute("DELETE FROM projects WHERE id=?", (project["id"],))
                messagebox.showinfo("Success", f"Project '{project['name']}' deleted.", parent=self)
                self.show_projects()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete project:\n{e}", parent=self)

    # ========================================================================
    # USER DASHBOARD
    # ========================================================================

    def show_user_dashboard(self):
        """User dashboard with widgets (PDF Page 12)"""
        self.clear_screen()
        self.push_history("user_dashboard")
        self.update_breadcrumb("Home > Dashboard")

        if self.use_premium_theme:
            frame = self.theme.create_glass_frame(self.main_container)
        else:
            frame = tk.Frame(self.main_container, bg=COLORS['bg_dark'])
        frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Header
        if self.use_premium_theme:
            title_label = self.theme.create_title_label(frame, text="Dashboard")
            title_label.pack(pady=(0, 20))
        else:
            tk.Label(frame, text="Dashboard",
                    font=('Arial', 24, 'bold'),
                    bg=COLORS['bg_dark'],
                    fg=COLORS['accent_cyan']).pack(pady=(0, 20))

        # 2x2 grid layout
        top_frame = tk.Frame(frame, bg=COLORS['bg_dark'])
        top_frame.pack(side='top', fill='both', expand=True, pady=(0, 10))

        bottom_frame = tk.Frame(frame, bg=COLORS['bg_dark'])
        bottom_frame.pack(side='top', fill='both', expand=True)

        # Use framework widgets if available
        if HAS_FRAMEWORK:
            company_id = None
            try:
                if isinstance(self.current_company, dict):
                    company_id = self.current_company.get("id")
            except Exception:
                company_id = None

            # Client mode: classic 2x2
            if self.user_mode != "it_founder":
                user_id = self._current_user_id_for_bento()
                okr_panel = self.create_panel(top_frame, "OKRs")
                okr_panel.pack(side='left', fill='both', expand=True, padx=(0, 5))
                OKRWidget(okr_panel, user_id=user_id).pack(fill='both', expand=True)

                task_panel = self.create_panel(top_frame, "Tasks")
                task_panel.pack(side='left', fill='both', expand=True, padx=(5, 0))
                TaskListWidget(task_panel, company_id=company_id).pack(fill='both', expand=True)

                cal_panel = self.create_panel(bottom_frame, "Calendar / Notes")
                cal_panel.pack(side='left', fill='both', expand=True, padx=(0, 5))
                nb = ttk.Notebook(cal_panel)
                nb.pack(fill="both", expand=True, padx=8, pady=8)
                cal_tab = ttk.Frame(nb)
                notes_tab = ttk.Frame(nb)
                nb.add(cal_tab, text="Calendar")
                nb.add(notes_tab, text="Notes")
                CalendarWidget(cal_tab).pack(fill='both', expand=True)
                NotesWidget(notes_tab, user_id=user_id).pack(fill="both", expand=True)

                links_panel = self.create_panel(bottom_frame, "Quick Actions")
                links_panel.pack(side='left', fill='both', expand=True, padx=(5, 0))
                links_widget = QuickLinksWidget(links_panel)
                links_widget.add_link("Open Document", self.show_document_viewer, ">")
                links_widget.add_link("New Project", self.create_project, "+")
                links_widget.add_link("Project Tree", self.show_project_tree, "T")
                links_widget.add_link("Z-Floors", self.show_z_floors_menu, "Z")
                links_widget.pack(fill='both', expand=True)
            else:
                # IT/Founder: bento-style 2x3 dashboard
                top_frame.pack_forget()
                bottom_frame.pack_forget()
                user_id = self._current_user_id_for_bento()

                grid = tk.Frame(frame, bg=COLORS['bg_dark'])
                grid.pack(fill="both", expand=True)
                for r in range(2):
                    grid.rowconfigure(r, weight=1, uniform="row")
                for c in range(3):
                    grid.columnconfigure(c, weight=1, uniform="col")

                okr_panel = self.create_panel(grid, "OKRs")
                okr_panel.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
                OKRWidget(okr_panel, user_id=user_id).pack(fill='both', expand=True)

                task_panel = self.create_panel(grid, "Tasks")
                task_panel.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
                TaskListWidget(task_panel, company_id=company_id).pack(fill='both', expand=True)

                jobs_panel = self.create_panel(grid, "Background Jobs")
                jobs_panel.grid(row=0, column=2, sticky="nsew", padx=6, pady=6)
                BackgroundJobsWidget(jobs_panel).pack(fill='both', expand=True)

                api_panel = self.create_panel(grid, "APIs")
                api_panel.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
                APITogglesWidget(api_panel).pack(fill='both', expand=True)

                dep_panel = self.create_panel(grid, "Dependencies / Notes")
                dep_panel.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)
                dep_nb = ttk.Notebook(dep_panel)
                dep_nb.pack(fill="both", expand=True, padx=8, pady=8)
                dep_tab = ttk.Frame(dep_nb)
                notes_tab = ttk.Frame(dep_nb)
                dep_nb.add(dep_tab, text="Dependencies")
                dep_nb.add(notes_tab, text="Notes")
                DependencyMapWidget(dep_tab).pack(fill='both', expand=True)
                NotesWidget(notes_tab, user_id=user_id).pack(fill="both", expand=True)

                links_panel = self.create_panel(grid, "Quick Actions")
                links_panel.grid(row=1, column=2, sticky="nsew", padx=6, pady=6)
                links_widget = QuickLinksWidget(links_panel)
                links_widget.add_link("IT Portal", self.open_it_portal, ">")
                links_widget.add_link("Oracle Ingestion", self.open_oracle_panel, ">")
                links_widget.add_link("Environment Host", self.open_3d_view, "3D")
                links_widget.add_link("Projects", self.show_projects, "+")
                links_widget.pack(fill='both', expand=True)
        else:
            # Fallback simple panels
            self.create_simple_dashboard_panels(top_frame, bottom_frame)

    def create_panel(self, parent, title):
        """Create dashboard panel"""
        if self.use_premium_theme:
            panel = self.theme.create_card_frame(parent)
            title_label = self.theme.create_header_label(panel, text=title)
            title_label.pack(pady=10)
        else:
            panel = tk.Frame(parent, bg=COLORS['bg_panel'], relief='solid', bd=2)
            tk.Label(panel, text=title,
                    bg=COLORS['bg_panel'], fg=COLORS['accent_cyan'],
                    font=('Arial', 13, 'bold')).pack(pady=10)

        return panel

    def create_simple_dashboard_panels(self, top_frame, bottom_frame):
        """Fallback dashboard panels"""
        panels = [
            (top_frame, "User Profile", "left"),
            (top_frame, "Recent Projects", "left"),
            (bottom_frame, "Recent Files", "left"),
            (bottom_frame, "Quick Actions", "left"),
        ]

        for parent, title, side in panels:
            panel = self.create_panel(parent, title)
            panel.pack(side=side, fill='both', expand=True,
                      padx=(0, 5) if side == "left" else (5, 0))

    # ========================================================================
    # IT PORTAL (IT/Founder Mode)
    # ========================================================================

    def open_it_portal(self):
        """
        Open IT Portal with integrated Z-floor tabs (IT/Founder only)
        Phase 3: Replaces Toplevel Z-floor windows with dedicated tabbed interface
        """
        if self.user_mode != "it_founder":
            messagebox.showwarning(
                "Access Denied",
                "IT Portal requires clearance level 4 (IT/Founder mode)",
            )
            return

        if not HAS_IT_PORTAL:
            try:
                self.show_floors_hub(select_floor="Trinity")
                self.update_status("Trinity functions opened (IT Portal unavailable)")
            except Exception:
                messagebox.showerror(
                    "IT Portal Unavailable",
                    "IT Portal module not loaded.\n"
                    "Check: Z Axis/Z+3_Trinity/ui/it_portal.py",
                )
            return

        # Reuse existing window if already open.
        try:
            existing = getattr(self, "_it_portal", None)
            if existing is not None:
                try:
                    if existing.winfo_exists():
                        existing.lift()
                        self.update_status("IT Portal focused")
                        return
                except Exception:
                    pass

            # IT Portal implies "automation enabled" for the current session.
            # If N started in retrieve-only mode, flip the gate and start Smith workers now.
            try:
                os.environ.pop("LIGHTSPEED_DISABLE_BACKGROUND_WORKERS", None)
            except Exception:
                pass
            try:
                import Smith  # type: ignore

                rt = getattr(Smith, "SMITH_RUNTIME", {}) or {}
                q = rt.get("queue")
                if q is not None:
                    fn = getattr(q, "ensure_oracle_ingestion_worker_started", None)
                    if callable(fn):
                        fn()
                    fn2 = getattr(q, "start_worker", None)
                    if callable(fn2):
                        fn2()
            except Exception:
                pass

            portal = ITPortal(
                parent=self,
                user=self.current_user,
                colors=COLORS,
                z_floors_available=Z_FLOORS_AVAILABLE,
            )
            self._it_portal = portal

            # Pass references to core services
            if hasattr(portal, "set_services"):
                portal.set_services(
                    db=self.db,
                    event_bus=self.event_bus,
                    storage=self.storage,
                )

            # Company + project context (multi-company lobby)
            try:
                company_id = (self.current_company or {}).get("id") if isinstance(self.current_company, dict) else None
                company_name = (self.current_company or {}).get("name") if isinstance(self.current_company, dict) else None
                if hasattr(portal, "set_company_context"):
                    portal.set_company_context(company_id=company_id, company_name=company_name)
                if hasattr(portal, "set_project_manager"):
                    portal.set_project_manager(self.project_manager)
            except Exception:
                pass

            self.update_status("IT Portal opened")
        except Exception as e:
            try:
                self.show_floors_hub(select_floor="Trinity")
                self.update_status("Trinity functions opened (IT Portal unavailable)")
                return
            except Exception:
                messagebox.showerror(
                    "Error Opening IT Portal",
                    f"Failed to launch IT Portal:\n{e}",
                )
                print(f"[ERROR] IT Portal launch failed: {e}")

    def open_it_portal_z_direct(
        self,
        *,
        channel: str = "Z+3",
        peer: str = "All",
        kind: str | None = None,
        tags: str | None = None,
        search: str | None = None,
    ) -> None:
        """
        Host action: open IT Portal and deep-link into the Z Direct operator view (scoped when possible).

        Used by data-defined Bento widgets via `config.host_action`.
        """
        try:
            if self.user_mode != "it_founder":
                messagebox.showwarning(
                    "Access Denied",
                    "Z Direct operator view requires clearance level 4 (IT/Founder mode).",
                    parent=self,
                )
                return
        except Exception:
            pass

        try:
            self.open_it_portal()
        except Exception:
            return

        try:
            portal = getattr(self, "_it_portal", None)
            if portal is None:
                return
            fn = getattr(portal, "_open_z_direct_view", None)
            if callable(fn):
                fn(channel=str(channel), peer=str(peer), kind=kind, tags=tags, search=search)
        except Exception:
            return

    def open_oracle_panel(self):
        """Open Oracle ingestion control center (UI-only)."""
        try:
            OracleUIPanel = _load_symbol_from_file("Z Axis/Z-2_Oracle/components/oracle_ui_panel.py", "OracleUIPanel")
            panel = OracleUIPanel(parent=self)
            panel.open_panel()
        except Exception as e:
            messagebox.showerror("Oracle", f"Failed to open Oracle panel:\n{e}", parent=self)

    def open_oracle_registry(self):
        """Open Oracle durable registry browser (Z Direct) with schemas visible (read-only)."""
        try:
            OracleUIPanel = _load_symbol_from_file("Z Axis/Z-2_Oracle/components/oracle_ui_panel.py", "OracleUIPanel")
            panel = OracleUIPanel(parent=self)
            # Best-effort: newer panels support selecting the registry tab on open.
            try:
                panel.open_panel(initial_tab="Durable Registry (Z Direct)")
                return
            except TypeError:
                panel.open_panel()
            try:
                select_tab = getattr(panel, "select_tab", None)
                if callable(select_tab):
                    select_tab("Durable Registry (Z Direct)")
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Oracle", f"Failed to open Oracle registry:\n{e}", parent=self)

    def launch_immersive_interface(self):
        """
        Launch Immersive Interface with 360-degree spherical navigation (IT/Founder only)
        V1.0.0 Feature: Complete 5-layer UI with HUD overlay and floor navigation
        """
        if self.user_mode != "it_founder":
            messagebox.showwarning("Access Denied",
                                  "Immersive UI requires clearance level 4 (IT/Founder mode)")
            return

        try:
            if not HAS_TRINITY_IMMERSIVE_UI:
                raise ImportError("Trinity immersive UI unavailable")

            # Create new window for immersive interface
            immersive_window = tk.Toplevel(self)
            immersive_window.title("LightSpeed V0.9.5 - Immersive Interface")
            immersive_window.geometry("1400x900")
            immersive_window.configure(bg='#000B1F')

            # Create immersive interface
            interface = ImmersiveInterface(
                immersive_window,
                db=self.db if hasattr(self, 'db') else None,
                event_bus=self.event_bus if hasattr(self, 'event_bus') else None,
                logger=None
            )
            interface.pack(fill='both', expand=True)

            self.update_status("Immersive Interface launched")

            # Log launch
            if hasattr(self, 'log'):
                self.log("Immersive Interface: Launched 360-degree spherical navigation")

        except ImportError as e:
            # Trinity owns the UI layer; when the dedicated immersive shell is unavailable,
            # fall back to opening Trinity's main hub rather than erroring out.
            try:
                self.open_z_floor("Trinity")
                self.update_status("Trinity Hub opened (fallback)")
                return
            except Exception:
                messagebox.showerror(
                    "Immersive UI Unavailable",
                    f"Immersive Interface module not found.\n"
                    f"Check: Z Axis/Z+3_Trinity/ui/immersive_interface.py\n\n"
                    f"Error: {e}",
                    parent=self,
                )
                print(f"[ERROR] Immersive Interface import failed: {e}")
        except Exception as e:
            try:
                self.open_z_floor("Trinity")
                self.update_status("Trinity Hub opened (fallback)")
                return
            except Exception:
                messagebox.showerror(
                    "Error Launching Immersive UI",
                    f"Failed to launch Immersive Interface:\n{e}",
                    parent=self,
                )
                print(f"[ERROR] Immersive Interface launch failed: {e}")
                import traceback
                traceback.print_exc()

    # ========================================================================
    # Z-FLOORS INTEGRATION (Inside-Out Architecture)
    # ========================================================================

    def _create_z_floors_dropdown(self):
        """
        Create Z-function dropdown menu button.
        Dropdown menu for invoking floor-owned functions in inside-out order.
        """
        floor_button = tk.Menubutton(
            self.controls,
            text="Z Functions",
            bg=COLORS['accent_cyan'],
            fg='#000000',
            font=('Arial', 10, 'bold'),
            relief='raised',
            borderwidth=2
        )
        floor_button.pack(side=tk.LEFT, padx=5)

        floor_menu = tk.Menu(floor_button, tearoff=0,
                            bg='#1e1e1e', fg='#ffffff',
                            activebackground=COLORS['accent_cyan'],
                            activeforeground='#000000',
                            font=('Arial', 10))
        floor_button.config(menu=floor_menu)

        # Expose for legacy callers (e.g., dashboard quick links)
        self.z_floors_button = floor_button
        self.z_floors_menu = floor_menu

        # Floor-owned functions in inside-out order (Core -> Surface)
        floors = [
            ("Merovingian: Core Services", "Merovingian", "#8B0000"),
            ("Smith: Job Router", "Smith", "#FF3333"),
            ("Oracle: Vault + Proofing", "Oracle", "#FFD700"),
            ("Morpheus: Knowledge", "Morpheus", "#9932CC"),
            ("TheConstruct: Simulation", "TheConstruct", "#00FF00"),
            ("Architect: Planning", "Architect", "#FF8C00"),
            ("Neo: AI Routing", "Neo", "#00FF88"),
            ("Trinity: Operator Surface", "Trinity", "#00D4FF"),
        ]

        for label, floor_name, color in floors:
            floor_menu.add_command(
                label=label if _is_floor_entry_available(floor_name) else f"{label} (Unavailable)",
                command=lambda f=floor_name: self.open_z_floor(f),
                foreground=color,
                state=("normal" if _is_floor_entry_available(floor_name) else "disabled"),
            )

        floor_menu.add_separator()
        floor_menu.add_command(
            label="Smith Task Scheduler",
            command=self.open_workflow_designer,
            foreground='#FF00FF'
        )
        floor_menu.add_command(
            label="Immersive World Host",
            command=self.open_3d_view,
            foreground=COLORS['accent_cyan']
        )

    def show_z_floors_menu(self):
        """Legacy method - redirects to the function selector (for compatibility)."""
        # This method is kept for compatibility with older widgets/menus that
        # expected a callable that shows a Z-floor selection menu.
        if not hasattr(self, "z_floors_menu") or not getattr(self, "z_floors_menu", None):
            try:
                self._create_z_floors_dropdown()
            except Exception:
                return

        menu = getattr(self, "z_floors_menu", None)
        button = getattr(self, "z_floors_button", None)
        if menu is None or button is None:
            return

        try:
            x = button.winfo_rootx()
            y = button.winfo_rooty() + button.winfo_height()
            menu.tk_popup(x, y)
        finally:
            try:
                menu.grab_release()
            except Exception:
                pass

    def open_workflow_designer(self):
        """Open workflow designer window"""
        # Canonical ownership: Smith (automation). Prefer the Smith Task Scheduler surface.
        try:
            if self.open_z_floor_tab("Smith", "Task Scheduler"):
                self.update_status("Opened Smith: Task Scheduler")
                return
        except Exception:
            pass

        # Fallback: legacy local workflow designer (kept for compatibility).
        try:
            from core.workflows.workflow_designer import WorkflowDesignerUI

            # Create workflow designer window
            designer_window = tk.Toplevel(self)
            designer_window.title("Workflow Designer")
            designer_window.geometry("1400x900")
            designer_window.configure(bg=COLORS['bg_dark'])

            # Create designer instance
            designer = WorkflowDesignerUI(
                parent=designer_window,
                base_path=LIGHTSPEED_ROOT
            )

            # The designer builds its own UI in __init__, just pack the frame
            designer.frame.pack(fill='both', expand=True)

            self.update_status("Workflow Designer opened")

        except ImportError as e:
            messagebox.showerror(
                "Workflow Designer Unavailable",
                f"Could not load workflow designer:\n{e}\n\n"
                f"Check: core/workflows/workflow_designer.py"
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to open workflow designer:\n{e}"
            )
            print(f"[ERROR] Workflow designer failed: {e}")

    def open_z_floor(self, floor_name: str):
        """
        Activate a Z-floor function surface.

        - Client mode: open the single-window functions hub by default.
        - IT/Founder mode: route through the operator hub when possible.
        """
        # Z+4_FirstRun is legacy-only; setup/login is consolidated into Trinity.
        if str(floor_name or "").strip().lower() in {"firstrun", "z+4_firstrun", "z+4"}:
            try:
                self.show_setup()
            except Exception:
                try:
                    self.open_z_floor("Trinity")
                except Exception:
                    pass
            return

        floor_name = str(floor_name or "").strip()
        if not _is_floor_entry_available(floor_name):
            missing_path = _resolve_floor_entry_path(floor_name)
            self.update_status(f"{floor_name} function unavailable in this checkout")
            messagebox.showinfo(
                "Function Unavailable",
                (
                    f"{floor_name} does not have a live floor entrypoint in this checkout.\n\n"
                    f"Expected file: {missing_path or 'Not configured'}\n\n"
                    "Use the active runtime-backed shell functions instead, or restore the missing floor package before reopening this surface."
                ),
                parent=self,
            )
            return

        # Keep Bento's active-floor filter in sync with navigation (used by both 2D and curved overlays).
        try:
            _force_trinity_ui_package()
            from ui.universal_bento_system import get_bento_system  # type: ignore

            b = get_bento_system()
            # Accept either human floor name ("Trinity") or canonical floor id ("Z+3_Trinity").
            name = str(floor_name or "").strip()
            floor_id = None
            if name.startswith("Z") and hasattr(b, "floor_configs") and name in getattr(b, "floor_configs", {}):
                floor_id = name
            else:
                mapping = {
                    "Merovingian": "Z-4_Merovingian",
                    "Smith": "Z-3_Smith",
                    "Oracle": "Z-2_Oracle",
                    "Morpheus": "Z-1_Morpheus",
                    "TheConstruct": "Z0_TheConstruct",
                    "Architect": "Z+1_Architect",
                    "Neo": "Z+2_Neo",
                    "Trinity": "Z+3_Trinity",
                }
                floor_id = mapping.get(name)
            if floor_id and hasattr(b, "set_active_floor"):
                b.set_active_floor(floor_id)
        except Exception:
            pass

        # IT/Founder mode prefers the operator hub, but falls back to the local
        # functions hub when Trinity-owned admin surfaces are unavailable.
        if self.user_mode == "it_founder":
            try:
                portal = getattr(self, "_it_portal", None)
                if HAS_IT_PORTAL and (portal is None or not portal.winfo_exists()):
                    self.open_it_portal()
                    portal = getattr(self, "_it_portal", None)
                if portal is not None and hasattr(portal, "select_z_floor"):
                    if portal.select_z_floor(floor_name):
                        self.update_status(f"Operator Hub: {floor_name}")
                        return
            except Exception:
                pass
            try:
                self.show_floors_hub(select_floor=floor_name)
                self.update_status(f"Functions: {floor_name}")
                return
            except Exception:
                pass
        else:
            # Client mode: keep the UX single-window by default.
            # Floors are hosted in the main container as a tabbed hub (no pop-out spam).
            try:
                self.show_floors_hub(select_floor=floor_name)
                self.update_status(f"Functions: {floor_name}")
                return
            except Exception:
                # Fall back to legacy pop-out behavior below.
                pass

        if floor_name in self.z_floor_windows and self.z_floor_windows[floor_name].winfo_exists():
            self.z_floor_windows[floor_name].lift()
            return

        # Respect service registry enablement when present
        if self.enabled_floor_names is not None and floor_name not in self.enabled_floor_names:
            messagebox.showwarning(
                "Floor Disabled",
                f"{floor_name} is disabled by the service registry.\n\n"
                f"Edit: Z Axis/Z0_TheConstruct/Config/service_registry.json",
            )
            return

        # Create new window
        window = tk.Toplevel(self)
        window.title(f"{floor_name} Floor")
        window.geometry("1000x700")

        if self.use_premium_theme:
            window.configure(bg=self.theme.palette.primary)
            # Apply theme to window
            try:
                self.theme.apply_to_root(window)
            except:
                window.configure(bg=COLORS["bg_dark"])
        else:
            window.configure(bg=COLORS["bg_dark"])

        self.z_floor_windows[floor_name] = window

        # Floor header
        if self.use_premium_theme:
            header = self.theme.create_glass_frame(window)
            header.configure(height=60)
        else:
            header = tk.Frame(window, bg=COLORS["bg_panel"], height=60)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        if self.use_premium_theme:
            title_label = self.theme.create_title_label(header, text=f"{floor_name}")
            title_label.pack(pady=15)
        else:
            tk.Label(
                header,
                text=f"{floor_name}",
                font=("Arial", 18, "bold"),
                bg=COLORS["bg_panel"],
                fg=COLORS["accent_cyan"],
            ).pack(pady=15)

        # Floor content
        if self.use_premium_theme:
            content = self.theme.create_glass_frame(window)
        else:
            content = tk.Frame(window, bg=COLORS["bg_dark"])
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Check if module available (lazy load)
        module = _get_z_floor_module(floor_name)
        if module:
            try:

                rendered = False
                last_type_error = None
                floor_ui = None

                # Support multiple legacy/new signatures across floors.
                # Preferred patterns:
                # - create_gui(parent, colors)
                # - create_gui(app, parent, colors)
                # - build(app, parent)
                # - build(app, parent, colors)
                for method_name, arg_sets in (
                    ("create_gui", [(content, COLORS), (self, content, COLORS), (self, content)]),
                    ("build", [(self, content, COLORS), (self, content), (content, COLORS), (content,)]),
                ):
                    if not hasattr(module, method_name):
                        continue
                    func = getattr(module, method_name)
                    for args in arg_sets:
                        try:
                            result = func(*args)
                            if isinstance(result, tk.Widget):
                                floor_ui = result
                                result.pack(fill="both", expand=True)
                            rendered = True
                            break
                        except TypeError as e:
                            last_type_error = e
                            continue
                    if rendered:
                        break

                if rendered:
                    # Store for deep-linking (command palette actions that open a specific sub-tab).
                    try:
                        if floor_ui is not None:
                            self._floor_ui_widgets[floor_name] = floor_ui
                    except Exception:
                        pass
                    tk.Label(
                        content,
                        text=f"{floor_name} module loaded",
                        font=("Arial", 12),
                        bg=COLORS["bg_dark"],
                        fg=COLORS["success_green"],
                    ).pack(side="bottom", pady=10)
                else:
                    self._render_floor_component_fallback(content, floor_name, last_type_error=last_type_error)
            except Exception as e:
                print(f"[ERROR] Failed to load {floor_name} GUI: {e}")
                messagebox.showerror(
                    f"{floor_name} Floor Error",
                    f"Failed to load {floor_name} interface:\n{e}\n\nCheck console for details.",
                )
                tk.Label(
                    content,
                    text=f"{floor_name} module error\nSee console for details",
                    font=("Arial", 16),
                    bg=COLORS["bg_dark"],
                    fg=COLORS["error_red"],
                ).pack(expand=True)
        else:
            tk.Label(
                content,
                text=f"{floor_name} function\n(Module not loaded)",
                font=("Arial", 16),
                bg=COLORS["bg_dark"],
                fg=COLORS["warning_orange"],
            ).pack(expand=True)

        self.update_status(f"Activated {floor_name}")

    def show_floors_hub(self, *, select_floor: str = ""):
        """
        Single-surface Functions Hub.

        Hosts one active floor surface at a time with a compact floor rail,
        runtime-backed readiness summaries, and lazy floor mounting to reduce
        UI sprawl and background load.
        """
        self.push_history("floors_hub")
        self.update_breadcrumb("Home > Functions")
        self.clear_screen()

        def _recover_agent_home_bridge():
            bridge = getattr(self, "agent_home_bridge", None)
            if bridge is not None:
                return bridge
            try:
                from lightspeed_runtime.agent_home_bridge import AgentHomeBridge
            except Exception:
                return None

            candidates: list[Path] = []
            if CANONICAL_RUNTIME_ROOT is not None:
                candidates.append(CANONICAL_RUNTIME_ROOT / "exports" / "agent_home")

            seen: set[str] = set()
            for export_dir in candidates:
                try:
                    resolved = export_dir.resolve()
                    key = str(resolved).lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    candidate = AgentHomeBridge(resolved)
                    candidate.agent_environment()
                    self.agent_home_bridge = candidate
                    return candidate
                except Exception:
                    continue
            return None

        def _safe_agent_home_summary() -> dict:
            bridge = _recover_agent_home_bridge()
            if bridge is None:
                return {}
            try:
                return bridge.summary()
            except Exception:
                return {}

        def _display_order(summary: dict) -> list[str]:
            alignment = summary.get("floor_alignment") or {}
            order = [str(item) for item in (alignment.get("display_order") or []) if item]
            if order:
                return order
            return [
                "Merovingian",
                "Smith",
                "Oracle",
                "Morpheus",
                "TheConstruct",
                "Architect",
                "Neo",
                "Trinity",
            ]

        def _floor_payload(summary: dict, floor_name: str) -> dict:
            alignment = summary.get("floor_alignment") or {}
            floors = alignment.get("floors") or {}
            payload = floors.get(floor_name)
            return payload if isinstance(payload, dict) else {}

        def _set_text(widget: tk.Text, payload: str) -> None:
            try:
                widget.configure(state="normal")
                widget.delete("1.0", "end")
                widget.insert("1.0", payload)
                widget.configure(state="disabled")
            except Exception:
                return

        def _first_active_stage(buildout: dict) -> dict:
            stages = buildout.get("stages") or []
            return next(
                (
                    stage
                    for stage in stages
                    if str(stage.get("state") or "").startswith(("ready", "active"))
                ),
                stages[0] if stages else {},
            )

        def _short_path(path_value: object) -> str:
            if not path_value:
                return "not exported"
            try:
                path = Path(str(path_value))
                parts = path.parts
                if len(parts) > 4:
                    return str(Path(*parts[-4:]))
                return str(path)
            except Exception:
                return str(path_value)

        def _safe_open_path(path_value: object, label: str) -> None:
            if not path_value:
                self.update_status(f"{label} not exported yet")
                return
            path = Path(str(path_value))
            if not path.exists():
                self.update_status(f"{label} missing: {path}")
                return
            try:
                os.startfile(str(path))
                self.update_status(f"Opened {label}")
            except Exception as exc:
                messagebox.showwarning(label, f"Could not open:\n{path}\n\n{exc}", parent=self)

        def _queue_path(summary: dict) -> Optional[Path]:
            smith_queue = LIGHTSPEED_ROOT / "Z Axis" / "Z-3_Smith" / "data" / "staging" / "buildout_phase_queue.json"
            if smith_queue.exists():
                return smith_queue
            queue = summary.get("consolidation_queue") or {}
            for key in ("path", "queue_path", "source_path", "artifact_path"):
                value = queue.get(key)
                if value and Path(str(value)).exists():
                    return Path(str(value))
            if CANONICAL_RUNTIME_ROOT is None:
                return None
            fallback = CANONICAL_RUNTIME_ROOT / "exports" / "agent_home" / "consolidation_queue.json"
            return fallback if fallback.exists() else None

        def _agentic_launch_queue_path(summary: dict) -> Optional[Path]:
            queue = summary.get("agentic_launch_queue") or {}
            mirrors = queue.get("mirrors") or {}
            for key in ("smith_staging", "desktop_config", "runtime_export", "neo_temp_shells"):
                value = mirrors.get(key)
                if value and Path(str(value)).exists():
                    return Path(str(value))
            fallbacks = [
                LIGHTSPEED_ROOT / "Z Axis" / "Z-3_Smith" / "data" / "staging" / "agentic_launch_queue.json",
                LIGHTSPEED_ROOT / "config" / "agentic_launch_queue.json",
            ]
            if CANONICAL_RUNTIME_ROOT is not None:
                fallbacks.append(
                    CANONICAL_RUNTIME_ROOT / "exports" / "agent_home" / "agentic_launch_queue.json"
                )
            return next((path for path in fallbacks if path.exists()), None)

        def _neo_receipt_path(summary: dict) -> Optional[Path]:
            candidates: list[Path] = []

            def collect(value: object) -> None:
                if isinstance(value, dict):
                    if value.get("receipt_id"):
                        for path_key in ("receipt_path", "path", "source_path", "artifact_path"):
                            item = value.get(path_key)
                            if item:
                                try:
                                    candidates.append(Path(str(item)))
                                except Exception:
                                    pass
                    for key, item in value.items():
                        key_text = str(key).lower()
                        if "receipt" in key_text and item:
                            try:
                                candidates.append(Path(str(item)))
                            except Exception:
                                pass
                        else:
                            collect(item)
                elif isinstance(value, list):
                    for item in value:
                        collect(item)

            collect(summary.get("neo") or {})
            collect(summary.get("neo_local_runtime") or {})
            collect(summary.get("neo_realisation_runtime") or {})
            collect(summary.get("smart_floor_artifacts") or {})
            output_dir = LIGHTSPEED_ROOT / "Z Axis" / "Z+2_Neo" / "data" / "temp_shells" / "outputs"
            if output_dir.exists():
                candidates.extend(
                    sorted(
                        output_dir.glob("*receipt*.json"),
                        key=lambda path: path.stat().st_mtime,
                        reverse=True,
                    )
                )
            for candidate in candidates:
                if candidate.exists():
                    return candidate
            return None

        def _format_overview(summary: dict) -> str:
            if not summary:
                return "Agent-home export unavailable. Functions Hub is operating in shell-only mode."
            build = summary.get("backend_frontend_build") or {}
            realization = summary.get("floor_environment_realization") or {}
            wakeup = summary.get("local_agent_wakeup") or {}
            buildout = wakeup.get("buildout_phase") or {}
            active_stage = _first_active_stage(buildout)
            queue = summary.get("consolidation_queue") or {}
            agent_queue = summary.get("agentic_launch_queue") or {}
            alignment = summary.get("floor_alignment") or {}
            host = summary.get("host_runtime_policy") or {}
            closure = host.get("resource_closure") or {}
            runtime_closure = closure.get("runtime_shares") or {}
            return "\n".join(
                [
                    "HOME: Functions Hub / Ask Achilles is the readable operator surface.",
                    f"FRONTEND: one N.py shell | backend floors open only by explicit drill-in.",
                    f"BACKEND: {build.get('backend_enabled_count', 0)}/{build.get('floor_count', 0)} enabled | floors={alignment.get('total_floors', 0)} | models={realization.get('floor_models_confirmed', 0)} confirmed.",
                    f"LOCAL AI: Ollama floors {wakeup.get('ollama_enabled_floor_count', 0)}/{wakeup.get('floor_count', 0)} | chat-ready {wakeup.get('chat_ready_floor_count', 0)}/{wakeup.get('floor_count', 0)} | queue={queue.get('total_items', 0)}.",
                    (
                        "AGENT QUEUE: "
                        f"{agent_queue.get('ready_count', 0)}/{agent_queue.get('task_count', 0)} ready | "
                        f"manual-heavy={agent_queue.get('manual_heavy_count', 0)} | "
                        f"state={agent_queue.get('state', 'not_exported')}."
                    ),
                    (
                        "CLOSURE: "
                        f"runtime={closure.get('runtime_total', 'n/a')} | "
                        f"LS={runtime_closure.get('lightspeed_resident', 'n/a')} "
                        f"DS idle={runtime_closure.get('de_sporte_idle_persistence', 'n/a')} "
                        f"DS active={runtime_closure.get('de_sporte_active_interaction', 'n/a')}."
                    ),
                    f"BUILDOUT: {buildout.get('state', 'not exported')} | active stage={active_stage.get('label') or active_stage.get('stage_id', 'not exported')}.",
                    f"GATE: {build.get('launch_gate', 'unknown')} | external writes blocked | heavy floors manual.",
                ]
            )

        def _format_operator_home(summary: dict, floor_name: str) -> str:
            build = summary.get("backend_frontend_build") or {}
            wakeup = summary.get("local_agent_wakeup") or {}
            buildout = wakeup.get("buildout_phase") or {}
            active_stage = _first_active_stage(buildout)
            agent_queue = summary.get("agentic_launch_queue") or {}
            queue_by_floor = agent_queue.get("by_floor") or {}
            wake_payload = ((summary.get("local_agent_wakeup") or {}).get("by_floor") or {}).get(floor_name) or {}
            wake_connection = wake_payload.get("ollama_connection") or {}
            chat_payload = wake_payload.get("ai_chat_enablement") or {}
            queue_path = _queue_path(summary)
            agent_queue_path = _agentic_launch_queue_path(summary)
            receipt_path = _neo_receipt_path(summary)
            return "\n".join(
                [
                    "OPERATOR HOME",
                    "",
                    f"Active floor: {floor_name}",
                    f"Floor chat: {chat_payload.get('state', 'not exported')}",
                    f"Ollama: {'enabled' if wake_connection.get('enabled') else 'not enabled'} | model={wake_connection.get('model', 'not exported')} | endpoint={wake_connection.get('endpoint', 'localhost:11434')}",
                    f"Buildout: {buildout.get('state', 'not exported')}",
                    f"Stage: {active_stage.get('label') or active_stage.get('stage_id', 'not exported')} | {active_stage.get('state', 'not exported')}",
                    f"Next safe action: {wake_payload.get('next_safe_action') or buildout.get('next_action') or 'not exported'}",
                    "",
                    f"Backend workspace: gated by {build.get('launch_gate', 'unknown')}",
                    f"Agent queue: {queue_by_floor.get(floor_name, 0)} floor tasks | {_short_path(agent_queue_path)}",
                    f"Wake packet: {_short_path(wake_payload.get('packet_path'))}",
                    f"Buildout handoff: {_short_path(LIGHTSPEED_ROOT / 'config' / 'buildout_phase_contract.json')}",
                    f"Neo receipt: {_short_path(receipt_path)}",
                    f"Smith queue: {_short_path(queue_path)}",
                ]
            )

        def _format_floor_detail(summary: dict, floor_name: str) -> str:
            payload = _floor_payload(summary, floor_name)
            if not payload:
                return f"{floor_name}\n\nNo smart-floor alignment export is available for this floor yet."
            build_payload = ((summary.get("backend_frontend_build") or {}).get("by_floor") or {}).get(floor_name) or {}
            backend = build_payload.get("backend") or {}
            frontend = build_payload.get("frontend") or {}
            build_state = build_payload.get("build") or {}
            realization_payload = ((summary.get("floor_environment_realization") or {}).get("by_floor") or {}).get(floor_name) or {}
            tool_realization = realization_payload.get("tool_realization") or {}
            post_population = realization_payload.get("post_population") or {}
            model_realization = realization_payload.get("model") or {}
            wake_payload = ((summary.get("local_agent_wakeup") or {}).get("by_floor") or {}).get(floor_name) or {}
            wake_connection = wake_payload.get("ollama_connection") or {}
            wake_draw = wake_payload.get("assimilation_draw") or {}
            chat_payload = wake_payload.get("ai_chat_enablement") or {}
            learning_sequence = (wake_payload.get("training_context") or {}).get("learning_sequence") or []
            priority_paths = wake_draw.get("priority_paths") or []
            agent_queue = summary.get("agentic_launch_queue") or {}
            queue_by_floor = agent_queue.get("by_floor") or {}
            return "\n".join(
                [
                    (
                        f"BACKEND FLOOR: {floor_name} | "
                        f"state={payload.get('primary_status', 'unknown')} | "
                        f"mode={payload.get('population_mode', 'unknown')}"
                    ),
                    (
                        f"LOCAL MODEL: {wake_connection.get('model', payload.get('model', 'unknown'))} | "
                        f"enabled={bool(wake_connection.get('enabled'))} | "
                        f"persona={payload.get('persona', 'unknown')}"
                    ),
                    (
                        f"Agent: {payload.get('assigned_agent_id', 'unknown')} | "
                        f"support={payload.get('de_sporte_support_resident_id', 'none')} | "
                        f"host={payload.get('resident_host_application', 'unknown')}"
                    ),
                    (
                        f"Backend/frontend: backend={'on' if backend.get('enabled') else 'off'} | "
                        f"frontend={'on' if frontend.get('enabled') else 'off'} | "
                        f"build_state={build_state.get('state', 'not_exported')}"
                    ),
                    f"Backend role: {backend.get('role', 'not exported')}",
                    f"Frontend surface: {frontend.get('surface', 'N.py shell')}",
                    (
                        f"Realization: {realization_payload.get('environment_label', 'not exported')} | "
                        f"outside_in={realization_payload.get('outside_in_order', 'n/a')} | "
                        f"model_confirmed={bool(model_realization.get('confirmed_installed'))}"
                    ),
                    "Backend tools: " + (", ".join(str(item) for item in (tool_realization.get("tool_transform") or [])[:2]) or "not exported"),
                    (
                        f"AI chat: {chat_payload.get('state', 'not exported')} | "
                        f"modes={', '.join(str(item) for item in (chat_payload.get('chat_modes') or [])[:4]) or 'none'}"
                    ),
                    "Learning: " + (" -> ".join(str(item) for item in learning_sequence[:3]) or "not exported"),
                    f"Next action: {wake_payload.get('next_safe_action') or build_state.get('next_safe_action') or 'not exported'}",
                    f"Agent queue tasks: {queue_by_floor.get(floor_name, 0)}",
                    f"Source draw paths: {len(priority_paths)}",
                    "Top draw: " + (", ".join(str(item.get("relative_path")) for item in priority_paths[:3] if item.get("relative_path")) or "none"),
                    "Post-population: " + (", ".join(str(item) for item in (post_population.get("path") or [])[:2]) or "not exported"),
                ]
            )

        def _floor_button_caption(summary: dict, floor_name: str) -> str:
            payload = _floor_payload(summary, floor_name)
            wake_payload = ((summary.get("local_agent_wakeup") or {}).get("by_floor") or {}).get(floor_name) or {}
            wake_connection = wake_payload.get("ollama_connection") or {}
            wake_draw = wake_payload.get("assimilation_draw") or {}
            if not payload and not wake_payload:
                return f"{floor_name}\nnot aligned"
            status = str(payload.get("primary_status") or "planned").replace("_", " ")
            agent = str(payload.get("assigned_agent_id") or "unknown")
            model = str(wake_connection.get("model") or payload.get("model") or "model?")
            draw_count = len(wake_draw.get("priority_paths") or [])
            return f"{floor_name}\n{status}\nagent={agent}\n{model} | draw={draw_count}"

        summary_state = {"payload": _safe_agent_home_summary()}
        floor_order = _display_order(summary_state["payload"])
        preferred_floor = (
            ((summary_state["payload"].get("workspace_lanes") or {}).get("primary_surface"))
            or "Trinity"
        )
        default_floor = select_floor if select_floor in floor_order else (
            preferred_floor if preferred_floor in floor_order else (floor_order[0] if floor_order else "Trinity")
        )
        selected_floor = {"name": default_floor}
        floor_buttons: Dict[str, tk.Button] = {}

        wrapper = tk.Frame(self.main_container, bg=COLORS["bg_dark"])
        wrapper.pack(fill="both", expand=True)

        header = tk.Frame(wrapper, bg=COLORS["bg_panel"], height=48)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Functions Hub Home",
            font=("Arial", 14, "bold"),
            bg=COLORS["bg_panel"],
            fg=COLORS["accent_cyan"],
        ).pack(side="left", padx=12)

        tk.Label(
            header,
            text="Ask Achilles, active floor context, local AI state, buildout stage, and gated floor actions.",
            font=("Arial", 9),
            bg=COLORS["bg_panel"],
            fg=COLORS["text_green"],
        ).pack(side="left", padx=12)

        body = tk.Frame(wrapper, bg=COLORS["bg_dark"])
        body.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        body.grid_columnconfigure(0, weight=0, minsize=250)
        body.grid_columnconfigure(1, weight=2, minsize=420)
        body.grid_columnconfigure(2, weight=2, minsize=420)
        body.grid_rowconfigure(0, weight=1)

        rail = tk.Frame(body, bg=COLORS["bg_panel"], bd=1, relief="flat")
        rail.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        info = tk.Frame(body, bg=COLORS["bg_panel"], bd=1, relief="flat")
        info.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        detail = tk.Frame(body, bg=COLORS["bg_panel"], bd=1, relief="flat")
        detail.grid(row=0, column=2, sticky="nsew")

        tk.Label(
            rail,
            text="Frontend",
            font=("Arial", 12, "bold"),
            bg=COLORS["bg_panel"],
            fg=COLORS["accent_cyan"],
        ).pack(anchor="w", padx=12, pady=(12, 6))

        frontend_actions = [
            ("Home", self.show_home),
            ("Dashboard", self.show_user_dashboard),
            ("Projects", self.show_projects),
            ("Documents", self.show_document_viewer),
            ("Ask Achilles", self.ask_achilles),
            ("Settings", self.show_settings),
        ]
        for label, command in frontend_actions:
            tk.Button(
                rail,
                text=label,
                command=command,
                anchor="w",
                bg=COLORS["bg_dark"],
                fg=COLORS["text_white"],
                activebackground=COLORS["accent_cyan"],
                activeforeground=COLORS["bg_dark"],
                relief="flat",
                font=("Arial", 9, "bold"),
            ).pack(fill="x", padx=12, pady=3)

        tk.Label(
            rail,
            text="Backend Floors",
            font=("Arial", 12, "bold"),
            bg=COLORS["bg_panel"],
            fg=COLORS["accent_cyan"],
        ).pack(anchor="w", padx=12, pady=(14, 6))

        overview = tk.Text(info, height=7, wrap="word", font=("Consolas", 9), bg=COLORS["bg_dark"], fg=COLORS["text_white"])
        overview.pack(fill="x", padx=12, pady=(12, 8))
        floor_detail = tk.Text(info, height=14, wrap="word", font=("Consolas", 9), bg=COLORS["bg_dark"], fg=COLORS["text_white"])
        floor_detail.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        actions = tk.Frame(info, bg=COLORS["bg_panel"])
        actions.pack(fill="x", padx=12, pady=(0, 12))

        detail_header = tk.Label(
            detail,
            text="Operator Surface",
            font=("Arial", 12, "bold"),
            bg=COLORS["bg_panel"],
            fg=COLORS["accent_cyan"],
        )
        detail_header.pack(anchor="w", padx=12, pady=(12, 8))
        detail_mount = tk.Frame(detail, bg=COLORS["bg_dark"])
        detail_mount.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        def _workspace_placeholder(floor_name: str) -> None:
            for child in detail_mount.winfo_children():
                child.destroy()
            tk.Label(
                detail_mount,
                text=_format_operator_home(summary_state["payload"], floor_name),
                justify="left",
                anchor="nw",
                bg=COLORS["bg_dark"],
                fg=COLORS["text_white"],
                font=("Consolas", 10),
                wraplength=520,
            ).pack(fill="both", expand=True, padx=14, pady=14)

        def _open_wakeup_packet() -> None:
            wake_payload = ((summary_state["payload"].get("local_agent_wakeup") or {}).get("by_floor") or {}).get(selected_floor["name"]) or {}
            _safe_open_path(wake_payload.get("packet_path"), f"Wake Packet: {selected_floor['name']}")

        def _open_buildout_handoff() -> None:
            _safe_open_path(LIGHTSPEED_ROOT / "config" / "buildout_phase_contract.json", "Buildout Handoff")

        def _open_agentic_launch_queue() -> None:
            _safe_open_path(_agentic_launch_queue_path(summary_state["payload"]), "Agentic Launch Queue")

        def _open_neo_smith_artifact() -> None:
            receipt_path = _neo_receipt_path(summary_state["payload"])
            if receipt_path:
                _safe_open_path(receipt_path, "Neo Receipt")
                return
            _safe_open_path(_queue_path(summary_state["payload"]), "Smith Queue")

        def _sync_button_states() -> None:
            for fname, button in floor_buttons.items():
                active = fname == selected_floor["name"]
                button.configure(
                    bg=COLORS["accent_cyan"] if active else COLORS["bg_dark"],
                    fg=COLORS["bg_dark"] if active else COLORS["text_white"],
                    relief="sunken" if active else "flat",
                )

        def _refresh_state(*, rebuild_detail: bool = False) -> None:
            summary_state["payload"] = _safe_agent_home_summary()
            _set_text(overview, _format_overview(summary_state["payload"]))
            _set_text(floor_detail, _format_floor_detail(summary_state["payload"], selected_floor["name"]))
            for fname, button in floor_buttons.items():
                button.configure(text=_floor_button_caption(summary_state["payload"], fname))
            if rebuild_detail:
                _mount_floor(selected_floor["name"])
            else:
                _workspace_placeholder(selected_floor["name"])
            _sync_button_states()

        def _select_floor(floor_name: str) -> None:
            selected_floor["name"] = floor_name
            detail_header.configure(text="Operator Surface")
            _set_text(floor_detail, _format_floor_detail(summary_state["payload"], floor_name))
            _workspace_placeholder(floor_name)
            self.update_status(f"Functions: {floor_name} selected")
            _sync_button_states()

        def _mount_floor(floor_name: str) -> None:
            selected_floor["name"] = floor_name
            detail_header.configure(text=f"{floor_name} Workspace")
            _set_text(floor_detail, _format_floor_detail(summary_state["payload"], floor_name))
            for child in detail_mount.winfo_children():
                child.destroy()
            self._render_floor_embedded(detail_mount, floor_name)
            self.update_status(f"Functions: {floor_name}")
            _sync_button_states()

        for fname in floor_order:
            button = tk.Button(
                rail,
                text=_floor_button_caption(summary_state["payload"], fname),
                justify="left",
                anchor="w",
                wraplength=150,
                bg=COLORS["bg_dark"],
                fg=COLORS["text_white"],
                activebackground=COLORS["accent_cyan"],
                activeforeground=COLORS["bg_dark"],
                relief="flat",
                font=("Arial", 9, "bold"),
                command=lambda floor_name=fname: _select_floor(floor_name),
            )
            button.pack(fill="x", padx=12, pady=4)
            floor_buttons[fname] = button

        tk.Button(
            actions,
            text="Refresh State",
            command=lambda: _refresh_state(rebuild_detail=False),
            bg=COLORS["bg_dark"],
            fg=COLORS["text_white"],
            relief="flat",
        ).pack(side="left")
        tk.Button(
            actions,
            text="Open Backend Workspace",
            command=lambda: _mount_floor(selected_floor["name"]),
            bg=COLORS["bg_dark"],
            fg=COLORS["text_white"],
            relief="flat",
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            actions,
            text="Open Wake Packet",
            command=_open_wakeup_packet,
            bg=COLORS["bg_dark"],
            fg=COLORS["text_white"],
            relief="flat",
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            actions,
            text="Open Buildout Handoff",
            command=_open_buildout_handoff,
            bg=COLORS["bg_dark"],
            fg=COLORS["text_white"],
            relief="flat",
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            actions,
            text="Open Agent Queue",
            command=_open_agentic_launch_queue,
            bg=COLORS["bg_dark"],
            fg=COLORS["text_white"],
            relief="flat",
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            actions,
            text="Open Neo Receipt / Smith Queue",
            command=_open_neo_smith_artifact,
            bg=COLORS["bg_dark"],
            fg=COLORS["text_white"],
            relief="flat",
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            actions,
            text="Home",
            command=self.show_home,
            bg=COLORS["bg_dark"],
            fg=COLORS["text_white"],
            relief="flat",
        ).pack(side="right")

        _refresh_state(rebuild_detail=False)
        _select_floor(selected_floor["name"])

    def _render_floor_embedded(self, parent: tk.Widget, floor_name: str) -> None:
        """
        Render a floor UI into an existing container (tab/frame).
        """
        header = tk.Frame(parent, bg=COLORS["bg_panel"], height=56)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text=floor_name,
            font=("Arial", 16, "bold"),
            bg=COLORS["bg_panel"],
            fg=COLORS["accent_cyan"],
        ).pack(side="left", padx=14, pady=10)

        content = tk.Frame(parent, bg=COLORS["bg_dark"])
        content.pack(fill="both", expand=True, padx=14, pady=14)

        module = _get_z_floor_module(floor_name)
        if not module:
            tk.Label(
                content,
                text=f"{floor_name} function\n(Module not loaded)",
                font=("Arial", 14),
                bg=COLORS["bg_dark"],
                fg=COLORS["warning_orange"],
            ).pack(expand=True)
            return

        rendered = False
        last_type_error = None
        floor_ui = None

        def _try_call(func, args):
            nonlocal rendered, last_type_error, floor_ui
            for kwargs in ({"compact": True}, {"compact": True, "it_portal": True}, {}):
                try:
                    result = func(*args, **kwargs)
                    if isinstance(result, tk.Widget):
                        floor_ui = result
                        result.pack(fill="both", expand=True)
                    rendered = True
                    return
                except TypeError as e:
                    last_type_error = e
                    continue

        for method_name, arg_sets in (
            ("create_gui", [(content, COLORS), (self, content, COLORS), (self, content)]),
            ("build", [(self, content, COLORS), (self, content), (content, COLORS), (content,)]),
        ):
            if not hasattr(module, method_name):
                continue
            func = getattr(module, method_name)
            for args in arg_sets:
                _try_call(func, args)
                if rendered:
                    break
            if rendered:
                break

        if rendered:
            try:
                if floor_ui is not None:
                    self._floor_ui_widgets[floor_name] = floor_ui
            except Exception:
                pass
        else:
            self._render_floor_component_fallback(content, floor_name, last_type_error=last_type_error)

    def open_z_floor_tab(self, floor_name: str, subtab_title: str = "") -> bool:
        """
        Open a floor and (best-effort) select a specific sub-tab inside that floor UI.

        - Client mode: opens/raises the floor Toplevel window and selects the UI subtab when possible.
        - IT/Founder mode: routes via IT Portal -> Floors to keep governance centralized.
        """
        # IT/Founder mode: use IT Portal's embedded floor UIs for deep-linking.
        if self.user_mode == "it_founder":
            try:
                portal = getattr(self, "_it_portal", None)
                if HAS_IT_PORTAL and (portal is None or not portal.winfo_exists()):
                    self.open_it_portal()
                    portal = getattr(self, "_it_portal", None)
                if portal is not None and hasattr(portal, "open_floor_tab"):
                    return bool(portal.open_floor_tab(floor_name, subtab_title))
            except Exception:
                pass
            try:
                self.show_floors_hub(select_floor=floor_name)
            except Exception:
                return False
            return True

        # Client mode: open floor window then select tab on the loaded floor widget.
        try:
            self.open_z_floor(floor_name)
        except Exception:
            return False

        if not subtab_title:
            return True

        ui = None
        try:
            ui = self._floor_ui_widgets.get(floor_name)
        except Exception:
            ui = None

        if ui is None:
            return True

        try:
            nb = getattr(ui, "notebook", None)
            tabs = getattr(ui, "_tabs", None)
            if nb is not None and isinstance(tabs, dict) and subtab_title in tabs:
                nb.select(tabs[subtab_title])
                return True
        except Exception:
            return True

        return True

    def _render_floor_component_fallback(self, parent: tk.Widget, floor_name: str, last_type_error=None):
        """Fallback UI when a floor module doesn't expose a compatible GUI entrypoint."""
        wrapper = tk.Frame(parent, bg=COLORS['bg_dark'])
        wrapper.pack(fill='both', expand=True)

        title = f"{floor_name} module loaded (no GUI entrypoint)"
        if last_type_error is not None:
            title += "\nSignature mismatch; see console for details."
            print(f"[WARN] {floor_name} GUI signature mismatch: {last_type_error}")

        tk.Label(
            wrapper,
            text=title,
            font=('Arial', 14),
            bg=COLORS['bg_dark'],
            fg=COLORS['warning_orange'],
        ).pack(pady=(10, 10))

        if self.floor_loader is None or not getattr(self.floor_loader, "manifests", None):
            tk.Label(
                wrapper,
                text="FloorLoader not available; cannot list components.",
                font=('Arial', 11),
                bg=COLORS['bg_dark'],
                fg=COLORS['text_cyan'],
            ).pack(pady=5)
            return

        match = None
        for floor_folder, manifest in self.floor_loader.manifests.items():
            if getattr(manifest, "floor_name", None) == floor_name:
                match = (floor_folder, manifest)
                break

        if match is None:
            tk.Label(
                wrapper,
                text="No manifest match found for this floor name.",
                font=('Arial', 11),
                bg=COLORS['bg_dark'],
                fg=COLORS['text_cyan'],
            ).pack(pady=5)
            return

        floor_folder, manifest = match
        floor_dir = LIGHTSPEED_ROOT / "Z Axis" / floor_folder

        tk.Label(
            wrapper,
            text=f"Components in `{floor_folder}`: {len(manifest.components)}",
            font=('Arial', 11),
            bg=COLORS['bg_dark'],
            fg=COLORS['text_green'],
        ).pack(pady=(0, 8))

        listbox = tk.Listbox(wrapper, height=10, font=('Consolas', 10))
        listbox.pack(fill='x', padx=20, pady=(0, 10))

        for comp in manifest.components:
            listbox.insert('end', f"{comp.id}  |  {comp.name}")

        btn_row = tk.Frame(wrapper, bg=COLORS['bg_dark'])
        btn_row.pack(pady=(0, 10))

        def open_selected():
            sel = listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            component_info = manifest.components[idx]

            try:
                cls = self.floor_loader.load_component(component_info, dependencies={
                    'db': self.db,
                    'event_bus': self.event_bus,
                    'storage': self.storage,
                    'accumulator': self.data_accumulator,
                    'app': self,
                }, floor_dir=floor_dir)
                if cls is None:
                    messagebox.showerror("Component Load Failed", f"Failed loading: {component_info.name}")
                    return

                if isinstance(cls, type) and issubclass(cls, tk.Toplevel):
                    cls(self)
                    return
                if isinstance(cls, type) and issubclass(cls, tk.Frame):
                    inst = cls(wrapper)
                    inst.pack(fill='both', expand=True, padx=20, pady=10)
                    return

                messagebox.showinfo(
                    "Component Loaded",
                    f"Loaded {component_info.name} ({component_info.class_name}).\n"
                    f"Non-UI component; use it via services/dependencies.",
                )
            except Exception as e:
                messagebox.showerror("Component Error", str(e))

        tk.Button(btn_row, text="Open Selected Component", command=open_selected).pack(side='left', padx=6)

    # ========================================================================
    # ACHILLES AI ASSISTANT
    # ========================================================================

    def ask_achilles(self):
        """Achilles AI Assistant interface"""
        dialog = tk.Toplevel(self)
        dialog.title("Ask Achilles - AI Assistant")
        dialog.geometry("600x500")
        dialog.configure(bg=COLORS['bg_dark'])

        # Title
        mode_text = "Guided Mode" if self.user_mode == "client" else "Orchestrator Mode"
        tk.Label(dialog, text=f"Ask Achilles ({mode_text})",
                font=('Arial', 20, 'bold'),
                bg=COLORS['bg_dark'],
                fg=COLORS['accent_magenta']).pack(pady=20)

        # Input
        tk.Label(dialog, text="What can I help you with?",
                font=('Arial', 12),
                bg=COLORS['bg_dark'],
                fg=COLORS['text_green']).pack(pady=10)

        input_frame = tk.Frame(dialog, bg=COLORS['bg_dark'])
        input_frame.pack(fill='x', padx=30, pady=10)

        input_text = tk.Text(input_frame, height=4, width=50,
                            font=('Arial', 12),
                            bg='#001122', fg=COLORS['text_green'])
        input_text.pack()

        # Response area
        response_frame = tk.Frame(dialog, bg=COLORS['bg_panel'])
        response_frame.pack(fill='both', expand=True, padx=30, pady=10)

        response_text = scrolledtext.ScrolledText(response_frame,
                                                  height=12, width=50,
                                                  font=('Arial', 11),
                                                  bg='#001122',
                                                  fg=COLORS['text_cyan'],
                                                  wrap='word')
        response_text.pack(fill='both', expand=True, padx=10, pady=10)

        def process():
            query = input_text.get('1.0', 'end-1c').strip()
            if not query:
                return

            response_text.insert('end', f"\nYou: {query}\n\n")

            response_text.insert('end', "Achilles: Processing...\n")
            response_text.see('end')

            def run():
                api = None
                if HAS_FRAMEWORK and self.api_manager:
                    try:
                        api = self.api_manager.get_api('ollama')
                    except Exception:
                        api = None

                if api and not api.enabled:
                    self.after(
                        0,
                        lambda: (
                            response_text.insert(
                                'end',
                                "Achilles: Ollama is disabled.\n"
                                "Enable it in Settings > APIs, and ensure `ollama serve` is running.\n\n"
                            ),
                            response_text.see('end')
                        )
                    )
                    return

                try:
                    from core.ai.ollama_connector import OllamaConnector, OllamaConfig
                except Exception as e:
                    self.after(
                        0,
                        lambda: (
                            response_text.insert('end', f"Achilles: Ollama connector unavailable: {e}\n\n"),
                            response_text.see('end')
                        )
                    )
                    return

                try:
                    cfg = OllamaConfig()
                    if api:
                        cfg.base_url = getattr(api, 'base_url', cfg.base_url) or cfg.base_url
                        cfg.default_model = (api.config or {}).get('default_model', cfg.default_model) or cfg.default_model
                        cfg.streaming = (api.config or {}).get('streaming', cfg.streaming)
                        cfg.temperature = (api.config or {}).get('temperature', cfg.temperature)
                        cfg.max_tokens = (api.config or {}).get('max_tokens', cfg.max_tokens)
                        cfg.timeout = (api.config or {}).get('timeout', cfg.timeout)

                    connector = OllamaConnector(cfg)
                    connector.set_dual_mode(self.user_mode or "client", self.current_user or {})

                    self._publish_event("ai.prompt.received", {"prompt": query, "model": cfg.default_model})

                    reply = connector.chat(
                        message=query,
                        model=cfg.default_model,
                        stream=False,
                        context={"screen": self.current_screen}
                    )

                    self._publish_event(
                        "ai.response.generated",
                        {"prompt": query, "response": reply[:4000], "model": cfg.default_model}
                    )

                    self.after(
                        0,
                        lambda: (
                            response_text.insert('end', f"Achilles: {reply}\n\n"),
                            response_text.see('end')
                        )
                    )
                except Exception as e:
                    self.after(
                        0,
                        lambda: (
                            response_text.insert('end', f"Achilles: Error: {e}\n\n"),
                            response_text.see('end')
                        )
                    )

            threading.Thread(target=run, daemon=True).start()

            response_text.see('end')

        tk.Button(dialog, text="Ask Achilles",
                 command=process,
                 bg=COLORS['accent_magenta'], fg='white',
                 font=('Arial', 12, 'bold'),
                 width=20, height=2).pack(pady=10)

    def open_command_palette(self, *, initial_query: str = "", initial_category: str = "all"):
        """
        Open the unified command palette (Trinity Unified Search).

        Open-world pattern: a single searchable surface for actions + documents + objects.
        """
        try:
            wizard_path = (Path(__file__).resolve().parent / "Z Axis" / "Z+3_Trinity" / "wizards" / "unified_search_system.py").resolve()
            if not wizard_path.exists():
                raise FileNotFoundError(wizard_path)

            spec = spec_from_file_location("lightspeed_unified_search_system_palette", wizard_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load UnifiedSearchSystem from {wizard_path}")
            mod = module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            SearchUI = getattr(mod, "SearchUI")

            win = tk.Toplevel(self)
            try:
                win.title("LightSpeed Command Palette")
                win.geometry("1000x600")
            except Exception:
                pass
            SearchUI(
                win,
                initial_query=str(initial_query or ""),
                initial_category=str(initial_category or "all"),
                host=self,
            )
            try:
                win.lift()
                win.focus_force()
            except Exception:
                pass
            return
        except Exception:
            # Fallback: open Morpheus for knowledge browsing.
            try:
                self.open_z_floor("Morpheus")
            except Exception:
                pass

    # ========================================================================
    # HELP
    # ========================================================================

    def show_help(self):
        """Show help"""
        it_portal_note = "\n- Operator OS: governance + approvals + Trinity functions (IT/Founder only)" if self.user_mode == "it_founder" and _trinity_ui_surface_available() else ""
        surface_rows = "\n".join(
            f"{item['shortcut']:<16} {item['label']}"
            + ("" if item["available"] else " (unavailable in this checkout)")
            for item in _shell_action_catalog()
        )
        help_text = f"""
LIGHTSPEED UNIFIED ORCHESTRATOR v3.0
Keyboard Shortcuts:

{surface_rows}
Ctrl+F          Focus Bento Search (when menu is visible)
Ctrl+Q          Quit
Esc             Go Back
F1              This Help

Immersive Overlay (when in interactive world):
Esc             Toggle pause-menu overlay
Tab / 1-4       Menu scope (All/Active/Fav/Recent)
V               Toggle favorite on hovered tile

Current Mode: {self.user_mode.upper() if self.user_mode else 'Not logged in'}
User: {self.current_user.get('fullname', 'N/A') if self.current_user else 'N/A'}
Clearance: Level {self.current_user.get('clearance', 0) if self.current_user else 0}

Visible Shell Controls:
- Ask Achilles, Immersive World, Z Functions
- Operator OS (IT/Founder only){" (not available in this checkout)" if not _trinity_ui_surface_available() else ""}
- Lobby HUD functions are page-local; Ctrl+H returns Home

FEATURES:
- Dual-mode: Client (guided) vs IT/Founder (full control)
- All 14 PDF screens implemented
- 8 Z-axis floor functions routed through one shell{it_portal_note}
- Framework layer (themes, settings, widgets, APIs)
- Unified database
- Document viewer + Project tree
- Real-time event processing
- Achilles AI ready (uses Ollama when enabled in Settings)
"""
        messagebox.showinfo("Help - LightSpeed Unified", help_text)


# ============================================================================
# CLI MODE (from original N.py)
# ============================================================================

def cli_mode():
    """Command-line interface mode"""
    from core.services import get_services_logger

    print("=" * 70)
    print(">> LightSpeed Portal - CLI Mode")
    print("=" * 70)

    services = initialize_services()
    logger = get_services_logger()

    def show_status():
        """Show system status"""
        db = get_db()
        event_bus = get_event_bus()
        storage = get_storage()

        print("\n[DATABASE]")
        tables = db.get_all_tables()
        print(f"  Tables: {len(tables)}")

        print("\n[EVENT BUS]")
        stats = event_bus.get_stats()
        print(f"  Subscribers: {stats['total_subscribers']}")

        print("\n[STORAGE]")
        storage_stats = storage.get_storage_stats()
        print(f"  Files: {storage_stats['total_files']}")

        print("\n[SERVICE REGISTRY]")
        try:
            from core.services.function_registry import validate_service_registry

            reg_status = validate_service_registry(LIGHTSPEED_ROOT, include_disabled=True)
            if not reg_status.get("exists"):
                print(f"  Registry not found: {reg_status.get('path')}")
            else:
                enabled = reg_status.get("enabled", 0)
                total = reg_status.get("total", 0)
                ok = reg_status.get("import_ok", 0)
                fail = reg_status.get("import_fail", 0)
                pct = (enabled / total * 100.0) if total else 0.0

                print(f"  Enabled: {enabled}/{total} ({pct:.0f}%)")
                print(f"  Imports: {ok} ok, {fail} failed")
                if fail:
                    errors = [
                        (name, entry.get("error"))
                        for name, entry in (reg_status.get("entries") or {}).items()
                        if entry and entry.get("enabled", False) and not entry.get("import_ok", False)
                    ]
                    for name, err in errors[:3]:
                        print(f"    - {name}: {(err or '')[:60]}")
        except Exception as e:
            print(f"  Error reading registry: {e}")

        print("\n[OK] All systems operational\n")

    # Interactive loop
    while True:
        try:
            cmd = input("N> ").strip().lower()

            if cmd in ['exit', 'quit', 'q']:
                break
            elif cmd == 'status':
                show_status()
            elif cmd == 'gui':
                shutdown_services()
                return gui_mode()
            elif cmd == 'help':
                print("Commands: status, gui, test, exit")
            else:
                print(f"Unknown command: {cmd}")

        except KeyboardInterrupt:
            break
        except EOFError:
            # Non-interactive environments (e.g., CI, redirected stdin).
            break

    shutdown_services()
    print("[OK] Shutdown complete\n")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def gui_mode(
    *,
    auto_trinity_login: bool = False,
    requested_it_portal: bool = False,
    start_in_immersive: bool = False,
    launch_profile: str = "resident",
):
    """Launch GUI mode (2D Portal Mode / Classic TTK Interface)."""
    # Ensure background automation can safely autostart when running N.py directly (without LAUNCH_GUI.bat).
    os.environ.setdefault("LIGHTSPEED_MODE", "GUI")
    os.environ.setdefault("LIGHTSPEED_AUTOSTART", "1")
    try:
        app = LightSpeedUnified(
            auto_trinity_login=auto_trinity_login,
            requested_it_portal=requested_it_portal,
            launch_profile=launch_profile,
        )
        if start_in_immersive:
            # Defer until Tk has a window and layout, otherwise some attach code will mis-measure sizes.
            try:
                app.after(50, lambda: app.show_immersive_world(interactive=False))
            except Exception:
                pass
        app.mainloop()
        shutdown_services()
        return 0
    except Exception as e:
        # If N.py is launched via pythonw/double-click, a console traceback may be invisible.
        # Make the failure loud and actionable.
        try:
            import traceback

            traceback.print_exc()
        except Exception:
            pass

        try:
            from tkinter import messagebox  # type: ignore

            messagebox.showerror(
                "LightSpeed - Launch Failed",
                "N.py could not start the UI.\n\n"
                f"Error: {e}\n\n"
                "Tip: Run `python N.py --verify` to validate dependencies and floors.",
            )
        except Exception:
            # Fall back to stderr/print only.
            pass

        try:
            shutdown_services()
        except Exception:
            pass
        return 2


def immersive_mode():
    """Legacy 3D immersive launcher (kept for backwards compatibility)."""
    print("\n" + "="*80)
    print("LIGHTSPEED V1.0.0 - IMMERSIVE 3D ENVIRONMENT")
    print("="*80 + "\n")

    # Initialize core services first
    print("[N.py] Initializing core services...")
    try:
        initialize_services()
        print("[N.py] [OK] Core services initialized")
    except Exception as e:
        print(f"[N.py] Error initializing services: {e}")
        print("[N.py] Continuing with limited functionality...")

    # Load Z-floors
    print("[N.py] Loading Z-floors...")
    if HAS_FLOOR_LOADER:
        try:
            loader = FloorLoader(lightspeed_root=LIGHTSPEED_ROOT)
            deps = {
                "db": get_db(),
                "database": get_db(),
                "event_bus": get_event_bus(),
                "storage": get_storage(),
            }
            ok = loader.initialize_all_floors_inside_out(dependencies=deps)
            print(f"[N.py] [OK] Z-floor bootstrap: {'OK' if ok else 'PARTIAL'}")
        except Exception as e:
            print(f"[N.py] Warning: Floor loader error: {e}")
    else:
        print("[N.py] Floor loader not available, skipping dynamic loading")

    # Launch unified immersive interface
    print("[N.py] Launching 3D Immersive Environment...")
    print()
    print("Controls:")
    print("  - WASD: Move around")
    print("  - Shift: Run")
    print("  - Space: Jump (tap again mid-air for double-jump)")
    print("  - Mouse: Look around")
    print("  - Caps Lock x2: Toggle UI overlay")
    print("  - F: Toggle flowchart quick-jump")
    print("  - Escape: Exit fullscreen / Exit app")
    print("  - Click objects to interact")
    print()

    try:
        # Load unified immersive interface
        launch_immersive = _load_symbol_from_file(
            "Z Axis/Z0_TheConstruct/gui/immersive_n_integrated.py",
            "launch_immersive",
        )

        # Create orchestrator if available
        orchestrator = None
        try:
            InterfaceOrchestrator = _load_symbol_from_file(
                "Z Axis/Z+3_Trinity/ui/interface_orchestrator.py",
                "InterfaceOrchestrator",
            )
            try:
                from ui.settings_manager import get_settings_manager  # type: ignore
                _trinity_settings = get_settings_manager()
            except Exception:
                _trinity_settings = None

            orchestrator = InterfaceOrchestrator(
                event_bus=get_event_bus(),
                database=get_db(),
                trinity=_trinity_settings,
            )
            print("[N.py] [OK] Interface Orchestrator initialized")
        except Exception as e:
            print(f"[N.py] Warning: Orchestrator not available: {e}")

        # Launch immersive interface
        physics_config = {
            "gravity_m_s2": 20.0,
            "jump_strength": 7.0,
            "double_jump_strength": 6.0
        }

        interface = launch_immersive(
            orchestrator=orchestrator,
            physics_config=physics_config,
            fullscreen=True
        )

        print()
        print("="*80)
        print("Immersive environment closed.")
        print("="*80)

        shutdown_services()
        return 0

    except ImportError as e:
        print(f"[N.py] ERROR: 3D environment not available: {e}")
        print("[N.py] Falling back to 2D Portal Mode (Classic GUI)...")
        return gui_mode()
    except Exception as e:
        print(f"[N.py] ERROR: 3D environment failed: {e}")
        import traceback
        traceback.print_exc()
        print("[N.py] Falling back to 2D Portal Mode (Classic GUI)...")
        return gui_mode()


def main():
    """Main entry point with argument parsing"""
    # N.py is often launched from a different working directory (Explorer, shortcuts, bat files).
    # Several components still use repo-relative paths (e.g. "config/settings.json"), so pin cwd.
    try:
        os.chdir(str(LIGHTSPEED_ROOT))
    except Exception:
        pass

    parser = argparse.ArgumentParser(
        description="LightSpeed Unified Orchestrator V1.0.0"
    )
    parser.add_argument('--cli', action='store_true', help='CLI mode')
    parser.add_argument('--portal', '--2d', '--gui', action='store_true',
                       help='Launch 2D Portal Mode (Classic TTK GUI)')
    parser.add_argument('--3d', '--immersive', action='store_true',
                       help='Launch 3D immersive environment (optional)')
    parser.add_argument(
        '--login',
        action='store_true',
        help='Open Trinity Login Portal on startup (preferred)',
    )
    parser.add_argument(
        '--it-portal',
        action='store_true',
        help='Open Trinity IT Portal after login (forces portal mode; requires IT clearance)',
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Non-GUI verification (superset of --smoke) and exit',
    )
    parser.add_argument(
        '--smoke',
        action='store_true',
        help='Non-GUI smoke test (init services, floors, UI imports) and exit',
    )
    parser.add_argument(
        '--launch-profile',
        choices=['resident', 'enabled'],
        default='resident',
        help='Boot resident floors by default, or use the legacy enabled-floor launch policy.',
    )
    parser.add_argument('--version', action='store_true', help='Show version')
    parser.add_argument('--depmap', action='store_true', help='Print platform dependency map JSON and exit')
    parser.add_argument('--depmap-out', type=str, default=None, help='Optional path to write dependency map JSON')
    parser.add_argument(
        '--sweep-legacy-packs',
        action='store_true',
        help='Non-GUI: ingest Z Axis/archive/legacy_packs into Oracle (dedupe-only) and stage one reconciliation task via Z Direct.',
    )
    parser.add_argument(
        '--sweep-legacy-packs-deep',
        action='store_true',
        help='Non-GUI: deeper legacy_packs sweep (more files + broader allowlist) and stage one reconciliation task via Z Direct.',
    )
    parser.add_argument(
        '--sweep-max-files',
        type=int,
        default=None,
        help='Optional cap for legacy sweep (overrides defaults).',
    )
    parser.add_argument(
        '--sweep-ext',
        action='append',
        default=None,
        help='Repeatable extension allowlist for legacy sweep (e.g. --sweep-ext .py --sweep-ext .md).',
    )

    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Background worker gating (operator expectation)
    # ------------------------------------------------------------------
    # - N portal mode (default): retrieve/display only; avoid heavy background tasks.
    # - IT Portal mode: enable Smith/Oracle background automation (approval-gated via Z Direct).
    # - verify/smoke: disable workers to avoid side effects and DB lock contention.
    try:
        if getattr(args, "verify", False) or getattr(args, "smoke", False):
            os.environ["LIGHTSPEED_DISABLE_BACKGROUND_WORKERS"] = "1"
        elif getattr(args, "it_portal", False):
            os.environ.pop("LIGHTSPEED_DISABLE_BACKGROUND_WORKERS", None)
        else:
            os.environ.setdefault("LIGHTSPEED_DISABLE_BACKGROUND_WORKERS", "1")
    except Exception:
        pass

    if args.version:
        try:
            v = (LIGHTSPEED_ROOT / "VERSION").read_text(encoding="utf-8", errors="replace").strip() or "unknown"
        except Exception:
            v = "unknown"
        print(f"LightSpeed Unified Orchestrator v{v}")
        print("Primary Interface: N.py (UI shell)")
        print("Admin Surface: Trinity IT Portal")
        print("Author: Romer Industries / EMASSC")
        print("\nPrimary Interface: UI-first Lobby (Bento over ambient 3D background)")
        print("Optional: 3D Immersive Environment (WASD/mouse look)")
        return 0

    if args.depmap:
        try:
            import json
            from core.analysis.dependencies import PlatformDependencyMapper

            root = Path(__file__).resolve().parent
            graph = PlatformDependencyMapper(root).build()

            if args.depmap_out:
                out_path = Path(args.depmap_out).expanduser()
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
                print(f"[OK] Wrote dependency map: {out_path}")
            else:
                print(json.dumps(graph, indent=2))
            return 0
        except Exception as e:
            print(f"[ERROR] Dependency map failed: {e}")
            return 2

    if args.sweep_legacy_packs or args.sweep_legacy_packs_deep:
        # Non-GUI legacy sweep: keep it safe + approval-gated via Z Direct.
        try:
            initialize_services()
        except Exception as e:
            print(f"[ERROR] Core services init failed: {e}")
            return 2

        try:
            root = Path(__file__).resolve().parent
            legacy_root = (root / "Z Axis" / "archive" / "legacy_packs").resolve()
            if not legacy_root.exists():
                print(f"[ERROR] Legacy packs folder not found: {legacy_root}")
                shutdown_services()
                return 2

            deep = bool(args.sweep_legacy_packs_deep)
            default_allow = [".py", ".md", ".json", ".txt"] if not deep else [".py", ".md", ".json", ".txt", ".yaml", ".yml", ".csv"]
            allow = list(args.sweep_ext) if args.sweep_ext else default_allow
            allow = [a if str(a).startswith(".") else f".{a}" for a in [str(x).strip().lower() for x in allow if str(x).strip()]]
            max_files = int(args.sweep_max_files) if args.sweep_max_files is not None else (2500 if deep else 200)

            try:
                OracleSmartFloorIntegrator = _load_symbol_from_file(
                    "Z Axis/Z-2_Oracle/components/oracle_smart_floor_integrator.py",
                    "OracleSmartFloorIntegrator",
                )
            except Exception as e:
                print(f"[ERROR] Oracle integrator load failed: {e}")
                shutdown_services()
                return 2

            try:
                from core.services import get_z_direct as _get_z_direct  # type: ignore
                zd = _get_z_direct()
            except Exception as e:
                print(f"[ERROR] Z Direct unavailable: {e}")
                shutdown_services()
                return 2

            oracle = OracleSmartFloorIntegrator(
                db=get_db(),
                event_bus=get_event_bus(),
                storage=get_storage(),
                z_direct=zd,
            )

            summary = oracle.ingest_directory(
                str(legacy_root),
                include_extensions=allow,
                max_files=max_files,
                recursive=True,
                metadata={"ingest_source": "legacy_packs_sweep_cli", "tags": ["legacy_packs"]},
            )

            if not isinstance(summary, dict) or not summary.get("success"):
                print(f"[ERROR] Sweep failed: {summary}")
                shutdown_services()
                return 2

            # Stage one reconciliation task via Z Direct (approval-gated; no commits).
            try:
                results = summary.get("results") if isinstance(summary.get("results"), list) else []
                sample = []
                for r in (results or [])[:50]:
                    if not isinstance(r, dict):
                        continue
                    sample.append(
                        {
                            "path": r.get("path"),
                            "success": bool(r.get("success")),
                            "already_archived": bool(r.get("already_archived")),
                            "vault_id": r.get("vault_id"),
                        }
                    )

                # Stable task id to avoid staging duplicates when the operator repeats sweeps.
                try:
                    import hashlib
                    import json as _json

                    digest_src = {
                        "directory": str(legacy_root),
                        "max_files": max_files,
                        "allowlist": allow,
                        "files_total": summary.get("files_total"),
                        "files_ingested": summary.get("files_ingested"),
                        "files_deduped": summary.get("files_deduped"),
                        "files_failed": summary.get("files_failed"),
                    }
                    digest = hashlib.sha256(
                        _json.dumps(digest_src, sort_keys=True, ensure_ascii=True).encode("utf-8")
                    ).hexdigest()[:12]
                except Exception:
                    digest = datetime.now().strftime("%Y%m%d_%H%M%S")

                task = {
                    "kind": "task",
                    "id": f"legacy_packs_reconcile_cli_{digest}",
                    "title": "Legacy packs reconciliation sweep (CLI)",
                    "status": "todo",
                    "priority": 2,
                    "tags": ["legacy_packs", "reconciliation", "oracle", "v1r"],
                    "details": {
                        "directory": str(legacy_root),
                        "max_files": max_files,
                        "allowlist": allow,
                        "files_total": summary.get("files_total"),
                        "files_ingested": summary.get("files_ingested"),
                        "files_deduped": summary.get("files_deduped"),
                        "files_failed": summary.get("files_failed"),
                        "sample": sample,
                        "operator_steps": [
                            "Open Trinity IT Portal -> Z Direct (channel Z-3) and filter tags legacy_packs",
                            "Commit this task into Smith, then split into sub-tasks by floor ownership",
                            "Use Oracle Registry to open referenced vault_file entries and extract missing capabilities",
                        ],
                    },
                }

                staged_already = False
                try:
                    tail = zd.tail_channel_outbox(from_channel="Z-3", to_channel="Z+3", limit=500)
                    for rec in tail:
                        p = rec.get("payload") if isinstance(rec, dict) else None
                        if isinstance(p, dict) and p.get("kind") == "task" and p.get("id") == task.get("id"):
                            staged_already = True
                            break
                except Exception:
                    staged_already = False

                if not staged_already:
                    env = zd.make_envelope(
                        kind="object",
                        channel="Z-3",
                        payload=task,
                        z_context="Z-3_Smith",
                        source="N.cli.sweep_legacy_packs",
                        tags=["task", "legacy_packs", "reconciliation"],
                    )
                    try:
                        zd.append_object("Z-3", env)
                    except Exception:
                        pass
                    try:
                        zd.append_channel_outbox(from_channel="Z-3", to_channel="Z+3", payload=env)
                    except Exception:
                        pass
                    try:
                        zd.append_channel_inbox(to_channel="Z+3", from_channel="Z-3", payload=env)
                    except Exception:
                        pass
            except Exception as e:
                print(f"[WARN] Sweep succeeded, but failed staging reconciliation task: {e}")

            print("[OK] Legacy sweep complete (non-destructive).")
            print(f"  Folder: {legacy_root}")
            print(f"  Allowlist: {', '.join(allow)}")
            print(f"  Max files: {max_files}")
            print(f"  Scanned: {summary.get('files_total')}")
            print(f"  Deduped: {summary.get('files_deduped')}")
            print(f"  New ingested: {summary.get('files_ingested')}")
            print(f"  Failed: {summary.get('files_failed')}")
            print("  Next: Trinity IT Portal -> Z Direct (channel Z-3) -> filter tags legacy_packs")

            shutdown_services()
            return 0
        except Exception as e:
            print(f"[ERROR] Legacy sweep failed: {e}")
            try:
                shutdown_services()
            except Exception:
                pass
            return 2

    if args.smoke or args.verify:
        print("\n" + "=" * 72)
        print("LIGHTSPEED VERIFY" if args.verify else "LIGHTSPEED SMOKE TEST (NON-GUI)")
        print("=" * 72)
        ui_ok = True
        try:
            from ui.premium_theme_engine import get_theme_engine  # noqa: F401
            from ui.universal_bento_system import get_bento_system  # noqa: F401
            from ui.interface_orchestrator import InterfaceOrchestrator  # noqa: F401
            print("[SMOKE] UI imports: OK")
        except Exception as e:
            ui_ok = False
            print(f"[SMOKE] UI imports: FAIL ({e})")

        services_ok = True
        try:
            initialize_services()
            print("[SMOKE] Core services: OK")
        except Exception as e:
            services_ok = False
            print(f"[SMOKE] Core services: FAIL ({e})")

        floors_ok = True
        if HAS_FLOOR_LOADER and services_ok:
            try:
                loader = FloorLoader(lightspeed_root=LIGHTSPEED_ROOT)
                deps = {
                    "db": get_db(),
                    "database": get_db(),
                    "event_bus": get_event_bus(),
                    "storage": get_storage(),
                }
                launch_boot_policy = _resolve_launch_boot_policy(
                    LIGHTSPEED_ROOT,
                    requested_profile=args.launch_profile,
                )
                floor_init = loader.initialize_all_floors_inside_out(
                    dependencies=deps,
                    boot_floor_names=launch_boot_policy.get("boot_floor_names"),
                    deferred_floor_names=launch_boot_policy.get("deferred_floor_names"),
                    manual_only_floor_names=launch_boot_policy.get("manual_only_floor_names"),
                    return_details=True,
                )
                floors_ok = bool((floor_init or {}).get("success"))
                print(f"[SMOKE] Floor bootstrap: {'OK' if floors_ok else 'PARTIAL'}")
                if isinstance(floor_init, dict):
                    print(
                        "[SMOKE] Launch profile: "
                        f"{args.launch_profile} | "
                        f"initialized={len(floor_init.get('initialized_floors') or [])} | "
                        f"deferred={len(floor_init.get('skipped_deferred') or [])} | "
                        f"manual={len(floor_init.get('skipped_manual') or [])}"
                    )
            except Exception as e:
                floors_ok = False
                print(f"[SMOKE] Floor bootstrap: FAIL ({e})")
        else:
            floors_ok = False
            print("[SMOKE] Floor bootstrap: SKIP (FloorLoader unavailable or services failed)")

        audit = _build_shell_startup_audit()
        missing_targets = audit.get("missing_targets", {})
        missing_floors = audit.get("missing_floors", [])
        print(
            "[SMOKE] Shell startup audit: "
            f"{len(audit.get('available_floors', []))} live floors, "
            f"{len(missing_floors)} missing floor entrypoints, "
            f"{len(missing_targets)} missing optional targets"
        )
        if missing_floors:
            print(f"[SMOKE] Missing floors: {', '.join(missing_floors)}")

        hygiene_ok = True
        if args.verify:
            # Canonical root should be minimal; floors own most code/data.
            allowed = {
                "ai_logs",
                "config",
                "data",
                "dataindex",
                "lightspeed_runtime",  # compatibility junction to the split canonical runtime
                "operations",  # legacy; tolerated during migration
                "tests",  # repo-level non-GUI regression/fitness tests
                "tools",  # D-shell support tooling
                "w6",
                "Z Axis",
                "__pycache__",
                ".pytest_cache",  # tooling cache (can appear when running pytest directly from repo root)
                ".gitattributes",
                "AGENTS.md",
                "cookies.txt",
                "LAUNCH_GUI.bat",
                "launcher_exe.py",
                "N.py",
                "README.md",
                "VERSION",
                "__main__.py",
                "verify_launch_ready.py",  # launch readiness verifier script
            }
            try:
                present = {p.name for p in LIGHTSPEED_ROOT.iterdir()}
                extras = sorted(present - allowed)
                if extras:
                    hygiene_ok = False
                    print(f"[VERIFY] Root hygiene: FAIL (unexpected: {', '.join(extras)})")
                else:
                    print("[VERIFY] Root hygiene: OK")
            except Exception as e:
                hygiene_ok = False
                print(f"[VERIFY] Root hygiene: FAIL ({e})")

        try:
            shutdown_services()
        except Exception:
            pass

        ok = ui_ok and services_ok and floors_ok and (hygiene_ok if args.verify else True)
        return 0 if ok else 2

    # Check user preference for interface mode
    # Canonical direction: UI-first. Immersive is optional/explicit.
    interface_mode = 'portal'

    try:
        prefs = get_user_preferences()
        if prefs and 'interface_mode' in prefs:
            interface_mode = prefs['interface_mode']
            print(f"[N.py] User preference: {interface_mode} mode")
    except:
        pass

    # Command-line args override user preference
    if getattr(args, 'portal', False) or getattr(args, 'gui', False):
        interface_mode = 'portal'
    elif getattr(args, 'login', False) or getattr(args, 'it_portal', False):
        interface_mode = 'portal'
    elif getattr(args, '3d', False):
        interface_mode = '3d'

    # Launch appropriate mode
    if args.cli:
        return cli_mode()
    elif interface_mode == 'portal':
        print("[N.py] Launching 2D Portal Mode (Classic GUI)...")
        return gui_mode(
            auto_trinity_login=bool(getattr(args, "login", False) or getattr(args, "it_portal", False)),
            requested_it_portal=bool(getattr(args, "it_portal", False)),
            launch_profile=str(getattr(args, "launch_profile", "resident") or "resident"),
        )
    else:
        # Embedded immersive mode (WASD) inside the canonical UI shell.
        # This keeps Bento/Trinity wiring consistent and avoids immersive-first drift.
        return gui_mode(
            start_in_immersive=True,
            launch_profile=str(getattr(args, "launch_profile", "resident") or "resident"),
        )


if __name__ == "__main__":
    sys.exit(main())
