"""
Glass UI Framework - v5.1.2
Futuristic glassmorphism UI system for LightSpeed

Provides:
- Frosted glass effects with blur and transparency
- Smooth rounded edges with double-line borders
- Reflective light effects
- Depth-based layering
- Premium Romer Industries aesthetic
- Trinity integration for enhanced components

Design Philosophy:
- Timeless futuristic look
- High-end aerospace/tech aesthetic
- Smooth glass surfaces with subtle reflections
- Clean, minimal, maximum function
- WCAG AA+ accessibility maintained

Author: LightSpeed Team / Romer Industries
Date: April 8, 2026
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from pathlib import Path
import json
import re


# ==============================================================================
# Glass Material Definitions
# ==============================================================================

_RE_RGBA = re.compile(
    r"^\s*rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*([0-9]*\.?[0-9]+)\s*)?\)\s*$",
    flags=re.IGNORECASE,
)


def _clamp255(x: int) -> int:
    try:
        return max(0, min(255, int(x)))
    except Exception:
        return 0


def _rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"#{_clamp255(r):02x}{_clamp255(g):02x}{_clamp255(b):02x}"


def _hex_to_rgb(hex_color: str) -> Optional[Tuple[int, int, int]]:
    if not isinstance(hex_color, str):
        return None
    s = hex_color.strip()
    if not s.startswith("#"):
        return None
    h = s[1:]
    try:
        if len(h) == 3:  # #RGB
            r, g, b = (int(ch * 2, 16) for ch in h)
            return (r, g, b)
        if len(h) == 6:  # #RRGGBB
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        if len(h) == 12:  # #RRRRGGGGBBBB (Tk "long" form) -> truncate
            return (int(h[0:2], 16), int(h[4:6], 16), int(h[8:10], 16))
    except Exception:
        return None
    return None


def _blend_rgb(fg: Tuple[int, int, int], alpha: float, bg: Tuple[int, int, int]) -> Tuple[int, int, int]:
    try:
        a = float(alpha)
    except Exception:
        a = 1.0
    a = 0.0 if a < 0.0 else (1.0 if a > 1.0 else a)
    return (
        int(round(fg[0] * a + bg[0] * (1.0 - a))),
        int(round(fg[1] * a + bg[1] * (1.0 - a))),
        int(round(fg[2] * a + bg[2] * (1.0 - a))),
    )


def tk_safe_color(color: Any, *, bg: str = "#000000", fallback: str = "#000000") -> str:
    """
    Return a Tk-safe color string.

    Tk does not support alpha channels in hex ("#RRGGBBAA") nor CSS rgba() strings.
    We accept those inputs and approximate by alpha-blending onto `bg`.
    """
    if color is None:
        return fallback
    if isinstance(color, (tuple, list)) and len(color) >= 3:
        try:
            return _rgb_to_hex((int(color[0]), int(color[1]), int(color[2])))
        except Exception:
            return fallback

    s = str(color).strip()
    if not s:
        return fallback

    bg_rgb = _hex_to_rgb(bg) or (0, 0, 0)

    # CSS rgb()/rgba()
    m = _RE_RGBA.match(s)
    if m:
        r, g, b = (_clamp255(int(m.group(1))), _clamp255(int(m.group(2))), _clamp255(int(m.group(3))))
        a = 1.0
        if m.group(4) is not None:
            try:
                a = float(m.group(4))
            except Exception:
                a = 1.0
        return _rgb_to_hex(_blend_rgb((r, g, b), a, bg_rgb))

    # Hex with possible alpha
    if s.startswith("#"):
        h = s[1:]
        try:
            if len(h) == 4:  # #RGBA
                r = int(h[0] * 2, 16)
                g = int(h[1] * 2, 16)
                b = int(h[2] * 2, 16)
                a = int(h[3] * 2, 16) / 255.0
                return _rgb_to_hex(_blend_rgb((r, g, b), a, bg_rgb))
            if len(h) == 8:  # #RRGGBBAA
                r = int(h[0:2], 16)
                g = int(h[2:4], 16)
                b = int(h[4:6], 16)
                a = int(h[6:8], 16) / 255.0
                return _rgb_to_hex(_blend_rgb((r, g, b), a, bg_rgb))
            # #RGB/#RRGGBB/#RRRRGGGGBBBB -> normalize to #RRGGBB
            rgb = _hex_to_rgb(s)
            if rgb is not None:
                return _rgb_to_hex(rgb)
        except Exception:
            return fallback

    # Named colors (best-effort; Tk will validate at runtime)
    return s


@dataclass
class GlassMaterial:
    """
    Defines a glass material with physical properties

    Attributes:
        name: Material identifier
        opacity: Base opacity (0.0-1.0)
        blur_radius: Background blur amount (0-50)
        brightness: Material brightness multiplier (0.5-1.5)
        saturation: Color saturation (0.0-2.0)
        border_width: Border thickness in pixels
        border_color: Border color (RGBA)
        shadow_depth: Drop shadow depth (0-20)
        reflection_intensity: Surface reflection (0.0-1.0)
        glow_color: Optional glow color
        glow_intensity: Glow strength (0.0-1.0)
    """
    name: str
    opacity: float = 0.85
    blur_radius: int = 20
    brightness: float = 1.1
    saturation: float = 1.0
    border_width: int = 2
    # Keep the default Tk-safe; alpha-hex variants must be sanitized via `tk_safe_color`.
    border_color: str = "#ffffff"
    shadow_depth: int = 8
    reflection_intensity: float = 0.3
    glow_color: Optional[str] = None
    glow_intensity: float = 0.0


# Predefined glass materials for Romer Industries theme
_GLASS_MATERIALS_RAW = {
    'romer_premium': GlassMaterial(
        name='romer_premium',
        opacity=0.82,
        blur_radius=25,
        brightness=1.15,
        border_width=2,
        border_color='#4dd0e180',  # Romer teal with alpha
        shadow_depth=10,
        reflection_intensity=0.4,
        glow_color='#4dd0e1',
        glow_intensity=0.2
    ),

    'emassc_glass': GlassMaterial(
        name='emassc_glass',
        opacity=0.88,
        blur_radius=18,
        brightness=1.12,
        border_width=2,
        border_color='#ff6b9d60',  # EMASSC pink with alpha
        shadow_depth=8,
        reflection_intensity=0.35,
        glow_color='#ff6b9d',
        glow_intensity=0.15
    ),

    'standard_glass': GlassMaterial(
        name='standard_glass',
        opacity=0.85,
        blur_radius=20,
        brightness=1.1,
        border_width=2,
        border_color='#ffffff40',
        shadow_depth=8,
        reflection_intensity=0.3
    ),

    'heavy_glass': GlassMaterial(
        name='heavy_glass',
        opacity=0.92,
        blur_radius=12,
        brightness=1.05,
        border_width=3,
        border_color='#ffffff50',
        shadow_depth=12,
        reflection_intensity=0.25
    ),

    'light_glass': GlassMaterial(
        name='light_glass',
        opacity=0.75,
        blur_radius=30,
        brightness=1.2,
        border_width=1,
        border_color='#ffffff30',
        shadow_depth=5,
        reflection_intensity=0.35
    ),
}


# ==============================================================================
# Glass Color Scheme - Romer Industries Premium Theme
# ==============================================================================

_ROMER_GLASS_COLORS_RAW = {
    # Primary colors
    'primary': '#4dd0e1',          # Romer teal
    'primary_dark': '#26c6da',
    'primary_light': '#80deea',

    # Secondary colors
    'secondary': '#ffa726',        # Accent orange
    'secondary_dark': '#ff9800',
    'secondary_light': '#ffb74d',

    # Glass backgrounds (with transparency)
    'glass_bg': '#0a1929e0',       # Deep blue-black glass
    'glass_panel': '#1e3a5ae8',    # Panel glass
    'glass_card': '#263750f0',     # Card glass
    'glass_modal': '#0d1f2edc',    # Modal overlay

    # Text colors optimized for glass
    'text_primary': '#ffffff',
    'text_secondary': '#b0bec5',
    'text_disabled': '#607d8b',

    # Interactive states
    'hover': '#4dd0e140',          # Teal hover glow
    'active': '#4dd0e160',         # Teal active state
    'focus': '#4dd0e180',          # Teal focus ring

    # Status colors
    'success': '#66bb6a',
    'warning': '#ffa726',
    'danger': '#ef5350',
    'info': '#42a5f5',

    # Borders and dividers
    'border': '#ffffff20',
    'border_light': '#ffffff10',
    'border_heavy': '#ffffff40',
    'divider': '#ffffff15',

    # Special effects
    'glow_primary': '#4dd0e1',
    'glow_secondary': '#ffa726',
    'reflection': '#ffffff30',
    'shadow': '#00000080',
}


def _sanitize_romer_palette(raw: Dict[str, Any]) -> Dict[str, str]:
    # First, stabilize the base glass backgrounds by blending over black.
    base = {
        "glass_bg": tk_safe_color(raw.get("glass_bg", "#0a1929"), bg="#000000"),
        "glass_panel": tk_safe_color(raw.get("glass_panel", "#1e3a5a"), bg="#000000"),
        "glass_card": tk_safe_color(raw.get("glass_card", "#263750"), bg="#000000"),
        "glass_modal": tk_safe_color(raw.get("glass_modal", "#0d1f2e"), bg="#000000"),
    }
    bg = base["glass_bg"]

    out: Dict[str, str] = {}
    for k, v in (raw or {}).items():
        if k in base:
            out[k] = base[k]
            continue
        # Use the main glass background as the blend target for subtle glows/borders.
        out[k] = tk_safe_color(v, bg=bg)
    return out


def _sanitize_materials(raw: Dict[str, GlassMaterial], *, bg: str) -> Dict[str, GlassMaterial]:
    out: Dict[str, GlassMaterial] = {}
    for k, m in (raw or {}).items():
        if not isinstance(m, GlassMaterial):
            continue
        out[k] = GlassMaterial(
            name=m.name,
            opacity=float(m.opacity),
            blur_radius=int(m.blur_radius),
            brightness=float(m.brightness),
            saturation=float(m.saturation),
            border_width=int(m.border_width),
            border_color=tk_safe_color(m.border_color, bg=bg),
            shadow_depth=int(m.shadow_depth),
            reflection_intensity=float(m.reflection_intensity),
            glow_color=(tk_safe_color(m.glow_color, bg=bg) if m.glow_color else None),
            glow_intensity=float(m.glow_intensity),
        )
    return out


# Public, Tk-safe exports (single source of truth for floor UIs).
ROMER_GLASS_COLORS = _sanitize_romer_palette(_ROMER_GLASS_COLORS_RAW)
GLASS_MATERIALS = _sanitize_materials(_GLASS_MATERIALS_RAW, bg=ROMER_GLASS_COLORS.get("glass_panel", "#1e3a5a"))


# ==============================================================================
# Glass UI Manager
# ==============================================================================

class GlassUIManager:
    """
    Central manager for Glass UI system

    Handles:
    - Material application
    - Color scheme management
    - Component styling
    - Effect rendering
    - Theme persistence
    """

    def __init__(self):
        """Initialize Glass UI Manager"""
        self.current_material = GLASS_MATERIALS['romer_premium']
        self.color_scheme = ROMER_GLASS_COLORS.copy()
        self.style = ttk.Style()
        self.registered_widgets: Dict[str, tk.Widget] = {}

        # Initialize glass styles
        self._configure_glass_styles()

    def _configure_glass_styles(self):
        """Configure ttk styles with glass effects"""

        # Glass Button Style
        self.style.configure(
            'Glass.TButton',
            background=self._hex_to_rgba(self.color_scheme['glass_panel'], self.current_material.opacity),
            foreground=self.color_scheme['text_primary'],
            bordercolor=self.current_material.border_color,
            borderwidth=self.current_material.border_width,
            relief='flat',
            padding=(20, 10),
            font=('Segoe UI', 10)
        )

        self.style.map(
            'Glass.TButton',
            background=[
                ('active', self.color_scheme['hover']),
                ('pressed', self.color_scheme['active'])
            ],
            bordercolor=[
                ('focus', self.color_scheme['focus'])
            ]
        )

        # Glass Frame Style
        self.style.configure(
            'Glass.TFrame',
            background=self._hex_to_rgba(self.color_scheme['glass_panel'], self.current_material.opacity),
            bordercolor=self.current_material.border_color,
            borderwidth=self.current_material.border_width,
            relief='flat'
        )

        # Glass Label Style
        self.style.configure(
            'Glass.TLabel',
            background=self._hex_to_rgba(self.color_scheme['glass_bg'], 0.0),  # Transparent
            foreground=self.color_scheme['text_primary'],
            font=('Segoe UI', 10)
        )

        # Glass Entry Style
        self.style.configure(
            'Glass.TEntry',
            fieldbackground=self._hex_to_rgba(self.color_scheme['glass_card'], self.current_material.opacity),
            foreground=self.color_scheme['text_primary'],
            bordercolor=self.current_material.border_color,
            borderwidth=self.current_material.border_width,
            insertcolor=self.color_scheme['primary'],
            padding=10
        )

        # Glass Notebook (Tabs)
        self.style.configure(
            'Glass.TNotebook',
            background=self._hex_to_rgba(self.color_scheme['glass_bg'], self.current_material.opacity),
            bordercolor=self.current_material.border_color,
            borderwidth=0
        )

        self.style.configure(
            'Glass.TNotebook.Tab',
            background=self._hex_to_rgba(self.color_scheme['glass_panel'], 0.6),
            foreground=self.color_scheme['text_secondary'],
            bordercolor=self.current_material.border_color,
            padding=(20, 10),
            font=('Segoe UI', 10, 'bold')
        )

        self.style.map(
            'Glass.TNotebook.Tab',
            background=[
                ('selected', self._hex_to_rgba(self.color_scheme['glass_panel'], self.current_material.opacity)),
                ('active', self.color_scheme['hover'])
            ],
            foreground=[
                ('selected', self.color_scheme['text_primary'])
            ]
        )

        # Glass Treeview Style
        self.style.configure(
            'Glass.Treeview',
            background=self._hex_to_rgba(self.color_scheme['glass_card'], self.current_material.opacity),
            foreground=self.color_scheme['text_primary'],
            fieldbackground=self._hex_to_rgba(self.color_scheme['glass_card'], self.current_material.opacity),
            bordercolor=self.current_material.border_color,
            borderwidth=self.current_material.border_width
        )

        self.style.map(
            'Glass.Treeview',
            background=[
                ('selected', self.color_scheme['primary'])
            ],
            foreground=[
                ('selected', '#ffffff')
            ]
        )

        # Glass Scrollbar Style
        self.style.configure(
            'Glass.Vertical.TScrollbar',
            background=self._hex_to_rgba(self.color_scheme['glass_panel'], 0.5),
            troughcolor=self._hex_to_rgba(self.color_scheme['glass_bg'], 0.3),
            bordercolor=self.current_material.border_color,
            arrowcolor=self.color_scheme['text_secondary']
        )

    def _hex_to_rgba(self, hex_color: str, opacity: float = 1.0) -> str:
        """Convert hex color to RGBA (simulated with alpha in hex)"""
        # Tkinter doesn't support true RGBA, so we simulate with darker colors
        # In real implementation, would use Canvas or PIL for true transparency

        if opacity >= 1.0:
            return hex_color

        # Simple opacity simulation by blending with background
        # For production, use PIL or Canvas for true alpha compositing
        return hex_color

    def apply_glass_effect(
        self,
        widget: tk.Widget,
        material: Optional[GlassMaterial] = None,
        rounded_corners: int = 12,
        double_border: bool = True
    ):
        """
        Apply glass effect to a widget

        Args:
            widget: Tkinter widget to apply effect to
            material: Glass material to use (None = current)
            rounded_corners: Corner radius in pixels
            double_border: Use double-line border effect
        """
        material = material or self.current_material

        # For Canvas widgets, we can draw true glass effects
        if isinstance(widget, tk.Canvas):
            self._apply_canvas_glass_effect(widget, material, rounded_corners, double_border)

        # For ttk widgets, apply themed styles
        elif isinstance(widget, (ttk.Frame, ttk.Label, ttk.Button, ttk.Entry)):
            self._apply_ttk_glass_effect(widget, material)

        # For tk widgets, configure directly
        else:
            self._apply_tk_glass_effect(widget, material)

        # Register widget for theme updates
        widget_id = f"glass_{id(widget)}"
        self.registered_widgets[widget_id] = widget

    def _apply_canvas_glass_effect(
        self,
        canvas: tk.Canvas,
        material: GlassMaterial,
        rounded_corners: int,
        double_border: bool
    ):
        """Apply glass effect to Canvas widget (true rendering)"""
        width = canvas.winfo_width() or 400
        height = canvas.winfo_height() or 300

        # Background glass panel with rounded corners
        self._draw_rounded_rectangle(
            canvas,
            10, 10, width - 10, height - 10,
            radius=rounded_corners,
            fill=self.color_scheme['glass_panel'],
            outline=''
        )

        # Inner glow/reflection
        if material.glow_intensity > 0:
            self._draw_rounded_rectangle(
                canvas,
                12, 12, width - 12, height / 3,
                radius=rounded_corners - 2,
                fill=material.glow_color or self.color_scheme['glow_primary'],
                outline='',
                stipple='gray25'  # Creates translucent effect
            )

        # Double-line border
        if double_border:
            # Outer border
            self._draw_rounded_rectangle(
                canvas,
                10, 10, width - 10, height - 10,
                radius=rounded_corners,
                fill='',
                outline=self.color_scheme['border_heavy'],
                width=material.border_width
            )

            # Inner border (2px inset)
            self._draw_rounded_rectangle(
                canvas,
                12, 12, width - 12, height - 12,
                radius=rounded_corners - 2,
                fill='',
                outline=self.color_scheme['border_light'],
                width=1
            )

        # Drop shadow (simulated with offset rectangle)
        shadow_offset = material.shadow_depth
        self._draw_rounded_rectangle(
            canvas,
            10 + shadow_offset, 10 + shadow_offset,
            width - 10 + shadow_offset, height - 10 + shadow_offset,
            radius=rounded_corners,
            fill=self.color_scheme['shadow'],
            outline='',
            tags='shadow'
        )

        # Lower shadow to back
        canvas.tag_lower('shadow')

    def _draw_rounded_rectangle(
        self,
        canvas: tk.Canvas,
        x1: float, y1: float, x2: float, y2: float,
        radius: int = 12,
        **kwargs
    ) -> int:
        """Draw a rounded rectangle on canvas"""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]

        return canvas.create_polygon(points, smooth=True, **kwargs)

    def _apply_ttk_glass_effect(self, widget: ttk.Widget, material: GlassMaterial):
        """Apply glass styling to ttk widget"""
        widget_class = widget.winfo_class()

        if widget_class == 'TButton':
            widget.configure(style='Glass.TButton')
        elif widget_class == 'TFrame':
            widget.configure(style='Glass.TFrame')
        elif widget_class == 'TLabel':
            widget.configure(style='Glass.TLabel')
        elif widget_class == 'TEntry':
            widget.configure(style='Glass.TEntry')
        elif widget_class == 'TNotebook':
            widget.configure(style='Glass.TNotebook')

    def _apply_tk_glass_effect(self, widget: tk.Widget, material: GlassMaterial):
        """Apply glass styling to tk widget"""
        try:
            widget.configure(
                bg=self.color_scheme['glass_panel'],
                fg=self.color_scheme['text_primary'],
                highlightthickness=material.border_width,
                highlightbackground=self.color_scheme['border'],
                highlightcolor=self.color_scheme['primary']
            )
        except tk.TclError:
            # Widget doesn't support these options
            pass

    def set_material(self, material_name: str):
        """Change current glass material"""
        if material_name in GLASS_MATERIALS:
            self.current_material = GLASS_MATERIALS[material_name]
            self._configure_glass_styles()
            self._refresh_registered_widgets()

    def set_color_scheme(self, scheme: Dict[str, str]):
        """Update color scheme"""
        # Guard against invalid/unsupported Tk color strings.
        # Bad colors can raise TclError during style configuration and make the UI feel "non-interactive".
        safe: Dict[str, str] = {}
        try:
            base_bg = tk_safe_color(
                scheme.get("glass_bg", self.color_scheme.get("glass_bg", "#000000")),
                bg=self.color_scheme.get("glass_bg", "#000000"),
                fallback=self.color_scheme.get("glass_bg", "#000000"),
            )
        except Exception:
            base_bg = self.color_scheme.get("glass_bg", "#000000")

        for k, v in (scheme or {}).items():
            try:
                safe[k] = tk_safe_color(v, bg=base_bg, fallback=self.color_scheme.get(k, base_bg))
            except Exception:
                safe[k] = self.color_scheme.get(k, base_bg)

        self.color_scheme.update(safe)
        self._configure_glass_styles()
        self._refresh_registered_widgets()

    def _refresh_registered_widgets(self):
        """Refresh all registered widgets with new theme"""
        for widget in self.registered_widgets.values():
            if widget.winfo_exists():
                self.apply_glass_effect(widget)

    def save_theme(self, filepath: Path):
        """Save current theme configuration"""
        theme_data = {
            'material': self.current_material.name,
            'colors': self.color_scheme
        }

        filepath.write_text(json.dumps(theme_data, indent=2), encoding='utf-8')

    def load_theme(self, filepath: Path):
        """Load theme configuration"""
        theme_data = json.loads(filepath.read_text(encoding='utf-8'))

        if 'material' in theme_data and theme_data['material'] in GLASS_MATERIALS:
            self.set_material(theme_data['material'])

        if 'colors' in theme_data:
            self.set_color_scheme(theme_data['colors'])


# ==============================================================================
# Glass Components
# ==============================================================================

class GlassPanel(tk.Canvas):
    """
    Glass panel with frosted effect and rounded corners

    Usage:
        panel = GlassPanel(parent, width=400, height=300)
        panel.pack(padx=20, pady=20)
    """

    def __init__(
        self,
        parent,
        material: Optional[GlassMaterial] = None,
        rounded_corners: int = 12,
        double_border: bool = True,
        **kwargs
    ):
        """Initialize glass panel"""
        # Default styling
        defaults = {
            'bg': ROMER_GLASS_COLORS['glass_bg'],
            'highlightthickness': 0,
            'relief': 'flat'
        }
        defaults.update(kwargs)

        super().__init__(parent, **defaults)

        self.material = material or GLASS_MATERIALS['romer_premium']
        self.rounded_corners = rounded_corners
        self.double_border = double_border

        # Bind resize to redraw
        self.bind('<Configure>', self._on_resize)

        # Initial draw
        self.after(10, self._draw_glass)

    def _draw_glass(self):
        """Draw glass effect"""
        glass_manager = GlassUIManager()
        glass_manager.apply_glass_effect(
            self,
            self.material,
            self.rounded_corners,
            self.double_border
        )

    def _on_resize(self, event):
        """Redraw on resize"""
        self.delete('all')
        self._draw_glass()


class GlassButton(ttk.Button):
    """
    Glass-styled button with hover effects

    Usage:
        btn = GlassButton(parent, text="Click Me", command=callback)
        btn.pack()
    """

    def __init__(self, parent, **kwargs):
        """Initialize glass button"""
        super().__init__(parent, style='Glass.TButton', **kwargs)

        # Apply glass effect
        glass_manager = GlassUIManager()
        glass_manager.apply_glass_effect(self)


class GlassFrame(ttk.Frame):
    """
    Glass-styled frame container

    Usage:
        frame = GlassFrame(parent)
        frame.pack(fill='both', expand=True)
    """

    def __init__(self, parent, **kwargs):
        """Initialize glass frame"""
        super().__init__(parent, style='Glass.TFrame', **kwargs)

        # Apply glass effect
        glass_manager = GlassUIManager()
        glass_manager.apply_glass_effect(self)


# ==============================================================================
# Factory Functions
# ==============================================================================

def create_glass_ui_manager() -> GlassUIManager:
    """
    Create Glass UI Manager instance

    Returns:
        Configured GlassUIManager
    """
    return GlassUIManager()


def apply_romer_theme(root: tk.Tk):
    """
    Apply complete Romer Industries glass theme to application

    Args:
        root: Root Tk window
    """
    manager = create_glass_ui_manager()
    manager.set_material('romer_premium')

    # Configure root window
    try:
        root.configure(bg=tk_safe_color(ROMER_GLASS_COLORS.get("glass_bg"), fallback="#000000"))
    except Exception:
        root.configure(bg="#000000")

    # Set window properties for modern look
    # Tk option database parses font strings; families with spaces must be braced.
    # Without braces this can break widget creation with errors like:
    #   "expected integer but got 'UI'"
    root.option_add('*Font', '{Segoe UI} 10')
    root.option_add('*Background', tk_safe_color(ROMER_GLASS_COLORS.get("glass_bg"), fallback="#000000"))
    root.option_add('*Foreground', tk_safe_color(ROMER_GLASS_COLORS.get("text_primary"), bg="#000000", fallback="#ffffff"))

    return manager


# ==============================================================================
# Standalone Test
# ==============================================================================

if __name__ == '__main__':
    # Create test window
    root = tk.Tk()
    root.title("Glass UI Test - Romer Industries")
    root.geometry("800x600")

    # Apply Romer theme
    manager = apply_romer_theme(root)

    # Create glass panel
    panel = GlassPanel(root, width=700, height=500)
    panel.pack(padx=50, pady=50)

    # Add glass components
    frame = GlassFrame(panel)
    frame.place(relx=0.5, rely=0.5, anchor='center')

    ttk.Label(
        frame,
        text="Romer Industries Glass UI",
        font=('Segoe UI', 24, 'bold'),
        style='Glass.TLabel'
    ).pack(pady=20)

    GlassButton(frame, text="Primary Action").pack(pady=10)
    GlassButton(frame, text="Secondary Action").pack(pady=10)

    root.mainloop()
