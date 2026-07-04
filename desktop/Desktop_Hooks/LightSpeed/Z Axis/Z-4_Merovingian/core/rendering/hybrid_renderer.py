"""
Hybrid Triangle-Sphere Renderer
LightSpeed Platform - Bridging Current Tools with Spherical Innovation

STRATEGY: Use triangles as the foundation structure with spheres at vertices
- Each triangle vertex = sphere center
- Each triangle edge = blended sphere intersection
- Uses existing libraries: Plotly, Matplotlib, PyVista
- Integrates Raphael equations for physics-based rendering

This approach:
1. Leverages existing triangle-based tools (Plotly 3D, VTK)
2. Adds sphere-based enhancements at vertices
3. Creates smooth surfaces through sphere blending
4. Maintains compatibility with current ecosystem

Author: LightSpeed Team / ACHILLES
Date: December 9, 2025
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import math

# Import existing sphere primitives
from .sphere_primitive import SpherePrimitive, Material, RGBT, SphereObject

# Import existing Vector3D
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from ui.immersive_engine import Vector3D

# Import Raphael equations
from physics_modules import raphael_equations


@dataclass
class Triangle:
    """
    Triangle with sphere centers at each vertex.

    Each vertex has an associated sphere that contributes to the final surface.
    The triangle mesh defines the connectivity, spheres define the appearance.
    """
    vertices: Tuple[Vector3D, Vector3D, Vector3D]  # Three corners
    vertex_spheres: Tuple[SpherePrimitive, SpherePrimitive, SpherePrimitive]
    normal: Vector3D = None  # Surface normal (calculated)

    def __post_init__(self):
        """Calculate triangle normal if not provided."""
        if self.normal is None:
            self.normal = self._calculate_normal()

    def _calculate_normal(self) -> Vector3D:
        """Calculate surface normal using cross product of edges."""
        v0, v1, v2 = self.vertices

        # Two edge vectors
        edge1 = v1 - v0
        edge2 = v2 - v0

        # Cross product
        normal = Vector3D(
            edge1.y * edge2.z - edge1.z * edge2.y,
            edge1.z * edge2.x - edge1.x * edge2.z,
            edge1.x * edge2.y - edge1.y * edge2.x
        )

        return normal.normalize()

    def calculate_normal(self) -> Vector3D:
        """Public method to calculate/return surface normal."""
        if self.normal is None:
            self.normal = self._calculate_normal()
        return self.normal

    def barycentric_coords(self, point: Vector3D) -> Tuple[float, float, float]:
        """
        Calculate barycentric coordinates of point within triangle.

        Returns (u, v, w) where point = u*v0 + v*v1 + w*v2
        and u + v + w = 1
        """
        v0, v1, v2 = self.vertices

        # Vectors
        v0v1 = v1 - v0
        v0v2 = v2 - v0
        v0p = point - v0

        # Dot products
        dot00 = v0v2.x * v0v2.x + v0v2.y * v0v2.y + v0v2.z * v0v2.z
        dot01 = v0v2.x * v0v1.x + v0v2.y * v0v1.y + v0v2.z * v0v1.z
        dot02 = v0v2.x * v0p.x + v0v2.y * v0p.y + v0v2.z * v0p.z
        dot11 = v0v1.x * v0v1.x + v0v1.y * v0v1.y + v0v1.z * v0v1.z
        dot12 = v0v1.x * v0p.x + v0v1.y * v0p.y + v0v1.z * v0p.z

        # Barycentric coordinates
        inv_denom = 1.0 / (dot00 * dot11 - dot01 * dot01)
        v = (dot11 * dot02 - dot01 * dot12) * inv_denom
        w = (dot00 * dot12 - dot01 * dot02) * inv_denom
        u = 1.0 - v - w

        return (u, v, w)

    def interpolate_color_at_point(self, point: Vector3D) -> Tuple[int, int, int]:
        """
        Calculate color at point using barycentric interpolation of vertex sphere colors.

        This creates smooth color gradients across the triangle surface
        based on the sphere colors at each vertex.
        """
        u, v, w = self.barycentric_coords(point)

        # Get colors from vertex spheres
        c0 = self.vertex_spheres[0].get_rgb_color()
        c1 = self.vertex_spheres[1].get_rgb_color()
        c2 = self.vertex_spheres[2].get_rgb_color()

        # Interpolate
        r = int(u * c0[0] + v * c1[0] + w * c2[0])
        g = int(u * c0[1] + v * c1[1] + w * c2[1])
        b = int(u * c0[2] + v * c1[2] + w * c2[2])

        # Clamp
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))

        return (r, g, b)

    def sphere_influence_at_point(self, point: Vector3D) -> float:
        """
        Calculate combined influence of vertex spheres at point.

        Closer to sphere center = stronger influence.
        Used for bump mapping and surface detail.
        """
        total_influence = 0.0

        for sphere in self.vertex_spheres:
            distance = (point - sphere.center).magnitude()

            # Inverse distance weighting
            if distance > 0:
                influence = 1.0 / (distance * distance)
                total_influence += influence

        return total_influence


class HybridMesh:
    """
    Triangle mesh with spheres at vertices.

    Combines the best of both worlds:
    - Triangle mesh defines connectivity and structure
    - Spheres at vertices define appearance and physics
    - Can use existing triangle libraries (Plotly, VTK, Matplotlib)
    - Enhanced with sphere-based rendering
    """

    def __init__(self, name: str = "hybrid_mesh"):
        self.name = name
        self.triangles: List[Triangle] = []
        self.vertices: List[Vector3D] = []
        self.vertex_spheres: List[SpherePrimitive] = []

        # Cached data for rendering
        self._vertex_array = None
        self._color_array = None
        self._normal_array = None

    def add_triangle(self, triangle: Triangle):
        """Add triangle to mesh."""
        self.triangles.append(triangle)

        # Invalidate caches
        self._vertex_array = None
        self._color_array = None
        self._normal_array = None

    def add_sphere_at_vertex(self, vertex: Vector3D, sphere: SpherePrimitive):
        """Add vertex and associated sphere."""
        self.vertices.append(vertex)
        self.vertex_spheres.append(sphere)

    def get_vertex_array(self) -> np.ndarray:
        """Get vertices as NumPy array for plotting libraries."""
        if self._vertex_array is None:
            vertices = []
            for tri in self.triangles:
                for v in tri.vertices:
                    vertices.append([v.x, v.y, v.z])

            self._vertex_array = np.array(vertices)

        return self._vertex_array

    def get_color_array(self) -> np.ndarray:
        """Get vertex colors as NumPy array."""
        if self._color_array is None:
            colors = []
            for tri in self.triangles:
                for sphere in tri.vertex_spheres:
                    rgb = sphere.get_rgb_color()
                    colors.append([rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0])

            self._color_array = np.array(colors)

        return self._color_array

    def get_normal_array(self) -> np.ndarray:
        """Get surface normals as NumPy array."""
        if self._normal_array is None:
            normals = []
            for tri in self.triangles:
                # Each vertex in triangle gets the same normal
                for _ in range(3):
                    normals.append([tri.normal.x, tri.normal.y, tri.normal.z])

            self._normal_array = np.array(normals)

        return self._normal_array

    def get_triangle_indices(self) -> np.ndarray:
        """Get triangle connectivity as index array."""
        indices = []
        for i in range(len(self.triangles)):
            base = i * 3
            indices.append([base, base+1, base+2])

        return np.array(indices)

    def calculate_raphael_field(self) -> np.ndarray:
        """
        Calculate Raphael equation field across mesh.

        Uses sphere material properties (density, rotation) to calculate
        energy/curvature fields from Raphael's equations.
        """
        vertices = self.get_vertex_array()
        field_values = np.zeros(len(vertices))

        for i, vertex in enumerate(vertices):
            # Find nearest sphere
            min_dist = float('inf')
            nearest_sphere = None

            for sphere in self.vertex_spheres:
                dist = math.sqrt(
                    (vertex[0] - sphere.center.x)**2 +
                    (vertex[1] - sphere.center.y)**2 +
                    (vertex[2] - sphere.center.z)**2
                )
                if dist < min_dist:
                    min_dist = dist
                    nearest_sphere = sphere

            if nearest_sphere:
                # Use Raphael equations to calculate field value
                # Convert position to spherical coordinates
                r = min_dist
                theta = math.atan2(vertex[1], vertex[0])
                # Clamp vertex[2]/r to [-1, 1] to avoid math domain error
                phi = math.acos(np.clip(vertex[2] / max(r, 0.001), -1.0, 1.0))

                # Get material properties
                mass = nearest_sphere.material.density * (4/3) * math.pi * (nearest_sphere.radius ** 3)
                spin = nearest_sphere.material.rotation_speed

                # Calculate Raphael field (using oval equations)
                curvature, density, energy, dark_energy = raphael_equations.raphael_equations_oval(
                    r=np.array([r]),
                    theta=np.array([theta]),
                    phi=np.array([phi]),
                    t=0.0,
                    mass=mass,
                    spin=spin
                )

                field_values[i] = energy[0]

        return field_values

    def to_plotly_mesh3d(self) -> Dict:
        """
        Export to Plotly Mesh3d format.

        Returns dict compatible with plotly.graph_objects.Mesh3d
        """
        vertices = self.get_vertex_array()
        colors = self.get_color_array()
        indices = self.get_triangle_indices()

        return {
            'x': vertices[:, 0],
            'y': vertices[:, 1],
            'z': vertices[:, 2],
            'i': indices[:, 0],
            'j': indices[:, 1],
            'k': indices[:, 2],
            'vertexcolor': colors,
            'name': self.name
        }

    def to_matplotlib_trisurf(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Export to Matplotlib TriSurf format.

        Returns (x, y, z, colors) for plot_trisurf()
        """
        vertices = self.get_vertex_array()
        colors = self.get_color_array()

        # Average RGB to single color value for colormap
        color_values = np.mean(colors, axis=1)

        return (vertices[:, 0], vertices[:, 1], vertices[:, 2], color_values)


class HybridRenderer:
    """
    Main renderer using hybrid triangle-sphere approach.

    Rendering modes:
    1. Plotly 3D - Interactive web-based visualization
    2. Matplotlib - Static high-quality renders
    3. PyVista/VTK - Advanced 3D with ray tracing (optional)
    """

    def __init__(self):
        self.meshes: List[HybridMesh] = []
        self.camera_position = Vector3D(0, 0, 10)
        self.camera_target = Vector3D(0, 0, 0)
        self.fov = 70.0  # 70-degree field of view

    def add_mesh(self, mesh: HybridMesh):
        """Add mesh to scene."""
        self.meshes.append(mesh)

    def render_plotly(self, show_spheres: bool = False) -> 'plotly.graph_objects.Figure':
        """
        Render scene using Plotly (interactive 3D).

        Args:
            show_spheres: If True, also render vertex spheres as wireframes

        Returns:
            Plotly Figure object
        """
        try:
            import plotly.graph_objects as go
        except ImportError:
            raise ImportError("Plotly not installed. Run: pip install plotly")

        data = []

        # Add meshes
        for mesh in self.meshes:
            mesh_dict = mesh.to_plotly_mesh3d()
            data.append(go.Mesh3d(**mesh_dict))

            # Optionally add sphere wireframes at vertices
            if show_spheres:
                for sphere in mesh.vertex_spheres:
                    sphere_trace = self._create_sphere_wireframe(sphere)
                    data.append(sphere_trace)

        # Create figure
        fig = go.Figure(data=data)

        # Camera setup
        fig.update_layout(
            scene=dict(
                camera=dict(
                    eye=dict(
                        x=self.camera_position.x / 10,
                        y=self.camera_position.y / 10,
                        z=self.camera_position.z / 10
                    ),
                    center=dict(
                        x=self.camera_target.x,
                        y=self.camera_target.y,
                        z=self.camera_target.z
                    )
                ),
                aspectmode='data'
            ),
            title=f"LightSpeed Hybrid Renderer - {len(self.meshes)} meshes"
        )

        return fig

    def render_matplotlib(self, ax=None, elevation=30, azimuth=45):
        """
        Render scene using Matplotlib (static image).

        Args:
            ax: Matplotlib 3D axis (creates new if None)
            elevation: Camera elevation angle
            azimuth: Camera azimuth angle

        Returns:
            Matplotlib axis object
        """
        try:
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
        except ImportError:
            raise ImportError("Matplotlib not installed. Run: pip install matplotlib")

        if ax is None:
            fig = plt.figure(figsize=(12, 9))
            ax = fig.add_subplot(111, projection='3d')

        # Render each mesh
        for mesh in self.meshes:
            x, y, z, colors = mesh.to_matplotlib_trisurf()
            ax.plot_trisurf(x, y, z, cmap='viridis', alpha=0.8)

        # Set view angle
        ax.view_init(elev=elevation, azim=azimuth)

        # Labels
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('LightSpeed Hybrid Renderer')

        return ax

    def _create_sphere_wireframe(self, sphere: SpherePrimitive) -> 'plotly.graph_objects.Scatter3d':
        """Create wireframe representation of sphere for debugging."""
        try:
            import plotly.graph_objects as go
        except ImportError:
            return None

        # Create sphere mesh
        u = np.linspace(0, 2 * np.pi, 20)
        v = np.linspace(0, np.pi, 20)

        x = sphere.center.x + sphere.radius * np.outer(np.cos(u), np.sin(v))
        y = sphere.center.y + sphere.radius * np.outer(np.sin(u), np.sin(v))
        z = sphere.center.z + sphere.radius * np.outer(np.ones(np.size(u)), np.cos(v))

        return go.Surface(
            x=x, y=y, z=z,
            opacity=0.3,
            colorscale='Viridis',
            showscale=False
        )


# ==================== PRESET MESH BUILDERS ====================

def create_asteroid_mesh(
    center: Vector3D,
    size: float,
    composition: Dict[str, float] = None,
    detail_level: int = 2
) -> HybridMesh:
    """
    Create asteroid mesh with sphere-enhanced vertices.

    Args:
        center: Center position
        size: Approximate radius
        composition: Material composition (e.g., {"iron": 0.6, "nickel": 0.3})
        detail_level: 1=low, 2=medium, 3=high polygon count

    Returns:
        HybridMesh representing asteroid
    """
    if composition is None:
        composition = {"iron": 0.5, "silicate": 0.4, "ice": 0.1}

    mesh = HybridMesh(name="asteroid")

    # Create icosahedron base mesh (good for irregular shapes)
    phi = (1 + math.sqrt(5)) / 2  # Golden ratio

    # Icosahedron vertices
    base_vertices = [
        (-1, phi, 0), (1, phi, 0), (-1, -phi, 0), (1, -phi, 0),
        (0, -1, phi), (0, 1, phi), (0, -1, -phi), (0, 1, -phi),
        (phi, 0, -1), (phi, 0, 1), (-phi, 0, -1), (-phi, 0, 1)
    ]

    # Normalize and scale
    vertices = []
    for v in base_vertices:
        mag = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
        # Add randomness for asteroid irregularity
        scale = size * (0.8 + np.random.random() * 0.4)
        vertices.append(Vector3D(
            center.x + (v[0] / mag) * scale,
            center.y + (v[1] / mag) * scale,
            center.z + (v[2] / mag) * scale
        ))

    # Create material based on composition
    # Dominant material determines color
    dominant_material = max(composition.items(), key=lambda x: x[1])[0]

    material_colors = {
        "iron": RGBT(red_nm=650, green_nm=600, blue_nm=580, transparency=0.0),
        "nickel": RGBT(red_nm=700, green_nm=680, blue_nm=650, transparency=0.0),
        "silicate": RGBT(red_nm=600, green_nm=550, blue_nm=500, transparency=0.0),
        "ice": RGBT(red_nm=500, green_nm=520, blue_nm=550, transparency=0.2)
    }

    rgbt = material_colors.get(dominant_material, RGBT())
    material = Material(base_diameter=size*0.3, rgbt=rgbt, reflectivity=0.4)

    # Create spheres at vertices
    vertex_spheres = []
    for vertex in vertices:
        sphere = SpherePrimitive(
            center=vertex,
            radius=size * 0.2,
            material=material,
            name=f"asteroid_vertex_{len(vertex_spheres)}"
        )
        vertex_spheres.append(sphere)
        mesh.add_sphere_at_vertex(vertex, sphere)

    # Create triangles (icosahedron faces)
    faces = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)
    ]

    for face in faces:
        triangle = Triangle(
            vertices=(vertices[face[0]], vertices[face[1]], vertices[face[2]]),
            vertex_spheres=(vertex_spheres[face[0]], vertex_spheres[face[1]], vertex_spheres[face[2]])
        )
        mesh.add_triangle(triangle)

    return mesh


def create_mark3_unit_mesh(center: Vector3D, size: float = 1.0) -> HybridMesh:
    """
    Create Mark III extraction unit mesh.

    Simplified cylindrical design with extraction head.
    """
    mesh = HybridMesh(name="mark3_unit")

    # Mark III is metallic
    material = Material(
        base_diameter=size*0.2,
        rgbt=RGBT(red_nm=680, green_nm=660, blue_nm=640, transparency=0.0),
        reflectivity=0.7
    )

    # Create simple cylinder with sphere vertices
    num_sides = 8
    height = size * 2
    radius = size * 0.5

    vertices = []
    vertex_spheres = []

    # Top circle
    for i in range(num_sides):
        angle = 2 * math.pi * i / num_sides
        x = center.x + radius * math.cos(angle)
        y = center.y + height/2
        z = center.z + radius * math.sin(angle)

        vertex = Vector3D(x, y, z)
        sphere = SpherePrimitive(vertex, radius*0.3, material)

        vertices.append(vertex)
        vertex_spheres.append(sphere)
        mesh.add_sphere_at_vertex(vertex, sphere)

    # Bottom circle
    for i in range(num_sides):
        angle = 2 * math.pi * i / num_sides
        x = center.x + radius * math.cos(angle)
        y = center.y - height/2
        z = center.z + radius * math.sin(angle)

        vertex = Vector3D(x, y, z)
        sphere = SpherePrimitive(vertex, radius*0.3, material)

        vertices.append(vertex)
        vertex_spheres.append(sphere)
        mesh.add_sphere_at_vertex(vertex, sphere)

    # Create side triangles
    for i in range(num_sides):
        next_i = (i + 1) % num_sides

        # Two triangles per side face
        triangle1 = Triangle(
            vertices=(vertices[i], vertices[next_i], vertices[i + num_sides]),
            vertex_spheres=(vertex_spheres[i], vertex_spheres[next_i], vertex_spheres[i + num_sides])
        )
        mesh.add_triangle(triangle1)

        triangle2 = Triangle(
            vertices=(vertices[next_i], vertices[next_i + num_sides], vertices[i + num_sides]),
            vertex_spheres=(vertex_spheres[next_i], vertex_spheres[next_i + num_sides], vertex_spheres[i + num_sides])
        )
        mesh.add_triangle(triangle2)

    return mesh
