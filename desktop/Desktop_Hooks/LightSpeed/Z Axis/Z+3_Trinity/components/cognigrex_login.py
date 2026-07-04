#!/usr/bin/env python
"""
COGNIGREX LOGIN PAGE
LightSpeed Consolidated Platform

Login interface displayed after setup completion.
Features:
- User selection from configured profiles
- Role-based interface loading
- IT Portal vs Dashboard selection
- 3D immersive toggle
- Quick access to floor navigation

Author: LightSpeed Team
Version: 5.1.0
Date: 2026-01-30
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import json
import sys
import importlib.util
import subprocess
from datetime import datetime

try:
    # Prefer the platform-wide sanitizer so alpha-hex and rgba() never crash Tk.
    from core.ui.glass_ui import tk_safe_color as _tk_safe_color
except Exception:  # pragma: no cover
    _tk_safe_color = None

# Path configuration
def _find_lightspeed_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
            return candidate
    return here.parents[3]


LIGHTSPEED_ROOT = _find_lightspeed_root()
CONFIG_ROOT = LIGHTSPEED_ROOT / "config"
SETUP_STATE_FILE = CONFIG_ROOT / "cognigrex_setup_state.json"
USER_CONFIG_FILE = CONFIG_ROOT / "user_config.json"
VERSION_FILE = LIGHTSPEED_ROOT / "VERSION"
UNIFIED_CONFIG_FILE = CONFIG_ROOT / "unified_config.json"
PREMIUM_THEME_FILE = CONFIG_ROOT / "premium_theme_config.json"
COGNIGREX_LOGIN_SETTINGS_CONTEXT = {
    "page_id": "trinity.cognigrex_login",
    "label": "Cognigrex Login / Profile + Setup",
}


def _read_version() -> str:
    try:
        v = VERSION_FILE.read_text(encoding="utf-8", errors="replace").strip()
        return v if v else "unknown"
    except Exception:
        return "unknown"


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def _tk_color(value: Any, fallback: str) -> str:
    """
    Tkinter color helper: sanitize rgba()/alpha-hex into Tk-safe colors.
    """
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return fallback
        if _tk_safe_color:
            # Blend onto fallback (always Tk-safe) to avoid hard failures.
            return _tk_safe_color(v, bg=fallback)
        # Best-effort fallback: ignore CSS rgba() strings.
        if v.lower().startswith("rgba"):
            return fallback
        return v
    return fallback


class CognigrexLogin:
    """
    Cognigrex Login Interface

    Displays after setup is complete, allowing users to:
    - Select their user profile
    - Choose launch mode (Dashboard, IT Portal, 3D Immersive)
    - Quick-access floor navigation
    """

    def __init__(self, parent: Optional[tk.Tk] = None, on_login: Optional[Callable] = None):
        # Window setup
        if parent is None:
            self.root = tk.Tk()
            self.standalone = True
        else:
            self.root = tk.Toplevel(parent)
            self.standalone = False

        self.on_login = on_login

        self.version = _read_version()
        self.root.title(f"Cognigrex Login - LightSpeed v{self.version}")
        self.root.geometry("800x600")
        self.root.configure(bg='#0a0a14')
        self.root.resizable(False, False)

        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 800) // 2
        y = (self.root.winfo_screenheight() - 600) // 2
        self.root.geometry(f"800x600+{x}+{y}")

        # Theme colors (Romer Premium; falls back safely when config files are missing)
        unified = _load_json(UNIFIED_CONFIG_FILE)
        ui_theme = unified.get("ui_theme") if isinstance(unified, dict) else {}
        ui_theme = ui_theme if isinstance(ui_theme, dict) else {}

        premium = _load_json(PREMIUM_THEME_FILE)
        palettes = premium.get("color_palettes") if isinstance(premium, dict) else {}
        palettes = palettes if isinstance(palettes, dict) else {}
        dark = palettes.get("dark_mode") if isinstance(palettes, dict) else {}
        dark = dark if isinstance(dark, dict) else {}

        self.font_title = str(ui_theme.get("font_title") or "Garamond")
        self.font_body = str(ui_theme.get("font_body") or "Arial")

        self.colors = {
            'bg_dark': _tk_color(ui_theme.get("background_color"), '#0a0a14'),
            'bg_panel': _tk_color(dark.get("secondary"), '#1a1a2e'),
            'bg_card': _tk_color(dark.get("accent_phthalo_green"), '#16213e'),
            'fg_primary': _tk_color(ui_theme.get("accent_color"), '#B8860B'),
            'fg_secondary': _tk_color(ui_theme.get("primary_color"), '#0A4D4D'),
            'fg_text': _tk_color(dark.get("text_primary"), '#FFFFFF'),
            'fg_muted': _tk_color(dark.get("text_secondary"), '#888888'),
            'success': _tk_color(dark.get("success"), '#00FF41'),
            'warning': _tk_color(dark.get("warning"), '#B8860B'),
            'error': _tk_color(dark.get("error"), '#FF4444'),
        }
        # Apply background now that theme is loaded.
        try:
            self.root.configure(bg=self.colors['bg_dark'])
        except Exception:
            pass

        # Load configuration
        self.users = self._load_users()
        self.selected_user = tk.StringVar()
        self.launch_mode = tk.StringVar(value='dashboard')
        self.immersive_3d = tk.BooleanVar(value=True)

        # Build UI
        self._build_ui()

    def _load_users(self) -> Dict[str, Dict]:
        """Load configured users"""
        users = {}

        # Try setup state first
        if SETUP_STATE_FILE.exists():
            try:
                with open(SETUP_STATE_FILE, 'r') as f:
                    state = json.load(f)
                    users = state.get('users', {})
            except Exception:
                pass

        # Fallback to user config
        if not users and USER_CONFIG_FILE.exists():
            try:
                with open(USER_CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    users = config.get('users', {})
            except Exception:
                pass

        # Default users if none found
        if not users:
            users = {
                'main': {
                    'username': 'User',
                    'display_name': 'Main User',
                    'role': 'main',
                    'clearance': 3,
                    'color': '#00DDFF',
                    'enabled': True
                },
                'it': {
                    'username': 'Admin',
                    'display_name': 'IT Admin',
                    'role': 'it',
                    'clearance': 4,
                    'color': '#FF00FF',
                    'enabled': True
                },
                'achilles': {
                    'username': 'Achilles',
                    'display_name': 'Achilles',
                    'role': 'achilles',
                    'clearance': 4,
                    'color': '#00FF88',
                    'enabled': True
                }
            }

        # Guest is off-by-default (config-gated).
        if not self._allow_guest_mode():
            try:
                users.pop("guest", None)
            except Exception:
                pass

        return users

    def _allow_guest_mode(self) -> bool:
        """Guest mode is off-by-default; controlled by `features.allow_guest_mode` in unified_config.json."""
        try:
            cfg_path = (LIGHTSPEED_ROOT / "config" / "unified_config.json").resolve()
            if not cfg_path.exists():
                return False
            data = json.loads(cfg_path.read_text(encoding="utf-8", errors="replace"))
            if not isinstance(data, dict):
                return False
            features = data.get("features") if isinstance(data.get("features"), dict) else {}
            return bool((features or {}).get("allow_guest_mode", False))
        except Exception:
            return False

    def _build_ui(self):
        """Build the login UI"""
        # Main container
        main = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main.pack(fill=tk.BOTH, expand=True, padx=50, pady=40)

        # Logo/Title area
        self._build_header(main)

        # User selection
        self._build_user_selection(main)

        # Launch options
        self._build_launch_options(main)

        # Login button
        self._build_login_button(main)

    def _build_header(self, parent: tk.Frame):
        """Build header with logo and title"""
        header = tk.Frame(parent, bg=self.colors['bg_dark'])
        header.pack(fill=tk.X, pady=(0, 30))

        # Logo placeholder (gradient text effect simulation)
        logo_frame = tk.Frame(header, bg=self.colors['bg_dark'])
        logo_frame.pack()

        tk.Label(
            logo_frame,
            text="COGNIGREX",
            font=(self.font_title, 42, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_dark']
        ).pack()

        tk.Label(
            logo_frame,
            text="LightSpeed Z-Floor Platform",
            font=(self.font_body, 14),
            fg=self.colors['fg_secondary'],
            bg=self.colors['bg_dark']
        ).pack(pady=(5, 0))

        # Separator line
        sep = tk.Frame(header, bg=self.colors['fg_primary'], height=2)
        sep.pack(fill=tk.X, pady=(20, 0))

    def _build_user_selection(self, parent: tk.Frame):
        """Build user profile selection"""
        section = tk.Frame(parent, bg=self.colors['bg_card'], padx=30, pady=25)
        section.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            section,
            text="Select User Profile",
            font=('Segoe UI', 14, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_card']
        ).pack(anchor='w', pady=(0, 15))

        # User buttons grid
        users_frame = tk.Frame(section, bg=self.colors['bg_card'])
        users_frame.pack(fill=tk.X)

        enabled_users = [(k, v) for k, v in self.users.items() if v.get('enabled', True)]

        for i, (role, user) in enumerate(enabled_users):
            self._create_user_button(users_frame, role, user, i)
            if i == 0:
                self.selected_user.set(role)

    def _create_user_button(self, parent: tk.Frame, role: str, user: Dict, index: int):
        """Create a user selection button"""
        color = user.get('color', '#00DDFF')
        display = user.get('display_name', role.capitalize())
        clearance = user.get('clearance', 1)

        # Container
        btn_frame = tk.Frame(parent, bg=self.colors['bg_panel'], padx=2, pady=2)
        btn_frame.grid(row=0, column=index, padx=10, pady=5, sticky='nsew')

        # Inner content
        inner = tk.Frame(btn_frame, bg=self.colors['bg_panel'], padx=15, pady=12)
        inner.pack(fill=tk.BOTH, expand=True)

        # Radio button
        rb = tk.Radiobutton(
            inner,
            text=display,
            variable=self.selected_user,
            value=role,
            font=('Segoe UI', 12, 'bold'),
            fg=color,
            bg=self.colors['bg_panel'],
            selectcolor=self.colors['bg_card'],
            activebackground=self.colors['bg_panel'],
            activeforeground=color,
            cursor='hand2'
        )
        rb.pack(anchor='w')

        # Clearance indicator
        clearance_text = "*" * clearance
        tk.Label(
            inner,
            text=f"Clearance: {clearance_text}",
            font=('Segoe UI', 9),
            fg=self.colors['fg_muted'],
            bg=self.colors['bg_panel']
        ).pack(anchor='w')

        # Role badge
        role_display = {
            'main': 'Dashboard User',
            'it': 'Full IT Access',
            'achilles': 'AI Orchestrator',
            'guest': 'View Only'
        }.get(role, role)

        tk.Label(
            inner,
            text=role_display,
            font=('Segoe UI', 8),
            fg=color,
            bg=self.colors['bg_panel']
        ).pack(anchor='w', pady=(5, 0))

        parent.columnconfigure(index, weight=1)

    def _build_launch_options(self, parent: tk.Frame):
        """Build launch mode options"""
        section = tk.Frame(parent, bg=self.colors['bg_card'], padx=30, pady=25)
        section.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            section,
            text="Launch Mode",
            font=('Segoe UI', 14, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_card']
        ).pack(anchor='w', pady=(0, 15))

        # Options frame
        options = tk.Frame(section, bg=self.colors['bg_card'])
        options.pack(fill=tk.X)

        # Dashboard mode
        dash_rb = tk.Radiobutton(
            options,
            text="Dashboard Mode",
            variable=self.launch_mode,
            value='dashboard',
            font=('Segoe UI', 11),
            fg=self.colors['fg_text'],
            bg=self.colors['bg_card'],
            selectcolor=self.colors['bg_panel'],
            activebackground=self.colors['bg_card'],
            cursor='hand2'
        )
        dash_rb.grid(row=0, column=0, sticky='w', padx=10)

        tk.Label(
            options,
            text="Standard dashboard with floor navigation",
            font=('Segoe UI', 9),
            fg=self.colors['fg_muted'],
            bg=self.colors['bg_card']
        ).grid(row=1, column=0, sticky='w', padx=30)

        # IT Portal mode
        it_rb = tk.Radiobutton(
            options,
            text="IT Portal Mode",
            variable=self.launch_mode,
            value='it_portal',
            font=('Segoe UI', 11),
            fg=self.colors['fg_text'],
            bg=self.colors['bg_card'],
            selectcolor=self.colors['bg_panel'],
            activebackground=self.colors['bg_card'],
            cursor='hand2'
        )
        it_rb.grid(row=0, column=1, sticky='w', padx=10)

        tk.Label(
            options,
            text="Governance + approvals + floors hub (IT/Founder only)",
            font=('Segoe UI', 9),
            fg=self.colors['fg_muted'],
            bg=self.colors['bg_card']
        ).grid(row=1, column=1, sticky='w', padx=30)

        # Immersive 3D toggle
        immersive_frame = tk.Frame(section, bg=self.colors['bg_card'])
        immersive_frame.pack(fill=tk.X, pady=(20, 0))

        immersive_cb = tk.Checkbutton(
            immersive_frame,
            text="Enable 3D Immersive Environment",
            variable=self.immersive_3d,
            font=('Segoe UI', 11),
            fg=self.colors['fg_secondary'],
            bg=self.colors['bg_card'],
            selectcolor=self.colors['bg_panel'],
            activebackground=self.colors['bg_card'],
            cursor='hand2'
        )
        immersive_cb.pack(anchor='w')

        tk.Label(
            immersive_frame,
            text="Dome projection, rolling hills, spatial UI widgets",
            font=('Segoe UI', 9),
            fg=self.colors['fg_muted'],
            bg=self.colors['bg_card']
        ).pack(anchor='w', padx=25)

    def _build_login_button(self, parent: tk.Frame):
        """Build login button"""
        btn_frame = tk.Frame(parent, bg=self.colors['bg_dark'])
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        login_btn = tk.Button(
            btn_frame,
            text="Enter Cognigrex",
            font=('Segoe UI', 14, 'bold'),
            fg=self.colors['bg_dark'],
            bg=self.colors['fg_primary'],
            activebackground=self.colors['fg_secondary'],
            activeforeground=self.colors['bg_dark'],
            relief=tk.FLAT,
            cursor='hand2',
            width=20,
            height=2,
            command=self._do_login
        )
        login_btn.pack()

        setup_btn = tk.Menubutton(
            btn_frame,
            text="Profile + Setup",
            font=('Segoe UI', 9),
            fg=self.colors['fg_muted'],
            bg=self.colors['bg_dark'],
            activebackground=self.colors['bg_panel'],
            activeforeground=self.colors['fg_text'],
            relief=tk.FLAT,
            cursor='hand2',
        )
        setup_menu = tk.Menu(setup_btn, tearoff=0, bg=self.colors['bg_card'], fg=self.colors['fg_text'])
        setup_menu.add_command(
            label="Profiles + Company",
            command=lambda: self._open_setup_hub("setup_state"),
        )
        setup_menu.add_command(
            label="Tailoring + Layout",
            command=lambda: self._open_setup_hub("tailoring"),
        )
        setup_btn.config(menu=setup_menu)
        setup_btn.pack(pady=(15, 0))

    def _do_login(self):
        """Process login and launch appropriate interface"""
        user_role = self.selected_user.get()
        user = self.users.get(user_role, {})
        mode = self.launch_mode.get()
        immersive = self.immersive_3d.get()

        # Validate IT Portal access
        if mode == 'it_portal' and user.get('clearance', 0) < 4:
            messagebox.showwarning(
                "Access Denied",
                "IT Portal requires clearance level 4.\nSwitching to Dashboard mode."
            )
            mode = 'dashboard'

        # Save session config
        session = {
            'user': user_role,
            'user_data': user,
            'mode': mode,
            'immersive_3d': immersive,
            'login_time': datetime.now().isoformat()
        }

        session_file = CONFIG_ROOT / "session.json"
        try:
            with open(session_file, 'w') as f:
                json.dump(session, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save session: {e}")

        # Close login window
        self.root.destroy()

        # Call callback or launch N.py
        if self.on_login:
            self.on_login(session)
        else:
            self._launch_n(mode, immersive)

    def _launch_n(self, mode: str, immersive: bool):
        """Launch N.py with appropriate flags"""
        import subprocess

        n_py = LIGHTSPEED_ROOT / "N.py"
        args = [sys.executable, str(n_py)]

        if mode == 'it_portal':
            args.append("--it-portal")
        else:
            args.append("--gui")

        if immersive:
            args.append("--3d")

        subprocess.Popen(args, cwd=str(LIGHTSPEED_ROOT))

    def _load_symbol_from_file(self, rel_path: str, symbol: str):
        path = (LIGHTSPEED_ROOT / rel_path).resolve()
        spec = importlib.util.spec_from_file_location(f"lightspeed_trinity_{path.stem}", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load {symbol} from {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return getattr(module, symbol)

    def _launch_legacy_setup_wizard(self) -> None:
        """Fallback launcher for the standalone Cognigrex setup wizard."""
        setup_script = LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "wizards" / "cognigrex_setup_wizard.py"
        if setup_script.exists():
            try:
                self.root.destroy()
            except Exception:
                pass
            # Direct file launch (floor folders contain non-package names like `Z+3_Trinity`).
            subprocess.Popen([sys.executable, str(setup_script)], cwd=str(LIGHTSPEED_ROOT))
        else:
            messagebox.showerror(
                "Setup Wizard Missing",
                f"Could not find setup wizard at:\n{setup_script}",
                parent=self.root,
            )

    def _open_setup_hub(self, focus_section: str = "setup_state") -> None:
        """Open the Trinity Settings Hub from login and fall back to the legacy wizard if needed."""
        try:
            SmartSettingsHub = self._load_symbol_from_file(
                "Z Axis/Z+3_Trinity/ui/smart_settings_hub.py",
                "SmartSettingsHub",
            )
            hub = SmartSettingsHub(self.root)
            hub.open_dialog_with_context(
                context=dict(COGNIGREX_LOGIN_SETTINGS_CONTEXT),
                focus_section=focus_section,
            )
        except Exception:
            if focus_section == "setup_state":
                self._launch_legacy_setup_wizard()
                return
            messagebox.showerror(
                "Settings Hub",
                "Profile and tailoring controls are currently unavailable.",
                parent=self.root,
            )

    def _open_setup(self):
        """Back-compat entry point for setup actions."""
        self._open_setup_hub("setup_state")

    def run(self):
        """Run the login interface"""
        self.root.mainloop()


def launch_login(parent: Optional[tk.Tk] = None, on_login: Optional[Callable] = None) -> CognigrexLogin:
    """Launch the Cognigrex Login interface"""
    login = CognigrexLogin(parent, on_login)
    return login


def check_setup_complete() -> bool:
    """Check if setup has been completed"""
    init_marker = CONFIG_ROOT / ".initialized"
    return init_marker.exists()


if __name__ == "__main__":
    if not check_setup_complete():
        print("Setup not complete. Launching setup wizard...")
        import subprocess
        setup_script = LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "wizards" / "cognigrex_setup_wizard.py"
        if setup_script.exists():
            subprocess.run([sys.executable, str(setup_script)], cwd=str(LIGHTSPEED_ROOT))
    else:
        login = launch_login()
        login.run()
