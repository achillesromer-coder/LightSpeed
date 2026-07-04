#!/usr/bin/env python
"""
Oracle Smart Floor UI Panel - Ingestion Control Center
Visual control panel for Oracle's continuous file ingestion system

Provides:
- Start/Stop/Pause ingestion controls
- Real-time monitoring dashboard
- CPU/Memory usage graphs
- File processing statistics
- Multi-select and batch operations
- Priority queue management
- Extracted objects browser
- Floor routing visualization

Author: LightSpeed Team / ACHILLES
Version: 0.9.11+
Date: January 4, 2026
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import time
from datetime import datetime
import threading
import queue
import importlib.util
import sqlite3

# Setup paths (robust to folder migrations)
ORACLE_ROOT = Path(__file__).parent.resolve()

def _find_lightspeed_root(start: Path) -> Path:
    start = start.resolve()
    for candidate in (start, *start.parents):
        try:
            if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
                return candidate
        except Exception:
            continue
    try:
        cwd = Path.cwd().resolve()
        if (cwd / "N.py").exists() and (cwd / "Z Axis").exists():
            return cwd
    except Exception:
        pass
    return start.parent


LIGHTSPEED_ROOT = _find_lightspeed_root(Path(__file__))
for _p in (
    LIGHTSPEED_ROOT,
    LIGHTSPEED_ROOT / "Z Axis",
    # Core services live under Merovingian (floor-native)
    LIGHTSPEED_ROOT / "Z Axis" / "Z-4_Merovingian",
    # Wizards live under Trinity (floor-native)
    LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity",
):
    try:
        if _p.exists():
            sys.path.insert(0, str(_p))
    except Exception:
        pass

try:
    from core.config.paths import ORACLE_ROOT as ORACLE_PATH, SMITH_LOGS  # type: ignore
    HAS_PATHS = True
except Exception:
    print("[WARNING] Path configuration not available")
    HAS_PATHS = False
    SMITH_LOGS = Path(LIGHTSPEED_ROOT) / "Z Axis" / "Z-3_Smith" / "logs"

# Try to import the Oracle integrator and provide a compatibility wrapper so the UI can run.
# `SmartFloorIngestion` was a legacy prototype; the canonical implementation is now
# `OracleSmartFloorIntegrator` (DB-backed queue + processing).
try:
    sys.path.insert(0, str(ORACLE_ROOT))
except Exception:
    pass

try:
    from oracle_smart_floor_integrator import OracleSmartFloorIntegrator
    HAS_INGESTION = True
except Exception as _e:
    OracleSmartFloorIntegrator = None  # type: ignore[assignment]
    HAS_INGESTION = False
    print(f"[WARNING] OracleSmartFloorIntegrator not available: {_e}")


class SmartFloorIngestion:
    """
    Compatibility wrapper used by the Oracle UI Panel.

    Exposes a small subset of the historical `SmartFloorIngestion` API while delegating
    to `OracleSmartFloorIntegrator` (DB-backed ingestion + processing).
    """

    def __init__(self):
        if OracleSmartFloorIntegrator is None:
            raise ImportError("OracleSmartFloorIntegrator not importable")

        self._integrator = OracleSmartFloorIntegrator()
        self._stop_event = threading.Event()

        # UI-tunable knobs (best-effort; CPU limiting is not enforced in this lightweight adapter)
        self.MAX_CPU_PERCENT = 15
        self.BATCH_SIZE = 5

        # Simple live counters used by the UI panel
        self.processed_files = set()
        self.error_files = set()

        # Legacy field expected by the panel (used only for "Clear Queue")
        self.task_queue: "queue.Queue[dict]" = queue.Queue()

        # Mimic the legacy ingestion object stats interface
        self.stats: Dict[str, Any] = {"current_cpu": 0.0}

    def add_file(self, file_path: Path, *, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = self._integrator.ingest_file(str(file_path), metadata=metadata or {})
        try:
            self.task_queue.put_nowait(res)
        except Exception:
            pass
        return res

    def add_directory(
        self,
        folder: Path,
        *,
        recursive: bool = True,
        priority: int = 5,
        include_extensions: Optional[set] = None,
        exclude_dirs: Optional[set] = None,
    ) -> Dict[str, Any]:
        folder = Path(folder)
        include_extensions = {str(e).lower() for e in (include_extensions or set())}
        exclude_dirs = exclude_dirs or set()

        submitted = 0
        failed = 0

        it = folder.rglob("*") if recursive else folder.glob("*")
        for fp in it:
            try:
                if not fp.is_file():
                    continue
                if exclude_dirs and any(part in exclude_dirs for part in fp.parts):
                    continue
                if include_extensions and fp.suffix.lower() not in include_extensions:
                    continue

                meta = {"priority": int(priority), "source": "oracle_ui_panel", "folder": str(folder)}
                res = self.add_file(fp, metadata=meta)
                if res.get("success"):
                    submitted += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

        return {"success": True, "submitted": submitted, "failed": failed}

    def start_continuous(self):
        """Process queued DB tasks in a loop until stopped."""
        self._stop_event.clear()
        while not self._stop_event.is_set():
            try:
                results = self._integrator.process_pending_tasks(max_tasks=int(self.BATCH_SIZE or 1))
            except Exception:
                results = []

            for r in results:
                try:
                    if r.get("success"):
                        self.processed_files.add(r.get("vault_id") or r.get("task_id") or len(self.processed_files) + 1)
                    else:
                        self.error_files.add(r.get("task_id") or len(self.error_files) + 1)
                except Exception:
                    continue

            # Keep the loop responsive without burning CPU.
            time.sleep(0.4)

    def stop(self):
        self._stop_event.set()

    def get_queue_status(self) -> Dict[str, Any]:
        try:
            return self._integrator.get_queue_status()
        except Exception:
            return {"total_tasks": 0, "completed": 0, "pending": 0, "failed": 0}

    def clear_pending_tasks(self) -> int:
        """
        Best-effort: mark queued/pending tasks as canceled in the DB.
        Returns the number of rows affected.
        """
        try:
            if getattr(self._integrator, "db", None) is None:
                return 0
            return int(
                self._integrator.db.execute_update(  # type: ignore[union-attr]
                    "UPDATE oracle_ingestion_tasks SET status = 'canceled' WHERE status IN ('queued', 'pending')"
                )
            )
        except Exception:
            return 0

# Ensure log directory exists
SMITH_LOGS.mkdir(parents=True, exist_ok=True)


class OracleUIPanel:
    """
    Oracle Smart Floor UI Panel

    Visual control center for managing the Oracle continuous ingestion system.
    Provides real-time monitoring, control, and analytics.
    """

    # Color scheme
    COLORS = {
        'bg': '#0A1628',
        'header': '#102040',
        'card': '#1E3A5F',
        'card_hover': '#2A5A8F',
        'accent': '#FF8000',  # Oracle orange
        'text': '#FFFFFF',
        'text_dim': '#AAAAAA',
        'success': '#00FF00',
        'warning': '#FFAA00',
        'error': '#FF0000',
        'active': '#00FF00',
        'inactive': '#FF0000'
    }

    def __init__(self, parent: Optional[tk.Tk] = None):
        """Initialize Oracle UI panel"""
        self.parent = parent
        self.window = None

        # Ingestion system
        self.ingestion = None
        self.is_running = False
        self.monitoring_thread = None
        self.should_monitor = False

        # Statistics
        self.stats = {
            'files_processed': 0,
            'objects_extracted': 0,
            'errors': 0,
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'processing_rate': 0.0,
            'start_time': None
        }

        # Recent activity
        self.recent_files = []
        self.recent_objects = []

    def open_panel(self, initial_tab: str = ""):
        """Open Oracle UI panel"""
        if self.parent:
            self.window = tk.Toplevel(self.parent)
        else:
            self.window = tk.Tk()

        self.window.title("Oracle Smart Floor - Ingestion Control Center")
        self.window.geometry("1200x800")
        self.window.configure(bg=self.COLORS['bg'])

        # Center window
        self._center_window()

        # Create UI
        self._create_ui()

        # Start monitoring if ingestion is available
        if HAS_INGESTION:
            self._start_monitoring()

        # Best-effort: select a specific observability tab (e.g., Durable Registry).
        if initial_tab:
            try:
                self.select_tab(initial_tab)
            except Exception:
                pass

        # Make modal if has parent
        if self.parent:
            self.window.transient(self.parent)
            try:
                self.window.grab_set()
            except Exception:
                pass

        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        if not self.parent:
            self.window.mainloop()
        return self.window

    def select_tab(self, tab_text: str) -> bool:
        """Select a tab within the Oracle Observability notebook (best-effort)."""
        tab_text = str(tab_text or "").strip()
        if not tab_text:
            return False
        nb = getattr(self, "monitoring_notebook", None)
        if nb is None or not hasattr(nb, "tabs"):
            return False
        try:
            for tab_id in nb.tabs():
                try:
                    t = str(nb.tab(tab_id, "text") or "")
                except Exception:
                    t = ""
                if not t:
                    continue
                if tab_text.lower() in t.lower() or t.lower() in tab_text.lower():
                    nb.select(tab_id)
                    return True
        except Exception:
            return False
        return False

    def _center_window(self):
        """Center window on screen"""
        self.window.update_idletasks()
        width = 1200
        height = 800
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

    def _create_ui(self):
        """Create main UI"""
        # Header
        header = tk.Frame(self.window, bg=self.COLORS['header'], height=90)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)

        # Logo/icon (colored square)
        logo_frame = tk.Frame(header, bg=self.COLORS['accent'], width=60, height=60)
        logo_frame.place(x=20, y=15)

        tk.Label(
            logo_frame,
            text="O",
            font=('Segoe UI', 30, 'bold'),
            bg=self.COLORS['accent'],
            fg=self.COLORS['bg']
        ).place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(
            header,
            text="Oracle Smart Floor",
            font=('Segoe UI', 22, 'bold'),
            bg=self.COLORS['header'],
            fg=self.COLORS['accent']
        ).place(x=95, y=18)

        tk.Label(
            header,
            text="Continuous Ingestion Control Center",
            font=('Segoe UI', 11),
            bg=self.COLORS['header'],
            fg=self.COLORS['text_dim']
        ).place(x=95, y=50)

        # Status indicator
        self.status_frame = tk.Frame(header, bg=self.COLORS['header'])
        self.status_frame.place(x=1020, y=25)

        self.status_indicator = tk.Label(
            self.status_frame,
            text="●",
            font=('Segoe UI', 20),
            bg=self.COLORS['header'],
            fg=self.COLORS['inactive']
        )
        self.status_indicator.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(
            self.status_frame,
            text="Inactive",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['header'],
            fg=self.COLORS['text_dim']
        )
        self.status_label.pack(side=tk.LEFT)

        # Main content area
        content = tk.Frame(self.window, bg=self.COLORS['bg'])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Left panel - Controls and stats
        left_panel = tk.Frame(content, bg=self.COLORS['bg'], width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))

        self._create_controls_section(left_panel)
        self._create_stats_section(left_panel)

        # Right panel - Activity and monitoring
        right_panel = tk.Frame(content, bg=self.COLORS['bg'])
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        self._create_activity_section(right_panel)
        self._create_monitoring_section(right_panel)

    def _create_controls_section(self, parent):
        """Create controls section"""
        section = tk.LabelFrame(
            parent,
            text="Ingestion Controls",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            relief=tk.FLAT,
            padx=15,
            pady=15
        )
        section.pack(fill=tk.X, pady=(0, 15))

        # Control buttons
        btn_frame = tk.Frame(section, bg=self.COLORS['card'])
        btn_frame.pack(fill=tk.X, pady=10)

        self.start_btn = tk.Button(
            btn_frame,
            text="▶ Start",
            command=self._start_ingestion,
            bg='#00AA00',
            fg=self.COLORS['text'],
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            state=tk.NORMAL if HAS_INGESTION else tk.DISABLED
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.pause_btn = tk.Button(
            btn_frame,
            text="⏸ Pause",
            command=self._pause_ingestion,
            bg=self.COLORS['warning'],
            fg=self.COLORS['bg'],
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            state=tk.DISABLED
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(
            btn_frame,
            text="■ Stop",
            command=self._stop_ingestion,
            bg=self.COLORS['error'],
            fg=self.COLORS['text'],
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Settings
        settings_frame = tk.Frame(section, bg=self.COLORS['card'])
        settings_frame.pack(fill=tk.X, pady=10)

        # CPU limit
        tk.Label(
            settings_frame,
            text="Max CPU %:",
            font=('Segoe UI', 10),
            bg=self.COLORS['card'],
            fg=self.COLORS['text']
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.cpu_limit_var = tk.DoubleVar(value=5.0)
        cpu_spinbox = ttk.Spinbox(
            settings_frame,
            from_=1.0,
            to=20.0,
            increment=1.0,
            textvariable=self.cpu_limit_var,
            width=8,
            font=('Segoe UI', 10)
        )
        cpu_spinbox.pack(side=tk.LEFT, padx=5)

        # Batch size
        tk.Label(
            settings_frame,
            text="Batch Size:",
            font=('Segoe UI', 10),
            bg=self.COLORS['card'],
            fg=self.COLORS['text']
        ).pack(side=tk.LEFT, padx=(20, 10))

        self.batch_size_var = tk.IntVar(value=5)
        batch_spinbox = ttk.Spinbox(
            settings_frame,
            from_=1,
            to=20,
            increment=1,
            textvariable=self.batch_size_var,
            width=8,
            font=('Segoe UI', 10)
        )
        batch_spinbox.pack(side=tk.LEFT, padx=5)

        # File operations
        ops_frame = tk.Frame(section, bg=self.COLORS['card'])
        ops_frame.pack(fill=tk.X, pady=(15, 5))

        tk.Button(
            ops_frame,
            text="Add Files",
            command=self._add_files,
            bg=self.COLORS['card_hover'],
            fg=self.COLORS['text'],
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            ops_frame,
            text="Add Folder",
            command=self._add_folder,
            bg=self.COLORS['card_hover'],
            fg=self.COLORS['text'],
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            ops_frame,
            text="Ingest LightSpeed",
            command=self._ingest_lightspeed_workspace,
            bg=self.COLORS['accent'],
            fg=self.COLORS['bg'],
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            ops_frame,
            text="Clear Queue",
            command=self._clear_queue,
            bg=self.COLORS['card_hover'],
            fg=self.COLORS['text'],
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)

        # Knowledge imports (Oracle -> Smith -> Merovingian DB)
        tools_frame = tk.Frame(section, bg=self.COLORS['card'])
        tools_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Button(
            tools_frame,
            text="Import GPT Export",
            command=self._import_gpt_export_ui,
            bg=self.COLORS['card_hover'],
            fg=self.COLORS['text'],
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            tools_frame,
            text="Scan Docs → Tasks",
            command=self._scan_docs_to_tasks_ui,
            bg=self.COLORS['card_hover'],
            fg=self.COLORS['text'],
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)

    def _create_stats_section(self, parent):
        """Create statistics section"""
        section = tk.LabelFrame(
            parent,
            text="Statistics",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            relief=tk.FLAT,
            padx=15,
            pady=15
        )
        section.pack(fill=tk.BOTH, expand=True)

        # Stats grid
        stats_items = [
            ('Files Processed:', 'files_processed'),
            ('Objects Extracted:', 'objects_extracted'),
            ('Errors:', 'errors'),
            ('CPU Usage:', 'cpu_usage', '%'),
            ('Memory Usage:', 'memory_usage', 'MB'),
            ('Processing Rate:', 'processing_rate', 'files/sec')
        ]

        self.stat_labels = {}

        for label, key, *unit in stats_items:
            row = tk.Frame(section, bg=self.COLORS['card'])
            row.pack(fill=tk.X, pady=6)

            tk.Label(
                row,
                text=label,
                font=('Segoe UI', 10),
                bg=self.COLORS['card'],
                fg=self.COLORS['text_dim'],
                anchor=tk.W,
                width=18
            ).pack(side=tk.LEFT)

            value_label = tk.Label(
                row,
                text="0" + (f" {unit[0]}" if unit else ""),
                font=('Segoe UI', 11, 'bold'),
                bg=self.COLORS['card'],
                fg=self.COLORS['accent'],
                anchor=tk.E
            )
            value_label.pack(side=tk.RIGHT)

            self.stat_labels[key] = (value_label, unit[0] if unit else "")

        # Uptime
        uptime_row = tk.Frame(section, bg=self.COLORS['card'])
        uptime_row.pack(fill=tk.X, pady=(15, 6))

        tk.Label(
            uptime_row,
            text="Uptime:",
            font=('Segoe UI', 10),
            bg=self.COLORS['card'],
            fg=self.COLORS['text_dim'],
            anchor=tk.W,
            width=18
        ).pack(side=tk.LEFT)

        self.uptime_label = tk.Label(
            uptime_row,
            text="00:00:00",
            font=('Segoe UI', 11, 'bold'),
            bg=self.COLORS['card'],
            fg=self.COLORS['accent'],
            anchor=tk.E
        )
        self.uptime_label.pack(side=tk.RIGHT)

    def _create_activity_section(self, parent):
        """Create activity log section"""
        section = tk.LabelFrame(
            parent,
            text="Recent Activity",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        section.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Activity list
        list_frame = tk.Frame(section, bg=self.COLORS['card'])
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")

        self.activity_list = tk.Listbox(
            list_frame,
            font=('Consolas', 9),
            bg=self.COLORS['bg'],
            fg=self.COLORS['text'],
            selectbackground=self.COLORS['accent'],
            selectforeground=self.COLORS['bg'],
            yscrollcommand=scrollbar.set,
            relief=tk.FLAT,
            highlightthickness=0
        )

        scrollbar.config(command=self.activity_list.yview)

        self.activity_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add sample entries
        self._add_activity("Oracle UI Panel initialized")
        if HAS_INGESTION:
            self._add_activity("OracleSmartFloorIntegrator available (DB-backed ingestion)")
        else:
            self._add_activity("WARNING: Oracle ingestion engine not available", is_warning=True)

    def _create_monitoring_section(self, parent):
        """Create monitoring section (ingestion extracts + durable registry browser)."""
        section = tk.LabelFrame(
            parent,
            text="Oracle Observability",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )
        section.pack(fill=tk.BOTH, expand=True)

        nb = ttk.Notebook(section)
        nb.pack(fill=tk.BOTH, expand=True)
        # Exposed for host actions (Bento/command palette) to deep-link into the registry view.
        self.monitoring_notebook = nb

        # Tab 1: ingestion extracts (legacy/sample browser)
        extracts = tk.Frame(nb, bg=self.COLORS['card'])
        nb.add(extracts, text="Ingestion Extracts")

        # Filter controls
        filter_frame = tk.Frame(extracts, bg=self.COLORS['card'])
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            filter_frame,
            text="Filter:",
            font=('Segoe UI', 10),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.filter_var = tk.StringVar(value="all")

        for filter_type in ['all', 'constants', 'functions', 'classes', 'strings', 'datasets']:
            tk.Radiobutton(
                filter_frame,
                text=filter_type.capitalize(),
                variable=self.filter_var,
                value=filter_type,
                bg=self.COLORS['card'],
                fg=self.COLORS['text'],
                selectcolor=self.COLORS['card'],
                activebackground=self.COLORS['card'],
                font=('Segoe UI', 9),
                command=self._apply_filter,
            ).pack(side=tk.LEFT, padx=5)

        # Objects tree
        tree_frame = tk.Frame(extracts, bg=self.COLORS['card'])
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")

        self.objects_tree = ttk.Treeview(
            tree_frame,
            columns=('Type', 'Name', 'Floor'),
            show='tree headings',
            yscrollcommand=scrollbar.set,
            height=10,
        )

        scrollbar.config(command=self.objects_tree.yview)

        self.objects_tree.heading('#0', text='Source')
        self.objects_tree.heading('Type', text='Type')
        self.objects_tree.heading('Name', text='Name')
        self.objects_tree.heading('Floor', text='Floor')

        self.objects_tree.column('#0', width=250)
        self.objects_tree.column('Type', width=100)
        self.objects_tree.column('Name', width=200)
        self.objects_tree.column('Floor', width=120)

        self.objects_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add sample data (real extraction is floor-specific and can be wired later)
        self._add_sample_objects()

        # Tab 2: durable registry (Z Direct) browser
        registry = tk.Frame(nb, bg=self.COLORS['card'])
        nb.add(registry, text="Durable Registry (Z Direct)")

        self._create_registry_browser(registry)
        self._refresh_registry_browser()

    def _create_registry_browser(self, parent):
        """Durable registry browser for Oracle's Z Direct objects.json."""
        top = tk.Frame(parent, bg=self.COLORS['card'])
        top.pack(fill=tk.X, pady=(0, 8))

        tk.Label(top, text="Kind:", bg=self.COLORS['card'], fg=self.COLORS['text'], font=('Segoe UI', 10)).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        self.registry_kind_var = tk.StringVar(value="all")
        self.registry_kind_combo = ttk.Combobox(
            top,
            textvariable=self.registry_kind_var,
            values=[
                "all",
                "schema",
                "vault_file",
                "knowledge_node",
                "citation",
                "workspace",
                "research_query",
                "dataset",
                "experiment_run",
                "learning_module",
                "task",
            ],
            state="readonly",
            width=18,
        )
        self.registry_kind_combo.pack(side=tk.LEFT)
        try:
            self.registry_kind_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_registry_browser())
        except Exception:
            pass

        tk.Label(top, text="Search:", bg=self.COLORS['card'], fg=self.COLORS['text'], font=('Segoe UI', 10)).pack(
            side=tk.LEFT, padx=(14, 6)
        )
        self.registry_search_var = tk.StringVar(value="")
        ent = ttk.Entry(top, textvariable=self.registry_search_var, width=40)
        ent.pack(side=tk.LEFT, fill=tk.X, expand=True)
        try:
            ent.bind("<Return>", lambda _e: self._refresh_registry_browser())
        except Exception:
            pass

        ttk.Button(top, text="Refresh", command=self._refresh_registry_browser).pack(side=tk.LEFT, padx=(10, 0))

        body = tk.Frame(parent, bg=self.COLORS['card'])
        body.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(body, bg=self.COLORS['card'])
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        columns = ("kind", "id", "name", "tags")
        self.registry_tree = ttk.Treeview(left, columns=columns, show="headings", height=12)
        for c in columns:
            self.registry_tree.heading(c, text=c.upper())
            if c == "kind":
                self.registry_tree.column(c, width=120, anchor="w")
            elif c == "id":
                self.registry_tree.column(c, width=120, anchor="w")
            elif c == "tags":
                self.registry_tree.column(c, width=220, anchor="w")
            else:
                self.registry_tree.column(c, width=420, anchor="w")
        self.registry_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb = ttk.Scrollbar(left, orient="vertical", command=self.registry_tree.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.registry_tree.configure(yscrollcommand=sb.set)

        try:
            self.registry_tree.bind("<<TreeviewSelect>>", lambda _e: self._on_registry_select())
        except Exception:
            pass
        try:
            self.registry_tree.bind("<Button-3>", self._on_registry_right_click)
        except Exception:
            pass

        right = tk.Frame(body, bg=self.COLORS['card'], width=360)
        right.pack(side=tk.LEFT, fill=tk.BOTH, padx=(10, 0))
        right.pack_propagate(False)

        tk.Label(
            right, text="Details", bg=self.COLORS['card'], fg=self.COLORS['text'], font=('Segoe UI', 11, 'bold')
        ).pack(anchor="w")

        self.registry_detail = tk.Text(right, height=14, wrap=tk.WORD)
        self.registry_detail.pack(fill=tk.BOTH, expand=True, pady=(8, 8))
        try:
            self.registry_detail.config(state=tk.DISABLED)
        except Exception:
            pass

        btns = tk.Frame(right, bg=self.COLORS['card'])
        btns.pack(fill=tk.X)

        ttk.Button(btns, text="Open", command=self._open_registry_selected).pack(side=tk.LEFT)
        ttk.Button(btns, text="Open Folder", command=self._open_registry_selected_folder).pack(side=tk.LEFT, padx=(6, 0))

        def _open_in_catalog() -> None:
            host = getattr(self, "parent", None)
            fn = getattr(host, "open_object_catalog", None) if host is not None else None
            if not callable(fn):
                return
            obj = self._selected_registry_object()
            if not isinstance(obj, dict):
                return
            try:
                fn(scope="oracle", kind=str(obj.get("kind") or "all"), query=str(obj.get("id") or ""))
            except Exception:
                try:
                    fn(scope="oracle", kind="all", query=str(obj.get("id") or ""))
                except Exception:
                    pass

        host = getattr(self, "parent", None)
        if callable(getattr(host, "open_object_catalog", None) if host is not None else None):
            ttk.Button(btns, text="Open in Catalog", command=_open_in_catalog).pack(side=tk.LEFT, padx=(6, 0))

        ttk.Button(btns, text="Copy ID", command=self._copy_registry_selected_id).pack(side=tk.RIGHT)

        self._registry_rows: List[Dict[str, Any]] = []
        self._registry_vault_path_cache: Dict[str, str] = {}

    def _load_registry_objects(self) -> List[Dict[str, Any]]:
        try:
            oracle_objects = (LIGHTSPEED_ROOT / "Z Axis" / "Z-2_Oracle" / "Z Direct" / "objects.json").resolve()
            if not oracle_objects.exists():
                return []
            data = json.loads(oracle_objects.read_text(encoding="utf-8", errors="replace"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _refresh_registry_browser(self):
        """Reload + repopulate the durable registry browser."""
        try:
            for item in self.registry_tree.get_children():
                self.registry_tree.delete(item)
        except Exception:
            return

        kind = (self.registry_kind_var.get() or "all").strip()
        q = (self.registry_search_var.get() or "").strip().lower()
        q_terms = [t for t in q.split() if t.strip()]

        rows = self._load_registry_objects()
        self._registry_rows = []

        for it in rows:
            if not isinstance(it, dict):
                continue
            k = str(it.get("kind") or "")
            if kind != "all" and k != kind:
                continue

            rid = str(it.get("id") or "")
            name = ""
            if k == "vault_file":
                name = str(it.get("source_name") or it.get("name") or "")
            elif k == "schema":
                js = it.get("json_schema") if isinstance(it.get("json_schema"), dict) else None
                if js is None:
                    js = it.get("schema") if isinstance(it.get("schema"), dict) else None
                title = str((js or {}).get("title") or "")
                name = title or str(it.get("name") or "")
            elif k == "knowledge_node":
                name = str(it.get("concept") or "")
            elif k == "citation":
                name = str(it.get("note") or "")
            else:
                name = str(it.get("name") or it.get("title") or it.get("query_text") or "")

            tags = it.get("tags")
            tags_s = ""
            try:
                if isinstance(tags, list):
                    cleaned = [str(t).strip() for t in tags if str(t).strip()]
                    tags_s = ", ".join(cleaned)
                elif isinstance(tags, str):
                    tags_s = tags.strip()
            except Exception:
                tags_s = ""

            # Broader blob for menu-first narrowing.
            hay = " ".join(
                [
                    k,
                    rid,
                    name,
                    tags_s,
                    str(it.get("description") or ""),
                    str(it.get("domain") or ""),
                    str(it.get("query_text") or it.get("query") or ""),
                    str(it.get("concept") or ""),
                    str(it.get("note") or ""),
                    str(it.get("vault_file_id") or ""),
                    str(it.get("path") or ""),
                ]
            ).lower()
            if q_terms and not all(t in hay for t in q_terms):
                continue

            self._registry_rows.append(it)
            try:
                self.registry_tree.insert(
                    "",
                    tk.END,
                    values=(
                        k,
                        rid,
                        (name[:160] + "...") if len(name) > 160 else name,
                        (tags_s[:80] + "...") if len(tags_s) > 80 else tags_s,
                    ),
                )
            except Exception:
                continue

        self._add_activity(f"Registry loaded: {len(self._registry_rows)} item(s)")
        self._on_registry_select()

    def _selected_registry_object(self) -> Optional[Dict[str, Any]]:
        try:
            sel = self.registry_tree.selection()
            if not sel:
                return None
            idx = self.registry_tree.index(sel[0])
            if 0 <= idx < len(self._registry_rows):
                return self._registry_rows[idx]
        except Exception:
            pass
        return None

    def _get_universal_file_context_menu(self):
        """Best-effort loader for Trinity's UniversalFileContextMenu (cached on the instance)."""
        cached = getattr(self, "_ucm_cached", None)
        if cached is False:
            return None
        if cached is not None:
            return cached

        try:
            ucm_path = (LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "ui" / "universal_context_menu.py").resolve()
            if not ucm_path.exists():
                self._ucm_cached = False
                return None
            spec = importlib.util.spec_from_file_location("lightspeed_universal_context_menu", str(ucm_path))
            if spec is None or spec.loader is None:
                self._ucm_cached = False
                return None
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            U = getattr(mod, "UniversalFileContextMenu", None)
            self._ucm_cached = U if U is not None else False
            return U
        except Exception:
            self._ucm_cached = False
            return None

    def _registry_best_effort_path(self, obj: Dict[str, Any]) -> str:
        """Resolve a filesystem path for the registry row when possible."""
        try:
            k = str(obj.get("kind") or "")
            path = ""
            if k == "vault_file":
                path = str(obj.get("path") or "")
            elif k == "citation":
                path = self._resolve_vault_file_path(str(obj.get("vault_file_id") or ""))
            elif k == "knowledge_node":
                sources = obj.get("sources") or []
                if isinstance(sources, list) and sources:
                    s0 = sources[0]
                    if isinstance(s0, dict):
                        path = self._resolve_vault_file_path(str(s0.get("vault_file_id") or s0.get("vault_id") or ""))
                    elif isinstance(s0, str) and s0.isdigit():
                        path = self._resolve_vault_file_path(s0)
            elif k == "dataset":
                path = str(obj.get("path") or "")
                if not path:
                    srcs = obj.get("source_paths") or []
                    if isinstance(srcs, list) and srcs:
                        path = str(srcs[0] or "")
            elif k == "experiment_run":
                # Artifacts may carry file paths; pick the first existing one.
                arts = obj.get("artifacts") or []
                if isinstance(arts, list):
                    for a in arts:
                        p = str(a or "").strip()
                        if not p:
                            continue
                        try:
                            if Path(p).exists():
                                path = p
                                break
                        except Exception:
                            continue
            return path
        except Exception:
            return ""

    def _on_registry_right_click(self, event=None):
        """Right-click: open universal file context menu for the selected registry item when path-backed."""
        if event is None:
            return
        try:
            iid = self.registry_tree.identify_row(event.y)
            if iid:
                self.registry_tree.selection_set(iid)
        except Exception:
            pass

        obj = self._selected_registry_object()
        if not obj:
            return

        path = self._registry_best_effort_path(obj)
        if not path:
            return
        try:
            target = Path(path)
            if not target.exists():
                return
        except Exception:
            return

        U = self._get_universal_file_context_menu()
        if U is None:
            return
        try:
            menu = U.create(
                self.registry_tree,
                filepath=(target if target.is_file() else None),
                folderpath=(target if target.is_dir() else None),
                show_advanced=True,
            )
            menu.tk_popup(event.x_root, event.y_root)
            menu.grab_release()
        except Exception:
            return

    def _on_registry_select(self):
        obj = self._selected_registry_object()
        try:
            self.registry_detail.config(state=tk.NORMAL)
            self.registry_detail.delete("1.0", tk.END)
            if obj is None:
                self.registry_detail.insert(tk.END, "Select an object to view details.")
            else:
                self.registry_detail.insert(tk.END, json.dumps(obj, indent=2))
            self.registry_detail.config(state=tk.DISABLED)
        except Exception:
            pass

    def _resolve_vault_file_path(self, vault_id: str) -> str:
        vault_id = (vault_id or "").strip()
        if not vault_id:
            return ""
        if vault_id in self._registry_vault_path_cache:
            return self._registry_vault_path_cache[vault_id]
        try:
            for it in (self._registry_rows or self._load_registry_objects()):
                if isinstance(it, dict) and it.get("kind") == "vault_file" and str(it.get("id") or "") == vault_id:
                    path = str(it.get("path") or "")
                    self._registry_vault_path_cache[vault_id] = path
                    return path
        except Exception:
            pass
        return ""

    def _open_registry_selected(self):
        obj = self._selected_registry_object()
        if not obj:
            return
        try:
            k = str(obj.get("kind") or "")
            path = ""
            if k == "schema":
                js = obj.get("json_schema") if isinstance(obj.get("json_schema"), dict) else None
                if js is None:
                    js = obj.get("schema") if isinstance(obj.get("schema"), dict) else None
                payload = js if isinstance(js, dict) else obj
                try:
                    txt = json.dumps(payload, indent=2, ensure_ascii=True)
                except Exception:
                    txt = str(payload)
                try:
                    self.window.clipboard_clear()
                    self.window.clipboard_append(txt)
                    self._add_activity("Copied schema JSON to clipboard")
                except Exception:
                    pass
                return
            if k == "vault_file":
                path = str(obj.get("path") or "")
            elif k == "citation":
                path = self._resolve_vault_file_path(str(obj.get("vault_file_id") or ""))
            elif k == "knowledge_node":
                sources = obj.get("sources") or []
                if isinstance(sources, list) and sources:
                    s0 = sources[0]
                    if isinstance(s0, dict):
                        path = self._resolve_vault_file_path(str(s0.get("vault_file_id") or s0.get("vault_id") or ""))
                    elif isinstance(s0, str) and s0.isdigit():
                        path = self._resolve_vault_file_path(s0)
            if path:
                os.startfile(path)  # type: ignore[attr-defined]
        except Exception:
            pass

    def _open_registry_selected_folder(self):
        obj = self._selected_registry_object()
        if not obj:
            return
        try:
            k = str(obj.get("kind") or "")
            path = ""
            if k == "vault_file":
                path = str(obj.get("path") or "")
            elif k == "citation":
                path = self._resolve_vault_file_path(str(obj.get("vault_file_id") or ""))
            if not path:
                return
            p = Path(path)
            os.startfile(str(p.parent if p.is_file() else p))  # type: ignore[attr-defined]
        except Exception:
            pass

    def _copy_registry_selected_id(self):
        obj = self._selected_registry_object()
        if not obj:
            return
        try:
            rid = str(obj.get("id") or "")
            self.window.clipboard_clear()
            self.window.clipboard_append(rid)
            self._add_activity(f"Copied id={rid} to clipboard")
        except Exception:
            pass

    def _add_activity(self, message: str, is_warning: bool = False):
        """Add activity log entry"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        prefix = "[WARN]" if is_warning else "[INFO]"
        entry = f"{timestamp} {prefix} {message}"

        self.activity_list.insert(tk.END, entry)
        self.activity_list.see(tk.END)

        # Color code
        if is_warning:
            self.activity_list.itemconfig(tk.END, fg=self.COLORS['warning'])

    def _add_sample_objects(self):
        """Add sample extracted objects"""
        samples = [
            ('example.py', 'constant', 'MAX_SIZE', 'Z+1_Architect'),
            ('utils.py', 'function', 'calculate_depth', 'Z0_TheConstruct'),
            ('models.py', 'class', 'BentoTile', 'Z+1_Architect'),
            ('config.py', 'constant', 'DEFAULT_RADIUS', 'Z0_TheConstruct'),
            ('data.csv', 'dataset', 'user_metrics.csv', 'Z-2_Oracle')
        ]

        for source, obj_type, name, floor in samples:
            self.objects_tree.insert('', tk.END, text=source, values=(obj_type, name, floor))

    def _apply_filter(self):
        """Apply object filter"""
        filter_type = self.filter_var.get()
        self._add_activity(f"Applied filter: {filter_type}")

        # Clear and repopulate (in real implementation, would filter actual data)
        for item in self.objects_tree.get_children():
            self.objects_tree.delete(item)

        self._add_sample_objects()

    # ===== CONTROL METHODS =====

    def _start_ingestion(self):
        """Start ingestion system"""
        if not HAS_INGESTION:
            messagebox.showerror("Error", "Oracle ingestion system not available")
            return

        if self.is_running:
            messagebox.showinfo("Info", "Ingestion is already running")
            return

        try:
            # Initialize ingestion
            self.ingestion = SmartFloorIngestion()
            self.ingestion.MAX_CPU_PERCENT = self.cpu_limit_var.get()
            self.ingestion.BATCH_SIZE = self.batch_size_var.get()

            # Start in background thread
            threading.Thread(target=self.ingestion.start_continuous, daemon=True).start()

            self.is_running = True
            self.stats['start_time'] = time.time()

            # Update UI
            self._update_status(True)
            self.start_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.NORMAL)

            self._add_activity("✓ Ingestion started successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start ingestion: {e}")
            self._add_activity(f"✗ Failed to start: {e}", is_warning=True)

    def _pause_ingestion(self):
        """Pause ingestion system"""
        if not self.is_running:
            return

        if self.ingestion:
            self.ingestion.stop()
            self.is_running = False
            self._update_status(False)
            self.pause_btn.config(state=tk.DISABLED)
            self.start_btn.config(state=tk.NORMAL, text="▶ Resume")
            self._add_activity("⏸ Ingestion paused")

    def _stop_ingestion(self):
        """Stop ingestion system"""
        if self.ingestion:
            self.ingestion.stop()
            self.ingestion = None

        self.is_running = False
        self.stats['start_time'] = None

        # Reset UI
        self._update_status(False)
        self.start_btn.config(state=tk.NORMAL, text="▶ Start")
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)

        self._add_activity("■ Ingestion stopped")

    def _add_files(self):
        """Add files to processing queue"""
        files = filedialog.askopenfilenames(
            title="Select Files to Process",
            filetypes=[
                ("Python files", "*.py"),
                ("All files", "*.*")
            ]
        )

        if files:
            if self.ingestion:
                ok = 0
                bad = 0
                for file_path in files:
                    res = self.ingestion.add_file(Path(file_path))
                    if res.get("success"):
                        ok += 1
                    else:
                        bad += 1
                self._add_activity(f"Added {ok} file(s) to queue" + (f" ({bad} failed)" if bad else ""))
            else:
                self._add_activity("Ingestion not started. Files not added.", is_warning=True)

    def _add_folder(self):
        """Add folder to processing queue"""
        folder = filedialog.askdirectory(title="Select Folder to Process")

        if folder:
            if self.ingestion:
                exclude = {".venv", "venv", "__pycache__", "node_modules", ".git"}
                res = self.ingestion.add_directory(Path(folder), recursive=True, exclude_dirs=exclude)
                self._add_activity(
                    f"Added folder: {Path(folder).name} (submitted={res.get('submitted', 0)}, failed={res.get('failed', 0)})"
                )
            else:
                self._add_activity("Ingestion not started. Folder not added.", is_warning=True)

    def _ingest_lightspeed_workspace(self):
        """Ingest the entire LightSpeed workspace (safe: stages files into Oracle incoming)."""
        if not self.ingestion:
            self._add_activity("Ingestion not started. Workspace not added.", is_warning=True)
            return

        # Confirm (can be a lot of files)
        if not messagebox.askyesno(
            "Ingest LightSpeed Workspace",
            "This will stage documentation + code files from the LightSpeed workspace into Oracle Incoming.\n"
            "Original files are NOT modified.\n\nProceed?",
            parent=self.window,
        ):
            return

        try:
            from core.config.paths import LIGHTSPEED_ROOT as ROOT  # type: ignore
            root = Path(ROOT)
        except Exception:
            root = Path.cwd()

        include_exts = {
            ".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
            ".csv", ".tsv", ".sql", ".pdf",
        }
        exclude_dirs = {
            ".git", "__pycache__", "node_modules", ".venv", "venv",
            "ai_logs", "logs", "legacy_archive",
        }

        self._add_activity(f"Workspace ingest queued: {root}")

        def run():
            try:
                res = self.ingestion.add_directory(
                    root,
                    recursive=True,
                    priority=5,
                    include_extensions=include_exts,
                    exclude_dirs=exclude_dirs,
                )
                msg = f"✓ Workspace ingest complete: submitted={res.get('submitted', 0)}, failed={res.get('failed', 0)}"
                try:
                    self.window.after(0, lambda: self._add_activity(msg))
                except Exception:
                    pass
            except Exception as e:
                try:
                    self.window.after(0, lambda: self._add_activity(f"✗ Workspace ingest failed: {e}", is_warning=True))
                except Exception:
                    pass

        threading.Thread(target=run, daemon=True).start()

    # ===== KNOWLEDGE IMPORTS (GPT Export + Doc Markers) =====

    def _get_db_path(self) -> Path:
        """Resolve Merovingian DB path from unified_config.json (floor-native)."""
        cfg_path = Path(LIGHTSPEED_ROOT) / "config" / "unified_config.json"
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            rel = (cfg.get("database") or {}).get("path")
            if rel:
                return (Path(LIGHTSPEED_ROOT) / rel).resolve()
        except Exception:
            pass
        return (Path(LIGHTSPEED_ROOT) / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db").resolve()

    def _create_job(self, job_type: str, params: Dict[str, Any]) -> int:
        """Create a Smith-style background job row (used by tools to report progress)."""
        db_path = self._get_db_path()
        now = datetime.now().isoformat()
        with sqlite3.connect(str(db_path)) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO jobs (job_type, params_json, status, scheduled_for, created_at) VALUES (?, ?, 'pending', ?, ?)",
                (job_type, json.dumps(params, ensure_ascii=False), None, now),
            )
            return int(cur.lastrowid)

    def _load_tool(self, rel_path: str, module_name: str):
        tool_path = (Path(LIGHTSPEED_ROOT) / rel_path).resolve()
        spec = importlib.util.spec_from_file_location(module_name, tool_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load tool module: {tool_path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _import_gpt_export_ui(self):
        """UI handler: import GPT Export conversations into DB (streaming)."""
        default_path = (
            Path(LIGHTSPEED_ROOT)
            / "Z Axis"
            / "Z-2_Oracle"
            / "archive"
            / "conversations"
            / "GPT_Export_2025-11-16"
            / "conversations.json"
        )
        export_path = filedialog.askopenfilename(
            parent=self.window,
            title="Select GPT Export conversations.json",
            initialdir=str(default_path.parent) if default_path.parent.exists() else str(Path(LIGHTSPEED_ROOT)),
            initialfile=default_path.name,
            filetypes=[("conversations.json", "conversations.json"), ("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not export_path:
            return

        company = simpledialog.askstring(
            "Company",
            "Assign imported conversations to company (type 'auto' to classify per conversation):",
            initialvalue="auto",
            parent=self.window,
        )
        if company is None:
            return
        company = company.strip() or "auto"

        source = simpledialog.askstring(
            "Source Label",
            "Source label (stored in DB):",
            initialvalue="GPT_Export_2025-11-16",
            parent=self.window,
        )
        if source is None:
            return
        source = source.strip() or "GPT_Export_2025-11-16"

        if not messagebox.askyesno(
            "Import GPT Export",
            "This will stream-import the selected conversations into the LightSpeed database.\n"
            "It is safe to re-run (idempotent upserts).\n\nProceed?",
            parent=self.window,
        ):
            return

        db_path = self._get_db_path()
        job_id = self._create_job("import_gpt_export", {"source": source, "company": company, "file": export_path})
        self._add_activity(f"Queued GPT export import job #{job_id}: {Path(export_path).name}")

        def run():
            try:
                tool = self._load_tool("Z Axis/Z-3_Smith/tools/import_gpt_export.py", "import_gpt_export_tool")

                def cb(p):
                    try:
                        self.window.after(
                            0,
                            lambda: self._add_activity(
                                f"Import progress: {p.pct:.2f}% (conv={p.conversations_seen}, msgs={p.messages_seen})"
                            ),
                        )
                    except Exception:
                        pass

                tool.import_gpt_export(
                    db_path=db_path,
                    export_path=Path(export_path),
                    source=source,
                    company_name=company,
                    commit_every=25,
                    job_id=job_id,
                    progress_cb=cb,
                )
                try:
                    self.window.after(0, lambda: self._add_activity(f"✓ GPT export import completed (job #{job_id})"))
                except Exception:
                    pass
            except Exception as e:
                try:
                    self.window.after(0, lambda: self._add_activity(f"✗ GPT export import failed: {e}", is_warning=True))
                except Exception:
                    pass

        threading.Thread(target=run, daemon=True).start()

    def _scan_docs_to_tasks_ui(self):
        """UI handler: scan MD/TXT docs for TODO/FIXME/etc and create tasks."""
        if not messagebox.askyesno(
            "Scan Docs → Tasks",
            "Scan documentation (MD/TXT) for TODO/FIXME/TBD/etc and create actionable tasks.\n\nProceed?",
            parent=self.window,
        ):
            return

        scan_root = filedialog.askdirectory(
            parent=self.window,
            title="Select directory to scan (recommended: Z Axis)",
            initialdir=str(Path(LIGHTSPEED_ROOT) / "Z Axis"),
        )
        if not scan_root:
            return

        db_path = self._get_db_path()
        self._add_activity(f"Scanning docs under: {scan_root}")

        def run():
            try:
                tool = self._load_tool("Z Axis/Z-3_Smith/tools/scan_docs_to_tasks.py", "scan_docs_to_tasks_tool")
                res = tool.scan_docs_to_db(db_path=db_path, scan_root=Path(scan_root), create_tasks=True)
                # Keep Z Direct observable even when invoked from an in-app UI action.
                try:
                    tool._emit_z_direct_summary(Path(LIGHTSPEED_ROOT), scan_root=Path(scan_root), res=res)  # type: ignore[attr-defined]
                except Exception:
                    pass
                try:
                    self.window.after(
                        0,
                        lambda: self._add_activity(
                            f"✓ Doc scan complete: files={res.files_scanned}, markers+={res.markers_inserted}, tasks+={res.tasks_created}"
                        ),
                    )
                except Exception:
                    pass
            except Exception as e:
                try:
                    self.window.after(0, lambda: self._add_activity(f"✗ Doc scan failed: {e}", is_warning=True))
                except Exception:
                    pass

        threading.Thread(target=run, daemon=True).start()

    def _clear_queue(self):
        """Clear processing queue"""
        if messagebox.askyesno("Confirm", "Clear all pending files from queue?"):
            if self.ingestion:
                # Clear in-memory queue (legacy UX)
                try:
                    while True:
                        self.ingestion.task_queue.get_nowait()
                        self.ingestion.task_queue.task_done()
                except queue.Empty:
                    pass
                # Also cancel queued DB tasks (best-effort)
                try:
                    affected = int(getattr(self.ingestion, "clear_pending_tasks", lambda: 0)())
                    if affected:
                        self._add_activity(f"Canceled {affected} queued DB task(s)")
                except Exception:
                    pass
            self._add_activity("Queue cleared")

    # ===== UI UPDATE METHODS =====

    def _update_status(self, is_active: bool):
        """Update status indicator"""
        if is_active:
            self.status_indicator.config(fg=self.COLORS['active'])
            self.status_label.config(text="Active", fg=self.COLORS['success'])
        else:
            self.status_indicator.config(fg=self.COLORS['inactive'])
            self.status_label.config(text="Inactive", fg=self.COLORS['text_dim'])

    def _update_stats(self):
        """Update statistics display"""
        # Update stat labels
        for key, (label, unit) in self.stat_labels.items():
            value = self.stats.get(key, 0)

            if isinstance(value, float):
                formatted = f"{value:.2f} {unit}" if unit else f"{value:.2f}"
            else:
                formatted = f"{value} {unit}" if unit else str(value)

            label.config(text=formatted)

        # Update uptime
        if self.stats['start_time']:
            uptime_seconds = int(time.time() - self.stats['start_time'])
            hours = uptime_seconds // 3600
            minutes = (uptime_seconds % 3600) // 60
            seconds = uptime_seconds % 60
            self.uptime_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def _start_monitoring(self):
        """Start monitoring thread"""
        self.should_monitor = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

    def _monitoring_loop(self):
        """Monitoring loop for updating stats"""
        while self.should_monitor:
            if self.is_running and self.ingestion:
                # Get stats from ingestion system (DB-backed when available)
                try:
                    q = self.ingestion.get_queue_status() if hasattr(self.ingestion, "get_queue_status") else {}
                except Exception:
                    q = {}

                completed = int(q.get("completed", len(getattr(self.ingestion, "processed_files", []) or [])))
                failed = int(q.get("failed", len(getattr(self.ingestion, "error_files", []) or [])))
                pending = int(q.get("pending", 0))
                total = int(q.get("total_tasks", completed + failed + pending))

                self.stats.update({
                    'files_processed': completed,
                    'errors': failed,
                    'queue_size': pending,
                    'objects_extracted': self.stats.get('objects_extracted', 0),
                    'cpu_usage': float(getattr(self.ingestion, "stats", {}).get('current_cpu', 0.0)),
                    'memory_usage': 0.0
                })

                # Update UI (schedule on main thread)
                try:
                    self.window.after(0, self._update_stats)
                except:
                    pass

            time.sleep(1)

    def _on_close(self):
        """Handle window close"""
        # Stop monitoring
        self.should_monitor = False

        # Stop ingestion if running
        if self.is_running:
            self._stop_ingestion()

        # Close window
        self.window.destroy()


def launch_oracle_panel(parent: Optional[tk.Tk] = None):
    """Launch Oracle UI panel"""
    panel = OracleUIPanel(parent)
    panel.open_panel()


if __name__ == "__main__":
    launch_oracle_panel()
