"""
LightSpeed Platform - Rendering Module
Triangle-based component rendering with vertex circles
"""

from .triangle_renderer import TriangleRenderer, Material
from .geometry import Triangle, Circle, calculate_triangle_vertices
from .materials import create_material_from_metadata
from .immersive_3d_interface import ImmersiveViewer3D, Scene3D, Camera, Vector3

__all__ = [
    'TriangleRenderer',
    'Material',
    'Triangle',
    'Circle',
    'calculate_triangle_vertices',
    'create_material_from_metadata',
    'ImmersiveViewer3D',
    'Scene3D',
    'Camera',
    'Vector3',
]
