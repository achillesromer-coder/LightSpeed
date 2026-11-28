"""Locate one immutable installed snapshot of canonical CGX metadata.

Git checkout is the authoring source; installed Core/cgx_catalogue is the
read-only deployment snapshot, not a second mutable registry or live database.
No network or file writes occur during resolution.
"""
from __future__ import annotations

from pathlib import Path

REQUIRED = (
    "cgx/domain_templates/plugin_capability_routes.json",
    "plugins/source/selector_shortcalls.json",
)


def resolve_cgx_catalogue_root(module_file: Path) -> Path:
    module = Path(module_file).resolve()
    # Source: repo/desktop/LightSpeed_Runtime/lightspeed_runtime/module.py
    source = module.parents[3]
    # Installed: D:/LightSpeed/Core/lightspeed_runtime/module.py
    installed = module.parents[1] / "cgx_catalogue"
    for candidate in (source, installed):
        if all((candidate / name).is_file() for name in REQUIRED):
            return candidate
    # Do not fall back to arbitrary drives, stale Git or untrusted URLs.
    # An absent installed snapshot will make the registry fail closed upon read
    # without blocking import of the host health endpoint.
    return installed if module.parent.name == "lightspeed_runtime" and module.parents[1].name.lower() == "core" else source
