"""
Triangle Render Engine - V1.0.0
Renders components as triangles with vertex circles

User Specification:
- Triangle with 3 vertices
- Circle at each vertex with radius r = 0.5 × L (edge length)
- Properties: color, brightness, reflectivity, opacity
- Lightweight, free/open-source implementation
- Enhanced with Raphael physics for wavefunction reflection
- Spherical rendering with light reflectivity
- Optimized for human vision on Full HD screens
"""

import tkinter as tk
from typing import Dict, Any, Optional, List, Tuple
from .geometry import Triangle, Circle, Point, calculate_triangle_vertices
from .materials import Material, create_material_from_metadata

# Optional Raphael physics integration
try:
    from core.physics.raphael import get_raphael_engine, RaphaelPhysicsEngine
    HAS_RAPHAEL = True
except ImportError:
    HAS_RAPHAEL = False
    get_raphael_engine = None
    RaphaelPhysicsEngine = None


class TriangleRenderer:
    """Renders components as triangles with vertex circles.

    This renderer implements the user's specification:
    - Each component is a triangle with edge length L
    - Each vertex has a circle with radius r = 0.5 × L
    - Material properties (color, brightness, reflectivity, opacity) applied
    """

    def __init__(self, canvas: tk.Canvas, scale: float = 40.0, use_raphael: bool = True):
        """Initialize triangle renderer.

        Args:
            canvas: Tkinter Canvas to render on
            scale: Pixels per unit (default: 40 means 1.0 unit = 40 pixels)
            use_raphael: Enable Raphael physics for enhanced rendering (default: True)
        """
        self.canvas = canvas
        self.scale = scale
        self.rendered_objects = {}  # Store canvas IDs for updates
        self.use_raphael = use_raphael and HAS_RAPHAEL
        self.raphael_engine = get_raphael_engine() if self.use_raphael else None
        self.camera_position = (0.0, 0.0, 10.0)  # Default camera position

    def render_component(
        self,
        component_id: str,
        metadata: Dict[str, Any],
        offset_x: float = 0.0,
        offset_y: float = 0.0
    ) -> Dict[str, List[int]]:
        """Render a single component as triangle with vertex circles.

        Args:
            component_id: Unique identifier for component
            metadata: Component metadata containing:
                - triangle_vertices: [[x, y, z], [x, y, z], [x, y, z]]
                - circle_radius: float (should be 0.5 × edge_length)
                - color: hex color string
                - brightness: 0.0-1.0
                - reflectivity: 0.0-1.0
                - opacity: 0.0-1.0
            offset_x: X offset in units (will be scaled)
            offset_y: Y offset in units (will be scaled)

        Returns:
            Dictionary with canvas IDs: {'triangle': [id], 'circles': [id1, id2, id3]}
        """
        # Extract geometry data
        vertices_data = metadata.get('triangle_vertices', [])
        if not vertices_data or len(vertices_data) != 3:
            # Fallback: generate default equilateral triangle
            vertices_data = calculate_triangle_vertices(0, 0, edge_length=1.0)

        # Create triangle
        triangle = Triangle.from_vertices_list(vertices_data)

        # Create material
        material = create_material_from_metadata(metadata)

        # Render triangle
        triangle_id = self._render_triangle(triangle, material, offset_x, offset_y)

        # Render circles at each vertex
        circle_radius = metadata.get('circle_radius', triangle.get_circle_radius())
        circle_ids = self._render_vertex_circles(
            triangle,
            circle_radius,
            material,
            offset_x,
            offset_y
        )

        # Store canvas IDs
        self.rendered_objects[component_id] = {
            'triangle': [triangle_id],
            'circles': circle_ids
        }

        return self.rendered_objects[component_id]

    def _render_triangle(
        self,
        triangle: Triangle,
        material: Material,
        offset_x: float = 0.0,
        offset_y: float = 0.0
    ) -> int:
        """Render triangle polygon on canvas.

        Args:
            triangle: Triangle geometry
            material: Material properties
            offset_x, offset_y: Offsets in units

        Returns:
            Canvas ID of created polygon
        """
        # Convert to screen coordinates
        points = []
        for vertex in triangle.vertices:
            screen_x = (vertex.x + offset_x) * self.scale
            screen_y = (vertex.y + offset_y) * self.scale
            points.extend([screen_x, screen_y])

        # Get colors
        fill_color = material.to_tkinter_color()
        outline_color = self._darken_color(fill_color, 0.3)

        # Create polygon
        polygon_id = self.canvas.create_polygon(
            *points,
            fill=fill_color,
            outline=outline_color,
            width=2,
            tags=('component_triangle',)
        )

        # Apply opacity (Tkinter doesn't support alpha, so we use stipple for transparency)
        if material.opacity < 1.0:
            # Use stipple pattern for semi-transparency effect
            stipple_patterns = {
                0.75: 'gray75',
                0.50: 'gray50',
                0.25: 'gray25'
            }
            closest_opacity = min(stipple_patterns.keys(), key=lambda x: abs(x - material.opacity))
            if material.opacity < 0.9:
                self.canvas.itemconfig(polygon_id, stipple=stipple_patterns[closest_opacity])

        return polygon_id

    def _render_vertex_circles(
        self,
        triangle: Triangle,
        radius: float,
        material: Material,
        offset_x: float = 0.0,
        offset_y: float = 0.0
    ) -> List[int]:
        """Render circles at each triangle vertex.

        User specification: Circle radius r = 0.5 × L (triangle edge length)

        Args:
            triangle: Triangle geometry
            radius: Circle radius in units
            material: Material properties
            offset_x, offset_y: Offsets in units

        Returns:
            List of canvas IDs for 3 circles
        """
        circle_ids = []

        for vertex in triangle.vertices:
            circle = Circle(center=vertex, radius=radius)
            circle_id = self._render_circle(circle, material, offset_x, offset_y)
            circle_ids.append(circle_id)

        return circle_ids

    def _render_circle(
        self,
        circle: Circle,
        material: Material,
        offset_x: float = 0.0,
        offset_y: float = 0.0
    ) -> int:
        """Render single circle on canvas.

        Args:
            circle: Circle geometry
            material: Material properties
            offset_x, offset_y: Offsets in units

        Returns:
            Canvas ID of created oval
        """
        # Get bounding box in units
        x1, y1, x2, y2 = circle.get_bbox()

        # Convert to screen coordinates with offset
        screen_x1 = (x1 + offset_x) * self.scale
        screen_y1 = (y1 + offset_y) * self.scale
        screen_x2 = (x2 + offset_x) * self.scale
        screen_y2 = (y2 + offset_y) * self.scale

        # Get colors (circles slightly brighter than triangle)
        fill_color = self._lighten_color(material.to_tkinter_color(), 0.2)
        outline_color = material.to_tkinter_color()

        # Create oval
        oval_id = self.canvas.create_oval(
            screen_x1, screen_y1, screen_x2, screen_y2,
            fill=fill_color,
            outline=outline_color,
            width=1,
            tags=('component_circle',)
        )

        # Apply opacity
        if material.opacity < 1.0:
            stipple_patterns = {
                0.75: 'gray75',
                0.50: 'gray50',
                0.25: 'gray25'
            }
            closest_opacity = min(stipple_patterns.keys(), key=lambda x: abs(x - material.opacity))
            if material.opacity < 0.9:
                self.canvas.itemconfig(oval_id, stipple=stipple_patterns[closest_opacity])

        return oval_id

    def update_component(
        self,
        component_id: str,
        metadata: Dict[str, Any],
        offset_x: float = 0.0,
        offset_y: float = 0.0
    ):
        """Update existing component rendering.

        Args:
            component_id: Component to update
            metadata: New metadata
            offset_x, offset_y: New offsets
        """
        # Remove old rendering
        self.remove_component(component_id)

        # Render with new properties
        self.render_component(component_id, metadata, offset_x, offset_y)

    def remove_component(self, component_id: str):
        """Remove component from canvas.

        Args:
            component_id: Component to remove
        """
        if component_id in self.rendered_objects:
            obj_ids = self.rendered_objects[component_id]

            # Delete triangle
            for tid in obj_ids.get('triangle', []):
                self.canvas.delete(tid)

            # Delete circles
            for cid in obj_ids.get('circles', []):
                self.canvas.delete(cid)

            del self.rendered_objects[component_id]

    def clear_all(self):
        """Clear all rendered components."""
        for component_id in list(self.rendered_objects.keys()):
            self.remove_component(component_id)

    def _darken_color(self, hex_color: str, factor: float) -> str:
        """Darken hex color by factor (0.0-1.0).

        Args:
            hex_color: Hex color string
            factor: Darkening factor

        Returns:
            Darkened hex color
        """
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        r = int(r * (1 - factor))
        g = int(g * (1 - factor))
        b = int(b * (1 - factor))

        return f'#{r:02x}{g:02x}{b:02x}'

    def _lighten_color(self, hex_color: str, factor: float) -> str:
        """Lighten hex color by factor (0.0-1.0).

        Args:
            hex_color: Hex color string
            factor: Lightening factor

        Returns:
            Lightened hex color
        """
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)

        return f'#{r:02x}{g:02x}{b:02x}'


def create_test_window():
    """Create test window to demonstrate triangle renderer."""
    root = tk.Tk()
    root.title("Triangle Renderer Test - V1.0.0")
    root.geometry("800x600")

    canvas = tk.Canvas(root, bg='#1a1a1a')
    canvas.pack(fill=tk.BOTH, expand=True)

    renderer = TriangleRenderer(canvas, scale=60)

    # Test components with different materials
    test_components = [
        {
            'id': 'comp1',
            'metadata': {
                'triangle_vertices': calculate_triangle_vertices(0, 0, 1.0),
                'circle_radius': 0.5,
                'color': '#8B0000',
                'brightness': 0.8,
                'reflectivity': 0.5,
                'opacity': 1.0
            },
            'offset': (2, 2)
        },
        {
            'id': 'comp2',
            'metadata': {
                'triangle_vertices': calculate_triangle_vertices(0, 0, 1.0),
                'circle_radius': 0.5,
                'color': '#00008B',
                'brightness': 0.9,
                'reflectivity': 0.7,
                'opacity': 0.75
            },
            'offset': (5, 2)
        },
        {
            'id': 'comp3',
            'metadata': {
                'triangle_vertices': calculate_triangle_vertices(0, 0, 1.0),
                'circle_radius': 0.5,
                'color': '#006400',
                'brightness': 0.7,
                'reflectivity': 0.3,
                'opacity': 1.0
            },
            'offset': (8, 2)
        }
    ]

    for comp in test_components:
        renderer.render_component(
            comp['id'],
            comp['metadata'],
            comp['offset'][0],
            comp['offset'][1]
        )

    # Add label
    label = tk.Label(
        root,
        text="Triangle Render Engine V1.0.0 - User Spec: r = 0.5 × L",
        bg='#1a1a1a',
        fg='white',
        font=('Arial', 10)
    )
    label.pack(side=tk.BOTTOM, pady=10)

    root.mainloop()


if __name__ == '__main__':
    create_test_window()
