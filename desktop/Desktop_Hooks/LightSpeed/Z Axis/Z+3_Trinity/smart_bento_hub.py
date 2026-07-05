"""
SMART BENTO HUB - Unified Settings & Widget Management
Compact Trinity bento/settings surface for LightSpeed

Features:
- Compact slide-out interface for the glass/bento operator shell
- Quick toggles for all system settings
- Widget management for all Z-floors
- Visible detailed settings surfaces
- Drag to reorder widgets
- Import settings from all Z-floors
- Live preview of changes

Author: LightSpeed Team
Version: 5.1.2
"""

import tkinter as tk
from tkinter import ttk, colorchooser, font, messagebox
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import importlib.util
import sys
from pathlib import Path

try:
    # Centralized Tk-safe color sanitizer (handles rgba() + #RRGGBBAA).
    from core.ui.glass_ui import tk_safe_color as _tk_safe_color
except Exception:  # pragma: no cover
    _tk_safe_color = None


def _find_lightspeed_root(start: Path) -> Path:
    start = start.resolve()
    for candidate in (start, *start.parents):
        try:
            if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
                return candidate
        except Exception:
            continue
    return start.parent


SMART_BENTO_SETTINGS_CONTEXT = {
    "page_id": "trinity.smart_bento_hub",
    "label": "Smart Bento Hub / Profile + Setup",
}


# ============================================================================
# SETTINGS SCHEMA
# ============================================================================

class SettingType(Enum):
    """Types of settings available"""
    TOGGLE = "toggle"
    SLIDER = "slider"
    DROPDOWN = "dropdown"
    COLOR = "color"
    TEXT = "text"
    NUMBER = "number"
    FONT = "font"


@dataclass
class Setting:
    """Individual setting definition"""
    id: str
    name: str
    type: SettingType
    value: Any
    floor: str  # Which Z-floor owns this setting
    category: str
    description: str = ""
    options: List[Any] = field(default_factory=list)  # For dropdowns
    min_val: float = 0.0  # For sliders
    max_val: float = 100.0  # For sliders
    on_change: Optional[Callable] = None
    requires_restart: bool = False


@dataclass
class WidgetConfig:
    """Widget configuration for Bento display"""
    id: str
    name: str
    floor: str
    enabled: bool = True
    position: Tuple[int, int] = (0, 0)
    size: Tuple[int, int] = (200, 150)
    settings: List[Setting] = field(default_factory=list)


# ============================================================================
# SMART BENTO HUB
# ============================================================================

class SmartBentoHub:
    """
    Unified settings and widget management hub.

    Think of it as the phone notification shade - quick access to everything.
    """

    def __init__(self, parent=None):
        self.parent = parent
        self.root = None
        self.canvas = None
        self.lightspeed_root = _find_lightspeed_root(Path(__file__))

        # Settings registry
        self.settings: Dict[str, Setting] = {}
        self.widgets: Dict[str, WidgetConfig] = {}

        # UI state
        self.visible = False
        self.slide_position = 0.0  # 0.0 = hidden, 1.0 = fully visible
        self.animation_speed = 0.15

        # Load settings from all Z-floors
        self._load_all_settings()

        # UI colors (UI Base.pdf aesthetic)
        base_bg = '#000033'
        panel_raw = 'rgba(0, 20, 60, 0.7)'
        self.colors = {
            'bg': base_bg,
            # Tk does not support rgba() strings; sanitize to a safe #RRGGBB.
            'panel': (_tk_safe_color(panel_raw, bg=base_bg) if _tk_safe_color else '#00143C'),
            'border': '#00d4ff',
            'accent_green': '#00ff88',
            'accent_cyan': '#00ffff',
            'accent_magenta': '#ff1493',
            'text': '#ffffff',
        }

    def _load_all_settings(self):
        """Load settings from all Z-floors"""
        # Trinity (Z+3) - UI settings
        self._register_trinity_settings()

        # Neo (Z+2) - AI settings
        self._register_neo_settings()

        # Architect (Z+1) - Project settings
        self._register_architect_settings()

        # TheConstruct (Z0) - GUI & Physics settings
        self._register_construct_settings()

        # Oracle (Z-1) - Knowledge settings
        self._register_oracle_settings()

        # Smith (Z-2) - Task automation settings
        self._register_smith_settings()

        # Merovingian (Z-3) - Monitoring settings
        self._register_merovingian_settings()

        # Core (Z-4) - Infrastructure settings
        self._register_core_settings()

    def _register_trinity_settings(self):
        """Register all Trinity (Z+3) settings"""
        self.register_setting(Setting(
            id='trinity.theme',
            name='UI Theme',
            type=SettingType.DROPDOWN,
            value='matrix_green',
            floor='Z+3_Trinity',
            category='Appearance',
            description='Visual theme for the interface',
            options=['matrix_green', 'deep_blue', 'dark_mode', 'cyberpunk']
        ))

        self.register_setting(Setting(
            id='trinity.glass_blur',
            name='Glass Blur',
            type=SettingType.SLIDER,
            value=12.0,
            floor='Z+3_Trinity',
            category='Appearance',
            description='Backdrop blur intensity for glass morphism',
            min_val=0.0,
            max_val=20.0
        ))

        self.register_setting(Setting(
            id='trinity.button_shape',
            name='Button Shape',
            type=SettingType.DROPDOWN,
            value='rounded',
            floor='Z+3_Trinity',
            category='Appearance',
            description='Shared button silhouette used by Bento tiles, menus, and shell controls',
            options=['rounded', 'pill', 'square']
        ))

        self.register_setting(Setting(
            id='trinity.button_corner_radius',
            name='Button Corner Radius',
            type=SettingType.SLIDER,
            value=12.0,
            floor='Z+3_Trinity',
            category='Appearance',
            description='Design-token radius in pixels; Tk fallback stores the value and uses flat borders',
            min_val=0.0,
            max_val=32.0
        ))

        self.register_setting(Setting(
            id='trinity.button_fill_color',
            name='Button Fill',
            type=SettingType.COLOR,
            value='#1A5F5F',
            floor='Z+3_Trinity',
            category='Appearance',
            description='Default button fill color for compact menus and Bento actions'
        ))

        self.register_setting(Setting(
            id='trinity.button_border_color',
            name='Button Border',
            type=SettingType.COLOR,
            value='#2F4F4F',
            floor='Z+3_Trinity',
            category='Appearance',
            description='Default button outline color for shell controls'
        ))

        self.register_setting(Setting(
            id='trinity.animations',
            name='Enable Animations',
            type=SettingType.TOGGLE,
            value=True,
            floor='Z+3_Trinity',
            category='Performance',
            description='Enable UI animations and transitions'
        ))

        self.register_setting(Setting(
            id='trinity.widget_grid',
            name='Widget Grid',
            type=SettingType.DROPDOWN,
            value='3x3',
            floor='Z+3_Trinity',
            category='Layout',
            options=['2x2', '3x3', '4x4', 'free_form']
        ))

    def _register_neo_settings(self):
        """Register all Neo (Z+2) AI settings"""
        self.register_setting(Setting(
            id='neo.learning_enabled',
            name='AI Learning',
            type=SettingType.TOGGLE,
            value=True,
            floor='Z+2_Neo',
            category='AI',
            description='Enable Neo learning engine'
        ))

        self.register_setting(Setting(
            id='neo.correlation_threshold',
            name='Correlation Threshold',
            type=SettingType.SLIDER,
            value=0.75,
            floor='Z+2_Neo',
            category='AI',
            description='Minimum correlation strength to detect patterns',
            min_val=0.0,
            max_val=1.0
        ))

        self.register_setting(Setting(
            id='neo.ollama_model',
            name='Ollama Model',
            type=SettingType.DROPDOWN,
            value='llama2',
            floor='Z+2_Neo',
            category='AI',
            options=['llama2', 'mistral', 'codellama', 'phi']
        ))

        self.register_setting(Setting(
            id='achilles.voice_enabled',
            name='Achilles Voice',
            type=SettingType.TOGGLE,
            value=False,
            floor='Z+2_Neo',
            category='AI',
            description='Enable voice interaction with Achilles'
        ))

    def _register_architect_settings(self):
        """Register all Architect (Z+1) project settings"""
        self.register_setting(Setting(
            id='architect.auto_save',
            name='Auto-save Projects',
            type=SettingType.TOGGLE,
            value=True,
            floor='Z+1_Architect',
            category='Projects',
            description='Automatically save project changes'
        ))

        self.register_setting(Setting(
            id='architect.default_company',
            name='Default Company',
            type=SettingType.DROPDOWN,
            value='EMASSC',
            floor='Z+1_Architect',
            category='Projects',
            options=['EMASSC', 'Römer Industries']
        ))

    def _register_construct_settings(self):
        """Register all TheConstruct (Z0) GUI & Physics settings"""
        self.register_setting(Setting(
            id='construct.render_mode',
            name='Render Mode',
            type=SettingType.DROPDOWN,
            value='immersive_3d',
            floor='Z0_TheConstruct',
            category='Graphics',
            options=['immersive_3d', '3d_tower', 'flat_2d'],
            requires_restart=True
        ))

        self.register_setting(Setting(
            id='construct.fps_target',
            name='Target FPS',
            type=SettingType.SLIDER,
            value=60.0,
            floor='Z0_TheConstruct',
            category='Performance',
            min_val=30.0,
            max_val=144.0
        ))

        self.register_setting(Setting(
            id='construct.physics_quality',
            name='Physics Quality',
            type=SettingType.DROPDOWN,
            value='high',
            floor='Z0_TheConstruct',
            category='Physics',
            options=['low', 'medium', 'high', 'ultra']
        ))

        self.register_setting(Setting(
            id='construct.minecraft_controls',
            name='Minecraft-style Controls',
            type=SettingType.TOGGLE,
            value=True,
            floor='Z0_TheConstruct',
            category='Controls',
            description='WASD movement, Space to jump, double-tap sprint'
        ))

        self.register_setting(Setting(
            id='construct.show_debug',
            name='Show Debug Info',
            type=SettingType.TOGGLE,
            value=False,
            floor='Z0_TheConstruct',
            category='Debug'
        ))

    def _register_oracle_settings(self):
        """Register all Oracle (Z-1) knowledge settings"""
        self.register_setting(Setting(
            id='oracle.auto_ingest',
            name='Auto-ingest Documents',
            type=SettingType.TOGGLE,
            value=False,
            floor='Z-2_Oracle',
            category='Knowledge',
            description='Automatically ingest new documents'
        ))

        self.register_setting(Setting(
            id='oracle.search_depth',
            name='Search Depth',
            type=SettingType.DROPDOWN,
            value='deep',
            floor='Z-2_Oracle',
            category='Knowledge',
            options=['shallow', 'medium', 'deep', 'exhaustive']
        ))

    def _register_smith_settings(self):
        """Register all Smith (Z-2) task automation settings"""
        self.register_setting(Setting(
            id='smith.automation_enabled',
            name='Enable Automation',
            type=SettingType.TOGGLE,
            value=True,
            floor='Z-3_Smith',
            category='Automation'
        ))

    def _register_merovingian_settings(self):
        """Register all Merovingian (Z-3) monitoring settings"""
        self.register_setting(Setting(
            id='merovingian.log_level',
            name='Log Level',
            type=SettingType.DROPDOWN,
            value='INFO',
            floor='Z-4_Merovingian',
            category='Logging',
            options=['DEBUG', 'INFO', 'WARNING', 'ERROR']
        ))

        self.register_setting(Setting(
            id='merovingian.monitor_cpu',
            name='Monitor CPU',
            type=SettingType.TOGGLE,
            value=True,
            floor='Z-4_Merovingian',
            category='Monitoring'
        ))

    def _register_core_settings(self):
        """Register all Core (Z-4) infrastructure settings"""
        self.register_setting(Setting(
            id='core.database_path',
            name='Database Path',
            type=SettingType.TEXT,
            value='Z Axis/Z-4_Merovingian/data/db/lightspeed_unified.db',
            floor='Z-4_Merovingian',
            category='Database'
        ))

        self.register_setting(Setting(
            id='core.event_bus_enabled',
            name='Event Bus',
            type=SettingType.TOGGLE,
            value=True,
            floor='Z-4_Merovingian',
            category='Infrastructure',
            requires_restart=True
        ))

        self.register_setting(Setting(
            id='core.sandbox_mode',
            name='Sandbox Mode',
            type=SettingType.TOGGLE,
            value=True,
            floor='Z-4_Merovingian',
            category='Security',
            description='Enable sandbox for safe code execution'
        ))

    def register_setting(self, setting: Setting):
        """Register a new setting"""
        self.settings[setting.id] = setting

    def get_setting(self, setting_id: str) -> Optional[Setting]:
        """Get a setting by ID"""
        return self.settings.get(setting_id)

    def update_setting(self, setting_id: str, value: Any):
        """Update a setting value"""
        setting = self.get_setting(setting_id)
        if setting:
            old_value = setting.value
            setting.value = value

            # Call on_change callback
            if setting.on_change:
                setting.on_change(old_value, value)

            # Save to persistent storage
            self.save_settings()

            # Show notification if restart required
            if setting.requires_restart:
                print(f"[BentoHub] Setting '{setting.name}' changed. Restart required.")

    def get_settings_by_floor(self, floor: str) -> List[Setting]:
        """Get all settings for a specific Z-floor"""
        return [s for s in self.settings.values() if s.floor == floor]

    def get_settings_by_category(self, category: str) -> List[Setting]:
        """Get all settings in a category"""
        return [s for s in self.settings.values() if s.category == category]

    def save_settings(self):
        """Save all settings to JSON"""
        settings_data = {}
        for sid, setting in self.settings.items():
            settings_data[sid] = {
                'value': setting.value,
                'floor': setting.floor,
                'category': setting.category
            }

        settings_file = Path("Z Axis/Z+3_Trinity/settings.json")
        settings_file.parent.mkdir(parents=True, exist_ok=True)

        with open(settings_file, 'w') as f:
            json.dump(settings_data, f, indent=2)

        print(f"[BentoHub] Settings saved to {settings_file}")

    def load_settings(self):
        """Load settings from JSON"""
        settings_file = Path("Z Axis/Z+3_Trinity/settings.json")

        if settings_file.exists():
            with open(settings_file, 'r') as f:
                settings_data = json.load(f)

            for sid, data in settings_data.items():
                if sid in self.settings:
                    self.settings[sid].value = data['value']

            print(f"[BentoHub] Settings loaded from {settings_file}")

    # ========================================================================
    # UI RENDERING
    # ========================================================================

    def _load_symbol_from_file(self, rel_path: str, symbol: str):
        path = (self.lightspeed_root / rel_path).resolve()
        spec = importlib.util.spec_from_file_location(f"lightspeed_trinity_{path.stem}", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load {symbol} from {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return getattr(module, symbol)

    def _open_settings_hub(self, focus_section: str = "") -> None:
        try:
            SmartSettingsHub = self._load_symbol_from_file(
                "Z Axis/Z+3_Trinity/ui/smart_settings_hub.py",
                "SmartSettingsHub",
            )
            hub = SmartSettingsHub(self.root)
            hub.open_dialog_with_context(
                context=dict(SMART_BENTO_SETTINGS_CONTEXT),
                focus_section=focus_section,
            )
        except Exception as exc:
            parent = self.root if self.root else self.parent
            messagebox.showerror("Settings Hub", f"Failed to open Settings Hub:\n{exc}", parent=parent)

    def _create_action_menu(self, parent, *, text: str, commands: List[Tuple[str, Callable[[], None]]]):
        button = tk.Menubutton(
            parent,
            text=text,
            bg=self.colors['panel'],
            fg=self.colors['accent_cyan'],
            relief=tk.FLAT,
            padx=10,
            pady=5,
            activebackground=self.colors['panel'],
            activeforeground=self.colors['text'],
            font=('Arial', 10, 'bold'),
        )
        menu = tk.Menu(button, tearoff=0, bg=self.colors['bg'], fg=self.colors['text'])
        for label, command in commands:
            menu.add_command(label=label, command=command)
        button.config(menu=menu)
        return button

    def _build_hub_launchers(self, parent) -> None:
        shell = tk.Frame(parent, bg=self.colors['panel'], highlightbackground=self.colors['border'], highlightthickness=1)
        shell.pack(fill='x', padx=10, pady=(10, 6))

        tk.Label(
            shell,
            text="Hub-first launchers",
            bg=self.colors['panel'],
            fg=self.colors['accent_cyan'],
            font=('Garamond', 16, 'bold'),
        ).pack(anchor='w', padx=10, pady=(8, 2))

        tk.Label(
            shell,
            text="Keep quick toggles here. Route profile, setup, theme, and template work through compact Settings Hub menus.",
            bg=self.colors['panel'],
            fg=self.colors['text'],
            justify='left',
            wraplength=320,
            font=('Arial', 9),
        ).pack(anchor='w', padx=10, pady=(0, 8))

        actions = tk.Frame(shell, bg=self.colors['panel'])
        actions.pack(fill='x', padx=10, pady=(0, 10))

        self._create_action_menu(
            actions,
            text="Profile + Setup",
            commands=[
                ("Profiles + Company", lambda: self._open_settings_hub("setup_state")),
                ("Tailoring + Layout", lambda: self._open_settings_hub("tailoring")),
            ],
        ).pack(side='left', padx=(0, 8))

        self._create_action_menu(
            actions,
            text="Trinity Tools",
            commands=[
                ("Theme + Templates", lambda: self._open_settings_hub("trinity_launchers")),
            ],
        ).pack(side='left')

    def create_gui(self, parent=None):
        """Create the Bento Hub GUI (phone-style slide-out)"""
        if parent:
            self.parent = parent
            self.root = tk.Toplevel(parent)
        else:
            self.root = tk.Tk()

        self.root.title("Smart Bento Hub")
        self.root.geometry("400x600")
        self.root.configure(bg=self.colors['bg'])

        # Main container with scrollbar
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill='both', expand=True)

        # Canvas for scrolling
        canvas = tk.Canvas(main_frame, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._build_hub_launchers(scrollable_frame)

        # Render all settings by category
        categories = set(s.category for s in self.settings.values())

        for category in sorted(categories):
            self._render_category(scrollable_frame, category)

        # Bottom buttons
        button_frame = tk.Frame(self.root, bg=self.colors['bg'])
        button_frame.pack(side='bottom', fill='x', padx=10, pady=10)

        tk.Button(
            button_frame,
            text="Apply",
            command=self.save_settings,
            bg=self.colors['accent_green'],
            fg='#000033',
            font=('Arial', 12, 'bold')
        ).pack(side='left', padx=5)

        tk.Button(
            button_frame,
            text="Reset",
            command=self.load_settings,
            bg=self.colors['accent_cyan'],
            fg='#000033',
            font=('Arial', 12, 'bold')
        ).pack(side='left', padx=5)

    def _render_category(self, parent, category: str):
        """Render all settings in a category"""
        # Category header
        header = tk.Label(
            parent,
            text=category.upper(),
            bg=self.colors['bg'],
            fg=self.colors['accent_cyan'],
            font=('Garamond', 16, 'bold')
        )
        header.pack(anchor='w', padx=10, pady=(15, 5))

        # Settings in this category
        settings = self.get_settings_by_category(category)

        for setting in settings:
            self._render_setting(parent, setting)

    def _render_setting(self, parent, setting: Setting):
        """Render an individual setting widget"""
        frame = tk.Frame(parent, bg=self.colors['bg'])
        frame.pack(fill='x', padx=15, pady=5)

        # Setting name
        label = tk.Label(
            frame,
            text=setting.name,
            bg=self.colors['bg'],
            fg=self.colors['text'],
            font=('Arial', 11)
        )
        label.pack(side='left')

        # Setting widget based on type
        if setting.type == SettingType.TOGGLE:
            var = tk.BooleanVar(value=setting.value)
            toggle = tk.Checkbutton(
                frame,
                variable=var,
                bg=self.colors['bg'],
                fg=self.colors['accent_green'],
                selectcolor=self.colors['accent_green'],
                command=lambda: self.update_setting(setting.id, var.get())
            )
            toggle.pack(side='right')

        elif setting.type == SettingType.SLIDER:
            slider = tk.Scale(
                frame,
                from_=setting.min_val,
                to=setting.max_val,
                orient='horizontal',
                bg=self.colors['bg'],
                fg=self.colors['text'],
                command=lambda v: self.update_setting(setting.id, float(v))
            )
            slider.set(setting.value)
            slider.pack(side='right')

        elif setting.type == SettingType.DROPDOWN:
            var = tk.StringVar(value=setting.value)
            dropdown = ttk.Combobox(
                frame,
                textvariable=var,
                values=setting.options,
                state='readonly'
            )
            dropdown.bind('<<ComboboxSelected>>',
                         lambda e: self.update_setting(setting.id, var.get()))
            dropdown.pack(side='right')

        elif setting.type == SettingType.TEXT:
            var = tk.StringVar(value=setting.value)
            entry = tk.Entry(
                frame,
                textvariable=var,
                bg=self.colors['panel'],
                fg=self.colors['text']
            )
            entry.bind('<Return>',
                      lambda e: self.update_setting(setting.id, var.get()))
            entry.pack(side='right', fill='x', expand=True)

    def show(self):
        """Show the Bento Hub"""
        if self.root:
            self.root.deiconify()
        else:
            self.create_gui()

    def hide(self):
        """Hide the Bento Hub"""
        if self.root:
            self.root.withdraw()

    def toggle(self):
        """Toggle visibility"""
        if self.visible:
            self.hide()
        else:
            self.show()
        self.visible = not self.visible


# ============================================================================
# STANDALONE TEST
# ============================================================================

if __name__ == '__main__':
    hub = SmartBentoHub()
    hub.create_gui()

    print("=" * 70)
    print("SMART BENTO HUB - Unified Settings Manager")
    print("=" * 70)
    print(f"Total settings: {len(hub.settings)}")

    # Show settings by floor
    for floor in ['Z+3_Trinity', 'Z+2_Neo', 'Z0_TheConstruct']:
        settings = hub.get_settings_by_floor(floor)
        print(f"\n{floor}: {len(settings)} settings")
        for s in settings:
            print(f"  - {s.name}: {s.value}")

    hub.root.mainloop()
