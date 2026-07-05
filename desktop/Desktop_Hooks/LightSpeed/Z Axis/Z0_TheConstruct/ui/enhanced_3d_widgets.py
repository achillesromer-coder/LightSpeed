"""
ENHANCED 3D WIDGETS SYSTEM
All floor widgets and UI elements as interactive 3D objects in the immersive environment

This allows every function, simulation, widget to exist as a physical object you can
walk up to and interact with in the 3D space.
"""

import tkinter as tk
from tkinter import Canvas
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
import math

from core.ui.immersive_3d_engine import Interactive3DObject, Vector3D, FloorType, Camera


class Widget3D:
    """Base class for 3D widgets that exist in space"""

    def __init__(
        self,
        id: str,
        name: str,
        position: Vector3D,
        size: Tuple[float, float, float],
        floor: FloorType
    ):
        self.id = id
        self.name = name
        self.position = position
        self.size = size
        self.floor = floor
        self.is_active = False
        self.content_canvas: Optional[tk.Canvas] = None

    def render_content(self, canvas: tk.Canvas, width: int, height: int):
        """Override to render widget-specific content"""
        pass

    def on_interact(self):
        """Called when user interacts with widget"""
        self.is_active = not self.is_active
        print(f"[Widget3D] Toggled {self.name}: {'Active' if self.is_active else 'Inactive'}")


class PhysicsSimulation3D(Widget3D):
    """
    3D widget for physics simulations - they render TO a texture
    that is displayed on a 3D panel in the environment
    """

    def __init__(self, id: str, name: str, position: Vector3D, floor: FloorType, simulation_type: str):
        super().__init__(id, name, position, (4.0, 3.0, 0.1), floor)
        self.simulation_type = simulation_type  # "black_hole", "spacetime", "quantum_foam", etc.
        self.simulation_running = False

    def render_content(self, canvas: Canvas, width: int, height: int):
        """Render simulation to canvas (which becomes a texture on 3D panel)"""
        if not self.simulation_running:
            # Show preview/title
            canvas.create_text(
                width // 2, height // 2,
                text=f"{self.name}\n\nClick to Start Simulation",
                fill='#00ffff',
                font=('Garamond', 16, 'bold'),
                justify='center'
            )
        else:
            # Run actual simulation rendering
            self._run_simulation_frame(canvas, width, height)

    def _run_simulation_frame(self, canvas: Canvas, width: int, height: int):
        """Run one frame of the simulation"""
        import math
        import time

        # Get current frame time
        current_time = time.time()
        if not hasattr(self, '_sim_start_time'):
            self._sim_start_time = current_time

        elapsed = current_time - self._sim_start_time

        if self.simulation_type == "black_hole":
            # Render black hole with event horizon and accretion disk
            center_x, center_y = width // 2, height // 2
            radius = 50

            # Event horizon
            canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                fill='#000000', outline='#ff6600', width=3
            )

            # Accretion disk (animated rotation)
            for i in range(12):
                angle = (elapsed * 50 + i * 30) % 360  # Rotating effect
                rad = math.radians(angle)
                disk_radius = radius * 1.5

                x = center_x + math.cos(rad) * disk_radius
                y = center_y + math.sin(rad) * disk_radius * 0.3  # Elliptical

                # Particles in accretion disk
                particle_color = '#ff' + hex(int((math.sin(angle) + 1) * 127))[2:].zfill(2) + '00'
                canvas.create_oval(
                    x - 3, y - 3, x + 3, y + 3,
                    fill=particle_color, outline=''
                )

            # Hawking radiation effect
            for i in range(8):
                angle = math.radians((elapsed * 100 + i * 45) % 360)
                rad_dist = radius + (elapsed * 10) % 20

                x = center_x + math.cos(angle) * rad_dist
                y = center_y + math.sin(angle) * rad_dist

                canvas.create_oval(
                    x - 2, y - 2, x + 2, y + 2,
                    fill='#00ffff', outline=''
                )

            # Info text
            canvas.create_text(
                width // 2, height - 40,
                text="Black Hole Simulation - Schwarzschild Metric",
                fill='#00ffff', font=('Consolas', 10, 'bold')
            )
            canvas.create_text(
                width // 2, height - 20,
                text=f"Event Horizon: {radius}px | Time: {elapsed:.1f}s",
                fill='#ffffff', font=('Consolas', 9)
            )

    def on_interact(self):
        """Start/stop simulation"""
        self.simulation_running = not self.simulation_running
        print(f"[PhysicsSimulation3D] {self.name}: {'Started' if self.simulation_running else 'Stopped'}")


class Dashboard3D(Widget3D):
    """3D version of dashboard quadrants from UI Base.pdf Page 11"""

    def __init__(self, id: str, position: Vector3D, floor: FloorType):
        super().__init__(id, "Dashboard", position, (6.0, 4.0, 0.1), floor)
        self.quadrants = {
            'projects': [],
            'notices': [],
            'quick_links': [],
            'user_settings': {}
        }

    def render_content(self, canvas: Canvas, width: int, height: int):
        """Render dashboard with 4 quadrants around central Achilles sphere"""
        # Draw quadrants
        hw, hh = width // 2, height // 2

        # Projects (top-left)
        self._draw_glass_panel(canvas, 10, 10, hw - 20, hh - 20, '#00d4ff')
        canvas.create_text(
            20, 20, text="CURRENT PROJECTS", fill='#ffffff',
            font=('Garamond', 14, 'bold'), anchor='nw'
        )

        # Quick Links (top-right)
        self._draw_glass_panel(canvas, hw + 10, 10, hw - 20, hh - 20, '#00d4ff')
        canvas.create_text(
            hw + 20, 20, text="QUICK LINKS", fill='#ffffff',
            font=('Garamond', 14, 'bold'), anchor='nw'
        )

        # Notices (bottom-left)
        self._draw_glass_panel(canvas, 10, hh + 10, hw - 20, hh - 20, '#00d4ff')
        canvas.create_text(
            20, hh + 20, text="NOTICE BOARD", fill='#ffffff',
            font=('Garamond', 14, 'bold'), anchor='nw'
        )

        # User Settings (bottom-right)
        self._draw_glass_panel(canvas, hw + 10, hh + 10, hw - 20, hh - 20, '#00d4ff')
        canvas.create_text(
            hw + 20, hh + 20, text="USER SETTINGS", fill='#ffffff',
            font=('Garamond', 14, 'bold'), anchor='nw'
        )

        # Central Achilles sphere
        self._draw_achilles_sphere(canvas, hw, hh, 60)

    def _draw_glass_panel(self, canvas: Canvas, x: int, y: int, w: int, h: int, border_color: str):
        """Draw glass morphism panel"""
        # Background with transparency effect (simulated)
        canvas.create_rectangle(
            x, y, x + w, y + h,
            fill='#0a1428',  # Dark blue
            outline=border_color,
            width=2
        )

    def _draw_achilles_sphere(self, canvas: Canvas, cx: int, cy: int, radius: int):
        """Draw central Achilles sphere"""
        # Gradient sphere (simplified)
        for i in range(3):
            r = radius - i * 10
            color_val = 255 - i * 40
            color = f'#{color_val:02x}00{color_val:02x}'  # Magenta gradient
            canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=color, outline=''
            )

        # Microphone icon (simplified)
        canvas.create_oval(
            cx - 10, cy - 15, cx + 10, cy + 15,
            fill='#ffffff', outline=''
        )


class DocumentViewer3D(Widget3D):
    """3D document viewer with stacked pages effect from UI Base.pdf Page 5"""

    def __init__(self, id: str, position: Vector3D, floor: FloorType, document_path: Optional[str] = None):
        super().__init__(id, "Document Viewer", position, (5.0, 6.0, 0.1), floor)
        self.document_path = document_path
        self.current_page = 1
        self.total_pages = self._get_document_page_count(document_path)

    def _get_document_page_count(self, path: Optional[str]) -> int:
        """Get actual page count from document"""
        if not path:
            return 1

        from pathlib import Path
        doc_path = Path(path)

        if not doc_path.exists():
            return 1

        # Try to determine page count based on file type
        if doc_path.suffix.lower() == '.pdf':
            try:
                # Would use PyPDF2 or similar if available
                # For now, estimate based on file size (rough approximation)
                size_kb = doc_path.stat().st_size / 1024
                estimated_pages = max(1, int(size_kb / 50))  # ~50KB per page average
                return min(estimated_pages, 999)  # Cap at 999 pages
            except Exception:
                return 1
        elif doc_path.suffix.lower() in ['.txt', '.md']:
            try:
                # Count pages based on line count (60 lines per page)
                with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = sum(1 for _ in f)
                return max(1, (lines // 60) + 1)
            except Exception:
                return 1
        else:
            # Default for unknown file types
            return 1

    def render_content(self, canvas: Canvas, width: int, height: int):
        """Render document with stacked pages effect"""
        # Breadcrumb
        canvas.create_text(
            20, 20,
            text=">Business > Project Title > Document",
            fill='#00ff88',  # Green from UI Base.pdf
            font=('Consolas', 12),
            anchor='nw'
        )

        # Draw 3 stacked layers
        for i in range(3):
            offset = i * 8
            shade = 180 - i * 40
            self._draw_page_layer(
                canvas,
                50 + offset, 60 + offset,
                width - 100, height - 150,
                f'#{shade:02x}{shade:02x}{shade:02x}'
            )

        # Front page content
        self._draw_page_content(canvas, 50, 60, width - 100, height - 150)

        # Page number
        canvas.create_text(
            width // 2, height - 20,
            text=f"Page {self.current_page} of {self.total_pages}",
            fill='#00d4ff',
            font=('Consolas', 10)
        )

    def _draw_page_layer(self, canvas: Canvas, x: int, y: int, w: int, h: int, fill_color: str):
        """Draw one layer of stacked pages"""
        canvas.create_rectangle(
            x, y, x + w, y + h,
            fill=fill_color,
            outline='#00d4ff',
            width=2
        )

    def _draw_page_content(self, canvas: Canvas, x: int, y: int, w: int, h: int):
        """Draw document content on front page"""
        # Title
        canvas.create_text(
            x + w // 2, y + 30,
            text="Document Title",
            fill='#000000',
            font=('Garamond', 18, 'bold')
        )

        # Content lines (mockup)
        for i in range(10):
            line_y = y + 70 + i * 20
            canvas.create_line(
                x + 30, line_y, x + w - 30, line_y,
                fill='#0066cc', width=2
            )


class FlowchartTree3D(Widget3D):
    """3D flowchart tree from UI Base.pdf Page 13"""

    def __init__(self, id: str, position: Vector3D, floor: FloorType):
        super().__init__(id, "Flowchart Tree", position, (8.0, 6.0, 0.1), floor)
        self.nodes = []
        self.connections = []

    def render_content(self, canvas: Canvas, width: int, height: int):
        """Render hierarchical flowchart with colored nodes"""
        # Draw connections first (behind nodes)
        for conn in self.connections:
            x1, y1, x2, y2 = conn
            canvas.create_line(
                x1, y1, x2, y2,
                fill='#ffffff', width=2
            )

        # Draw nodes
        node_colors = ['#ff0000', '#ff9900', '#00ffff', '#00ff00', '#ff00ff']
        x_start = 100
        y_positions = [height // 4, height // 2, 3 * height // 4]

        for i, y in enumerate(y_positions):
            color = node_colors[i % len(node_colors)]
            self._draw_node(canvas, x_start + i * 150, y, 80, 40, color, f"Node {i+1}")

        # Central sphere
        cx, cy = width - 200, height // 2
        for r in range(50, 10, -10):
            alpha = (50 - r) / 40.0
            color_val = int(255 * alpha)
            color = f'#{color_val:02x}00{color_val:02x}'
            canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=color, outline=''
            )

    def _draw_node(self, canvas: Canvas, x: int, y: int, w: int, h: int, color: str, text: str):
        """Draw rounded rectangle node"""
        canvas.create_rectangle(
            x - w // 2, y - h // 2, x + w // 2, y + h // 2,
            fill=color, outline='#ffffff', width=2
        )
        canvas.create_oval(
            x - w // 2 - 5, y - h // 2 - 5, x - w // 2 + 5, y - h // 2 + 5,
            fill='#ffffff', outline=''
        )
        canvas.create_text(
            x, y, text=text, fill='#ffffff', font=('Arial', 10, 'bold')
        )


# ============================================================================
# WIDGET 3D FACTORY
# ============================================================================

class Widget3DFactory:
    """Factory to create all floor-specific widgets as 3D objects"""

    @staticmethod
    def create_floor_widgets(floor: FloorType) -> List[Widget3D]:
        """Create all widgets for a specific floor"""
        widgets = []

        if floor == FloorType.Z_ZERO:
            # TheConstruct - Physics simulations
            widgets.append(PhysicsSimulation3D(
                "black_hole_sim",
                "Black Hole Simulation",
                Vector3D(5, 0, 0),
                floor,
                "black_hole"
            ))
            widgets.append(PhysicsSimulation3D(
                "spacetime_sim",
                "Spacetime Curvature",
                Vector3D(-5, 0, 0),
                floor,
                "spacetime"
            ))
            widgets.append(PhysicsSimulation3D(
                "quantum_foam_sim",
                "Quantum Foam",
                Vector3D(0, 0, -5),
                floor,
                "quantum_foam"
            ))

        elif floor == FloorType.Z_PLUS_3:
            # Trinity - Dashboard
            widgets.append(Dashboard3D(
                "main_dashboard",
                Vector3D(0, 0, 0),
                floor
            ))

        elif floor == FloorType.Z_MINUS_1:
            # Oracle - Document viewer
            widgets.append(DocumentViewer3D(
                "doc_viewer",
                Vector3D(3, 0, 0),
                floor
            ))
            widgets.append(FlowchartTree3D(
                "project_tree",
                Vector3D(-3, 0, 0),
                floor
            ))

        # Add more floor-specific widgets...

        return widgets


# ============================================================================
# 3D WIDGET RENDERER
# ============================================================================

class Widget3DRenderer:
    """Renders widgets as textured 3D panels in the environment"""

    def __init__(self):
        self.widget_canvases: Dict[str, tk.Canvas] = {}
        self.widget_textures: Dict[str, any] = {}  # Image textures

    def prepare_widget_texture(self, widget: Widget3D, width: int = 800, height: int = 600) -> tk.Canvas:
        """Create off-screen canvas for widget to render to"""
        # Create hidden root for off-screen rendering
        if widget.id not in self.widget_canvases:
            root = tk.Tk()
            root.withdraw()
            canvas = tk.Canvas(root, width=width, height=height, bg='#000033')
            canvas.pack()
            self.widget_canvases[widget.id] = canvas

        canvas = self.widget_canvases[widget.id]

        # Clear canvas
        canvas.delete('all')

        # Let widget render its content
        widget.render_content(canvas, width, height)

        return canvas

    def render_widget_as_3d_panel(
        self,
        canvas: tk.Canvas,
        widget: Widget3D,
        camera: Camera,
        screen_width: int,
        screen_height: int
    ):
        """Render widget as a textured 3D panel in the environment"""

        # Get widget's 3D position
        obj = Interactive3DObject(
            id=widget.id,
            name=widget.name,
            position=widget.position,
            size=widget.size,
            color='#1a2332',
            object_type='widget',
            floor=widget.floor
        )

        # Get screen position
        screen_pos = obj.get_screen_position(camera, screen_width, screen_height)
        if not screen_pos:
            return  # Behind camera or off-screen

        x, y, dist = screen_pos

        # Scale based on distance
        size_scale = 100 / (dist + 1)
        width = int(widget.size[0] * size_scale * 100)
        height = int(widget.size[1] * size_scale * 100)

        # Draw panel background
        canvas.create_rectangle(
            x - width // 2, y - height // 2,
            x + width // 2, y + height // 2,
            fill='#0a1428',
            outline='#00d4ff' if widget.is_active else '#00ffff',
            width=3 if widget.is_active else 2,
            tags=('widget_3d', widget.id)
        )

        # Draw simplified widget content
        # (In full implementation, this would use the rendered canvas texture)
        canvas.create_text(
            x, y - height // 2 + 20,
            text=widget.name,
            fill='#00ff88',
            font=('Garamond', 14, 'bold'),
            tags=('widget_3d_label', widget.id)
        )

        # Interaction prompt if close
        if dist < 3.0:
            canvas.create_text(
                x, y + height // 2 + 20,
                text="[E] to Interact",
                fill='#ffff00',
                font=('Consolas', 10),
                tags=('widget_3d_prompt', widget.id)
            )


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'Widget3D',
    'PhysicsSimulation3D',
    'Dashboard3D',
    'DocumentViewer3D',
    'FlowchartTree3D',
    'Widget3DFactory',
    'Widget3DRenderer'
]
