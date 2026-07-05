#!/usr/bin/env python
"""
Premium Theme Engine - Glassmorphism & Marble Aesthetic
Trinity Floor (Z+3) - UI Enhancement System

Provides high-quality UI theming with:
- Marble/glassy 3D effects
- Gold and white accents (Light Mode)
- Phthalo green, deep gold, velvet blue (Dark Mode)
- Professional icon kit integration
- Sunset hues backgrounds
- Premium glassmorphism effects

Floor: Trinity
Z-Level: +3
Author: LightSpeed Team
Version: 1.0.0
Date: 2026-01-13
"""

import tkinter as tk
from tkinter import ttk, font
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path
import json
from dataclasses import dataclass, field
from enum import Enum

try:
    # Use the canonical sanitizer so rgba()/alpha-hex never hit Tk directly.
    from core.ui.glass_ui import tk_safe_color as _tk_safe_color
except Exception:  # pragma: no cover
    _tk_safe_color = None

class ThemeMode(Enum):
    """Theme mode enumeration."""
    LIGHT = "light"
    DARK = "dark"


@dataclass
class ColorPalette:
    """Color palette for theme."""
    primary: str
    secondary: str
    accent_1: str
    accent_2: str
    text_primary: str
    text_secondary: str
    border: str
    shadow: str
    glass_overlay: str
    gradient_start: str
    gradient_end: str
    success: str
    warning: str
    error: str
    info: str


class PremiumThemeEngine:
    """
    Premium theme engine for LightSpeed Platform.

    Provides consistent high-quality UI theming across all interfaces.
    Based on marble/glassy aesthetic with gold accents.

    Features:
    - Light mode: Gold, white, marble
    - Dark mode: Phthalo green, deep gold, velvet blue
    - Glassmorphism effects
    - 3D icon support
    - Professional typography
    - Sunset hues backgrounds
    """

    def __init__(self, mode: ThemeMode = ThemeMode.LIGHT):
        """
        Initialize theme engine.

        Parameters:
            mode: Theme mode (light or dark)
        """
        self.mode = mode
        self.config = self._load_theme_config()
        self.palette = self._get_color_palette()

        # Cache for created styles
        self._style_cache: Dict[str, Any] = {}

    def _load_theme_config(self) -> Dict[str, Any]:
        """Load theme configuration from JSON."""
        try:
            config_path = Path(__file__).parents[3] / "config" / "premium_theme_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[Theme] Failed to load config: {e}")

        # Fallback minimal config
        return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default theme configuration."""
        return {
            "color_palettes": {
                "light_mode": {
                    "primary": "#FFFFFF",
                    "secondary": "#F5F5F5",
                    "accent_gold": "#FFD700",
                    "accent_white_marble": "#F8F8FF",
                    "text_primary": "#2F4F4F",
                    "text_secondary": "#696969",
                    "border": "#E8E8E8",
                    "glass_overlay": "rgba(255, 255, 255, 0.85)"
                },
                "dark_mode": {
                    "primary": "#0A4D4D",
                    "secondary": "#1A5F5F",
                    "accent_phthalo_green": "#123524",
                    "accent_deep_gold": "#B8860B",
                    "accent_velvet_blue": "#191970",
                    "text_primary": "#F5F5DC",
                    "text_secondary": "#D3D3D3",
                    "matrix_green": "#00FF41",
                    "border": "#2F4F4F",
                    "glass_overlay": "rgba(18, 53, 36, 0.75)"
                }
            },
            "typography": {
                "font_primary": "Garamond",
                "font_secondary": "Arial",
                "font_code": "Consolas"
            }
        }

    def _get_color_palette(self) -> ColorPalette:
        """Get color palette for current mode."""
        palettes = self.config.get("color_palettes", {})

        if self.mode == ThemeMode.LIGHT:
            colors = palettes.get("light_mode", {})
            primary = colors.get("primary", "#FFFFFF")
            return ColorPalette(
                primary=colors.get("primary", "#FFFFFF"),
                secondary=colors.get("secondary", "#F5F5F5"),
                accent_1=colors.get("accent_gold", "#FFD700"),
                accent_2=colors.get("accent_white_marble", "#F8F8FF"),
                text_primary=colors.get("text_primary", "#2F4F4F"),
                text_secondary=colors.get("text_secondary", "#696969"),
                border=colors.get("border", "#E8E8E8"),
                shadow=(
                    _tk_safe_color(colors.get("shadow", "rgba(0, 0, 0, 0.1)"), bg=primary)
                    if _tk_safe_color else colors.get("shadow", "#000000")
                ),
                glass_overlay=(
                    _tk_safe_color(colors.get("glass_overlay", "rgba(255, 255, 255, 0.85)"), bg=primary)
                    if _tk_safe_color else colors.get("glass_overlay", colors.get("secondary", "#F5F5F5"))
                ),
                gradient_start=colors.get("gradient_start", "#FFFAF0"),
                gradient_end=colors.get("gradient_end", "#FFE4B5"),
                success=colors.get("success", "#98FB98"),
                warning=colors.get("warning", "#FFD700"),
                error=colors.get("error", "#FFB6C1"),
                info=colors.get("info", "#87CEEB")
            )
        else:  # Dark mode
            colors = palettes.get("dark_mode", {})
            primary = colors.get("primary", "#0A4D4D")
            return ColorPalette(
                primary=colors.get("primary", "#0A4D4D"),
                secondary=colors.get("secondary", "#1A5F5F"),
                accent_1=colors.get("accent_deep_gold", "#B8860B"),
                accent_2=colors.get("accent_velvet_blue", "#191970"),
                text_primary=colors.get("text_primary", "#F5F5DC"),
                text_secondary=colors.get("text_secondary", "#D3D3D3"),
                border=colors.get("border", "#2F4F4F"),
                shadow=(
                    _tk_safe_color(colors.get("shadow", "rgba(0, 0, 0, 0.5)"), bg=primary)
                    if _tk_safe_color else colors.get("shadow", "#000000")
                ),
                glass_overlay=(
                    _tk_safe_color(colors.get("glass_overlay", "rgba(18, 53, 36, 0.75)"), bg=primary)
                    if _tk_safe_color else colors.get("glass_overlay", colors.get("secondary", "#1A5F5F"))
                ),
                gradient_start=colors.get("gradient_start", "#0A4D4D"),
                gradient_end=colors.get("gradient_end", "#191970"),
                success=colors.get("success", "#00FF41"),
                warning=colors.get("warning", "#B8860B"),
                error=colors.get("error", "#DC143C"),
                info=colors.get("info", "#4682B4")
            )

    def apply_to_root(self, root: tk.Tk):
        """
        Apply premium theme to root window.

        Parameters:
            root: Root Tk window
        """
        # Configure ttk style
        style = ttk.Style(root)

        # Try to use clam theme as base
        try:
            style.theme_use('clam')
        except:
            pass

        # Apply custom styles
        self._configure_button_style(style)
        self._configure_label_style(style)
        self._configure_frame_style(style)
        self._configure_entry_style(style)
        self._configure_treeview_style(style)

        # Configure root window
        root.configure(bg=self.palette.primary)

    def _configure_button_style(self, style: ttk.Style):
        """Configure button styles."""
        # Primary button (glass effect with gold accent)
        style.configure(
            'Premium.TButton',
            background=self.palette.accent_1,
            foreground=self.palette.text_primary,
            borderwidth=2,
            relief='raised',
            padding=(12, 8),
            font=(self.config.get("typography", {}).get("font_secondary", "Arial"), 11, 'bold')
        )

        style.map(
            'Premium.TButton',
            background=[('active', self.palette.accent_2)],
            relief=[('pressed', 'sunken')]
        )

        # Secondary button (glass effect)
        style.configure(
            'Glass.TButton',
            background=self.palette.secondary,
            foreground=self.palette.text_primary,
            borderwidth=2,
            relief='flat',
            padding=(10, 6)
        )

    def _configure_label_style(self, style: ttk.Style):
        """Configure label styles."""
        # Title labels
        style.configure(
            'Title.TLabel',
            background=self.palette.primary,
            foreground=self.palette.text_primary,
            font=(self.config.get("typography", {}).get("font_primary", "Garamond"), 24, 'bold')
        )

        # Header labels
        style.configure(
            'Header.TLabel',
            background=self.palette.primary,
            foreground=self.palette.text_primary,
            font=(self.config.get("typography", {}).get("font_primary", "Garamond"), 18, 'bold')
        )

        # Body labels
        style.configure(
            'Body.TLabel',
            background=self.palette.primary,
            foreground=self.palette.text_secondary,
            font=(self.config.get("typography", {}).get("font_secondary", "Arial"), 11)
        )

        # Accent labels (gold)
        style.configure(
            'Accent.TLabel',
            background=self.palette.primary,
            foreground=self.palette.accent_1,
            font=(self.config.get("typography", {}).get("font_secondary", "Arial"), 11, 'bold')
        )

    def _configure_frame_style(self, style: ttk.Style):
        """Configure frame styles."""
        # Glass frame
        style.configure(
            'Glass.TFrame',
            background=self.palette.secondary,
            borderwidth=2,
            relief='flat'
        )

        # Card frame (elevated)
        style.configure(
            'Card.TFrame',
            background=self.palette.primary,
            borderwidth=1,
            relief='raised'
        )

    def _configure_entry_style(self, style: ttk.Style):
        """Configure entry/input styles."""
        style.configure(
            'Premium.TEntry',
            fieldbackground=self.palette.secondary,
            foreground=self.palette.text_primary,
            borderwidth=2,
            relief='flat',
            padding=8
        )

    def _configure_treeview_style(self, style: ttk.Style):
        """Configure treeview/table styles."""
        style.configure(
            'Premium.Treeview',
            background=self.palette.primary,
            foreground=self.palette.text_primary,
            fieldbackground=self.palette.secondary,
            borderwidth=1,
            relief='flat',
            rowheight=48
        )

        style.configure(
            'Premium.Treeview.Heading',
            background=self.palette.accent_1,
            foreground=self.palette.text_primary,
            borderwidth=2,
            relief='raised',
            font=(self.config.get("typography", {}).get("font_secondary", "Arial"), 11, 'bold')
        )

        style.map(
            'Premium.Treeview',
            background=[('selected', self.palette.accent_2)],
            foreground=[('selected', self.palette.text_primary)]
        )

    def create_glass_frame(
        self,
        parent: tk.Widget,
        **kwargs
    ) -> tk.Frame:
        """
        Create a glassmorphism-style frame.

        Parameters:
            parent: Parent widget
            **kwargs: Additional frame options

        Returns:
            tk.Frame with glass effect
        """
        frame = tk.Frame(
            parent,
            bg=self.palette.secondary,
            relief='flat',
            borderwidth=2,
            **kwargs
        )

        # Add subtle border for glass effect
        frame.configure(highlightbackground=self.palette.border, highlightthickness=1)

        return frame

    def create_premium_button(
        self,
        parent: tk.Widget,
        text: str,
        command: Optional[callable] = None,
        style: str = "primary",
        **kwargs
    ) -> tk.Button:
        """
        Create premium-styled button.

        Parameters:
            parent: Parent widget
            text: Button text
            command: Button command
            style: Button style ('primary', 'secondary', 'gold')
            **kwargs: Additional button options

        Returns:
            Styled tk.Button
        """
        if style == "primary":
            bg = self.palette.accent_1
            fg = self.palette.text_primary if self.mode == ThemeMode.LIGHT else "#000000"
            active_bg = self.palette.accent_2
        elif style == "secondary":
            bg = self.palette.secondary
            fg = self.palette.text_primary
            active_bg = self.palette.primary
        elif style == "gold":
            bg = self.palette.accent_1
            fg = "#000000"
            active_bg = self.palette.warning
        else:
            bg = self.palette.primary
            fg = self.palette.text_primary
            active_bg = self.palette.secondary

        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=fg,
            relief='raised',
            borderwidth=2,
            font=(self.config.get("typography", {}).get("font_secondary", "Arial"), 11, 'bold'),
            padx=16,
            pady=8,
            cursor='hand2',
            **kwargs
        )

        return button

    def create_title_label(
        self,
        parent: tk.Widget,
        text: str,
        **kwargs
    ) -> tk.Label:
        """
        Create premium title label.

        Parameters:
            parent: Parent widget
            text: Label text
            **kwargs: Additional label options

        Returns:
            Styled tk.Label
        """
        font = kwargs.pop(
            "font",
            (self.config.get("typography", {}).get("font_primary", "Garamond"), 24, "bold"),
        )
        return tk.Label(
            parent,
            text=text,
            bg=self.palette.primary,
            fg=self.palette.text_primary,
            font=font,
            **kwargs
        )

    def create_header_label(
        self,
        parent: tk.Widget,
        text: str,
        **kwargs
    ) -> tk.Label:
        """Create header label."""
        font = kwargs.pop(
            "font",
            (self.config.get("typography", {}).get("font_primary", "Garamond"), 18, "bold"),
        )
        return tk.Label(
            parent,
            text=text,
            bg=self.palette.primary,
            fg=self.palette.text_primary,
            font=font,
            **kwargs
        )

    def create_body_label(
        self,
        parent: tk.Widget,
        text: str,
        **kwargs
    ) -> tk.Label:
        """Create body text label."""
        font = kwargs.pop(
            "font",
            (self.config.get("typography", {}).get("font_secondary", "Arial"), 11),
        )
        return tk.Label(
            parent,
            text=text,
            bg=self.palette.primary,
            fg=self.palette.text_secondary,
            font=font,
            **kwargs
        )

    def create_card_frame(
        self,
        parent: tk.Widget,
        **kwargs
    ) -> tk.Frame:
        """
        Create elevated card frame.

        Parameters:
            parent: Parent widget
            **kwargs: Additional frame options

        Returns:
            Styled card frame
        """
        frame = tk.Frame(
            parent,
            bg=self.palette.primary,
            relief='raised',
            borderwidth=2,
            **kwargs
        )

        # Add gold accent border for premium look
        frame.configure(
            highlightbackground=self.palette.accent_1,
            highlightthickness=1
        )

        return frame

    def create_premium_entry(
        self,
        parent: tk.Widget,
        **kwargs
    ) -> tk.Entry:
        """
        Create premium-styled entry widget.

        Parameters:
            parent: Parent widget
            **kwargs: Additional entry options

        Returns:
            Styled tk.Entry
        """
        entry = tk.Entry(
            parent,
            bg=self.palette.secondary,
            fg=self.palette.text_primary,
            insertbackground=self.palette.accent_1,
            relief='flat',
            borderwidth=2,
            font=(self.config.get("typography", {}).get("font_secondary", "Arial"), 11),
            **kwargs
        )

        # Add focus effects
        entry.bind('<FocusIn>', lambda e: entry.configure(
            highlightbackground=self.palette.accent_1,
            highlightthickness=2
        ))
        entry.bind('<FocusOut>', lambda e: entry.configure(
            highlightthickness=0
        ))

        return entry

    def create_sunset_gradient_canvas(
        self,
        parent: tk.Widget,
        width: int,
        height: int
    ) -> tk.Canvas:
        """
        Create canvas with sunset hues gradient background.

        Parameters:
            parent: Parent widget
            width: Canvas width
            height: Canvas height

        Returns:
            Canvas with sunset gradient
        """
        canvas = tk.Canvas(
            parent,
            width=width,
            height=height,
            highlightthickness=0
        )

        # Create vertical gradient (sunset hues)
        sunset_config = self.config.get("sunset_hues", {})
        stops = sunset_config.get("gradient_stops", [
            {"color": "#FFE5B4", "position": 0},
            {"color": "#FFDAB9", "position": 0.3},
            {"color": "#FFB6C1", "position": 0.6},
            {"color": "#DDA0DD", "position": 1.0}
        ])

        # Draw gradient rectangles
        num_steps = 100
        for i in range(num_steps):
            y = (i / num_steps) * height

            # Interpolate color based on position
            pos = i / num_steps
            color = self._interpolate_gradient_color(stops, pos)

            canvas.create_rectangle(
                0, y,
                width, y + (height / num_steps) + 1,
                fill=color,
                outline=''
            )

        return canvas

    def _interpolate_gradient_color(
        self,
        stops: List[Dict[str, Any]],
        position: float
    ) -> str:
        """Interpolate color from gradient stops."""
        # Find surrounding stops
        before_stop = stops[0]
        after_stop = stops[-1]

        for i in range(len(stops) - 1):
            if stops[i]["position"] <= position <= stops[i + 1]["position"]:
                before_stop = stops[i]
                after_stop = stops[i + 1]
                break

        # Simple return (full interpolation would require RGB mixing)
        if position - before_stop["position"] < after_stop["position"] - position:
            return before_stop["color"]
        else:
            return after_stop["color"]

    def get_floor_theme(self, floor_name: str) -> Dict[str, str]:
        """
        Get theme configuration for specific Z-floor.

        Parameters:
            floor_name: Floor name (e.g., "Z+3_Trinity")

        Returns:
            Floor-specific theme colors
        """
        floor_themes = self.config.get("floor_specific_themes", {})
        return floor_themes.get(floor_name, {
            "primary_color": self.palette.primary,
            "accent_color": self.palette.accent_1,
            "icon_theme": "default"
        })

    def toggle_mode(self):
        """Toggle between light and dark mode."""
        self.mode = ThemeMode.DARK if self.mode == ThemeMode.LIGHT else ThemeMode.LIGHT
        self.palette = self._get_color_palette()


# Global theme engine instance
_theme_engine: Optional[PremiumThemeEngine] = None


def get_theme_engine(mode: ThemeMode = ThemeMode.LIGHT) -> PremiumThemeEngine:
    """
    Get global theme engine instance.

    Parameters:
        mode: Theme mode (light or dark)

    Returns:
        PremiumThemeEngine instance
    """
    global _theme_engine
    if _theme_engine is None:
        _theme_engine = PremiumThemeEngine(mode)
    return _theme_engine


def set_theme_mode(mode: ThemeMode):
    """
    Set global theme mode.

    Parameters:
        mode: Theme mode to set
    """
    global _theme_engine
    if _theme_engine is not None:
        _theme_engine.mode = mode
        _theme_engine.palette = _theme_engine._get_color_palette()


if __name__ == '__main__':
    # Test premium theme engine
    root = tk.Tk()
    root.title("Premium Theme Engine - Test")
    root.geometry("800x600")

    # Create theme engine
    theme = PremiumThemeEngine(ThemeMode.LIGHT)
    theme.apply_to_root(root)

    # Test components
    main_frame = theme.create_glass_frame(root, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Title
    theme.create_title_label(
        main_frame,
        text="Premium Theme Engine"
    ).pack(pady=(0, 10))

    # Header
    theme.create_header_label(
        main_frame,
        text="High-Quality Glassmorphism UI"
    ).pack(pady=(0, 20))

    # Card
    card = theme.create_card_frame(main_frame, padding=20)
    card.pack(fill=tk.X, pady=10)

    theme.create_body_label(
        card,
        text="This is a premium card with marble/glassy aesthetic"
    ).pack()

    # Buttons
    button_frame = tk.Frame(main_frame, bg=theme.palette.primary)
    button_frame.pack(pady=20)

    theme.create_premium_button(
        button_frame,
        text="Primary Button",
        style="primary"
    ).pack(side=tk.LEFT, padx=5)

    theme.create_premium_button(
        button_frame,
        text="Gold Button",
        style="gold"
    ).pack(side=tk.LEFT, padx=5)

    theme.create_premium_button(
        button_frame,
        text="Secondary Button",
        style="secondary"
    ).pack(side=tk.LEFT, padx=5)

    # Entry
    theme.create_body_label(
        main_frame,
        text="Premium Input:"
    ).pack(anchor='w', pady=(10, 5))

    theme.create_premium_entry(
        main_frame,
        width=40
    ).pack(fill=tk.X, padx=20)

    # Mode toggle
    def toggle_theme():
        theme.toggle_mode()
        mode_label.config(text=f"Current Mode: {theme.mode.value.upper()}")

    tk.Button(
        main_frame,
        text="Toggle Light/Dark Mode",
        command=toggle_theme
    ).pack(pady=20)

    mode_label = tk.Label(
        main_frame,
        text=f"Current Mode: {theme.mode.value.upper()}",
        bg=theme.palette.primary,
        fg=theme.palette.text_secondary
    )
    mode_label.pack()

    root.mainloop()
