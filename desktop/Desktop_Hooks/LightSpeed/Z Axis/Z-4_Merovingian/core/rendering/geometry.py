"""
Geometric Primitives for Triangle Rendering
Triangle and Circle classes with vertex calculations
"""

from dataclasses import dataclass
from typing import List, Tuple
import math


@dataclass
class Point:
    """2D or 3D point."""
    x: float
    y: float
    z: float = 0.0

    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert to tuple format."""
        return (self.x, self.y, self.z)

    def to_2d(self) -> Tuple[float, float]:
        """Convert to 2D tuple (x, y) for Tkinter."""
        return (self.x, self.y)


@dataclass
class Triangle:
    """Equilateral triangle with 3 vertices.

    User specification: Triangle with edge length L, each vertex
    is the center of a circle with radius r = 0.5 × L
    """

    vertices: List[Point]  # 3 vertices
    edge_length: float

    @classmethod
    def from_vertices_list(cls, vertices: List[List[float]]) -> 'Triangle':
        """Create triangle from vertex list [[x, y, z], [x, y, z], [x, y, z]]."""
        points = [Point(v[0], v[1], v[2] if len(v) > 2 else 0.0) for v in vertices]

        # Calculate edge length from first two vertices
        dx = points[1].x - points[0].x
        dy = points[1].y - points[0].y
        edge_length = math.sqrt(dx**2 + dy**2)

        return cls(vertices=points, edge_length=edge_length)

    def get_circle_radius(self) -> float:
        """Calculate circle radius: r = 0.5 × L (user specification)."""
        return 0.5 * self.edge_length

    def get_center(self) -> Point:
        """Calculate centroid of triangle."""
        x = sum(v.x for v in self.vertices) / 3
        y = sum(v.y for v in self.vertices) / 3
        z = sum(v.z for v in self.vertices) / 3
        return Point(x, y, z)

    def to_2d_polygon(self) -> List[Tuple[float, float]]:
        """Convert to 2D polygon for Tkinter rendering."""
        return [v.to_2d() for v in self.vertices]


@dataclass
class Circle:
    """Circle at triangle vertex.

    User specification: Circle with radius r = 0.5 × L where L is triangle edge length
    """

    center: Point
    radius: float

    def get_bbox(self) -> Tuple[float, float, float, float]:
        """Get bounding box for Tkinter: (x1, y1, x2, y2)."""
        return (
            self.center.x - self.radius,
            self.center.y - self.radius,
            self.center.x + self.radius,
            self.center.y + self.radius
        )


def calculate_triangle_vertices(
    base_x: float,
    base_y: float,
    edge_length: float = 1.0,
    z_level: float = 0.0
) -> List[List[float]]:
    """Calculate equilateral triangle vertices.

    Args:
        base_x: X coordinate of bottom-left vertex
        base_y: Y coordinate of bottom edge
        edge_length: Length of each edge (default: 1.0)
        z_level: Z coordinate for 3D positioning

    Returns:
        List of 3 vertices: [[x, y, z], [x, y, z], [x, y, z]]

    Triangle specification:
        - Equilateral triangle with edge length L
        - Height = √3/2 × L
        - Vertices: bottom-left, bottom-right, top-center
    """
    height = math.sqrt(3) / 2 * edge_length

    return [
        [base_x, base_y, z_level],  # Bottom-left
        [base_x + edge_length, base_y, z_level],  # Bottom-right
        [base_x + edge_length / 2, base_y + height, z_level]  # Top-center
    ]


def calculate_grid_position(
    index: int,
    columns: int = 3,
    spacing: float = 2.0,
    edge_length: float = 1.0
) -> Tuple[float, float]:
    """Calculate grid position for component at given index.

    Args:
        index: Component index (0-based)
        columns: Number of columns in grid
        spacing: Spacing between triangles
        edge_length: Triangle edge length

    Returns:
        (base_x, base_y) coordinates for triangle
    """
    row = index // columns
    col = index % columns

    base_x = col * spacing
    base_y = row * spacing

    return (base_x, base_y)


def scale_vertices(vertices: List[List[float]], scale: float) -> List[List[float]]:
    """Scale triangle vertices by given factor.

    Args:
        vertices: Original vertices
        scale: Scale factor

    Returns:
        Scaled vertices
    """
    return [[v[0] * scale, v[1] * scale, v[2] * scale] for v in vertices]


def translate_vertices(
    vertices: List[List[float]],
    dx: float,
    dy: float,
    dz: float = 0.0
) -> List[List[float]]:
    """Translate triangle vertices by given offset.

    Args:
        vertices: Original vertices
        dx, dy, dz: Translation offsets

    Returns:
        Translated vertices
    """
    return [[v[0] + dx, v[1] + dy, v[2] + dz] for v in vertices]
