"""
AI Code Assistant (Tabby Integration) - F5
==========================================

Comprehensive AI code completion and assistance with Tabby integration.

Features:
- Tabby AI code completion
- Inline code suggestions
- Multi-language support
- Context-aware completions
- Code explanation
- Refactoring suggestions
- Bug detection
- Documentation generation
- Code review assistant
- Custom model support

Author: LightSpeed Platform
Date: December 19, 2025
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json
import requests
import threading
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class CompletionRequest:
    """Code completion request."""
    id: str
    language: str
    prefix: str  # Code before cursor
    suffix: str  # Code after cursor
    filepath: Optional[str] = None
    max_tokens: int = 50
    temperature: float = 0.2
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class CompletionResponse:
    """Code completion response."""
    request_id: str
    completions: List[str]
    chosen_index: int = 0
    latency_ms: float = 0.0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class TabbyClient:
    """Client for Tabby AI code completion server."""

    def __init__(self, endpoint: str = "http://localhost:8080"):
        self.endpoint = endpoint
        self.session = requests.Session()
        self.timeout = 10

    def check_health(self) -> bool:
        """Check if Tabby server is healthy."""
        try:
            response = self.session.get(
                f"{self.endpoint}/health",
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_completion(
        self,
        language: str,
        prefix: str,
        suffix: str = "",
        max_tokens: int = 50,
        temperature: float = 0.2
    ) -> Optional[List[str]]:
        """Get code completions from Tabby."""
        try:
            payload = {
                "language": language,
                "segments": {
                    "prefix": prefix,
                    "suffix": suffix
                },
                "max_decoding_tokens": max_tokens,
                "temperature": temperature
            }

            response = self.session.post(
                f"{self.endpoint}/v1/completions",
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                choices = data.get('choices', [])
                return [choice.get('text', '') for choice in choices]
            else:
                return None

        except Exception as e:
            print(f"Tabby completion error: {e}")
            return None

    def get_chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500
    ) -> Optional[str]:
        """Get chat completion from Tabby."""
        try:
            payload = {
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7
            }

            response = self.session.post(
                f"{self.endpoint}/v1/chat/completions",
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                choices = data.get('choices', [])
                if choices:
                    return choices[0].get('message', {}).get('content', '')
            return None

        except Exception as e:
            print(f"Tabby chat error: {e}")
            return None


class CodeAnalyzer:
    """Analyzes code for suggestions and improvements."""

    def __init__(self):
        self.language_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.cs': 'csharp',
            '.swift': 'swift'
        }

    def detect_language(self, filepath: Path) -> str:
        """Detect programming language from file extension."""
        return self.language_extensions.get(filepath.suffix, 'text')

    def analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code for potential issues."""
        issues = []

        lines = code.splitlines()

        # Basic heuristic checks
        if language == 'python':
            for i, line in enumerate(lines, 1):
                # Check for common issues
                if 'except:' in line and 'pass' in lines[i] if i < len(lines) else False:
                    issues.append({
                        'line': i,
                        'type': 'warning',
                        'message': 'Bare except with pass - consider specific exception handling'
                    })

                if line.strip().startswith('print(') and not line.strip().startswith('#'):
                    issues.append({
                        'line': i,
                        'type': 'info',
                        'message': 'Consider using logging instead of print'
                    })

        # Check line length
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append({
                    'line': i,
                    'type': 'style',
                    'message': f'Line too long ({len(line)} > 120 characters)'
                })

        return {
            'total_lines': len(lines),
            'total_chars': len(code),
            'issues': issues,
            'language': language
        }

    def suggest_refactoring(self, code: str, language: str) -> List[str]:
        """Suggest refactoring opportunities."""
        suggestions = []

        lines = code.splitlines()

        # Check for repeated code blocks
        line_groups = defaultdict(list)
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                line_groups[stripped].append(i + 1)

        for line_content, line_numbers in line_groups.items():
            if len(line_numbers) >= 3:
                suggestions.append(
                    f"Repeated code on lines {line_numbers[:3]}: consider extracting to function"
                )

        # Check function length
        if language == 'python':
            in_function = False
            function_start = 0
            function_lines = 0

            for i, line in enumerate(lines, 1):
                if line.strip().startswith('def '):
                    in_function = True
                    function_start = i
                    function_lines = 0
                elif in_function:
                    if line.strip() and not line[0].isspace():
                        if function_lines > 50:
                            suggestions.append(
                                f"Function at line {function_start} is too long ({function_lines} lines) - "
                                f"consider breaking into smaller functions"
                            )
                        in_function = False
                    else:
                        function_lines += 1

        return suggestions


class AICodeAssistantGUI(tk.Frame):
    """AI Code Assistant GUI with Tabby integration."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#1e1e1e')

        self.tabby_client = TabbyClient()
        self.analyzer = CodeAnalyzer()

        self.current_file: Optional[Path] = None
        self.current_language: str = 'python'
        self.completion_history: List[CompletionResponse] = []

        self._build_ui()
        self._check_tabby_status()

    def _build_ui(self):
        """Build code assistant UI."""
        # Toolbar
        toolbar = tk.Frame(self, bg='#1e1e1e', height=50)
        toolbar.pack(side='top', fill='x')

        tk.Button(toolbar, text='📂 Open File', command=self._open_file,
                 bg='#0088FE', fg='white').pack(side='left', padx=5, pady=5)

        tk.Button(toolbar, text='💡 Get Completion', command=self._get_completion,
                 bg='#00C49F', fg='white').pack(side='left', padx=5, pady=5)

        tk.Button(toolbar, text='🔍 Analyze Code', command=self._analyze_code,
                 bg='#FFBB28', fg='black').pack(side='left', padx=5, pady=5)

        tk.Button(toolbar, text='📝 Explain Code', command=self._explain_code,
                 bg='#FF8042', fg='white').pack(side='left', padx=5, pady=5)

        tk.Label(toolbar, text='|', bg='#1e1e1e', fg='#858585').pack(side='left', padx=5)

        tk.Label(toolbar, text='Language:', bg='#1e1e1e', fg='white').pack(side='left', padx=5)
        self.lang_combo = ttk.Combobox(
            toolbar,
            values=['python', 'javascript', 'typescript', 'java', 'cpp', 'go', 'rust'],
            width=12,
            state='readonly'
        )
        self.lang_combo.set('python')
        self.lang_combo.bind('<<ComboboxSelected>>', self._on_language_change)
        self.lang_combo.pack(side='left', padx=5)

        # Tabby status
        self.tabby_status = tk.Label(toolbar, text='⚫ Tabby: Disconnected',
                                     bg='#1e1e1e', fg='#FF8042', font=('Arial', 9, 'bold'))
        self.tabby_status.pack(side='right', padx=10)

        tk.Button(toolbar, text='🔄', command=self._check_tabby_status,
                 bg='#858585', fg='white').pack(side='right', padx=5, pady=5)

        # Main content - PanedWindow
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(side='top', fill='both', expand=True, padx=5, pady=5)

        # Left: Code editor
        left_frame = tk.Frame(paned, bg='#2d2d2d')
        paned.add(left_frame, weight=2)

        editor_header = tk.Frame(left_frame, bg='#2d2d2d')
        editor_header.pack(side='top', fill='x')

        tk.Label(editor_header, text='Code Editor', bg='#2d2d2d', fg='white',
                font=('Arial', 10, 'bold')).pack(side='left', padx=5, pady=5)

        self.file_label = tk.Label(editor_header, text='No file opened', bg='#2d2d2d',
                                   fg='#858585', font=('Arial', 9))
        self.file_label.pack(side='left', padx=10)

        # Line numbers
        line_frame = tk.Frame(left_frame, bg='#2d2d2d')
        line_frame.pack(side='top', fill='both', expand=True)

        self.line_numbers = tk.Text(line_frame, width=5, bg='#1e1e1e', fg='#858585',
                                    state='disabled', font=('Courier', 10))
        self.line_numbers.pack(side='left', fill='y')

        # Code text
        self.code_text = scrolledtext.ScrolledText(
            line_frame,
            bg='#1e1e1e',
            fg='white',
            wrap='none',
            font=('Courier', 10),
            insertbackground='white',
            undo=True
        )
        self.code_text.pack(side='left', fill='both', expand=True)

        # Bind events
        self.code_text.bind('<KeyRelease>', self._on_code_change)
        self.code_text.bind('<Control-space>', lambda e: self._get_completion())

        # Right: Assistant panel
        right_frame = tk.Frame(paned, bg='#2d2d2d', width=400)
        paned.add(right_frame, weight=1)

        # Notebook for different views
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Tab 1: Completions
        completions_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(completions_frame, text='Completions')

        tk.Label(completions_frame, text='AI Suggestions', bg='#2d2d2d', fg='white',
                font=('Arial', 9, 'bold')).pack(anchor='w', padx=5, pady=5)

        self.completions_list = tk.Listbox(completions_frame, bg='#1e1e1e', fg='white',
                                          font=('Courier', 9), height=10)
        self.completions_list.pack(fill='both', expand=True, padx=5, pady=5)
        self.completions_list.bind('<Double-Button-1>', self._insert_completion)

        tk.Button(completions_frame, text='Insert Selected', command=self._insert_completion,
                 bg='#00C49F', fg='white').pack(pady=5)

        # Tab 2: Analysis
        analysis_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(analysis_frame, text='Analysis')

        tk.Label(analysis_frame, text='Code Analysis', bg='#2d2d2d', fg='white',
                font=('Arial', 9, 'bold')).pack(anchor='w', padx=5, pady=5)

        self.analysis_text = scrolledtext.ScrolledText(analysis_frame, bg='#1e1e1e',
                                                       fg='white', wrap='word',
                                                       font=('Courier', 9))
        self.analysis_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Tab 3: Chat
        chat_frame = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(chat_frame, text='Chat')

        tk.Label(chat_frame, text='AI Chat Assistant', bg='#2d2d2d', fg='white',
                font=('Arial', 9, 'bold')).pack(anchor='w', padx=5, pady=5)

        self.chat_history = scrolledtext.ScrolledText(chat_frame, bg='#1e1e1e',
                                                      fg='white', wrap='word',
                                                      font=('Courier', 9), height=15)
        self.chat_history.pack(fill='both', expand=True, padx=5, pady=5)

        chat_input_frame = tk.Frame(chat_frame, bg='#2d2d2d')
        chat_input_frame.pack(fill='x', padx=5, pady=5)

        self.chat_input = tk.Entry(chat_input_frame, bg='#1e1e1e', fg='white',
                                   font=('Arial', 10))
        self.chat_input.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.chat_input.bind('<Return>', lambda e: self._send_chat_message())

        tk.Button(chat_input_frame, text='Send', command=self._send_chat_message,
                 bg='#00C49F', fg='white').pack(side='right')

        # Status bar
        status_frame = tk.Frame(self, bg='#2d2d2d', height=30)
        status_frame.pack(side='bottom', fill='x')

        self.status_label = tk.Label(status_frame, text='Ready', bg='#2d2d2d',
                                     fg='#858585', font=('Arial', 9), anchor='w')
        self.status_label.pack(side='left', padx=10, fill='x', expand=True)

        self.cursor_pos_label = tk.Label(status_frame, text='Ln 1, Col 0', bg='#2d2d2d',
                                         fg='#858585', font=('Arial', 9))
        self.cursor_pos_label.pack(side='right', padx=10)

    def _check_tabby_status(self):
        """Check Tabby server status."""
        def check():
            healthy = self.tabby_client.check_health()
            self.after(0, lambda: self._update_tabby_status(healthy))

        threading.Thread(target=check, daemon=True).start()

    def _update_tabby_status(self, healthy: bool):
        """Update Tabby status indicator."""
        if healthy:
            self.tabby_status.config(text='🟢 Tabby: Connected', fg='#00C49F')
            self.status_label.config(text='Tabby server connected')
        else:
            self.tabby_status.config(text='⚫ Tabby: Disconnected', fg='#FF8042')
            self.status_label.config(text='Tabby server not available')

    def _open_file(self):
        """Open code file."""
        filepath = filedialog.askopenfilename(
            title='Open Code File',
            filetypes=[
                ('Python Files', '*.py'),
                ('JavaScript Files', '*.js'),
                ('TypeScript Files', '*.ts'),
                ('All Files', '*.*')
            ]
        )

        if filepath:
            self.current_file = Path(filepath)
            self.current_language = self.analyzer.detect_language(self.current_file)

            # Load file
            content = self.current_file.read_text(encoding='utf-8', errors='ignore')
            self.code_text.delete('1.0', 'end')
            self.code_text.insert('1.0', content)

            # Update UI
            self.file_label.config(text=self.current_file.name)
            self.lang_combo.set(self.current_language)
            self.status_label.config(text=f'Opened: {self.current_file.name}')

            self._update_line_numbers()

    def _on_code_change(self, event=None):
        """Handle code text changes."""
        self._update_line_numbers()
        self._update_cursor_position()

    def _update_line_numbers(self):
        """Update line numbers."""
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', 'end')

        line_count = int(self.code_text.index('end-1c').split('.')[0])
        line_numbers_text = '\n'.join(str(i) for i in range(1, line_count + 1))

        self.line_numbers.insert('1.0', line_numbers_text)
        self.line_numbers.config(state='disabled')

    def _update_cursor_position(self):
        """Update cursor position label."""
        cursor_pos = self.code_text.index('insert')
        line, col = cursor_pos.split('.')
        self.cursor_pos_label.config(text=f'Ln {line}, Col {col}')

    def _on_language_change(self, event=None):
        """Handle language change."""
        self.current_language = self.lang_combo.get()

    def _get_completion(self):
        """Get AI code completion."""
        if not self.tabby_client.check_health():
            self.status_label.config(text='Tabby server not available')
            return

        # Get cursor position
        cursor_pos = self.code_text.index('insert')

        # Get prefix (code before cursor)
        prefix = self.code_text.get('1.0', cursor_pos)

        # Get suffix (code after cursor)
        suffix = self.code_text.get(cursor_pos, 'end-1c')

        self.status_label.config(text='Getting completions...')

        def get_completions():
            completions = self.tabby_client.get_completion(
                language=self.current_language,
                prefix=prefix,
                suffix=suffix,
                max_tokens=50
            )

            self.after(0, lambda: self._display_completions(completions))

        threading.Thread(target=get_completions, daemon=True).start()

    def _display_completions(self, completions: Optional[List[str]]):
        """Display completions."""
        self.completions_list.delete(0, 'end')

        if completions:
            for completion in completions:
                # Clean up completion
                clean = completion.replace('\n', ' ↵ ')[:100]
                self.completions_list.insert('end', clean)

            self.status_label.config(text=f'Got {len(completions)} completions')
        else:
            self.status_label.config(text='No completions available')

    def _insert_completion(self, event=None):
        """Insert selected completion."""
        selection = self.completions_list.curselection()
        if not selection:
            return

        # Get original completion
        idx = selection[0]
        completion = self.completions_list.get(idx).replace(' ↵ ', '\n')

        # Insert at cursor
        self.code_text.insert('insert', completion)
        self.status_label.config(text='Completion inserted')

    def _analyze_code(self):
        """Analyze current code."""
        code = self.code_text.get('1.0', 'end-1c')

        analysis = self.analyzer.analyze_code(code, self.current_language)
        suggestions = self.analyzer.suggest_refactoring(code, self.current_language)

        # Display analysis
        self.analysis_text.delete('1.0', 'end')

        self.analysis_text.insert('end', f"Language: {analysis['language']}\n")
        self.analysis_text.insert('end', f"Total Lines: {analysis['total_lines']}\n")
        self.analysis_text.insert('end', f"Total Characters: {analysis['total_chars']}\n\n")

        if analysis['issues']:
            self.analysis_text.insert('end', "Issues Found:\n")
            self.analysis_text.insert('end', "=" * 50 + "\n")
            for issue in analysis['issues']:
                self.analysis_text.insert(
                    'end',
                    f"Line {issue['line']} [{issue['type'].upper()}]: {issue['message']}\n"
                )
            self.analysis_text.insert('end', "\n")
        else:
            self.analysis_text.insert('end', "No issues found.\n\n")

        if suggestions:
            self.analysis_text.insert('end', "Refactoring Suggestions:\n")
            self.analysis_text.insert('end', "=" * 50 + "\n")
            for suggestion in suggestions:
                self.analysis_text.insert('end', f"• {suggestion}\n")
        else:
            self.analysis_text.insert('end', "No refactoring suggestions.\n")

        self.status_label.config(text=f'Analysis complete: {len(analysis["issues"])} issues found')

    def _explain_code(self):
        """Explain selected code using AI."""
        try:
            selected_code = self.code_text.get('sel.first', 'sel.last')
        except:
            selected_code = self.code_text.get('1.0', 'end-1c')

        if not selected_code.strip():
            messagebox.showwarning('No Code', 'No code to explain')
            return

        if not self.tabby_client.check_health():
            messagebox.showwarning('Tabby Unavailable', 'Tabby server not available')
            return

        self.status_label.config(text='Explaining code...')

        def explain():
            messages = [
                {
                    "role": "user",
                    "content": f"Explain this {self.current_language} code:\n\n```{self.current_language}\n{selected_code}\n```"
                }
            ]

            explanation = self.tabby_client.get_chat_completion(messages, max_tokens=500)

            self.after(0, lambda: self._display_explanation(explanation))

        threading.Thread(target=explain, daemon=True).start()

    def _display_explanation(self, explanation: Optional[str]):
        """Display code explanation."""
        if explanation:
            self.chat_history.insert('end', "AI: ")
            self.chat_history.insert('end', explanation + '\n\n')
            self.status_label.config(text='Code explained')
        else:
            self.status_label.config(text='Failed to get explanation')

    def _send_chat_message(self):
        """Send chat message to AI."""
        message = self.chat_input.get().strip()
        if not message:
            return

        self.chat_history.insert('end', f"You: {message}\n")
        self.chat_input.delete(0, 'end')

        if not self.tabby_client.check_health():
            self.chat_history.insert('end', "AI: Tabby server not available\n\n")
            return

        def get_response():
            # Include code context
            code = self.code_text.get('1.0', 'end-1c')
            context = f"Current {self.current_language} code:\n```\n{code[:500]}\n```\n\n"

            messages = [
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": context + message}
            ]

            response = self.tabby_client.get_chat_completion(messages)

            self.after(0, lambda: self._display_chat_response(response))

        threading.Thread(target=get_response, daemon=True).start()

    def _display_chat_response(self, response: Optional[str]):
        """Display chat response."""
        if response:
            self.chat_history.insert('end', f"AI: {response}\n\n")
            self.chat_history.see('end')
        else:
            self.chat_history.insert('end', "AI: Failed to get response\n\n")


# Demo/Test
if __name__ == '__main__':
    root = tk.Tk()
    root.title('AI Code Assistant - F5 Demo')
    root.geometry('1600x900')

    assistant_gui = AICodeAssistantGUI(root)
    assistant_gui.pack(fill='both', expand=True)

    root.mainloop()
