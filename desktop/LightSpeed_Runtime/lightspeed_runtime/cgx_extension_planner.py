from __future__ import annotations

"""Deterministic preflight planner for extending CGX capabilities.

The planner proves whether a new shortcall/tool/adapter is actually needed before
code is created. It never installs dependencies, writes manifests, or exposes a
model-callable generic executor.
"""

import json
from pathlib import Path
import re
from typing import Any, Iterable

from lightspeed_runtime.cgx_capability_registry import (
    DEFAULT_ROUTES_PATH,
    DEFAULT_SHORTCALLS_PATH,
    load_capability_routes,
    load_selector_shortcalls,
    normalize_shortcall,
    selector_profile,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TOOLKIT_PATH = REPO_ROOT / "cgx" / "domain_templates" / "toolkit_registry.json"


class CGXExtensionPlanError(ValueError):
    """Raised when an extension request is malformed."""


def _tokens(value: Any) -> set[str]:
    text = re.sub(r"[^a-z0-9]+", " ", str(value or "").lower())
    return {token for token in text.split() if len(token) > 1}


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CGXExtensionPlanError(f"expected object: {path}")
    return payload


def _score(needle: set[str], values: Iterable[Any]) -> int:
    haystack: set[str] = set()
    for value in values:
        haystack |= _tokens(value)
    return len(needle & haystack)


def plan_tool_extension(
    selector: str,
    goal: str,
    *,
    desired_kind: str = "auto",
    requested_shortcall: str | None = None,
    required_capabilities: Iterable[str] = (),
    toolkit_path: Path = DEFAULT_TOOLKIT_PATH,
) -> dict[str, Any]:
    goal = str(goal or "").strip()
    if not goal:
        raise CGXExtensionPlanError("goal must be non-empty")

    routes_payload = load_capability_routes(DEFAULT_ROUTES_PATH)
    shortcalls_payload = load_selector_shortcalls(DEFAULT_SHORTCALLS_PATH)
    profile = selector_profile(selector, routes=routes_payload, shortcalls=shortcalls_payload)
    routes = routes_payload["routes"]
    goal_tokens = _tokens(goal) | set().union(*(_tokens(item) for item in required_capabilities))

    if requested_shortcall:
        token = normalize_shortcall(requested_shortcall)
        all_calls = dict(profile["global_shortcalls"])
        all_calls.update(profile["shortcalls"])
        route_id = all_calls.get(token)
        if route_id:
            return {
                "schema": "CGX-EXTENSION-PLAN/0.1",
                "selector": profile["selector"],
                "goal": goal,
                "decision": "reuse_existing",
                "existing_route": route_id,
                "requested_shortcall": token,
                "route": routes[route_id],
                "implementation_required": False,
                "next_steps": [
                    "use the existing route",
                    "add no duplicate tool",
                    "collect normal receipt/evidence output",
                ],
            }

    route_candidates: list[dict[str, Any]] = []
    selector_calls = dict(profile["global_shortcalls"])
    selector_calls.update(profile["shortcalls"])
    for route_id, record in routes.items():
        aliases = [call for call, rid in selector_calls.items() if rid == route_id]
        score = _score(
            goal_tokens,
            [
                route_id,
                record.get("kind"),
                record.get("state"),
                record.get("limitation"),
                *aliases,
                *(record.get("uses") or []),
            ],
        )
        if score:
            route_candidates.append(
                {
                    "route_id": route_id,
                    "score": score,
                    "state": record.get("state"),
                    "kind": record.get("kind"),
                    "aliases": aliases,
                    "handler": record.get("handler"),
                    "limitation": record.get("limitation"),
                }
            )
    route_candidates.sort(key=lambda item: (-int(item["score"]), str(item["route_id"])))

    toolkit_payload = _read_json(toolkit_path)
    toolkit_candidates: list[dict[str, Any]] = []
    for item in toolkit_payload.get("toolkits") or []:
        score = _score(
            goal_tokens,
            [item.get("id"), item.get("kind"), item.get("binding"), *(item.get("capabilities") or [])],
        )
        if score:
            toolkit_candidates.append(
                {
                    "toolkit_id": item.get("id"),
                    "score": score,
                    "kind": item.get("kind"),
                    "binding": item.get("binding"),
                    "capabilities": list(item.get("capabilities") or []),
                }
            )
    toolkit_candidates.sort(key=lambda item: (-int(item["score"]), str(item["toolkit_id"])))

    gap_candidates: list[dict[str, Any]] = []
    for gap in routes_payload.get("gaps") or []:
        score = _score(goal_tokens, [gap.get("id"), gap.get("state"), gap.get("priority"), gap.get("note")])
        if score:
            gap_candidates.append({**gap, "score": score})
    gap_candidates.sort(key=lambda item: (-int(item["score"]), str(item["id"])))

    best_route = route_candidates[0] if route_candidates else None
    if best_route and best_route["state"] in {"available", "workflow", "gated", "assisted"}:
        decision = "reuse_or_alias"
        implementation_required = False
    elif best_route and best_route["state"] == "registered_unwrapped":
        decision = "wrap_registered_tool"
        implementation_required = True
    elif best_route and best_route["state"] == "missing":
        decision = "implement_smallest_adapter"
        implementation_required = True
    elif gap_candidates:
        decision = "implement_smallest_adapter"
        implementation_required = True
    else:
        decision = "extension_candidate"
        implementation_required = True

    return {
        "schema": "CGX-EXTENSION-PLAN/0.1",
        "selector": profile["selector"],
        "goal": goal,
        "desired_kind": str(desired_kind or "auto"),
        "required_capabilities": [str(item) for item in required_capabilities],
        "decision": decision,
        "implementation_required": implementation_required,
        "best_existing_route": best_route,
        "route_candidates": route_candidates[:8],
        "toolkit_candidates": toolkit_candidates[:8],
        "gap_candidates": gap_candidates[:8],
        "extension_sequence": [
            "resolve current authority/recovery state",
            "reuse existing route or alias when sufficient",
            "define bounded inputs/outputs and evidence state",
            "implement the smallest typed adapter only if missing",
            "add unit/failure/receipt tests",
            "register route once in the shared capability registry",
            "add shortcall/skill only when it improves human invocation",
            "rebuild all selector packages from the shared source",
            "expose validated operations individually through one shared MCP plane when transport is available",
        ],
        "safety": {
            "generic_shell_tool": False,
            "automatic_install": False,
            "automatic_external_write": False,
            "automatic_authority": False,
        },
    }


__all__ = ["CGXExtensionPlanError", "plan_tool_extension"]
