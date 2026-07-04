#!/usr/bin/env python
"""
Settings Panel - Visual settings editor using Bento Hub pattern
Provides interactive UI for all 60+ settings across all categories
"""

import tkinter as tk
from tkinter import ttk, colorchooser, font as tkfont
from typing import Dict, Any, Optional, Callable
from .base_portal_glass import GlassPanel, GlassButton, GlassEntry, BentoConstraints


class SettingsPanel:
    """
    Visual settings editor with glassmorphism aesthetic

    Features:
    - Category-based navigation
    - Real-time preview
    - Reset to defaults
    - Import/export settings
    - Search functionality
    """

    def __init__(self, parent, settings_hub=None):
        self.parent = parent
        self.constraints = BentoConstraints()

        if settings_hub is None:
            from core.services import get_settings_hub
            self.settings_hub = get_settings_hub()
        else:
            self.settings_hub = settings_hub

        self.categories = self._get_categories()
        self.current_category = 'vr'
        self.search_query = ''

        self.widgets: Dict[str, tk.Widget] = {}
        self.change_callbacks: Dict[str, Callable] = {}

    def _get_categories(self) -> Dict[str, str]:
        """Get setting categories"""
        return {
            'vr': 'VR Settings',
            'ai': 'AI Settings',
            'ui': 'UI Settings',
            'performance': 'Performance',
            'integration': 'Integration',
            'developer': 'Developer'
        }

    def create_panel(self) -> tk.Frame:
        """
        Create settings panel UI

        Returns:
            Main settings frame
        """
        main_frame = tk.Frame(self.parent, bg=self.constraints.bg)

        # Header
        header = self._create_header(main_frame)
        header.pack(fill='x', pady=(0, 10))

        # Content area with sidebar and settings
        content = tk.Frame(main_frame, bg=self.constraints.bg)
        content.pack(fill='both', expand=True)

        # Sidebar (categories)
        sidebar = self._create_sidebar(content)
        sidebar.pack(side='left', fill='y', padx=(0, 10))

        # Settings area
        settings_area = self._create_settings_area(content)
        settings_area.pack(side='left', fill='both', expand=True)

        return main_frame

    def _create_header(self, parent) -> tk.Frame:
        """Create header with title and search"""
        header = GlassPanel(parent, self.constraints)

        title = tk.Label(
            header,
            text="Settings",
            font=('Arial', 18, 'bold'),
            fg=self.constraints.accent_cyan,
            bg=self.constraints.panel
        )
        title.pack(side='left', padx=15, pady=10)

        # Search bar
        search_frame = tk.Frame(header, bg=self.constraints.panel)
        search_frame.pack(side='right', padx=15, pady=10)

        search_label = tk.Label(
            search_frame,
            text="Search:",
            font=('Arial', 10),
            fg=self.constraints.text,
            bg=self.constraints.panel
        )
        search_label.pack(side='left', padx=(0, 5))

        search_var = tk.StringVar()
        search_var.trace('w', lambda *args: self._on_search(search_var.get()))

        search_entry = GlassEntry(search_frame, self.constraints, textvariable=search_var)
        search_entry.pack(side='left')

        return header

    def _create_sidebar(self, parent) -> tk.Frame:
        """Create sidebar with category buttons"""
        sidebar = GlassPanel(parent, self.constraints)
        sidebar.config(width=200)

        title = tk.Label(
            sidebar,
            text="Categories",
            font=('Arial', 12, 'bold'),
            fg=self.constraints.text,
            bg=self.constraints.panel
        )
        title.pack(pady=10, padx=10, anchor='w')

        for category_id, category_name in self.categories.items():
            btn = GlassButton(
                sidebar,
                self.constraints,
                text=category_name,
                command=lambda c=category_id: self._switch_category(c)
            )
            btn.pack(pady=5, padx=10, fill='x')

        # Separator
        sep = tk.Frame(sidebar, bg=self.constraints.border, height=2)
        sep.pack(fill='x', pady=10, padx=10)

        # Action buttons
        reset_btn = GlassButton(
            sidebar,
            self.constraints,
            text="Reset to Defaults",
            command=self._reset_to_defaults
        )
        reset_btn.pack(pady=5, padx=10, fill='x')

        save_btn = GlassButton(
            sidebar,
            self.constraints,
            text="Save Settings",
            command=self._save_settings
        )
        save_btn.pack(pady=5, padx=10, fill='x')

        return sidebar

    def _create_settings_area(self, parent) -> tk.Frame:
        """Create scrollable settings area"""
        container = tk.Frame(parent, bg=self.constraints.bg)

        # Create canvas with scrollbar
        canvas = tk.Canvas(
            container,
            bg=self.constraints.bg,
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)

        self.settings_frame = tk.Frame(canvas, bg=self.constraints.bg)
        self.settings_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )

        canvas.create_window((0, 0), window=self.settings_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Load initial category
        self._load_category_settings(self.current_category)

        return container

    def _load_category_settings(self, category: str):
        """Load and display settings for a category"""
        # Clear existing widgets
        for widget in self.settings_frame.winfo_children():
            widget.destroy()

        self.widgets.clear()

        all_settings = self.settings_hub.get_all_settings()

        # Filter by category
        if category not in all_settings:
            no_settings = tk.Label(
                self.settings_frame,
                text=f"No settings found for {self.categories.get(category, category)}",
                font=('Arial', 12),
                fg=self.constraints.text_dim,
                bg=self.constraints.bg
            )
            no_settings.pack(pady=20)
            return

        category_settings = all_settings[category]

        # Create setting widgets
        for setting_name, setting_config in category_settings.items():
            if self.search_query and self.search_query.lower() not in setting_name.lower():
                continue

            self._create_setting_widget(category, setting_name, setting_config)

    def _create_setting_widget(self, category: str, setting_name: str, config: Dict[str, Any]):
        """Create widget for a single setting"""
        panel = GlassPanel(self.settings_frame, self.constraints)
        panel.pack(fill='x', pady=8, padx=10)

        # Setting name and description
        header_frame = tk.Frame(panel, bg=self.constraints.panel)
        header_frame.pack(fill='x', padx=15, pady=(10, 5))

        name_label = tk.Label(
            header_frame,
            text=setting_name.replace('_', ' ').title(),
            font=('Arial', 11, 'bold'),
            fg=self.constraints.text,
            bg=self.constraints.panel
        )
        name_label.pack(anchor='w')

        if 'description' in config:
            desc_label = tk.Label(
                header_frame,
                text=config['description'],
                font=('Arial', 9),
                fg=self.constraints.text_dim,
                bg=self.constraints.panel
            )
            desc_label.pack(anchor='w')

        # Setting control
        control_frame = tk.Frame(panel, bg=self.constraints.panel)
        control_frame.pack(fill='x', padx=15, pady=(0, 10))

        setting_type = config.get('type', 'text')
        current_value = config.get('value', config.get('default'))

        if setting_type == 'toggle':
            widget = self._create_toggle(control_frame, category, setting_name, current_value)
        elif setting_type == 'slider':
            widget = self._create_slider(control_frame, category, setting_name, config)
        elif setting_type == 'dropdown':
            widget = self._create_dropdown(control_frame, category, setting_name, config)
        elif setting_type == 'number':
            widget = self._create_number(control_frame, category, setting_name, config)
        elif setting_type == 'color':
            widget = self._create_color(control_frame, category, setting_name, current_value)
        else:
            widget = self._create_text(control_frame, category, setting_name, current_value)

        self.widgets[f"{category}.{setting_name}"] = widget

    def _create_toggle(self, parent, category: str, setting_name: str, value: bool) -> tk.Widget:
        """Create toggle switch"""
        var = tk.BooleanVar(value=value)

        def on_change():
            self.settings_hub.set_setting(category, setting_name, var.get())

        var.trace('w', lambda *args: on_change())

        check = tk.Checkbutton(
            parent,
            text="Enabled" if value else "Disabled",
            variable=var,
            font=('Arial', 10),
            fg=self.constraints.text,
            bg=self.constraints.panel,
            selectcolor=self.constraints.accent_cyan,
            activebackground=self.constraints.panel,
            command=lambda: check.config(text="Enabled" if var.get() else "Disabled")
        )
        check.pack(anchor='w')

        return check

    def _create_slider(self, parent, category: str, setting_name: str, config: Dict[str, Any]) -> tk.Widget:
        """Create slider control"""
        frame = tk.Frame(parent, bg=self.constraints.panel)
        frame.pack(fill='x')

        current_value = config.get('value', config.get('default'))
        min_val = config.get('min', 0)
        max_val = config.get('max', 100)
        step = config.get('step', 1)

        var = tk.DoubleVar(value=current_value)

        def on_change(val):
            self.settings_hub.set_setting(category, setting_name, float(val))
            value_label.config(text=f"{float(val):.2f}")

        slider = tk.Scale(
            frame,
            from_=min_val,
            to=max_val,
            resolution=step,
            variable=var,
            orient='horizontal',
            font=('Arial', 9),
            fg=self.constraints.text,
            bg=self.constraints.panel,
            troughcolor=self.constraints.bg,
            activebackground=self.constraints.accent_cyan,
            command=on_change
        )
        slider.pack(side='left', fill='x', expand=True)

        value_label = tk.Label(
            frame,
            text=f"{current_value:.2f}",
            font=('Arial', 10, 'bold'),
            fg=self.constraints.accent_cyan,
            bg=self.constraints.panel,
            width=8
        )
        value_label.pack(side='right', padx=(10, 0))

        return slider

    def _create_dropdown(self, parent, category: str, setting_name: str, config: Dict[str, Any]) -> tk.Widget:
        """Create dropdown control"""
        current_value = config.get('value', config.get('default'))
        options = config.get('options', [])

        var = tk.StringVar(value=str(current_value))

        def on_change(*args):
            val = var.get()
            # Try to convert to original type
            if isinstance(current_value, int):
                val = int(val)
            elif isinstance(current_value, float):
                val = float(val)
            self.settings_hub.set_setting(category, setting_name, val)

        var.trace('w', on_change)

        dropdown = ttk.Combobox(
            parent,
            textvariable=var,
            values=[str(opt) for opt in options],
            state='readonly',
            font=('Arial', 10)
        )
        dropdown.pack(anchor='w', fill='x')

        return dropdown

    def _create_number(self, parent, category: str, setting_name: str, config: Dict[str, Any]) -> tk.Widget:
        """Create number input"""
        current_value = config.get('value', config.get('default'))

        var = tk.StringVar(value=str(current_value))

        def on_change(*args):
            try:
                val = int(var.get()) if isinstance(current_value, int) else float(var.get())
                self.settings_hub.set_setting(category, setting_name, val)
            except ValueError:
                pass

        var.trace('w', on_change)

        entry = GlassEntry(parent, self.constraints, textvariable=var, width=15)
        entry.pack(anchor='w')

        return entry

    def _create_color(self, parent, category: str, setting_name: str, value: str) -> tk.Widget:
        """Create color picker"""
        frame = tk.Frame(parent, bg=self.constraints.panel)
        frame.pack(fill='x')

        color_display = tk.Label(
            frame,
            text="   ",
            bg=value,
            relief='solid',
            borderwidth=1
        )
        color_display.pack(side='left', padx=(0, 10))

        def choose_color():
            color = colorchooser.askcolor(initialcolor=value)
            if color[1]:
                color_display.config(bg=color[1])
                self.settings_hub.set_setting(category, setting_name, color[1])

        btn = GlassButton(frame, self.constraints, text="Choose Color", command=choose_color)
        btn.pack(side='left')

        return frame

    def _create_text(self, parent, category: str, setting_name: str, value: str) -> tk.Widget:
        """Create text input"""
        var = tk.StringVar(value=str(value))

        def on_change(*args):
            self.settings_hub.set_setting(category, setting_name, var.get())

        var.trace('w', on_change)

        entry = GlassEntry(parent, self.constraints, textvariable=var)
        entry.pack(anchor='w', fill='x')

        return entry

    def _switch_category(self, category: str):
        """Switch to different settings category"""
        self.current_category = category
        self._load_category_settings(category)

    def _on_search(self, query: str):
        """Handle search query"""
        self.search_query = query
        self._load_category_settings(self.current_category)

    def _reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings_hub.reset_to_defaults()
        self._load_category_settings(self.current_category)

    def _save_settings(self):
        """Save settings to disk"""
        self.settings_hub.save()
        print("✓ Settings saved")


def create_settings_window():
    """
    Create standalone settings window

    Returns:
        Tkinter root window
    """
    root = tk.Tk()
    root.title("LightSpeed Settings")
    root.geometry("900x700")

    from core.services import get_settings_hub
    settings_hub = get_settings_hub()

    panel = SettingsPanel(root, settings_hub)
    frame = panel.create_panel()
    frame.pack(fill='both', expand=True, padx=10, pady=10)

    return root


if __name__ == '__main__':
    window = create_settings_window()
    window.mainloop()
