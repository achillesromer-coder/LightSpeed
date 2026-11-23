"""Source-only CGX agent/model capability projection over the existing UniSpace root.

This does not create an agent, connect a model, hydrate private memory, modify
weights, grant provider authority, or create another capability registry.
Canonical source: existing domains, runtime contract, technology stack, route
catalogue, nine plugin selector profiles, and the original five-facet mesh.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from tools.cgx_unispace_facet_mesh import FACETS, ROOT_ID, build_unispace_facet_mesh

SCHEMA = "CGX-UNISPACE-AGENT-MODEL-SOURCE-PROJECTION/0.1"
SELECTORS = (
    "achilles", "neo", "athene", "raphael", "cognigrex",
    "romer-grex", "eco-grex", "emassc", "lightspeed",
)
ROOT = "Cognigrex.cgx"
MAX_BYTES = 256_000
MAIN_CONTRACTS = {
    "domains": "cgx/domain_templates/domains.json",
    "agent_runtime": "cgx/domain_templates/agent_runtime_contract.json",
    "technology_stack": "cgx/domain_templates/technology_stack_registry.json",
    "capability_routes": "cgx/domain_templates/plugin_capability_routes.json",
    "selector_shortcalls": "plugins/source/selector_shortcalls.json",
}
MODEL_CLASSES = {
    "remote_llm", "local_llm", "specialist_model",
    "classical_solver", "no_model_deterministic",
}
ROUTE_STATES = {
    "available", "workflow", "gated", "assisted",
    "registered_unwrapped", "missing",
}


class AgentModelHold(ValueError):
    """Unqualified existing source or an attempted authority escalation."""


def _tracked(repo: Path) -> set[str]:
    done = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "-z"],
        capture_output=True, check=False, timeout=20,
    )
    if done.returncode != 0:
        raise AgentModelHold("original Git source index unavailable")
    return {p.decode("utf-8") for p in done.stdout.split(b"\0") if p}


def _source(repo: Path, rel: str, tracked: set[str]) -> tuple[dict, dict]:
    if (rel not in tracked or rel.startswith("/") or ".." in rel.split("/")
            or "\\" in rel or not (rel.startswith("cgx/domain_templates/")
            or rel.startswith("plugins/source/")
            or rel.startswith("plugins/packages/"))):
        raise AgentModelHold("unqualified reference: " + rel)
    path = repo / rel
    if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(repo):
        raise AgentModelHold("missing or redirected original source: " + rel)
    raw = path.read_bytes()
    if not 0 < len(raw) <= MAX_BYTES:
        raise AgentModelHold("unbounded or empty original source: " + rel)
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise AgentModelHold("invalid original source root: " + rel)
    return obj, {"path": rel, "sha256": hashlib.sha256(raw).hexdigest(),
                 "bytes": len(raw), "source_only": True}


def build(repo: Path, *, tracked: set[str] | None = None) -> dict[str, Any]:
    repo = Path(repo).resolve(strict=True)
    index = _tracked(repo) if tracked is None else set(tracked)
    mesh = build_unispace_facet_mesh(repo, index)
    if (mesh.get("state") != "SOURCE_CONTRACT_MESH_OBSERVED"
            or mesh.get("canonical_root_id") != ROOT_ID
            or mesh.get("facet_count") != 5
            or {f.get("id") for f in mesh.get("facets", [])} != set(FACETS)):
        raise AgentModelHold("existing parent five-facet source mesh not qualified")

    contracts = {}
    provenance = {}
    for key, rel in MAIN_CONTRACTS.items():
        contracts[key], provenance[key] = _source(repo, rel, index)
    domains = contracts["domains"]
    runtime = contracts["agent_runtime"]
    tech = contracts["technology_stack"]
    routes = contracts["capability_routes"]
    shortcalls = contracts["selector_shortcalls"]

    if (domains.get("parent_filespace", {}).get("file") != ROOT
            or domains.get("schema") != "CGX-DOMAIN-TEMPLATES/0.4"
            or runtime.get("schema") != "CGX-AGENT-RUNTIME-CONTRACT/0.1"
            or "model-is-capability-not-agent-identity" not in runtime.get("invariants", [])
            or "prompt-is-not-canon" not in runtime.get("invariants", [])
            or runtime.get("execution_lease", {}).get("default_on_missing") != "NO_EXECUTION"):
        raise AgentModelHold("canonical source/agent identity or authority contract mismatch")
    model_binding = runtime.get("model_binding")
    allowed = model_binding.get("allowed") if isinstance(model_binding, dict) else None
    if not isinstance(allowed, list) or set(allowed) != MODEL_CLASSES or len(allowed) != len(MODEL_CLASSES):
        raise AgentModelHold("model classes not bound to canonical agent runtime")
    layers = {layer.get("id"): layer for layer in tech.get("layers", [])
              if isinstance(layer, dict)}
    if set(("L04", "L09", "L10", "L13", "L14")) - set(layers):
        raise AgentModelHold("source technology-stack model/agent/safety layers unavailable")
    if (layers["L09"].get("name") != "Agent Runtime"
            or layers["L10"].get("name") != "Model / Reasoning Capabilities"):
        raise AgentModelHold("model/agent layer identities disagree")

    declared = shortcalls.get("selectors")
    canonical_routes = routes.get("routes")
    if (not isinstance(declared, dict) or set(declared) != set(SELECTORS)
            or not isinstance(canonical_routes, dict)
            or not canonical_routes):
        raise AgentModelHold("original nine-selector/route source unavailable")
    domain_map = domains.get("domains")
    if not isinstance(domain_map, dict) or set(domain_map) != {"romer", "eco", "emassc"}:
        raise AgentModelHold("existing domain families not qualified")
    owned_roles = {}
    for key, entry in domain_map.items():
        if not isinstance(entry, dict):
            raise AgentModelHold("invalid domain owner")
        owner = entry.get("principal_agent")
        if owner not in {"Achilles", "Neo", "Athene"} or owner in owned_roles:
            raise AgentModelHold("ambiguous principal agent ownership")
        owned_roles[owner.lower()] = {
            "domain": key,
            "canonical_filespace": entry["file"],
            "role_origin": "EXISTING_DOMAIN_PRINCIPAL_AGENT",
        }
    if set(owned_roles) != {"achilles", "neo", "athene"}:
        raise AgentModelHold("original three principal agent roles changed")
    global_calls = shortcalls.get("global")
    if not isinstance(global_calls, dict) or not global_calls:
        raise AgentModelHold("global source shortcalls unavailable")

    selectors = []
    frontier = []
    for selector in SELECTORS:
        rel = f"plugins/packages/{selector}/references/capabilities.json"
        package, proof = _source(repo, rel, index)
        provenance[selector] = proof
        if (package.get("schema") != "CGX-PLUGIN-CAPABILITY-PROFILE/0.1"
                or package.get("package") != selector
                or package.get("selector") != selector):
            raise AgentModelHold("selector source identity mismatch: " + selector)
        profile = declared[selector]
        if not isinstance(profile, dict) or not isinstance(profile.get("shortcalls"), dict):
            raise AgentModelHold("invalid original selector shortcalls: " + selector)
        if package.get("profile", {}).get("shortcalls") != profile["shortcalls"]:
            raise AgentModelHold("stale selector-specific shortcalls: " + selector)
        if package.get("global_shortcalls") != global_calls:
            raise AgentModelHold("stale global shortcalls: " + selector)
        resolved = set(global_calls.values()) | set(profile["shortcalls"].values())
        if not resolved.issubset(canonical_routes):
            raise AgentModelHold("unregistered original route: " + selector)
        package_routes = package.get("routes")
        if not isinstance(package_routes, dict) or not resolved.issubset(package_routes):
            raise AgentModelHold("missing selector route expansion: " + selector)
        route_ids = sorted(package_routes)
        for route_id in route_ids:
            source_route = canonical_routes.get(route_id)
            package_route = package_routes[route_id]
            if (not isinstance(source_route, dict)
                    or not isinstance(package_route, dict)
                    or source_route.get("state") not in ROUTE_STATES
                    or package_route.get("state") not in ROUTE_STATES):
                raise AgentModelHold("unqualified route state: " + route_id)
            if package_route != source_route:
                frontier.append({"selector": selector, "route_id": route_id,
                                 "state": "SOURCE_VARIANCE_NEEDS_RECONCILIATION"})
        role = owned_roles.get(selector)
        selectors.append({
            "selector": selector,
            "kind": "EXISTING_PRINCIPAL_AGENT" if role else "EXISTING_SELECTOR_ONLY",
            "role": role,
            "route_count": len(route_ids),
            "shortcall_count": len(profile["shortcalls"]) + len(global_calls),
            "route_ids": route_ids,
            "plugin_source_sha256": proof["sha256"],
            "presentable_facets": sorted(FACETS),
            "facets_granted_by_projection": [],
            "provider_bound": False,
            "model_installed_verified": False,
            "model_context_hydrated": False,
            "native_executed": False,
        })
    result = {
        "schema": SCHEMA,
        "canonical_root_id": ROOT_ID,
        "state": "SOURCE_AGENT_MODEL_PROJECTION_ONLY",
        "source_refs": [provenance[k] for k in sorted(provenance)],
        "parent_facet_mesh_schema": mesh["schema"],
        "principal_agent_count": len(owned_roles),
        "selector_count": len(selectors),
        "selectors": selectors,
        "model_classes": sorted(MODEL_CLASSES),
        "model_classes_are_declared_not_live_models": True,
        "model_provider_selection_requires_live_scope": True,
        "independent_role_and_model_identity": True,
        "routing_frontier": frontier,
        "native_profile_handshake_verified": False,
        "native_dbr_authorized": False,
        "model_weights_changed": False,
        "model_training_executed": False,
        "private_memory_hydrated": False,
        "agent_spawned": False,
        "execution_or_publication_authorized": False,
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    result["source_projection_sha256"] = hashlib.sha256(canonical).hexdigest()
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(build(args.repo), sort_keys=True, indent=2))
