#!/usr/bin/env python
"""
Theme Designer - Complete theme customization system
Visual theme builder with live preview and export

Features:
- Color wheel picker
- Gradient editor
- Live theme preview
- Theme import/export (JSON)
- Preset themes library
- Apply to entire application
- Custom color palettes
- Font customization

Author: LightSpeed Team
Version: 5.1.2
Date: April 9, 2026
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from typing import Dict, Tuple, Optional
import json
import math
from pathlib import Path

try:
    from core.config.paths import TRINITY_SETTINGS, TRINITY_THEMES  # type: ignore
except Exception:
    _ROOT = Path.cwd()
    TRINITY_SETTINGS = _ROOT / "Z Axis" / "Z+3_Trinity" / "settings"
    TRINITY_THEMES = _ROOT / "Z Axis" / "Z+3_Trinity" / "themes"


class ColorWheel(tk.Canvas):
    """Interactive color wheel picker"""

    def __init__(self, parent, size=200, on_color_change=None, **kwargs):
        super().__init__(parent, width=size, height=size,
                        bg='#1e1e1e', highlightthickness=0, **kwargs)

        self.size = size
        self.center = size // 2
        self.radius = (size // 2) - 10
        self.on_color_change = on_color_change

        self.current_hue = 0
        self.current_sat = 100
        self.current_val = 100

        self._draw_wheel()
        self.bind('<Button-1>', self._on_click)
        self.bind('<B1-Motion>', self._on_drag)

    def _draw_wheel(self):
        """Draw the color wheel"""
        self.delete('all')

        # Draw color wheel
        for angle in range(360):
            x1 = self.center + int(self.radius * math.cos(math.radians(angle)))
            y1 = self.center + int(self.radius * math.sin(math.radians(angle)))

            # Convert HSV to RGB
            h = angle / 360
            r, g, b = self._hsv_to_rgb(h, 1, 1)
            color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

            self.create_line(
                self.center, self.center, x1, y1,
                fill=color,
                width=2
            )

        # Draw saturation/value gradient in center
        gradient_size = self.radius // 2
        for y in range(gradient_size):
            for x in range(gradient_size):
                dist = math.sqrt(x**2 + y**2)
                if dist <= gradient_size:
                    sat = dist / gradient_size
                    val = 1 - (y / gradient_size)

                    h = self.current_hue / 360
                    r, g, b = self._hsv_to_rgb(h, sat, val)
                    color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

                    self.create_rectangle(
                        self.center - gradient_size + x,
                        self.center - gradient_size + y,
                        self.center - gradient_size + x + 1,
                        self.center - gradient_size + y + 1,
                        fill=color,
                        outline=''
                    )

        # Draw current color indicator
        angle = math.radians(self.current_hue)
        sat_radius = (self.current_sat / 100) * (self.radius // 2)

        indicator_x = self.center + int(sat_radius * math.cos(angle))
        indicator_y = self.center + int(sat_radius * math.sin(angle))

        self.create_oval(
            indicator_x - 8, indicator_y - 8,
            indicator_x + 8, indicator_y + 8,
            outline='white',
            width=3
        )

    def _hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB"""
        if s == 0:
            return v, v, v

        h = h * 6
        i = int(h)
        f = h - i

        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1 - f))

        if i == 0:
            return v, t, p
        elif i == 1:
            return q, v, p
        elif i == 2:
            return p, v, t
        elif i == 3:
            return p, q, v
        elif i == 4:
            return t, p, v
        else:
            return v, p, q

    def _on_click(self, event):
        """Handle click on color wheel"""
        self._update_color(event.x, event.y)

    def _on_drag(self, event):
        """Handle drag on color wheel"""
        self._update_color(event.x, event.y)

    def _update_color(self, x, y):
        """Update color based on click position"""
        dx = x - self.center
        dy = y - self.center

        # Calculate angle (hue)
        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 360

        # Calculate distance (saturation)
        dist = math.sqrt(dx**2 + dy**2)
        sat = min(100, (dist / self.radius) * 100)

        self.current_hue = angle
        self.current_sat = sat

        self._draw_wheel()

        if self.on_color_change:
            self.on_color_change(self.get_current_color())

    def get_current_color(self) -> str:
        """Get current color as hex string"""
        h = self.current_hue / 360
        s = self.current_sat / 100
        v = self.current_val / 100

        r, g, b = self._hsv_to_rgb(h, s, v)
        return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

    def set_color(self, hex_color: str):
        """Set color from hex string"""
        # Convert hex to RGB
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255

        # Convert RGB to HSV (simplified)
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        diff = max_c - min_c

        # Hue
        if diff == 0:
            h = 0
        elif max_c == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif max_c == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        else:
            h = (60 * ((r - g) / diff) + 240) % 360

        # Saturation
        s = 0 if max_c == 0 else (diff / max_c) * 100

        # Value
        v = max_c * 100

        self.current_hue = h
        self.current_sat = s
        self.current_val = v

        self._draw_wheel()


class ThemePreview(tk.Frame):
    """Live preview of theme applied to sample widgets"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg='#2d2d2d')

        self.theme_colors = {}
        self._build_preview()

    def _build_preview(self):
        """Build preview widgets"""
        tk.Label(self, text="Theme Preview",
                font=('Arial', 14, 'bold')).pack(pady=10)

        # Sample button
        self.sample_button = tk.Button(
            self,
            text="Sample Button",
            font=('Arial', 11)
        )
        self.sample_button.pack(pady=5)

        # Sample label
        self.sample_label = tk.Label(
            self,
            text="Sample Label Text",
            font=('Arial', 10)
        )
        self.sample_label.pack(pady=5)

        # Sample entry
        self.sample_entry = tk.Entry(
            self,
            font=('Arial', 10),
            width=20
        )
        self.sample_entry.insert(0, "Sample Input")
        self.sample_entry.pack(pady=5)

        # Sample frame
        self.sample_frame = tk.Frame(self, width=200, height=100)
        self.sample_frame.pack(pady=10)
        self.sample_frame.pack_propagate(False)

        tk.Label(self.sample_frame, text="Sample Panel",
                font=('Arial', 9)).pack(expand=True)

    def apply_theme(self, theme: Dict[str, str]):
        """Apply theme to preview widgets"""
        self.theme_colors = theme

        # Apply colors
        bg = theme.get('bg_dark', '#1e1e1e')
        fg = theme.get('text_white', '#ffffff')
        accent = theme.get('accent_cyan', '#00FFFF')

        self.configure(bg=bg)
        self.sample_button.configure(bg=accent, fg='#000000')
        self.sample_label.configure(bg=bg, fg=fg)
        self.sample_entry.configure(bg=theme.get('bg_panel', '#2d2d2d'), fg=fg)
        self.sample_frame.configure(bg=theme.get('bg_blue', '#001B3F'))


class ThemeDesigner(tk.Frame):
    """Complete theme designer with all features"""

    def __init__(self, parent, base_path: Path = None, on_apply=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg='#1e1e1e')

        self.base_path = base_path or Path.cwd()
        self.on_apply = on_apply
        self.current_theme = self._get_default_theme()
        self.preset_themes = self._load_preset_themes()

        self._build_ui()
        self._update_preview()

    def _custom_theme_root(self) -> Path:
        return Path(TRINITY_THEMES) / "custom"

    def _active_theme_path(self) -> Path:
        return Path(TRINITY_SETTINGS) / "active_theme.json"

    def _build_ui(self):
        """Build theme designer UI"""
        # Title
        tk.Label(self, text="Theme Designer",
                bg='#1e1e1e', fg='#00FFFF',
                font=('Arial', 18, 'bold')).pack(pady=20)

        # Main container
        main = tk.Frame(self, bg='#1e1e1e')
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Left panel - Color pickers
        left_panel = tk.Frame(main, bg='#2d2d2d', width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_panel.pack_propagate(False)

        tk.Label(left_panel, text="Color Customization",
                bg='#2d2d2d', fg='#ffffff',
                font=('Arial', 14, 'bold')).pack(pady=10)

        # Color categories
        self.color_entries = {}
        categories = [
            ('bg_dark', 'Background Dark'),
            ('bg_blue', 'Background Blue'),
            ('bg_panel', 'Panel Background'),
            ('accent_cyan', 'Accent Cyan'),
            ('accent_magenta', 'Accent Magenta'),
            ('text_white', 'Text White'),
            ('text_green', 'Text Green'),
            ('border_blue', 'Border Blue')
        ]

        for color_key, label in categories:
            self._create_color_picker(left_panel, color_key, label)

        # Preset themes
        preset_frame = tk.LabelFrame(left_panel, text="Preset Themes",
                                     bg='#2d2d2d', fg='#ffffff',
                                     font=('Arial', 11, 'bold'))
        preset_frame.pack(fill=tk.X, padx=10, pady=10)

        preset_btn = tk.Menubutton(
            preset_frame,
            text="Preset Themes",
            bg='#0e639c',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief='raised',
            width=20,
        )
        preset_menu = tk.Menu(preset_btn, tearoff=0)
        for theme_name in self.preset_themes.keys():
            preset_menu.add_command(label=theme_name, command=lambda n=theme_name: self._load_preset(n))
        preset_btn.config(menu=preset_menu)
        preset_btn.pack(pady=8, padx=5)

        # Right panel - Preview and actions
        right_panel = tk.Frame(main, bg='#1e1e1e')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Preview
        self.preview = ThemePreview(right_panel, bg='#2d2d2d')
        self.preview.pack(fill=tk.BOTH, expand=True, pady=10)

        # Actions
        action_frame = tk.Frame(right_panel, bg='#1e1e1e')
        action_frame.pack(fill=tk.X, pady=10)

        action_btn = tk.Menubutton(
            action_frame,
            text="Theme Actions",
            bg='#5cb85c',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief='raised',
            width=18,
        )
        action_menu = tk.Menu(action_btn, tearoff=0)
        action_menu.add_command(label="Save Theme", command=self._save_theme)
        action_menu.add_command(label="Load Theme", command=self._load_theme)
        action_menu.add_command(label="Apply Theme", command=self._apply_theme)
        action_menu.add_command(label="Export JSON", command=self._export_theme)
        action_btn.config(menu=action_menu)
        action_btn.pack(side=tk.LEFT, padx=5)

    def _create_color_picker(self, parent, color_key: str, label: str):
        """Create a color picker row"""
        frame = tk.Frame(parent, bg='#2d2d2d')
        frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frame, text=label, bg='#2d2d2d', fg='#ffffff',
                font=('Arial', 10), width=20, anchor='w').pack(side=tk.LEFT)

        entry = tk.Entry(frame, font=('Consolas', 10), width=10)
        entry.insert(0, self.current_theme.get(color_key, '#000000'))
        entry.pack(side=tk.LEFT, padx=5)

        self.color_entries[color_key] = entry

        # Color preview
        preview = tk.Canvas(frame, width=30, height=20,
                           bg=self.current_theme.get(color_key, '#000000'),
                           highlightthickness=1, highlightbackground='#ffffff')
        preview.pack(side=tk.LEFT, padx=5)

        # Pick button
        def pick_color():
            color = colorchooser.askcolor(
                initialcolor=entry.get(),
                title=f"Choose {label}"
            )
            if color[1]:
                entry.delete(0, tk.END)
                entry.insert(0, color[1])
                preview.configure(bg=color[1])
                self.current_theme[color_key] = color[1]
                self._update_preview()

        tk.Button(frame, text="Pick", command=pick_color,
                 bg='#0e639c', fg='white',
                 font=('Arial', 8), width=5).pack(side=tk.LEFT)

    def _update_preview(self):
        """Update preview with current theme"""
        self.preview.apply_theme(self.current_theme)

    def _get_default_theme(self) -> Dict[str, str]:
        """Get default LightSpeed theme"""
        return {
            'bg_dark': '#000B1F',
            'bg_blue': '#001B3F',
            'bg_panel': '#002855',
            'accent_cyan': '#00FFFF',
            'accent_magenta': '#FF00FF',
            'accent_pink': '#FF0088',
            'text_green': '#00FF88',
            'text_cyan': '#00DDFF',
            'text_white': '#FFFFFF',
            'border_blue': '#0055FF',
            'button_green': '#00AA00',
            'error_red': '#FF3333',
            'warning_orange': '#FF9900',
            'success_green': '#00FF00'
        }

    def _load_preset_themes(self) -> Dict[str, Dict[str, str]]:
        """Load preset theme library"""
        return {
            'LightSpeed Default': self._get_default_theme(),
            'Dark Matrix': {
                'bg_dark': '#0d0d0d',
                'bg_blue': '#1a1a1a',
                'bg_panel': '#262626',
                'accent_cyan': '#00ff00',
                'accent_magenta': '#00ff00',
                'text_white': '#00ff00',
                'text_green': '#00ff00',
                'border_blue': '#00ff00'
            },
            'Ocean Blue': {
                'bg_dark': '#0a1929',
                'bg_blue': '#0f2942',
                'bg_panel': '#1a3a52',
                'accent_cyan': '#66d9ef',
                'accent_magenta': '#ae81ff',
                'text_white': '#f8f8f2',
                'text_green': '#a6e22e',
                'border_blue': '#3daee9'
            },
            'Sunset Orange': {
                'bg_dark': '#2b1b17',
                'bg_blue': '#3e2723',
                'bg_panel': '#4e342e',
                'accent_cyan': '#ff9800',
                'accent_magenta': '#ff5722',
                'text_white': '#ffccbc',
                'text_green': '#ffab91',
                'border_blue': '#d84315'
            },
            'Arctic White': {
                'bg_dark': '#eceff1',
                'bg_blue': '#cfd8dc',
                'bg_panel': '#b0bec5',
                'accent_cyan': '#0288d1',
                'accent_magenta': '#7b1fa2',
                'text_white': '#263238',
                'text_green': '#00796b',
                'border_blue': '#01579b'
            }
        }

    def _load_preset(self, theme_name: str):
        """Load a preset theme"""
        if theme_name in self.preset_themes:
            self.current_theme = self.preset_themes[theme_name].copy()

            # Update all entry fields
            for color_key, entry in self.color_entries.items():
                if color_key in self.current_theme:
                    entry.delete(0, tk.END)
                    entry.insert(0, self.current_theme[color_key])

            self._update_preview()
            messagebox.showinfo("Theme Loaded", f"Loaded preset theme: {theme_name}")

    def _save_theme(self):
        """Save current theme"""
        # Update theme from entries
        for color_key, entry in self.color_entries.items():
            self.current_theme[color_key] = entry.get()

        # Ask for theme name
        name = tk.simpledialog.askstring("Save Theme", "Enter theme name:")
        if name:
            themes_file = self._custom_theme_root() / f"{name}.json"
            themes_file.parent.mkdir(parents=True, exist_ok=True)

            themes_file.write_text(json.dumps(self.current_theme, indent=2))
            messagebox.showinfo("Success", f"Theme saved: {name}")

    def _load_theme(self):
        """Load theme from file"""
        filepath = filedialog.askopenfilename(
            title="Load Theme",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filepath:
            try:
                theme_data = json.loads(Path(filepath).read_text())
                self.current_theme = theme_data

                # Update entries
                for color_key, entry in self.color_entries.items():
                    if color_key in theme_data:
                        entry.delete(0, tk.END)
                        entry.insert(0, theme_data[color_key])

                self._update_preview()
                messagebox.showinfo("Success", "Theme loaded successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load theme:\n{e}")

    def _export_theme(self):
        """Export theme to JSON"""
        # Update theme from entries
        for color_key, entry in self.color_entries.items():
            self.current_theme[color_key] = entry.get()

        filepath = filedialog.asksaveasfilename(
            title="Export Theme",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filepath:
            try:
                Path(filepath).write_text(json.dumps(self.current_theme, indent=2))
                messagebox.showinfo("Success", f"Theme exported to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export theme:\n{e}")

    def _apply_theme(self):
        """Apply theme to entire application"""
        # Update theme from entries
        for color_key, entry in self.color_entries.items():
            self.current_theme[color_key] = entry.get()

        applied = False
        if callable(self.on_apply):
            try:
                self.on_apply(dict(self.current_theme))
                applied = True
            except Exception as e:
                messagebox.showerror("Apply Theme", f"Failed to apply theme:\n{e}")
                applied = False

        if applied:
            messagebox.showinfo("Apply Theme", "Theme applied to the live UI.")
        else:
            messagebox.showinfo(
                "Apply Theme",
                "Theme saved.\n\n"
                "Live theme application is not available in this context."
            )

        # Save as active theme
        active_theme_file = self._active_theme_path()
        active_theme_file.parent.mkdir(parents=True, exist_ok=True)
        active_theme_file.write_text(json.dumps(self.current_theme, indent=2))


# Demo/Test
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Theme Designer - Test")
    root.geometry("1200x800")

    designer = ThemeDesigner(root, base_path=Path.cwd())
    designer.pack(fill='both', expand=True)

    root.mainloop()
