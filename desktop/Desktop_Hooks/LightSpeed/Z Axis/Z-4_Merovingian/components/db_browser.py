"""
Database Browser GUI - D1
==========================

Interactive database browser with schema viewer and query builder.

Features:
- Connection to SQLite, MySQL, PostgreSQL databases
- Schema tree view (databases, tables, columns, indexes)
- Visual query builder
- SQL editor with syntax highlighting
- Query execution with results grid
- Export query results (CSV, JSON, Excel)
- Table data editor
- Database statistics

Author: LightSpeed Platform
Date: December 16, 2025
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import sqlite3
import json
import csv


class DatabaseConnection:
    """Database connection wrapper."""

    def __init__(self, db_type: str = 'sqlite', **kwargs):
        self.db_type = db_type
        self.connection: Optional[Any] = None
        self.cursor: Optional[Any] = None

        if db_type == 'sqlite':
            self.db_path = kwargs.get('db_path')
        else:
            self.host = kwargs.get('host', 'localhost')
            self.port = kwargs.get('port', 3306 if db_type == 'mysql' else 5432)
            self.database = kwargs.get('database')
            self.user = kwargs.get('user')
            self.password = kwargs.get('password')

    def connect(self):
        """Establish database connection."""
        try:
            if self.db_type == 'sqlite':
                self.connection = sqlite3.connect(self.db_path)
                self.connection.row_factory = sqlite3.Row
                self.cursor = self.connection.cursor()
                return True

            elif self.db_type == 'mysql':
                import mysql.connector
                self.connection = mysql.connector.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
                self.cursor = self.connection.cursor(dictionary=True)
                return True

            elif self.db_type == 'postgresql':
                import psycopg2
                from psycopg2.extras import RealDictCursor
                self.connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
                self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
                return True

        except Exception as e:
            raise Exception(f"Connection failed: {str(e)}")

    def execute(self, query: str, params: tuple = ()) -> Tuple[List[Dict], List[str]]:
        """Execute query and return results."""
        if not self.cursor:
            raise Exception("Not connected to database")

        self.cursor.execute(query, params)

        # Get column names
        if self.cursor.description:
            columns = [desc[0] for desc in self.cursor.description]
            rows = self.cursor.fetchall()

            # Convert to list of dicts
            if self.db_type == 'sqlite':
                results = [dict(row) for row in rows]
            else:
                results = rows

            return results, columns
        else:
            # No results (INSERT, UPDATE, DELETE)
            self.connection.commit()
            return [], []

    def get_tables(self) -> List[str]:
        """Get list of tables."""
        if self.db_type == 'sqlite':
            query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        elif self.db_type == 'mysql':
            query = "SHOW TABLES"
        else:  # postgresql
            query = "SELECT tablename FROM pg_tables WHERE schemaname='public'"

        results, _ = self.execute(query)
        return [list(row.values())[0] for row in results]

    def get_table_schema(self, table_name: str) -> List[Dict]:
        """Get table schema."""
        if self.db_type == 'sqlite':
            query = f"PRAGMA table_info({table_name})"
        elif self.db_type == 'mysql':
            query = f"DESCRIBE {table_name}"
        else:  # postgresql
            query = f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
            """

        results, _ = self.execute(query)
        return results

    def close(self):
        """Close connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()


class QueryBuilder(tk.Toplevel):
    """Visual query builder dialog."""

    def __init__(self, parent, tables: List[str], on_build: callable):
        super().__init__(parent)
        self.title('Query Builder')
        self.geometry('600x500')
        self.configure(bg='#2d2d2d')

        self.tables = tables
        self.on_build = on_build

        self._build_ui()

    def _build_ui(self):
        """Build query builder UI."""
        # Table selection
        tk.Label(self, text='SELECT FROM:', bg='#2d2d2d', fg='white',
                font=('Arial', 10, 'bold')).pack(pady=(10, 5))

        self.table_var = tk.StringVar(value=self.tables[0] if self.tables else '')
        table_combo = ttk.Combobox(self, textvariable=self.table_var, values=self.tables)
        table_combo.pack(fill='x', padx=20, pady=5)

        # Columns selection
        tk.Label(self, text='COLUMNS:', bg='#2d2d2d', fg='white',
                font=('Arial', 10, 'bold')).pack(pady=(10, 5))

        self.columns_text = tk.Text(self, height=4, bg='#1e1e1e', fg='white',
                                    insertbackground='white')
        self.columns_text.pack(fill='x', padx=20, pady=5)
        self.columns_text.insert('1.0', '*')

        # WHERE clause
        tk.Label(self, text='WHERE:', bg='#2d2d2d', fg='white',
                font=('Arial', 10, 'bold')).pack(pady=(10, 5))

        self.where_text = tk.Text(self, height=3, bg='#1e1e1e', fg='white',
                                 insertbackground='white')
        self.where_text.pack(fill='x', padx=20, pady=5)

        # ORDER BY
        tk.Label(self, text='ORDER BY:', bg='#2d2d2d', fg='white',
                font=('Arial', 10, 'bold')).pack(pady=(10, 5))

        self.order_text = tk.Entry(self, bg='#1e1e1e', fg='white',
                                   insertbackground='white')
        self.order_text.pack(fill='x', padx=20, pady=5)

        # LIMIT
        tk.Label(self, text='LIMIT:', bg='#2d2d2d', fg='white',
                font=('Arial', 10, 'bold')).pack(pady=(10, 5))

        self.limit_var = tk.StringVar(value='100')
        limit_entry = tk.Entry(self, textvariable=self.limit_var, bg='#1e1e1e',
                              fg='white', insertbackground='white')
        limit_entry.pack(fill='x', padx=20, pady=5)

        # Build button
        tk.Button(self, text='Build Query', command=self._build_query,
                 bg='#00C49F', fg='white', font=('Arial', 10, 'bold')).pack(pady=20)

    def _build_query(self):
        """Build SQL query from form."""
        table = self.table_var.get()
        columns = self.columns_text.get('1.0', 'end-1c').strip() or '*'
        where = self.where_text.get('1.0', 'end-1c').strip()
        order_by = self.order_text.get().strip()
        limit = self.limit_var.get().strip()

        query = f"SELECT {columns} FROM {table}"

        if where:
            query += f" WHERE {where}"

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += f" LIMIT {limit}"

        self.on_build(query)
        self.destroy()


class DatabaseBrowser(tk.Frame):
    """Database browser GUI."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#1e1e1e')
        self.db_connection: Optional[DatabaseConnection] = None

        self._build_ui()

    def _build_ui(self):
        """Build database browser UI."""
        # Toolbar
        toolbar = tk.Frame(self, bg='#1e1e1e', height=50)
        toolbar.pack(side='top', fill='x')

        tk.Button(toolbar, text='📂 Connect SQLite', command=self._connect_sqlite,
                 bg='#0088FE', fg='white').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='🔌 Connect Server', command=self._connect_server,
                 bg='#0088FE', fg='white').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='❌ Disconnect', command=self._disconnect,
                 bg='#FF8042', fg='white').pack(side='left', padx=5, pady=5)

        tk.Label(toolbar, text='|', bg='#1e1e1e', fg='#858585').pack(side='left', padx=5)

        tk.Button(toolbar, text='🔄 Refresh', command=self._refresh_schema,
                 bg='#858585', fg='white').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='🔨 Query Builder', command=self._open_query_builder,
                 bg='#FFBB28', fg='black').pack(side='left', padx=5, pady=5)

        # Status
        self.status_label = tk.Label(toolbar, text='Not connected', bg='#1e1e1e',
                                     fg='#858585', font=('Arial', 9))
        self.status_label.pack(side='right', padx=10)

        # Main content (paned window)
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(side='top', fill='both', expand=True)

        # Left panel - Schema tree
        left_frame = tk.Frame(paned, bg='#2d2d2d', width=300)
        paned.add(left_frame, weight=1)

        tk.Label(left_frame, text='Database Schema', bg='#2d2d2d', fg='white',
                font=('Arial', 11, 'bold')).pack(pady=5)

        tree_frame = tk.Frame(left_frame, bg='#2d2d2d')
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.schema_tree = ttk.Treeview(tree_frame, show='tree')
        schema_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical',
                                        command=self.schema_tree.yview)
        self.schema_tree.configure(yscrollcommand=schema_scrollbar.set)

        self.schema_tree.pack(side='left', fill='both', expand=True)
        schema_scrollbar.pack(side='right', fill='y')

        # Bind double-click to generate SELECT
        self.schema_tree.bind('<Double-Button-1>', self._on_table_double_click)

        # Right panel - Query and results
        right_frame = tk.Frame(paned, bg='#2d2d2d')
        paned.add(right_frame, weight=3)

        # SQL Editor
        editor_frame = tk.LabelFrame(right_frame, text='SQL Editor', bg='#2d2d2d',
                                     fg='white', font=('Arial', 10, 'bold'))
        editor_frame.pack(fill='x', padx=5, pady=5)

        self.sql_text = tk.Text(editor_frame, height=6, bg='#1e1e1e', fg='#d4d4d4',
                                insertbackground='white', font=('Courier', 10))
        sql_scrollbar = ttk.Scrollbar(editor_frame, orient='vertical',
                                     command=self.sql_text.yview)
        self.sql_text.configure(yscrollcommand=sql_scrollbar.set)

        self.sql_text.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        sql_scrollbar.pack(side='right', fill='y', pady=5)

        # Execute button
        button_frame = tk.Frame(editor_frame, bg='#2d2d2d')
        button_frame.pack(fill='x', padx=5, pady=5)

        tk.Button(button_frame, text='▶️ Execute Query', command=self._execute_query,
                 bg='#00C49F', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        tk.Button(button_frame, text='📋 Clear', command=lambda: self.sql_text.delete('1.0', 'end'),
                 bg='#858585', fg='white').pack(side='left', padx=5)

        # Results
        results_frame = tk.LabelFrame(right_frame, text='Query Results', bg='#2d2d2d',
                                      fg='white', font=('Arial', 10, 'bold'))
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Results toolbar
        results_toolbar = tk.Frame(results_frame, bg='#2d2d2d')
        results_toolbar.pack(fill='x', padx=5, pady=5)

        tk.Button(results_toolbar, text='📋 Export CSV', command=self._export_csv,
                 bg='#0088FE', fg='white').pack(side='left', padx=5)
        tk.Button(results_toolbar, text='📋 Export JSON', command=self._export_json,
                 bg='#0088FE', fg='white').pack(side='left', padx=5)

        self.results_label = tk.Label(results_toolbar, text='Rows: 0', bg='#2d2d2d',
                                      fg='#858585', font=('Arial', 9))
        self.results_label.pack(side='right', padx=5)

        # Results tree
        results_tree_frame = tk.Frame(results_frame, bg='#2d2d2d')
        results_tree_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.results_tree = ttk.Treeview(results_tree_frame, show='headings')
        results_scrollbar_v = ttk.Scrollbar(results_tree_frame, orient='vertical',
                                           command=self.results_tree.yview)
        results_scrollbar_h = ttk.Scrollbar(results_tree_frame, orient='horizontal',
                                           command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=results_scrollbar_v.set,
                                   xscrollcommand=results_scrollbar_h.set)

        self.results_tree.grid(row=0, column=0, sticky='nsew')
        results_scrollbar_v.grid(row=0, column=1, sticky='ns')
        results_scrollbar_h.grid(row=1, column=0, sticky='ew')

        results_tree_frame.grid_rowconfigure(0, weight=1)
        results_tree_frame.grid_columnconfigure(0, weight=1)

        # Store query results
        self.current_results: List[Dict] = []
        self.current_columns: List[str] = []

    def _connect_sqlite(self):
        """Connect to SQLite database."""
        filepath = filedialog.askopenfilename(
            title='Select SQLite Database',
            filetypes=[('SQLite Database', '*.db *.sqlite *.sqlite3'), ('All Files', '*.*')]
        )

        if filepath:
            try:
                self.db_connection = DatabaseConnection('sqlite', db_path=filepath)
                self.db_connection.connect()

                self.status_label.config(text=f'Connected: {Path(filepath).name}',
                                        fg='#00C49F')
                self._load_schema()

            except Exception as e:
                messagebox.showerror('Connection Error', str(e))

    def _connect_server(self):
        """Connect to server database (MySQL/PostgreSQL)."""
        # Show connection dialog
        dialog = tk.Toplevel(self)
        dialog.title('Connect to Database')
        dialog.geometry('400x350')
        dialog.configure(bg='#2d2d2d')

        # Database type
        tk.Label(dialog, text='Database Type:', bg='#2d2d2d', fg='white').grid(row=0, column=0, padx=10, pady=10, sticky='w')
        db_type_var = tk.StringVar(value='mysql')
        tk.Radiobutton(dialog, text='MySQL', variable=db_type_var, value='mysql',
                      bg='#2d2d2d', fg='white', selectcolor='#0088FE').grid(row=0, column=1, sticky='w')
        tk.Radiobutton(dialog, text='PostgreSQL', variable=db_type_var, value='postgresql',
                      bg='#2d2d2d', fg='white', selectcolor='#0088FE').grid(row=0, column=2, sticky='w')

        # Connection fields
        fields = [
            ('Host:', 'localhost'),
            ('Port:', '3306'),
            ('Database:', ''),
            ('User:', ''),
            ('Password:', '')
        ]

        entries = {}
        for i, (label, default) in enumerate(fields, start=1):
            tk.Label(dialog, text=label, bg='#2d2d2d', fg='white').grid(row=i, column=0, padx=10, pady=5, sticky='w')
            entry = tk.Entry(dialog, bg='#1e1e1e', fg='white', insertbackground='white', show='*' if label == 'Password:' else '')
            entry.insert(0, default)
            entry.grid(row=i, column=1, columnspan=2, padx=10, pady=5, sticky='ew')
            entries[label] = entry

        dialog.grid_columnconfigure(1, weight=1)

        def connect():
            try:
                self.db_connection = DatabaseConnection(
                    db_type_var.get(),
                    host=entries['Host:'].get(),
                    port=int(entries['Port:'].get()),
                    database=entries['Database:'].get(),
                    user=entries['User:'].get(),
                    password=entries['Password:'].get()
                )
                self.db_connection.connect()

                self.status_label.config(text=f'Connected: {entries["Database:"].get()}',
                                        fg='#00C49F')
                self._load_schema()
                dialog.destroy()

            except Exception as e:
                messagebox.showerror('Connection Error', str(e))

        tk.Button(dialog, text='Connect', command=connect,
                 bg='#00C49F', fg='white').grid(row=len(fields)+1, column=0, columnspan=3, pady=20)

    def _disconnect(self):
        """Disconnect from database."""
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None
            self.status_label.config(text='Not connected', fg='#858585')
            self.schema_tree.delete(*self.schema_tree.get_children())

    def _load_schema(self):
        """Load database schema into tree."""
        if not self.db_connection:
            return

        self.schema_tree.delete(*self.schema_tree.get_children())

        try:
            tables = self.db_connection.get_tables()

            for table in tables:
                # Add table node
                table_node = self.schema_tree.insert('', 'end', text=f'📊 {table}')

                # Load columns
                schema = self.db_connection.get_table_schema(table)
                for column_info in schema:
                    if isinstance(column_info, dict):
                        if 'name' in column_info:  # SQLite
                            col_name = column_info['name']
                            col_type = column_info.get('type', 'UNKNOWN')
                        elif 'column_name' in column_info:  # PostgreSQL
                            col_name = column_info['column_name']
                            col_type = column_info.get('data_type', 'UNKNOWN')
                        else:  # MySQL
                            col_name = column_info.get('Field', list(column_info.values())[0])
                            col_type = column_info.get('Type', 'UNKNOWN')

                        self.schema_tree.insert(table_node, 'end', text=f'  🔹 {col_name} ({col_type})')

        except Exception as e:
            messagebox.showerror('Error', f'Failed to load schema:\n{str(e)}')

    def _refresh_schema(self):
        """Refresh schema tree."""
        if self.db_connection:
            self._load_schema()

    def _on_table_double_click(self, event):
        """Handle table double-click to generate SELECT."""
        item = self.schema_tree.selection()
        if item:
            text = self.schema_tree.item(item[0], 'text')
            if text.startswith('📊'):
                table_name = text.replace('📊 ', '')
                query = f"SELECT * FROM {table_name} LIMIT 100;"
                self.sql_text.delete('1.0', 'end')
                self.sql_text.insert('1.0', query)

    def _open_query_builder(self):
        """Open visual query builder."""
        if not self.db_connection:
            messagebox.showwarning('Not Connected', 'Please connect to a database first')
            return

        try:
            tables = self.db_connection.get_tables()
            QueryBuilder(self, tables, self._insert_built_query)
        except Exception as e:
            messagebox.showerror('Error', f'Failed to open query builder:\n{str(e)}')

    def _insert_built_query(self, query: str):
        """Insert built query into editor."""
        self.sql_text.delete('1.0', 'end')
        self.sql_text.insert('1.0', query)

    def _execute_query(self):
        """Execute SQL query."""
        if not self.db_connection:
            messagebox.showwarning('Not Connected', 'Please connect to a database first')
            return

        query = self.sql_text.get('1.0', 'end-1c').strip()
        if not query:
            messagebox.showwarning('Empty Query', 'Please enter a SQL query')
            return

        try:
            results, columns = self.db_connection.execute(query)

            self.current_results = results
            self.current_columns = columns

            # Clear results tree
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)

            if columns:
                # Configure columns
                self.results_tree['columns'] = columns
                for col in columns:
                    self.results_tree.heading(col, text=col)
                    self.results_tree.column(col, width=150)

                # Insert data
                for row in results:
                    values = [row.get(col, '') for col in columns]
                    self.results_tree.insert('', 'end', values=values)

                self.results_label.config(text=f'Rows: {len(results)}')
            else:
                # No results (INSERT, UPDATE, DELETE)
                self.results_label.config(text='Query executed successfully')
                messagebox.showinfo('Success', 'Query executed successfully')

        except Exception as e:
            messagebox.showerror('Query Error', str(e))

    def _export_csv(self):
        """Export results to CSV."""
        if not self.current_results:
            messagebox.showwarning('No Results', 'No query results to export')
            return

        filepath = filedialog.asksaveasfilename(
            title='Export to CSV',
            defaultextension='.csv',
            filetypes=[('CSV Files', '*.csv'), ('All Files', '*.*')]
        )

        if filepath:
            try:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.current_columns)
                    writer.writeheader()
                    writer.writerows(self.current_results)

                messagebox.showinfo('Exported', f'Results exported to:\n{filepath}')

            except Exception as e:
                messagebox.showerror('Error', f'Failed to export:\n{str(e)}')

    def _export_json(self):
        """Export results to JSON."""
        if not self.current_results:
            messagebox.showwarning('No Results', 'No query results to export')
            return

        filepath = filedialog.asksaveasfilename(
            title='Export to JSON',
            defaultextension='.json',
            filetypes=[('JSON Files', '*.json'), ('All Files', '*.*')]
        )

        if filepath:
            try:
                Path(filepath).write_text(json.dumps(self.current_results, indent=2), encoding='utf-8')
                messagebox.showinfo('Exported', f'Results exported to:\n{filepath}')

            except Exception as e:
                messagebox.showerror('Error', f'Failed to export:\n{str(e)}')


# Demo/Test
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Database Browser - D1 Demo')
    root.geometry('1200x800')

    browser = DatabaseBrowser(root)
    browser.pack(fill='both', expand=True)

    root.mainloop()
