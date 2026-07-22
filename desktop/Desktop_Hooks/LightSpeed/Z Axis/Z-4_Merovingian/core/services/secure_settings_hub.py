"""Secure provider-secret boundary for the LightSpeed Settings Hub.

Provider API keys are runtime secrets. They are read from environment variables,
never returned through generic UI/settings access, and never written to
``config/settings.json``. The legacy SettingsHub remains the source for ordinary
settings while this wrapper safely scrubs any older plaintext secret values.
"""

from __future__ import annotations

from copy import deepcopy
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .settings_hub import SettingsHub as LegacySettingsHub

logger = logging.getLogger(__name__)

SECRET_ENVIRONMENTS: dict[tuple[str, str], str] = {
    ("integration", "openai_api_key"): "OPENAI_API_KEY",
    ("integration", "anthropic_api_key"): "ANTHROPIC_API_KEY",
}


class SettingsHub(LegacySettingsHub):
    """Settings hub that keeps provider credentials outside persisted config."""

    def _initialize_default_settings(self) -> None:
        super()._initialize_default_settings()
        for (category, setting_name), environment_name in SECRET_ENVIRONMENTS.items():
            setting = self.settings[category][setting_name]
            setting.update(
                {
                    "type": "secret_env",
                    "default": "",
                    "env_var": environment_name,
                    "persist": False,
                    "description": f"Provider credential supplied through {environment_name}",
                }
            )
            setting.pop("value", None)

    @staticmethod
    def _secret_environment(category: str, setting_name: str) -> Optional[str]:
        return SECRET_ENVIRONMENTS.get((category, setting_name))

    def get_setting(self, category: str, setting_name: str) -> Any:
        """Return ordinary values while keeping secrets out of generic UI access."""
        if self._secret_environment(category, setting_name):
            return ""
        return super().get_setting(category, setting_name)

    def get_secret(self, category: str, setting_name: str) -> str:
        """Return one provider secret from its environment variable.

        This method is intended for the local provider adapter only. Callers must
        not log, persist, serialize or expose its return value to LS GO or UI state.
        """
        environment_name = self._secret_environment(category, setting_name)
        if environment_name is None:
            raise KeyError(f"{category}.{setting_name} is not a registered secret setting")
        return os.environ.get(environment_name, "")

    def secret_status(self, category: str, setting_name: str) -> dict[str, Any]:
        """Return non-sensitive provider configuration state."""
        environment_name = self._secret_environment(category, setting_name)
        if environment_name is None:
            raise KeyError(f"{category}.{setting_name} is not a registered secret setting")
        return {
            "configured": bool(os.environ.get(environment_name)),
            "source": "environment",
            "env_var": environment_name,
        }

    def set_setting(self, category: str, setting_name: str, value: Any) -> None:
        """Reject attempts to place provider keys into the persisted settings UI."""
        environment_name = self._secret_environment(category, setting_name)
        if environment_name is not None:
            if value not in (None, ""):
                raise ValueError(
                    f"{category}.{setting_name} is environment-only; configure {environment_name} instead"
                )
            return
        super().set_setting(category, setting_name, value)

    def _sanitized_settings(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        sanitized = deepcopy(self.settings)
        for (category, setting_name), environment_name in SECRET_ENVIRONMENTS.items():
            record = sanitized[category][setting_name]
            record.pop("value", None)
            record["default"] = ""
            record["configured"] = bool(os.environ.get(environment_name))
            record["source"] = "environment"
            record["env_var"] = environment_name
            record["persist"] = False
        return sanitized

    def get_category_settings(self, category: str) -> Dict[str, Dict[str, Any]]:
        """Return a defensive, redacted copy of one settings category."""
        return self._sanitized_settings().get(category, {})

    def get_all_settings(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Return a defensive, redacted copy of all settings."""
        return self._sanitized_settings()

    def save(self) -> None:
        """Persist ordinary settings and non-sensitive secret status metadata."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            save_data: dict[str, dict[str, dict[str, Any]]] = {}
            for category, settings in self.settings.items():
                save_data[category] = {}
                for name, config in settings.items():
                    environment_name = self._secret_environment(category, name)
                    if environment_name is not None:
                        save_data[category][name] = {
                            "configured": bool(os.environ.get(environment_name)),
                            "source": "environment",
                            "env_var": environment_name,
                        }
                        continue
                    save_data[category][name] = {
                        "value": config.get("value", config.get("default"))
                    }

            temporary = self.config_file.with_suffix(self.config_file.suffix + ".tmp")
            temporary.write_text(json.dumps(save_data, indent=2) + "\n", encoding="utf-8")
            temporary.replace(self.config_file)
            logger.info("Settings saved to %s with provider secrets redacted", self.config_file)
        except Exception as exc:
            logger.error("Failed to save settings: %s", exc)

    def _load_from_disk(self) -> None:
        """Load ordinary settings and scrub any legacy plaintext provider keys."""
        if not self.config_file.exists():
            return

        legacy_secret_found = False
        try:
            saved_data = json.loads(self.config_file.read_text(encoding="utf-8"))
            if not isinstance(saved_data, dict):
                raise ValueError("settings root must be an object")

            for category, settings in saved_data.items():
                if category not in self.settings or not isinstance(settings, dict):
                    continue
                for name, data in settings.items():
                    if name not in self.settings[category] or not isinstance(data, dict):
                        continue
                    if self._secret_environment(category, name) is not None:
                        if data.get("value"):
                            legacy_secret_found = True
                        self.settings[category][name].pop("value", None)
                        continue
                    if "value" in data:
                        self.settings[category][name]["value"] = data["value"]

            logger.info("Settings loaded from %s", self.config_file)
            if legacy_secret_found:
                logger.warning(
                    "Legacy plaintext provider secret found in %s; rewriting a redacted settings file",
                    self.config_file,
                )
                self.save()
        except Exception as exc:
            logger.error("Failed to load settings: %s", exc)


_settings_hub_instance: Optional[SettingsHub] = None


def get_settings_hub() -> SettingsHub:
    """Return the secure Settings Hub singleton."""
    global _settings_hub_instance
    if _settings_hub_instance is None:
        _settings_hub_instance = SettingsHub()
    return _settings_hub_instance
