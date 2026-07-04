"""
Sphere Primitive - Revolutionary Rendering Building Block
LightSpeed Platform

Instead of triangles, we use overlapping spheres to create smooth 3D objects.
Materials defined by wavelength-diameter encoding (RGBT system).

Author: LightSpeed Team / ACHILLES
Date: December 9, 2025
"""

from typing import Tuple, Dict, Optional
from dataclasses import dataclass, field
import math

# Import from existing immersive engine
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from ui.immersive_engine import Vector3D


@dataclass
class RGBT:
    """
    Red/Green/Blue/Transparency wavelength encoding.

    Instead of arbitrary RGB values, we use actual wavelengths:
    - Red: 700 nm (long wavelength)
    - Green: 550 nm (medium wavelength)
    - Blue: 450 nm (short wavelength)
    - Transparency: 0.0 (opaque) to 1.0 (invisible)

    Sphere diameter modulates with wavelength for physics-based rendering.
    """
    red_nm: float = 700.0      # Red wavelength (nanometers)
    green_nm: float = 550.0    # Green wavelength
    blue_nm: float = 450.0     # Blue wavelength
    transparency: float = 0.0  # 0 = opaque, 1 = fully transparent

    def to_rgb_tuple(self) -> Tuple[int, int, int]:
        """
        Convert wavelengths to RGB color values (0-255).

        Uses inverse mapping: wavelength → perceived color intensity
        """
        # Normalize wavelengths to 0-1 range
        r = (self.red_nm - 380) / (750 - 380)
        g = (self.green_nm - 380) / (750 - 380)
        b = (self.blue_nm - 380) / (750 - 380)

        # Clamp and convert to 0-255
        r = int(max(0, min(255, r * 255)))
        g = int(max(0, min(255, g * 255)))
        b = int(max(0, min(255, b * 255)))

        return (r, g, b)

    def diameter_multiplier(self, wavelength_nm: float) -> float:
        """
        Calculate sphere diameter multiplier based on wavelength.

        Long wavelengths (red) → larger diameter mult (1.0)
        Short wavelengths (blue) → smaller diameter mult (0.64)
        """
        # Reference wavelength (red = 1.0)
        ref_wavelength = 700.0

        # Multiplier scales linearly with wavelength
        multiplier = wavelength_nm / ref_wavelength

        return multiplier


@dataclass
class Material:
    """
    Wavelength-based material properties.

    Physical properties determine how light interacts with sphere surfaces:
    - Wavelength modulation for color
    - Transparency for opacity
    - Iridescence for angle-dependent color shifts
    - Pearlescence for subsurface scattering
    - Reflectivity for mirror-like surfaces
    """
    base_diameter: float = 1.0  # Meters
    rgbt: RGBT = field(default_factory=RGBT)

    # Physical properties
    iridescence: bool = False         # Thin-film interference (oil-on-water effect)
    iridescence_strength: float = 0.5 # 0-1, how strong the color shift
    pearlescence: float = 0.0         # 0-1, subsurface scattering amount
    reflectivity: float = 0.3          # 0-1, mirror-like reflection
    index_of_refraction: float = 1.5  # IOR for Fresnel calc (glass ~1.5)

    # Glow properties (for UI elements)
    emissive: bool = False             # Self-illuminating
    glow_color: Tuple[int, int, int] = (255, 255, 255)
    glow_intensity: float = 0.0       # 0-1

    # Density (affects Raphael equation calculations)
    density: float = 1000.0           # kg/m³ (water = 1000)
    rotation_speed: float = 0.0       # rad/s (for spin in Raphael equations)

    def get_effective_diameter(self, wavelength_nm: float) -> float:
        """
        Calculate effective sphere diameter for given wavelength.

        This is the core innovation: sphere size varies with wavelength,
        creating natural color variation through geometry.
        """
        multiplier = self.rgbt.diameter_multiplier(wavelength_nm)
        return self.base_diameter * multiplier

    def get_color_at_wavelength(self, wavelength_nm: float) -> Tuple[int, int, int]:
        """Get RGB color for specific wavelength."""
        # Simplified wavelength to RGB conversion
        if 620 <= wavelength_nm <= 750:  # Red
            r = 255
            g = int(255 * (750 - wavelength_nm) / 130)
            b = 0
        elif 500 <= wavelength_nm < 620:  # Yellow/Orange/Red
            r = 255
            g = int(255 * (wavelength_nm - 500) / 120)
            b = 0
        elif 450 <= wavelength_nm < 500:  # Green/Blue
            r = 0
            g = int(255 * (500 - wavelength_nm) / 50)
            b = 255
        elif 380 <= wavelength_nm < 450:  # Blue/Violet
            r = int(128 * (450 - wavelength_nm) / 70)
            g = 0
            b = 255
        else:
            r, g, b = 128, 128, 128  # Gray fallback

        return (r, g, b)


class SpherePrimitive:
    """
    Fundamental rendering primitive - a sphere.

    Traditional graphics: thousands of triangles to approximate sphere
    LightSpeed: mathematical sphere definition (center + radius)

    Properties:
    - center: 3D position
    - radius: distance from center to surface
    - material: wavelength-based material properties

    4-6 overlapping spheres create smooth 3D objects.
    """

    def __init__(
        self,
        center: Vector3D,
        radius: float,
        material: Material,
        name: str = "sphere"
    ):
        self.center = center
        self.radius = radius
        self.material = material
        self.name = name

        # Cached values for performance
        self._cached_rgb = None
        self._cached_effective_diameters = {}

    def intersects(self, other: 'SpherePrimitive') -> bool:
        """
        Check if this sphere intersects another sphere.

        Two spheres intersect if distance between centers < sum of radii
        """
        distance = (self.center - other.center).magnitude()
        return distance < (self.radius + other.radius)

    def intersection_point(self, other: 'SpherePrimitive') -> Optional[Vector3D]:
        """
        Calculate intersection point between two spheres.

        Returns the point on the line connecting centers where surfaces meet.
        This point becomes a "surface node" for rendering.
        """
        if not self.intersects(other):
            return None

        # Vector from self to other
        direction = (other.center - self.center).normalize()

        # Distance along direction to intersection
        distance = self.radius

        # Intersection point
        intersection = self.center + Vector3D(
            direction.x * distance,
            direction.y * distance,
            direction.z * distance
        )

        return intersection

    def surface_normal(self, point: Vector3D) -> Vector3D:
        """
        Calculate surface normal at given point.

        Normal always points outward from sphere center.
        """
        normal = (point - self.center).normalize()
        return normal

    def distance_to_point(self, point: Vector3D) -> float:
        """
        Calculate distance from point to sphere surface.

        Negative = inside sphere
        Positive = outside sphere
        Zero = on surface
        """
        distance_to_center = (point - self.center).magnitude()
        distance_to_surface = distance_to_center - self.radius

        return distance_to_surface

    def ray_intersection(self, ray_origin: Vector3D, ray_direction: Vector3D) -> Optional[float]:
        """
        Calculate intersection of ray with sphere.

        Returns distance along ray to intersection point (or None if no hit).

        Math:
        Ray: P = O + tD (origin + t * direction)
        Sphere: |P - C|² = r² (points at distance r from center C)

        Substitute ray into sphere equation:
        |O + tD - C|² = r²
        (O - C + tD)·(O - C + tD) = r²

        Expand to quadratic: at² + bt + c = 0
        a = D·D
        b = 2D·(O - C)
        c = (O - C)·(O - C) - r²
        """
        # Vector from ray origin to sphere center
        oc = ray_origin - self.center

        # Quadratic coefficients
        a = ray_direction.x**2 + ray_direction.y**2 + ray_direction.z**2
        b = 2.0 * (ray_direction.x * oc.x + ray_direction.y * oc.y + ray_direction.z * oc.z)
        c = (oc.x**2 + oc.y**2 + oc.z**2) - self.radius**2

        # Discriminant
        discriminant = b**2 - 4*a*c

        if discriminant < 0:
            return None  # No intersection

        # Two solutions (entry and exit points)
        sqrt_disc = math.sqrt(discriminant)
        t1 = (-b - sqrt_disc) / (2*a)
        t2 = (-b + sqrt_disc) / (2*a)

        # Return closest positive intersection
        if t1 > 0:
            return t1
        elif t2 > 0:
            return t2
        else:
            return None  # Behind ray origin

    def get_rgb_color(self) -> Tuple[int, int, int]:
        """
        Get RGB color representation of material.

        Cached for performance.
        """
        if self._cached_rgb is None:
            self._cached_rgb = self.material.rgbt.to_rgb_tuple()

        return self._cached_rgb

    def get_effective_diameter(self, wavelength_nm: float) -> float:
        """
        Get effective diameter for wavelength (with caching).
        """
        if wavelength_nm not in self._cached_effective_diameters:
            self._cached_effective_diameters[wavelength_nm] = \
                self.material.get_effective_diameter(wavelength_nm)

        return self._cached_effective_diameters[wavelength_nm]

    def __repr__(self) -> str:
        return (f"SpherePrimitive(name='{self.name}', "
                f"center={self.center}, "
                f"radius={self.radius}, "
                f"material_rgb={self.get_rgb_color()})")


class SphereObject:
    """
    Complete 3D object composed of 4-6 overlapping spheres.

    This is the higher-level primitive users interact with.
    Each object consists of multiple SpherePrimitives arranged to
    create smooth surfaces through intersection.
    """

    def __init__(
        self,
        name: str,
        spheres: list[SpherePrimitive],
        position: Vector3D = Vector3D(0, 0, 0)
    ):
        self.name = name
        self.spheres = spheres
        self.position = position

        # Calculate central node (average of sphere centers)
        self.central_node = self._calculate_central_node()

    def _calculate_central_node(self) -> Vector3D:
        """Calculate geometric center of all spheres."""
        if not self.spheres:
            return Vector3D(0, 0, 0)

        total = Vector3D(0, 0, 0)
        for sphere in self.spheres:
            total = total + sphere.center

        count = len(self.spheres)
        return Vector3D(total.x / count, total.y / count, total.z / count)

    def get_surface_nodes(self) -> list[Vector3D]:
        """
        Get all surface intersection points.

        These are the points where sphere surfaces overlap,
        forming the visual surface of the object.
        """
        nodes = []

        for i, sphere_a in enumerate(self.spheres):
            for sphere_b in self.spheres[i+1:]:
                intersection = sphere_a.intersection_point(sphere_b)
                if intersection:
                    nodes.append(intersection)

        return nodes

    def translate(self, offset: Vector3D):
        """Move entire object by offset."""
        for sphere in self.spheres:
            sphere.center = sphere.center + offset

        self.central_node = self._calculate_central_node()
        self.position = self.position + offset

    def rotate(self, axis: Vector3D, angle_rad: float):
        """Rotate object around axis through central node."""
        # Axis-angle rotation using Rodrigues' rotation formula.
        # Rotates each sphere center around the object's central node.
        try:
            import math

            # Normalize axis
            axis_len = math.sqrt(axis.x * axis.x + axis.y * axis.y + axis.z * axis.z)
            if axis_len == 0:
                return
            k = Vector3D(axis.x / axis_len, axis.y / axis_len, axis.z / axis_len)

            cos_t = math.cos(angle_rad)
            sin_t = math.sin(angle_rad)

            def dot(a: Vector3D, b: Vector3D) -> float:
                return (a.x * b.x) + (a.y * b.y) + (a.z * b.z)

            def cross(a: Vector3D, b: Vector3D) -> Vector3D:
                return Vector3D(
                    (a.y * b.z) - (a.z * b.y),
                    (a.z * b.x) - (a.x * b.z),
                    (a.x * b.y) - (a.y * b.x),
                )

            for sphere in self.spheres:
                v = sphere.center - self.central_node
                kxv = cross(k, v)
                kdotv = dot(k, v)
                v_rot = Vector3D(
                    v.x * cos_t + kxv.x * sin_t + k.x * kdotv * (1 - cos_t),
                    v.y * cos_t + kxv.y * sin_t + k.y * kdotv * (1 - cos_t),
                    v.z * cos_t + kxv.z * sin_t + k.z * kdotv * (1 - cos_t),
                )
                sphere.center = self.central_node + v_rot

            # If the object's "position" is distinct from central node, rotate it too.
            try:
                vpos = self.position - self.central_node
                kxv = cross(k, vpos)
                kdotv = dot(k, vpos)
                vpos_rot = Vector3D(
                    vpos.x * cos_t + kxv.x * sin_t + k.x * kdotv * (1 - cos_t),
                    vpos.y * cos_t + kxv.y * sin_t + k.y * kdotv * (1 - cos_t),
                    vpos.z * cos_t + kxv.z * sin_t + k.z * kdotv * (1 - cos_t),
                )
                self.position = self.central_node + vpos_rot
            except Exception:
                pass

        finally:
            # Recompute derived node after mutation.
            self.central_node = self._calculate_central_node()

    def scale(self, factor: float):
        """Uniformly scale object."""
        for sphere in self.spheres:
            # Scale radius
            sphere.radius *= factor

            # Scale distance from central node
            offset = sphere.center - self.central_node
            sphere.center = self.central_node + Vector3D(
                offset.x * factor,
                offset.y * factor,
                offset.z * factor
            )

    def __repr__(self) -> str:
        return (f"SphereObject(name='{self.name}', "
                f"spheres={len(self.spheres)}, "
                f"position={self.position})")


# Preset constructors for common objects

def create_tetrahedron_object(
    center: Vector3D,
    size: float,
    material: Material,
    name: str = "tetrahedron"
) -> SphereObject:
    """
    Create minimal 4-sphere object (tetrahedron arrangement).

    Perfect for distant LOD or simple objects.
    """
    # Tetrahedron vertices
    vertices = [
        Vector3D(0, 1, 0),                      # Top
        Vector3D(0.943, -0.333, 0),             # Base 1
        Vector3D(-0.471, -0.333, 0.816),        # Base 2
        Vector3D(-0.471, -0.333, -0.816),       # Base 3
    ]

    spheres = []
    for i, vertex in enumerate(vertices):
        sphere_center = center + Vector3D(
            vertex.x * size,
            vertex.y * size,
            vertex.z * size
        )
        spheres.append(SpherePrimitive(
            center=sphere_center,
            radius=size * 0.6,  # Overlap factor
            material=material,
            name=f"{name}_sphere{i}"
        ))

    return SphereObject(name=name, spheres=spheres, position=center)


def create_octahedron_object(
    center: Vector3D,
    size: float,
    material: Material,
    name: str = "octahedron"
) -> SphereObject:
    """
    Create standard 6-sphere object (octahedron arrangement).

    Recommended for most objects - smooth from all angles.
    """
    # Octahedron vertices (6 directions)
    vertices = [
        Vector3D(0, 1, 0),   # Top
        Vector3D(0, -1, 0),  # Bottom
        Vector3D(1, 0, 0),   # Right
        Vector3D(-1, 0, 0),  # Left
        Vector3D(0, 0, 1),   # Front
        Vector3D(0, 0, -1),  # Back
    ]

    spheres = []
    for i, vertex in enumerate(vertices):
        sphere_center = center + Vector3D(
            vertex.x * size,
            vertex.y * size,
            vertex.z * size
        )
        spheres.append(SpherePrimitive(
            center=sphere_center,
            radius=size * 0.7,  # Larger overlap for smoother surface
            material=material,
            name=f"{name}_sphere{i}"
        ))

    return SphereObject(name=name, spheres=spheres, position=center)
