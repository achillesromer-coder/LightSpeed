from __future__ import annotations

"""Resolve CGX selector shortcalls against the canonical capability registries."""

from copy import deepcopy
import json
from pathlib import Path
import re
import unicodedata
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ROUTES_PATH = REPO_ROOT / "cgx" / "domain_templates" / "plugin_capability_routes.json"
DEFAULT_SHORTCALLS_PATH = REPO_ROOT / "plugins" / "source" / "selector_shortcalls.json"

_SHORTCALL_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class CapabilityRegistryError(RuntimeError):
    """Raised when capability metadata is missing, inconsistent, or unresolved."""


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CapabilityRegistryError(f"expected object: {path}")
    return payload


def normalize_shortcall(value: str) -> str:
    token = str(value or "").strip().lower()
    if token.startswith("/"):
        token = token[1:]
    token = token.replace(" ", "-")
    if not token or not _SHORTCALL_RE.fullmatch(token):
        raise CapabilityRegistryError(f"invalid shortcall: {value!r}")
    return token
def load_capability_routes(path: Path = DEFAULT_ROUTES_PATH) -> dict[str, Any]:
    payload = _read_json(path)
    validate_capability_routes(payload)
    return payload


def load_selector_shortcalls(path: Path = DEFAULT_SHORTCALLS_PATH) -> dict[str, Any]:
    payload = _read_json(path)
    validate_selector_shortcalls(payload, load_capability_routes())
    return payload


def validate_capability_routes(payload: dict[str, Any]) -> None:
    routes = payload.get("routes")
    if not isinstance(routes, dict) or not routes:
        raise CapabilityRegistryError("capability routes are missing")
    valid_states = {"available", "workflow", "gated", "assisted", "registered_unwrapped", "missing"}
    for route_id, record in routes.items():
        if not isinstance(route_id, str) or not route_id:
            raise CapabilityRegistryError("route id must be a non-empty string")
        if not isinstance(record, dict):
            raise CapabilityRegistryError(f"route must be object: {route_id}")
        if record.get("state") not in valid_states:
            raise CapabilityRegistryError(f"invalid route state: {route_id}")
        if record.get("kind") == "runtime" and not record.get("handler"):
            raise CapabilityRegistryError(f"runtime route missing handler: {route_id}")
        if record.get("state") == "missing" and record.get("handler"):
            raise CapabilityRegistryError(f"missing route cannot have handler: {route_id}")


def validate_selector_shortcalls(
    payload: dict[str, Any],
    route_registry: dict[str, Any],
) -> None:
    routes = route_registry["routes"]
    selectors = payload.get("selectors")
    if not isinstance(selectors, dict) or len(selectors) != 9:
        raise CapabilityRegistryError("expected nine selector profiles")
    for selector, profile in selectors.items():
        if not isinstance(profile, dict):
            raise CapabilityRegistryError(f"invalid selector profile: {selector}")
        shortcalls = profile.get("shortcalls")
        if not isinstance(shortcalls, dict) or not shortcalls:
            raise CapabilityRegistryError(f"selector has no shortcalls: {selector}")
        for raw, route_id in shortcalls.items():
            token = normalize_shortcall(raw)
            if token != raw:
                raise CapabilityRegistryError(f"shortcall must already be normalized: {raw}")
            if route_id not in routes:
                raise CapabilityRegistryError(f"unknown route {route_id!r} in {selector}/{raw}")
    for raw, route_id in (payload.get("global") or {}).items():
        normalize_shortcall(raw)
        if route_id not in routes:
            raise CapabilityRegistryError(f"unknown global route: {route_id}")


def expand_route_dependencies(
    route_ids: set[str], routes: dict[str, Any]
) -> set[str]:
    resolved: set[str] = set()
    pending = list(route_ids)
    while pending:
        route_id = pending.pop()
        if route_id in resolved:
            continue
        if route_id not in routes:
            raise CapabilityRegistryError(f"capability dependency missing: {route_id}")
        resolved.add(route_id)
        pending.extend(str(item) for item in (routes[route_id].get("uses") or []))
    return resolved


def selector_profile(
    selector: str,
    *,
    routes: dict[str, Any] | None = None,
    shortcalls: dict[str, Any] | None = None,
) -> dict[str, Any]:
    route_registry = routes or load_capability_routes()
    shortcall_registry = shortcalls or load_selector_shortcalls()
    selector_token = unicodedata.normalize("NFKD", str(selector or "").lstrip("@"))
    selector_token = "".join(ch for ch in selector_token if not unicodedata.combining(ch))
    key = normalize_shortcall(selector_token)
    profile = (shortcall_registry.get("selectors") or {}).get(key)
    if not isinstance(profile, dict):
        raise CapabilityRegistryError(f"unknown selector: {selector}")
    merged = deepcopy(profile)
    merged["selector"] = key
    merged["global_shortcalls"] = deepcopy(shortcall_registry.get("global") or {})
    referenced = set(merged["shortcalls"].values()) | set(merged["global_shortcalls"].values())
    referenced = expand_route_dependencies(referenced, route_registry["routes"])
    merged["routes"] = {route_id: deepcopy(route_registry["routes"][route_id]) for route_id in sorted(referenced)}
    merged["gaps"] = deepcopy(route_registry.get("gaps") or [])
    merged["extension"] = deepcopy(route_registry.get("extension") or {})
    return merged


def list_shortcalls(selector: str) -> dict[str, str]:
    profile = selector_profile(selector)
    output = dict(profile["global_shortcalls"])
    output.update(profile["shortcalls"])
    return output
def resolve_shortcall(selector: str, shortcall: str) -> dict[str, Any]:
    profile = selector_profile(selector)
    token = normalize_shortcall(shortcall)
    route_id = profile["shortcalls"].get(token)
    scope = "selector"
    if route_id is None:
        route_id = profile["global_shortcalls"].get(token)
        scope = "global"
    if route_id is None:
        raise CapabilityRegistryError(f"unknown shortcall /{token} for {profile['selector']}")
    route = load_capability_routes()["routes"][route_id]
    return {
        "selector": profile["selector"],
        "shortcall": token,
        "scope": scope,
        "route_id": route_id,
        "route": deepcopy(route),
        "preferred_floors": list(profile.get("floors") or []),
        "toolkits": list(profile.get("toolkits") or []),
    }


def capability_summary(selector: str) -> dict[str, Any]:
    profile = selector_profile(selector)
    routes = load_capability_routes()["routes"]
    calls = list_shortcalls(selector)
    grouped: dict[str, list[str]] = {}
    for call, route_id in sorted(calls.items()):
        state = str(routes[route_id]["state"])
        grouped.setdefault(state, []).append(call)
    return {
        "selector": profile["selector"],
        "shortcall_count": len(calls),
        "by_state": grouped,
        "preferred_floors": profile.get("floors") or [],
        "toolkits": profile.get("toolkits") or [],
        "gaps": profile.get("gaps") or [],
    }
