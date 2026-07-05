"""
Oracle Portal Glass - Glassmorphism UI Interface
Oracle Floor Component

Modern glassmorphism-themed UI portal for Oracle floor operations.
Provides intuitive interface for floor-specific functionality with consistent
LightSpeed aesthetic.

NOTE (Codex 2026-02-03): Added a read-only "Z Direct" tab for local stream/registry browsing.
Trinity remains the commit/approval gate for durable registry writes.

Floor: Oracle
Z-Level: -2
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
import time


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


def _load_symbol_from_file(rel_path: str, symbol: str):
    """
    Load a Python symbol (class/function) from a file path relative to LightSpeed root.
    Keeps floor portals decoupled from fragile package import paths.
    """
    abs_path = (LIGHTSPEED_ROOT / rel_path).resolve()
    spec = importlib.util.spec_from_file_location(symbol, abs_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from: {abs_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    if not hasattr(module, symbol):
        raise AttributeError(f"{symbol} not found in {abs_path}")
    return getattr(module, symbol)


def _load_unified_config(root: Path) -> Dict[str, Any]:
    cfg_path = root / "config" / "unified_config.json"
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _default_db_path(root: Path) -> Path:
    cfg = _load_unified_config(root)
    rel = (cfg.get("database") or {}).get("path")
    if rel:
        return (root / rel).resolve()
    return (root / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db").resolve()


def _connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception:
        pass
    return conn


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


class OraclePortalGlass:
    """
    Oracle Floor Portal with Glassmorphism UI

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
        Initialize Oracle Portal

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
        self.root.title("Oracle Portal Glass - LightSpeed V0.9.5")
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
        self.floor_dir = Z_AXIS_ROOT / "Z-2_Oracle"
        self.config_dir = self.floor_dir / "config"
        self.data_dir = self.floor_dir / "Data"
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        self._db_path = _default_db_path(self.lightspeed_root)

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
            text=f"⚡ Oracle Floor Portal",
            font=(self.theme.font_family, self.theme.font_size_title, 'bold'),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary
        )
        title.pack(side=tk.LEFT, padx=20, pady=15)

        # Subtitle
        subtitle = tk.Label(
            header_frame,
            text=f"Z-Level -2 | Floor operations portal",
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

        header = tk.Label(
            section,
            text="Oracle Overview",
            font=(self.theme.font_family, self.theme.font_size_header, "bold"),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary,
        )
        header.pack(anchor="w", padx=18, pady=(16, 10))

        stats = tk.Frame(section, bg=self.theme.bg_secondary)
        stats.pack(fill="x", padx=18)

        def stat_card(title: str, value: str = "…") -> tk.Label:
            card = tk.Frame(stats, bg=self.theme.bg_glass, highlightbackground=self.theme.border_color, highlightthickness=1)
            card.pack(side="left", padx=(0, 12), pady=(0, 10))
            tk.Label(card, text=title, bg=self.theme.bg_glass, fg=self.theme.fg_muted,
                     font=(self.theme.font_family, self.theme.font_size_normal)).pack(anchor="w", padx=10, pady=(8, 0))
            val = tk.Label(card, text=value, bg=self.theme.bg_glass, fg=self.theme.fg_text,
                           font=(self.theme.font_family, 16, "bold"))
            val.pack(anchor="w", padx=10, pady=(2, 10))
            return val

        self.stat_files = stat_card("Files", "0")
        self.stat_ingest = stat_card("Ingestion Queue", "0")
        self.stat_encyclopedia = stat_card("Encyclopedia Entries", "0")
        self.stat_conversations = stat_card("Chat Conversations", "0")

        panes = tk.PanedWindow(section, orient="horizontal", bg=self.theme.bg_secondary, sashwidth=6, relief="flat")
        panes.pack(fill="both", expand=True, padx=18, pady=(10, 16))

        left = tk.Frame(panes, bg=self.theme.bg_secondary)
        right = tk.Frame(panes, bg=self.theme.bg_secondary)
        panes.add(left, minsize=420)
        panes.add(right, minsize=420)

        tk.Label(left, text="Recent Files", bg=self.theme.bg_secondary, fg=self.theme.fg_text,
                 font=(self.theme.font_family, 11, "bold")).pack(anchor="w", pady=(0, 6))
        self.files_tree = ttk.Treeview(left, columns=("id", "name", "path", "created"), show="headings", height=10)
        for col, w in [("id", 70), ("name", 180), ("path", 360), ("created", 160)]:
            self.files_tree.heading(col, text=col)
            self.files_tree.column(col, width=w, anchor="w")
        self.files_tree.pack(fill="both", expand=True)

        tk.Label(right, text="Ingestion Tasks (latest)", bg=self.theme.bg_secondary, fg=self.theme.fg_text,
                 font=(self.theme.font_family, 11, "bold")).pack(anchor="w", pady=(0, 6))
        self.ingest_tree = ttk.Treeview(right, columns=("id", "vault_id", "type", "status", "created"), show="headings", height=10)
        for col, w in [("id", 70), ("vault_id", 80), ("type", 170), ("status", 120), ("created", 160)]:
            self.ingest_tree.heading(col, text=col)
            self.ingest_tree.column(col, width=w, anchor="w")
        self.ingest_tree.pack(fill="both", expand=True)

    def _build_section_2(self):
        """Build second section: Operations"""
        if HAS_GLASS_UI:
            section = GlassFrame(self.notebook)
        else:
            section = tk.Frame(self.notebook, bg=self.theme.bg_secondary)

        self.notebook.add(section, text="Operations")

        header = tk.Label(
            section,
            text="Oracle Operations",
            font=(self.theme.font_family, self.theme.font_size_header, "bold"),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary,
        )
        header.pack(anchor="w", padx=18, pady=(16, 10))

        actions = tk.Frame(section, bg=self.theme.bg_secondary)
        actions.pack(fill="x", padx=18)

        def btn(label: str, cmd: Callable[[], None]):
            tk.Button(
                actions,
                text=label,
                command=cmd,
                bg=self.theme.bg_glass,
                fg=self.theme.fg_text,
                relief=tk.FLAT,
                padx=14,
                pady=6,
            ).pack(side="left", padx=(0, 10), pady=(0, 10))

        btn("Open Oracle Panel", self._open_oracle_panel)
        btn("Ingest Directory…", self._ingest_directory_dialog)
        btn("Process Pending Tasks", self._process_pending_tasks_dialog)
        btn("Refresh Metrics", self.refresh_status)

        io_frame = tk.LabelFrame(section, text="Output / Logs", bg=self.theme.bg_secondary, fg=self.theme.fg_text)
        io_frame.pack(fill="both", expand=True, padx=18, pady=(6, 16))
        self.ops_log = scrolledtext.ScrolledText(io_frame, height=14, wrap="word")
        self.ops_log.pack(fill="both", expand=True, padx=10, pady=10)
        self._ops_log("[READY] Oracle operations console.")

    def _build_section_3(self):
        """Build third section: Settings"""
        if HAS_GLASS_UI:
            section = GlassFrame(self.notebook)
        else:
            section = tk.Frame(self.notebook, bg=self.theme.bg_secondary)

        self.notebook.add(section, text="Settings")

        header = tk.Label(
            section,
            text="Oracle Settings",
            font=(self.theme.font_family, self.theme.font_size_header, "bold"),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary,
        )
        header.pack(anchor="w", padx=18, pady=(16, 10))

        form = tk.Frame(section, bg=self.theme.bg_secondary)
        form.pack(fill="x", padx=18)

        self.var_auto_refresh = tk.BooleanVar(value=bool(self.config.get("auto_refresh", True)))
        self.var_refresh_ms = tk.IntVar(value=int(self.config.get("refresh_interval_ms", 5000)))

        tk.Checkbutton(
            form,
            text="Auto refresh metrics",
            variable=self.var_auto_refresh,
            bg=self.theme.bg_secondary,
            fg=self.theme.fg_text,
            selectcolor=self.theme.bg_primary,
            activebackground=self.theme.bg_secondary,
        ).grid(row=0, column=0, sticky="w", pady=8)

        tk.Label(form, text="Refresh interval (ms)", bg=self.theme.bg_secondary, fg=self.theme.fg_text).grid(
            row=1, column=0, sticky="w", pady=8
        )
        tk.Spinbox(form, from_=500, to=60000, increment=250, textvariable=self.var_refresh_ms, width=10).grid(
            row=1, column=1, sticky="w", pady=8, padx=(10, 0)
        )

        tk.Label(form, text=f"DB: {self._db_path}", bg=self.theme.bg_secondary, fg=self.theme.fg_muted).grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(18, 0)
        )

        btns = tk.Frame(section, bg=self.theme.bg_secondary)
        btns.pack(fill="x", padx=18, pady=14)
        tk.Button(btns, text="Save Settings", command=self._save_settings, bg=self.theme.bg_glass, fg=self.theme.fg_text,
                  relief=tk.FLAT, padx=14, pady=6).pack(side="left")
        tk.Button(btns, text="Open Config Folder", command=self._open_config_folder, bg=self.theme.bg_glass, fg=self.theme.fg_text,
                  relief=tk.FLAT, padx=14, pady=6).pack(side="left", padx=(10, 0))

    def _build_section_z_direct(self):
        """Build read-only Z Direct viewer for this floor (streams + durable registries)."""
        if HAS_GLASS_UI:
            section = GlassFrame(self.notebook)
        else:
            section = tk.Frame(self.notebook, bg=self.theme.bg_secondary)

        self.notebook.add(section, text="Z Direct")

        label = tk.Label(
            section,
            text="Oracle Z Direct (read-only)",
            font=(self.theme.font_family, self.theme.font_size_header),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary,
        )
        label.pack(pady=16)

        body = tk.Frame(section, bg=self.theme.bg_secondary)
        body.pack(fill="both", expand=True, padx=18, pady=10)

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

        channel = "Z-2"

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
            text=f"Floor: Oracle | Z-Level: -2",
            font=(self.theme.font_family, self.theme.font_size_normal),
            fg=self.theme.fg_muted,
            bg=self.theme.bg_secondary
        )
        floor_info.pack(side=tk.RIGHT, padx=20)

    def _initialize_components(self):
        """Initialize floor components"""
        try:
            self.update_status("Initializing components...", "warning")

            # Read-only: Oracle can browse Z Direct streams/registries, but Trinity owns commits.
            try:
                from core.services import get_z_direct  # type: ignore

                self.components["z_direct"] = get_z_direct()
            except Exception:
                self.components["z_direct"] = None

            try:
                Integrator = _load_symbol_from_file(
                    "Z Axis/Z-2_Oracle/components/oracle_smart_floor_integrator.py",
                    "OracleSmartFloorIntegrator",
                )
                self.components["smart_integrator"] = Integrator()
            except Exception as e:
                self.components["smart_integrator"] = None
                self._ops_log(f"[WARN] Smart integrator unavailable: {e}")

            # Initial refresh
            self.refresh_status()
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

    # ------------------------------------------------------------------
    # Operations helpers
    # ------------------------------------------------------------------

    def _ops_log(self, line: str):
        widget = getattr(self, "ops_log", None)
        if widget is None:
            return
        try:
            widget.insert("end", line.rstrip() + "\n")
            widget.see("end")
        except Exception:
            return

    def _open_oracle_panel(self):
        try:
            open_panel = _load_symbol_from_file(
                "Z Axis/Z-2_Oracle/components/oracle_ui_panel.py",
                "open_panel",
            )
            open_panel(parent=self.root)
        except Exception as e:
            messagebox.showerror("Oracle Panel", f"Failed to open Oracle Panel:\n{e}", parent=self.root)

    def _ingest_directory_dialog(self):
        start = str((self.floor_dir / "archive").resolve())
        dir_path = filedialog.askdirectory(parent=self.root, initialdir=start, title="Select a directory to ingest")
        if not dir_path:
            return

        integrator = self.components.get("smart_integrator")
        if integrator is None:
            messagebox.showerror("Ingest", "OracleSmartFloorIntegrator is not available.", parent=self.root)
            return

        def worker():
            t0 = time.time()
            try:
                self._ops_log(f"[INGEST] Directory: {dir_path}")
                result = integrator.ingest_directory(dir_path, recursive=True, metadata={"source": "oracle_portal"})
                dt = time.time() - t0
                self._ops_log(f"[OK] Ingested {result.get('files_ingested', 0)} files in {dt:.2f}s")
            except Exception as e:
                self._ops_log(f"[ERROR] Ingest failed: {e}")
            finally:
                try:
                    self.root.after(0, self.refresh_status)
                except Exception:
                    pass

        threading.Thread(target=worker, daemon=True).start()

    def _process_pending_tasks_dialog(self):
        integrator = self.components.get("smart_integrator")
        if integrator is None:
            messagebox.showerror("Process Tasks", "OracleSmartFloorIntegrator is not available.", parent=self.root)
            return

        def worker():
            try:
                self._ops_log("[PROCESS] Processing pending ingestion tasks…")
                results = integrator.process_pending_tasks(max_tasks=5)
                self._ops_log(f"[OK] Processed {len(results)} tasks")
            except Exception as e:
                self._ops_log(f"[ERROR] Processing failed: {e}")
            finally:
                try:
                    self.root.after(0, self.refresh_status)
                except Exception:
                    pass

        threading.Thread(target=worker, daemon=True).start()

    def _open_config_folder(self):
        try:
            path = str(self.config_dir.resolve())
        except Exception:
            return
        try:
            import os
            os.startfile(path)  # type: ignore[attr-defined]
        except Exception:
            pass

    def _save_settings(self):
        self.config["auto_refresh"] = bool(self.var_auto_refresh.get())
        self.config["refresh_interval_ms"] = int(self.var_refresh_ms.get() or 5000)
        cfg_path = self.config_dir / "portal_config.json"
        try:
            cfg_path.parent.mkdir(parents=True, exist_ok=True)
            cfg_path.write_text(json.dumps(self.config, indent=2), encoding="utf-8")
            self._ops_log(f"[OK] Saved settings: {cfg_path}")
        except Exception as e:
            messagebox.showerror("Settings", f"Failed to save settings:\n{e}", parent=self.root)
            return

        if self.config.get("auto_refresh", False):
            self._start_auto_refresh()

    # ------------------------------------------------------------------
    # DB-backed metrics
    # ------------------------------------------------------------------

    def _refresh_db_metrics(self):
        db_path = self._db_path
        try:
            with _connect_db(db_path) as conn:
                cur = conn.cursor()
                try:
                    cur.execute("PRAGMA table_info(files)")
                    files_cols = {r[1] for r in (cur.fetchall() or [])}
                except Exception:
                    files_cols = set()

                deleted_filter = "deleted_at IS NULL" if "deleted_at" in files_cols else "1=1"
                cur.execute(f"SELECT COUNT(*) FROM files WHERE {deleted_filter}")
                files_total = int(cur.fetchone()[0])
                cur.execute("SELECT COUNT(*) FROM oracle_ingestion_tasks WHERE status IN ('queued','pending')")
                ingest_q = int(cur.fetchone()[0])
                cur.execute("SELECT COUNT(*) FROM encyclopedia_entries")
                enc_total = int(cur.fetchone()[0])
                cur.execute("SELECT COUNT(*) FROM chat_conversations")
                conv_total = int(cur.fetchone()[0])

                self.stat_files.config(text=str(files_total))
                self.stat_ingest.config(text=str(ingest_q))
                self.stat_encyclopedia.config(text=str(enc_total))
                self.stat_conversations.config(text=str(conv_total))

                # Recent files
                try:
                    for row in self.files_tree.get_children():
                        self.files_tree.delete(row)
                except Exception:
                    pass
                name_col = "name" if "name" in files_cols else ("filename" if "filename" in files_cols else None)
                path_col = "path" if "path" in files_cols else ("filepath" if "filepath" in files_cols else ("original_path" if "original_path" in files_cols else None))
                created_col = "created_at" if "created_at" in files_cols else None
                select_cols = ["id"]
                if name_col:
                    select_cols.append(name_col)
                if path_col:
                    select_cols.append(path_col)
                if created_col:
                    select_cols.append(created_col)

                if len(select_cols) == 1:
                    # No usable columns; avoid noisy SQL errors on legacy DBs.
                    return

                cur.execute(
                    f"SELECT {', '.join(select_cols)} FROM files WHERE {deleted_filter} ORDER BY id DESC LIMIT 50"
                )
                for row in cur.fetchall() or []:
                    # Row shape depends on which columns were available.
                    rid = row[0]
                    nm = row[1] if len(row) > 1 else ""
                    pth = row[2] if len(row) > 2 else ""
                    created = row[3] if len(row) > 3 else ""
                    self.files_tree.insert("", "end", values=(rid, nm, pth, created))

                # Recent ingestion tasks
                try:
                    for row in self.ingest_tree.get_children():
                        self.ingest_tree.delete(row)
                except Exception:
                    pass
                cur.execute(
                    "SELECT id, vault_id, task_type, status, created_at FROM oracle_ingestion_tasks ORDER BY id DESC LIMIT 50"
                )
                for rid, vault_id, task_type, status, created in cur.fetchall() or []:
                    self.ingest_tree.insert("", "end", values=(rid, vault_id, task_type, status, created))

        except Exception as e:
            self._ops_log(f"[WARN] DB metrics unavailable: {e}")

    def _start_auto_refresh(self):
        """Start automatic status refresh"""
        interval = self.config.get('refresh_interval_ms', 5000)

        def refresh_loop():
            try:
                if self.config.get("auto_refresh", False):
                    self.refresh_status()
                    self.root.after(interval, refresh_loop)
            except Exception:
                return

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
    portal = OraclePortalGlass()
    portal.run()


if __name__ == "__main__":
    main()
