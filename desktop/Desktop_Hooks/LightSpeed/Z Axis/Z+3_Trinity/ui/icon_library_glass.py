"""
Icon Library System with Glass Materials - v5.1.2
Comprehensive icon management with depth, size, material properties

Features:
- SVG-based icon system
- Material properties (glass, metal, plastic)
- Depth-based rendering
- Size variants (16, 24, 32, 48, 64, 128, 256px)
- Theme-aware color substitution
- Lazy loading and caching
- Romer Industries / EMASSC icon sets

Author: LightSpeed Team / Romer Industries
Date: April 8, 2026
"""

import tkinter as tk
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from PIL import Image, ImageDraw, ImageTk, ImageFilter
import io


# ==============================================================================
# Icon Categories
# ==============================================================================

class IconCategory(Enum):
    """Icon categories for organization"""
    DOCUMENTS = "documents"
    TOOLS = "tools"
    SYSTEM = "system"
    AI = "ai"
    DATA = "data"
    NAVIGATION = "navigation"
    STATUS = "status"
    ACTIONS = "actions"
    FILES = "files"
    WORKSPACE = "workspace"


# ==============================================================================
# Icon Material Types
# ==============================================================================

class IconMaterial(Enum):
    """Material types for icon rendering"""
    GLASS = "glass"
    METAL = "metal"
    PLASTIC = "plastic"
    NEON = "neon"
    HOLOGRAM = "hologram"


# ==============================================================================
# Icon Definition
# ==============================================================================

@dataclass
class IconDefinition:
    """
    Complete icon definition with all properties

    Attributes:
        icon_id: Unique identifier (e.g., "document_pdf")
        category: Icon category
        base_svg: Path to base SVG file
        sizes: Available sizes in pixels
        material: Rendering material
        depth: Z-depth (0.0-1.0, lower = closer)
        glow: Enable glow effect
        glow_color: Glow color (hex)
        theme_colors: Color substitutions per theme
        metadata: Additional properties
    """
    icon_id: str
    category: IconCategory
    base_svg: Optional[Path] = None
    sizes: List[int] = field(default_factory=lambda: [16, 24, 32, 48, 64])
    material: IconMaterial = IconMaterial.GLASS
    depth: float = 0.8
    glow: bool = False
    glow_color: str = "#4dd0e1"
    theme_colors: Dict[str, Dict[str, str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'icon_id': self.icon_id,
            'category': self.category.value,
            'base_svg': str(self.base_svg) if self.base_svg else None,
            'sizes': self.sizes,
            'material': self.material.value,
            'depth': self.depth,
            'glow': self.glow,
            'glow_color': self.glow_color,
            'theme_colors': self.theme_colors,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IconDefinition':
        """Create from dictionary"""
        return cls(
            icon_id=data['icon_id'],
            category=IconCategory(data['category']),
            base_svg=Path(data['base_svg']) if data.get('base_svg') else None,
            sizes=data.get('sizes', [16, 24, 32, 48, 64]),
            material=IconMaterial(data.get('material', 'glass')),
            depth=data.get('depth', 0.8),
            glow=data.get('glow', False),
            glow_color=data.get('glow_color', '#4dd0e1'),
            theme_colors=data.get('theme_colors', {}),
            metadata=data.get('metadata', {})
        )


# ==============================================================================
# Icon Library Manager
# ==============================================================================

class IconLibraryManager:
    """
    Central icon library manager

    Handles:
    - Icon loading and caching
    - Material rendering
    - Size generation
    - Theme application
    - Lazy loading
    """

    def __init__(self, assets_path: Optional[Path] = None):
        """
        Initialize icon library

        Args:
            assets_path: Path to assets directory
        """
        self.assets_path = assets_path or Path(__file__).parents[2] / "assets" / "icons"
        self.icons: Dict[str, IconDefinition] = {}
        self.cache: Dict[Tuple[str, int, str], ImageTk.PhotoImage] = {}
        self.current_theme = "romer"

        # Create default assets path if doesn't exist
        self.assets_path.mkdir(parents=True, exist_ok=True)

        # Load icon manifest
        self._load_manifest()

        # Create default icons if manifest empty
        if not self.icons:
            self._create_default_icons()

    def _load_manifest(self):
        """Load icon manifest from JSON"""
        manifest_path = self.assets_path / "icon_manifest.json"

        if manifest_path.exists():
            try:
                data = json.loads(manifest_path.read_text(encoding='utf-8'))

                for icon_data in data.get('icons', []):
                    icon = IconDefinition.from_dict(icon_data)
                    self.icons[icon.icon_id] = icon

            except Exception as e:
                print(f"Failed to load icon manifest: {e}")

    def _create_default_icons(self):
        """Create default icon set programmatically"""
        # Document icons
        self.register_icon(IconDefinition(
            icon_id="document_pdf",
            category=IconCategory.DOCUMENTS,
            material=IconMaterial.GLASS,
            glow=True,
            glow_color="#ff0000",
            theme_colors={
                'romer': {'primary': '#ff0000', 'secondary': '#ffffff'},
                'emassc': {'primary': '#ff6b9d', 'secondary': '#ffffff'}
            },
            metadata={'file_extension': '.pdf', 'mime_type': 'application/pdf'}
        ))

        self.register_icon(IconDefinition(
            icon_id="document_text",
            category=IconCategory.DOCUMENTS,
            material=IconMaterial.GLASS,
            theme_colors={
                'romer': {'primary': '#4dd0e1', 'secondary': '#ffffff'},
                'emassc': {'primary': '#ff6b9d', 'secondary': '#ffffff'}
            },
            metadata={'file_extensions': ['.txt', '.md'], 'mime_type': 'text/plain'}
        ))

        # Code file icons
        self.register_icon(IconDefinition(
            icon_id="code_python",
            category=IconCategory.FILES,
            material=IconMaterial.NEON,
            glow=True,
            glow_color="#3776ab",
            theme_colors={
                'romer': {'primary': '#3776ab', 'secondary': '#ffd343'},
            },
            metadata={'file_extension': '.py', 'language': 'Python'}
        ))

        self.register_icon(IconDefinition(
            icon_id="code_javascript",
            category=IconCategory.FILES,
            material=IconMaterial.NEON,
            glow=True,
            glow_color="#f7df1e",
            theme_colors={
                'romer': {'primary': '#f7df1e', 'secondary': '#000000'},
            },
            metadata={'file_extension': '.js', 'language': 'JavaScript'}
        ))

        # System icons
        self.register_icon(IconDefinition(
            icon_id="system_settings",
            category=IconCategory.SYSTEM,
            material=IconMaterial.METAL,
            theme_colors={
                'romer': {'primary': '#90caf9', 'secondary': '#ffffff'},
            }
        ))

        self.register_icon(IconDefinition(
            icon_id="system_health",
            category=IconCategory.STATUS,
            material=IconMaterial.GLASS,
            glow=True,
            glow_color="#66bb6a",
            theme_colors={
                'romer': {'primary': '#66bb6a', 'secondary': '#ffffff'},
            }
        ))

        # AI icons
        self.register_icon(IconDefinition(
            icon_id="ai_neo",
            category=IconCategory.AI,
            material=IconMaterial.HOLOGRAM,
            glow=True,
            glow_color="#4dd0e1",
            theme_colors={
                'romer': {'primary': '#4dd0e1', 'secondary': '#ffa726'},
            }
        ))

        # Tool icons
        self.register_icon(IconDefinition(
            icon_id="tool_workspace",
            category=IconCategory.WORKSPACE,
            material=IconMaterial.GLASS,
            theme_colors={
                'romer': {'primary': '#4caf50', 'secondary': '#ffffff'},
            }
        ))

        # Save manifest
        self.save_manifest()

    def register_icon(self, icon: IconDefinition):
        """Register an icon in the library"""
        self.icons[icon.icon_id] = icon

    def get_icon(
        self,
        icon_id: str,
        size: int = 32,
        theme: Optional[str] = None
    ) -> Optional[ImageTk.PhotoImage]:
        """
        Get icon image

        Args:
            icon_id: Icon identifier
            size: Size in pixels
            theme: Theme name (None = current theme)

        Returns:
            PhotoImage or None if not found
        """
        theme = theme or self.current_theme

        # Check cache
        cache_key = (icon_id, size, theme)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Get icon definition
        if icon_id not in self.icons:
            return None

        icon_def = self.icons[icon_id]

        # Generate icon image
        image = self._generate_icon(icon_def, size, theme)

        if image:
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)

            # Cache
            self.cache[cache_key] = photo

            return photo

        return None

    def _generate_icon(
        self,
        icon_def: IconDefinition,
        size: int,
        theme: str
    ) -> Optional[Image.Image]:
        """
        Generate icon image with material effects

        Args:
            icon_def: Icon definition
            size: Icon size
            theme: Theme name

        Returns:
            PIL Image or None
        """
        # If SVG exists, render it
        if icon_def.base_svg and icon_def.base_svg.exists():
            return self._render_svg(icon_def.base_svg, size, icon_def, theme)

        # Otherwise, generate programmatically
        return self._generate_programmatic_icon(icon_def, size, theme)

    def _render_svg(
        self,
        svg_path: Path,
        size: int,
        icon_def: IconDefinition,
        theme: str
    ) -> Optional[Image.Image]:
        """Render SVG to image (requires cairosvg or similar)"""
        # In production, would use cairosvg or svglib
        # For now, return programmatic fallback
        return self._generate_programmatic_icon(icon_def, size, theme)

    def _generate_programmatic_icon(
        self,
        icon_def: IconDefinition,
        size: int,
        theme: str
    ) -> Image.Image:
        """Generate icon programmatically based on material and properties"""
        # Create image with alpha channel
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Get theme colors
        colors = icon_def.theme_colors.get(theme, {
            'primary': '#4dd0e1',
            'secondary': '#ffffff'
        })

        primary = colors['primary']
        secondary = colors.get('secondary', '#ffffff')

        # Draw based on material
        if icon_def.material == IconMaterial.GLASS:
            self._draw_glass_icon(draw, size, primary, secondary)

        elif icon_def.material == IconMaterial.METAL:
            self._draw_metal_icon(draw, size, primary, secondary)

        elif icon_def.material == IconMaterial.NEON:
            self._draw_neon_icon(draw, size, primary, secondary)

        elif icon_def.material == IconMaterial.HOLOGRAM:
            self._draw_hologram_icon(draw, size, primary, secondary)

        else:  # PLASTIC
            self._draw_plastic_icon(draw, size, primary, secondary)

        # Add glow if enabled
        if icon_def.glow:
            image = self._add_glow(image, icon_def.glow_color)

        return image

    def _draw_glass_icon(self, draw: ImageDraw.Draw, size: int, primary: str, secondary: str):
        """Draw glass-style icon"""
        margin = size * 0.1
        inner_size = size - 2 * margin

        # Outer glass shape (rounded square)
        draw.rounded_rectangle(
            [(margin, margin), (size - margin, size - margin)],
            radius=size * 0.15,
            fill=self._hex_to_rgba(primary, 0.3),
            outline=self._hex_to_rgba(secondary, 0.6),
            width=max(2, size // 16)
        )

        # Inner highlight
        highlight_margin = margin + size * 0.05
        draw.rounded_rectangle(
            [(highlight_margin, highlight_margin), (size * 0.6, size * 0.4)],
            radius=size * 0.1,
            fill=self._hex_to_rgba(secondary, 0.2)
        )

    def _draw_metal_icon(self, draw: ImageDraw.Draw, size: int, primary: str, secondary: str):
        """Draw metallic-style icon"""
        margin = size * 0.1

        # Metal circle
        draw.ellipse(
            [(margin, margin), (size - margin, size - margin)],
            fill=self._hex_to_rgba(primary, 0.8),
            outline=self._hex_to_rgba(secondary, 1.0),
            width=max(2, size // 12)
        )

        # Reflection gradient (simulated)
        for i in range(5):
            alpha = 0.3 - i * 0.05
            offset = margin + i * (size * 0.05)
            draw.ellipse(
                [(offset, offset), (size * 0.5, size * 0.5)],
                fill=self._hex_to_rgba(secondary, alpha)
            )

    def _draw_neon_icon(self, draw: ImageDraw.Draw, size: int, primary: str, secondary: str):
        """Draw neon-style icon"""
        margin = size * 0.15
        center = size / 2

        # Neon glow layers
        for i in range(3, 0, -1):
            alpha = 0.3 * (i / 3)
            radius = size * 0.35 * (1 + i * 0.1)

            draw.ellipse(
                [(center - radius, center - radius),
                 (center + radius, center + radius)],
                fill=self._hex_to_rgba(primary, alpha)
            )

        # Bright center
        draw.ellipse(
            [(center - size * 0.15, center - size * 0.15),
             (center + size * 0.15, center + size * 0.15)],
            fill=self._hex_to_rgba(primary, 1.0)
        )

    def _draw_hologram_icon(self, draw: ImageDraw.Draw, size: int, primary: str, secondary: str):
        """Draw hologram-style icon"""
        center = size / 2
        margin = size * 0.1

        # Hologram lines
        for i in range(5):
            y = margin + i * (size - 2 * margin) / 4
            alpha = 0.4 + (i % 2) * 0.2

            draw.line(
                [(margin, y), (size - margin, y)],
                fill=self._hex_to_rgba(primary, alpha),
                width=max(2, size // 20)
            )

        # Central diamond
        diamond_size = size * 0.3
        points = [
            (center, center - diamond_size),  # Top
            (center + diamond_size, center),  # Right
            (center, center + diamond_size),  # Bottom
            (center - diamond_size, center),  # Left
        ]

        draw.polygon(points, fill=self._hex_to_rgba(secondary, 0.5), outline=primary)

    def _draw_plastic_icon(self, draw: ImageDraw.Draw, size: int, primary: str, secondary: str):
        """Draw plastic-style icon"""
        margin = size * 0.1

        # Solid color shape
        draw.rounded_rectangle(
            [(margin, margin), (size - margin, size - margin)],
            radius=size * 0.2,
            fill=self._hex_to_rgba(primary, 0.9),
            outline=self._hex_to_rgba(secondary, 0.5),
            width=max(1, size // 20)
        )

    def _add_glow(self, image: Image.Image, glow_color: str) -> Image.Image:
        """Add glow effect to icon"""
        # Create glow layer
        glow = image.copy()
        glow = glow.filter(ImageFilter.GaussianBlur(radius=5))

        # Composite
        result = Image.alpha_composite(glow, image)

        return result

    def _hex_to_rgba(self, hex_color: str, alpha: float = 1.0) -> Tuple[int, int, int, int]:
        """Convert hex color to RGBA tuple"""
        hex_color = hex_color.lstrip('#')

        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        a = int(alpha * 255)

        return (r, g, b, a)

    def save_manifest(self):
        """Save icon manifest to JSON"""
        manifest_path = self.assets_path / "icon_manifest.json"

        manifest_data = {
            'version': '1.0.0',
            'theme': self.current_theme,
            'icons': [icon.to_dict() for icon in self.icons.values()]
        }

        manifest_path.write_text(
            json.dumps(manifest_data, indent=2),
            encoding='utf-8'
        )

    def get_icon_by_extension(self, file_extension: str, size: int = 32) -> Optional[ImageTk.PhotoImage]:
        """Get icon for file extension"""
        # Map extensions to icon IDs
        extension_map = {
            '.pdf': 'document_pdf',
            '.txt': 'document_text',
            '.md': 'document_text',
            '.py': 'code_python',
            '.js': 'code_javascript',
            '.json': 'code_javascript',
        }

        icon_id = extension_map.get(file_extension.lower())

        if icon_id:
            return self.get_icon(icon_id, size)

        # Return generic document icon
        return self.get_icon('document_text', size)


# ==============================================================================
# Factory Function
# ==============================================================================

def create_icon_library(assets_path: Optional[Path] = None) -> IconLibraryManager:
    """
    Create icon library manager

    Args:
        assets_path: Path to assets directory

    Returns:
        IconLibraryManager instance
    """
    return IconLibraryManager(assets_path)


# ==============================================================================
# Standalone Test
# ==============================================================================

if __name__ == '__main__':
    root = tk.Tk()
    root.title("Icon Library Test")
    root.geometry("800x600")
    root.configure(bg='#0a1929')

    # Create icon library
    library = create_icon_library()

    # Display grid
    frame = tk.Frame(root, bg='#0a1929')
    frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Show all icons
    row = 0
    col = 0

    for icon_id in library.icons.keys():
        # Label
        label_frame = tk.Frame(frame, bg='#1e3a5a', relief=tk.RAISED, bd=2)
        label_frame.grid(row=row, column=col, padx=10, pady=10)

        # Icon
        icon = library.get_icon(icon_id, size=48)
        if icon:
            icon_label = tk.Label(label_frame, image=icon, bg='#1e3a5a')
            icon_label.image = icon  # Keep reference
            icon_label.pack(padx=10, pady=10)

        # Name
        name_label = tk.Label(
            label_frame,
            text=icon_id.replace('_', ' ').title(),
            font=('Segoe UI', 9),
            bg='#1e3a5a',
            fg='#ffffff'
        )
        name_label.pack(pady=5)

        col += 1
        if col >= 4:
            col = 0
            row += 1

    root.mainloop()
