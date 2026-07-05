"""
Trinity Portal Glass - Glassmorphism UI Interface
Trinity Floor Component

Modern glassmorphism-themed UI portal for Trinity floor operations.
Provides intuitive interface for floor-specific functionality with consistent
LightSpeed aesthetic.

Floor: Trinity
Z-Level: 3
Author: LightSpeed Team
Version: 0.9.5
Date: 2026-01-12
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
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


TRINITY_PORTAL_GLASS_SETTINGS_CONTEXT = {
    "page_id": "trinity.portal_glass.settings",
    "label": "Trinity Portal Glass / Settings",
}


class TrinityPortalGlass:
    """
    Trinity Floor Portal with Glassmorphism UI

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
    """

    def __init__(self, parent: Optional[tk.Tk] = None):
        """
        Initialize Trinity Portal

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
        self.root.title("Trinity Portal Glass - LightSpeed V0.9.5")
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
        self.floor_dir = Z_AXIS_ROOT / "Z+3_Trinity"
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
    # DB + dynamic module loading (Trinity surfaces UI; Merovingian owns DB)
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

    def _load_symbol_from_file(self, rel_path: str, symbol: str):
        path = (self.lightspeed_root / rel_path).resolve()
        spec = importlib.util.spec_from_file_location(f"trinity_dynamic_{path.stem}", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load: {path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, symbol):
            raise AttributeError(f"{symbol} not found in {path}")
        return getattr(mod, symbol)

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
            text=f"⚡ Trinity Floor Portal",
            font=(self.theme.font_family, self.theme.font_size_title, 'bold'),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary
        )
        title.pack(side=tk.LEFT, padx=20, pady=15)

        # Subtitle
        subtitle = tk.Label(
            header_frame,
            text=f"Z-Level 3 | Floor operations portal",
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

        metrics = tk.Frame(section, bg=self.theme.bg_secondary)
        metrics.pack(fill=tk.X, padx=20, pady=(0, 10))

        self._metric_labels: Dict[str, tk.Label] = {}
        for key, title in [
            ("jobs_total", "Jobs"),
            ("tasks_total", "Tasks"),
            ("projects_total", "Projects"),
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

        links = tk.LabelFrame(section, text="Quick Launch", bg=self.theme.bg_secondary, fg=self.theme.fg_text)
        links.pack(fill=tk.X, padx=20, pady=10)

        tk.Button(
            links,
            text="Open Dialogue Board (Codex / Claude / User)",
            command=self.open_open_dialogue_board,
            bg=self.theme.bg_glass,
            fg=self.theme.fg_primary,
            relief=tk.FLAT,
            padx=12,
            pady=8,
        ).pack(side=tk.LEFT, padx=10, pady=10)

        profile_menu_btn = tk.Menubutton(
            links,
            text="Profile + Setup",
            bg=self.theme.bg_glass,
            fg=self.theme.fg_primary,
            relief=tk.FLAT,
            padx=12,
            pady=8,
            font=(self.theme.font_family, self.theme.font_size_normal, "bold"),
            activebackground=self.theme.bg_secondary,
            activeforeground=self.theme.fg_primary,
        )
        profile_menu = tk.Menu(profile_menu_btn, tearoff=0, bg=self.theme.bg_secondary, fg=self.theme.fg_text)
        profile_menu.add_command(
            label="Profiles + Company",
            command=lambda: self.open_smart_settings(
                focus_section="setup_state",
                context=dict(TRINITY_PORTAL_GLASS_SETTINGS_CONTEXT),
            ),
        )
        profile_menu.add_command(
            label="Tailoring + Layout",
            command=lambda: self.open_smart_settings(
                focus_section="tailoring",
                context=dict(TRINITY_PORTAL_GLASS_SETTINGS_CONTEXT),
            ),
        )
        profile_menu_btn.config(menu=profile_menu)
        profile_menu_btn.pack(side=tk.LEFT, padx=10, pady=10)

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

        for text, cmd in [
            ("Open IT Portal (IT/Founder)", self.open_it_portal),
            ("Open Oracle Ingestion Panel", self.open_oracle_panel),
            ("Import GPT Export (Smith)", self.open_smith_gpt_importer),
            ("Browse Chat Conversations", self.open_chat_browser),
            ("Sync Open Dialogue → DB (Smith)", self.sync_open_dialogue_to_db),
            ("Open Collaboration Hub (M1-2/2-3)", self.open_collaboration_hub),
            ("Open Tower View (TheConstruct)", self.open_tower_view),
            ("Open Immersive 3D (TheConstruct)", self.open_immersive_3d),
        ]:
            tk.Button(
                actions,
                text=text,
                command=cmd,
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
        self.activity_text.insert("end", "Trinity Operations ready.\n")
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
            text="Portal Settings",
            font=(self.theme.font_family, self.theme.font_size_header),
            fg=self.theme.fg_primary,
            bg=self.theme.bg_secondary
        )
        label.pack(pady=20)

        help_text = tk.Label(
            section,
            text=(
                "Keep portal refresh controls here and route theme, template, and setup work\n"
                "through Trinity's floor-owned Settings Hub."
            ),
            font=(self.theme.font_family, self.theme.font_size_normal),
            fg=self.theme.fg_text,
            bg=self.theme.bg_secondary,
            justify=tk.LEFT,
        )
        help_text.pack(anchor="w", padx=20, pady=(0, 10))

        form = tk.LabelFrame(section, text="Portal Refresh", bg=self.theme.bg_secondary, fg=self.theme.fg_text)
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

        launchers = tk.LabelFrame(section, text="Trinity Actions", bg=self.theme.bg_secondary, fg=self.theme.fg_text)
        launchers.pack(fill=tk.X, padx=20, pady=(4, 10))

        tk.Label(
            launchers,
            text="Open page-specific settings or route Trinity-owned theme, template, and setup tools through one compact menu.",
            bg=self.theme.bg_secondary,
            fg=self.theme.fg_text,
            justify=tk.LEFT,
            font=(self.theme.font_family, self.theme.font_size_normal),
        ).pack(anchor="w", padx=10, pady=(8, 6))

        actions = tk.Frame(launchers, bg=self.theme.bg_secondary)
        actions.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(
            actions,
            text="Page Settings",
            command=lambda: self.open_smart_settings(
                focus_section="page",
                context=dict(TRINITY_PORTAL_GLASS_SETTINGS_CONTEXT),
            ),
            bg=self.theme.bg_glass,
            fg=self.theme.fg_primary,
            relief=tk.FLAT,
            padx=12,
            pady=6,
        ).pack(side=tk.LEFT, padx=(0, 8))

        tools_menu_btn = tk.Menubutton(
            actions,
            text="Trinity Tools",
            bg=self.theme.bg_glass,
            fg=self.theme.fg_primary,
            relief=tk.FLAT,
            padx=12,
            pady=6,
            font=(self.theme.font_family, self.theme.font_size_normal, "bold"),
            activebackground=self.theme.bg_secondary,
            activeforeground=self.theme.fg_primary,
        )
        tools_menu = tk.Menu(tools_menu_btn, tearoff=0, bg=self.theme.bg_secondary, fg=self.theme.fg_text)
        tools_menu.add_command(
            label="Theme + Templates",
            command=lambda: self.open_smart_settings(
                focus_section="trinity_launchers",
                context=dict(TRINITY_PORTAL_GLASS_SETTINGS_CONTEXT),
            ),
        )
        tools_menu.add_command(
            label="Profile + Setup",
            command=lambda: self.open_smart_settings(
                focus_section="setup_state",
                context=dict(TRINITY_PORTAL_GLASS_SETTINGS_CONTEXT),
            ),
        )
        tools_menu_btn.config(menu=tools_menu)
        tools_menu_btn.pack(side=tk.LEFT)

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
            text=f"Floor: Trinity | Z-Level: 3",
            font=(self.theme.font_family, self.theme.font_size_normal),
            fg=self.theme.fg_muted,
            bg=self.theme.bg_secondary
        )
        floor_info.pack(side=tk.RIGHT, padx=20)

    def _initialize_components(self):
        """Initialize floor components"""
        try:
            self.update_status("Initializing components...", "warning")

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
        """Persist settings to `portal_config.json` (Trinity floor-local)."""
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
                cur.execute("SELECT COUNT(*) FROM jobs")
                jobs_total = int(cur.fetchone()[0])
                cur.execute("SELECT COUNT(*) FROM tasks")
                tasks_total = int(cur.fetchone()[0])
                cur.execute("SELECT COUNT(*) FROM projects")
                projects_total = int(cur.fetchone()[0])
                cur.execute("SELECT COUNT(*) FROM chat_conversations")
                chats_total = int(cur.fetchone()[0])

                labels = getattr(self, "_metric_labels", {})
                for k, v in [
                    ("jobs_total", jobs_total),
                    ("tasks_total", tasks_total),
                    ("projects_total", projects_total),
                    ("chat_conversations", chats_total),
                ]:
                    if k in labels:
                        try:
                            labels[k].config(text=str(v))
                        except Exception:
                            pass
        except Exception:
            return

    # ---------------------------------------------------------------------
    # Actions (floor-native loaders)
    # ---------------------------------------------------------------------

    def open_open_dialogue_board(self):
        try:
            launch_dialogue_board = self._load_symbol_from_file(
                "Z Axis/Z+3_Trinity/tools/open_dialogue_board.py",
                "launch_dialogue_board",
            )
            launch_dialogue_board(parent=self.root)
            self._append_activity("Opened Open Dialogue Board.")
        except Exception as e:
            messagebox.showerror("Open Dialogue", f"Failed to open board:\n{e}", parent=self.root)

    def open_smart_settings(self, focus_section: str = "", context: Optional[Dict[str, str]] = None):
        try:
            SmartSettingsHub = self._load_symbol_from_file(
                "Z Axis/Z+3_Trinity/ui/smart_settings_hub.py",
                "SmartSettingsHub",
            )
            hub = SmartSettingsHub(self.root)
            hub.open_dialog_with_context(context=context, focus_section=focus_section)
            self._append_activity("Opened Smart Settings Hub.")
        except Exception as e:
            messagebox.showerror("Settings", f"Failed to open Settings Hub:\n{e}", parent=self.root)

    def open_it_portal(self):
        try:
            ITPortal = self._load_symbol_from_file("Z Axis/Z+3_Trinity/ui/it_portal.py", "ITPortal")
            colors = {
                "bg_dark": "#0b121a",
                "bg_panel": "#101a25",
                "bg_blue": "#001B3F",
                "accent": "#00FFFF",
                "accent_cyan": "#00FFFF",
                "text_green": "#00FF88",
                "text_cyan": "#00DDFF",
                "text_white": "#FFFFFF",
                "button_green": "#00AA00",
                "button_orange": "#FF9900",
                "error_red": "#FF3333",
                "warning_orange": "#FF9900",
                "success_green": "#00FF00",
            }
            user = {"username": "it_founder", "role": "it_founder", "clearance": 5}
            ITPortal(parent=self.root, user=user, colors=colors, z_floors_available={})
            self._append_activity("Opened IT Portal.")
        except Exception as e:
            messagebox.showerror("IT Portal", f"Failed to open IT Portal:\n{e}", parent=self.root)

    def open_oracle_panel(self):
        try:
            OracleUIPanel = self._load_symbol_from_file(
                "Z Axis/Z-2_Oracle/components/oracle_ui_panel.py",
                "OracleUIPanel",
            )
            OracleUIPanel(parent=self.root).open_panel()
            self._append_activity("Opened Oracle Ingestion Panel.")
        except Exception as e:
            messagebox.showerror("Oracle", f"Failed to open Oracle panel:\n{e}", parent=self.root)

    def open_smith_gpt_importer(self):
        try:
            SmithPortalGlass = self._load_symbol_from_file(
                "Z Axis/Z-3_Smith/components/smith_portal_glass.py",
                "SmithPortalGlass",
            )
            portal = SmithPortalGlass(parent=self.root)
            try:
                portal.lift()
            except Exception:
                pass
            portal.open_gpt_export_importer()
            self._append_activity("Opened Smith GPT Export Importer.")
        except Exception as e:
            messagebox.showerror("Smith", f"Failed to open Smith importer:\n{e}", parent=self.root)

    def open_chat_browser(self):
        try:
            launch_chat_browser = self._load_symbol_from_file(
                "Z Axis/Z+3_Trinity/ui/dashboard_widgets.py",
                "launch_chat_browser",
            )
            launch_chat_browser(parent=self.root)
            self._append_activity("Opened Chat Conversations Browser.")
        except Exception as e:
            messagebox.showerror("Chat Browser", f"Failed to open chat browser:\n{e}", parent=self.root)

    def open_collaboration_hub(self):
        try:
            TrinityCollaborationHub = self._load_symbol_from_file(
                "Z Axis/Z+3_Trinity/components/trinity_collaboration_hub.py",
                "TrinityCollaborationHub",
            )
            hub = TrinityCollaborationHub(self.lightspeed_root, parent=self.root)
            hub.run()
            self._append_activity("Opened Collaboration Hub.")
        except Exception as e:
            messagebox.showerror("Collaboration Hub", f"Failed to open collaboration hub:\n{e}", parent=self.root)

    def sync_open_dialogue_to_db(self):
        try:
            sync_open_dialogue_to_db = self._load_symbol_from_file(
                "Z Axis/Z-3_Smith/tools/sync_open_dialogue_to_db.py",
                "sync_open_dialogue_to_db",
            )
            from pathlib import Path
            import json as _json

            # Use the platform DB from config; keep company unset (NULL) unless user ties it later.
            db_path = self._db_path()
            log_path = (self.lightspeed_root / "ai_logs" / "open_dialogue" / "live_conversation.jsonl").resolve()
            res = sync_open_dialogue_to_db(db_path=Path(db_path), log_path=Path(log_path), company_id=None)
            self._append_activity("Synced Open Dialogue → DB.")
            try:
                messagebox.showinfo("Sync Complete", _json.dumps(res, indent=2), parent=self.root)
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Sync Open Dialogue", f"Failed to sync Open Dialogue:\n{e}", parent=self.root)

    def open_tower_view(self):
        try:
            show_tower_3d_view = self._load_symbol_from_file(
                "Z Axis/Z0_TheConstruct/ui/tower_3d_view.py",
                "show_tower_3d_view",
            )
            show_tower_3d_view(parent=self.root)
            self._append_activity("Opened Tower View.")
        except Exception as e:
            messagebox.showerror("Tower View", f"Failed to open Tower view:\n{e}", parent=self.root)

    def open_immersive_3d(self):
        try:
            launch_immersive_3d_environment = self._load_symbol_from_file(
                "Z Axis/Z0_TheConstruct/ui/immersive_3d_engine.py",
                "launch_immersive_3d_environment",
            )
            launch_immersive_3d_environment(parent=self.root)
            self._append_activity("Opened Immersive 3D.")
        except Exception as e:
            messagebox.showerror("Immersive 3D", f"Failed to open Immersive 3D:\n{e}", parent=self.root)

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
    portal = TrinityPortalGlass()
    portal.run()


if __name__ == "__main__":
    main()
