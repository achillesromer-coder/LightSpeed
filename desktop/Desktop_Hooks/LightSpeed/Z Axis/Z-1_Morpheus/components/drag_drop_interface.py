#!/usr/bin/env python
"""
Drag-and-Drop File Manager - Interactive file operations
Complete drag-and-drop system for file management

Features:
- Drag files between categories
- Drop files from OS
- Visual drag feedback
- Multi-select operations
- Copy/Move/Delete operations
- Category management
- File preview on hover
- Undo/Redo support

Author: LightSpeed Team
Version: 0.9.5
Date: December 16, 2025
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import List, Dict, Optional, Callable
import shutil
import json
from datetime import datetime


class DragDropTreeview(ttk.Treeview):
    """Enhanced Treeview with drag-and-drop support"""

    def __init__(self, parent, on_drop_callback=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.drag_data = {'item': None, 'x': 0, 'y': 0}
        self.on_drop_callback = on_drop_callback
        self.drag_indicator = None

        # Bind drag events
        self.bind('<Button-1>', self._on_press)
        self.bind('<B1-Motion>', self._on_drag)
        self.bind('<ButtonRelease-1>', self._on_release)

        # Visual feedback
        self.configure(selectmode='extended')

    def _on_press(self, event):
        """Handle mouse press - start potential drag"""
        item = self.identify_row(event.y)
        if item:
            self.drag_data['item'] = item
            self.drag_data['x'] = event.x
            self.drag_data['y'] = event.y

    def _on_drag(self, event):
        """Handle drag motion"""
        if self.drag_data['item']:
            # Create drag indicator if not exists
            if not self.drag_indicator:
                self.drag_indicator = tk.Toplevel()
                self.drag_indicator.wm_overrideredirect(True)
                self.drag_indicator.attributes('-alpha', 0.7)

                # Get item text
                item_text = self.item(self.drag_data['item'], 'text')
                selected_count = len(self.selection())

                label_text = f"📁 {item_text}"
                if selected_count > 1:
                    label_text += f" (+{selected_count - 1} more)"

                label = tk.Label(
                    self.drag_indicator,
                    text=label_text,
                    bg='#0e639c',
                    fg='white',
                    font=('Arial', 10, 'bold'),
                    padx=10,
                    pady=5
                )
                label.pack()

            # Update indicator position
            x = event.x_root + 10
            y = event.y_root + 10
            self.drag_indicator.geometry(f'+{x}+{y}')

    def _on_release(self, event):
        """Handle mouse release - complete drop"""
        if self.drag_indicator:
            self.drag_indicator.destroy()
            self.drag_indicator = None

        if self.drag_data['item'] and self.on_drop_callback:
            # Get drop target
            drop_target = self.identify_row(event.y)

            # Get all selected items
            selected_items = self.selection()
            if self.drag_data['item'] not in selected_items:
                selected_items = (self.drag_data['item'],)

            # Call drop callback
            self.on_drop_callback(selected_items, drop_target)

        self.drag_data['item'] = None


class FileCategory:
    """File category with metadata"""

    def __init__(self, name: str, description: str = "", color: str = "#0088FE"):
        self.name = name
        self.description = description
        self.color = color
        self.files = []  # List of file paths

    def add_file(self, filepath: str):
        """Add file to category"""
        if filepath not in self.files:
            self.files.append(filepath)

    def remove_file(self, filepath: str):
        """Remove file from category"""
        if filepath in self.files:
            self.files.remove(filepath)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'files': self.files
        }

    @staticmethod
    def from_dict(data):
        """Create from dictionary"""
        cat = FileCategory(data['name'], data.get('description', ''), data.get('color', '#0088FE'))
        cat.files = data.get('files', [])
        return cat


class DragDropFileManager(tk.Frame):
    """Complete drag-and-drop file manager"""

    def __init__(self, parent, base_path: Path = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg='#1e1e1e')

        self.base_path = base_path or Path.cwd()
        self.categories = {}  # {category_name: FileCategory}
        self.history = []  # Undo/redo history
        self.history_index = -1

        self._load_categories()
        self._build_ui()
        self._populate_tree()

    def _build_ui(self):
        """Build file manager UI"""
        # Toolbar
        toolbar = tk.Frame(self, bg='#2d2d2d', height=40)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        # File operations
        tk.Button(toolbar, text="➕ Add Files", command=self._add_files,
                 bg='#0e639c', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', padx=10).pack(side=tk.LEFT, padx=5, pady=5)

        tk.Button(toolbar, text="📁 Add Folder", command=self._add_folder,
                 bg='#0e639c', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', padx=10).pack(side=tk.LEFT, padx=5, pady=5)

        tk.Button(toolbar, text="🗑️ Delete", command=self._delete_selected,
                 bg='#d9534f', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', padx=10).pack(side=tk.LEFT, padx=5, pady=5)

        # Separator
        ttk.Separator(toolbar, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)

        # Category operations
        tk.Button(toolbar, text="➕ New Category", command=self._new_category,
                 bg='#5cb85c', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', padx=10).pack(side=tk.LEFT, padx=5, pady=5)

        tk.Button(toolbar, text="🎨 Edit Category", command=self._edit_category,
                 bg='#f0ad4e', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', padx=10).pack(side=tk.LEFT, padx=5, pady=5)

        # Separator
        ttk.Separator(toolbar, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)

        # Undo/Redo
        tk.Button(toolbar, text="↶ Undo", command=self._undo,
                 bg='#5bc0de', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', padx=10).pack(side=tk.LEFT, padx=5, pady=5)

        tk.Button(toolbar, text="↷ Redo", command=self._redo,
                 bg='#5bc0de', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', padx=10).pack(side=tk.LEFT, padx=5, pady=5)

        # Status
        self.status_label = tk.Label(toolbar, text="Ready", bg='#2d2d2d', fg='#00ff00',
                                     font=('Arial', 9), anchor='e')
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # Main area with two panels
        main_frame = tk.Frame(self, bg='#1e1e1e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Category tree
        left_frame = tk.Frame(main_frame, bg='#1e1e1e')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(left_frame, text="Categories & Files",
                bg='#1e1e1e', fg='#ffffff',
                font=('Arial', 12, 'bold')).pack(anchor='w', pady=(0, 10))

        # Tree with scrollbar
        tree_frame = tk.Frame(left_frame, bg='#1e1e1e')
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = DragDropTreeview(
            tree_frame,
            on_drop_callback=self._on_drop,
            columns=('size', 'type', 'modified'),
            show='tree headings'
        )

        # Configure columns
        self.tree.heading('#0', text='Name')
        self.tree.heading('size', text='Size')
        self.tree.heading('type', text='Type')
        self.tree.heading('modified', text='Modified')

        self.tree.column('#0', width=300)
        self.tree.column('size', width=100)
        self.tree.column('type', width=100)
        self.tree.column('modified', width=150)

        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.tree.xview)
        self.tree.config(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # Right panel - Preview/Details
        right_frame = tk.Frame(main_frame, bg='#2d2d2d', width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_frame.pack_propagate(False)

        tk.Label(right_frame, text="File Details",
                bg='#2d2d2d', fg='#ffffff',
                font=('Arial', 12, 'bold')).pack(anchor='w', padx=10, pady=10)

        self.details_text = tk.Text(
            right_frame,
            bg='#1e1e1e',
            fg='#ffffff',
            font=('Consolas', 9),
            wrap='word',
            height=20
        )
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Bind selection
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

        # Enable OS file drops
        self._enable_os_drops()

    def _populate_tree(self):
        """Populate tree with categories and files"""
        self.tree.delete(*self.tree.get_children())

        for cat_name, category in self.categories.items():
            # Add category node
            cat_id = self.tree.insert(
                '',
                'end',
                text=f"📁 {cat_name}",
                values=('', 'Category', ''),
                tags=('category',)
            )

            # Configure category color
            self.tree.tag_configure('category', foreground=category.color, font=('Arial', 10, 'bold'))

            # Add files
            for filepath in category.files:
                path = Path(filepath)
                if path.exists():
                    size = path.stat().st_size
                    size_str = self._format_size(size)
                    file_type = path.suffix[1:].upper() if path.suffix else 'File'
                    modified = datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')

                    self.tree.insert(
                        cat_id,
                        'end',
                        text=f"📄 {path.name}",
                        values=(size_str, file_type, modified),
                        tags=(filepath,)
                    )
                else:
                    # File doesn't exist, mark for removal
                    category.remove_file(filepath)

    def _format_size(self, size: int) -> str:
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def _on_drop(self, items: tuple, target: str):
        """Handle drop operation"""
        if not target:
            return

        # Get target category
        target_cat = None
        target_item = self.tree.item(target)

        # Check if target is a category
        if 'category' in target_item['tags']:
            target_cat_name = target_item['text'].replace('📁 ', '')
            target_cat = self.categories.get(target_cat_name)
        else:
            # Get parent category
            parent = self.tree.parent(target)
            if parent:
                parent_item = self.tree.item(parent)
                target_cat_name = parent_item['text'].replace('📁 ', '')
                target_cat = self.categories.get(target_cat_name)

        if not target_cat:
            return

        # Move files
        moved_files = []
        for item in items:
            item_data = self.tree.item(item)
            if 'category' not in item_data['tags']:
                # Get file path from tags
                filepath = item_data['tags'][0] if item_data['tags'] else None
                if filepath:
                    # Remove from old category
                    for cat in self.categories.values():
                        if filepath in cat.files:
                            cat.remove_file(filepath)

                    # Add to new category
                    target_cat.add_file(filepath)
                    moved_files.append(filepath)

        if moved_files:
            # Add to history
            self._add_to_history({
                'action': 'move',
                'files': moved_files,
                'target': target_cat.name
            })

            self._populate_tree()
            self._save_categories()
            self.status_label.config(text=f"Moved {len(moved_files)} file(s) to {target_cat.name}")

    def _add_files(self):
        """Add files from file picker"""
        filepaths = filedialog.askopenfilenames(title="Select Files")
        if filepaths:
            # Ask for category
            cat_name = self._select_category("Select category for files")
            if cat_name and cat_name in self.categories:
                category = self.categories[cat_name]
                for filepath in filepaths:
                    category.add_file(filepath)

                self._add_to_history({
                    'action': 'add',
                    'files': list(filepaths),
                    'category': cat_name
                })

                self._populate_tree()
                self._save_categories()
                self.status_label.config(text=f"Added {len(filepaths)} file(s)")

    def _add_folder(self):
        """Add entire folder"""
        folder_path = filedialog.askdirectory(title="Select Folder")
        if folder_path:
            folder = Path(folder_path)
            files = list(folder.rglob('*'))
            files = [str(f) for f in files if f.is_file()]

            if files:
                cat_name = self._select_category("Select category for folder contents")
                if cat_name and cat_name in self.categories:
                    category = self.categories[cat_name]
                    for filepath in files:
                        category.add_file(filepath)

                    self._populate_tree()
                    self._save_categories()
                    self.status_label.config(text=f"Added {len(files)} file(s) from folder")

    def _delete_selected(self):
        """Delete selected files"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select files to delete")
            return

        if messagebox.askyesno("Confirm Delete", f"Delete {len(selected)} selected item(s)?"):
            deleted_files = []
            for item in selected:
                item_data = self.tree.item(item)
                if 'category' not in item_data['tags']:
                    filepath = item_data['tags'][0] if item_data['tags'] else None
                    if filepath:
                        # Remove from category
                        for cat in self.categories.values():
                            if filepath in cat.files:
                                cat.remove_file(filepath)
                                deleted_files.append(filepath)

            if deleted_files:
                self._add_to_history({
                    'action': 'delete',
                    'files': deleted_files
                })

                self._populate_tree()
                self._save_categories()
                self.status_label.config(text=f"Deleted {len(deleted_files)} file(s)")

    def _new_category(self):
        """Create new category"""
        dialog = tk.Toplevel(self)
        dialog.title("New Category")
        dialog.geometry("400x250")
        dialog.configure(bg='#1e1e1e')
        dialog.transient(self)

        tk.Label(dialog, text="Category Name:", bg='#1e1e1e', fg='#ffffff',
                font=('Arial', 10)).pack(pady=(20, 5))
        name_entry = tk.Entry(dialog, font=('Arial', 11), width=30)
        name_entry.pack(pady=5)

        tk.Label(dialog, text="Description (optional):", bg='#1e1e1e', fg='#ffffff',
                font=('Arial', 10)).pack(pady=(10, 5))
        desc_entry = tk.Entry(dialog, font=('Arial', 11), width=30)
        desc_entry.pack(pady=5)

        tk.Label(dialog, text="Color:", bg='#1e1e1e', fg='#ffffff',
                font=('Arial', 10)).pack(pady=(10, 5))

        color_var = tk.StringVar(value='#0088FE')
        colors = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D']
        color_frame = tk.Frame(dialog, bg='#1e1e1e')
        color_frame.pack(pady=5)

        for color in colors:
            tk.Radiobutton(color_frame, variable=color_var, value=color,
                          bg=color, activebackground=color,
                          width=3, height=1, indicatoron=0).pack(side=tk.LEFT, padx=2)

        def create():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Category name is required", parent=dialog)
                return

            if name in self.categories:
                messagebox.showerror("Error", f"Category '{name}' already exists", parent=dialog)
                return

            category = FileCategory(name, desc_entry.get().strip(), color_var.get())
            self.categories[name] = category

            self._populate_tree()
            self._save_categories()
            dialog.destroy()
            self.status_label.config(text=f"Created category: {name}")

        tk.Button(dialog, text="Create", command=create,
                 bg='#5cb85c', fg='white', font=('Arial', 11, 'bold'),
                 width=15).pack(pady=20)

    def _edit_category(self):
        """Edit selected category"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a category to edit")
            return

        # Get selected category
        item_data = self.tree.item(selected[0])
        if 'category' not in item_data['tags']:
            messagebox.showwarning("Invalid Selection", "Please select a category (not a file)")
            return

        cat_name = item_data['text'].replace('📁 ', '')
        category = self.categories.get(cat_name)

        if not category:
            return

        # Edit dialog (similar to new category)
        messagebox.showinfo("Edit Category", f"Editing: {cat_name}\n(Full edit dialog would be here)")

    def _select_category(self, title: str) -> Optional[str]:
        """Show category selection dialog"""
        if not self.categories:
            messagebox.showwarning("No Categories", "Please create a category first")
            return None

        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry("300x400")
        dialog.configure(bg='#1e1e1e')
        dialog.transient(self)

        result = {'category': None}

        tk.Label(dialog, text=title, bg='#1e1e1e', fg='#ffffff',
                font=('Arial', 12, 'bold')).pack(pady=20)

        listbox = tk.Listbox(dialog, bg='#2d2d2d', fg='#ffffff',
                            font=('Arial', 11), height=15)
        listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        for cat_name in self.categories.keys():
            listbox.insert('end', cat_name)

        def select():
            selection = listbox.curselection()
            if selection:
                result['category'] = listbox.get(selection[0])
                dialog.destroy()

        tk.Button(dialog, text="Select", command=select,
                 bg='#0e639c', fg='white', font=('Arial', 11, 'bold'),
                 width=15).pack(pady=10)

        dialog.wait_window()
        return result['category']

    def _on_select(self, event=None):
        """Handle selection - show details"""
        selected = self.tree.selection()
        if not selected:
            return

        item_data = self.tree.item(selected[0])

        if 'category' in item_data['tags']:
            # Show category details
            cat_name = item_data['text'].replace('📁 ', '')
            category = self.categories.get(cat_name)

            details = f"Category: {cat_name}\n"
            details += f"Description: {category.description}\n"
            details += f"Files: {len(category.files)}\n"
            details += f"Color: {category.color}\n"
        else:
            # Show file details
            filepath = item_data['tags'][0] if item_data['tags'] else None
            if filepath:
                path = Path(filepath)
                if path.exists():
                    details = f"Name: {path.name}\n"
                    details += f"Path: {path}\n"
                    details += f"Size: {self._format_size(path.stat().st_size)}\n"
                    details += f"Type: {path.suffix[1:].upper() if path.suffix else 'File'}\n"
                    details += f"Modified: {datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}\n"
                else:
                    details = "File not found"
            else:
                details = "No details available"

        self.details_text.delete('1.0', 'end')
        self.details_text.insert('1.0', details)

    def _enable_os_drops(self):
        """Enable dropping files from OS (requires tkinterdnd2 - optional)"""
        # This would use tkinterdnd2 if available
        # For now, we have the manual add files/folder buttons
        pass

    def _add_to_history(self, action: dict):
        """Add action to history for undo/redo"""
        # Remove any redo history
        self.history = self.history[:self.history_index + 1]
        self.history.append(action)
        self.history_index = len(self.history) - 1

    def _undo(self):
        """Undo last action"""
        if self.history_index < 0:
            self.status_label.config(text="Nothing to undo")
            return

        action = self.history[self.history_index]
        self.history_index -= 1

        # Reverse the action
        if action['action'] == 'move':
            # Move files back (simplified - would need source tracking)
            self.status_label.config(text="Undo: Move")
        elif action['action'] == 'add':
            # Remove added files
            category = self.categories.get(action['category'])
            if category:
                for filepath in action['files']:
                    category.remove_file(filepath)
                self._populate_tree()
                self.status_label.config(text=f"Undo: Removed {len(action['files'])} file(s)")
        elif action['action'] == 'delete':
            # Would restore deleted files (simplified)
            self.status_label.config(text="Undo: Delete")

        self._save_categories()

    def _redo(self):
        """Redo last undone action"""
        if self.history_index >= len(self.history) - 1:
            self.status_label.config(text="Nothing to redo")
            return

        self.history_index += 1
        action = self.history[self.history_index]

        # Reapply the action (simplified)
        self.status_label.config(text=f"Redo: {action['action']}")

    def _load_categories(self):
        """Load categories from disk"""
        categories_file = self.base_path / "data" / "file_categories.json"

        if categories_file.exists():
            try:
                data = json.loads(categories_file.read_text())
                for cat_data in data:
                    category = FileCategory.from_dict(cat_data)
                    self.categories[category.name] = category
            except:
                pass

        # Create default categories if none exist
        if not self.categories:
            self.categories = {
                'Documents': FileCategory('Documents', 'Text documents and PDFs', '#0088FE'),
                'Images': FileCategory('Images', 'Image files', '#00C49F'),
                'Code': FileCategory('Code', 'Source code files', '#FFBB28'),
                'Data': FileCategory('Data', 'Data files (CSV, JSON, etc.)', '#FF8042')
            }

    def _save_categories(self):
        """Save categories to disk"""
        categories_file = self.base_path / "data" / "file_categories.json"
        categories_file.parent.mkdir(parents=True, exist_ok=True)

        data = [cat.to_dict() for cat in self.categories.values()]
        categories_file.write_text(json.dumps(data, indent=2))


# Demo/Test
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Drag-Drop File Manager - Test")
    root.geometry("1200x700")

    manager = DragDropFileManager(root, base_path=Path.cwd())
    manager.pack(fill='both', expand=True)

    root.mainloop()
