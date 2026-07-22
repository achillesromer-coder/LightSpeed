from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

DESKTOP_ROOT = Path(__file__).resolve().parents[2] / "Desktop_Hooks" / "LightSpeed"
if str(DESKTOP_ROOT) not in sys.path:
    sys.path.insert(0, str(DESKTOP_ROOT))

from core.services.secure_settings_hub import SettingsHub


def test_provider_secret_is_environment_only(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")

    hub = SettingsHub()

    assert hub.get_setting("integration", "openai_api_key") == ""
    assert hub.get_secret("integration", "openai_api_key") == "sk-test-not-a-real-key"
    assert hub.secret_status("integration", "openai_api_key") == {
        "configured": True,
        "source": "environment",
        "env_var": "OPENAI_API_KEY",
    }

    hub.set_setting("integration", "api_endpoint", "https://api.openai.com/v1")
    persisted = (tmp_path / "config" / "settings.json").read_text(encoding="utf-8")
    payload = json.loads(persisted)

    assert "sk-test-not-a-real-key" not in persisted
    assert payload["integration"]["openai_api_key"] == {
        "configured": True,
        "source": "environment",
        "env_var": "OPENAI_API_KEY",
    }

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        hub.set_setting("integration", "openai_api_key", "sk-inline-not-allowed")


def test_legacy_plaintext_secret_is_scrubbed(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config_path = tmp_path / "config" / "settings.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "integration": {
                    "openai_api_key": {"value": "sk-legacy-not-allowed"},
                    "api_endpoint": {"value": "https://api.openai.com/v1"},
                }
            }
        ),
        encoding="utf-8",
    )

    hub = SettingsHub()
    persisted = config_path.read_text(encoding="utf-8")
    payload = json.loads(persisted)

    assert hub.get_secret("integration", "openai_api_key") == ""
    assert hub.get_setting("integration", "api_endpoint") == "https://api.openai.com/v1"
    assert "sk-legacy-not-allowed" not in persisted
    assert payload["integration"]["openai_api_key"] == {
        "configured": False,
        "source": "environment",
        "env_var": "OPENAI_API_KEY",
    }


def test_redacted_exports_do_not_expose_environment_values(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test-secret")

    hub = SettingsHub()
    category = hub.get_category_settings("integration")
    all_settings = hub.get_all_settings()

    assert category["anthropic_api_key"]["configured"] is True
    assert category["anthropic_api_key"]["default"] == ""
    assert "value" not in category["anthropic_api_key"]
    assert "anthropic-test-secret" not in json.dumps(all_settings)
