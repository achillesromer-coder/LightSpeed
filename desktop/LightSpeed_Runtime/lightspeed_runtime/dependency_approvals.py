from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from lightspeed_runtime.ai_settings import load_ai_settings
from lightspeed_runtime.storage_paths import architect_root


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_dependency_approval_path(root: Path) -> Path:
    return architect_root(root) / "data" / "approvals" / "dependency_approvals.json"


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            if isinstance(payload, dict):
                return payload
    except Exception:
        pass
    return {}


def _normalize_name(value: str) -> str:
    return str(value or "").strip()


def _approval_record(
    *,
    kind: str,
    name: str,
    available: bool,
    owner_floor: str,
    request_floor: str,
    reason: str,
    source: str,
    priority: str = "medium",
) -> Dict[str, Any]:
    status = "available" if available else "approval_required"
    return {
        "id": f"{kind}.{_normalize_name(name).lower().replace(' ', '_')}",
        "kind": kind,
        "name": _normalize_name(name),
        "status": status,
        "available": bool(available),
        "owner_floor": owner_floor,
        "request_floor": request_floor,
        "priority": priority,
        "reason": reason,
        "source": source,
        "requested_at": utc_now_iso(),
    }


def _iter_enabled_api_tools(settings: Dict[str, Any]) -> Iterable[tuple[str, bool]]:
    apis = settings.get("apis_enabled") if isinstance(settings.get("apis_enabled"), dict) else {}
    for key, value in sorted(apis.items(), key=lambda item: str(item[0])):
        yield str(key), bool(value)


def build_dependency_approval_queue(root: Path) -> Dict[str, Any]:
    """
    Plan approvals for missing tools/libraries without mutating installation state.

    This returns a queue that Smith/Neo/Trinity can use to request approval or
    show disabled actions in compact menus.
    """
    root = Path(root).resolve()
    registry = _read_json(root / "config" / "function_registry.json")
    settings = _read_json(root / "config" / "settings.json")
    ai_settings = load_ai_settings(root)

    libraries = registry.get("libraries") if isinstance(registry.get("libraries"), dict) else {}
    missing_libraries = []
    for name, record in sorted(libraries.items(), key=lambda item: str(item[0]).lower()):
        if isinstance(record, dict) and record.get("available") is False:
            missing_libraries.append(
                _approval_record(
                    kind="library",
                    name=name,
                    available=False,
                    owner_floor="Merovingian",
                    request_floor="Smith",
                    reason=str(record.get("description") or "Library is unavailable and should be queued for approval."),
                    source="config/function_registry.json",
                    priority="medium",
                )
            )

    missing_tools = []
    for name, enabled in _iter_enabled_api_tools(settings):
        if enabled:
            continue
        missing_tools.append(
            _approval_record(
                kind="api",
                name=name,
                available=False,
                owner_floor="Trinity",
                request_floor="Neo",
                reason=f"{name} API is disabled in settings and should be approved before use.",
                source="config/settings.json",
                priority="low" if name in {"weather", "qr"} else "medium",
            )
        )

    backend_enabled = bool(ai_settings.get("achilles", {}).get("enabled", True))
    backend_status = _approval_record(
        kind="ai_backend",
        name=str(ai_settings.get("active_backend") or "ollama_local"),
        available=backend_enabled,
        owner_floor="Neo",
        request_floor="Trinity",
        reason="AI backend availability and approval gating should remain explicit in compact menus.",
        source="config/ai_config.json",
        priority="high" if backend_enabled else "medium",
    )

    approvals = missing_libraries + missing_tools
    approvals.sort(key=lambda item: (item.get("kind", ""), item.get("name", "").lower()))

    return {
        "generated_at": utc_now_iso(),
        "owner_floor": "Trinity",
        "source_files": {
            "function_registry": str(root / "config" / "function_registry.json"),
            "settings": str(root / "config" / "settings.json"),
            "ai_settings": str(root / "config" / "ai_config.json"),
        },
        "approval_queue": approvals,
        "ai_backend_status": backend_status,
        "missing_library_count": len(missing_libraries),
        "missing_tool_count": len(missing_tools),
        "total_approvals": len(approvals),
        "summary": (
            f"{len(missing_tools)} tool/API approvals and {len(missing_libraries)} library approvals pending."
        ),
    }


def build_compact_tool_status_descriptors(root: Path) -> List[Dict[str, Any]]:
    """
    Build compact menu descriptors for tool/API status surfaces.

    The output is intentionally terse so it can drive a small smart menu.
    """
    root = Path(root).resolve()
    settings = _read_json(root / "config" / "settings.json")
    ai_settings = load_ai_settings(root)
    registry = _read_json(root / "config" / "function_registry.json")
    libraries = registry.get("libraries") if isinstance(registry.get("libraries"), dict) else {}
    descriptors: List[Dict[str, Any]] = []

    for name, enabled in sorted(_iter_enabled_api_tools(settings), key=lambda item: item[0].lower()):
        descriptors.append(
            {
                "kind": "api",
                "name": name,
                "label": name.replace("_", " ").title(),
                "status": "enabled" if enabled else "disabled",
                "owner_floor": "Trinity",
                "request_floor": "Neo" if not enabled else "Trinity",
                "action": "use" if enabled else "queue_approval",
                "summary": "Enabled in settings" if enabled else "Disabled in settings",
            }
        )

    for backend_name, backend in sorted((ai_settings.get("backends") or {}).items(), key=lambda item: str(item[0]).lower()):
        if not isinstance(backend, dict):
            continue
        descriptors.append(
            {
                "kind": "ai_backend",
                "name": backend_name,
                "label": backend.get("label") or backend_name,
                "status": "enabled" if backend.get("enabled") else "disabled",
                "owner_floor": "Neo",
                "request_floor": "Trinity",
                "action": "select" if backend.get("enabled") else "queue_approval",
                "summary": f"{backend.get('type') or 'backend'} backend",
            }
        )

    for name, record in sorted(libraries.items(), key=lambda item: str(item[0]).lower()):
        if not isinstance(record, dict):
            continue
        descriptors.append(
            {
                "kind": "library",
                "name": name,
                "label": name,
                "status": "available" if record.get("available") else "missing",
                "owner_floor": "Merovingian",
                "request_floor": "Smith",
                "action": "use" if record.get("available") else "queue_approval",
                "summary": str(record.get("description") or ""),
            }
        )

    descriptors.sort(key=lambda item: (item.get("kind", ""), item.get("name", "").lower()))
    return descriptors


def read_dependency_approval_queue(root: Path, output_path: Path | None = None) -> Dict[str, Any]:
    path = output_path or default_dependency_approval_path(root)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def write_dependency_approval_queue(root: Path, output_path: Path | None = None) -> Dict[str, Any]:
    destination = output_path or default_dependency_approval_path(root)
    payload = build_dependency_approval_queue(root)
    payload["path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
