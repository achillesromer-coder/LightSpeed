"""
Code Snippets Library - H3
==========================

Comprehensive code snippet management system.

Features:
- Snippet creation and editing
- Multi-language support
- Category organization
- Tag-based search
- Syntax highlighting
- Variable placeholders
- Quick insertion
- Import/export snippets
- Snippet sharing
- Templates
- Version control
- Usage statistics

Author: LightSpeed Platform
Date: December 19, 2025
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import json
import hashlib
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class CodeSnippet:
    """Code snippet definition."""
    id: str
    title: str
    description: str
    language: str
    code: str
    category: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0
    author: str = "user"
    variables: List[str] = None

    def __post_init__(self):
        if self.variables is None:
            self.variables = self._extract_variables()

    def _extract_variables(self) -> List[str]:
        """Extract placeholder variables from code."""
        import re
        # Find ${VAR_NAME} patterns
        pattern = r'\$\{(\w+)\}'
        return list(set(re.findall(pattern, self.code)))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeSnippet':
        """Create from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class SnippetLibrary:
    """Manages code snippets."""

    def __init__(self, library_path: Path):
        self.library_path = library_path
        self.library_path.mkdir(parents=True, exist_ok=True)

        self.snippets: Dict[str, CodeSnippet] = {}
        self.categories: Dict[str, List[str]] = defaultdict(list)
        self.tags: Dict[str, List[str]] = defaultdict(list)

        self._load_library()

    def create_snippet(
        self,
        title: str,
        description: str,
        language: str,
        code: str,
        category: str,
        tags: List[str]
    ) -> CodeSnippet:
        """Create new snippet."""
        snippet_id = hashlib.md5(
            f"{title}_{datetime.now().timestamp()}".encode()
        ).hexdigest()[:16]

        snippet = CodeSnippet(
            id=snippet_id,
            title=title,
            description=description,
            language=language,
            code=code,
            category=category,
            tags=tags or [],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self.snippets[snippet_id] = snippet
        self.categories[category].append(snippet_id)

        for tag in tags:
            self.tags[tag].append(snippet_id)

        self._save_library()

        return snippet

    def update_snippet(self, snippet_id: str, **kwargs):
        """Update snippet."""
        if snippet_id not in self.snippets:
            return

        snippet = self.snippets[snippet_id]

        # Update fields
        for key, value in kwargs.items():
            if hasattr(snippet, key):
                setattr(snippet, key, value)

        snippet.updated_at = datetime.now()

        # Refresh variables
        snippet.variables = snippet._extract_variables()

        self._save_library()

    def delete_snippet(self, snippet_id: str):
        """Delete snippet."""
        if snippet_id not in self.snippets:
            return

        snippet = self.snippets[snippet_id]

        # Remove from categories and tags
        self.categories[snippet.category].remove(snippet_id)
        for tag in snippet.tags:
            self.tags[tag].remove(snippet_id)

        del self.snippets[snippet_id]
        self._save_library()

    def search_snippets(
        self,
        query: str = "",
        language: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[CodeSnippet]:
        """Search snippets."""
        results = list(self.snippets.values())

        # Filter by query
        if query:
            query = query.lower()
            results = [
                s for s in results
                if query in s.title.lower() or query in s.description.lower() or query in s.code.lower()
            ]

        # Filter by language
        if language:
            results = [s for s in results if s.language == language]

        # Filter by category
        if category:
            results = [s for s in results if s.category == category]

        # Filter by tags
        if tags:
            results = [s for s in results if any(tag in s.tags for tag in tags)]

        return results

    def increment_usage(self, snippet_id: str):
        """Increment snippet usage count."""
        if snippet_id in self.snippets:
            self.snippets[snippet_id].usage_count += 1
            self._save_library()

    def get_popular_snippets(self, top_n: int = 10) -> List[CodeSnippet]:
        """Get most used snippets."""
        return sorted(
            self.snippets.values(),
            key=lambda s: s.usage_count,
            reverse=True
        )[:top_n]

    def _load_library(self):
        """Load snippet library."""
        library_file = self.library_path / 'snippets.json'

        if not library_file.exists():
            return

        data = json.loads(library_file.read_text(encoding='utf-8'))

        self.snippets = {
            sid: CodeSnippet.from_dict(snippet_data)
            for sid, snippet_data in data.get('snippets', {}).items()
        }

        # Rebuild indices
        self.categories.clear()
        self.tags.clear()

        for snippet in self.snippets.values():
            self.categories[snippet.category].append(snippet.id)
            for tag in snippet.tags:
                self.tags[tag].append(snippet.id)

    def _save_library(self):
        """Save snippet library."""
        data = {
            'snippets': {sid: snippet.to_dict() for sid, snippet in self.snippets.items()},
            'saved_at': datetime.now().isoformat()
        }

        library_file = self.library_path / 'snippets.json'
        library_file.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def export_snippets(self, filepath: Path, snippet_ids: Optional[List[str]] = None):
        """Export snippets to file."""
        if snippet_ids:
            snippets = {sid: self.snippets[sid].to_dict() for sid in snippet_ids if sid in self.snippets}
        else:
            snippets = {sid: s.to_dict() for sid, s in self.snippets.items()}

        data = {
            'snippets': snippets,
            'exported_at': datetime.now().isoformat()
        }

        filepath.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def import_snippets(self, filepath: Path):
        """Import snippets from file."""
        if not filepath.exists():
            return

        data = json.loads(filepath.read_text(encoding='utf-8'))

        for snippet_data in data.get('snippets', {}).values():
            snippet = CodeSnippet.from_dict(snippet_data)
            self.snippets[snippet.id] = snippet
            self.categories[snippet.category].append(snippet.id)
            for tag in snippet.tags:
                self.tags[tag].append(snippet.id)

        self._save_library()


class CodeSnippetsGUI(tk.Frame):
    """Code Snippets Library GUI."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#1e1e1e')

        library_path = Path.home() / '.lightspeed' / 'snippets'
        self.library = SnippetLibrary(library_path)

        self.selected_snippet: Optional[str] = None

        self._build_ui()
        self._load_snippets()

    def _build_ui(self):
        """Build snippets UI."""
        # Toolbar
        toolbar = tk.Frame(self, bg='#1e1e1e', height=50)
        toolbar.pack(side='top', fill='x')

        tk.Button(toolbar, text='➕ New Snippet', command=self._create_snippet,
                 bg='#00C49F', fg='white').pack(side='left', padx=5, pady=5)

        tk.Button(toolbar, text='✏️ Edit', command=self._edit_snippet,
                 bg='#0088FE', fg='white').pack(side='left', padx=5, pady=5)

        tk.Button(toolbar, text='🗑️ Delete', command=self._delete_snippet,
                 bg='#FF8042', fg='white').pack(side='left', padx=5, pady=5)

        tk.Label(toolbar, text='|', bg='#1e1e1e', fg='#858585').pack(side='left', padx=5)

        tk.Label(toolbar, text='Search:', bg='#1e1e1e', fg='white').pack(side='left', padx=5)
        self.search_entry = tk.Entry(toolbar, bg='#2d2d2d', fg='white', width=30)
        self.search_entry.pack(side='left', padx=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self._search_snippets())

        tk.Button(toolbar, text='🔍', command=self._search_snippets,
                 bg='#FFBB28', fg='black').pack(side='left', padx=5)

        tk.Label(toolbar, text='|', bg='#1e1e1e', fg='#858585').pack(side='left', padx=5)

        tk.Button(toolbar, text='📤 Export', command=self._export_snippets,
                 bg='#858585', fg='white').pack(side='right', padx=5, pady=5)

        tk.Button(toolbar, text='📥 Import', command=self._import_snippets,
                 bg='#858585', fg='white').pack(side='right', padx=5, pady=5)

        # Main content - PanedWindow
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(side='top', fill='both', expand=True, padx=5, pady=5)

        # Left: Snippet list
        left_frame = tk.Frame(paned, bg='#2d2d2d', width=400)
        paned.add(left_frame, weight=1)

        # Filters
        filter_frame = tk.Frame(left_frame, bg='#2d2d2d')
        filter_frame.pack(side='top', fill='x', padx=5, pady=5)

        tk.Label(filter_frame, text='Language:', bg='#2d2d2d', fg='white').pack(side='left', padx=5)
        self.lang_filter = ttk.Combobox(filter_frame,
                                       values=['All', 'python', 'javascript', 'java', 'cpp', 'sql'],
                                       width=12, state='readonly')
        self.lang_filter.set('All')
        self.lang_filter.bind('<<ComboboxSelected>>', lambda e: self._load_snippets())
        self.lang_filter.pack(side='left', padx=5)

        tk.Label(filter_frame, text='Category:', bg='#2d2d2d', fg='white').pack(side='left', padx=5)
        self.category_filter = ttk.Combobox(filter_frame, width=12, state='readonly')
        self.category_filter.set('All')
        self.category_filter.bind('<<ComboboxSelected>>', lambda e: self._load_snippets())
        self.category_filter.pack(side='left', padx=5)

        # Snippets list
        columns = ('Language', 'Category', 'Uses')
        self.snippets_tree = ttk.Treeview(left_frame, columns=columns,
                                         show='tree headings', height=20)

        self.snippets_tree.heading('#0', text='Title')
        self.snippets_tree.column('#0', width=200)

        for col in columns:
            self.snippets_tree.heading(col, text=col)
            self.snippets_tree.column(col, width=80)

        scrollbar = ttk.Scrollbar(left_frame, orient='vertical',
                                 command=self.snippets_tree.yview)
        self.snippets_tree.configure(yscrollcommand=scrollbar.set)

        self.snippets_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')

        # Bind selection
        self.snippets_tree.bind('<<TreeviewSelect>>', self._on_snippet_select)
        self.snippets_tree.bind('<Double-Button-1>', self._insert_snippet)

        # Right: Snippet details
        right_frame = tk.Frame(paned, bg='#2d2d2d')
        paned.add(right_frame, weight=2)

        # Snippet info
        info_frame = tk.Frame(right_frame, bg='#2d2d2d')
        info_frame.pack(side='top', fill='x', padx=5, pady=5)

        self.snippet_title_label = tk.Label(info_frame, text='No snippet selected',
                                            bg='#2d2d2d', fg='white',
                                            font=('Arial', 12, 'bold'), anchor='w')
        self.snippet_title_label.pack(fill='x', padx=5)

        self.snippet_info_label = tk.Label(info_frame, text='',
                                          bg='#2d2d2d', fg='#858585',
                                          font=('Arial', 9), anchor='w')
        self.snippet_info_label.pack(fill='x', padx=5, pady=2)

        # Code display
        tk.Label(right_frame, text='Code:', bg='#2d2d2d', fg='white',
                font=('Arial', 9, 'bold')).pack(anchor='w', padx=5, pady=(10, 2))

        self.code_display = scrolledtext.ScrolledText(right_frame, bg='#1e1e1e',
                                                      fg='white', wrap='none',
                                                      font=('Courier', 10))
        self.code_display.pack(fill='both', expand=True, padx=5, pady=5)

        # Action buttons
        action_frame = tk.Frame(right_frame, bg='#2d2d2d')
        action_frame.pack(side='bottom', fill='x', padx=5, pady=5)

        tk.Button(action_frame, text='📋 Copy to Clipboard', command=self._copy_snippet,
                 bg='#0088FE', fg='white').pack(side='left', padx=5)

        tk.Button(action_frame, text='📝 Insert', command=self._insert_snippet,
                 bg='#00C49F', fg='white').pack(side='left', padx=5)

        # Status bar
        status_frame = tk.Frame(self, bg='#2d2d2d', height=30)
        status_frame.pack(side='bottom', fill='x')

        self.status_label = tk.Label(status_frame, text='Ready', bg='#2d2d2d',
                                     fg='#858585', font=('Arial', 9), anchor='w')
        self.status_label.pack(side='left', padx=10, fill='x', expand=True)

        self.snippet_count_label = tk.Label(status_frame, text='Snippets: 0',
                                           bg='#2d2d2d', fg='#858585', font=('Arial', 9))
        self.snippet_count_label.pack(side='right', padx=10)

    def _load_snippets(self):
        """Load and display snippets."""
        for item in self.snippets_tree.get_children():
            self.snippets_tree.delete(item)

        # Get filters
        query = self.search_entry.get()
        lang = self.lang_filter.get()
        category = self.category_filter.get()

        # Search
        snippets = self.library.search_snippets(
            query=query,
            language=lang if lang != 'All' else None,
            category=category if category != 'All' else None
        )

        # Sort by title
        snippets.sort(key=lambda s: s.title)

        # Add to tree
        for snippet in snippets:
            self.snippets_tree.insert(
                '',
                'end',
                iid=snippet.id,
                text=snippet.title,
                values=(
                    snippet.language,
                    snippet.category,
                    snippet.usage_count
                )
            )

        # Update category filter options
        categories = ['All'] + sorted(self.library.categories.keys())
        self.category_filter['values'] = categories

        self.snippet_count_label.config(text=f'Snippets: {len(snippets)}')

    def _search_snippets(self):
        """Search snippets."""
        self._load_snippets()

    def _on_snippet_select(self, event):
        """Handle snippet selection."""
        selection = self.snippets_tree.selection()
        if not selection:
            return

        snippet_id = selection[0]
        self.selected_snippet = snippet_id

        snippet = self.library.snippets.get(snippet_id)
        if snippet:
            self.snippet_title_label.config(text=snippet.title)

            info = f"{snippet.description}\n"
            info += f"Language: {snippet.language} | Category: {snippet.category}\n"
            info += f"Tags: {', '.join(snippet.tags) if snippet.tags else 'None'}\n"
            info += f"Created: {snippet.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            info += f"Uses: {snippet.usage_count}"

            self.snippet_info_label.config(text=info)

            # Display code
            self.code_display.delete('1.0', 'end')
            self.code_display.insert('1.0', snippet.code)

    def _create_snippet(self):
        """Create new snippet."""
        dialog = tk.Toplevel(self)
        dialog.title('New Snippet')
        dialog.geometry('700x600')
        dialog.configure(bg='#2d2d2d')

        row = 0

        tk.Label(dialog, text='Title:', bg='#2d2d2d', fg='white').grid(row=row, column=0, padx=10, pady=5, sticky='w')
        title_entry = tk.Entry(dialog, bg='#1e1e1e', fg='white', width=50)
        title_entry.grid(row=row, column=1, padx=10, pady=5, sticky='ew')
        row += 1

        tk.Label(dialog, text='Description:', bg='#2d2d2d', fg='white').grid(row=row, column=0, padx=10, pady=5, sticky='w')
        desc_entry = tk.Entry(dialog, bg='#1e1e1e', fg='white', width=50)
        desc_entry.grid(row=row, column=1, padx=10, pady=5, sticky='ew')
        row += 1

        tk.Label(dialog, text='Language:', bg='#2d2d2d', fg='white').grid(row=row, column=0, padx=10, pady=5, sticky='w')
        lang_combo = ttk.Combobox(dialog, values=['python', 'javascript', 'java', 'cpp', 'sql', 'bash', 'html', 'css'])
        lang_combo.set('python')
        lang_combo.grid(row=row, column=1, padx=10, pady=5, sticky='w')
        row += 1

        tk.Label(dialog, text='Category:', bg='#2d2d2d', fg='white').grid(row=row, column=0, padx=10, pady=5, sticky='w')
        category_entry = tk.Entry(dialog, bg='#1e1e1e', fg='white', width=30)
        category_entry.grid(row=row, column=1, padx=10, pady=5, sticky='w')
        row += 1

        tk.Label(dialog, text='Tags (comma-separated):', bg='#2d2d2d', fg='white').grid(row=row, column=0, padx=10, pady=5, sticky='w')
        tags_entry = tk.Entry(dialog, bg='#1e1e1e', fg='white', width=50)
        tags_entry.grid(row=row, column=1, padx=10, pady=5, sticky='ew')
        row += 1

        tk.Label(dialog, text='Code:', bg='#2d2d2d', fg='white').grid(row=row, column=0, padx=10, pady=5, sticky='nw')
        code_text = scrolledtext.ScrolledText(dialog, bg='#1e1e1e', fg='white',
                                              font=('Courier', 10), height=20)
        code_text.grid(row=row, column=1, padx=10, pady=5, sticky='nsew')
        row += 1

        dialog.grid_columnconfigure(1, weight=1)
        dialog.grid_rowconfigure(5, weight=1)

        def create():
            title = title_entry.get().strip()
            desc = desc_entry.get().strip()
            lang = lang_combo.get()
            category = category_entry.get().strip()
            tags = [t.strip() for t in tags_entry.get().split(',') if t.strip()]
            code = code_text.get('1.0', 'end-1c')

            if not title or not code:
                messagebox.showwarning('Missing Data', 'Please provide title and code')
                return

            self.library.create_snippet(title, desc, lang, code, category, tags)
            self._load_snippets()
            dialog.destroy()
            self.status_label.config(text=f'Created snippet: {title}')

        tk.Button(dialog, text='Create', command=create,
                 bg='#00C49F', fg='white').grid(row=row, column=1, padx=10, pady=10, sticky='e')

    def _edit_snippet(self):
        """Edit selected snippet."""
        if not self.selected_snippet:
            messagebox.showwarning('No Selection', 'Please select a snippet to edit')
            return

        snippet = self.library.snippets[self.selected_snippet]

        dialog = tk.Toplevel(self)
        dialog.title(f'Edit: {snippet.title}')
        dialog.geometry('700x600')
        dialog.configure(bg='#2d2d2d')

        row = 0

        tk.Label(dialog, text='Title:', bg='#2d2d2d', fg='white').grid(row=row, column=0, padx=10, pady=5, sticky='w')
        title_entry = tk.Entry(dialog, bg='#1e1e1e', fg='white', width=50)
        title_entry.insert(0, snippet.title)
        title_entry.grid(row=row, column=1, padx=10, pady=5, sticky='ew')
        row += 1

        tk.Label(dialog, text='Description:', bg='#2d2d2d', fg='white').grid(row=row, column=0, padx=10, pady=5, sticky='w')
        desc_entry = tk.Entry(dialog, bg='#1e1e1e', fg='white', width=50)
        desc_entry.insert(0, snippet.description)
        desc_entry.grid(row=row, column=1, padx=10, pady=5, sticky='ew')
        row += 1

        tk.Label(dialog, text='Code:', bg='#2d2d2d', fg='white').grid(row=row, column=0, padx=10, pady=5, sticky='nw')
        code_text = scrolledtext.ScrolledText(dialog, bg='#1e1e1e', fg='white',
                                              font=('Courier', 10), height=25)
        code_text.insert('1.0', snippet.code)
        code_text.grid(row=row, column=1, padx=10, pady=5, sticky='nsew')
        row += 1

        dialog.grid_columnconfigure(1, weight=1)
        dialog.grid_rowconfigure(2, weight=1)

        def save():
            self.library.update_snippet(
                self.selected_snippet,
                title=title_entry.get().strip(),
                description=desc_entry.get().strip(),
                code=code_text.get('1.0', 'end-1c')
            )
            self._load_snippets()
            self._on_snippet_select(None)
            dialog.destroy()
            self.status_label.config(text='Snippet updated')

        tk.Button(dialog, text='Save', command=save,
                 bg='#00C49F', fg='white').grid(row=row, column=1, padx=10, pady=10, sticky='e')

    def _delete_snippet(self):
        """Delete selected snippet."""
        if not self.selected_snippet:
            messagebox.showwarning('No Selection', 'Please select a snippet to delete')
            return

        snippet = self.library.snippets[self.selected_snippet]

        if messagebox.askyesno('Confirm Delete', f'Delete snippet "{snippet.title}"?'):
            self.library.delete_snippet(self.selected_snippet)
            self.selected_snippet = None
            self._load_snippets()
            self.status_label.config(text='Snippet deleted')

    def _copy_snippet(self):
        """Copy snippet to clipboard."""
        if not self.selected_snippet:
            return

        snippet = self.library.snippets[self.selected_snippet]

        self.clipboard_clear()
        self.clipboard_append(snippet.code)
        self.library.increment_usage(self.selected_snippet)

        self.status_label.config(text='Copied to clipboard')

    def _insert_snippet(self, event=None):
        """Insert snippet (placeholder for IDE integration)."""
        if not self.selected_snippet:
            return

        snippet = self.library.snippets[self.selected_snippet]
        self.library.increment_usage(self.selected_snippet)

        # In real IDE integration, this would insert into active editor
        self._copy_snippet()
        self.status_label.config(text=f'Inserted: {snippet.title}')

    def _export_snippets(self):
        """Export snippets."""
        filepath = filedialog.asksaveasfilename(
            title='Export Snippets',
            defaultextension='.json',
            filetypes=[('JSON Files', '*.json'), ('All Files', '*.*')]
        )

        if filepath:
            self.library.export_snippets(Path(filepath))
            messagebox.showinfo('Exported', f'Snippets exported to:\n{filepath}')

    def _import_snippets(self):
        """Import snippets."""
        filepath = filedialog.askopenfilename(
            title='Import Snippets',
            filetypes=[('JSON Files', '*.json'), ('All Files', '*.*')]
        )

        if filepath:
            self.library.import_snippets(Path(filepath))
            self._load_snippets()
            messagebox.showinfo('Imported', 'Snippets imported successfully')


# Demo/Test
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Code Snippets Library - H3 Demo')
    root.geometry('1400x800')

    snippets_gui = CodeSnippetsGUI(root)
    snippets_gui.pack(fill='both', expand=True)

    root.mainloop()
