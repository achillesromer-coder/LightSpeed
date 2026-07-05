#!/usr/bin/env python
"""
Merovingian (Z-4) - System Health & Diagnostics Floor
Complete Floor Coordinator with System Monitoring, Logging, and Performance Metrics

Merovingian is the primary system health, diagnostics, telemetry, and audit layer. It holds:
- System health monitoring and metrics
- Compact activity tables and queryable activity DB
- Runtime exports, finalization overviews, and closure readiness
- Performance tracking and profiling
- Error tracking, telemetry, and audit evidence

Variables Held:
- system_health: Current system health metrics
- log_buffer: Aggregated system logs and compact activity-table summaries
- performance_metrics: Performance data and trends
- error_log: Tracked errors and exceptions
- resource_usage: CPU, memory, disk utilization

Renders:
- Merovingian portal (glass UI dashboard)
- Activity table and audit evidence surfaces
- System health monitor
- Log viewer and filter
- Performance metrics charts
- Error tracking interface
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Optional, Dict, List, Any
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import os
import re


def _load_symbol(rel_path: str, symbol: str):
    """Load a symbol (class/function) from a file by relative path"""
    root = Path(__file__).resolve().parents[1]
    path = (root / rel_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
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


# Backwards compatibility
_load_class = _load_symbol


class MerovingianFloorState:
    """
    State manager for Merovingian floor

    This class holds all state variables for system health and diagnostics
    """

    def __init__(self):
        # System health state
        self.system_health: Dict[str, Any] = {
            'status': 'healthy',
            'uptime': 0,
            'last_check': None
        }
        self.health_history: List[Dict] = []

        # Logging state
        self.log_buffer: List[Dict[str, Any]] = []
        self.log_level = 'INFO'
        self.max_log_entries = 10000

        # Performance metrics
        self.performance_metrics: Dict[str, List[float]] = {
            'cpu': [],
            'memory': [],
            'disk': []
        }
        self.performance_alerts: List[Dict] = []

        # Error tracking
        self.error_log: List[Dict[str, Any]] = []
        self.total_errors = 0
        self.critical_errors = 0

        # Resource usage
        self.resource_usage: Dict[str, float] = {
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'disk_percent': 0.0
        }

    def log(self, level: str, message: str, source: str):
        """Add a log entry"""
        entry = {
            'level': level,
            'message': message,
            'source': source,
            'timestamp': None  # Would use datetime in production
        }
        self.log_buffer.append(entry)
        if len(self.log_buffer) > self.max_log_entries:
            self.log_buffer.pop(0)

    def record_error(self, error: str, critical: bool = False):
        """Record an error"""
        self.error_log.append({
            'error': error,
            'critical': critical,
            'timestamp': None
        })
        self.total_errors += 1
        if critical:
            self.critical_errors += 1


class MerovingianUI(ttk.Frame):
    """
    Primary Merovingian UI - System Health & Diagnostics

    Merovingian owns all system monitoring, logging, performance tracking, and diagnostics.
    It provides comprehensive visibility into system health and operation.
    """

    def __init__(self, parent: tk.Misc, app: Optional[object] = None, *, compact: bool = False, **_ignored):
        super().__init__(parent)
        self.app = app
        self.compact = bool(compact)
        self.state = MerovingianFloorState()

        try:
            from core.services import get_db, get_event_bus, get_storage
            self.db = getattr(app, "db", None) or get_db()
            self.event_bus = getattr(app, "event_bus", None) or get_event_bus()
            self.storage = getattr(app, "storage", None) or get_storage()
        except Exception:
            self.db = None
            self.event_bus = None
            self.storage = None

        # Register Bento widgets
        self._register_bento_widgets()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Tabs
        self._tabs: Dict[str, ttk.Frame] = {}
        self._builders: Dict[str, Any] = {}
        self._tab_group: Dict[str, str] = {}
        self._tab_container: Dict[str, Any] = {}
        self._group_frames: Dict[str, ttk.Frame] = {}

        if self.compact:
            self._build_compact_shell()
        else:
            self._build_full_shell()

    def _build_full_shell(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self._register_tab("Portal", self._build_portal)
        # NOTE: IT Portal should not be a dumping ground; Merovingian owns health/diagnostics/tools here.
        self._register_tab("System Metrics", self._build_system_metrics)
        self._register_tab("Logs", self._build_logs)
        self._register_tab("Database Browser", self._build_database_browser)
        self._register_tab("Performance Profiler", self._build_performance_profiler)

        self._ensure_built("Portal")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _build_compact_shell(self) -> None:
        """
        Compact embedding for IT Portal:
        - Portal (single surface)
        - Diagnostics (metrics/logs/profiler)
        - Data (DB browser)
        """
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        portal_group = ttk.Frame(self.notebook)
        diag_group = ttk.Frame(self.notebook)
        data_group = ttk.Frame(self.notebook)

        self.notebook.add(portal_group, text="Portal")
        self.notebook.add(diag_group, text="Diagnostics")
        self.notebook.add(data_group, text="Data")

        self._group_frames = {
            "Portal": portal_group,
            "Diagnostics": diag_group,
            "Data": data_group,
        }

        self._tabs["Portal"] = portal_group
        self._builders["Portal"] = self._build_portal
        self._tab_group["Portal"] = "Portal"
        self._tab_container["Portal"] = None

        diag_nb = ttk.Notebook(diag_group)
        diag_nb.pack(fill="both", expand=True)
        self._register_tab("System Metrics", self._build_system_metrics, notebook=diag_nb, group="Diagnostics")
        self._register_tab("Logs", self._build_logs, notebook=diag_nb, group="Diagnostics")
        self._register_tab("Performance Profiler", self._build_performance_profiler, notebook=diag_nb, group="Diagnostics")

        data_nb = ttk.Notebook(data_group)
        data_nb.pack(fill="both", expand=True)
        self._register_tab("Database Browser", self._build_database_browser, notebook=data_nb, group="Data")

        self._ensure_built("Portal")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_group_tab_changed)
        diag_nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        data_nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _register_tab(self, title: str, builder, *, notebook: Optional[ttk.Notebook] = None, group: str = "Portal"):
        """Register a lazy-loaded tab (supports nested notebooks in compact mode)."""
        nb = notebook or self.notebook
        frame = ttk.Frame(nb)
        nb.add(frame, text=title)
        self._tabs[title] = frame
        self._builders[title] = builder
        self._tab_group[title] = group
        self._tab_container[title] = nb

    def _ensure_built(self, title: str):
        """Ensure tab is built"""
        frame = self._tabs.get(title)
        builder = self._builders.get(title)
        if frame is None or builder is None:
            return
        if getattr(frame, "_built", False):
            return
        builder(frame)
        setattr(frame, "_built", True)

    def _on_tab_changed(self, event):
        """Handle tab change - lazy load content"""
        nb = getattr(event, "widget", None) or self.notebook
        current_tab = nb.select()
        tab_text = nb.tab(current_tab, "text")
        self._ensure_built(tab_text)

    def _on_group_tab_changed(self, _event):
        """When switching compact groups, ensure the visible leaf is built."""
        try:
            group = self.notebook.tab(self.notebook.select(), "text")
        except Exception:
            return
        if group == "Portal":
            self._ensure_built("Portal")
            return
        try:
            grp_frame = self._group_frames.get(group)
            if grp_frame is None:
                return
            children = [w for w in grp_frame.winfo_children() if isinstance(w, ttk.Notebook)]
            if not children:
                return
            nb = children[0]
            leaf = nb.tab(nb.select(), "text")
            self._ensure_built(leaf)
        except Exception:
            return

    def select_tab(self, title: str) -> None:
        """Select a leaf tab by title, regardless of compact/full shell."""
        if title not in self._tabs:
            return
        if not self.compact:
            try:
                self.notebook.select(self._tabs[title])
            except Exception:
                pass
            self._ensure_built(title)
            return
        group = self._tab_group.get(title) or "Portal"
        try:
            self.notebook.select(self._group_frames[group])
        except Exception:
            pass
        if group == "Portal":
            self._ensure_built("Portal")
            return
        nb = self._tab_container.get(title)
        if nb is not None:
            try:
                nb.select(self._tabs[title])
            except Exception:
                pass
        self._ensure_built(title)

    def _build_portal(self, parent: ttk.Frame):
        """Build portal dashboard tab"""
        try:
            from core.ui.base_portal_glass import mount_smart_ops_strip  # type: ignore

            mount_smart_ops_strip(parent, app=self.app, floor_channel="Z-4", it_portal=self.compact, title="Merovingian Ops")
        except Exception:
            pass
        try:
            Portal = _load_class("Z Axis/Z-4_Merovingian/components/merovingian_portal_glass.py", "MerovingianPortalGlass")
            ui = Portal(parent)
            ui.pack(fill="both", expand=True)
        except Exception as e:
            ttk.Label(parent, text=f"Merovingian Portal unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )

    def _build_system_metrics(self, parent: ttk.Frame):
        """Build system metrics (health) tab."""
        ttk.Label(parent, text="System Metrics (Merovingian)", font=("Consolas", 14, "bold")).pack(pady=(10, 6))
        ttk.Label(
            parent,
            text=(
                "If psutil is installed, the full SystemMetrics GUI will load.\n"
                "Otherwise this tab stays informational."
            ),
            justify="left",
        ).pack(padx=12, pady=(0, 10), anchor="w")

        try:
            Metrics = _load_class("Z Axis/Z-4_Merovingian/components/system_metrics.py", "SystemMetricsGUI")
            ui = Metrics(parent)
            ui.pack(fill="both", expand=True, padx=10, pady=10)
        except Exception as e:
            ttk.Label(parent, text=f"SystemMetricsGUI unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )

    def _build_logs(self, parent: ttk.Frame):
        """Build log viewer tab (reads floor log files; no terminal required)."""
        ttk.Label(parent, text="Logs (Merovingian)", font=("Consolas", 14, "bold")).pack(pady=(10, 6))

        logs_dir = Path(__file__).parent / "Z-4_Merovingian" / "data" / "logs"
        if not logs_dir.exists():
            ttk.Label(parent, text=f"Log directory missing: {logs_dir}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )
            return

        controls = ttk.Frame(parent)
        controls.pack(fill="x", padx=10, pady=(0, 8))

        ttk.Label(controls, text="File:").pack(side="left")
        file_var = tk.StringVar(value="")
        file_combo = ttk.Combobox(controls, textvariable=file_var, state="readonly", width=42)
        file_combo.pack(side="left", padx=(6, 12))

        ttk.Label(controls, text="Filter:").pack(side="left")
        filter_var = tk.StringVar(value="")
        ttk.Entry(controls, textvariable=filter_var, width=28).pack(side="left", padx=(6, 0))

        body = ttk.Frame(parent)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        text = scrolledtext.ScrolledText(body, height=24, bg="#1e1e1e", fg="#00FF88", font=("Consolas", 9))
        text.pack(fill="both", expand=True)

        def _list_files() -> List[str]:
            items: List[str] = []
            try:
                for p in sorted(logs_dir.iterdir(), key=lambda x: x.name.lower()):
                    if p.is_file() and p.suffix.lower() in (".jsonl", ".log", ".txt", ".json"):
                        items.append(p.name)
            except Exception:
                pass
            return items

        def _tail_bytes(path: Path, *, max_bytes: int = 1_250_000) -> str:
            try:
                size = path.stat().st_size
            except Exception:
                size = 0
            try:
                with path.open("rb") as f:
                    if size > max_bytes:
                        f.seek(-max_bytes, 2)
                    data = f.read()
                return data.decode("utf-8", errors="replace")
            except Exception:
                try:
                    return path.read_text(encoding="utf-8", errors="replace")
                except Exception as e:
                    return f"[error reading file] {e}"

        def _apply_filter(content: str) -> str:
            q = (filter_var.get() or "").strip()
            if not q:
                return content
            out: List[str] = []
            try:
                rx = re.compile(q, re.IGNORECASE)
                for line in content.splitlines():
                    if rx.search(line):
                        out.append(line)
            except Exception:
                ql = q.lower()
                for line in content.splitlines():
                    if ql in line.lower():
                        out.append(line)
            return "\n".join(out)

        def _load_selected():
            name = (file_var.get() or "").strip()
            if not name:
                return
            p = logs_dir / name
            if not p.exists():
                return
            raw = _tail_bytes(p)
            view = _apply_filter(raw)
            try:
                text.delete("1.0", tk.END)
                text.insert(tk.END, view)
                text.see(tk.END)
            except Exception:
                pass

        def _refresh_files():
            files = _list_files()
            file_combo["values"] = files
            if files and not file_var.get():
                file_var.set(files[-1])
            _load_selected()

        ttk.Button(controls, text="Refresh", command=_refresh_files).pack(side="right")

        file_combo.bind("<<ComboboxSelected>>", lambda _e: _load_selected())
        filter_var.trace_add("write", lambda *_: _load_selected())
        _refresh_files()

    def _build_database_browser(self, parent: ttk.Frame):
        """Build database browser tab (operator tool owned by Merovingian)."""
        ttk.Label(parent, text="Database Browser (Merovingian)", font=("Consolas", 14, "bold")).pack(pady=(10, 6))

        quick = ttk.Frame(parent)
        quick.pack(fill="x", padx=10, pady=(0, 10))

        db_path = ""
        try:
            db_path = str(getattr(self.db, "db_path", "") or "")
        except Exception:
            db_path = ""
        if not db_path:
            try:
                db_path = str(getattr(self.db, "path", "") or "")
            except Exception:
                db_path = ""

        ttk.Label(quick, text=f"Default DB: {db_path or '(unknown)'}").pack(side="left")

        try:
            Browser = _load_class("Z Axis/Z-4_Merovingian/components/db_browser.py", "DatabaseBrowser")
            ui = Browser(parent)
            ui.pack(fill="both", expand=True, padx=10, pady=10)

            def _connect_default():
                p = db_path
                if not p:
                    return
                try:
                    fn = getattr(ui, "connect_sqlite_path", None)
                    if callable(fn):
                        fn(p)
                    else:
                        from tkinter import messagebox
                        messagebox.showinfo("Database", "Use 'Connect SQLite' and select the DB file.", parent=self.winfo_toplevel())
                except Exception:
                    return

            ttk.Button(quick, text="Connect Default DB", command=_connect_default).pack(side="right")
        except Exception as e:
            ttk.Label(parent, text=f"DatabaseBrowser unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )

    def _build_performance_profiler(self, parent: ttk.Frame):
        """Build performance profiler tab (operator tool owned by Merovingian)."""
        ttk.Label(parent, text="Performance Profiler (Merovingian)", font=("Consolas", 14, "bold")).pack(pady=(10, 6))
        try:
            Profiler = _load_class("Z Axis/Z-4_Merovingian/components/performance_profiler.py", "PerformanceProfilerGUI")
            ui = Profiler(parent)
            ui.pack(fill="both", expand=True, padx=10, pady=10)
        except Exception as e:
            ttk.Label(parent, text=f"PerformanceProfilerGUI unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )


    def _register_bento_widgets(self):
        """Register Merovingian widgets with Bento system"""
        try:
            import sys
            trinity_path = Path(__file__).parent / "Z+3_Trinity"
            if str(trinity_path) not in sys.path:
                sys.path.insert(0, str(trinity_path))

            from ui.universal_bento_system import register_floor_widgets, BentoWidget, BentoWidgetType

            widgets = [
                BentoWidget(
                    id="merovingian_system_health",
                    title="System Metrics",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z-4_Merovingian",
                    callback=lambda w: self._open_system_metrics(),
                    config={"icon": "HEALTH", "description": "View system health/metrics"}
                ),
                BentoWidget(
                    id="merovingian_log_viewer",
                    title="Logs",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z-4_Merovingian",
                    callback=lambda w: self._open_logs(),
                    config={"icon": "LOGS", "description": "Browse system logs"}
                ),
                BentoWidget(
                    id="merovingian_performance",
                    title="Profiler",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z-4_Merovingian",
                    callback=lambda w: self._open_profiler(),
                    config={"icon": "PERF", "description": "Profile performance"}
                ),
                BentoWidget(
                    id="merovingian_db_browser",
                    title="Database Browser",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z-4_Merovingian",
                    callback=lambda w: self._open_database_browser(),
                    config={"icon": "DB", "description": "Browse database (operator tool)"}
                )
            ]

            register_floor_widgets("Z-4_Merovingian", widgets)
            print("[Merovingian] Registered Merovingian Bento widgets")
        except Exception as e:
            print(f"[Merovingian] Could not register Bento widgets: {e}")
    def _open_system_metrics(self):
        """Open system metrics tab."""
        print("[Merovingian] Opening System Metrics...")
        self.select_tab("System Metrics")

    def _open_logs(self):
        """Open logs tab."""
        print("[Merovingian] Opening Logs...")
        self.select_tab("Logs")

    def _open_profiler(self):
        """Open performance profiler tab."""
        print("[Merovingian] Opening Performance Profiler...")
        self.select_tab("Performance Profiler")

    def _open_database_browser(self):
        """Open database browser tab."""
        print("[Merovingian] Opening Database Browser...")
        self.select_tab("Database Browser")


def create_gui(*args, **kwargs):
    """
    N.py / IT Portal integration entry point.

    Supported call shapes:
    - create_gui(parent, colors)
    - create_gui(app, parent, colors)
    """
    app = None
    parent = None
    if args and isinstance(args[0], tk.Misc):
        parent = args[0]
    elif len(args) >= 2 and isinstance(args[1], tk.Misc):
        app = args[0]
        parent = args[1]
    if parent is None:
        return None
    compact = bool(kwargs.get("compact") or kwargs.get("it_portal"))
    return MerovingianUI(parent, app=app, compact=compact)


def build(*args, **kwargs):
    """Alias for legacy floor loaders."""
    return create_gui(*args, **kwargs)


# ---------------------------------------------------------------------------
# Floor boot hook (used by FloorLoader)
# ---------------------------------------------------------------------------

_MEROVINGIAN_INITIALIZED = False
MEROVINGIAN_RUNTIME: Dict[str, Any] = {}


def initialize(*, components: Optional[Dict[str, Any]] = None, dependencies: Optional[Dict[str, Any]] = None, **_kwargs) -> bool:
    """
    Initialize Merovingian floor runtime services.

    This runs during floor bootstrap (no UI) and ensures Merovingian's
    background services and integrations are active.

    Args:
        components: Pre-loaded component classes/instances
        dependencies: Shared services (db, event_bus, storage, logger)
        **_kwargs: Additional platform parameters

    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    global _MEROVINGIAN_INITIALIZED, MEROVINGIAN_RUNTIME
    if _MEROVINGIAN_INITIALIZED:
        return True
    _MEROVINGIAN_INITIALIZED = True

    try:
        # Merovingian provides the basement services; the stable import path is `core.services`.
        # Avoid invalid module names like `Z-4_Merovingian` in dotted imports.
        from core.services import get_db, get_event_bus, get_storage, get_logger  # type: ignore

        db = get_db()
        event_bus = get_event_bus()
        storage = get_storage()
        logger = get_logger()
    except Exception as e:
        print(f"[Merovingian] Failed to load core services: {e}")
        db = None
        event_bus = None
        storage = None
        logger = None

    MEROVINGIAN_RUNTIME["db"] = db
    MEROVINGIAN_RUNTIME["event_bus"] = event_bus
    MEROVINGIAN_RUNTIME["storage"] = storage
    MEROVINGIAN_RUNTIME["logger"] = logger

    # Floor-specific initialization

    # Start health monitoring service
    try:
        from core.services import get_predictive_maintenance_engine  # type: ignore
        pm_engine = get_predictive_maintenance_engine()
        MEROVINGIAN_RUNTIME["predictive_maintenance"] = pm_engine
        if logger:
            logger.info("[Merovingian] Predictive maintenance engine initialized")
    except Exception as e:
        MEROVINGIAN_RUNTIME["pm_error"] = str(e)

    # Initialize system diagnostics
    if db:
        try:
            # Log initial system health
            health_data = {
                "cpu_available": True,
                "memory_available": True,
                "disk_available": True,
                "timestamp": "system_start"
            }
            MEROVINGIAN_RUNTIME["initial_health"] = health_data
        except Exception as e:
            if logger:
                logger.debug(f"[Merovingian] Health logging skipped: {e}")


    # Subscribe to relevant events
    if event_bus:
        try:
            event_bus.subscribe("system.health.check", _on_health_check)
        except Exception as e:
            if logger:
                logger.warning(f"[Merovingian] Event subscription failed: {e}")

    # Publish floor ready event
    if event_bus:
        try:
            event_bus.publish("merovingian.floor.ready", {
                "floor": "Merovingian",
                "z_level": -4,
                "capabilities": ['system_health', 'diagnostics', 'predictive_maintenance', 'monitoring']
            })
        except Exception as e:
            if logger:
                logger.warning(f"[Merovingian] Failed to publish ready event: {e}")

    if logger:
        logger.info("[Merovingian] Floor initialized successfully")

    return True


def _on_health_check(event):
    """Respond to health check events"""
    event_bus = MEROVINGIAN_RUNTIME.get("event_bus")
    if event_bus:
        try:
            event_bus.publish("merovingian.health.status", {
                "floor": "Merovingian",
                "status": "operational",
                "z_level": -4
            })
        except Exception:
            pass

def main() -> int:
    root = tk.Tk()
    root.title("Merovingian (Z-4) - System Health")
    root.geometry("1200x800")
    MerovingianUI(root).pack(fill="both", expand=True)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
