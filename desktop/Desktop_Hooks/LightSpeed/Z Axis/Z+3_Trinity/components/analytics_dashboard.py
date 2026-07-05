#!/usr/bin/env python
"""
Analytics Dashboard - Real-time System Performance Monitoring
LightSpeed Type I Civilization Platform - Trinity Floor

Comprehensive dashboard for monitoring:
- System performance metrics across all floors
- Real-time alerts and notifications
- Cache performance statistics
- Event bus throughput
- Database query performance
- Floor-specific analytics

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 11, 2026
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Any
from datetime import datetime
import threading
import time
import json
from pathlib import Path
import os

try:
    from . import state_store
except ImportError:
    import sys
    from pathlib import Path
    CURRENT = Path(__file__).resolve()
    sys.path.append(str(CURRENT.parent))
    import state_store  # type: ignore

# Import core services (floor-native via Merovingian core.services)
from core.services import (
    get_performance_monitor,
    get_cache_manager,
    get_event_bus,
    MetricType,
    AlertLevel
)


class MetricChart(ttk.Frame):
    """Simple line chart for metrics"""

    def __init__(self, parent, title: str, metric_type: MetricType, **kwargs):
        super().__init__(parent, **kwargs)
        self.title = title
        self.metric_type = metric_type

        # Title
        title_label = ttk.Label(self, text=title, font=('Segoe UI', 10, 'bold'))
        title_label.pack(pady=(0, 5))

        # Canvas for chart
        self.canvas = tk.Canvas(self, height=150, bg='#1e1e1e', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Stats display
        stats_frame = ttk.Frame(self)
        stats_frame.pack(fill=tk.X, pady=(5, 0))

        self.stats_labels = {}
        for stat_name in ['Current', 'Mean', 'P95', 'P99']:
            label = ttk.Label(stats_frame, text=f"{stat_name}: --", font=('Consolas', 9))
            label.pack(side=tk.LEFT, padx=5)
            self.stats_labels[stat_name.lower()] = label

        self.data_points: List[float] = []
        self.max_points = 60

    def update_chart(self, value: float, stats: Dict[str, float]):
        """Update chart with new data point"""
        # Add data point
        self.data_points.append(value)
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)

        # Update stats
        self.stats_labels['current'].config(text=f"Current: {value:.2f}")
        if stats.get('count', 0) > 0:
            self.stats_labels['mean'].config(text=f"Mean: {stats['mean']:.2f}")
            self.stats_labels['p95'].config(text=f"P95: {stats['p95']:.2f}")
            self.stats_labels['p99'].config(text=f"P99: {stats['p99']:.2f}")

        # Redraw chart
        self._draw_chart()

    def _draw_chart(self):
        """Draw the chart"""
        self.canvas.delete('all')

        if not self.data_points:
            return

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width < 10 or height < 10:
            return

        # Calculate scaling
        max_value = max(self.data_points) if self.data_points else 1
        min_value = min(self.data_points) if self.data_points else 0

        # Add padding
        value_range = max_value - min_value if max_value != min_value else 1
        max_value += value_range * 0.1
        min_value -= value_range * 0.1

        # Draw grid lines
        for i in range(5):
            y = height * (i / 4)
            self.canvas.create_line(0, y, width, y, fill='#3a3a3a', dash=(2, 2))

            # Value label
            value = max_value - (max_value - min_value) * (i / 4)
            self.canvas.create_text(5, y, text=f"{value:.1f}", anchor='w', fill='#888888', font=('Consolas', 8))

        # Draw line chart
        if len(self.data_points) > 1:
            points = []
            for i, value in enumerate(self.data_points):
                x = (i / (self.max_points - 1)) * width
                y = height - ((value - min_value) / (max_value - min_value)) * height
                points.extend([x, y])

            self.canvas.create_line(points, fill='#00ff88', width=2, smooth=True)

            # Draw points
            for i in range(0, len(points), 2):
                x, y = points[i], points[i + 1]
                self.canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill='#00ff88', outline='')


class AlertPanel(ttk.Frame):
    """Panel showing recent alerts"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Title
        title = ttk.Label(self, text="Recent Alerts", font=('Segoe UI', 10, 'bold'))
        title.pack(pady=(0, 5))

        # Scrolled text for alerts
        scroll_frame = ttk.Frame(self)
        scroll_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.alerts_text = tk.Text(
            scroll_frame,
            height=10,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#ffffff',
            yscrollcommand=scrollbar.set,
            wrap=tk.WORD
        )
        self.alerts_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.alerts_text.yview)

        # Color tags
        self.alerts_text.tag_config('critical', foreground='#ff4444')
        self.alerts_text.tag_config('error', foreground='#ff8844')
        self.alerts_text.tag_config('warning', foreground='#ffaa44')
        self.alerts_text.tag_config('info', foreground='#4488ff')

    def add_alert(self, alert):
        """Add alert to display"""
        timestamp = alert.timestamp.strftime("%H:%M:%S")
        message = f"[{timestamp}] {alert.message}\n"

        self.alerts_text.insert('1.0', message, alert.level.value)

        # Limit to 100 lines
        lines = int(self.alerts_text.index('end-1c').split('.')[0])
        if lines > 100:
            self.alerts_text.delete('100.0', tk.END)


class FloorPerformancePanel(ttk.LabelFrame):
    """Panel showing performance for specific floor"""

    def __init__(self, parent, floor_name: str, **kwargs):
        super().__init__(parent, text=floor_name, **kwargs)
        self.floor_name = floor_name

        # Metrics display
        self.metric_labels = {}

        metrics = [
            ('Response Time', 'response_time'),
            ('Event Count', 'event_count'),
            ('Error Rate', 'error_rate')
        ]

        for i, (label, key) in enumerate(metrics):
            row_frame = ttk.Frame(self)
            row_frame.pack(fill=tk.X, pady=2)

            ttk.Label(row_frame, text=f"{label}:", width=15).pack(side=tk.LEFT)
            value_label = ttk.Label(row_frame, text="--", font=('Consolas', 9, 'bold'))
            value_label.pack(side=tk.LEFT)

            self.metric_labels[key] = value_label

    def update_metrics(self, metrics: Dict[str, Any]):
        """Update floor metrics"""
        for key, label in self.metric_labels.items():
            if key in metrics and metrics[key].get('count', 0) > 0:
                mean = metrics[key]['mean']
                label.config(text=f"{mean:.3f}")
            else:
                label.config(text="--")


class AnalyticsDashboard(ttk.Frame):
    """
    Main analytics dashboard for system monitoring

    Real-time display of performance metrics, alerts, and statistics
    across all LightSpeed floors.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.monitor = get_performance_monitor()
        self.cache = get_cache_manager()
        self.event_bus = get_event_bus()

        # Monitoring state
        self.monitoring = False
        self.update_interval = 2.0  # seconds
        self.monitor_thread: Optional[threading.Thread] = None
        self.ui_state = state_store.load_state(Path(__file__).resolve())

        self._build_ui()
        self.after(500, self._restore_ui_state)

    def _build_ui(self):
        """Build dashboard UI"""
        # Title
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        title = ttk.Label(
            title_frame,
            text="Analytics Dashboard",
            font=('Segoe UI', 14, 'bold')
        )
        title.pack(side=tk.LEFT)

        # Control buttons
        self.start_btn = ttk.Button(
            title_frame,
            text="Start Monitoring",
            command=self.start_monitoring
        )
        self.start_btn.pack(side=tk.RIGHT, padx=5)

        self.stop_btn = ttk.Button(
            title_frame,
            text="Stop Monitoring",
            command=self.stop_monitoring,
            state='disabled'
        )
        self.stop_btn.pack(side=tk.RIGHT)

        # Main notebook with paned wrapper (resizable)
        notebook = ttk.Notebook(self)
        wrapper = ttk.Panedwindow(self, orient=tk.VERTICAL)
        wrapper.pack(fill=tk.BOTH, expand=True)
        wrapper.add(notebook, weight=1)
        self._ensure_menu()
        self._wire_window_callbacks()

        # System Overview Tab
        self._build_overview_tab(notebook)

        # Performance Metrics Tab
        self._build_metrics_tab(notebook)

        # Floor Details Tab
        self._build_floors_tab(notebook)

        # Cache Statistics Tab
        self._build_cache_tab(notebook)

        # Operations Workspace Tab (registry views)
        self._build_operations_tab(notebook)

        # Tools Catalog Tab (capability listings)
        self._build_tools_tab(notebook)

        # Startup Wizard Tab
        self._build_startup_tab(notebook)

        # Tool Runner Tab (schema-aware launchers)
        self._build_runner_tab(notebook)

    def _build_overview_tab(self, notebook):
        """Build system overview tab"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="System Overview")

        # System health
        health_frame = ttk.LabelFrame(tab, text="System Health", padding=10)
        health_frame.pack(fill=tk.X, padx=10, pady=10)

        self.health_status = ttk.Label(
            health_frame,
            text="Status: --",
            font=('Segoe UI', 12, 'bold')
        )
        self.health_status.pack()

        # Key metrics grid
        metrics_frame = ttk.Frame(health_frame)
        metrics_frame.pack(fill=tk.X, pady=10)

        self.overview_labels = {}

        metrics = [
            ('CPU Usage', 'cpu'),
            ('Memory Usage', 'memory'),
            ('Cache Hit Rate', 'cache_hit'),
            ('Event Throughput', 'events')
        ]

        for i, (label, key) in enumerate(metrics):
            row = i // 2
            col = i % 2

            frame = ttk.Frame(metrics_frame)
            frame.grid(row=row, column=col, padx=20, pady=5, sticky='w')

            ttk.Label(frame, text=f"{label}:", font=('Segoe UI', 10)).pack(side=tk.LEFT)
            value_label = ttk.Label(frame, text="--", font=('Consolas', 10, 'bold'))
            value_label.pack(side=tk.LEFT, padx=(5, 0))

            self.overview_labels[key] = value_label

        # Alert panel
        self.alert_panel = AlertPanel(tab)
        self.alert_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _build_metrics_tab(self, notebook):
        """Build performance metrics tab"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Performance Metrics")

        # Scrollable canvas
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        # Charts
        self.charts: Dict[str, MetricChart] = {}

        chart_configs = [
            ('CPU Usage (%)', MetricType.CPU_USAGE),
            ('Memory Usage (%)', MetricType.MEMORY_USAGE),
            ('Response Time (s)', MetricType.RESPONSE_TIME),
            ('Event Count', MetricType.EVENT_COUNT)
        ]

        for title, metric_type in chart_configs:
            chart = MetricChart(scrollable_frame, title, metric_type)
            chart.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.charts[metric_type.value] = chart

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_floors_tab(self, notebook):
        """Build floor details tab"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Floor Details")

        # Scrollable canvas
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        # Floor panels
        self.floor_panels: Dict[str, FloorPerformancePanel] = {}

        floors = ['Neo', 'Architect', 'TheConstruct', 'Morpheus', 'Oracle', 'Smith', 'Merovingian', 'Trinity']

        for floor in floors:
            panel = FloorPerformancePanel(scrollable_frame, floor)
            panel.pack(fill=tk.X, padx=10, pady=5)
            self.floor_panels[floor] = panel

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_cache_tab(self, notebook):
        """Build cache statistics tab"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Cache Statistics")

        # Memory cache
        mem_frame = ttk.LabelFrame(tab, text="Memory Cache", padding=10)
        mem_frame.pack(fill=tk.X, padx=10, pady=10)

        self.mem_cache_labels = {}
        for stat in ['size', 'hit_rate', 'hits', 'misses', 'evictions']:
            row = ttk.Frame(mem_frame)
            row.pack(fill=tk.X, pady=2)

            ttk.Label(row, text=f"{stat.replace('_', ' ').title()}:", width=15).pack(side=tk.LEFT)
            label = ttk.Label(row, text="--", font=('Consolas', 10))
            label.pack(side=tk.LEFT)

            self.mem_cache_labels[stat] = label

        # Disk cache
        disk_frame = ttk.LabelFrame(tab, text="Disk Cache", padding=10)
        disk_frame.pack(fill=tk.X, padx=10, pady=10)

        self.disk_cache_labels = {}
        for stat in ['size', 'hit_rate', 'hits', 'misses']:
            row = ttk.Frame(disk_frame)
            row.pack(fill=tk.X, pady=2)

            ttk.Label(row, text=f"{stat.replace('_', ' ').title()}:", width=15).pack(side=tk.LEFT)
            label = ttk.Label(row, text="--", font=('Consolas', 10))
            label.pack(side=tk.LEFT)

            self.disk_cache_labels[stat] = label

    def _build_operations_tab(self, notebook):
        """Build operations workspace tab (registry + stubs)."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Operations")

        try:
            from .operations_workspace_manager import OperationsWorkspaceManager
            from .operations_status_cards import OperationsStatusCards
        except ImportError as exc:
            ttk.Label(tab, text=f"Operations components unavailable: {exc}").pack(padx=10, pady=10)
            return

        paned = ttk.Panedwindow(tab, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        left = ttk.Frame(paned)
        right = ttk.Frame(paned, width=360)
        paned.add(left, weight=3)
        paned.add(right, weight=2)

        ttk.Label(left, text="Workspace Manager", font=('Segoe UI', 10, 'bold')).pack(anchor="w", padx=6, pady=(0, 4))
        manager = OperationsWorkspaceManager(left)
        manager.frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(right, text="Status Cards (GMAT, Asset Library)", font=('Segoe UI', 10, 'bold')).pack(anchor="w", padx=6, pady=(0, 4))
        cards = OperationsStatusCards(right)
        cards.pack(fill=tk.BOTH, expand=True)

        # Scenario catalog panel
        scen_frame = ttk.LabelFrame(right, text="Scenario Catalog", padding=6)
        scen_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(6, 0))
        scen_path = None
        probe_roots = list(Path(__file__).resolve().parents)
        for candidate in probe_roots:
            for probe in [
                candidate / "operations" / "registry" / "scenario_catalog.json",
                candidate / "Z Axis" / "Z-4_Merovingian" / "data" / "operations" / "registry" / "scenario_catalog.json",
            ]:
                if probe.exists():
                    scen_path = probe
                    break
            if scen_path:
                break
        if not scen_path:
            ttk.Label(scen_frame, text="scenario_catalog.json not found").pack(anchor="w")
        else:
            try:
                data = json.loads(scen_path.read_text(encoding="utf-8"))
                scenarios = data.get("scenarios", [])
                # Filter row
                filter_frame = ttk.Frame(scen_frame)
                filter_frame.pack(fill=tk.X, pady=(0, 4))
                ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=(0, 4))
                filter_var = tk.StringVar()
                filter_entry = ttk.Entry(filter_frame, textvariable=filter_var, width=30)
                filter_entry.pack(side=tk.LEFT, padx=(0, 6))

                cols = ("id", "name", "type", "status", "metric", "run_ref")
                tree = ttk.Treeview(scen_frame, columns=cols, show="headings", height=10)
                tree.heading("id", text="ID")
                tree.heading("name", text="Name")
                tree.heading("type", text="Type")
                tree.heading("status", text="Status")
                tree.heading("metric", text="Key Metric")
                tree.heading("run_ref", text="Run Manifest")
                for col, width in [
                    ("id", 110),
                    ("name", 200),
                    ("type", 120),
                    ("status", 90),
                    ("metric", 160),
                    ("run_ref", 240),
                ]:
                    tree.column(col, width=width, anchor="w")

                def _fmt_metric(val: Any) -> str:
                    if isinstance(val, dict):
                        # show first key:value
                        for k, v in val.items():
                            return f"{k}={v}"
                        return ""
                    return str(val)

                for s in scenarios:
                    run_ref = ""
                    rrefs = s.get("run_refs") or []
                    if rrefs:
                        run_ref = rrefs[-1]
                    tree.insert("", "end", iid=s.get("scenario_id", ""), values=(
                        s.get("scenario_id", ""),
                        s.get("scenario_name", ""),
                        s.get("simulation_type", ""),
                        s.get("last_run_status", ""),
                        _fmt_metric(s.get("best_result_metric", "")),
                        run_ref,
                    ))
                tree.pack(fill=tk.BOTH, expand=True)
                ttk.Label(scen_frame, text=f"Scenarios listed: {len(scenarios)}").pack(anchor="w", pady=(4, 0))

                def apply_filter(*args):
                    term = filter_var.get().strip().lower()
                    for item in tree.get_children():
                        vals = tree.item(item, "values")
                        hay = " ".join(str(v).lower() for v in vals)
                        tree.detach(item)
                        if term in hay or term == "":
                            tree.reattach(item, "", "end")

                filter_var.trace_add("write", apply_filter)

                def on_double_click(event):
                    item = tree.identify_row(event.y)
                    if not item:
                        return
                    vals = tree.item(item, "values")
                    run_ref = vals[5] if len(vals) > 5 else ""
                    if not run_ref:
                        return
                    # Resolve relative to repo root
                    root = None
                    current = Path(__file__).resolve()
                    for candidate in (current, *current.parents):
                        if (candidate / "N.py").exists():
                            root = candidate
                            break
                    if not root:
                        return
                    full_path = (root / run_ref).resolve()
                    try:
                        if os.name == "nt":
                            os.startfile(str(full_path))
                        else:
                            import subprocess
                            subprocess.Popen(["xdg-open", str(full_path)])
                    except Exception as exc:
                        messagebox.showinfo("Open manifest", f"Could not open {full_path}: {exc}")

                tree.bind("<Double-1>", on_double_click)

            except Exception as exc:
                ttk.Label(scen_frame, text=f"Error loading scenario catalog: {exc}").pack(anchor="w")

    def _build_tools_tab(self, notebook):
        """Build tools catalog tab from dataindex/tool_catalog.json."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Tools")

        try:
            from pathlib import Path
            import json
            catalog_path = None
            root = Path(__file__).resolve()
            for candidate in (root, *root.parents):
                probe = candidate / "dataindex" / "tool_catalog.json"
                if probe.exists():
                    catalog_path = probe
                    break
            if not catalog_path:
                ttk.Label(tab, text="tool_catalog.json not found").pack(padx=10, pady=10)
                return

            data = json.loads(catalog_path.read_text(encoding="utf-8"))
            tools = data.get("tools", [])

            tree = ttk.Treeview(tab, columns=("key", "name", "workspace", "category"), show="headings")
            for col, text, width in [
                ("key", "Tool Key", 160),
                ("name", "Tool Name", 260),
                ("workspace", "Workspace", 140),
                ("category", "Category", 140),
            ]:
                tree.heading(col, text=text)
                tree.column(col, width=width, anchor="w")

            for t in tools:
                tree.insert(
                    "",
                    "end",
                    iid=t.get("tool_key"),
                    values=(
                        t.get("tool_key", ""),
                        t.get("tool_name", ""),
                        t.get("default_workspace", ""),
                        t.get("ui_category", ""),
                    ),
                )

            tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
            ttk.Label(tab, text=f"Tools listed: {len(tools)}").pack(anchor="w", padx=8, pady=(0, 4))

            # Quick launcher for selected tool (opens schema-aware dialog)
            from .tool_runner_dialog import ToolRunnerDialog

            def open_runner():
                ToolRunnerDialog(tab, tools, root)

            ttk.Button(tab, text="Run a tool", command=open_runner).pack(anchor="w", padx=8, pady=(0, 8))
        except Exception as exc:
            ttk.Label(tab, text=f"Error loading tool catalog: {exc}").pack(padx=10, pady=10)

    def _build_startup_tab(self, notebook):
        """Build startup wizard tab (script triggers)."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Startup")
        try:
            from .startup_wizard import StartupWizard
            wizard = StartupWizard(tab)
            wizard.pack(fill=tk.BOTH, expand=True)
        except Exception as exc:
            ttk.Label(tab, text=f"Startup wizard unavailable: {exc}").pack(padx=10, pady=10)

    def _ensure_menu(self):
        """Attach a Tools menu to launch the runner dialog."""
        try:
            from pathlib import Path
            import json
            from .tool_runner_dialog import ToolRunnerDialog

            toplevel = self.winfo_toplevel()
            menubar = getattr(toplevel, "_ls_menubar", None)
            if menubar is None:
                menubar = tk.Menu(toplevel)
                toplevel.config(menu=menubar)
                toplevel._ls_menubar = menubar  # type: ignore[attr-defined]
            tools_menu = tk.Menu(menubar, tearoff=0)

            def open_runner():
                # Load catalog dynamically
                catalog_path = None
                root = Path(__file__).resolve()
                for candidate in (root, *root.parents):
                    probe = candidate / "dataindex" / "tool_catalog.json"
                    if probe.exists():
                        catalog_path = probe
                        break
                if not catalog_path:
                    messagebox.showinfo("Tools", "tool_catalog.json not found")
                    return
                data = json.loads(catalog_path.read_text(encoding="utf-8"))
                tools = data.get("tools", [])
                ToolRunnerDialog(self, tools, root)

            tools_menu.add_command(label="Run tool...", command=open_runner)
            menubar.add_cascade(label="Tools", menu=tools_menu)
        except Exception:
            # Fail silently to avoid UI breakage
            pass

    def _wire_window_callbacks(self):
        """Attach close handler to persist geometry."""
        try:
            toplevel = self.winfo_toplevel()
            toplevel.protocol("WM_DELETE_WINDOW", self._on_close)
        except Exception:
            pass

    def _restore_ui_state(self):
        """Restore window geometry if saved."""
        try:
            geo = self.ui_state.get("window_geometry")
            if geo:
                self.winfo_toplevel().geometry(geo)
        except Exception:
            pass

    def _on_close(self):
        """Save geometry and close."""
        try:
            geo = self.winfo_toplevel().geometry()
            self.ui_state["window_geometry"] = geo
            state_store.save_state(Path(__file__).resolve(), self.ui_state)
        except Exception:
            pass
        self.winfo_toplevel().destroy()

    def _build_runner_tab(self, notebook):
        """Build tool runner tab (schema-aware runner)."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Run Tools")

        try:
            from pathlib import Path
            import json
            from .tool_runner_dialog import ToolRunnerDialog

            catalog_path = None
            root = Path(__file__).resolve()
            for candidate in (root, *root.parents):
                probe = candidate / "dataindex" / "tool_catalog.json"
                if probe.exists():
                    catalog_path = probe
                    break
            if not catalog_path:
                ttk.Label(tab, text="tool_catalog.json not found").pack(padx=10, pady=10)
                return

            data = json.loads(catalog_path.read_text(encoding="utf-8"))
            tools = data.get("tools", [])
            ttk.Button(tab, text="Open Tool Runner", command=lambda: ToolRunnerDialog(tab, tools, root)).pack(anchor="w", padx=8, pady=8)
            ttk.Label(tab, text=f"Tools available: {len(tools)}").pack(anchor="w", padx=8)
        except Exception as exc:
            ttk.Label(tab, text=f"Tool runner unavailable: {exc}").pack(padx=10, pady=10)

    def start_monitoring(self):
        """Start monitoring"""
        if self.monitoring:
            return

        self.monitoring = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')

        # Start performance monitor
        self.monitor.start_system_monitoring(interval=5.0)

        # Start update thread
        self.monitor_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.monitor_thread.start()

        # Subscribe to alerts
        self.event_bus.subscribe('system.alert', self._on_alert)

    def stop_monitoring(self):
        """Stop monitoring"""
        if not self.monitoring:
            return

        self.monitoring = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

        # Stop performance monitor
        self.monitor.stop_system_monitoring()

        # Unsubscribe from alerts
        self.event_bus.unsubscribe('system.alert', self._on_alert)

    def _update_loop(self):
        """Background update loop"""
        while self.monitoring:
            try:
                self.after(0, self._update_dashboard)
            except:
                pass

            time.sleep(self.update_interval)

    def _update_dashboard(self):
        """Update all dashboard components"""
        # System health
        health = self.monitor.get_system_health()
        status = health['status']

        status_colors = {
            'healthy': '#00ff00',
            'warning': '#ffaa00',
            'degraded': '#ff8800',
            'critical': '#ff0000'
        }

        self.health_status.config(
            text=f"Status: {status.upper()}",
            foreground=status_colors.get(status, '#ffffff')
        )

        # Overview metrics
        cpu = health['system']['cpu_mean']
        memory = health['system']['memory_mean']

        self.overview_labels['cpu'].config(text=f"{cpu:.1f}%")
        self.overview_labels['memory'].config(text=f"{memory:.1f}%")

        # Cache hit rate
        cache_stats = self.cache.get_stats()
        if 'combined' in cache_stats:
            hit_rate = cache_stats['combined']['hit_rate']
            self.overview_labels['cache_hit'].config(text=f"{hit_rate:.1f}%")

        # Event throughput
        eb_stats = self.event_bus.get_stats()
        self.overview_labels['events'].config(text=f"{eb_stats['total_published']}")

        # Update charts
        for metric_type in MetricType:
            if metric_type.value in self.charts:
                recent = self.monitor.get_recent_metrics(metric_type, limit=1)
                if recent:
                    value = recent[0].value
                    stats = self.monitor.get_statistics(metric_type)
                    self.charts[metric_type.value].update_chart(value, stats)

        # Update cache stats
        if 'memory' in cache_stats:
            mem = cache_stats['memory']
            self.mem_cache_labels['size'].config(text=f"{mem['size']}/{mem['max_size']}")
            self.mem_cache_labels['hit_rate'].config(text=f"{mem['hit_rate']:.1f}%")
            self.mem_cache_labels['hits'].config(text=str(mem['hits']))
            self.mem_cache_labels['misses'].config(text=str(mem['misses']))
            self.mem_cache_labels['evictions'].config(text=str(mem['evictions']))

        if 'disk' in cache_stats:
            disk = cache_stats['disk']
            self.disk_cache_labels['size'].config(text=str(disk['size']))
            self.disk_cache_labels['hit_rate'].config(text=f"{disk['hit_rate']:.1f}%")
            self.disk_cache_labels['hits'].config(text=str(disk['hits']))
            self.disk_cache_labels['misses'].config(text=str(disk['misses']))

    def _on_alert(self, event):
        """Handle alert event"""
        # Create alert object
        from core.services.performance_monitor import PerformanceAlert

        alert = PerformanceAlert(
            level=AlertLevel(event.data.get('level', 'info')),
            message=event.data.get('message', ''),
            metric_type=MetricType(event.data.get('metric_type', 'response_time')),
            value=event.data.get('value', 0.0),
            threshold=event.data.get('threshold', 0.0),
            timestamp=datetime.now(),
            floor=event.data.get('floor')
        )

        self.after(0, lambda: self.alert_panel.add_alert(alert))


if __name__ == "__main__":
    # Test dashboard
    root = tk.Tk()
    root.title("LightSpeed Analytics Dashboard")
    root.geometry("1200x800")

    dashboard = AnalyticsDashboard(root, padding=10)
    dashboard.pack(fill=tk.BOTH, expand=True)

    # Auto-start monitoring
    dashboard.after(100, dashboard.start_monitoring)

    root.mainloop()
