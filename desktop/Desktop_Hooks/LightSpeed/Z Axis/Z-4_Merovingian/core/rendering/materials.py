"""
Material Properties for Triangle Rendering
Handles color, brightness, reflectivity, and opacity
"""

from dataclasses import dataclass
from typing import Tuple, Dict, Any


@dataclass
class Material:
    """Material properties for rendering components."""

    color: str  # Hex color code (e.g., "#8B0000")
    brightness: float  # 0.0 to 1.0
    reflectivity: float  # 0.0 to 1.0
    opacity: float  # 0.0 to 1.0

    def to_rgb(self) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = self.color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def to_rgba(self) -> Tuple[int, int, int, int]:
        """Convert hex color to RGBA tuple with opacity."""
        r, g, b = self.to_rgb()
        alpha = int(self.opacity * 255)
        return (r, g, b, alpha)

    def apply_brightness(self) -> Tuple[int, int, int]:
        """Apply brightness adjustment to RGB color."""
        r, g, b = self.to_rgb()
        return (
            int(r * self.brightness),
            int(g * self.brightness),
            int(b * self.brightness)
        )

    def to_tkinter_color(self) -> str:
        """Convert to Tkinter-compatible color string."""
        if self.brightness != 1.0:
            r, g, b = self.apply_brightness()
            return f'#{r:02x}{g:02x}{b:02x}'
        return self.color


def create_material_from_metadata(metadata: Dict[str, Any]) -> Material:
    """Create Material from component metadata dictionary.

    Args:
        metadata: Component metadata containing color, brightness, reflectivity, opacity

    Returns:
        Material object ready for rendering
    """
    return Material(
        color=metadata.get('color', '#FFFFFF'),
        brightness=metadata.get('brightness', 1.0),
        reflectivity=metadata.get('reflectivity', 0.5),
        opacity=metadata.get('opacity', 1.0)
    )


def interpolate_materials(mat1: Material, mat2: Material, t: float) -> Material:
    """Interpolate between two materials for animations.

    Args:
        mat1: Starting material
        mat2: Ending material
        t: Interpolation factor (0.0 to 1.0)

    Returns:
        Interpolated material
    """
    # Interpolate RGB colors
    r1, g1, b1 = mat1.to_rgb()
    r2, g2, b2 = mat2.to_rgb()

    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)

    return Material(
        color=f'#{r:02x}{g:02x}{b:02x}',
        brightness=mat1.brightness + (mat2.brightness - mat1.brightness) * t,
        reflectivity=mat1.reflectivity + (mat2.reflectivity - mat1.reflectivity) * t,
        opacity=mat1.opacity + (mat2.opacity - mat1.opacity) * t
    )
