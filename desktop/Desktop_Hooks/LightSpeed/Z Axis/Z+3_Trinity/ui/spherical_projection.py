#!/usr/bin/env python
"""
Spherical 360-degree Projection UI System
Universal UI wrapper for all Z-floor interfaces

Provides immersive spherical projection rendering with:
- 360-degree panoramic view
- Spherical coordinate mapping
- Auto-default for all floors and menus
- Glass UI integration
- 3D navigation controls

Author: LightSpeed Team / Romer Industries
Version: 5.1.2
Date: April 8, 2026
"""

import tkinter as tk
from tkinter import ttk
import math
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass


@dataclass
class SphericalCoordinate:
    """Spherical coordinate (r, theta, phi)"""
    radius: float          # Distance from origin
    theta: float          # Azimuthal angle (0-360 deg)
    phi: float            # Polar angle (0-180 deg)

    def to_cartesian(self) -> Tuple[float, float, float]:
        """Convert to Cartesian coordinates (x, y, z)"""
        theta_rad = math.radians(self.theta)
        phi_rad = math.radians(self.phi)

        x = self.radius * math.sin(phi_rad) * math.cos(theta_rad)
        y = self.radius * math.sin(phi_rad) * math.sin(theta_rad)
        z = self.radius * math.cos(phi_rad)

        return (x, y, z)


class SphericalProjection:
    """
    Spherical 360-degree Projection System

    Maps rectangular UI elements onto spherical surface for immersive viewing.
    Auto-applied to all Z-floor interfaces.
    """

    def __init__(self, canvas: tk.Canvas, radius: float = 500.0,
                center: Tuple[float, float] = None):
        """
        Initialize spherical projection

        Parameters:
            canvas: Tkinter canvas for rendering
            radius: Sphere radius (pixels)
            center: Center point (x, y) or None for canvas center
        """
        self.canvas = canvas
        self.radius = radius

        # Camera/view parameters
        self.camera_theta = 0.0    # Horizontal rotation
        self.camera_phi = 90.0     # Vertical rotation (90 deg = equator view)
        self.camera_distance = radius * 2.5
        self.fov = 70.0  # Field of view (degrees)

        # Center point
        if center:
            self.center_x, self.center_y = center
        else:
            self.center_x = self.canvas.winfo_width() / 2
            self.center_y = self.canvas.winfo_height() / 2

        # UI element registry (spherical positions)
        self.elements = {}

        # Projection mode
        self.projection_mode = 'equirectangular'  # equirectangular, stereographic, orthographic

        # Drag state
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0

        # Bind mouse controls
        self._setup_controls()

    def _setup_controls(self):
        """Setup mouse/keyboard controls for spherical navigation"""
        # Mouse drag to rotate
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_end)

        # Mouse wheel to zoom
        self.canvas.bind("<MouseWheel>", self._on_zoom)

        # Keyboard controls
        self.canvas.bind("<Left>", lambda e: self.rotate(-5, 0))
        self.canvas.bind("<Right>", lambda e: self.rotate(5, 0))
        self.canvas.bind("<Up>", lambda e: self.rotate(0, -5))
        self.canvas.bind("<Down>", lambda e: self.rotate(0, 5))

    def _on_drag_start(self, event):
        """Start drag rotation"""
        self.dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def _on_drag_motion(self, event):
        """Handle drag rotation"""
        if not self.dragging:
            return

        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y

        # Rotate camera
        self.camera_theta += dx * 0.5
        self.camera_phi -= dy * 0.5

        # Clamp phi to 0-180 deg
        self.camera_phi = max(0.1, min(179.9, self.camera_phi))

        # Normalize theta to 0-360 deg
        self.camera_theta = self.camera_theta % 360

        self.drag_start_x = event.x
        self.drag_start_y = event.y

        # Redraw
        self.render()

    def _on_drag_end(self, event):
        """End drag rotation"""
        self.dragging = False

    def _on_zoom(self, event):
        """Handle zoom (mouse wheel)"""
        if event.delta > 0:
            self.camera_distance *= 0.9  # Zoom in
        else:
            self.camera_distance *= 1.1  # Zoom out

        # Clamp distance
        self.camera_distance = max(self.radius * 1.2, min(self.radius * 10, self.camera_distance))

        self.render()

    def rotate(self, delta_theta: float, delta_phi: float):
        """Rotate camera view"""
        self.camera_theta += delta_theta
        self.camera_phi += delta_phi

        # Clamp and normalize
        self.camera_phi = max(0.1, min(179.9, self.camera_phi))
        self.camera_theta = self.camera_theta % 360

        self.render()

    def add_element(self, element_id: str, theta: float, phi: float,
                   content: str, width: int = 200, height: int = 100,
                   floor_color: str = '#00FFFF'):
        """
        Add UI element at spherical position

        Parameters:
            element_id: Unique element ID
            theta: Azimuthal angle (0-360 deg)
            phi: Polar angle (0-180 deg)
            content: Text content
            width: Element width (pixels)
            height: Element height (pixels)
            floor_color: Element color
        """
        self.elements[element_id] = {
            'theta': theta,
            'phi': phi,
            'content': content,
            'width': width,
            'height': height,
            'color': floor_color,
            'visible': True
        }

    def project_to_screen(self, coord: SphericalCoordinate) -> Tuple[float, float, bool]:
        """
        Project spherical coordinate to screen position

        Parameters:
            coord: Spherical coordinate

        Returns:
            (screen_x, screen_y, visible) tuple
        """
        # Convert to Cartesian relative to camera
        x, y, z = coord.to_cartesian()

        # Camera rotation (simplified)
        # Rotate around Y axis (theta)
        theta_rad = math.radians(self.camera_theta)
        x_rot = x * math.cos(theta_rad) - z * math.sin(theta_rad)
        z_rot = x * math.sin(theta_rad) + z * math.cos(theta_rad)

        # Rotate around X axis (phi offset from 90 deg)
        phi_offset = self.camera_phi - 90.0
        phi_rad = math.radians(phi_offset)
        y_rot = y * math.cos(phi_rad) - z_rot * math.sin(phi_rad)
        z_final = y * math.sin(phi_rad) + z_rot * math.cos(phi_rad)

        # Check if behind camera
        if z_final >= 0:
            return (0, 0, False)

        # Perspective projection
        scale = self.camera_distance / abs(z_final)
        screen_x = self.center_x + x_rot * scale
        screen_y = self.center_y - y_rot * scale

        # Check if in viewport
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        visible = (0 <= screen_x <= canvas_width and
                  0 <= screen_y <= canvas_height)

        return (screen_x, screen_y, visible)

    def render(self):
        """Render all elements with spherical projection"""
        self.canvas.delete("spherical")  # Clear previous spherical elements

        # Update center if canvas resized
        self.center_x = self.canvas.winfo_width() / 2
        self.center_y = self.canvas.winfo_height() / 2

        # Draw sphere grid (latitude/longitude lines)
        self._draw_sphere_grid()

        # Render elements
        for element_id, element in self.elements.items():
            if not element['visible']:
                continue

            # Create spherical coordinate
            coord = SphericalCoordinate(
                radius=self.radius,
                theta=element['theta'],
                phi=element['phi']
            )

            # Project to screen
            screen_x, screen_y, visible = self.project_to_screen(coord)

            if not visible:
                continue

            # Calculate scale based on distance from camera
            # Elements farther from center are smaller
            center_dist = math.sqrt((screen_x - self.center_x)**2 +
                                   (screen_y - self.center_y)**2)
            scale_factor = max(0.5, 1.0 - (center_dist / (self.canvas.winfo_width() / 2)) * 0.5)

            # Draw element
            width = element['width'] * scale_factor
            height = element['height'] * scale_factor

            # Background
            self.canvas.create_rectangle(
                screen_x - width/2, screen_y - height/2,
                screen_x + width/2, screen_y + height/2,
                fill=element['color'], outline='#FFFFFF',
                width=2, tags="spherical"
            )

            # Text
            self.canvas.create_text(
                screen_x, screen_y,
                text=element['content'],
                fill='#FFFFFF',
                font=('Arial', int(12 * scale_factor), 'bold'),
                tags="spherical"
            )

    def _draw_sphere_grid(self):
        """Draw latitude/longitude grid lines"""
        grid_color = '#004466'  # Dark cyan (Tkinter doesn't support alpha in hex)

        # Latitude lines (horizontal)
        for phi in range(0, 181, 30):
            points = []
            for theta in range(0, 361, 10):
                coord = SphericalCoordinate(self.radius, theta, phi)
                screen_x, screen_y, visible = self.project_to_screen(coord)
                if visible:
                    points.extend([screen_x, screen_y])

            if len(points) >= 4:
                self.canvas.create_line(*points, fill=grid_color, width=1, tags="spherical")

        # Longitude lines (vertical)
        for theta in range(0, 360, 30):
            points = []
            for phi in range(0, 181, 10):
                coord = SphericalCoordinate(self.radius, theta, phi)
                screen_x, screen_y, visible = self.project_to_screen(coord)
                if visible:
                    points.extend([screen_x, screen_y])

            if len(points) >= 4:
                self.canvas.create_line(*points, fill=grid_color, width=1, tags="spherical")


class SphericalFloorLayout:
    """
    Spherical Layout for Z-Floors

    Auto-arranges Z-floors in spherical shell configuration:
    - Z+3 (Trinity): North pole (phi=0 deg)
    - Z+2 (Neo): Upper equator
    - Z+1 (Architect): Equator
    - Z0 (TheConstruct): Center/Equator
    - Z-1 (Morpheus): Lower equator
    - Z-2 (Oracle): Lower hemisphere
    - Z-3 (Smith): Lower hemisphere
    - Z-4 (Merovingian): South pole (phi=180 deg)
    """

    # Floor positions (theta, phi) in degrees
    FLOOR_POSITIONS = {
        'Z+3_Trinity': (45, 40),        # Upper right
        'Z+2_Neo': (135, 40),           # Upper left
        'Z+1_Architect': (225, 60),     # Middle left
        'Z0_TheConstruct': (0, 90),     # Center (equator)
        'Z-1_Morpheus': (135, 120),     # Lower left
        'Z-2_Oracle': (225, 120),       # Lower right
        'Z-3_Smith': (315, 140),        # Lower far right
        'Z-4_Merovingian': (0, 170)     # Bottom
    }

    # Floor colors (Glass UI theme)
    FLOOR_COLORS = {
        'Z+3_Trinity': '#00FFFF',       # Cyan
        'Z+2_Neo': '#00FF00',           # Green
        'Z+1_Architect': '#FFFF00',     # Yellow
        'Z0_TheConstruct': '#FFFFFF',   # White
        'Z-1_Morpheus': '#FF8800',      # Orange
        'Z-2_Oracle': '#0088FF',        # Blue
        'Z-3_Smith': '#FF0088',         # Pink
        'Z-4_Merovingian': '#88FF00'    # Lime
    }

    @classmethod
    def setup_floor_projection(cls, projection: SphericalProjection):
        """Setup all Z-floors in spherical projection"""
        for floor, (theta, phi) in cls.FLOOR_POSITIONS.items():
            projection.add_element(
                element_id=floor,
                theta=theta,
                phi=phi,
                content=floor.replace('_', ' '),
                width=220,
                height=120,
                floor_color=cls.FLOOR_COLORS.get(floor, '#00FFFF')
            )


# Standalone test
def test_spherical_projection():
    """Test spherical projection UI"""
    root = tk.Tk()
    root.title("Spherical 360-degree Projection - LightSpeed V1.0")
    root.geometry("1200x800")
    root.configure(bg='#000B1F')

    # Create canvas
    canvas = tk.Canvas(root, bg='#000B1F', highlightthickness=0)
    canvas.pack(fill='both', expand=True)

    # Wait for canvas to render
    root.update()

    # Create spherical projection
    projection = SphericalProjection(canvas, radius=400)

    # Setup Z-floors
    SphericalFloorLayout.setup_floor_projection(projection)

    # Initial render
    projection.render()

    # Info label
    info_label = tk.Label(root, text="Controls: Drag to rotate | Mouse wheel to zoom | Arrow keys to navigate",
                         bg='#001B3F', fg='#00FFFF', font=('Arial', 10))
    info_label.pack(side='bottom', fill='x')

    # Camera info
    def update_camera_info():
        info_label.config(text=f"Camera: theta={projection.camera_theta:.1f} deg phi={projection.camera_phi:.1f} deg "
                              f"dist={projection.camera_distance:.0f} | "
                              f"Controls: Drag to rotate | Wheel to zoom | Arrows to navigate")
        root.after(100, update_camera_info)

    update_camera_info()

    root.mainloop()


if __name__ == '__main__':
    test_spherical_projection()
