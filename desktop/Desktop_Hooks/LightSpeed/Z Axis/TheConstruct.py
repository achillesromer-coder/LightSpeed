#!/usr/bin/env python
"""
TheConstruct (Z0) - Physics & Simulation Floor
Complete Floor Coordinator with 3D Rendering, Physics, and Visualization

The Construct is THE primary simulation environment. It holds:
- All 3D rendering (immersive engine)
- Physics simulations (Raphael engine)
- Scientific calculations (12+ physics formulas)
- Physical constants (CODATA 2018)
- 3D object management

Variables Held:
- camera_position: (x, y, z, yaw, pitch)
- physics_state: {gravity, velocities, forces}
- simulation_results: Active calculation results
- 3d_objects: All interactive 3D objects
- active_calculations: Running simulations

Renders:
- 3D environment (WASD navigation)
- Physics graphs and visualizations
- Calculator interfaces
- Simulation dashboards
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Optional, Dict, List, Any
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os


def _load_symbol(rel_path: str, symbol: str):
    """Load a symbol (class/function) from a file by relative path"""
    root = Path(__file__).resolve().parents[1]
    path = (root / rel_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    mod_name = f"lightspeed_dynamic_{path.stem}_{abs(hash(str(path)))%1_000_000}"
    spec = spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    mod = module_from_spec(spec)
    # Ensure dataclasses/type evaluation can resolve __module__ via sys.modules.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    if not hasattr(mod, symbol):
        raise AttributeError(f"{symbol} not found in {path}")
    return getattr(mod, symbol)


# Backwards compatibility
_load_class = _load_symbol


class TheConstructFloorState:
    """
    State manager for TheConstruct floor

    This class holds all state variables for the physics/simulation floor
    """

    def __init__(self):
        # Physics simulation state
        self.gravity = 9.8  # m/s²
        self.active_simulations: List[Dict[str, Any]] = []
        self.simulation_results: Dict[str, Any] = {}

        # Constants library loaded flag
        self.constants_loaded = False
        self.physical_constants: Dict[str, float] = {}

        # Calculator state
        self.active_calculator: Optional[str] = None
        self.last_calculations: List[Dict] = []

        # 3D engine state (if running)
        self.immersive_active = False
        self.camera_position = {'x': 0.0, 'y': 5.0, 'z': -18.0}
        self.camera_rotation = {'yaw': 0.0, 'pitch': 0.0}

    def add_calculation(self, calc_type: str, inputs: Dict, result: Any):
        """Record a calculation"""
        self.last_calculations.append({
            'type': calc_type,
            'inputs': inputs,
            'result': result
        })
        if len(self.last_calculations) > 100:
            self.last_calculations.pop(0)


class TheConstructUI(ttk.Frame):
    """Primary Construct UI - Physics, Simulations, 3D Rendering"""

    def __init__(self, parent: tk.Misc, app: Optional[object] = None, *, compact: bool = False, **_ignored):
        super().__init__(parent)
        self.app = app
        self.compact = bool(compact)
        self.state = TheConstructFloorState()
        self.shell_bridge = getattr(app, "trinity_shell_bridge", None)

        # Services
        try:
            from core.services import get_db, get_event_bus, get_storage
            self.db = getattr(app, "db", None) or get_db()
            self.event_bus = getattr(app, "event_bus", None) or get_event_bus()
            self.storage = getattr(app, "storage", None) or get_storage()
        except Exception:
            self.db = None
            self.event_bus = None
            self.storage = None

        # Register with Bento system
        self._register_bento_widgets()

        # Build UI
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Tabs
        self._tabs: Dict[str, ttk.Frame] = {}
        self._builders: Dict[str, Any] = {}
        self._tab_group: Dict[str, str] = {}
        self._tab_container: Dict[str, Any] = {}
        self._group_frames: Dict[str, ttk.Frame] = {}

        if self.compact:
            self._build_compact_shell()
        else:
            self._build_full_shell()

    def _build_full_shell(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self._register_tab("Dashboard", self._build_dashboard)
        self._register_tab("Physics Calculators", self._build_calculators)
        self._register_tab("3D Immersive", self._build_3d_launcher)
        self._register_tab("Z Direct Registry", self._build_z_direct_registry)

        self._ensure_built("Dashboard")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _build_compact_shell(self) -> None:
        """
        Compact embedding for IT Portal:
        - Dashboard (single surface)
        - Tools (calculators + 3D launcher)
        - Registry (Z Direct)
        """
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        dash_group = ttk.Frame(self.notebook)
        tools_group = ttk.Frame(self.notebook)
        reg_group = ttk.Frame(self.notebook)

        self.notebook.add(dash_group, text="Dashboard")
        self.notebook.add(tools_group, text="Tools")
        self.notebook.add(reg_group, text="Registry")

        self._group_frames = {
            "Dashboard": dash_group,
            "Tools": tools_group,
            "Registry": reg_group,
        }

        self._tabs["Dashboard"] = dash_group
        self._builders["Dashboard"] = self._build_dashboard
        self._tab_group["Dashboard"] = "Dashboard"
        self._tab_container["Dashboard"] = None

        tools_nb = ttk.Notebook(tools_group)
        tools_nb.pack(fill="both", expand=True)
        self._register_tab("Physics Calculators", self._build_calculators, notebook=tools_nb, group="Tools")
        self._register_tab("3D Immersive", self._build_3d_launcher, notebook=tools_nb, group="Tools")

        reg_nb = ttk.Notebook(reg_group)
        reg_nb.pack(fill="both", expand=True)
        self._register_tab("Z Direct Registry", self._build_z_direct_registry, notebook=reg_nb, group="Registry")

        self._ensure_built("Dashboard")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_group_tab_changed)
        tools_nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        reg_nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _register_tab(self, title: str, builder, *, notebook: Optional[ttk.Notebook] = None, group: str = "Dashboard"):
        """Register a lazy-loaded tab (supports nested notebooks in compact mode)."""
        nb = notebook or self.notebook
        frame = ttk.Frame(nb)
        nb.add(frame, text=title)
        self._tabs[title] = frame
        self._builders[title] = builder
        self._tab_group[title] = group
        self._tab_container[title] = nb

    def _ensure_built(self, title: str):
        """Ensure tab is built"""
        frame = self._tabs.get(title)
        builder = self._builders.get(title)
        if frame is None or builder is None:
            return
        if getattr(frame, "_built", False):
            return
        builder(frame)
        setattr(frame, "_built", True)

    def _on_tab_changed(self, event):
        """Handle tab change - lazy load content"""
        try:
            nb = getattr(event, "widget", None) or self.notebook
            current_tab = nb.select()
            tab_text = nb.tab(current_tab, "text")
            self._ensure_built(tab_text)
        except Exception:
            return

    def _on_group_tab_changed(self, _event):
        """When switching compact groups, ensure the visible leaf is built."""
        try:
            group = self.notebook.tab(self.notebook.select(), "text")
        except Exception:
            return
        if group == "Dashboard":
            self._ensure_built("Dashboard")
            return
        try:
            grp_frame = self._group_frames.get(group)
            if grp_frame is None:
                return
            children = [w for w in grp_frame.winfo_children() if isinstance(w, ttk.Notebook)]
            if not children:
                return
            nb = children[0]
            leaf = nb.tab(nb.select(), "text")
            self._ensure_built(leaf)
        except Exception:
            return

    def select_tab(self, title: str) -> None:
        """Select a leaf tab by title, regardless of compact/full shell."""
        if title not in self._tabs:
            return
        if not self.compact:
            try:
                self.notebook.select(self._tabs[title])
            except Exception:
                pass
            self._ensure_built(title)
            return
        group = self._tab_group.get(title) or "Dashboard"
        try:
            self.notebook.select(self._group_frames[group])
        except Exception:
            pass
        if group == "Dashboard":
            self._ensure_built("Dashboard")
            return
        nb = self._tab_container.get(title)
        if nb is not None:
            try:
                nb.select(self._tabs[title])
            except Exception:
                pass
        self._ensure_built(title)

    def _build_z_direct_registry(self, parent: ttk.Frame):
        """
        Z Direct Registry (TheConstruct): browse committed objects for interactability.

        Trinity is the approval gate for commits; this view reads the durable registry:
        `Z Axis/Z0_TheConstruct/Z Direct/objects.json`.
        """
        ttk.Label(parent, text="Z Direct Registry (Committed Objects)", font=("Consolas", 14, "bold")).pack(pady=10)

        try:
            from core.services import get_z_direct  # type: ignore
            z_direct = get_z_direct()
        except Exception as e:
            ttk.Label(parent, text=f"Z Direct unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )
            return

        outer = ttk.Frame(parent)
        outer.pack(fill="both", expand=True, padx=10, pady=10)
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=2)
        outer.rowconfigure(0, weight=1)

        left = ttk.Frame(outer)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        right = ttk.Frame(outer)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        listbox = tk.Listbox(left, height=20, font=("Consolas", 10))
        listbox.pack(fill="both", expand=True)

        details = tk.Text(right, wrap="word", font=("Consolas", 10))
        details.pack(fill="both", expand=True)

        btns = ttk.Frame(parent)
        btns.pack(fill="x", padx=10, pady=(0, 10))

        state: Dict[str, Any] = {"items": []}

        def _render_details(item: Any) -> None:
            try:
                details.delete("1.0", "end")
            except Exception:
                pass
            try:
                details.insert("1.0", json.dumps(item, indent=2, ensure_ascii=True))
            except Exception:
                details.insert("1.0", str(item))

        def _load() -> None:
            try:
                items = z_direct.read_registry("Z0", name="objects")
            except Exception:
                items = []
            state["items"] = items or []
            listbox.delete(0, "end")
            for it in state["items"]:
                if not isinstance(it, dict):
                    listbox.insert("end", str(it))
                    continue
                kind = it.get("kind") or "object"
                oid = it.get("id") or ""
                title = it.get("title") or it.get("name") or ""
                listbox.insert("end", f"{kind} {oid} {title}".strip())
            _render_details({"count": len(state["items"]), "channel": "Z0"})

        def _open_selected() -> None:
            try:
                sel = listbox.curselection()
                if not sel:
                    messagebox.showwarning("Registry", "Select an item first.", parent=self.winfo_toplevel())
                    return
                it = state["items"][int(sel[0])]
                if not isinstance(it, dict):
                    messagebox.showwarning("Registry", "Invalid item selection.", parent=self.winfo_toplevel())
                    return
                p = it.get("path") or it.get("source_path")
                if not isinstance(p, str) or not p.strip():
                    messagebox.showwarning("Registry", "No file path on this object.", parent=self.winfo_toplevel())
                    return
                fp = Path(p)
                if not fp.exists():
                    messagebox.showwarning("Registry", f"File not found:\n{fp}", parent=self.winfo_toplevel())
                    return
                os.startfile(str(fp))  # type: ignore[attr-defined]
            except Exception as e:
                messagebox.showerror("Registry", f"Open failed:\n{e}", parent=self.winfo_toplevel())

        def _on_select(_evt=None) -> None:
            try:
                sel = listbox.curselection()
                if not sel:
                    return
                it = state["items"][int(sel[0])]
                _render_details(it)
            except Exception:
                return

        ttk.Button(btns, text="Refresh", command=_load).pack(side="left")
        ttk.Button(btns, text="Open File", command=_open_selected).pack(side="left", padx=(8, 0))

        listbox.bind("<<ListboxSelect>>", _on_select)
        _load()

    def _register_bento_widgets(self):
        """Register TheConstruct widgets with Bento system"""
        try:
            import sys
            trinity_path = Path(__file__).parent / "Z+3_Trinity"
            if str(trinity_path) not in sys.path:
                sys.path.insert(0, str(trinity_path))

            from ui.universal_bento_system import register_floor_widgets, BentoWidget, BentoWidgetType

            widgets = [
                BentoWidget(
                    id="construct_raphael_full",
                    title="Raphael Engine",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z0_TheConstruct",
                    callback=lambda w: self._launch_raphael(),
                    config={"icon": "⚛️", "description": "Full physics engine"}
                ),
                BentoWidget(
                    id="construct_3d_launcher",
                    title="3D Environment",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z0_TheConstruct",
                    callback=lambda w: self._launch_3d_immersive(),
                    config={"icon": "🌌", "description": "Launch immersive 3D"}
                )
            ]

            register_floor_widgets("Z0_TheConstruct", widgets)
            print("[TheConstruct] Registered additional Bento widgets")
        except Exception as e:
            print(f"[TheConstruct] Could not register Bento widgets: {e}")

    def _build_dashboard(self, parent: ttk.Frame):
        """Build dashboard tab"""
        try:
            from core.ui.base_portal_glass import mount_smart_ops_strip  # type: ignore

            mount_smart_ops_strip(parent, app=self.app, floor_channel="Z0", it_portal=self.compact, title="Construct Ops")
        except Exception:
            pass
        actions = ttk.Frame(parent)
        actions.pack(fill="x", padx=12, pady=(0, 10))
        ttk.Label(
            actions,
            text="Primary Construct workbench: use the dashboard as the floor home, then launch tools on demand.",
            justify="left",
        ).pack(side="left", padx=(0, 12))
        ttk.Button(actions, text="Physics Tools", command=lambda: self.select_tab("Physics Calculators")).pack(side="left")
        ttk.Button(actions, text="Immersive", command=lambda: self.select_tab("3D Immersive")).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Registry", command=lambda: self.select_tab("Z Direct Registry")).pack(side="left", padx=(8, 0))
        try:
            Dashboard = _load_class("Z Axis/Z0_TheConstruct/components/construct_dashboard_glass.py", "ConstructDashboardGlass")
            ui = Dashboard(parent)
            ui.pack(fill="both", expand=True)
        except Exception as e:
            ttk.Label(parent, text=f"Construct dashboard unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )
        try:
            from lightspeed_runtime.desktop_adapters import mount_construct_scenario_lab

            mount_construct_scenario_lab(parent, self.app)
        except Exception:
            pass
        try:
            from lightspeed_runtime.desktop_adapters import build_construct_runtime_panel

            panel = build_construct_runtime_panel(parent, self.app)
            if panel is not None:
                panel.pack(fill="x", padx=12, pady=(0, 10))
        except Exception:
            pass

    def _build_calculators(self, parent: ttk.Frame):
        """Build physics calculators tab"""
        # Load the calculator registry from the Construct floor (file-path load avoids invalid package names).
        try:
            calculators = _load_symbol("Z Axis/Z0_TheConstruct/physics_calculators.py", "PHYSICS_CALCULATORS")
        except Exception as e:
            ttk.Label(parent, text=f"Physics calculators unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )
            return

        import inspect
        import json
        from dataclasses import asdict, is_dataclass

        root = ttk.Frame(parent)
        root.pack(fill="both", expand=True, padx=12, pady=12)

        # Left: calculator list
        left = ttk.Frame(root)
        left.pack(side="left", fill="y")

        ttk.Label(left, text="Calculators", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 6))
        filter_var = tk.StringVar(value="")
        ttk.Entry(left, textvariable=filter_var).pack(fill="x", pady=(0, 8))

        tree = ttk.Treeview(left, columns=("id",), show="tree")
        tree.pack(fill="y", expand=True)

        # Right: form + output
        right = ttk.Frame(root)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))

        form = ttk.LabelFrame(right, text="Inputs", padding=10)
        form.pack(fill="x")

        out = ttk.LabelFrame(right, text="Result", padding=10)
        out.pack(fill="both", expand=True, pady=(10, 0))

        output = tk.Text(out, height=12, wrap="word")
        output.pack(fill="both", expand=True)
        output.configure(state="disabled")

        selected_name = tk.StringVar(value="")
        inputs: Dict[str, tk.StringVar] = {}
        input_widgets: List[tk.Widget] = []

        def _clear_form():
            for w in input_widgets:
                try:
                    w.destroy()
                except Exception:
                    pass
            input_widgets.clear()
            inputs.clear()

        def _set_output(text: str):
            try:
                output.configure(state="normal")
                output.delete("1.0", "end")
                output.insert("end", text.rstrip() + "\n")
                output.configure(state="disabled")
            except Exception:
                pass

        def _populate_list():
            tree.delete(*tree.get_children())
            q = (filter_var.get() or "").strip().lower()
            for key in sorted(calculators.keys()):
                if q and q not in key.lower():
                    continue
                tree.insert("", "end", text=key)

        def _select_calc(name: str):
            fn = calculators.get(name)
            if fn is None:
                return
            selected_name.set(name)
            _clear_form()

            sig = inspect.signature(fn)
            row = 0
            for param_name, param in sig.parameters.items():
                if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                    continue

                label = ttk.Label(form, text=param_name)
                label.grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
                input_widgets.append(label)

                var = tk.StringVar(value="" if param.default is inspect._empty else str(param.default))
                ent = ttk.Entry(form, textvariable=var, width=28)
                ent.grid(row=row, column=1, sticky="ew", pady=4)
                input_widgets.append(ent)
                inputs[param_name] = var
                row += 1

            form.columnconfigure(1, weight=1)
            _set_output(f"Selected: {name}\nEnter inputs and click Run.\n")

        def _run():
            name = selected_name.get().strip()
            fn = calculators.get(name)
            if fn is None:
                _set_output("No calculator selected.\n")
                return

            # Parse inputs based on annotations (int/float), fall back to float.
            sig = inspect.signature(fn)
            parsed = {}
            for param_name, param in sig.parameters.items():
                if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                    continue
                raw = (inputs.get(param_name).get() if param_name in inputs else "").strip()
                if raw == "" and param.default is not inspect._empty:
                    raw = str(param.default)
                if raw == "":
                    raise ValueError(f"Missing required input: {param_name}")
                ann = param.annotation
                if ann is int:
                    parsed[param_name] = int(float(raw))
                else:
                    parsed[param_name] = float(raw)

            res = fn(**parsed)
            self.state.add_calculation(name, parsed, res)

            # Emit event for cross-floor pipelines (Oracle/Morpheus ingestion can subscribe).
            try:
                if self.event_bus is not None:
                    payload = {"calculator": name, "inputs": parsed}
                    if is_dataclass(res):
                        payload["result"] = asdict(res)
                    else:
                        payload["result"] = getattr(res, "__dict__", res)
                    self.event_bus.publish("construct.physics_calculation", payload)
            except Exception:
                pass

            if is_dataclass(res):
                data = asdict(res)
                pretty = json.dumps(data, indent=2, ensure_ascii=False)
                _set_output(pretty)
            else:
                _set_output(str(res))

        def _on_select(_evt=None):
            sel = tree.selection()
            if not sel:
                return
            item = sel[0]
            name = tree.item(item, "text")
            if name:
                _select_calc(name)

        tree.bind("<<TreeviewSelect>>", _on_select)
        filter_var.trace_add("write", lambda *_: _populate_list())

        actions = ttk.Frame(right)
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="Run", command=lambda: _run()).pack(side="left")
        ttk.Button(actions, text="Clear", command=lambda: _set_output("")).pack(side="left", padx=(8, 0))

        _populate_list()

    def _build_3d_launcher(self, parent: ttk.Frame):
        """Build 3D immersive launcher tab"""
        runtime_summary = tk.Text(parent, height=10, wrap="word", font=("Consolas", 9))
        runtime_summary.pack(fill="x", padx=12, pady=(0, 12))

        def _refresh_runtime_profile() -> None:
            try:
                load_profile = _load_symbol(
                    "Z Axis/Z0_TheConstruct/render_engine/runtime_profiles.py",
                    "load_construct_runtime_profile",
                )
                load_tests = _load_symbol(
                    "Z Axis/Z0_TheConstruct/render_engine/runtime_profiles.py",
                    "load_virtual_space_test_matrix",
                )
                profile = load_profile()
                tests = load_tests()
                mode_lines = []
                for item in profile.get("render_modes", []):
                    mode_lines.append(f"{item.get('mode')}={item.get('target_fps')}fps")
                lines = [
                    f"Profile: {profile.get('profile_id', 'unknown')}",
                    f"Default surface: {profile.get('default_surface', 'unknown')}",
                    f"Render modes: {', '.join(mode_lines) if mode_lines else 'none'}",
                    (
                        "Guards: "
                        f"widgets={((profile.get('resource_guards') or {}).get('max_visible_widgets', 'n/a'))} | "
                        f"texture_panels={((profile.get('resource_guards') or {}).get('max_live_texture_panels', 'n/a'))}"
                    ),
                    (
                        "Virtual space tests: "
                        f"smoke={len(((tests.get('virtual_space_tests') or {}).get('smoke_lanes') or []))} | "
                        f"manual={len(((tests.get('virtual_space_tests') or {}).get('manual_lanes') or []))}"
                    ),
                ]
            except Exception as exc:
                lines = [f"Construct runtime profile unavailable: {exc}"]
            runtime_summary.delete("1.0", "end")
            runtime_summary.insert("1.0", "\n".join(lines))

        actions = ttk.Frame(parent)
        actions.pack(pady=(0, 20))
        ttk.Button(actions, text="Refresh Runtime Profile", command=_refresh_runtime_profile).pack(side="left")
        _refresh_runtime_profile()
        ttk.Label(parent, text="🌌 Launch 3D Immersive Environment", font=("Consolas", 14, "bold")).pack(pady=10)
        ttk.Button(parent, text="🚀 Launch 3D", command=self._launch_3d_immersive).pack(pady=20)

    def _launch_3d_immersive(self):
        """Launch full 3D immersive environment"""
        try:
            launch_fn = _load_symbol("Z Axis/Z0_TheConstruct/ui/immersive_3d_engine.py", "launch_immersive_3d_environment")
            self.state.immersive_active = True
            launch_fn(parent=self.winfo_toplevel())
        except Exception as e:
            print(f"[TheConstruct] Error launching 3D: {e}")

    def _launch_raphael(self):
        """Launch Raphael physics engine"""
        print("[TheConstruct] Launching Raphael physics engine...")
        self.select_tab("Physics Calculators")


def create_gui(*args, **kwargs):
    """
    N.py / IT Portal integration entry point.

    Supported call shapes:
    - create_gui(parent, colors)
    - create_gui(app, parent, colors)
    """
    app = None
    parent = None
    if args and isinstance(args[0], tk.Misc):
        parent = args[0]
    elif len(args) >= 2 and isinstance(args[1], tk.Misc):
        app = args[0]
        parent = args[1]
    if parent is None:
        return None
    compact = bool(kwargs.get("compact") or kwargs.get("it_portal"))
    return TheConstructUI(parent, app=app, compact=compact)


def build(*args, **kwargs):
    """Alias for legacy floor loaders."""
    return create_gui(*args, **kwargs)


# ---------------------------------------------------------------------------
# Floor boot hook (used by FloorLoader)
# ---------------------------------------------------------------------------

_THECONSTRUCT_INITIALIZED = False
THECONSTRUCT_RUNTIME: Dict[str, Any] = {}


def initialize(*, components: Optional[Dict[str, Any]] = None, dependencies: Optional[Dict[str, Any]] = None, **_kwargs) -> bool:
    """
    Initialize TheConstruct floor runtime services.

    This runs during floor bootstrap (no UI) and ensures TheConstruct's
    background services and integrations are active.

    Args:
        components: Pre-loaded component classes/instances
        dependencies: Shared services (db, event_bus, storage, logger)
        **_kwargs: Additional platform parameters

    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    global _THECONSTRUCT_INITIALIZED, THECONSTRUCT_RUNTIME
    if _THECONSTRUCT_INITIALIZED:
        return True
    _THECONSTRUCT_INITIALIZED = True

    try:
        # Core services are provided by the Merovingian floor (`Z Axis/Z-4_Merovingian/core`).
        # Use the stable namespace import path (`core.services`) and avoid invalid module names
        # such as `Z-4_Merovingian`.
        from core.services import get_db, get_event_bus, get_storage, get_logger  # type: ignore

        db = get_db()
        event_bus = get_event_bus()
        storage = get_storage()
        logger = get_logger()
    except Exception as e:
        print(f"[TheConstruct] Failed to load core services: {e}")
        db = None
        event_bus = None
        storage = None
        logger = None

    THECONSTRUCT_RUNTIME["db"] = db
    THECONSTRUCT_RUNTIME["event_bus"] = event_bus
    THECONSTRUCT_RUNTIME["storage"] = storage
    THECONSTRUCT_RUNTIME["logger"] = logger

    # Floor-specific initialization

    # Initialize physics simulation engines
    try:
        from core.services import get_physics_tools  # type: ignore
        physics = get_physics_tools()
        THECONSTRUCT_RUNTIME["physics_tools"] = physics
        if logger:
            logger.info("[TheConstruct] Physics tools initialized")
    except Exception as e:
        THECONSTRUCT_RUNTIME["physics_error"] = str(e)

    try:
        load_profile = _load_symbol(
            "Z Axis/Z0_TheConstruct/render_engine/runtime_profiles.py",
            "load_construct_runtime_profile",
        )
        load_tests = _load_symbol(
            "Z Axis/Z0_TheConstruct/render_engine/runtime_profiles.py",
            "load_virtual_space_test_matrix",
        )
        THECONSTRUCT_RUNTIME["runtime_profile"] = load_profile()
        THECONSTRUCT_RUNTIME["virtual_space_tests"] = load_tests()
        if event_bus:
            event_bus.publish(
                "theconstruct.runtime.profile.ready",
                {
                    "floor": "TheConstruct",
                    "default_surface": THECONSTRUCT_RUNTIME["runtime_profile"].get("default_surface"),
                    "smoke_lane_count": len(
                        ((THECONSTRUCT_RUNTIME["virtual_space_tests"].get("virtual_space_tests") or {}).get("smoke_lanes") or [])
                    ),
                },
            )
    except Exception as e:
        THECONSTRUCT_RUNTIME["runtime_profile_error"] = str(e)

    # Start 3D rendering service
    try:
        # `Z0_TheConstruct` is a valid package name when `Z Axis/` is on sys.path.
        from Z0_TheConstruct.components.visualization_3d import Visualization3DComponent  # type: ignore
        # Do not instantiate a Tk frame during non-GUI floor bootstrap. Store the
        # class so UIs (N.py / Trinity overlays) can instantiate it with a parent.
        THECONSTRUCT_RUNTIME["visualization_class"] = Visualization3DComponent
    except Exception as e:
        if logger:
            logger.debug(f"[TheConstruct] 3D visualization not available: {e}")


    # Subscribe to relevant events
    if event_bus:
        try:
            event_bus.subscribe("system.health.check", _on_health_check)
        except Exception as e:
            if logger:
                logger.warning(f"[TheConstruct] Event subscription failed: {e}")

    # Publish floor ready event
    if event_bus:
        try:
            event_bus.publish("theconstruct.floor.ready", {
                "floor": "TheConstruct",
                "z_level": 0,
                "capabilities": ['physics_simulations', 'raphael_equations', 'big_bang', 'orbital_mechanics', 'quantum_mechanics']
            })
        except Exception as e:
            if logger:
                logger.warning(f"[TheConstruct] Failed to publish ready event: {e}")

    if logger:
        logger.info("[TheConstruct] Floor initialized successfully")

    return True


def _on_health_check(event):
    """Respond to health check events"""
    event_bus = THECONSTRUCT_RUNTIME.get("event_bus")
    if event_bus:
        try:
            event_bus.publish("theconstruct.health.status", {
                "floor": "TheConstruct",
                "status": "operational",
                "z_level": 0
            })
        except Exception:
            pass

def main() -> int:
    root = tk.Tk()
    root.title("TheConstruct (Z0) - Physics & Simulations")
    root.geometry("1400x900")
    TheConstructUI(root).pack(fill="both", expand=True)
    print("[TheConstruct] Floor running standalone")
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
