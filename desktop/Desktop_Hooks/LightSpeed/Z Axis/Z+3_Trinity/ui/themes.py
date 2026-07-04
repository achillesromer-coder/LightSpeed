"""
LightSpeed Theme Manager
Consolidated from: first_run.py (Trinity), lightspeed_complete_gui.py
Features: Light/Dark themes, live preview, color schemes
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Literal

ThemeType = Literal["light", "dark"]

class ThemeManager:
    """
    Centralized theme management for LightSpeed platform.
    Supports light/dark modes with live preview capability.
    """

    # Color schemes extracted from lightspeed_complete_gui.py
    LIGHT_COLORS = {
        "bg": "#f7f7f9",
        "fg": "#1d1d1f",
        "accent": "#ffffff",
        "highlight": "#e9ecf2",
        "primary": "#0066cc",
        "secondary": "#5856d6",
        "success": "#34c759",
        "warning": "#ff9500",
        "danger": "#ff3b30",
        "border": "#d1d1d6",
        "text_dark": "#1d1d1f",
        "text_light": "#8e8e93",
        "sidebar_bg": "#ffffff",
        "header_bg": "#f7f7f9",
        "card_bg": "#ffffff",
        "hover": "#e9ecf2",
    }

    DARK_COLORS = {
        "bg": "#1f2127",
        "fg": "#e8e8e8",
        "accent": "#2d2f36",
        "highlight": "#3a3d46",
        "primary": "#0a84ff",
        "secondary": "#5e5ce6",
        "success": "#30d158",
        "warning": "#ff9f0a",
        "danger": "#ff453a",
        "border": "#38383a",
        "text_dark": "#e8e8e8",
        "text_light": "#98989d",
        "sidebar_bg": "#2d2f36",
        "header_bg": "#1f2127",
        "card_bg": "#2d2f36",
        "hover": "#3a3d46",
    }

    def __init__(self, app: tk.Tk, initial_theme: ThemeType = "light"):
        """
        Initialize theme manager.

        Args:
            app: Root Tkinter application
            initial_theme: Starting theme ("light" or "dark")
        """
        self.app = app
        self.current_theme = initial_theme
        self.style = ttk.Style(app)

        # Try to use 'clam' theme as base for better styling
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        # Apply initial theme
        self.apply_theme(initial_theme)

    def get_colors(self, theme: ThemeType = None) -> Dict[str, str]:
        """
        Get color scheme for specified theme.

        Args:
            theme: Theme name (defaults to current theme)

        Returns:
            Dictionary of color values
        """
        if theme is None:
            theme = self.current_theme

        return self.DARK_COLORS if theme == "dark" else self.LIGHT_COLORS

    def apply_theme(self, theme: ThemeType) -> None:
        """
        Apply theme to application.

        Args:
            theme: Theme to apply ("light" or "dark")
        """
        self.current_theme = theme
        colors = self.get_colors(theme)

        # Base configuration
        self.style.configure(".",
            background=colors["bg"],
            foreground=colors["fg"]
        )

        # Frame styles
        self.style.configure("TFrame",
            background=colors["bg"]
        )

        self.style.configure("Card.TFrame",
            background=colors["card_bg"],
            relief="flat",
            borderwidth=1
        )

        # Label styles
        self.style.configure("TLabel",
            background=colors["bg"],
            foreground=colors["fg"]
        )

        self.style.configure("Header.TLabel",
            background=colors["header_bg"],
            foreground=colors["text_dark"],
            font=("Arial", 14, "bold")
        )

        self.style.configure("Subheader.TLabel",
            background=colors["bg"],
            foreground=colors["text_light"],
            font=("Arial", 10)
        )

        # Button styles
        self.style.configure("TButton",
            background=colors["accent"],
            foreground=colors["fg"],
            padding=6,
            borderwidth=1,
            relief="flat"
        )

        self.style.map("TButton",
            background=[("active", colors["hover"])]
        )

        self.style.configure("Primary.TButton",
            background=colors["primary"],
            foreground="#ffffff",
            padding=8
        )

        self.style.map("Primary.TButton",
            background=[("active", colors["highlight"])]
        )

        self.style.configure("Success.TButton",
            background=colors["success"],
            foreground="#ffffff",
            padding=6
        )

        self.style.configure("Danger.TButton",
            background=colors["danger"],
            foreground="#ffffff",
            padding=6
        )

        # Entry styles
        self.style.configure("TEntry",
            fieldbackground=colors["accent"],
            foreground=colors["fg"],
            borderwidth=1,
            relief="flat"
        )

        # Notebook (tabs) styles
        self.style.configure("TNotebook",
            background=colors["bg"],
            borderwidth=0
        )

        self.style.configure("TNotebook.Tab",
            background=colors["accent"],
            foreground=colors["fg"],
            padding=(10, 6)
        )

        self.style.map("TNotebook.Tab",
            background=[("selected", colors["highlight"])]
        )

        # Treeview styles
        self.style.configure("Treeview",
            background=colors["accent"],
            fieldbackground=colors["accent"],
            foreground=colors["fg"],
            borderwidth=0
        )

        self.style.configure("Treeview.Heading",
            background=colors["header_bg"],
            foreground=colors["text_dark"],
            borderwidth=1,
            relief="flat"
        )

        self.style.map("Treeview",
            background=[("selected", colors["primary"])]
        )

        # Scrollbar styles
        self.style.configure("TScrollbar",
            background=colors["accent"],
            troughcolor=colors["bg"],
            borderwidth=0,
            arrowcolor=colors["fg"]
        )

        # Progressbar styles
        self.style.configure("TProgressbar",
            background=colors["primary"],
            troughcolor=colors["accent"],
            borderwidth=0,
            thickness=6
        )

        # Checkbutton styles
        self.style.configure("TCheckbutton",
            background=colors["bg"],
            foreground=colors["fg"]
        )

        # Radiobutton styles
        self.style.configure("TRadiobutton",
            background=colors["bg"],
            foreground=colors["fg"]
        )

        # Combobox styles
        self.style.configure("TCombobox",
            fieldbackground=colors["accent"],
            background=colors["accent"],
            foreground=colors["fg"],
            arrowcolor=colors["fg"]
        )

        # Separator styles
        self.style.configure("TSeparator",
            background=colors["border"]
        )

        # LabelFrame styles
        self.style.configure("TLabelframe",
            background=colors["bg"],
            foreground=colors["fg"],
            borderwidth=1,
            relief="flat"
        )

        self.style.configure("TLabelframe.Label",
            background=colors["bg"],
            foreground=colors["text_dark"],
            font=("Arial", 10, "bold")
        )

        # Update root window background
        self.app.configure(bg=colors["bg"])

    def toggle_theme(self) -> ThemeType:
        """
        Toggle between light and dark themes.

        Returns:
            New theme name
        """
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme(new_theme)
        return new_theme

    def set_theme(self, theme: ThemeType) -> None:
        """
        Set specific theme.

        Args:
            theme: Theme to apply ("light" or "dark")
        """
        self.apply_theme(theme)

    def apply_custom_theme(self, colors: Dict[str, str]) -> None:
        """
        Apply custom color scheme (e.g., from smart theme extractor).

        Args:
            colors: Dictionary of color values matching theme structure

        Example:
            from core.ui.smart_theme import create_theme_from_image
            custom_colors = create_theme_from_image("background.jpg")
            theme_manager.apply_custom_theme(custom_colors)
        """
        self.current_theme = "custom"

        # Base configuration
        self.style.configure(".",
            background=colors.get("bg", "#1f2127"),
            foreground=colors.get("fg", "#e8e8e8")
        )

        # Frame styles
        self.style.configure("TFrame",
            background=colors.get("bg", "#1f2127")
        )

        self.style.configure("Card.TFrame",
            background=colors.get("card_bg", "#2d2f36"),
            relief="flat",
            borderwidth=1
        )

        # Label styles
        self.style.configure("TLabel",
            background=colors.get("bg", "#1f2127"),
            foreground=colors.get("fg", "#e8e8e8")
        )

        self.style.configure("Header.TLabel",
            background=colors.get("header_bg", "#1f2127"),
            foreground=colors.get("text_dark", "#e8e8e8"),
            font=("Arial", 14, "bold")
        )

        self.style.configure("Subheader.TLabel",
            background=colors.get("bg", "#1f2127"),
            foreground=colors.get("text_light", "#98989d"),
            font=("Arial", 10)
        )

        # Button styles
        self.style.configure("TButton",
            background=colors.get("accent", "#2d2f36"),
            foreground=colors.get("fg", "#e8e8e8"),
            padding=6,
            borderwidth=1,
            relief="flat"
        )

        self.style.map("TButton",
            background=[("active", colors.get("hover", "#3a3d46"))]
        )

        self.style.configure("Primary.TButton",
            background=colors.get("primary", "#0a84ff"),
            foreground="#ffffff",
            padding=8
        )

        self.style.map("Primary.TButton",
            background=[("active", colors.get("highlight", "#3a3d46"))]
        )

        self.style.configure("Success.TButton",
            background=colors.get("success", "#30d158"),
            foreground="#ffffff",
            padding=6
        )

        self.style.configure("Danger.TButton",
            background=colors.get("danger", "#ff453a"),
            foreground="#ffffff",
            padding=6
        )

        # Apply all other widget styles with custom colors
        self._apply_all_widget_styles(colors)

        # Update root window background
        self.app.configure(bg=colors.get("bg", "#1f2127"))

    def _apply_all_widget_styles(self, colors: Dict[str, str]) -> None:
        """Apply custom colors to all widget types."""
        # Entry styles
        self.style.configure("TEntry",
            fieldbackground=colors.get("accent", "#2d2f36"),
            foreground=colors.get("fg", "#e8e8e8"),
            borderwidth=1,
            relief="flat"
        )

        # Notebook (tabs) styles
        self.style.configure("TNotebook",
            background=colors.get("bg", "#1f2127"),
            borderwidth=0
        )

        self.style.configure("TNotebook.Tab",
            background=colors.get("accent", "#2d2f36"),
            foreground=colors.get("fg", "#e8e8e8"),
            padding=(10, 6)
        )

        self.style.map("TNotebook.Tab",
            background=[("selected", colors.get("highlight", "#3a3d46"))]
        )

        # Treeview styles
        self.style.configure("Treeview",
            background=colors.get("accent", "#2d2f36"),
            fieldbackground=colors.get("accent", "#2d2f36"),
            foreground=colors.get("fg", "#e8e8e8"),
            borderwidth=0
        )

        self.style.configure("Treeview.Heading",
            background=colors.get("header_bg", "#1f2127"),
            foreground=colors.get("text_dark", "#e8e8e8"),
            borderwidth=1,
            relief="flat"
        )

        self.style.map("Treeview",
            background=[("selected", colors.get("primary", "#0a84ff"))]
        )

        # Scrollbar, Progressbar, Checkbutton, Radiobutton, Combobox, etc.
        self.style.configure("TScrollbar",
            background=colors.get("accent", "#2d2f36"),
            troughcolor=colors.get("bg", "#1f2127"),
            borderwidth=0,
            arrowcolor=colors.get("fg", "#e8e8e8")
        )

        self.style.configure("TProgressbar",
            background=colors.get("primary", "#0a84ff"),
            troughcolor=colors.get("accent", "#2d2f36"),
            borderwidth=0,
            thickness=6
        )

        self.style.configure("TCheckbutton",
            background=colors.get("bg", "#1f2127"),
            foreground=colors.get("fg", "#e8e8e8")
        )

        self.style.configure("TRadiobutton",
            background=colors.get("bg", "#1f2127"),
            foreground=colors.get("fg", "#e8e8e8")
        )

        self.style.configure("TCombobox",
            fieldbackground=colors.get("accent", "#2d2f36"),
            background=colors.get("accent", "#2d2f36"),
            foreground=colors.get("fg", "#e8e8e8"),
            arrowcolor=colors.get("fg", "#e8e8e8")
        )

        self.style.configure("TSeparator",
            background=colors.get("border", "#38383a")
        )

        self.style.configure("TLabelframe",
            background=colors.get("bg", "#1f2127"),
            foreground=colors.get("fg", "#e8e8e8"),
            borderwidth=1,
            relief="flat"
        )

        self.style.configure("TLabelframe.Label",
            background=colors.get("bg", "#1f2127"),
            foreground=colors.get("text_dark", "#e8e8e8"),
            font=("Arial", 10, "bold")
        )

    def get_current_theme(self) -> ThemeType:
        """
        Get current theme name.

        Returns:
            Current theme ("light" or "dark")
        """
        return self.current_theme


def create_theme_toggle_button(parent: tk.Widget, theme_manager: ThemeManager) -> ttk.Button:
    """
    Create a button that toggles between light/dark themes.

    Args:
        parent: Parent widget
        theme_manager: ThemeManager instance

    Returns:
        Toggle button widget
    """
    def on_toggle():
        new_theme = theme_manager.toggle_theme()
        btn.configure(text=f"🌙 Dark" if new_theme == "light" else "☀️ Light")

    initial_text = "🌙 Dark" if theme_manager.current_theme == "light" else "☀️ Light"
    btn = ttk.Button(parent, text=initial_text, command=on_toggle)

    return btn


# Backward compatibility - direct color access
def get_light_colors() -> Dict[str, str]:
    """Get light theme colors (backward compatibility)."""
    return ThemeManager.LIGHT_COLORS.copy()


def get_dark_colors() -> Dict[str, str]:
    """Get dark theme colors (backward compatibility)."""
    return ThemeManager.DARK_COLORS.copy()
