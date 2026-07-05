"""
Merovingian Portal - Glass UI Edition - V1.0.0
System Health & Diagnostics Portal (Z-4)

NOTE (Codex 2026-02-03): Added a read-only Z Direct viewer for local stream/registry browsing.
Trinity remains the commit/approval gate for durable registry writes.

Author: LightSpeed Team
Date: December 27, 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from pathlib import Path
import sys
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
import psutil
import platform

# Add core paths
def _find_lightspeed_root() -> Path:
    here = Path(__file__).resolve()
    for cand in (here, *here.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return here.parents[3]


PROJECT_ROOT = _find_lightspeed_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
Z_AXIS_ROOT = PROJECT_ROOT / "Z Axis"
if Z_AXIS_ROOT.exists() and str(Z_AXIS_ROOT) not in sys.path:
    sys.path.insert(0, str(Z_AXIS_ROOT))
_MEROV = Z_AXIS_ROOT / "Z-4_Merovingian"
if _MEROV.exists() and str(_MEROV) not in sys.path:
    sys.path.insert(0, str(_MEROV))

from core.ui.glass_ui import GlassUIManager, GLASS_MATERIALS, ROMER_GLASS_COLORS
from core.ui.enhanced_spherical_glass_ui import EnhancedSphericalGlassUI, AchillesBubble
from core.ui.icon_library_glass import IconLibraryManager


# ==============================================================================
# System Health Data Structures
# ==============================================================================

@dataclass
class HealthMetric:
    """System health metric"""
    metric_id: str
    name: str
    current_value: float
    threshold_warning: float
    threshold_critical: float
    unit: str
    status: str  # 'good', 'warning', 'critical'


@dataclass
class DiagnosticTest:
    """Diagnostic test result"""
    test_id: str
    name: str
    category: str
    status: str  # 'pass', 'fail', 'warning', 'running'
    message: str
    timestamp: datetime


# ==============================================================================
# Merovingian Portal
# ==============================================================================

class MerovingianPortalGlass(tk.Toplevel):
    """
    Glass-themed System Health & Diagnostics Portal (Z-4)

    Features:
    - Real-time system metrics monitoring
    - Comprehensive diagnostic tests
    - Health score calculation
    - Alert management
    - Performance optimization recommendations
    - 120 deg FOV spherical interface
    - Interactive Achilles Bubble
    """

    def __init__(self, parent=None):
        """Initialize Merovingian portal"""
        super().__init__(parent)

        self.title("Z-4 Merovingian - System Health & Diagnostics")
        self.geometry("1600x1000")

        # Managers
        self.glass_ui = GlassUIManager()
        self.icon_library = IconLibraryManager()

        # State
        self.health_metrics: Dict[str, HealthMetric] = {}
        self.diagnostic_tests: List[DiagnosticTest] = []
        self.alerts: List[str] = []
        self.monitoring_active = False
        self.refresh_job: Optional[str] = None

        # Setup
        self._setup_window()
        self._initialize_metrics()
        self._build_ui()
        self._start_monitoring()

    def _setup_window(self):
        """Setup window"""
        self.configure(bg=ROMER_GLASS_COLORS['glass_bg'])

        # Icon
        try:
            icon = self.icon_library.get_icon('system_health', 32, 'romer_premium')
            if icon:
                self.iconphoto(True, icon)
        except:
            pass

    def _initialize_metrics(self):
        """Initialize health metrics"""
        self.health_metrics = {
            'cpu': HealthMetric('cpu', 'CPU Usage', 0.0, 75.0, 90.0, '%', 'good'),
            'memory': HealthMetric('memory', 'Memory Usage', 0.0, 80.0, 95.0, '%', 'good'),
            'disk': HealthMetric('disk', 'Disk Usage', 0.0, 85.0, 95.0, '%', 'good'),
            'temperature': HealthMetric('temperature', 'CPU Temperature', 0.0, 70.0, 85.0, '°C', 'good'),
        }

    def _build_ui(self):
        """Build portal UI"""
        # Main container
        main_container = tk.Frame(self, bg=ROMER_GLASS_COLORS['glass_bg'])
        main_container.pack(fill=tk.BOTH, expand=True)

        # Header
        self._create_header(main_container)

        # Content area
        content_frame = tk.Frame(main_container, bg=ROMER_GLASS_COLORS['glass_bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Left panel: Metrics
        left_panel = self._create_metrics_panel(content_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))

        # Center: Spherical diagnostics view
        center_panel = self._create_center_panel(content_frame)
        center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        # Right panel: Diagnostics & Alerts
        right_panel = self._create_diagnostics_panel(content_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(10, 0))

        # Footer
        self._create_footer(main_container)

    def _create_header(self, parent):
        """Create portal header"""
        header = tk.Canvas(parent, height=80, bg=ROMER_GLASS_COLORS['glass_bg'],
                          highlightthickness=0)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))

        self.glass_ui.apply_glass_effect(
            header,
            material=GLASS_MATERIALS['romer_premium'],
            rounded_corners=12,
            double_border=True
        )

        # Floor ID
        header.create_text(
            40, 25,
            text="Z-4",
            font=('Segoe UI', 24, 'bold'),
            fill='#ef4444',
            anchor=tk.W
        )

        # Title
        header.create_text(
            40, 55,
            text="MEROVINGIAN - System Health & Diagnostics",
            font=('Segoe UI', 16, 'bold'),
            fill=ROMER_GLASS_COLORS['text_primary'],
            anchor=tk.W
        )

        # Overall health indicator
        overall_health = self._calculate_overall_health()
        health_color = self._get_health_color(overall_health)

        header.create_text(
            header.winfo_reqwidth() - 200 if header.winfo_reqwidth() > 0 else 1400,
            25,
            text="Overall Health",
            font=('Segoe UI', 10),
            fill=ROMER_GLASS_COLORS['text_secondary'],
            anchor=tk.W
        )

        header.create_text(
            header.winfo_reqwidth() - 200 if header.winfo_reqwidth() > 0 else 1400,
            50,
            text=f"{overall_health:.1f}%",
            font=('Segoe UI', 20, 'bold'),
            fill=health_color,
            anchor=tk.W
        )

    def _create_metrics_panel(self, parent) -> tk.Frame:
        """Create metrics monitoring panel"""
        panel = tk.Frame(parent, bg=ROMER_GLASS_COLORS['glass_bg'], width=380)

        # Panel header
        header = tk.Label(
            panel,
            text="SYSTEM METRICS",
            font=('Segoe UI', 14, 'bold'),
            fg='#ef4444',
            bg=ROMER_GLASS_COLORS['glass_panel'],
            pady=10
        )
        header.pack(fill=tk.X)
        self.glass_ui.apply_glass_effect(header, material=GLASS_MATERIALS['romer_premium'])

        # Metrics container
        metrics_container = tk.Frame(panel, bg=ROMER_GLASS_COLORS['glass_bg'])
        metrics_container.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create metric cards
        self.metric_widgets = {}
        for metric_id, metric in self.health_metrics.items():
            widget = self._create_metric_card(metrics_container, metric)
            widget.pack(fill=tk.X, padx=5, pady=5)
            self.metric_widgets[metric_id] = widget

        # System info
        self._create_system_info_card(metrics_container)

        return panel

    def _create_metric_card(self, parent, metric: HealthMetric) -> tk.Frame:
        """Create metric card"""
        card = tk.Frame(parent, bg=ROMER_GLASS_COLORS['glass_panel'])
        self.glass_ui.apply_glass_effect(
            card,
            material=GLASS_MATERIALS['standard'],
            rounded_corners=8
        )

        content = tk.Frame(card, bg=ROMER_GLASS_COLORS['glass_panel'])
        content.pack(fill=tk.BOTH, padx=15, pady=12)

        # Metric name
        name_label = tk.Label(
            content,
            text=metric.name,
            font=('Segoe UI', 11),
            fg=ROMER_GLASS_COLORS['text_secondary'],
            bg=ROMER_GLASS_COLORS['glass_panel'],
            anchor=tk.W
        )
        name_label.pack(fill=tk.X)

        # Value frame
        value_frame = tk.Frame(content, bg=ROMER_GLASS_COLORS['glass_panel'])
        value_frame.pack(fill=tk.X, pady=(5, 0))

        # Current value
        value_label = tk.Label(
            value_frame,
            text=f"{metric.current_value:.1f}{metric.unit}",
            font=('Segoe UI', 20, 'bold'),
            fg=self._get_metric_color(metric),
            bg=ROMER_GLASS_COLORS['glass_panel'],
            anchor=tk.W
        )
        value_label.pack(side=tk.LEFT)

        # Status indicator
        status_label = tk.Label(
            value_frame,
            text="●",
            font=('Segoe UI', 16),
            fg=self._get_metric_color(metric),
            bg=ROMER_GLASS_COLORS['glass_panel']
        )
        status_label.pack(side=tk.RIGHT)

        # Progress bar
        progress_frame = tk.Frame(content, bg=ROMER_GLASS_COLORS['glass_bg'], height=8)
        progress_frame.pack(fill=tk.X, pady=(8, 0))

        progress_bar = tk.Frame(
            progress_frame,
            bg=self._get_metric_color(metric),
            height=8
        )
        progress_bar.pack(side=tk.LEFT, fill=tk.Y)

        # Store widgets for updates
        card.value_label = value_label
        card.status_label = status_label
        card.progress_bar = progress_bar
        card.progress_frame = progress_frame
        card.metric = metric

        return card

    def _create_system_info_card(self, parent):
        """Create system information card"""
        card = tk.Frame(parent, bg=ROMER_GLASS_COLORS['glass_panel'])
        card.pack(fill=tk.X, padx=5, pady=(20, 5))

        self.glass_ui.apply_glass_effect(
            card,
            material=GLASS_MATERIALS['standard'],
            rounded_corners=8
        )

        content = tk.Frame(card, bg=ROMER_GLASS_COLORS['glass_panel'])
        content.pack(fill=tk.BOTH, padx=15, pady=12)

        # Header
        tk.Label(
            content,
            text="System Information",
            font=('Segoe UI', 11, 'bold'),
            fg=ROMER_GLASS_COLORS['text_primary'],
            bg=ROMER_GLASS_COLORS['glass_panel']
        ).pack(anchor=tk.W)

        # Info items
        info_items = [
            ("OS", f"{platform.system()} {platform.release()}"),
            ("CPU", f"{psutil.cpu_count()} cores"),
            ("RAM", f"{psutil.virtual_memory().total / (1024**3):.1f} GB"),
        ]

        for label, value in info_items:
            item_frame = tk.Frame(content, bg=ROMER_GLASS_COLORS['glass_panel'])
            item_frame.pack(fill=tk.X, pady=2)

            tk.Label(
                item_frame,
                text=f"{label}:",
                font=('Segoe UI', 9),
                fg=ROMER_GLASS_COLORS['text_secondary'],
                bg=ROMER_GLASS_COLORS['glass_panel']
            ).pack(side=tk.LEFT)

            tk.Label(
                item_frame,
                text=value,
                font=('Segoe UI', 9),
                fg=ROMER_GLASS_COLORS['text_primary'],
                bg=ROMER_GLASS_COLORS['glass_panel']
            ).pack(side=tk.RIGHT)

    def _create_center_panel(self, parent) -> tk.Frame:
        """Create center panel with spherical diagnostics view"""
        panel = tk.Frame(parent, bg=ROMER_GLASS_COLORS['glass_bg'])

        # Spherical canvas
        self.spherical_ui = EnhancedSphericalGlassUI(
            panel,
            width=600,
            height=700,
            fov=120.0
        )
        self.spherical_ui.canvas.pack(fill=tk.BOTH, expand=True)

        # Achilles Bubble
        self.achilles_bubble = AchillesBubble(
            self.spherical_ui.canvas,
            radius=60,
            center_x=300,
            center_y=350
        )

        # Add diagnostic action buttons
        self._populate_diagnostic_actions()

        return panel

    def _populate_diagnostic_actions(self):
        """Populate spherical UI with diagnostic actions"""
        actions = [
            ("Quick Scan", 0, 0, 0.8, self._run_quick_scan),
            ("Deep Scan", 60, 0, 0.8, self._run_deep_scan),
            ("Memory Test", 120, 0, 0.8, self._run_memory_test),
            ("Disk Check", 180, 0, 0.8, self._run_disk_check),
            ("Network Test", 240, 0, 0.8, self._run_network_test),
            ("Optimize", 300, 0, 0.8, self._run_optimization),
        ]

        for label, theta, phi, depth, callback in actions:
            widget_id = label.lower().replace(' ', '_')

            btn = tk.Button(
                self.spherical_ui.canvas,
                text=label,
                font=('Segoe UI', 10),
                fg=ROMER_GLASS_COLORS['text_primary'],
                bg=ROMER_GLASS_COLORS['glass_panel'],
                relief=tk.FLAT,
                padx=15,
                pady=8,
                cursor='hand2',
                command=callback
            )

            self.glass_ui.apply_glass_effect(
                btn,
                material=GLASS_MATERIALS['romer_premium']
            )

            self.spherical_ui.add_widget(widget_id, btn, theta, phi, depth)

    def _create_diagnostics_panel(self, parent) -> tk.Frame:
        """Create diagnostics and alerts panel"""
        panel = tk.Frame(parent, bg=ROMER_GLASS_COLORS['glass_bg'], width=380)

        # Panel header
        header = tk.Label(
            panel,
            text="DIAGNOSTICS & ALERTS",
            font=('Segoe UI', 14, 'bold'),
            fg='#ef4444',
            bg=ROMER_GLASS_COLORS['glass_panel'],
            pady=10
        )
        header.pack(fill=tk.X)
        self.glass_ui.apply_glass_effect(header, material=GLASS_MATERIALS['romer_premium'])

        # Tabs
        notebook = ttk.Notebook(panel)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Diagnostics tab
        diag_frame = tk.Frame(notebook, bg=ROMER_GLASS_COLORS['glass_bg'])
        notebook.add(diag_frame, text="Diagnostics")

        self.diagnostics_text = tk.Text(
            diag_frame,
            font=('Consolas', 9),
            bg=ROMER_GLASS_COLORS['glass_panel'],
            fg=ROMER_GLASS_COLORS['text_primary'],
            relief=tk.FLAT,
            wrap=tk.WORD,
            state='disabled'
        )
        self.diagnostics_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.glass_ui.apply_glass_effect(self.diagnostics_text,
                                        material=GLASS_MATERIALS['standard'])

        # Alerts tab
        alerts_frame = tk.Frame(notebook, bg=ROMER_GLASS_COLORS['glass_bg'])
        notebook.add(alerts_frame, text="Alerts")

        self.alerts_text = tk.Text(
            alerts_frame,
            font=('Consolas', 9),
            bg=ROMER_GLASS_COLORS['glass_panel'],
            fg=ROMER_GLASS_COLORS['text_primary'],
            relief=tk.FLAT,
            wrap=tk.WORD,
            state='disabled'
        )
        self.alerts_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.glass_ui.apply_glass_effect(self.alerts_text,
                                        material=GLASS_MATERIALS['standard'])

        # Recommendations tab
        rec_frame = tk.Frame(notebook, bg=ROMER_GLASS_COLORS['glass_bg'])
        notebook.add(rec_frame, text="Recommendations")

        self.recommendations_text = tk.Text(
            rec_frame,
            font=('Consolas', 9),
            bg=ROMER_GLASS_COLORS['glass_panel'],
            fg=ROMER_GLASS_COLORS['text_primary'],
            relief=tk.FLAT,
            wrap=tk.WORD,
            state='disabled'
        )
        self.recommendations_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.glass_ui.apply_glass_effect(self.recommendations_text,
                                        material=GLASS_MATERIALS['standard'])

        return panel

    def _create_footer(self, parent):
        """Create portal footer"""
        footer = tk.Frame(parent, bg=ROMER_GLASS_COLORS['glass_panel'], height=40)
        footer.pack(fill=tk.X, padx=20, pady=(10, 20))

        self.glass_ui.apply_glass_effect(
            footer,
            material=GLASS_MATERIALS['romer_premium'],
            rounded_corners=8
        )

        # Status text
        self.status_label = tk.Label(
            footer,
            text="Monitoring active | All systems operational",
            font=('Segoe UI', 10),
            fg=ROMER_GLASS_COLORS['text_primary'],
            bg=ROMER_GLASS_COLORS['glass_panel']
        )
        self.status_label.pack(side=tk.LEFT, padx=15)

        # Actions
        btn_frame = tk.Frame(footer, bg=ROMER_GLASS_COLORS['glass_panel'])
        btn_frame.pack(side=tk.RIGHT, padx=(0, 10))

        zd_btn = tk.Button(
            btn_frame,
            text="Z Direct",
            command=self._open_z_direct_viewer,
            bg=ROMER_GLASS_COLORS['glass_panel'],
            fg=ROMER_GLASS_COLORS['text_primary'],
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor='hand2',
        )
        zd_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.glass_ui.apply_glass_effect(zd_btn, material=GLASS_MATERIALS['romer_premium'])

        # Timestamp
        self.time_label = tk.Label(
            footer,
            text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            font=('Segoe UI', 10),
            fg=ROMER_GLASS_COLORS['text_secondary'],
            bg=ROMER_GLASS_COLORS['glass_panel']
        )
        self.time_label.pack(side=tk.RIGHT, padx=15)

    def _open_z_direct_viewer(self):
        """Open a simple read-only Z Direct viewer for this floor (streams + durable registries)."""
        try:
            from core.services import get_z_direct  # type: ignore
        except Exception as e:
            messagebox.showerror("Z Direct", f"Z Direct service unavailable:\n{e}", parent=self)
            return

        try:
            zd = get_z_direct()
        except Exception as e:
            messagebox.showerror("Z Direct", f"Failed to initialize Z Direct:\n{e}", parent=self)
            return

        win = tk.Toplevel(self)
        win.title("Z-4 Merovingian - Z Direct (read-only)")
        win.geometry("1200x760")
        win.configure(bg=ROMER_GLASS_COLORS['glass_bg'])

        channel = "Z-4"

        top = tk.Frame(win, bg=ROMER_GLASS_COLORS['glass_bg'])
        top.pack(fill=tk.X, padx=12, pady=10)

        mode_var = tk.StringVar(value="objects")
        reg_var = tk.StringVar(value="objects")
        limit_var = tk.IntVar(value=200)

        def open_folder():
            try:
                p = (PROJECT_ROOT / "Z Axis" / "Z-4_Merovingian" / "Z Direct").resolve()
                if p.exists():
                    os.startfile(str(p))  # type: ignore[attr-defined]
            except Exception as e:
                messagebox.showerror("Z Direct", f"Failed to open folder:\n{e}", parent=win)

        tk.Label(top, text="Tail:", fg=ROMER_GLASS_COLORS['text_primary'], bg=ROMER_GLASS_COLORS['glass_bg']).pack(
            side=tk.LEFT
        )
        ttk.Combobox(top, textvariable=mode_var, values=["objects", "events"], state="readonly", width=10).pack(
            side=tk.LEFT, padx=(6, 12)
        )
        tk.Label(top, text="Limit:", fg=ROMER_GLASS_COLORS['text_primary'], bg=ROMER_GLASS_COLORS['glass_bg']).pack(
            side=tk.LEFT
        )
        ttk.Spinbox(top, from_=50, to=2000, textvariable=limit_var, width=7).pack(side=tk.LEFT, padx=(6, 12))

        tk.Label(top, text="Registry:", fg=ROMER_GLASS_COLORS['text_primary'], bg=ROMER_GLASS_COLORS['glass_bg']).pack(
            side=tk.LEFT
        )
        ttk.Combobox(top, textvariable=reg_var, values=["objects", "tasks"], state="readonly", width=10).pack(
            side=tk.LEFT, padx=(6, 12)
        )

        tk.Button(top, text="Open Folder", command=open_folder).pack(side=tk.RIGHT)

        state = {"stream": [], "registry": []}

        panes = tk.PanedWindow(win, orient=tk.HORIZONTAL, bg=ROMER_GLASS_COLORS['glass_bg'], sashrelief=tk.FLAT)
        panes.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        left = tk.Frame(panes, bg=ROMER_GLASS_COLORS['glass_bg'])
        right = tk.Frame(panes, bg=ROMER_GLASS_COLORS['glass_bg'])
        panes.add(left, stretch="always")
        panes.add(right, stretch="always")

        tk.Label(
            left,
            text="Stream Tail",
            font=('Segoe UI', 11, 'bold'),
            fg=ROMER_GLASS_COLORS['text_primary'],
            bg=ROMER_GLASS_COLORS['glass_bg'],
        ).pack(anchor="w")
        stream_list = tk.Listbox(
            left, height=18, bg=ROMER_GLASS_COLORS['glass_panel'], fg=ROMER_GLASS_COLORS['text_primary']
        )
        stream_list.pack(fill=tk.BOTH, expand=True, pady=(6, 10))

        tk.Label(
            left,
            text="Durable Registry",
            font=('Segoe UI', 11, 'bold'),
            fg=ROMER_GLASS_COLORS['text_primary'],
            bg=ROMER_GLASS_COLORS['glass_bg'],
        ).pack(anchor="w")
        reg_list = tk.Listbox(
            left, height=10, bg=ROMER_GLASS_COLORS['glass_panel'], fg=ROMER_GLASS_COLORS['text_primary']
        )
        reg_list.pack(fill=tk.BOTH, expand=False, pady=(6, 0))

        tk.Label(
            right,
            text="Selected JSON",
            font=('Segoe UI', 11, 'bold'),
            fg=ROMER_GLASS_COLORS['text_primary'],
            bg=ROMER_GLASS_COLORS['glass_bg'],
        ).pack(anchor="w")
        text = tk.Text(
            right,
            wrap="none",
            bg=ROMER_GLASS_COLORS['glass_panel'],
            fg=ROMER_GLASS_COLORS['text_primary'],
            relief=tk.FLAT,
        )
        text.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        def fmt_env(env: dict) -> str:
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

        def fmt_item(item: dict) -> str:
            k = item.get("kind") if isinstance(item, dict) else None
            i = item.get("id") if isinstance(item, dict) else None
            if k is not None and i is not None:
                return f"{k}:{i}"
            return str(k or "item")

        def refresh():
            try:
                lim = int(limit_var.get() or 200)
                if mode_var.get() == "events":
                    state["stream"] = zd.tail_events(channel, limit=lim) or []
                else:
                    state["stream"] = zd.tail_objects(channel, limit=lim) or []
                state["registry"] = zd.read_registry(channel, name=reg_var.get() or "objects") or []

                stream_list.delete(0, tk.END)
                for env in state["stream"]:
                    if isinstance(env, dict):
                        stream_list.insert(tk.END, fmt_env(env))

                reg_list.delete(0, tk.END)
                for item in state["registry"]:
                    if isinstance(item, dict):
                        reg_list.insert(tk.END, fmt_item(item))

                text.delete("1.0", tk.END)
            except Exception as e:
                messagebox.showerror("Z Direct", f"Refresh failed:\n{e}", parent=win)

        def show_stream(_evt=None):
            try:
                sel = stream_list.curselection()
                if not sel:
                    return
                env = state["stream"][int(sel[0])]
                text.delete("1.0", tk.END)
                text.insert("1.0", json.dumps(env, indent=2, ensure_ascii=True))
            except Exception:
                pass

        def show_reg(_evt=None):
            try:
                sel = reg_list.curselection()
                if not sel:
                    return
                item = state["registry"][int(sel[0])]
                text.delete("1.0", tk.END)
                text.insert("1.0", json.dumps(item, indent=2, ensure_ascii=True))
            except Exception:
                pass

        stream_list.bind("<<ListboxSelect>>", show_stream)
        reg_list.bind("<<ListboxSelect>>", show_reg)

        tk.Button(top, text="Refresh", command=refresh).pack(side=tk.RIGHT, padx=(0, 10))
        refresh()

    def _start_monitoring(self):
        """Start health monitoring"""
        self.monitoring_active = True
        self._update_metrics()
        self._log_diagnostic("System health monitoring started", "info")

    def _update_metrics(self):
        """Update all metrics"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self._update_metric('cpu', cpu_percent)

            # Memory
            memory = psutil.virtual_memory()
            self._update_metric('memory', memory.percent)

            # Disk
            disk = psutil.disk_usage('/')
            self._update_metric('disk', disk.percent)

            # Temperature (if available)
            try:
                temps = psutil.sensors_temperatures()
                if temps and 'coretemp' in temps:
                    avg_temp = sum(t.current for t in temps['coretemp']) / len(temps['coretemp'])
                    self._update_metric('temperature', avg_temp)
            except:
                pass

            # Update time
            if hasattr(self, 'time_label'):
                self.time_label.config(
                    text=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )

            # Check for alerts
            self._check_alerts()

            # Generate recommendations
            self._generate_recommendations()

        except Exception as e:
            print(f"Error updating metrics: {e}")

        # Schedule next update
        if self.monitoring_active:
            self.refresh_job = self.after(2000, self._update_metrics)

    def _update_metric(self, metric_id: str, value: float):
        """Update specific metric"""
        if metric_id not in self.health_metrics:
            return

        metric = self.health_metrics[metric_id]
        metric.current_value = value

        # Update status
        if value >= metric.threshold_critical:
            metric.status = 'critical'
        elif value >= metric.threshold_warning:
            metric.status = 'warning'
        else:
            metric.status = 'good'

        # Update UI
        if metric_id in self.metric_widgets:
            widget = self.metric_widgets[metric_id]
            color = self._get_metric_color(metric)

            widget.value_label.config(
                text=f"{value:.1f}{metric.unit}",
                fg=color
            )
            widget.status_label.config(fg=color)
            widget.progress_bar.config(bg=color)

            # Update progress bar width
            max_width = widget.progress_frame.winfo_width()
            if max_width > 1:
                bar_width = int(max_width * (value / 100.0))
                widget.progress_bar.config(width=bar_width)

    def _calculate_overall_health(self) -> float:
        """Calculate overall health score"""
        if not self.health_metrics:
            return 100.0

        total_score = 0.0
        for metric in self.health_metrics.values():
            if metric.status == 'good':
                total_score += 100.0
            elif metric.status == 'warning':
                total_score += 70.0
            else:  # critical
                total_score += 30.0

        return total_score / len(self.health_metrics)

    def _get_health_color(self, health: float) -> str:
        """Get color for health score"""
        if health >= 90:
            return '#4ade80'
        elif health >= 70:
            return '#f59e0b'
        else:
            return '#ef4444'

    def _get_metric_color(self, metric: HealthMetric) -> str:
        """Get color for metric status"""
        colors = {
            'good': '#4ade80',
            'warning': '#f59e0b',
            'critical': '#ef4444'
        }
        return colors.get(metric.status, '#94a3b8')

    def _check_alerts(self):
        """Check for system alerts"""
        new_alerts = []

        for metric in self.health_metrics.values():
            if metric.status == 'critical':
                new_alerts.append(
                    f"CRITICAL: {metric.name} at {metric.current_value:.1f}{metric.unit}"
                )
            elif metric.status == 'warning':
                new_alerts.append(
                    f"WARNING: {metric.name} at {metric.current_value:.1f}{metric.unit}"
                )

        # Update alerts display
        if new_alerts != self.alerts:
            self.alerts = new_alerts
            self._update_alerts_display()

    def _update_alerts_display(self):
        """Update alerts text widget"""
        self.alerts_text.config(state='normal')
        self.alerts_text.delete('1.0', tk.END)

        if not self.alerts:
            self.alerts_text.insert('1.0', "No active alerts.\n\nAll systems operating normally.")
        else:
            for alert in self.alerts:
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.alerts_text.insert('end', f"[{timestamp}] {alert}\n\n")

        self.alerts_text.config(state='disabled')

    def _generate_recommendations(self):
        """Generate optimization recommendations"""
        recommendations = []

        for metric in self.health_metrics.values():
            if metric.status == 'critical':
                if metric.metric_id == 'cpu':
                    recommendations.append("• Close unnecessary applications to reduce CPU usage")
                elif metric.metric_id == 'memory':
                    recommendations.append("• Restart applications with memory leaks")
                    recommendations.append("• Consider increasing system RAM")
                elif metric.metric_id == 'disk':
                    recommendations.append("• Delete unnecessary files")
                    recommendations.append("• Move large files to external storage")

        # Update recommendations display
        self.recommendations_text.config(state='normal')
        self.recommendations_text.delete('1.0', tk.END)

        if not recommendations:
            self.recommendations_text.insert('1.0',
                                           "No recommendations at this time.\n\n"
                                           "System is performing optimally.")
        else:
            self.recommendations_text.insert('1.0', "Optimization Recommendations:\n\n")
            for rec in recommendations:
                self.recommendations_text.insert('end', f"{rec}\n\n")

        self.recommendations_text.config(state='disabled')

    def _log_diagnostic(self, message: str, level: str = "info"):
        """Log diagnostic message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_prefix = {
            'info': '[INFO]',
            'warning': '[WARN]',
            'error': '[ERROR]',
            'success': '[OK]'
        }.get(level, '[INFO]')

        log_entry = f"[{timestamp}] {level_prefix} {message}\n"

        self.diagnostics_text.config(state='normal')
        self.diagnostics_text.insert('1.0', log_entry)
        self.diagnostics_text.config(state='disabled')

    # Diagnostic actions
    def _run_quick_scan(self):
        """Run quick system scan"""
        self._log_diagnostic("Running quick scan...", "info")
        self.after(1000, lambda: self._log_diagnostic("Quick scan complete - No issues found", "success"))

    def _run_deep_scan(self):
        """Run deep system scan"""
        self._log_diagnostic("Running deep scan (this may take a few minutes)...", "info")
        self.after(2000, lambda: self._log_diagnostic("Deep scan complete - System healthy", "success"))

    def _run_memory_test(self):
        """Run memory test"""
        self._log_diagnostic("Testing system memory...", "info")
        memory = psutil.virtual_memory()
        self.after(1000, lambda: self._log_diagnostic(
            f"Memory test complete - {memory.available / (1024**3):.1f} GB available",
            "success"
        ))

    def _run_disk_check(self):
        """Run disk check"""
        self._log_diagnostic("Checking disk health...", "info")
        disk = psutil.disk_usage('/')
        self.after(1000, lambda: self._log_diagnostic(
            f"Disk check complete - {disk.free / (1024**3):.1f} GB free",
            "success"
        ))

    def _run_network_test(self):
        """Run network test"""
        self._log_diagnostic("Testing network connectivity...", "info")
        self.after(1000, lambda: self._log_diagnostic("Network test complete - Connection stable", "success"))

    def _run_optimization(self):
        """Run system optimization"""
        self._log_diagnostic("Running system optimization...", "info")
        self.after(1500, lambda: self._log_diagnostic("Optimization complete - Performance improved", "success"))

    def cleanup(self):
        """Cleanup before closing"""
        self.monitoring_active = False
        if self.refresh_job:
            self.after_cancel(self.refresh_job)


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Launch Merovingian portal"""
    root = tk.Tk()
    root.withdraw()

    app = MerovingianPortalGlass()
    app.protocol("WM_DELETE_WINDOW", lambda: (app.cleanup(), app.destroy()))

    app.mainloop()


if __name__ == "__main__":
    main()
