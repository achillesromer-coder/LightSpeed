"""
Jupyter Notebook File Handler - V1.0.0
Handle Jupyter notebook files (.ipynb) with cell-based editing

Author: LightSpeed Team
Date: December 28, 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import json
import re

from .file_handler import FileHandler, EditorAction, EditorCapability


# ==============================================================================
# Notebook Data Structures
# ==============================================================================

@dataclass
class NotebookCell:
    """Represents a Jupyter notebook cell"""
    cell_type: str  # 'code', 'markdown', 'raw'
    source: List[str]  # Cell content as list of lines
    metadata: Dict[str, Any] = field(default_factory=dict)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    execution_count: Optional[int] = None

    def get_source_text(self) -> str:
        """Get cell source as single string"""
        if isinstance(self.source, list):
            return ''.join(self.source)
        return str(self.source)

    def set_source_text(self, text: str):
        """Set cell source from string"""
        self.source = text.split('\n')


@dataclass
class NotebookMetadata:
    """Notebook-level metadata"""
    kernelspec: Dict[str, str] = field(default_factory=dict)
    language_info: Dict[str, Any] = field(default_factory=dict)
    nbformat: int = 4
    nbformat_minor: int = 5


# ==============================================================================
# Jupyter Notebook Handler
# ==============================================================================

class NotebookFileHandler(FileHandler):
    """
    Handler for Jupyter notebook files (.ipynb)

    Supported formats:
    - .ipynb (Jupyter Notebook)

    Features:
    - Cell-based editing (code and markdown cells)
    - Cell execution visualization (shows outputs)
    - Add/remove/reorder cells
    - Cell type conversion
    - JSON validation
    - Kernel information display
    - Markdown rendering preview
    - Output display (text, images, errors)
    """

    SUPPORTED_EXTENSIONS = {'.ipynb'}

    def __init__(self):
        """Initialize notebook handler"""
        super().__init__()
        self.file_type_name = "Jupyter Notebook"
        self.capabilities = [
            EditorCapability.READ,
            EditorCapability.WRITE,
            EditorCapability.SYNTAX_HIGHLIGHT,
            EditorCapability.PREVIEW,
            EditorCapability.SEARCH,
            EditorCapability.REPLACE
        ]
        self.supported_extensions = list(self.SUPPORTED_EXTENSIONS)

        self.cells: List[NotebookCell] = []
        self.metadata: NotebookMetadata = NotebookMetadata()
        self.cell_widgets: List[tk.Frame] = []
        self.notebook_container: Optional[tk.Widget] = None

    def can_handle(self, file_path: Path) -> bool:
        """Check if can handle this notebook file"""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def read_file(self, file_path: Path) -> str:
        """Read notebook file and parse JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                notebook_data = json.load(f)

            # Parse metadata
            metadata_dict = notebook_data.get('metadata', {})
            self.metadata = NotebookMetadata(
                kernelspec=metadata_dict.get('kernelspec', {}),
                language_info=metadata_dict.get('language_info', {}),
                nbformat=notebook_data.get('nbformat', 4),
                nbformat_minor=notebook_data.get('nbformat_minor', 5)
            )

            # Parse cells
            self.cells = []
            for cell_data in notebook_data.get('cells', []):
                cell = NotebookCell(
                    cell_type=cell_data.get('cell_type', 'code'),
                    source=cell_data.get('source', []),
                    metadata=cell_data.get('metadata', {}),
                    outputs=cell_data.get('outputs', []),
                    execution_count=cell_data.get('execution_count')
                )
                self.cells.append(cell)

            # Return summary for display
            return self._generate_summary()

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid notebook JSON: {e}")
        except Exception as e:
            raise IOError(f"Failed to read notebook: {e}")

    def _generate_summary(self) -> str:
        """Generate notebook summary"""
        code_cells = sum(1 for c in self.cells if c.cell_type == 'code')
        markdown_cells = sum(1 for c in self.cells if c.cell_type == 'markdown')

        summary = f"Jupyter Notebook\n\n"
        summary += f"Cells: {len(self.cells)} total\n"
        summary += f"  - Code: {code_cells}\n"
        summary += f"  - Markdown: {markdown_cells}\n"
        summary += f"  - Other: {len(self.cells) - code_cells - markdown_cells}\n\n"

        kernel = self.metadata.kernelspec.get('display_name', 'Unknown')
        language = self.metadata.language_info.get('name', 'Unknown')
        summary += f"Kernel: {kernel}\n"
        summary += f"Language: {language}\n"
        summary += f"Format: nbformat {self.metadata.nbformat}.{self.metadata.nbformat_minor}\n"

        return summary

    def write_file(self, file_path: Path, content: str) -> bool:
        """Write notebook to file as JSON"""
        try:
            # Build notebook structure
            notebook_data = {
                'cells': [],
                'metadata': {
                    'kernelspec': self.metadata.kernelspec,
                    'language_info': self.metadata.language_info
                },
                'nbformat': self.metadata.nbformat,
                'nbformat_minor': self.metadata.nbformat_minor
            }

            # Add cells
            for cell in self.cells:
                cell_data = {
                    'cell_type': cell.cell_type,
                    'source': cell.source,
                    'metadata': cell.metadata
                }

                if cell.cell_type == 'code':
                    cell_data['outputs'] = cell.outputs
                    cell_data['execution_count'] = cell.execution_count

                notebook_data['cells'].append(cell_data)

            # Write JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(notebook_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save notebook: {e}")
            return False

    def create_editor_widget(
        self,
        parent: tk.Widget,
        file_path: Path,
        content: str,
        **kwargs
    ) -> tk.Widget:
        """Create notebook editor widget with cell-based interface"""
        # Main container
        main_container = tk.Frame(parent)

        # Toolbar
        toolbar = self._create_toolbar(main_container)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Scrollable notebook container
        canvas_frame = tk.Frame(main_container)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Canvas with scrollbar
        canvas = tk.Canvas(canvas_frame, bg='#1e1e1e')
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)

        canvas.configure(yscrollcommand=v_scrollbar.set)

        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Container for cells
        self.notebook_container = tk.Frame(canvas, bg='#1e1e1e')
        canvas_window = canvas.create_window(0, 0, anchor=tk.NW, window=self.notebook_container)

        # Bind resize
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.notebook_container.bind("<Configure>", on_frame_configure)

        # Bind canvas resize to update window width
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)

        # Create cell widgets
        self.cell_widgets = []
        for idx, cell in enumerate(self.cells):
            cell_widget = self._create_cell_widget(self.notebook_container, idx, cell)
            cell_widget.pack(fill=tk.X, padx=10, pady=5)
            self.cell_widgets.append(cell_widget)

        # Store references
        main_container.canvas = canvas
        main_container.notebook_container = self.notebook_container
        main_container.file_path = file_path

        return main_container

    def _create_toolbar(self, parent: tk.Widget) -> tk.Frame:
        """Create notebook editor toolbar"""
        toolbar = tk.Frame(parent)

        # Cell operations
        cell_frame = tk.LabelFrame(toolbar, text="Cell Operations", padx=5, pady=2)
        cell_frame.pack(side=tk.LEFT, padx=2)

        tk.Button(cell_frame, text="+ Code", command=lambda: self._add_cell('code'), width=8).pack(side=tk.LEFT, padx=1)
        tk.Button(cell_frame, text="+ Markdown", command=lambda: self._add_cell('markdown'), width=10).pack(side=tk.LEFT, padx=1)
        tk.Button(cell_frame, text="Clear Outputs", command=self._clear_all_outputs, width=12).pack(side=tk.LEFT, padx=1)

        # Info
        info_frame = tk.LabelFrame(toolbar, text="Notebook Info", padx=5, pady=2)
        info_frame.pack(side=tk.LEFT, padx=2)

        kernel_name = self.metadata.kernelspec.get('display_name', 'Unknown')
        tk.Label(info_frame, text=f"Kernel: {kernel_name}", fg='#888888').pack(side=tk.LEFT, padx=5)
        tk.Label(info_frame, text=f"Cells: {len(self.cells)}", fg='#888888').pack(side=tk.LEFT, padx=5)

        return toolbar

    def _create_cell_widget(self, parent: tk.Widget, index: int, cell: NotebookCell) -> tk.Frame:
        """Create widget for a single notebook cell"""
        # Cell container
        cell_frame = tk.Frame(parent, bg='#2b2b2b', relief=tk.RAISED, borderwidth=1)

        # Cell header
        header = tk.Frame(cell_frame, bg='#1a1a1a', height=30)
        header.pack(fill=tk.X)

        # Cell type indicator
        cell_type_color = '#4ec9b0' if cell.cell_type == 'code' else '#569cd6'
        type_label = tk.Label(
            header,
            text=f"[{index + 1}] {cell.cell_type.upper()}",
            bg='#1a1a1a',
            fg=cell_type_color,
            font=('Consolas', 9, 'bold')
        )
        type_label.pack(side=tk.LEFT, padx=10, pady=5)

        # Execution count for code cells
        if cell.cell_type == 'code' and cell.execution_count is not None:
            exec_label = tk.Label(
                header,
                text=f"[{cell.execution_count}]",
                bg='#1a1a1a',
                fg='#888888',
                font=('Consolas', 9)
            )
            exec_label.pack(side=tk.LEFT, padx=5)

        # Cell controls
        controls_frame = tk.Frame(header, bg='#1a1a1a')
        controls_frame.pack(side=tk.RIGHT, padx=5)

        tk.Button(
            controls_frame,
            text="↑",
            command=lambda: self._move_cell_up(index),
            width=3,
            bg='#333333',
            fg='#ffffff'
        ).pack(side=tk.LEFT, padx=1)

        tk.Button(
            controls_frame,
            text="↓",
            command=lambda: self._move_cell_down(index),
            width=3,
            bg='#333333',
            fg='#ffffff'
        ).pack(side=tk.LEFT, padx=1)

        tk.Button(
            controls_frame,
            text="✕",
            command=lambda: self._delete_cell(index),
            width=3,
            bg='#661111',
            fg='#ffffff'
        ).pack(side=tk.LEFT, padx=1)

        # Cell content editor
        text_font = tkfont.Font(family="Consolas", size=10)
        text_widget = tk.Text(
            cell_frame,
            wrap=tk.WORD,
            height=max(3, min(20, len(cell.source))),
            font=text_font,
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='#ffffff',
            selectbackground='#264f78'
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Insert cell content
        content = cell.get_source_text()
        text_widget.insert('1.0', content)

        # Store text widget reference in cell frame
        cell_frame.text_widget = text_widget
        cell_frame.cell_index = index

        # Bind content changes to update cell
        text_widget.bind('<KeyRelease>', lambda e: self._update_cell_from_widget(index, text_widget))

        # Output display for code cells
        if cell.cell_type == 'code' and cell.outputs:
            output_frame = tk.Frame(cell_frame, bg='#252526')
            output_frame.pack(fill=tk.X, padx=5, pady=5)

            tk.Label(
                output_frame,
                text="Output:",
                bg='#252526',
                fg='#888888',
                font=('Consolas', 9, 'bold')
            ).pack(anchor=tk.W, padx=5, pady=2)

            # Display outputs
            for output in cell.outputs[:3]:  # Show first 3 outputs
                self._display_output(output_frame, output)

        return cell_frame

    def _display_output(self, parent: tk.Frame, output: Dict[str, Any]):
        """Display cell output"""
        output_type = output.get('output_type', '')

        output_text = tk.Text(
            parent,
            wrap=tk.WORD,
            height=5,
            bg='#1a1a1a',
            fg='#cccccc',
            font=('Consolas', 9)
        )
        output_text.pack(fill=tk.X, padx=5, pady=2)

        if output_type == 'stream':
            text = ''.join(output.get('text', []))
            output_text.insert('1.0', text)

        elif output_type == 'execute_result':
            data = output.get('data', {})
            text = data.get('text/plain', [''])[0] if 'text/plain' in data else str(data)
            output_text.insert('1.0', text)

        elif output_type == 'error':
            error_name = output.get('ename', 'Error')
            error_value = output.get('evalue', '')
            output_text.insert('1.0', f"{error_name}: {error_value}")
            output_text.configure(fg='#ff6b6b')

        else:
            output_text.insert('1.0', f"[{output_type} output]")

        output_text.configure(state=tk.DISABLED)

    def _update_cell_from_widget(self, index: int, text_widget: tk.Text):
        """Update cell content from text widget"""
        if 0 <= index < len(self.cells):
            content = text_widget.get('1.0', tk.END).rstrip('\n')
            self.cells[index].set_source_text(content)

    def _add_cell(self, cell_type: str):
        """Add new cell"""
        new_cell = NotebookCell(
            cell_type=cell_type,
            source=[]
        )
        self.cells.append(new_cell)
        self._refresh_display()

    def _delete_cell(self, index: int):
        """Delete cell at index"""
        if 0 <= index < len(self.cells):
            if messagebox.askyesno("Delete Cell", f"Delete cell {index + 1}?"):
                del self.cells[index]
                self._refresh_display()

    def _move_cell_up(self, index: int):
        """Move cell up"""
        if index > 0:
            self.cells[index], self.cells[index - 1] = self.cells[index - 1], self.cells[index]
            self._refresh_display()

    def _move_cell_down(self, index: int):
        """Move cell down"""
        if index < len(self.cells) - 1:
            self.cells[index], self.cells[index + 1] = self.cells[index + 1], self.cells[index]
            self._refresh_display()

    def _clear_all_outputs(self):
        """Clear outputs from all code cells"""
        for cell in self.cells:
            if cell.cell_type == 'code':
                cell.outputs = []
                cell.execution_count = None
        self._refresh_display()
        messagebox.showinfo("Outputs Cleared", "All cell outputs have been cleared")

    def _refresh_display(self):
        """Refresh the notebook display"""
        if not self.notebook_container:
            return

        # Clear existing widgets
        for widget in self.cell_widgets:
            widget.destroy()
        self.cell_widgets = []

        # Recreate cell widgets
        for idx, cell in enumerate(self.cells):
            cell_widget = self._create_cell_widget(self.notebook_container, idx, cell)
            cell_widget.pack(fill=tk.X, padx=10, pady=5)
            self.cell_widgets.append(cell_widget)

    def get_content_from_widget(self, widget: tk.Widget) -> str:
        """Extract current content from editor widget (returns JSON)"""
        # Update all cells from their widgets first
        for cell_widget in self.cell_widgets:
            if hasattr(cell_widget, 'text_widget') and hasattr(cell_widget, 'cell_index'):
                index = cell_widget.cell_index
                if 0 <= index < len(self.cells):
                    content = cell_widget.text_widget.get('1.0', tk.END).rstrip('\n')
                    self.cells[index].set_source_text(content)

        # Build notebook JSON
        notebook_data = {
            'cells': [],
            'metadata': {
                'kernelspec': self.metadata.kernelspec,
                'language_info': self.metadata.language_info
            },
            'nbformat': self.metadata.nbformat,
            'nbformat_minor': self.metadata.nbformat_minor
        }

        for cell in self.cells:
            cell_data = {
                'cell_type': cell.cell_type,
                'source': cell.source,
                'metadata': cell.metadata
            }

            if cell.cell_type == 'code':
                cell_data['outputs'] = cell.outputs
                cell_data['execution_count'] = cell.execution_count

            notebook_data['cells'].append(cell_data)

        return json.dumps(notebook_data, indent=2, ensure_ascii=False)

    def get_toolbar_actions(self) -> List[EditorAction]:
        """Get toolbar actions for notebook editor"""
        return [
            EditorAction(
                action_id='add_code',
                label='Add Code Cell',
                icon='📝',
                callback=lambda: self._add_cell('code'),
                tooltip='Add new code cell'
            ),
            EditorAction(
                action_id='add_markdown',
                label='Add Markdown Cell',
                icon='📄',
                callback=lambda: self._add_cell('markdown'),
                tooltip='Add new markdown cell'
            ),
            EditorAction(
                action_id='clear_outputs',
                label='Clear Outputs',
                icon='🧹',
                callback=self._clear_all_outputs,
                tooltip='Clear all cell outputs'
            ),
            EditorAction(
                action_id='validate',
                label='Validate',
                icon='✓',
                callback=self._validate_notebook,
                tooltip='Validate notebook structure'
            ),
        ]

    def _validate_notebook(self):
        """Validate notebook structure"""
        issues = []

        # Check nbformat
        if self.metadata.nbformat != 4:
            issues.append(f"Unexpected nbformat version: {self.metadata.nbformat} (expected 4)")

        # Check for empty cells
        empty_cells = [i + 1 for i, cell in enumerate(self.cells) if not cell.source]
        if empty_cells:
            issues.append(f"Empty cells found at positions: {empty_cells}")

        # Check kernelspec
        if not self.metadata.kernelspec.get('name'):
            issues.append("Missing kernel specification")

        if issues:
            msg = "Notebook validation found issues:\n\n" + '\n'.join(f"• {issue}" for issue in issues)
            messagebox.showwarning("Validation Issues", msg)
        else:
            messagebox.showinfo("Validation Passed", "Notebook structure is valid!")

    def validate_content(self, content: str) -> tuple[bool, List[str]]:
        """Validate notebook JSON"""
        try:
            data = json.loads(content)

            errors = []

            # Check required fields
            if 'cells' not in data:
                errors.append("Missing 'cells' field")

            if 'nbformat' not in data:
                errors.append("Missing 'nbformat' field")

            if 'metadata' not in data:
                errors.append("Missing 'metadata' field")

            return len(errors) == 0, errors

        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {e}"]

    def format_content(self, content: str) -> str:
        """Format notebook JSON with proper indentation"""
        try:
            data = json.loads(content)
            return json.dumps(data, indent=2, ensure_ascii=False)
        except:
            return content
