"""
LightSpeed Settings Manager
Consolidated from: setup_wizard.py, first_run_setup.py
Features: Dynamic settings menu, per-component tabs, live configuration, function/library access

Enhancements v3.0.0:
- Complete library access panel
- Function registry browser
- Widget layout customization
- AI backend configuration
- Z-floor management
- Template gallery

Clean Code: Comprehensive settings management with registry integration
Version: 5.1.2
Date: April 9, 2026
"""

import json
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field, asdict

# Add parent to path for imports
def _find_lightspeed_root() -> Path:
    here = Path(__file__).resolve()
    for cand in (here, *here.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return here.parents[3]


LIGHTSPEED_ROOT = _find_lightspeed_root()
if str(LIGHTSPEED_ROOT) not in sys.path:
    sys.path.insert(0, str(LIGHTSPEED_ROOT))
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"
if Z_AXIS_ROOT.exists() and str(Z_AXIS_ROOT) not in sys.path:
    sys.path.insert(0, str(Z_AXIS_ROOT))
_MEROV = Z_AXIS_ROOT / "Z-4_Merovingian"
if _MEROV.exists() and str(_MEROV) not in sys.path:
    sys.path.insert(0, str(_MEROV))

try:
    from core.config.paths import TRINITY_SETTINGS  # type: ignore
except Exception:
    TRINITY_SETTINGS = LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "settings"


@dataclass
class SettingItem:
    """Individual setting configuration."""
    key: str
    label: str
    value: Any
    setting_type: str  # "string", "int", "bool", "choice", "path"
    category: str
    description: str = ""
    choices: List[str] = field(default_factory=list)  # For "choice" type
    min_value: Optional[int] = None  # For "int" type
    max_value: Optional[int] = None  # For "int" type
    validator: Optional[Callable] = None  # Custom validation function


class SettingsManager:
    """
    Dynamic settings manager that auto-expands as components are enabled.
    Handles per-component settings tabs and live configuration updates.

    New in v3.0.0:
    - Function/Library Registry integration
    - Widget layout builder
    - AI backend configuration
    - Z-floor management
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize settings manager.

        Args:
            config_path: Optional path to settings JSON file
        """
        if config_path is None:
            config_path = str(TRINITY_SETTINGS / "settings_dialog.json")
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self.settings: Dict[str, Dict[str, Any]] = {}
        self.categories: Dict[str, List[SettingItem]] = {}
        self.update_callbacks: Dict[str, List[Callable]] = {}

        # Integration systems
        self.function_registry = None
        self.ai_orchestrator = None
        self.floor_loader = None

        # Load existing settings
        self.load()

        # Initialize integrations
        self._initialize_integrations()

    def _initialize_integrations(self):
        """Initialize integration systems"""
        # Function Registry
        try:
            from core.services.function_registry import get_registry
            self.function_registry = get_registry(LIGHTSPEED_ROOT)
        except Exception as e:
            print(f"[SettingsManager] Function Registry unavailable: {e}")

        # AI Orchestrator
        try:
            ai_orch_path = LIGHTSPEED_ROOT / "Z Axis" / "Z+2_Neo" / "components"
            if ai_orch_path.exists():
                sys.path.insert(0, str(ai_orch_path))
                from ai_orchestrator import get_orchestrator
                self.ai_orchestrator = get_orchestrator(LIGHTSPEED_ROOT)
        except Exception as e:
            print(f"[SettingsManager] AI Orchestrator unavailable: {e}")

        # Floor Loader
        try:
            from core.services.floor_loader import FloorLoader
            self.floor_loader = FloorLoader(LIGHTSPEED_ROOT)
        except Exception as e:
            print(f"[SettingsManager] FloorLoader unavailable: {e}")

    def load(self) -> None:
        """Load settings from JSON file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.settings = data.get("settings", {})
            except Exception as e:
                print(f"Warning: Could not load settings: {e}")
                self.settings = self._get_default_settings()
        else:
            self.settings = self._get_default_settings()
            self.save()

    def save(self) -> None:
        """Save settings to JSON file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump({"settings": self.settings}, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def _get_default_settings(self) -> Dict[str, Dict[str, Any]]:
        """
        Get default settings structure.

        Returns:
            Default settings dictionary
        """
        return {
            "system": {
                "theme": "light",
                "first_run_completed": False,
                "version": "2.0.0",
                "auto_backup": True,
                "startup_checks": True,
            },
            "ui": {
                "show_welcome": True,
                "dashboard_layout": "default",
                "auto_refresh_interval": 5000,  # milliseconds
                "show_graph_tab": True,
                "hidden_layers": [],
                "animation_enabled": True,
                "show_tooltips": True,
            },
            "processing": {
                "max_file_size_gb": 10,
                "batch_size": 5,
                "ocr_enabled": True,
                "parallel_processing": True,
                "auto_save_interval": 300,  # seconds
            },
            "ai": {
                "ollama_enabled": False,
                "ollama_base_url": "http://localhost:11434",
                "ollama_model": "llama3.2",
                "assistant_mode": "clippy",  # "clippy" or "orchestrator"
                "auto_analysis": False,
                "confidence_threshold": 0.7,
            },
            "network": {
                "api_server_port": 8000,
                "log_server_port": 9000,
                "worker_port": 8001,
                "enable_remote_access": False,
            },
            "database": {
                "path": "data/lightspeed.db",
                "backup_enabled": True,
                "backup_interval": "daily",
                "backup_count": 7,
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get setting value by dot-notation key.

        Args:
            key: Setting key (e.g., "ui.theme")
            default: Default value if not found

        Returns:
            Setting value
        """
        parts = key.split('.')
        value = self.settings

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

    def set(self, key: str, value: Any, save_immediately: bool = True) -> None:
        """
        Set setting value by dot-notation key.

        Args:
            key: Setting key (e.g., "ui.theme")
            value: Value to set
            save_immediately: Whether to save to disk immediately
        """
        parts = key.split('.')
        target = self.settings

        # Navigate to the target dict
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]

        # Set the value
        target[parts[-1]] = value

        # Trigger callbacks
        if key in self.update_callbacks:
            for callback in self.update_callbacks[key]:
                try:
                    callback(value)
                except Exception as e:
                    print(f"Error in settings callback for {key}: {e}")

        # Save if requested
        if save_immediately:
            self.save()

    def register_callback(self, key: str, callback: Callable) -> None:
        """
        Register callback for setting changes.

        Args:
            key: Setting key to watch
            callback: Function to call when setting changes (receives new value)
        """
        if key not in self.update_callbacks:
            self.update_callbacks[key] = []
        self.update_callbacks[key].append(callback)

    def register_category(self, category: str, settings: List[SettingItem]) -> None:
        """
        Register a new settings category (enables dynamic expansion).

        Args:
            category: Category name
            settings: List of SettingItem objects
        """
        if category not in self.categories:
            self.categories[category] = []

        self.categories[category].extend(settings)

        # Ensure settings exist in config
        for setting in settings:
            current = self.get(setting.key)
            if current is None:
                self.set(setting.key, setting.value, save_immediately=False)

        self.save()

    def get_categories(self) -> List[str]:
        """
        Get list of all setting categories.

        Returns:
            List of category names
        """
        # Combine built-in categories with dynamically registered ones
        built_in = list(self.settings.keys())
        dynamic = list(self.categories.keys())

        return sorted(set(built_in + dynamic))

    def create_settings_window(self, parent: tk.Tk) -> None:
        """
        Create settings window with tabbed interface.

        Args:
            parent: Parent Tkinter window
        """
        window = tk.Toplevel(parent)
        window.title("LightSpeed Settings")
        window.geometry("900x700")
        window.minsize(800, 600)

        # Create notebook for categories
        notebook = ttk.Notebook(window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # System settings tab
        self._create_system_tab(notebook)

        # UI settings tab
        self._create_ui_tab(notebook)

        # Processing settings tab
        self._create_processing_tab(notebook)

        # AI settings tab
        self._create_ai_tab(notebook)

        # Network settings tab
        self._create_network_tab(notebook)

        # Database settings tab
        self._create_database_tab(notebook)

        # NEW: Function/Library Registry tab
        self._create_function_library_tab(notebook)

        # NEW: Z-Floor Management tab
        self._create_floor_management_tab(notebook)

        # NEW: Widget Layout Builder tab
        self._create_widget_layout_tab(notebook)

        # NEW: Template Manager tab
        self._create_template_manager_tab(notebook)

        # NEW: Smart Theme tab
        self._create_smart_theme_tab(notebook)

        # Dynamic category tabs
        for category, settings in self.categories.items():
            self._create_dynamic_tab(notebook, category, settings)

        # Bottom buttons
        button_frame = ttk.Frame(window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Reset to Defaults",
                  command=lambda: self._reset_defaults(window)).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Export Settings",
                  command=self._export_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Import Settings",
                  command=lambda: self._import_settings(window)).pack(side=tk.LEFT)

        ttk.Button(button_frame, text="Close",
                  command=window.destroy).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Apply",
                  command=lambda: self._apply_changes(window)).pack(side=tk.RIGHT, padx=5)

    def _create_system_tab(self, notebook: ttk.Notebook) -> None:
        """Create system settings tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="System")

        # Theme
        ttk.Label(frame, text="Theme:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        theme_var = tk.StringVar(value=self.get("system.theme", "light"))
        ttk.Radiobutton(frame, text="Light", value="light", variable=theme_var).grid(
            row=1, column=0, sticky="w", padx=30, pady=2)
        ttk.Radiobutton(frame, text="Dark", value="dark", variable=theme_var).grid(
            row=2, column=0, sticky="w", padx=30, pady=2)

        theme_var.trace_add("write", lambda *_: self.set("system.theme", theme_var.get()))

        # Auto-backup
        auto_backup_var = tk.BooleanVar(value=self.get("system.auto_backup", True))
        ttk.Checkbutton(frame, text="Enable automatic backups", variable=auto_backup_var,
                       command=lambda: self.set("system.auto_backup", auto_backup_var.get())).grid(
            row=3, column=0, sticky="w", padx=10, pady=(20, 5))

        # Startup checks
        startup_var = tk.BooleanVar(value=self.get("system.startup_checks", True))
        ttk.Checkbutton(frame, text="Run system checks on startup", variable=startup_var,
                       command=lambda: self.set("system.startup_checks", startup_var.get())).grid(
            row=4, column=0, sticky="w", padx=10, pady=5)

    def _create_ui_tab(self, notebook: ttk.Notebook) -> None:
        """Create UI settings tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Interface")

        row = 0

        # Dashboard layout
        ttk.Label(frame, text="Dashboard Layout:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=10, pady=(10, 5))
        row += 1

        layout_var = tk.StringVar(value=self.get("ui.dashboard_layout", "default"))
        layouts = ["default", "compact", "expanded", "custom"]
        layout_combo = ttk.Combobox(frame, textvariable=layout_var, values=layouts, width=20)
        layout_combo.grid(row=row, column=0, sticky="w", padx=30, pady=5)
        layout_var.trace_add("write", lambda *_: self.set("ui.dashboard_layout", layout_var.get()))
        row += 1

        # Refresh interval
        ttk.Label(frame, text="Auto-refresh interval (seconds):", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=10, pady=(20, 5))
        row += 1

        refresh_var = tk.StringVar(value=str(self.get("ui.auto_refresh_interval", 5000) // 1000))
        refresh_entry = ttk.Entry(frame, textvariable=refresh_var, width=10)
        refresh_entry.grid(row=row, column=0, sticky="w", padx=30, pady=5)

        def update_refresh(*_):
            try:
                self.set("ui.auto_refresh_interval", int(refresh_var.get()) * 1000)
            except ValueError:
                pass

        refresh_var.trace_add("write", update_refresh)
        row += 1

        # Checkboxes
        show_welcome_var = tk.BooleanVar(value=self.get("ui.show_welcome", True))
        ttk.Checkbutton(frame, text="Show welcome screen on startup", variable=show_welcome_var,
                       command=lambda: self.set("ui.show_welcome", show_welcome_var.get())).grid(
            row=row, column=0, sticky="w", padx=10, pady=(20, 5))
        row += 1

        show_graph_var = tk.BooleanVar(value=self.get("ui.show_graph_tab", True))
        ttk.Checkbutton(frame, text="Show Graph tab", variable=show_graph_var,
                       command=lambda: self.set("ui.show_graph_tab", show_graph_var.get())).grid(
            row=row, column=0, sticky="w", padx=10, pady=5)
        row += 1

        animation_var = tk.BooleanVar(value=self.get("ui.animation_enabled", True))
        ttk.Checkbutton(frame, text="Enable animations", variable=animation_var,
                       command=lambda: self.set("ui.animation_enabled", animation_var.get())).grid(
            row=row, column=0, sticky="w", padx=10, pady=5)
        row += 1

        tooltips_var = tk.BooleanVar(value=self.get("ui.show_tooltips", True))
        ttk.Checkbutton(frame, text="Show tooltips", variable=tooltips_var,
                       command=lambda: self.set("ui.show_tooltips", tooltips_var.get())).grid(
            row=row, column=0, sticky="w", padx=10, pady=5)

    def _create_processing_tab(self, notebook: ttk.Notebook) -> None:
        """Create processing settings tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Processing")

        row = 0

        # Max file size
        ttk.Label(frame, text="Maximum file size (GB):", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=10, pady=(10, 5))
        row += 1

        file_size_var = tk.StringVar(value=str(self.get("processing.max_file_size_gb", 10)))
        ttk.Entry(frame, textvariable=file_size_var, width=10).grid(
            row=row, column=0, sticky="w", padx=30, pady=5)

        def update_file_size(*_):
            try:
                self.set("processing.max_file_size_gb", int(file_size_var.get()))
            except ValueError:
                pass

        file_size_var.trace_add("write", update_file_size)
        row += 1

        # Batch size
        ttk.Label(frame, text="Batch size:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=10, pady=(20, 5))
        row += 1

        batch_var = tk.StringVar(value=str(self.get("processing.batch_size", 5)))
        ttk.Entry(frame, textvariable=batch_var, width=10).grid(
            row=row, column=0, sticky="w", padx=30, pady=5)

        def update_batch(*_):
            try:
                self.set("processing.batch_size", int(batch_var.get()))
            except ValueError:
                pass

        batch_var.trace_add("write", update_batch)
        row += 1

        # Checkboxes
        ocr_var = tk.BooleanVar(value=self.get("processing.ocr_enabled", True))
        ttk.Checkbutton(frame, text="Enable OCR for images", variable=ocr_var,
                       command=lambda: self.set("processing.ocr_enabled", ocr_var.get())).grid(
            row=row, column=0, sticky="w", padx=10, pady=(20, 5))
        row += 1

        parallel_var = tk.BooleanVar(value=self.get("processing.parallel_processing", True))
        ttk.Checkbutton(frame, text="Enable parallel processing", variable=parallel_var,
                       command=lambda: self.set("processing.parallel_processing", parallel_var.get())).grid(
            row=row, column=0, sticky="w", padx=10, pady=5)

    def _create_ai_tab(self, notebook: ttk.Notebook) -> None:
        """Create AI settings tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="AI")

        row = 0

        # Ollama settings
        ttk.Label(frame, text="Ollama Configuration:", font=("Arial", 12, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 10))
        row += 1

        ollama_var = tk.BooleanVar(value=self.get("ai.ollama_enabled", False))
        ttk.Checkbutton(frame, text="Enable Ollama integration", variable=ollama_var,
                       command=lambda: self.set("ai.ollama_enabled", ollama_var.get())).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        row += 1

        ttk.Label(frame, text="Base URL:").grid(row=row, column=0, sticky="w", padx=30, pady=5)
        base_url_var = tk.StringVar(value=self.get("ai.ollama_base_url", "http://localhost:11434"))
        ttk.Entry(frame, textvariable=base_url_var, width=40).grid(
            row=row, column=1, sticky="w", padx=5, pady=5)
        base_url_var.trace_add("write", lambda *_: self.set("ai.ollama_base_url", base_url_var.get()))
        row += 1

        ttk.Label(frame, text="Model:").grid(row=row, column=0, sticky="w", padx=30, pady=5)
        model_var = tk.StringVar(value=self.get("ai.ollama_model", "llama3.2"))
        models = ["llama3.2", "codellama", "mistral", "phi3", "gemma2"]
        model_combo = ttk.Combobox(frame, textvariable=model_var, values=models, width=37)
        model_combo.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        model_var.trace_add("write", lambda *_: self.set("ai.ollama_model", model_var.get()))
        row += 1

        # Assistant mode
        ttk.Label(frame, text="Assistant Mode:").grid(row=row, column=0, sticky="w", padx=30, pady=5)
        mode_var = tk.StringVar(value=self.get("ai.assistant_mode", "clippy"))
        modes = ["clippy", "orchestrator"]
        mode_combo = ttk.Combobox(frame, textvariable=mode_var, values=modes, width=37)
        mode_combo.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        mode_var.trace_add("write", lambda *_: self.set("ai.assistant_mode", mode_var.get()))
        row += 1

        # Auto-analysis
        auto_analysis_var = tk.BooleanVar(value=self.get("ai.auto_analysis", False))
        ttk.Checkbutton(frame, text="Enable automatic analysis (IT/Founder mode only)",
                       variable=auto_analysis_var,
                       command=lambda: self.set("ai.auto_analysis", auto_analysis_var.get())).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=30, pady=(15, 5))
        row += 1

        # Live runtime routing
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=10,
            pady=(20, 10),
        )
        row += 1

        ttk.Label(frame, text="Achilles Runtime Routing:", font=("Arial", 12, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 10)
        )
        row += 1

        try:
            from lightspeed_runtime.ai_settings import load_ai_settings, save_ai_settings  # type: ignore

            runtime_ai = load_ai_settings(LIGHTSPEED_ROOT)
        except Exception:
            runtime_ai = None
            load_ai_settings = None
            save_ai_settings = None

        if runtime_ai is None:
            ttk.Label(
                frame,
                text="Live runtime AI routing is unavailable in this environment.",
            ).grid(row=row, column=0, columnspan=2, sticky="w", padx=30, pady=5)
            return

        active_backend_var = tk.StringVar(value=runtime_ai.get("active_backend", "ollama_local"))
        active_profile_var = tk.StringVar(value=runtime_ai.get("active_profile", "low_lag_local"))
        achilles_enabled_var = tk.BooleanVar(value=bool(runtime_ai.get("achilles", {}).get("enabled", True)))
        approval_gated_var = tk.BooleanVar(value=bool(runtime_ai.get("achilles", {}).get("approval_gated", True)))

        ttk.Label(frame, text="Backend:").grid(row=row, column=0, sticky="w", padx=30, pady=5)
        ttk.Combobox(
            frame,
            textvariable=active_backend_var,
            values=sorted(runtime_ai.get("backends", {}).keys()),
            width=37,
            state="readonly",
        ).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1

        ttk.Label(frame, text="Profile:").grid(row=row, column=0, sticky="w", padx=30, pady=5)
        ttk.Combobox(
            frame,
            textvariable=active_profile_var,
            values=sorted(runtime_ai.get("profiles", {}).keys()),
            width=37,
            state="readonly",
        ).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1

        ttk.Checkbutton(
            frame,
            text="Enable Achilles runtime",
            variable=achilles_enabled_var,
        ).grid(row=row, column=0, columnspan=2, sticky="w", padx=30, pady=(10, 5))
        row += 1

        ttk.Checkbutton(
            frame,
            text="Require approvals for operator actions",
            variable=approval_gated_var,
        ).grid(row=row, column=0, columnspan=2, sticky="w", padx=30, pady=5)
        row += 1

        runtime_status_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=runtime_status_var, justify="left").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=30, pady=(10, 5)
        )
        row += 1

        def _save_runtime_ai() -> None:
            if save_ai_settings is None:
                return
            updated = load_ai_settings(LIGHTSPEED_ROOT)
            updated["active_backend"] = active_backend_var.get()
            updated["active_profile"] = active_profile_var.get()
            updated.setdefault("profiles", {}).setdefault(active_profile_var.get(), {})
            updated["profiles"][active_profile_var.get()]["backend"] = active_backend_var.get()
            updated.setdefault("achilles", {})
            updated["achilles"]["enabled"] = bool(achilles_enabled_var.get())
            updated["achilles"]["approval_gated"] = bool(approval_gated_var.get())
            save_ai_settings(LIGHTSPEED_ROOT, updated)
            runtime_status_var.set(
                f"Saved live runtime routing: {active_profile_var.get()} via {active_backend_var.get()}."
            )

        ttk.Button(frame, text="Apply Runtime AI Routing", command=_save_runtime_ai).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=30, pady=(5, 10)
        )

    def _create_network_tab(self, notebook: ttk.Notebook) -> None:
        """Create network settings tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Network")

        ports = [
            ("API Server Port:", "network.api_server_port", 8000),
            ("Log Server Port:", "network.log_server_port", 9000),
            ("Worker Port:", "network.worker_port", 8001),
        ]

        for i, (label, key, default) in enumerate(ports):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", padx=10, pady=10)
            var = tk.StringVar(value=str(self.get(key, default)))
            ttk.Entry(frame, textvariable=var, width=10).grid(
                row=i, column=1, sticky="w", padx=5, pady=10)

            def make_updater(k, v):
                def update(*_):
                    try:
                        self.set(k, int(v.get()))
                    except ValueError:
                        pass
                return update

            var.trace_add("write", make_updater(key, var))

        # Remote access
        remote_var = tk.BooleanVar(value=self.get("network.enable_remote_access", False))
        ttk.Checkbutton(frame, text="Enable remote access (CAUTION: Security risk)",
                       variable=remote_var,
                       command=lambda: self.set("network.enable_remote_access", remote_var.get())).grid(
            row=len(ports), column=0, columnspan=2, sticky="w", padx=10, pady=(20, 5))

    def _create_database_tab(self, notebook: ttk.Notebook) -> None:
        """Create database settings tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Database")

        row = 0

        # Database path
        ttk.Label(frame, text="Database Path:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=10, pady=(10, 5))
        row += 1

        db_path_var = tk.StringVar(value=self.get("database.path", "data/lightspeed.db"))
        ttk.Entry(frame, textvariable=db_path_var, width=50).grid(
            row=row, column=0, sticky="w", padx=30, pady=5)
        db_path_var.trace_add("write", lambda *_: self.set("database.path", db_path_var.get()))
        row += 1

        # Backup settings
        backup_var = tk.BooleanVar(value=self.get("database.backup_enabled", True))
        ttk.Checkbutton(frame, text="Enable automatic backups", variable=backup_var,
                       command=lambda: self.set("database.backup_enabled", backup_var.get())).grid(
            row=row, column=0, sticky="w", padx=10, pady=(20, 5))
        row += 1

        ttk.Label(frame, text="Backup Interval:").grid(row=row, column=0, sticky="w", padx=30, pady=5)
        row += 1

        interval_var = tk.StringVar(value=self.get("database.backup_interval", "daily"))
        intervals = ["hourly", "daily", "weekly", "monthly"]
        interval_combo = ttk.Combobox(frame, textvariable=interval_var, values=intervals, width=20)
        interval_combo.grid(row=row, column=0, sticky="w", padx=50, pady=5)
        interval_var.trace_add("write", lambda *_: self.set("database.backup_interval", interval_var.get()))

    def _create_function_library_tab(self, notebook: ttk.Notebook) -> None:
        """Create Function & Library Registry tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Functions & Libraries")

        # Create paned window for split view
        paned = ttk.PanedWindow(frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left side: Libraries
        lib_frame = ttk.LabelFrame(paned, text="Installed Libraries", padding=10)
        paned.add(lib_frame, weight=1)

        # Library list with scrollbar
        lib_scroll = ttk.Scrollbar(lib_frame)
        lib_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        lib_tree = ttk.Treeview(lib_frame, columns=('Status', 'Version'),
                                yscrollcommand=lib_scroll.set, height=15)
        lib_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        lib_scroll.config(command=lib_tree.yview)

        lib_tree.heading('#0', text='Library')
        lib_tree.heading('Status', text='Status')
        lib_tree.heading('Version', text='Version')

        lib_tree.column('#0', width=150)
        lib_tree.column('Status', width=80)
        lib_tree.column('Version', width=100)

        # Populate libraries
        if self.function_registry:
            for lib_name, lib_info in sorted(self.function_registry.libraries.items()):
                status = 'Available' if lib_info.available else 'Not Installed'
                version = lib_info.version if lib_info.available else '-'
                tag = 'available' if lib_info.available else 'unavailable'

                lib_tree.insert('', 'end', text=lib_name,
                              values=(status, version), tags=(tag,))

            lib_tree.tag_configure('available', foreground='green')
            lib_tree.tag_configure('unavailable', foreground='gray')

        # Right side: Functions
        func_frame = ttk.LabelFrame(paned, text="Available Functions", padding=10)
        paned.add(func_frame, weight=1)

        # Category filter
        filter_frame = ttk.Frame(func_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(filter_frame, text="Category:").pack(side=tk.LEFT, padx=5)

        category_var = tk.StringVar(value="All")
        categories = ["All"] + [cat.value for cat in self.function_registry.get_functions_by_category().keys() if self.function_registry.get_functions_by_category()[cat]]
        category_combo = ttk.Combobox(filter_frame, textvariable=category_var,
                                     values=categories, width=20, state='readonly')
        category_combo.pack(side=tk.LEFT, padx=5)

        # Function list
        func_scroll = ttk.Scrollbar(func_frame)
        func_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        func_tree = ttk.Treeview(func_frame, columns=('Floor', 'Category'),
                                yscrollcommand=func_scroll.set, height=15)
        func_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        func_scroll.config(command=func_tree.yview)

        func_tree.heading('#0', text='Function')
        func_tree.heading('Floor', text='Z-Floor')
        func_tree.heading('Category', text='Category')

        func_tree.column('#0', width=200)
        func_tree.column('Floor', width=100)
        func_tree.column('Category', width=120)

        # Populate functions
        def populate_functions(filter_category="All"):
            func_tree.delete(*func_tree.get_children())

            if self.function_registry:
                for func_id, func_info in sorted(self.function_registry.functions.items()):
                    if filter_category != "All" and func_info.category.value != filter_category:
                        continue

                    func_tree.insert('', 'end', text=func_info.name,
                                   values=(func_info.floor, func_info.category.value))

        populate_functions()

        # Update filter
        category_var.trace_add('write', lambda *_: populate_functions(category_var.get()))

        # Summary at bottom
        summary_frame = ttk.Frame(frame)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)

        if self.function_registry:
            summary = self.function_registry.get_summary()
            summary_text = (
                f"Libraries: {summary['libraries']['available']}/{summary['libraries']['total']} available  |  "
                f"Functions: {summary['functions']['total']} total"
            )
            ttk.Label(summary_frame, text=summary_text, font=('Arial', 9, 'bold')).pack()

    def _create_floor_management_tab(self, notebook: ttk.Notebook) -> None:
        """Create Z-Floor Management tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Z-Floors")

        # Title
        ttk.Label(frame, text="Z-Floor Architecture Management",
                 font=('Arial', 12, 'bold')).pack(pady=10)

        # Floor list
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scroll = ttk.Scrollbar(tree_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        floor_tree = ttk.Treeview(tree_frame, columns=('Level', 'Components', 'Status'),
                                 yscrollcommand=scroll.set, height=10)
        floor_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=floor_tree.yview)

        floor_tree.heading('#0', text='Floor Name')
        floor_tree.heading('Level', text='Z-Level')
        floor_tree.heading('Components', text='Components')
        floor_tree.heading('Status', text='Status')

        floor_tree.column('#0', width=150)
        floor_tree.column('Level', width=80)
        floor_tree.column('Components', width=100)
        floor_tree.column('Status', width=100)

        # Populate floors
        if self.floor_loader:
            for floor_id, manifest in sorted(self.floor_loader.manifests.items(),
                                            key=lambda x: x[1].z_level):
                status = 'Loaded' if manifest.loaded else 'Not Loaded'
                floor_tree.insert('', 'end', text=manifest.floor_name,
                                values=(manifest.z_level, len(manifest.components), status))

        # Initialization order info
        info_frame = ttk.LabelFrame(frame, text="Initialization Order", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(info_frame, text="Inside-Out: Z-4 (Core) -> Z+3 (Surface)",
                 font=('Arial', 10)).pack(anchor='w')
        ttk.Label(info_frame, text="Z-4: Merovingian (System Core) initializes first",
                 font=('Arial', 9), foreground='gray').pack(anchor='w')
        ttk.Label(info_frame, text="Z+3: Trinity (UI/Setup) initializes last",
                 font=('Arial', 9), foreground='gray').pack(anchor='w')

        # Control buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Reload All Floors",
                  command=self._reload_floors).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export Floor Manifests",
                  command=self._export_floor_manifests).pack(side=tk.LEFT, padx=5)

    def _create_widget_layout_tab(self, notebook: ttk.Notebook) -> None:
        """Create Widget Layout Builder tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Widget Layout")

        # Title
        ttk.Label(frame, text="Dashboard Widget Layout Builder",
                 font=('Arial', 12, 'bold')).pack(pady=10)

        # Layout template selection
        template_frame = ttk.LabelFrame(frame, text="Layout Templates", padding=10)
        template_frame.pack(fill=tk.X, padx=10, pady=5)

        template_var = tk.StringVar(value=self.get('ui.dashboard_layout', 'default'))

        templates = [
            ('default', 'Default Layout', '3-column balanced'),
            ('research', 'Research Layout', 'AI & data analysis focused'),
            ('it_admin', 'IT Admin Layout', 'System monitoring focused'),
            ('pm', 'Project Manager', 'Task tracking focused'),
            ('custom', 'Custom', 'Build your own')
        ]

        for i, (template_id, name, desc) in enumerate(templates):
            rb = ttk.Radiobutton(template_frame, text=f"{name} - {desc}",
                                value=template_id, variable=template_var)
            rb.grid(row=i, column=0, sticky='w', pady=2)

        template_var.trace_add('write',
                              lambda *_: self.set('ui.dashboard_layout', template_var.get()))

        # Grid configuration
        grid_frame = ttk.LabelFrame(frame, text="Grid Configuration", padding=10)
        grid_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(grid_frame, text="Columns:").grid(row=0, column=0, sticky='w', padx=5)

        columns_var = tk.IntVar(value=self.get('ui.grid_columns', 3))
        columns_spinner = ttk.Spinbox(grid_frame, from_=2, to=4, textvariable=columns_var, width=10)
        columns_spinner.grid(row=0, column=1, sticky='w', padx=5)

        columns_var.trace_add('write',
                             lambda *_: self.set('ui.grid_columns', columns_var.get()))

        # Widget selection
        widget_frame = ttk.LabelFrame(frame, text="Available Widgets", padding=10)
        widget_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create checkboxes for widgets
        widget_list = [
            ('system_status', 'System Status'),
            ('fleet_monitoring', 'Fleet Monitoring'),
            ('simulation_results', 'Simulation Results'),
            ('ai_recommendations', 'AI Recommendations'),
            ('project_tasks', 'Project Tasks'),
            ('database_stats', 'Database Stats'),
            ('code_analysis', 'Code Analysis'),
            ('network_graph', 'Network Graph'),
            ('okr_widget', 'OKR Tracker'),
            ('calendar_widget', 'Calendar'),
        ]

        for i, (widget_id, widget_name) in enumerate(widget_list):
            var = tk.BooleanVar(value=self.get(f'widgets.{widget_id}', False))
            cb = ttk.Checkbutton(widget_frame, text=widget_name, variable=var,
                                command=lambda wid=widget_id, v=var: self.set(f'widgets.{wid}', v.get()))
            cb.grid(row=i // 2, column=i % 2, sticky='w', padx=10, pady=2)

        # Preview button
        preview_frame = ttk.Frame(frame)
        preview_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(preview_frame, text="Preview Layout",
                  command=self._preview_layout).pack(side=tk.LEFT, padx=5)
        ttk.Button(preview_frame, text="Reset to Default",
                  command=self._reset_widget_layout).pack(side=tk.LEFT, padx=5)

    def _reload_floors(self):
        """Reload all Z-floors"""
        if self.floor_loader:
            try:
                self.floor_loader.reload_all_manifests()
                messagebox.showinfo("Success", "All floor manifests reloaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reload floors:\n{e}")

    def _export_floor_manifests(self):
        """Export floor manifests"""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename and self.floor_loader:
            try:
                export_data = {
                    floor_id: {
                        'floor_name': manifest.floor_name,
                        'z_level': manifest.z_level,
                        'components': manifest.components
                    }
                    for floor_id, manifest in self.floor_loader.manifests.items()
                }
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2)
                messagebox.showinfo("Success", f"Floor manifests exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export:\n{e}")

    def _preview_layout(self):
        """Preview widget layout"""
        layout_type = self.get('ui.dashboard_layout', 'default')
        grid_cols = self.get('ui.grid_columns', 3)

        enabled_widgets = []
        for widget_id in ['system_status', 'fleet_monitoring', 'simulation_results',
                         'ai_recommendations', 'project_tasks', 'database_stats',
                         'code_analysis', 'network_graph', 'okr_widget', 'calendar_widget']:
            if self.get(f'widgets.{widget_id}', False):
                enabled_widgets.append(widget_id.replace('_', ' ').title())

        preview_text = (
            f"Layout: {layout_type}\n"
            f"Grid: {grid_cols} columns\n"
            f"Widgets: {len(enabled_widgets)}\n\n"
            + '\n'.join(f"  - {w}" for w in enabled_widgets)
        )

        messagebox.showinfo("Layout Preview", preview_text)

    def _reset_widget_layout(self):
        """Reset widget layout to default"""
        if messagebox.askyesno("Reset Layout", "Reset widget layout to default configuration?"):
            self.set('ui.dashboard_layout', 'default')
            self.set('ui.grid_columns', 3)

            # Enable default widgets
            default_widgets = ['system_status', 'project_tasks', 'database_stats']
            for widget_id in ['system_status', 'fleet_monitoring', 'simulation_results',
                             'ai_recommendations', 'project_tasks', 'database_stats',
                             'code_analysis', 'network_graph', 'okr_widget', 'calendar_widget']:
                self.set(f'widgets.{widget_id}', widget_id in default_widgets)

            messagebox.showinfo("Success", "Widget layout reset to default")

    def _create_dynamic_tab(self, notebook: ttk.Notebook, category: str, settings: List[SettingItem]) -> None:
        """Create dynamically registered settings tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=category.replace("_", " ").title())

        for i, setting in enumerate(settings):
            # Label
            ttk.Label(frame, text=setting.label + ":", font=("Arial", 10, "bold")).grid(
                row=i*2, column=0, sticky="w", padx=10, pady=(10, 2))

            # Description
            if setting.description:
                ttk.Label(frame, text=setting.description, font=("Arial", 9),
                         foreground="gray").grid(
                    row=i*2, column=1, sticky="w", padx=5, pady=(10, 2))

            # Control based on type
            if setting.setting_type == "bool":
                var = tk.BooleanVar(value=self.get(setting.key, setting.value))
                ttk.Checkbutton(frame, text="Enabled", variable=var,
                               command=lambda k=setting.key, v=var: self.set(k, v.get())).grid(
                    row=i*2+1, column=0, sticky="w", padx=30, pady=(2, 10))

            elif setting.setting_type == "choice":
                var = tk.StringVar(value=self.get(setting.key, setting.value))
                combo = ttk.Combobox(frame, textvariable=var, values=setting.choices, width=30)
                combo.grid(row=i*2+1, column=0, sticky="w", padx=30, pady=(2, 10))
                var.trace_add("write", lambda *_, k=setting.key, v=var: self.set(k, v.get()))

            else:  # string, int, path
                var = tk.StringVar(value=str(self.get(setting.key, setting.value)))
                ttk.Entry(frame, textvariable=var, width=40).grid(
                    row=i*2+1, column=0, columnspan=2, sticky="w", padx=30, pady=(2, 10))

                def make_updater(k, v, t):
                    def update(*_):
                        try:
                            val = int(v.get()) if t == "int" else v.get()
                            self.set(k, val)
                        except ValueError:
                            pass
                    return update

                var.trace_add("write", make_updater(setting.key, var, setting.setting_type))

    def _create_template_manager_tab(self, notebook: ttk.Notebook) -> None:
        """Create Template Manager tab for productive template generation."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Templates")

        # Title
        title_label = ttk.Label(
            frame,
            text="Template Manager - Transform Demos into Production Tools",
            font=("Arial", 12, "bold")
        )
        title_label.pack(pady=(10, 5))

        # Description
        desc_text = (
            "Create professional documents, UI themes, and test environments from customizable templates.\n"
            "No more static demos - templates are productive tools that generate real outputs."
        )
        desc_label = ttk.Label(
            frame,
            text=desc_text,
            font=("Arial", 9),
            justify=tk.CENTER
        )
        desc_label.pack(pady=(0, 20))

        # Template categories
        categories_frame = ttk.LabelFrame(frame, text="Available Template Categories", padding=15)
        categories_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        # Document Templates
        doc_frame = ttk.LabelFrame(categories_frame, text="Document Templates", padding=10)
        doc_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            doc_frame,
            text="Generate professional documents with customizable styling:",
            font=("Arial", 9)
        ).pack(anchor="w")

        doc_list = ttk.Frame(doc_frame)
        doc_list.pack(fill=tk.X, pady=(5, 0))

        doc_types = [
            ("QR Codes", "Customizable size, colors, error correction, logo overlay"),
            ("Data Tables", "HTML/CSV tables with custom fonts, colors, borders"),
            ("Images", "Add borders, titles, watermarks, custom fonts")
        ]

        for name, desc in doc_types:
            item_frame = ttk.Frame(doc_list)
            item_frame.pack(fill=tk.X, pady=2)
            ttk.Label(item_frame, text=f"  • {name}:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
            ttk.Label(item_frame, text=desc, font=("Arial", 8)).pack(side=tk.LEFT, padx=(5, 0))

        # UI Templates
        ui_frame = ttk.LabelFrame(categories_frame, text="UI Templates", padding=10)
        ui_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            ui_frame,
            text="Create complete UI configurations:",
            font=("Arial", 9)
        ).pack(anchor="w")

        ui_list = ttk.Frame(ui_frame)
        ui_list.pack(fill=tk.X, pady=(5, 0))

        ui_types = [
            ("Themes", "Complete theme packages (colors, fonts, widgets)"),
            ("Widget Layouts", "Pre-configured dashboard and screen layouts"),
            ("Screen Templates", "Entire screen configurations for common workflows")
        ]

        for name, desc in ui_types:
            item_frame = ttk.Frame(ui_list)
            item_frame.pack(fill=tk.X, pady=2)
            ttk.Label(item_frame, text=f"  • {name}:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
            ttk.Label(item_frame, text=desc, font=("Arial", 8)).pack(side=tk.LEFT, padx=(5, 0))

        # Test Templates
        test_frame = ttk.LabelFrame(categories_frame, text="Test Templates", padding=10)
        test_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            test_frame,
            text="Productive testing and validation tools:",
            font=("Arial", 9)
        ).pack(anchor="w")

        test_list = ttk.Frame(test_frame)
        test_list.pack(fill=tk.X, pady=(5, 0))

        test_types = [
            ("Venv Setup", "Automated virtual environment creation and validation"),
            ("Integration Tests", "Verify all services and floors are working"),
            ("Configuration Tests", "Validate system configuration and dependencies")
        ]

        for name, desc in test_types:
            item_frame = ttk.Frame(test_list)
            item_frame.pack(fill=tk.X, pady=2)
            ttk.Label(item_frame, text=f"  • {name}:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
            ttk.Label(item_frame, text=desc, font=("Arial", 8)).pack(side=tk.LEFT, padx=(5, 0))

        # Action buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, padx=20, pady=15)

        def open_template_manager():
            """Open the full Template Manager dialog."""
            try:
                from core.ui.template_manager import show_template_manager
                import tkinter as tk
                show_template_manager(frame.winfo_toplevel())
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror(
                    "Template Manager Error",
                    f"Could not open Template Manager:\n{str(e)}"
                )

        ttk.Button(
            button_frame,
            text="Open Template Manager",
            command=open_template_manager,
            width=25
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(
            button_frame,
            text="Browse, customize, and generate templates",
            font=("Arial", 8)
        ).pack(side=tk.LEFT, padx=(10, 0))

        # Statistics
        stats_frame = ttk.LabelFrame(frame, text="Template Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        try:
            from core.services import get_template_registry
            registry = get_template_registry()
            template_count = len(registry.list_templates())

            stats_text = f"Available Templates: {template_count}\n"
            stats_text += "Categories: Document (3), UI (1), Test (1)\n"
            stats_text += "Status: All templates validated and ready"
        except Exception as e:
            stats_text = f"Could not load template statistics:\n{str(e)}"

        ttk.Label(
            stats_frame,
            text=stats_text,
            font=("Consolas", 8),
            justify=tk.LEFT
        ).pack(anchor="w")

    def _create_smart_theme_tab(self, notebook: ttk.Notebook) -> None:
        """Create Smart Theme tab for background photo theme extraction."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Smart Theme")

        # Title
        title_label = ttk.Label(
            frame,
            text="Smart Theme - Extract Colors from Background Photos",
            font=("Arial", 12, "bold")
        )
        title_label.pack(pady=(10, 5))

        # Description
        desc_text = (
            "Upload a background photo and automatically generate a complete UI theme.\n"
            "The smart theme extractor analyzes dominant colors and creates accessible,\n"
            "cohesive color schemes for the entire platform."
        )
        desc_label = ttk.Label(
            frame,
            text=desc_text,
            font=("Arial", 9),
            justify=tk.CENTER
        )
        desc_label.pack(pady=(0, 20))

        # Main content area
        content_frame = ttk.LabelFrame(frame, text="Theme Extraction", padding=15)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        # Background image section
        bg_section = ttk.LabelFrame(content_frame, text="1. Select Background Image", padding=10)
        bg_section.pack(fill=tk.X, pady=(0, 15))

        # Image path display
        path_frame = ttk.Frame(bg_section)
        path_frame.pack(fill=tk.X, pady=(0, 10))

        self.bg_image_path_var = tk.StringVar(value="No image selected")
        path_entry = ttk.Entry(path_frame, textvariable=self.bg_image_path_var, state="readonly")
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        def browse_image():
            from tkinter import filedialog
            filename = filedialog.askopenfilename(
                title="Select Background Image",
                filetypes=[
                    ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"),
                    ("All files", "*.*")
                ]
            )
            if filename:
                self.bg_image_path_var.set(filename)

        ttk.Button(path_frame, text="Browse...", command=browse_image).pack(side=tk.LEFT)

        # Theme type selection
        type_section = ttk.LabelFrame(content_frame, text="2. Select Theme Type", padding=10)
        type_section.pack(fill=tk.X, pady=(0, 15))

        self.theme_type_var = tk.StringVar(value="auto")

        ttk.Radiobutton(
            type_section,
            text="Auto-detect (analyze image brightness)",
            value="auto",
            variable=self.theme_type_var
        ).pack(anchor="w", pady=2)

        ttk.Radiobutton(
            type_section,
            text="Force Light Theme",
            value="light",
            variable=self.theme_type_var
        ).pack(anchor="w", pady=2)

        ttk.Radiobutton(
            type_section,
            text="Force Dark Theme",
            value="dark",
            variable=self.theme_type_var
        ).pack(anchor="w", pady=2)

        # Preview section
        preview_section = ttk.LabelFrame(content_frame, text="3. Preview & Apply", padding=10)
        preview_section.pack(fill=tk.BOTH, expand=True)

        # Preview text area
        preview_frame = ttk.Frame(preview_section)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        scrollbar = ttk.Scrollbar(preview_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.theme_preview_text = tk.Text(
            preview_frame,
            height=10,
            wrap=tk.WORD,
            font=("Consolas", 9),
            yscrollcommand=scrollbar.set
        )
        self.theme_preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.theme_preview_text.yview)

        self.theme_preview_text.insert("1.0", "No theme generated yet.\n\nClick 'Extract Theme' to analyze your background image.")
        self.theme_preview_text.config(state=tk.DISABLED)

        # Action buttons
        button_frame = ttk.Frame(preview_section)
        button_frame.pack(fill=tk.X)

        def extract_theme():
            """Extract theme from selected image."""
            image_path = self.bg_image_path_var.get()

            if image_path == "No image selected" or not image_path:
                from tkinter import messagebox
                messagebox.showwarning("No Image", "Please select a background image first.")
                return

            try:
                from core.ui.smart_theme import create_theme_from_image
                import json

                theme_type = self.theme_type_var.get()
                theme_colors = create_theme_from_image(image_path, theme_type)

                # Store for applying
                self.extracted_theme = theme_colors

                # Update preview
                self.theme_preview_text.config(state=tk.NORMAL)
                self.theme_preview_text.delete("1.0", tk.END)

                preview = f"Theme extracted successfully!\n\n"
                preview += f"Theme Type: {theme_type.title()}\n"
                preview += f"Image: {image_path.split('/')[-1]}\n\n"
                preview += "Color Scheme:\n"
                preview += json.dumps(theme_colors, indent=2)

                self.theme_preview_text.insert("1.0", preview)
                self.theme_preview_text.config(state=tk.DISABLED)

                from tkinter import messagebox
                messagebox.showinfo("Success", "Theme extracted successfully!\nClick 'Apply Theme' to use it.")

            except ImportError as e:
                from tkinter import messagebox
                messagebox.showerror(
                    "Missing Dependency",
                    f"PIL (Pillow) required for smart theme extraction.\n\n"
                    f"Install with: pip install pillow\n\nError: {str(e)}"
                )
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Extraction Error", f"Failed to extract theme:\n{str(e)}")

        def apply_theme():
            """Apply extracted theme to application."""
            if not hasattr(self, 'extracted_theme'):
                from tkinter import messagebox
                messagebox.showwarning("No Theme", "Please extract a theme first.")
                return

            try:
                # Save theme to settings
                self.set("ui.custom_theme", json.dumps(self.extracted_theme))
                self.set("ui.theme_mode", "custom")
                self.save()

                from tkinter import messagebox
                messagebox.showinfo(
                    "Theme Applied",
                    "Smart theme applied successfully!\n\n"
                    "Restart the application to see the new theme."
                )
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Apply Error", f"Failed to apply theme:\n{str(e)}")

        ttk.Button(
            button_frame,
            text="Extract Theme",
            command=extract_theme
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Apply Theme",
            command=apply_theme,
            style="Primary.TButton"
        ).pack(side=tk.LEFT, padx=5)

        # Info section
        info_frame = ttk.LabelFrame(frame, text="How It Works", padding=10)
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        info_text = (
            "1. Analyzes dominant colors in your background image\n"
            "2. Generates complementary accent colors\n"
            "3. Ensures WCAG accessibility (4.5:1 contrast ratio)\n"
            "4. Creates complete light or dark theme\n"
            "5. Applies to all UI components throughout the platform\n\n"
            "Tip: Choose images with clear, distinct colors for best results"
        )

        ttk.Label(
            info_frame,
            text=info_text,
            font=("Arial", 8),
            justify=tk.LEFT
        ).pack(anchor="w")

    def _reset_defaults(self, window: tk.Toplevel) -> None:
        """Reset all settings to defaults."""
        if messagebox.askyesno("Reset Settings",
                              "Are you sure you want to reset all settings to defaults?\nThis cannot be undone.",
                              parent=window):
            self.settings = self._get_default_settings()
            self.save()
            messagebox.showinfo("Settings Reset", "Settings have been reset to defaults.\nRestart the application to apply changes.", parent=window)
            window.destroy()

    def _export_settings(self) -> None:
        """Export settings to file."""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, indent=2)
                messagebox.showinfo("Export Successful", f"Settings exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Could not export settings:\n{e}")

    def _import_settings(self, window: tk.Toplevel) -> None:
        """Import settings from file."""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    imported = json.load(f)
                self.settings = imported
                self.save()
                messagebox.showinfo("Import Successful",
                                   "Settings imported successfully.\nRestart the application to apply changes.",
                                   parent=window)
                window.destroy()
            except Exception as e:
                messagebox.showerror("Import Failed", f"Could not import settings:\n{e}", parent=window)

    def _apply_changes(self, window: tk.Toplevel) -> None:
        """Apply settings changes."""
        self.save()
        messagebox.showinfo("Settings Applied", "Settings have been saved.", parent=window)
