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



def capability_interop_review(selector: str, *, reference: str | None = None,
                             expected_view_sha256: str | None = None) -> dict[str, Any]:
    """Read-only shared catalogue projection; no provider invocation or authority.

    Stable symbolic IDs reference canonical metadata objects across selectors.
    Ternary roots use the existing transport primitive, not validated geometry.
    A reference read is bound to the current selector view and exact revision.
    """
    import hashlib
    from lightspeed_runtime.cgx_cross_analysis import pack_nested_review_payload

    def canonical(value):
        return json.dumps(value, sort_keys=True, separators=(",",":"),
                          ensure_ascii=True, allow_nan=False).encode("ascii")

    def digest(raw):
        return hashlib.sha256(raw).hexdigest()

    def read_source(path):
        raw = path.read_bytes()
        if not 1 <= len(raw) <= 1024 * 1024:
            raise CapabilityRegistryError("interop source size")
        return raw

    toolkit_path = REPO_ROOT / "cgx/domain_templates/toolkit_registry.json"
    config_path = REPO_ROOT / "plugins/source/selector_packages.json"
    paths = (DEFAULT_ROUTES_PATH, DEFAULT_SHORTCALLS_PATH, toolkit_path, config_path)
    raw = [read_source(path) for path in paths]
    route_registry, shortcalls, toolkit_registry, config = (json.loads(x) for x in raw)
    validate_capability_routes(route_registry)
    validate_selector_shortcalls(shortcalls, route_registry)
    profile = selector_profile(selector, routes=route_registry, shortcalls=shortcalls)
    toolkits = {}
    for item in toolkit_registry["toolkits"]:
        key = item["id"]
        if key in toolkits:
            raise CapabilityRegistryError("duplicate toolkit ID")
        # Do not propagate credential refs, executable paths or secret values.
        toolkits[key] = {k:item[k] for k in ("id","kind","binding","capabilities","state") if k in item}
    surfaces = toolkit_registry["interoperability_surfaces"]
    if any(r not in route_registry["routes"] for v in surfaces.values() for r in v["routes"]):
        raise CapabilityRegistryError("unknown surface route")
    if any(k not in toolkits for v in surfaces.values() for k in v["toolkits"]):
        raise CapabilityRegistryError("unknown surface toolkit")
    if len(surfaces)>64 or len(profile["routes"])>256 or len(toolkits)>128:
        raise CapabilityRegistryError("interop catalogue limit")

    values = {}
    refs = {}
    def add(key, val):
        if key in refs:
            raise CapabilityRegistryError("duplicate metadata reference")
        encoded=canonical(val)
        root,_=pack_nested_review_payload(encoded)
        refs[key]={"sha256":digest(encoded),"ternary_root":root,"bytes":len(encoded)}
        values[key]=val

    for rid, route in profile["routes"].items():
        add("route:"+rid, {"route_id":rid, **{k:route[k] for k in
            ("state","kind","ro","handler","uses","gate","limitation","authority_transfer") if k in route}})
    for key in profile.get("toolkits") or []:
        if key not in toolkits:
            raise CapabilityRegistryError("unknown selector toolkit")
        add("toolkit:"+key, toolkits[key])

    for name in config["shared_skills"]:
        if not isinstance(name,str) or not _SHORTCALL_RE.fullmatch(name):
            raise CapabilityRegistryError("invalid shared skill name")
        path=REPO_ROOT / "plugins/source/core-skills" / name / "SKILL.md"
        data=read_source(path)
        add("skill:"+name, {"skill_id":name,"source_path":path.relative_to(REPO_ROOT).as_posix(),
                           "source_sha256":digest(data),"source_bytes":len(data),
                           "execution_authorized":False})
    for key,surface in sorted(surfaces.items()):
        # Report missing selector exposure explicitly, never widen it.
        add("surface:"+key, {
            "surface_id":key,
            "route_refs":["route:"+r for r in surface["routes"] if "route:"+r in refs],
            "unexposed_routes":[r for r in surface["routes"] if "route:"+r not in refs],
            "toolkit_refs":["toolkit:"+k for k in surface["toolkits"] if "toolkit:"+k in refs],
            "unexposed_toolkits":[k for k in surface["toolkits"] if "toolkit:"+k not in refs],
            "provider_candidates":surface["provider_candidates"],
            "provider_binding":"UNVERIFIED_AT_RUNTIME",
            "boundary":surface["boundary"],
        })
    view={"schema":"CGX-CAPABILITY-INTEROP-REVIEW/0.1",
          "selector":profile["selector"],"floors":list(profile.get("floors") or []),
          "source_sha256":{p.relative_to(REPO_ROOT).as_posix():digest(b) for p,b in zip(paths,raw)},
          "references":dict(sorted(refs.items())),
          "provider_invocation_performed":False,"authority_transfer":False,
          "native_admitted":False}
    stamp=digest(canonical(view))
    if reference is None:
        if expected_view_sha256 is not None:
            raise CapabilityRegistryError("view revision without reference")
        return {**view,"view_sha256":stamp}
    if type(reference) is not str or reference not in refs:
        raise CapabilityRegistryError("reference outside selector view")
    if expected_view_sha256!=stamp:
        raise CapabilityRegistryError("stale or missing selector view revision")
    return {"schema":"CGX-CAPABILITY-METADATA-REFERENCE/0.1","selector":profile["selector"],
            "view_sha256":stamp,"reference":reference,"descriptor":refs[reference],
            "metadata":values[reference],"provider_invocation_performed":False,
            "execution_authorized":False,"authority_transfer":False,"native_admitted":False}



def compose_capability_review(selector: str, *, task_id: str, expected_view_sha256: str,
                              references: list[str]) -> dict[str, Any]:
    """One compact task-bound skill/tool manifest; reference-only, not execution."""
    import hashlib
    from lightspeed_runtime.cgx_cross_analysis import pack_nested_review_payload
    if type(task_id) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}",task_id):
        raise CapabilityRegistryError("invalid composition task ID")
    if (type(references) is not list or not 1<=len(references)<=64 or
            any(type(k) is not str or not 1<=len(k)<=256 for k in references) or
            len(set(references))!=len(references)):
        raise CapabilityRegistryError("invalid composition references")
    view=capability_interop_review(selector)
    if expected_view_sha256!=view["view_sha256"]:
        raise CapabilityRegistryError("stale composition view")
    if any(k not in view["references"] for k in references):
        raise CapabilityRegistryError("composition reference outside selector")
    payload={"schema":"CGX-CAPABILITY-COMPOSITION-REVIEW/0.1","task_id":task_id,
             "selector":view["selector"],"view_sha256":expected_view_sha256,
             "references":{k:view["references"][k] for k in sorted(references)},
             "provider_invocation_performed":False,"execution_authorized":False,
             "authority_transfer":False,"native_admitted":False}
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")
    root,_=pack_nested_review_payload(raw)
    return {**payload,"composition_sha256":hashlib.sha256(raw).hexdigest(),"composition_ternary_root":root}
