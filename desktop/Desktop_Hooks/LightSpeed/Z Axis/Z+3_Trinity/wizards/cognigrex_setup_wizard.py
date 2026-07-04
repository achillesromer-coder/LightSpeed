#!/usr/bin/env python
"""
COGNIGREX SETUP WIZARD - Complete Z-Floor System Builder
LightSpeed Consolidated Platform

Comprehensive setup wizard that:
1. Sets up core user types (Main User, IT, Achilles; Guest is optional and off-by-default)
2. Discovers and hooks all Z-floor components
3. Configures floor colors, widgets, dashboards
4. Builds the smart floor workflow system
5. Tracks progress and supports resume/restart
6. Creates login page after completion

All components are callable via Z Direct system.

Author: LightSpeed Team
Version: 5.0.0
Date: 2026-01-25
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Callable
from dataclasses import dataclass, field, asdict
import json
import sys
import os
import threading
import time
from datetime import datetime
import hashlib
import importlib.util
import sqlite3


# Path configuration
def _find_lightspeed_root() -> Path:
    """Locate LightSpeed root by searching for N.py"""
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
            return candidate
    return here.parents[4]


LIGHTSPEED_ROOT = _find_lightspeed_root()
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"
CONFIG_ROOT = LIGHTSPEED_ROOT / "config"
DATAINDEX_ROOT = LIGHTSPEED_ROOT / "dataindex"

# Setup state file
SETUP_STATE_FILE = CONFIG_ROOT / "cognigrex_setup_state.json"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class UserProfile:
    """User profile configuration"""
    username: str
    display_name: str
    email: str = ""
    role: str = "user"  # main, it, achilles, guest
    clearance: int = 1  # 1-4
    enabled: bool = True
    avatar_color: str = "#00DDFF"
    floor_access: List[str] = field(default_factory=list)
    widget_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FloorConfig:
    """Z-Floor configuration"""
    floor_id: str
    floor_name: str
    z_level: int
    color: str
    icon: str = ""
    enabled: bool = True
    components: List[Dict[str, Any]] = field(default_factory=list)
    widgets: List[str] = field(default_factory=list)
    hooked: bool = False
    services: List[str] = field(default_factory=list)
    smart_floor_enabled: bool = True


@dataclass
class SetupState:
    """Complete setup state - supports resume/restart"""
    version: str = "5.0.0"
    started_at: str = ""
    last_updated: str = ""
    current_step: int = 0
    total_steps: int = 12
    completed: bool = False

    # User setup
    users: Dict[str, Dict] = field(default_factory=dict)
    active_user: str = ""

    # Floor setup
    floors_discovered: List[str] = field(default_factory=list)
    floors_configured: Dict[str, Dict] = field(default_factory=dict)
    components_hooked: int = 0
    components_total: int = 0

    # System setup
    database_initialized: bool = False
    event_bus_ready: bool = False
    smart_floor_enabled: bool = False
    widgets_configured: int = 0

    # Features
    immersive_3d_enabled: bool = True
    it_portal_configured: bool = False
    achilles_voice_enabled: bool = True


# ============================================================================
# FLOOR DEFINITIONS (Canonical)
# ============================================================================

CANONICAL_FLOORS = {
    # NOTE: First-run/setup is intentionally consolidated into Trinity (Z+3).
    "Z+3_Trinity": {
        "z_level": 3,
        "color": "#FF1493",
        "name": "Trinity",
        "description": "UI Layer & Customization",
        "icon": "palette",
        "services": ["settings_manager", "theme_designer", "code_editor", "analytics"]
    },
    "Z+2_Neo": {
        "z_level": 2,
        "color": "#00FF00",
        "name": "Neo",
        "description": "AI Assistant & Ollama",
        "icon": "brain",
        "services": ["ai_assistant", "code_completion", "training", "context"]
    },
    "Z+1_Architect": {
        "z_level": 1,
        "color": "#DAA520",
        "name": "Architect",
        "description": "Mission Planning & Goals",
        "icon": "blueprint",
        "services": ["mission_planner", "okr_tracker", "task_board"]
    },
    "Z0_TheConstruct": {
        "z_level": 0,
        "color": "#808080",
        "name": "TheConstruct",
        "description": "Training & Simulations",
        "icon": "cube",
        "services": ["physics_engine", "visualization_3d", "workspace"]
    },
    "Z-1_Morpheus": {
        "z_level": -1,
        "color": "#4B0082",
        "name": "Morpheus",
        "description": "Knowledge Base & Documentation",
        "icon": "book",
        "services": ["file_manager", "rich_text_editor", "chat_archive"]
    },
    "Z-2_Oracle": {
        "z_level": -2,
        "color": "#00008B",
        "name": "Oracle",
        "description": "IP Vault & Archiving",
        "icon": "vault",
        "services": ["smart_floor_integrator", "encyclopedia", "ingestion"]
    },
    "Z-3_Smith": {
        "z_level": -3,
        "color": "#006400",
        "name": "Smith",
        "description": "Background Jobs & Automation",
        "icon": "gear",
        "services": ["task_queue", "workflow_scheduler", "interfloor_coordinator"]
    },
    "Z-4_Merovingian": {
        "z_level": -4,
        "color": "#8B0000",
        "name": "Merovingian",
        "description": "System Core & Diagnostics",
        "icon": "server",
        "services": ["database", "event_bus", "settings_hub", "floor_manager"]
    }
}


# ============================================================================
# USER ROLE DEFINITIONS
# ============================================================================

USER_ROLES = {
    "main": {
        "display": "Main User",
        "description": "Primary user with guided experience",
        "clearance": 3,
        "color": "#00DDFF",
        "floor_access": ["all"],
        "features": ["dashboard", "settings", "floor_navigation", "widgets"]
    },
    "it": {
        "display": "IT / Founder",
        "description": "Full system access with IT Portal (21 tabs)",
        "clearance": 4,
        "color": "#FF00FF",
        "floor_access": ["all"],
        "features": ["it_portal", "diagnostics", "database", "all_settings", "god_mode"]
    },
    "achilles": {
        "display": "Achilles",
        "description": "Voice assistant persona with AI capabilities",
        "clearance": 4,
        "color": "#00FF88",
        "floor_access": ["all"],
        "features": ["voice_control", "ai_integration", "orchestrator_mode"]
    },
    "guest": {
        "display": "Guest",
        "description": "Limited access for demonstration",
        "clearance": 1,
        "color": "#888888",
        "floor_access": ["Z+3_Trinity", "Z0_TheConstruct"],
        "features": ["view_only", "limited_dashboard"]
    }
}


# ============================================================================
# WIDGET DEFINITIONS
# ============================================================================

WIDGET_CATALOG = {
    "status_monitor": {"name": "Status Monitor", "category": "system", "floor": "all"},
    "metrics_display": {"name": "Metrics Display", "category": "analytics", "floor": "all"},
    "task_queue": {"name": "Task Queue", "category": "productivity", "floor": "Z-3_Smith"},
    "console_output": {"name": "Console Output", "category": "dev", "floor": "all"},
    "file_browser": {"name": "File Browser", "category": "files", "floor": "Z-1_Morpheus"},
    "ai_chat": {"name": "AI Chat", "category": "ai", "floor": "Z+2_Neo"},
    "graph_chart": {"name": "Graph Chart", "category": "analytics", "floor": "all"},
    "quick_actions": {"name": "Quick Actions", "category": "productivity", "floor": "all"},
    "notifications": {"name": "Notifications", "category": "system", "floor": "all"},
    "system_info": {"name": "System Info", "category": "system", "floor": "Z-4_Merovingian"},
    "okr_tracker": {"name": "OKR Tracker", "category": "goals", "floor": "Z+1_Architect"},
    "calendar": {"name": "Calendar", "category": "productivity", "floor": "Z+3_Trinity"},
    "db_browser": {"name": "Database Browser", "category": "data", "floor": "Z-4_Merovingian"},
    "workflow_status": {"name": "Workflow Status", "category": "automation", "floor": "Z-3_Smith"},
    "encyclopedia": {"name": "Encyclopedia", "category": "knowledge", "floor": "Z-2_Oracle"},
    "training_progress": {"name": "Training Progress", "category": "ai", "floor": "Z+2_Neo"},
    "physics_sim": {"name": "Physics Simulation", "category": "simulation", "floor": "Z0_TheConstruct"},
    "voice_control": {"name": "Voice Control", "category": "ai", "floor": "Z+2_Neo"},
    "performance_profiler": {"name": "Performance Profiler", "category": "dev", "floor": "Z-4_Merovingian"},
    "theme_preview": {"name": "Theme Preview", "category": "ui", "floor": "Z+3_Trinity"}
}


# ============================================================================
# SETUP WIZARD CLASS
# ============================================================================

class CognigrexSetupWizard:
    """
    Complete Cognigrex Setup Wizard

    Setup process (steps may vary; Guest is optional and off-by-default):
    1. Welcome & Resume Check
    2. Main User Setup
    3. IT User Setup
    4. Achilles Setup
    5. (Optional) Guest Setup
    6. Z-Floor Discovery
    7. Component Hooking
    8. Floor Colors & Themes
    9. Widget Configuration
    10. Smart Floor Integration
    11. IT Portal & Dashboard
    12. Final Verification & Launch
    """

    def __init__(self, parent: Optional[tk.Tk] = None, *, on_complete: Optional[Callable[[Dict[str, Any]], None]] = None):
        # Window setup
        if parent is None:
            self.root = tk.Tk()
            self.standalone = True
        else:
            self.root = tk.Toplevel(parent)
            self.standalone = False

        # Optional callback for embedded usage (e.g. invoked from a running N/IT Portal).
        # When provided, the wizard will NOT spawn a new N.py process on completion.
        self._on_complete = on_complete

        self.root.title("Cognigrex Setup Wizard - LightSpeed V5.0")
        self.root.geometry("1200x800")
        self.root.configure(bg='#0a0a14')

        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 1200) // 2
        y = (self.root.winfo_screenheight() - 800) // 2
        self.root.geometry(f"1200x800+{x}+{y}")

        # Theme colors
        self.colors = {
            'bg_dark': '#0a0a14',
            'bg_panel': '#1a1a2e',
            'bg_card': '#16213e',
            'fg_primary': '#00DDFF',
            'fg_secondary': '#FF1493',
            'fg_text': '#FFFFFF',
            'fg_muted': '#888888',
            'success': '#00FF88',
            'warning': '#FFAA00',
            'error': '#FF4444',
            'border': '#00DDFF'
        }

        # Setup state
        self.state = self._load_state()

        # Feature gates (Guest is off-by-default; controlled via unified_config.json).
        self.allow_guest_mode = self._allow_guest_mode()

        # Step definitions
        self.steps = [
            ("Welcome", self._step_welcome),
            ("Main User", self._step_main_user),
            ("IT User", self._step_it_user),
            ("Achilles Setup", self._step_achilles),
            *([("Guest Setup", self._step_guest)] if self.allow_guest_mode else []),
            ("Floor Discovery", self._step_floor_discovery),
            ("Component Hook", self._step_component_hook),
            ("Floor Colors", self._step_floor_colors),
            ("Widget Config", self._step_widgets),
            ("Smart Floor", self._step_smart_floor),
            ("IT Portal", self._step_it_portal),
            ("Complete", self._step_complete)
        ]

        # Keep persisted state consistent with current step list.
        try:
            self.state.total_steps = len(self.steps)
            if int(self.state.current_step or 0) >= len(self.steps):
                self.state.current_step = max(0, len(self.steps) - 1)
        except Exception:
            pass

        # Current step data
        self.step_data: Dict[str, Any] = {}

        # Build UI
        self._build_ui()

        # Show current step
        self._show_step(self.state.current_step)

    def _allow_guest_mode(self) -> bool:
        """Guest mode is off-by-default; controlled by `features.allow_guest_mode` in unified_config.json."""
        try:
            cfg_path = (CONFIG_ROOT / "unified_config.json").resolve()
            if not cfg_path.exists():
                return False
            data = json.loads(cfg_path.read_text(encoding="utf-8", errors="replace"))
            if not isinstance(data, dict):
                return False
            features = data.get("features") if isinstance(data.get("features"), dict) else {}
            return bool((features or {}).get("allow_guest_mode", False))
        except Exception:
            return False

    def _get_z_direct(self):
        """Best-effort access to Merovingian's ZDirectService."""
        merov = (LIGHTSPEED_ROOT / "Z Axis" / "Z-4_Merovingian").resolve()
        try:
            if merov.exists() and str(merov) not in sys.path:
                sys.path.insert(0, str(merov))
            from core.services import get_z_direct  # type: ignore

            return get_z_direct()
        except Exception as e:
            raise RuntimeError(f"Z Direct service unavailable: {e}")

    def _active_username(self) -> str:
        try:
            active = str(self.state.active_user or "").strip() or "main"
            users = self.state.users or {}
            if isinstance(users, dict):
                u = users.get(active) or users.get("main")
                if isinstance(u, dict):
                    return str(u.get("username") or "").strip()
        except Exception:
            pass
        return ""

    def _reset_active_user_tailoring(self) -> None:
        """Reset tailoring for the active user (does not delete vault/registries)."""
        username = self._active_username()
        if not username:
            messagebox.showwarning("Reset Tailoring", "No active user is configured yet.", parent=self.root)
            return
        ok = messagebox.askyesno(
            "Reset Tailoring",
            f"Reset tailoring for '{username}'?\n\n"
            "This clears UI preferences, Bento layout/recents/favorites, OKRs, and Notes.\n"
            "It does not delete vault contents or durable registries.",
            parent=self.root,
        )
        if not ok:
            return
        try:
            merov = (LIGHTSPEED_ROOT / "Z Axis" / "Z-4_Merovingian").resolve()
            if merov.exists() and str(merov) not in sys.path:
                sys.path.insert(0, str(merov))
            from core.services import get_user_preferences  # type: ignore

            prefs = get_user_preferences(username)
            prefs.reset_to_defaults()
            messagebox.showinfo("Reset Tailoring", "Tailoring has been reset.", parent=self.root)
        except Exception as e:
            messagebox.showerror("Reset Tailoring", f"Failed to reset tailoring:\n{e}", parent=self.root)

    def _open_it_portal_host(self) -> None:
        """If embedded in a running N instance, focus/open the IT Portal for commit review."""
        host = getattr(self.root, "master", None)
        fn = getattr(host, "open_it_portal", None)
        if callable(fn):
            try:
                fn()
                return
            except Exception:
                pass
        messagebox.showinfo(
            "IT Portal",
            "IT Portal can be opened from N (IT/Founder mode): Dashboard -> Quick Actions -> IT Portal.",
            parent=self.root,
        )

    def _stage_v1r_definitions(self) -> None:
        """
        Stage a baseline set of V1R definitions into Z Direct (append-only).

        This does NOT commit anything into durable registries; use Trinity IT Portal to review/commit.
        """
        try:
            zd = self._get_z_direct()
        except Exception as e:
            messagebox.showerror("Stage V1R", str(e), parent=self.root)
            return

        staged = 0

        def _stage(payload: Dict[str, Any], tags: List[str]) -> None:
            nonlocal staged
            env = zd.make_envelope(
                kind="object",
                channel="Z+3",
                payload=payload,
                z_context="Trinity",
                source="CognigrexSetupWizard.stage_v1r_definitions",
                tags=tags,
            )
            zd.append_object("Z+3", env)
            staged += 1

        # 1) Built-in schemas (bootstrap; operators can evolve/commit from IT Portal).
        try:
            want = {
                "task",
                "simulation_result",
                "bento_widget",
                "action_def",
                "simulation_def",
                "workflow_def",
                "knowledge_node",
                "project",
            }
            for s in zd.builtin_schema_payloads() or []:
                if not isinstance(s, dict):
                    continue
                if str(s.get("id") or "").strip() in want:
                    _stage(s, ["v1r", "bootstrap", "schema"])
        except Exception:
            pass

        # 2) Simulation definitions (typed params; rendered by SpecForm).
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

        # 3) Action definitions (host-aware; runnable from Unified Search / command palette).
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
        ]
        for a in action_defs:
            _stage(a, ["v1r", "bootstrap", "action_def"])

        # 4) Bento widget definitions (optional UI extensions; can be enabled/disabled post-commit).
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

        messagebox.showinfo(
            "Stage V1R",
            f"Staged {staged} V1R definition(s) into Z Direct:\n\n"
            f"{(Z_AXIS_ROOT / 'Z+3_Trinity' / 'Z Direct' / 'objects.jsonl').resolve()}\n\n"
            "Open Trinity IT Portal to review and commit to durable registries.",
            parent=self.root,
        )

    def _load_state(self) -> SetupState:
        """Load setup state from file or create new"""
        if SETUP_STATE_FILE.exists():
            try:
                with open(SETUP_STATE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    state = SetupState(**data)
                    return state
            except Exception as e:
                print(f"Warning: Could not load state: {e}")

        # New state
        state = SetupState()
        state.started_at = datetime.now().isoformat()
        return state

    def _save_state(self):
        """Save current state to file"""
        self.state.last_updated = datetime.now().isoformat()
        CONFIG_ROOT.mkdir(parents=True, exist_ok=True)

        try:
            with open(SETUP_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.state), f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save state: {e}")

    def _build_ui(self):
        """Build the wizard UI"""
        # Main container
        self.main_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        self._build_header()

        # Progress bar
        self._build_progress()

        # Content area
        self.content_frame = tk.Frame(self.main_frame, bg=self.colors['bg_dark'])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

        # Navigation buttons
        self._build_navigation()

    def _build_header(self):
        """Build header with title and status"""
        header = tk.Frame(self.main_frame, bg=self.colors['bg_panel'], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # Title
        title = tk.Label(
            header,
            text="COGNIGREX SETUP WIZARD",
            font=('Segoe UI', 24, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_panel']
        )
        title.pack(side=tk.LEFT, padx=40, pady=20)

        # Version
        version = tk.Label(
            header,
            text="LightSpeed V5.0 | Z-Floor System Builder",
            font=('Segoe UI', 12),
            fg=self.colors['fg_muted'],
            bg=self.colors['bg_panel']
        )
        version.pack(side=tk.RIGHT, padx=40, pady=25)

    def _build_progress(self):
        """Build progress indicator"""
        progress_frame = tk.Frame(self.main_frame, bg=self.colors['bg_dark'])
        progress_frame.pack(fill=tk.X, padx=40, pady=(20, 0))

        # Step indicators
        self.step_indicators = []
        for i, (step_name, _) in enumerate(self.steps):
            indicator = tk.Frame(progress_frame, bg=self.colors['bg_dark'])
            indicator.pack(side=tk.LEFT, expand=True, fill=tk.X)

            # Circle
            circle_color = self.colors['fg_primary'] if i <= self.state.current_step else self.colors['fg_muted']
            circle = tk.Label(
                indicator,
                text=str(i + 1),
                font=('Segoe UI', 10, 'bold'),
                fg=self.colors['bg_dark'] if i <= self.state.current_step else self.colors['fg_muted'],
                bg=circle_color,
                width=3,
                height=1
            )
            circle.pack()

            # Name
            name = tk.Label(
                indicator,
                text=step_name,
                font=('Segoe UI', 8),
                fg=circle_color,
                bg=self.colors['bg_dark']
            )
            name.pack(pady=(2, 0))

            self.step_indicators.append((circle, name))

        # Progress bar
        self.progress_var = tk.DoubleVar(value=(self.state.current_step / len(self.steps)) * 100)
        progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=800
        )
        progress_bar.pack(fill=tk.X, pady=(15, 0))

    def _build_navigation(self):
        """Build navigation buttons"""
        nav_frame = tk.Frame(self.main_frame, bg=self.colors['bg_panel'], height=70)
        nav_frame.pack(fill=tk.X, side=tk.BOTTOM)
        nav_frame.pack_propagate(False)

        # Restart button
        self.restart_btn = tk.Button(
            nav_frame,
            text="Restart Setup",
            font=('Segoe UI', 11),
            fg=self.colors['warning'],
            bg=self.colors['bg_card'],
            activebackground=self.colors['bg_panel'],
            activeforeground=self.colors['warning'],
            relief=tk.FLAT,
            cursor='hand2',
            command=self._restart_setup
        )
        self.restart_btn.pack(side=tk.LEFT, padx=40, pady=15)

        # Next button
        self.next_btn = tk.Button(
            nav_frame,
            text="Next Step",
            font=('Segoe UI', 12, 'bold'),
            fg=self.colors['bg_dark'],
            bg=self.colors['fg_primary'],
            activebackground=self.colors['fg_secondary'],
            activeforeground=self.colors['bg_dark'],
            relief=tk.FLAT,
            cursor='hand2',
            width=15,
            command=self._next_step
        )
        self.next_btn.pack(side=tk.RIGHT, padx=40, pady=15)

        # Back button
        self.back_btn = tk.Button(
            nav_frame,
            text="Back",
            font=('Segoe UI', 11),
            fg=self.colors['fg_text'],
            bg=self.colors['bg_card'],
            activebackground=self.colors['bg_panel'],
            activeforeground=self.colors['fg_text'],
            relief=tk.FLAT,
            cursor='hand2',
            command=self._prev_step
        )
        self.back_btn.pack(side=tk.RIGHT, padx=10, pady=15)

    def _show_step(self, step_index: int):
        """Display a specific step"""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Update state
        self.state.current_step = step_index
        self._save_state()

        # Update progress
        self.progress_var.set((step_index / len(self.steps)) * 100)

        # Update indicators
        for i, (circle, name) in enumerate(self.step_indicators):
            if i < step_index:
                circle.configure(bg=self.colors['success'], fg=self.colors['bg_dark'])
                name.configure(fg=self.colors['success'])
            elif i == step_index:
                circle.configure(bg=self.colors['fg_primary'], fg=self.colors['bg_dark'])
                name.configure(fg=self.colors['fg_primary'])
            else:
                circle.configure(bg=self.colors['fg_muted'], fg=self.colors['fg_muted'])
                name.configure(fg=self.colors['fg_muted'])

        # Update buttons
        self.back_btn.configure(state=tk.NORMAL if step_index > 0 else tk.DISABLED)

        if step_index == len(self.steps) - 1:
            self.next_btn.configure(text="Launch Cognigrex")
        else:
            self.next_btn.configure(text="Next Step")

        # Call step function
        _, step_func = self.steps[step_index]
        step_func()

    def _next_step(self):
        """Advance to next step"""
        if self.state.current_step < len(self.steps) - 1:
            self._show_step(self.state.current_step + 1)
        else:
            self._launch_cognigrex()

    def _prev_step(self):
        """Go back to previous step"""
        if self.state.current_step > 0:
            self._show_step(self.state.current_step - 1)

    def _restart_setup(self):
        """Restart setup from beginning"""
        if messagebox.askyesno("Restart Setup", "Are you sure you want to restart the setup? All progress will be lost."):
            self.state = SetupState()
            self.state.started_at = datetime.now().isoformat()
            self._save_state()
            self._show_step(0)

    # ========================================================================
    # STEP IMPLEMENTATIONS
    # ========================================================================

    def _step_welcome(self):
        """Step 1: Welcome and resume check"""
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_dark'])
        frame.pack(fill=tk.BOTH, expand=True)

        # Welcome message
        title = tk.Label(
            frame,
            text="Welcome to Cognigrex",
            font=('Segoe UI', 32, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_dark']
        )
        title.pack(pady=(50, 20))

        subtitle = tk.Label(
            frame,
            text="Complete Z-Floor System Builder",
            font=('Segoe UI', 16),
            fg=self.colors['fg_secondary'],
            bg=self.colors['bg_dark']
        )
        subtitle.pack(pady=(0, 40))

        # Description
        desc = tk.Label(
            frame,
            text="""This wizard will guide you through the complete setup of your Cognigrex system.

You will configure:
- 4 User Profiles (Main User, IT, Achilles, Guest)
- 9 Z-Axis Floors with smart integration
- Dashboard widgets and floor colors
- Smart floor workflows and automation
- IT Portal with 21 management tabs
- 3D Immersive environment options

The setup can be paused and resumed at any time.""",
            font=('Segoe UI', 12),
            fg=self.colors['fg_text'],
            bg=self.colors['bg_dark'],
            justify=tk.CENTER
        )
        desc.pack(pady=20)

        # Show resume info if applicable
        if self.state.last_updated:
            resume_frame = tk.Frame(frame, bg=self.colors['bg_card'], padx=20, pady=15)
            resume_frame.pack(pady=30)

            resume_label = tk.Label(
                resume_frame,
                text=f"Previous setup found from {self.state.last_updated[:19]}",
                font=('Segoe UI', 11),
                fg=self.colors['warning'],
                bg=self.colors['bg_card']
            )
            resume_label.pack()

            resume_info = tk.Label(
                resume_frame,
                text=f"Step {self.state.current_step + 1} of {len(self.steps)} | Click 'Next Step' to continue or 'Restart Setup' to begin fresh",
                font=('Segoe UI', 10),
                fg=self.colors['fg_muted'],
                bg=self.colors['bg_card']
            )
            resume_info.pack(pady=(5, 0))

    def _step_main_user(self):
        """Step 2: Main User Setup"""
        self._build_user_form("main", "Main User", "Primary user with guided dashboard experience")

    def _step_it_user(self):
        """Step 3: IT User Setup"""
        self._build_user_form("it", "IT / Founder", "Full system access with IT Portal (21 tabs)")

    def _step_achilles(self):
        """Step 4: Achilles Setup"""
        self._build_user_form("achilles", "Achilles", "Voice assistant persona with AI orchestrator mode")

    def _step_guest(self):
        """Step 5: Guest Setup"""
        self._build_user_form("guest", "Guest", "Limited read-only access for demonstrations")

    def _build_user_form(self, role: str, title: str, description: str):
        """Build user configuration form"""
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_dark'])
        frame.pack(fill=tk.BOTH, expand=True)

        role_config = USER_ROLES[role]

        # Title
        header = tk.Label(
            frame,
            text=f"Configure {title}",
            font=('Segoe UI', 24, 'bold'),
            fg=role_config['color'],
            bg=self.colors['bg_dark']
        )
        header.pack(pady=(30, 10))

        desc = tk.Label(
            frame,
            text=description,
            font=('Segoe UI', 12),
            fg=self.colors['fg_muted'],
            bg=self.colors['bg_dark']
        )
        desc.pack(pady=(0, 30))

        # Form
        form_frame = tk.Frame(frame, bg=self.colors['bg_card'], padx=40, pady=30)
        form_frame.pack(fill=tk.X, padx=100)

        # Get existing data
        existing = self.state.users.get(role, {})

        # Username
        tk.Label(
            form_frame,
            text="Username:",
            font=('Segoe UI', 11),
            fg=self.colors['fg_text'],
            bg=self.colors['bg_card']
        ).grid(row=0, column=0, sticky='w', pady=10)

        username_var = tk.StringVar(value=existing.get('username', role.capitalize()))
        username_entry = tk.Entry(
            form_frame,
            textvariable=username_var,
            font=('Segoe UI', 11),
            width=40,
            bg=self.colors['bg_panel'],
            fg=self.colors['fg_text'],
            insertbackground=self.colors['fg_primary']
        )
        username_entry.grid(row=0, column=1, pady=10, padx=(20, 0))

        # Display Name
        tk.Label(
            form_frame,
            text="Display Name:",
            font=('Segoe UI', 11),
            fg=self.colors['fg_text'],
            bg=self.colors['bg_card']
        ).grid(row=1, column=0, sticky='w', pady=10)

        display_var = tk.StringVar(value=existing.get('display_name', role_config['display']))
        display_entry = tk.Entry(
            form_frame,
            textvariable=display_var,
            font=('Segoe UI', 11),
            width=40,
            bg=self.colors['bg_panel'],
            fg=self.colors['fg_text'],
            insertbackground=self.colors['fg_primary']
        )
        display_entry.grid(row=1, column=1, pady=10, padx=(20, 0))

        # Email (optional for guest)
        tk.Label(
            form_frame,
            text="Email:" + (" (optional)" if role == "guest" else ""),
            font=('Segoe UI', 11),
            fg=self.colors['fg_text'],
            bg=self.colors['bg_card']
        ).grid(row=2, column=0, sticky='w', pady=10)

        email_var = tk.StringVar(value=existing.get('email', ''))
        email_entry = tk.Entry(
            form_frame,
            textvariable=email_var,
            font=('Segoe UI', 11),
            width=40,
            bg=self.colors['bg_panel'],
            fg=self.colors['fg_text'],
            insertbackground=self.colors['fg_primary']
        )
        email_entry.grid(row=2, column=1, pady=10, padx=(20, 0))

        # Enabled checkbox
        enabled_var = tk.BooleanVar(value=existing.get('enabled', True))
        enabled_check = tk.Checkbutton(
            form_frame,
            text="Enable this user profile",
            variable=enabled_var,
            font=('Segoe UI', 11),
            fg=self.colors['fg_text'],
            bg=self.colors['bg_card'],
            selectcolor=self.colors['bg_panel'],
            activebackground=self.colors['bg_card'],
            activeforeground=self.colors['fg_text']
        )
        enabled_check.grid(row=3, column=0, columnspan=2, sticky='w', pady=20)

        # Features info
        features_frame = tk.Frame(frame, bg=self.colors['bg_panel'], padx=20, pady=15)
        features_frame.pack(fill=tk.X, padx=100, pady=20)

        tk.Label(
            features_frame,
            text="Features for this role:",
            font=('Segoe UI', 11, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_panel']
        ).pack(anchor='w')

        features_text = ", ".join(role_config['features'])
        tk.Label(
            features_frame,
            text=features_text,
            font=('Segoe UI', 10),
            fg=self.colors['fg_text'],
            bg=self.colors['bg_panel']
        ).pack(anchor='w', pady=(5, 0))

        # Floor access info
        access_text = "All floors" if "all" in role_config['floor_access'] else ", ".join(role_config['floor_access'])
        tk.Label(
            features_frame,
            text=f"Floor access: {access_text}",
            font=('Segoe UI', 10),
            fg=self.colors['fg_muted'],
            bg=self.colors['bg_panel']
        ).pack(anchor='w', pady=(5, 0))

        # Store vars for saving
        self.step_data = {
            'role': role,
            'username_var': username_var,
            'display_var': display_var,
            'email_var': email_var,
            'enabled_var': enabled_var
        }

        # Override next to save
        def save_and_next():
            self.state.users[role] = {
                'username': username_var.get(),
                'display_name': display_var.get(),
                'email': email_var.get(),
                'enabled': enabled_var.get(),
                'role': role,
                'clearance': role_config['clearance'],
                'color': role_config['color'],
                'features': role_config['features'],
                'floor_access': role_config['floor_access']
            }
            self._save_state()
            self._next_step()

        self.next_btn.configure(command=save_and_next)

    def _step_floor_discovery(self):
        """Step 6: Discover all Z-Floors"""
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_dark'])
        frame.pack(fill=tk.BOTH, expand=True)

        # Title
        tk.Label(
            frame,
            text="Z-Floor Discovery",
            font=('Segoe UI', 24, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_dark']
        ).pack(pady=(30, 10))

        tk.Label(
            frame,
            text="Scanning for Z-Axis floors and components...",
            font=('Segoe UI', 12),
            fg=self.colors['fg_muted'],
            bg=self.colors['bg_dark']
        ).pack(pady=(0, 30))

        # Floor list
        list_frame = tk.Frame(frame, bg=self.colors['bg_card'], padx=20, pady=20)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=100)

        # Discover floors
        discovered = []
        for floor_dir in Z_AXIS_ROOT.iterdir():
            if floor_dir.is_dir() and floor_dir.name in CANONICAL_FLOORS:
                floor_config = CANONICAL_FLOORS[floor_dir.name]

                # Count components
                components_dir = floor_dir / "components"
                component_count = len(list(components_dir.glob("*.py"))) if components_dir.exists() else 0

                # Check Z Direct
                z_direct = floor_dir / "Z Direct"
                has_z_direct = z_direct.exists()

                discovered.append({
                    'id': floor_dir.name,
                    'name': floor_config['name'],
                    'z_level': floor_config['z_level'],
                    'color': floor_config['color'],
                    'description': floor_config['description'],
                    'components': component_count,
                    'has_z_direct': has_z_direct,
                    'path': str(floor_dir)
                })

        # Sort by z_level descending
        discovered.sort(key=lambda x: x['z_level'], reverse=True)

        # Display floors
        for i, floor in enumerate(discovered):
            row_frame = tk.Frame(list_frame, bg=self.colors['bg_panel'])
            row_frame.pack(fill=tk.X, pady=3)

            # Color indicator
            color_bar = tk.Frame(row_frame, bg=floor['color'], width=4)
            color_bar.pack(side=tk.LEFT, fill=tk.Y)

            # Floor info
            info_frame = tk.Frame(row_frame, bg=self.colors['bg_panel'], padx=15, pady=10)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Name and level
            name_label = tk.Label(
                info_frame,
                text=f"Z{'+' if floor['z_level'] >= 0 else ''}{floor['z_level']} {floor['name']}",
                font=('Segoe UI', 12, 'bold'),
                fg=floor['color'],
                bg=self.colors['bg_panel']
            )
            name_label.pack(side=tk.LEFT)

            # Description
            desc_label = tk.Label(
                info_frame,
                text=f" - {floor['description']}",
                font=('Segoe UI', 11),
                fg=self.colors['fg_text'],
                bg=self.colors['bg_panel']
            )
            desc_label.pack(side=tk.LEFT)

            # Component count
            comp_label = tk.Label(
                info_frame,
                text=f"{floor['components']} components",
                font=('Segoe UI', 10),
                fg=self.colors['fg_muted'],
                bg=self.colors['bg_panel']
            )
            comp_label.pack(side=tk.RIGHT, padx=10)

            # Z Direct status
            zd_color = self.colors['success'] if floor['has_z_direct'] else self.colors['warning']
            zd_text = "Z Direct" if floor['has_z_direct'] else "No Z Direct"
            zd_label = tk.Label(
                info_frame,
                text=zd_text,
                font=('Segoe UI', 10),
                fg=zd_color,
                bg=self.colors['bg_panel']
            )
            zd_label.pack(side=tk.RIGHT, padx=10)

        # Update state
        self.state.floors_discovered = [f['id'] for f in discovered]
        self.state.components_total = sum(f['components'] for f in discovered)
        self._save_state()

        # Summary
        summary_frame = tk.Frame(frame, bg=self.colors['bg_panel'], padx=20, pady=15)
        summary_frame.pack(fill=tk.X, padx=100, pady=20)

        tk.Label(
            summary_frame,
            text=f"Discovered {len(discovered)} floors with {self.state.components_total} total components",
            font=('Segoe UI', 12, 'bold'),
            fg=self.colors['success'],
            bg=self.colors['bg_panel']
        ).pack()

    def _step_component_hook(self):
        """Step 7: Hook all components"""
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_dark'])
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame,
            text="Component Hooking",
            font=('Segoe UI', 24, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_dark']
        ).pack(pady=(30, 10))

        tk.Label(
            frame,
            text="Connecting floor components to Z Direct system...",
            font=('Segoe UI', 12),
            fg=self.colors['fg_muted'],
            bg=self.colors['bg_dark']
        ).pack(pady=(0, 30))

        # Progress area
        progress_frame = tk.Frame(frame, bg=self.colors['bg_card'], padx=40, pady=30)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=100)

        # Log area
        log_text = scrolledtext.ScrolledText(
            progress_frame,
            font=('Consolas', 10),
            bg=self.colors['bg_panel'],
            fg=self.colors['fg_text'],
            height=15,
            state=tk.DISABLED
        )
        log_text.pack(fill=tk.BOTH, expand=True)

        # Progress bar
        hook_progress = ttk.Progressbar(progress_frame, mode='determinate', length=600)
        hook_progress.pack(fill=tk.X, pady=(20, 10))

        status_label = tk.Label(
            progress_frame,
            text="Starting component hook...",
            font=('Segoe UI', 11),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_card']
        )
        status_label.pack()

        def add_log(msg: str, color: str = None):
            log_text.configure(state=tk.NORMAL)
            log_text.insert(tk.END, msg + "\n")
            log_text.see(tk.END)
            log_text.configure(state=tk.DISABLED)
            self.root.update()

        def hook_components():
            hooked = 0
            total = self.state.components_total

            for floor_id in self.state.floors_discovered:
                floor_dir = Z_AXIS_ROOT / floor_id
                components_dir = floor_dir / "components"
                z_direct = floor_dir / "Z Direct"

                add_log(f"\n[{floor_id}] Processing floor...")

                # Ensure Z Direct exists
                z_direct.mkdir(exist_ok=True)

                # Process components
                if components_dir.exists():
                    for comp_file in components_dir.glob("*.py"):
                        if comp_file.name.startswith("_"):
                            continue

                        comp_name = comp_file.stem
                        add_log(f"  Hooking {comp_name}...")

                        # Update floor manifest
                        manifest_file = z_direct / "floor_manifest.json"
                        try:
                            if manifest_file.exists():
                                with open(manifest_file, 'r') as f:
                                    manifest = json.load(f)
                            else:
                                manifest = {"floor": floor_id, "components": []}

                            # Add component if not exists
                            comp_entry = {
                                "id": comp_name,
                                "file": str(comp_file.relative_to(floor_dir)),
                                "hooked": True,
                                "hooked_at": datetime.now().isoformat()
                            }

                            existing_ids = [c.get('id') for c in manifest.get('components', [])]
                            if comp_name not in existing_ids:
                                manifest.setdefault('components', []).append(comp_entry)

                            with open(manifest_file, 'w') as f:
                                json.dump(manifest, f, indent=2)

                            hooked += 1

                        except Exception as e:
                            add_log(f"    Warning: {e}")

                        # Update progress
                        hook_progress['value'] = (hooked / max(total, 1)) * 100
                        status_label.configure(text=f"Hooked {hooked} / {total} components")
                        self.root.update()
                        time.sleep(0.05)  # Visual feedback

                # Store floor config
                self.state.floors_configured[floor_id] = {
                    "hooked": True,
                    "components": hooked,
                    "z_direct": str(z_direct)
                }

            self.state.components_hooked = hooked
            self._save_state()

            add_log(f"\n[COMPLETE] Hooked {hooked} components across {len(self.state.floors_discovered)} floors")
            status_label.configure(text=f"Component hooking complete! ({hooked} components)", fg=self.colors['success'])

        # Run hooking in thread
        thread = threading.Thread(target=hook_components, daemon=True)
        thread.start()

    def _step_floor_colors(self):
        """Step 8: Configure floor colors and themes"""
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_dark'])
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame,
            text="Floor Colors & Themes",
            font=('Segoe UI', 24, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_dark']
        ).pack(pady=(30, 10))

        tk.Label(
            frame,
            text="Configure the visual appearance of each Z-Floor",
            font=('Segoe UI', 12),
            fg=self.colors['fg_muted'],
            bg=self.colors['bg_dark']
        ).pack(pady=(0, 30))

        # Color grid
        grid_frame = tk.Frame(frame, bg=self.colors['bg_card'], padx=30, pady=20)
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=100)

        # Create visual floor display
        for i, floor_id in enumerate(self.state.floors_discovered):
            floor_config = CANONICAL_FLOORS.get(floor_id, {})
            color = floor_config.get('color', '#808080')
            name = floor_config.get('name', floor_id)
            z_level = floor_config.get('z_level', 0)

            # Floor card
            card = tk.Frame(grid_frame, bg=color, padx=3, pady=3)
            card.grid(row=i // 3, column=i % 3, padx=10, pady=10, sticky='nsew')

            inner = tk.Frame(card, bg=self.colors['bg_panel'], padx=15, pady=15)
            inner.pack(fill=tk.BOTH, expand=True)

            # Floor name
            tk.Label(
                inner,
                text=f"Z{'+' if z_level >= 0 else ''}{z_level}",
                font=('Segoe UI', 14, 'bold'),
                fg=color,
                bg=self.colors['bg_panel']
            ).pack()

            tk.Label(
                inner,
                text=name,
                font=('Segoe UI', 11),
                fg=self.colors['fg_text'],
                bg=self.colors['bg_panel']
            ).pack()

            # Color display
            tk.Label(
                inner,
                text=color,
                font=('Consolas', 9),
                fg=self.colors['fg_muted'],
                bg=self.colors['bg_panel']
            ).pack(pady=(5, 0))

        # Configure grid
        for i in range(3):
            grid_frame.columnconfigure(i, weight=1)

    def _step_widgets(self):
        """Step 9: Configure widgets"""
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_dark'])
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame,
            text="Widget Configuration",
            font=('Segoe UI', 24, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_dark']
        ).pack(pady=(30, 10))

        tk.Label(
            frame,
            text="Select widgets to enable on your dashboard",
            font=('Segoe UI', 12),
            fg=self.colors['fg_muted'],
            bg=self.colors['bg_dark']
        ).pack(pady=(0, 30))

        # Widget selection
        widget_frame = tk.Frame(frame, bg=self.colors['bg_card'], padx=30, pady=20)
        widget_frame.pack(fill=tk.BOTH, expand=True, padx=100)

        # Create scrollable list
        canvas = tk.Canvas(widget_frame, bg=self.colors['bg_card'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(widget_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.colors['bg_card'])

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Widget checkboxes
        widget_vars = {}
        categories = {}

        for widget_id, widget_info in WIDGET_CATALOG.items():
            cat = widget_info['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((widget_id, widget_info))

        row = 0
        for category, widgets in categories.items():
            # Category header
            tk.Label(
                scroll_frame,
                text=category.upper(),
                font=('Segoe UI', 10, 'bold'),
                fg=self.colors['fg_secondary'],
                bg=self.colors['bg_card']
            ).grid(row=row, column=0, columnspan=3, sticky='w', pady=(15, 5), padx=10)
            row += 1

            col = 0
            for widget_id, widget_info in widgets:
                var = tk.BooleanVar(value=True)
                widget_vars[widget_id] = var

                cb = tk.Checkbutton(
                    scroll_frame,
                    text=widget_info['name'],
                    variable=var,
                    font=('Segoe UI', 10),
                    fg=self.colors['fg_text'],
                    bg=self.colors['bg_card'],
                    selectcolor=self.colors['bg_panel'],
                    activebackground=self.colors['bg_card'],
                    activeforeground=self.colors['fg_text']
                )
                cb.grid(row=row, column=col, sticky='w', padx=10, pady=2)

                col += 1
                if col >= 3:
                    col = 0
                    row += 1

            if col != 0:
                row += 1

        # Store for saving
        self.step_data['widget_vars'] = widget_vars

        # Count enabled
        def count_widgets():
            return sum(1 for v in widget_vars.values() if v.get())

        count_label = tk.Label(
            frame,
            text=f"{count_widgets()} widgets selected",
            font=('Segoe UI', 11),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_dark']
        )
        count_label.pack(pady=10)

        # Override next to save
        def save_and_next():
            self.state.widgets_configured = count_widgets()
            self._save_state()
            self._next_step()

        self.next_btn.configure(command=save_and_next)

    def _step_smart_floor(self):
        """Step 10: Smart Floor Integration"""
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_dark'])
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame,
            text="Smart Floor Integration",
            font=('Segoe UI', 24, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_dark']
        ).pack(pady=(30, 10))

        tk.Label(
            frame,
            text="Configure intelligent floor workflows and automation",
            font=('Segoe UI', 12),
            fg=self.colors['fg_muted'],
            bg=self.colors['bg_dark']
        ).pack(pady=(0, 30))

        # Smart floor options
        options_frame = tk.Frame(frame, bg=self.colors['bg_card'], padx=40, pady=30)
        options_frame.pack(fill=tk.X, padx=100)

        smart_vars = {}

        options = [
            ("smart_floor_enabled", "Enable Smart Floor System", "Automatic file routing and floor coordination"),
            ("event_bus_enabled", "Enable Event Bus", "Inter-floor communication and events"),
            ("auto_ingestion", "Oracle Auto-Ingestion", "Automatically process and route incoming files"),
            ("smith_coordination", "Smith Inter-Floor Coordination", "Background job distribution across floors"),
            ("neo_ai_integration", "Neo AI Integration", "AI-powered suggestions and automation"),
            ("immersive_3d", "3D Immersive Environment", "Enable dome projection and spatial UI")
        ]

        for i, (key, title, desc) in enumerate(options):
            var = tk.BooleanVar(value=True)
            smart_vars[key] = var

            row_frame = tk.Frame(options_frame, bg=self.colors['bg_card'])
            row_frame.pack(fill=tk.X, pady=10)

            cb = tk.Checkbutton(
                row_frame,
                text=title,
                variable=var,
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['fg_primary'],
                bg=self.colors['bg_card'],
                selectcolor=self.colors['bg_panel'],
                activebackground=self.colors['bg_card'],
                activeforeground=self.colors['fg_primary']
            )
            cb.pack(anchor='w')

            tk.Label(
                row_frame,
                text=desc,
                font=('Segoe UI', 10),
                fg=self.colors['fg_muted'],
                bg=self.colors['bg_card']
            ).pack(anchor='w', padx=(25, 0))

        self.step_data['smart_vars'] = smart_vars

        # Override next to save
        def save_and_next():
            self.state.smart_floor_enabled = smart_vars['smart_floor_enabled'].get()
            self.state.event_bus_ready = smart_vars['event_bus_enabled'].get()
            self.state.immersive_3d_enabled = smart_vars['immersive_3d'].get()
            self._save_state()
            self._next_step()

        self.next_btn.configure(command=save_and_next)

    def _step_it_portal(self):
        """Step 11: IT Portal Configuration"""
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_dark'])
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame,
            text="IT Portal Configuration",
            font=('Segoe UI', 24, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_dark']
        ).pack(pady=(30, 10))

        tk.Label(
            frame,
            text="Configure the 21-tab IT Portal for system administration",
            font=('Segoe UI', 12),
            fg=self.colors['fg_muted'],
            bg=self.colors['bg_dark']
        ).pack(pady=(0, 30))

        # Portal tabs preview
        tabs_frame = tk.Frame(frame, bg=self.colors['bg_card'], padx=30, pady=20)
        tabs_frame.pack(fill=tk.BOTH, expand=True, padx=100)

        # IT Portal tabs
        it_tabs = [
            "Dashboard", "Users", "Floors", "Settings", "Performance",
            "Database", "Events", "Workflows", "Diagnostics", "Logs",
            "Backups", "Security", "AI Config", "Widgets", "Themes",
            "Imports", "Exports", "Scheduler", "Metrics", "API",
            "System"
        ]

        tk.Label(
            tabs_frame,
            text="IT Portal Tabs (21):",
            font=('Segoe UI', 12, 'bold'),
            fg=self.colors['fg_secondary'],
            bg=self.colors['bg_card']
        ).pack(anchor='w', pady=(0, 10))

        grid = tk.Frame(tabs_frame, bg=self.colors['bg_card'])
        grid.pack(fill=tk.X)

        for i, tab in enumerate(it_tabs):
            tab_btn = tk.Label(
                grid,
                text=tab,
                font=('Segoe UI', 10),
                fg=self.colors['fg_text'],
                bg=self.colors['bg_panel'],
                padx=15,
                pady=8
            )
            tab_btn.grid(row=i // 7, column=i % 7, padx=3, pady=3)

        # Access note
        note_frame = tk.Frame(frame, bg=self.colors['bg_panel'], padx=20, pady=15)
        note_frame.pack(fill=tk.X, padx=100, pady=20)

        tk.Label(
            note_frame,
            text="IT Portal Access",
            font=('Segoe UI', 11, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_panel']
        ).pack(anchor='w')

        tk.Label(
            note_frame,
            text="Only users with IT role (clearance 4) can access the full IT Portal.\nOther users will see a simplified dashboard with Z-axis floor tabs.",
            font=('Segoe UI', 10),
            fg=self.colors['fg_text'],
            bg=self.colors['bg_panel'],
            justify=tk.LEFT
        ).pack(anchor='w', pady=(5, 0))

        self.state.it_portal_configured = True
        self._save_state()

    def _step_complete(self):
        """Step 12: Setup Complete"""
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_dark'])
        frame.pack(fill=tk.BOTH, expand=True)

        # Success message
        tk.Label(
            frame,
            text="Setup Complete!",
            font=('Segoe UI', 32, 'bold'),
            fg=self.colors['success'],
            bg=self.colors['bg_dark']
        ).pack(pady=(50, 20))

        tk.Label(
            frame,
            text="Cognigrex is ready to launch",
            font=('Segoe UI', 16),
            fg=self.colors['fg_secondary'],
            bg=self.colors['bg_dark']
        ).pack(pady=(0, 40))

        # Summary
        summary_frame = tk.Frame(frame, bg=self.colors['bg_card'], padx=40, pady=30)
        summary_frame.pack(fill=tk.X, padx=150)

        summary_items = [
            (f"Users configured: {len(self.state.users)}", self.colors['fg_primary']),
            (f"Z-Floors discovered: {len(self.state.floors_discovered)}", self.colors['fg_primary']),
            (f"Components hooked: {self.state.components_hooked}", self.colors['fg_primary']),
            (f"Widgets enabled: {self.state.widgets_configured}", self.colors['fg_primary']),
            (f"Smart Floor: {'Enabled' if self.state.smart_floor_enabled else 'Disabled'}",
             self.colors['success'] if self.state.smart_floor_enabled else self.colors['warning']),
            (f"3D Immersive: {'Enabled' if self.state.immersive_3d_enabled else 'Disabled'}",
             self.colors['success'] if self.state.immersive_3d_enabled else self.colors['warning']),
            (f"IT Portal: {'Configured' if self.state.it_portal_configured else 'Not Configured'}",
             self.colors['success'] if self.state.it_portal_configured else self.colors['warning'])
        ]

        for text, color in summary_items:
            tk.Label(
                summary_frame,
                text=text,
                font=('Segoe UI', 12),
                fg=color,
                bg=self.colors['bg_card']
            ).pack(anchor='w', pady=3)

        # Next actions (operator approval gate lives in Trinity IT Portal).
        actions_frame = tk.Frame(frame, bg=self.colors['bg_panel'], padx=40, pady=24)
        actions_frame.pack(fill=tk.X, padx=150, pady=(24, 0))

        tk.Label(
            actions_frame,
            text="Next Actions",
            font=('Segoe UI', 12, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_panel'],
        ).pack(anchor='w')

        tk.Label(
            actions_frame,
            text=(
                "Stage V1R definitions to Z Direct (append-only), then review/commit via IT Portal.\n"
                "Tailoring reset only clears user preferences (does not delete vault/registries)."
            ),
            font=('Segoe UI', 10),
            fg=self.colors['fg_text'],
            bg=self.colors['bg_panel'],
            justify=tk.LEFT,
        ).pack(anchor='w', pady=(6, 14))

        btn_row = tk.Frame(actions_frame, bg=self.colors['bg_panel'])
        btn_row.pack(fill=tk.X)

        tk.Button(
            btn_row,
            text="Stage V1R Definitions (Z Direct)",
            command=self._stage_v1r_definitions,
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg_text'],
            bg=self.colors['fg_secondary'],
            relief='flat',
            padx=14,
            pady=8,
        ).pack(side='left', padx=(0, 10))

        tk.Button(
            btn_row,
            text="Open IT Portal (Commit Review)",
            command=self._open_it_portal_host,
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg_text'],
            bg=self.colors['bg_card'],
            relief='flat',
            padx=14,
            pady=8,
        ).pack(side='left', padx=(0, 10))

        tk.Button(
            btn_row,
            text="Reset Tailoring (Active User)",
            command=self._reset_active_user_tailoring,
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg_text'],
            bg=self.colors['bg_card'],
            relief='flat',
            padx=14,
            pady=8,
        ).pack(side='left')

        # Mark complete
        self.state.completed = True
        self._save_state()

        # Write final config
        self._write_final_config()

        # Update next button
        self.next_btn.configure(text="Launch Cognigrex", command=self._launch_cognigrex)

    def _write_final_config(self):
        """Write final configuration files"""
        # Update user_config.json
        user_config_file = CONFIG_ROOT / "user_config.json"

        try:
            if user_config_file.exists():
                with open(user_config_file, 'r') as f:
                    config = json.load(f)
            else:
                config = {}

            # Add/update users section
            config['users'] = self.state.users
            config['active_user'] = self.state.active_user or 'main'
            config['setup_completed'] = True
            config['setup_date'] = datetime.now().isoformat()
            config['version'] = self.state.version

            # Floor config
            config['floors'] = {
                'floor_loader_enabled': True,
                'enabled_floors': self.state.floors_discovered,
                'total_floors': len(self.state.floors_discovered),
                'total_components': self.state.components_hooked
            }

            # Features
            config['features'] = {
                'smart_floor': self.state.smart_floor_enabled,
                'event_bus': self.state.event_bus_ready,
                'immersive_3d': self.state.immersive_3d_enabled,
                'it_portal': self.state.it_portal_configured,
                'widgets_count': self.state.widgets_configured
            }

            with open(user_config_file, 'w') as f:
                json.dump(config, f, indent=2)

            # Create initialized marker
            init_marker = CONFIG_ROOT / ".initialized"
            init_marker.write_text(datetime.now().isoformat())

            # -----------------------------------------------------------------
            # Explicit setup actions (DB schema + seed users/company)
            # -----------------------------------------------------------------
            # This is the consolidated Trinity-owned setup flow; it is allowed to
            # apply migrations and seed initial records.
            db_report: Optional[Dict[str, Any]] = None
            try:
                init_script = LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "tools" / "initialize_database.py"
                if init_script.exists():
                    mod_name = f"lightspeed_dynamic_dbinit_{abs(hash(str(init_script)))}"
                    spec = importlib.util.spec_from_file_location(mod_name, init_script)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)  # type: ignore[union-attr]
                        fn = getattr(mod, "initialize_database", None)
                        if callable(fn):
                            db_report = fn(quiet=True)
                            try:
                                self.state.database_initialized = bool((db_report or {}).get("ok"))
                            except Exception:
                                pass
            except Exception as e:
                print(f"Warning: DB initialization skipped: {e}")

            try:
                # Resolve DB path deterministically (prefer initializer output).
                db_path = None
                if isinstance(db_report, dict):
                    p = db_report.get("db_path")
                    if p:
                        db_path = Path(str(p))
                if db_path is None:
                    db_path = (
                        LIGHTSPEED_ROOT
                        / "Z Axis"
                        / "Z-4_Merovingian"
                        / "data"
                        / "db"
                        / "lightspeed_unified.db"
                    )
                db_path = Path(db_path)
                db_path.parent.mkdir(parents=True, exist_ok=True)

                conn = sqlite3.connect(str(db_path))
                cur = conn.cursor()

                # Ensure at least one company exists.
                cur.execute("SELECT id FROM companies LIMIT 1")
                row = cur.fetchone()
                if row and row[0] is not None:
                    company_id = int(row[0])
                else:
                    now = datetime.now().isoformat()
                    cur.execute(
                        "INSERT INTO companies (name, industry, created_at, updated_at) VALUES (?, ?, ?, ?)",
                        ("Romer Industries", "General", now, now),
                    )
                    company_id = int(cur.lastrowid or 1)

                # Upsert configured users (password-less by design; username + clearance are authoritative).
                now = datetime.now().isoformat()
                for _role, u in (self.state.users or {}).items():
                    if not isinstance(u, dict):
                        continue
                    if not bool(u.get("enabled", True)):
                        continue
                    username = str(u.get("username") or "").strip()
                    if not username:
                        continue
                    fullname = str(u.get("display_name") or u.get("fullname") or username).strip()
                    email = str(u.get("email") or "").strip()
                    role_name = str(u.get("role") or "user").strip()
                    clearance = int(u.get("clearance") or 1)

                    cur.execute("SELECT id FROM users WHERE username = ? LIMIT 1", (username,))
                    urow = cur.fetchone()
                    if urow and urow[0] is not None:
                        uid = int(urow[0])
                        cur.execute(
                            "UPDATE users SET fullname=?, email=?, role=?, clearance=?, updated_at=? WHERE id=?",
                            (fullname, email, role_name, clearance, now, uid),
                        )
                    else:
                        cur.execute(
                            "INSERT INTO users (username, fullname, email, role, clearance, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (username, fullname, email, role_name, clearance, now, now),
                        )

                conn.commit()
                conn.close()

                # Record in state for downstream UIs (best-effort; informational only).
                self.state.database_initialized = True
                self._save_state()
            except Exception as e:
                print(f"Warning: Could not seed DB: {e}")

        except Exception as e:
            print(f"Warning: Could not write final config: {e}")

    def _launch_cognigrex(self):
        """Launch the main Cognigrex application"""
        try:
            self.root.destroy()
        except Exception:
            pass

        # Embedded: do not spawn a new process. Signal completion back to caller if requested.
        if not getattr(self, "standalone", True):
            try:
                if callable(getattr(self, "_on_complete", None)):
                    payload: Dict[str, Any] = {"setup_state": asdict(self.state)}
                    # Compatibility: older callers expect `{"user": {"username": ...}}` to prefill login fields.
                    try:
                        users = self.state.users or {}
                        active = (self.state.active_user or "").strip() or "main"
                        u = None
                        if isinstance(users, dict):
                            u = users.get(active) or users.get("main")
                            if u is None and users:
                                u = next(iter(users.values()), None)
                        if isinstance(u, dict):
                            payload["user"] = {
                                "username": u.get("username"),
                                "fullname": u.get("display_name") or u.get("fullname"),
                                "role": u.get("role"),
                                "clearance": u.get("clearance"),
                            }
                    except Exception:
                        pass
                    self._on_complete(payload)
            except Exception:
                pass
            return

        # Launch N.py with GUI
        import subprocess
        n_py = LIGHTSPEED_ROOT / "N.py"
        if n_py.exists():
            subprocess.Popen([sys.executable, str(n_py), "--gui"], cwd=str(LIGHTSPEED_ROOT))
        else:
            # Fallback to __main__.py
            subprocess.Popen([sys.executable, "-m", "LightSpeed"], cwd=str(LIGHTSPEED_ROOT))

    def run(self):
        """Run the wizard"""
        self.root.mainloop()


# ============================================================================
# ENTRY POINT
# ============================================================================

def launch_setup_wizard(parent: Optional[tk.Tk] = None, on_complete: Optional[Callable[[Dict[str, Any]], None]] = None) -> CognigrexSetupWizard:
    """Launch the Cognigrex Setup Wizard"""
    wizard = CognigrexSetupWizard(parent, on_complete=on_complete)
    return wizard


if __name__ == "__main__":
    wizard = launch_setup_wizard()
    wizard.run()
