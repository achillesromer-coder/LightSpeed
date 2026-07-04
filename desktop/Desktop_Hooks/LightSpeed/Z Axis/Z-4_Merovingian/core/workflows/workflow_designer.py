#!/usr/bin/env python
"""
Workflow Designer - Visual Workflow Builder UI
Interactive workflow design interface with canvas-based node editor

Features:
- Drag-and-drop node placement
- Visual node connections
- Node property editor
- Workflow execution controls
- Real-time execution monitoring
- Workflow templates
- Export/Import workflows

Author: LightSpeed Team
Version: 0.9.5
Date: December 15, 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import time
from .workflow_engine import WorkflowEngine, Workflow, WorkflowNode, NodeType, TaskStatus


class WorkflowDesignerUI:
    """Visual workflow designer interface"""

    def __init__(self, parent, base_path: Path):
        self.parent = parent
        self.base_path = base_path
        self.engine = WorkflowEngine(base_path)

        self.current_workflow: Optional[Workflow] = None
        self.selected_node: Optional[WorkflowNode] = None
        self.canvas_nodes: Dict[str, int] = {}  # node_id -> canvas_id
        self.canvas_connections: List[int] = []  # canvas line IDs
        self._drag_state: Optional[Dict[str, object]] = None

        # Build UI
        self.frame = tk.Frame(parent, bg='#0a0a1a')
        self._build_ui()

        # Load workflows
        self._refresh_workflow_list()

    def _build_ui(self):
        """Build designer interface"""

        # Header
        header = tk.Frame(self.frame, bg='#15152a', height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="⚙️ WORKFLOW DESIGNER",
                font=('Arial', 18, 'bold'),
                bg='#15152a', fg='#00d4ff').pack(pady=10)

        # Main content
        content = tk.Frame(self.frame, bg='#0a0a1a')
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel: Workflow list + Node palette
        left_panel = tk.Frame(content, bg='#0a0a1a', width=250)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))

        self._build_workflow_list(left_panel)
        self._build_node_palette(left_panel)

        # Center: Canvas
        center_panel = tk.Frame(content, bg='#0a0a1a')
        center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self._build_canvas(center_panel)

        # Right panel: Properties
        right_panel = tk.Frame(content, bg='#0a0a1a', width=300)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH)

        self._build_properties_panel(right_panel)

        # Bottom: Controls
        self._build_controls()

    def _build_workflow_list(self, parent):
        """Build workflow list panel"""
        list_frame = tk.LabelFrame(parent, text="Workflows",
                                  bg='#15152a', fg='#ffffff',
                                  font=('Arial', 11, 'bold'))
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Workflow listbox
        self.workflow_listbox = tk.Listbox(list_frame, bg='#000000', fg='#00d4ff',
                                          font=('Consolas', 9),
                                          selectmode='single')
        self.workflow_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.workflow_listbox.bind('<<ListboxSelect>>', self._on_workflow_select)

        # Workflow controls
        btn_frame = tk.Frame(list_frame, bg='#15152a')
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(btn_frame, text="New", command=self._new_workflow,
                 bg='#00ff88', fg='#000000',
                 font=('Arial', 8, 'bold'), width=8).pack(side=tk.LEFT, padx=2)

        tk.Button(btn_frame, text="Delete", command=self._delete_workflow,
                 bg='#ff3333', fg='#ffffff',
                 font=('Arial', 8, 'bold'), width=8).pack(side=tk.LEFT, padx=2)

    def _build_node_palette(self, parent):
        """Build node palette panel"""
        palette_frame = tk.LabelFrame(parent, text="Node Palette",
                                     bg='#15152a', fg='#ffffff',
                                     font=('Arial', 11, 'bold'))
        palette_frame.pack(fill=tk.BOTH)

        # Node types
        node_types = [
            ("📋 Task", NodeType.TASK),
            ("❓ Condition", NodeType.CONDITION),
            ("🔁 Loop", NodeType.LOOP),
            ("⏸️ Wait", NodeType.WAIT),
            ("📢 Notify", NodeType.NOTIFY),
        ]

        for label, node_type in node_types:
            btn = tk.Button(palette_frame, text=label,
                          command=lambda nt=node_type: self._add_node_to_canvas(nt),
                          bg='#0088ff', fg='#ffffff',
                          font=('Arial', 9),
                          anchor='w')
            btn.pack(fill=tk.X, padx=5, pady=2)

    def _build_canvas(self, parent):
        """Build workflow canvas"""
        canvas_frame = tk.LabelFrame(parent, text="Workflow Canvas",
                                    bg='#15152a', fg='#ffffff',
                                    font=('Arial', 11, 'bold'))
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas with scrollbars
        self.canvas = tk.Canvas(canvas_frame, bg='#0a0a1a',
                               highlightthickness=0)

        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL,
                                   command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL,
                                   command=self.canvas.yview)

        self.canvas.configure(xscrollcommand=h_scrollbar.set,
                            yscrollcommand=v_scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky='nsew')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # Configure scrollable region
        self.canvas.configure(scrollregion=(0, 0, 2000, 2000))

        # Bind events
        self.canvas.bind('<Button-1>', self._on_canvas_click)
        self.canvas.bind('<B1-Motion>', self._on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_canvas_release)

    def _build_properties_panel(self, parent):
        """Build node properties panel"""
        props_frame = tk.LabelFrame(parent, text="Node Properties",
                                   bg='#15152a', fg='#ffffff',
                                   font=('Arial', 11, 'bold'))
        props_frame.pack(fill=tk.BOTH, expand=True)

        # Properties display
        self.props_text = tk.Text(props_frame, height=20, wrap='word',
                                 bg='#000000', fg='#00ff88',
                                 font=('Consolas', 9))
        self.props_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Edit button
        tk.Button(props_frame, text="✏️ Edit Properties",
                 command=self._edit_node_properties,
                 bg='#ff9900', fg='#000000',
                 font=('Arial', 9, 'bold')).pack(pady=5)

    def _build_controls(self):
        """Build bottom controls"""
        controls = tk.Frame(self.frame, bg='#0a0a1a')
        controls.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(controls, text="▶️ Execute Workflow",
                 command=self._execute_workflow,
                 bg='#00ff00', fg='#000000',
                 font=('Arial', 10, 'bold'),
                 width=18).pack(side=tk.LEFT, padx=5)

        tk.Button(controls, text="💾 Save",
                 command=self._save_workflow,
                 bg='#0088ff', fg='#ffffff',
                 font=('Arial', 10, 'bold'),
                 width=18).pack(side=tk.LEFT, padx=5)

        tk.Button(controls, text="📜 History",
                 command=self._show_history,
                 bg='#9932cc', fg='#ffffff',
                 font=('Arial', 10, 'bold'),
                 width=18).pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(controls, text="Ready",
                                     bg='#0a0a1a', fg='#00d4ff',
                                     font=('Arial', 10))
        self.status_label.pack(side=tk.RIGHT, padx=10)

    def _refresh_workflow_list(self):
        """Refresh workflow list"""
        self.workflow_listbox.delete(0, tk.END)
        for workflow in self.engine.workflows.values():
            self.workflow_listbox.insert(tk.END, f"{workflow.name} (v{workflow.version})")

    def _on_workflow_select(self, event):
        """Handle workflow selection"""
        selection = self.workflow_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        workflow_id = list(self.engine.workflows.keys())[idx]
        self.current_workflow = self.engine.workflows[workflow_id]

        self._draw_workflow()
        self.status_label.config(text=f"Loaded: {self.current_workflow.name}")

    def _draw_workflow(self):
        """Draw current workflow on canvas"""
        if not self.current_workflow:
            return

        # Clear canvas
        self.canvas.delete('all')
        self.canvas_nodes.clear()
        self.canvas_connections.clear()

        # Draw grid
        self._draw_grid()

        # Draw connections first
        for node in self.current_workflow.nodes:
            for conn_id in node.connections:
                conn_node = next((n for n in self.current_workflow.nodes if n.id == conn_id), None)
                if conn_node:
                    line_id = self.canvas.create_line(
                        node.position[0] + 60, node.position[1] + 20,
                        conn_node.position[0], conn_node.position[1] + 20,
                        arrow=tk.LAST,
                        fill='#00d4ff',
                        width=2
                    )
                    self.canvas_connections.append(line_id)

        # Draw nodes
        for node in self.current_workflow.nodes:
            self._draw_node(node)

    def _redraw_connections(self) -> None:
        """Redraw connection lines only (keeps grid/nodes)."""
        if not self.current_workflow:
            return

        for line_id in self.canvas_connections:
            try:
                self.canvas.delete(line_id)
            except Exception:
                continue
        self.canvas_connections.clear()

        for node in self.current_workflow.nodes:
            for conn_id in node.connections:
                conn_node = next((n for n in self.current_workflow.nodes if n.id == conn_id), None)
                if conn_node:
                    line_id = self.canvas.create_line(
                        node.position[0] + 60, node.position[1] + 20,
                        conn_node.position[0], conn_node.position[1] + 20,
                        arrow=tk.LAST,
                        fill='#00d4ff',
                        width=2
                    )
                    self.canvas_connections.append(line_id)

    def _draw_grid(self):
        """Draw grid on canvas"""
        for x in range(0, 2000, 50):
            self.canvas.create_line(x, 0, x, 2000, fill='#1a1a2a', width=1)
        for y in range(0, 2000, 50):
            self.canvas.create_line(0, y, 2000, y, fill='#1a1a2a', width=1)

    def _draw_node(self, node: WorkflowNode):
        """Draw a single node on canvas"""
        x, y = node.position

        # Node color based on type
        colors = {
            NodeType.START: '#00ff00',
            NodeType.END: '#ff0000',
            NodeType.TASK: '#0088ff',
            NodeType.CONDITION: '#ff9900',
            NodeType.LOOP: '#9932cc',
            NodeType.WAIT: '#ffaa00',
            NodeType.NOTIFY: '#00ffff',
            NodeType.PARALLEL: '#ff00ff',
        }
        color = colors.get(node.type, '#888888')

        # Status outline
        status_colors = {
            TaskStatus.PENDING: '#666666',
            TaskStatus.RUNNING: '#ffff00',
            TaskStatus.COMPLETED: '#00ff00',
            TaskStatus.FAILED: '#ff0000',
            TaskStatus.SKIPPED: '#888888',
        }
        outline_color = status_colors.get(node.status, '#666666')

        # Draw rectangle
        rect_id = self.canvas.create_rectangle(
            x, y, x + 120, y + 40,
            fill=color,
            outline=outline_color,
            width=3,
            tags=f'node_{node.id}'
        )

        # Draw text
        text_id = self.canvas.create_text(
            x + 60, y + 20,
            text=node.name,
            fill='#000000' if node.type != NodeType.START else '#ffffff',
            font=('Arial', 9, 'bold'),
            tags=f'node_{node.id}'
        )

        self.canvas_nodes[node.id] = rect_id

        # Bind click event
        self.canvas.tag_bind(f'node_{node.id}', '<Button-1>',
                           lambda e, n=node: self._on_node_click(n, e))

    def _on_node_click(self, node: WorkflowNode, event=None):
        """Handle node click"""
        self.selected_node = node
        self._show_node_properties(node)

        if event is not None:
            self._drag_state = {
                "node_id": node.id,
                "last_x": int(getattr(event, "x", 0)),
                "last_y": int(getattr(event, "y", 0)),
            }

    def _show_node_properties(self, node: WorkflowNode):
        """Show node properties"""
        props = f"""Node: {node.name}
Type: {node.type.value}
ID: {node.id}

Floor: {node.floor or 'N/A'}
Function: {node.function or 'N/A'}

Parameters:
{json.dumps(node.parameters, indent=2) if node.parameters else 'None'}

Connections: {', '.join(node.connections) if node.connections else 'None'}
Status: {node.status.value}
"""
        self.props_text.delete('1.0', 'end')
        self.props_text.insert('1.0', props)

    def _on_canvas_click(self, event):
        """Handle canvas click"""
        self._drag_state = None

        current = self.canvas.find_withtag('current')
        if not current:
            self.selected_node = None
            self._clear_node_properties()
            return

        tags = self.canvas.gettags(current[0])
        node_tag = next((t for t in tags if t.startswith('node_')), None)
        if not node_tag:
            self.selected_node = None
            self._clear_node_properties()
            return

        node_id = node_tag[len('node_'):]
        node = None
        if self.current_workflow:
            node = next((n for n in self.current_workflow.nodes if n.id == node_id), None)
        if node is None:
            self.selected_node = None
            self._clear_node_properties()
            return

        self.selected_node = node
        self._show_node_properties(node)
        self._drag_state = {"node_id": node_id, "last_x": int(event.x), "last_y": int(event.y)}

    def _on_canvas_drag(self, event):
        """Handle canvas drag"""
        if not self.current_workflow or not self._drag_state:
            return

        node_id = self._drag_state.get("node_id")
        if not node_id:
            return

        node = next((n for n in self.current_workflow.nodes if n.id == node_id), None)
        if node is None:
            return

        last_x = int(self._drag_state.get("last_x", event.x))
        last_y = int(self._drag_state.get("last_y", event.y))
        dx = int(event.x) - last_x
        dy = int(event.y) - last_y
        if dx == 0 and dy == 0:
            return

        # Move visuals and update stored position
        self.canvas.move(f'node_{node.id}', dx, dy)
        x, y = node.position
        node.position = (int(x + dx), int(y + dy))
        self._drag_state["last_x"] = int(event.x)
        self._drag_state["last_y"] = int(event.y)

        # Keep connection lines accurate during drag
        self._redraw_connections()

    def _on_canvas_release(self, _event):
        """Finalize drag and persist position."""
        if not self.current_workflow or not self._drag_state:
            return
        try:
            self.engine.save_workflow(self.current_workflow)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Failed to persist workflow after drag: %s", e)
        self._drag_state = None

    def _new_workflow(self):
        """Create new workflow"""
        name = simpledialog.askstring("New Workflow", "Enter workflow name:")
        if name:
            description = simpledialog.askstring("New Workflow", "Enter description:")
            workflow = self.engine.create_workflow(name, description or "")
            self._refresh_workflow_list()
            messagebox.showinfo("Success", f"Workflow '{name}' created")

    def _delete_workflow(self):
        """Delete selected workflow"""
        if not self.current_workflow:
            messagebox.showwarning("No Selection", "Please select a workflow")
            return

        if messagebox.askyesno("Confirm Delete",
                              f"Delete workflow '{self.current_workflow.name}'?"):
            self.engine.delete_workflow(self.current_workflow.id)
            self.current_workflow = None
            self.canvas.delete('all')
            self._refresh_workflow_list()

    def _add_node_to_canvas(self, node_type: NodeType):
        """Add node to current workflow"""
        if not self.current_workflow:
            messagebox.showwarning("No Workflow", "Please create or select a workflow first")
            return

        name = simpledialog.askstring("New Node", f"Enter {node_type.value} node name:")
        if name:
            node = WorkflowNode(
                id=f"node_{int(time.time() * 1000)}",
                type=node_type,
                name=name,
                position=(200, len(self.current_workflow.nodes) * 60 + 50)
            )
            self.engine.add_node(self.current_workflow.id, node)
            self._draw_workflow()

    def _edit_node_properties(self):
        """Edit selected node properties"""
        if not self.selected_node:
            messagebox.showwarning("No Selection", "Please select a node")
            return

        if not self.current_workflow:
            messagebox.showwarning("No Workflow", "Please select a workflow")
            return

        node = self.selected_node

        win = tk.Toplevel(self.frame)
        win.title(f"Edit Node: {node.name}")
        win.geometry("650x650")
        win.configure(bg='#15152a')

        container = tk.Frame(win, bg='#15152a')
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        def row(label: str, widget: tk.Widget):
            r = tk.Frame(container, bg='#15152a')
            r.pack(fill=tk.X, pady=6)
            tk.Label(r, text=label, width=16, anchor='w', bg='#15152a', fg='#ffffff', font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
            widget.pack(side=tk.LEFT, fill=tk.X, expand=True)

        name_var = tk.StringVar(value=node.name)
        floor_var = tk.StringVar(value=node.floor or "")
        function_var = tk.StringVar(value=node.function or "")
        status_var = tk.StringVar(value=node.status.value if hasattr(node.status, "value") else str(node.status))
        connections_var = tk.StringVar(value=", ".join(node.connections or []))
        pos_var = tk.StringVar(value=f"{node.position[0]},{node.position[1]}")

        name_entry = tk.Entry(container, textvariable=name_var, font=('Arial', 11))
        row("Name", name_entry)

        tk.Label(container, text=f"Type: {node.type.value}", bg='#15152a', fg='#00d4ff', font=('Arial', 10, 'italic')).pack(anchor='w', pady=(4, 10))

        floors = sorted(self.engine.floor_functions.keys())
        floor_combo = ttk.Combobox(container, textvariable=floor_var, values=[""] + floors, state="readonly")
        row("Floor", floor_combo)

        function_combo = ttk.Combobox(container, textvariable=function_var, values=[""], state="readonly")
        row("Function", function_combo)

        def refresh_functions(*_args):
            floor = floor_var.get().strip()
            funcs = []
            if floor and floor in self.engine.floor_functions:
                funcs = sorted(self.engine.floor_functions[floor].keys())
            function_combo.configure(values=[""] + funcs)
            if function_var.get().strip() not in funcs:
                function_var.set(funcs[0] if funcs else "")

        floor_var.trace_add("write", refresh_functions)
        refresh_functions()

        status_combo = ttk.Combobox(container, textvariable=status_var,
                                   values=[s.value for s in TaskStatus], state="readonly")
        row("Status", status_combo)

        connections_entry = tk.Entry(container, textvariable=connections_var, font=('Arial', 11))
        row("Connections", connections_entry)

        pos_entry = tk.Entry(container, textvariable=pos_var, font=('Arial', 11))
        row("Position x,y", pos_entry)

        tk.Label(container, text="Parameters (JSON)", bg='#15152a', fg='#ffffff', font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 4))
        params_text = tk.Text(container, height=12, wrap='word', bg='#000000', fg='#00ff88', font=('Consolas', 9))
        params_text.pack(fill=tk.BOTH, expand=True)
        params_text.insert('1.0', json.dumps(node.parameters or {}, indent=2))

        def save():
            # Parse/validate params
            try:
                params = json.loads(params_text.get('1.0', 'end').strip() or "{}")
                if not isinstance(params, dict):
                    raise ValueError("Parameters must be a JSON object")
            except Exception as e:
                messagebox.showerror("Invalid Parameters", f"Parameters JSON is invalid:\n{e}", parent=win)
                return

            # Parse position
            try:
                x_str, y_str = (pos_var.get() or "").split(",", 1)
                x = int(float(x_str.strip()))
                y = int(float(y_str.strip()))
            except Exception:
                messagebox.showerror("Invalid Position", "Position must be in the form: x,y", parent=win)
                return

            # Parse connections
            raw_conns = [c.strip() for c in (connections_var.get() or "").split(",") if c.strip()]
            valid_ids = {n.id for n in self.current_workflow.nodes}
            raw_conns = [c for c in raw_conns if c in valid_ids and c != node.id]

            # Apply changes
            node.name = name_var.get().strip() or node.name
            node.floor = floor_var.get().strip() or None
            node.function = function_var.get().strip() or None
            node.parameters = params
            node.connections = raw_conns
            try:
                node.status = TaskStatus(status_var.get())
            except Exception:
                node.status = TaskStatus.PENDING
            node.position = (x, y)

            try:
                self.engine.save_workflow(self.current_workflow)
            except Exception as e:
                messagebox.showerror("Save Failed", f"Could not save workflow:\n{e}", parent=win)
                return

            self._draw_workflow()
            self._show_node_properties(node)
            win.destroy()
            self.status_label.config(text=f"Saved node: {node.name}")

        btns = tk.Frame(container, bg='#15152a')
        btns.pack(fill=tk.X, pady=10)
        tk.Button(btns, text="Save", command=save, bg='#00ff88', fg='#000000', font=('Arial', 10, 'bold'), width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="Cancel", command=win.destroy, bg='#ff3333', fg='#ffffff', font=('Arial', 10, 'bold'), width=10).pack(side=tk.LEFT, padx=5)

    def _clear_node_properties(self):
        """Clear the properties pane."""
        try:
            self.props_text.delete('1.0', 'end')
            self.props_text.insert('1.0', "No node selected.\nClick a node to view or edit its properties.")
        except Exception:
            return

    def _save_workflow(self):
        """Save current workflow"""
        if not self.current_workflow:
            messagebox.showwarning("No Workflow", "No workflow to save")
            return

        self.engine.save_workflow(self.current_workflow)
        messagebox.showinfo("Saved", f"Workflow '{self.current_workflow.name}' saved")

    def _execute_workflow(self):
        """Execute current workflow"""
        if not self.current_workflow:
            messagebox.showwarning("No Workflow", "Please select a workflow")
            return

        result = self.engine.execute_workflow(self.current_workflow.id, async_mode=False)

        if result["status"] == "completed":
            messagebox.showinfo("Execution Complete",
                              f"Workflow completed in {result['duration']:.2f}s")
            self._draw_workflow()  # Refresh to show status
        else:
            messagebox.showerror("Execution Failed",
                               f"Error: {result.get('message', 'Unknown error')}")

    def _show_history(self):
        """Show execution history"""
        history_win = tk.Toplevel(self.frame)
        history_win.title("Workflow Execution History")
        history_win.geometry("800x500")
        history_win.configure(bg='#15152a')

        tk.Label(history_win, text="Execution History",
                font=('Arial', 14, 'bold'),
                bg='#15152a', fg='#00d4ff').pack(pady=10)

        # History TreeView
        columns = ('Workflow', 'Start Time', 'Duration', 'Status')
        history_tree = ttk.Treeview(history_win, columns=columns,
                                   show='headings', height=20)

        for col in columns:
            history_tree.heading(col, text=col)

        history_tree.column('Workflow', width=200)
        history_tree.column('Start Time', width=150)
        history_tree.column('Duration', width=100)
        history_tree.column('Status', width=100)

        scrollbar = ttk.Scrollbar(history_win, orient=tk.VERTICAL,
                                 command=history_tree.yview)
        history_tree.configure(yscrollcommand=scrollbar.set)

        history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        # Populate history
        for entry in self.engine.get_execution_history():
            duration_str = f"{entry['duration']:.2f}s"
            history_tree.insert("", "end", values=(
                entry["workflow_name"],
                entry["start_time"],
                duration_str,
                entry["status"]
            ))


def build(app, parent):
    """Build workflow designer UI"""
    base_path = Path(__file__).resolve().parents[2]
    return WorkflowDesignerUI(parent, base_path).frame
