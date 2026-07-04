"""
TheConstruct Dashboard - Glass UI Edition - V1.0.0
Holospace command deck for LightSpeed

Author: LightSpeed Team
Date: December 27, 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import sys
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import psutil
import json

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
# Dashboard Configuration
# ==============================================================================

@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    title: str = "TheConstruct - LightSpeed Holospace"
    width: int = 1920
    height: int = 1080
    fov: float = 120.0
    theme: str = "romer_premium"
    enable_achilles: bool = True
    enable_neo: bool = True
    show_system_status: bool = True
    auto_refresh_interval: int = 2000  # ms


@dataclass
class ZFloorStatus:
    """Z-Floor status information"""
    floor_id: str
    floor_name: str
    status: str  # 'online', 'offline', 'error', 'maintenance'
    active_tools: int
    health_score: float  # 0.0-1.0
    last_activity: Optional[datetime] = None


# ==============================================================================
# TheConstruct Dashboard
# ==============================================================================

class ConstructDashboardGlass(tk.Tk):
    """
    Glass-themed central dashboard for TheConstruct (Z0)

    Features:
    - 120° FOV spherical interface
    - Interactive Achilles Bubble
    - Real-time Z-floor status monitoring
    - Achilles-facing operator console integration
    - System health metrics
    - Quick launch portals to all Z-floors
    - LightSpeed premium glass theme
    """

    def __init__(self, config: Optional[DashboardConfig] = None):
        """Initialize TheConstruct dashboard"""
        super().__init__()

        self.config = config or DashboardConfig()

        # Managers
        self.glass_ui = GlassUIManager()
        self.icon_library = IconLibraryManager()

        # State
        self.z_floor_status: Dict[str, ZFloorStatus] = {}
        self.active_portals: Dict[str, tk.Toplevel] = {}
        self.refresh_job: Optional[str] = None

        # Setup
        self._setup_window()
        self._load_z_floor_status()
        self._build_ui()
        self._start_monitoring()

    def _setup_window(self):
        """Setup main window"""
        self.title(self.config.title)
        self.geometry(f"{self.config.width}x{self.config.height}")

        # Glass background
        self.configure(bg=ROMER_GLASS_COLORS['glass_bg'])

        # Fullscreen option
        self.bind('<F11>', lambda e: self.attributes('-fullscreen',
                                                     not self.attributes('-fullscreen')))
        self.bind('<Escape>', lambda e: self.attributes('-fullscreen', False))

    def _build_ui(self):
        """Build dashboard UI"""
        # Main container
        main_container = tk.Frame(self, bg=ROMER_GLASS_COLORS['glass_bg'])
        main_container.pack(fill=tk.BOTH, expand=True)

        # Header
        self._create_header(main_container)

        # Content area with spherical UI
        content_frame = tk.Frame(main_container, bg=ROMER_GLASS_COLORS['glass_bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Left panel: Z-Floor status
        left_panel = self._create_left_panel(content_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))

        # Center: Spherical interface with Achilles Bubble
        center_panel = self._create_center_panel(content_frame)
        center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        # Right panel: System status
        right_panel = self._create_right_panel(content_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(10, 0))

        # Footer
        self._create_footer(main_container)

    def _create_header(self, parent):
        """Create dashboard header"""
        header = tk.Canvas(parent, height=80, bg=ROMER_GLASS_COLORS['glass_bg'],
                          highlightthickness=0)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))

        # Apply glass effect
        self.glass_ui.apply_glass_effect(
            header,
            material=GLASS_MATERIALS['romer_premium'],
            rounded_corners=12,
            double_border=True
        )

        # Title
        header.create_text(
            40, 40,
            text="⚡ LIGHTSPEED",
            font=('Segoe UI', 28, 'bold'),
            fill=ROMER_GLASS_COLORS['primary'],
            anchor=tk.W
        )

        # Subtitle
        header.create_text(
            42, 55,
            text="Holospace Command Deck - Z0",
            font=('Segoe UI', 11),
            fill=ROMER_GLASS_COLORS['text_secondary'],
            anchor=tk.W
        )

        # NEO/Achilles button
        if self.config.enable_neo:
            neo_btn_x = header.winfo_reqwidth() - 200 if header.winfo_reqwidth() > 0 else 1720

            # NEO button background
            btn_bg = header.create_rectangle(
                neo_btn_x - 10, 20, neo_btn_x + 150, 60,
                fill=ROMER_GLASS_COLORS['glass_panel'],
                outline=ROMER_GLASS_COLORS['primary'],
                width=2
            )

            # NEO icon and text
            header.create_text(
                neo_btn_x, 40,
                text="🤖 Achilles Console",
                font=('Segoe UI', 12, 'bold'),
                fill=ROMER_GLASS_COLORS['primary'],
                anchor=tk.W
            )

            # Bind click
            header.tag_bind(btn_bg, '<Button-1>', lambda e: self._open_neo())

    def _create_left_panel(self, parent) -> tk.Frame:
        """Create left panel with Z-floor status"""
        panel = tk.Frame(parent, bg=ROMER_GLASS_COLORS['glass_bg'], width=320)

        # Panel header
        header = tk.Label(
            panel,
            text="SMART FLOOR STATUS",
            font=('Segoe UI', 14, 'bold'),
            fg=ROMER_GLASS_COLORS['primary'],
            bg=ROMER_GLASS_COLORS['glass_panel'],
            pady=10
        )
        header.pack(fill=tk.X)
        self.glass_ui.apply_glass_effect(header, material=GLASS_MATERIALS['romer_premium'])

        # Scrollable floor list
        canvas = tk.Canvas(panel, bg=ROMER_GLASS_COLORS['glass_bg'],
                          highlightthickness=0)
        scrollbar = ttk.Scrollbar(panel, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=ROMER_GLASS_COLORS['glass_bg'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Create floor status cards
        self._create_floor_status_cards(scrollable_frame)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.floor_cards_container = scrollable_frame

        return panel

    def _create_floor_status_cards(self, parent):
        """Create status cards for each Z-floor"""
        z_floors = [
            ("Z-4", "Merovingian", "System Health"),
            ("Z-3", "Smith", "Framework Management"),
            ("Z-2", "Oracle", "Data Intelligence"),
            ("Z-1", "Morpheus", "Knowledge & Analysis"),
            ("Z0", "TheConstruct", "Physics & 3D"),
            ("Z+1", "Architect", "Planning & Dev Tools"),
            ("Z+2", "Neo", "AI & Intelligence"),
            ("Z+3", "Trinity", "UI & Dashboards"),
        ]

        for floor_id, floor_name, description in z_floors:
            self._create_floor_card(parent, floor_id, floor_name, description)

    def _create_floor_card(self, parent, floor_id: str, floor_name: str,
                           description: str):
        """Create individual floor status card"""
        card = tk.Frame(parent, bg=ROMER_GLASS_COLORS['glass_panel'],
                       relief=tk.FLAT, bd=0)
        card.pack(fill=tk.X, padx=5, pady=5)

        # Apply glass effect
        self.glass_ui.apply_glass_effect(
            card,
            material=GLASS_MATERIALS['standard'],
            rounded_corners=8
        )

        # Content
        content = tk.Frame(card, bg=ROMER_GLASS_COLORS['glass_panel'])
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Floor ID and name
        title_frame = tk.Frame(content, bg=ROMER_GLASS_COLORS['glass_panel'])
        title_frame.pack(fill=tk.X)

        floor_id_label = tk.Label(
            title_frame,
            text=floor_id,
            font=('Segoe UI', 11, 'bold'),
            fg=ROMER_GLASS_COLORS['primary'],
            bg=ROMER_GLASS_COLORS['glass_panel']
        )
        floor_id_label.pack(side=tk.LEFT)

        floor_name_label = tk.Label(
            title_frame,
            text=f" {floor_name}",
            font=('Segoe UI', 11),
            fg=ROMER_GLASS_COLORS['text_primary'],
            bg=ROMER_GLASS_COLORS['glass_panel']
        )
        floor_name_label.pack(side=tk.LEFT)

        # Status indicator
        status = self.z_floor_status.get(floor_id)
        status_color = self._get_status_color(status.status if status else 'offline')

        status_indicator = tk.Label(
            title_frame,
            text="●",
            font=('Segoe UI', 14),
            fg=status_color,
            bg=ROMER_GLASS_COLORS['glass_panel']
        )
        status_indicator.pack(side=tk.RIGHT)

        # Description
        desc_label = tk.Label(
            content,
            text=description,
            font=('Segoe UI', 9),
            fg=ROMER_GLASS_COLORS['text_secondary'],
            bg=ROMER_GLASS_COLORS['glass_panel']
        )
        desc_label.pack(anchor=tk.W, pady=(2, 5))

        # Health bar
        if status and status.health_score > 0:
            health_frame = tk.Frame(content, bg=ROMER_GLASS_COLORS['glass_bg'],
                                   height=6)
            health_frame.pack(fill=tk.X, pady=(0, 5))

            health_bar = tk.Frame(
                health_frame,
                bg=status_color,
                width=int(280 * status.health_score),
                height=6
            )
            health_bar.pack(side=tk.LEFT)

        # Quick actions
        actions_frame = tk.Frame(content, bg=ROMER_GLASS_COLORS['glass_panel'])
        actions_frame.pack(fill=tk.X)

        open_btn = tk.Button(
            actions_frame,
            text="Open Floor",
            font=('Segoe UI', 9),
            fg=ROMER_GLASS_COLORS['primary'],
            bg=ROMER_GLASS_COLORS['glass_bg'],
            relief=tk.FLAT,
            cursor='hand2',
            command=lambda: self._open_floor_portal(floor_id)
        )
        open_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Bind hover effects
        card.bind('<Enter>', lambda e: card.configure(
            bg=ROMER_GLASS_COLORS['accent_bg']
        ))
        card.bind('<Leave>', lambda e: card.configure(
            bg=ROMER_GLASS_COLORS['glass_panel']
        ))

    def _create_center_panel(self, parent) -> tk.Frame:
        """Create center panel with spherical UI"""
        panel = tk.Frame(parent, bg=ROMER_GLASS_COLORS['glass_bg'])

        # Spherical canvas
        self.spherical_ui = EnhancedSphericalGlassUI(
            panel,
            width=900,
            height=700,
            fov=self.config.fov
        )
        self.spherical_ui.canvas.pack(fill=tk.BOTH, expand=True)

        # Add Achilles Bubble if enabled
        if self.config.enable_achilles:
            center_x = 450
            center_y = 350
            self.achilles_bubble = AchillesBubble(
                self.spherical_ui.canvas,
                radius=80,
                center_x=center_x,
                center_y=center_y
            )

        # Add workspace portals to spherical layout
        self._populate_spherical_portals()

        return panel

    def _populate_spherical_portals(self):
        """Populate spherical UI with portal widgets"""
        # Portal positions in spherical coordinates (theta, phi, depth)
        portal_positions = [
            ("Project Workspace", 0, 0, 0.8, self._open_project_workspace),
            ("Universal Editor", 60, 0, 0.8, self._open_universal_editor),
            ("Data Objectifier", 120, 0, 0.8, self._open_objectifier),
            ("Trinity Tools", 180, 0, 0.8, self._open_trinity),
            ("Z-Floor Navigator", 240, 0, 0.8, self._open_navigator),
            ("System Health", 300, 0, 0.8, self._open_health),
        ]

        for label, theta, phi, depth, callback in portal_positions:
            widget_id = label.lower().replace(' ', '_')

            # Create glass button
            btn = tk.Button(
                self.spherical_ui.canvas,
                text=label,
                font=('Segoe UI', 11),
                fg=ROMER_GLASS_COLORS['text_primary'],
                bg=ROMER_GLASS_COLORS['glass_panel'],
                relief=tk.FLAT,
                padx=20,
                pady=10,
                cursor='hand2',
                command=callback
            )

            self.glass_ui.apply_glass_effect(
                btn,
                material=GLASS_MATERIALS['romer_premium']
            )

            # Add to spherical layout
            self.spherical_ui.add_widget(widget_id, btn, theta, phi, depth)

    def _create_right_panel(self, parent) -> tk.Frame:
        """Create right panel with system status"""
        panel = tk.Frame(parent, bg=ROMER_GLASS_COLORS['glass_bg'], width=320)

        # Panel header
        header = tk.Label(
            panel,
            text="SYSTEM STATUS",
            font=('Segoe UI', 14, 'bold'),
            fg=ROMER_GLASS_COLORS['primary'],
            bg=ROMER_GLASS_COLORS['glass_panel'],
            pady=10
        )
        header.pack(fill=tk.X)
        self.glass_ui.apply_glass_effect(header, material=GLASS_MATERIALS['romer_premium'])

        # Status container
        status_container = tk.Frame(panel, bg=ROMER_GLASS_COLORS['glass_bg'])
        status_container.pack(fill=tk.BOTH, expand=True, pady=10)

        # System metrics
        self._create_metric_card(status_container, "CPU Usage", "cpu_usage")
        self._create_metric_card(status_container, "Memory Usage", "memory_usage")
        self._create_metric_card(status_container, "Active Floors", "active_floors")
        self._create_metric_card(status_container, "Running Tools", "running_tools")

        # Recent activity
        activity_header = tk.Label(
            status_container,
            text="Recent Activity",
            font=('Segoe UI', 12, 'bold'),
            fg=ROMER_GLASS_COLORS['text_primary'],
            bg=ROMER_GLASS_COLORS['glass_bg'],
            pady=10
        )
        activity_header.pack(fill=tk.X, pady=(10, 5))

        # Activity log
        self.activity_log = tk.Text(
            status_container,
            height=12,
            font=('Consolas', 9),
            bg=ROMER_GLASS_COLORS['glass_panel'],
            fg=ROMER_GLASS_COLORS['text_primary'],
            relief=tk.FLAT,
            wrap=tk.WORD,
            state='disabled'
        )
        self.activity_log.pack(fill=tk.BOTH, expand=True, padx=5)
        self.glass_ui.apply_glass_effect(self.activity_log,
                                        material=GLASS_MATERIALS['standard'])

        self.metric_labels: Dict[str, tk.Label] = {}

        return panel

    def _create_metric_card(self, parent, title: str, metric_id: str):
        """Create system metric card"""
        card = tk.Frame(parent, bg=ROMER_GLASS_COLORS['glass_panel'])
        card.pack(fill=tk.X, padx=5, pady=5)

        self.glass_ui.apply_glass_effect(
            card,
            material=GLASS_MATERIALS['standard'],
            rounded_corners=8
        )

        content = tk.Frame(card, bg=ROMER_GLASS_COLORS['glass_panel'])
        content.pack(fill=tk.BOTH, padx=15, pady=10)

        title_label = tk.Label(
            content,
            text=title,
            font=('Segoe UI', 10),
            fg=ROMER_GLASS_COLORS['text_secondary'],
            bg=ROMER_GLASS_COLORS['glass_panel'],
            anchor=tk.W
        )
        title_label.pack(fill=tk.X)

        value_label = tk.Label(
            content,
            text="--",
            font=('Segoe UI', 18, 'bold'),
            fg=ROMER_GLASS_COLORS['primary'],
            bg=ROMER_GLASS_COLORS['glass_panel'],
            anchor=tk.W
        )
        value_label.pack(fill=tk.X)

        self.metric_labels[metric_id] = value_label

    def _create_footer(self, parent):
        """Create dashboard footer"""
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
            text="⚡ LightSpeed Holospace | Smart floors online",
            font=('Segoe UI', 10),
            fg=ROMER_GLASS_COLORS['text_primary'],
            bg=ROMER_GLASS_COLORS['glass_panel']
        )
        self.status_label.pack(side=tk.LEFT, padx=15)

        # Timestamp
        self.time_label = tk.Label(
            footer,
            text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            font=('Segoe UI', 10),
            fg=ROMER_GLASS_COLORS['text_secondary'],
            bg=ROMER_GLASS_COLORS['glass_panel']
        )
        self.time_label.pack(side=tk.RIGHT, padx=15)

    def _load_z_floor_status(self):
        """Load smart-floor status (mock data for V1.0.0)"""
        floors = [
            ("Z-4", "Merovingian", "online", 3, 0.95),
            ("Z-3", "Smith", "online", 5, 0.88),
            ("Z-2", "Oracle", "online", 4, 0.92),
            ("Z-1", "Morpheus", "online", 4, 0.87),
            ("Z0", "TheConstruct", "online", 8, 1.0),
            ("Z+1", "Architect", "online", 6, 0.90),
            ("Z+2", "Neo", "online", 7, 0.94),
            ("Z+3", "Trinity", "online", 6, 0.93),
        ]

        for floor_id, floor_name, status, tools, health in floors:
            self.z_floor_status[floor_id] = ZFloorStatus(
                floor_id=floor_id,
                floor_name=floor_name,
                status=status,
                active_tools=tools,
                health_score=health,
                last_activity=datetime.now()
            )

    def _start_monitoring(self):
        """Start system monitoring"""
        self._update_system_metrics()

    def _update_system_metrics(self):
        """Update system metrics display"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if 'cpu_usage' in self.metric_labels:
                self.metric_labels['cpu_usage'].config(
                    text=f"{cpu_percent:.1f}%"
                )

            # Memory usage
            memory = psutil.virtual_memory()
            if 'memory_usage' in self.metric_labels:
                self.metric_labels['memory_usage'].config(
                    text=f"{memory.percent:.1f}%"
                )

            # Active floors
            active_count = sum(1 for status in self.z_floor_status.values()
                             if status.status == 'online')
            if 'active_floors' in self.metric_labels:
                self.metric_labels['active_floors'].config(
                    text=f"{active_count}/9"
                )

            # Running tools
            total_tools = sum(status.active_tools for status in self.z_floor_status.values())
            if 'running_tools' in self.metric_labels:
                self.metric_labels['running_tools'].config(
                    text=str(total_tools)
                )

            # Update timestamp
            if hasattr(self, 'time_label'):
                self.time_label.config(
                    text=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )

        except Exception as e:
            print(f"Error updating metrics: {e}")

        # Schedule next update
        self.refresh_job = self.after(self.config.auto_refresh_interval,
                                      self._update_system_metrics)

    def _get_status_color(self, status: str) -> str:
        """Get color for status indicator"""
        colors = {
            'online': '#4ade80',
            'offline': '#94a3b8',
            'error': '#ef4444',
            'maintenance': '#f59e0b'
        }
        return colors.get(status, '#94a3b8')

    def _log_activity(self, message: str):
        """Log activity to activity log"""
        if not hasattr(self, 'activity_log'):
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.activity_log.config(state='normal')
        self.activity_log.insert('1.0', log_entry)
        self.activity_log.config(state='disabled')

    # Portal launch methods
    def _open_neo(self):
        """Open Neo / Achilles operator console"""
        try:
            # Floor folders like `Z+2_Neo` are not valid Python packages; load by file.
            from importlib.util import module_from_spec, spec_from_file_location

            z_axis_root = Path(__file__).resolve().parents[2]
            neo_file = (z_axis_root / "Z+2_Neo" / "components" / "neo_lab_assistant_glass.py").resolve()
            if not neo_file.exists():
                raise FileNotFoundError(str(neo_file))

            mod_name = f"lightspeed_dynamic_neo_lab_{abs(hash(str(neo_file)))%1_000_000}"
            spec = spec_from_file_location(mod_name, neo_file)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load Neo lab module from {neo_file}")
            mod = module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            NEOLabAssistant = getattr(mod, "NEOLabAssistant")

            if 'neo_assistant' not in self.active_portals:
                neo = NEOLabAssistant(self)
                self.active_portals['neo_assistant'] = neo
                self._log_activity("Opened Neo / Achilles Operator Console")
            else:
                self.active_portals['neo_assistant'].lift()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open NEO: {e}")

    def _open_floor_portal(self, floor_id: str):
        """Open specific Z-floor surface"""
        self._log_activity(f"Opening {floor_id} smart-floor surface...")
        messagebox.showinfo("Smart Floor",
                          f"{floor_id} workspace surface will open here.\n\n"
                          "Full floor integration is being aligned into the live Z-axis runtime.")

    def _open_project_workspace(self):
        """Open project workspace shell"""
        try:
            from Z0_TheConstruct.components.project_workspace_portal import ProjectWorkspacePortal  # type: ignore

            if 'workspace_portal' not in self.active_portals:
                portal = tk.Toplevel(self)
                portal.title("Project Workspace Shell")
                portal.geometry("1200x800")

                workspace_portal = ProjectWorkspacePortal(portal)
                workspace_portal.pack(fill=tk.BOTH, expand=True)

                self.active_portals['workspace_portal'] = portal
                self._log_activity("Opened Project Workspace Shell")
            else:
                self.active_portals['workspace_portal'].lift()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Project Workspace: {e}")

    def _open_universal_editor(self):
        """Open Universal Editor"""
        try:
            from core.universal_editor.universal_editor import UniversalEditor

            if 'universal_editor' not in self.active_portals:
                portal = tk.Toplevel(self)
                portal.title("Universal Editor")
                portal.geometry("1400x900")

                editor = UniversalEditor(portal)
                editor.pack(fill=tk.BOTH, expand=True)

                self.active_portals['universal_editor'] = portal
                self._log_activity("Opened Universal Editor")
            else:
                self.active_portals['universal_editor'].lift()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Universal Editor: {e}")

    def _open_objectifier(self):
        """Open Data Objectifier UI"""
        self._log_activity("Opening Data Objectifier...")
        try:
            from core.ui.data_objectifier_ui import DataObjectifierUI
            DataObjectifierUI(parent=self)
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to open Data Objectifier:\n{str(e)}")

    def _open_trinity(self):
        """Open Trinity Tools"""
        self._log_activity("Opening Trinity Tools...")
        try:
            # Trinity owns `ui.*` and `components/*` under `Z Axis/Z+3_Trinity`.
            # Prefer direct path insertion to the Trinity floor root (not a relative guess).
            trinity_root = Path(__file__).resolve().parents[2] / "Z+3_Trinity"
            if str(trinity_root) not in sys.path:
                sys.path.insert(0, str(trinity_root))
            from components.trinity_portal_glass import TrinityPortalGlass
            TrinityPortalGlass(parent=self)
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to open Trinity Tools:\n{str(e)}")

    def _open_navigator(self):
        """Open Z-Floor Navigator"""
        self._log_activity("Opening Z-Floor Navigator...")
        try:
            from core.ui.zfloor_navigator_3d import ZFloorNavigator3D
            ZFloorNavigator3D(parent=self)
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to open Z-Floor Navigator:\n{str(e)}")

    def _open_health(self):
        """Open System Health Monitor"""
        self._log_activity("Opening System Health Monitor...")
        messagebox.showinfo("System Health",
                          "Detailed health monitor available from Z-4 Merovingian.")

    def cleanup(self):
        """Cleanup before closing"""
        if self.refresh_job:
            self.after_cancel(self.refresh_job)

        for portal in self.active_portals.values():
            try:
                portal.destroy()
            except:
                pass


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Launch TheConstruct dashboard"""
    app = ConstructDashboardGlass()

    # Cleanup on close
    app.protocol("WM_DELETE_WINDOW", lambda: (app.cleanup(), app.destroy()))

    app.mainloop()


if __name__ == "__main__":
    main()
