"""
Rich Text Document Editor - A5
==============================

Advanced rich text editor with Markdown support, live preview, and export capabilities.

Features:
- Markdown editing with syntax highlighting
- Live preview (split view)
- Formatting toolbar (bold, italic, headers, lists, code blocks)
- Insert images, links, tables
- Export to HTML, PDF, Markdown
- Auto-save functionality
- Word count and reading time

Author: LightSpeed Platform
Date: December 16, 2025
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json


class MarkdownSyntaxHighlighter:
    """Syntax highlighting for Markdown text."""

    def __init__(self, text_widget: tk.Text):
        self.text = text_widget
        self._configure_tags()

    def _configure_tags(self):
        """Configure text tags for different Markdown elements."""
        # Headers
        self.text.tag_config('h1', font=('Arial', 18, 'bold'), foreground='#00C49F')
        self.text.tag_config('h2', font=('Arial', 16, 'bold'), foreground='#00C49F')
        self.text.tag_config('h3', font=('Arial', 14, 'bold'), foreground='#00C49F')
        self.text.tag_config('h4', font=('Arial', 12, 'bold'), foreground='#0088FE')

        # Text formatting
        self.text.tag_config('bold', font=('Arial', 10, 'bold'))
        self.text.tag_config('italic', font=('Arial', 10, 'italic'))
        self.text.tag_config('code_inline', background='#2d2d2d', foreground='#00ff00', font=('Courier', 10))
        self.text.tag_config('code_block', background='#1e1e1e', foreground='#d4d4d4', font=('Courier', 10))

        # Links and images
        self.text.tag_config('link', foreground='#0088FE', underline=True)
        self.text.tag_config('image', foreground='#FFBB28')

        # Lists
        self.text.tag_config('list_item', foreground='#FF8042')

        # Blockquotes
        self.text.tag_config('blockquote', foreground='#858585', font=('Arial', 10, 'italic'))

        # Horizontal rule
        self.text.tag_config('hr', foreground='#404040')

    def highlight(self):
        """Apply syntax highlighting to entire document."""
        # Remove all existing tags
        for tag in self.text.tag_names():
            if tag not in ('sel', 'search'):
                self.text.tag_remove(tag, '1.0', 'end')

        content = self.text.get('1.0', 'end-1c')
        lines = content.split('\n')

        current_line = 1
        in_code_block = False

        for line in lines:
            line_start = f'{current_line}.0'
            line_end = f'{current_line}.end'

            # Code blocks (triple backticks)
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                self.text.tag_add('code_block', line_start, line_end)
                current_line += 1
                continue

            if in_code_block:
                self.text.tag_add('code_block', line_start, line_end)
                current_line += 1
                continue

            # Headers
            if line.startswith('# '):
                self.text.tag_add('h1', line_start, line_end)
            elif line.startswith('## '):
                self.text.tag_add('h2', line_start, line_end)
            elif line.startswith('### '):
                self.text.tag_add('h3', line_start, line_end)
            elif line.startswith('#### '):
                self.text.tag_add('h4', line_start, line_end)

            # Horizontal rule
            elif line.strip() in ('---', '***', '___'):
                self.text.tag_add('hr', line_start, line_end)

            # Lists
            elif re.match(r'^[\s]*[-*+]\s', line) or re.match(r'^[\s]*\d+\.\s', line):
                self.text.tag_add('list_item', line_start, line_end)

            # Blockquotes
            elif line.strip().startswith('>'):
                self.text.tag_add('blockquote', line_start, line_end)

            # Inline formatting (bold, italic, code, links, images)
            else:
                # Bold **text**
                for match in re.finditer(r'\*\*(.*?)\*\*', line):
                    start_idx = f'{current_line}.{match.start()}'
                    end_idx = f'{current_line}.{match.end()}'
                    self.text.tag_add('bold', start_idx, end_idx)

                # Italic *text* or _text_
                for match in re.finditer(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)', line):
                    start_idx = f'{current_line}.{match.start()}'
                    end_idx = f'{current_line}.{match.end()}'
                    self.text.tag_add('italic', start_idx, end_idx)

                for match in re.finditer(r'_([^_]+)_', line):
                    start_idx = f'{current_line}.{match.start()}'
                    end_idx = f'{current_line}.{match.end()}'
                    self.text.tag_add('italic', start_idx, end_idx)

                # Inline code `code`
                for match in re.finditer(r'`([^`]+)`', line):
                    start_idx = f'{current_line}.{match.start()}'
                    end_idx = f'{current_line}.{match.end()}'
                    self.text.tag_add('code_inline', start_idx, end_idx)

                # Links [text](url)
                for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', line):
                    start_idx = f'{current_line}.{match.start()}'
                    end_idx = f'{current_line}.{match.end()}'
                    self.text.tag_add('link', start_idx, end_idx)

                # Images ![alt](url)
                for match in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', line):
                    start_idx = f'{current_line}.{match.start()}'
                    end_idx = f'{current_line}.{match.end()}'
                    self.text.tag_add('image', start_idx, end_idx)

            current_line += 1


class MarkdownPreview(tk.Frame):
    """Live preview of rendered Markdown."""

    def __init__(self, parent):
        super().__init__(parent, bg='#ffffff')
        self._build_ui()

    def _build_ui(self):
        """Build preview UI."""
        # Preview text widget (read-only)
        self.preview_text = tk.Text(
            self,
            wrap='word',
            bg='#ffffff',
            fg='#000000',
            font=('Arial', 10),
            state='disabled',
            padx=20,
            pady=20
        )

        scrollbar = ttk.Scrollbar(self, command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=scrollbar.set)

        self.preview_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self._configure_preview_tags()

    def _configure_preview_tags(self):
        """Configure text tags for rendered preview."""
        self.preview_text.tag_config('h1', font=('Arial', 24, 'bold'), foreground='#1a1a1a', spacing3=10)
        self.preview_text.tag_config('h2', font=('Arial', 20, 'bold'), foreground='#1a1a1a', spacing3=8)
        self.preview_text.tag_config('h3', font=('Arial', 16, 'bold'), foreground='#1a1a1a', spacing3=6)
        self.preview_text.tag_config('h4', font=('Arial', 14, 'bold'), foreground='#1a1a1a', spacing3=4)
        self.preview_text.tag_config('bold', font=('Arial', 10, 'bold'))
        self.preview_text.tag_config('italic', font=('Arial', 10, 'italic'))
        self.preview_text.tag_config('code_inline', background='#f0f0f0', foreground='#d73a49', font=('Courier', 10))
        self.preview_text.tag_config('code_block', background='#f6f8fa', foreground='#24292e', font=('Courier', 10), lmargin1=20, lmargin2=20)
        self.preview_text.tag_config('link', foreground='#0366d6', underline=True)
        self.preview_text.tag_config('list_item', lmargin1=20, lmargin2=40)
        self.preview_text.tag_config('blockquote', background='#f6f8fa', foreground='#6a737d', font=('Arial', 10, 'italic'), lmargin1=20, lmargin2=20)
        self.preview_text.tag_config('hr', foreground='#d1d5da')

    def render(self, markdown_text: str):
        """Render Markdown text to preview."""
        self.preview_text.configure(state='normal')
        self.preview_text.delete('1.0', 'end')

        lines = markdown_text.split('\n')
        in_code_block = False

        for line in lines:
            # Code blocks
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                if not in_code_block:
                    self.preview_text.insert('end', '\n')
                continue

            if in_code_block:
                self.preview_text.insert('end', line + '\n', 'code_block')
                continue

            # Headers
            if line.startswith('# '):
                self.preview_text.insert('end', line[2:] + '\n', 'h1')
            elif line.startswith('## '):
                self.preview_text.insert('end', line[3:] + '\n', 'h2')
            elif line.startswith('### '):
                self.preview_text.insert('end', line[4:] + '\n', 'h3')
            elif line.startswith('#### '):
                self.preview_text.insert('end', line[5:] + '\n', 'h4')

            # Horizontal rule
            elif line.strip() in ('---', '***', '___'):
                self.preview_text.insert('end', '─' * 60 + '\n', 'hr')

            # Lists
            elif re.match(r'^[\s]*[-*+]\s', line):
                indent = len(line) - len(line.lstrip())
                self.preview_text.insert('end', ' ' * indent + '• ' + line.lstrip()[2:] + '\n', 'list_item')
            elif re.match(r'^[\s]*(\d+)\.\s', line):
                indent = len(line) - len(line.lstrip())
                match = re.match(r'^[\s]*(\d+)\.\s', line)
                num = match.group(1)
                self.preview_text.insert('end', ' ' * indent + num + '. ' + line.lstrip()[len(num)+2:] + '\n', 'list_item')

            # Blockquotes
            elif line.strip().startswith('>'):
                quote_text = line.strip()[1:].strip()
                self.preview_text.insert('end', '┃ ' + quote_text + '\n', 'blockquote')

            # Regular text with inline formatting
            else:
                self._render_inline_formatting(line + '\n')

        self.preview_text.configure(state='disabled')

    def _render_inline_formatting(self, text: str):
        """Render inline formatting (bold, italic, code, links)."""
        pos = 0
        while pos < len(text):
            # Bold **text**
            bold_match = re.match(r'\*\*(.*?)\*\*', text[pos:])
            if bold_match:
                self.preview_text.insert('end', bold_match.group(1), 'bold')
                pos += bold_match.end()
                continue

            # Italic *text* or _text_
            italic_match = re.match(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)', text[pos:])
            if not italic_match:
                italic_match = re.match(r'_([^_]+)_', text[pos:])
            if italic_match:
                self.preview_text.insert('end', italic_match.group(1), 'italic')
                pos += italic_match.end()
                continue

            # Inline code `code`
            code_match = re.match(r'`([^`]+)`', text[pos:])
            if code_match:
                self.preview_text.insert('end', code_match.group(1), 'code_inline')
                pos += code_match.end()
                continue

            # Links [text](url)
            link_match = re.match(r'\[([^\]]+)\]\(([^)]+)\)', text[pos:])
            if link_match:
                self.preview_text.insert('end', link_match.group(1), 'link')
                pos += link_match.end()
                continue

            # Images ![alt](url)
            image_match = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', text[pos:])
            if image_match:
                self.preview_text.insert('end', f'[Image: {image_match.group(1) or "No alt text"}]', 'link')
                pos += image_match.end()
                continue

            # Regular character
            self.preview_text.insert('end', text[pos])
            pos += 1


class RichTextEditor(tk.Frame):
    """Complete rich text editor with Markdown support and live preview."""

    def __init__(self, parent, app_root: Path = None):
        super().__init__(parent, bg='#2d2d2d')
        self.app_root = app_root or Path(__file__).resolve().parent.parent.parent
        self.current_file: Optional[Path] = None
        self.modified = False
        self.auto_save_enabled = True
        self.auto_save_interval = 60000  # 60 seconds

        self._build_ui()
        self._setup_bindings()
        self._start_auto_save()

    def _build_ui(self):
        """Build editor UI."""
        # Toolbar
        toolbar = tk.Frame(self, bg='#1e1e1e', height=40)
        toolbar.pack(side='top', fill='x')

        # File operations
        tk.Button(toolbar, text='📄 New', command=self._new_file, bg='#0088FE', fg='white').pack(side='left', padx=2, pady=4)
        tk.Button(toolbar, text='📁 Open', command=self._open_file, bg='#0088FE', fg='white').pack(side='left', padx=2, pady=4)
        tk.Button(toolbar, text='💾 Save', command=self._save_file, bg='#00C49F', fg='white').pack(side='left', padx=2, pady=4)
        tk.Button(toolbar, text='💾 Save As', command=self._save_as_file, bg='#00C49F', fg='white').pack(side='left', padx=2, pady=4)

        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=5)

        # Formatting buttons
        tk.Button(toolbar, text='B', command=self._insert_bold, font=('Arial', 10, 'bold'), bg='#404040', fg='white', width=3).pack(side='left', padx=2)
        tk.Button(toolbar, text='I', command=self._insert_italic, font=('Arial', 10, 'italic'), bg='#404040', fg='white', width=3).pack(side='left', padx=2)
        tk.Button(toolbar, text='`', command=self._insert_code, font=('Courier', 10), bg='#404040', fg='white', width=3).pack(side='left', padx=2)

        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=5)

        # Headers
        tk.Button(toolbar, text='H1', command=lambda: self._insert_header(1), bg='#404040', fg='white', width=3).pack(side='left', padx=2)
        tk.Button(toolbar, text='H2', command=lambda: self._insert_header(2), bg='#404040', fg='white', width=3).pack(side='left', padx=2)
        tk.Button(toolbar, text='H3', command=lambda: self._insert_header(3), bg='#404040', fg='white', width=3).pack(side='left', padx=2)

        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=5)

        # Lists and other
        tk.Button(toolbar, text='• List', command=self._insert_list, bg='#404040', fg='white').pack(side='left', padx=2)
        tk.Button(toolbar, text='🔗 Link', command=self._insert_link, bg='#404040', fg='white').pack(side='left', padx=2)
        tk.Button(toolbar, text='🖼️ Image', command=self._insert_image, bg='#404040', fg='white').pack(side='left', padx=2)
        tk.Button(toolbar, text='📊 Table', command=self._insert_table, bg='#404040', fg='white').pack(side='left', padx=2)

        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=5)

        # Export
        tk.Button(toolbar, text='📤 Export HTML', command=self._export_html, bg='#FFBB28', fg='black').pack(side='left', padx=2)
        tk.Button(toolbar, text='📤 Export PDF', command=self._export_pdf, bg='#FFBB28', fg='black').pack(side='left', padx=2)

        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=5)

        # Preview toggle
        self.preview_visible = tk.BooleanVar(value=True)
        tk.Checkbutton(toolbar, text='👁️ Preview', variable=self.preview_visible,
                      command=self._toggle_preview, bg='#1e1e1e', fg='white',
                      selectcolor='#0088FE').pack(side='left', padx=5)

        # Status bar (word count, reading time)
        self.status_label = tk.Label(toolbar, text='Words: 0 | Characters: 0 | Reading: 0 min',
                                     bg='#1e1e1e', fg='#858585', font=('Arial', 9))
        self.status_label.pack(side='right', padx=10)

        # Main content area (split view)
        self.content_frame = tk.Frame(self, bg='#2d2d2d')
        self.content_frame.pack(side='top', fill='both', expand=True)

        # Editor pane
        editor_frame = tk.Frame(self.content_frame, bg='#2d2d2d')
        editor_frame.pack(side='left', fill='both', expand=True)

        self.editor_text = tk.Text(
            editor_frame,
            wrap='word',
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='#ffffff',
            font=('Arial', 11),
            undo=True,
            maxundo=-1,
            padx=10,
            pady=10
        )

        editor_scrollbar = ttk.Scrollbar(editor_frame, command=self.editor_text.yview)
        self.editor_text.configure(yscrollcommand=editor_scrollbar.set)

        self.editor_text.pack(side='left', fill='both', expand=True)
        editor_scrollbar.pack(side='right', fill='y')

        # Syntax highlighter
        self.highlighter = MarkdownSyntaxHighlighter(self.editor_text)

        # Preview pane
        self.preview_frame = tk.Frame(self.content_frame, bg='#ffffff', width=400)
        self.preview_frame.pack(side='right', fill='both', expand=True)

        tk.Label(self.preview_frame, text='Preview', bg='#f0f0f0', fg='#000000',
                font=('Arial', 12, 'bold'), pady=5).pack(side='top', fill='x')

        self.preview = MarkdownPreview(self.preview_frame)
        self.preview.pack(side='top', fill='both', expand=True)

    def _setup_bindings(self):
        """Setup keyboard bindings."""
        self.editor_text.bind('<KeyRelease>', self._on_text_change)
        self.editor_text.bind('<Control-s>', lambda e: self._save_file())
        self.editor_text.bind('<Control-o>', lambda e: self._open_file())
        self.editor_text.bind('<Control-n>', lambda e: self._new_file())
        self.editor_text.bind('<Control-b>', lambda e: self._insert_bold())
        self.editor_text.bind('<Control-i>', lambda e: self._insert_italic())

    def _on_text_change(self, event=None):
        """Handle text changes."""
        self.modified = True

        # Update syntax highlighting
        self.highlighter.highlight()

        # Update preview
        if self.preview_visible.get():
            content = self.editor_text.get('1.0', 'end-1c')
            self.preview.render(content)

        # Update word count
        self._update_status()

    def _update_status(self):
        """Update status bar with word count and reading time."""
        content = self.editor_text.get('1.0', 'end-1c')

        # Word count
        words = len(content.split())

        # Character count
        chars = len(content)

        # Reading time (average 200 words per minute)
        reading_time = max(1, words // 200)

        self.status_label.config(text=f'Words: {words} | Characters: {chars} | Reading: {reading_time} min')

    def _toggle_preview(self):
        """Toggle preview visibility."""
        if self.preview_visible.get():
            self.preview_frame.pack(side='right', fill='both', expand=True)
            self._on_text_change()
        else:
            self.preview_frame.pack_forget()

    def _new_file(self):
        """Create new document."""
        if self.modified:
            response = messagebox.askyesnocancel('Unsaved Changes',
                                                'Save current document before creating new?')
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self._save_file()

        self.editor_text.delete('1.0', 'end')
        self.current_file = None
        self.modified = False

    def _open_file(self):
        """Open existing document."""
        if self.modified:
            response = messagebox.askyesnocancel('Unsaved Changes',
                                                'Save current document before opening?')
            if response is None:
                return
            elif response:
                self._save_file()

        filepath = filedialog.askopenfilename(
            title='Open Document',
            filetypes=[
                ('Markdown Files', '*.md'),
                ('Text Files', '*.txt'),
                ('All Files', '*.*')
            ]
        )

        if filepath:
            try:
                content = Path(filepath).read_text(encoding='utf-8')
                self.editor_text.delete('1.0', 'end')
                self.editor_text.insert('1.0', content)
                self.current_file = Path(filepath)
                self.modified = False
                self._on_text_change()
            except Exception as e:
                messagebox.showerror('Error', f'Failed to open file:\n{str(e)}')

    def _save_file(self):
        """Save current document."""
        if not self.current_file:
            self._save_as_file()
        else:
            try:
                content = self.editor_text.get('1.0', 'end-1c')
                self.current_file.write_text(content, encoding='utf-8')
                self.modified = False
                messagebox.showinfo('Saved', f'Document saved to:\n{self.current_file}')
            except Exception as e:
                messagebox.showerror('Error', f'Failed to save file:\n{str(e)}')

    def _save_as_file(self):
        """Save document as new file."""
        filepath = filedialog.asksaveasfilename(
            title='Save Document As',
            defaultextension='.md',
            filetypes=[
                ('Markdown Files', '*.md'),
                ('Text Files', '*.txt'),
                ('All Files', '*.*')
            ]
        )

        if filepath:
            self.current_file = Path(filepath)
            self._save_file()

    def _insert_bold(self):
        """Insert bold formatting."""
        try:
            selected = self.editor_text.get('sel.first', 'sel.last')
            self.editor_text.delete('sel.first', 'sel.last')
            self.editor_text.insert('insert', f'**{selected}**')
        except tk.TclError:
            self.editor_text.insert('insert', '****')
            self.editor_text.mark_set('insert', 'insert-2c')
        self._on_text_change()

    def _insert_italic(self):
        """Insert italic formatting."""
        try:
            selected = self.editor_text.get('sel.first', 'sel.last')
            self.editor_text.delete('sel.first', 'sel.last')
            self.editor_text.insert('insert', f'*{selected}*')
        except tk.TclError:
            self.editor_text.insert('insert', '**')
            self.editor_text.mark_set('insert', 'insert-1c')
        self._on_text_change()

    def _insert_code(self):
        """Insert inline code formatting."""
        try:
            selected = self.editor_text.get('sel.first', 'sel.last')
            if '\n' in selected:
                # Multi-line code block
                self.editor_text.delete('sel.first', 'sel.last')
                self.editor_text.insert('insert', f'```\n{selected}\n```')
            else:
                # Inline code
                self.editor_text.delete('sel.first', 'sel.last')
                self.editor_text.insert('insert', f'`{selected}`')
        except tk.TclError:
            self.editor_text.insert('insert', '``')
            self.editor_text.mark_set('insert', 'insert-1c')
        self._on_text_change()

    def _insert_header(self, level: int):
        """Insert header formatting."""
        prefix = '#' * level + ' '
        self.editor_text.insert('insert', prefix)
        self._on_text_change()

    def _insert_list(self):
        """Insert list item."""
        self.editor_text.insert('insert', '- ')
        self._on_text_change()

    def _insert_link(self):
        """Insert link."""
        self.editor_text.insert('insert', '[text](url)')
        self._on_text_change()

    def _insert_image(self):
        """Insert image."""
        self.editor_text.insert('insert', '![alt text](image-url)')
        self._on_text_change()

    def _insert_table(self):
        """Insert table template."""
        table = (
            '| Header 1 | Header 2 | Header 3 |\n'
            '|----------|----------|----------|\n'
            '| Cell 1   | Cell 2   | Cell 3   |\n'
            '| Cell 4   | Cell 5   | Cell 6   |\n'
        )
        self.editor_text.insert('insert', table)
        self._on_text_change()

    def _export_html(self):
        """Export document as HTML."""
        if not self.current_file:
            messagebox.showwarning('No File', 'Please save the document first.')
            return

        filepath = filedialog.asksaveasfilename(
            title='Export as HTML',
            defaultextension='.html',
            filetypes=[('HTML Files', '*.html'), ('All Files', '*.*')]
        )

        if filepath:
            try:
                content = self.editor_text.get('1.0', 'end-1c')
                html = self._markdown_to_html(content)
                Path(filepath).write_text(html, encoding='utf-8')
                messagebox.showinfo('Exported', f'Document exported to:\n{filepath}')
            except Exception as e:
                messagebox.showerror('Error', f'Failed to export:\n{str(e)}')

    def _markdown_to_html(self, markdown: str) -> str:
        """Convert Markdown to HTML (basic implementation)."""
        html = ['<!DOCTYPE html>', '<html>', '<head>',
                '<meta charset="utf-8">',
                '<style>',
                'body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }',
                'code { background: #f0f0f0; padding: 2px 5px; border-radius: 3px; }',
                'pre { background: #f6f8fa; padding: 10px; border-radius: 5px; overflow-x: auto; }',
                'blockquote { border-left: 4px solid #ddd; padding-left: 15px; color: #666; }',
                '</style>',
                '</head>', '<body>']

        lines = markdown.split('\n')
        in_code_block = False

        for line in lines:
            # Code blocks
            if line.strip().startswith('```'):
                if in_code_block:
                    html.append('</pre>')
                else:
                    html.append('<pre><code>')
                in_code_block = not in_code_block
                continue

            if in_code_block:
                html.append(line)
                continue

            # Headers
            if line.startswith('# '):
                html.append(f'<h1>{line[2:]}</h1>')
            elif line.startswith('## '):
                html.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('### '):
                html.append(f'<h3>{line[4:]}</h3>')
            elif line.startswith('#### '):
                html.append(f'<h4>{line[5:]}</h4>')
            # Horizontal rule
            elif line.strip() in ('---', '***', '___'):
                html.append('<hr>')
            # Lists
            elif re.match(r'^[\s]*[-*+]\s', line):
                item = re.sub(r'^[\s]*[-*+]\s', '', line)
                html.append(f'<ul><li>{item}</li></ul>')
            # Blockquotes
            elif line.strip().startswith('>'):
                quote = line.strip()[1:].strip()
                html.append(f'<blockquote>{quote}</blockquote>')
            # Regular paragraph
            elif line.strip():
                # Apply inline formatting
                processed = self._apply_inline_html(line)
                html.append(f'<p>{processed}</p>')
            else:
                html.append('<br>')

        html.extend(['</body>', '</html>'])
        return '\n'.join(html)

    def _apply_inline_html(self, text: str) -> str:
        """Apply inline HTML formatting."""
        # Bold
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        # Italic
        text = re.sub(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)', r'<em>\1</em>', text)
        text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)
        # Inline code
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        # Links
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        # Images
        text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)
        return text

    def _export_pdf(self):
        """Export document as PDF (placeholder - requires external library)."""
        messagebox.showinfo('PDF Export',
                          'PDF export requires additional libraries (reportlab).\n'
                          'Export as HTML and convert using browser print-to-PDF instead.')

    def _start_auto_save(self):
        """Start auto-save timer."""
        if self.auto_save_enabled and self.modified and self.current_file:
            self._save_file()

        # Schedule next auto-save
        self.after(self.auto_save_interval, self._start_auto_save)


# Demo/Test
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Rich Text Editor - A5 Demo')
    root.geometry('1200x700')

    editor = RichTextEditor(root)
    editor.pack(fill='both', expand=True)

    # Insert sample Markdown
    sample = """# LightSpeed Platform Documentation

## Introduction

Welcome to **LightSpeed**, a powerful platform for *workflow automation* and system management.

### Features

- Advanced text editing with syntax highlighting
- Real-time Markdown preview
- Export to multiple formats (HTML, PDF)
- Auto-save functionality

### Code Example

Here's a simple Python function:

```python
def hello_world():
    print("Hello, LightSpeed!")
    return True
```

Inline code example: `import tkinter as tk`

### Links and Images

Visit our [website](https://example.com) for more information.

![LightSpeed Logo](logo.png)

### Tables

| Feature | Status | Priority |
|---------|--------|----------|
| Editor  | ✅     | High     |
| Preview | ✅     | High     |
| Export  | ✅     | Medium   |

### Blockquotes

> "The best way to predict the future is to create it."
> - Alan Kay

---

**Thank you** for using LightSpeed!
"""

    editor.editor_text.insert('1.0', sample)
    editor._on_text_change()

    root.mainloop()
