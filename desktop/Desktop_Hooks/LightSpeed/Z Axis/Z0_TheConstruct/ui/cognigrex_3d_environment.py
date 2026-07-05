#!/usr/bin/env python
"""
COGNIGREX 3D ENVIRONMENT V5.0.0
Stubbed 3D environment with fixed camera position
Uses venv as dynamic background host environment

This is the canonical 3D rendering system for Cognigrex.
Features:
- Fixed camera position (no FPS controls for now)
- Dynamic venv background with rolling hills
- Z-floor tower visualization
- Interactive floor portals
- Bento widget overlay system
- Full Z-stack integration

The environment serves as the host for all Z-floor visualizations
and provides the base "ground" level for navigation.

Author: LightSpeed Team
Version: 5.0.0
Date: 2026-01-25
"""

import tkinter as tk
from tkinter import Canvas
import math
import time
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import threading
import json
from pathlib import Path
import sys

# Tk does not support alpha in hex colors ("#RRGGBBAA") nor CSS rgba().
# Use canonical sanitizer when available.
try:
    from core.ui.glass_ui import tk_safe_color  # type: ignore
except Exception:
    def tk_safe_color(color, *, bg="#000000", fallback="#000000"):  # type: ignore
        return str(color) if color is not None else fallback


# ============================================================================
# PATH CONFIGURATION
# ============================================================================

def _find_lightspeed_root() -> Path:
    """Locate LightSpeed root by searching for N.py"""
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
            return candidate
    return here.parents[4]


LIGHTSPEED_ROOT = _find_lightspeed_root()
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"
CONFIG_ROOT = LIGHTSPEED_ROOT / "config"


# ============================================================================
# Z-FLOOR DEFINITIONS (Canonical)
# ============================================================================

class ZFloor(Enum):
    """Canonical Z-Axis floor enumeration"""
    Z_PLUS_3 = ("Z+3", "Trinity", "#FF1493", 30.0)
    Z_PLUS_2 = ("Z+2", "Neo", "#00FF00", 20.0)
    Z_PLUS_1 = ("Z+1", "Architect", "#DAA520", 10.0)
    Z_ZERO = ("Z0", "TheConstruct", "#808080", 0.0)
    Z_MINUS_1 = ("Z-1", "Morpheus", "#4B0082", -10.0)
    Z_MINUS_2 = ("Z-2", "Oracle", "#00008B", -20.0)
    Z_MINUS_3 = ("Z-3", "Smith", "#006400", -30.0)
    Z_MINUS_4 = ("Z-4", "Merovingian", "#8B0000", -40.0)

    @property
    def level(self) -> str:
        return self.value[0]

    @property
    def name(self) -> str:
        return self.value[1]

    @property
    def color(self) -> str:
        return self.value[2]

    @property
    def y_position(self) -> float:
        return self.value[3]


# Floor spacing in virtual meters
FLOOR_SPACING = 10.0
ACTIVE_FRAME_INTERVAL_MS = 33
PASSIVE_FRAME_INTERVAL_MS = 250
MAX_FRAME_INTERVAL_MS = 1000


# ============================================================================
# 3D PRIMITIVES
# ============================================================================

@dataclass
class Vector3:
    """3D point/vector"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def length(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalize(self) -> 'Vector3':
        l = self.length()
        if l == 0:
            return Vector3(0, 0, 0)
        return Vector3(self.x/l, self.y/l, self.z/l)


@dataclass
class FixedCamera:
    """Fixed position camera for stubbed 3D view"""
    position: Vector3 = field(default_factory=lambda: Vector3(0.0, 15.0, -50.0))
    target: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, 0.0))
    fov: float = 60.0
    near: float = 0.1
    far: float = 1000.0

    def look_at(self, target: Vector3):
        """Set camera to look at target"""
        self.target = target


# ============================================================================
# ENVIRONMENT BACKGROUND (VENV)
# ============================================================================

class VenvBackground:
    """
    Virtual environment background system
    Creates the dynamic rolling hills and sky backdrop
    """

    def __init__(self, canvas: Canvas):
        self.canvas = canvas
        self.width = 0
        self.height = 0
        self.time = 0.0
        self.hill_points: List[Tuple[float, float]] = []

        # Colors
        self.sky_top = "#000B1F"      # Deep space blue
        self.sky_bottom = "#1a1a2e"   # Dark purple
        self.hill_color = "#0d3320"   # Dark green
        self.hill_highlight = "#1a5c3a"  # Lighter green
        self.grid_color = tk_safe_color("#00DDFF20", bg=self.sky_top)  # Cyan with alpha (sanitized)

    def update_size(self, width: int, height: int):
        """Update canvas size"""
        self.width = width
        self.height = height
        self._generate_hills()

    def _generate_hills(self):
        """Generate rolling hills silhouette"""
        self.hill_points = []
        if self.width == 0:
            return

        # Generate 3 layers of hills
        for i in range(self.width + 10):
            x = i
            # Multiple sine waves for natural rolling effect
            y = (math.sin(i * 0.02 + self.time) * 30 +
                 math.sin(i * 0.01 + self.time * 0.5) * 50 +
                 math.sin(i * 0.005) * 20)
            self.hill_points.append((x, y))

    def render(self):
        """Render the background environment"""
        if self.width == 0 or self.height == 0:
            return

        # Clear canvas
        self.canvas.delete("venv_bg")

        # Draw gradient sky
        gradient_steps = 20
        for i in range(gradient_steps):
            ratio = i / gradient_steps
            # Interpolate colors
            y1 = int(self.height * 0.6 * ratio)
            y2 = int(self.height * 0.6 * (ratio + 1/gradient_steps))

            # Simple color interpolation
            self.canvas.create_rectangle(
                0, y1, self.width, y2,
                fill=self._lerp_color(self.sky_top, self.sky_bottom, ratio),
                outline="",
                tags="venv_bg"
            )

        # Draw ground plane
        ground_y = int(self.height * 0.6)
        self.canvas.create_rectangle(
            0, ground_y, self.width, self.height,
            fill="#0a1a0f",
            outline="",
            tags="venv_bg"
        )

        # Draw rolling hills (3 layers for depth)
        self._draw_hill_layer(0.7, self.hill_color, 0.5)
        self._draw_hill_layer(0.65, self.hill_highlight, 0.3)
        self._draw_hill_layer(0.6, "#2a8c5a", 0.15)

        # Draw grid lines on ground (perspective)
        self._draw_perspective_grid(ground_y)

    def _draw_hill_layer(self, y_ratio: float, color: str, amplitude: float):
        """Draw a single hill layer"""
        base_y = int(self.height * y_ratio)
        points = []

        for i in range(0, self.width + 10, 5):
            x = i
            y = base_y + int(
                (math.sin(i * 0.02 + self.time * amplitude) * 30 +
                 math.sin(i * 0.01 + self.time * 0.5 * amplitude) * 50) * amplitude
            )
            points.extend([x, y])

        # Close polygon at bottom
        points.extend([self.width, self.height, 0, self.height])

        if len(points) >= 6:
            self.canvas.create_polygon(
                points,
                fill=color,
                outline="",
                tags="venv_bg"
            )

    def _draw_perspective_grid(self, ground_y: int):
        """Draw perspective grid on ground plane"""
        horizon_y = ground_y
        bottom_y = self.height
        center_x = self.width // 2

        # Vertical lines (converging to horizon)
        for i in range(-10, 11, 2):
            x_offset = i * 100
            x_bottom = center_x + x_offset
            x_top = center_x + int(x_offset * 0.1)

            self.canvas.create_line(
                x_bottom, bottom_y,
                x_top, horizon_y,
                fill=self.grid_color,
                tags="venv_bg"
            )

        # Horizontal lines (with perspective spacing)
        for i in range(1, 10):
            ratio = 1 - (1 / (i * 0.5 + 1))
            y = horizon_y + int((bottom_y - horizon_y) * ratio)

            self.canvas.create_line(
                0, y, self.width, y,
                fill=self.grid_color,
                tags="venv_bg"
            )

    def _lerp_color(self, c1: str, c2: str, t: float) -> str:
        """Linear interpolate between two hex colors"""
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)

        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)

        return f"#{r:02x}{g:02x}{b:02x}"

    def update(self, dt: float):
        """Update animation state"""
        self.time += dt * 0.5  # Slow animation


# ============================================================================
# Z-TOWER VISUALIZATION
# ============================================================================

class ZTower:
    """
    Z-Axis tower visualization
    Shows all 9 floors as a vertical stack
    """

    def __init__(self, canvas: Canvas, camera: FixedCamera):
        self.canvas = canvas
        self.camera = camera
        self.floors: List[Dict] = []
        self.selected_floor: Optional[ZFloor] = None
        self.on_floor_select: Optional[Callable[[ZFloor], None]] = None

        # Tower dimensions
        self.tower_width = 200
        self.tower_height = 400
        self.floor_height = 40

        self._build_floors()

    def _build_floors(self):
        """Build floor data for all Z-levels"""
        self.floors = []
        for floor in ZFloor:
            self.floors.append({
                'enum': floor,
                'level': floor.level,
                'name': floor.name,
                'color': floor.color,
                'y_pos': floor.y_position
            })

    def render(self, center_x: int, base_y: int):
        """Render the Z-tower at specified position"""
        self.canvas.delete("z_tower")

        # Sort floors by y_position (bottom to top)
        sorted_floors = sorted(self.floors, key=lambda f: f['y_pos'])

        # Draw tower structure
        tower_left = center_x - self.tower_width // 2
        tower_right = center_x + self.tower_width // 2

        for i, floor in enumerate(sorted_floors):
            floor_top = base_y - (i + 1) * self.floor_height
            floor_bottom = base_y - i * self.floor_height

            # Floor panel
            is_selected = self.selected_floor == floor['enum']
            fill_color = floor['color'] if is_selected else self._darken(floor['color'], 0.5)

            # Draw 3D-ish floor panel
            self.canvas.create_polygon(
                tower_left, floor_bottom,
                tower_left + 20, floor_top + 5,
                tower_right - 20, floor_top + 5,
                tower_right, floor_bottom,
                fill=fill_color,
                outline=floor['color'],
                width=2,
                tags=("z_tower", f"floor_{floor['level']}")
            )

            # Floor label
            self.canvas.create_text(
                center_x,
                (floor_top + floor_bottom) // 2,
                text=f"{floor['level']} {floor['name']}",
                fill="#FFFFFF" if is_selected else "#AAAAAA",
                font=('Segoe UI', 10, 'bold' if is_selected else 'normal'),
                tags=("z_tower", f"floor_label_{floor['level']}")
            )

            # Bind click events
            self.canvas.tag_bind(
                f"floor_{floor['level']}",
                '<Button-1>',
                lambda e, f=floor['enum']: self._on_floor_click(f)
            )
            self.canvas.tag_bind(
                f"floor_label_{floor['level']}",
                '<Button-1>',
                lambda e, f=floor['enum']: self._on_floor_click(f)
            )

        # Tower title
        self.canvas.create_text(
            center_x, base_y - len(sorted_floors) * self.floor_height - 20,
            text="Z-AXIS TOWER",
            fill="#00DDFF",
            font=('Segoe UI', 14, 'bold'),
            tags="z_tower"
        )

    def _on_floor_click(self, floor: ZFloor):
        """Handle floor click"""
        self.selected_floor = floor
        if self.on_floor_select:
            self.on_floor_select(floor)

    def _darken(self, color: str, factor: float) -> str:
        """Darken a hex color"""
        r = int(int(color[1:3], 16) * factor)
        g = int(int(color[3:5], 16) * factor)
        b = int(int(color[5:7], 16) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"


# ============================================================================
# WIDGET OVERLAY SYSTEM
# ============================================================================

class WidgetOverlay:
    """
    Bento widget overlay system
    Displays interactive widgets in 3D space
    """

    def __init__(self, canvas: Canvas):
        self.canvas = canvas
        self.widgets: List[Dict] = []
        self.visible = True

        # Default widgets
        self._create_default_widgets()

    def _create_default_widgets(self):
        """Create default widget set"""
        self.widgets = [
            {
                'id': 'status_monitor',
                'name': 'System Status',
                'x': 50, 'y': 50,
                'width': 200, 'height': 120,
                'color': '#00DDFF',
                'content': 'All Systems Operational'
            },
            {
                'id': 'floor_navigator',
                'name': 'Floor Navigator',
                'x': 50, 'y': 190,
                'width': 200, 'height': 100,
                'color': '#FF1493',
                'content': 'Click Z-Tower to navigate'
            },
            {
                'id': 'quick_actions',
                'name': 'Quick Actions',
                'x': 50, 'y': 310,
                'width': 200, 'height': 80,
                'color': '#00FF88',
                'content': 'Settings | Dashboard | Help'
            }
        ]

    def render(self):
        """Render all widgets"""
        if not self.visible:
            return

        self.canvas.delete("widget_overlay")

        for widget in self.widgets:
            self._render_widget(widget)

    def _render_widget(self, widget: Dict):
        """Render a single widget"""
        x, y = widget['x'], widget['y']
        w, h = widget['width'], widget['height']

        # Glass panel background
        self.canvas.create_rectangle(
            x, y, x + w, y + h,
            fill=tk_safe_color('#1a1a2eCC', bg="#000B1F"),
            outline=widget['color'],
            width=2,
            tags="widget_overlay"
        )

        # Widget title bar
        self.canvas.create_rectangle(
            x, y, x + w, y + 25,
            fill=tk_safe_color(str(widget['color']) + '40', bg="#000B1F"),
            outline="",
            tags="widget_overlay"
        )

        # Widget name
        self.canvas.create_text(
            x + 10, y + 12,
            text=widget['name'],
            fill=widget['color'],
            font=('Segoe UI', 10, 'bold'),
            anchor='w',
            tags="widget_overlay"
        )

        # Widget content
        self.canvas.create_text(
            x + w // 2, y + h // 2 + 10,
            text=widget['content'],
            fill='#FFFFFF',
            font=('Segoe UI', 9),
            tags="widget_overlay"
        )

    def toggle(self):
        """Toggle widget visibility"""
        self.visible = not self.visible


# ============================================================================
# MAIN 3D ENVIRONMENT CLASS
# ============================================================================

class Cognigrex3DEnvironment:
    """
    Main Cognigrex 3D Environment
    Stubbed implementation with fixed camera
    """

    def __init__(
        self,
        parent: tk.Widget,
        canvas: Optional[Canvas] = None,
        on_floor_select: Optional[Callable[[ZFloor], None]] = None,
        *,
        frame_interval_ms: int = PASSIVE_FRAME_INTERVAL_MS,
    ):
        self.parent = parent
        self.on_floor_select = on_floor_select
        self.frame_interval_ms = max(
            ACTIVE_FRAME_INTERVAL_MS,
            min(int(frame_interval_ms), MAX_FRAME_INTERVAL_MS),
        )

        # Create or use canvas
        if canvas is None:
            self.canvas = Canvas(parent, bg='#000000', highlightthickness=0)
            self.canvas.pack(fill='both', expand=True)
            self.owns_canvas = True
        else:
            self.canvas = canvas
            self.owns_canvas = False

        # Fixed camera
        self.camera = FixedCamera()

        # Environment components
        self.background = VenvBackground(self.canvas)
        self.z_tower = ZTower(self.canvas, self.camera)
        self.widgets = WidgetOverlay(self.canvas)

        # Connect floor selection
        self.z_tower.on_floor_select = self._handle_floor_select

        # Animation state
        self.running = True
        self.last_time = time.time()

        # Bind events
        self.canvas.bind('<Configure>', self._on_resize)
        self.canvas.bind('<KeyPress-w>', lambda e: self.widgets.toggle())

        # Start render loop
        self._render_loop()

    def _on_resize(self, event):
        """Handle canvas resize"""
        self.background.update_size(event.width, event.height)

    def _handle_floor_select(self, floor: ZFloor):
        """Handle floor selection from Z-tower"""
        print(f"[3D] Selected floor: {floor.level} {floor.name}")
        if self.on_floor_select:
            self.on_floor_select(floor)

    def _render_loop(self):
        """Main render loop"""
        if not self.running:
            return

        try:
            current_time = time.time()
            dt = current_time - self.last_time
            self.last_time = current_time

            # Update animation
            self.background.update(dt)

            # Render everything
            self._render()

            self.parent.after(self.frame_interval_ms, self._render_loop)

        except tk.TclError:
            # Window closed
            self.running = False

    def _render(self):
        """Render complete frame"""
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width <= 1 or height <= 1:
            return

        # Render layers (back to front)
        self.background.render()
        self.z_tower.render(width - 150, height - 50)
        self.widgets.render()

        # Optional dim overlay for UI-first host shells (e.g., N lobby Bento panel).
        # Tkinter doesn't support alpha, but stipple gives a convincing dimming effect.
        try:
            self.canvas.delete("dim_overlay")
            dim = float(getattr(self.canvas, "_lightspeed_dim", 0.0) or 0.0)
            if dim > 0.05:
                if dim >= 0.6:
                    stipple = "gray75"
                elif dim >= 0.35:
                    stipple = "gray50"
                elif dim >= 0.2:
                    stipple = "gray25"
                else:
                    stipple = "gray12"
                self.canvas.create_rectangle(
                    0,
                    0,
                    width,
                    height,
                    fill="#000000",
                    outline="",
                    stipple=stipple,
                    tags="dim_overlay",
                )
        except Exception:
            pass

        # Render HUD
        self._render_hud(width, height)

    def _render_hud(self, width: int, height: int):
        """Render heads-up display"""
        self.canvas.delete("hud")

        # Title
        self.canvas.create_text(
            width // 2, 30,
            text="COGNIGREX 3D ENVIRONMENT",
            fill="#00DDFF",
            font=('Segoe UI', 18, 'bold'),
            tags="hud"
        )

        # Subtitle
        self.canvas.create_text(
            width // 2, 55,
            text="Fixed Camera Mode | Press W to toggle widgets | Click Z-Tower to navigate",
            fill="#888888",
            font=('Segoe UI', 10),
            tags="hud"
        )

        # Floor info (bottom left)
        if self.z_tower.selected_floor:
            floor = self.z_tower.selected_floor
            self.canvas.create_text(
                20, height - 30,
                text=f"Selected: {floor.level} {floor.name}",
                fill=floor.color,
                font=('Segoe UI', 12, 'bold'),
                anchor='w',
                tags="hud"
            )

    def stop(self):
        """Stop the environment"""
        self.running = False

    def set_floor(self, floor: ZFloor):
        """Set the selected floor"""
        self.z_tower.selected_floor = floor


# ============================================================================
# LAUNCH FUNCTIONS
# ============================================================================

def launch_cognigrex_3d(parent: Optional[tk.Tk] = None,
                        on_floor_select: Optional[Callable] = None) -> Cognigrex3DEnvironment:
    """Launch standalone Cognigrex 3D environment"""
    if parent is None:
        root = tk.Tk()
        root.title("Cognigrex 3D Environment - LightSpeed V5.0")
        root.geometry("1400x900")
        root.configure(bg='#000000')

        env = Cognigrex3DEnvironment(
            root,
            on_floor_select=on_floor_select,
            frame_interval_ms=ACTIVE_FRAME_INTERVAL_MS,
        )

        def on_close():
            env.stop()
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_close)
        root.mainloop()
        return env
    else:
        return Cognigrex3DEnvironment(
            parent,
            on_floor_select=on_floor_select,
            frame_interval_ms=ACTIVE_FRAME_INTERVAL_MS,
        )


def attach_cognigrex_3d(parent: tk.Widget, canvas: Canvas,
                        on_floor_select: Optional[Callable] = None) -> Cognigrex3DEnvironment:
    """Attach Cognigrex 3D environment to existing canvas"""
    return Cognigrex3DEnvironment(
        parent,
        canvas,
        on_floor_select=on_floor_select,
        frame_interval_ms=PASSIVE_FRAME_INTERVAL_MS,
    )


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    def on_floor_selected(floor: ZFloor):
        print(f"Floor selected: {floor.level} - {floor.name} (Color: {floor.color})")

    launch_cognigrex_3d(on_floor_select=on_floor_selected)
