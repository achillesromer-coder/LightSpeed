"""
ComponentLinker - lightweight component discovery for LightSpeed.

This module exists to support `wizards/startup_wizard.py` and other runtime tooling
that expects a `ComponentLinker` with a `discover_all_components()` method.

Design goals:
- No external dependencies (stdlib only)
- Fast, best-effort discovery (never crash startup if a directory is missing)
- Return objects with a `component_type` attribute for summary counts

Floor-native layout (current workspace):
- Platform code is organized under `LightSpeed/Z Axis/<floor>/...`
- "Core" namespaces like `core.services.*` are provided by Z-4_Merovingian
- UI namespaces like `core.ui.*` are provided by Trinity (Z+3) and TheConstruct (Z0)
- Analysis namespaces like `core.analysis.*` are provided by Morpheus (Z-1)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class ComponentInfo:
    key: str
    name: str
    component_type: str
    path: str
    module: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ComponentLinker:
    """
    Discovers components across the LightSpeed workspace.

    The discovery output is intentionally conservative: it is used primarily for
    inventory and health reporting (not for dynamic imports).
    """

    def __init__(self, root: Optional[Path | str] = None):
        self.root = Path(root).resolve() if root else Path(__file__).parent.resolve()
        self.lightspeed_root = self.root
        if not (self.lightspeed_root / "Z Axis").exists():
            # If we were given the repo root, prefer its `LightSpeed/` child.
            candidate = self.root / "LightSpeed"
            if candidate.exists() and (candidate / "Z Axis").exists():
                self.lightspeed_root = candidate.resolve()

    def _iter_py_modules(self, folder: Path):
        if not folder.exists():
            return
        for py in folder.glob("*.py"):
            if py.name.startswith("_"):
                continue
            yield py

    def discover_all_components(self) -> Dict[str, ComponentInfo]:
        components: Dict[str, ComponentInfo] = {}

        # Z-floor manifests (authoritative for floors/components)
        z_axis = self.lightspeed_root / "Z Axis"
        if z_axis.exists():
            for manifest in z_axis.glob("*/_FLOOR_MANIFEST.json"):
                floor_id = manifest.parent.name
                components[f"floor:{floor_id}"] = ComponentInfo(
                    key=f"floor:{floor_id}",
                    name=floor_id,
                    component_type="floor",
                    path=str(manifest.parent),
                    module=None,
                    metadata={"manifest": str(manifest)},
                )
                try:
                    data = json.loads(manifest.read_text(encoding="utf-8"))
                    for comp in data.get("components", []):
                        comp_name = comp.get("name") or comp.get("id") or "component"
                        src = comp.get("source_file") or comp.get("source") or ""
                        comp_type = (comp.get("type") or "").lower() or "ui"
                        key = f"{floor_id}:{comp_name}"
                        if key in components:
                            continue
                        components[key] = ComponentInfo(
                            key=key,
                            name=str(comp_name),
                            component_type=comp_type if comp_type in {"ui", "service", "analyzer", "renderer", "simulator"} else "ui",
                            path=str((manifest.parent / src).resolve()) if src else str(manifest.parent),
                            module=comp.get("module"),
                            metadata={"floor": floor_id, "class": comp.get("class"), "source_file": src},
                        )
                except Exception:
                    # Best-effort: a malformed manifest shouldn't break discovery.
                    continue

        # Core services (Z-4_Merovingian provides `core.services.*`)
        for services_dir in [
            z_axis / "Z-4_Merovingian" / "core" / "services",
            z_axis / "core" / "services",  # legacy (if present)
            self.lightspeed_root / "core" / "services",  # legacy (if present)
        ]:
            for py in self._iter_py_modules(services_dir):
                key = f"service:{py.stem}"
                components.setdefault(
                    key,
                    ComponentInfo(
                        key=key,
                        name=py.stem,
                        component_type="service",
                        path=str(py),
                        module=f"core.services.{py.stem}",
                    ),
                )

        # Code analysis (Morpheus provides `core.analysis.*`)
        for analysis_dir in [
            z_axis / "Z-1_Morpheus" / "analysis",
            z_axis / "Z-4_Merovingian" / "core" / "analysis",  # shim package only
        ]:
            for py in self._iter_py_modules(analysis_dir):
                key = f"analyzer:{py.stem}"
                components.setdefault(
                    key,
                    ComponentInfo(
                        key=key,
                        name=py.stem,
                        component_type="analyzer",
                        path=str(py),
                        module=f"core.analysis.{py.stem}",
                    ),
                )

        # UI modules (Trinity + TheConstruct provide `core.ui.*`)
        for ui_dir in [
            z_axis / "Z+3_Trinity" / "ui",
            z_axis / "Z0_TheConstruct" / "ui",
            z_axis / "Z-4_Merovingian" / "core" / "ui",  # shim package
        ]:
            for py in self._iter_py_modules(ui_dir):
                key = f"ui:{py.stem}"
                components.setdefault(
                    key,
                    ComponentInfo(
                        key=key,
                        name=py.stem,
                        component_type="ui",
                        path=str(py),
                        module=f"core.ui.{py.stem}",
                    ),
                )

        # Wizards (Trinity owns wizards)
        for wiz_dir in [
            z_axis / "Z+3_Trinity" / "wizards",
            z_axis / "wizards",  # legacy (if present)
            self.lightspeed_root / "wizards",  # legacy (if present)
        ]:
            for py in self._iter_py_modules(wiz_dir):
                key = f"wizard:{py.stem}"
                components.setdefault(
                    key,
                    ComponentInfo(
                        key=key,
                        name=py.stem,
                        component_type="wizard",
                        path=str(py),
                        module=f"wizards.{py.stem}",
                    ),
                )

        return components
