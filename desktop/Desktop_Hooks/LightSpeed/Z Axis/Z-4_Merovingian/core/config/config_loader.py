"""
Unified Configuration Loader
Consolidates all .txt configuration files into single source of truth
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SystemConfig:
    """System-wide configuration"""
    version: str
    platform: str
    company: str
    product: str
    deployment_env: str


@dataclass
class ZFloorConfig:
    """Single Z-floor configuration"""
    y_position: float
    color: str
    theme: str
    description: str
    enabled: bool
    services: list = None
    widgets: list = None
    engines: list = None
    calculators: int = 0


class ConfigLoader:
    """
    Load and manage unified configuration
    Replaces scattered .txt files with single JSON source
    """

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            # Default to unified_config.json in config directory
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "config" / "unified_config.json"

        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
        self._expand_env_vars()

    def _load_config(self):
        """Load configuration from JSON"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = json.load(f)

        print(f"[Config] Loaded configuration from {self.config_path}")

    def _expand_env_vars(self):
        """Expand environment variables in config"""
        def expand_dict(d: dict) -> dict:
            """Recursively expand {{ENV:VAR}} patterns"""
            result = {}
            for key, value in d.items():
                if isinstance(value, str) and value.startswith("{{ENV:"):
                    # Extract environment variable name
                    env_var = value[6:-2]  # Remove {{ENV: and }}
                    result[key] = os.environ.get(env_var, value)  # Keep original if not found
                elif isinstance(value, dict):
                    result[key] = expand_dict(value)
                elif isinstance(value, list):
                    result[key] = [expand_dict(item) if isinstance(item, dict) else item for item in value]
                else:
                    result[key] = value
            return result

        self._config = expand_dict(self._config)

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation

        Example:
            config.get('z_floors.Z0_TheConstruct.y_position')  # Returns 50.0
        """
        keys = key_path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_system_config(self) -> SystemConfig:
        """Get system configuration"""
        sys_data = self._config.get('system', {})
        return SystemConfig(
            version=sys_data.get('version', '1.0.0'),
            platform=sys_data.get('platform', 'LightSpeed'),
            company=sys_data.get('company', 'Romer Industries'),
            product=sys_data.get('product', 'Achilles Protocol'),
            deployment_env=sys_data.get('deployment_env', 'production')
        )

    def get_z_floor_config(self, floor_id: str) -> Optional[ZFloorConfig]:
        """Get configuration for specific Z-floor"""
        floors = self._config.get('z_floors', {})

        if floor_id not in floors:
            return None

        floor_data = floors[floor_id]
        return ZFloorConfig(
            y_position=floor_data.get('y_position', 0.0),
            color=floor_data.get('color', '#FFFFFF'),
            theme=floor_data.get('theme', 'default'),
            description=floor_data.get('description', ''),
            enabled=floor_data.get('enabled', True),
            services=floor_data.get('services', []),
            widgets=floor_data.get('widgets', []),
            engines=floor_data.get('engines', []),
            calculators=floor_data.get('calculators', 0)
        )

    def get_all_z_floors(self) -> Dict[str, ZFloorConfig]:
        """Get all Z-floor configurations"""
        floors = {}
        for floor_id in self._config.get('z_floors', {}).keys():
            floors[floor_id] = self.get_z_floor_config(floor_id)
        return floors

    def get_api_config(self, service: str) -> Dict[str, Any]:
        """Get API configuration for specific service"""
        return self._config.get('api_keys', {}).get(service, {})

    def is_service_enabled(self, service: str) -> bool:
        """Check if a service is enabled"""
        api_config = self.get_api_config(service)
        if api_config and 'enabled' in api_config:
            return api_config['enabled']

        # Check features
        features = self._config.get('features', {})
        return features.get(service, False)

    def get_database_path(self) -> Path:
        """Get database file path"""
        db_config = self._config.get('database', {})
        path_str = db_config.get('path', 'data/databases/lightspeed_unified.db')

        # Make relative to project root
        base_dir = Path(__file__).parent.parent.parent
        return base_dir / path_str

    def get_trinity_path(self) -> Path:
        """Get Trinity storage path"""
        trinity_config = self._config.get('trinity_storage', {})
        path_str = trinity_config.get('base_path', 'data/trinity')

        base_dir = Path(__file__).parent.parent.parent
        return base_dir / path_str

    def get_ui_theme(self) -> Dict[str, Any]:
        """Get UI theme configuration"""
        return self._config.get('ui_theme', {})

    def get_rendering_config(self) -> Dict[str, Any]:
        """Get rendering configuration"""
        return self._config.get('rendering', {})

    def get_physics_config(self) -> Dict[str, Any]:
        """Get physics configuration"""
        return self._config.get('physics', {})

    def reload(self):
        """Reload configuration from disk"""
        self._load_config()
        self._expand_env_vars()
        print("[Config] Configuration reloaded")


# Global configuration instance
_config_instance: Optional[ConfigLoader] = None


def get_config() -> ConfigLoader:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader()
    return _config_instance


def reload_config():
    """Reload global configuration"""
    global _config_instance
    if _config_instance is not None:
        _config_instance.reload()
    else:
        _config_instance = ConfigLoader()
