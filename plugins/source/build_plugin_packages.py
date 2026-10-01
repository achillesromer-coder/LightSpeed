from __future__ import annotations

"""Build thin selector plugin packages from the shared CGX skill source.

This builder produces skills-only selector packages plus the repo marketplace.
It deliberately does not invent or deploy an MCP endpoint. A verified MCP
transport can be added later without changing selector identity or authority.
"""

import json
from pathlib import Path
import shutil
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "plugins" / "source"
PACKAGES = ROOT / "plugins" / "packages"
SELECTORS = ROOT / "cgx" / "domain_templates" / "plugin_selector_registry.json"
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
        "current CGX context, minimum sufficient work, and existing LightSpeed/"
        "connector execution path without creating a second runtime or authority."
    )


def build_package(
    package_name: str,
    profile: dict[str, Any],
    *,
    config: dict[str, Any],
    selectors: dict[str, Any],
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
        "schema": "CGX-PLUGIN-SELECTOR-PROFILE/0.2",
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

    version = str(config.get("version") or "0.2.0")
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
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
