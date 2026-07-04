from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lightspeed_runtime.domain_registry import FLOOR_RUNTIME_MAPPING


@dataclass(frozen=True)
class DesktopIntegrationTarget:
    floor_name: str
    runtime_domain: str
    current_owner_path: str
    integration_goal: str


CURRENT_DESKTOP_ROOT = Path(r"C:\Users\acc\Desktop\LightSpeed Consolidated\LightSpeed")
CURRENT_RUNTIME_ROOT = Path(r"D:\LightSpeed_Consolidated\LightSpeed_Runtime")


INTEGRATION_TARGETS: list[DesktopIntegrationTarget] = [
    DesktopIntegrationTarget(
        floor_name="Oracle",
        runtime_domain=FLOOR_RUNTIME_MAPPING["Oracle"],
        current_owner_path=str(CURRENT_DESKTOP_ROOT / "Z Axis" / "Oracle.py"),
        integration_goal="Replace archive-centric discovery with reservoir-backed search and provenance.",
    ),
    DesktopIntegrationTarget(
        floor_name="Morpheus",
        runtime_domain=FLOOR_RUNTIME_MAPPING["Morpheus"],
        current_owner_path=str(CURRENT_DESKTOP_ROOT / "Z Axis" / "Morpheus.py"),
        integration_goal="Move parsing, extraction, and ingest previews onto reservoir manifests and indexed assets.",
    ),
    DesktopIntegrationTarget(
        floor_name="TheConstruct",
        runtime_domain=FLOOR_RUNTIME_MAPPING["TheConstruct"],
        current_owner_path=str(CURRENT_DESKTOP_ROOT / "Z Axis" / "TheConstruct.py"),
        integration_goal="Bind graph/scenario structures to lab runs and dataset references rather than freeform artifacts.",
    ),
    DesktopIntegrationTarget(
        floor_name="Architect",
        runtime_domain=FLOOR_RUNTIME_MAPPING["Architect"],
        current_owner_path=str(CURRENT_DESKTOP_ROOT / "Z Axis" / "Architect.py"),
        integration_goal="Generate publish manifests and task states from the canonical workspace runtime.",
    ),
    DesktopIntegrationTarget(
        floor_name="Neo",
        runtime_domain=FLOOR_RUNTIME_MAPPING["Neo"],
        current_owner_path=str(CURRENT_DESKTOP_ROOT / "Z Axis" / "Neo.py"),
        integration_goal="Route prompts and actions through Achilles envelopes and approval gates.",
    ),
    DesktopIntegrationTarget(
        floor_name="Trinity",
        runtime_domain=FLOOR_RUNTIME_MAPPING["Trinity"],
        current_owner_path=str(CURRENT_DESKTOP_ROOT / "N.py"),
        integration_goal="Attach calculator and GMAT execution to lab run contracts and dataset refs.",
    ),
    DesktopIntegrationTarget(
        floor_name="Smith",
        runtime_domain=FLOOR_RUNTIME_MAPPING["Smith"],
        current_owner_path=str(CURRENT_RUNTIME_ROOT / "lightspeed_runtime" / "runtime.py"),
        integration_goal="Use approval queues and SOP boundaries from the shell domain.",
    ),
    DesktopIntegrationTarget(
        floor_name="Merovingian",
        runtime_domain=FLOOR_RUNTIME_MAPPING["Merovingian"],
        current_owner_path=str(CURRENT_RUNTIME_ROOT / "lightspeed_runtime" / "publishing" / "manager.py"),
        integration_goal="Expose diagnostics, audits, and publication health from canonical runtime state.",
    ),
]


def build_integration_backlog() -> list[dict]:
    return [
        {
            "floor_name": target.floor_name,
            "runtime_domain": target.runtime_domain,
            "current_owner_path": target.current_owner_path,
            "integration_goal": target.integration_goal,
        }
        for target in INTEGRATION_TARGETS
    ]
