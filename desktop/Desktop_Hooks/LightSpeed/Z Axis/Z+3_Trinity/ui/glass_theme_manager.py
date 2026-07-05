#!/usr/bin/env python
"""
Glass UI Theme Manager - Unified Visual System
Provides cohesive Glass UI theme with immersive overlays for all components

Features:
- Glass morphism effects (transparency, blur, gradients)
- Animated transitions between floors
- Heads-up display (HUD) overlay
- Unified color palette (Romer Industries brand)
- Dynamic lighting and glow effects
- Depth layers (background -> mid -> foreground -> overlay)

Author: LightSpeed Team / Romer Industries
Version: 5.1.2
Date: April 8, 2026
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Tuple, Optional, Callable
import math


class GlassTheme:
    """
    Glass UI Theme - Unified color palette and styling

    Based on Romer Industries brand identity with Glass morphism design
    """

    # Core Colors (Dark mode optimized)
    BG_DARKEST = '#000B1F'      # Deep space blue (main background)
    BG_DARK = '#001B3F'          # Dark blue (panels)
    BG_PANEL = '#002855'         # Panel blue (cards, containers)
    BG_HOVER = '#003875'         # Hover state

    # Accent Colors
    ACCENT_CYAN = '#00FFFF'      # Primary accent (highlights, buttons)
    ACCENT_MAGENTA = '#FF00FF'   # Secondary accent (alerts, focus)
    ACCENT_PINK = '#FF0088'      # Tertiary accent (special items)

    # Text Colors
    TEXT_WHITE = '#FFFFFF'       # Primary text
    TEXT_CYAN = '#00DDFF'        # Secondary text / links
    TEXT_GREEN = '#00FF88'       # Success / operational
    TEXT_YELLOW = '#FFDD00'      # Warning / attention
    TEXT_GRAY = '#AAAAAA'        # Disabled / subtle

    # Status Colors
    SUCCESS_GREEN = '#00FF00'    # Success operations
    ERROR_RED = '#FF3333'        # Errors / critical
    WARNING_ORANGE = '#FF9900'   # Warnings
    INFO_BLUE = '#0088FF'        # Information

    # Glass Effects
    GLASS_OPACITY_HIGH = 0.95    # Almost opaque
    GLASS_OPACITY_MED = 0.85     # Medium transparency
    GLASS_OPACITY_LOW = 0.70     # High transparency

    # Glow Colors
    # Tk does not support alpha in hex colors ("#RRGGBBAA"). Use solid colors and
    # simulate translucency via `stipple=` on Canvas items where needed.
    GLOW_CYAN = '#00FFFF'
    GLOW_MAGENTA = '#FF00FF'
    GLOW_WHITE = '#FFFFFF'

    # Floor-specific Colors (for spherical UI and navigation)
    FLOOR_COLORS = {
        'Z+3_Trinity': ACCENT_CYAN,
        'Z+2_Neo': SUCCESS_GREEN,
        'Z+1_Architect': TEXT_YELLOW,
        'Z0_TheConstruct': TEXT_WHITE,
        'Z-1_Morpheus': WARNING_ORANGE,
        'Z-2_Oracle': INFO_BLUE,
        'Z-3_Smith': ACCENT_PINK,
        'Z-4_Merovingian': '#88FF00'  # Lime
    }

    # Typography
    FONT_FAMILY = 'Segoe UI'
    FONT_SIZE_HUGE = 24
    FONT_SIZE_LARGE = 18
    FONT_SIZE_NORMAL = 12
    FONT_SIZE_SMALL = 10
    FONT_SIZE_TINY = 8

    # Spacing
    PADDING_HUGE = 30
    PADDING_LARGE = 20
    PADDING_NORMAL = 10
    PADDING_SMALL = 5

    # Border Radius (for rounded corners - simulated with frames)
    RADIUS_LARGE = 15
    RADIUS_NORMAL = 10
    RADIUS_SMALL = 5

    @classmethod
    def configure_ttk_style(cls):
        """Configure TTK style with Glass theme"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure TFrame
        style.configure('Glass.TFrame', background=cls.BG_PANEL)
        style.configure('Transparent.TFrame', background=cls.BG_DARKEST)

        # Configure TLabel
        style.configure('Glass.TLabel',
                       background=cls.BG_PANEL,
                       foreground=cls.TEXT_WHITE,
                       font=(cls.FONT_FAMILY, cls.FONT_SIZE_NORMAL))

        style.configure('GlassTitle.TLabel',
                       background=cls.BG_PANEL,
                       foreground=cls.ACCENT_CYAN,
                       font=(cls.FONT_FAMILY, cls.FONT_SIZE_LARGE, 'bold'))

        # Configure TButton
        style.configure('Glass.TButton',
                       background=cls.BG_HOVER,
                       foreground=cls.TEXT_WHITE,
                       borderwidth=1,
                       relief='flat',
                       font=(cls.FONT_FAMILY, cls.FONT_SIZE_NORMAL))

        style.map('Glass.TButton',
                 background=[('active', cls.ACCENT_CYAN)],
                 foreground=[('active', cls.BG_DARKEST)])

        return style


class GlassPanel(tk.Frame):
    """
    Glass morphism panel with border, shadow, and transparency effect
    """

    def __init__(self, parent, width: int = 300, height: int = 200,
                 title: str = None, **kwargs):
        """Initialize glass panel"""
        super().__init__(parent, bg=GlassTheme.BG_PANEL,
                        highlightbackground=GlassTheme.ACCENT_CYAN,
                        highlightthickness=2, **kwargs)

        self.width = width
        self.height = height

        # Set size
        self.config(width=width, height=height)
        self.pack_propagate(False)

        # Title bar
        if title:
            self.title_bar = tk.Frame(self, bg=GlassTheme.BG_DARK, height=40)
            self.title_bar.pack(fill='x', side='top')
            self.title_bar.pack_propagate(False)

            tk.Label(self.title_bar, text=title,
                    bg=GlassTheme.BG_DARK, fg=GlassTheme.ACCENT_CYAN,
                    font=(GlassTheme.FONT_FAMILY, GlassTheme.FONT_SIZE_NORMAL, 'bold')
                    ).pack(side='left', padx=GlassTheme.PADDING_NORMAL)

        # Content area
        self.content = tk.Frame(self, bg=GlassTheme.BG_PANEL)
        self.content.pack(fill='both', expand=True, padx=5, pady=5)


class HUDOverlay(tk.Canvas):
    """
    Heads-Up Display overlay with system status, floor info, and quick actions

    Appears as transparent overlay on top of main UI
    Shows:
    - Current Z-floor
    - System status (CPU, memory, services)
    - Active tasks count
    - Quick navigation shortcuts
    - Time / date
    """

    def __init__(self, parent, width: int = 1400, height: int = 900):
        """Initialize HUD overlay"""
        super().__init__(parent, width=width, height=height,
                        bg=GlassTheme.BG_DARKEST, highlightthickness=0)

        self.width = width
        self.height = height

        # HUD elements
        self.elements = {}

        # Initialize HUD components
        self._create_floor_indicator()
        self._create_status_bar()
        self._create_quick_nav()
        self._create_notification_area()

    def _create_floor_indicator(self):
        """Create current floor indicator (top-left)"""
        x, y = 30, 30

        # Floor badge
        self.elements['floor_badge'] = self.create_rectangle(
            x, y, x + 200, y + 80,
            fill=GlassTheme.BG_PANEL,
            outline=GlassTheme.ACCENT_CYAN,
            width=2,
            tags='hud_floor'
        )

        # Floor name
        self.elements['floor_name'] = self.create_text(
            x + 100, y + 25,
            text='Z0: THE CONSTRUCT',
            fill=GlassTheme.ACCENT_CYAN,
            font=(GlassTheme.FONT_FAMILY, 14, 'bold'),
            tags='hud_floor'
        )

        # Floor status
        self.elements['floor_status'] = self.create_text(
            x + 100, y + 55,
            text='OPERATIONAL',
            fill=GlassTheme.SUCCESS_GREEN,
            font=(GlassTheme.FONT_FAMILY, 10),
            tags='hud_floor'
        )

    def _create_status_bar(self):
        """Create system status bar (top-right)"""
        x, y = self.width - 350, 30

        # Status panel
        self.elements['status_panel'] = self.create_rectangle(
            x, y, x + 320, y + 80,
            fill=GlassTheme.BG_PANEL,
            outline=GlassTheme.ACCENT_CYAN,
            width=2,
            tags='hud_status'
        )

        # Services status
        self.elements['services_status'] = self.create_text(
            x + 20, y + 20,
            text='Services: 18/18',
            fill=GlassTheme.TEXT_GREEN,
            font=(GlassTheme.FONT_FAMILY, 10),
            anchor='w',
            tags='hud_status'
        )

        # Tasks status
        self.elements['tasks_status'] = self.create_text(
            x + 20, y + 40,
            text='Active Tasks: 0',
            fill=GlassTheme.TEXT_CYAN,
            font=(GlassTheme.FONT_FAMILY, 10),
            anchor='w',
            tags='hud_status'
        )

        # Time
        self.elements['time_display'] = self.create_text(
            x + 20, y + 60,
            text='2025-12-31 12:00',
            fill=GlassTheme.TEXT_GRAY,
            font=(GlassTheme.FONT_FAMILY, 9),
            anchor='w',
            tags='hud_status'
        )

    def _create_quick_nav(self):
        """Create quick navigation panel (left side)"""
        x, y = 30, 130

        # Nav panel
        self.elements['nav_panel'] = self.create_rectangle(
            x, y, x + 200, y + 400,
            fill=GlassTheme.BG_PANEL,
            outline=GlassTheme.ACCENT_CYAN,
            width=2,
            tags='hud_nav'
        )

        # Nav title
        self.create_text(
            x + 100, y + 20,
            text='QUICK NAVIGATION',
            fill=GlassTheme.ACCENT_CYAN,
            font=(GlassTheme.FONT_FAMILY, 11, 'bold'),
            tags='hud_nav'
        )

        # Floor shortcuts (will be populated dynamically)
        self.nav_items = []
        # Setup/login is consolidated into Trinity (Z+3); no separate FirstRun floor.
        floor_names = ['Trinity', 'Neo', 'Architect', 'TheConstruct',
                      'Morpheus', 'Oracle', 'Smith', 'Merovingian']

        for i, floor in enumerate(floor_names):
            item_y = y + 50 + (i * 35)

            # Floor button background
            btn_id = self.create_rectangle(
                x + 10, item_y, x + 190, item_y + 30,
                fill=GlassTheme.BG_HOVER,
                outline='',
                tags=('hud_nav', f'nav_btn_{floor}')
            )

            # Floor text
            txt_id = self.create_text(
                x + 100, item_y + 15,
                text=f'{floor[:3].upper()}',
                fill=GlassTheme.TEXT_CYAN,
                font=(GlassTheme.FONT_FAMILY, 9),
                tags=('hud_nav', f'nav_btn_{floor}')
            )

            self.nav_items.append((btn_id, txt_id, floor))

    def _create_notification_area(self):
        """Create notification/alert area (bottom-right)"""
        x, y = self.width - 350, self.height - 150

        # Notification panel
        self.elements['notif_panel'] = self.create_rectangle(
            x, y, x + 320, y + 120,
            fill=GlassTheme.BG_PANEL,
            outline=GlassTheme.WARNING_ORANGE,
            width=2,
            tags='hud_notif'
        )

        # Notification title
        self.create_text(
            x + 160, y + 15,
            text='NOTIFICATIONS',
            fill=GlassTheme.WARNING_ORANGE,
            font=(GlassTheme.FONT_FAMILY, 10, 'bold'),
            tags='hud_notif'
        )

        # Sample notification
        self.create_text(
            x + 20, y + 40,
            text='System: All services operational',
            fill=GlassTheme.TEXT_GREEN,
            font=(GlassTheme.FONT_FAMILY, 9),
            anchor='w',
            tags='hud_notif'
        )

    def update_floor(self, floor_name: str, status: str = 'OPERATIONAL'):
        """Update current floor display"""
        self.itemconfig(self.elements['floor_name'], text=floor_name)

        status_color = GlassTheme.SUCCESS_GREEN if status == 'OPERATIONAL' else GlassTheme.WARNING_ORANGE
        self.itemconfig(self.elements['floor_status'], text=status, fill=status_color)

    def update_status(self, services: str = '18/18', tasks: int = 0):
        """Update system status"""
        self.itemconfig(self.elements['services_status'], text=f'Services: {services}')
        self.itemconfig(self.elements['tasks_status'], text=f'Active Tasks: {tasks}')

    def add_notification(self, message: str, level: str = 'info'):
        """Add notification to HUD"""
        color_map = {
            'info': GlassTheme.TEXT_CYAN,
            'success': GlassTheme.SUCCESS_GREEN,
            'warning': GlassTheme.WARNING_ORANGE,
            'error': GlassTheme.ERROR_RED
        }

        color = color_map.get(level, GlassTheme.TEXT_CYAN)

        # Create notification text (this is simplified - would scroll in real implementation)
        x = self.width - 330
        y = self.height - 100

        self.create_text(
            x, y,
            text=message[:50],  # Truncate long messages
            fill=color,
            font=(GlassTheme.FONT_FAMILY, 9),
            anchor='w',
            tags='hud_notif_msg'
        )


class FloorTransition:
    """
    Animated transition between Z-floors

    Provides smooth visual transition with fade and slide effects
    """

    def __init__(self, canvas: tk.Canvas):
        """Initialize transition animator"""
        self.canvas = canvas
        self.transition_active = False
        self.transition_steps = 20
        self.current_step = 0

    def fade_transition(self, from_floor: str, to_floor: str,
                       on_complete: Callable = None):
        """
        Fade transition between floors

        Parameters:
            from_floor: Source floor name
            to_floor: Target floor name
            on_complete: Callback when transition completes
        """
        if self.transition_active:
            return

        self.transition_active = True
        self.current_step = 0

        # Get floor colors
        from_color = GlassTheme.FLOOR_COLORS.get(from_floor, GlassTheme.TEXT_WHITE)
        to_color = GlassTheme.FLOOR_COLORS.get(to_floor, GlassTheme.TEXT_WHITE)

        def animate_step():
            if self.current_step >= self.transition_steps:
                self.transition_active = False
                if on_complete:
                    on_complete()
                return

            # Calculate alpha (0 to 1)
            alpha = self.current_step / self.transition_steps

            # Interpolate colors (simplified)
            # In real implementation, would use proper color interpolation

            # Draw transition overlay
            self.canvas.delete('transition')
            opacity_value = int((1 - alpha) * 255)

            # Continue animation
            self.current_step += 1
            self.canvas.after(30, animate_step)

        animate_step()


class SmartFloorPanel(GlassPanel):
    """
    Smart Floor expansion panel

    Shows floor capabilities, active tasks, and quick actions
    Can expand/collapse for detailed view
    """

    def __init__(self, parent, floor_name: str, floor_data: Dict):
        """Initialize smart floor panel"""
        super().__init__(parent, width=350, height=200, title=floor_name)

        self.floor_name = floor_name
        self.floor_data = floor_data
        self.expanded = False

        # Floor color
        self.floor_color = GlassTheme.FLOOR_COLORS.get(floor_name, GlassTheme.ACCENT_CYAN)

        # Create content
        self._create_content()

    def _create_content(self):
        """Create panel content"""
        # Floor icon/badge
        icon_frame = tk.Frame(self.content, bg=self.floor_color, width=50, height=50)
        icon_frame.pack(pady=10)
        icon_frame.pack_propagate(False)

        tk.Label(icon_frame, text=self.floor_name[0:3].upper(),
                bg=self.floor_color, fg=GlassTheme.BG_DARKEST,
                font=(GlassTheme.FONT_FAMILY, 14, 'bold')).pack(expand=True)

        # Capabilities
        cap_text = ', '.join(self.floor_data.get('capabilities', [])[:3])
        tk.Label(self.content, text=cap_text,
                bg=GlassTheme.BG_PANEL, fg=GlassTheme.TEXT_GRAY,
                font=(GlassTheme.FONT_FAMILY, 9),
                wraplength=300).pack(pady=5)

        # Status
        status_frame = tk.Frame(self.content, bg=GlassTheme.BG_PANEL)
        status_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(status_frame, text='Status:',
                bg=GlassTheme.BG_PANEL, fg=GlassTheme.TEXT_GRAY,
                font=(GlassTheme.FONT_FAMILY, 9)).pack(side='left')

        tk.Label(status_frame, text=self.floor_data.get('status', 'Unknown'),
                bg=GlassTheme.BG_PANEL, fg=GlassTheme.SUCCESS_GREEN,
                font=(GlassTheme.FONT_FAMILY, 9, 'bold')).pack(side='left', padx=5)

        # Expand button
        expand_btn = tk.Button(self.content, text='Expand v',
                              bg=GlassTheme.BG_HOVER, fg=GlassTheme.ACCENT_CYAN,
                              font=(GlassTheme.FONT_FAMILY, 9),
                              relief='flat',
                              command=self.toggle_expand)
        expand_btn.pack(pady=10)

    def toggle_expand(self):
        """Toggle panel expansion"""
        self.expanded = not self.expanded

        if self.expanded:
            self.config(height=400)  # Expand
        else:
            self.config(height=200)  # Collapse


# Standalone test
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Glass UI Theme Manager - Demo")
    root.geometry("1400x900")
    root.configure(bg=GlassTheme.BG_DARKEST)

    # Configure TTK style
    GlassTheme.configure_ttk_style()

    # Create HUD overlay
    hud = HUDOverlay(root)
    hud.pack(fill='both', expand=True)

    # Update HUD
    hud.update_floor('Z0: THE CONSTRUCT', 'OPERATIONAL')
    hud.update_status('18/18', 5)
    hud.add_notification('System initialized successfully', 'success')

    # Test Glass Panel
    panel = GlassPanel(root, width=400, height=300, title='Test Panel')
    panel.place(x=500, y=200)

    tk.Label(panel.content, text='Glass morphism panel test',
            bg=GlassTheme.BG_PANEL, fg=GlassTheme.TEXT_WHITE,
            font=(GlassTheme.FONT_FAMILY, 12)).pack(pady=20)

    root.mainloop()
