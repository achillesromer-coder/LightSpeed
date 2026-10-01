from __future__ import annotations

"""Build thin selector plugin packages from the shared CGX skill source.

The builder intentionally does not invent or deploy an MCP endpoint. When a
verified MCP config is supplied later it can be copied into packages as a
separate controlled step.
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


def build_package(
    package_name: str,
    profile: dict[str, Any],
    *,
    version: str,
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

    selector_payload = {
        "schema": "CGX-PLUGIN-SELECTOR-PROFILE/0.1",
        "package": package_name,
        "display": profile.get("display") or package_name,
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
    # Keep the selector reference beside the selector skill because plugin skill
    # resources must remain package-local.
    selector_ref = destination / "skills" / "cgx-selector" / "references"
    selector_ref.mkdir(parents=True, exist_ok=True)
    (selector_ref / "selector.json").write_text(selector_text, encoding="utf-8")

    description = (
        f"Select {profile.get('display') or package_name} as a thin Cognigrex "
        "routing surface; resolve current CGX context and use existing "
        "LightSpeed/connector execution paths without creating a second runtime."
    )
    portable = {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": package_name,
        "version": version,
        "description": description,
        "skills": "./skills/",
        "repository": "https://github.com/achillesromer-coder/LightSpeed",
        "keywords": ["cognigrex", "lightspeed", "cgx", "selector"],
    }
    compat = {
        "name": package_name,
        "version": version,
        "description": description,
        "skills": "./skills/",
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


def main() -> int:
    config = read_json(CONFIG)
    selectors = read_json(SELECTORS)
    packages = config.get("packages") or {}
    shared = [str(item) for item in config.get("shared_skills") or []]
    version = str(config.get("version") or "0.1.0")
    built = []
    for name, profile in packages.items():
        if not isinstance(profile, dict):
            raise ValueError(f"invalid package profile: {name}")
        built.append(
            str(
                build_package(
                    str(name),
                    profile,
                    version=version,
                    selectors=selectors,
                    shared_skills=shared,
                )
            )
        )
    print(json.dumps({"built": built, "mcp_emitted": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
