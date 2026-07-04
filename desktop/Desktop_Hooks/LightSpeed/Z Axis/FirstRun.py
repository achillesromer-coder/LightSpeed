#!/usr/bin/env python
"""
FirstRun (Consolidated into Trinity) - Setup & Configuration Entry
Compatibility entrypoint for the setup/login flow now hosted in Trinity (Z+3).

This module exists for backwards compatibility with older tooling that expects
`Z Axis/FirstRun.py` to exist. Current runtime hosts setup/login under Trinity.

Variables Held:
- setup_completed: Whether initial setup is done
- user_preferences: First-time user preferences
- system_config: Initial system configuration
- wizard_state: Current wizard progress

Renders:
- FirstRun wizard interface
- Setup progress indicators
- Configuration forms
- Validation dialogs
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Optional, Dict, Any
import sys


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
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    if not hasattr(mod, symbol):
        raise AttributeError(f"{symbol} not found in {path}")
    return getattr(mod, symbol)


class FirstRunFloorState:
    """
    State manager for FirstRun floor

    This class holds all state variables for setup and configuration
    """

    def __init__(self):
        self.setup_completed = False
        self.wizard_active = False
        self.current_step = 0
        self.total_steps = 10

        self.user_preferences: Dict[str, Any] = {}
        self.system_config: Dict[str, Any] = {}
        self.wizard_state: Dict[str, Any] = {
            'started_at': None,
            'completed_at': None,
            'steps_completed': [],
            'current_page': 'welcome'
        }

        self.errors: list = []
        self.warnings: list = []

    def start_wizard(self):
        """Start the FirstRun wizard"""
        self.wizard_active = True
        self.current_step = 0
        import datetime
        self.wizard_state['started_at'] = datetime.datetime.now().isoformat()

    def complete_wizard(self):
        """Mark wizard as completed"""
        self.wizard_active = False
        self.setup_completed = True
        import datetime
        self.wizard_state['completed_at'] = datetime.datetime.now().isoformat()

    def advance_step(self):
        """Move to next wizard step"""
        if self.current_step < self.total_steps:
            self.current_step += 1
            self.wizard_state['steps_completed'].append(self.current_step)

    def get_progress(self) -> float:
        """Get wizard completion percentage"""
        if self.total_steps == 0:
            return 0.0
        return (self.current_step / self.total_steps) * 100


# Singleton state instance
_state = FirstRunFloorState()


def get_state() -> FirstRunFloorState:
    """Get the global FirstRun floor state"""
    return _state


def render_setup_wizard(parent=None):
    """
    Render the FirstRun setup wizard

    Args:
        parent: Optional parent Tk window

    Returns:
        Wizard window instance
    """
    try:
        UnifiedWizardComplete = _load_symbol(
            "Z Axis/Z+3_Trinity/wizards/unified_wizard_complete.py",
            "UnifiedWizardComplete"
        )

        get_state().start_wizard()

        wizard = UnifiedWizardComplete(parent)
        wizard.title("LightSpeed Setup")

        def on_wizard_complete():
            get_state().complete_wizard()

        wizard.protocol("WM_DELETE_WINDOW", on_wizard_complete)

        return wizard

    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox

        root = parent or tk.Tk()
        messagebox.showerror(
            "Setup",
            f"Could not load setup wizard:\n{str(e)}\n\nUsing fallback wizard."
        )

        return None


def render_quick_setup(parent=None):
    """
    Render a quick setup dialog (minimal configuration)

    Args:
        parent: Optional parent Tk window

    Returns:
        Setup dialog instance
    """
    import tkinter as tk
    from tkinter import ttk, messagebox

    dialog = tk.Toplevel(parent) if parent else tk.Tk()
    dialog.title("LightSpeed Setup")
    dialog.geometry("500x400")

    # Center window
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
    y = (dialog.winfo_screenheight() // 2) - (400 // 2)
    dialog.geometry(f"500x400+{x}+{y}")

    frame = ttk.Frame(dialog, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(
        frame,
        text="Welcome to LightSpeed",
        font=('Arial', 16, 'bold')
    ).pack(pady=(0, 20))

    ttk.Label(
        frame,
        text="Quick Setup - Essential Configuration",
        font=('Arial', 10)
    ).pack(pady=(0, 30))

    doctrine_lines = [
        "Role: Setup initializes the desktop workspace shell and operator routing.",
        "Knowns: Achilles remains the governed primary operator under Cognigrex oversight.",
        "Output: preferences and first-run configuration for the local workspace.",
        "Gate: staged here, approved in Trinity, committed on review.",
    ]
    try:
        runtime_root = Path(__file__).resolve().parents[1]
        from lightspeed_runtime.runtime import LightSpeedRuntime

        runtime = LightSpeedRuntime(root=runtime_root)
        knowns = runtime.knowns_registry()
        bellcurve = knowns.get("bellcurve_overlay", {}) or {}
        center_mass = ", ".join((bellcurve.get("center_of_gravity") or [])[:2]) or "desktop operating shell"
        doctrine_lines = [
            f"Role: Setup initializes {knowns.get('operator_model', {}).get('workspace_mode', 'desktop-first')} routing.",
            f"Knowns: {knowns.get('mission_statement', 'Achilles remains the governed primary operator.')}",
            f"Output: local workspace preferences and the first active operator profile.",
            f"Gate: staged here, approved in Trinity, committed on review. Center: {center_mass}.",
        ]
    except Exception:
        pass

    doctrine_box = ttk.LabelFrame(frame, text="Doctrine / Knowns")
    doctrine_box.pack(fill=tk.X, pady=(0, 22))
    ttk.Label(
        doctrine_box,
        text="\n".join(doctrine_lines),
        justify=tk.LEFT,
        wraplength=430,
    ).pack(anchor=tk.W, padx=12, pady=10)

    # User name
    ttk.Label(frame, text="Your Name:").pack(anchor=tk.W)
    name_entry = ttk.Entry(frame, width=40)
    name_entry.pack(pady=(5, 20), fill=tk.X)

    # Theme selection
    ttk.Label(frame, text="Preferred Theme:").pack(anchor=tk.W)
    theme_var = tk.StringVar(value="dark")
    theme_frame = ttk.Frame(frame)
    theme_frame.pack(pady=(5, 20), fill=tk.X)

    ttk.Radiobutton(theme_frame, text="Dark", variable=theme_var, value="dark").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(theme_frame, text="Light", variable=theme_var, value="light").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(theme_frame, text="OASIS", variable=theme_var, value="oasis").pack(side=tk.LEFT, padx=5)

    def complete_setup():
        name = name_entry.get().strip()
        if not name:
            messagebox.showwarning("Setup", "Please enter your name")
            return

        state = get_state()
        state.user_preferences['name'] = name
        state.user_preferences['theme'] = theme_var.get()
        state.complete_wizard()

        messagebox.showinfo("Setup Complete", f"Welcome to LightSpeed, {name}!")
        dialog.destroy()

    button_frame = ttk.Frame(frame)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))

    ttk.Button(
        button_frame,
        text="Complete Setup",
        command=complete_setup
    ).pack(side=tk.RIGHT)

    ttk.Button(
        button_frame,
        text="Cancel",
        command=dialog.destroy
    ).pack(side=tk.RIGHT, padx=(0, 10))

    return dialog


def check_setup_status() -> Dict[str, Any]:
    """
    Check if FirstRun setup has been completed

    Returns:
        Dictionary with setup status information
    """
    state = get_state()

    return {
        'completed': state.setup_completed,
        'wizard_active': state.wizard_active,
        'progress': state.get_progress(),
        'current_step': state.current_step,
        'total_steps': state.total_steps,
        'errors': state.errors,
        'warnings': state.warnings
    }


def reset_setup():
    """Reset FirstRun setup state (for testing)"""
    global _state
    _state = FirstRunFloorState()


def create_gui(parent=None, colors=None, **kwargs):
    """
    IT Portal integration entry point

    Creates a legacy FirstRun surface for IT Portal tabs.

    Canonical first-run/setup flow is Trinity-owned (Z+3) via the Cognigrex Setup Wizard.
    """
    import tkinter as tk
    from tkinter import ttk

    frame = ttk.Frame(parent) if parent else tk.Frame()
    frame.pack(fill=tk.BOTH, expand=True)

    header = ttk.Label(
        frame,
        text="FirstRun Redirect",
        font=('Arial', 14, 'bold')
    )
    header.pack(pady=20)

    ttk.Label(
        frame,
        text=(
            "Setup/login is consolidated into Trinity (Z+3).\n\n"
            "Use the button below to open the Cognigrex Setup Wizard."
        ),
        font=('Arial', 10),
        justify="center",
        wraplength=520,
    ).pack(pady=10)

    def _open_trinity_setup():
        try:
            launch = _load_symbol(
                "Z Axis/Z+3_Trinity/wizards/cognigrex_setup_wizard.py",
                "launch_setup_wizard",
            )
            wizard = launch(parent=None)
            try:
                wizard.run()
            except Exception:
                pass
        except Exception as e:
            from tkinter import messagebox

            messagebox.showerror("Setup Wizard", f"Failed to open Trinity Setup Wizard:\n{e}")

    ttk.Button(
        frame,
        text="Open Trinity Setup Wizard",
        command=_open_trinity_setup,
    ).pack(pady=8)

    return frame


def build(*args, **kwargs):
    """Alias for legacy floor loaders"""
    return create_gui(*args, **kwargs)


# Main entry point for floor operations
def main():
    """Main entry point when FirstRun floor is launched directly"""
    # Legacy alias: always route to the canonical Trinity Setup Wizard.
    try:
        launch = _load_symbol(
            "Z Axis/Z+3_Trinity/wizards/cognigrex_setup_wizard.py",
            "launch_setup_wizard",
        )
        wizard = launch(parent=None)
        wizard.run()
    except Exception as e:
        print(f"[FirstRun] Failed to open Trinity Setup Wizard: {e}")


if __name__ == "__main__":
    main()
