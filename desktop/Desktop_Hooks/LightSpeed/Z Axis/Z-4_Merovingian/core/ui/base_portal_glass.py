#!/usr/bin/env python
"""
Base Portal Glass UI - Single Source of Truth for All Z-Floor UIs
Eliminates ~2000+ lines of duplicate code across 9 floor implementations
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, Tuple
import tkinter as tk
from tkinter import ttk
import json
import ast
import math


@dataclass
class PortalTheme:
    """
    Universal Portal Glass Theme (Glassmorphism Aesthetic)
    Used by all Z-floor portal interfaces
    """
    bg_primary: str = '#1e1e1e'
    bg_secondary: str = '#2a2a2a'
    # Tk does not support alpha in hex colors; keep all defaults Tk-safe.
    bg_glass: str = '#2a2a2a'
    fg_primary: str = '#00DDFF'
    fg_secondary: str = '#FF00FF'
    fg_text: str = '#FFFFFF'
    fg_muted: str = '#888888'
    accent_success: str = '#00FF88'
    accent_warning: str = '#FFAA00'
    accent_error: str = '#FF4444'
    border_color: str = '#00DDFF'


@dataclass
class BentoConstraints:
    """
    Universal Bento Interface Constraints (OASIS Aesthetic)
    Single source for all Bento system configurations
    Based on UI Base.pdf design system
    """
    bg: str = '#000033'
    # Tk does not support CSS rgba(); approximate with a solid dark blue.
    panel: str = '#00143C'
    border: str = '#00d4ff'
    accent_green: str = '#00ff88'
    accent_cyan: str = '#00ffff'
    accent_magenta: str = '#ff1493'
    text: str = '#ffffff'
    radius_3d: float = 1.5
    grid_cols: int = 4
    grid_rows: int = 12
    cell_width: float = 0.25
    cell_height: float = 0.30
    corner_radius: int = 15
    glass_blur: int = 10
    animation_duration_ms: int = 300


def find_lightspeed_root() -> Path:
    """
    Universal LightSpeed root finder
    Searches upward from current file until finding N.py
    """
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / 'N.py').exists():
            return parent
    return Path.cwd()


def _safe_eval_expr(expr: str, variables: Dict[str, Any]) -> Any:
    """
    Evaluate a small arithmetic expression safely for suggestion/inference hints.

    Allowed:
    - numbers, names, + - * / // % **, parentheses
    - functions: min, max, abs, round

    This is used only for UI suggestions; it must never be used for critical logic.
    """
    if not isinstance(expr, str) or not expr.strip():
        raise ValueError("empty expr")

    allowed_funcs = {"min": min, "max": max, "abs": abs, "round": round}
    allowed_names: Dict[str, Any] = {
        **allowed_funcs,
        "pi": math.pi,
        "e": math.e,
        "tau": getattr(math, "tau", 2.0 * math.pi),
    }

    def _convert(v: Any) -> Any:
        # Permit ints/floats, coerce numeric-ish strings.
        if isinstance(v, (int, float)):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return None
            try:
                if "." in s or "e" in s.lower():
                    return float(s)
                return int(s)
            except Exception:
                return None
        return None

    local_vars: Dict[str, Any] = {}
    for k, v in (variables or {}).items():
        if not isinstance(k, str) or not k.strip():
            continue
        if k in allowed_names:
            continue
        local_vars[k] = _convert(v)

    node = ast.parse(expr, mode="eval")

    allowed_nodes = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.FloorDiv,
        ast.Mod,
        ast.Pow,
        ast.UAdd,
        ast.USub,
        ast.Constant,
        ast.Name,
        ast.Load,
        ast.Call,
    )

    for sub in ast.walk(node):
        if not isinstance(sub, allowed_nodes):
            raise ValueError(f"disallowed node: {type(sub).__name__}")
        if isinstance(sub, ast.Call):
            if not isinstance(sub.func, ast.Name) or sub.func.id not in allowed_funcs:
                raise ValueError("disallowed call")

    code = compile(node, "<spec_expr>", "eval")
    return eval(code, {"__builtins__": {}}, {**allowed_names, **local_vars})


class SpecForm:
    """
    Render typed parameter specs into a consistent, "menu-first" form (no placeholders).

    Specs shape (minimal):
      {
        "name": "protons",
        "type": "int" | "number" | "float" | "bool" | "string" | "enum" | "json",
        "required": true|false,
        "default": 1,
        "ui": {
          "control": "spinbox"|"slider"|"toggle"|"entry"|"dropdown"|"json",
          "min": 0, "max": 500, "step": 1,
          "label": "Protons",
          "help": "Helper text shown under the control",
          "units": "count",
          "suggest_expr": "width*height"  # optional; computed hint only (not auto-filled)
        }
      }
    """

    def __init__(
        self,
        parent: tk.Misc,
        specs: List[Dict[str, Any]],
        *,
        colors: Optional[Dict[str, str]] = None,
        on_change: Optional[Callable[[str, Any], None]] = None,
    ):
        self.parent = parent
        self.colors = colors or {}
        self.on_change = on_change

        self.frame = tk.Frame(parent, bg=self.colors.get("bg", None))
        self._specs: List[Dict[str, Any]] = []
        self._vars: Dict[str, Any] = {}
        self._widgets: Dict[str, tk.Widget] = {}
        self._suggest_labels: Dict[str, tk.Label] = {}

        self._show_optional_var = tk.BooleanVar(value=False)

        self.set_specs(specs or [])

    def pack(self, *args, **kwargs):
        return self.frame.pack(*args, **kwargs)

    def grid(self, *args, **kwargs):
        return self.frame.grid(*args, **kwargs)

    def destroy(self) -> None:
        try:
            self.frame.destroy()
        except Exception:
            pass

    def set_specs(self, specs: List[Dict[str, Any]]) -> None:
        self._specs = [s for s in (specs or []) if isinstance(s, dict)]
        for w in list(self.frame.winfo_children()):
            try:
                w.destroy()
            except Exception:
                pass
        self._vars.clear()
        self._widgets.clear()
        self._suggest_labels.clear()

        required_specs = [s for s in self._specs if bool(s.get("required", False))]
        optional_specs = [s for s in self._specs if not bool(s.get("required", False))]

        # Required fields
        if required_specs:
            req = tk.LabelFrame(self.frame, text="Required", bg=self.colors.get("bg_panel", self.frame["bg"]))
            req.pack(fill="x", padx=8, pady=(0, 10))
            for s in required_specs:
                self._render_field(req, s, is_optional=False)
        else:
            tk.Label(self.frame, text="No required parameters.", fg=self.colors.get("fg_muted", "#888888")).pack(
                anchor="w", padx=8, pady=(0, 8)
            )

        # Optional expander
        if optional_specs:
            bar = tk.Frame(self.frame, bg=self.colors.get("bg", None))
            bar.pack(fill="x", padx=8, pady=(0, 6))
            tk.Checkbutton(
                bar,
                text="Show optional fields",
                variable=self._show_optional_var,
                command=self._rebuild_optional_section,
                bg=self.colors.get("bg", None),
                fg=self.colors.get("fg_text", "#ffffff"),
                selectcolor=self.colors.get("bg_panel", "#2a2a2a"),
                activebackground=self.colors.get("bg", None),
                activeforeground=self.colors.get("fg_text", "#ffffff"),
            ).pack(side="left")

            self._optional_host = tk.Frame(self.frame, bg=self.colors.get("bg", None))
            self._optional_host.pack(fill="x", padx=0, pady=0)
            self._optional_specs = optional_specs
            self._rebuild_optional_section()

    def _rebuild_optional_section(self) -> None:
        host = getattr(self, "_optional_host", None)
        if host is None:
            return
        for w in list(host.winfo_children()):
            try:
                w.destroy()
            except Exception:
                pass
        if not bool(self._show_optional_var.get()):
            return

        opt = tk.LabelFrame(host, text="Optional", bg=self.colors.get("bg_panel", host["bg"]))
        opt.pack(fill="x", padx=8, pady=(0, 10))
        for s in list(getattr(self, "_optional_specs", []) or []):
            self._render_field(opt, s, is_optional=True)

    def _render_field(self, parent: tk.Misc, spec: Dict[str, Any], *, is_optional: bool) -> None:
        name = str(spec.get("name") or "").strip()
        if not name:
            return

        typ = str(spec.get("type") or "string").strip().lower()
        ui = spec.get("ui") if isinstance(spec.get("ui"), dict) else {}
        label = str(ui.get("label") or name).strip()
        help_text = str(ui.get("help") or "").strip()
        units = str(ui.get("units") or "").strip()
        control = str(ui.get("control") or "").strip().lower()
        default = spec.get("default", None)

        row = tk.Frame(parent, bg=self.colors.get("bg_panel", None))
        row.pack(fill="x", padx=10, pady=8)

        # Labels
        left = tk.Frame(row, bg=self.colors.get("bg_panel", None))
        left.pack(side="left", fill="x", expand=True)

        title = tk.Label(
            left,
            text=label + (" *" if not is_optional and bool(spec.get("required", False)) else ""),
            fg=self.colors.get("fg_text", "#ffffff"),
            bg=self.colors.get("bg_panel", None),
            font=("Segoe UI", 10, "bold"),
        )
        title.pack(anchor="w")

        if units:
            tk.Label(
                left,
                text=f"Units: {units}",
                fg=self.colors.get("fg_muted", "#888888"),
                bg=self.colors.get("bg_panel", None),
                font=("Segoe UI", 8),
            ).pack(anchor="w", pady=(1, 0))

        if help_text:
            tk.Label(
                left,
                text=help_text,
                fg=self.colors.get("fg_muted", "#888888"),
                bg=self.colors.get("bg_panel", None),
                font=("Segoe UI", 8),
            ).pack(anchor="w", pady=(2, 0))

        # Control host
        right = tk.Frame(row, bg=self.colors.get("bg_panel", None))
        right.pack(side="right", anchor="e")

        def _changed(_evt=None):
            if callable(self.on_change):
                try:
                    self.on_change(name, self.get_raw_value(name))
                except Exception:
                    pass
            self._refresh_suggestions()

        # Decide control by explicit hint first, then type.
        if control == "toggle" or typ == "bool":
            var = tk.BooleanVar(value=bool(default) if default is not None else False)
            w = tk.Checkbutton(
                right,
                variable=var,
                bg=self.colors.get("bg_panel", None),
                fg=self.colors.get("fg_text", "#ffffff"),
                selectcolor=self.colors.get("bg_panel", "#2a2a2a"),
                command=_changed,
            )
            w.pack()
            self._vars[name] = var
            self._widgets[name] = w

        elif control == "dropdown" or typ == "enum":
            options = spec.get("options") if isinstance(spec.get("options"), list) else ui.get("options")
            if not isinstance(options, list):
                options = []
            options = [str(o) for o in options if str(o).strip()]
            var = tk.StringVar(value=str(default) if default is not None else (options[0] if options else ""))
            w = ttk.Combobox(right, textvariable=var, values=options, state="readonly", width=24)
            w.bind("<<ComboboxSelected>>", _changed)
            w.pack()
            self._vars[name] = var
            self._widgets[name] = w

        elif control == "slider" or (typ in ("int", "float", "number") and isinstance(ui.get("min"), (int, float)) and isinstance(ui.get("max"), (int, float)) and control == "slider"):
            mn = float(ui.get("min", 0.0))
            mx = float(ui.get("max", 100.0))
            step = float(ui.get("step", 1.0) or 1.0)
            init = default
            try:
                init = float(init) if init is not None else mn
            except Exception:
                init = mn
            var = tk.DoubleVar(value=float(init))
            w = ttk.Scale(right, from_=mn, to=mx, variable=var, orient="horizontal", length=220)
            w.pack(side="left")
            val_lbl = tk.Label(right, text=str(var.get()), fg=self.colors.get("fg_text", "#ffffff"), bg=self.colors.get("bg_panel", None))
            val_lbl.pack(side="left", padx=(8, 0))

            def _on_scale(_v):
                # Quantize display to step (doesn't mutate the underlying variable).
                try:
                    cur = float(var.get())
                    q = round(cur / step) * step if step > 0 else cur
                    val_lbl.config(text=str(q))
                except Exception:
                    pass
                _changed()

            w.configure(command=_on_scale)
            self._vars[name] = var
            self._widgets[name] = w

        elif typ == "int":
            mn = ui.get("min")
            mx = ui.get("max")
            step = ui.get("step", 1)
            init = default if default is not None else (mn if isinstance(mn, int) else 0)
            try:
                init = int(init)
            except Exception:
                init = 0
            var = tk.IntVar(value=init)
            w = ttk.Spinbox(
                right,
                from_=int(mn) if isinstance(mn, int) else -10_000_000,
                to=int(mx) if isinstance(mx, int) else 10_000_000,
                increment=int(step) if isinstance(step, int) else 1,
                textvariable=var,
                width=10,
                command=_changed,
            )
            w.bind("<KeyRelease>", _changed)
            w.pack()
            self._vars[name] = var
            self._widgets[name] = w

        elif typ in ("float", "number"):
            init = default
            if init is None and not spec.get("required", False):
                init = ""
            try:
                init = "" if init == "" else str(float(init))
            except Exception:
                init = "" if init == "" else str(init or "")
            var = tk.StringVar(value=str(init))
            w = ttk.Entry(right, textvariable=var, width=24)
            w.bind("<KeyRelease>", _changed)
            w.pack()
            self._vars[name] = var
            self._widgets[name] = w

        elif control == "json" or typ in ("json", "object", "dict", "list"):
            init = default if default is not None else {}
            try:
                init_text = json.dumps(init, indent=2, ensure_ascii=False)
            except Exception:
                init_text = "{}"
            txt = tk.Text(right, width=36, height=5, wrap="word")
            txt.insert("1.0", init_text)
            txt.bind("<KeyRelease>", _changed)
            txt.pack()
            self._vars[name] = txt  # raw widget; handled specially
            self._widgets[name] = txt

        else:
            # Default string entry
            init = default
            if init is None and not spec.get("required", False):
                init = ""
            var = tk.StringVar(value=str(init) if init is not None else "")
            w = ttk.Entry(right, textvariable=var, width=36)
            w.bind("<KeyRelease>", _changed)
            w.pack()
            self._vars[name] = var
            self._widgets[name] = w

        # Suggestion hint (computed, non-invasive)
        suggest_expr = str(ui.get("suggest_expr") or "").strip()
        if suggest_expr:
            sug_row = tk.Frame(parent, bg=self.colors.get("bg_panel", None))
            sug_row.pack(fill="x", padx=10, pady=(0, 6))
            lbl = tk.Label(
                sug_row,
                text="Suggested: ...",
                fg=self.colors.get("fg_muted", "#888888"),
                bg=self.colors.get("bg_panel", None),
                font=("Segoe UI", 8),
            )
            lbl.pack(side="left")
            self._suggest_labels[name] = lbl

            def _apply_suggestion():
                try:
                    val = self._compute_suggestion(name)
                except Exception:
                    return
                self.set_value(name, val)
                _changed()

            ttk.Button(sug_row, text="Apply", command=_apply_suggestion).pack(side="left", padx=(10, 0))

        self._refresh_suggestions()

    def get_raw_value(self, name: str) -> Any:
        v = self._vars.get(name)
        if v is None:
            return None
        if isinstance(v, (tk.StringVar, tk.IntVar, tk.DoubleVar, tk.BooleanVar)):
            try:
                return v.get()
            except Exception:
                return None
        if isinstance(v, tk.Text):
            try:
                return v.get("1.0", tk.END).strip()
            except Exception:
                return None
        return None

    def set_value(self, name: str, value: Any) -> None:
        v = self._vars.get(name)
        if v is None:
            return
        try:
            if isinstance(v, tk.StringVar):
                v.set("" if value is None else str(value))
            elif isinstance(v, tk.IntVar):
                v.set(int(value))
            elif isinstance(v, tk.DoubleVar):
                v.set(float(value))
            elif isinstance(v, tk.BooleanVar):
                v.set(bool(value))
            elif isinstance(v, tk.Text):
                v.delete("1.0", tk.END)
                v.insert("1.0", json.dumps(value, indent=2, ensure_ascii=False))
        except Exception:
            return

    def _compute_suggestion(self, field_name: str) -> Any:
        spec = next((s for s in self._specs if str(s.get("name") or "").strip() == field_name), None)
        if not isinstance(spec, dict):
            raise ValueError("unknown field")
        ui = spec.get("ui") if isinstance(spec.get("ui"), dict) else {}
        expr = str(ui.get("suggest_expr") or "").strip()
        if not expr:
            raise ValueError("no expr")
        variables = {s.get("name"): self.get_raw_value(str(s.get("name") or "")) for s in self._specs if isinstance(s, dict)}
        return _safe_eval_expr(expr, variables)

    def _refresh_suggestions(self) -> None:
        for name, lbl in list(self._suggest_labels.items()):
            try:
                val = self._compute_suggestion(name)
                lbl.config(text=f"Suggested: {val}")
            except Exception:
                try:
                    lbl.config(text="Suggested: ...")
                except Exception:
                    pass

    def get_values(self) -> Tuple[Dict[str, Any], List[str]]:
        """
        Return typed values and a list of validation errors.

        Optional fields that are empty are omitted from the output dict.
        """
        out: Dict[str, Any] = {}
        errs: List[str] = []

        for s in self._specs:
            if not isinstance(s, dict):
                continue
            name = str(s.get("name") or "").strip()
            if not name:
                continue
            typ = str(s.get("type") or "string").strip().lower()
            required = bool(s.get("required", False))
            raw = self.get_raw_value(name)

            if raw is None:
                if required:
                    errs.append(f"{name}: required")
                continue

            if isinstance(raw, str) and not raw.strip():
                if required:
                    errs.append(f"{name}: required")
                else:
                    continue

            try:
                if typ == "bool":
                    out[name] = bool(raw)
                elif typ == "int":
                    out[name] = int(raw)
                elif typ in ("float", "number"):
                    out[name] = float(raw)
                elif typ in ("json", "object", "dict", "list"):
                    if isinstance(raw, str):
                        out[name] = json.loads(raw)
                    else:
                        out[name] = raw
                else:
                    out[name] = str(raw)
            except Exception:
                errs.append(f"{name}: invalid {typ}")

        return out, errs


class BasePortalGlass(tk.Frame):
    """
    Base class for all Z-floor Portal Glass UIs

    Provides:
    - Standard theme configuration
    - Service loading (DB, Event Bus, Storage)
    - Path resolution
    - Bento widget registration interface
    - Common UI patterns

    Subclasses must implement:
    - _create_ui(): Floor-specific UI construction
    - get_bento_widgets(): Floor-specific Bento widget list
    """

    def __init__(
        self,
        parent,
        floor_name: str,
        colors: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.floor_name = floor_name
        self.lightspeed_root = find_lightspeed_root()
        self.theme = PortalTheme()
        self.bento_constraints = BentoConstraints()
        self.colors = colors or self._get_default_colors()

        self.db = None
        self.event_bus = None
        self.storage = None

        self._load_services()
        self._apply_theme()
        self._create_ui()

    def _get_default_colors(self) -> Dict[str, str]:
        """Generate default color scheme from PortalTheme"""
        return {
            'bg_dark': self.theme.bg_primary,
            'bg_panel': self.theme.bg_secondary,
            'bg_glass': self.theme.bg_glass,
            'fg_cyan': self.theme.fg_primary,
            'fg_magenta': self.theme.fg_secondary,
            'fg_text': self.theme.fg_text,
            'fg_muted': self.theme.fg_muted,
            'accent_green': self.theme.accent_success,
            'accent_warning': self.theme.accent_warning,
            'accent_error': self.theme.accent_error,
            'border': self.theme.border_color,
        }

    def _load_services(self):
        """Load core services from Merovingian"""
        try:
            from core.services import get_db, get_event_bus, get_storage
            self.db = get_db()
            self.event_bus = get_event_bus()
            self.storage = get_storage()
        except Exception as e:
            print(f"[{self.floor_name}] Core services not available: {e}")
            self.db = None
            self.event_bus = None
            self.storage = None

    def _apply_theme(self):
        """Apply theme colors to frame"""
        self.configure(bg=self.colors['bg_dark'])

    def _create_ui(self):
        """
        Create floor-specific UI
        MUST be overridden by subclasses
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _create_ui()"
        )

    def get_bento_widgets(self) -> List[Dict[str, Any]]:
        """
        Return floor-specific Bento widget descriptors
        MUST be overridden by subclasses

        Returns:
            List of widget descriptors with format:
            {
                'type': str,  # Widget type identifier
                'title': str,  # Display title
                'position': tuple,  # (col, row) in Bento grid
                'size': tuple,  # (cols, rows) widget size
                'floor': str,  # Floor name
                'resizable': bool,  # Allow user resize
                'min_size': tuple,  # Minimum (cols, rows)
            }
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_bento_widgets()"
        )

    def create_glass_frame(
        self,
        parent,
        padding: int = 20,
        corner_radius: Optional[int] = None
    ) -> ttk.Frame:
        """
        Create a glassmorphism-styled frame

        Args:
            parent: Parent widget
            padding: Internal padding
            corner_radius: Corner radius (defaults to BentoConstraints value)

        Returns:
            Styled ttk.Frame
        """
        frame = ttk.Frame(parent)

        try:
            style = ttk.Style()
            style.configure(
                f'{self.floor_name}.Glass.TFrame',
                background=self.colors['bg_glass'],
                bordercolor=self.colors['border'],
                borderwidth=1,
                relief='flat'
            )
            frame.configure(style=f'{self.floor_name}.Glass.TFrame')
        except Exception:
            frame.configure(bg=self.theme.bg_secondary)

        return frame

    def create_header(
        self,
        parent,
        title: str,
        subtitle: Optional[str] = None
    ) -> tk.Frame:
        """
        Create standard floor header with title and optional subtitle

        Args:
            parent: Parent widget
            title: Main title text
            subtitle: Optional subtitle text

        Returns:
            Header frame containing title labels
        """
        header = tk.Frame(parent, bg=self.colors['bg_dark'])

        title_label = tk.Label(
            header,
            text=title,
            font=('Arial', 18, 'bold'),
            fg=self.colors['fg_cyan'],
            bg=self.colors['bg_dark']
        )
        title_label.pack(side='top', anchor='w', pady=(0, 5))

        if subtitle:
            subtitle_label = tk.Label(
                header,
                text=subtitle,
                font=('Arial', 10),
                fg=self.colors['fg_muted'],
                bg=self.colors['bg_dark']
            )
            subtitle_label.pack(side='top', anchor='w')

        return header

    def create_status_bar(self, parent) -> tk.Frame:
        """
        Create standard status bar

        Args:
            parent: Parent widget

        Returns:
            Status bar frame with label
        """
        status_bar = tk.Frame(parent, bg=self.colors['bg_panel'], height=30)

        self.status_label = tk.Label(
            status_bar,
            text=f"{self.floor_name} Floor Ready",
            font=('Arial', 9),
            fg=self.colors['fg_text'],
            bg=self.colors['bg_panel']
        )
        self.status_label.pack(side='left', padx=10, pady=5)

        return status_bar

    def update_status(self, message: str):
        """
        Update status bar message

        Args:
            message: Status message to display
        """
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message)

    def publish_event(self, event_type: str, data: Any):
        """
        Publish event to Event Bus if available

        Args:
            event_type: Event type identifier
            data: Event payload
        """
        if self.event_bus:
            try:
                self.event_bus.publish(event_type, data)
            except Exception as e:
                print(f"[{self.floor_name}] Event publish failed: {e}")

    def subscribe_event(self, event_type: str, callback: callable):
        """
        Subscribe to Event Bus events if available

        Args:
            event_type: Event type to subscribe to
            callback: Function to call when event occurs
        """
        if self.event_bus:
            try:
                self.event_bus.subscribe(event_type, callback)
            except Exception as e:
                print(f"[{self.floor_name}] Event subscribe failed: {e}")

    def register_bento_widgets(self):
        """
        Register this floor's Bento widgets with the Bento Hub

        Called automatically after UI creation
        """
        try:
            widgets = self.get_bento_widgets()
            self.publish_event(
                'bento.register_widgets',
                {
                    'floor': self.floor_name,
                    'widgets': widgets
                }
            )
        except NotImplementedError:
            pass
        except Exception as e:
            print(f"[{self.floor_name}] Bento widget registration failed: {e}")


class GlassFrame(tk.Frame):
    """
    Standalone glassmorphism frame
    Fallback for floors that don't use full BasePortalGlass
    """

    def __init__(self, parent, theme: Optional[PortalTheme] = None, **kwargs):
        self.theme = theme or PortalTheme()

        super().__init__(
            parent,
            bg=self.theme.bg_glass[:7],
            bd=1,
            relief='flat',
            **kwargs
        )


# Alias for consistency with settings_panel.py
GlassPanel = GlassFrame


class GlassButton(tk.Button):
    """Glassmorphism styled button"""

    def __init__(self, parent, constraints, text="", command=None, **kwargs):
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=constraints.panel if hasattr(constraints, 'panel') else '#2a2a2a',
            fg=constraints.text if hasattr(constraints, 'text') else '#ffffff',
            activebackground=constraints.border if hasattr(constraints, 'border') else '#00d4ff',
            activeforeground='#ffffff',
            bd=0,
            relief='flat',
            padx=15,
            pady=8,
            font=('Arial', 10),
            cursor='hand2',
            **kwargs
        )


class GlassEntry(tk.Entry):
    """Glassmorphism styled text entry"""

    def __init__(self, parent, constraints, **kwargs):
        super().__init__(
            parent,
            bg=constraints.panel if hasattr(constraints, 'panel') else '#2a2a2a',
            fg=constraints.text if hasattr(constraints, 'text') else '#ffffff',
            insertbackground=constraints.accent_cyan if hasattr(constraints, 'accent_cyan') else '#00ffff',
            bd=1,
            relief='solid',
            font=('Arial', 10),
            **kwargs
        )


class GlassNotification(tk.Toplevel):
    """Glassmorphism styled notification window"""

    def __init__(self, parent, title="Notification", message="", duration_ms=3000):
        super().__init__(parent)

        self.title(title)
        self.geometry("300x100")
        self.overrideredirect(True)

        constraints = BentoConstraints()

        frame = tk.Frame(
            self,
            bg=constraints.panel if hasattr(constraints, 'panel') else '#2a2a2a',
            bd=2,
            relief='solid'
        )
        frame.pack(fill='both', expand=True, padx=2, pady=2)

        label = tk.Label(
            frame,
            text=message,
            bg=constraints.panel if hasattr(constraints, 'panel') else '#2a2a2a',
            fg=constraints.text if hasattr(constraints, 'text') else '#ffffff',
            font=('Arial', 10),
            wraplength=280
        )
        label.pack(expand=True, padx=15, pady=15)

        # Auto-dismiss after duration
        if duration_ms > 0:
            self.after(duration_ms, self.destroy)


def get_portal_theme() -> PortalTheme:
    """Get the universal Portal Theme"""
    return PortalTheme()


def get_bento_constraints() -> BentoConstraints:
    """Get the universal Bento Constraints"""
    return BentoConstraints()


# ---------------------------------------------------------------------------
# Smart Ops (shared, operator-first UI strip)
# ---------------------------------------------------------------------------


class SmartOpsStrip(ttk.Frame):
    """
    Shared, low-risk "ops visibility + quick actions" strip.

    Design goals:
    - Safe in retrieve-only mode (does not start background workers implicitly).
    - Gives operator clarity: worker gate state + routed-task visibility.
    - Provides non-destructive actions: enable ops for session, run a single Oracle drain cycle,
      deep-link to Trinity Z Direct (when hosted inside N.py).
    """

    def __init__(
        self,
        parent: tk.Misc,
        *,
        app: Optional[object] = None,
        floor_channel: str = "Z+3",
        it_portal: bool = False,
        auto_drain: bool = False,
        title: Optional[str] = None,
    ):
        super().__init__(parent)
        self.app = app
        self.floor_channel = str(floor_channel or "Z+3")
        self.it_portal = bool(it_portal)

        self._var_gate = tk.StringVar(value="-")
        self._var_inbox = tk.StringVar(value="-")
        self._var_smith = tk.StringVar(value="-")

        self._auto_drain = tk.BooleanVar(value=bool(auto_drain))
        self._auto_drain_job = None

        self._build_ui(title=title)
        self._refresh()
        if bool(auto_drain):
            self._on_toggle_auto_drain()

    def _build_ui(self, *, title: Optional[str]) -> None:
        top = ttk.Frame(self)
        top.pack(fill="x", expand=True)

        left = ttk.Frame(top)
        left.pack(side="left", fill="x", expand=True)

        hdr = title or "Smart Ops"
        ttk.Label(left, text=hdr, font=("Arial", 10, "bold")).pack(side="left", padx=(0, 10))
        ttk.Label(left, text="Gate:").pack(side="left")
        ttk.Label(left, textvariable=self._var_gate).pack(side="left", padx=(4, 12))
        ttk.Label(left, text="Inbox(Z-3->%s):" % self.floor_channel).pack(side="left")
        ttk.Label(left, textvariable=self._var_inbox).pack(side="left", padx=(4, 12))
        ttk.Label(left, text="Smith:").pack(side="left")
        ttk.Label(left, textvariable=self._var_smith).pack(side="left", padx=(4, 12))

        right = ttk.Frame(top)
        right.pack(side="right")

        ttk.Checkbutton(
            right,
            text="Auto-drain routes",
            variable=self._auto_drain,
            command=self._on_toggle_auto_drain,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(right, text="Enable Ops", command=self._enable_ops_for_session).pack(side="left", padx=(0, 6))
        ttk.Button(right, text="Run Oracle Cycle", command=self._run_oracle_cycle_once).pack(side="left", padx=(0, 6))
        ttk.Button(right, text="Open Z Direct", command=self._open_z_direct).pack(side="left")

    def _is_workers_disabled(self) -> bool:
        try:
            import os

            return os.environ.get("LIGHTSPEED_DISABLE_BACKGROUND_WORKERS", "").strip() == "1"
        except Exception:
            return False

    def _smith_queue(self):
        try:
            import Smith  # type: ignore

            rt = getattr(Smith, "SMITH_RUNTIME", {}) or {}
            return rt.get("queue")
        except Exception:
            return None

    def _enable_ops_for_session(self) -> None:
        # Session-scoped: clear the worker gate and (best-effort) start Smith workers.
        try:
            import os

            os.environ.pop("LIGHTSPEED_DISABLE_BACKGROUND_WORKERS", None)
        except Exception:
            pass

        q = self._smith_queue()
        try:
            fn = getattr(q, "ensure_oracle_ingestion_worker_started", None)
            if callable(fn):
                fn()
        except Exception:
            pass
        try:
            fn2 = getattr(q, "start_worker", None)
            if callable(fn2):
                fn2()
        except Exception:
            pass

        self._refresh()

    def _run_oracle_cycle_once(self) -> None:
        q = self._smith_queue()
        try:
            fn = getattr(q, "run_oracle_ingestion_cycle_once", None)
            if callable(fn):
                fn()
        except Exception:
            pass
        self._refresh()

    def _open_z_direct(self) -> None:
        # Prefer the host deep-link helper if present (N.py).
        try:
            fn = getattr(self.app, "open_it_portal_z_direct", None)
            if callable(fn):
                fn(channel=self.floor_channel, peer="Z-3", tags="oracle,route")
                return
        except Exception:
            pass

        # Fallback: at least open IT portal if possible.
        try:
            fn2 = getattr(self.app, "open_it_portal", None)
            if callable(fn2):
                fn2()
        except Exception:
            pass

    def _refresh(self) -> None:
        # Gate state
        disabled = self._is_workers_disabled()
        self._var_gate.set("DISABLED" if disabled else "ENABLED")

        # Inbox visibility (tail count is "recent", but that's enough for operator confirmation)
        inbox_n = "-"
        try:
            from core.services import get_z_direct  # type: ignore

            zd = get_z_direct()
            items = zd.tail_channel_inbox(to_channel=self.floor_channel, from_channel="Z-3", limit=200)
            inbox_n = str(len(items))
        except Exception:
            inbox_n = "-"
        self._var_inbox.set(inbox_n)

        # Smith worker status (best-effort)
        smith_s = "-"
        try:
            q = self._smith_queue()
            has = getattr(q, "has_oracle_ingestion_worker", None)
            if callable(has):
                smith_s = "oracle_worker=" + ("yes" if bool(has()) else "no")
        except Exception:
            smith_s = "-"
        self._var_smith.set(smith_s)

        # Refresh loop (lightweight)
        try:
            self.after(1500, self._refresh)
        except Exception:
            pass

    def _on_toggle_auto_drain(self) -> None:
        enabled = bool(self._auto_drain.get())
        if not enabled:
            try:
                if self._auto_drain_job is not None:
                    self.after_cancel(self._auto_drain_job)
            except Exception:
                pass
            self._auto_drain_job = None
            return

        # Auto drain is only meaningful when ops are enabled.
        if self._is_workers_disabled():
            self._enable_ops_for_session()

        self._schedule_auto_drain()

    def _schedule_auto_drain(self) -> None:
        try:
            self._run_oracle_cycle_once()
        except Exception:
            pass
        try:
            # Keep the cadence gentle to avoid UI stalls / DB contention.
            self._auto_drain_job = self.after(6000, self._schedule_auto_drain)
        except Exception:
            self._auto_drain_job = None


def mount_smart_ops_strip(
    parent: tk.Misc,
    *,
    app: Optional[object] = None,
    floor_channel: str = "Z+3",
    it_portal: bool = False,
    auto_drain: bool = False,
    title: Optional[str] = None,
) -> Optional[SmartOpsStrip]:
    """
    Convenience helper used by floor UIs and IT Portal to mount the ops strip.
    Returns the created widget (or None if something fails).
    """
    try:
        w = SmartOpsStrip(
            parent,
            app=app,
            floor_channel=floor_channel,
            it_portal=it_portal,
            auto_drain=auto_drain,
            title=title,
        )
        w.pack(fill="x", padx=8, pady=(8, 6))
        return w
    except Exception:
        return None
