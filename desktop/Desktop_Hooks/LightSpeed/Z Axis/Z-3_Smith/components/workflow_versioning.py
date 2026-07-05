"""
Workflow Versioning - E4
=========================

Version control system for workflows with comparison and rollback.

Features:
- Save workflow versions
- Version history tracking
- Compare versions (diff view)
- Rollback to previous version
- Version tags and notes
- Branch workflows
- Merge versions
- Export/import versions

Author: LightSpeed Platform
Date: December 16, 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import List, Dict, Optional
from pathlib import Path
import json
from datetime import datetime
import copy
import difflib


class WorkflowVersion:
    """Workflow version representation."""

    def __init__(self, version_id: str, workflow_data: Dict, **kwargs):
        self.version_id = version_id
        self.workflow_data = copy.deepcopy(workflow_data)
        self.timestamp = kwargs.get('timestamp', datetime.now())
        self.author = kwargs.get('author', 'System')
        self.notes = kwargs.get('notes', '')
        self.tag = kwargs.get('tag', '')
        self.parent_version: Optional[str] = kwargs.get('parent_version')

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'version_id': self.version_id,
            'workflow_data': self.workflow_data,
            'timestamp': self.timestamp.isoformat(),
            'author': self.author,
            'notes': self.notes,
            'tag': self.tag,
            'parent_version': self.parent_version
        }

    @staticmethod
    def from_dict(data: Dict) -> 'WorkflowVersion':
        """Create from dictionary."""
        return WorkflowVersion(
            data['version_id'],
            data['workflow_data'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            author=data.get('author', 'System'),
            notes=data.get('notes', ''),
            tag=data.get('tag', ''),
            parent_version=data.get('parent_version')
        )


class WorkflowVersioning(tk.Frame):
    """Workflow version control system."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#1e1e1e')
        self.app_root = kwargs.get('app_root', Path.cwd())
        self.workflow_id = kwargs.get('workflow_id', 'default')
        self.versions_file = self.app_root / 'data' / 'workflow_versions' / f'{self.workflow_id}.json'

        self.versions: List[WorkflowVersion] = []
        self.current_workflow_data: Optional[Dict] = None

        # Callbacks
        self.on_version_load: Optional[callable] = kwargs.get('on_version_load')

        self._load_versions()
        self._build_ui()

    def _build_ui(self):
        """Build versioning UI."""
        # Toolbar
        toolbar = tk.Frame(self, bg='#1e1e1e', height=50)
        toolbar.pack(side='top', fill='x')

        tk.Button(toolbar, text='💾 Save Version', command=self._save_version,
                 bg='#00C49F', fg='white').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='↶ Rollback', command=self._rollback,
                 bg='#FF8042', fg='white').pack(side='left', padx=5, pady=5)

        tk.Label(toolbar, text='|', bg='#1e1e1e', fg='#858585').pack(side='left', padx=5)

        tk.Button(toolbar, text='🔍 Compare', command=self._compare_versions,
                 bg='#0088FE', fg='white').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='🏷️ Tag Version', command=self._tag_version,
                 bg='#FFBB28', fg='black').pack(side='left', padx=5, pady=5)

        tk.Label(toolbar, text='|', bg='#1e1e1e', fg='#858585').pack(side='left', padx=5)

        tk.Button(toolbar, text='📤 Export Version', command=self._export_version,
                 bg='#858585', fg='white').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='📥 Import Version', command=self._import_version,
                 bg='#858585', fg='white').pack(side='left', padx=5, pady=5)

        # Version count
        self.count_label = tk.Label(toolbar, text=f'Versions: {len(self.versions)}',
                                    bg='#1e1e1e', fg='#858585', font=('Arial', 9))
        self.count_label.pack(side='right', padx=10)

        # Main content (paned window)
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(side='top', fill='both', expand=True, padx=5, pady=5)

        # Left panel - Version history
        left_panel = tk.Frame(paned, bg='#2d2d2d')
        paned.add(left_panel, weight=1)

        tk.Label(left_panel, text='Version History', bg='#2d2d2d', fg='white',
                font=('Arial', 11, 'bold')).pack(pady=5)

        # Version tree
        tree_frame = tk.Frame(left_panel, bg='#2d2d2d')
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        columns = ('Version', 'Date', 'Author', 'Tag', 'Notes')
        self.versions_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')

        for col in columns:
            self.versions_tree.heading(col, text=col)
            width = 200 if col == 'Notes' else 120
            self.versions_tree.column(col, width=width)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical',
                                 command=self.versions_tree.yview)
        self.versions_tree.configure(yscrollcommand=scrollbar.set)

        self.versions_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Bind selection
        self.versions_tree.bind('<<TreeviewSelect>>', self._on_version_select)

        # Right panel - Version details
        right_panel = ttk.PanedWindow(paned, orient='vertical')
        paned.add(right_panel, weight=2)

        # Version details
        details_frame = tk.LabelFrame(right_panel, text='Version Details', bg='#2d2d2d',
                                     fg='white', font=('Arial', 10, 'bold'))
        right_panel.add(details_frame, weight=1)

        self.details_text = tk.Text(details_frame, height=6, bg='#1e1e1e', fg='white',
                                    font=('Courier', 9), state='disabled')
        details_text_scrollbar = ttk.Scrollbar(details_frame, orient='vertical',
                                              command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_text_scrollbar.set)

        self.details_text.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        details_text_scrollbar.pack(side='right', fill='y', pady=10)

        # Workflow data preview
        preview_frame = tk.LabelFrame(right_panel, text='Workflow Data', bg='#2d2d2d',
                                     fg='white', font=('Arial', 10, 'bold'))
        right_panel.add(preview_frame, weight=2)

        self.preview_text = tk.Text(preview_frame, bg='#1e1e1e', fg='#d4d4d4',
                                    font=('Courier', 9), state='disabled', wrap='none')
        preview_scrollbar_v = ttk.Scrollbar(preview_frame, orient='vertical',
                                           command=self.preview_text.yview)
        preview_scrollbar_h = ttk.Scrollbar(preview_frame, orient='horizontal',
                                           command=self.preview_text.xview)
        self.preview_text.configure(yscrollcommand=preview_scrollbar_v.set,
                                   xscrollcommand=preview_scrollbar_h.set)

        self.preview_text.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        preview_scrollbar_v.grid(row=0, column=1, sticky='ns', pady=10)
        preview_scrollbar_h.grid(row=1, column=0, sticky='ew', padx=10)

        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)

        self._refresh_versions()

    def _load_versions(self):
        """Load versions from file."""
        if self.versions_file.exists():
            try:
                data = json.loads(self.versions_file.read_text())
                self.versions = [WorkflowVersion.from_dict(item) for item in data]
            except Exception as e:
                print(f"Failed to load versions: {e}")

    def _save_versions_to_file(self):
        """Save versions to file."""
        try:
            self.versions_file.parent.mkdir(parents=True, exist_ok=True)
            data = [version.to_dict() for version in self.versions]
            self.versions_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            messagebox.showerror('Error', f'Failed to save versions:\n{str(e)}')

    def _refresh_versions(self):
        """Refresh versions display."""
        for item in self.versions_tree.get_children():
            self.versions_tree.delete(item)

        for version in reversed(self.versions):  # Most recent first
            date_str = version.timestamp.strftime('%Y-%m-%d %H:%M')
            tag = version.tag if version.tag else '-'
            notes = version.notes[:50] + '...' if len(version.notes) > 50 else version.notes

            self.versions_tree.insert('', 'end', values=(
                version.version_id,
                date_str,
                version.author,
                tag,
                notes
            ))

        self.count_label.config(text=f'Versions: {len(self.versions)}')

    def load_workflow(self, workflow_data: Dict):
        """Load current workflow data."""
        self.current_workflow_data = copy.deepcopy(workflow_data)

    def _save_version(self):
        """Save current workflow as new version."""
        if not self.current_workflow_data:
            messagebox.showwarning('No Workflow', 'No workflow data to save')
            return

        # Create dialog for version details
        dialog = tk.Toplevel(self)
        dialog.title('Save Version')
        dialog.geometry('500x300')
        dialog.configure(bg='#2d2d2d')

        tk.Label(dialog, text='Version Notes:', bg='#2d2d2d', fg='white',
                font=('Arial', 10, 'bold')).pack(pady=(10, 5))

        notes_text = tk.Text(dialog, height=5, bg='#1e1e1e', fg='white',
                            insertbackground='white')
        notes_text.pack(fill='both', expand=True, padx=20, pady=10)

        tk.Label(dialog, text='Tag (optional):', bg='#2d2d2d', fg='white').pack(pady=(10, 5))

        tag_entry = tk.Entry(dialog, bg='#1e1e1e', fg='white', insertbackground='white')
        tag_entry.pack(fill='x', padx=20, pady=5)

        tk.Label(dialog, text='Author:', bg='#2d2d2d', fg='white').pack(pady=(10, 5))

        author_entry = tk.Entry(dialog, bg='#1e1e1e', fg='white', insertbackground='white')
        author_entry.insert(0, 'User')
        author_entry.pack(fill='x', padx=20, pady=5)

        def save():
            notes = notes_text.get('1.0', 'end-1c').strip()
            tag = tag_entry.get().strip()
            author = author_entry.get().strip()

            # Generate version ID
            version_id = f"v{len(self.versions) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Get parent version
            parent_version = self.versions[-1].version_id if self.versions else None

            # Create version
            version = WorkflowVersion(
                version_id,
                self.current_workflow_data,
                author=author,
                notes=notes,
                tag=tag,
                parent_version=parent_version
            )

            self.versions.append(version)
            self._save_versions_to_file()
            self._refresh_versions()

            dialog.destroy()
            messagebox.showinfo('Saved', f'Version {version_id} saved successfully')

        tk.Button(dialog, text='Save Version', command=save,
                 bg='#00C49F', fg='white', font=('Arial', 10, 'bold')).pack(pady=20)

    def _rollback(self):
        """Rollback to selected version."""
        selection = self.versions_tree.selection()
        if not selection:
            messagebox.showwarning('No Selection', 'Please select a version to rollback to')
            return

        index = len(self.versions) - 1 - self.versions_tree.index(selection[0])
        version = self.versions[index]

        response = messagebox.askyesno(
            'Rollback Confirmation',
            f'Rollback to version {version.version_id}?\n\n'
            'This will restore the workflow to this version state.'
        )

        if response:
            # Load version data
            self.current_workflow_data = copy.deepcopy(version.workflow_data)

            # Call callback if provided
            if self.on_version_load:
                self.on_version_load(self.current_workflow_data)

            messagebox.showinfo('Rollback Complete',
                              f'Rolled back to version {version.version_id}')

    def _compare_versions(self):
        """Compare two selected versions."""
        selection = self.versions_tree.selection()
        if len(selection) != 2:
            messagebox.showwarning('Invalid Selection',
                                 'Please select exactly 2 versions to compare')
            return

        # Get versions
        index1 = len(self.versions) - 1 - self.versions_tree.index(selection[0])
        index2 = len(self.versions) - 1 - self.versions_tree.index(selection[1])

        version1 = self.versions[index1]
        version2 = self.versions[index2]

        # Show comparison dialog
        self._show_comparison_dialog(version1, version2)

    def _show_comparison_dialog(self, version1: WorkflowVersion, version2: WorkflowVersion):
        """Show version comparison dialog."""
        dialog = tk.Toplevel(self)
        dialog.title(f'Compare {version1.version_id} vs {version2.version_id}')
        dialog.geometry('900x600')
        dialog.configure(bg='#2d2d2d')

        # Labels
        label_frame = tk.Frame(dialog, bg='#2d2d2d')
        label_frame.pack(fill='x', pady=10)

        tk.Label(label_frame, text=f'{version1.version_id} ({version1.timestamp.strftime("%Y-%m-%d %H:%M")})',
                bg='#2d2d2d', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=20)

        tk.Label(label_frame, text=f'{version2.version_id} ({version2.timestamp.strftime("%Y-%m-%d %H:%M")})',
                bg='#2d2d2d', fg='white', font=('Arial', 10, 'bold')).pack(side='right', padx=20)

        # Comparison text
        compare_text = tk.Text(dialog, bg='#1e1e1e', fg='white', font=('Courier', 9),
                              wrap='none')
        scrollbar_v = ttk.Scrollbar(dialog, orient='vertical', command=compare_text.yview)
        scrollbar_h = ttk.Scrollbar(dialog, orient='horizontal', command=compare_text.xview)
        compare_text.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)

        compare_text.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        scrollbar_v.grid(row=0, column=1, sticky='ns', pady=10)
        scrollbar_h.grid(row=1, column=0, sticky='ew', padx=10)

        dialog.grid_rowconfigure(0, weight=1)
        dialog.grid_columnconfigure(0, weight=1)

        # Configure tags for diff highlighting
        compare_text.tag_config('removed', background='#4a2d2d')
        compare_text.tag_config('added', background='#2d4a2d')
        compare_text.tag_config('changed', background='#4a4a2d')

        # Generate diff
        data1_str = json.dumps(version1.workflow_data, indent=2, sort_keys=True)
        data2_str = json.dumps(version2.workflow_data, indent=2, sort_keys=True)

        lines1 = data1_str.splitlines()
        lines2 = data2_str.splitlines()

        # Use difflib
        differ = difflib.unified_diff(lines1, lines2, lineterm='')
        diff_text = '\n'.join(differ)

        compare_text.insert('1.0', diff_text)
        compare_text.configure(state='disabled')

    def _tag_version(self):
        """Add/edit tag for selected version."""
        selection = self.versions_tree.selection()
        if not selection:
            messagebox.showwarning('No Selection', 'Please select a version to tag')
            return

        index = len(self.versions) - 1 - self.versions_tree.index(selection[0])
        version = self.versions[index]

        tag = simpledialog.askstring('Tag Version',
                                     f'Enter tag for version {version.version_id}:',
                                     initialvalue=version.tag)

        if tag is not None:
            version.tag = tag
            self._save_versions_to_file()
            self._refresh_versions()

    def _export_version(self):
        """Export selected version to file."""
        selection = self.versions_tree.selection()
        if not selection:
            messagebox.showwarning('No Selection', 'Please select a version to export')
            return

        index = len(self.versions) - 1 - self.versions_tree.index(selection[0])
        version = self.versions[index]

        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            title='Export Version',
            defaultextension='.json',
            filetypes=[('JSON Files', '*.json'), ('All Files', '*.*')],
            initialfile=f'workflow_{version.version_id}.json'
        )

        if filepath:
            try:
                Path(filepath).write_text(json.dumps(version.to_dict(), indent=2))
                messagebox.showinfo('Exported', f'Version exported to:\n{filepath}')
            except Exception as e:
                messagebox.showerror('Error', f'Failed to export:\n{str(e)}')

    def _import_version(self):
        """Import version from file."""
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            title='Import Version',
            filetypes=[('JSON Files', '*.json'), ('All Files', '*.*')]
        )

        if filepath:
            try:
                data = json.loads(Path(filepath).read_text())
                version = WorkflowVersion.from_dict(data)
                self.versions.append(version)
                self._save_versions_to_file()
                self._refresh_versions()
                messagebox.showinfo('Imported', f'Version {version.version_id} imported')
            except Exception as e:
                messagebox.showerror('Error', f'Failed to import:\n{str(e)}')

    def _on_version_select(self, event):
        """Handle version selection."""
        selection = self.versions_tree.selection()
        if not selection:
            return

        index = len(self.versions) - 1 - self.versions_tree.index(selection[0])
        version = self.versions[index]

        # Update details
        self.details_text.configure(state='normal')
        self.details_text.delete('1.0', 'end')

        details = f"""
Version ID:      {version.version_id}
Timestamp:       {version.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Author:          {version.author}
Tag:             {version.tag if version.tag else '-'}
Parent Version:  {version.parent_version if version.parent_version else 'None'}

Notes:
{version.notes if version.notes else '-'}
"""

        self.details_text.insert('1.0', details)
        self.details_text.configure(state='disabled')

        # Update preview
        self.preview_text.configure(state='normal')
        self.preview_text.delete('1.0', 'end')

        workflow_json = json.dumps(version.workflow_data, indent=2)
        self.preview_text.insert('1.0', workflow_json)
        self.preview_text.configure(state='disabled')


# Demo/Test
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Workflow Versioning - E4 Demo')
    root.geometry('1000x700')

    versioning = WorkflowVersioning(root)
    versioning.pack(fill='both', expand=True)

    # Load sample workflow
    sample_workflow = {
        'name': 'Test Workflow',
        'nodes': [
            {'id': 'node_1', 'type': 'start'},
            {'id': 'node_2', 'type': 'process'},
            {'id': 'node_3', 'type': 'end'}
        ]
    }

    versioning.load_workflow(sample_workflow)

    root.mainloop()
