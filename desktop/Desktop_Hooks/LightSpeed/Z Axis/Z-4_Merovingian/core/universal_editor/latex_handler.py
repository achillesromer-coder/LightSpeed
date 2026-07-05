"""
LaTeX File Handler - V1.0.0
Handle LaTeX files with syntax highlighting and live preview

Author: LightSpeed Team
Date: December 28, 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
import re
import subprocess
import tempfile
import threading
import os

from .file_handler import FileHandler, EditorAction, EditorCapability

# Try to import PDF rendering libraries
try:
    from PIL import Image, ImageTk
    import pdf2image
    HAS_PDF_SUPPORT = True
except ImportError:
    HAS_PDF_SUPPORT = False


# ==============================================================================
# LaTeX Handler
# ==============================================================================

class LaTeXFileHandler(FileHandler):
    """
    Handler for LaTeX files with syntax highlighting and preview

    Supported formats:
    - .tex (LaTeX documents)
    - .sty (LaTeX style files)
    - .cls (LaTeX class files)

    Features:
    - Syntax highlighting
    - Live preview (if pdflatex available)
    - LaTeX command insertion
    - Document structure navigation
    - Symbol insertion
    - Compile to PDF
    - Error highlighting
    """

    SUPPORTED_EXTENSIONS = {'.tex', '.sty', '.cls'}

    # LaTeX command patterns for syntax highlighting
    SYNTAX_PATTERNS = {
        'command': r'\\[a-zA-Z]+',
        'environment': r'\\(?:begin|end)\{[^}]+\}',
        'comment': r'%.*$',
        'math_inline': r'\$[^$]+\$',
        'math_display': r'\$\$[^$]+\$\$',
        'curly_braces': r'[{}]',
        'square_brackets': r'[\[\]]',
        'section': r'\\(?:section|subsection|subsubsection|chapter|part)\*?\{[^}]+\}'
    }

    # Common LaTeX commands for quick insertion
    COMMON_COMMANDS = {
        'Sections': [
            ('\\section{}', 'Section'),
            ('\\subsection{}', 'Subsection'),
            ('\\subsubsection{}', 'Subsubsection'),
        ],
        'Formatting': [
            ('\\textbf{}', 'Bold'),
            ('\\textit{}', 'Italic'),
            ('\\underline{}', 'Underline'),
            ('\\emph{}', 'Emphasis'),
        ],
        'Math': [
            ('$  $', 'Inline Math'),
            ('\\[ \\]', 'Display Math'),
            ('\\begin{equation}\n\n\\end{equation}', 'Equation'),
            ('\\frac{}{}', 'Fraction'),
        ],
        'Lists': [
            ('\\begin{itemize}\n\\item \n\\end{itemize}', 'Bullet List'),
            ('\\begin{enumerate}\n\\item \n\\end{enumerate}', 'Numbered List'),
        ],
        'Environments': [
            ('\\begin{figure}\n\n\\end{figure}', 'Figure'),
            ('\\begin{table}\n\n\\end{table}', 'Table'),
            ('\\begin{center}\n\n\\end{center}', 'Center'),
        ]
    }

    def __init__(self):
        """Initialize LaTeX handler"""
        super().__init__()
        self.file_type_name = "LaTeX"
        self.capabilities = [
            EditorCapability.READ,
            EditorCapability.WRITE,
            EditorCapability.SYNTAX_HIGHLIGHT,
            EditorCapability.PREVIEW,
            EditorCapability.SPLIT_VIEW,
            EditorCapability.SEARCH,
            EditorCapability.REPLACE
        ]
        self.supported_extensions = list(self.SUPPORTED_EXTENSIONS)
        self.text_widget: Optional[tk.Text] = None
        self.preview_enabled: bool = False
        self.last_compiled_content: str = ""
        self.preview_canvas: Optional[tk.Canvas] = None
        self.preview_image: Optional[ImageTk.PhotoImage] = None
        self.temp_pdf_path: Optional[str] = None
        self.auto_compile: bool = False
        self.compile_thread: Optional[threading.Thread] = None

    def can_handle(self, file_path: Path) -> bool:
        """Check if can handle this LaTeX file"""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def read_file(self, file_path: Path) -> str:
        """Read LaTeX file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Failed to read LaTeX file: {e}")

    def write_file(self, file_path: Path, content: str) -> bool:
        """Write LaTeX file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save LaTeX file: {e}")
            return False

    def create_editor_widget(
        self,
        parent: tk.Widget,
        file_path: Path,
        content: str,
        **kwargs
    ) -> tk.Widget:
        """Create LaTeX editor widget with syntax highlighting"""
        # Main container with split view
        container = tk.PanedWindow(parent, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)

        # Left panel - Editor
        editor_frame = tk.Frame(container)

        # Toolbar
        toolbar = self._create_toolbar(editor_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Text editor with scrollbars
        text_frame = tk.Frame(editor_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create text widget with larger font for better readability
        text_font = tkfont.Font(family="Consolas", size=11)
        self.text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            undo=True,
            font=text_font,
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='#ffffff',
            selectbackground='#264f78'
        )

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        h_scrollbar = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=self.text_widget.xview)

        self.text_widget.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Insert content
        self.text_widget.insert('1.0', content)

        # Configure syntax highlighting tags
        self._configure_syntax_tags()

        # Apply initial syntax highlighting
        self._highlight_syntax()

        # Bind events for live highlighting
        self.text_widget.bind('<<Modified>>', self._on_text_modified)
        self.text_widget.bind('<KeyRelease>', lambda e: self._delayed_highlight())

        # Add editor to container
        container.add(editor_frame, stretch="always")

        # Right panel - Preview (optional)
        if kwargs.get('show_preview', False):
            self._add_preview_panel(container)

        # Store references
        container.text_widget = self.text_widget
        container.file_path = file_path

        return container

    def _create_toolbar(self, parent: tk.Widget) -> tk.Frame:
        """Create LaTeX editor toolbar"""
        toolbar = tk.Frame(parent)

        # Quick insert sections
        insert_frame = tk.LabelFrame(toolbar, text="Quick Insert", padx=5, pady=2)
        insert_frame.pack(side=tk.LEFT, padx=2)

        # Section commands
        section_var = tk.StringVar()
        section_menu = ttk.Combobox(
            insert_frame,
            textvariable=section_var,
            values=['Section', 'Subsection', 'Bold', 'Italic', 'Inline Math', 'Equation'],
            width=15,
            state='readonly'
        )
        section_menu.pack(side=tk.LEFT, padx=2)
        section_menu.bind('<<ComboboxSelected>>', lambda e: self._insert_command(section_var.get()))

        # Compile controls
        compile_frame = tk.LabelFrame(toolbar, text="Build", padx=5, pady=2)
        compile_frame.pack(side=tk.LEFT, padx=2)

        tk.Button(compile_frame, text="Compile", command=self._compile_latex, width=10).pack(side=tk.LEFT, padx=1)
        tk.Button(compile_frame, text="View PDF", command=self._view_pdf, width=10).pack(side=tk.LEFT, padx=1)

        # View controls
        view_frame = tk.LabelFrame(toolbar, text="View", padx=5, pady=2)
        view_frame.pack(side=tk.LEFT, padx=2)

        tk.Button(view_frame, text="Structure", command=self._show_structure, width=10).pack(side=tk.LEFT, padx=1)
        tk.Button(view_frame, text="Preview", command=self._toggle_preview, width=10).pack(side=tk.LEFT, padx=1)

        return toolbar

    def _toggle_preview(self):
        """Toggle preview panel visibility (placeholder for UI integration)"""
        if hasattr(self, 'preview_canvas') and self.preview_canvas:
            # Trigger a preview refresh
            self._refresh_preview()
        else:
            messagebox.showinfo(
                "Preview Panel",
                "To use live preview, open the file with show_preview=True\nor use the split view option in Universal Editor"
            )

    def _configure_syntax_tags(self):
        """Configure text tags for syntax highlighting"""
        if not self.text_widget:
            return

        # Define colors for different LaTeX elements
        self.text_widget.tag_configure('command', foreground='#569cd6')  # Blue
        self.text_widget.tag_configure('environment', foreground='#4ec9b0')  # Cyan
        self.text_widget.tag_configure('comment', foreground='#6a9955')  # Green
        self.text_widget.tag_configure('math_inline', foreground='#ce9178')  # Orange
        self.text_widget.tag_configure('math_display', foreground='#ce9178')  # Orange
        self.text_widget.tag_configure('section', foreground='#dcdcaa', font=('Consolas', 11, 'bold'))  # Yellow bold
        self.text_widget.tag_configure('curly_braces', foreground='#ffd700')  # Gold
        self.text_widget.tag_configure('square_brackets', foreground='#da70d6')  # Orchid

    def _highlight_syntax(self):
        """Apply syntax highlighting to entire document"""
        if not self.text_widget:
            return

        # Remove all existing tags
        for tag in self.SYNTAX_PATTERNS.keys():
            self.text_widget.tag_remove(tag, '1.0', tk.END)

        content = self.text_widget.get('1.0', tk.END)

        # Apply highlighting for each pattern
        for tag, pattern in self.SYNTAX_PATTERNS.items():
            for match in re.finditer(pattern, content, re.MULTILINE):
                start_idx = match.start()
                end_idx = match.end()

                # Convert to line.column format
                start_pos = self._index_to_position(content, start_idx)
                end_pos = self._index_to_position(content, end_idx)

                self.text_widget.tag_add(tag, start_pos, end_pos)

    def _index_to_position(self, content: str, index: int) -> str:
        """Convert string index to Tk Text widget position (line.column)"""
        lines = content[:index].split('\n')
        line = len(lines)
        col = len(lines[-1])
        return f"{line}.{col}"

    def _delayed_highlight(self):
        """Delayed syntax highlighting (debounced)"""
        # Cancel previous scheduled highlight
        if hasattr(self, '_highlight_timer'):
            self.text_widget.after_cancel(self._highlight_timer)

        # Schedule new highlight
        self._highlight_timer = self.text_widget.after(300, self._highlight_syntax)

    def _on_text_modified(self, event):
        """Handle text modification event"""
        if self.text_widget.edit_modified():
            self.text_widget.edit_modified(False)

    def _insert_command(self, command_name: str):
        """Insert LaTeX command at cursor"""
        if not self.text_widget:
            return

        # Map display names to commands
        command_map = {
            'Section': '\\section{}',
            'Subsection': '\\subsection{}',
            'Bold': '\\textbf{}',
            'Italic': '\\textit{}',
            'Inline Math': '$  $',
            'Equation': '\\begin{equation}\n\n\\end{equation}'
        }

        command = command_map.get(command_name, '')
        if command:
            self.text_widget.insert(tk.INSERT, command)
            # Move cursor inside braces/environment
            if '{}' in command:
                self.text_widget.mark_set(tk.INSERT, f"{tk.INSERT}-2c")
            elif command.startswith('\\begin'):
                # Move cursor to middle of environment
                lines = command.count('\n')
                self.text_widget.mark_set(tk.INSERT, f"{tk.INSERT}-{lines}l")

    def _compile_latex(self):
        """Compile LaTeX to PDF"""
        if not self.text_widget:
            return

        # Get current content
        content = self.text_widget.get('1.0', tk.END)

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False, encoding='utf-8') as f:
            temp_tex = f.name
            f.write(content)

        # Try to compile
        try:
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', temp_tex],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                messagebox.showinfo("Compile Success", "LaTeX compiled successfully!")
                self.last_compiled_content = content
            else:
                # Show compilation errors
                errors = self._parse_latex_errors(result.stdout)
                error_msg = f"Compilation failed with {len(errors)} error(s):\n\n"
                error_msg += '\n'.join(errors[:5])  # Show first 5 errors
                messagebox.showerror("Compile Error", error_msg)

        except FileNotFoundError:
            messagebox.showwarning(
                "LaTeX Not Found",
                "pdflatex not found. Please install a LaTeX distribution (TeX Live, MiKTeX, etc.)"
            )
        except subprocess.TimeoutExpired:
            messagebox.showerror("Compile Error", "Compilation timed out after 30 seconds")
        except Exception as e:
            messagebox.showerror("Compile Error", f"Failed to compile: {e}")
        finally:
            # Clean up temporary files
            import os
            for ext in ['.tex', '.aux', '.log', '.pdf']:
                try:
                    temp_file = temp_tex.replace('.tex', ext)
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass

    def _parse_latex_errors(self, log_output: str) -> List[str]:
        """Parse LaTeX compilation errors from log"""
        errors = []
        for line in log_output.split('\n'):
            if line.startswith('!'):
                errors.append(line)
        return errors

    def _view_pdf(self):
        """Open compiled PDF"""
        messagebox.showinfo("View PDF", "PDF viewing will open the compiled document in your default viewer")

    def _show_structure(self):
        """Show document structure (sections, subsections, etc.)"""
        if not self.text_widget:
            return

        content = self.text_widget.get('1.0', tk.END)

        # Find all sections
        structure = []
        for match in re.finditer(r'\\((?:chapter|section|subsection|subsubsection))\*?\{([^}]+)\}', content):
            level = match.group(1)
            title = match.group(2)
            structure.append(f"{'  ' * self._get_section_level(level)}{level.title()}: {title}")

        if structure:
            msg = "Document Structure:\n\n" + '\n'.join(structure)
        else:
            msg = "No document structure found (no sections defined)"

        messagebox.showinfo("Document Structure", msg)

    def _get_section_level(self, section_type: str) -> int:
        """Get indentation level for section type"""
        levels = {
            'chapter': 0,
            'section': 0,
            'subsection': 1,
            'subsubsection': 2
        }
        return levels.get(section_type, 0)

    def _add_preview_panel(self, container: tk.PanedWindow):
        """Add PDF preview panel with live rendering"""
        preview_frame = tk.Frame(container, bg='#2b2b2b')

        # Preview toolbar
        preview_toolbar = tk.Frame(preview_frame, bg='#3c3c3c', height=40)
        preview_toolbar.pack(fill=tk.X)
        preview_toolbar.pack_propagate(False)

        tk.Label(
            preview_toolbar,
            text="PDF Preview",
            bg='#3c3c3c',
            fg='#ffffff',
            font=('Arial', 10, 'bold')
        ).pack(side=tk.LEFT, padx=10)

        # Auto-compile checkbox
        auto_var = tk.BooleanVar(value=self.auto_compile)
        tk.Checkbutton(
            preview_toolbar,
            text="Auto-compile",
            variable=auto_var,
            command=lambda: setattr(self, 'auto_compile', auto_var.get()),
            bg='#3c3c3c',
            fg='#ffffff',
            selectcolor='#2b2b2b'
        ).pack(side=tk.LEFT, padx=5)

        # Refresh button
        tk.Button(
            preview_toolbar,
            text="Refresh",
            command=self._refresh_preview,
            bg='#0e639c',
            fg='#ffffff',
            relief=tk.FLAT,
            padx=10
        ).pack(side=tk.LEFT, padx=5)

        # Canvas for PDF display with scrollbars
        canvas_frame = tk.Frame(preview_frame, bg='#2b2b2b')
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_canvas = tk.Canvas(
            canvas_frame,
            bg='#2b2b2b',
            highlightthickness=0
        )

        v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.preview_canvas.yview)
        h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.preview_canvas.xview)

        self.preview_canvas.configure(
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set
        )

        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Status label for messages
        self.preview_status = tk.Label(
            preview_frame,
            text="Compile LaTeX to see preview",
            bg='#1e1e1e',
            fg='#888888',
            font=('Arial', 9),
            anchor='w',
            padx=5
        )
        self.preview_status.pack(fill=tk.X)

        container.add(preview_frame, stretch="always")

    def _refresh_preview(self):
        """Refresh PDF preview by recompiling"""
        if not self.text_widget:
            return

        # Update status
        if hasattr(self, 'preview_status'):
            self.preview_status.config(text="Compiling LaTeX...", fg='#4ec9b0')

        # Run compilation in thread to avoid UI freeze
        def compile_and_preview():
            success = self._compile_latex_to_preview()
            if success:
                self.text_widget.after(0, self._render_pdf_preview)

        if not self.compile_thread or not self.compile_thread.is_alive():
            self.compile_thread = threading.Thread(target=compile_and_preview, daemon=True)
            self.compile_thread.start()

    def _compile_latex_to_preview(self) -> bool:
        """Compile LaTeX to PDF for preview (returns success)"""
        if not self.text_widget:
            return False

        # Get current content
        content = self.text_widget.get('1.0', tk.END)

        # Create temporary directory for compilation
        temp_dir = tempfile.mkdtemp()
        temp_tex = os.path.join(temp_dir, 'preview.tex')
        temp_pdf = os.path.join(temp_dir, 'preview.pdf')

        try:
            # Write content to temp file
            with open(temp_tex, 'w', encoding='utf-8') as f:
                f.write(content)

            # Compile with pdflatex
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', temp_dir, temp_tex],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=temp_dir
            )

            if result.returncode == 0 and os.path.exists(temp_pdf):
                # Store PDF path for preview
                self.temp_pdf_path = temp_pdf
                self.last_compiled_content = content

                # Update status on UI thread
                if hasattr(self, 'preview_status'):
                    self.text_widget.after(0, lambda: self.preview_status.config(
                        text="Compilation successful", fg='#6a9955'
                    ))
                return True
            else:
                # Parse errors
                errors = self._parse_latex_errors(result.stdout)
                error_msg = f"Compilation failed: {errors[0] if errors else 'Unknown error'}"

                if hasattr(self, 'preview_status'):
                    self.text_widget.after(0, lambda: self.preview_status.config(
                        text=error_msg[:80], fg='#f48771'
                    ))
                return False

        except FileNotFoundError:
            if hasattr(self, 'preview_status'):
                self.text_widget.after(0, lambda: self.preview_status.config(
                    text="pdflatex not found - install TeX Live or MiKTeX", fg='#ce9178'
                ))
            return False

        except subprocess.TimeoutExpired:
            if hasattr(self, 'preview_status'):
                self.text_widget.after(0, lambda: self.preview_status.config(
                    text="Compilation timeout (30s)", fg='#f48771'
                ))
            return False

        except Exception as e:
            if hasattr(self, 'preview_status'):
                self.text_widget.after(0, lambda: self.preview_status.config(
                    text=f"Error: {str(e)[:60]}", fg='#f48771'
                ))
            return False

    def _render_pdf_preview(self):
        """Render PDF to canvas"""
        if not self.temp_pdf_path or not os.path.exists(self.temp_pdf_path):
            return

        if not self.preview_canvas:
            return

        try:
            if HAS_PDF_SUPPORT:
                # Convert PDF to images
                images = pdf2image.convert_from_path(self.temp_pdf_path, dpi=150)

                if images:
                    # Display first page (can be enhanced for multi-page)
                    first_page = images[0]

                    # Convert to PhotoImage
                    self.preview_image = ImageTk.PhotoImage(first_page)

                    # Clear canvas
                    self.preview_canvas.delete("all")

                    # Display image
                    self.preview_canvas.create_image(
                        0, 0,
                        anchor=tk.NW,
                        image=self.preview_image
                    )

                    # Update scroll region
                    self.preview_canvas.config(scrollregion=self.preview_canvas.bbox("all"))

                    # Update status
                    if hasattr(self, 'preview_status'):
                        page_count = len(images)
                        self.preview_status.config(
                            text=f"Preview ready ({page_count} page{'s' if page_count > 1 else ''})",
                            fg='#6a9955'
                        )
            else:
                # Fallback: show message about missing dependencies
                self.preview_canvas.delete("all")
                self.preview_canvas.create_text(
                    200, 150,
                    text="PDF Preview requires:\npip install pdf2image pillow\n\nAnd install poppler-utils",
                    fill='#888888',
                    font=('Arial', 12),
                    justify=tk.CENTER
                )

                if hasattr(self, 'preview_status'):
                    self.preview_status.config(
                        text="Install pdf2image and poppler for preview",
                        fg='#ce9178'
                    )

        except Exception as e:
            # Error rendering
            if hasattr(self, 'preview_status'):
                self.preview_status.config(
                    text=f"Preview error: {str(e)[:60]}",
                    fg='#f48771'
                )

    def get_content_from_widget(self, widget: tk.Widget) -> str:
        """Extract current content from editor widget"""
        if hasattr(widget, 'text_widget'):
            return widget.text_widget.get('1.0', tk.END).rstrip('\n')
        return ""

    def get_toolbar_actions(self) -> List[EditorAction]:
        """Get toolbar actions for LaTeX editor"""
        return [
            EditorAction(
                action_id='compile',
                label='Compile',
                icon='🔨',
                callback=self._compile_latex,
                tooltip='Compile LaTeX to PDF'
            ),
            EditorAction(
                action_id='structure',
                label='Structure',
                icon='📑',
                callback=self._show_structure,
                tooltip='Show document structure'
            ),
            EditorAction(
                action_id='symbols',
                label='Symbols',
                icon='∑',
                callback=self._show_symbols,
                tooltip='Insert mathematical symbols'
            ),
        ]

    def _show_symbols(self):
        """Show symbol insertion dialog"""
        symbols = {
            'Greek': ['\\alpha', '\\beta', '\\gamma', '\\delta', '\\epsilon', '\\theta', '\\pi', '\\sigma'],
            'Operators': ['\\sum', '\\prod', '\\int', '\\partial', '\\nabla', '\\infty'],
            'Relations': ['\\leq', '\\geq', '\\neq', '\\approx', '\\equiv', '\\subset', '\\supset'],
            'Arrows': ['\\rightarrow', '\\leftarrow', '\\Rightarrow', '\\Leftarrow', '\\leftrightarrow']
        }

        # Create dialog
        dialog = tk.Toplevel()
        dialog.title("Insert Symbol")
        dialog.geometry("400x300")

        for category, syms in symbols.items():
            frame = tk.LabelFrame(dialog, text=category, padx=5, pady=5)
            frame.pack(fill=tk.X, padx=10, pady=5)

            for sym in syms:
                btn = tk.Button(
                    frame,
                    text=sym,
                    command=lambda s=sym: self._insert_symbol(s, dialog),
                    width=12
                )
                btn.pack(side=tk.LEFT, padx=2, pady=2)

    def _insert_symbol(self, symbol: str, dialog: tk.Toplevel):
        """Insert symbol and close dialog"""
        if self.text_widget:
            self.text_widget.insert(tk.INSERT, symbol)
        dialog.destroy()

    def validate_content(self, content: str) -> tuple[bool, List[str]]:
        """Validate LaTeX content"""
        errors = []

        # Check for balanced braces
        brace_count = content.count('{') - content.count('}')
        if brace_count != 0:
            errors.append(f"Unbalanced braces: {abs(brace_count)} {'extra {' if brace_count > 0 else 'extra }'}")

        # Check for balanced environments
        begins = re.findall(r'\\begin\{([^}]+)\}', content)
        ends = re.findall(r'\\end\{([^}]+)\}', content)

        for env in set(begins + ends):
            begin_count = begins.count(env)
            end_count = ends.count(env)
            if begin_count != end_count:
                errors.append(f"Unbalanced environment '{env}': {begin_count} begin, {end_count} end")

        return len(errors) == 0, errors

    def format_content(self, content: str) -> str:
        """Format LaTeX content (basic indentation)"""
        lines = content.split('\n')
        formatted = []
        indent_level = 0

        for line in lines:
            stripped = line.strip()

            # Decrease indent before \end
            if stripped.startswith('\\end{'):
                indent_level = max(0, indent_level - 1)

            # Add indented line
            formatted.append('  ' * indent_level + stripped)

            # Increase indent after \begin
            if stripped.startswith('\\begin{'):
                indent_level += 1

        return '\n'.join(formatted)
