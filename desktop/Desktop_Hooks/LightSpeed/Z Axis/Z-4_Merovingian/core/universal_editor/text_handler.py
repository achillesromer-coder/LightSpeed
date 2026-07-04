"""
Text File Handler - V1.0.0
Handler for plain text and Markdown files

Author: LightSpeed Team
Date: December 27, 2025
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
from pathlib import Path
from typing import List, Dict, Any
import re

from .file_handler import FileHandler, EditorCapability, EditorAction


# ==============================================================================
# Text File Handler
# ==============================================================================

class TextFileHandler(FileHandler):
    """
    Handler for text files (.txt, .md, .markdown, .rst, etc.)

    Features:
    - Basic text editing
    - Line numbers
    - Word wrap toggle
    - Find and replace
    - Markdown preview (for .md files)
    - Character/word/line count
    """

    def __init__(self):
        """Initialize text file handler"""
        super().__init__()

        self.file_type_name = "Text"
        self.supported_extensions = [
            '.txt', '.md', '.markdown', '.rst', '.log',
            '.readme', '.text', '.mdown', '.mdwn'
        ]

        self.capabilities = [
            EditorCapability.READ,
            EditorCapability.WRITE,
            EditorCapability.SEARCH,
            EditorCapability.REPLACE,
            EditorCapability.UNDO_REDO,
        ]

        # Current editor widget reference (for toolbar actions)
        self.current_widget: Optional[tk.Text] = None
        self.current_file: Optional[Path] = None

    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can handle the file"""
        return file_path.suffix.lower() in self.supported_extensions

    def read_file(self, file_path: Path) -> str:
        """Read text file"""
        try:
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Try other encodings
            for encoding in ['latin-1', 'cp1252', 'ascii']:
                try:
                    return file_path.read_text(encoding=encoding)
                except:
                    continue

            raise IOError(f"Could not decode file with any known encoding")

    def write_file(self, file_path: Path, content: str) -> bool:
        """Write text file"""
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
        """Create text editor widget"""
        self.current_file = file_path

        # Create container frame
        container = ttk.Frame(parent)

        # Create text widget with scrollbar
        text_frame = ttk.Frame(container)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Line numbers (optional, can be toggled)
        line_numbers = tk.Text(
            text_frame,
            width=4,
            padx=3,
            takefocus=0,
            border=0,
            background='lightgray',
            state='disabled'
        )
        line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Main text widget
        text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            undo=True,
            maxundo=-1,
            autoseparators=True
        )
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=text_widget.yview)

        # Configure font
        editor_font = tkfont.Font(family="Consolas", size=10)
        text_widget.config(font=editor_font)

        # Insert content
        text_widget.insert('1.0', content)

        # Mark as unmodified
        text_widget.edit_modified(False)

        # Update line numbers
        def update_line_numbers(event=None):
            line_numbers.config(state='normal')
            line_numbers.delete('1.0', tk.END)

            # Get number of lines
            num_lines = int(text_widget.index('end-1c').split('.')[0])

            # Add line numbers
            line_numbers_text = '\n'.join(str(i) for i in range(1, num_lines + 1))
            line_numbers.insert('1.0', line_numbers_text)

            line_numbers.config(state='disabled')

        # Bind line number updates
        text_widget.bind('<<Modified>>', update_line_numbers)
        text_widget.bind('<KeyRelease>', update_line_numbers)

        # Initial line numbers
        update_line_numbers()

        # Apply Markdown syntax highlighting if .md file
        if file_path.suffix.lower() in ['.md', '.markdown']:
            self._apply_markdown_highlighting(text_widget)

        # Info bar at bottom
        info_bar = ttk.Label(container, text="", relief=tk.SUNKEN, anchor=tk.W)
        info_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Update info bar
        def update_info_bar(event=None):
            content = text_widget.get('1.0', 'end-1c')
            lines = content.count('\n') + 1
            words = len(content.split())
            chars = len(content)

            cursor_pos = text_widget.index(tk.INSERT)

            info_bar.config(
                text=f"Line {cursor_pos} | {lines} lines | {words} words | {chars} chars"
            )

        text_widget.bind('<KeyRelease>', update_info_bar)
        text_widget.bind('<ButtonRelease>', update_info_bar)
        update_info_bar()

        # Store reference
        self.current_widget = text_widget

        # Store line numbers widget as attribute for toggling
        text_widget.line_numbers = line_numbers

        return container

    def get_content_from_widget(self, widget: tk.Widget) -> str:
        """Get content from text widget"""
        # Widget is the container frame, find the Text widget
        for child in widget.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Text) and subchild.cget('takefocus') != 0:
                        return subchild.get('1.0', 'end-1c')

        return ""

    def get_toolbar_actions(self) -> List[EditorAction]:
        """Get toolbar actions for text editing"""
        actions = [
            EditorAction(
                action_id="word_wrap",
                label="Word Wrap",
                callback=self._toggle_word_wrap,
                tooltip="Toggle word wrap"
            ),
            EditorAction(
                action_id="line_numbers",
                label="Line #",
                callback=self._toggle_line_numbers,
                tooltip="Toggle line numbers"
            ),
        ]

        # Add Markdown preview for .md files
        if self.current_file and self.current_file.suffix.lower() in ['.md', '.markdown']:
            actions.append(EditorAction(
                action_id="markdown_preview",
                label="Preview",
                callback=self._show_markdown_preview,
                tooltip="Show Markdown preview"
            ))

        actions.extend([
            EditorAction(
                action_id="stats",
                label="Stats",
                callback=self._show_stats,
                tooltip="Show document statistics"
            ),
            EditorAction(
                action_id="format",
                label="Format",
                callback=self._format_text,
                tooltip="Format text"
            ),
        ])

        return actions

    def _toggle_word_wrap(self):
        """Toggle word wrap"""
        if not self.current_widget:
            return

        current_wrap = self.current_widget.cget('wrap')
        new_wrap = tk.NONE if current_wrap == tk.WORD else tk.WORD
        self.current_widget.config(wrap=new_wrap)

    def _toggle_line_numbers(self):
        """Toggle line numbers display"""
        if not self.current_widget or not hasattr(self.current_widget, 'line_numbers'):
            return

        line_numbers = self.current_widget.line_numbers

        if line_numbers.winfo_viewable():
            line_numbers.pack_forget()
        else:
            line_numbers.pack(side=tk.LEFT, fill=tk.Y, before=self.current_widget)

    def _show_markdown_preview(self):
        """Show Markdown preview in new window"""
        if not self.current_widget:
            return

        content = self.current_widget.get('1.0', 'end-1c')

        # Create preview window
        preview_window = tk.Toplevel()
        preview_window.title(f"Preview: {self.current_file.name}")
        preview_window.geometry("600x800")

        # Convert Markdown to HTML (basic)
        html_content = self._markdown_to_html(content)

        # Display in text widget (in production, use HTML renderer)
        preview_text = tk.Text(preview_window, wrap=tk.WORD)
        preview_text.pack(fill=tk.BOTH, expand=True)
        preview_text.insert('1.0', html_content)
        preview_text.config(state='disabled')

    def _show_stats(self):
        """Show document statistics"""
        if not self.current_widget:
            return

        content = self.current_widget.get('1.0', 'end-1c')

        lines = content.count('\n') + 1
        words = len(content.split())
        chars = len(content)
        chars_no_spaces = len(content.replace(' ', '').replace('\n', '').replace('\t', ''))

        # Count paragraphs
        paragraphs = len([p for p in content.split('\n\n') if p.strip()])

        # Count sentences (approximation)
        sentences = content.count('.') + content.count('!') + content.count('?')

        stats = f"""Document Statistics

File: {self.current_file.name if self.current_file else 'Untitled'}

Lines: {lines}
Paragraphs: {paragraphs}
Sentences: {sentences}
Words: {words}
Characters (with spaces): {chars}
Characters (without spaces): {chars_no_spaces}

Average words per sentence: {words / max(sentences, 1):.1f}
Average characters per word: {chars / max(words, 1):.1f}
"""

        from tkinter import messagebox
        messagebox.showinfo("Document Statistics", stats)

    def _format_text(self):
        """Format text (remove extra whitespace, etc.)"""
        if not self.current_widget:
            return

        content = self.current_widget.get('1.0', 'end-1c')

        # Remove trailing whitespace from lines
        lines = content.split('\n')
        lines = [line.rstrip() for line in lines]

        # Remove multiple blank lines
        formatted_lines = []
        prev_blank = False

        for line in lines:
            is_blank = not line.strip()

            if is_blank:
                if not prev_blank:
                    formatted_lines.append('')
                prev_blank = True
            else:
                formatted_lines.append(line)
                prev_blank = False

        formatted_content = '\n'.join(formatted_lines)

        # Update widget
        self.current_widget.delete('1.0', tk.END)
        self.current_widget.insert('1.0', formatted_content)

    def _apply_markdown_highlighting(self, text_widget: tk.Text):
        """Apply basic Markdown syntax highlighting"""
        # Define tags
        text_widget.tag_config('heading1', font=('Helvetica', 16, 'bold'), foreground='#2E86AB')
        text_widget.tag_config('heading2', font=('Helvetica', 14, 'bold'), foreground='#2E86AB')
        text_widget.tag_config('heading3', font=('Helvetica', 12, 'bold'), foreground='#2E86AB')
        text_widget.tag_config('bold', font=('Consolas', 10, 'bold'))
        text_widget.tag_config('italic', font=('Consolas', 10, 'italic'))
        text_widget.tag_config('code', background='#f0f0f0', foreground='#c7254e')
        text_widget.tag_config('link', foreground='#0366d6', underline=True)
        text_widget.tag_config('quote', foreground='#6a737d', lmargin1=20, lmargin2=20)

        def highlight_markdown(event=None):
            # Remove existing tags
            for tag in ['heading1', 'heading2', 'heading3', 'bold', 'italic', 'code', 'link', 'quote']:
                text_widget.tag_remove(tag, '1.0', tk.END)

            content = text_widget.get('1.0', 'end-1c')
            lines = content.split('\n')

            for i, line in enumerate(lines, 1):
                # Headings
                if line.startswith('# '):
                    text_widget.tag_add('heading1', f'{i}.0', f'{i}.end')
                elif line.startswith('## '):
                    text_widget.tag_add('heading2', f'{i}.0', f'{i}.end')
                elif line.startswith('### '):
                    text_widget.tag_add('heading3', f'{i}.0', f'{i}.end')

                # Blockquotes
                elif line.startswith('> '):
                    text_widget.tag_add('quote', f'{i}.0', f'{i}.end')

                # Inline code
                for match in re.finditer(r'`([^`]+)`', line):
                    start = f'{i}.{match.start()}'
                    end = f'{i}.{match.end()}'
                    text_widget.tag_add('code', start, end)

                # Bold
                for match in re.finditer(r'\*\*([^*]+)\*\*', line):
                    start = f'{i}.{match.start()}'
                    end = f'{i}.{match.end()}'
                    text_widget.tag_add('bold', start, end)

                # Italic
                for match in re.finditer(r'\*([^*]+)\*', line):
                    start = f'{i}.{match.start()}'
                    end = f'{i}.{match.end()}'
                    text_widget.tag_add('italic', start, end)

                # Links
                for match in re.finditer(r'\[([^\]]+)\]\(([^\)]+)\)', line):
                    start = f'{i}.{match.start()}'
                    end = f'{i}.{match.end()}'
                    text_widget.tag_add('link', start, end)

        # Bind highlighting
        text_widget.bind('<KeyRelease>', highlight_markdown)
        highlight_markdown()

    def _markdown_to_html(self, markdown: str) -> str:
        """Convert Markdown to HTML (basic implementation)"""
        html_lines = []

        for line in markdown.split('\n'):
            # Headings
            if line.startswith('### '):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith('## '):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith('# '):
                html_lines.append(f"<h1>{line[2:]}</h1>")

            # Bold
            elif '**' in line:
                line = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', line)
                html_lines.append(f"<p>{line}</p>")

            # Italic
            elif '*' in line:
                line = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', line)
                html_lines.append(f"<p>{line}</p>")

            # Links
            elif '[' in line and '](' in line:
                line = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', line)
                html_lines.append(f"<p>{line}</p>")

            # Regular paragraph
            elif line.strip():
                html_lines.append(f"<p>{line}</p>")

            # Empty line
            else:
                html_lines.append("<br>")

        return '\n'.join(html_lines)
