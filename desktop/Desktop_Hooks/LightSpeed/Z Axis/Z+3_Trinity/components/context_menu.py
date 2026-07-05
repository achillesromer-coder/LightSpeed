"""
Context Menus - A7
==================

Comprehensive context menu system for all LightSpeed components.

Features:
- Reusable context menu builder
- Component-specific menus (file, text, tree, canvas, etc.)
- Dynamic menu items based on context
- Keyboard shortcuts integration
- Icon support
- Cascading submenus
- Separator management
- Enable/disable items based on state

Author: LightSpeed Platform
Date: December 16, 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import List, Dict, Callable, Optional, Any
from pathlib import Path
import subprocess
import sys


class ContextMenuItem:
    """Single context menu item configuration."""

    def __init__(
        self,
        label: str,
        command: Optional[Callable] = None,
        icon: str = '',
        accelerator: str = '',
        enabled: bool = True,
        checkable: bool = False,
        checked: bool = False,
        submenu: Optional[List['ContextMenuItem']] = None
    ):
        self.label = label
        self.command = command
        self.icon = icon
        self.accelerator = accelerator
        self.enabled = enabled
        self.checkable = checkable
        self.checked = checked
        self.submenu = submenu


class ContextMenuBuilder:
    """Builder for creating context menus."""

    def __init__(self, parent: tk.Widget, tearoff: bool = False):
        self.parent = parent
        self.menu = tk.Menu(parent, tearoff=tearoff, bg='#2d2d2d', fg='white',
                           activebackground='#0088FE', activeforeground='white')

    def add_item(self, item: ContextMenuItem) -> 'ContextMenuBuilder':
        """Add menu item."""
        if item.label == 'separator':
            self.menu.add_separator()
        elif item.submenu:
            # Create submenu
            submenu = tk.Menu(self.menu, tearoff=0, bg='#2d2d2d', fg='white',
                            activebackground='#0088FE', activeforeground='white')
            for subitem in item.submenu:
                if subitem.label == 'separator':
                    submenu.add_separator()
                else:
                    label = f"{subitem.icon} {subitem.label}" if subitem.icon else subitem.label
                    submenu.add_command(
                        label=label,
                        command=subitem.command,
                        accelerator=subitem.accelerator,
                        state='normal' if subitem.enabled else 'disabled'
                    )
            self.menu.add_cascade(label=f"{item.icon} {item.label}" if item.icon else item.label,
                                menu=submenu)
        elif item.checkable:
            self.menu.add_checkbutton(
                label=f"{item.icon} {item.label}" if item.icon else item.label,
                command=item.command,
                accelerator=item.accelerator,
                state='normal' if item.enabled else 'disabled'
            )
        else:
            label = f"{item.icon} {item.label}" if item.icon else item.label
            self.menu.add_command(
                label=label,
                command=item.command,
                accelerator=item.accelerator,
                state='normal' if item.enabled else 'disabled'
            )
        return self

    def add_items(self, items: List[ContextMenuItem]) -> 'ContextMenuBuilder':
        """Add multiple items."""
        for item in items:
            self.add_item(item)
        return self

    def build(self) -> tk.Menu:
        """Return the built menu."""
        return self.menu

    def show(self, event):
        """Show menu at event location."""
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()


class FileContextMenu:
    """Context menu for file operations."""

    @staticmethod
    def create(widget: tk.Widget, filepath: Optional[Path] = None,
              on_open: Optional[Callable] = None,
              on_rename: Optional[Callable] = None,
              on_delete: Optional[Callable] = None,
              on_properties: Optional[Callable] = None) -> tk.Menu:
        """Create file context menu."""

        items = []

        if filepath and filepath.exists():
            # File exists - show file operations
            items.extend([
                ContextMenuItem('Open', on_open or (lambda: FileContextMenu._default_open(filepath)), accelerator='Ctrl+O'),
                ContextMenuItem('Rename', on_rename or (lambda: FileContextMenu._default_rename(filepath)), accelerator='F2'),
                ContextMenuItem('separator'),
                ContextMenuItem('Copy Path', lambda: FileContextMenu._copy_path(filepath)),
                ContextMenuItem('Open Location', lambda: FileContextMenu._open_location(filepath)),
                ContextMenuItem('separator'),
                ContextMenuItem('Properties', on_properties or (lambda: FileContextMenu._show_properties(filepath))),
                ContextMenuItem('separator'),
                ContextMenuItem('Delete', on_delete or (lambda: FileContextMenu._default_delete(filepath)), accelerator='Del'),
            ])
        else:
            # No file - show create operations
            items.extend([
                ContextMenuItem('New File', lambda: FileContextMenu._create_file(widget)),
                ContextMenuItem('New Folder', lambda: FileContextMenu._create_folder(widget)),
                ContextMenuItem('separator'),
                ContextMenuItem('Import', lambda: FileContextMenu._import_file(widget)),
            ])

        builder = ContextMenuBuilder(widget)
        builder.add_items(items)
        return builder.build()

    @staticmethod
    def _default_open(filepath: Path):
        """Default open file action."""
        if sys.platform == 'win32':
            subprocess.run(['start', '', str(filepath)], shell=True)
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(filepath)])
        else:
            subprocess.run(['xdg-open', str(filepath)])

    @staticmethod
    def _default_rename(filepath: Path):
        """Default rename action."""
        new_name = simpledialog.askstring('Rename', 'New name:', initialvalue=filepath.name)
        if new_name:
            new_path = filepath.parent / new_name
            filepath.rename(new_path)
            messagebox.showinfo('Renamed', f'File renamed to:\n{new_name}')

    @staticmethod
    def _default_delete(filepath: Path):
        """Default delete action."""
        response = messagebox.askyesno('Delete', f'Delete {filepath.name}?')
        if response:
            filepath.unlink()
            messagebox.showinfo('Deleted', 'File deleted successfully')

    @staticmethod
    def _copy_path(filepath: Path):
        """Copy file path to clipboard."""
        import tkinter as tk_module
        root = tk_module.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(str(filepath))
        root.destroy()
        messagebox.showinfo('Copied', 'Path copied to clipboard')

    @staticmethod
    def _open_location(filepath: Path):
        """Open file location in explorer."""
        location = filepath.parent
        if sys.platform == 'win32':
            subprocess.run(['explorer', str(location)])
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(location)])
        else:
            subprocess.run(['xdg-open', str(location)])

    @staticmethod
    def _show_properties(filepath: Path):
        """Show file properties."""
        stats = filepath.stat()
        info = f"""
File: {filepath.name}
Location: {filepath.parent}
Size: {stats.st_size} bytes
Created: {stats.st_ctime}
Modified: {stats.st_mtime}
"""
        messagebox.showinfo('Properties', info)

    @staticmethod
    def _create_file(widget):
        """Create new file."""
        filename = simpledialog.askstring('New File', 'File name:')
        if filename:
            Path(filename).touch()
            messagebox.showinfo('Created', f'File created: {filename}')

    @staticmethod
    def _create_folder(widget):
        """Create new folder."""
        foldername = simpledialog.askstring('New Folder', 'Folder name:')
        if foldername:
            Path(foldername).mkdir(exist_ok=True)
            messagebox.showinfo('Created', f'Folder created: {foldername}')

    @staticmethod
    def _import_file(widget):
        """Import file."""
        filepath = filedialog.askopenfilename(title='Import File')
        if filepath:
            messagebox.showinfo('Imported', f'File selected: {filepath}')


class TextContextMenu:
    """Context menu for text widgets."""

    @staticmethod
    def create(text_widget: tk.Text, custom_items: Optional[List[ContextMenuItem]] = None) -> tk.Menu:
        """Create text context menu."""

        def has_selection():
            try:
                text_widget.get('sel.first', 'sel.last')
                return True
            except tk.TclError:
                return False

        items = [
            ContextMenuItem('Cut', lambda: text_widget.event_generate('<<Cut>>'),
                          accelerator='Ctrl+X', enabled=has_selection()),
            ContextMenuItem('Copy', lambda: text_widget.event_generate('<<Copy>>'),
                          accelerator='Ctrl+C', enabled=has_selection()),
            ContextMenuItem('Paste', lambda: text_widget.event_generate('<<Paste>>'),
                          accelerator='Ctrl+V'),
            ContextMenuItem('separator'),
            ContextMenuItem('Select All', lambda: text_widget.tag_add('sel', '1.0', 'end'),
                          accelerator='Ctrl+A'),
            ContextMenuItem('separator'),
            ContextMenuItem('Find', lambda: TextContextMenu._show_find(text_widget),
                          accelerator='Ctrl+F'),
            ContextMenuItem('Replace', lambda: TextContextMenu._show_replace(text_widget),
                          accelerator='Ctrl+H'),
        ]

        if custom_items:
            items.append(ContextMenuItem('separator'))
            items.extend(custom_items)

        builder = ContextMenuBuilder(text_widget)
        builder.add_items(items)
        return builder.build()

    @staticmethod
    def _show_find(text_widget):
        """Show find dialog."""
        try:
            try:
                from .code_editor import FindReplaceDialog  # type: ignore
            except Exception:
                from components.code_editor import FindReplaceDialog  # type: ignore

            dlg = FindReplaceDialog(text_widget.winfo_toplevel(), text_widget)
            try:
                dlg.find_entry.focus_set()
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror('Find', f'Find dialog failed to open:\\n{e}')

    @staticmethod
    def _show_replace(text_widget):
        """Show replace dialog."""
        try:
            try:
                from .code_editor import FindReplaceDialog  # type: ignore
            except Exception:
                from components.code_editor import FindReplaceDialog  # type: ignore

            dlg = FindReplaceDialog(text_widget.winfo_toplevel(), text_widget)
            try:
                dlg.replace_entry.focus_set()
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror('Replace', f'Replace dialog failed to open:\\n{e}')


class TreeContextMenu:
    """Context menu for treeview widgets."""

    @staticmethod
    def create(
        tree_widget: ttk.Treeview,
        on_add: Optional[Callable] = None,
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        on_expand_all: Optional[Callable] = None,
        on_collapse_all: Optional[Callable] = None,
        custom_items: Optional[List[ContextMenuItem]] = None
    ) -> tk.Menu:
        """Create treeview context menu."""

        def has_selection():
            return len(tree_widget.selection()) > 0

        items = [
            ContextMenuItem('Add Item', on_add, icon='', enabled=True),
            ContextMenuItem('Edit Item', on_edit, icon='', enabled=has_selection()),
            ContextMenuItem('Delete Item', on_delete, icon='', enabled=has_selection(), accelerator='Del'),
            ContextMenuItem('separator'),
            ContextMenuItem('Expand All', on_expand_all or (lambda: TreeContextMenu._expand_all(tree_widget))),
            ContextMenuItem('Collapse All', on_collapse_all or (lambda: TreeContextMenu._collapse_all(tree_widget))),
            ContextMenuItem('separator'),
            ContextMenuItem('Copy', lambda: TreeContextMenu._copy_selection(tree_widget),
                          enabled=has_selection(), accelerator='Ctrl+C'),
        ]

        if custom_items:
            items.append(ContextMenuItem('separator'))
            items.extend(custom_items)

        builder = ContextMenuBuilder(tree_widget)
        builder.add_items(items)
        return builder.build()

    @staticmethod
    def _expand_all(tree_widget: ttk.Treeview):
        """Expand all tree items."""
        def expand_recursive(item):
            tree_widget.item(item, open=True)
            for child in tree_widget.get_children(item):
                expand_recursive(child)

        for item in tree_widget.get_children():
            expand_recursive(item)

    @staticmethod
    def _collapse_all(tree_widget: ttk.Treeview):
        """Collapse all tree items."""
        def collapse_recursive(item):
            tree_widget.item(item, open=False)
            for child in tree_widget.get_children(item):
                collapse_recursive(child)

        for item in tree_widget.get_children():
            collapse_recursive(item)

    @staticmethod
    def _copy_selection(tree_widget: ttk.Treeview):
        """Copy selected item to clipboard."""
        selection = tree_widget.selection()
        if selection:
            item = selection[0]
            values = tree_widget.item(item, 'values')
            if values:
                tree_widget.clipboard_clear()
                tree_widget.clipboard_append(str(values))


class CanvasContextMenu:
    """Context menu for canvas widgets."""

    @staticmethod
    def create(
        canvas_widget: tk.Canvas,
        on_clear: Optional[Callable] = None,
        on_save: Optional[Callable] = None,
        on_export: Optional[Callable] = None,
        custom_items: Optional[List[ContextMenuItem]] = None
    ) -> tk.Menu:
        """Create canvas context menu."""

        items = [
            ContextMenuItem('Drawing Tools', submenu=[
                ContextMenuItem('Pencil', lambda: messagebox.showinfo('Tool', 'Pencil selected')),
                ContextMenuItem('Brush', lambda: messagebox.showinfo('Tool', 'Brush selected')),
                ContextMenuItem('Circle', lambda: messagebox.showinfo('Tool', 'Circle selected')),
                ContextMenuItem('Rectangle', lambda: messagebox.showinfo('Tool', 'Rectangle selected')),
                ContextMenuItem('Line', lambda: messagebox.showinfo('Tool', 'Line selected')),
            ]),
            ContextMenuItem('separator'),
            ContextMenuItem('Clear Canvas', on_clear or (lambda: canvas_widget.delete('all')),
                          accelerator='Ctrl+Del'),
            ContextMenuItem('separator'),
            ContextMenuItem('Save', on_save, accelerator='Ctrl+S'),
            ContextMenuItem('Export', submenu=[
                ContextMenuItem('Export as PNG', on_export),
                ContextMenuItem('Export as JPG', on_export),
                ContextMenuItem('Export as PostScript', lambda: CanvasContextMenu._export_ps(canvas_widget)),
            ]),
        ]

        if custom_items:
            items.append(ContextMenuItem('separator'))
            items.extend(custom_items)

        builder = ContextMenuBuilder(canvas_widget)
        builder.add_items(items)
        return builder.build()

    @staticmethod
    def _export_ps(canvas_widget: tk.Canvas):
        """Export canvas to PostScript."""
        filepath = filedialog.asksaveasfilename(
            title='Export as PostScript',
            defaultextension='.ps',
            filetypes=[('PostScript', '*.ps'), ('All Files', '*.*')]
        )
        if filepath:
            canvas_widget.postscript(file=filepath, colormode='color')
            messagebox.showinfo('Exported', f'Canvas exported to:\n{filepath}')


class WorkflowContextMenu:
    """Context menu for workflow nodes."""

    @staticmethod
    def create(
        widget: tk.Widget,
        on_edit: Optional[Callable] = None,
        on_execute: Optional[Callable] = None,
        on_disable: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        on_duplicate: Optional[Callable] = None,
        custom_items: Optional[List[ContextMenuItem]] = None
    ) -> tk.Menu:
        """Create workflow node context menu."""

        items = [
            ContextMenuItem('Edit Node', on_edit, accelerator='F2'),
            ContextMenuItem('Execute Node', on_execute, accelerator='F5'),
            ContextMenuItem('separator'),
            ContextMenuItem('Duplicate', on_duplicate, accelerator='Ctrl+D'),
            ContextMenuItem('Disable', on_disable, checkable=True),
            ContextMenuItem('separator'),
            ContextMenuItem('Connections', submenu=[
                ContextMenuItem('Add Input', lambda: messagebox.showinfo('Input', 'Add input connection')),
                ContextMenuItem('Add Output', lambda: messagebox.showinfo('Output', 'Add output connection')),
                ContextMenuItem('separator'),
                ContextMenuItem('Clear Connections', lambda: messagebox.showinfo('Clear', 'Clear all connections')),
            ]),
            ContextMenuItem('separator'),
            ContextMenuItem('Delete Node', on_delete, accelerator='Del'),
        ]

        if custom_items:
            items.append(ContextMenuItem('separator'))
            items.extend(custom_items)

        builder = ContextMenuBuilder(widget)
        builder.add_items(items)
        return builder.build()


class ZFloorContextMenu:
    """Context menu for Z-Floor components."""

    @staticmethod
    def create(
        widget: tk.Widget,
        floor_name: str,
        on_refresh: Optional[Callable] = None,
        on_configure: Optional[Callable] = None,
        on_export: Optional[Callable] = None,
        custom_items: Optional[List[ContextMenuItem]] = None
    ) -> tk.Menu:
        """Create Z-Floor context menu."""

        items = [
            ContextMenuItem(f'Refresh {floor_name}', on_refresh, accelerator='F5'),
            ContextMenuItem(f'Configure {floor_name}', on_configure),
            ContextMenuItem('separator'),
            ContextMenuItem('Export Data', submenu=[
                ContextMenuItem('Export as CSV', lambda: ZFloorContextMenu._export(widget, 'csv')),
                ContextMenuItem('Export as JSON', lambda: ZFloorContextMenu._export(widget, 'json')),
                ContextMenuItem('Export as PDF', lambda: ZFloorContextMenu._export(widget, 'pdf')),
            ]),
            ContextMenuItem('separator'),
            ContextMenuItem('View Logs', lambda: messagebox.showinfo('Logs', f'{floor_name} logs')),
            ContextMenuItem('View Metrics', lambda: messagebox.showinfo('Metrics', f'{floor_name} metrics')),
        ]

        if custom_items:
            items.append(ContextMenuItem('separator'))
            items.extend(custom_items)

        builder = ContextMenuBuilder(widget)
        builder.add_items(items)
        return builder.build()

    @staticmethod
    def _export(widget, format_type: str):
        """Export floor data."""
        filepath = filedialog.asksaveasfilename(
            title=f'Export as {format_type.upper()}',
            defaultextension=f'.{format_type}',
            filetypes=[(f'{format_type.upper()} Files', f'*.{format_type}'), ('All Files', '*.*')]
        )
        if filepath:
            messagebox.showinfo('Exported', f'Data exported to:\n{filepath}')


# Demo/Test
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Context Menus - A7 Demo')
    root.geometry('800x600')
    root.configure(bg='#1e1e1e')

    # Create demo widgets
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)

    # Text widget demo
    text_frame = tk.Frame(notebook, bg='#2d2d2d')
    notebook.add(text_frame, text='Text Menu')

    text_widget = tk.Text(text_frame, bg='#1e1e1e', fg='white', insertbackground='white')
    text_widget.pack(fill='both', expand=True, padx=10, pady=10)
    text_widget.insert('1.0', 'Right-click for text context menu\n\nTry selecting text first!')

    text_menu = TextContextMenu.create(text_widget)
    text_widget.bind('<Button-3>', lambda e: ContextMenuBuilder(text_widget).add_items([
        ContextMenuItem('Cut', lambda: text_widget.event_generate('<<Cut>>'), accelerator='Ctrl+X'),
        ContextMenuItem('Copy', lambda: text_widget.event_generate('<<Copy>>'), accelerator='Ctrl+C'),
        ContextMenuItem('Paste', lambda: text_widget.event_generate('<<Paste>>'), accelerator='Ctrl+V'),
        ContextMenuItem('separator'),
        ContextMenuItem('Select All', lambda: text_widget.tag_add('sel', '1.0', 'end'), accelerator='Ctrl+A'),
    ]).show(e))

    # Tree widget demo
    tree_frame = tk.Frame(notebook, bg='#2d2d2d')
    notebook.add(tree_frame, text='Tree Menu')

    tree_widget = ttk.Treeview(tree_frame, columns=('Value',), show='tree headings')
    tree_widget.pack(fill='both', expand=True, padx=10, pady=10)

    tree_widget.heading('#0', text='Item')
    tree_widget.heading('Value', text='Value')

    for i in range(5):
        parent = tree_widget.insert('', 'end', text=f'Item {i+1}', values=(f'Value {i+1}',))
        for j in range(3):
            tree_widget.insert(parent, 'end', text=f'Child {j+1}', values=(f'Sub-value {j+1}',))

    tree_menu = TreeContextMenu.create(
        tree_widget,
        on_add=lambda: messagebox.showinfo('Add', 'Add item clicked'),
        on_edit=lambda: messagebox.showinfo('Edit', 'Edit item clicked'),
        on_delete=lambda: messagebox.showinfo('Delete', 'Delete item clicked')
    )
    tree_widget.bind('<Button-3>', lambda e: ContextMenuBuilder(tree_widget).add_items([
        ContextMenuItem('Add Item', lambda: messagebox.showinfo('Add', 'Add item')),
        ContextMenuItem('Edit Item', lambda: messagebox.showinfo('Edit', 'Edit item')),
        ContextMenuItem('Delete Item', lambda: messagebox.showinfo('Delete', 'Delete item')),
        ContextMenuItem('separator'),
        ContextMenuItem('Expand All', lambda: TreeContextMenu._expand_all(tree_widget)),
        ContextMenuItem('Collapse All', lambda: TreeContextMenu._collapse_all(tree_widget)),
    ]).show(e))

    # Canvas widget demo
    canvas_frame = tk.Frame(notebook, bg='#2d2d2d')
    notebook.add(canvas_frame, text='Canvas Menu')

    canvas_widget = tk.Canvas(canvas_frame, bg='#ffffff', highlightthickness=0)
    canvas_widget.pack(fill='both', expand=True, padx=10, pady=10)

    # Draw sample shapes
    canvas_widget.create_rectangle(50, 50, 150, 150, fill='#0088FE', outline='#00C49F', width=3)
    canvas_widget.create_oval(200, 50, 300, 150, fill='#FFBB28', outline='#FF8042', width=3)
    canvas_widget.create_text(400, 100, text='Right-click me!', font=('Arial', 16, 'bold'), fill='#000000')

    canvas_menu = CanvasContextMenu.create(
        canvas_widget,
        on_save=lambda: messagebox.showinfo('Save', 'Save canvas'),
        on_export=lambda: messagebox.showinfo('Export', 'Export canvas')
    )
    canvas_widget.bind('<Button-3>', lambda e: ContextMenuBuilder(canvas_widget).add_items([
        ContextMenuItem('Clear Canvas', lambda: canvas_widget.delete('all')),
        ContextMenuItem('separator'),
        ContextMenuItem('Save', lambda: messagebox.showinfo('Save', 'Save canvas')),
        ContextMenuItem('Export', lambda: CanvasContextMenu._export_ps(canvas_widget)),
    ]).show(e))

    # File context menu demo (label with right-click)
    file_frame = tk.Frame(notebook, bg='#2d2d2d')
    notebook.add(file_frame, text='File Menu')

    file_label = tk.Label(
        file_frame,
        text='Right-click for file operations menu\n\n(Demo: No actual file)',
        bg='#2d2d2d',
        fg='white',
        font=('Arial', 14),
        justify='center'
    )
    file_label.pack(fill='both', expand=True)

    file_menu = FileContextMenu.create(file_label, filepath=None)
    file_label.bind('<Button-3>', lambda e: ContextMenuBuilder(file_label).add_items([
        ContextMenuItem('New File', lambda: messagebox.showinfo('New', 'Create file')),
        ContextMenuItem('New Folder', lambda: messagebox.showinfo('New', 'Create folder')),
        ContextMenuItem('separator'),
        ContextMenuItem('Import', lambda: messagebox.showinfo('Import', 'Import file')),
    ]).show(e))

    root.mainloop()
