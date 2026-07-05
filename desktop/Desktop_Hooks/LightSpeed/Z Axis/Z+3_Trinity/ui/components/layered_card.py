"""
LightSpeed V0.9.5 - Multi-Layer Card/Pane UI Component
Modern glass morphism design with open-angle enhanced visual layout
Reusable across all Z-floor UIs

Features:
- Layered card system with depth and shadows
- Glass morphism with transparency and blur effects
- Smooth animations and transitions
- Flexible content panels
- Theme-aware styling

Author: LightSpeed Team
Version: 0.9.5
Date: January 2, 2026
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Dict, Any, List
from pathlib import Path


class LayeredCard(tk.Frame):
    """
    Multi-layer card component with glass morphism design.

    Features:
    - Primary card layer with shadow
    - Secondary content layers
    - Glass effect with transparency
    - Smooth hover effects
    - Flexible content slots
    """

    # Color scheme (glass morphism)
    COLORS = {
        'card_bg': '#0A1628',           # Dark blue card background
        'card_border': '#1E3A5F',       # Border accent
        'glass_overlay': '#102040',     # Semi-transparent overlay
        'shadow': '#000000',            # Shadow color
        'accent_cyan': '#00FFFF',       # Cyan accent
        'accent_blue': '#0088FF',       # Blue accent
        'text_primary': '#FFFFFF',      # Primary text
        'text_secondary': '#88CCFF',    # Secondary text
        'hover_highlight': '#1A4070',   # Hover effect
    }

    def __init__(self, parent, title: str = "", subtitle: str = "",
                 height: int = 200, elevation: int = 2, **kwargs):
        """
        Initialize layered card component.

        Args:
            parent: Parent tkinter widget
            title: Card title text
            subtitle: Card subtitle text
            height: Card height in pixels
            elevation: Shadow depth (0-5)
            **kwargs: Additional Frame parameters
        """
        super().__init__(parent, **kwargs)

        self.title_text = title
        self.subtitle_text = subtitle
        self.card_height = height
        self.elevation = max(0, min(5, elevation))

        self.configure(bg=self.COLORS['card_bg'], relief='flat')

        # Build card structure
        self._build_card()

    def _build_card(self):
        """Build the multi-layer card structure"""

        # Shadow layer (bottom)
        shadow_offset = self.elevation * 2
        shadow_frame = tk.Frame(
            self,
            bg=self.COLORS['shadow'],
            height=self.card_height + shadow_offset,
            relief='flat'
        )
        shadow_frame.pack(fill='x', padx=shadow_offset, pady=(shadow_offset, 0))
        shadow_frame.pack_propagate(False)

        # Main card layer (middle)
        self.card_frame = tk.Frame(
            self,
            bg=self.COLORS['card_bg'],
            relief='solid',
            bd=1,
            highlightthickness=1,
            highlightbackground=self.COLORS['card_border'],
            highlightcolor=self.COLORS['accent_cyan']
        )
        self.card_frame.place(relx=0, rely=0, relwidth=1, height=self.card_height)

        # Header section
        self.header = tk.Frame(self.card_frame, bg=self.COLORS['glass_overlay'], height=50)
        self.header.pack(fill='x')
        self.header.pack_propagate(False)

        # Title
        if self.title_text:
            title_label = tk.Label(
                self.header,
                text=self.title_text,
                font=('Segoe UI', 14, 'bold'),
                bg=self.COLORS['glass_overlay'],
                fg=self.COLORS['text_primary'],
                anchor='w'
            )
            title_label.pack(side='left', padx=20, pady=10)

        # Subtitle
        if self.subtitle_text:
            subtitle_label = tk.Label(
                self.header,
                text=self.subtitle_text,
                font=('Segoe UI', 9),
                bg=self.COLORS['glass_overlay'],
                fg=self.COLORS['text_secondary'],
                anchor='w'
            )
            subtitle_label.pack(side='left', padx=(0, 20), pady=10)

        # Content area
        self.content = tk.Frame(self.card_frame, bg=self.COLORS['card_bg'])
        self.content.pack(fill='both', expand=True, padx=2, pady=2)

        # Add hover effect
        self._setup_hover_effect()

    def _setup_hover_effect(self):
        """Setup subtle hover effect"""
        def on_enter(e):
            self.card_frame.configure(highlightbackground=self.COLORS['accent_cyan'])

        def on_leave(e):
            self.card_frame.configure(highlightbackground=self.COLORS['card_border'])

        self.card_frame.bind('<Enter>', on_enter)
        self.card_frame.bind('<Leave>', on_leave)

    def set_content(self, widget):
        """
        Set the main content widget for the card.

        Args:
            widget: tkinter widget to display in content area
        """
        # Clear existing content
        for child in self.content.winfo_children():
            child.destroy()

        # Pack new content
        widget.pack(fill='both', expand=True)

    def add_header_button(self, text: str, command: Callable, style: str = 'primary'):
        """
        Add a button to the card header.

        Args:
            text: Button text
            command: Button command callback
            style: Button style ('primary', 'secondary', 'success', 'danger')
        """
        btn_colors = {
            'primary': ('#0088FF', '#FFFFFF'),
            'secondary': ('#1E3A5F', '#88CCFF'),
            'success': ('#00AA00', '#FFFFFF'),
            'danger': ('#FF3333', '#FFFFFF'),
        }

        bg, fg = btn_colors.get(style, btn_colors['primary'])

        btn = tk.Button(
            self.header,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            font=('Segoe UI', 9, 'bold'),
            relief='flat',
            padx=15,
            pady=5,
            cursor='hand2'
        )
        btn.pack(side='right', padx=5)

        # Hover effect
        def on_enter(e):
            btn.configure(bg=self._lighten_color(bg))

        def on_leave(e):
            btn.configure(bg=bg)

        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)

        return btn

    def _lighten_color(self, hex_color: str, factor: float = 1.2) -> str:
        """Lighten a hex color by factor"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        return f'#{r:02x}{g:02x}{b:02x}'


class LayeredPane(tk.Frame):
    """
    Multi-pane container with layered cards.

    Organizes multiple LayeredCard components in a flexible layout.
    """

    def __init__(self, parent, orientation: str = 'vertical', **kwargs):
        """
        Initialize layered pane container.

        Args:
            parent: Parent tkinter widget
            orientation: Layout orientation ('vertical' or 'horizontal')
            **kwargs: Additional Frame parameters
        """
        super().__init__(parent, **kwargs)

        self.orientation = orientation
        self.configure(bg='#000B1F')

        self.cards: List[LayeredCard] = []

    def add_card(self, title: str = "", subtitle: str = "",
                 height: int = 200, elevation: int = 2) -> LayeredCard:
        """
        Add a new layered card to the pane.

        Args:
            title: Card title
            subtitle: Card subtitle
            height: Card height
            elevation: Shadow depth

        Returns:
            LayeredCard instance
        """
        card = LayeredCard(
            self,
            title=title,
            subtitle=subtitle,
            height=height,
            elevation=elevation
        )

        if self.orientation == 'vertical':
            card.pack(fill='x', padx=10, pady=10)
        else:
            card.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        self.cards.append(card)
        return card


class GlassPanel(tk.Frame):
    """
    Glass morphism panel with blur effect simulation.

    Creates a modern, semi-transparent panel with frosted glass appearance.
    """

    def __init__(self, parent, title: str = "", opacity: float = 0.85, **kwargs):
        """
        Initialize glass panel.

        Args:
            parent: Parent tkinter widget
            title: Panel title
            opacity: Panel opacity (0.0-1.0)
            **kwargs: Additional Frame parameters
        """
        super().__init__(parent, **kwargs)

        self.title_text = title
        self.opacity = max(0.0, min(1.0, opacity))

        # Calculate glass color based on opacity
        base_color = '#0A1628'
        self.configure(
            bg=base_color,
            relief='solid',
            bd=1,
            highlightthickness=2,
            highlightbackground='#1E3A5F',
            highlightcolor='#00FFFF'
        )

        # Title bar
        if self.title_text:
            title_bar = tk.Frame(self, bg='#102040', height=40)
            title_bar.pack(fill='x')
            title_bar.pack_propagate(False)

            tk.Label(
                title_bar,
                text=self.title_text,
                font=('Segoe UI', 12, 'bold'),
                bg='#102040',
                fg='#FFFFFF',
                anchor='w'
            ).pack(side='left', padx=15, pady=10)

        # Content frame
        self.content = tk.Frame(self, bg=base_color)
        self.content.pack(fill='both', expand=True, padx=10, pady=10)


# Export public API
__all__ = ['LayeredCard', 'LayeredPane', 'GlassPanel']
