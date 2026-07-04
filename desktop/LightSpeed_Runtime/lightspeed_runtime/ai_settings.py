from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from lightspeed_runtime.storage_paths import canonical_ai_settings_path, resolve_ai_settings_path


DEFAULT_AI_SETTINGS: dict = {
    "active_backend": "ollama_local",
    "active_profile": "low_lag_local",
    "hardcoded_automation": {
        "enabled": True,
        "mode": "local_assisted",
        "approval_required": True,
        "low_lag": True,
    },
    "backends": {
        "ollama_local": {
            "label": "Local Ollama",
            "type": "ollama",
            "enabled": True,
            "host": "http://localhost:11434",
            "model": "qwen3:8b",
            "timeout_s": 30,
        },
        "remote_api": {
            "label": "Remote API",
            "type": "api",
            "enabled": False,
            "provider": "openai",
            "model": "gpt-5-mini",
            "timeout_s": 45,
        },
        "disabled": {
            "label": "Disabled",
            "type": "disabled",
            "enabled": False,
        },
    },
    "profiles": {
        "low_lag_local": {
            "label": "Low-Lag Local",
            "backend": "ollama_local",
            "max_context_chars": 6000,
            "stream": True,
            "local_first": True,
        },
        "balanced_local": {
            "label": "Balanced Local",
            "backend": "ollama_local",
            "max_context_chars": 12000,
            "stream": True,
            "local_first": True,
        },
        "deep_reasoning_remote": {
            "label": "Deep Reasoning Remote",
            "backend": "remote_api",
            "max_context_chars": 24000,
            "stream": False,
            "local_first": False,
        },
    },
    "achilles": {
        "enabled": True,
        "approval_gated": True,
        "operator_mode": "desktop_orchestrator",
        "auto_safe_actions": True,
    },
    "smart_floors": {
        "Oracle": {"mode": "retrieval"},
        "Morpheus": {"mode": "search"},
        "Architect": {"mode": "approval"},
        "Trinity": {"mode": "execution"},
        "Neo": {"mode": "operator"},
    },
    "personas": {
        "achilles": {
            "system_prompt": "You are Achilles, the primary Cognigrex operator for LightSpeed.",
            "tone": "precise",
        },
        "clippy": {
            "system_prompt": "You are Clippy, a friendly LightSpeed assistant.",
            "tone": "friendly",
        },
        "orchestrator": {
            "system_prompt": "You are the LightSpeed Orchestrator AI.",
            "tone": "professional",
        },
    },
}


def runtime_ai_config_path(root: Path) -> Path:
    return canonical_ai_settings_path(root)


def _merge_dict(base: dict, incoming: dict) -> dict:
    merged = deepcopy(base)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def normalize_ai_settings(raw: dict | None) -> dict:
    """Normalize hardened AI settings while preserving legacy shapes."""
    settings = deepcopy(DEFAULT_AI_SETTINGS)
    if not isinstance(raw, dict):
        return settings

    if any(key in raw for key in ("active_backend", "backends", "profiles", "smart_floors", "personas")):
        settings = _merge_dict(settings, raw)

    old_ollama = raw.get("ollama")
    if isinstance(old_ollama, dict):
        settings["backends"]["ollama_local"] = _merge_dict(settings["backends"]["ollama_local"], old_ollama)
        if old_ollama.get("enabled") is False and settings.get("active_backend") == "ollama_local":
            settings["active_backend"] = "disabled"

    old_achilles = raw.get("achilles")
    if isinstance(old_achilles, dict):
        achilles_settings = dict(settings.get("achilles", {}))
        achilles_settings["enabled"] = bool(old_achilles.get("enabled", achilles_settings.get("enabled", True)))
        if "approval_gated" in old_achilles:
            achilles_settings["approval_gated"] = bool(old_achilles["approval_gated"])
        settings["achilles"] = achilles_settings

    old_modes = raw.get("modes")
    if isinstance(old_modes, dict):
        personas = dict(settings.get("personas", {}))
        for name, value in old_modes.items():
            if isinstance(value, dict):
                personas[name] = _merge_dict(personas.get(name, {}), value)
        settings["personas"] = personas

    active_backend = settings.get("active_backend")
    if active_backend not in settings["backends"]:
        settings["active_backend"] = "ollama_local"

    active_profile = settings.get("active_profile")
    if active_profile not in settings["profiles"]:
        settings["active_profile"] = "low_lag_local"

    profile_backend = settings["profiles"][settings["active_profile"]].get("backend")
    if profile_backend in settings["backends"]:
        settings["active_backend"] = profile_backend

    return settings


def load_ai_settings(root: Path) -> dict:
    root = Path(root)
    path = resolve_ai_settings_path(root)
    if not path.exists():
        return deepcopy(DEFAULT_AI_SETTINGS)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        raw = {}
    if not isinstance(raw, dict):
        return deepcopy(DEFAULT_AI_SETTINGS)
    return normalize_ai_settings(raw)


def save_ai_settings(root: Path, settings: dict) -> Path:
    path = runtime_ai_config_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_ai_settings(settings)
    path.write_text(json.dumps(normalized, indent=2), encoding="utf-8")
    return path


def ai_backend_summary(settings: dict) -> dict:
    active_backend = settings.get("active_backend", "ollama_local")
    backend = dict(settings.get("backends", {}).get(active_backend, {}))
    active_profile = settings.get("active_profile", "low_lag_local")
    profile = dict(settings.get("profiles", {}).get(active_profile, {}))
    achilles = dict(settings.get("achilles", {}))
    automation = dict(settings.get("hardcoded_automation", {}))
    return {
        "active_backend": active_backend,
        "backend_label": backend.get("label", active_backend),
        "backend_type": backend.get("type", "unknown"),
        "host": backend.get("host", ""),
        "model": backend.get("model", ""),
        "active_profile": active_profile,
        "profile_label": profile.get("label", active_profile),
        "local_first": bool(profile.get("local_first", True)),
        "low_lag": bool(automation.get("low_lag", True)),
        "automation_enabled": bool(automation.get("enabled", True)),
        "automation_mode": automation.get("mode", "local_assisted"),
        "achilles_enabled": bool(achilles.get("enabled", True)),
        "approval_gated": bool(achilles.get("approval_gated", True)),
        "auto_safe_actions": bool(achilles.get("auto_safe_actions", True)),
    }
