from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class CGXViewPolicyError(RuntimeError):
    """Raised when a requested CGX projection cannot satisfy policy."""


_HYDRATION_SECONDARY_LIMITS = {
    "projection-lite": 0,
    "reader": 1,
    "editor": 2,
    "workstation": 3,
    "distributed": None,
}


def _load_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CGXViewPolicyError(f"unable to load CGX policy contract: {path}") from exc
    if not isinstance(payload, dict):
        raise CGXViewPolicyError(f"CGX policy contract is not an object: {path}")
    return payload


def resolve_domain_template_root(runtime_root: Path | str) -> Path:
    root = Path(runtime_root).resolve()
    for candidate in (root, *root.parents):
        templates = candidate / "cgx" / "domain_templates"
        if (templates / "view_selection_policy.json").is_file() and (
            templates / "semantic_view_lens_registry.json"
        ).is_file():
            return templates
    raise CGXViewPolicyError("CGX domain template root is unavailable")


def load_runtime_view_contracts(runtime_root: Path | str) -> tuple[dict, dict]:
    templates = resolve_domain_template_root(runtime_root)
    return (
        _load_json(templates / "view_selection_policy.json"),
        _load_json(templates / "semantic_view_lens_registry.json"),
    )


def _registered_view_ids(registry: dict) -> set[str]:
    ids = {
        item.get("id")
        for item in registry.get("shared_view_families", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    for key in ("eco_specialised_views", "romer_specialised_views", "emassc_ls_specialised_views"):
        ids.update(value for value in registry.get(key, []) if isinstance(value, str))
    return ids


def _normalized_string_list(value: Any, *, field: str, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list):
        raise CGXViewPolicyError(f"{field} must be an explicit list")
    normalized = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise CGXViewPolicyError(f"{field} contains an invalid value")
        item = item.strip()
        if item not in normalized:
            normalized.append(item)
    if not normalized and not allow_empty:
        raise CGXViewPolicyError(f"{field} must not be empty")
    return normalized


def _stable_lens_id(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return "lens-" + hashlib.sha256(encoded).hexdigest()[:20]


def select_view_projection(
    *,
    policy: dict,
    registry: dict,
    security_and_admission: dict,
    task_intent: str,
    active_object_domain_and_type: str,
    work_mode: str,
    device_hydration_capability: str,
    role_or_audience: str,
    source_root_binding: str,
    selected_subgraph: list[str] | None = None,
    saved_profile_preferences: dict | None = None,
    session_override: dict | None = None,
    z_depth: int | str | None = None,
    filters: dict | None = None,
    units: str | dict | None = None,
    layout: str | dict | None = None,
    interaction_capabilities: list[str] | None = None,
) -> dict:
    """Return one deterministic, policy-constrained CGX projection.

    Security/admission is authoritative. Preferences can only select among
    views already admitted for the same object/source scope; they never alter
    evidence ceiling, semantic content, authority, or canonical state.
    """

    if policy.get("schema") != "CGX-VIEW-SELECTION-POLICY/0.1":
        raise CGXViewPolicyError("unsupported CGX view-selection policy schema")
    if policy.get("output", {}).get("canonical_mutation") is not False:
        raise CGXViewPolicyError("view policy permits canonical mutation")
    priority = policy.get("inputs_in_priority_order") or []
    if not priority or priority[0] != "security_and_admission":
        raise CGXViewPolicyError("security_and_admission is not the first policy input")

    if not isinstance(security_and_admission, dict) or security_and_admission.get("admitted") is not True:
        raise CGXViewPolicyError("security/admission lease is not admitted")

    security_scope = security_and_admission.get("security_scope")
    evidence_ceiling = security_and_admission.get("evidence_ceiling")
    if security_scope in (None, "", {}):
        raise CGXViewPolicyError("security_scope is required")
    if evidence_ceiling in (None, "", {}):
        raise CGXViewPolicyError("evidence_ceiling is required")

    registered = _registered_view_ids(registry)
    allowed_views = _normalized_string_list(
        security_and_admission.get("allowed_views"), field="security_and_admission.allowed_views"
    )
    unknown_allowed = sorted(set(allowed_views) - registered)
    if unknown_allowed:
        raise CGXViewPolicyError(f"admission lease references unknown views: {unknown_allowed}")

    allowed_objects = _normalized_string_list(
        security_and_admission.get("allowed_object_ids"),
        field="security_and_admission.allowed_object_ids",
    )
    allowed_roots = _normalized_string_list(
        security_and_admission.get("allowed_source_roots"),
        field="security_and_admission.allowed_source_roots",
    )
    if not isinstance(source_root_binding, str) or not source_root_binding.strip():
        raise CGXViewPolicyError("source_root_binding is required")
    source_root_binding = source_root_binding.strip()
    if source_root_binding not in allowed_roots:
        raise CGXViewPolicyError("source_root_binding is outside admission lease")

    if selected_subgraph is None:
        selected = list(allowed_objects)
    else:
        selected = _normalized_string_list(selected_subgraph, field="selected_subgraph")
        unauthorized = sorted(set(selected) - set(allowed_objects))
        if unauthorized:
            raise CGXViewPolicyError(f"selected_subgraph exceeds admission lease: {unauthorized}")

    task_mapping = policy.get("task_mapping") or {}
    mapped_views = task_mapping.get(task_intent)
    if not isinstance(mapped_views, list) or not mapped_views:
        raise CGXViewPolicyError(f"unsupported task_intent: {task_intent}")
    unknown_mapped = sorted({view for view in mapped_views if view not in registered})
    if unknown_mapped:
        raise CGXViewPolicyError(f"task mapping references unknown views: {unknown_mapped}")

    candidates = [view for view in mapped_views if view in allowed_views]
    if not candidates:
        raise CGXViewPolicyError("no admitted view satisfies task intent")

    preferences = saved_profile_preferences if isinstance(saved_profile_preferences, dict) else {}
    session = session_override if isinstance(session_override, dict) else {}
    preferred = preferences.get("primary_view")
    session_preferred = session.get("primary_view")

    primary_view = candidates[0]
    preference_rejections: list[str] = []
    if isinstance(preferred, str) and preferred:
        if preferred in candidates:
            primary_view = preferred
        else:
            preference_rejections.append("saved_profile_preferences.primary_view")
    elif isinstance(session_preferred, str) and session_preferred:
        if session_preferred in candidates:
            primary_view = session_preferred
        else:
            preference_rejections.append("session_override.primary_view")

    if preferred and session_preferred and preferred != session_preferred:
        preference_rejections.append("session_override.primary_view_lower_priority_than_saved_profile")

    hydration = str(device_hydration_capability or "").strip()
    if hydration not in _HYDRATION_SECONDARY_LIMITS:
        raise CGXViewPolicyError(f"unsupported device hydration profile: {hydration}")
    secondary = [view for view in candidates if view != primary_view]
    limit = _HYDRATION_SECONDARY_LIMITS[hydration]
    if limit is not None:
        secondary = secondary[:limit]

    requested_secondary = session.get("secondary_views") or preferences.get("secondary_views")
    if requested_secondary:
        requested_secondary = _normalized_string_list(
            requested_secondary, field="preferred secondary_views", allow_empty=True
        )
        authorized_requested = [
            view for view in requested_secondary
            if view in candidates and view != primary_view and view in secondary
        ]
        unauthorized_requested = [view for view in requested_secondary if view not in authorized_requested]
        if unauthorized_requested:
            preference_rejections.append("preferred secondary_views outside policy/hydration")
        if authorized_requested:
            remainder = [view for view in secondary if view not in authorized_requested]
            secondary = authorized_requested + remainder
            if limit is not None:
                secondary = secondary[:limit]

    lens_seed = {
        "task_intent": task_intent,
        "domain_type": active_object_domain_and_type,
        "work_mode": work_mode,
        "role": role_or_audience,
        "primary_view": primary_view,
        "secondary_views": secondary,
        "selected_subgraph": selected,
        "security_scope": security_scope,
        "evidence_ceiling": evidence_ceiling,
        "hydration_profile": hydration,
        "source_root_binding": source_root_binding,
    }

    return {
        "lens_id": _stable_lens_id(lens_seed),
        "primary_view": primary_view,
        "secondary_views": secondary,
        "selected_subgraph": selected,
        "z_depth": z_depth,
        "filters": dict(filters or {}),
        "units": units,
        "layout": layout,
        "interaction_capabilities": list(interaction_capabilities or []),
        "evidence_ceiling": evidence_ceiling,
        "security_scope": security_scope,
        "hydration_profile": hydration,
        "source_root_binding": source_root_binding,
        "canonical_mutation": False,
        "policy_schema": policy.get("schema"),
        "policy_status": policy.get("status"),
        "preference_rejections": preference_rejections,
    }


def select_runtime_view_projection(runtime_root: Path | str, **kwargs: Any) -> dict:
    policy, registry = load_runtime_view_contracts(runtime_root)
    return select_view_projection(policy=policy, registry=registry, **kwargs)
