"""
Universal Editor - V1.0.0
Main editor engine supporting multiple file formats

Author: LightSpeed Team
Date: December 27, 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

from .file_handler import FileHandlerRegistry, FileHandler, create_handler_registry, EditorCapability


# ==============================================================================
# Editor Session
# ==============================================================================

@dataclass
class EditorSession:
    """
    Represents an active editing session

    Attributes:
        session_id: Unique identifier
        file_path: Path to file being edited
        handler: FileHandler for this file
        widget: Editor widget
        content_modified: Whether content has been modified
        last_saved: Timestamp of last save
        undo_stack: Undo history
        redo_stack: Redo history
    """
    session_id: str
    file_path: Path
    handler: FileHandler
    widget: tk.Widget
    content_modified: bool = False
    last_saved: Optional[datetime] = None
    undo_stack: List[str] = field(default_factory=list)
    redo_stack: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def mark_modified(self):
        """Mark session as modified"""
        self.content_modified = True

    def mark_saved(self):
        """Mark session as saved"""
        self.content_modified = False
        self.last_saved = datetime.now()

    def get_current_content(self) -> str:
        """Get current content from widget"""
        return self.handler.get_content_from_widget(self.widget)


# ==============================================================================
# Universal Editor
# ==============================================================================

class UniversalEditor(tk.Frame):
    """
    Universal file editor supporting multiple formats

    Features:
    - Multi-file tabbed interface
    - Format-specific editing widgets
    - Context-aware toolbars
    - Search and replace
    - Undo/redo
    - Auto-save
    - Split view
    """

    def __init__(self, parent, **kwargs):
        """
        Initialize universal editor

        Args:
            parent: Parent widget
            **kwargs: Additional options
        """
        super().__init__(parent, **kwargs)

        # Initialize handler registry
        self.handler_registry = create_handler_registry()

        # Active sessions
        self.sessions: Dict[str, EditorSession] = {}
        self.active_session_id: Optional[str] = None

        # Callbacks
        self.on_file_opened: Optional[Callable] = None
        self.on_file_saved: Optional[Callable] = None
        self.on_file_closed: Optional[Callable] = None

        # Build UI
        self._build_ui()

    def _build_ui(self):
        """Build editor UI"""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Toolbar
        self.toolbar_frame = ttk.Frame(self)
        self.toolbar_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)

        # Standard toolbar buttons
        ttk.Button(
            self.toolbar_frame,
            text="Open",
            command=self.open_file
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            self.toolbar_frame,
            text="Save",
            command=self.save_file
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            self.toolbar_frame,
            text="Save As",
            command=self.save_file_as
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            self.toolbar_frame,
            text="Close",
            command=self.close_file
        ).pack(side=tk.LEFT, padx=2)

        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(
            side=tk.LEFT, padx=5, fill=tk.Y
        )

        ttk.Button(
            self.toolbar_frame,
            text="Search",
            command=self.show_search
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            self.toolbar_frame,
            text="Replace",
            command=self.show_replace
        ).pack(side=tk.LEFT, padx=2)

        # Context toolbar (for file-specific actions)
        self.context_toolbar_frame = ttk.Frame(self.toolbar_frame)
        self.context_toolbar_frame.pack(side=tk.LEFT, padx=10)

        # Notebook for tabbed interface
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

        # Status bar
        self.status_bar = ttk.Label(
            self,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.grid(row=2, column=0, sticky='ew')

    def open_file(self, file_path: Optional[Path] = None):
        """
        Open a file for editing

        Args:
            file_path: Path to file (None = show dialog)
        """
        # Show file dialog if no path provided
        if file_path is None:
            file_path_str = filedialog.askopenfilename(
                title="Open File",
                filetypes=[
                    ("All Files", "*.*"),
                    ("Text Files", "*.txt"),
                    ("Markdown", "*.md"),
                    ("Python", "*.py"),
                    ("JavaScript", "*.js"),
                    ("JSON", "*.json"),
                    ("YAML", "*.yaml *.yml"),
                    ("CSV", "*.csv"),
                ]
            )

            if not file_path_str:
                return

            file_path = Path(file_path_str)

        # Check if file already open
        for session in self.sessions.values():
            if session.file_path == file_path:
                # Switch to existing tab
                self._activate_session(session.session_id)
                return

        # Get appropriate handler
        handler = self.handler_registry.get_handler(file_path)

        if handler is None:
            messagebox.showerror(
                "Unsupported File Type",
                f"No handler available for {file_path.suffix}"
            )
            return

        # Read file
        try:
            content = handler.read_file(file_path)
        except Exception as e:
            messagebox.showerror(
                "Error Reading File",
                f"Failed to read {file_path.name}:\n{str(e)}"
            )
            return

        # Create editor widget
        tab_frame = ttk.Frame(self.notebook)

        try:
            editor_widget = handler.create_editor_widget(
                tab_frame,
                file_path,
                content
            )
            editor_widget.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            messagebox.showerror(
                "Error Creating Editor",
                f"Failed to create editor for {file_path.name}:\n{str(e)}"
            )
            return

        # Create session
        session_id = f"session_{len(self.sessions)}"
        session = EditorSession(
            session_id=session_id,
            file_path=file_path,
            handler=handler,
            widget=editor_widget
        )

        self.sessions[session_id] = session

        # Add tab
        self.notebook.add(tab_frame, text=file_path.name)
        self.notebook.select(tab_frame)

        # Setup content change tracking
        if isinstance(editor_widget, tk.Text):
            editor_widget.bind('<<Modified>>', lambda e: self._on_content_modified(session_id))

        # Update context toolbar
        self._update_context_toolbar(session)

        # Update status
        self.status_bar.config(text=f"Opened: {file_path}")

        # Callback
        if self.on_file_opened:
            self.on_file_opened(file_path)

    def save_file(self):
        """Save current file"""
        session = self._get_active_session()
        if not session:
            return

        try:
            content = session.get_current_content()

            # Validate content
            is_valid, errors = session.handler.validate_content(content)
            if not is_valid:
                response = messagebox.askyesno(
                    "Validation Errors",
                    f"File has validation errors:\n" +
                    "\n".join(errors) +
                    "\n\nSave anyway?"
                )
                if not response:
                    return

            # Write file
            success = session.handler.write_file(session.file_path, content)

            if success:
                session.mark_saved()
                session.handler.on_save(session.file_path, content)

                # Update tab title (remove asterisk if present)
                tab_index = self._get_tab_index(session.session_id)
                if tab_index is not None:
                    self.notebook.tab(tab_index, text=session.file_path.name)

                self.status_bar.config(text=f"Saved: {session.file_path}")

                # Callback
                if self.on_file_saved:
                    self.on_file_saved(session.file_path)

        except Exception as e:
            messagebox.showerror(
                "Error Saving File",
                f"Failed to save {session.file_path.name}:\n{str(e)}"
            )

    def save_file_as(self):
        """Save current file with new name"""
        session = self._get_active_session()
        if not session:
            return

        file_path_str = filedialog.asksaveasfilename(
            title="Save File As",
            initialfile=session.file_path.name,
            defaultextension=session.file_path.suffix
        )

        if not file_path_str:
            return

        # Update session path
        old_path = session.file_path
        session.file_path = Path(file_path_str)

        # Save
        self.save_file()

        # Update tab title
        tab_index = self._get_tab_index(session.session_id)
        if tab_index is not None:
            self.notebook.tab(tab_index, text=session.file_path.name)

    def close_file(self):
        """Close current file"""
        session = self._get_active_session()
        if not session:
            return

        # Check for unsaved changes
        if session.content_modified:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                f"{session.file_path.name} has unsaved changes.\n\nSave before closing?"
            )

            if response is None:  # Cancel
                return
            elif response:  # Yes - save
                self.save_file()
                # Check if save was successful
                if session.content_modified:
                    return

        # Remove tab
        tab_index = self._get_tab_index(session.session_id)
        if tab_index is not None:
            self.notebook.forget(tab_index)

        # Cleanup session
        session.handler.on_close()
        del self.sessions[session.session_id]

        # Update active session
        if self.active_session_id == session.session_id:
            self.active_session_id = None

        # Clear context toolbar
        for widget in self.context_toolbar_frame.winfo_children():
            widget.destroy()

        # Update status
        self.status_bar.config(text=f"Closed: {session.file_path}")

        # Callback
        if self.on_file_closed:
            self.on_file_closed(session.file_path)

    def show_search(self):
        """Show search dialog"""
        session = self._get_active_session()
        if not session:
            return

        # Create search dialog
        dialog = tk.Toplevel(self)
        dialog.title("Search")
        dialog.geometry("400x150")

        ttk.Label(dialog, text="Search for:").pack(pady=5)

        search_entry = ttk.Entry(dialog, width=40)
        search_entry.pack(pady=5)
        search_entry.focus()

        case_var = tk.BooleanVar()
        ttk.Checkbutton(
            dialog,
            text="Case sensitive",
            variable=case_var
        ).pack(pady=5)

        def do_search():
            query = search_entry.get()
            if not query:
                return

            matches = session.handler.search(
                session.widget,
                query,
                case_var.get()
            )

            if matches:
                # Highlight first match
                if isinstance(session.widget, tk.Text):
                    session.widget.tag_remove('search', '1.0', tk.END)
                    for start, end in matches:
                        session.widget.tag_add('search', start, end)
                    session.widget.tag_config('search', background='yellow')
                    session.widget.see(matches[0][0])

                messagebox.showinfo(
                    "Search Results",
                    f"Found {len(matches)} matches"
                )
            else:
                messagebox.showinfo("Search Results", "No matches found")

        ttk.Button(dialog, text="Search", command=do_search).pack(pady=10)

    def show_replace(self):
        """Show replace dialog"""
        session = self._get_active_session()
        if not session:
            return

        # Create replace dialog
        dialog = tk.Toplevel(self)
        dialog.title("Replace")
        dialog.geometry("400x200")

        ttk.Label(dialog, text="Find:").pack(pady=5)
        find_entry = ttk.Entry(dialog, width=40)
        find_entry.pack(pady=5)

        ttk.Label(dialog, text="Replace with:").pack(pady=5)
        replace_entry = ttk.Entry(dialog, width=40)
        replace_entry.pack(pady=5)

        case_var = tk.BooleanVar()
        ttk.Checkbutton(
            dialog,
            text="Case sensitive",
            variable=case_var
        ).pack(pady=5)

        def do_replace_all():
            old_text = find_entry.get()
            new_text = replace_entry.get()

            if not old_text:
                return

            count = session.handler.replace(
                session.widget,
                old_text,
                new_text,
                case_var.get(),
                all_occurrences=True
            )

            session.mark_modified()
            messagebox.showinfo("Replace", f"Replaced {count} occurrences")
            dialog.destroy()

        ttk.Button(
            dialog,
            text="Replace All",
            command=do_replace_all
        ).pack(pady=10)

    def _get_active_session(self) -> Optional[EditorSession]:
        """Get currently active session"""
        selected = self.notebook.select()
        if not selected:
            return None

        tab_index = self.notebook.index(selected)

        # Find session by tab index
        for i, session in enumerate(self.sessions.values()):
            if i == tab_index:
                return session

        return None

    def _activate_session(self, session_id: str):
        """Activate a session by ID"""
        tab_index = self._get_tab_index(session_id)
        if tab_index is not None:
            self.notebook.select(tab_index)

    def _get_tab_index(self, session_id: str) -> Optional[int]:
        """Get tab index for session"""
        for i, sid in enumerate(self.sessions.keys()):
            if sid == session_id:
                return i
        return None

    def _on_tab_changed(self, event):
        """Handle tab change"""
        session = self._get_active_session()
        if session:
            self.active_session_id = session.session_id
            self._update_context_toolbar(session)
            self.status_bar.config(text=f"Editing: {session.file_path}")

    def _on_content_modified(self, session_id: str):
        """Handle content modification"""
        session = self.sessions.get(session_id)
        if not session:
            return

        if not session.content_modified:
            session.mark_modified()

            # Add asterisk to tab title
            tab_index = self._get_tab_index(session_id)
            if tab_index is not None:
                current_text = self.notebook.tab(tab_index, 'text')
                if not current_text.startswith('*'):
                    self.notebook.tab(tab_index, text='*' + current_text)

        # Reset the modified flag on the widget
        if isinstance(session.widget, tk.Text):
            session.widget.edit_modified(False)

    def _update_context_toolbar(self, session: EditorSession):
        """Update context toolbar for session"""
        # Clear existing buttons
        for widget in self.context_toolbar_frame.winfo_children():
            widget.destroy()

        # Add handler-specific actions
        actions = session.handler.get_toolbar_actions()

        for action in actions:
            btn = ttk.Button(
                self.context_toolbar_frame,
                text=action.label,
                command=action.callback,
                state=tk.NORMAL if action.enabled else tk.DISABLED
            )
            btn.pack(side=tk.LEFT, padx=2)

            if action.tooltip:
                # Simple tooltip (in production, use proper tooltip widget)
                btn.bind('<Enter>', lambda e, t=action.tooltip:
                        self.status_bar.config(text=t))
                btn.bind('<Leave>', lambda e:
                        self.status_bar.config(text=f"Editing: {session.file_path}"))


# ==============================================================================
# Factory Function
# ==============================================================================

def create_editor(parent, **kwargs) -> UniversalEditor:
    """
    Create a new UniversalEditor instance

    Args:
        parent: Parent widget
        **kwargs: Additional options

    Returns:
        UniversalEditor instance
    """
    return UniversalEditor(parent, **kwargs)


# ==============================================================================
# Standalone Test
# ==============================================================================

if __name__ == '__main__':
    root = tk.Tk()
    root.title("Universal Editor Test")
    root.geometry("800x600")

    editor = create_editor(root)
    editor.pack(fill=tk.BOTH, expand=True)

    root.mainloop()
