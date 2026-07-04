"""
LightSpeed 5.1.2 - Smart Settings Hub
Ultra-condensed settings with multi-facet navigation and smart toggles

Reduces tabs from 6 to 3 MAIN tabs with faceted sub-navigation:
1. Platform (General + Z-Floors with smart toggles)
2. Features (Spatial UI + AI with integrated controls)
3. System (Advanced + About with expandable sections)

Features:
- Multi-facet navigation (expandable sections within tabs)
- Smart toggles (enable/disable entire feature sets)
- Condensed view (more settings visible at once)
- Quick access shortcuts
- Live preview panels
- Integrated wizards access

Author: LightSpeed Team / ACHILLES
Version: 5.1.2
Date: April 8, 2026
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from core.config.paths import TRINITY_SETTINGS, LIGHTSPEED_ROOT

try:
    from lightspeed_runtime.startup_options import (
        startup_setting_defaults,
        startup_summary_lines,
        write_startup_option_values,
    )
except Exception:
    startup_setting_defaults = None
    startup_summary_lines = None
    write_startup_option_values = None

SETTINGS_HUB_TAB_INDEX = {
    "general": 0,
    "page": 0,
    "zfloors": 0,
    "spatial": 1,
    "backgrounds": 1,
    "ai": 1,
    "database": 2,
    "performance": 2,
    "startup_options": 2,
    "tailoring": 2,
    "setup_state": 2,
    "trinity_launchers": 2,
    "about": 2,
}

SETTINGS_HUB_FOCUS_ALIASES = {
    "theme": "trinity_launchers",
    "themes": "trinity_launchers",
    "template": "trinity_launchers",
    "templates": "trinity_launchers",
    "profile": "setup_state",
    "profiles": "setup_state",
    "account": "setup_state",
    "accounts": "setup_state",
    "user": "setup_state",
    "users": "setup_state",
    "company": "setup_state",
    "companies": "setup_state",
    "wizard": "setup_state",
    "wizards": "setup_state",
    "startup": "startup_options",
    "autostart": "startup_options",
    "launch": "startup_options",
    "boot": "startup_options",
    "background": "backgrounds",
    "backgrounds": "backgrounds",
    "wallpaper": "backgrounds",
    "environment": "backgrounds",
}


@dataclass
class SettingGroup:
    """Group of related settings with toggle"""
    name: str
    enabled_key: str  # Key for master enable/disable
    settings: List[str]  # List of setting keys in this group
    # ASCII-only label support (avoid emoji/mojibake in some Windows terminals).
    icon: str = ""
    collapsible: bool = True


class SmartSettingsHub:
    """
    Ultra-condensed settings hub with smart navigation.

    3 main tabs instead of 6, with faceted sub-navigation.
    """

    def __init__(self, parent: Optional[tk.Misc] = None, host: Optional[object] = None):
        """Initialize smart settings hub.

        `parent` controls window ownership (Toplevel parenting).
        `host` is the application host that implements optional actions (tailoring resets, etc.).
        """
        self.parent = parent
        self.host = host or parent
        self.window: Optional[tk.Toplevel] = None
        self._notebook: Optional[ttk.Notebook] = None

        # Optional IT/Portal caller context (used for Page Settings).
        self.page_context: Dict[str, str] = {}
        self._focus_section: str = ""

        # Settings storage
        self.settings: Dict[str, Any] = {}
        self.widgets: Dict[str, tk.Widget] = {}
        self.group_frames: Dict[str, tk.Frame] = {}
        self.collapsed_groups: set = set()

        # Load settings
        self.load_settings()

    def load_settings(self):
        """Load settings from Trinity"""
        settings_file = TRINITY_SETTINGS / "smart_settings.json"

        try:
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
            else:
                self.settings = self._get_defaults()
        except Exception as e:
            print(f"[SMART SETTINGS] Load error: {e}")
            self.settings = self._get_defaults()
        self._merge_runtime_startup_defaults()

    def _get_defaults(self) -> Dict[str, Any]:
        """Get default settings"""
        return {
            # Platform
            "app.theme": "dark",
            "app.language": "en",
            "ui.window_width": 1400,
            "ui.window_height": 900,
            "ui.font_size": 10,

            # Z-Floors (master toggle + individual)
            "zfloors.enabled": True,
            "zfloors.neo_enabled": True,
            "zfloors.morpheus_enabled": True,
            "zfloors.architect_enabled": True,
            "zfloors.construct_enabled": True,
            "zfloors.oracle_enabled": True,
            "zfloors.smith_enabled": True,
            "zfloors.merovingian_enabled": True,
            "zfloors.trinity_enabled": True,
            "zfloors.navigation_style": "dropdown",

            # Spatial UI (master toggle)
            "spatial.enabled": True,
            "spatial.radius": 1.5,
            "spatial.fov_range": 100,
            "spatial.glass_enabled": True,
            "spatial.parallax_strength": 0.3,
            "background.mode": "balanced",
            "background.input_type": "multi_stop_gradient",
            "background.gradient": "#0A4D4D,#191970,#123524",
            "background.image_path": "",
            "background.environment_reference": "",
            "background.scope": "workspace",

            # AI (master toggle)
            "ai.enabled": False,
            "ai.ollama_url": "http://localhost:11434",
            "ai.model": "llama2",
            "ai.temperature": 0.7,

            # System
            "db.auto_backup": True,
            "startup.show_splash_screen": True,
            "startup.z_floor_dropdown_enabled": True,
            "startup.ollama_auto_start": False,
            "startup.web_server_auto_start": False,
            "startup.db_auto_backup": True,
            "startup.db_vacuum_on_startup": False,
            "startup.max_concurrent_jobs": 4,
            "api.timeout": 30,
        }

    def _merge_runtime_startup_defaults(self) -> None:
        """Mirror startup defaults from canonical config without creating another source."""
        if not callable(startup_setting_defaults):
            return
        try:
            for key, value in startup_setting_defaults(Path(LIGHTSPEED_ROOT)).items():
                self.settings.setdefault(key, value)
        except Exception:
            return

    def save_settings(self):
        """Save settings to Trinity"""
        settings_file = TRINITY_SETTINGS / "smart_settings.json"

        try:
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            try:
                if callable(write_startup_option_values):
                    write_startup_option_values(Path(LIGHTSPEED_ROOT), self.settings)
            except Exception as e:
                print(f"[SMART SETTINGS] Startup option sync error: {e}")
            return True
        except Exception as e:
            print(f"[SMART SETTINGS] Save error: {e}")
            return False

    def open_dialog(self):
        """Open smart settings dialog (back-compat)."""
        return self.open_dialog_with_context()

    def open_dialog_with_context(self, *, context: Optional[Dict[str, str]] = None, focus_section: str = ""):
        """
        Open the Settings Hub and optionally focus to a section.

        context:
          - page_id: stable page identifier (e.g. "it.dashboard" or "floors.neo.portal")
          - label: human-readable context label for display
        """
        if context is not None:
            self.page_context = dict(context)
        if focus_section:
            self._focus_section = str(focus_section or "").strip()

        # Open smart settings dialog
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self._apply_focus_section()
            return

        # Create window
        if self.parent:
            self.window = tk.Toplevel(self.parent)
        else:
            root = tk.Tk()
            self.window = root

        self.window.title("LightSpeed Settings Hub")
        self.window.geometry("1000x700")
        self.window.configure(bg='#0A1628')

        self._create_ui()

    def _create_ui(self):
        """Create condensed UI"""
        # Title bar with quick actions
        title_bar = tk.Frame(self.window, bg='#102040', height=60)
        title_bar.pack(side=tk.TOP, fill=tk.X)
        title_bar.pack_propagate(False)

        tk.Label(
            title_bar,
            text="Settings Hub",
            font=('Segoe UI', 16, 'bold'),
            bg='#102040',
            fg='#00FFFF'
        ).pack(side=tk.LEFT, padx=20, pady=15)

        # Quick action buttons
        quick_frame = tk.Frame(title_bar, bg='#102040')
        quick_frame.pack(side=tk.RIGHT, padx=20)

        self._create_action_menu(
            quick_frame,
            text="Profile + Setup",
            commands=[
                ("Profiles + Company", lambda: self._focus_section_in_hub("setup_state")),
                ("Startup & Auto Options", lambda: self._focus_section_in_hub("startup_options")),
                ("Tailoring + Layout", lambda: self._focus_section_in_hub("tailoring")),
                ("Trinity Launchers", lambda: self._focus_section_in_hub("trinity_launchers")),
            ],
        ).pack(side=tk.LEFT, padx=3)

        for text, command in [
            ("Preview", self._show_preview),
            ("Import", self._import),
            ("Export", self._export)
        ]:
            tk.Button(
                quick_frame,
                text=text,
                command=command,
                bg='#1E3A5F',
                fg='#FFFFFF',
                font=('Segoe UI', 9),
                relief=tk.FLAT,
                padx=10,
                pady=5
            ).pack(side=tk.LEFT, padx=3)

        # Main content with 3 tabs
        content = tk.Frame(self.window, bg='#0A1628')
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        notebook = ttk.Notebook(content)
        notebook.pack(fill=tk.BOTH, expand=True)
        self._notebook = notebook

        # TAB 1: Platform (General + Z-Floors)
        self._create_platform_tab(notebook)

        # TAB 2: Features (Spatial + AI)
        self._create_features_tab(notebook)

        # TAB 3: System (Advanced + About)
        self._create_system_tab(notebook)

        self._apply_focus_section()

        # Button bar
        btn_bar = tk.Frame(self.window, bg='#0A1628', height=60)
        btn_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        btn_bar.pack_propagate(False)

        tk.Button(
            btn_bar,
            text="Reset All",
            command=self._reset_all,
            bg='#601010',
            fg='#FFFFFF',
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_bar,
            text="Cancel",
            command=self.window.destroy,
            bg='#252526',
            fg='#FFFFFF',
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=20,
            pady=8
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            btn_bar,
            text="Apply",
            command=self._apply,
            bg='#1E3A5F',
            fg='#FFFFFF',
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=20,
            pady=8
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            btn_bar,
            text="OK",
            command=self._ok,
            bg='#00FFFF',
            fg='#000000',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=30,
            pady=8
        ).pack(side=tk.RIGHT, padx=5)

    def _create_platform_tab(self, notebook: ttk.Notebook):
        """TAB 1: Platform settings (General + Z-Floors)"""
        tab = tk.Frame(notebook, bg='#0A1628')
        notebook.add(tab, text="Platform")

        # Scrollable
        canvas = tk.Canvas(tab, bg='#0A1628', highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=canvas.yview)
        content = tk.Frame(canvas, bg='#0A1628')

        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # SECTION: General
        self._create_collapsible_section(
            content,
            "general",
            "General Settings",
            [
                ("Theme", "app.theme", "choice", ["dark", "light", "matrix", "ocean"]),
                ("Language", "app.language", "choice", ["en", "es", "fr", "de", "ja"]),
                ("Window Width", "ui.window_width", "scale", (800, 3840, 100)),
                ("Window Height", "ui.window_height", "scale", (600, 2160, 100)),
                ("Font Size", "ui.font_size", "scale", (8, 24, 1)),
            ]
        )

        # SECTION: Page Settings (context-aware; called from IT Portal)
        page_frame = self._create_collapsible_section(
            content,
            "page",
            "Page Settings (Current Context)",
            [],
            collapsible=True,
        )
        if page_frame:
            ctx = dict(getattr(self, "page_context", {}) or {})
            page_id = str(ctx.get("page_id") or "").strip()
            label = str(ctx.get("label") or "").strip()

            tk.Label(
                page_frame,
                text=("Context: " + (label or "(none)")),
                bg="#0A1628",
                fg="#cfeaff",
                font=("Segoe UI", 9),
                justify=tk.LEFT,
            ).pack(anchor="w", padx=10, pady=(6, 2))

            tk.Label(
                page_frame,
                text=("Page ID: " + (page_id or "(unset)")),
                bg="#0A1628",
                fg="#AAAAAA",
                font=("Segoe UI", 9),
                justify=tk.LEFT,
            ).pack(anchor="w", padx=10, pady=(0, 8))

            if page_id:
                title_key = f"pages.{page_id}.title"
                blurb_key = f"pages.{page_id}.blurb"
                show_ask_key = f"pages.{page_id}.show_ask_achilles"
                show_bento_key = f"pages.{page_id}.show_bento"

                self._create_setting_row(page_frame, "Title Override", title_key, "string", None)
                self._create_setting_row(page_frame, "Blurb Override", blurb_key, "text", None)
                self._create_setting_row(page_frame, "Show Ask Achilles", show_ask_key, "bool", None)
                self._create_setting_row(page_frame, "Show Bento", show_bento_key, "bool", None)

                btns = tk.Frame(page_frame, bg="#0A1628")
                btns.pack(fill=tk.X, padx=10, pady=(8, 4))

                def _clear_overrides():
                    for k in (title_key, blurb_key, show_ask_key, show_bento_key):
                        try:
                            self.settings.pop(k, None)
                        except Exception:
                            pass
                        w = self.widgets.get(k)
                        try:
                            if hasattr(w, "var"):
                                if isinstance(getattr(w, "var", None), tk.BooleanVar):
                                    w.var.set(True)
                                else:
                                    w.var.set("")
                            elif isinstance(w, tk.Text):
                                w.delete("1.0", "end")
                        except Exception:
                            pass

                tk.Button(
                    btns,
                    text="Clear Overrides",
                    command=_clear_overrides,
                    bg="#601010",
                    fg="#FFFFFF",
                    font=("Segoe UI", 9, "bold"),
                    relief=tk.FLAT,
                    padx=12,
                    pady=6,
                ).pack(side=tk.LEFT)
            else:
                tk.Label(
                    page_frame,
                    text="Open this dialog from the IT Portal to edit the active page.",
                    bg="#0A1628",
                    fg="#AAAAAA",
                    font=("Segoe UI", 9),
                    justify=tk.LEFT,
                ).pack(anchor="w", padx=10, pady=(0, 8))

        # SECTION: Z-Floors (with master toggle)
        floor_frame = self._create_collapsible_section(
            content,
            "zfloors",
            "Z-Floor System",
            [],
            master_toggle="zfloors.enabled"
        )

        # Sub-content for Z-Floors
        if floor_frame:
            # Navigation style
            self._create_setting_row(
                floor_frame,
                "Navigation Style",
                "zfloors.navigation_style",
                "choice",
                ["dropdown", "sidebar", "tabs", "minimap"]
            )

            # Individual floor toggles (2 columns for compactness)
            floors_grid = tk.Frame(floor_frame, bg='#0A1628')
            floors_grid.pack(fill=tk.X, padx=10, pady=5)

            floors = [
                ("Neo", "neo"),
                ("Morpheus", "morpheus"),
                ("Architect", "architect"),
                ("TheConstruct", "construct"),
                ("Oracle", "oracle"),
                ("Smith", "smith"),
                ("Merovingian", "merovingian"),
                ("Trinity", "trinity")
            ]

            for i, (name, key) in enumerate(floors):
                col = i % 2
                row = i // 2

                check_var = tk.BooleanVar(value=self.settings.get(f"zfloors.{key}_enabled", True))
                check = tk.Checkbutton(
                    floors_grid,
                    text=name,
                    variable=check_var,
                    bg='#0A1628',
                    fg='#FFFFFF',
                    selectcolor='#102040',
                    activebackground='#0A1628',
                    font=('Segoe UI', 9)
                )
                check.grid(row=row, column=col, sticky=tk.W, padx=10, pady=2)
                check.var = check_var
                self.widgets[f"zfloors.{key}_enabled"] = check

    def _create_features_tab(self, notebook: ttk.Notebook):
        """TAB 2: Features (Spatial UI + AI)"""
        tab = tk.Frame(notebook, bg='#0A1628')
        notebook.add(tab, text="Features")

        # Scrollable
        canvas = tk.Canvas(tab, bg='#0A1628', highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=canvas.yview)
        content = tk.Frame(canvas, bg='#0A1628')

        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # SECTION: Spatial UI (with master toggle)
        spatial_frame = self._create_collapsible_section(
            content,
            "spatial",
            "Spatial UI (3D Interface)",
            [],
            master_toggle="spatial.enabled"
        )

        if spatial_frame:
            settings = [
                ("Bento Radius (locked)", "spatial.radius", "label", 1.5),
                ("Field of View Range", "spatial.fov_range", "scale", (60, 120, 10)),
                ("Enable Glass Morphism", "spatial.glass_enabled", "bool", None),
                ("Parallax Strength", "spatial.parallax_strength", "scale", (0.0, 1.0, 0.1)),
            ]

            for label, key, widget_type, config in settings:
                self._create_setting_row(spatial_frame, label, key, widget_type, config)

        background_frame = self._create_collapsible_section(
            content,
            "backgrounds",
            "Background Builder",
            [],
            collapsible=True,
        )

        if background_frame:
            tk.Label(
                background_frame,
                text=(
                    "Backgrounds are visual cues for the Bento wall. Uploaded images or environment references "
                    "stay as lightweight desktop/background inputs; heavy traversal remains Construct/Holospace-owned."
                ),
                bg="#0A1628",
                fg="#cfeaff",
                font=("Segoe UI", 9),
                justify=tk.LEFT,
                wraplength=820,
            ).pack(anchor="w", padx=10, pady=(6, 6))
            settings = [
                ("Base Theme Mode", "background.mode", "choice", ["minimal", "balanced", "futuristic_gamelike"]),
                ("Input Type", "background.input_type", "choice", ["solid_color", "multi_stop_gradient", "uploaded_picture", "uploaded_environment_reference"]),
                ("Gradient / Color", "background.gradient", "string", None),
                ("Uploaded Picture Path", "background.image_path", "string", None),
                ("Environment Reference", "background.environment_reference", "string", None),
                ("Apply Scope", "background.scope", "choice", ["workspace", "project", "floor", "global"]),
            ]
            for label, key, widget_type, config in settings:
                self._create_setting_row(background_frame, label, key, widget_type, config)

        # SECTION: AI & Ollama (with master toggle)
        ai_frame = self._create_collapsible_section(
            content,
            "ai",
            "AI & Ollama",
            [],
            master_toggle="ai.enabled"
        )

        if ai_frame:
            settings = [
                ("Ollama URL", "ai.ollama_url", "string", None),
                ("Model", "ai.model", "choice", ["llama2", "llama2:7b", "mistral", "codellama"]),
                ("Temperature", "ai.temperature", "scale", (0.0, 2.0, 0.1)),
            ]

            for label, key, widget_type, config in settings:
                self._create_setting_row(ai_frame, label, key, widget_type, config)

    def _create_system_tab(self, notebook: ttk.Notebook):
        """TAB 3: System (Advanced + About)"""
        tab = tk.Frame(notebook, bg='#0A1628')
        notebook.add(tab, text="System")

        # Scrollable
        canvas = tk.Canvas(tab, bg='#0A1628', highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=canvas.yview)
        content = tk.Frame(canvas, bg='#0A1628')

        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # SECTION: Database
        self._create_collapsible_section(
            content,
            "database",
            "Database",
            [
                ("Auto Backup", "db.auto_backup", "bool", None),
            ]
        )

        # SECTION: Performance
        self._create_collapsible_section(
            content,
            "performance",
            "Performance",
            [
                ("Max Concurrent Jobs", "startup.max_concurrent_jobs", "scale", (1, 16, 1)),
            ]
        )

        startup_frame = self._create_collapsible_section(
            content,
            "startup_options",
            "Startup & Auto Options",
            [
                ("Show Splash Screen", "startup.show_splash_screen", "bool", None),
                ("Use Z Floor Dropdown", "startup.z_floor_dropdown_enabled", "bool", None),
                ("Auto-start Ollama", "startup.ollama_auto_start", "bool", None),
                ("Auto-start Web Server", "startup.web_server_auto_start", "bool", None),
                ("Auto Backup Database", "startup.db_auto_backup", "bool", None),
                ("Vacuum DB on Startup", "startup.db_vacuum_on_startup", "bool", None),
            ],
            collapsible=True,
        )

        if startup_frame:
            tk.Label(
                startup_frame,
                text=(
                    "These global startup toggles write to config/settings.json. "
                    "Per-floor autostart is shown below as read-only runtime policy."
                ),
                bg="#0A1628",
                fg="#cfeaff",
                font=("Segoe UI", 9),
                justify=tk.LEFT,
                wraplength=820,
            ).pack(anchor="w", padx=10, pady=(6, 4))

            summary = []
            try:
                if callable(startup_summary_lines):
                    summary = startup_summary_lines(Path(LIGHTSPEED_ROOT))
            except Exception:
                summary = []
            if summary:
                for line in summary:
                    tk.Label(
                        startup_frame,
                        text="- " + str(line),
                        bg="#0A1628",
                        fg="#AAAAAA",
                        font=("Segoe UI", 9),
                        anchor=tk.W,
                        justify=tk.LEFT,
                    ).pack(anchor="w", padx=18, pady=1)

        # SECTION: User Tailoring (per-user; delegated to host when available)
        tailoring_frame = self._create_collapsible_section(
            content,
            "tailoring",
            "Tailoring (Per User)",
            [],
            collapsible=True,
        )

        if tailoring_frame:
            host = self.host
            user_id = ""
            try:
                getter = getattr(host, "_current_user_id_for_bento", None)
                if callable(getter):
                    user_id = str(getter() or "").strip()
            except Exception:
                user_id = ""

            tk.Label(
                tailoring_frame,
                text=(
                    "Tailoring is per-user (preferences, Bento layout/recents/favorites, OKRs, Notes).\n"
                    "Reset does NOT delete vault contents or durable registries."
                ),
                bg="#0A1628",
                fg="#cfeaff",
                font=("Segoe UI", 9),
                justify=tk.LEFT,
            ).pack(anchor="w", padx=10, pady=(6, 6))

            tk.Label(
                tailoring_frame,
                text=f"Active user: {user_id or '(unknown)'}",
                bg="#0A1628",
                fg="#AAAAAA",
                font=("Segoe UI", 9),
                justify=tk.LEFT,
            ).pack(anchor="w", padx=10, pady=(0, 10))

            btns = tk.Frame(tailoring_frame, bg="#0A1628")
            btns.pack(fill=tk.X, padx=10, pady=(0, 8))

            def _call_host(name: str, **kwargs):
                fn = getattr(host, name, None)
                if callable(fn):
                    return fn(**kwargs) if kwargs else fn()
                messagebox.showinfo(
                    "Unavailable",
                    "This action is only available when the Settings Hub is opened from N (host context).",
                    parent=self.window,
                )
                return None

            tk.Button(
                btns,
                text="Reset Tailoring",
                command=lambda: _call_host("reset_tailoring", confirm=True),
                bg="#601010",
                fg="#FFFFFF",
                font=("Segoe UI", 9, "bold"),
                relief=tk.FLAT,
                padx=12,
                pady=6,
            ).pack(side=tk.LEFT, padx=(0, 8))

            # Immersive unpin toggle (per-user)
            unpin_var = tk.BooleanVar(value=False)
            try:
                fn = getattr(host, "_immersive_unpinned", None)
                if callable(fn):
                    unpin_var.set(bool(fn()))
            except Exception:
                pass

            def _apply_unpin():
                try:
                    _call_host("set_immersive_unpinned", enabled=bool(unpin_var.get()))
                except Exception:
                    pass

            tk.Checkbutton(
                btns,
                text="Allow immersive controls (unpinned)",
                variable=unpin_var,
                command=_apply_unpin,
                bg="#0A1628",
                fg="#00FFFF",
                selectcolor="#102040",
                activebackground="#0A1628",
                font=("Segoe UI", 9, "bold"),
            ).pack(side=tk.LEFT, padx=(6, 0))

            # Optional: stage V1R definitions (append-only; commit via IT Portal)
            if callable(getattr(host, "stage_v1r_definitions", None)):
                tk.Button(
                    btns,
                    text="Stage V1R (Z Direct)",
                    command=lambda: _call_host("stage_v1r_definitions", confirm=True),
                    bg="#1E3A5F",
                    fg="#FFFFFF",
                    font=("Segoe UI", 9, "bold"),
                    relief=tk.FLAT,
                    padx=12,
                    pady=6,
                ).pack(side=tk.RIGHT)

        # SECTION: Setup State (launcher-level markers)
        setup_frame = self._create_collapsible_section(
            content,
            "setup_state",
            "Setup State (First-Run)",
            [],
            collapsible=True,
        )

        if setup_frame:
            host = self.host

            tk.Label(
                setup_frame,
                text=(
                    "Profiles, company bootstrap, and launch-state recovery stay in this hub-first flow.\n"
                    "Resetting setup state replays the first-run wizard flow.\n"
                    "This only removes setup marker/resume files. It does NOT delete DB/vault/registries."
                ),
                bg="#0A1628",
                fg="#cfeaff",
                font=("Segoe UI", 9),
                justify=tk.LEFT,
            ).pack(anchor="w", padx=10, pady=(6, 8))

            btns = tk.Frame(setup_frame, bg="#0A1628")
            btns.pack(fill=tk.X, padx=10, pady=(0, 8))

            def _call_host(name: str, **kwargs):
                fn = getattr(host, name, None)
                if callable(fn):
                    return fn(**kwargs) if kwargs else fn()
                messagebox.showinfo(
                    "Unavailable",
                    "This action is only available when the Settings Hub is opened from N (host context).",
                    parent=self.window,
                )
                return None

            tk.Button(
                btns,
                text="Reset Setup State",
                command=lambda: _call_host("reset_first_run_state", confirm=True),
                bg="#601010",
                fg="#FFFFFF",
                font=("Segoe UI", 9, "bold"),
                relief=tk.FLAT,
                padx=12,
                pady=6,
            ).pack(side=tk.LEFT, padx=(0, 8))

            self._create_action_menu(
                btns,
                text="Profile + Setup",
                commands=[
                    ("Profiles + Company", lambda: self._focus_section_in_hub("setup_state")),
                    ("Startup & Auto Options", lambda: self._focus_section_in_hub("startup_options")),
                    ("Tailoring + Layout", lambda: self._focus_section_in_hub("tailoring")),
                    ("Startup Diagnostics", self._launch_startup_diagnostics),
                    ("Enhanced Startup Wizard", self._launch_enhanced_startup_wizard),
                ],
            ).pack(side=tk.LEFT)

        trinity_frame = self._create_collapsible_section(
            content,
            "trinity_launchers",
            "Trinity Theme & Templates",
            [],
            collapsible=True,
        )

        if trinity_frame:
            tk.Label(
                trinity_frame,
                text=(
                    "Open Trinity-owned theme and template tools from this page.\n"
                    "Settings remain under Trinity roots; no root-relative writes are used."
                ),
                bg="#0A1628",
                fg="#cfeaff",
                font=("Segoe UI", 9),
                justify=tk.LEFT,
            ).pack(anchor="w", padx=10, pady=(6, 8))

            btns = tk.Frame(trinity_frame, bg="#0A1628")
            btns.pack(fill=tk.X, padx=10, pady=(0, 8))

            self._create_action_menu(
                btns,
                text="Trinity Tools",
                commands=[
                    ("Open Theme Designer", self._launch_theme_designer),
                    ("Open Template Manager", self._launch_template_manager),
                ],
            ).pack(side=tk.LEFT)

        # SECTION: About (read-only)
        about_frame = self._create_collapsible_section(
            content,
            "about",
            "About",
            [],
            collapsible=True
        )

        if about_frame:
            info = [
            ("Version", "LightSpeed 5.1.2"),
            ("Build Date", "April 8, 2026"),
                ("Author", "LightSpeed Team / ACHILLES"),
                ("Root", str(LIGHTSPEED_ROOT)),
            ]

            for label, value in info:
                row = tk.Frame(about_frame, bg='#0A1628')
                row.pack(fill=tk.X, padx=10, pady=2)

                tk.Label(
                    row,
                    text=f"{label}:",
                    bg='#0A1628',
                    fg='#AAAAAA',
                    font=('Segoe UI', 9),
                    width=15,
                    anchor=tk.W
                ).pack(side=tk.LEFT)

                tk.Label(
                    row,
                    text=value,
                    bg='#0A1628',
                    fg='#FFFFFF',
                    font=('Segoe UI', 9),
                    anchor=tk.W
                ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _create_collapsible_section(
        self,
        parent: tk.Frame,
        section_id: str,
        title: str,
        settings: List[tuple],
        master_toggle: Optional[str] = None,
        collapsible: bool = True
    ) -> Optional[tk.Frame]:
        """Create a collapsible section with optional master toggle"""
        # Header
        header = tk.Frame(parent, bg='#102040', height=40)
        header.pack(fill=tk.X, padx=5, pady=(10, 0))
        header.pack_propagate(False)

        # Collapse button
        if collapsible:
            collapse_btn = tk.Label(
                header,
                text="v" if section_id not in self.collapsed_groups else ">",
                bg='#102040',
                fg='#00FFFF',
                font=('Segoe UI', 12),
                cursor='hand2'
            )
            collapse_btn.pack(side=tk.LEFT, padx=10)
            collapse_btn.bind('<Button-1>', lambda e, sid=section_id: self._toggle_collapse(sid))

        # Title
        tk.Label(
            header,
            text=title,
            font=('Segoe UI', 11, 'bold'),
            bg='#102040',
            fg='#00FFFF',
            anchor=tk.W
        ).pack(side=tk.LEFT, padx=5)

        # Master toggle (if provided)
        if master_toggle:
            toggle_var = tk.BooleanVar(value=self.settings.get(master_toggle, True))
            toggle = tk.Checkbutton(
                header,
                text="Enabled",
                variable=toggle_var,
                bg='#102040',
                fg='#FFFFFF',
                selectcolor='#1E3A5F',
                activebackground='#102040',
                font=('Segoe UI', 9, 'bold')
            )
            toggle.pack(side=tk.RIGHT, padx=10)
            toggle.var = toggle_var
            self.widgets[master_toggle] = toggle

        # Content frame
        content_frame = tk.Frame(parent, bg='#0A1628')
        if section_id not in self.collapsed_groups:
            content_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        self.group_frames[section_id] = content_frame

        # Add settings
        for setting in settings:
            label, key, widget_type, config = setting
            self._create_setting_row(content_frame, label, key, widget_type, config)

        return content_frame

    def _create_setting_row(
        self,
        parent: tk.Frame,
        label: str,
        key: str,
        widget_type: str,
        config: Any
    ):
        """Create a single setting row"""
        row = tk.Frame(parent, bg='#0A1628')
        row.pack(fill=tk.X, padx=10, pady=3)

        # Label (30% width)
        tk.Label(
            row,
            text=label,
            bg='#0A1628',
            fg='#FFFFFF',
            font=('Segoe UI', 9),
            width=25,
            anchor=tk.W
        ).pack(side=tk.LEFT)

        # Widget (70% width)
        widget_frame = tk.Frame(row, bg='#0A1628')
        widget_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        current_value = self.settings.get(key)

        if widget_type == "bool":
            var = tk.BooleanVar(value=current_value if current_value is not None else False)
            widget = tk.Checkbutton(
                widget_frame,
                variable=var,
                bg='#0A1628',
                fg='#00FFFF',
                selectcolor='#102040',
                activebackground='#0A1628'
            )
            widget.pack(side=tk.LEFT)
            widget.var = var
            self.widgets[key] = widget

        elif widget_type == "choice":
            var = tk.StringVar(value=current_value if current_value else config[0])
            combo = ttk.Combobox(
                widget_frame,
                textvariable=var,
                values=config,
                state='readonly',
                width=20
            )
            combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
            combo.var = var
            self.widgets[key] = combo

        elif widget_type == "scale":
            min_val, max_val, step = config
            var = tk.DoubleVar(value=current_value if current_value is not None else min_val)
            scale = tk.Scale(
                widget_frame,
                from_=min_val,
                to=max_val,
                resolution=step,
                orient=tk.HORIZONTAL,
                variable=var,
                bg='#102040',
                fg='#00FFFF',
                highlightthickness=0,
                troughcolor='#0A1628'
            )
            scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
            scale.var = var
            self.widgets[key] = scale

        elif widget_type == "string":
            var = tk.StringVar(value=current_value if current_value else "")
            entry = tk.Entry(
                widget_frame,
                textvariable=var,
                bg='#102040',
                fg='#FFFFFF',
                font=('Segoe UI', 9),
                insertbackground='#00FFFF'
            )
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            entry.var = var
            self.widgets[key] = entry

        elif widget_type == "text":
            txt = scrolledtext.ScrolledText(
                widget_frame,
                height=4,
                bg="#102040",
                fg="#FFFFFF",
                font=("Segoe UI", 9),
                insertbackground="#00FFFF",
                wrap=tk.WORD,
            )
            try:
                if current_value:
                    txt.insert("1.0", str(current_value))
            except Exception:
                pass
            txt.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.widgets[key] = txt

        elif widget_type == "label":
            tk.Label(
                widget_frame,
                text=str(config),
                bg='#0A1628',
                fg='#888888',
                font=('Segoe UI', 9),
                anchor=tk.W
            ).pack(side=tk.LEFT)

    def _toggle_collapse(self, section_id: str):
        """Toggle section collapse"""
        if section_id in self.collapsed_groups:
            self.collapsed_groups.remove(section_id)
            self.group_frames[section_id].pack(fill=tk.X, padx=5, pady=(0, 5))
        else:
            self.collapsed_groups.add(section_id)
            self.group_frames[section_id].pack_forget()

        # Update arrow - would need to store button reference
        # For now, just close/reopen dialog to update

    def _normalize_focus_section(self, section_id: str) -> str:
        section = str(section_id or "").strip().lower()
        return SETTINGS_HUB_FOCUS_ALIASES.get(section, section)

    def _focus_section_in_hub(self, section_id: str) -> None:
        self._focus_section = self._normalize_focus_section(section_id)
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self._apply_focus_section()

    def _apply_focus_section(self) -> None:
        notebook = self._notebook
        section_id = self._normalize_focus_section(getattr(self, "_focus_section", ""))
        if notebook is None or not section_id:
            return

        tab_index = SETTINGS_HUB_TAB_INDEX.get(section_id)
        if tab_index is not None:
            try:
                notebook.select(tab_index)
            except Exception:
                pass

        frame = self.group_frames.get(section_id)
        if frame is None:
            return

        if section_id in self.collapsed_groups:
            self.collapsed_groups.discard(section_id)
            try:
                frame.pack(fill=tk.X, padx=5, pady=(0, 5))
            except Exception:
                pass

        try:
            frame.update_idletasks()
        except Exception:
            pass

    def _load_symbol_from_file(self, rel_path: str, symbol: str):
        import importlib.util
        import sys

        path = (LIGHTSPEED_ROOT / rel_path).resolve()
        spec = importlib.util.spec_from_file_location(f"lightspeed_trinity_{path.stem}", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load {symbol} from {path}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        return getattr(mod, symbol)

    def _safe_launch(self, launcher, *, title: str) -> None:
        try:
            launcher()
        except Exception as e:
            parent = self.window if self.window and self.window.winfo_exists() else self.parent
            messagebox.showerror(title, str(e), parent=parent)

    def _create_action_menu(self, parent: tk.Misc, *, text: str, commands: List[tuple]) -> tk.Menubutton:
        """Create a compact dropdown action button for Trinity hub launchers."""
        button = tk.Menubutton(
            parent,
            text=text,
            bg="#1E3A5F",
            fg="#FFFFFF",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=6,
            activebackground="#274B73",
            activeforeground="#FFFFFF",
        )
        menu = tk.Menu(button, tearoff=0, bg="#0A1628", fg="#FFFFFF")
        for label, command in commands:
            menu.add_command(label=label, command=command)
        button.config(menu=menu)
        return button

    def _open_wizards(self):
        """Route operators to the integrated setup tools section."""
        self._focus_section_in_hub("setup_state")

    def _launch_setup_wizard(self) -> None:
        """Open the Settings Hub setup section instead of spawning a separate wizard page."""
        if self.window and self.window.winfo_exists():
            self._focus_section_in_hub("setup_state")
            return
        self._safe_launch(lambda: self._focus_section_in_hub("setup_state"), title="Setup Hub")

    def _launch_startup_diagnostics(self) -> None:
        def launcher():
            fn = self._load_symbol_from_file(
                "Z Axis/Z+3_Trinity/wizards/startup_wizard.py",
                "main",
            )
            fn()

        self._safe_launch(launcher, title="Startup Diagnostics")

    def _launch_enhanced_startup_wizard(self) -> None:
        def launcher():
            fn = self._load_symbol_from_file(
                "Z Axis/Z+3_Trinity/wizards/enhanced_startup_wizard.py",
                "launch_enhanced_startup_wizard",
            )
            fn(parent=self.window)

        self._safe_launch(launcher, title="Enhanced Startup Wizard")

    def _launch_theme_designer(self) -> None:
        def launcher():
            theme_cls = self._load_symbol_from_file(
                "Z Axis/Z+3_Trinity/components/theme_switcher.py",
                "ThemeDesigner",
            )
            win = tk.Toplevel(self.window)
            win.title("Trinity Theme Designer")
            win.geometry("1280x860")
            win.configure(bg="#1e1e1e")
            theme_cls(win).pack(fill=tk.BOTH, expand=True)

        self._safe_launch(launcher, title="Theme Designer")

    def _launch_template_manager(self) -> None:
        def launcher():
            dialog_cls = self._load_symbol_from_file(
                "Z Axis/Z+3_Trinity/ui/template_manager.py",
                "TemplateManagerDialog",
            )
            dialog_cls(self.window)

        self._safe_launch(launcher, title="Template Manager")

    def _show_preview(self):
        """Show live preview"""
        import json as _json

        win = tk.Toplevel(self.window)
        win.title("LightSpeed Preview")
        win.geometry("1000x700")
        win.configure(bg="#0A1628")

        tk.Label(
            win,
            text="Preview",
            bg="#0A1628",
            fg="#00FFFF",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=(16, 6))

        tk.Label(
            win,
            text="This preview reflects current settings values loaded in the hub.\n"
                 "Use Bento Preview to see the curved widget grid in 2D fallback.",
            bg="#0A1628",
            fg="#cfeaff",
            font=("Segoe UI", 10),
        ).pack(pady=(0, 10))

        top = tk.Frame(win, bg="#0A1628")
        top.pack(fill="x", padx=16)

        def _open_bento_preview():
            try:
                from ui.universal_bento_system import get_bento_system  # type: ignore
                get_bento_system().create_2d_window()
            except Exception as e:
                messagebox.showerror("Bento Preview", str(e), parent=win)

        tk.Button(
            top,
            text="Open Bento Preview",
            bg="#183046",
            fg="#cfeaff",
            relief=tk.FLAT,
            padx=12,
            pady=8,
            command=_open_bento_preview,
        ).pack(side="left")

        body = tk.Text(win, bg="#0b141d", fg="#cfeaff", insertbackground="#cfeaff")
        body.pack(fill="both", expand=True, padx=16, pady=16)
        try:
            body.insert("1.0", _json.dumps(self.settings, indent=2))
        except Exception:
            body.insert("1.0", str(self.settings))

    def _import(self):
        """Import settings"""
        file_path = filedialog.askopenfilename(
            title="Import Settings",
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                messagebox.showinfo("Import", "Settings imported successfully")
                # Refresh UI
                self.window.destroy()
                self.open_dialog()
            except Exception as e:
                messagebox.showerror("Import", f"Failed: {e}")

    def _export(self):
        """Export settings"""
        file_path = filedialog.asksaveasfilename(
            title="Export Settings",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, indent=2)
                messagebox.showinfo("Export", "Settings exported successfully")
            except Exception as e:
                messagebox.showerror("Export", f"Failed: {e}")

    def _reset_all(self):
        """Reset all settings"""
        if messagebox.askyesno("Reset", "Reset all settings to defaults?"):
            self.settings = self._get_defaults()
            self.window.destroy()
            self.open_dialog()

    def _apply(self):
        """Apply settings"""
        self._collect_values()
        if self.save_settings():
            messagebox.showinfo("Settings", "Applied successfully")
        else:
            messagebox.showerror("Settings", "Failed to save")

    def _ok(self):
        """Apply and close"""
        self._collect_values()
        if self.save_settings():
            self.window.destroy()
        else:
            messagebox.showerror("Settings", "Failed to save")

    def _collect_values(self):
        """Collect values from widgets"""
        for key, widget in self.widgets.items():
            if hasattr(widget, 'var'):
                self.settings[key] = widget.var.get()
            elif isinstance(widget, tk.Text):
                try:
                    self.settings[key] = widget.get("1.0", "end-1c")
                except Exception:
                    pass


def launch_smart_settings():
    """Launch smart settings hub"""
    hub = SmartSettingsHub()
    hub.open_dialog()

    if hub.window and not isinstance(hub.window, tk.Toplevel):
        hub.window.mainloop()


if __name__ == "__main__":
    launch_smart_settings()


__all__ = ['SmartSettingsHub', 'launch_smart_settings']
