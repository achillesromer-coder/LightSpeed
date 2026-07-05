#!/usr/bin/env python
"""
Unified Settings Manager
Centralizes all configuration across LightSpeed components

Features:
- Single source of truth for all settings
- Automatic persistence to JSON
- Observer pattern for real-time updates
- Type-safe settings with dataclasses
- Import/Export functionality

Author: LightSpeed Team
Version: 5.1.2
Date: April 8, 2026
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict, field, fields as dataclass_fields
from datetime import datetime

try:
    from core.config.paths import ARCHITECT_PROJECTS, MEROVINGIAN_DATA, TRINITY_SETTINGS  # type: ignore
except Exception:
    ARCHITECT_PROJECTS = Path("Z Axis") / "Z+1_Architect" / "projects"
    MEROVINGIAN_DATA = Path("Z Axis") / "Z-4_Merovingian" / "data"
    TRINITY_SETTINGS = Path("Z Axis") / "Z+3_Trinity" / "settings"

SETTINGS_FILE = TRINITY_SETTINGS / "settings.json"
CANONICAL_DB_PATH = MEROVINGIAN_DATA / "db" / "lightspeed_unified.db"
CANONICAL_LOG_FILE = MEROVINGIAN_DATA / "logs" / "main.log"
CANONICAL_BACKUP_DIR = MEROVINGIAN_DATA / "backups"
CONFIG_SCHEMA_VERSION = "2026.04.finalization"
PORTABLE_DB_PATH = "Z Axis/Z-4_Merovingian/data/db/lightspeed_unified.db"
PORTABLE_LOG_FILE = "Z Axis/Z-4_Merovingian/data/logs/main.log"
PORTABLE_ACTIVITY_TABLE = PORTABLE_DB_PATH
PORTABLE_APPROVAL_LEDGER = "Z Axis/Z+1_Architect/data/approval_ledger.jsonl"
PORTABLE_PROJECTS_ROOT = "Z Axis/Z+1_Architect/projects"
PORTABLE_BACKUP_DIR = "Z Axis/Z-4_Merovingian/data/backups"


@dataclass
class LightSpeedSettings:
    """Complete LightSpeed application settings"""

    # =========================================================================
    # APP SETTINGS
    # =========================================================================
    app_version: str = "5.1.2"
    config_schema_version: str = CONFIG_SCHEMA_VERSION
    theme: str = "dark"  # dark, light, matrix, ocean, custom
    language: str = "en"
    first_run_complete: bool = False
    last_launched: str = ""

    # =========================================================================
    # UI SETTINGS
    # =========================================================================
    window_width: int = 1280
    window_height: int = 800
    window_maximized: bool = True
    window_position_x: int = 100
    window_position_y: int = 100

    show_tooltips: bool = True
    animation_enabled: bool = True
    show_splash_screen: bool = True
    show_status_bar: bool = True

    # Fonts
    font_family: str = "Arial"
    font_size: int = 10
    code_font_family: str = "Consolas"
    code_font_size: int = 9

    # Colors (hex values)
    color_bg_dark: str = "#1e1e1e"
    color_bg_panel: str = "#252526"
    color_text_primary: str = "#ffffff"
    color_text_secondary: str = "#cccccc"
    color_accent_cyan: str = "#00d4ff"
    color_accent_green: str = "#00ff88"
    color_error: str = "#ff3333"
    color_warning: str = "#ffaa00"
    color_success: str = "#00ff00"

    # =========================================================================
    # Z-FLOOR SETTINGS
    # =========================================================================
    active_floors: List[str] = field(default_factory=lambda: [
        "Neo", "Architect", "Trinity", "TheConstruct",
        "Oracle", "Morpheus", "Smith", "Merovingian"
    ])
    default_floor: str = "Neo"
    floor_navigation_style: str = "tabs"  # tabs, sidebar, dropdown

    # =========================================================================
    # AI SETTINGS
    # =========================================================================
    ollama_enabled: bool = False
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    ollama_temperature: float = 0.7
    ollama_max_tokens: int = 2048
    ollama_stream_responses: bool = True
    ollama_auto_start: bool = False

    # AI Features
    ai_chat_history_limit: int = 100
    ai_code_completion: bool = True
    ai_suggestions: bool = True

    # =========================================================================
    # API SETTINGS
    # =========================================================================
    apis_enabled: Dict[str, bool] = field(default_factory=lambda: {
        "qr": True,
        "tol": True,  # Tree of Life
        "weather": False,
        "ollama": False
    })

    api_keys: Dict[str, str] = field(default_factory=dict)

    api_endpoints: Dict[str, str] = field(default_factory=lambda: {
        "tol": "https://api.opentreeoflife.org",
        "weather": "https://api.open-meteo.com/v1"
    })

    # API Timeouts
    api_timeout_seconds: int = 30
    api_retry_attempts: int = 3

    # =========================================================================
    # DATABASE SETTINGS
    # =========================================================================
    db_path: str = str(CANONICAL_DB_PATH)
    activity_table_path: str = str(CANONICAL_DB_PATH)
    approval_ledger_path: str = str(
        ARCHITECT_PROJECTS.parent / "data" / "approval_ledger.jsonl"
    )
    db_auto_backup: bool = True
    db_backup_interval_hours: int = 24
    db_backup_keep_count: int = 7
    db_vacuum_on_startup: bool = False

    # =========================================================================
    # PROJECT MANAGER SETTINGS
    # =========================================================================
    projects_root: str = str(ARCHITECT_PROJECTS)
    project_auto_venv: bool = True
    project_default_python: str = "python"
    project_templates_enabled: bool = True

    # =========================================================================
    # SERVER SETTINGS
    # =========================================================================
    web_server_enabled: bool = False
    web_server_host: str = "127.0.0.1"
    web_server_port: int = 8080
    web_server_auto_start: bool = False
    web_server_open_browser: bool = True

    websocket_enabled: bool = True
    websocket_port: int = 8081

    # =========================================================================
    # PERFORMANCE SETTINGS
    # =========================================================================
    max_concurrent_jobs: int = 4
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_to_file: bool = True
    log_file_path: str = str(CANONICAL_LOG_FILE)
    log_max_size_mb: int = 10
    log_backup_count: int = 5

    cache_enabled: bool = True
    cache_size_mb: int = 500
    cache_ttl_seconds: int = 3600

    # =========================================================================
    # SECURITY SETTINGS
    # =========================================================================
    require_login: bool = True
    session_timeout_minutes: int = 60
    password_min_length: int = 8
    enable_2fa: bool = False

    # =========================================================================
    # BACKUP & RESTORE
    # =========================================================================
    backup_enabled: bool = True
    backup_directory: str = str(CANONICAL_BACKUP_DIR)
    backup_schedule: str = "daily"  # hourly, daily, weekly
    backup_retention_days: int = 30
    backup_include_projects: bool = False

    # =========================================================================
    # NOTIFICATION SETTINGS
    # =========================================================================
    notifications_enabled: bool = True
    notification_sound: bool = True
    notification_duration_seconds: int = 5

    # =========================================================================
    # DEVELOPER SETTINGS
    # =========================================================================
    developer_mode: bool = False
    show_debug_info: bool = False
    enable_profiling: bool = False
    auto_reload_on_change: bool = False


class SettingsManager:
    """
    Manages application settings with persistence and observer pattern

    Usage:
        settings_mgr = SettingsManager()
        settings_mgr.set('theme', 'dark')
        theme = settings_mgr.get('theme')
        settings_mgr.register_observer(on_settings_changed)
    """

    def __init__(self, config_path: Optional[Path | str] = None):
        if config_path is None:
            config_path = SETTINGS_FILE

        self.config_path = Path(config_path)
        self._unknown_settings: Dict[str, Any] = {}
        self.settings = self.load()
        self._observers: List[Callable] = []

        # Update last launched
        self.settings.last_launched = datetime.now().isoformat()
        self.save()

    def load(self) -> LightSpeedSettings:
        """Load settings from disk"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if not isinstance(data, dict):
                    raise TypeError("settings document must be a JSON object")
                known_fields = {item.name for item in dataclass_fields(LightSpeedSettings)}
                self._unknown_settings = {
                    key: value for key, value in data.items() if key not in known_fields
                }
                known_data = {
                    key: value for key, value in data.items() if key in known_fields
                }
                return LightSpeedSettings(**known_data)
            except Exception as e:
                print(f"[!] Error loading settings: {e}")
                print("[!] Using default settings")
                return LightSpeedSettings()
        else:
            print("[*] No settings file found, creating default settings")
            return LightSpeedSettings()

    def _is_root_config(self) -> bool:
        parts = tuple(part.casefold() for part in self.config_path.parts)
        return len(parts) >= 2 and parts[-2:] == ("config", "settings.json")

    def _serialized_settings(self) -> Dict[str, Any]:
        payload = {**self._unknown_settings, **asdict(self.settings)}
        if self._is_root_config():
            payload.update(
                {
                    "config_schema_version": CONFIG_SCHEMA_VERSION,
                    "db_path": PORTABLE_DB_PATH,
                    "activity_table_path": PORTABLE_ACTIVITY_TABLE,
                    "approval_ledger_path": PORTABLE_APPROVAL_LEDGER,
                    "projects_root": PORTABLE_PROJECTS_ROOT,
                    "log_file_path": PORTABLE_LOG_FILE,
                    "backup_directory": PORTABLE_BACKUP_DIR,
                }
            )
        return payload

    def save(self):
        """Save settings to disk and notify observers"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.config_path.with_name(f".{self.config_path.name}.tmp")
            with open(temporary, 'w', encoding='utf-8') as f:
                json.dump(self._serialized_settings(), f, indent=2)
                f.write("\n")
            temporary.replace(self.config_path)

            # Notify observers
            self._notify_observers()
        except Exception as e:
            print(f"[!] Error saving settings: {e}")

    def get(self, key: str, default=None) -> Any:
        """Get a setting value"""
        return getattr(self.settings, key, default)

    def set(self, key: str, value: Any):
        """Set a setting value and save"""
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            self.save()
        else:
            raise KeyError(f"Setting '{key}' does not exist")

    def update(self, **kwargs):
        """Update multiple settings at once"""
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
            else:
                print(f"[!] Warning: Setting '{key}' does not exist, skipping")

        self.save()

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self._unknown_settings = {}
        self.settings = LightSpeedSettings()
        self.save()
        print("[*] Settings reset to defaults")

    def export_settings(self, export_path: Path):
        """Export settings to a JSON file"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self._serialized_settings(), f, indent=2)
            print(f"[*] Settings exported to: {export_path}")
            return True
        except Exception as e:
            print(f"[!] Error exporting settings: {e}")
            return False

    def import_settings(self, import_path: Path):
        """Import settings from a JSON file"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise TypeError("settings import must be a JSON object")
            known_fields = {item.name for item in dataclass_fields(LightSpeedSettings)}
            self._unknown_settings = {
                key: value for key, value in data.items() if key not in known_fields
            }
            self.settings = LightSpeedSettings(
                **{key: value for key, value in data.items() if key in known_fields}
            )
            self.save()
            print(f"[*] Settings imported from: {import_path}")
            return True
        except Exception as e:
            print(f"[!] Error importing settings: {e}")
            return False

    def register_observer(self, callback: Callable):
        """Register a callback for settings changes"""
        if callback not in self._observers:
            self._observers.append(callback)

    def unregister_observer(self, callback: Callable):
        """Unregister a callback"""
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self):
        """Notify all observers of settings change"""
        for callback in self._observers:
            try:
                callback(self.settings)
            except Exception as e:
                print(f"[!] Error notifying observer: {e}")

    def get_category(self, category: str) -> Dict[str, Any]:
        """Get all settings in a category (e.g., 'ai', 'ui')"""
        category_prefix = f"{category}_"
        return {
            key: value
            for key, value in asdict(self.settings).items()
            if key.startswith(category_prefix) or key == category
        }

    def create_settings_window(self, parent):
        """
        Create a settings dialog window (compatibility method for N.py)
        Opens a Toplevel window with current settings
        """
        import tkinter as tk
        from tkinter import ttk, messagebox

        # Create settings window
        settings_window = tk.Toplevel(parent)
        settings_window.title("Trinity Master Settings")
        settings_window.geometry("800x600")
        settings_window.configure(bg='#000B1F')
        try:
            settings_window.transient(parent)
            settings_window.grab_set()
        except Exception:
            pass

        # Header
        header = tk.Frame(settings_window, bg='#001B3F', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text="⚙️ Master Settings", font=('Arial', 18, 'bold'),
                bg='#001B3F', fg='#00FFFF').pack(side='left', padx=20, pady=10)

        # Create notebook for categories
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Get current settings
        current_settings = asdict(self.settings)

        # Group settings by category
        categories = {}
        for key, value in current_settings.items():
            # Determine category from key prefix
            if '_' in key:
                category = key.split('_')[0].title()
            else:
                category = 'General'

            if category not in categories:
                categories[category] = {}
            categories[category][key] = value

        # Create tab for each category
        for category_name, settings in sorted(categories.items()):
            tab = tk.Frame(notebook, bg='#000B1F')
            notebook.add(tab, text=category_name)

            # Create scrollable frame
            canvas = tk.Canvas(tab, bg='#000B1F')
            scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg='#000B1F')

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            # Add settings to tab
            row = 0
            for key, value in sorted(settings.items()):
                # Setting label
                label_text = key.replace('_', ' ').title()
                tk.Label(scrollable_frame, text=label_text + ":",
                        bg='#000B1F', fg='#00FF88',
                        font=('Arial', 10, 'bold')).grid(row=row, column=0,
                                                         sticky='w', padx=20, pady=10)

                # Setting value display
                value_display = str(value) if value is not None else 'Not Set'
                tk.Label(scrollable_frame, text=value_display,
                        bg='#000B1F', fg='#00DDFF',
                        font=('Arial', 10)).grid(row=row, column=1,
                                                sticky='w', padx=20, pady=10)
                row += 1

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

        # Button frame
        btn_frame = tk.Frame(settings_window, bg='#000B1F')
        btn_frame.pack(fill='x', padx=10, pady=10)

        def save_and_close():
            try:
                self.save()
                messagebox.showinfo("Success", "Settings saved successfully!",
                                   parent=settings_window)
                settings_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save settings: {e}",
                                    parent=settings_window)

        def save_only():
            try:
                self.save()
                messagebox.showinfo("Success", "Settings saved successfully!", parent=settings_window)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save settings: {e}", parent=settings_window)

        actions_btn = tk.Menubutton(
            btn_frame,
            text="Settings Actions",
            bg='#001B3F',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief='raised',
            width=12,
        )
        actions_menu = tk.Menu(actions_btn, tearoff=0)
        actions_menu.add_command(label="Save & Close", command=save_and_close)
        actions_menu.add_command(label="Save", command=save_only)
        actions_menu.add_separator()
        actions_menu.add_command(label="Close", command=settings_window.destroy)
        actions_btn.config(menu=actions_menu)
        actions_btn.pack(side='right', padx=5)

    def __repr__(self):
        return f"<SettingsManager: {self.config_path}>"


# ============================================================================
# GLOBAL INSTANCE (Singleton Pattern)
# ============================================================================

_settings_manager: Optional[SettingsManager] = None


def get_settings_manager() -> SettingsManager:
    """Get the global settings manager instance (singleton)"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


def get_settings() -> LightSpeedSettings:
    """Quick access to settings object"""
    return get_settings_manager().settings


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_setting(key: str, default=None) -> Any:
    """Quick function to get a single setting"""
    return get_settings_manager().get(key, default)


def set_setting(key: str, value: Any):
    """Quick function to set a single setting"""
    get_settings_manager().set(key, value)


def update_settings(**kwargs):
    """Quick function to update multiple settings"""
    get_settings_manager().update(**kwargs)


if __name__ == "__main__":
    # Test the settings manager
    print("=" * 80)
    print("LIGHTSPEED SETTINGS MANAGER TEST")
    print("=" * 80)

    mgr = get_settings_manager()

    print(f"\nSettings file: {mgr.config_path}")
    print(f"Theme: {mgr.get('theme')}")
    print(f"Window size: {mgr.get('window_width')}x{mgr.get('window_height')}")
    print(f"Active floors: {mgr.get('active_floors')}")
    print(f"Ollama enabled: {mgr.get('ollama_enabled')}")

    # Test observer
    def on_change(settings):
        print(f"\n[Observer] Settings changed! Theme is now: {settings.theme}")

    mgr.register_observer(on_change)

    # Change a setting
    print("\nChanging theme to 'matrix'...")
    mgr.set('theme', 'matrix')

    print("\nTest complete!")
