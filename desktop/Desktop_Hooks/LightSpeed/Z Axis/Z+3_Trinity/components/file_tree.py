"""
Enhanced Treeview - A6
======================

Advanced Treeview widget with sorting, filtering, grouping, and search capabilities.

Features:
- Column sorting (ascending/descending)
- Advanced filtering (text, numeric, date)
- Row grouping by column
- Search with highlighting
- Export to CSV/JSON
- Column visibility toggle
- Custom row colors
- Context menu integration

Author: LightSpeed Platform
Date: December 16, 2025
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import json
import csv
from datetime import datetime


class FilterDialog(tk.Toplevel):
    """Dialog for configuring column filters."""

    def __init__(self, parent, column: str, callback: Callable):
        super().__init__(parent)
        self.column = column
        self.callback = callback
        self.title(f'Filter: {column}')
        self.geometry('400x300')
        self.resizable(False, False)

        self._build_ui()

    def _build_ui(self):
        """Build filter UI."""
        # Filter type selection
        type_frame = tk.Frame(self, bg='#2d2d2d')
        type_frame.pack(side='top', fill='x', padx=10, pady=10)

        tk.Label(type_frame, text='Filter Type:', bg='#2d2d2d', fg='white').pack(side='left', padx=5)

        self.filter_type = tk.StringVar(value='contains')
        types = [
            ('Contains', 'contains'),
            ('Equals', 'equals'),
            ('Starts With', 'startswith'),
            ('Ends With', 'endswith'),
            ('Greater Than', 'gt'),
            ('Less Than', 'lt'),
            ('Between', 'between')
        ]

        for label, value in types:
            tk.Radiobutton(type_frame, text=label, variable=self.filter_type, value=value,
                          bg='#2d2d2d', fg='white', selectcolor='#0088FE').pack(anchor='w', padx=20)

        # Filter value input
        value_frame = tk.Frame(self, bg='#2d2d2d')
        value_frame.pack(side='top', fill='x', padx=10, pady=10)

        tk.Label(value_frame, text='Value:', bg='#2d2d2d', fg='white').pack(side='top', anchor='w')

        self.value_entry = tk.Entry(value_frame, bg='#1e1e1e', fg='white', insertbackground='white')
        self.value_entry.pack(side='top', fill='x', pady=5)

        tk.Label(value_frame, text='Second Value (for Between):', bg='#2d2d2d', fg='white').pack(side='top', anchor='w', pady=(10, 0))

        self.value2_entry = tk.Entry(value_frame, bg='#1e1e1e', fg='white', insertbackground='white')
        self.value2_entry.pack(side='top', fill='x', pady=5)

        # Case sensitive option
        self.case_sensitive = tk.BooleanVar(value=False)
        tk.Checkbutton(value_frame, text='Case Sensitive', variable=self.case_sensitive,
                      bg='#2d2d2d', fg='white', selectcolor='#0088FE').pack(anchor='w', pady=5)

        # Buttons
        button_frame = tk.Frame(self, bg='#2d2d2d')
        button_frame.pack(side='bottom', fill='x', padx=10, pady=10)

        tk.Button(button_frame, text='Apply', command=self._apply, bg='#00C49F', fg='white').pack(side='right', padx=5)
        tk.Button(button_frame, text='Clear', command=self._clear, bg='#FF8042', fg='white').pack(side='right', padx=5)
        tk.Button(button_frame, text='Cancel', command=self.destroy, bg='#858585', fg='white').pack(side='right', padx=5)

    def _apply(self):
        """Apply filter."""
        filter_config = {
            'type': self.filter_type.get(),
            'value': self.value_entry.get(),
            'value2': self.value2_entry.get(),
            'case_sensitive': self.case_sensitive.get()
        }
        self.callback(self.column, filter_config)
        self.destroy()

    def _clear(self):
        """Clear filter."""
        self.callback(self.column, None)
        self.destroy()


class SearchPanel(tk.Frame):
    """Search panel with highlighting."""

    def __init__(self, parent, search_callback: Callable):
        super().__init__(parent, bg='#1e1e1e', height=40)
        self.search_callback = search_callback
        self._build_ui()

    def _build_ui(self):
        """Build search UI."""
        tk.Label(self, text='🔍', bg='#1e1e1e', fg='white', font=('Arial', 14)).pack(side='left', padx=5)

        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._on_search())

        self.search_entry = tk.Entry(
            self,
            textvariable=self.search_var,
            bg='#2d2d2d',
            fg='white',
            insertbackground='white',
            font=('Arial', 10)
        )
        self.search_entry.pack(side='left', fill='x', expand=True, padx=5, pady=5)

        self.case_sensitive = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text='Aa', variable=self.case_sensitive,
                      command=self._on_search, bg='#1e1e1e', fg='white',
                      selectcolor='#0088FE').pack(side='left', padx=5)

        tk.Button(self, text='✕', command=self._clear_search,
                 bg='#FF8042', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)

    def _on_search(self):
        """Trigger search."""
        query = self.search_var.get()
        case_sensitive = self.case_sensitive.get()
        self.search_callback(query, case_sensitive)

    def _clear_search(self):
        """Clear search."""
        self.search_var.set('')


class EnhancedTreeview(tk.Frame):
    """Enhanced Treeview with advanced features."""

    def __init__(self, parent, columns: List[str], show_search: bool = True):
        super().__init__(parent, bg='#2d2d2d')
        self.columns = columns
        self.show_search = show_search

        # Data storage
        self.all_items: List[Dict[str, Any]] = []  # All data
        self.filtered_items: List[Dict[str, Any]] = []  # Filtered data
        self.item_id_map: Dict[str, Dict[str, Any]] = {}  # Map tree item IDs to data

        # State
        self.sort_column: Optional[str] = None
        self.sort_reverse: bool = False
        self.filters: Dict[str, Dict] = {}  # Column -> filter config
        self.hidden_columns: set = set()
        self.row_colors: Dict[str, str] = {}  # Item ID -> color

        self._build_ui()

    def _build_ui(self):
        """Build treeview UI."""
        # Search panel
        if self.show_search:
            self.search_panel = SearchPanel(self, self._on_search)
            self.search_panel.pack(side='top', fill='x')

        # Toolbar
        toolbar = tk.Frame(self, bg='#1e1e1e', height=40)
        toolbar.pack(side='top', fill='x')

        tk.Button(toolbar, text='📋 Export CSV', command=self._export_csv,
                 bg='#0088FE', fg='white').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='📋 Export JSON', command=self._export_json,
                 bg='#0088FE', fg='white').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='👁️ Columns', command=self._toggle_columns_dialog,
                 bg='#00C49F', fg='white').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='📊 Group By', command=self._group_by_dialog,
                 bg='#FFBB28', fg='black').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='🔄 Clear Filters', command=self._clear_all_filters,
                 bg='#FF8042', fg='white').pack(side='left', padx=5, pady=5)

        self.status_label = tk.Label(toolbar, text='Rows: 0', bg='#1e1e1e', fg='#858585')
        self.status_label.pack(side='right', padx=10)

        # Treeview frame
        tree_frame = tk.Frame(self, bg='#2d2d2d')
        tree_frame.pack(side='top', fill='both', expand=True)

        # Treeview
        self.tree = ttk.Treeview(tree_frame, columns=self.columns, show='headings', selectmode='extended')

        # Configure columns
        for col in self.columns:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_by_column(c))
            self.tree.column(col, width=150, anchor='w')

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Context menu
        self.context_menu = tk.Menu(self.tree, tearoff=0, bg='#2d2d2d', fg='white')
        self.context_menu.add_command(label='Filter Column', command=self._filter_selected_column)
        self.context_menu.add_command(label='Sort Ascending', command=self._sort_selected_asc)
        self.context_menu.add_command(label='Sort Descending', command=self._sort_selected_desc)
        self.context_menu.add_separator()
        self.context_menu.add_command(label='Set Row Color', command=self._set_row_color)
        self.context_menu.add_command(label='Clear Row Color', command=self._clear_row_color)
        self.context_menu.add_separator()
        self.context_menu.add_command(label='Copy Value', command=self._copy_value)
        self.context_menu.add_command(label='Delete Row', command=self._delete_row)

        self.tree.bind('<Button-3>', self._show_context_menu)

        # Configure tags for row colors
        self.tree.tag_configure('search_highlight', background='#FFBB28')

    def load_data(self, data: List[Dict[str, Any]]):
        """Load data into treeview."""
        self.all_items = data
        self._apply_filters()

    def _apply_filters(self):
        """Apply all filters and refresh treeview."""
        # Start with all items
        self.filtered_items = self.all_items.copy()

        # Apply each filter
        for column, filter_config in self.filters.items():
            if filter_config:
                self.filtered_items = [
                    item for item in self.filtered_items
                    if self._item_matches_filter(item, column, filter_config)
                ]

        # Refresh display
        self._refresh_tree()

    def _item_matches_filter(self, item: Dict[str, Any], column: str, filter_config: Dict) -> bool:
        """Check if item matches filter."""
        value = str(item.get(column, ''))
        filter_type = filter_config['type']
        filter_value = filter_config['value']
        filter_value2 = filter_config.get('value2', '')
        case_sensitive = filter_config.get('case_sensitive', False)

        if not case_sensitive:
            value = value.lower()
            filter_value = filter_value.lower()
            filter_value2 = filter_value2.lower()

        if filter_type == 'contains':
            return filter_value in value
        elif filter_type == 'equals':
            return value == filter_value
        elif filter_type == 'startswith':
            return value.startswith(filter_value)
        elif filter_type == 'endswith':
            return value.endswith(filter_value)
        elif filter_type == 'gt':
            try:
                return float(value) > float(filter_value)
            except ValueError:
                return value > filter_value
        elif filter_type == 'lt':
            try:
                return float(value) < float(filter_value)
            except ValueError:
                return value < filter_value
        elif filter_type == 'between':
            try:
                val_num = float(value)
                return float(filter_value) <= val_num <= float(filter_value2)
            except ValueError:
                return filter_value <= value <= filter_value2

        return True

    def _refresh_tree(self):
        """Refresh treeview display."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.item_id_map.clear()

        # Apply sorting if active
        items_to_display = self.filtered_items.copy()
        if self.sort_column:
            items_to_display.sort(
                key=lambda x: x.get(self.sort_column, ''),
                reverse=self.sort_reverse
            )

        # Insert items
        for item_data in items_to_display:
            values = [item_data.get(col, '') for col in self.columns if col not in self.hidden_columns]
            display_columns = [col for col in self.columns if col not in self.hidden_columns]

            # Configure tree columns for hidden columns
            self.tree.configure(columns=display_columns)
            for col in display_columns:
                self.tree.heading(col, text=col, command=lambda c=col: self._sort_by_column(c))

            item_id = self.tree.insert('', 'end', values=values)
            self.item_id_map[item_id] = item_data

            # Apply row color if set
            if item_id in self.row_colors:
                self.tree.item(item_id, tags=(f'color_{item_id}',))
                self.tree.tag_configure(f'color_{item_id}', background=self.row_colors[item_id])

        # Update status
        self.status_label.config(text=f'Rows: {len(items_to_display)} / {len(self.all_items)}')

    def _sort_by_column(self, column: str):
        """Sort by column."""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        # Update heading to show sort direction
        for col in self.columns:
            heading_text = col
            if col == self.sort_column:
                heading_text += ' ▼' if self.sort_reverse else ' ▲'
            self.tree.heading(col, text=heading_text, command=lambda c=col: self._sort_by_column(c))

        self._refresh_tree()

    def _on_search(self, query: str, case_sensitive: bool):
        """Handle search."""
        # Remove existing highlights
        for item in self.tree.get_children():
            self.tree.item(item, tags=())

        if not query:
            return

        # Highlight matching rows
        search_query = query if case_sensitive else query.lower()
        for item_id in self.tree.get_children():
            item_data = self.item_id_map[item_id]
            for value in item_data.values():
                value_str = str(value) if case_sensitive else str(value).lower()
                if search_query in value_str:
                    self.tree.item(item_id, tags=('search_highlight',))
                    break

    def _filter_selected_column(self):
        """Open filter dialog for selected column."""
        # Get selected column from click
        region = self.tree.identify('region', self.tree.winfo_pointerx() - self.tree.winfo_rootx(),
                                    self.tree.winfo_pointery() - self.tree.winfo_rooty())
        if region == 'heading':
            column = self.tree.identify_column(self.tree.winfo_pointerx() - self.tree.winfo_rootx())
            col_index = int(column.replace('#', '')) - 1
            if 0 <= col_index < len(self.columns):
                col_name = self.columns[col_index]
                FilterDialog(self, col_name, self._set_filter)

    def _set_filter(self, column: str, filter_config: Optional[Dict]):
        """Set or clear filter for column."""
        if filter_config:
            self.filters[column] = filter_config
        else:
            self.filters.pop(column, None)

        self._apply_filters()

    def _clear_all_filters(self):
        """Clear all filters."""
        self.filters.clear()
        self._apply_filters()

    def _sort_selected_asc(self):
        """Sort selected column ascending."""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            col_index = 0  # Default to first column
            self.sort_column = self.columns[col_index]
            self.sort_reverse = False
            self._refresh_tree()

    def _sort_selected_desc(self):
        """Sort selected column descending."""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            col_index = 0
            self.sort_column = self.columns[col_index]
            self.sort_reverse = True
            self._refresh_tree()

    def _set_row_color(self):
        """Set color for selected row."""
        from tkinter import colorchooser
        selection = self.tree.selection()
        if selection:
            color = colorchooser.askcolor(title='Select Row Color')
            if color[1]:
                for item_id in selection:
                    self.row_colors[item_id] = color[1]
                self._refresh_tree()

    def _clear_row_color(self):
        """Clear color from selected row."""
        selection = self.tree.selection()
        if selection:
            for item_id in selection:
                self.row_colors.pop(item_id, None)
            self._refresh_tree()

    def _copy_value(self):
        """Copy selected value to clipboard."""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            values = self.tree.item(item_id, 'values')
            if values:
                self.clipboard_clear()
                self.clipboard_append(str(values[0]))

    def _delete_row(self):
        """Delete selected rows."""
        selection = self.tree.selection()
        if selection:
            response = messagebox.askyesno('Delete Rows',
                                          f'Delete {len(selection)} row(s)?')
            if response:
                for item_id in selection:
                    item_data = self.item_id_map[item_id]
                    if item_data in self.all_items:
                        self.all_items.remove(item_data)
                self._apply_filters()

    def _toggle_columns_dialog(self):
        """Show dialog to toggle column visibility."""
        dialog = tk.Toplevel(self)
        dialog.title('Column Visibility')
        dialog.geometry('300x400')
        dialog.configure(bg='#2d2d2d')

        tk.Label(dialog, text='Show/Hide Columns:', bg='#2d2d2d', fg='white',
                font=('Arial', 12, 'bold')).pack(pady=10)

        column_vars = {}
        for col in self.columns:
            var = tk.BooleanVar(value=col not in self.hidden_columns)
            column_vars[col] = var
            tk.Checkbutton(dialog, text=col, variable=var, bg='#2d2d2d', fg='white',
                          selectcolor='#0088FE').pack(anchor='w', padx=20, pady=2)

        def apply_visibility():
            self.hidden_columns.clear()
            for col, var in column_vars.items():
                if not var.get():
                    self.hidden_columns.add(col)
            self._refresh_tree()
            dialog.destroy()

        tk.Button(dialog, text='Apply', command=apply_visibility,
                 bg='#00C49F', fg='white').pack(pady=10)

    def _group_by_dialog(self):
        """Show dialog to group by column."""
        dialog = tk.Toplevel(self)
        dialog.title('Group By Column')
        dialog.geometry('300x200')
        dialog.configure(bg='#2d2d2d')

        tk.Label(dialog, text='Select Column:', bg='#2d2d2d', fg='white',
                font=('Arial', 12, 'bold')).pack(pady=10)

        column_var = tk.StringVar(value=self.columns[0] if self.columns else '')
        for col in self.columns:
            tk.Radiobutton(dialog, text=col, variable=column_var, value=col,
                          bg='#2d2d2d', fg='white', selectcolor='#0088FE').pack(anchor='w', padx=20)

        def apply_grouping():
            column = column_var.get()
            self._group_by_column(column)
            dialog.destroy()

        tk.Button(dialog, text='Apply', command=apply_grouping,
                 bg='#00C49F', fg='white').pack(pady=10)

    def _group_by_column(self, column: str):
        """Group items by column value."""
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Group items
        groups: Dict[str, List[Dict]] = {}
        for item in self.filtered_items:
            group_key = str(item.get(column, 'Unknown'))
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(item)

        # Insert grouped items
        for group_key in sorted(groups.keys()):
            # Insert group header
            group_id = self.tree.insert('', 'end', text=f'{column}: {group_key}',
                                       values=[f'▶ {group_key}'] + [''] * (len(self.columns) - 1))
            self.tree.item(group_id, tags=('group_header',))
            self.tree.tag_configure('group_header', background='#404040', foreground='#00C49F', font=('Arial', 10, 'bold'))

            # Insert group items
            for item_data in groups[group_key]:
                values = [item_data.get(col, '') for col in self.columns]
                item_id = self.tree.insert(group_id, 'end', values=values)
                self.item_id_map[item_id] = item_data

    def _export_csv(self):
        """Export data to CSV."""
        filepath = filedialog.asksaveasfilename(
            title='Export to CSV',
            defaultextension='.csv',
            filetypes=[('CSV Files', '*.csv'), ('All Files', '*.*')]
        )

        if filepath:
            try:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.columns)
                    writer.writeheader()
                    writer.writerows(self.filtered_items)
                messagebox.showinfo('Exported', f'Data exported to:\n{filepath}')
            except Exception as e:
                messagebox.showerror('Error', f'Failed to export:\n{str(e)}')

    def _export_json(self):
        """Export data to JSON."""
        filepath = filedialog.asksaveasfilename(
            title='Export to JSON',
            defaultextension='.json',
            filetypes=[('JSON Files', '*.json'), ('All Files', '*.*')]
        )

        if filepath:
            try:
                Path(filepath).write_text(json.dumps(self.filtered_items, indent=2), encoding='utf-8')
                messagebox.showinfo('Exported', f'Data exported to:\n{filepath}')
            except Exception as e:
                messagebox.showerror('Error', f'Failed to export:\n{str(e)}')

    def _show_context_menu(self, event):
        """Show context menu."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()


# Demo/Test
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Enhanced Treeview - A6 Demo')
    root.geometry('1000x600')

    # Sample data
    sample_data = [
        {'Name': 'Mission Alpha', 'Status': 'Active', 'Priority': 'High', 'Progress': '75%', 'Owner': 'Alice'},
        {'Name': 'Mission Beta', 'Status': 'Completed', 'Priority': 'Medium', 'Progress': '100%', 'Owner': 'Bob'},
        {'Name': 'Mission Gamma', 'Status': 'Active', 'Priority': 'High', 'Progress': '45%', 'Owner': 'Charlie'},
        {'Name': 'Mission Delta', 'Status': 'Pending', 'Priority': 'Low', 'Progress': '0%', 'Owner': 'Alice'},
        {'Name': 'Mission Epsilon', 'Status': 'Active', 'Priority': 'High', 'Progress': '90%', 'Owner': 'Diana'},
        {'Name': 'Mission Zeta', 'Status': 'Completed', 'Priority': 'Medium', 'Progress': '100%', 'Owner': 'Eve'},
        {'Name': 'Mission Eta', 'Status': 'Active', 'Priority': 'Low', 'Progress': '30%', 'Owner': 'Frank'},
        {'Name': 'Mission Theta', 'Status': 'Pending', 'Priority': 'High', 'Progress': '5%', 'Owner': 'Bob'},
        {'Name': 'Mission Iota', 'Status': 'Active', 'Priority': 'Medium', 'Progress': '60%', 'Owner': 'Alice'},
        {'Name': 'Mission Kappa', 'Status': 'Completed', 'Priority': 'Low', 'Progress': '100%', 'Owner': 'Grace'},
    ]

    columns = ['Name', 'Status', 'Priority', 'Progress', 'Owner']

    tree_widget = EnhancedTreeview(root, columns=columns, show_search=True)
    tree_widget.pack(fill='both', expand=True)

    tree_widget.load_data(sample_data)

    root.mainloop()
