"""
Architect Operator Portal - Glassmorphism UI Interface
Architect Floor Component

Modern glassmorphism-themed UI portal for Architect orchestration and publish
governance. Provides intuitive interface for floor-specific workflow control
with consistent LightSpeed aesthetic.

NOTE (Codex 2026-02-03): Added a read-only "Z Direct" tab for local stream/registry browsing.
Trinity remains the commit/approval gate for durable registry writes.

Floor: Architect
Z-Level: 1
Author: LightSpeed Team
Version: 0.9.5
Date: 2026-01-12
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
import json
import sys
import importlib.util
import sqlite3
from datetime import datetime
import threading


def _find_lightspeed_root() -> Path:
    """
    Locate LightSpeed root directory by searching for N.py

    Returns:
        Path to LightSpeed root directory
    """
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
            return candidate
    # Fallback: assume 3 levels up
    return here.parents[3]


# Configure paths
LIGHTSPEED_ROOT = _find_lightspeed_root()
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"

# Add to sys.path if not already present
for path in [LIGHTSPEED_ROOT, Z_AXIS_ROOT]:
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Import Merovingian core services
_MEROV = Z_AXIS_ROOT / "Z-4_Merovingian"
if _MEROV.exists() and str(_MEROV) not in sys.path:
    sys.path.insert(0, str(_MEROV))

# Import glass UI framework
try:
    from core.ui.glass_ui import GlassFrame
    HAS_GLASS_UI = True
except ImportError:
    HAS_GLASS_UI = False
    print("Warning: GlassFrame not available, using standard frames")


@dataclass
class PortalTheme:
    """Portal glassmorphism theme configuration"""
    bg_primary: str = '#1e1e1e'
    bg_secondary: str = '#2a2a2a'
    bg_glass: str = '#2a2a2a'  # Tk-safe (alpha not supported)
    fg_primary: str = '#00DDFF'  # Cyan
    fg_secondary: str = '#FF00FF'  # Magenta
    fg_text: str = '#FFFFFF'
    fg_muted: str = '#888888'
    accent_success: str = '#00FF88'
    accent_warning: str = '#FFAA00'
    accent_error: str = '#FF4444'
    border_color: str = '#00DDFF'
    border_width: int = 1
    border_radius: int = 10
    font_family: str = 'Segoe UI'
    font_size_normal: int = 10
    font_size_header: int = 14
    font_size_title: int = 18


class ArchitectPortalGlass:
    """
    Architect operator portal with glassmorphism UI

    Features:
    - Modern glass-themed interface
    - Floor-specific workflow and governance tools
    - Real-time status monitoring
    - Event bus integration
    - Cross-floor communication

    Sections:
    1. Signals - Floor status and metrics
    2. Workflows - Floor-specific operations
    3. Governance - Configuration and preferences
    4. Z Direct - read-only streams + durable registry viewer
    """

    def __init__(self, parent: Optional[tk.Tk] = None):
        """
        Initialize Architect Portal

        Parameters:
            parent: Parent Tk window (creates standalone if None)
        """
        # Create window
        if parent is None:
            self.root = tk.Tk()
            self.standalone = True
        else:
            self.root = tk.Toplevel(parent)
            self.standalone = False

        # Window configuration
        self.root.title("Architect Operator Portal - LightSpeed V0.9.5")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e1e')

        # Theme
        self.theme = PortalTheme()

        # State
        self.active_section = None
        self.components: Dict[str, Any] = {}
        self.status_indicators: Dict[str, tk.Label] = {}

        # Paths
        self.lightspeed_root = LIGHTSPEED_ROOT
        self.floor_dir = Z_AXIS_ROOT / "Z+1_Architect"
        self.config_dir = self.floor_dir / "config"
        self.data_dir = self.floor_dir / "data"

        # Load configuration
        self.config = self._load_config()

        # Build UI
        self._build_ui()

        # Initialize components
        self._initialize_components()

        # Start auto-refresh if enabled
        if self.config.get('auto_refresh', False):
            self._start_auto_refresh()

    def _load_config(self) -> Dict[str, Any]:
        """Load portal configuration from file"""
        config_file = self.config_dir / "portal_config.json"

        default_config = {
            'auto_refresh': True,
            'refresh_interval_ms': 5000,
            'show_metrics': True,
            'log_events': True,
            'theme': 'dark'
        }

        if not config_file.exists():
            return default_config

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return {**default_config, **json.load(f)}
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")
            return default_config

    def _build_ui(self):
        """Build complete UI structure"""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.theme.bg_primary)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header
        self._build_header(main_frame)

        # Content area (tabs/sections)
        self._build_content_area(main_frame)

        # Status bar
        self._build_status_bar(main_frame)

    def _build_header(self, parent: tk.Frame):
        """Build header section with title and controls"""
        if HAS_GLASS_UI:
            header_frame = GlassFrame(parent)
        else:
            header_frame = tk.Frame(parent, bg=self.theme.bg_secondary)

        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Title
        title = tk.Label(
            header_frame,
            text=f"⚡ Architect Operator Portal",
            font=(self.theme.font_family, self.theme.font_size_title, 'bold'),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary
        )
        title.pack(side=tk.LEFT, padx=20, pady=15)

        # Subtitle
        subtitle = tk.Label(
            header_frame,
            text=f"Z-Level 1 | Project orchestration and publish governance",
            font=(self.theme.font_family, self.theme.font_size_normal),
            fg=self.theme.fg_muted,
            bg=self.theme.bg_secondary
        )
        subtitle.pack(side=tk.LEFT, padx=10, pady=15)

        # Controls (right side)
        controls_frame = tk.Frame(header_frame, bg=self.theme.bg_secondary)
        controls_frame.pack(side=tk.RIGHT, padx=20)

        # Refresh button
        refresh_btn = tk.Button(
            controls_frame,
            text="↻ Refresh",
            command=self.refresh_status,
            bg=self.theme.bg_glass,
            fg=self.theme.fg_primary,
            font=(self.theme.font_family, self.theme.font_size_normal),
            relief=tk.FLAT,
            padx=15,
            pady=5
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        # Governance button
        settings_btn = tk.Button(
            controls_frame,
            text="⚙ Governance",
            command=self.open_settings,
            bg=self.theme.bg_glass,
            fg=self.theme.fg_primary,
            font=(self.theme.font_family, self.theme.font_size_normal),
            relief=tk.FLAT,
            padx=15,
            pady=5
        )
        settings_btn.pack(side=tk.LEFT, padx=5)

    def _build_content_area(self, parent: tk.Frame):
        """Build main content area with sections/tabs"""
        # Create notebook for sections
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'Glass.TNotebook',
            background=self.theme.bg_secondary,
            borderwidth=0
        )
        style.configure(
            'Glass.TNotebook.Tab',
            background=self.theme.bg_secondary,
            foreground=self.theme.fg_text,
            padding=[20, 10],
            font=(self.theme.font_family, self.theme.font_size_normal)
        )

        self.notebook = ttk.Notebook(parent, style='Glass.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Build individual sections
        self._build_section_1()
        self._build_section_2()
        self._build_section_3()
        self._build_section_z_direct()

    def _build_section_1(self):
        """Build first section: Signals"""
        if HAS_GLASS_UI:
            section = GlassFrame(self.notebook)
        else:
            section = tk.Frame(self.notebook, bg=self.theme.bg_secondary)

        self.notebook.add(section, text="Signals")

        # Section content
        label = tk.Label(
            section,
            text="Signals",
            font=(self.theme.font_family, self.theme.font_size_header),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary
        )
        label.pack(pady=20)

        # Metrics
        metrics = tk.Frame(section, bg=self.theme.bg_secondary)
        metrics.pack(fill="x", padx=20, pady=(0, 10))

        def metric_row(title_text: str, value_attr: str):
            row = tk.Frame(metrics, bg=self.theme.bg_secondary)
            row.pack(fill="x", pady=4)
            tk.Label(
                row,
                text=title_text,
                font=(self.theme.font_family, self.theme.font_size_normal),
                fg=self.theme.fg_muted,
                bg=self.theme.bg_secondary,
            ).pack(side="left")
            value = tk.Label(
                row,
                text="…",
                font=(self.theme.font_family, self.theme.font_size_normal, "bold"),
                fg=self.theme.fg_primary,
                bg=self.theme.bg_secondary,
            )
            value.pack(side="right")
            setattr(self, value_attr, value)

        metric_row("Schema status", "metric_schema")
        metric_row("Projects", "metric_projects")
        metric_row("Tasks (pending)", "metric_tasks_pending")
        metric_row("Tasks (in progress)", "metric_tasks_in_progress")

        # Quick actions
        actions = tk.Frame(section, bg=self.theme.bg_secondary)
        actions.pack(fill="x", padx=20, pady=(10, 10))
        tk.Label(
            actions,
            text="Quick Actions",
            font=(self.theme.font_family, self.theme.font_size_header, "bold"),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary,
        ).pack(anchor="w", pady=(0, 6))

        btns = tk.Frame(actions, bg=self.theme.bg_secondary)
        btns.pack(fill="x")

        tk.Button(
            btns,
            text="Open Operator Portal",
            command=self._open_it_portal,
            bg=self.theme.bg_glass,
            fg=self.theme.fg_text,
            relief=tk.FLAT,
            padx=12,
            pady=6,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            btns,
            text="Open Governance Hub",
            command=self.open_settings,
            bg=self.theme.bg_glass,
            fg=self.theme.fg_text,
            relief=tk.FLAT,
            padx=12,
            pady=6,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            btns,
            text="Refresh Metrics",
            command=self._refresh_overview_metrics,
            bg=self.theme.bg_glass,
            fg=self.theme.fg_text,
            relief=tk.FLAT,
            padx=12,
            pady=6,
        ).pack(side="left")

        self._refresh_overview_metrics()

    def _build_section_2(self):
        """Build second section: Workflows"""
        if HAS_GLASS_UI:
            section = GlassFrame(self.notebook)
        else:
            section = tk.Frame(self.notebook, bg=self.theme.bg_secondary)

        self.notebook.add(section, text="Workflows")

        # Section content
        label = tk.Label(
            section,
            text="Workflows",
            font=(self.theme.font_family, self.theme.font_size_header),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary
        )
        label.pack(pady=20)

        body = tk.Frame(section, bg=self.theme.bg_secondary)
        body.pack(fill="both", expand=True, padx=20, pady=10)

        tk.Label(
            body,
            text="Create Task (Architect)",
            font=(self.theme.font_family, self.theme.font_size_header, "bold"),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary,
        ).pack(anchor="w", pady=(0, 8))

        form = tk.Frame(body, bg=self.theme.bg_secondary)
        form.pack(fill="x")

        tk.Label(form, text="Title", fg=self.theme.fg_muted, bg=self.theme.bg_secondary).grid(row=0, column=0, sticky="w", pady=6)
        self.var_task_title = tk.StringVar(value="")
        ttk.Entry(form, textvariable=self.var_task_title).grid(row=0, column=1, sticky="ew", pady=6)

        tk.Label(form, text="Priority", fg=self.theme.fg_muted, bg=self.theme.bg_secondary).grid(row=1, column=0, sticky="w", pady=6)
        self.var_task_priority = tk.StringVar(value="medium")
        ttk.Combobox(form, textvariable=self.var_task_priority, state="readonly", values=["low", "medium", "high", "critical"]).grid(
            row=1, column=1, sticky="w", pady=6
        )

        tk.Label(form, text="Description", fg=self.theme.fg_muted, bg=self.theme.bg_secondary).grid(row=2, column=0, sticky="nw", pady=6)
        self.txt_task_desc = scrolledtext.ScrolledText(form, height=6, wrap=tk.WORD)
        self.txt_task_desc.grid(row=2, column=1, sticky="ew", pady=6)

        form.columnconfigure(1, weight=1)

        tk.Button(
            body,
            text="Create Task",
            command=self._create_task_action,
            bg=self.theme.bg_glass,
            fg=self.theme.fg_text,
            relief=tk.FLAT,
            padx=12,
            pady=6,
        ).pack(anchor="w", pady=(10, 0))

        tk.Label(
            body,
            text="Tip: If the schema needs an update, open Operator Portal -> Database -> Update Schema.",
            fg=self.theme.fg_muted,
            bg=self.theme.bg_secondary,
            font=(self.theme.font_family, 9),
        ).pack(anchor="w", pady=(8, 0))

    def _build_section_3(self):
        """Build third section: Governance"""
        if HAS_GLASS_UI:
            section = GlassFrame(self.notebook)
        else:
            section = tk.Frame(self.notebook, bg=self.theme.bg_secondary)

        self.notebook.add(section, text="Governance")

        # Section content
        label = tk.Label(
            section,
            text="Governance",
            font=(self.theme.font_family, self.theme.font_size_header),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary
        )
        label.pack(pady=20)

        body = tk.Frame(section, bg=self.theme.bg_secondary)
        body.pack(fill="both", expand=True, padx=20, pady=10)

        tk.Label(
            body,
            text="Governance Settings",
            font=(self.theme.font_family, self.theme.font_size_header, "bold"),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary,
        ).pack(anchor="w", pady=(0, 8))

        self.var_auto_refresh = tk.BooleanVar(value=bool(self.config.get("auto_refresh", True)))
        ttk.Checkbutton(body, text="Auto-refresh", variable=self.var_auto_refresh).pack(anchor="w", pady=4)

        ttk.Button(body, text="Save Governance Config", command=self._save_portal_config).pack(anchor="w", pady=(10, 0))
        ttk.Button(body, text="Open Trinity Governance Hub", command=self.open_settings).pack(anchor="w", pady=6)

    def _build_section_z_direct(self):
        """Build read-only Z Direct viewer for this floor (streams + durable registries)."""
        if HAS_GLASS_UI:
            section = GlassFrame(self.notebook)
        else:
            section = tk.Frame(self.notebook, bg=self.theme.bg_secondary)

        self.notebook.add(section, text="Z Direct")

        label = tk.Label(
            section,
            text="Architect Z Direct (read-only)",
            font=(self.theme.font_family, self.theme.font_size_header),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary,
        )
        label.pack(pady=16)

        body = tk.Frame(section, bg=self.theme.bg_secondary)
        body.pack(fill="both", expand=True, padx=20, pady=10)

        zd = self.components.get("z_direct")
        if zd is None:
            tk.Label(
                body,
                text="Z Direct service unavailable (core.services.get_z_direct).",
                font=(self.theme.font_family, self.theme.font_size_normal),
                fg=self.theme.fg_muted,
                bg=self.theme.bg_secondary,
            ).pack(anchor="w")
            return

        channel = "Z+1"

        actions = tk.Frame(body, bg=self.theme.bg_secondary)
        actions.pack(fill="x", pady=(0, 10))

        def open_z_direct_folder():
            try:
                zdir = (self.floor_dir / "Z Direct").resolve()
                if zdir.exists():
                    os.startfile(str(zdir))  # type: ignore[attr-defined]
            except Exception as e:
                messagebox.showerror("Z Direct", f"Failed to open folder:\n{e}", parent=self.root)

        state: Dict[str, Any] = {"objects": [], "events": [], "registry": []}

        payload_kind_var = tk.StringVar(value="objects")
        limit_var = tk.IntVar(value=200)
        registry_var = tk.StringVar(value="objects")

        tk.Label(actions, text="Tail:", fg=self.theme.fg_text, bg=self.theme.bg_secondary).pack(side="left")
        ttk.Combobox(
            actions,
            textvariable=payload_kind_var,
            values=["objects", "events"],
            state="readonly",
            width=10,
        ).pack(side="left", padx=(6, 10))
        tk.Label(actions, text="Limit:", fg=self.theme.fg_text, bg=self.theme.bg_secondary).pack(side="left")
        ttk.Spinbox(actions, from_=50, to=2000, textvariable=limit_var, width=6).pack(side="left", padx=(6, 10))
        tk.Button(actions, text="Open Folder", command=open_z_direct_folder).pack(side="right")

        def refresh():
            try:
                mode = payload_kind_var.get()
                lim = int(limit_var.get() or 200)
                if mode == "events":
                    state["events"] = zd.tail_events(channel, limit=lim) or []
                    state["objects"] = []
                else:
                    state["objects"] = zd.tail_objects(channel, limit=lim) or []
                    state["events"] = []

                reg_name = registry_var.get() or "objects"
                state["registry"] = zd.read_registry(channel, name=reg_name) or []

                populate_lists()
            except Exception as e:
                messagebox.showerror("Z Direct", f"Refresh failed:\n{e}", parent=self.root)

        def _extract_path(obj: Any) -> Optional[str]:
            try:
                if not isinstance(obj, dict):
                    return None
                for k in ("path", "vault_path", "file_path", "source_path"):
                    v = obj.get(k)
                    if isinstance(v, str) and v.strip():
                        return v
                payload = obj.get("payload")
                if isinstance(payload, dict):
                    for k in ("path", "vault_path", "file_path", "source_path"):
                        v = payload.get(k)
                        if isinstance(v, str) and v.strip():
                            return v
            except Exception:
                pass
            return None

        def open_selected_path():
            try:
                envs = state.get("events") or state.get("objects") or []
                item = None
                sel = stream_list.curselection()
                if sel and envs:
                    item = envs[int(sel[0])]
                else:
                    rsel = registry_list.curselection()
                    reg = state.get("registry") or []
                    if rsel and reg:
                        item = reg[int(rsel[0])]

                p = _extract_path(item)
                if not p:
                    messagebox.showinfo("Z Direct", "No path found on the selected item.", parent=self.root)
                    return
                path = Path(p).expanduser()
                if not path.exists():
                    messagebox.showwarning("Z Direct", f"Path not found:\n{path}", parent=self.root)
                    return
                os.startfile(str(path))  # type: ignore[attr-defined]
            except Exception as e:
                messagebox.showerror("Z Direct", f"Open path failed:\n{e}", parent=self.root)

        tk.Button(actions, text="Refresh", command=refresh).pack(side="right", padx=(0, 8))
        tk.Button(actions, text="Open Path", command=open_selected_path).pack(side="right", padx=(0, 8))

        panes = tk.PanedWindow(body, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, bg=self.theme.bg_secondary)
        panes.pack(fill="both", expand=True)

        left = tk.Frame(panes, bg=self.theme.bg_secondary)
        right = tk.Frame(panes, bg=self.theme.bg_secondary)
        panes.add(left, stretch="always")
        panes.add(right, stretch="always")

        tk.Label(
            left,
            text="Stream Tail",
            font=(self.theme.font_family, self.theme.font_size_normal, "bold"),
            fg=self.theme.fg_text,
            bg=self.theme.bg_secondary,
        ).pack(anchor="w")

        stream_list = tk.Listbox(left, height=18, bg=self.theme.bg_primary, fg=self.theme.fg_text, activestyle="none")
        stream_list.pack(fill="both", expand=True, pady=(6, 10))

        reg_hdr = tk.Frame(left, bg=self.theme.bg_secondary)
        reg_hdr.pack(fill="x")
        tk.Label(
            reg_hdr,
            text="Registry:",
            font=(self.theme.font_family, self.theme.font_size_normal, "bold"),
            fg=self.theme.fg_text,
            bg=self.theme.bg_secondary,
        ).pack(side="left")
        ttk.Combobox(
            reg_hdr,
            textvariable=registry_var,
            values=["objects", "tasks"],
            state="readonly",
            width=10,
        ).pack(side="left", padx=(6, 10))
        tk.Button(reg_hdr, text="Load Registry", command=refresh).pack(side="right")

        registry_list = tk.Listbox(left, height=10, bg=self.theme.bg_primary, fg=self.theme.fg_text, activestyle="none")
        registry_list.pack(fill="both", expand=False, pady=(6, 0))

        tk.Label(
            right,
            text="Selected JSON",
            font=(self.theme.font_family, self.theme.font_size_normal, "bold"),
            fg=self.theme.fg_text,
            bg=self.theme.bg_secondary,
        ).pack(anchor="w")

        detail = scrolledtext.ScrolledText(
            right,
            wrap=tk.NONE,
            height=28,
            bg=self.theme.bg_primary,
            fg=self.theme.fg_text,
            insertbackground=self.theme.fg_text,
        )
        detail.pack(fill="both", expand=True, pady=(6, 0))

        def _format_env(env: Dict[str, Any]) -> str:
            created = str(env.get("created_at") or "")
            kind = str(env.get("kind") or "")
            payload = env.get("payload") if isinstance(env, dict) else None
            if isinstance(payload, dict) and kind == "object":
                pk = payload.get("kind")
                pid = payload.get("id")
                if pk is not None and pid is not None:
                    return f"{created} object {pk}:{pid}"
            if isinstance(payload, dict) and kind == "event":
                action = payload.get("action") or payload.get("type") or "event"
                return f"{created} event {action}"
            return f"{created} {kind}".strip()

        def _format_item(item: Dict[str, Any]) -> str:
            if not isinstance(item, dict):
                return "item"
            k = item.get("kind")
            i = item.get("id")
            if k is not None and i is not None:
                return f"{k}:{i}"
            return str(k or "item")

        def populate_lists():
            stream_list.delete(0, tk.END)
            envs = state.get("events") or state.get("objects") or []
            for env in envs:
                if isinstance(env, dict):
                    stream_list.insert(tk.END, _format_env(env))

            registry_list.delete(0, tk.END)
            for item in state.get("registry") or []:
                if isinstance(item, dict):
                    registry_list.insert(tk.END, _format_item(item))

            detail.delete("1.0", tk.END)

        def show_stream_selected(_evt=None):
            try:
                sel = stream_list.curselection()
                if not sel:
                    return
                idx = int(sel[0])
                envs = state.get("events") or state.get("objects") or []
                env = envs[idx]
                detail.delete("1.0", tk.END)
                detail.insert(tk.END, json.dumps(env, indent=2, ensure_ascii=False))
            except Exception:
                pass

        def show_registry_selected(_evt=None):
            try:
                sel = registry_list.curselection()
                if not sel:
                    return
                idx = int(sel[0])
                items = state.get("registry") or []
                item = items[idx]
                detail.delete("1.0", tk.END)
                detail.insert(tk.END, json.dumps(item, indent=2, ensure_ascii=False))
            except Exception:
                pass

        stream_list.bind("<<ListboxSelect>>", show_stream_selected)
        registry_list.bind("<<ListboxSelect>>", show_registry_selected)

        refresh()

    def _build_status_bar(self, parent: tk.Frame):
        """Build status bar at bottom"""
        status_frame = tk.Frame(parent, bg=self.theme.bg_secondary, height=40)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)

        # Status indicator
        self.status_label = tk.Label(
            status_frame,
            text="● Ready",
            font=(self.theme.font_family, self.theme.font_size_normal),
            fg=self.theme.accent_success,
            bg=self.theme.bg_secondary
        )
        self.status_label.pack(side=tk.LEFT, padx=20)

        # Component count
        self.component_count_label = tk.Label(
            status_frame,
            text="Components: 0",
            font=(self.theme.font_family, self.theme.font_size_normal),
            fg=self.theme.fg_muted,
            bg=self.theme.bg_secondary
        )
        self.component_count_label.pack(side=tk.LEFT, padx=20)

        # Floor info
        floor_info = tk.Label(
            status_frame,
            text=f"Floor: Architect | Z-Level: 1",
            font=(self.theme.font_family, self.theme.font_size_normal),
            fg=self.theme.fg_muted,
            bg=self.theme.bg_secondary
        )
        floor_info.pack(side=tk.RIGHT, padx=20)

    def _initialize_components(self):
        """Initialize floor components"""
        try:
            self.update_status("Initializing components...", "warning")
            # Architect stays light: gather DB status + expose cross-floor launchers.
            self.components["db_path"] = str(self._db_path())
            self.components["schema_ok"] = self._schema_ok()
            # Read-only: Architect can browse Z Direct streams/registries, but Trinity owns commits.
            try:
                from core.services import get_z_direct  # type: ignore

                self.components["z_direct"] = get_z_direct()
            except Exception:
                self.components["z_direct"] = None
            self.update_status("Ready", "success")
            self._update_component_count()

        except Exception as e:
            self.update_status(f"Initialization error: {e}", "error")
            print(f"Error initializing components: {e}")

    def refresh_status(self):
        """Refresh all status indicators and metrics"""
        try:
            self.update_status("Refreshing...", "warning")

            # Refresh component statuses
            for name, component in self.components.items():
                if hasattr(component, 'get_status'):
                    status = component.get_status()
                    # Update UI with component status

            self.update_status("Ready", "success")

        except Exception as e:
            self.update_status(f"Refresh error: {e}", "error")

    def update_status(self, message: str, status_type: str = "info"):
        """
        Update status bar message

        Parameters:
            message: Status message
            status_type: Type (success, warning, error, info)
        """
        colors = {
            'success': self.theme.accent_success,
            'warning': self.theme.accent_warning,
            'error': self.theme.accent_error,
            'info': self.theme.fg_primary
        }

        self.status_label.config(
            text=f"● {message}",
            fg=colors.get(status_type, colors['info'])
        )

    def _update_component_count(self):
        """Update component count in status bar"""
        count = len(self.components)
        self.component_count_label.config(text=f"Components: {count}")

    def open_settings(self):
        """Open settings dialog"""
        try:
            hub = self._load_symbol_from_file("Z Axis/Z+3_Trinity/ui/smart_settings_hub.py", "SmartSettingsHub")
            hub(parent=self.root).open_dialog()
        except Exception as e:
            messagebox.showerror("Settings", f"Failed to open Settings Hub:\n{e}", parent=self.root)

    # ------------------------------------------------------------------
    # DB helpers (read-only friendly; explicit migrations owned by Trinity (Z+3))
    # ------------------------------------------------------------------

    def _db_path(self) -> Path:
        cfg_path = self.lightspeed_root / "config" / "unified_config.json"
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8", errors="replace"))
            rel = (cfg.get("database") or {}).get("path")
            if rel:
                return (self.lightspeed_root / rel).resolve()
        except Exception:
            pass
        return (self.lightspeed_root / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db").resolve()

    def _connect_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path()))
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass
        return conn

    def _schema_ok(self) -> Optional[bool]:
        try:
            from core.services import get_db  # type: ignore

            db = get_db()
            return bool(getattr(db, "schema_ok", None))
        except Exception:
            return None

    def _refresh_overview_metrics(self):
        try:
            schema_ok = self._schema_ok()
            if hasattr(self, "metric_schema"):
                if schema_ok is True:
                    self.metric_schema.config(text="Ready", fg=self.theme.accent_success)
                elif schema_ok is False:
                    self.metric_schema.config(text="Update required", fg=self.theme.accent_warning)
                else:
                    self.metric_schema.config(text="Unknown", fg=self.theme.fg_muted)

            db_path = self._db_path()
            if not db_path.exists():
                return

            with self._connect_db() as conn:
                cur = conn.cursor()
                # Projects count (best-effort)
                projects = "n/a"
                tasks_pending = "n/a"
                tasks_in_progress = "n/a"
                try:
                    cur.execute("SELECT COUNT(*) FROM projects")
                    projects = str(int(cur.fetchone()[0]))
                except Exception:
                    pass
                try:
                    cur.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
                    tasks_pending = str(int(cur.fetchone()[0]))
                except Exception:
                    pass
                try:
                    cur.execute("SELECT COUNT(*) FROM tasks WHERE status = 'in_progress'")
                    tasks_in_progress = str(int(cur.fetchone()[0]))
                except Exception:
                    pass

                if hasattr(self, "metric_projects"):
                    self.metric_projects.config(text=projects)
                if hasattr(self, "metric_tasks_pending"):
                    self.metric_tasks_pending.config(text=tasks_pending)
                if hasattr(self, "metric_tasks_in_progress"):
                    self.metric_tasks_in_progress.config(text=tasks_in_progress)
        except Exception:
            return

    # ------------------------------------------------------------------
    # Cross-floor launchers
    # ------------------------------------------------------------------

    def _load_symbol_from_file(self, rel_path: str, symbol: str):
        tool_path = (self.lightspeed_root / rel_path).resolve()
        spec = importlib.util.spec_from_file_location(f"ls_{symbol}", tool_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module: {tool_path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, symbol):
            raise AttributeError(f"{tool_path} missing symbol {symbol}")
        return getattr(mod, symbol)

    def _open_it_portal(self):
        try:
            itp = self._load_symbol_from_file("Z Axis/Z+3_Trinity/ui/it_portal.py", "ITPortal")
            itp(parent=self.root).open_portal()
        except Exception as e:
            messagebox.showerror("IT Portal", f"Failed to open IT Portal:\n{e}", parent=self.root)

    # ------------------------------------------------------------------
    # Architect operations
    # ------------------------------------------------------------------

    def _create_task_action(self):
        title = (self.var_task_title.get() or "").strip()
        desc = (self.txt_task_desc.get("1.0", "end") or "").strip()
        priority = (self.var_task_priority.get() or "medium").strip().lower()
        if not title:
            messagebox.showerror("Create Task", "Title is required.", parent=self.root)
            return

        db_path = self._db_path()
        if not db_path.exists():
            messagebox.showerror("Create Task", f"Database not found:\n{db_path}", parent=self.root)
            return

        try:
            now = datetime.now().isoformat()
            with self._connect_db() as conn:
                cur = conn.cursor()
                cur.execute("PRAGMA table_info(tasks)")
                cols = {r[1] for r in (cur.fetchall() or [])}
                if not cols:
                    raise RuntimeError("tasks table missing")

                data: Dict[str, Any] = {}
                if "title" in cols:
                    data["title"] = title
                if "description" in cols:
                    data["description"] = desc
                if "project_id" in cols:
                    data["project_id"] = None
                if "assigned_to" in cols:
                    data["assigned_to"] = None
                if "priority" in cols:
                    data["priority"] = priority
                if "status" in cols:
                    data["status"] = "pending"
                if "created_at" in cols:
                    data["created_at"] = now
                if "updated_at" in cols:
                    data["updated_at"] = now

                if "title" not in data or "status" not in data:
                    raise RuntimeError("tasks schema missing required columns (title/status)")

                insert_cols = list(data.keys())
                placeholders = ", ".join(["?"] * len(insert_cols))
                cur.execute(
                    f"INSERT INTO tasks ({', '.join(insert_cols)}) VALUES ({placeholders})",
                    tuple(data[c] for c in insert_cols),
                )
                task_id = int(cur.lastrowid)

            self.update_status(f"Created task #{task_id}", "success")
            messagebox.showinfo("Create Task", f"Created task #{task_id}", parent=self.root)
            self.var_task_title.set("")
            self.txt_task_desc.delete("1.0", "end")
        except Exception as e:
            self.update_status("Create task failed", "error")
            messagebox.showerror("Create Task", f"Failed to create task:\n{e}", parent=self.root)

    def _save_portal_config(self):
        try:
            self.config["auto_refresh"] = bool(self.var_auto_refresh.get())
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_dir / "portal_config.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            messagebox.showinfo("Settings", "Portal settings saved.", parent=self.root)
        except Exception as e:
            messagebox.showerror("Settings", f"Failed to save portal settings:\n{e}", parent=self.root)

    def _start_auto_refresh(self):
        """Start automatic status refresh"""
        interval = self.config.get('refresh_interval_ms', 5000)

        def refresh_loop():
            self.refresh_status()
            self.root.after(interval, refresh_loop)

        self.root.after(interval, refresh_loop)

    def run(self):
        """Start portal (blocking call)"""
        if self.standalone:
            self.root.mainloop()
        else:
            # Non-blocking for embedded mode
            pass


def main():
    """Main entry point for standalone execution"""
    portal = ArchitectPortalGlass()
    portal.run()


if __name__ == "__main__":
    main()
