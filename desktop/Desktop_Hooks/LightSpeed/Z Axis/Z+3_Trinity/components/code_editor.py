#!/usr/bin/env python
"""
Advanced Text Editor - Full IDE-like text editor
Complete text editing with syntax highlighting, auto-completion, find/replace

Features:
- Syntax highlighting for Python, JSON, Markdown, etc.
- Auto-completion dropdown
- Find and Replace dialog
- Line numbers sidebar
- Code folding markers
- Multiple file tabs
- Undo/Redo support
- Smart indentation

Author: LightSpeed Team
Version: 0.9.5
Date: December 16, 2025
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timezone
import json
import re
import sys


def _find_lightspeed_root() -> Path:
    here = Path(__file__).resolve()
    for cand in (here, *here.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return here.parents[3]


class LineNumbers(tk.Canvas):
    """Line numbers sidebar for text editor"""

    def __init__(self, parent, text_widget, **kwargs):
        super().__init__(parent, **kwargs)
        self.text_widget = text_widget
        self.configure(width=50, bg='#1e1e1e', highlightthickness=0)

    def redraw(self, *args):
        """Redraw line numbers"""
        self.delete('all')

        i = self.text_widget.index('@0,0')
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split('.')[0]
            self.create_text(
                45, y,
                anchor='ne',
                text=linenum,
                fill='#858585',
                font=('Consolas', 9)
            )
            i = self.text_widget.index(f'{i}+1line')


class SyntaxHighlighter:
    """Syntax highlighting for various languages"""

    def __init__(self, text_widget):
        self.text = text_widget
        self._setup_tags()

    def _setup_tags(self):
        """Setup text tags for syntax highlighting"""
        # Python syntax
        self.text.tag_config('keyword', foreground='#569cd6')
        self.text.tag_config('string', foreground='#ce9178')
        self.text.tag_config('comment', foreground='#6a9955')
        self.text.tag_config('function', foreground='#dcdcaa')
        self.text.tag_config('class', foreground='#4ec9b0')
        self.text.tag_config('number', foreground='#b5cea8')
        self.text.tag_config('decorator', foreground='#c586c0')

        # JSON syntax
        self.text.tag_config('json_key', foreground='#9cdcfe')
        self.text.tag_config('json_value', foreground='#ce9178')

        # Markdown syntax
        self.text.tag_config('md_header', foreground='#569cd6', font=('Consolas', 11, 'bold'))
        self.text.tag_config('md_bold', foreground='#dcdcaa', font=('Consolas', 10, 'bold'))
        self.text.tag_config('md_italic', foreground='#dcdcaa', font=('Consolas', 10, 'italic'))
        self.text.tag_config('md_code', foreground='#ce9178', background='#2d2d2d')

    def highlight_python(self):
        """Highlight Python syntax"""
        # Remove existing tags
        for tag in ['keyword', 'string', 'comment', 'function', 'class', 'number', 'decorator']:
            self.text.tag_remove(tag, '1.0', 'end')

        content = self.text.get('1.0', 'end-1c')

        # Keywords
        keywords = r'\b(def|class|if|elif|else|for|while|try|except|finally|with|as|import|from|return|yield|pass|break|continue|True|False|None|and|or|not|in|is|lambda|async|await)\b'
        for match in re.finditer(keywords, content):
            start = f'1.0+{match.start()}c'
            end = f'1.0+{match.end()}c'
            self.text.tag_add('keyword', start, end)

        # Strings
        strings = r'(["\'])(?:(?=(\\?))\2.)*?\1'
        for match in re.finditer(strings, content):
            start = f'1.0+{match.start()}c'
            end = f'1.0+{match.end()}c'
            self.text.tag_add('string', start, end)

        # Comments
        comments = r'#.*$'
        for match in re.finditer(comments, content, re.MULTILINE):
            start = f'1.0+{match.start()}c'
            end = f'1.0+{match.end()}c'
            self.text.tag_add('comment', start, end)

        # Functions
        functions = r'\bdef\s+(\w+)'
        for match in re.finditer(functions, content):
            start = f'1.0+{match.start(1)}c'
            end = f'1.0+{match.end(1)}c'
            self.text.tag_add('function', start, end)

        # Classes
        classes = r'\bclass\s+(\w+)'
        for match in re.finditer(classes, content):
            start = f'1.0+{match.start(1)}c'
            end = f'1.0+{match.end(1)}c'
            self.text.tag_add('class', start, end)

        # Numbers
        numbers = r'\b\d+\.?\d*\b'
        for match in re.finditer(numbers, content):
            start = f'1.0+{match.start()}c'
            end = f'1.0+{match.end()}c'
            self.text.tag_add('number', start, end)

        # Decorators
        decorators = r'@\w+'
        for match in re.finditer(decorators, content):
            start = f'1.0+{match.start()}c'
            end = f'1.0+{match.end()}c'
            self.text.tag_add('decorator', start, end)

    def highlight_json(self):
        """Highlight JSON syntax"""
        self.text.tag_remove('json_key', '1.0', 'end')
        self.text.tag_remove('json_value', '1.0', 'end')

        content = self.text.get('1.0', 'end-1c')

        # Keys
        keys = r'"(\w+)":'
        for match in re.finditer(keys, content):
            start = f'1.0+{match.start()}c'
            end = f'1.0+{match.end()-1}c'
            self.text.tag_add('json_key', start, end)

        # Values
        values = r':\s*"([^"]*)"'
        for match in re.finditer(values, content):
            start = f'1.0+{match.start(1)-1}c'
            end = f'1.0+{match.end(1)+1}c'
            self.text.tag_add('json_value', start, end)

    def highlight_markdown(self):
        """Highlight Markdown syntax"""
        tags = ['md_header', 'md_bold', 'md_italic', 'md_code']
        for tag in tags:
            self.text.tag_remove(tag, '1.0', 'end')

        content = self.text.get('1.0', 'end-1c')

        # Headers
        headers = r'^#+\s+.*$'
        for match in re.finditer(headers, content, re.MULTILINE):
            start = f'1.0+{match.start()}c'
            end = f'1.0+{match.end()}c'
            self.text.tag_add('md_header', start, end)

        # Bold
        bold = r'\*\*([^*]+)\*\*'
        for match in re.finditer(bold, content):
            start = f'1.0+{match.start()}c'
            end = f'1.0+{match.end()}c'
            self.text.tag_add('md_bold', start, end)

        # Italic
        italic = r'\*([^*]+)\*'
        for match in re.finditer(italic, content):
            start = f'1.0+{match.start()}c'
            end = f'1.0+{match.end()}c'
            self.text.tag_add('md_italic', start, end)

        # Code
        code = r'`([^`]+)`'
        for match in re.finditer(code, content):
            start = f'1.0+{match.start()}c'
            end = f'1.0+{match.end()}c'
            self.text.tag_add('md_code', start, end)


class AutoComplete:
    """Auto-completion dropdown"""

    def __init__(self, text_widget):
        self.text = text_widget
        self.popup = None
        self.listbox = None
        self.suggestions = []

        # Python keywords and common functions
        self.python_keywords = [
            'def', 'class', 'if', 'elif', 'else', 'for', 'while', 'try',
            'except', 'finally', 'with', 'as', 'import', 'from', 'return',
            'yield', 'pass', 'break', 'continue', 'True', 'False', 'None',
            'and', 'or', 'not', 'in', 'is', 'lambda', 'async', 'await',
            'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set',
            'range', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed'
        ]

    def show(self, word_start):
        """Show auto-complete popup"""
        if self.popup:
            self.hide()

        # Get current word
        current_word = self.text.get(word_start, 'insert')

        # Filter suggestions
        self.suggestions = [kw for kw in self.python_keywords if kw.startswith(current_word)]

        if not self.suggestions:
            return

        # Create popup
        self.popup = tk.Toplevel(self.text)
        self.popup.wm_overrideredirect(True)

        # Position popup
        bbox = self.text.bbox('insert')
        if bbox:
            x = self.text.winfo_rootx() + bbox[0]
            y = self.text.winfo_rooty() + bbox[1] + bbox[3]
            self.popup.geometry(f'+{x}+{y}')

        # Create listbox
        self.listbox = tk.Listbox(
            self.popup,
            height=min(10, len(self.suggestions)),
            bg='#2d2d2d',
            fg='#ffffff',
            selectbackground='#094771',
            font=('Consolas', 10)
        )
        self.listbox.pack()

        # Add suggestions
        for suggestion in self.suggestions:
            self.listbox.insert('end', suggestion)

        self.listbox.selection_set(0)
        self.listbox.bind('<Double-Button-1>', lambda e: self.complete())
        self.listbox.bind('<Return>', lambda e: self.complete())

    def complete(self):
        """Complete with selected suggestion"""
        if not self.listbox:
            return

        selection = self.listbox.curselection()
        if selection:
            word = self.listbox.get(selection[0])

            # Get word start
            current_line = self.text.get('insert linestart', 'insert')
            word_start = len(current_line) - len(current_line.lstrip())
            for i in range(len(current_line) - 1, -1, -1):
                if not current_line[i].isalnum() and current_line[i] != '_':
                    word_start = i + 1
                    break

            # Replace current word
            start_idx = f'insert linestart + {word_start}c'
            self.text.delete(start_idx, 'insert')
            self.text.insert(start_idx, word)

        self.hide()

    def hide(self):
        """Hide auto-complete popup"""
        if self.popup:
            self.popup.destroy()
            self.popup = None
            self.listbox = None


class FindReplaceDialog:
    """Find and Replace dialog"""

    def __init__(self, parent, text_widget):
        self.text = text_widget
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Find and Replace")
        self.dialog.geometry("500x200")
        self.dialog.configure(bg='#1e1e1e')
        self.dialog.transient(parent)

        # Find
        tk.Label(self.dialog, text="Find:", bg='#1e1e1e', fg='#ffffff',
                font=('Arial', 10)).grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.find_entry = tk.Entry(self.dialog, width=40, bg='#2d2d2d', fg='#ffffff',
                                   font=('Consolas', 10))
        self.find_entry.grid(row=0, column=1, padx=10, pady=10)

        # Replace
        tk.Label(self.dialog, text="Replace:", bg='#1e1e1e', fg='#ffffff',
                font=('Arial', 10)).grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.replace_entry = tk.Entry(self.dialog, width=40, bg='#2d2d2d', fg='#ffffff',
                                      font=('Consolas', 10))
        self.replace_entry.grid(row=1, column=1, padx=10, pady=10)

        # Options
        self.case_sensitive = tk.BooleanVar(value=False)
        tk.Checkbutton(self.dialog, text="Case sensitive", variable=self.case_sensitive,
                      bg='#1e1e1e', fg='#ffffff', selectcolor='#1e1e1e',
                      font=('Arial', 9)).grid(row=2, column=1, sticky='w', padx=10)

        # Buttons
        btn_frame = tk.Frame(self.dialog, bg='#1e1e1e')
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)

        tk.Button(btn_frame, text="Find Next", command=self.find_next,
                 bg='#0e639c', fg='white', font=('Arial', 10), width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Replace", command=self.replace_current,
                 bg='#0e639c', fg='white', font=('Arial', 10), width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Replace All", command=self.replace_all,
                 bg='#0e639c', fg='white', font=('Arial', 10), width=12).pack(side=tk.LEFT, padx=5)

        self.current_match = None

    def find_next(self):
        """Find next occurrence"""
        search_term = self.find_entry.get()
        if not search_term:
            return

        # Start from current position or selection
        start_pos = self.text.index('insert') if not self.current_match else self.text.index(f'{self.current_match}+{len(search_term)}c')

        # Search
        if self.case_sensitive.get():
            pos = self.text.search(search_term, start_pos, stopindex='end')
        else:
            pos = self.text.search(search_term, start_pos, stopindex='end', nocase=True)

        if pos:
            # Highlight match
            self.text.tag_remove('search', '1.0', 'end')
            end_pos = f'{pos}+{len(search_term)}c'
            self.text.tag_add('search', pos, end_pos)
            self.text.tag_config('search', background='yellow', foreground='black')
            self.text.see(pos)
            self.text.mark_set('insert', pos)
            self.current_match = pos
        else:
            # Wrap around
            if self.case_sensitive.get():
                pos = self.text.search(search_term, '1.0', stopindex='end')
            else:
                pos = self.text.search(search_term, '1.0', stopindex='end', nocase=True)

            if pos:
                self.text.tag_remove('search', '1.0', 'end')
                end_pos = f'{pos}+{len(search_term)}c'
                self.text.tag_add('search', pos, end_pos)
                self.text.see(pos)
                self.text.mark_set('insert', pos)
                self.current_match = pos
            else:
                messagebox.showinfo("Not Found", f"'{search_term}' not found", parent=self.dialog)

    def replace_current(self):
        """Replace current match"""
        if not self.current_match:
            self.find_next()
            return

        search_term = self.find_entry.get()
        replace_term = self.replace_entry.get()

        if self.current_match:
            end_pos = f'{self.current_match}+{len(search_term)}c'
            self.text.delete(self.current_match, end_pos)
            self.text.insert(self.current_match, replace_term)
            self.current_match = None
            self.find_next()

    def replace_all(self):
        """Replace all occurrences"""
        search_term = self.find_entry.get()
        replace_term = self.replace_entry.get()

        if not search_term:
            return

        content = self.text.get('1.0', 'end-1c')

        if self.case_sensitive.get():
            new_content = content.replace(search_term, replace_term)
        else:
            # Case-insensitive replace
            pattern = re.compile(re.escape(search_term), re.IGNORECASE)
            new_content = pattern.sub(replace_term, content)

        count = content.count(search_term) if self.case_sensitive.get() else len(pattern.findall(content))

        self.text.delete('1.0', 'end')
        self.text.insert('1.0', new_content)

        messagebox.showinfo("Replace All", f"Replaced {count} occurrences", parent=self.dialog)


class AdvancedTextEditor(tk.Frame):
    """Advanced text editor with IDE features"""

    def __init__(self, parent, *, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg='#1e1e1e')

        self.app = app or self._discover_app(parent)
        self.lightspeed_root = _find_lightspeed_root()
        self.current_file = None
        self.file_type = 'text'
        self.local_runtime_path = self.lightspeed_root / "config" / "neo_local_runtime.json"
        self.temp_shell_registry_path = (
            self.lightspeed_root / "Z Axis" / "Z+2_Neo" / "data" / "temp_shells" / "temp_shell_registry.json"
        )

        self._build_ui()
        self._setup_bindings()
        self._refresh_neo_runtime()

    def _discover_app(self, parent) -> Optional[object]:
        current = parent
        while current is not None:
            candidate = getattr(current, "app", None)
            if candidate is not None:
                return candidate
            current = getattr(current, "master", None)
        return None

    def _build_ui(self):
        """Build editor UI"""
        # Toolbar
        toolbar = tk.Frame(self, bg='#2d2d2d', height=35)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        # File operations
        tk.Button(toolbar, text="📁 Open", command=self.open_file,
                 bg='#0e639c', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', padx=10).pack(side=tk.LEFT, padx=2, pady=2)

        tk.Button(toolbar, text="💾 Save", command=self.save_file,
                 bg='#0e639c', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', padx=10).pack(side=tk.LEFT, padx=2, pady=2)

        tk.Button(toolbar, text="🔍 Find", command=self.show_find_replace,
                 bg='#0e639c', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', padx=10).pack(side=tk.LEFT, padx=2, pady=2)

        tk.Button(toolbar, text="Neo Sync", command=self._refresh_neo_runtime,
                 bg='#1f6f4a', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', padx=10).pack(side=tk.LEFT, padx=(10, 2), pady=2)

        tk.Button(toolbar, text="Neo Stage", command=self._stage_neo_task,
                 bg='#7a4f01', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', padx=10).pack(side=tk.LEFT, padx=2, pady=2)

        # Syntax selection
        tk.Label(toolbar, text="Syntax:", bg='#2d2d2d', fg='#ffffff',
                font=('Arial', 9)).pack(side=tk.LEFT, padx=10)

        self.syntax_var = tk.StringVar(value='Python')
        syntax_combo = ttk.Combobox(toolbar, textvariable=self.syntax_var,
                                    values=['Python', 'JSON', 'Markdown', 'Text'],
                                    state='readonly', width=15)
        syntax_combo.pack(side=tk.LEFT, padx=2)
        syntax_combo.bind('<<ComboboxSelected>>', self._on_syntax_change)

        self.neo_status_label = tk.Label(
            toolbar,
            text="Neo local: loading",
            bg='#2d2d2d',
            fg='#9cdcfe',
            font=('Arial', 9),
            anchor='e'
        )
        self.neo_status_label.pack(side=tk.RIGHT, padx=(10, 0))

        # Status label
        self.status_label = tk.Label(toolbar, text="Ready", bg='#2d2d2d', fg='#00ff00',
                                     font=('Arial', 9), anchor='e')
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # Editor frame with line numbers
        editor_frame = tk.Frame(self, bg='#1e1e1e')
        editor_frame.pack(fill=tk.BOTH, expand=True)

        # Line numbers
        self.line_numbers = LineNumbers(editor_frame, None, bg='#1e1e1e')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Text widget
        self.text = tk.Text(
            editor_frame,
            wrap='none',
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='#ffffff',
            font=('Consolas', 11),
            undo=True,
            maxundo=-1,
            autoseparators=True
        )
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Link line numbers to text
        self.line_numbers.text_widget = self.text

        # Scrollbars
        v_scroll = ttk.Scrollbar(editor_frame, orient='vertical', command=self.text.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.config(yscrollcommand=v_scroll.set)

        h_scroll = ttk.Scrollbar(self, orient='horizontal', command=self.text.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.text.config(xscrollcommand=h_scroll.set)

        # Components
        self.highlighter = SyntaxHighlighter(self.text)
        self.autocomplete = AutoComplete(self.text)

    def _setup_bindings(self):
        """Setup keyboard bindings"""
        self.text.bind('<KeyRelease>', self._on_key_release)
        self.text.bind('<Control-s>', lambda e: self.save_file())
        self.text.bind('<Control-o>', lambda e: self.open_file())
        self.text.bind('<Control-f>', lambda e: self.show_find_replace())
        self.text.bind('<Control-space>', self._show_autocomplete)
        self.text.bind('<Tab>', self._handle_tab)
        self.text.bind('<Return>', self._handle_return)

    def _on_key_release(self, event=None):
        """Handle key release for updates"""
        # Update line numbers
        self.line_numbers.redraw()

        # Update status
        cursor_pos = self.text.index('insert')
        line, col = cursor_pos.split('.')
        self.status_label.config(text=f"Line {line}, Col {col}")

        # Trigger syntax highlighting (debounced)
        if hasattr(self, '_highlight_timer'):
            self.after_cancel(self._highlight_timer)
        self._highlight_timer = self.after(300, self._apply_syntax_highlight)

    def _apply_syntax_highlight(self):
        """Apply syntax highlighting based on selected language"""
        syntax = self.syntax_var.get()
        if syntax == 'Python':
            self.highlighter.highlight_python()
        elif syntax == 'JSON':
            self.highlighter.highlight_json()
        elif syntax == 'Markdown':
            self.highlighter.highlight_markdown()

    def _on_syntax_change(self, event=None):
        """Handle syntax language change"""
        self._apply_syntax_highlight()

    def _set_neo_status(self, message: str, *, foreground: str = '#9cdcfe') -> None:
        self.neo_status_label.config(text=message, fg=foreground)

    def _load_neo_local_runtime(self) -> Dict[str, Any]:
        if not self.local_runtime_path.exists():
            return {}
        try:
            return json.loads(self.local_runtime_path.read_text(encoding='utf-8'))
        except Exception:
            return {}

    def _refresh_neo_runtime(self) -> None:
        payload = self._load_neo_local_runtime()
        if not payload:
            self._set_neo_status("Neo local: contract missing", foreground='#d7ba7d')
            return

        endpoint = (payload.get("endpoint_policy") or {}).get("base_url", "http://localhost:11434")
        models = payload.get("available_models") or []
        active_profile = payload.get("active_profile", "unknown")
        self.temp_shell_registry_path = Path(
            (payload.get("editor_bridge") or {}).get("temp_shell_registry_path") or self.temp_shell_registry_path
        )
        model_name = models[0] if models else 'n/a'
        self._set_neo_status(f"Neo local: {active_profile} | {model_name} | {endpoint}")

    def _stage_neo_task(self) -> None:
        payload = self._load_neo_local_runtime()
        if not payload:
            messagebox.showwarning(
                "Neo Local Runtime",
                "Neo local runtime contract is not available yet.",
                parent=self,
            )
            self._set_neo_status("Neo local: no contract", foreground='#d7ba7d')
            return

        editor_bridge = payload.get("editor_bridge") or {}
        self.temp_shell_registry_path = Path(
            editor_bridge.get("temp_shell_registry_path") or self.temp_shell_registry_path
        )
        temp_shells = payload.get("temp_shells") or []
        active_shell = next(
            (
                item for item in temp_shells
                if isinstance(item, dict) and item.get("shell_id") == "trinity_editor_shell"
            ),
            temp_shells[0] if temp_shells else {},
        )

        current_file = str(self.current_file) if self.current_file else f"scratch://{self.syntax_var.get().lower()}"
        buffer_content = self.get_content()
        task_id = f"neo_temp_shell_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        entry = {
            "task_id": task_id,
            "kind": "editor_temp_shell_task",
            "source_floor": "Trinity",
            "target_floor": "Neo",
            "shell_id": active_shell.get("shell_id", "trinity_editor_shell"),
            "model": active_shell.get("default_model"),
            "file_path": current_file,
            "file_name": Path(current_file).name if not current_file.startswith("scratch://") else current_file,
            "syntax": self.syntax_var.get(),
            "cursor": self.text.index('insert'),
            "line_count": buffer_content.count('\n') + 1 if buffer_content else 0,
            "char_count": len(buffer_content),
            "write_scope": active_shell.get("write_scope") or [],
            "requested_outcome": "bounded_local_code_assist_or_handoff",
            "approval_required": True,
            "staged_at": datetime.now(timezone.utc).isoformat(),
            "context_excerpt": buffer_content.splitlines()[:20],
        }

        registry = {
            "runtime_id": payload.get("runtime_id"),
            "primary_floor": payload.get("primary_floor"),
            "local_endpoint": (payload.get("endpoint_policy") or {}).get("base_url"),
            "temp_shells": temp_shells,
            "handoff_contract": payload.get("handoff_contract") or {},
            "staged_tasks": [],
        }
        if self.temp_shell_registry_path.exists():
            try:
                existing = json.loads(self.temp_shell_registry_path.read_text(encoding='utf-8'))
                if isinstance(existing, dict):
                    registry.update(existing)
                    registry["staged_tasks"] = list(existing.get("staged_tasks") or [])
            except Exception:
                pass
        registry["staged_tasks"].append(entry)
        self.temp_shell_registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.temp_shell_registry_path.write_text(json.dumps(registry, indent=2), encoding='utf-8')

        channel_note = "registry staged"
        try:
            z_axis_root = self.lightspeed_root / "Z Axis"
            merovingian_root = z_axis_root / "Z-4_Merovingian"
            for path in (self.lightspeed_root, z_axis_root, merovingian_root):
                value = str(path)
                if value not in sys.path and path.exists():
                    sys.path.insert(0, value)
            from core.services import get_z_direct  # type: ignore

            z_direct = get_z_direct()
            envelope = z_direct.make_envelope(
                kind="object",
                channel="Z+2",
                z_context="Z+3_Trinity",
                source="trinity.code_editor.stage_temp_shell",
                tags=["neo_temp_shell", "editor_handoff", "local_llm"],
                payload=entry,
            )
            z_direct.append_object("Z+2", envelope)
            channel_note = "Z+2 staged"
        except Exception:
            channel_note = "registry staged"

        self._set_neo_status(
            f"Neo local: staged {entry['file_name']} ({channel_note})",
            foreground='#4ec9b0',
        )
        self.status_label.config(text=f"Neo staged: {entry['file_name']}")

    def _show_autocomplete(self, event=None):
        """Show auto-complete"""
        # Get word start
        current_line = self.text.get('insert linestart', 'insert')
        word_start_idx = len(current_line)
        for i in range(len(current_line) - 1, -1, -1):
            if not current_line[i].isalnum() and current_line[i] != '_':
                word_start_idx = i + 1
                break

        word_start = f'insert linestart + {word_start_idx}c'
        self.autocomplete.show(word_start)
        return 'break'

    def _handle_tab(self, event=None):
        """Handle tab key - insert spaces"""
        self.text.insert('insert', '    ')
        return 'break'

    def _handle_return(self, event=None):
        """Handle return key - smart indentation"""
        # Get current line
        current_line = self.text.get('insert linestart', 'insert')

        # Calculate indentation
        indent = len(current_line) - len(current_line.lstrip())

        # Add extra indent if line ends with ':'
        if current_line.rstrip().endswith(':'):
            indent += 4

        # Insert newline and indentation
        self.text.insert('insert', '\n' + ' ' * indent)
        return 'break'

    def open_path(self, filepath: str) -> bool:
        """Open a specific file path (non-dialog). Returns True on success."""
        if not filepath:
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            self.text.delete('1.0', 'end')
            self.text.insert('1.0', content)
            self.current_file = filepath

            # Detect syntax
            if filepath.endswith('.py'):
                self.syntax_var.set('Python')
            elif filepath.endswith('.json'):
                self.syntax_var.set('JSON')
            elif filepath.endswith('.md'):
                self.syntax_var.set('Markdown')
            else:
                self.syntax_var.set('Text')

            self._apply_syntax_highlight()
            self.status_label.config(text=f"Opened: {Path(filepath).name}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{e}")
            return False

    def open_file(self):
        """Open file (dialog)"""
        filepath = filedialog.askopenfilename(
            title="Open File",
            filetypes=[
                ("Python files", "*.py"),
                ("JSON files", "*.json"),
                ("Markdown files", "*.md"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )

        if filepath:
            self.open_path(filepath)

    def save_file(self):
        """Save file"""
        if not self.current_file:
            filepath = filedialog.asksaveasfilename(
                title="Save File",
                defaultextension=".py",
                filetypes=[
                    ("Python files", "*.py"),
                    ("JSON files", "*.json"),
                    ("Markdown files", "*.md"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ]
            )
            if not filepath:
                return
            self.current_file = filepath

        try:
            content = self.text.get('1.0', 'end-1c')
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(content)

            self.status_label.config(text=f"Saved: {Path(self.current_file).name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")

    def show_find_replace(self):
        """Show find and replace dialog"""
        FindReplaceDialog(self, self.text)

    def get_content(self):
        """Get editor content"""
        return self.text.get('1.0', 'end-1c')

    def set_content(self, content: str):
        """Set editor content"""
        self.text.delete('1.0', 'end')
        self.text.insert('1.0', content)
        self._apply_syntax_highlight()


# Demo/Test function
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Advanced Text Editor - Test")
    root.geometry("900x600")

    editor = AdvancedTextEditor(root)
    editor.pack(fill='both', expand=True)

    # Sample Python code
    sample_code = '''def hello_world():
    """Sample function with syntax highlighting"""
    # This is a comment
    name = "LightSpeed"
    version = 3.5

    if name == "LightSpeed":
        print(f"Welcome to {name} v{version}!")
        return True
    return False

class MyClass:
    def __init__(self, value):
        self.value = value

    @property
    def double(self):
        return self.value * 2
'''

    editor.set_content(sample_code)

    root.mainloop()
