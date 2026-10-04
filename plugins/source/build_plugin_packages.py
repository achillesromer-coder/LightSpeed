from __future__ import annotations

"""Build thin selector plugin packages from the shared CGX skill source.

Packages remain selector surfaces over the existing Cognigrex/LightSpeed runtime.
Capability profiles expose real current routes and shortcalls without inventing
an MCP endpoint or duplicating the runtime.
"""

import json
from pathlib import Path
import shutil
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "plugins" / "source"
PACKAGES = ROOT / "plugins" / "packages"
SELECTORS = ROOT / "cgx" / "domain_templates" / "plugin_selector_registry.json"
CAPABILITY_ROUTES = ROOT / "cgx" / "domain_templates" / "plugin_capability_routes.json"
SHORTCALLS = SOURCE / "selector_shortcalls.json"
CONFIG = SOURCE / "selector_packages.json"
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"



def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object: {path}")
    return payload


def copy_skill(name: str, destination: Path) -> None:
    candidates = [
        SOURCE / "core-skills" / name,
        SOURCE / "agent-skills" / name,
        SOURCE / "domain-skills" / name,
    ]
    source = next((path for path in candidates if path.exists()), None)
    if source is None:
        raise FileNotFoundError(f"shared skill not found: {name}")
    shutil.copytree(source, destination / name)


def plugin_description(display: str) -> str:
    return (
        f"Select {display} as a thin Cognigrex routing surface. Resolve the "
        "current CGX context, capability route, minimum sufficient work, and "
        "existing LightSpeed/connector execution path without creating a "
        "second runtime or authority."
    )


def expand_route_ids(route_ids: set[str], routes: dict[str, Any]) -> set[str]:
    resolved: set[str] = set()
    pending = list(route_ids)
    while pending:
        route_id = pending.pop()
        if route_id in resolved:
            continue
        if route_id not in routes:
            raise ValueError(f"capability dependency missing: {route_id}")
        resolved.add(route_id)
        pending.extend(str(item) for item in (routes[route_id].get("uses") or []))
    return resolved


def build_capability_payload(
    package_name: str,
    selector_name: str,
    *,
    capability_routes: dict[str, Any],
    shortcalls: dict[str, Any],
) -> dict[str, Any]:
    profile = (shortcalls.get("selectors") or {}).get(selector_name)
    if not isinstance(profile, dict):
        raise ValueError(f"shortcall profile missing: {selector_name}")
    global_calls = dict(shortcalls.get("global") or {})
    selector_calls = dict(profile.get("shortcalls") or {})
    direct_ids = set(global_calls.values()) | set(selector_calls.values())
    routes = capability_routes.get("routes") or {}
    missing = sorted(route_id for route_id in direct_ids if route_id not in routes)
    if missing:
        raise ValueError(
            f"capability routes missing for {selector_name}: {', '.join(missing)}"
        )
    route_ids = expand_route_ids(direct_ids, routes)
    return {
        "schema": "CGX-PLUGIN-CAPABILITY-PROFILE/0.1",
        "package": package_name,
        "selector": selector_name,
        "syntax": shortcalls.get("syntax"),
        "global_shortcalls": global_calls,
        "profile": profile,
        "routes": {route_id: routes[route_id] for route_id in sorted(route_ids)},
        "gaps": capability_routes.get("gaps") or [],
        "extension": capability_routes.get("extension") or {},
        "toolkit_registry": capability_routes.get("toolkit_registry"),
        "shared_tool_plane": capability_routes.get("shared_tool_plane") or {},
        "authority_note": (
            "Capability and toolkit bindings do not create authority. Resolve "
            "live CGX/Recovery state through cgx-handshake before execution."
        ),
    }


def build_package(
    package_name: str,
    profile: dict[str, Any],
    *,
    config: dict[str, Any],
    selectors: dict[str, Any],
    capability_routes: dict[str, Any],
    shortcalls: dict[str, Any],
    shared_skills: list[str],
) -> Path:
    selector_name = str(profile["selector"])
    selector = (selectors.get("selectors") or {}).get(selector_name)
    if not isinstance(selector, dict):
        raise ValueError(f"selector missing from canonical registry: {selector_name}")

    destination = PACKAGES / package_name
    if destination.exists():
        shutil.rmtree(destination)
    (destination / "skills").mkdir(parents=True)
    (destination / "references").mkdir(parents=True)
    (destination / ".codex-plugin").mkdir(parents=True)

    for skill in shared_skills:
        copy_skill(skill, destination / "skills")

    display = str(profile.get("display") or package_name)
    description = plugin_description(display)
    selector_payload = {
        "schema": "CGX-PLUGIN-SELECTOR-PROFILE/0.3",
        "package": package_name,
        "display": display,
        "selector": selector_name,
        "profile": selector,
        "source_registry": "cgx/domain_templates/plugin_selector_registry.json",
        "authority_note": (
            "This profile is a routing default only. Resolve live CGX authority "
            "and current Recovery state through cgx-handshake."
        ),
    }
    selector_text = json.dumps(selector_payload, indent=2, ensure_ascii=False) + "\n"
    (destination / "references" / "selector.json").write_text(
        selector_text, encoding="utf-8"
    )
    selector_ref = destination / "skills" / "cgx-selector" / "references"
    selector_ref.mkdir(parents=True, exist_ok=True)
    (selector_ref / "selector.json").write_text(selector_text, encoding="utf-8")

    capability_payload = build_capability_payload(
        package_name,
        selector_name,
        capability_routes=capability_routes,
        shortcalls=shortcalls,
    )
    capability_text = json.dumps(
        capability_payload, indent=2, ensure_ascii=False
    ) + "\n"
    (destination / "references" / "capabilities.json").write_text(
        capability_text, encoding="utf-8"
    )
    for skill_name in ("cgx-capability-router", "cgx-tool-extension"):
        skill_ref = destination / "skills" / skill_name / "references"
        skill_ref.mkdir(parents=True, exist_ok=True)
        (skill_ref / "capabilities.json").write_text(
            capability_text, encoding="utf-8"
        )

    version = str(config.get("version") or "0.3.0")
    author = dict(config.get("author") or {"name": "Römer Industries"})
    repository = str(config.get("repository") or "")
    category = str(config.get("category") or "Developer Tools")
    short = str(profile.get("short") or "Resolve Cognigrex context")[:30]
    capabilities = [str(x) for x in profile.get("capabilities") or []]
    interface = {
        "displayName": display,
        "shortDescription": short,
        "longDescription": description,
        "developerName": str(author.get("name") or "Römer Industries"),
        "category": category,
        "capabilities": capabilities,
    }
    portable = {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": package_name,
        "version": version,
        "description": description,
        "author": author,
        "repository": repository,
        "keywords": ["cognigrex", "lightspeed", "cgx", "selector"],
        "extensions": {"com.openai": {"interface": interface}},
    }
    compat = {
        "name": package_name,
        "version": version,
        "description": description,
        "author": author,
        "repository": repository,
        "keywords": ["cognigrex", "lightspeed", "cgx", "selector"],
        "skills": "./skills/",
        "interface": interface,
    }
    (destination / "plugin.json").write_text(
        json.dumps(portable, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (destination / ".codex-plugin" / "plugin.json").write_text(
        json.dumps(compat, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return destination


def build_marketplace(config: dict[str, Any]) -> Path:
    plugins = []
    for name, profile in (config.get("packages") or {}).items():
        plugins.append(
            {
                "name": str(name),
                "source": {
                    "source": "local",
                    "path": f"./plugins/packages/{name}",
                },
                "policy": {
                    "installation": "INSTALLED_BY_DEFAULT",
                    "authentication": "ON_INSTALL",
                },
                "category": str(config.get("category") or "Developer Tools"),
                "interface": {
                    "displayName": str(profile.get("display") or name)
                },
            }
        )
    payload = {
        "name": "cognigrex-lightspeed",
        "interface": {"displayName": "Cognigrex / LightSpeed"},
        "plugins": plugins,
    }
    MARKETPLACE.parent.mkdir(parents=True, exist_ok=True)
    MARKETPLACE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return MARKETPLACE


def main() -> int:
    config = read_json(CONFIG)
    selectors = read_json(SELECTORS)
    capability_routes = read_json(CAPABILITY_ROUTES)
    shortcalls = read_json(SHORTCALLS)
    packages = config.get("packages") or {}
    shared = [str(item) for item in config.get("shared_skills") or []]
    built = []
    for name, profile in packages.items():
        if not isinstance(profile, dict):
            raise ValueError(f"invalid package profile: {name}")
        built.append(
            str(
                build_package(
                    str(name),
                    profile,
                    config=config,
                    selectors=selectors,
                    capability_routes=capability_routes,
                    shortcalls=shortcalls,
                    shared_skills=shared,
                )
            )
        )
    marketplace = build_marketplace(config)
    print(
        json.dumps(
            {
                "built": built,
                "marketplace": str(marketplace),
                "mcp_emitted": False,
                "shared_skill_count": len(shared),
                "capability_route_count": len(capability_routes.get("routes") or {}),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
