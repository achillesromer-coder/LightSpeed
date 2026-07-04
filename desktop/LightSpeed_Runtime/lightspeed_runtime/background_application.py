from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from lightspeed_runtime.storage_paths import trinity_root


BACKGROUND_SCOPES = ("workspace", "project", "floor", "global")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_background_application_path(root: Path) -> Path:
    return trinity_root(root) / "ui" / "background_application.json"


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            if isinstance(payload, dict):
                return payload
    except Exception:
        pass
    return {}


def _normalize_scope(scope: str) -> str:
    value = str(scope or "").strip().lower()
    if value not in BACKGROUND_SCOPES:
        raise ValueError(f"Unsupported background scope: {scope}")
    return value


def _summary_scope_label(scope: str) -> str:
    mapping = {
        "workspace": "Workspace shell",
        "project": "Selected project wall",
        "floor": "Active Z-floor surface",
        "global": "All live surfaces",
    }
    return mapping[_normalize_scope(scope)]


def _surface_targets() -> List[Dict[str, str]]:
    return [
        {
            "scope": "workspace",
            "surface": "Workspace",
            "effect": "Apply to the top-level operator workspace shell only.",
            "scope_policy": "default_shell",
        },
        {
            "scope": "project",
            "surface": "Project",
            "effect": "Apply to the selected project wall and its component sets.",
            "scope_policy": "project_root_context",
        },
        {
            "scope": "floor",
            "surface": "Floor",
            "effect": "Apply to the current Z-floor surface and its compact inspector.",
            "scope_policy": "floor_context",
        },
        {
            "scope": "global",
            "surface": "Global",
            "effect": "Apply consistently across workspace, project, and floor surfaces.",
            "scope_policy": "all_surfaces",
        },
    ]


def build_background_application_plan(
    root: Path,
    *,
    settings: Dict[str, Any] | None = None,
    theme: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Build a deterministic background application plan without mutating live UI.

    Trinity owns the settings source. This module turns those values into a
    surface plan that the UI can consume later.
    """
    root = Path(root).resolve()
    settings_source = dict(settings or _read_json(root / "config" / "settings.json"))
    theme_source = dict(theme or _read_json(root / "config" / "premium_theme_config.json"))

    background_settings = {
        "mode": str(settings_source.get("background.mode") or "balanced"),
        "input_type": str(settings_source.get("background.input_type") or "multi_stop_gradient"),
        "gradient": str(settings_source.get("background.gradient") or ""),
        "image_path": str(settings_source.get("background.image_path") or ""),
        "environment_reference": str(settings_source.get("background.environment_reference") or ""),
        "scope": _normalize_scope(settings_source.get("background.scope") or "workspace"),
    }
    editable_inputs = list((theme_source.get("editable_backgrounds") or {}).get("inputs") or [])
    base_theme_modes = dict((theme_source.get("editable_backgrounds") or {}).get("base_themes") or {})

    surface_plans = []
    for target in _surface_targets():
        scope = target["scope"]
        scope_enabled = scope == background_settings["scope"] or background_settings["scope"] == "global"
        surface_plans.append(
            {
                "scope": scope,
                "surface": target["surface"],
                "scope_label": _summary_scope_label(scope),
                "active": scope_enabled,
                "mode": background_settings["mode"],
                "input_type": background_settings["input_type"],
                "effect": target["effect"],
                "scope_policy": target["scope_policy"],
                "preview": {
                    "gradient": background_settings["gradient"],
                    "image_path": background_settings["image_path"],
                    "environment_reference": background_settings["environment_reference"],
                },
            }
        )

    return {
        "generated_at": utc_now_iso(),
        "owner_floor": "Trinity",
        "contract_path": str(default_background_application_path(root)),
        "settings_path": str(root / "config" / "settings.json"),
        "theme_path": str(root / "config" / "premium_theme_config.json"),
        "base_theme_modes": base_theme_modes,
        "editable_inputs": editable_inputs,
        "background_settings": background_settings,
        "scope": background_settings["scope"],
        "surface_plans": surface_plans,
        "summary": (
            f"Planned {background_settings['mode']} background for "
            f"{_summary_scope_label(background_settings['scope'])}."
        ),
        "live_surface_policy": "read_only_plan",
    }


def build_background_scope_plan(root: Path, scope: str, *, settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    plan = build_background_application_plan(root, settings=settings)
    normalized = _normalize_scope(scope)
    selected = next((item for item in plan["surface_plans"] if item["scope"] == normalized), None)
    if selected is None:
        raise ValueError(f"Unsupported background scope: {scope}")
    return {
        "generated_at": plan["generated_at"],
        "owner_floor": plan["owner_floor"],
        "scope": normalized,
        "scope_label": selected["scope_label"],
        "mode": plan["background_settings"]["mode"],
        "input_type": plan["background_settings"]["input_type"],
        "surface": selected["surface"],
        "effect": selected["effect"],
        "active": selected["active"],
        "preview": selected["preview"],
        "summary": selected["effect"],
        "live_surface_policy": plan["live_surface_policy"],
    }


def read_background_application_plan(root: Path, output_path: Path | None = None) -> Dict[str, Any]:
    path = output_path or default_background_application_path(root)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def write_background_application_plan(root: Path, output_path: Path | None = None) -> Dict[str, Any]:
    destination = output_path or default_background_application_path(root)
    payload = build_background_application_plan(root)
    payload["path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
