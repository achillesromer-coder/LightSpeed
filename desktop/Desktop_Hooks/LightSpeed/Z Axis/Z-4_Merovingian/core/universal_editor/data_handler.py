"""
Data File Handler - V1.0.0
Handler for structured data files (JSON, YAML, CSV, XML)

Author: LightSpeed Team
Date: December 27, 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import List, Optional
import json
import csv

from .file_handler import FileHandler, EditorCapability, EditorAction


# ==============================================================================
# Data File Handler
# ==============================================================================

class DataFileHandler(FileHandler):
    """
    Handler for structured data files

    Supports:
    - JSON (with validation and formatting)
    - YAML (basic support)
    - CSV (with table view)
    - XML (basic support)
    """

    def __init__(self):
        """Initialize data file handler"""
        super().__init__()

        self.file_type_name = "Data"
        self.supported_extensions = ['.json', '.yaml', '.yml', '.csv', '.xml', '.toml']

        self.capabilities = [
            EditorCapability.READ,
            EditorCapability.WRITE,
            EditorCapability.FORMAT,
            EditorCapability.SYNTAX_HIGHLIGHT,
            EditorCapability.SEARCH,
            EditorCapability.REPLACE,
        ]

        self.current_widget: Optional[tk.Text] = None
        self.current_file: Optional[Path] = None

    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can handle the file"""
        return file_path.suffix.lower() in self.supported_extensions

    def read_file(self, file_path: Path) -> str:
        """Read data file"""
        return file_path.read_text(encoding='utf-8')

    def write_file(self, file_path: Path, content: str) -> bool:
        """Write data file"""
        file_path.write_text(content, encoding='utf-8')
        return True

    def create_editor_widget(
        self,
        parent: tk.Widget,
        file_path: Path,
        content: str,
        **kwargs
    ) -> tk.Widget:
        """Create data editor widget"""
        self.current_file = file_path

        # For CSV, show table view
        if file_path.suffix.lower() == '.csv':
            return self._create_csv_editor(parent, content)
        else:
            return self._create_text_editor(parent, content)

    def _create_text_editor(self, parent: tk.Widget, content: str) -> tk.Widget:
        """Create text-based editor for JSON/YAML/XML"""
        container = ttk.Frame(parent)

        # Text widget with scrollbar
        text_frame = ttk.Frame(container)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(
            text_frame,
            wrap=tk.NONE,
            yscrollcommand=scrollbar.set,
            undo=True,
            font=('Consolas', 10)
        )
        text_widget.pack(fill=tk.BOTH, expand=True)

        scrollbar.config(command=text_widget.yview)

        # Insert content
        text_widget.insert('1.0', content)
        text_widget.edit_modified(False)

        # Apply syntax highlighting for JSON
        if self.current_file.suffix.lower() == '.json':
            self._apply_json_highlighting(text_widget)

        self.current_widget = text_widget
        return container

    def _create_csv_editor(self, parent: tk.Widget, content: str) -> tk.Widget:
        """Create table view for CSV"""
        container = ttk.Frame(parent)

        # Parse CSV
        lines = content.strip().split('\n')
        reader = csv.reader(lines)
        rows = list(reader)

        if not rows:
            return container

        # Create Treeview
        tree_frame = ttk.Frame(container)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview
        headers = rows[0]
        tree = ttk.Treeview(
            tree_frame,
            columns=headers,
            show='headings',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        tree.pack(fill=tk.BOTH, expand=True)

        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

        # Setup columns
        for header in headers:
            tree.heading(header, text=header)
            tree.column(header, width=100)

        # Insert rows
        for row in rows[1:]:
            if len(row) == len(headers):
                tree.insert('', tk.END, values=row)

        self.current_widget = tree
        return container

    def get_content_from_widget(self, widget: tk.Widget) -> str:
        """Get content from widget"""
        for child in widget.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Text):
                        return subchild.get('1.0', 'end-1c')
                    elif isinstance(subchild, ttk.Treeview):
                        # Convert Treeview back to CSV
                        return self._treeview_to_csv(subchild)
        return ""

    def _treeview_to_csv(self, tree: ttk.Treeview) -> str:
        """Convert Treeview to CSV string"""
        lines = []

        # Headers
        headers = tree['columns']
        lines.append(','.join(headers))

        # Rows
        for item in tree.get_children():
            values = tree.item(item)['values']
            lines.append(','.join(str(v) for v in values))

        return '\n'.join(lines)

    def get_toolbar_actions(self) -> List[EditorAction]:
        """Get toolbar actions"""
        actions = [
            EditorAction(
                action_id="format",
                label="Format",
                callback=self._format_data,
                tooltip="Format and prettify data"
            ),
            EditorAction(
                action_id="validate",
                label="Validate",
                callback=self._validate_data,
                tooltip="Validate data structure"
            ),
        ]

        if self.current_file and self.current_file.suffix.lower() == '.json':
            actions.append(EditorAction(
                action_id="minify",
                label="Minify",
                callback=self._minify_json,
                tooltip="Minify JSON"
            ))

        return actions

    def _format_data(self):
        """Format data"""
        if not self.current_widget:
            return

        if isinstance(self.current_widget, tk.Text):
            content = self.current_widget.get('1.0', 'end-1c')

            try:
                if self.current_file.suffix.lower() == '.json':
                    # Parse and format JSON
                    data = json.loads(content)
                    formatted = json.dumps(data, indent=2)

                    self.current_widget.delete('1.0', tk.END)
                    self.current_widget.insert('1.0', formatted)

                    messagebox.showinfo("Success", "JSON formatted successfully")
            except Exception as e:
                messagebox.showerror("Format Error", f"Failed to format: {e}")

    def _validate_data(self):
        """Validate data"""
        if not self.current_widget or not isinstance(self.current_widget, tk.Text):
            return

        content = self.current_widget.get('1.0', 'end-1c')

        try:
            if self.current_file.suffix.lower() == '.json':
                json.loads(content)
                messagebox.showinfo("Validation", "Valid JSON")
        except Exception as e:
            messagebox.showerror("Validation Error", f"Invalid data: {e}")

    def _minify_json(self):
        """Minify JSON"""
        if not self.current_widget or not isinstance(self.current_widget, tk.Text):
            return

        content = self.current_widget.get('1.0', 'end-1c')

        try:
            data = json.loads(content)
            minified = json.dumps(data, separators=(',', ':'))

            self.current_widget.delete('1.0', tk.END)
            self.current_widget.insert('1.0', minified)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to minify: {e}")

    def _apply_json_highlighting(self, text_widget: tk.Text):
        """Apply JSON syntax highlighting"""
        text_widget.tag_config('key', foreground='#92c5f7')
        text_widget.tag_config('string', foreground='#ce9178')
        text_widget.tag_config('number', foreground='#b5cea8')
        text_widget.tag_config('boolean', foreground='#569cd6')
        text_widget.tag_config('null', foreground='#569cd6')

        def highlight(event=None):
            import re

            for tag in ['key', 'string', 'number', 'boolean', 'null']:
                text_widget.tag_remove(tag, '1.0', tk.END)

            content = text_widget.get('1.0', 'end-1c')

            # Keys
            for match in re.finditer(r'"([^"]+)"\s*:', content):
                start = f'1.0+{match.start()}c'
                end = f'1.0+{match.end()-1}c'
                text_widget.tag_add('key', start, end)

            # Strings (not keys)
            for match in re.finditer(r':\s*"([^"]*)"', content):
                start = f'1.0+{match.start()+1}c'
                end = f'1.0+{match.end()}c'
                text_widget.tag_add('string', start, end)

            # Numbers
            for match in re.finditer(r':\s*(\d+\.?\d*)', content):
                start = f'1.0+{match.start(1)}c'
                end = f'1.0+{match.end(1)}c'
                text_widget.tag_add('number', start, end)

            # Booleans
            for match in re.finditer(r'\b(true|false)\b', content):
                start = f'1.0+{match.start()}c'
                end = f'1.0+{match.end()}c'
                text_widget.tag_add('boolean', start, end)

            # Null
            for match in re.finditer(r'\bnull\b', content):
                start = f'1.0+{match.start()}c'
                end = f'1.0+{match.end()}c'
                text_widget.tag_add('null', start, end)

        text_widget.bind('<KeyRelease>', lambda e: text_widget.after(100, highlight))
        highlight()

    def validate_content(self, content: str) -> tuple[bool, List[str]]:
        """Validate content"""
        errors = []

        try:
            if self.current_file.suffix.lower() == '.json':
                json.loads(content)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")

        return len(errors) == 0, errors
