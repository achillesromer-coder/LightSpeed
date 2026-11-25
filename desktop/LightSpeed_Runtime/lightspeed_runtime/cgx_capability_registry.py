from __future__ import annotations

"""Resolve CGX selector shortcalls against the canonical capability registries."""

from copy import deepcopy
import json
from pathlib import Path
import re
import unicodedata
from typing import Any

from lightspeed_runtime.cgx_catalogue_root import resolve_cgx_catalogue_root

REPO_ROOT = resolve_cgx_catalogue_root(Path(__file__))
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



def _capability_review_snapshot(selector: str) -> tuple[dict, dict]:
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
        if not path.resolve().is_relative_to(REPO_ROOT.resolve()):
            raise CapabilityRegistryError("interop source outside repository")
        with path.open("rb") as stream:
            raw=stream.read(1024*1024+1)
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
    # Reference the existing floor manifests; do not turn role metadata into a grant.
    floor_dirs={"Architect":"Z+1_Architect","Neo":"Z+2_Neo","Trinity":"Z+3_Trinity",
                "Morpheus":"Z-1_Morpheus","Oracle":"Z-2_Oracle","Smith":"Z-3_Smith",
                "Merovingian":"Z-4_Merovingian","TheConstruct":"Z0_TheConstruct"}
    mandatory={"dry_run_first","one_active_floor","one_ollama_session","no_secret_values",
               "no_destructive_moves","no_drive_mutation","no_public_route_mutation",
               "no_main_merge","no_heavy_runner_without_gate"}
    role_source_holds=[]
    for floor in profile.get("floors") or []:
        if floor not in floor_dirs:
            role_source_holds.append(floor)
            continue
        path=REPO_ROOT/"docs/agent-ingestion/local-agent-homes"/floor_dirs[floor]/"agent_manifest.json"
        if not path.is_file():
            role_source_holds.append(floor)
            continue
        data=read_source(path)
        manifest=json.loads(data)
        gates=manifest.get("gates")
        function=manifest.get("function")
        if (manifest.get("lightspeed_floor")!=floor or manifest.get("lightspeed_agent_id")!=floor.lower()
                or type(gates) is not list or len(gates)>64
                or not all(type(g) is str and 0<len(g)<=128 for g in gates)
                or not mandatory.issubset(gates)
                or type(function) is not str or not 0<len(function)<=512):
            raise CapabilityRegistryError("specialist source identity or gates changed")
        add("role:"+floor.lower(),{"role_id":floor.lower(),"floor":floor,
            "responsibility":function,"standing_gates":sorted(set(gates)),
            "source_path":path.relative_to(REPO_ROOT).as_posix(),"source_sha256":digest(data),
            "source_bytes":len(data),"execution_authorized":False,
            "authority_transfer":False,"live_skill_learning_verified":False})
    if profile["selector"]=="achilles":
        path=REPO_ROOT/"cgx/domain_templates/achilles_owner_operator_profile.json"
        data=read_source(path)
        owner=json.loads(data)
        if (owner.get("identity",{}).get("agent")!="Achilles"
                or owner.get("authority",{}).get("agent_can_self_approve") is not False
                or owner.get("authority",{}).get("default_execution_class")!="READ_ONLY"
                or owner.get("lifecycle",{}).get("native_dbr_admission") is not False
                or owner.get("lifecycle",{}).get("release_authorized") is not False):
            raise CapabilityRegistryError("Achilles role authority hold")
        add("role:achilles",{"role_id":"achilles","floor":"Achilles",
            "responsibility":"Owner/operator review profile",
            "standing_gates":["read_only","no_self_approval","native_admission_hold","release_hold"],
            "source_path":path.relative_to(REPO_ROOT).as_posix(),"source_sha256":digest(data),
            "source_bytes":len(data),"execution_authorized":False,
            "authority_transfer":False,"live_skill_learning_verified":False})
    # Domain and system references are not aliases for the corresponding
    # resident agent's identity. Retain the unresolved authority distinction.
    scoped_candidates={
        "athene":("athene","cgx/domain_templates/agent_assurance_role_matrix.json"),
        "raphael":("raphael","plugins/source/selector_shortcalls.json"),
        "romer-grex":("romer","cgx/domain_templates/agent_role_reconciliation.md"),
        "cognigrex":("load","plugins/source/selector_shortcalls.json"),
        "lightspeed":("unispace","UniSpace/product.json"),
    }
    if profile["selector"] in scoped_candidates:
        rid,rel=scoped_candidates[profile["selector"]]
        data=read_source(REPO_ROOT/rel)
        details={}
        if rid=="athene":
            matrix=json.loads(data)
            rows=[row for row in matrix["roles"] if row.get("agent")=="Athene"]
            if len(rows)!=1 or not rows[0].get("assurance_role") or not rows[0].get("forbidden"):
                raise CapabilityRegistryError("Athene assurance mapping missing")
            details={"assurance_role":rows[0]["assurance_role"],"forbidden":rows[0]["forbidden"]}
            state="SOURCE_ROLE_MAPPED_RESIDENT_BINDING_HOLD"
        elif rid=="raphael":
            details={"selector_route_ids":sorted(profile["routes"])}
            state="PHYSICS_SELECTOR_RESIDENT_BINDING_HOLD"
        elif rid=="romer":
            state="DOMAIN_OWNERSHIP_RECONCILIATION_HOLD"
        elif rid=="load":
            state="RESOLVER_SURFACE_RESIDENT_IDENTITY_HOLD"
        else:
            product=json.loads(data)
            if product.get("product")!="UniSpace":
                raise CapabilityRegistryError("UniSpace source identity changed")
            details={"product":product["product"],"product_acceptance_verified":False}
            state="PRODUCT_SURFACE_RESIDENT_IDENTITY_HOLD"
        add("resident-review:"+rid,{"resident_role_candidate":rid,"qualification":state,
            "source_path":rel,"source_sha256":digest(data),"source_bytes":len(data),
            **details,"execution_authorized":False,"authority_transfer":False,
            "resident_binding_verified":False,"live_skill_learning_verified":False})
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
          "role_source_holds":sorted(role_source_holds),
          "provider_invocation_performed":False,"authority_transfer":False,
          "native_admitted":False}
    stamp=digest(canonical(view))
    return {**view,"view_sha256":stamp},values


def capability_interop_review(selector: str, *, reference: str | None = None,
                             expected_view_sha256: str | None = None) -> dict[str, Any]:
    view,values=_capability_review_snapshot(selector)
    stamp=view["view_sha256"]
    refs=view["references"]
    if reference is None:
        if expected_view_sha256 is not None:
            raise CapabilityRegistryError("view revision without reference")
        return view
    if type(reference) is not str or reference not in refs:
        raise CapabilityRegistryError("reference outside selector view")
    if expected_view_sha256!=stamp:
        raise CapabilityRegistryError("stale or missing selector view revision")
    return {"schema":"CGX-CAPABILITY-METADATA-REFERENCE/0.1","selector":view["selector"],
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
    view,_=_capability_review_snapshot(selector)
    return _compose_from_snapshot(view,task_id,expected_view_sha256,references)


def _compose_from_snapshot(view,task_id,expected_view_sha256,references):
    import hashlib
    from lightspeed_runtime.cgx_cross_analysis import pack_nested_review_payload
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



def hydrate_composed_skill_review(selector: str, *, task_id: str, composition: dict,
                                  expected_composition_sha256: str,
                                  selected_skills: list[str], scope_revision: str,
                                  max_bytes: int, authorise) -> tuple[dict[str, bytes],dict]:
    """Return exact selected shared skill bytes, not native state or execution.

    Caller authenticates the expected composition and live authorisation.
    Registry metadata discovery still hashes all shared skill sources; only
    selected skill payloads are returned. Role manifests are never hydrated.
    """
    import hashlib
    from lightspeed_runtime.cgx_cross_analysis import pack_nested_review_payload
    if (type(task_id) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}",task_id)
            or type(scope_revision) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}",scope_revision)
            or type(max_bytes) is not int or not 1<=max_bytes<=1024*1024
            or type(selected_skills) is not list or not 1<=len(selected_skills)<=64
            or any(type(k) is not str or not re.fullmatch(r"skill:[a-z0-9][a-z0-9_-]{0,127}",k) for k in selected_skills)
            or len(set(selected_skills))!=len(selected_skills)
            or type(expected_composition_sha256) is not str
            or not re.fullmatch(r"[a-f0-9]{64}",expected_composition_sha256)):
        raise CapabilityRegistryError("invalid selected skill request")
    # Validate bounded shape before comparing any external composition.
    fields={"schema","task_id","selector","view_sha256","references","provider_invocation_performed",
            "execution_authorized","authority_transfer","native_admitted",
            "composition_sha256","composition_ternary_root"}
    if (type(composition) is not dict or set(composition)!=fields
            or type(composition["references"]) is not dict
            or not 1<=len(composition["references"])<=64
            or any(type(k) is not str or not 1<=len(k)<=256 for k in composition["references"])
            or composition["task_id"]!=task_id
            or composition["composition_sha256"]!=expected_composition_sha256
            or not set(selected_skills).issubset(composition["references"])):
        raise CapabilityRegistryError("composition binding mismatch")
    for key,v in composition.items():
        if key=="references":continue
        if type(v) not in (str,bool) or (type(v) is str and len(v)>256):
            raise CapabilityRegistryError("composition scalar shape")
    for ref in composition["references"].values():
        if (type(ref) is not dict or set(ref)!={"sha256","ternary_root","bytes"}
                or any(type(ref[k]) is not str or not re.fullmatch(r"[a-f0-9]{64}",ref[k])
                       for k in ("sha256","ternary_root"))
                or type(ref["bytes"]) is not int or not 0<=ref["bytes"]<=1024*1024):
            raise CapabilityRegistryError("composition reference shape")
    keys=sorted(selected_skills)
    def check(key):
        if authorise(task_id,key,scope_revision,expected_composition_sha256) is not True:
            raise PermissionError("skill scope denied or revoked")
    for key in keys:check(key)
    view,values=_capability_review_snapshot(selector)
    rebuilt=_compose_from_snapshot(view,task_id,composition["view_sha256"],
                                  list(composition["references"]))
    if rebuilt!=composition or rebuilt["composition_sha256"]!=expected_composition_sha256:
        raise CapabilityRegistryError("composition revision changed")
    resolved={}
    evidence={}
    remaining=max_bytes
    if sum(values[k]["source_bytes"] for k in keys)>max_bytes:
        raise CapabilityRegistryError("skill payload byte budget")
    for key in keys:
        check(key)
        meta=values[key]
        size=meta["source_bytes"]
        if type(size) is not int or not 0<size<=remaining:
            raise CapabilityRegistryError("skill payload byte budget")
        path=REPO_ROOT/"plugins/source/core-skills"/key.split(":",1)[1]/"SKILL.md"
        if (path.relative_to(REPO_ROOT).as_posix()!=meta["source_path"]
                or not path.resolve().is_relative_to(REPO_ROOT.resolve())):
            raise CapabilityRegistryError("skill locator mismatch")
        with path.open("rb") as stream:
            raw=stream.read(size+1)
        digest=hashlib.sha256(raw).hexdigest()
        if len(raw)!=size or digest!=meta["source_sha256"]:
            raise CapabilityRegistryError("skill source revision changed")
        check(key)
        root,_=pack_nested_review_payload(raw)
        resolved[key]=raw
        evidence[key]={"source_sha256":digest,"bytes":size,"payload_ternary_root":root}
        remaining-=size
    for key in keys:check(key)
    receipt={"schema":"CGX-COMPOSED-SKILL-REVIEW/0.1","task_id":task_id,
             "selector":rebuilt["selector"],"composition_sha256":expected_composition_sha256,
             "scope_revision":scope_revision,"skills":evidence,"payload_bytes":max_bytes-remaining,
             "caller_scope_authenticated_by_module":False,"execution_authorized":False,
             "authority_transfer":False,"live_skill_learning_verified":False,"native_admitted":False}
    encoded=json.dumps(receipt,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")
    receipt["review_sha256"]=hashlib.sha256(encoded).hexdigest()
    return resolved,receipt
