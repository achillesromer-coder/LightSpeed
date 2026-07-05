"""
Workflow Debugger - E3
=======================

Interactive workflow debugger with step execution, breakpoints, and state inspection.

Features:
- Step-by-step execution
- Breakpoint management
- Variable/state inspection
- Execution stack trace
- Node highlighting
- Watch expressions
- Continue/pause execution
- Execution timeline

Author: LightSpeed Platform
Date: December 16, 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import json
from datetime import datetime
import copy


class DebuggerState:
    """Debugger execution state."""

    def __init__(self):
        self.current_node_id: Optional[str] = None
        self.execution_stack: List[str] = []
        self.variables: Dict[str, Any] = {}
        self.breakpoints: Set[str] = set()
        self.watch_expressions: List[str] = []
        self.execution_history: List[Dict] = []
        self.paused = False
        self.step_mode = False

    def add_to_history(self, node_id: str, node_type: str, status: str, data: Any = None):
        """Add execution entry to history."""
        self.execution_history.append({
            'timestamp': datetime.now().isoformat(),
            'node_id': node_id,
            'node_type': node_type,
            'status': status,
            'data': data,
            'variables': copy.deepcopy(self.variables)
        })


class WorkflowDebugger(tk.Frame):
    """Interactive workflow debugger."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#1e1e1e')
        self.workflow_data: Optional[Dict] = None
        self.debugger_state = DebuggerState()
        self.current_node_index = 0

        # Callbacks
        self.on_node_execute: Optional[callable] = kwargs.get('on_node_execute')

        self._build_ui()

    def _build_ui(self):
        """Build debugger UI."""
        # Toolbar
        toolbar = tk.Frame(self, bg='#1e1e1e', height=50)
        toolbar.pack(side='top', fill='x')

        # Execution controls
        tk.Button(toolbar, text='▶️ Run', command=self._run,
                 bg='#00C49F', fg='white').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='⏸️ Pause', command=self._pause,
                 bg='#FFBB28', fg='black').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='⏹️ Stop', command=self._stop,
                 bg='#FF8042', fg='white').pack(side='left', padx=5, pady=5)

        tk.Label(toolbar, text='|', bg='#1e1e1e', fg='#858585').pack(side='left', padx=5)

        # Step controls
        tk.Button(toolbar, text='⏭️ Step Over', command=self._step_over,
                 bg='#0088FE', fg='white').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='⏬ Step Into', command=self._step_into,
                 bg='#0088FE', fg='white').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='⏫ Step Out', command=self._step_out,
                 bg='#0088FE', fg='white').pack(side='left', padx=5, pady=5)

        tk.Label(toolbar, text='|', bg='#1e1e1e', fg='#858585').pack(side='left', padx=5)

        # Breakpoint controls
        tk.Button(toolbar, text='🔴 Toggle Breakpoint', command=self._toggle_breakpoint,
                 bg='#858585', fg='white').pack(side='left', padx=5, pady=5)
        tk.Button(toolbar, text='🗑️ Clear All Breakpoints', command=self._clear_breakpoints,
                 bg='#858585', fg='white').pack(side='left', padx=5, pady=5)

        # Status
        self.status_label = tk.Label(toolbar, text='Status: Stopped', bg='#1e1e1e',
                                     fg='#858585', font=('Arial', 9))
        self.status_label.pack(side='right', padx=10)

        # Main content (paned window)
        main_paned = ttk.PanedWindow(self, orient='horizontal')
        main_paned.pack(side='top', fill='both', expand=True, padx=5, pady=5)

        # Left panel - Workflow nodes
        left_panel = tk.Frame(main_paned, bg='#2d2d2d')
        main_paned.add(left_panel, weight=2)

        tk.Label(left_panel, text='Workflow Nodes', bg='#2d2d2d', fg='white',
                font=('Arial', 11, 'bold')).pack(pady=5)

        # Nodes list
        nodes_frame = tk.Frame(left_panel, bg='#2d2d2d')
        nodes_frame.pack(fill='both', expand=True, padx=10, pady=10)

        columns = ('ID', 'Type', 'Status', 'BP')
        self.nodes_tree = ttk.Treeview(nodes_frame, columns=columns, show='headings')

        for col in columns:
            self.nodes_tree.heading(col, text=col)
            width = 200 if col == 'ID' else 100
            self.nodes_tree.column(col, width=width)

        nodes_scrollbar = ttk.Scrollbar(nodes_frame, orient='vertical',
                                       command=self.nodes_tree.yview)
        self.nodes_tree.configure(yscrollcommand=nodes_scrollbar.set)

        self.nodes_tree.pack(side='left', fill='both', expand=True)
        nodes_scrollbar.pack(side='right', fill='y')

        # Configure tags for highlighting
        self.nodes_tree.tag_configure('current', background='#0088FE')
        self.nodes_tree.tag_configure('completed', background='#2d4a2d')
        self.nodes_tree.tag_configure('error', background='#4a2d2d')
        self.nodes_tree.tag_configure('breakpoint', foreground='#FF0000')

        # Right panel - Debug info
        right_panel = ttk.PanedWindow(main_paned, orient='vertical')
        main_paned.add(right_panel, weight=1)

        # Variables panel
        vars_frame = tk.LabelFrame(right_panel, text='Variables', bg='#2d2d2d',
                                  fg='white', font=('Arial', 10, 'bold'))
        right_panel.add(vars_frame, weight=1)

        vars_tree_frame = tk.Frame(vars_frame, bg='#2d2d2d')
        vars_tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.vars_tree = ttk.Treeview(vars_tree_frame, columns=('Variable', 'Value'),
                                     show='headings')
        self.vars_tree.heading('Variable', text='Variable')
        self.vars_tree.heading('Value', text='Value')
        self.vars_tree.column('Variable', width=150)
        self.vars_tree.column('Value', width=200)

        vars_scrollbar = ttk.Scrollbar(vars_tree_frame, orient='vertical',
                                      command=self.vars_tree.yview)
        self.vars_tree.configure(yscrollcommand=vars_scrollbar.set)

        self.vars_tree.pack(side='left', fill='both', expand=True)
        vars_scrollbar.pack(side='right', fill='y')

        # Call stack panel
        stack_frame = tk.LabelFrame(right_panel, text='Call Stack', bg='#2d2d2d',
                                   fg='white', font=('Arial', 10, 'bold'))
        right_panel.add(stack_frame, weight=1)

        self.stack_list = tk.Listbox(stack_frame, bg='#1e1e1e', fg='white',
                                     font=('Courier', 9))
        stack_scrollbar = ttk.Scrollbar(stack_frame, orient='vertical',
                                       command=self.stack_list.yview)
        self.stack_list.configure(yscrollcommand=stack_scrollbar.set)

        self.stack_list.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        stack_scrollbar.pack(side='right', fill='y', pady=10)

        # Watch expressions panel
        watch_frame = tk.LabelFrame(right_panel, text='Watch Expressions', bg='#2d2d2d',
                                   fg='white', font=('Arial', 10, 'bold'))
        right_panel.add(watch_frame, weight=1)

        watch_control_frame = tk.Frame(watch_frame, bg='#2d2d2d')
        watch_control_frame.pack(fill='x', padx=10, pady=5)

        self.watch_entry = tk.Entry(watch_control_frame, bg='#1e1e1e', fg='white',
                                    insertbackground='white')
        self.watch_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))

        tk.Button(watch_control_frame, text='Add', command=self._add_watch,
                 bg='#0088FE', fg='white').pack(side='left')

        self.watch_list = tk.Listbox(watch_frame, bg='#1e1e1e', fg='white',
                                     font=('Courier', 9))
        watch_scrollbar = ttk.Scrollbar(watch_frame, orient='vertical',
                                       command=self.watch_list.yview)
        self.watch_list.configure(yscrollcommand=watch_scrollbar.set)

        self.watch_list.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        watch_scrollbar.pack(side='right', fill='y', pady=10)

        # Execution history panel
        history_frame = tk.LabelFrame(right_panel, text='Execution History', bg='#2d2d2d',
                                     fg='white', font=('Arial', 10, 'bold'))
        right_panel.add(history_frame, weight=1)

        self.history_list = tk.Listbox(history_frame, bg='#1e1e1e', fg='white',
                                       font=('Courier', 9))
        history_scrollbar = ttk.Scrollbar(history_frame, orient='vertical',
                                         command=self.history_list.yview)
        self.history_list.configure(yscrollcommand=history_scrollbar.set)

        self.history_list.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        history_scrollbar.pack(side='right', fill='y', pady=10)

    def load_workflow(self, workflow_data: Dict):
        """Load workflow for debugging."""
        self.workflow_data = workflow_data
        self.debugger_state = DebuggerState()
        self.current_node_index = 0

        # Clear nodes tree
        for item in self.nodes_tree.get_children():
            self.nodes_tree.delete(item)

        # Load nodes
        if 'nodes' in workflow_data:
            for node in workflow_data['nodes']:
                node_id = node.get('id', 'unknown')
                node_type = node.get('type', 'unknown')
                bp_marker = '🔴' if node_id in self.debugger_state.breakpoints else ''

                self.nodes_tree.insert('', 'end', values=(
                    node_id,
                    node_type,
                    'Pending',
                    bp_marker
                ), tags=())

    def _run(self):
        """Run workflow (continue execution)."""
        if not self.workflow_data:
            messagebox.showwarning('No Workflow', 'Please load a workflow first')
            return

        self.debugger_state.paused = False
        self.debugger_state.step_mode = False
        self.status_label.config(text='Status: Running', fg='#00C49F')

        # Execute nodes
        self._execute_next_node()

    def _pause(self):
        """Pause execution."""
        self.debugger_state.paused = True
        self.status_label.config(text='Status: Paused', fg='#FFBB28')

    def _stop(self):
        """Stop execution."""
        self.debugger_state.paused = True
        self.current_node_index = 0
        self.status_label.config(text='Status: Stopped', fg='#858585')

        # Reset node statuses
        for item in self.nodes_tree.get_children():
            self.nodes_tree.item(item, tags=())
            values = list(self.nodes_tree.item(item, 'values'))
            values[2] = 'Pending'
            self.nodes_tree.item(item, values=values)

    def _step_over(self):
        """Step over (execute current node)."""
        self.debugger_state.step_mode = True
        self.debugger_state.paused = False
        self._execute_next_node()
        self.debugger_state.paused = True

    def _step_into(self):
        """Step into (execute current node and enter)."""
        # For now, same as step over
        self._step_over()

    def _step_out(self):
        """Step out (execute until current level completes)."""
        # For now, same as step over
        self._step_over()

    def _execute_next_node(self):
        """Execute next node in workflow."""
        if not self.workflow_data or 'nodes' not in self.workflow_data:
            return

        nodes = self.workflow_data['nodes']

        if self.current_node_index >= len(nodes):
            self.status_label.config(text='Status: Complete', fg='#00C49F')
            return

        # Get current node
        node = nodes[self.current_node_index]
        node_id = node.get('id', 'unknown')
        node_type = node.get('type', 'unknown')

        # Check if breakpoint
        if node_id in self.debugger_state.breakpoints and not self.debugger_state.step_mode:
            self.debugger_state.paused = True
            self.status_label.config(text=f'Status: Breakpoint at {node_id}', fg='#FF8042')
            messagebox.showinfo('Breakpoint', f'Breakpoint hit at node: {node_id}')

        # Update current node
        self.debugger_state.current_node_id = node_id

        # Update display
        self._highlight_current_node()

        # Execute node
        result = self._execute_node(node)

        # Update status
        status = 'Completed' if result else 'Error'
        self._update_node_status(self.current_node_index, status, 'completed' if result else 'error')

        # Add to history
        self.debugger_state.add_to_history(node_id, node_type, status, result)
        self._update_history_display()

        # Update stack
        self.debugger_state.execution_stack.append(node_id)
        self._update_stack_display()

        # Move to next node
        self.current_node_index += 1

        # Continue if not paused
        if not self.debugger_state.paused and not self.debugger_state.step_mode:
            self.after(500, self._execute_next_node)  # 500ms delay between nodes

    def _execute_node(self, node: Dict) -> Any:
        """Execute a single node."""
        node_type = node.get('type', 'unknown')
        node_config = node.get('config', {})

        # Simulate node execution
        result = {'status': 'success', 'output': f'Executed {node_type}'}

        # Update variables (simulate)
        if node_type == 'set_variable':
            var_name = node_config.get('variable', 'result')
            var_value = node_config.get('value', 'test_value')
            self.debugger_state.variables[var_name] = var_value

        # Update variables display
        self._update_variables_display()

        # Evaluate watch expressions
        self._update_watch_display()

        # Call callback if provided
        if self.on_node_execute:
            self.on_node_execute(node)

        return result

    def _highlight_current_node(self):
        """Highlight current node being executed."""
        # Remove previous highlight
        for item in self.nodes_tree.get_children():
            tags = list(self.nodes_tree.item(item, 'tags'))
            if 'current' in tags:
                tags.remove('current')
                self.nodes_tree.item(item, tags=tags)

        # Add current highlight
        if self.current_node_index < len(self.nodes_tree.get_children()):
            items = self.nodes_tree.get_children()
            item = items[self.current_node_index]
            tags = list(self.nodes_tree.item(item, 'tags'))
            tags.append('current')
            self.nodes_tree.item(item, tags=tags)

            # Scroll to current item
            self.nodes_tree.see(item)

    def _update_node_status(self, index: int, status: str, tag: str):
        """Update node status in tree."""
        items = self.nodes_tree.get_children()
        if index < len(items):
            item = items[index]
            values = list(self.nodes_tree.item(item, 'values'))
            values[2] = status
            self.nodes_tree.item(item, values=values)

            # Add tag
            tags = list(self.nodes_tree.item(item, 'tags'))
            if tag not in tags:
                tags.append(tag)
            self.nodes_tree.item(item, tags=tags)

    def _update_variables_display(self):
        """Update variables display."""
        for item in self.vars_tree.get_children():
            self.vars_tree.delete(item)

        for var_name, var_value in self.debugger_state.variables.items():
            self.vars_tree.insert('', 'end', values=(var_name, str(var_value)))

    def _update_stack_display(self):
        """Update call stack display."""
        self.stack_list.delete(0, 'end')

        for i, node_id in enumerate(reversed(self.debugger_state.execution_stack)):
            self.stack_list.insert('end', f"#{len(self.debugger_state.execution_stack) - i}: {node_id}")

    def _update_history_display(self):
        """Update execution history display."""
        self.history_list.delete(0, 'end')

        for entry in reversed(self.debugger_state.execution_history[-50:]):  # Last 50
            timestamp = entry['timestamp'].split('T')[1][:8]  # Time only
            text = f"[{timestamp}] {entry['node_id']}: {entry['status']}"
            self.history_list.insert('end', text)

    def _toggle_breakpoint(self):
        """Toggle breakpoint on selected node."""
        selection = self.nodes_tree.selection()
        if not selection:
            messagebox.showwarning('No Selection', 'Please select a node')
            return

        item = selection[0]
        values = list(self.nodes_tree.item(item, 'values'))
        node_id = values[0]

        if node_id in self.debugger_state.breakpoints:
            self.debugger_state.breakpoints.remove(node_id)
            values[3] = ''
            tags = [t for t in self.nodes_tree.item(item, 'tags') if t != 'breakpoint']
        else:
            self.debugger_state.breakpoints.add(node_id)
            values[3] = '🔴'
            tags = list(self.nodes_tree.item(item, 'tags'))
            tags.append('breakpoint')

        self.nodes_tree.item(item, values=values, tags=tags)

    def _clear_breakpoints(self):
        """Clear all breakpoints."""
        self.debugger_state.breakpoints.clear()

        for item in self.nodes_tree.get_children():
            values = list(self.nodes_tree.item(item, 'values'))
            values[3] = ''
            tags = [t for t in self.nodes_tree.item(item, 'tags') if t != 'breakpoint']
            self.nodes_tree.item(item, values=values, tags=tags)

    def _add_watch(self):
        """Add watch expression."""
        expression = self.watch_entry.get().strip()
        if expression:
            self.debugger_state.watch_expressions.append(expression)
            self.watch_entry.delete(0, 'end')
            self._update_watch_display()

    def _update_watch_display(self):
        """Update watch expressions display."""
        self.watch_list.delete(0, 'end')

        for expr in self.debugger_state.watch_expressions:
            # Try to evaluate expression
            try:
                # Simple variable lookup
                if expr in self.debugger_state.variables:
                    value = self.debugger_state.variables[expr]
                    self.watch_list.insert('end', f"{expr} = {value}")
                else:
                    self.watch_list.insert('end', f"{expr} = <undefined>")
            except Exception as e:
                self.watch_list.insert('end', f"{expr} = <error>")


# Demo/Test
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Workflow Debugger - E3 Demo')
    root.geometry('1200x800')

    debugger = WorkflowDebugger(root)
    debugger.pack(fill='both', expand=True)

    # Load sample workflow
    sample_workflow = {
        'name': 'Test Workflow',
        'nodes': [
            {'id': 'node_1', 'type': 'start', 'config': {}},
            {'id': 'node_2', 'type': 'set_variable', 'config': {'variable': 'count', 'value': 10}},
            {'id': 'node_3', 'type': 'process', 'config': {}},
            {'id': 'node_4', 'type': 'decision', 'config': {}},
            {'id': 'node_5', 'type': 'end', 'config': {}}
        ]
    }

    debugger.load_workflow(sample_workflow)

    root.mainloop()
