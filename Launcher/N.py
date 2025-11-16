# N.py — Launcher Root
# Orchestrates Z-axis plugins into a cohesive app.
#
# Responsibilities:
#  - Load Z-axis plugins from ./Launcher/Z Axis/*.py
#  - Order them by LAYER_FLOOR (-3..+4)
#  - Create tabbed UI with quick-switcher
#  - Persist workspace/theme/auth config under ./config/auth.json
#  - Provide login → company → project → subproject selection at startup
#
# Run with: python Launcher/N.py

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path
from types import ModuleType
from dataclasses import dataclass   # ✅ Fix: import dataclass

# ---------- Paths ----------
ROOT          = Path(__file__).resolve().parent
LAUNCHER_DIR  = ROOT
Z_AXIS_DIR    = LAUNCHER_DIR / "Z Axis"
CONFIG_DIR    = ROOT / "config"; CONFIG_DIR.mkdir(exist_ok=True)
AUTH_FILE     = CONFIG_DIR / "auth.json"

# ---------- Defaults ----------
DEFAULT_CONFIG = {
    "user": None,
    "workspace": "default",
    "company": None,
    "project": None,
    "subprojects": [],
    "theme": "light"
}

# ---------- State ----------
class AppState:
    def __init__(self):
        self.config = self._load_auth()
        self.user = self.config.get("user")
        self.workspace_name = self.config.get("workspace", "default")
        self.company = self.config.get("company")
        self.project = self.config.get("project")
        self.subprojects = self.config.get("subprojects", [])
        self.theme = self.config.get("theme", "light")

    def _load_auth(self):
        if AUTH_FILE.exists():
            try:
                return json.loads(AUTH_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return dict(DEFAULT_CONFIG)

    def save(self):
        data = {
            "user": self.user,
            "workspace": self.workspace_name,
            "company": self.company,
            "project": self.project,
            "subprojects": self.subprojects,
            "theme": self.theme,
        }
        AUTH_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

# ---------- Plugin Loader ----------
@dataclass
class Layer:
    id: str
    name: str
    floor: int
    module: ModuleType
    build: callable

def discover_layers() -> list[Layer]:
    layers = []
    for file in sorted(Z_AXIS_DIR.glob("*.py")):
        spec = importlib.util.spec_from_file_location(file.stem, file)
        if not spec or not spec.loader:
            continue
        mod = importlib.util.module_from_spec(spec)
        sys.modules[file.stem] = mod
        try:
            spec.loader.exec_module(mod)  # type: ignore
        except Exception as e:
            print(f"[warn] failed to load {file}: {e}", file=sys.stderr)
            continue
        if not hasattr(mod, "build"):
            continue
        lid    = getattr(mod, "LAYER_ID", file.stem)
        lname  = getattr(mod, "LAYER_NAME", file.stem)
        lfloor = getattr(mod, "LAYER_FLOOR", 0)
        layers.append(Layer(lid, lname, lfloor, mod, mod.build))
    # Sort by floor (-3..+4)
    return sorted(layers, key=lambda l: l.floor)

# ---------- UI ----------
class LauncherApp(tk.Tk):
    def __init__(self, state: AppState, layers: list[Layer]):
        super().__init__()
        self.state = state
        self.layers = layers
        self.title("Immersive Venv Launcher — Z Axis")
        self.geometry("1600x900")

        # Notebook for tabs
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)

        for layer in self.layers:
            try:
                frm = layer.build(self, self.nb)
                self.nb.add(frm, text=layer.name)
            except Exception as e:
                frm = ttk.Frame(self.nb)
                ttk.Label(frm, text=f"Failed to load {layer.name}: {e}").pack(padx=20, pady=20)
                self.nb.add(frm, text=f"{layer.name} (error)")

        # Quick switcher
        self.bind_all("<Control-Tab>", self._next_tab)
        self.bind_all("<Shift-Control-Tab>", self._prev_tab)

        # Menu
        self._build_menu()

        # Apply theme
        self._apply_theme()

        # On startup: auth / project selection if missing
        self.after(100, self._startup_checks)

    # ---- menu ----
    def _build_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        filem = tk.Menu(menubar, tearoff=False)
        filem.add_command(label="Switch Workspace", command=self._switch_workspace)
        filem.add_command(label="Change Theme", command=self._toggle_theme)
        filem.add_separator()
        filem.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=filem)

        projm = tk.Menu(menubar, tearoff=False)
        projm.add_command(label="Select Company", command=self._choose_company)
        projm.add_command(label="Select Project", command=self._choose_project)
        projm.add_command(label="Add Subproject", command=self._add_subproject)
        menubar.add_cascade(label="Projects", menu=projm)

    def _apply_theme(self):
        if self.state.theme == "dark":
            self.tk_setPalette(background="#1e1e1e", foreground="#d4d4d4")
        else:
            self.tk_setPalette(background="#f5f5f5", foreground="#000")

    def _toggle_theme(self):
        self.state.theme = "dark" if self.state.theme == "light" else "light"
        self.state.save()
        self._apply_theme()

    # ---- workspace ----
    def _switch_workspace(self):
        ws = simpledialog.askstring("Workspace", "Enter workspace name:")
        if ws:
            self.state.workspace_name = ws
            self.state.save()
            messagebox.showinfo("Workspace", f"Workspace switched to {ws}. Restart recommended.")

    # ---- company/project ----
    def _choose_company(self):
        c = simpledialog.askstring("Company", "Enter company name:")
        if c:
            self.state.company = c
            self.state.save()

    def _choose_project(self):
        p = simpledialog.askstring("Project", "Enter project name:")
        if p:
            self.state.project = p
            self.state.save()

    def _add_subproject(self):
        s = simpledialog.askstring("Subproject", "Enter subproject name:")
        if s:
            self.state.subprojects.append(s)
            self.state.save()

    # ---- startup ----
    def _startup_checks(self):
        if not self.state.user:
            u = simpledialog.askstring("Login", "Enter username:")
            if not u:
                self.quit(); return
            self.state.user = u
            self.state.save()
        if not self.state.company:
            self._choose_company()
        if not self.state.project:
            self._choose_project()

    # ---- tab switching ----
    def _next_tab(self, event=None):
        idx = self.nb.index(self.nb.select())
        self.nb.select((idx + 1) % len(self.nb.tabs()))

    def _prev_tab(self, event=None):
        idx = self.nb.index(self.nb.select())
        self.nb.select((idx - 1) % len(self.nb.tabs()))

# ---------- main ----------
def main():
    state = AppState()
    layers = discover_layers()
    app = LauncherApp(state, layers)
    app.mainloop()

if __name__ == "__main__":
    main()
