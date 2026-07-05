"""
Project Workspace Portal - V1.0.0
Main UI for creating and managing project workspaces in TheConstruct (Z0)

This is the entry point for users to create isolated project environments
that pull components from the entire Z-stack.

Author: LightSpeed Team
Date: December 27, 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, List, Any
from pathlib import Path

# Import workspace system
import sys
def _find_lightspeed_root() -> Path:
    here = Path(__file__).resolve()
    for cand in (here, *here.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return here.parents[3]


_ROOT = _find_lightspeed_root()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_Z_AXIS = _ROOT / "Z Axis"
if _Z_AXIS.exists() and str(_Z_AXIS) not in sys.path:
    sys.path.insert(0, str(_Z_AXIS))
_MEROV = _Z_AXIS / "Z-4_Merovingian"
if _MEROV.exists() and str(_MEROV) not in sys.path:
    sys.path.insert(0, str(_MEROV))

from core.project_workspace import (
    ComponentPuller,
    ProjectWorkspaceCreator,
    WorkspaceType,
    WorkspaceStatus,
    create_component_puller,
    create_schema_validator,
    create_workspace_layout,
    get_workspace_config,
    get_template,
    list_templates_by_type
)


# ==============================================================================
# Main Workspace Portal
# ==============================================================================

class ProjectWorkspacePortal(tk.Frame):
    """
    Main UI for project workspace creation and management

    Provides:
    - Workspace type selection
    - Template browser
    - Component selection from Z-stack
    - Spherical layout configuration
    - Standards configuration
    - Workspace launch
    """

    def __init__(self, parent, **kwargs):
        """
        Initialize workspace portal

        Args:
            parent: Parent widget
            **kwargs: Additional frame options
        """
        super().__init__(parent, bg=kwargs.get('bg', '#1e1e1e'))

        # Initialize workspace system
        self.workspace_creator = ProjectWorkspaceCreator()
        self.component_puller = create_component_puller()
        self.schema_validator = create_schema_validator()

        # Current state
        self.current_workspace_type: Optional[WorkspaceType] = None
        self.selected_template: Optional[str] = None
        self.selected_components: List[str] = []

        # Build UI
        self._build_ui()

    def _build_ui(self):
        """Build the portal UI"""
        # Header
        header = tk.Frame(self, bg='#0a0a0a', height=60)
        header.pack(side='top', fill='x')

        tk.Label(
            header,
            text='PROJECT WORKSPACE CREATOR',
            bg='#0a0a0a',
            fg='#00d4ff',
            font=('Arial', 18, 'bold')
        ).pack(side='left', padx=20, pady=15)

        tk.Label(
            header,
            text='TheConstruct (Z0)',
            bg='#0a0a0a',
            fg='#888888',
            font=('Arial', 12)
        ).pack(side='right', padx=20)

        # Main content area with notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Tab 1: Create New Workspace
        self.create_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.create_tab, text='Create New')

        # Tab 2: Manage Existing Workspaces
        self.manage_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.manage_tab, text='Manage Workspaces')

        # Build tabs
        self._build_create_tab()
        self._build_manage_tab()

    def _build_create_tab(self):
        """Build workspace creation tab"""
        # Left panel - Workspace Type Selection
        left_panel = tk.Frame(self.create_tab, bg='#2d2d2d', width=300)
        left_panel.pack(side='left', fill='y', padx=10, pady=10)
        left_panel.pack_propagate(False)

        tk.Label(
            left_panel,
            text='Select Workspace Type',
            bg='#2d2d2d',
            fg='white',
            font=('Arial', 12, 'bold')
        ).pack(pady=10)

        # Workspace type buttons
        self.type_buttons = {}
        for ws_type in WorkspaceType:
            config = get_workspace_config(ws_type)
            btn = tk.Button(
                left_panel,
                text=config.display_name,
                bg='#404040',
                fg='white',
                font=('Arial', 10),
                relief='flat',
                activebackground='#00d4ff',
                activeforeground='black',
                command=lambda t=ws_type: self._select_workspace_type(t),
                width=25,
                height=2
            )
            btn.pack(pady=5, padx=10)
            self.type_buttons[ws_type] = btn

        # Right panel - Workspace Configuration
        right_panel = tk.Frame(self.create_tab, bg='#1e1e1e')
        right_panel.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        # Workspace details section
        details_frame = tk.LabelFrame(
            right_panel,
            text='Workspace Details',
            bg='#2d2d2d',
            fg='white',
            font=('Arial', 11, 'bold')
        )
        details_frame.pack(fill='x', pady=5)

        # Name input
        tk.Label(details_frame, text='Name:', bg='#2d2d2d', fg='white').grid(
            row=0, column=0, sticky='w', padx=10, pady=5
        )
        self.name_var = tk.StringVar()
        tk.Entry(
            details_frame,
            textvariable=self.name_var,
            bg='#404040',
            fg='white',
            insertbackground='white',
            font=('Arial', 10),
            width=40
        ).grid(row=0, column=1, padx=10, pady=5)

        # Description input
        tk.Label(details_frame, text='Description:', bg='#2d2d2d', fg='white').grid(
            row=1, column=0, sticky='nw', padx=10, pady=5
        )
        self.description_text = tk.Text(
            details_frame,
            bg='#404040',
            fg='white',
            insertbackground='white',
            font=('Arial', 10),
            height=3,
            width=40
        )
        self.description_text.grid(row=1, column=1, padx=10, pady=5)

        # Template selection
        template_frame = tk.LabelFrame(
            right_panel,
            text='Templates (Optional)',
            bg='#2d2d2d',
            fg='white',
            font=('Arial', 11, 'bold')
        )
        template_frame.pack(fill='x', pady=5)

        self.template_listbox = tk.Listbox(
            template_frame,
            bg='#404040',
            fg='white',
            selectbackground='#00d4ff',
            selectforeground='black',
            font=('Arial', 10),
            height=4
        )
        self.template_listbox.pack(fill='x', padx=10, pady=5)
        self.template_listbox.bind('<<ListboxSelect>>', self._on_template_select)

        # Component selection
        component_frame = tk.LabelFrame(
            right_panel,
            text='Components from Z-Stack',
            bg='#2d2d2d',
            fg='white',
            font=('Arial', 11, 'bold')
        )
        component_frame.pack(fill='both', expand=True, pady=5)

        # Component tree
        self.component_tree = ttk.Treeview(
            component_frame,
            columns=('Z-Floor', 'Category'),
            show='tree headings',
            height=8
        )
        self.component_tree.heading('#0', text='Component')
        self.component_tree.heading('Z-Floor', text='Z-Floor')
        self.component_tree.heading('Category', text='Category')

        scrollbar = ttk.Scrollbar(component_frame, orient='vertical', command=self.component_tree.yview)
        self.component_tree.configure(yscrollcommand=scrollbar.set)

        self.component_tree.pack(side='left', fill='both', expand=True, padx=(10, 0), pady=5)
        scrollbar.pack(side='right', fill='y', padx=(0, 10), pady=5)

        # Create button
        button_frame = tk.Frame(right_panel, bg='#1e1e1e')
        button_frame.pack(fill='x', pady=10)

        tk.Button(
            button_frame,
            text='Create Workspace',
            bg='#00d4ff',
            fg='black',
            font=('Arial', 12, 'bold'),
            command=self._create_workspace,
            width=20,
            height=2
        ).pack(side='right', padx=10)

    def _build_manage_tab(self):
        """Build workspace management tab"""
        # Workspace list
        list_frame = tk.Frame(self.manage_tab, bg='#2d2d2d')
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Workspace tree
        self.workspace_tree = ttk.Treeview(
            list_frame,
            columns=('Type', 'Created', 'Status'),
            show='tree headings',
            height=15
        )
        self.workspace_tree.heading('#0', text='Workspace Name')
        self.workspace_tree.heading('Type', text='Type')
        self.workspace_tree.heading('Created', text='Created')
        self.workspace_tree.heading('Status', text='Status')

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.workspace_tree.yview)
        self.workspace_tree.configure(yscrollcommand=scrollbar.set)

        self.workspace_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Action buttons
        button_frame = tk.Frame(self.manage_tab, bg='#1e1e1e')
        button_frame.pack(fill='x', pady=10, padx=10)

        tk.Button(
            button_frame,
            text='Open',
            bg='#00d4ff',
            fg='black',
            command=self._open_workspace,
            width=12
        ).pack(side='left', padx=5)

        tk.Button(
            button_frame,
            text='Refresh',
            bg='#404040',
            fg='white',
            command=self._refresh_workspace_list,
            width=12
        ).pack(side='left', padx=5)

        tk.Button(
            button_frame,
            text='Delete',
            bg='#ff4444',
            fg='white',
            command=self._delete_workspace,
            width=12
        ).pack(side='right', padx=5)

        # Initial load
        self._refresh_workspace_list()

    def _select_workspace_type(self, workspace_type: WorkspaceType):
        """Handle workspace type selection"""
        self.current_workspace_type = workspace_type

        # Highlight selected button
        for ws_type, btn in self.type_buttons.items():
            if ws_type == workspace_type:
                btn.configure(bg='#00d4ff', fg='black')
            else:
                btn.configure(bg='#404040', fg='white')

        # Update templates for this type
        self._update_templates()

        # Update available components
        self._update_components()

    def _update_templates(self):
        """Update template list for selected workspace type"""
        self.template_listbox.delete(0, tk.END)

        if self.current_workspace_type:
            templates = list_templates_by_type(self.current_workspace_type)
            for template in templates:
                self.template_listbox.insert(tk.END, template.name)

    def _update_components(self):
        """Update component list for selected workspace type"""
        self.component_tree.delete(*self.component_tree.get_children())

        if not self.current_workspace_type:
            return

        # Get compatible components
        components = self.component_puller.discover_compatible_components(
            self.current_workspace_type
        )

        # Group by Z-floor
        floor_groups = {}
        for comp_meta in components:
            if comp_meta.z_floor not in floor_groups:
                floor_groups[comp_meta.z_floor] = []
            floor_groups[comp_meta.z_floor].append(comp_meta)

        # Add to tree
        for floor, comps in sorted(floor_groups.items()):
            floor_node = self.component_tree.insert(
                '',
                'end',
                text=floor,
                values=('', ''),
                open=True
            )

            for comp in comps:
                self.component_tree.insert(
                    floor_node,
                    'end',
                    text=comp.name,
                    values=(comp.z_floor, comp.category),
                    tags=(comp.component_id,)
                )

    def _on_template_select(self, event):
        """Handle template selection"""
        selection = self.template_listbox.curselection()
        if selection:
            self.selected_template = self.template_listbox.get(selection[0])

    def _create_workspace(self):
        """Create new workspace"""
        # Validate inputs
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror('Error', 'Workspace name is required')
            return

        if not self.current_workspace_type:
            messagebox.showerror('Error', 'Please select a workspace type')
            return

        description = self.description_text.get('1.0', 'end-1c').strip()

        # Get selected components
        selected_items = self.component_tree.selection()
        custom_components = []
        for item in selected_items:
            tags = self.component_tree.item(item, 'tags')
            if tags:
                custom_components.append({
                    'component_id': tags[0],
                    'position': {'theta': 0, 'phi': 0, 'depth': 0.8},
                    'config': {}
                })

        # Create workspace
        try:
            workspace = self.workspace_creator.create_workspace(
                name=name,
                workspace_type=self.current_workspace_type,
                description=description,
                template_id=self.selected_template,
                custom_components=custom_components if custom_components else None
            )

            messagebox.showinfo(
                'Success',
                f'Workspace "{name}" created successfully!\n\n'
                f'Path: {workspace.workspace_path}\n'
                f'Components: {len(workspace.components)}\n'
                f'Standards: {", ".join(workspace.required_standards)}'
            )

            # Clear form
            self.name_var.set('')
            self.description_text.delete('1.0', 'end')
            self.template_listbox.selection_clear(0, tk.END)

            # Refresh manage tab
            self._refresh_workspace_list()

        except Exception as e:
            messagebox.showerror('Error', f'Failed to create workspace:\n{str(e)}')

    def _refresh_workspace_list(self):
        """Refresh workspace list in manage tab"""
        self.workspace_tree.delete(*self.workspace_tree.get_children())

        workspaces = self.workspace_creator.list_workspaces()

        for ws in workspaces:
            self.workspace_tree.insert(
                '',
                'end',
                text=ws.name,
                values=(
                    ws.workspace_type.value,
                    ws.created_at.strftime('%Y-%m-%d'),
                    ws.status.value
                ),
                tags=(ws.id,)
            )

    def _open_workspace(self):
        """Open selected workspace"""
        selection = self.workspace_tree.selection()
        if not selection:
            messagebox.showwarning('Warning', 'Please select a workspace')
            return

        item = selection[0]
        workspace_id = self.workspace_tree.item(item, 'tags')[0]

        workspace = self.workspace_creator.get_workspace(workspace_id)
        if workspace:
            # Open workspace in spherical layout
            # In full implementation, this would launch the workspace UI
            messagebox.showinfo(
                'Workspace',
                f'Opening workspace: {workspace.name}\n\n'
                f'Components: {len(workspace.components)}\n'
                f'Z-Floors: {len(workspace.z_components)}\n'
                f'Path: {workspace.workspace_path}'
            )

    def _delete_workspace(self):
        """Delete selected workspace"""
        selection = self.workspace_tree.selection()
        if not selection:
            messagebox.showwarning('Warning', 'Please select a workspace')
            return

        item = selection[0]
        workspace_name = self.workspace_tree.item(item, 'text')
        workspace_id = self.workspace_tree.item(item, 'tags')[0]

        if messagebox.askyesno(
            'Confirm Delete',
            f'Delete workspace "{workspace_name}"?\n\nThis cannot be undone.'
        ):
            try:
                self.workspace_creator.delete_workspace(workspace_id, remove_files=True)
                messagebox.showinfo('Success', f'Workspace "{workspace_name}" deleted')
                self._refresh_workspace_list()
            except Exception as e:
                messagebox.showerror('Error', f'Failed to delete workspace:\n{str(e)}')


# ==============================================================================
# Standalone Test
# ==============================================================================

if __name__ == '__main__':
    root = tk.Tk()
    root.title('Project Workspace Portal - TheConstruct (Z0)')
    root.geometry('1200x800')
    root.configure(bg='#1e1e1e')

    portal = ProjectWorkspacePortal(root)
    portal.pack(fill='both', expand=True)

    root.mainloop()
