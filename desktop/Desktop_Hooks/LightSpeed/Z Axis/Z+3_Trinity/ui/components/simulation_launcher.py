"""
LightSpeed V0.9.5 - Physics Simulation Launcher Component
Universal launcher for Raphael physics simulations

Features:
- Auto-discover physics simulation modules
- Dynamic parameter input forms
- Real-time execution with progress
- Result visualization
- Export functionality

Author: LightSpeed Team
Version: 0.9.5
Date: January 3, 2026
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, List, Callable, Optional
import sys
from pathlib import Path
import importlib.util
import inspect
import threading
import json

from .layered_card import LayeredCard
from .loading import ProgressBar, LoadingSpinner
from .charts import ChartCard


class SimulationInfo:
    """Metadata for a physics simulation"""

    def __init__(self, name: str, module_path: Path, description: str = ""):
        self.name = name
        self.module_path = module_path
        self.description = description
        self.parameters = {}
        self.module = None

    def load_module(self):
        """Load the simulation module dynamically"""
        if self.module:
            return self.module

        try:
            spec = importlib.util.spec_from_file_location(self.name, self.module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.module = module
                return module
        except Exception as e:
            print(f"[SimulationLauncher] Failed to load {self.name}: {e}")
            return None

    def get_callable_functions(self) -> List[str]:
        """Get list of callable simulation functions"""
        if not self.module:
            self.load_module()

        if not self.module:
            return []

        functions = []
        for name, obj in inspect.getmembers(self.module):
            if inspect.isfunction(obj) and not name.startswith('_'):
                functions.append(name)
        return functions


class SimulationLauncher(LayeredCard):
    """
    Universal physics simulation launcher.

    Discovers and runs Raphael physics simulations with GUI.
    """

    def __init__(self, parent, **kwargs):
        """Initialize simulation launcher"""
        super().__init__(
            parent,
            title="🔬 Physics Simulation Launcher",
            subtitle="Raphael Theory of Everything Engine",
            height=500,
            elevation=3,
            **kwargs
        )

        self.simulations: Dict[str, SimulationInfo] = {}
        self.current_simulation: Optional[SimulationInfo] = None
        self.current_function: Optional[str] = None
        self.results: Optional[Any] = None

        # Add header buttons
        self.add_header_button("Discover Simulations", self._discover_simulations, 'primary')
        self.add_header_button("Export Results", self._export_results, 'secondary')

        # Build UI
        self._build_launcher_ui()

        # Auto-discover on init
        self._discover_simulations()

    def _build_launcher_ui(self):
        """Build launcher interface"""
        # Main container with notebook
        self.notebook = ttk.Notebook(self.content)
        self.notebook.pack(fill='both', expand=True)

        # Tab 1: Simulation Browser
        self.browser_tab = tk.Frame(self.notebook, bg='#0A1628')
        self.notebook.add(self.browser_tab, text="Browse")
        self._build_browser_tab()

        # Tab 2: Parameter Input
        self.params_tab = tk.Frame(self.notebook, bg='#0A1628')
        self.notebook.add(self.params_tab, text="Parameters")
        self._build_params_tab()

        # Tab 3: Results
        self.results_tab = tk.Frame(self.notebook, bg='#0A1628')
        self.notebook.add(self.results_tab, text="Results")
        self._build_results_tab()

    def _build_browser_tab(self):
        """Build simulation browser"""
        # Simulation list
        list_frame = tk.Frame(self.browser_tab, bg='#0A1628')
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')

        self.sim_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            bg='#0F1F35',
            fg='#FFFFFF',
            selectbackground='#1E3A5F',
            selectforeground='#00FFFF',
            font=('Segoe UI', 10),
            relief='flat'
        )
        self.sim_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.sim_listbox.yview)

        self.sim_listbox.bind('<<ListboxSelect>>', self._on_simulation_select)

        # Info panel
        info_frame = tk.Frame(self.browser_tab, bg='#102040', relief='solid', bd=1)
        info_frame.pack(fill='x', padx=10, pady=(0, 10))

        self.info_label = tk.Label(
            info_frame,
            text="Select a simulation to view details",
            bg='#102040',
            fg='#88CCFF',
            font=('Segoe UI', 9),
            anchor='w',
            justify='left',
            wraplength=400
        )
        self.info_label.pack(padx=10, pady=10)

    def _build_params_tab(self):
        """Build parameter input form"""
        # Function selector
        func_frame = tk.Frame(self.params_tab, bg='#0A1628')
        func_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(
            func_frame,
            text="Simulation Function:",
            bg='#0A1628',
            fg='#88CCFF',
            font=('Segoe UI', 10)
        ).pack(side='left', padx=5)

        self.func_var = tk.StringVar()
        self.func_combo = ttk.Combobox(
            func_frame,
            textvariable=self.func_var,
            state='readonly',
            width=30
        )
        self.func_combo.pack(side='left', padx=5)
        self.func_combo.bind('<<ComboboxSelected>>', self._on_function_select)

        # Parameter input area (scrollable)
        param_container = tk.Frame(self.params_tab, bg='#0A1628')
        param_container.pack(fill='both', expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(param_container)
        scrollbar.pack(side='right', fill='y')

        canvas = tk.Canvas(param_container, bg='#0A1628', yscrollcommand=scrollbar.set, highlightthickness=0)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=canvas.yview)

        self.param_frame = tk.Frame(canvas, bg='#0A1628')
        canvas.create_window((0, 0), window=self.param_frame, anchor='nw')

        self.param_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        self.param_entries = {}

        # Run button
        tk.Button(
            self.params_tab,
            text="▶ Run Simulation",
            command=self._run_simulation,
            bg='#00AA00',
            fg='#FFFFFF',
            font=('Segoe UI', 11, 'bold'),
            relief='flat',
            padx=20,
            pady=10
        ).pack(pady=10)

    def _build_results_tab(self):
        """Build results display"""
        # Results display area
        self.results_text = tk.Text(
            self.results_tab,
            bg='#0F1F35',
            fg='#FFFFFF',
            font=('Consolas', 9),
            relief='flat',
            wrap='word'
        )
        self.results_text.pack(fill='both', expand=True, padx=10, pady=10)

    def _discover_simulations(self):
        """Discover all available physics simulations"""
        # Clear existing
        self.simulations.clear()
        self.sim_listbox.delete(0, 'end')

        # Get Raphael physics path
        physics_path = Path(__file__).parents[3] / "physics" / "raphael"

        if not physics_path.exists():
            self.info_label.config(text="Raphael physics directory not found")
            return

        # Scan for .py files
        discovered = 0
        for py_file in physics_path.rglob("*.py"):
            # Skip __init__, __pycache__, .venv
            if (py_file.name.startswith('__') or
                '.venv' in str(py_file) or
                '__pycache__' in str(py_file)):
                continue

            sim_name = py_file.stem
            sim_info = SimulationInfo(
                name=sim_name,
                module_path=py_file,
                description=f"Physics simulation: {sim_name}"
            )

            self.simulations[sim_name] = sim_info
            self.sim_listbox.insert('end', f"🔬 {sim_name}")
            discovered += 1

        # Also add built-in raphael.py simulations
        raphael_main = physics_path.parent / "raphael.py"
        if raphael_main.exists():
            sim_info = SimulationInfo(
                name="raphael_main",
                module_path=raphael_main,
                description="Main Raphael physics engine (wavefunction, light reflectivity)"
            )
            self.simulations["raphael_main"] = sim_info
            self.sim_listbox.insert('end', "🔬 raphael_main")
            discovered += 1

        self.info_label.config(text=f"Discovered {discovered} physics simulation(s)")

    def _on_simulation_select(self, event):
        """Handle simulation selection"""
        selection = self.sim_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        sim_name = self.sim_listbox.get(idx).replace('🔬 ', '')

        if sim_name not in self.simulations:
            return

        self.current_simulation = self.simulations[sim_name]

        # Load module and get functions
        self.current_simulation.load_module()
        functions = self.current_simulation.get_callable_functions()

        # Update info
        info_text = f"Simulation: {sim_name}\n"
        info_text += f"Path: {self.current_simulation.module_path}\n"
        info_text += f"Functions: {len(functions)}\n"
        info_text += f"Available: {', '.join(functions[:5])}"
        if len(functions) > 5:
            info_text += f", ... ({len(functions)-5} more)"

        self.info_label.config(text=info_text)

        # Update function selector
        self.func_combo['values'] = functions
        if functions:
            self.func_var.set(functions[0])
            self._on_function_select(None)

    def _on_function_select(self, event):
        """Handle function selection"""
        func_name = self.func_var.get()
        if not func_name or not self.current_simulation or not self.current_simulation.module:
            return

        self.current_function = func_name

        # Get function signature
        try:
            func = getattr(self.current_simulation.module, func_name)
            sig = inspect.signature(func)

            # Clear existing parameter inputs
            for widget in self.param_frame.winfo_children():
                widget.destroy()
            self.param_entries.clear()

            # Create input for each parameter
            row = 0
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue

                # Label
                tk.Label(
                    self.param_frame,
                    text=f"{param_name}:",
                    bg='#0A1628',
                    fg='#88CCFF',
                    font=('Segoe UI', 9)
                ).grid(row=row, column=0, sticky='w', padx=5, pady=5)

                # Entry
                entry = tk.Entry(
                    self.param_frame,
                    bg='#0F1F35',
                    fg='#FFFFFF',
                    font=('Segoe UI', 9),
                    width=30
                )
                entry.grid(row=row, column=1, padx=5, pady=5)

                # Default value if available
                if param.default != inspect.Parameter.empty:
                    entry.insert(0, str(param.default))

                self.param_entries[param_name] = entry
                row += 1

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load function signature: {e}")

    def _run_simulation(self):
        """Run the selected simulation"""
        if not self.current_simulation or not self.current_function:
            messagebox.showwarning("No Selection", "Please select a simulation and function")
            return

        # Get parameter values
        params = {}
        for param_name, entry in self.param_entries.items():
            value_str = entry.get()
            if not value_str:
                continue

            # Try to parse value
            try:
                # Try numeric first
                if '.' in value_str:
                    params[param_name] = float(value_str)
                else:
                    params[param_name] = int(value_str)
            except ValueError:
                # String or tuple/list
                if value_str.startswith('(') or value_str.startswith('['):
                    try:
                        params[param_name] = eval(value_str)
                    except:
                        params[param_name] = value_str
                else:
                    params[param_name] = value_str

        # Run simulation in thread
        def run_thread():
            try:
                func = getattr(self.current_simulation.module, self.current_function)
                result = func(**params)
                self.results = result

                # Display results
                self.after(0, lambda: self._display_results(result))

            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Simulation Error", str(e)))

        threading.Thread(target=run_thread, daemon=True).start()

        # Switch to results tab
        self.notebook.select(self.results_tab)
        self.results_text.delete('1.0', 'end')
        self.results_text.insert('end', "⏳ Running simulation...\n\n")

    def _display_results(self, result):
        """Display simulation results"""
        self.results_text.delete('1.0', 'end')

        # Format results
        output = f"=== Simulation Results ===\n\n"
        output += f"Simulation: {self.current_simulation.name}\n"
        output += f"Function: {self.current_function}\n\n"
        output += f"Results:\n"
        output += "-" * 50 + "\n"

        if hasattr(result, '__dict__'):
            # Dataclass or object
            for key, value in result.__dict__.items():
                output += f"{key}: {value}\n"
        elif isinstance(result, dict):
            for key, value in result.items():
                output += f"{key}: {value}\n"
        elif isinstance(result, (list, tuple)):
            for i, item in enumerate(result):
                output += f"[{i}]: {item}\n"
        else:
            output += str(result)

        self.results_text.insert('end', output)

        messagebox.showinfo("Complete", "Simulation completed successfully!")

    def _export_results(self):
        """Export results to file"""
        if not self.results:
            messagebox.showwarning("No Results", "Run a simulation first")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Text", "*.txt"), ("All Files", "*.*")]
        )

        if not filename:
            return

        try:
            # Convert results to dict
            if hasattr(self.results, '__dict__'):
                data = self.results.__dict__
            elif isinstance(self.results, dict):
                data = self.results
            else:
                data = {"result": str(self.results)}

            # Add metadata
            export_data = {
                "simulation": self.current_simulation.name,
                "function": self.current_function,
                "results": data
            }

            if filename.endswith('.json'):
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
            else:
                with open(filename, 'w') as f:
                    f.write(self.results_text.get('1.0', 'end'))

            messagebox.showinfo("Exported", f"Results exported to {filename}")

        except Exception as e:
            messagebox.showerror("Export Error", str(e))


# Export
__all__ = ['SimulationLauncher', 'SimulationInfo']
