"""
Z-Floor Navigator 3D - V1.0.0
Interactive 3D visualization and navigation for all 8 Z-floor portals

Features:
- 3D spherical layout of Z-floors (Z-4 through Z+3)
- Interactive rotation and navigation
- Floor information cards with quick launch
- Glass-themed interface matching portal designs
- Smooth animations and transitions

Author: LightSpeed Team
Date: December 28, 2025
"""

import importlib.util
import math
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Type

from core.ui.glass_ui import ROMER_GLASS_COLORS


# Z-Floor configuration
ZFLOOR_CONFIG = {
    'z-4': {
        'name': 'Merovingian',
        'role': 'System Health & Monitoring',
        'color': '#ef4444',
        'icon': 'ðŸ¥',
        'position': -4,
        'source_file': 'Z Axis/Z-4_Merovingian/components/merovingian_portal_glass.py',
        'class': 'MerovingianPortalGlass',
    },
    'z-3': {
        'name': 'Smith',
        'role': 'Framework Management',
        'color': '#f59e0b',
        'icon': 'ðŸ¤–',
        'position': -3,
        'source_file': 'Z Axis/Z-3_Smith/components/smith_portal_glass.py',
        'class': 'SmithPortalGlass',
    },
    'z-2': {
        'name': 'Oracle',
        'role': 'Data Intelligence',
        'color': '#8b5cf6',
        'icon': 'ðŸ“š',
        'position': -2,
        'source_file': 'Z Axis/Z-2_Oracle/components/oracle_portal_glass.py',
        'class': 'OraclePortalGlass',
    },
    'z-1': {
        'name': 'Morpheus',
        'role': 'Knowledge & Editing',
        'color': '#06b6d4',
        'icon': 'ðŸ§ ',
        'position': -1,
        'source_file': 'Z Axis/Z-1_Morpheus/components/morpheus_portal_glass.py',
        'class': 'MorpheusPortalGlass',
    },
    'z0': {
        'name': 'TheConstruct',
        'role': 'Command Center',
        'color': '#4dd0e1',
        'icon': 'ðŸŒ',
        'position': 0,
        'source_file': 'Z Axis/Z0_TheConstruct/components/construct_dashboard_glass.py',
        'class': 'ConstructDashboardGlass',
    },
    'z+1': {
        'name': 'Architect',
        'role': 'Planning & Project Structure',
        'color': '#DAA520',
        'icon': 'ðŸ“',
        'position': 1,
        'source_file': 'Z Axis/Z+1_Architect/components/architect_portal_glass.py',
        'class': 'ArchitectPortalGlass',
    },
    'z+2': {
        'name': 'Neo',
        'role': 'AI Lab Assistant',
        'color': '#4dd0e1',
        'icon': 'ðŸ¤–',
        'position': 2,
        'source_file': 'Z Axis/Z+2_Neo/components/neo_lab_assistant_glass.py',
        'class': 'NEOLabAssistant',
    },
    'z+3': {
        'name': 'Trinity',
        'role': 'UI, Tools & Control Center',
        'color': '#00e5ff',
        'icon': 'ðŸŽ¨',
        'position': 3,
        'source_file': 'Z Axis/Z+3_Trinity/components/trinity_portal_glass.py',
        'class': 'TrinityPortalGlass',
    }
}


def _find_lightspeed_root() -> Path:
    here = Path(__file__).resolve()
    for cand in (here, *here.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return here.parents[3]


LIGHTSPEED_ROOT = _find_lightspeed_root()


def _load_class_from_file(source_file: str, class_name: str) -> Type[Any]:
    file_path = (LIGHTSPEED_ROOT / source_file).resolve()
    module_name = f"lightspeed_dynamic_{file_path.stem}_{abs(hash(str(file_path)))}"

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    try:
        return getattr(module, class_name)
    except AttributeError as e:
        raise ImportError(f"Class {class_name} not found in {file_path}") from e


class ZFloorNavigator3D:
    """
    3D Navigator for Z-Floor portals

    Displays all 9 floors in a vertical spherical arrangement
    with interactive navigation and information cards.
    """

    def __init__(self, parent: Optional[tk.Tk] = None):
        """Initialize Z-Floor Navigator"""
        if parent is None:
            self.root = tk.Tk()
            self.standalone = True
        else:
            self.root = tk.Toplevel(parent)
            self.standalone = False

        self.root.title("Z-Floor Navigator 3D - LightSpeed V0.9.5")
        self.root.geometry("1200x900")
        self.root.configure(bg='#1e1e1e')

        # Navigation state
        self.rotation_angle = 0.0  # Vertical rotation
        self.selected_floor = 'z0'  # Currently selected floor
        self.hover_floor = None  # Floor being hovered
        self.dragging = False
        self.drag_start_y = 0

        # Canvas dimensions
        self.canvas_width = 800
        self.canvas_height = 700
        self.center_x = self.canvas_width // 2
        self.center_y = self.canvas_height // 2
        self.sphere_radius = 250  # Radius of navigation sphere

        self._build_ui()
        self._draw_floors()

    def _build_ui(self):
        """Build main UI layout"""
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Header
        self._build_header(main_frame)

        # Content area (two columns)
        content_frame = tk.Frame(main_frame, bg='#1e1e1e')
        content_frame.pack(fill='both', expand=True, pady=10)

        # Left: 3D visualization
        self._build_visualization_panel(content_frame)

        # Right: Floor info card
        self._build_info_panel(content_frame)

        # Bottom: Controls
        self._build_controls(main_frame)

    def _build_header(self, parent):
        """Build header with title"""
        header_frame = tk.Frame(parent, bg=ROMER_GLASS_COLORS.get('glass_bg', '#1e1e1e'))
        header_frame.pack(fill='x', pady=(0, 10))

        title = tk.Label(
            header_frame,
            text="Z-Floor Navigator 3D",
            font=('Arial', 20, 'bold'),
            fg='#4dd0e1',
            bg=ROMER_GLASS_COLORS.get('glass_bg', '#1e1e1e')
        )
        title.pack(pady=5)

        subtitle = tk.Label(
            header_frame,
            text="Interactive navigation across all 9 Z-floor portals",
            font=('Arial', 10),
            fg='#a0a0a0',
            bg=ROMER_GLASS_COLORS.get('glass_bg', '#1e1e1e')
        )
        subtitle.pack(pady=(0, 5))

    def _build_visualization_panel(self, parent):
        """Build left panel with 3D visualization"""
        viz_frame = tk.Frame(parent, bg='#1e1e1e')
        viz_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Title
        tk.Label(
            viz_frame,
            text="3D Spherical View",
            font=('Arial', 12, 'bold'),
            fg='#4dd0e1',
            bg='#1e1e1e'
        ).pack(pady=10)

        # Canvas for 3D visualization
        self.canvas = tk.Canvas(
            viz_frame,
            width=self.canvas_width,
            height=self.canvas_height,
            bg='#1e1e1e',
            highlightthickness=0
        )
        self.canvas.pack(pady=10)

        # Mouse bindings for rotation
        self.canvas.bind('<Button-1>', self._on_mouse_down)
        self.canvas.bind('<B1-Motion>', self._on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_mouse_up)
        self.canvas.bind('<Motion>', self._on_mouse_move)
        self.canvas.bind('<Button-3>', self._on_floor_click)  # Right-click for info

        # Instructions
        instructions = (
            "Controls:\n"
            "- Drag vertically to rotate\n"
            "- Left-click floor bubble for info\n"
            "- Right-click floor bubble to launch\n"
            "- Use buttons below for quick access"
        )

        tk.Label(
            viz_frame,
            text=instructions,
            font=('Courier', 9),
            fg='#a0a0a0',
            bg='#1e1e1e',
            justify='left'
        ).pack(pady=10)

    def _build_info_panel(self, parent):
        """Build right panel with floor information"""
        info_frame = tk.Frame(parent, bg='#1e1e1e')
        info_frame.pack(side='right', fill='both', expand=False)
        info_frame.configure(width=350)

        # Dynamic content based on selected floor
        self.info_container = tk.Frame(info_frame, bg='#1e1e1e')
        self.info_container.pack(fill='both', expand=True, padx=10, pady=10)

        self._update_info_card()

    def _build_controls(self, parent):
        """Build bottom control panel"""
        controls_frame = tk.Frame(parent, bg='#1e1e1e')
        controls_frame.pack(fill='x', pady=(10, 0))

        # Quick navigation buttons
        btn_frame = tk.Frame(controls_frame, bg='#1e1e1e')
        btn_frame.pack(pady=10)

        tk.Label(
            btn_frame,
            text="Quick Navigate:",
            font=('Arial', 10, 'bold'),
            fg='#a0a0a0',
            bg='#1e1e1e'
        ).pack(side='left', padx=10)

        # Create button for each floor
        for floor_id in ['z-4', 'z-3', 'z-2', 'z-1', 'z0', 'z+1', 'z+2', 'z+3']:
            config = ZFLOOR_CONFIG[floor_id]
            btn = tk.Button(
                btn_frame,
                text=f"{config['icon']} {config['name']}",
                command=lambda fid=floor_id: self._navigate_to_floor(fid),
                bg=config['color'],
                fg='#ffffff',
                font=('Arial', 8, 'bold'),
                relief='flat',
                cursor='hand2',
                padx=5,
                pady=3
            )
            btn.pack(side='left', padx=2)

    # =========================================================================
    # 3D Visualization
    # =========================================================================

    def _draw_floors(self):
        """Draw all floors in 3D spherical arrangement"""
        self.canvas.delete('all')

        # Draw connection lines first (behind bubbles)
        self._draw_connections()

        # Draw floor bubbles
        floor_data = []

        for floor_id, config in ZFLOOR_CONFIG.items():
            # Calculate 3D position on sphere
            z_position = config['position']

            # Vertical position with rotation
            angle = (z_position * 40) + self.rotation_angle  # 40 degrees between floors
            angle_rad = math.radians(angle)

            # 3D to 2D projection (simple orthographic)
            y_3d = math.sin(angle_rad) * self.sphere_radius
            z_3d = math.cos(angle_rad) * self.sphere_radius

            # Screen coordinates
            x_screen = self.center_x
            y_screen = self.center_y - y_3d  # Invert Y for screen coords

            # Size based on Z-depth (perspective)
            depth_factor = (z_3d + self.sphere_radius) / (2 * self.sphere_radius)
            depth_factor = max(0.3, min(1.0, depth_factor))  # Clamp
            bubble_radius = int(40 * depth_factor)

            # Store for z-ordering
            floor_data.append((z_3d, floor_id, config, x_screen, y_screen, bubble_radius))

        # Sort by Z-depth (draw far to near)
        floor_data.sort(key=lambda x: x[0])

        # Draw bubbles
        self.floor_positions = {}
        for z_depth, floor_id, config, x, y, radius in floor_data:
            # Bubble color
            color = config['color']

            # Highlight selected or hovered floor
            outline_width = 1
            outline_color = '#666666'

            if floor_id == self.selected_floor:
                outline_width = 3
                outline_color = config['color']
            elif floor_id == self.hover_floor:
                outline_width = 2
                outline_color = '#ffffff'

            # Draw bubble
            bubble = self.canvas.create_oval(
                x - radius, y - radius,
                x + radius, y + radius,
                fill=color,
                outline=outline_color,
                width=outline_width,
                tags=(floor_id, 'bubble')
            )

            # Draw floor name (centered)
            text_color = '#ffffff' if z_depth > 0 else '#888888'
            self.canvas.create_text(
                x, y,
                text=config['icon'],
                font=('Arial', int(12 * (radius / 40)), 'bold'),
                fill=text_color,
                tags=(floor_id, 'text')
            )

            # Store position for click detection
            self.floor_positions[floor_id] = (x, y, radius)

        # Draw center axis line
        self.canvas.create_line(
            self.center_x, 50,
            self.center_x, self.canvas_height - 50,
            fill='#333333',
            width=2,
            dash=(5, 5)
        )

    def _draw_connections(self):
        """Draw connection lines between adjacent floors"""
        floor_ids = list(ZFLOOR_CONFIG.keys())

        for i in range(len(floor_ids) - 1):
            floor_id1 = floor_ids[i]
            floor_id2 = floor_ids[i + 1]

            config1 = ZFLOOR_CONFIG[floor_id1]
            config2 = ZFLOOR_CONFIG[floor_id2]

            # Calculate positions
            angle1 = (config1['position'] * 40) + self.rotation_angle
            angle2 = (config2['position'] * 40) + self.rotation_angle

            y1 = self.center_y - math.sin(math.radians(angle1)) * self.sphere_radius
            y2 = self.center_y - math.sin(math.radians(angle2)) * self.sphere_radius

            # Draw connection line
            self.canvas.create_line(
                self.center_x, y1,
                self.center_x, y2,
                fill='#444444',
                width=1,
                dash=(3, 3),
                tags='connection'
            )

    # =========================================================================
    # Mouse Interaction
    # =========================================================================

    def _on_mouse_down(self, event):
        """Handle mouse button press"""
        self.dragging = True
        self.drag_start_y = event.y

        # Check if clicked on a floor bubble
        clicked_floor = self._get_floor_at_position(event.x, event.y)
        if clicked_floor:
            self.selected_floor = clicked_floor
            self._update_info_card()
            self._draw_floors()

    def _on_mouse_drag(self, event):
        """Handle mouse drag for rotation"""
        if not self.dragging:
            return

        # Calculate rotation delta
        delta_y = event.y - self.drag_start_y
        self.rotation_angle += delta_y * 0.5  # Sensitivity factor

        self.drag_start_y = event.y

        # Redraw
        self._draw_floors()

    def _on_mouse_up(self, event):
        """Handle mouse button release"""
        self.dragging = False

    def _on_mouse_move(self, event):
        """Handle mouse movement for hover effects"""
        if self.dragging:
            return

        # Check hover
        hovered_floor = self._get_floor_at_position(event.x, event.y)

        if hovered_floor != self.hover_floor:
            self.hover_floor = hovered_floor
            self._draw_floors()

    def _on_floor_click(self, event):
        """Handle right-click to launch floor portal"""
        clicked_floor = self._get_floor_at_position(event.x, event.y)

        if clicked_floor:
            self._launch_floor(clicked_floor)

    def _get_floor_at_position(self, x: int, y: int) -> Optional[str]:
        """Get floor ID at given screen position"""
        for floor_id, (fx, fy, radius) in self.floor_positions.items():
            distance = math.sqrt((x - fx)**2 + (y - fy)**2)
            if distance <= radius:
                return floor_id
        return None

    # =========================================================================
    # Floor Navigation
    # =========================================================================

    def _navigate_to_floor(self, floor_id: str):
        """Navigate to specific floor"""
        self.selected_floor = floor_id

        # Animate rotation to center this floor
        config = ZFLOOR_CONFIG[floor_id]
        target_angle = -config['position'] * 40  # Negate to center

        # Smooth rotation (simple step)
        self.rotation_angle = target_angle

        self._update_info_card()
        self._draw_floors()

    def _update_info_card(self):
        """Update information card for selected floor"""
        # Clear existing
        for widget in self.info_container.winfo_children():
            widget.destroy()

        config = ZFLOOR_CONFIG[self.selected_floor]

        # Floor icon and name
        header_frame = tk.Frame(self.info_container, bg=config['color'])
        header_frame.pack(fill='x', pady=(0, 10))

        tk.Label(
            header_frame,
            text=f"{config['icon']} {config['name']}",
            font=('Arial', 18, 'bold'),
            fg='#ffffff',
            bg=config['color']
        ).pack(pady=10)

        # Floor position
        position_text = f"Level: {config['name']} ({self.selected_floor.upper()})"
        tk.Label(
            self.info_container,
            text=position_text,
            font=('Arial', 12, 'bold'),
            fg='#4dd0e1',
            bg='#1e1e1e'
        ).pack(anchor='w', pady=5)

        # Role
        tk.Label(
            self.info_container,
            text="Primary Role:",
            font=('Arial', 10, 'bold'),
            fg='#a0a0a0',
            bg='#1e1e1e'
        ).pack(anchor='w', pady=(10, 2))

        tk.Label(
            self.info_container,
            text=config['role'],
            font=('Arial', 11),
            fg='#ffffff',
            bg='#1e1e1e',
            wraplength=300,
            justify='left'
        ).pack(anchor='w', padx=10)

        # Description (floor-specific)
        descriptions = {
            'z-4': "Real-time system monitoring, health diagnostics, performance metrics, and resource tracking.",
            'z-3': "Framework orchestration, hook management, event bus coordination, and tool integration.",
            'z-2': "Data analysis engine with statistical methods, pattern recognition, and predictive modeling.",
            'z-1': "System architecture design, blueprint management, requirements tracking, and component planning.",
            'z0': "Central command center, project workspace management, and core tool coordination.",
            'z+1': "Development environment, integrated terminal, Git operations, and package management.",
            'z+2': "AI-powered lab assistant with natural language interface and code generation.",
            'z+3': "UI, tools, bento layout, themes, setup/login, and control center."
        }

        tk.Label(
            self.info_container,
            text="Description:",
            font=('Arial', 10, 'bold'),
            fg='#a0a0a0',
            bg='#1e1e1e'
        ).pack(anchor='w', pady=(15, 2))

        tk.Label(
            self.info_container,
            text=descriptions.get(self.selected_floor, "Z-floor portal"),
            font=('Arial', 9),
            fg='#cccccc',
            bg='#1e1e1e',
            wraplength=300,
            justify='left'
        ).pack(anchor='w', padx=10)

        # Launch button
        tk.Button(
            self.info_container,
            text=f"Launch {config['name']} Portal",
            command=lambda: self._launch_floor(self.selected_floor),
            bg=config['color'],
            fg='#ffffff',
            font=('Arial', 11, 'bold'),
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=10
        ).pack(pady=20)

        # Quick stats
        stats_frame = tk.Frame(self.info_container, bg='#2e2e2e')
        stats_frame.pack(fill='x', pady=10)

        stats = {
            'z-4': "Status: Operational\nServices: 4 active",
            'z-3': "Status: Operational\nHooks: 12 configured",
            'z-2': "Status: Operational\nMethods: 6 available",
            'z-1': "Status: Operational\nBlueprints: Ready",
            'z0': "Status: Operational\nTools: 7 integrated",
            'z+1': "Status: Operational\nEnvs: Available",
            'z+2': "Status: Operational\nModels: Ready",
            'z+3': "Status: Operational\nUI: Ready"
        }

        tk.Label(
            stats_frame,
            text=stats.get(self.selected_floor, "Status: Operational"),
            font=('Courier', 8),
            fg='#10b981',
            bg='#2e2e2e',
            justify='left'
        ).pack(pady=5, padx=10)

    def _launch_floor(self, floor_id: str):
        """Launch the selected floor portal"""
        config = ZFLOOR_CONFIG[floor_id]

        try:
            portal_class = _load_class_from_file(config['source_file'], config['class'])

            # Some portals are tk.Tk roots (e.g., ConstructDashboardGlass); most are tk.Toplevel.
            if isinstance(portal_class, type) and issubclass(portal_class, tk.Tk):
                app = portal_class()
                app.mainloop()
            else:
                try:
                    portal_class(self.root)
                except TypeError:
                    portal_class()

        except Exception as e:
            messagebox.showerror(
                f"Launch Error - {config['name']}",
                f"Failed to launch {config['name']} portal:\n\n{str(e)}"
            )

    # =========================================================================
    # Main Loop
    # =========================================================================

    def run(self):
        """Run navigator (standalone mode)"""
        if self.standalone:
            self.root.mainloop()


def launch_zfloor_navigator():
    """Launch standalone Z-Floor Navigator"""
    navigator = ZFloorNavigator3D()
    navigator.run()


if __name__ == "__main__":
    launch_zfloor_navigator()
