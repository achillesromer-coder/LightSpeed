# Launcher/first_run.py
from __future__ import annotations
import json, os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Resolve project folders relative to this file
LAUNCHER_DIR = Path(__file__).resolve().parent
ROOT = LAUNCHER_DIR.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = DATA_DIR / "config.json"
USERS_FILE  = DATA_DIR / "users.json"

# ----------------- Config I/O -----------------
def default_config() -> dict:
    return {
        "first_run": True,
        "theme": "light",          # "light" | "dark"
        "hidden_layers": [],       # list of LAYER_ID strings to hide
        "show_graph_tab": True,    # show the Graph sandbox tab
    }

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default_config()

def save_config(cfg: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def load_users() -> list[dict]:
    if USERS_FILE.exists():
        try:
            return json.loads(USERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []

def save_users(users: list[dict]) -> None:
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")

# ----------------- Theme -----------------
def apply_theme(app: tk.Tk, theme: str = "light") -> None:
    """Very lightweight ttk theming (no external deps)."""
    style = ttk.Style(app)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    if theme == "dark":
        bg  = "#1f2127"
        fg  = "#e8e8e8"
        acc = "#2d2f36"
        hi  = "#3a3d46"
        style.configure(".", background=bg, foreground=fg)
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TButton", background=acc, foreground=fg, padding=6)
        style.map("TButton", background=[("active", hi)])
        style.configure("TNotebook", background=bg, borderwidth=0)
        style.configure("TNotebook.Tab", background=acc, foreground=fg, padding=(10, 6))
        style.map("TNotebook.Tab", background=[("selected", hi)])
        style.configure("Treeview", background=acc, fieldbackground=acc, foreground=fg, borderwidth=0)
    else:
        # light
        bg  = "#f7f7f9"
        fg  = "#1d1d1f"
        acc = "#ffffff"
        hi  = "#e9ecf2"
        style.configure(".", background=bg, foreground=fg)
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TButton", background=acc, foreground=fg, padding=6)
        style.map("TButton", background=[("active", hi)])
        style.configure("TNotebook", background=bg, borderwidth=0)
        style.configure("TNotebook.Tab", background=acc, foreground=fg, padding=(10, 6))
        style.map("TNotebook.Tab", background=[("selected", hi)])
        style.configure("Treeview", background=acc, fieldbackground=acc, foreground=fg, borderwidth=0)

# ----------------- Wizard -----------------
def show_wizard(app: tk.Tk, layer_registry) -> dict | None:
    """
    Modal setup wizard. Returns a config dict (or None if cancelled).
    layer_registry: object with .modules (dict of {LAYER_ID: module})
    """
    cfg = load_config()
    users = load_users()

    win = tk.Toplevel(app)
    win.title("First-Run Setup")
    win.transient(app)
    win.grab_set()
    win.geometry("760x560")
    win.minsize(720, 520)

    nb = ttk.Notebook(win)
    nb.pack(fill="both", expand=True, padx=8, pady=8)

    # --- Page 1: Theme ---
    p_theme = ttk.Frame(nb); nb.add(p_theme, text="Theme")
    theme_var = tk.StringVar(value=cfg.get("theme", "light"))
    ttk.Label(p_theme, text="Choose a UI theme for the desktop shell.", font=("Arial", 12)).pack(anchor="w", padx=8, pady=(12,6))
    ttk.Radiobutton(p_theme, text="Light", value="light", variable=theme_var).pack(anchor="w", padx=12, pady=4)
    ttk.Radiobutton(p_theme, text="Dark",  value="dark",  variable=theme_var).pack(anchor="w", padx=12, pady=4)
    ttk.Checkbutton(p_theme, text="Show Graph tab (sandbox)", variable=tk.BooleanVar(value=cfg.get("show_graph_tab", True)),
                    command=lambda: None).pack_forget()  # legacy, handled below in controls

    # --- Page 2: Tabs (show/hide) ---
    p_tabs = ttk.Frame(nb); nb.add(p_tabs, text="Tabs")
    ttk.Label(p_tabs, text="Enable or hide layer tabs for this workspace.", font=("Arial", 12)).grid(row=0, column=0, sticky="w", padx=8, pady=(12,6))
    # Build a scrollable frame of checkbuttons for layers
    canvas = tk.Canvas(p_tabs, highlightthickness=0)
    scroll = ttk.Scrollbar(p_tabs, orient="vertical", command=canvas.yview)
    inner  = ttk.Frame(canvas)
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0,0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)
    canvas.grid(row=1, column=0, sticky="nsew", padx=(8,0), pady=(6,8))
    scroll.grid(row=1, column=1, sticky="ns", padx=(0,8), pady=(6,8))
    p_tabs.rowconfigure(1, weight=1); p_tabs.columnconfigure(0, weight=1)

    hidden = set(cfg.get("hidden_layers", []))
    layer_vars: dict[str, tk.BooleanVar] = {}
    ttk.Label(inner, text="Layer visibility:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0,6))
    for lid, mod in sorted(layer_registry.modules.items(), key=lambda kv: kv[1].__dict__.get("LAYER_NAME", kv[0])):
        v = tk.BooleanVar(value=(lid not in hidden))
        layer_vars[lid] = v
        cb = ttk.Checkbutton(inner, text=f"{getattr(mod, 'LAYER_NAME', lid)}  [{lid}]", variable=v)
        cb.pack(anchor="w", padx=6, pady=4)

    # Also allow toggling Graph tab (home is always on)
    graph_var = tk.BooleanVar(value=cfg.get("show_graph_tab", True))
    ttk.Separator(inner).pack(fill="x", pady=(10,6), padx=6)
    ttk.Checkbutton(inner, text="Show 'Graph' tab", variable=graph_var).pack(anchor="w", padx=6, pady=4)
    ttk.Label(inner, text="Note: 'Layer N' (home) is always enabled.", font=("Arial", 9)).pack(anchor="w", padx=8, pady=(4,8))

    # --- Page 3: Users ---
    p_users = ttk.Frame(nb); nb.add(p_users, text="Users")
    p_users.rowconfigure(1, weight=1)
    p_users.columnconfigure(1, weight=1)

    ttk.Label(p_users, text="Add users for this workspace (name, position, clearance).", font=("Arial", 12))\
        .grid(row=0, column=0, columnspan=3, sticky="w", padx=8, pady=(12,6))

    lb = tk.Listbox(p_users, height=12, width=28)
    lb.grid(row=1, column=0, rowspan=4, sticky="ns", padx=(8,6), pady=6)
    for u in users:
        lb.insert("end", f"{u.get('name','(no name)')} — {u.get('position','')}")

    # Editor panel
    editor = ttk.Frame(p_users); editor.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)
    editor.columnconfigure(1, weight=1)
    name_var      = tk.StringVar()
    company_var   = tk.StringVar(value="Romer / EMASSC")
    position_var  = tk.StringVar()
    clearance_var = tk.StringVar(value="Tier 1")
    avatar_var    = tk.StringVar()

    def _row(lbl, var, r):
        ttk.Label(editor, text=lbl).grid(row=r, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(editor, textvariable=var).grid(row=r, column=1, sticky="ew", padx=4, pady=4)

    _row("Name", name_var, 0)
    _row("Company", company_var, 1)
    _row("Position", position_var, 2)
    _row("Clearance", clearance_var, 3)

    def pick_avatar():
        p = filedialog.askopenfilename(title="Choose avatar", filetypes=[("Images","*.png;*.jpg;*.jpeg;*.gif"),("All","*.*")])
        if p: avatar_var.set(p)
    ttk.Label(editor, text="Avatar").grid(row=4, column=0, sticky="w", padx=4, pady=4)
    row4 = ttk.Frame(editor); row4.grid(row=4, column=1, sticky="ew")
    ttk.Entry(row4, textvariable=avatar_var).pack(side="left", fill="x", expand=True, padx=(0,4))
    ttk.Button(row4, text="Browse…", command=pick_avatar).pack(side="left")

    # Buttons
    def refresh_list():
        lb.delete(0, "end")
        for u in users:
            lb.insert("end", f"{u.get('name','(no name)')} — {u.get('position','')}")

    def clear_editor():
        name_var.set(""); position_var.set(""); clearance_var.set("Tier 1"); avatar_var.set("")

    def add_or_update():
        data = {
            "name": name_var.get().strip() or "(no name)",
            "company": company_var.get().strip(),
            "position": position_var.get().strip(),
            "clearance": clearance_var.get().strip(),
            "avatar": avatar_var.get().strip(),
        }
        if lb.curselection():
            users[lb.curselection()[0]] = data
        else:
            users.append(data)
        refresh_list(); clear_editor()

    def delete_sel():
        if lb.curselection():
            del users[lb.curselection()[0]]
            refresh_list(); clear_editor()

    btns = ttk.Frame(p_users); btns.grid(row=2, column=1, sticky="e", padx=6, pady=(0,6))
    ttk.Button(btns, text="Add / Update", command=add_or_update).pack(side="left", padx=4)
    ttk.Button(btns, text="Delete", command=delete_sel).pack(side="left", padx=4)

    # --- Footer ---
    footer = ttk.Frame(win); footer.pack(fill="x", padx=8, pady=(0,8))
    footer.columnconfigure(0, weight=1)

    def on_cancel():
        win.grab_release()
        win.destroy()

    def on_save():
        # Gather config
        hidden_layers = [lid for lid, var in layer_vars.items() if not var.get()]
        out = {
            "first_run": False,
            "theme": theme_var.get(),
            "hidden_layers": hidden_layers,
            "show_graph_tab": bool(graph_var.get()),
        }
        save_config(out)
        save_users(users)
        win.result = out
        win.grab_release()
        win.destroy()

    ttk.Button(footer, text="Cancel", command=on_cancel).pack(side="right", padx=4)
    ttk.Button(footer, text="Save", command=on_save).pack(side="right", padx=4)

    # Live preview theme toggle
    def _preview(*_):
        apply_theme(app, theme_var.get())
    theme_var.trace_add("write", _preview)

    # modal loop
    app.wait_window(win)
    return getattr(win, "result", None)
