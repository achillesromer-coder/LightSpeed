"""
Enhanced Spherical Glass UI - V2.0.0
120° FOV Equirectangular projection with Romer Industries Glass Theme

Enhancements over v1.0:
- Increased FOV from 70° to 120° for wider immersion
- Integrated glass UI effects (frosted, blur, transparency)
- Interactive 3D Achilles Bubble (centered, stays fixed while UI rotates)
- Smooth rounded edges, double-line borders
- Reflective light effects and depth-based glow
- Premium Romer Industries aesthetic
- Hardware-accelerated rendering where possible

Author: LightSpeed Team / Romer Industries
Date: December 27, 2025
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
import math

# Import glass UI framework
from .glass_ui import (
    GlassUIManager,
    GlassMaterial,
    GLASS_MATERIALS,
    ROMER_GLASS_COLORS,
    apply_romer_theme
)


# ==============================================================================
# 3D Widget with Glass Properties
# ==============================================================================

@dataclass
class GlassWidget3D:
    """
    Widget with 3D position and glass material properties

    Attributes:
        id: Unique identifier
        widget: Tkinter widget
        theta: Horizontal angle (0-360°)
        phi: Vertical angle (-90 to +90°)
        depth: Distance from center (0.0-1.0, closer = smaller depth value)
        material: Glass material for this widget
        glow_enabled: Whether widget has glow effect
        visible: Visibility flag
        interactive: Whether widget responds to mouse events
        scale: Size scale factor (affected by depth)
    """
    id: str
    widget: tk.Widget
    theta: float
    phi: float
    depth: float = 0.8
    material: Optional[GlassMaterial] = None
    glow_enabled: bool = False
    visible: bool = True
    interactive: bool = True
    scale: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ==============================================================================
# Interactive Achilles Bubble
# ==============================================================================

class AchillesBubble:
    """
    Interactive 3D Achilles Bubble - centered, stays fixed while environment rotates

    Design:
    - 3D sphere rendered on canvas
    - Stays centered in view regardless of camera pan/rotation
    - Interactive: click to expand, hover for info
    - Glows with Romer teal color
    - Shows status, notifications, quick actions
    - Access to NEO Lab Assistant
    """

    def __init__(
        self,
        canvas: tk.Canvas,
        radius: int = 80,
        color: str = ROMER_GLASS_COLORS['primary']
    ):
        """
        Initialize Achilles Bubble

        Args:
            canvas: Canvas to draw on
            radius: Bubble radius in pixels
            color: Primary bubble color
        """
        self.canvas = canvas
        self.radius = radius
        self.color = color
        self.expanded = False
        self.hover = False

        # Bubble state
        self.position = (0, 0)  # Will be centered
        self.pulse_phase = 0
        self.rotation = 0

        # Create bubble elements
        self.elements = {}
        self._create_bubble()

        # Bind interactions
        self._bind_interactions()

        # Start animation loop
        self._animate()

    def _create_bubble(self):
        """Create bubble visual elements"""
        # Calculate center
        width = self.canvas.winfo_width() or 800
        height = self.canvas.winfo_height() or 600
        cx, cy = width / 2, height / 2
        self.position = (cx, cy)

        # Outer glow ring (pulsing)
        self.elements['glow'] = self.canvas.create_oval(
            cx - self.radius - 20, cy - self.radius - 20,
            cx + self.radius + 20, cy + self.radius + 20,
            fill='',
            outline=self.color,
            width=3,
            tags='achilles_glow',
            stipple='gray25'
        )

        # Main bubble sphere (gradient effect simulated with concentric circles)
        for i in range(5, 0, -1):
            r = self.radius * (i / 5)
            alpha = int(255 * (i / 5))
            color_hex = f"{self.color}{alpha:02x}"

            self.canvas.create_oval(
                cx - r, cy - r,
                cx + r, cy + r,
                fill=color_hex,
                outline='',
                tags='achilles_sphere'
            )

        # Inner core (bright center)
        self.elements['core'] = self.canvas.create_oval(
            cx - 15, cy - 15,
            cx + 15, cy + 15,
            fill='#ffffff',
            outline='',
            tags='achilles_core'
        )

        # Rotating ring (orbital indicator)
        self.elements['ring'] = self._draw_orbital_ring(cx, cy, self.radius + 10)

        # Status indicators (3 small dots around bubble)
        self._create_status_indicators(cx, cy)

    def _draw_orbital_ring(self, cx: float, cy: float, radius: float) -> int:
        """Draw orbital ring around bubble"""
        points = []
        segments = 60

        for i in range(segments):
            angle = (i / segments) * 2 * math.pi
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)

            # Create dashed effect
            if i % 4 < 2:
                points.extend([x, y])

        if len(points) >= 4:
            return self.canvas.create_line(
                *points,
                fill=self.color,
                width=2,
                tags='achilles_ring'
            )
        return None

    def _create_status_indicators(self, cx: float, cy: float):
        """Create status indicator dots"""
        self.elements['indicators'] = []

        angles = [0, 120, 240]  # Three indicators at 120° apart
        indicator_radius = self.radius + 30

        for i, angle in enumerate(angles):
            rad = math.radians(angle)
            x = cx + indicator_radius * math.cos(rad)
            y = cy + indicator_radius * math.sin(rad)

            # Status colors: green (system), blue (ai), orange (tasks)
            colors = [
                ROMER_GLASS_COLORS['success'],
                ROMER_GLASS_COLORS['info'],
                ROMER_GLASS_COLORS['warning']
            ]

            indicator = self.canvas.create_oval(
                x - 6, y - 6,
                x + 6, y + 6,
                fill=colors[i],
                outline='#ffffff',
                width=2,
                tags=f'achilles_indicator_{i}'
            )

            self.elements['indicators'].append(indicator)

    def _bind_interactions(self):
        """Bind mouse interactions"""
        # Bind to all achilles elements
        self.canvas.tag_bind('achilles_sphere', '<Button-1>', self._on_click)
        self.canvas.tag_bind('achilles_sphere', '<Enter>', self._on_hover_enter)
        self.canvas.tag_bind('achilles_sphere', '<Leave>', self._on_hover_leave)

        self.canvas.tag_bind('achilles_core', '<Button-1>', self._on_click)
        self.canvas.tag_bind('achilles_core', '<Enter>', self._on_hover_enter)
        self.canvas.tag_bind('achilles_core', '<Leave>', self._on_hover_leave)

    def _on_click(self, event):
        """Handle bubble click - toggle expansion"""
        self.expanded = not self.expanded

        if self.expanded:
            self._expand_bubble()
        else:
            self._collapse_bubble()

    def _on_hover_enter(self, event):
        """Handle mouse hover enter"""
        self.hover = True

        # Brighten bubble
        self.canvas.itemconfig('achilles_glow', width=5)

    def _on_hover_leave(self, event):
        """Handle mouse hover leave"""
        self.hover = False

        # Restore normal glow
        self.canvas.itemconfig('achilles_glow', width=3)

    def _expand_bubble(self):
        """Expand bubble to show menu/options"""
        cx, cy = self.position

        # Create expanded menu (radial menu around bubble)
        menu_items = [
            ("NEO Assistant", self._open_neo),
            ("System Status", self._show_status),
            ("Quick Actions", self._show_actions),
            ("Settings", self._show_settings)
        ]

        self.elements['menu_items'] = []

        for i, (label, callback) in enumerate(menu_items):
            angle = (i / len(menu_items)) * 2 * math.pi - math.pi / 2
            distance = self.radius + 80

            x = cx + distance * math.cos(angle)
            y = cy + distance * math.sin(angle)

            # Menu button
            btn_id = self.canvas.create_oval(
                x - 30, y - 30,
                x + 30, y + 30,
                fill=ROMER_GLASS_COLORS['glass_panel'],
                outline=self.color,
                width=2,
                tags='achilles_menu_item'
            )

            # Label
            text_id = self.canvas.create_text(
                x, y,
                text=label.split()[0],  # First word only
                fill='#ffffff',
                font=('Segoe UI', 9, 'bold'),
                tags='achilles_menu_text'
            )

            self.elements['menu_items'].append((btn_id, text_id, callback))

            # Bind callback
            self.canvas.tag_bind(btn_id, '<Button-1>', lambda e, cb=callback: cb())

    def _collapse_bubble(self):
        """Collapse bubble menu"""
        # Remove menu items
        if 'menu_items' in self.elements:
            for btn_id, text_id, _ in self.elements['menu_items']:
                self.canvas.delete(btn_id)
                self.canvas.delete(text_id)

            del self.elements['menu_items']

    def _open_neo(self):
        """Open NEO Assistant"""
        try:
            import importlib.util
            from types import SimpleNamespace
            from pathlib import Path
            import tkinter as tk
            from tkinter import ttk, messagebox

            root = self.canvas.winfo_toplevel()
            dialog = tk.Toplevel(root)
            dialog.title("Neo Assistant (Z+2)")
            dialog.geometry("1100x750")

            container = ttk.Frame(dialog)
            container.pack(fill=tk.BOTH, expand=True)

            lightspeed_root = Path(__file__).resolve().parents[2]
            neo_path = lightspeed_root / "Z Axis" / "Neo.py"

            if not neo_path.exists():
                ttk.Label(
                    container,
                    text=f"Neo floor not found:\n{neo_path}",
                    justify="center"
                ).pack(expand=True)
                return

            spec = importlib.util.spec_from_file_location("lightspeed_zaxis_neo", str(neo_path))
            if not spec or not spec.loader:
                ttk.Label(container, text="Failed to load Neo module spec.").pack(expand=True)
                return

            neo_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(neo_mod)

            try:
                initialize = getattr(neo_mod, "initialize", None)
                if callable(initialize):
                    initialize(dependencies=None)
            except Exception:
                pass

            neo_ui_cls = getattr(neo_mod, "NeoUI", None)
            if not neo_ui_cls:
                ttk.Label(container, text="NeoUI class not found in Neo.py").pack(expand=True)
                return

            session = SimpleNamespace(company="default_company", project_id="default_workspace")
            app_stub = SimpleNamespace(
                session=session,
                user_mode="client",
                current_user={}
            )

            ui = neo_ui_cls(app_stub, container)
            if getattr(ui, "frame", None) is not None:
                ui.frame.pack(fill=tk.BOTH, expand=True)
            else:
                ttk.Label(container, text="NeoUI initialized without a frame.").pack(expand=True)

        except Exception as e:
            try:
                messagebox.showerror("Neo Assistant", f"Failed to open Neo Assistant:\n{e}")
            except Exception:
                print(f"[Neo Assistant] Failed: {e}")

    def _show_status(self):
        """Show system status"""
        print("Showing system status...")

    def _show_actions(self):
        """Show quick actions"""
        print("Showing quick actions...")

    def _show_settings(self):
        """Show settings"""
        print("Showing settings...")

    def _animate(self):
        """Animate bubble (pulsing glow, rotating ring)"""
        # Pulse glow
        self.pulse_phase += 0.05
        glow_radius = self.radius + 20 + 5 * math.sin(self.pulse_phase)

        cx, cy = self.position

        if 'glow' in self.elements:
            self.canvas.coords(
                self.elements['glow'],
                cx - glow_radius, cy - glow_radius,
                cx + glow_radius, cy + glow_radius
            )

        # Rotate ring
        self.rotation += 2
        if self.rotation >= 360:
            self.rotation = 0

        # Redraw ring
        if 'ring' in self.elements and self.elements['ring']:
            self.canvas.delete(self.elements['ring'])
            self.elements['ring'] = self._draw_orbital_ring(cx, cy, self.radius + 10)

        # Continue animation
        self.canvas.after(50, self._animate)


# ==============================================================================
# Enhanced Spherical Glass UI
# ==============================================================================

class EnhancedSphericalGlassUI:
    """
    Enhanced 120° FOV Spherical UI with Glass Effects and Achilles Bubble

    Features:
    - 120° FOV (upgrade from 70°)
    - Glass UI integration
    - Interactive Achilles Bubble (center-fixed)
    - Smooth camera pan/tilt/zoom
    - Depth-based widget scaling
    - Glow effects for widgets
    - Double-line borders
    - Reflective surfaces
    """

    def __init__(
        self,
        parent: tk.Widget,
        width: int = 1920,
        height: int = 1080,
        fov: float = 120.0,
        grid_width: int = 12,
        grid_height: int = 8
    ):
        """
        Initialize Enhanced Spherical Glass UI

        Args:
            parent: Parent widget
            width: Canvas width
            height: Canvas height
            fov: Field of view in degrees (120° recommended)
            grid_width: Number of horizontal grid sections
            grid_height: Number of vertical grid sections
        """
        self.parent = parent
        self.width = width
        self.height = height
        self.fov = fov
        self.grid_width = grid_width
        self.grid_height = grid_height

        # Camera properties
        self.camera_theta = 0.0  # Horizontal rotation
        self.camera_phi = 0.0    # Vertical rotation
        self.camera_zoom = 1.0

        # Widget registry
        self.widgets: Dict[str, GlassWidget3D] = {}

        # Glass UI manager
        self.glass_manager = GlassUIManager()

        # Create UI
        self._create_canvas()
        self._create_achilles_bubble()
        self._bind_controls()

        # Render loop
        self._render()

    def _create_canvas(self):
        """Create main canvas"""
        self.canvas = tk.Canvas(
            self.parent,
            width=self.width,
            height=self.height,
            bg=ROMER_GLASS_COLORS['glass_bg'],
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Draw grid
        self._draw_grid()

    def _create_achilles_bubble(self):
        """Create interactive Achilles Bubble"""
        self.achilles = AchillesBubble(
            self.canvas,
            radius=80,
            color=ROMER_GLASS_COLORS['primary']
        )

    def _draw_grid(self):
        """Draw spherical grid overlay"""
        # Draw horizontal grid lines (latitude)
        for i in range(self.grid_height + 1):
            phi = -90 + (180 / self.grid_height) * i
            points = []

            for j in range(self.grid_width * 4):
                theta = (360 / (self.grid_width * 4)) * j
                x, y, visible = self._project_3d_to_2d(theta, phi, 0.95)

                if visible:
                    points.extend([x, y])

            if len(points) >= 4:
                self.canvas.create_line(
                    *points,
                    fill=ROMER_GLASS_COLORS['border_light'],
                    width=1,
                    tags='grid',
                    dash=(4, 4)
                )

        # Draw vertical grid lines (longitude)
        for i in range(self.grid_width):
            theta = (360 / self.grid_width) * i
            points = []

            for j in range(self.grid_height * 4):
                phi = -90 + (180 / (self.grid_height * 4)) * j
                x, y, visible = self._project_3d_to_2d(theta, phi, 0.95)

                if visible:
                    points.extend([x, y])

            if len(points) >= 4:
                self.canvas.create_line(
                    *points,
                    fill=ROMER_GLASS_COLORS['border_light'],
                    width=1,
                    tags='grid',
                    dash=(4, 4)
                )

    def _project_3d_to_2d(
        self,
        theta: float,
        phi: float,
        depth: float
    ) -> Tuple[float, float, bool]:
        """
        Project 3D spherical coordinates to 2D canvas with 120° FOV

        Args:
            theta: Horizontal angle (0-360°)
            phi: Vertical angle (-90 to +90°)
            depth: Distance from center (0.0-1.0)

        Returns:
            Tuple of (x, y, visible)
        """
        # Adjust for camera rotation
        adjusted_theta = theta - self.camera_theta
        adjusted_phi = phi - self.camera_phi

        # Normalize angles
        while adjusted_theta < 0:
            adjusted_theta += 360
        while adjusted_theta >= 360:
            adjusted_theta -= 360

        # Check if within FOV
        fov_half = self.fov / 2

        # Horizontal FOV check
        if adjusted_theta > fov_half and adjusted_theta < 360 - fov_half:
            return (0, 0, False)

        # Convert to radians
        theta_rad = math.radians(adjusted_theta)
        phi_rad = math.radians(adjusted_phi)

        # Spherical to Cartesian
        x_3d = depth * math.cos(phi_rad) * math.sin(theta_rad)
        y_3d = depth * math.sin(phi_rad)
        z_3d = depth * math.cos(phi_rad) * math.cos(theta_rad)

        # Perspective projection
        if z_3d <= 0.1:  # Behind camera
            return (0, 0, False)

        # Project to 2D
        scale = 1.0 / z_3d * self.camera_zoom
        x_2d = x_3d * scale * self.width / 2 + self.width / 2
        y_2d = -y_3d * scale * self.height / 2 + self.height / 2

        # Check if on screen
        margin = 100
        visible = (
            -margin < x_2d < self.width + margin and
            -margin < y_2d < self.height + margin
        )

        return (x_2d, y_2d, visible)

    def _bind_controls(self):
        """Bind camera controls"""
        # Mouse drag to rotate
        self.canvas.bind('<B1-Motion>', self._on_drag)

        # Mouse wheel to zoom
        self.canvas.bind('<MouseWheel>', self._on_scroll)

        # Keyboard controls
        self.canvas.bind('<Left>', lambda e: self.rotate_camera(-10, 0))
        self.canvas.bind('<Right>', lambda e: self.rotate_camera(10, 0))
        self.canvas.bind('<Up>', lambda e: self.rotate_camera(0, 10))
        self.canvas.bind('<Down>', lambda e: self.rotate_camera(0, -10))

        self.canvas.focus_set()

    def _on_drag(self, event):
        """Handle mouse drag"""
        if hasattr(self, '_last_x'):
            dx = event.x - self._last_x
            dy = event.y - self._last_y

            self.rotate_camera(dx * 0.5, -dy * 0.5)

        self._last_x = event.x
        self._last_y = event.y

    def _on_scroll(self, event):
        """Handle mouse scroll (zoom)"""
        if event.delta > 0:
            self.camera_zoom *= 1.1
        else:
            self.camera_zoom *= 0.9

        self.camera_zoom = max(0.5, min(self.camera_zoom, 3.0))

    def rotate_camera(self, d_theta: float, d_phi: float):
        """Rotate camera"""
        self.camera_theta += d_theta
        self.camera_phi += d_phi

        # Clamp phi
        self.camera_phi = max(-80, min(self.camera_phi, 80))

        # Normalize theta
        while self.camera_theta < 0:
            self.camera_theta += 360
        while self.camera_theta >= 360:
            self.camera_theta -= 360

    def add_widget(
        self,
        widget_id: str,
        widget: tk.Widget,
        theta: float,
        phi: float,
        depth: float = 0.8,
        material: Optional[GlassMaterial] = None,
        glow: bool = False
    ):
        """Add widget to spherical space"""
        glass_widget = GlassWidget3D(
            id=widget_id,
            widget=widget,
            theta=theta,
            phi=phi,
            depth=depth,
            material=material or GLASS_MATERIALS['romer_premium'],
            glow_enabled=glow
        )

        self.widgets[widget_id] = glass_widget

        # Apply glass effect
        self.glass_manager.apply_glass_effect(widget, glass_widget.material)

    def _render(self):
        """Render all widgets"""
        # Update widget positions
        for widget_3d in self.widgets.values():
            if not widget_3d.visible:
                continue

            x, y, visible = self._project_3d_to_2d(
                widget_3d.theta,
                widget_3d.phi,
                widget_3d.depth
            )

            if visible:
                # Scale based on depth (closer = larger)
                scale = (1.0 - widget_3d.depth * 0.5) * self.camera_zoom
                widget_3d.scale = scale

                # Position widget (if it's a Canvas item)
                # For tk.Widget, use place()
                widget_3d.widget.place(x=int(x), y=int(y), anchor='center')

        # Continue render loop
        self.canvas.after(16, self._render)  # ~60 FPS


# ==============================================================================
# Factory Function
# ==============================================================================

def create_enhanced_spherical_glass_ui(
    parent: tk.Widget,
    **kwargs
) -> EnhancedSphericalGlassUI:
    """
    Create Enhanced Spherical Glass UI

    Args:
        parent: Parent widget
        **kwargs: Additional configuration

    Returns:
        Configured EnhancedSphericalGlassUI instance
    """
    return EnhancedSphericalGlassUI(parent, **kwargs)


# ==============================================================================
# Standalone Test
# ==============================================================================

if __name__ == '__main__':
    root = tk.Tk()
    root.title("Enhanced Spherical Glass UI - Romer Industries")
    root.geometry("1920x1080")

    # Apply Romer theme
    apply_romer_theme(root)

    # Create spherical UI
    spherical_ui = create_enhanced_spherical_glass_ui(
        root,
        width=1920,
        height=1080,
        fov=120.0
    )

    # Add some test widgets
    from .glass_ui import GlassButton

    for i in range(8):
        theta = (360 / 8) * i
        btn = GlassButton(
            spherical_ui.canvas,
            text=f"Action {i+1}"
        )

        spherical_ui.add_widget(
            f"btn_{i}",
            btn,
            theta=theta,
            phi=0,
            depth=0.7,
            glow=True
        )

    root.mainloop()
