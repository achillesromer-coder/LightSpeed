"""
Widget Base - Foundation for all Trinity UI widgets

Provides consistent UI patterns across all interface components.
Follows Clean Code principles for UI consistency and reusability.

Features:
- Consistent dark theme styling
- Standard toolbar/statusbar patterns
- Event handling infrastructure
- Common UI utilities
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, Any, List
from abc import ABC, abstractmethod
from dataclasses import dataclass


# ============================================================================
# Theme Configuration
# ============================================================================

@dataclass
class ThemeColors:
    """Dark theme color palette"""
    background: str = "#1e1e1e"
    secondary_bg: str = "#2d2d2d"
    tertiary_bg: str = "#3d3d3d"
    foreground: str = "white"
    secondary_fg: str = "#858585"
    primary_action: str = "#0088FE"
    success: str = "#00C49F"
    warning: str = "#FFBB28"
    error: str = "#FF8042"
    accent: str = "#00d4ff"
    border: str = "#404040"

# Global theme instance
DARK_THEME = ThemeColors()


# ============================================================================
# Abstract Widget Base
# ============================================================================

class LightSpeedWidget(tk.Frame, ABC):
    """
    Base class for all LightSpeed UI widgets

    Provides:
    - Consistent dark theme styling
    - Standard toolbar and status bar
    - Event bus integration
    - Common UI patterns

    Subclasses must implement:
    - _build_main_content(): Create the main widget content
    """

    def __init__(self, parent, title: str = "LightSpeed Widget"):
        super().__init__(parent, bg=DARK_THEME.background)

        self.title = title
        self.theme = DARK_THEME
        self.toolbar: Optional[tk.Frame] = None
        self.content_frame: Optional[tk.Frame] = None
        self.statusbar: Optional[tk.Frame] = None
        self.status_label: Optional[tk.Label] = None

        self._build_ui()

    def _build_ui(self):
        """Build standard widget structure"""
        # Toolbar (optional - can be overridden)
        if self._should_show_toolbar():
            self.toolbar = self._create_toolbar()
            self.toolbar.pack(fill='x', padx=5, pady=5)

        # Main content area
        self.content_frame = tk.Frame(self, bg=DARK_THEME.secondary_bg)
        self.content_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Build widget-specific content
        self._build_main_content()

        # Status bar (optional - can be overridden)
        if self._should_show_statusbar():
            self.statusbar = self._create_statusbar()
            self.statusbar.pack(fill='x', side='bottom')

    @abstractmethod
    def _build_main_content(self):
        """Build main widget content - must be implemented by subclasses"""
        pass

    def _should_show_toolbar(self) -> bool:
        """Override to hide toolbar"""
        return True

    def _should_show_statusbar(self) -> bool:
        """Override to hide status bar"""
        return True

    def _create_toolbar(self) -> tk.Frame:
        """Create standard toolbar - can be overridden"""
        toolbar = tk.Frame(self, bg=DARK_THEME.tertiary_bg, height=40)

        # Title label
        title_label = tk.Label(
            toolbar,
            text=self.title,
            font=('Arial', 12, 'bold'),
            bg=DARK_THEME.tertiary_bg,
            fg=DARK_THEME.foreground
        )
        title_label.pack(side='left', padx=10)

        return toolbar

    def _create_statusbar(self) -> tk.Frame:
        """Create standard status bar"""
        statusbar = tk.Frame(self, bg=DARK_THEME.tertiary_bg, height=25)

        self.status_label = tk.Label(
            statusbar,
            text="Ready",
            font=('Arial', 9),
            bg=DARK_THEME.tertiary_bg,
            fg=DARK_THEME.secondary_fg,
            anchor='w'
        )
        self.status_label.pack(side='left', padx=10, fill='x', expand=True)

        return statusbar

    def set_status(self, message: str, level: str = "info"):
        """
        Update status bar message

        Args:
            message: Status message
            level: info, success, warning, error
        """
        if self.status_label:
            color = {
                'info': DARK_THEME.secondary_fg,
                'success': DARK_THEME.success,
                'warning': DARK_THEME.warning,
                'error': DARK_THEME.error
            }.get(level, DARK_THEME.secondary_fg)

            self.status_label.config(text=message, fg=color)

    def add_toolbar_button(
        self,
        text: str,
        command: Callable,
        icon: Optional[str] = None,
        side: str = 'left'
    ) -> tk.Button:
        """Add button to toolbar"""
        if not self.toolbar:
            raise ValueError("Toolbar not enabled")

        display_text = f"{icon} {text}" if icon else text

        btn = tk.Button(
            self.toolbar,
            text=display_text,
            command=command,
            bg=DARK_THEME.primary_action,
            fg=DARK_THEME.foreground,
            relief='flat',
            padx=15,
            pady=5,
            cursor='hand2'
        )
        btn.pack(side=side, padx=5)

        # Hover effects
        btn.bind('<Enter>', lambda e: btn.config(bg=DARK_THEME.accent))
        btn.bind('<Leave>', lambda e: btn.config(bg=DARK_THEME.primary_action))

        return btn

    def add_toolbar_separator(self):
        """Add visual separator to toolbar"""
        if self.toolbar:
            sep = tk.Frame(
                self.toolbar,
                width=2,
                bg=DARK_THEME.border
            )
            sep.pack(side='left', fill='y', padx=10)

    def create_styled_button(
        self,
        parent,
        text: str,
        command: Callable,
        style: str = 'primary'
    ) -> tk.Button:
        """
        Create themed button

        Args:
            parent: Parent widget
            text: Button text
            command: Click callback
            style: primary, success, warning, error
        """
        color_map = {
            'primary': DARK_THEME.primary_action,
            'success': DARK_THEME.success,
            'warning': DARK_THEME.warning,
            'error': DARK_THEME.error
        }

        bg_color = color_map.get(style, DARK_THEME.primary_action)

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg=DARK_THEME.foreground,
            relief='flat',
            padx=15,
            pady=5,
            cursor='hand2'
        )

        # Hover effect
        def on_enter(e):
            btn.config(bg=self._lighten_color(bg_color))

        def on_leave(e):
            btn.config(bg=bg_color)

        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)

        return btn

    def create_styled_entry(
        self,
        parent,
        placeholder: str = "",
        **kwargs
    ) -> tk.Entry:
        """Create themed text entry"""
        entry = tk.Entry(
            parent,
            bg=DARK_THEME.secondary_bg,
            fg=DARK_THEME.foreground,
            insertbackground=DARK_THEME.foreground,
            relief='flat',
            **kwargs
        )

        # Placeholder text handling
        if placeholder:
            entry.insert(0, placeholder)
            entry.config(fg=DARK_THEME.secondary_fg)

            def on_focus_in(e):
                if entry.get() == placeholder:
                    entry.delete(0, 'end')
                    entry.config(fg=DARK_THEME.foreground)

            def on_focus_out(e):
                if not entry.get():
                    entry.insert(0, placeholder)
                    entry.config(fg=DARK_THEME.secondary_fg)

            entry.bind('<FocusIn>', on_focus_in)
            entry.bind('<FocusOut>', on_focus_out)

        return entry

    def create_styled_label(
        self,
        parent,
        text: str,
        style: str = 'normal'
    ) -> tk.Label:
        """
        Create themed label

        Args:
            parent: Parent widget
            text: Label text
            style: normal, heading, subheading, caption
        """
        font_map = {
            'normal': ('Arial', 10),
            'heading': ('Arial', 14, 'bold'),
            'subheading': ('Arial', 12, 'bold'),
            'caption': ('Arial', 9)
        }

        label = tk.Label(
            parent,
            text=text,
            font=font_map.get(style, ('Arial', 10)),
            bg=DARK_THEME.secondary_bg,
            fg=DARK_THEME.foreground
        )

        return label

    def show_error(self, title: str, message: str):
        """Show error dialog"""
        messagebox.showerror(title, message)
        self.set_status(f"Error: {message}", level="error")

    def show_success(self, title: str, message: str):
        """Show success dialog"""
        messagebox.showinfo(title, message)
        self.set_status(message, level="success")

    def show_warning(self, title: str, message: str):
        """Show warning dialog"""
        messagebox.showwarning(title, message)
        self.set_status(f"Warning: {message}", level="warning")

    def confirm(self, title: str, message: str) -> bool:
        """Show confirmation dialog"""
        return messagebox.askyesno(title, message)

    @staticmethod
    def _lighten_color(hex_color: str, factor: float = 1.2) -> str:
        """Lighten a hex color"""
        # Remove '#'
        hex_color = hex_color.lstrip('#')

        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Lighten
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))

        # Convert back to hex
        return f'#{r:02x}{g:02x}{b:02x}'


# ============================================================================
# Specialized Widget Bases
# ============================================================================

class EditorWidget(LightSpeedWidget):
    """Base for editor-style widgets (text, code, etc.)"""

    def __init__(self, parent, title: str = "Editor"):
        self.text_widget: Optional[tk.Text] = None
        super().__init__(parent, title)

    def _build_main_content(self):
        """Create text editing area"""
        # Scrollbars
        y_scrollbar = tk.Scrollbar(self.content_frame)
        y_scrollbar.pack(side='right', fill='y')

        x_scrollbar = tk.Scrollbar(self.content_frame, orient='horizontal')
        x_scrollbar.pack(side='bottom', fill='x')

        # Text widget
        self.text_widget = tk.Text(
            self.content_frame,
            bg=DARK_THEME.background,
            fg=DARK_THEME.foreground,
            insertbackground=DARK_THEME.foreground,
            selectbackground=DARK_THEME.primary_action,
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set,
            wrap='none',
            font=('Consolas', 11)
        )
        self.text_widget.pack(fill='both', expand=True)

        y_scrollbar.config(command=self.text_widget.yview)
        x_scrollbar.config(command=self.text_widget.xview)

    def get_content(self) -> str:
        """Get editor content"""
        return self.text_widget.get('1.0', 'end-1c')

    def set_content(self, content: str):
        """Set editor content"""
        self.text_widget.delete('1.0', 'end')
        self.text_widget.insert('1.0', content)

    def clear(self):
        """Clear editor content"""
        self.text_widget.delete('1.0', 'end')


class TableWidget(LightSpeedWidget):
    """Base for table-style widgets"""

    def __init__(self, parent, title: str = "Table", columns: List[str] = None):
        self.columns = columns or []
        self.tree: Optional[ttk.Treeview] = None
        super().__init__(parent, title)

    def _build_main_content(self):
        """Create treeview table"""
        # Scrollbars
        y_scrollbar = tk.Scrollbar(self.content_frame)
        y_scrollbar.pack(side='right', fill='y')

        x_scrollbar = tk.Scrollbar(self.content_frame, orient='horizontal')
        x_scrollbar.pack(side='bottom', fill='x')

        # Treeview
        self.tree = ttk.Treeview(
            self.content_frame,
            columns=self.columns,
            show='headings',
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )
        self.tree.pack(fill='both', expand=True)

        # Configure columns
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        y_scrollbar.config(command=self.tree.yview)
        x_scrollbar.config(command=self.tree.xview)

    def insert_row(self, values: List[Any]):
        """Insert row into table"""
        self.tree.insert('', 'end', values=values)

    def clear_rows(self):
        """Clear all rows"""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def get_selected(self) -> Optional[List[Any]]:
        """Get selected row values"""
        selection = self.tree.selection()
        if selection:
            return self.tree.item(selection[0])['values']
        return None


# ============================================================================
# Example Usage
# ============================================================================

class ExampleWidget(LightSpeedWidget):
    """Example widget implementation"""

    def _build_main_content(self):
        """Build example content"""
        label = self.create_styled_label(
            self.content_frame,
            "Example LightSpeed Widget",
            style='heading'
        )
        label.pack(pady=20)

        button = self.create_styled_button(
            self.content_frame,
            "Click Me",
            self._on_button_click,
            style='primary'
        )
        button.pack(pady=10)

    def _on_button_click(self):
        """Handle button click"""
        self.show_success("Success", "Button clicked!")


if __name__ == "__main__":
    # Test widget base
    root = tk.Tk()
    root.title("Widget Base Test")
    root.geometry("800x600")
    root.configure(bg=DARK_THEME.background)

    widget = ExampleWidget(root, title="Test Widget")
    widget.pack(fill='both', expand=True)

    # Add toolbar buttons
    widget.add_toolbar_button("Save", lambda: widget.set_status("Saved!", "success"), "💾")
    widget.add_toolbar_button("Load", lambda: widget.set_status("Loaded!", "info"), "📂")
    widget.add_toolbar_separator()
    widget.add_toolbar_button("Settings", lambda: widget.set_status("Settings opened"), "⚙")

    print("✅ Widget base test running...")
    root.mainloop()
