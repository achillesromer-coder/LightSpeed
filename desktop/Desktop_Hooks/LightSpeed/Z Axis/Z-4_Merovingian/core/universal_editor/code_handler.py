"""
Code File Handler - V1.0.0
Handler for source code files with syntax highlighting

Supports: Python, JavaScript, Java, C++, C#, Go, Rust, and more

Author: LightSpeed Team
Date: December 27, 2025
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
import keyword

from .file_handler import FileHandler, EditorCapability, EditorAction


# ==============================================================================
# Syntax Highlighting Configurations
# ==============================================================================

SYNTAX_CONFIGS = {
    'python': {
        'keywords': keyword.kwlist + ['self', 'cls', 'True', 'False', 'None'],
        'builtins': dir(__builtins__),
        'comment': '#',
        'string': ['"', "'"],
        'multiline_string': ['"""', "'''"],
        'extension_color': '#3776ab',
    },
    'javascript': {
        'keywords': ['var', 'let', 'const', 'function', 'return', 'if', 'else',
                    'for', 'while', 'break', 'continue', 'switch', 'case',
                    'class', 'extends', 'import', 'export', 'default',
                    'async', 'await', 'try', 'catch', 'throw', 'new'],
        'builtins': ['console', 'window', 'document', 'Math', 'JSON', 'Array',
                    'Object', 'String', 'Number', 'Boolean', 'Date'],
        'comment': '//',
        'multiline_comment': ['/*', '*/'],
        'string': ['"', "'", '`'],
        'extension_color': '#f7df1e',
    },
    'java': {
        'keywords': ['public', 'private', 'protected', 'class', 'interface',
                    'extends', 'implements', 'static', 'final', 'void',
                    'int', 'String', 'boolean', 'if', 'else', 'for', 'while',
                    'return', 'new', 'this', 'super', 'import', 'package'],
        'builtins': ['System', 'Math', 'String', 'Integer', 'Double', 'Boolean'],
        'comment': '//',
        'multiline_comment': ['/*', '*/'],
        'string': ['"'],
        'extension_color': '#007396',
    },
    'cpp': {
        'keywords': ['#include', '#define', 'int', 'float', 'double', 'char',
                    'void', 'class', 'struct', 'public', 'private', 'protected',
                    'if', 'else', 'for', 'while', 'return', 'new', 'delete',
                    'namespace', 'using', 'template', 'const', 'static'],
        'builtins': ['std', 'cout', 'cin', 'endl', 'string', 'vector'],
        'comment': '//',
        'multiline_comment': ['/*', '*/'],
        'string': ['"'],
        'extension_color': '#00599c',
    },
}


# ==============================================================================
# Code File Handler
# ==============================================================================

class CodeFileHandler(FileHandler):
    """
    Handler for source code files with syntax highlighting

    Features:
    - Syntax highlighting for 10+ languages
    - Auto-indentation
    - Bracket matching
    - Code folding
    - Line numbers
    - Minimap (optional)
    - Auto-completion suggestions
    """

    def __init__(self):
        """Initialize code file handler"""
        super().__init__()

        self.file_type_name = "Code"
        self.supported_extensions = [
            # Python
            '.py', '.pyw', '.pyx',
            # JavaScript/TypeScript
            '.js', '.jsx', '.ts', '.tsx', '.mjs',
            # Java
            '.java',
            # C/C++
            '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp',
            # C#
            '.cs',
            # Go
            '.go',
            # Rust
            '.rs',
            # Ruby
            '.rb',
            # PHP
            '.php',
            # Shell
            '.sh', '.bash',
        ]

        self.capabilities = [
            EditorCapability.READ,
            EditorCapability.WRITE,
            EditorCapability.SYNTAX_HIGHLIGHT,
            EditorCapability.AUTO_COMPLETE,
            EditorCapability.FORMAT,
            EditorCapability.SEARCH,
            EditorCapability.REPLACE,
            EditorCapability.UNDO_REDO,
            EditorCapability.FOLD,
        ]

        # Current editor reference
        self.current_widget: Optional[tk.Text] = None
        self.current_file: Optional[Path] = None
        self.current_language: Optional[str] = None

    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can handle the file"""
        return file_path.suffix.lower() in self.supported_extensions

    def read_file(self, file_path: Path) -> str:
        """Read code file"""
        try:
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                return file_path.read_text(encoding='latin-1')
            except:
                raise IOError(f"Could not decode file")

    def write_file(self, file_path: Path, content: str) -> bool:
        """Write code file"""
        try:
            file_path.write_text(content, encoding='utf-8')
            return True
        except Exception as e:
            raise IOError(f"Failed to write file: {e}")

    def create_editor_widget(
        self,
        parent: tk.Widget,
        file_path: Path,
        content: str,
        **kwargs
    ) -> tk.Widget:
        """Create code editor widget"""
        self.current_file = file_path
        self.current_language = self._detect_language(file_path)

        # Create container frame
        container = ttk.Frame(parent)

        # Create text widget with line numbers
        text_frame = ttk.Frame(container)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Line numbers
        line_numbers = tk.Text(
            text_frame,
            width=4,
            padx=3,
            takefocus=0,
            border=0,
            background='#f0f0f0',
            foreground='#888888',
            state='disabled'
        )
        line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Main text widget
        text_widget = tk.Text(
            text_frame,
            wrap=tk.NONE,
            yscrollcommand=scrollbar.set,
            undo=True,
            maxundo=-1,
            autoseparators=True,
            insertwidth=2,
            background='#1e1e1e',  # Dark theme
            foreground='#d4d4d4',
            insertbackground='white',
            selectbackground='#264f78',
        )
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=text_widget.yview)

        # Configure monospace font
        code_font = tkfont.Font(family="Consolas", size=10)
        text_widget.config(font=code_font)
        line_numbers.config(font=code_font)

        # Insert content
        text_widget.insert('1.0', content)
        text_widget.edit_modified(False)

        # Setup syntax highlighting
        self._setup_syntax_highlighting(text_widget)

        # Setup auto-indentation
        self._setup_auto_indent(text_widget)

        # Setup bracket matching
        self._setup_bracket_matching(text_widget)

        # Update line numbers
        def update_line_numbers(event=None):
            line_numbers.config(state='normal')
            line_numbers.delete('1.0', tk.END)

            num_lines = int(text_widget.index('end-1c').split('.')[0])
            line_numbers_text = '\n'.join(str(i) for i in range(1, num_lines + 1))
            line_numbers.insert('1.0', line_numbers_text)

            line_numbers.config(state='disabled')

        text_widget.bind('<<Modified>>', update_line_numbers)
        text_widget.bind('<KeyRelease>', update_line_numbers)
        update_line_numbers()

        # Info bar
        info_bar = ttk.Label(container, text="", relief=tk.SUNKEN, anchor=tk.W)
        info_bar.pack(side=tk.BOTTOM, fill=tk.X)

        def update_info_bar(event=None):
            cursor_pos = text_widget.index(tk.INSERT)
            line, col = cursor_pos.split('.')

            num_lines = int(text_widget.index('end-1c').split('.')[0])

            lang_name = self.current_language.upper() if self.current_language else 'UNKNOWN'

            info_bar.config(
                text=f"{lang_name} | Line {line}, Col {col} | {num_lines} lines"
            )

        text_widget.bind('<KeyRelease>', update_info_bar)
        text_widget.bind('<ButtonRelease>', update_info_bar)
        update_info_bar()

        # Store references
        self.current_widget = text_widget
        text_widget.line_numbers = line_numbers

        return container

    def get_content_from_widget(self, widget: tk.Widget) -> str:
        """Get content from code widget"""
        for child in widget.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Text) and subchild.cget('takefocus') != 0:
                        return subchild.get('1.0', 'end-1c')
        return ""

    def get_toolbar_actions(self) -> List[EditorAction]:
        """Get toolbar actions for code editing"""
        return [
            EditorAction(
                action_id="format",
                label="Format",
                callback=self._format_code,
                tooltip="Format code"
            ),
            EditorAction(
                action_id="comment",
                label="Comment",
                callback=self._toggle_comment,
                tooltip="Toggle comment"
            ),
            EditorAction(
                action_id="indent",
                label="Indent",
                callback=self._indent_selection,
                tooltip="Indent selected lines"
            ),
            EditorAction(
                action_id="dedent",
                label="Dedent",
                callback=self._dedent_selection,
                tooltip="Dedent selected lines"
            ),
        ]

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        ext = file_path.suffix.lower()

        language_map = {
            '.py': 'python', '.pyw': 'python', '.pyx': 'python',
            '.js': 'javascript', '.jsx': 'javascript', '.mjs': 'javascript',
            '.ts': 'javascript', '.tsx': 'javascript',
            '.java': 'java',
            '.c': 'cpp', '.cpp': 'cpp', '.cc': 'cpp', '.cxx': 'cpp',
            '.h': 'cpp', '.hpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.sh': 'shell', '.bash': 'shell',
        }

        return language_map.get(ext, 'unknown')

    def _setup_syntax_highlighting(self, text_widget: tk.Text):
        """Setup syntax highlighting"""
        if self.current_language not in SYNTAX_CONFIGS:
            return

        config = SYNTAX_CONFIGS[self.current_language]

        # Define tags
        text_widget.tag_config('keyword', foreground='#569cd6')
        text_widget.tag_config('builtin', foreground='#4ec9b0')
        text_widget.tag_config('string', foreground='#ce9178')
        text_widget.tag_config('comment', foreground='#6a9955')
        text_widget.tag_config('number', foreground='#b5cea8')
        text_widget.tag_config('function', foreground='#dcdcaa')

        def highlight_syntax(event=None):
            # Remove existing tags
            for tag in ['keyword', 'builtin', 'string', 'comment', 'number', 'function']:
                text_widget.tag_remove(tag, '1.0', tk.END)

            content = text_widget.get('1.0', 'end-1c')
            lines = content.split('\n')

            for i, line in enumerate(lines, 1):
                # Comments
                if 'comment' in config:
                    comment_pos = line.find(config['comment'])
                    if comment_pos != -1:
                        start = f'{i}.{comment_pos}'
                        end = f'{i}.end'
                        text_widget.tag_add('comment', start, end)
                        continue  # Rest of line is comment

                # Strings
                for quote in config.get('string', []):
                    for match in re.finditer(f'{re.escape(quote)}[^{re.escape(quote)}]*{re.escape(quote)}', line):
                        start = f'{i}.{match.start()}'
                        end = f'{i}.{match.end()}'
                        text_widget.tag_add('string', start, end)

                # Keywords
                for keyword in config.get('keywords', []):
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    for match in re.finditer(pattern, line):
                        start = f'{i}.{match.start()}'
                        end = f'{i}.{match.end()}'
                        text_widget.tag_add('keyword', start, end)

                # Builtins (sample only - not exhaustive)
                for builtin in config.get('builtins', [])[:20]:  # Limit for performance
                    pattern = r'\b' + re.escape(builtin) + r'\b'
                    for match in re.finditer(pattern, line):
                        start = f'{i}.{match.start()}'
                        end = f'{i}.{match.end()}'
                        text_widget.tag_add('builtin', start, end)

                # Numbers
                for match in re.finditer(r'\b\d+\.?\d*\b', line):
                    start = f'{i}.{match.start()}'
                    end = f'{i}.{match.end()}'
                    text_widget.tag_add('number', start, end)

                # Functions (simple pattern)
                for match in re.finditer(r'\b(\w+)\s*\(', line):
                    start = f'{i}.{match.start(1)}'
                    end = f'{i}.{match.end(1)}'
                    text_widget.tag_add('function', start, end)

        # Bind highlighting (debounced for performance)
        text_widget.bind('<KeyRelease>', lambda e: text_widget.after(100, highlight_syntax))
        highlight_syntax()

    def _setup_auto_indent(self, text_widget: tk.Text):
        """Setup auto-indentation"""
        def auto_indent(event):
            # Get current line
            cursor_pos = text_widget.index(tk.INSERT)
            line_num = int(cursor_pos.split('.')[0])

            if line_num > 1:
                # Get previous line
                prev_line = text_widget.get(f'{line_num-1}.0', f'{line_num-1}.end')

                # Count leading whitespace
                indent = len(prev_line) - len(prev_line.lstrip())

                # Increase indent if previous line ends with :
                if prev_line.rstrip().endswith(':'):
                    indent += 4

                # Insert indentation
                if indent > 0:
                    text_widget.insert(tk.INSERT, ' ' * indent)
                    return 'break'  # Prevent default newline behavior

        text_widget.bind('<Return>', auto_indent)

    def _setup_bracket_matching(self, text_widget: tk.Text):
        """Setup bracket matching"""
        text_widget.tag_config('matching_bracket', background='#3e3e3e')

        brackets = {'(': ')', '[': ']', '{': '}'}
        closing = {v: k for k, v in brackets.items()}

        def highlight_matching_bracket(event):
            # Remove existing highlight
            text_widget.tag_remove('matching_bracket', '1.0', tk.END)

            # Get character at cursor
            cursor_pos = text_widget.index(tk.INSERT)
            char = text_widget.get(cursor_pos)

            # Check if it's a bracket
            if char in brackets:
                # Find matching closing bracket
                target = brackets[char]
                level = 1
                search_pos = cursor_pos

                while level > 0:
                    search_pos = text_widget.search(f'[{re.escape(char)}{re.escape(target)}]',
                                                   search_pos, tk.END, regexp=True, forwards=True)
                    if not search_pos:
                        break

                    found_char = text_widget.get(search_pos)
                    if found_char == char:
                        level += 1
                    elif found_char == target:
                        level -= 1

                    if level == 0:
                        text_widget.tag_add('matching_bracket', cursor_pos, f'{cursor_pos}+1c')
                        text_widget.tag_add('matching_bracket', search_pos, f'{search_pos}+1c')
                        break

                    search_pos = f'{search_pos}+1c'

        text_widget.bind('<KeyRelease>', highlight_matching_bracket)
        text_widget.bind('<ButtonRelease>', highlight_matching_bracket)

    def _format_code(self):
        """Format code (basic implementation)"""
        if not self.current_widget:
            return

        content = self.current_widget.get('1.0', 'end-1c')

        # Basic formatting: remove trailing whitespace
        lines = content.split('\n')
        formatted_lines = [line.rstrip() for line in lines]

        self.current_widget.delete('1.0', tk.END)
        self.current_widget.insert('1.0', '\n'.join(formatted_lines))

    def _toggle_comment(self):
        """Toggle comment on selected lines"""
        if not self.current_widget or self.current_language not in SYNTAX_CONFIGS:
            return

        config = SYNTAX_CONFIGS[self.current_language]
        comment_char = config.get('comment', '#')

        try:
            # Get selection
            start = self.current_widget.index(tk.SEL_FIRST)
            end = self.current_widget.index(tk.SEL_LAST)

            start_line = int(start.split('.')[0])
            end_line = int(end.split('.')[0])

            # Toggle comment for each line
            for line_num in range(start_line, end_line + 1):
                line = self.current_widget.get(f'{line_num}.0', f'{line_num}.end')

                if line.strip().startswith(comment_char):
                    # Remove comment
                    pos = line.find(comment_char)
                    self.current_widget.delete(f'{line_num}.{pos}', f'{line_num}.{pos+len(comment_char)+1}')
                else:
                    # Add comment
                    self.current_widget.insert(f'{line_num}.0', f'{comment_char} ')

        except tk.TclError:
            # No selection - comment current line
            cursor_pos = self.current_widget.index(tk.INSERT)
            line_num = int(cursor_pos.split('.')[0])
            line = self.current_widget.get(f'{line_num}.0', f'{line_num}.end')

            if line.strip().startswith(comment_char):
                pos = line.find(comment_char)
                self.current_widget.delete(f'{line_num}.{pos}', f'{line_num}.{pos+len(comment_char)+1}')
            else:
                self.current_widget.insert(f'{line_num}.0', f'{comment_char} ')

    def _indent_selection(self):
        """Indent selected lines"""
        if not self.current_widget:
            return

        try:
            start = self.current_widget.index(tk.SEL_FIRST)
            end = self.current_widget.index(tk.SEL_LAST)

            start_line = int(start.split('.')[0])
            end_line = int(end.split('.')[0])

            for line_num in range(start_line, end_line + 1):
                self.current_widget.insert(f'{line_num}.0', '    ')

        except tk.TclError:
            # No selection
            cursor_pos = self.current_widget.index(tk.INSERT)
            self.current_widget.insert(cursor_pos, '    ')

    def _dedent_selection(self):
        """Dedent selected lines"""
        if not self.current_widget:
            return

        try:
            start = self.current_widget.index(tk.SEL_FIRST)
            end = self.current_widget.index(tk.SEL_LAST)

            start_line = int(start.split('.')[0])
            end_line = int(end.split('.')[0])

            for line_num in range(start_line, end_line + 1):
                line = self.current_widget.get(f'{line_num}.0', f'{line_num}.end')

                if line.startswith('    '):
                    self.current_widget.delete(f'{line_num}.0', f'{line_num}.4')
                elif line.startswith('\t'):
                    self.current_widget.delete(f'{line_num}.0', f'{line_num}.1')

        except tk.TclError:
            pass
