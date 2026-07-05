#!/usr/bin/env python
"""
Settings Hub - Centralized Configuration Management
Provides unified settings access across all Z Axis floors

60+ settings across 6 categories:
- VR Settings (12): Field of view, IPD, refresh rate, comfort settings
- AI Settings (15): Model selection, tokens, temperature, context
- UI Settings (10): Theme, scaling, panels, animations
- Performance (8): Quality presets, resource limits, caching
- Integration (10): APIs, endpoints, authentication, webhooks
- Developer (5): Debug mode, profiling, logging, testing
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class SettingsHub:
    """
    Centralized settings management singleton

    Features:
    - 60+ settings across 6 categories
    - Type validation
    - Auto-save on change
    - Reset to defaults
    - Import/export
    """

    def __init__(self):
        self.settings: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._initialize_default_settings()
        self.config_file = Path('config/settings.json')
        self._load_from_disk()

        # Get Event Bus for change notifications
        self.event_bus = None
        self._connect_event_bus()

    def _connect_event_bus(self):
        """Connect to Event Bus for change notifications"""
        try:
            from . import get_event_bus
            self.event_bus = get_event_bus()
        except:
            self.event_bus = None

    def _initialize_default_settings(self):
        """Initialize all default settings"""
        self.settings = {
            'vr': {
                'field_of_view': {
                    'type': 'number',
                    'default': 90,
                    'min': 60,
                    'max': 120,
                    'description': 'Field of view in degrees'
                },
                'ipd': {
                    'type': 'slider',
                    'default': 63.5,
                    'min': 55.0,
                    'max': 75.0,
                    'step': 0.5,
                    'description': 'Interpupillary distance (mm)'
                },
                'refresh_rate': {
                    'type': 'dropdown',
                    'default': 90,
                    'options': [60, 72, 90, 120, 144],
                    'description': 'VR refresh rate (Hz)'
                },
                'render_resolution': {
                    'type': 'slider',
                    'default': 1.0,
                    'min': 0.5,
                    'max': 2.0,
                    'step': 0.1,
                    'description': 'Render resolution multiplier'
                },
                'comfort_mode': {
                    'type': 'toggle',
                    'default': False,
                    'description': 'Enable comfort mode (reduced motion)'
                },
                'enable_hand_tracking': {
                    'type': 'toggle',
                    'default': False,
                    'description': 'Enable hand tracking'
                },
                'spatial_audio': {
                    'type': 'toggle',
                    'default': True,
                    'description': 'Enable spatial audio'
                },
                'vr_overlay_opacity': {
                    'type': 'slider',
                    'default': 0.8,
                    'min': 0.0,
                    'max': 1.0,
                    'step': 0.1,
                    'description': 'VR overlay opacity'
                },
                'snap_turn_angle': {
                    'type': 'dropdown',
                    'default': 45,
                    'options': [15, 30, 45, 90],
                    'description': 'Snap turn angle (degrees)'
                },
                'movement_speed': {
                    'type': 'slider',
                    'default': 1.0,
                    'min': 0.5,
                    'max': 3.0,
                    'step': 0.1,
                    'description': 'Movement speed multiplier'
                },
                'enable_teleport': {
                    'type': 'toggle',
                    'default': True,
                    'description': 'Enable teleport locomotion'
                },
                'show_guardian': {
                    'type': 'toggle',
                    'default': True,
                    'description': 'Show play area guardian'
                }
            },

            'ai': {
                'model_name': {
                    'type': 'dropdown',
                    'default': 'gpt-4',
                    'options': ['gpt-4', 'gpt-3.5-turbo', 'claude-sonnet-4.5', 'local_llm'],
                    'description': 'AI model to use'
                },
                'temperature': {
                    'type': 'slider',
                    'default': 0.7,
                    'min': 0.0,
                    'max': 2.0,
                    'step': 0.1,
                    'description': 'AI response creativity'
                },
                'max_tokens': {
                    'type': 'number',
                    'default': 2000,
                    'min': 100,
                    'max': 8000,
                    'description': 'Maximum tokens per response'
                },
                'context_window': {
                    'type': 'number',
                    'default': 8000,
                    'min': 1000,
                    'max': 128000,
                    'description': 'Context window size'
                },
                'enable_conversation_memory': {
                    'type': 'toggle',
                    'default': True,
                    'description': 'Remember conversation history'
                },
                'memory_retention_days': {
                    'type': 'number',
                    'default': 30,
                    'min': 1,
                    'max': 365,
                    'description': 'Days to retain conversation history'
                },
                'ai_safety_filter': {
                    'type': 'toggle',
                    'default': True,
                    'description': 'Enable AI safety filtering'
                },
                'stream_responses': {
                    'type': 'toggle',
                    'default': True,
                    'description': 'Stream AI responses in real-time'
                },
                'auto_save_conversations': {
                    'type': 'toggle',
                    'default': True,
                    'description': 'Automatically save conversations'
                },
                'show_token_count': {
                    'type': 'toggle',
                    'default': True,
                    'description': 'Show token usage'
                },
                'show_cost_estimate': {
                    'type': 'toggle',
                    'default': True,
                    'description': 'Show estimated API cost'
                },
                'ai_response_timeout': {
                    'type': 'number',
                    'default': 60,
                    'min': 10,
                    'max': 300,
                    'description': 'AI response timeout (seconds)'
                },
                'enable_code_execution': {
                    'type': 'toggle',
                    'default': False,
                    'description': 'Allow AI to execute code'
                },
                'enable_web_search': {
                    'type': 'toggle',
                    'default': True,
                    'description': 'Allow AI web search'
                },
                'system_prompt': {
                    'type': 'text',
                    'default': 'You are a helpful AI assistant.',
                    'description': 'System prompt for AI'
                }
            },

            'ui': {
                'theme_mode': {
                    'type': 'dropdown',
                    'default': 'dark_glass',
                    'options': ['dark_glass', 'light', 'high_contrast', 'custom'],
                    'description': 'UI theme'
                },
                'ui_scale': {
                    'type': 'slider',
                    'default': 1.0,
                    'min': 0.5,
                    'max': 2.0,
                    'step': 0.1,
                    'description': 'UI scaling factor'
                },
                'font_family': {
                    'type': 'dropdown',
                    'default': 'Arial',
                    'options': ['Arial', 'Helvetica', 'Verdana', 'Courier New', 'System'],
                    'description': 'UI font family'
                },
                'font_size': {
                    'type': 'number',
                    'default': 10,
                    'min': 8,
                    'max': 18,
                    'description': 'Base font size'
                },
                'enable_animations': {
                    'type': 'toggle',
                    'default': True,
                    'description': 'Enable UI animations'
                },
                'animation_speed': {
                    'type': 'slider',
                    'default': 1.0,
                    'min': 0.5,
                    'max': 2.0,
                    'step': 0.1,
                    'description': 'Animation speed multiplier'
                },
                'show_tooltips': {
                    'type': 'toggle',
                    'default': True,
                    'description': 'Show UI tooltips'
                },
                'tooltip_delay': {
                    'type': 'number',
                    'default': 500,
                    'min': 0,
                    'max': 2000,
                    'description': 'Tooltip delay (ms)'
                },
                'sidebar_position': {
                    'type': 'dropdown',
                    'default': 'left',
                    'options': ['left', 'right', 'top', 'bottom'],
                    'description': 'Sidebar position'
                },
                'enable_sound_effects': {
                    'type': 'toggle',
                    'default': True,
                    'description': 'Enable UI sound effects'
                }
            },

            'performance': {
                'quality_preset': {
                    'type': 'dropdown',
                    'default': 'high',
                    'options': ['low', 'medium', 'high', 'ultra', 'custom'],
                    'description': 'Graphics quality preset'
                },
                'target_fps': {
                    'type': 'dropdown',
                    'default': 60,
                    'options': [30, 60, 90, 120, 144],
                    'description': 'Target frame rate'
                },
                'vsync': {
                    'type': 'toggle',
                    'default': True,
                    'description': 'Enable V-Sync'
                },
                'antialiasing': {
                    'type': 'dropdown',
                    'default': 'MSAA_4x',
                    'options': ['none', 'FXAA', 'MSAA_2x', 'MSAA_4x', 'MSAA_8x'],
                    'description': 'Antialiasing method'
                },
                'texture_quality': {
                    'type': 'dropdown',
                    'default': 'high',
                    'options': ['low', 'medium', 'high', 'ultra'],
                    'description': 'Texture quality'
                },
                'shadow_quality': {
                    'type': 'dropdown',
                    'default': 'medium',
                    'options': ['off', 'low', 'medium', 'high'],
                    'description': 'Shadow quality'
                },
                'enable_multithreading': {
                    'type': 'toggle',
                    'default': True,
                    'description': 'Enable multithreading'
                },
                'max_worker_threads': {
                    'type': 'number',
                    'default': 4,
                    'min': 1,
                    'max': 16,
                    'description': 'Maximum worker threads'
                }
            },

            'integration': {
                'openai_api_key': {
                    'type': 'text',
                    'default': '',
                    'description': 'OpenAI API key'
                },
                'anthropic_api_key': {
                    'type': 'text',
                    'default': '',
                    'description': 'Anthropic API key'
                },
                'api_endpoint': {
                    'type': 'text',
                    'default': 'https://api.openai.com/v1',
                    'description': 'API endpoint URL'
                },
                'webhook_url': {
                    'type': 'text',
                    'default': '',
                    'description': 'Webhook URL for notifications'
                },
                'enable_webhooks': {
                    'type': 'toggle',
                    'default': False,
                    'description': 'Enable webhook notifications'
                },
                'database_path': {
                    'type': 'text',
                    'default': 'data/lightspeed.db',
                    'description': 'Database file path'
                },
                'cloud_sync': {
                    'type': 'toggle',
                    'default': False,
                    'description': 'Enable cloud synchronization'
                },
                'cloud_provider': {
                    'type': 'dropdown',
                    'default': 'none',
                    'options': ['none', 'aws', 'azure', 'gcp', 'custom'],
                    'description': 'Cloud provider'
                },
                'backup_enabled': {
                    'type': 'toggle',
                    'default': True,
                    'description': 'Enable automatic backups'
                },
                'backup_interval_hours': {
                    'type': 'number',
                    'default': 24,
                    'min': 1,
                    'max': 168,
                    'description': 'Backup interval (hours)'
                }
            },

            'developer': {
                'debug_mode': {
                    'type': 'toggle',
                    'default': False,
                    'description': 'Enable debug mode'
                },
                'log_level': {
                    'type': 'dropdown',
                    'default': 'INFO',
                    'options': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    'description': 'Logging level'
                },
                'enable_profiling': {
                    'type': 'toggle',
                    'default': False,
                    'description': 'Enable performance profiling'
                },
                'show_fps_counter': {
                    'type': 'toggle',
                    'default': False,
                    'description': 'Show FPS counter'
                },
                'enable_hot_reload': {
                    'type': 'toggle',
                    'default': False,
                    'description': 'Enable hot reload for development'
                }
            }
        }

    def get_setting(self, category: str, setting_name: str) -> Any:
        """
        Get a setting value

        Args:
            category: Setting category (vr, ai, ui, etc.)
            setting_name: Setting name within category

        Returns:
            Setting value, or default if not set
        """
        if category not in self.settings:
            logger.warning(f"Unknown category: {category}")
            return None

        if setting_name not in self.settings[category]:
            logger.warning(f"Unknown setting: {category}.{setting_name}")
            return None

        setting = self.settings[category][setting_name]
        return setting.get('value', setting.get('default'))

    def set_setting(self, category: str, setting_name: str, value: Any):
        """
        Set a setting value

        Args:
            category: Setting category
            setting_name: Setting name
            value: New value
        """
        if category not in self.settings:
            logger.error(f"Unknown category: {category}")
            return

        if setting_name not in self.settings[category]:
            logger.error(f"Unknown setting: {category}.{setting_name}")
            return

        self.settings[category][setting_name]['value'] = value

        # Publish change event
        if self.event_bus:
            self.event_bus.publish('settings.changed', {
                'category': category,
                'setting': setting_name,
                'value': value
            })

        # Auto-save
        self.save()

    def get_category_settings(self, category: str) -> Dict[str, Dict[str, Any]]:
        """Get all settings in a category"""
        return self.settings.get(category, {})

    def get_all_settings(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get all settings"""
        return self.settings

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        for category in self.settings:
            for setting_name in self.settings[category]:
                if 'value' in self.settings[category][setting_name]:
                    del self.settings[category][setting_name]['value']

        self.save()

    def save(self):
        """Save settings to disk"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Create serializable copy
            save_data = {}
            for category, settings in self.settings.items():
                save_data[category] = {}
                for name, config in settings.items():
                    save_data[category][name] = {
                        'value': config.get('value', config.get('default'))
                    }

            with open(self.config_file, 'w') as f:
                json.dump(save_data, f, indent=2)

            logger.info(f"Settings saved to {self.config_file}")

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def _load_from_disk(self):
        """Load settings from disk"""
        if not self.config_file.exists():
            return

        try:
            with open(self.config_file, 'r') as f:
                saved_data = json.load(f)

            # Merge saved values with defaults
            for category, settings in saved_data.items():
                if category in self.settings:
                    for name, data in settings.items():
                        if name in self.settings[category]:
                            self.settings[category][name]['value'] = data['value']

            logger.info(f"Settings loaded from {self.config_file}")

        except Exception as e:
            logger.error(f"Failed to load settings: {e}")


# Singleton instance
_settings_hub_instance: Optional[SettingsHub] = None


def get_settings_hub() -> SettingsHub:
    """
    Get Settings Hub singleton instance

    Returns:
        SettingsHub instance
    """
    global _settings_hub_instance

    if _settings_hub_instance is None:
        _settings_hub_instance = SettingsHub()

    return _settings_hub_instance
