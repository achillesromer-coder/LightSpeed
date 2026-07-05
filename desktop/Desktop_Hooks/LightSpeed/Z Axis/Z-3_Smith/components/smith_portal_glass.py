"""
Smith Portal Glass - Glassmorphism UI Interface
Smith Floor Component

Modern glassmorphism-themed UI portal for Smith floor operations.
Provides intuitive interface for floor-specific functionality with consistent
LightSpeed aesthetic.

NOTE (Codex 2026-02-03): Added a read-only "Z Direct" tab for local stream/registry browsing.
Trinity remains the commit/approval gate for durable registry writes.

Floor: Smith
Z-Level: -3
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
import threading
from datetime import datetime


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


class SmithPortalGlass:
    """
    Smith Floor Portal with Glassmorphism UI

    Features:
    - Modern glass-themed interface
    - Floor-specific tools and operations
    - Real-time status monitoring
    - Event bus integration
    - Cross-floor communication

    Sections:
    1. Overview - Floor status and metrics
    2. Operations - Floor-specific operations
    3. Settings - Configuration and preferences
    4. Z Direct - read-only streams + durable registry viewer
    """

    def __init__(self, parent: Optional[tk.Tk] = None):
        """
        Initialize Smith Portal

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
        self.root.title("Smith Portal Glass - LightSpeed V0.9.5")
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
        self.floor_dir = Z_AXIS_ROOT / "Z-3_Smith"
        self.config_dir = self.floor_dir / "config"
        self.data_dir = self.floor_dir / "data"

        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        # Load configuration
        self.config = self._load_config()

        # Build UI
        self._build_ui()

        # Initialize components
        self._initialize_components()

        # Start auto-refresh if enabled
        if self.config.get('auto_refresh', False):
            self._start_auto_refresh()

    # ---------------------------------------------------------------------
    # DB + dynamic tool loading (Smith owns jobs; Merovingian owns DB file)
    # ---------------------------------------------------------------------

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

    def _create_job(self, job_type: str, params: Dict[str, Any]) -> Optional[int]:
        db_path = self._db_path()
        if not db_path.exists():
            return None
        now = datetime.now().isoformat()
        try:
            with sqlite3.connect(str(db_path)) as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO jobs (job_type, params_json, status, scheduled_for, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (job_type, json.dumps(params or {}, ensure_ascii=False), "pending", None, now, now),
                )
                return int(cur.lastrowid)
        except Exception:
            return None

    def _load_tool(self, rel_path: str, module_name: str):
        tool_path = (self.lightspeed_root / rel_path).resolve()
        spec = importlib.util.spec_from_file_location(module_name, tool_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load tool module: {tool_path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

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
            text=f"⚡ Smith Floor Portal",
            font=(self.theme.font_family, self.theme.font_size_title, 'bold'),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary
        )
        title.pack(side=tk.LEFT, padx=20, pady=15)

        # Subtitle
        subtitle = tk.Label(
            header_frame,
            text=f"Z-Level -3 | Floor operations portal",
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

        # Settings button
        settings_btn = tk.Button(
            controls_frame,
            text="⚙ Settings",
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
        """Build first section: Overview"""
        if HAS_GLASS_UI:
            section = GlassFrame(self.notebook)
        else:
            section = tk.Frame(self.notebook, bg=self.theme.bg_secondary)

        self.notebook.add(section, text="Overview")

        # Section content
        label = tk.Label(
            section,
            text="Overview Content",
            font=(self.theme.font_family, self.theme.font_size_header),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary
        )
        label.pack(pady=20)

        # Quick metrics (DB-backed)
        metrics = tk.Frame(section, bg=self.theme.bg_secondary)
        metrics.pack(fill=tk.X, padx=20, pady=(0, 10))

        self._metric_labels: Dict[str, tk.Label] = {}
        for key, title in [
            ("jobs_total", "Jobs"),
            ("jobs_running", "Running"),
            ("tasks_total", "Tasks"),
            ("chat_conversations", "Chat Convs"),
        ]:
            card = tk.Frame(
                metrics,
                bg=self.theme.bg_glass,
                highlightbackground=self.theme.border_color,
                highlightthickness=1,
            )
            card.pack(side=tk.LEFT, padx=8, pady=8)
            tk.Label(
                card,
                text=title,
                bg=self.theme.bg_glass,
                fg=self.theme.fg_muted,
                font=(self.theme.font_family, 9),
            ).pack(anchor="w", padx=10, pady=(8, 2))
            val = tk.Label(
                card,
                text="—",
                bg=self.theme.bg_glass,
                fg=self.theme.fg_primary,
                font=(self.theme.font_family, 14, "bold"),
            )
            val.pack(anchor="w", padx=10, pady=(0, 8))
            self._metric_labels[key] = val

        # Recent jobs
        jobs_frame = tk.LabelFrame(section, text="Recent Jobs", bg=self.theme.bg_secondary, fg=self.theme.fg_text)
        jobs_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        jobs_frame.columnconfigure(0, weight=1)
        jobs_frame.rowconfigure(0, weight=1)

        cols = ("id", "job_type", "status", "updated_at")
        self.jobs_tree = ttk.Treeview(jobs_frame, columns=cols, show="headings", height=10)
        for c, w in [("id", 80), ("job_type", 220), ("status", 120), ("updated_at", 220)]:
            self.jobs_tree.heading(c, text=c)
            self.jobs_tree.column(c, width=w, anchor="w")
        self.jobs_tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(jobs_frame, orient="vertical", command=self.jobs_tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.jobs_tree.configure(yscrollcommand=sb.set)

    def _build_section_2(self):
        """Build second section: Operations"""
        if HAS_GLASS_UI:
            section = GlassFrame(self.notebook)
        else:
            section = tk.Frame(self.notebook, bg=self.theme.bg_secondary)

        self.notebook.add(section, text="Operations")

        # Section content
        label = tk.Label(
            section,
            text="Operations Content",
            font=(self.theme.font_family, self.theme.font_size_header),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary
        )
        label.pack(pady=20)

        body = tk.Frame(section, bg=self.theme.bg_secondary)
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(1, weight=1)

        actions = tk.LabelFrame(body, text="Actions", bg=self.theme.bg_secondary, fg=self.theme.fg_text)
        actions.grid(row=0, column=0, sticky="nw", padx=(0, 12), pady=(0, 12))

        tk.Button(
            actions,
            text="Import GPT Export (conversations.json)",
            command=self.open_gpt_export_importer,
            bg=self.theme.bg_glass,
            fg=self.theme.fg_primary,
            relief=tk.FLAT,
            padx=12,
            pady=8,
        ).pack(fill=tk.X, padx=10, pady=(10, 6))

        tk.Button(
            actions,
            text="Scan Docs → Tasks (MD/TXT)",
            command=self.open_doc_scan_dialog,
            bg=self.theme.bg_glass,
            fg=self.theme.fg_primary,
            relief=tk.FLAT,
            padx=12,
            pady=8,
        ).pack(fill=tk.X, padx=10, pady=6)

        tk.Button(
            actions,
            text="Sync Open Dialogue → DB",
            command=self.sync_open_dialogue_to_db,
            bg=self.theme.bg_glass,
            fg=self.theme.fg_primary,
            relief=tk.FLAT,
            padx=12,
            pady=8,
        ).pack(fill=tk.X, padx=10, pady=6)

        tk.Button(
            actions,
            text="Rebuild dataindex/depmap",
            command=self.run_generate_dataindex,
            bg=self.theme.bg_glass,
            fg=self.theme.fg_primary,
            relief=tk.FLAT,
            padx=12,
            pady=8,
        ).pack(fill=tk.X, padx=10, pady=6)

        log_frame = tk.LabelFrame(body, text="Activity Log", bg=self.theme.bg_secondary, fg=self.theme.fg_text)
        log_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", pady=(0, 12))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.activity_text = scrolledtext.ScrolledText(
            log_frame,
            height=18,
            wrap="word",
            bg=self.theme.bg_primary,
            fg=self.theme.fg_text,
            insertbackground=self.theme.fg_text,
            relief=tk.FLAT,
        )
        self.activity_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.activity_text.insert("end", "Smith Operations ready.\n")
        self.activity_text.configure(state="disabled")

        jobs_panel = tk.LabelFrame(body, text="Jobs Monitor", bg=self.theme.bg_secondary, fg=self.theme.fg_text)
        jobs_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        jobs_panel.rowconfigure(0, weight=1)
        jobs_panel.columnconfigure(0, weight=1)

        try:
            from core.ui.dashboard_widgets import BackgroundJobsWidget

            widget = BackgroundJobsWidget(jobs_panel)
            widget.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        except Exception as e:
            tk.Label(
                jobs_panel,
                text=f"Jobs widget unavailable:\n{e}",
                bg=self.theme.bg_secondary,
                fg=self.theme.fg_muted,
                justify=tk.LEFT,
            ).pack(anchor="w", padx=10, pady=10)

    def _build_section_3(self):
        """Build third section: Settings"""
        if HAS_GLASS_UI:
            section = GlassFrame(self.notebook)
        else:
            section = tk.Frame(self.notebook, bg=self.theme.bg_secondary)

        self.notebook.add(section, text="Settings")

        # Section content
        label = tk.Label(
            section,
            text="Settings Content",
            font=(self.theme.font_family, self.theme.font_size_header),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary
        )
        label.pack(pady=20)

        form = tk.Frame(section, bg=self.theme.bg_secondary)
        form.pack(fill=tk.X, padx=20, pady=10)

        self.var_auto_refresh = tk.BooleanVar(value=bool(self.config.get("auto_refresh", True)))
        self.var_refresh_ms = tk.StringVar(value=str(int(self.config.get("refresh_interval_ms", 5000))))

        tk.Checkbutton(
            form,
            text="Enable auto-refresh",
            variable=self.var_auto_refresh,
            bg=self.theme.bg_secondary,
            fg=self.theme.fg_text,
            selectcolor=self.theme.bg_primary,
            activebackground=self.theme.bg_secondary,
        ).grid(row=0, column=0, sticky="w", pady=6)

        tk.Label(form, text="Refresh interval (ms)", bg=self.theme.bg_secondary, fg=self.theme.fg_text).grid(
            row=1, column=0, sticky="w", pady=6
        )
        ttk.Entry(form, textvariable=self.var_refresh_ms, width=12).grid(row=1, column=1, sticky="w", padx=(10, 0))

        tk.Button(
            form,
            text="Save Settings",
            command=self.save_settings,
            bg=self.theme.bg_glass,
            fg=self.theme.fg_primary,
            relief=tk.FLAT,
            padx=12,
            pady=6,
        ).grid(row=2, column=0, sticky="w", pady=(12, 6))

    def _build_section_z_direct(self):
        """Build read-only Z Direct viewer for this floor (streams + durable registries)."""
        if HAS_GLASS_UI:
            section = GlassFrame(self.notebook)
        else:
            section = tk.Frame(self.notebook, bg=self.theme.bg_secondary)

        self.notebook.add(section, text="Z Direct")

        label = tk.Label(
            section,
            text="Smith Z Direct (read-only)",
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

        channel = "Z-3"

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
        registry_var = tk.StringVar(value="tasks")

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

                reg_name = registry_var.get() or "tasks"
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
            text=f"Floor: Smith | Z-Level: -3",
            font=(self.theme.font_family, self.theme.font_size_normal),
            fg=self.theme.fg_muted,
            bg=self.theme.bg_secondary
        )
        floor_info.pack(side=tk.RIGHT, padx=20)

    def _initialize_components(self):
        """Initialize floor components"""
        try:
            self.update_status("Initializing components...", "warning")
            # Read-only: Smith can browse Z Direct streams/registries, but Trinity owns commits.
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

            self._refresh_db_metrics()

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
            self.notebook.select(2)
        except Exception:
            pass

    def save_settings(self):
        """Persist settings to `portal_config.json` (Smith floor-local)."""
        try:
            refresh_ms = int(str(self.var_refresh_ms.get()).strip() or "5000")
        except Exception:
            refresh_ms = 5000

        self.config["auto_refresh"] = bool(self.var_auto_refresh.get())
        self.config["refresh_interval_ms"] = max(250, min(600_000, refresh_ms))

        try:
            cfg_path = self.config_dir / "portal_config.json"
            cfg_path.write_text(json.dumps(self.config, indent=2), encoding="utf-8")
            self.update_status("Settings saved", "success")
        except Exception as e:
            self.update_status(f"Save failed: {e}", "error")

    def _append_activity(self, text: str):
        widget = getattr(self, "activity_text", None)
        if widget is None:
            return
        try:
            widget.configure(state="normal")
            widget.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {text}\n")
            widget.see("end")
            widget.configure(state="disabled")
        except Exception:
            pass

    def _refresh_db_metrics(self):
        db_path = self._db_path()
        if not db_path.exists():
            return
        try:
            with self._connect_db() as conn:
                cur = conn.cursor()
                counts = {}
                cur.execute("SELECT COUNT(*) FROM jobs")
                counts["jobs_total"] = int(cur.fetchone()[0])
                cur.execute("SELECT COUNT(*) FROM jobs WHERE status='running'")
                counts["jobs_running"] = int(cur.fetchone()[0])
                cur.execute("SELECT COUNT(*) FROM tasks")
                counts["tasks_total"] = int(cur.fetchone()[0])
                cur.execute("SELECT COUNT(*) FROM chat_conversations")
                counts["chat_conversations"] = int(cur.fetchone()[0])

                labels = getattr(self, "_metric_labels", {})
                for k, v in counts.items():
                    if k in labels:
                        try:
                            labels[k].config(text=str(v))
                        except Exception:
                            pass

                tree = getattr(self, "jobs_tree", None)
                if tree is not None:
                    try:
                        for item in tree.get_children():
                            tree.delete(item)
                        cur.execute(
                            "SELECT id, job_type, status, COALESCE(updated_at, created_at) FROM jobs ORDER BY id DESC LIMIT 30"
                        )
                        for row in cur.fetchall():
                            tree.insert("", "end", values=(row[0], row[1], row[2], row[3]))
                    except Exception:
                        pass
        except Exception:
            return

    # ---------------------------------------------------------------------
    # Actions
    # ---------------------------------------------------------------------

    def open_gpt_export_importer(self):
        """Open GPT Export importer dialog (streams conversations.json into DB)."""
        win = tk.Toplevel(self.root)
        win.title("GPT Export Importer (Smith)")
        win.geometry("860x520")
        win.minsize(780, 480)
        win.configure(bg=self.theme.bg_primary)

        default_path = (
            self.lightspeed_root
            / "Z Axis"
            / "Z-2_Oracle"
            / "archive"
            / "conversations"
            / "GPT_Export_2025-11-16"
            / "conversations.json"
        )

        export_var = tk.StringVar(value=str(default_path if default_path.exists() else ""))
        company_var = tk.StringVar(value="auto")
        source_var = tk.StringVar(value="GPT_Export_2025-11-16")
        status_var = tk.StringVar(value="Ready.")
        pct_var = tk.DoubleVar(value=0.0)

        def browse():
            p = filedialog.askopenfilename(
                parent=win,
                title="Select GPT Export conversations.json",
                initialdir=str(default_path.parent) if default_path.parent.exists() else str(self.lightspeed_root),
                initialfile=default_path.name,
                filetypes=[("conversations.json", "conversations.json"), ("JSON files", "*.json"), ("All files", "*.*")],
            )
            if p:
                export_var.set(p)

        frm = tk.Frame(win, bg=self.theme.bg_primary)
        frm.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        frm.columnconfigure(1, weight=1)

        tk.Label(frm, text="Export file", bg=self.theme.bg_primary, fg=self.theme.fg_text).grid(row=0, column=0, sticky="w", pady=6)
        ttk.Entry(frm, textvariable=export_var).grid(row=0, column=1, sticky="ew", pady=6, padx=(10, 10))
        ttk.Button(frm, text="Browse", command=browse).grid(row=0, column=2, sticky="e", pady=6)

        tk.Label(frm, text="Company", bg=self.theme.bg_primary, fg=self.theme.fg_text).grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(frm, textvariable=company_var, width=18).grid(row=1, column=1, sticky="w", pady=6, padx=(10, 10))
        tk.Label(frm, text="(use 'auto' to classify Romer vs EMASSC)", bg=self.theme.bg_primary, fg=self.theme.fg_muted).grid(row=1, column=2, sticky="w", pady=6)

        tk.Label(frm, text="Source label", bg=self.theme.bg_primary, fg=self.theme.fg_text).grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(frm, textvariable=source_var, width=22).grid(row=2, column=1, sticky="w", pady=6, padx=(10, 10))

        prog = ttk.Progressbar(frm, variable=pct_var, maximum=100.0)
        prog.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(16, 6))

        tk.Label(frm, textvariable=status_var, bg=self.theme.bg_primary, fg=self.theme.fg_text, font=("Consolas", 10), anchor="w").grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=(6, 10)
        )

        buttons = tk.Frame(frm, bg=self.theme.bg_primary)
        buttons.grid(row=5, column=0, columnspan=3, sticky="ew")

        running = {"flag": False}

        def set_running(is_running: bool):
            running["flag"] = is_running
            for child in buttons.winfo_children():
                try:
                    child.configure(state=("disabled" if is_running else "normal"))
                except Exception:
                    pass

        def start():
            if running["flag"]:
                return
            export_path = Path(export_var.get()).resolve()
            if not export_path.exists():
                messagebox.showerror("Import", f"File not found:\n{export_path}", parent=win)
                return
            db_path = self._db_path()
            if not db_path.exists():
                messagebox.showerror("Import", f"Database not found:\n{db_path}", parent=win)
                return

            set_running(True)
            status_var.set("Starting…")
            pct_var.set(0.0)

            tool = self._load_tool("Z Axis/Z-3_Smith/tools/import_gpt_export.py", "import_gpt_export_tool")
            job_id = self._create_job(
                "import_gpt_export",
                {"source": source_var.get().strip(), "company": company_var.get().strip(), "file": str(export_path)},
            )

            def progress_cb(p):
                def ui():
                    pct_var.set(float(getattr(p, "pct", 0.0) or 0.0))
                    status_var.set(
                        f"[{pct_var.get():6.2f}%] conv={getattr(p, 'conversations_seen', 0)} msgs={getattr(p, 'messages_seen', 0)}"
                    )
                try:
                    win.after(0, ui)
                except Exception:
                    pass

            def worker():
                try:
                    tool.import_gpt_export(
                        db_path=db_path,
                        export_path=export_path,
                        source=source_var.get().strip() or "GPT_Export",
                        company_name=(company_var.get().strip() or "auto"),
                        commit_every=25,
                        job_id=(job_id or None),
                        progress_cb=progress_cb,
                    )
                    try:
                        win.after(0, lambda: status_var.set("Completed. See Jobs Monitor."))
                    except Exception:
                        pass
                except Exception as exc:
                    try:
                        win.after(0, lambda: status_var.set(f"Error: {exc}"))
                    except Exception:
                        pass
                finally:
                    try:
                        win.after(0, lambda: set_running(False))
                    except Exception:
                        pass

            threading.Thread(target=worker, daemon=True).start()
            self._append_activity(f"Queued GPT export import (job #{job_id or 'n/a'}): {export_path.name}")

        ttk.Button(buttons, text="Start Import", command=start).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Close", command=win.destroy).pack(side=tk.RIGHT)

    def open_doc_scan_dialog(self):
        """Scan MD/TXT docs for markers (TODO/FIXME/etc) and write to DB."""
        scan_root = filedialog.askdirectory(
            parent=self.root,
            title="Select directory to scan (recommended: Z Axis)",
            initialdir=str(self.lightspeed_root / "Z Axis"),
        )
        if not scan_root:
            return
        db_path = self._db_path()
        if not db_path.exists():
            messagebox.showerror("Scan", f"Database not found:\n{db_path}", parent=self.root)
            return
        self._append_activity(f"Scanning docs for markers: {scan_root}")

        tool = self._load_tool("Z Axis/Z-3_Smith/tools/scan_docs_to_tasks.py", "scan_docs_to_tasks_tool")

        def worker():
            try:
                res = tool.scan_docs_to_db(db_path=db_path, scan_root=Path(scan_root))
                self.root.after(0, lambda: self._append_activity(f"Doc scan complete: files={res.files_scanned}, markers={res.markers_found}, tasks={res.tasks_created}"))
            except Exception as exc:
                try:
                    self.root.after(0, lambda: self._append_activity(f"Doc scan failed: {exc}"))
                except Exception:
                    pass

        threading.Thread(target=worker, daemon=True).start()

    def sync_open_dialogue_to_db(self):
        """Sync `ai_logs/open_dialogue/live_conversation.jsonl` into chat tables."""
        db_path = self._db_path()
        if not db_path.exists():
            messagebox.showerror("Sync", f"Database not found:\n{db_path}", parent=self.root)
            return

        log_path = (self.lightspeed_root / "ai_logs" / "open_dialogue" / "live_conversation.jsonl").resolve()
        if not log_path.exists():
            messagebox.showerror("Sync", f"Open Dialogue log not found:\n{log_path}", parent=self.root)
            return

        job_id = self._create_job(
            "sync_open_dialogue_to_db",
            {"source": "open_dialogue", "log_path": str(log_path)},
        )

        self._append_activity(f"Syncing Open Dialogue → DB (job #{job_id or 'n/a'})")
        tool = self._load_tool("Z Axis/Z-3_Smith/tools/sync_open_dialogue_to_db.py", "sync_open_dialogue_to_db_tool")

        def worker():
            try:
                res = tool.sync_open_dialogue_to_db(db_path=db_path, log_path=log_path, job_id=(job_id or None))
                if not isinstance(res, dict):
                    res = {"result": str(res)}
                self.root.after(
                    0,
                    lambda: self._append_activity(
                        "Open Dialogue sync complete: "
                        f"events={res.get('events_seen')}, inserted_messages={res.get('inserted_messages')}, inserted_reviews={res.get('inserted_reviews')}"
                    ),
                )
            except Exception as exc:
                try:
                    self.root.after(0, lambda: self._append_activity(f"Open Dialogue sync failed: {exc}"))
                except Exception:
                    pass

        threading.Thread(target=worker, daemon=True).start()

    def run_generate_dataindex(self):
        """Regenerate the z_axis index + depmap (Smith tool)."""
        self._append_activity("Regenerating dataindex/depmap…")
        tool = self._load_tool("Z Axis/Z-3_Smith/tools/generate_dataindex.py", "generate_dataindex_tool")

        def worker():
            try:
                rc = tool.main([])
                self.root.after(0, lambda: self._append_activity(f"Dataindex regeneration complete (rc={rc})."))
            except SystemExit as exc:
                self.root.after(0, lambda: self._append_activity(f"Dataindex regeneration complete (exit={exc.code})."))
            except Exception as exc:
                self.root.after(0, lambda: self._append_activity(f"Dataindex regeneration failed: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def lift(self):
        """Bring the portal window to front (compat for callers)."""
        try:
            self.root.lift()
        except Exception:
            pass

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
            return


def main():
    """Main entry point for standalone execution"""
    portal = SmithPortalGlass()
    portal.run()


if __name__ == "__main__":
    main()
