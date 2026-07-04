"""
LightSpeed API Manager
Consolidated from: first_run_setup.py (AI connectors, cloud storage)
Features: Wizard-driven API addition, auto-discovery, integration points
"""

import json
import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict

try:
    from core.config.paths import LIGHTSPEED_ROOT  # type: ignore
except Exception:
    LIGHTSPEED_ROOT = Path(__file__).resolve()
    for _cand in (LIGHTSPEED_ROOT, *LIGHTSPEED_ROOT.parents):
        if (_cand / "N.py").exists() and (_cand / "Z Axis").exists():
            LIGHTSPEED_ROOT = _cand
            break


@dataclass
class APIConnector:
    """API connector configuration."""
    name: str
    provider: str
    api_type: str  # "ai", "cloud", "data", "custom"
    base_url: str
    api_key: str = ""
    enabled: bool = False
    config: Dict[str, Any] = None

    def __post_init__(self):
        if self.config is None:
            self.config = {}


class APIManager:
    """
    Manages API integrations for LightSpeed platform.
    Supports AI services, cloud storage, and custom APIs.
    """

    def __init__(self, config_path: str = "config/apis.json"):
        """
        Initialize API manager.

        Args:
            config_path: Path to APIs configuration file
        """
        cfg = Path(config_path)
        if not cfg.is_absolute():
            cfg = (Path(LIGHTSPEED_ROOT) / cfg).resolve()
        self.config_path = cfg
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self.apis: Dict[str, APIConnector] = {}
        self.test_callbacks: Dict[str, Callable] = {}

        # Load existing APIs
        self.load()

        # Register default APIs
        self._register_default_apis()

    def load(self) -> None:
        """Load API configurations from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, value in data.get("apis", {}).items():
                        self.apis[key] = APIConnector(**value)
            except Exception as e:
                print(f"Warning: Could not load API config: {e}")

    def save(self) -> None:
        """Save API configurations to file."""
        try:
            data = {
                "apis": {key: asdict(api) for key, api in self.apis.items()}
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving API config: {e}")

    def _register_default_apis(self) -> None:
        """Register default API connectors."""
        defaults = [
            # AI Services
            APIConnector(
                name="Ollama",
                provider="ollama",
                api_type="ai",
                base_url="http://localhost:11434",
                enabled=False,
                config={
                    "models": ["llama3.2", "codellama", "mistral", "phi3"],
                    "default_model": "llama3.2",
                    "streaming": True,
                }
            ),
            APIConnector(
                name="OpenAI",
                provider="openai",
                api_type="ai",
                base_url="https://api.openai.com/v1",
                enabled=False,
                config={
                    "model": "gpt-4",
                    "max_tokens": 2000,
                    "temperature": 0.7,
                }
            ),
            APIConnector(
                name="Anthropic Claude",
                provider="anthropic",
                api_type="ai",
                base_url="https://api.anthropic.com/v1",
                enabled=False,
                config={
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 4096,
                }
            ),
            APIConnector(
                name="Google Gemini",
                provider="google",
                api_type="ai",
                base_url="https://generativelanguage.googleapis.com/v1",
                enabled=False,
                config={
                    "model": "gemini-pro",
                }
            ),

            # Cloud Storage
            APIConnector(
                name="Google Drive",
                provider="google_drive",
                api_type="cloud",
                base_url="https://www.googleapis.com/drive/v3",
                enabled=False,
                config={
                    "credentials_path": "",
                    "folder_id": "",
                }
            ),
            APIConnector(
                name="Dropbox",
                provider="dropbox",
                api_type="cloud",
                base_url="https://api.dropboxapi.com/2",
                enabled=False,
                config={
                    "access_token": "",
                }
            ),
            APIConnector(
                name="OneDrive",
                provider="onedrive",
                api_type="cloud",
                base_url="https://graph.microsoft.com/v1.0",
                enabled=False,
                config={
                    "client_id": "",
                    "client_secret": "",
                }
            ),

            # Data Services
            APIConnector(
                name="nullschool",
                provider="nullschool",
                api_type="data",
                base_url="https://earth.nullschool.net",
                enabled=False,
                config={
                    "description": "Earth wind, weather, ocean & pollution visualization",
                }
            ),
            APIConnector(
                name="Tree of Life",
                provider="onezoom",
                api_type="data",
                base_url="https://www.onezoom.org",
                enabled=False,
                config={
                    "description": "OneZoom tree of life explorer",
                }
            ),
            APIConnector(
                name="Romer Industries Data",
                provider="romer_industries",
                api_type="data",
                base_url="https://romer.industries/data",
                enabled=False,
                config={
                    "description": "Romer Industries data endpoint (D1 hook)",
                    "paths": {
                        "root": "/data",
                    },
                }
            ),
        ]

        for api in defaults:
            if api.provider not in self.apis:
                self.apis[api.provider] = api

        self.save()

    def register_api(self, connector: APIConnector) -> None:
        """
        Register new API connector.

        Args:
            connector: APIConnector instance
        """
        self.apis[connector.provider] = connector
        self.save()

    def get_api(self, provider: str) -> Optional[APIConnector]:
        """
        Get API connector by provider name.

        Args:
            provider: Provider identifier

        Returns:
            APIConnector or None if not found
        """
        return self.apis.get(provider)

    def get_enabled_apis(self, api_type: Optional[str] = None) -> List[APIConnector]:
        """
        Get list of enabled API connectors.

        Args:
            api_type: Optional filter by API type

        Returns:
            List of enabled APIConnector instances
        """
        apis = [api for api in self.apis.values() if api.enabled]

        if api_type:
            apis = [api for api in apis if api.api_type == api_type]

        return apis

    def test_connection(self, provider: str) -> tuple[bool, str]:
        """
        Test API connection.

        Args:
            provider: Provider identifier

        Returns:
            Tuple of (success: bool, message: str)
        """
        api = self.get_api(provider)
        if not api:
            return False, f"API {provider} not found"

        # Custom test callback if registered
        if provider in self.test_callbacks:
            try:
                return self.test_callbacks[provider](api)
            except Exception as e:
                return False, f"Test failed: {e}"

        # Default tests for known providers
        try:
            if api.provider == "ollama":
                return self._test_ollama(api)
            elif api.provider == "openai":
                return self._test_openai(api)
            elif api.provider == "anthropic":
                return self._test_anthropic(api)
            elif api.provider == "google":
                return self._test_google(api)
            elif api.api_type == "cloud":
                return self._test_cloud_storage(api)
            else:
                return self._test_generic(api)

        except Exception as e:
            return False, f"Connection error: {e}"

    def _test_ollama(self, api: APIConnector) -> tuple[bool, str]:
        """Test Ollama connection."""
        try:
            response = requests.get(f"{api.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name") for m in models]
                return True, f"Connected successfully. Available models: {', '.join(model_names)}"
            else:
                return False, f"Connection failed (status {response.status_code})"
        except requests.RequestException as e:
            return False, f"Could not reach Ollama server: {e}"

    def _test_openai(self, api: APIConnector) -> tuple[bool, str]:
        """Test OpenAI connection."""
        headers = {
            "Authorization": f"Bearer {api.api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(f"{api.base_url}/models", headers=headers, timeout=10)

        if response.status_code == 200:
            return True, "Connected successfully"
        elif response.status_code == 401:
            return False, "Invalid API key"
        else:
            return False, f"Connection failed (status {response.status_code})"

    def _test_anthropic(self, api: APIConnector) -> tuple[bool, str]:
        """Test Anthropic connection."""
        return True, "Anthropic test requires special setup (skipped)"

    def _test_google(self, api: APIConnector) -> tuple[bool, str]:
        """Test Google Gemini connection."""
        return True, "Google test requires special setup (skipped)"

    def _test_cloud_storage(self, api: APIConnector) -> tuple[bool, str]:
        """Test cloud storage connection."""
        return True, f"{api.name} test requires authentication setup (skipped)"

    def _test_generic(self, api: APIConnector) -> tuple[bool, str]:
        """Generic API test (simple ping)."""
        try:
            response = requests.get(api.base_url, timeout=5)
            if response.status_code < 500:
                return True, f"Server reachable (status {response.status_code})"
            else:
                return False, f"Server error (status {response.status_code})"
        except requests.RequestException as e:
            return False, f"Connection error: {e}"

    def create_wizard_window(self, parent: tk.Tk) -> None:
        """
        Create API integration wizard window.

        Args:
            parent: Parent Tkinter window
        """
        window = tk.Toplevel(parent)
        window.title("API Integration Wizard")
        window.geometry("900x700")
        window.minsize(800, 600)

        # Create notebook for API categories
        notebook = ttk.Notebook(window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # AI Services tab
        self._create_ai_tab(notebook)

        # Cloud Storage tab
        self._create_cloud_tab(notebook)

        # Data Services tab
        self._create_data_tab(notebook)

        # Custom APIs tab
        self._create_custom_tab(notebook)

        # Bottom buttons
        button_frame = ttk.Frame(window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Close",
                  command=window.destroy).pack(side=tk.RIGHT)

    def _create_ai_tab(self, notebook: ttk.Notebook) -> None:
        """Create AI services configuration tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="AI Services")

        ttk.Label(frame, text="Configure AI Services for Document Analysis",
                 font=("Arial", 12, "bold")).pack(pady=10)

        # Ollama section
        self._create_api_section(frame, "ollama", "Ollama (Local LLM)")

        # OpenAI section
        self._create_api_section(frame, "openai", "OpenAI GPT")

        # Anthropic section
        self._create_api_section(frame, "anthropic", "Anthropic Claude")

        # Google section
        self._create_api_section(frame, "google", "Google Gemini")

    def _create_cloud_tab(self, notebook: ttk.Notebook) -> None:
        """Create cloud storage configuration tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Cloud Storage")

        ttk.Label(frame, text="Configure Cloud Storage Connections",
                 font=("Arial", 12, "bold")).pack(pady=10)

        # Google Drive
        self._create_api_section(frame, "google_drive", "Google Drive")

        # Dropbox
        self._create_api_section(frame, "dropbox", "Dropbox")

        # OneDrive
        self._create_api_section(frame, "onedrive", "OneDrive")

    def _create_data_tab(self, notebook: ttk.Notebook) -> None:
        """Create data services configuration tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Data Services")

        ttk.Label(frame, text="Scientific & Data Visualization APIs",
                 font=("Arial", 12, "bold")).pack(pady=10)

        # nullschool
        self._create_api_section(frame, "nullschool", "nullschool Earth")

        # Tree of Life
        self._create_api_section(frame, "onezoom", "Tree of Life")

        # Romer Industries Data (D1 hook)
        self._create_api_section(frame, "romer_industries", "Romer Industries Data")

    def _create_custom_tab(self, notebook: ttk.Notebook) -> None:
        """Create custom APIs tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Custom APIs")

        ttk.Label(frame, text="Add Custom API Integrations",
                 font=("Arial", 12, "bold")).pack(pady=10)

        # Add custom API button
        ttk.Button(frame, text="+ Add Custom API",
                  command=lambda: self._add_custom_api_dialog(frame)).pack(pady=10)

        # List of custom APIs
        custom_frame = ttk.LabelFrame(frame, text="Custom APIs", padding=15)
        custom_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create treeview for custom APIs
        columns = ('Type', 'Base URL', 'Status')
        api_tree = ttk.Treeview(custom_frame, columns=columns, show='tree headings', height=8)

        api_tree.heading('#0', text='API Name')
        api_tree.heading('Type', text='Type')
        api_tree.heading('Base URL', text='Base URL')
        api_tree.heading('Status', text='Status')

        api_tree.column('#0', width=150)
        api_tree.column('Type', width=80)
        api_tree.column('Base URL', width=300)
        api_tree.column('Status', width=80)

        api_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Populate with custom APIs
        for provider, api in self.apis.items():
            if api.api_type == "custom":
                status = "Enabled" if api.enabled else "Disabled"
                api_tree.insert('', 'end', text=api.name,
                              values=(api.api_type, api.base_url, status))

        # Action buttons
        btn_frame = ttk.Frame(custom_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        def test_selected():
            selection = api_tree.selection()
            if selection:
                item_text = api_tree.item(selection[0], 'text')
                # Find provider by name
                for provider, api in self.apis.items():
                    if api.name == item_text:
                        success, message = self.test_connection(provider)
                        messagebox.showinfo("Test Result",
                                          f"{'✅' if success else '❌'} {message}",
                                          parent=frame)
                        break
            else:
                messagebox.showwarning("No Selection", "Please select an API to test", parent=frame)

        def remove_selected():
            selection = api_tree.selection()
            if selection:
                item_text = api_tree.item(selection[0], 'text')
                if messagebox.askyesno("Confirm Delete",
                                      f"Remove API '{item_text}'?",
                                      parent=frame):
                    # Find and remove
                    for provider, api in list(self.apis.items()):
                        if api.name == item_text and api.api_type == "custom":
                            del self.apis[provider]
                            self.save()
                            api_tree.delete(selection[0])
                            messagebox.showinfo("Success", f"API '{item_text}' removed", parent=frame)
                            break
            else:
                messagebox.showwarning("No Selection", "Please select an API to remove", parent=frame)

        ttk.Button(btn_frame, text="Test Selected", command=test_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Remove Selected", command=remove_selected).pack(side=tk.LEFT, padx=5)

    def _create_api_section(self, parent: tk.Widget, provider: str, title: str) -> None:
        """
        Create API configuration section.

        Args:
            parent: Parent widget
            provider: API provider identifier
            title: Section title
        """
        api = self.get_api(provider)
        if not api:
            return

        section = ttk.LabelFrame(parent, text=title, padding=15)
        section.pack(fill=tk.X, padx=20, pady=10)

        # Enable checkbox
        enabled_var = tk.BooleanVar(value=api.enabled)

        def toggle_enabled():
            api.enabled = enabled_var.get()
            self.save()

        ttk.Checkbutton(section, text=f"Enable {title}",
                       variable=enabled_var,
                       command=toggle_enabled).pack(anchor=tk.W)

        # API key (if needed)
        if api.api_type == "ai" or api.api_type == "cloud":
            ttk.Label(section, text="API Key / Token:").pack(anchor=tk.W, pady=(10, 0))
            key_var = tk.StringVar(value=api.api_key)

            key_entry = ttk.Entry(section, textvariable=key_var, width=60, show="*")
            key_entry.pack(fill=tk.X, pady=5)

            def update_key(*_):
                api.api_key = key_var.get()
                self.save()

            key_var.trace_add("write", update_key)

        # Base URL
        if provider in ["ollama", "openai", "anthropic", "google"]:
            ttk.Label(section, text="Base URL:").pack(anchor=tk.W, pady=(10, 0))
            url_var = tk.StringVar(value=api.base_url)

            url_entry = ttk.Entry(section, textvariable=url_var, width=60)
            url_entry.pack(fill=tk.X, pady=5)

            def update_url(*_):
                api.base_url = url_var.get()
                self.save()

            url_var.trace_add("write", update_url)

        # Test connection button
        def test_conn():
            success, message = self.test_connection(provider)
            messagebox.showinfo(
                "Connection Test",
                f"{'✅' if success else '❌'} {message}",
                parent=section
            )

        ttk.Button(section, text="Test Connection",
                  command=test_conn).pack(pady=10)

    def _add_custom_api_dialog(self, parent: tk.Widget) -> None:
        """Show dialog to add custom API."""
        dialog = tk.Toplevel(parent)
        dialog.title("Add Custom API")
        dialog.geometry("500x400")

        ttk.Label(dialog, text="API Name:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Provider ID:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        provider_entry = ttk.Entry(dialog, width=40)
        provider_entry.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Base URL:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        url_entry = ttk.Entry(dialog, width=40)
        url_entry.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="API Type:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        type_var = tk.StringVar(value="custom")
        ttk.Combobox(dialog, textvariable=type_var,
                    values=["ai", "cloud", "data", "custom"], width=37).grid(
            row=3, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="API Key:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        key_entry = ttk.Entry(dialog, width=40, show="*")
        key_entry.grid(row=4, column=1, padx=10, pady=5)

        def save_api():
            name = name_entry.get().strip()
            provider = provider_entry.get().strip()
            url = url_entry.get().strip()

            if name and provider and url:
                connector = APIConnector(
                    name=name,
                    provider=provider,
                    api_type=type_var.get(),
                    base_url=url,
                    api_key=key_entry.get().strip(),
                    enabled=True
                )
                self.register_api(connector)
                messagebox.showinfo("Success", f"API '{name}' added successfully!", parent=dialog)
                dialog.destroy()
            else:
                messagebox.showwarning("Missing Information",
                                      "Please fill in all required fields.", parent=dialog)

        ttk.Button(dialog, text="Add API", command=save_api).grid(
            row=5, column=1, pady=20, sticky="e", padx=10)
