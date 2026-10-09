from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VOLUMETRIC_KERNEL_PATH = ROOT / "cgx" / "component_atlas" / "type1_volumetric_kernel_v0_1.json"

EXACT_INSTANCE_TOPOLOGY: dict[str, dict[str, Any]] = {
    "CGXI-P0-SH01-ID-A": {
        "kernel_ids": ["VGK-030"],
        "state": "RESOLVED_SYMBOLIC",
        "reason": "Passive identity/readback region is the current first-proof topology.",
    },
    "CGXI-P1-TRACE-001": {
        "kernel_ids": ["VGK-001"],
        "state": "RESOLVED_SYMBOLIC",
        "reason": "Current P1 trace instance is a planar/serpentine conductor coupon.",
    },
    "CGXI-P1-VIA-001": {
        "kernel_ids": ["VGK-002"],
        "state": "RESOLVED_SYMBOLIC",
        "reason": "Current P1 via instance is a vertical cylindrical/filled interconnect candidate.",
    },
    "CGXI-P2-R-001": {
        "kernel_ids": ["VGK-035"],
        "state": "RESOLVED_SYMBOLIC",
        "reason": "The 1.0 kΩ first-proof resistor uses the embedded/serpentine resistive-path topology; thermal coupling remains bounded by the declared benign coupon test.",
    },
    "CGXI-P2-C-001": {
        "kernel_ids": ["VGK-003"],
        "state": "RESOLVED_SYMBOLIC",
        "reason": "The current exact-instance candidate is a parallel-plate electrode/Kapton/electrode stack; other capacitor kernels remain alternatives only after a geometry revision.",
    },
    "CGXI-P2-L-001": {
        "kernel_ids": ["VGK-008", "VGK-010"],
        "state": "HOLD_TOPOLOGY_CHOICE",
        "reason": "The owner instance still permits a canonical solenoid/coil route or a general 3D multi-coil field-solved route; lots, machine envelope and exact geometry must resolve the choice.",
    },
    "CGXI-P3-LC-001": {
        "kernel_ids": ["VGK-012", "VGK-036"],
        "state": "HOLD_UPSTREAM_EVIDENCE",
        "reason": "LC resonance topology remains downstream of measured P2 L/C values; do not independently optimize it before upstream evidence.",
    },
    "CGXI-P3-LOOP-001": {
        "kernel_ids": ["VGK-012"],
        "state": "RESOLVED_SYMBOLIC",
        "reason": "The reviewed 13.56 MHz first-proof target is a passive near-field loop/resonator topology; exact geometry, lots and calibrated fixture remain open.",
    },
}


def load_volumetric_kernel() -> dict[str, Any]:
    return json.loads(VOLUMETRIC_KERNEL_PATH.read_text(encoding="utf-8"))


def find_volumetric_kernel(kernel_id: str, kernel: dict[str, Any] | None = None) -> dict[str, Any]:
    kernel = kernel or load_volumetric_kernel()
    matches = [row for row in kernel["records"] if row.get("kernel_id") == kernel_id]
    if len(matches) != 1:
        raise KeyError(f"volumetric-kernel-not-found:{kernel_id}")
    return matches[0]


def _generic_kernel_candidates(record: dict[str, Any]) -> list[str]:
    name = str(record.get("Component Archetype", "")).lower()
    domain = str(record.get("Domain", "")).lower()

    if "via" in name or "vertical interconnect" in name:
        return ["VGK-002"]
    if "parallel-plate capacitor" in name:
        return ["VGK-003"]
    if "multilayer capacitor" in name:
        return ["VGK-004"]
    if "coax" in name and "capac" in name:
        return ["VGK-005"]
    if "spherical" in name and "capac" in name:
        return ["VGK-006"]
    if "capacitor" in name:
        return ["VGK-003", "VGK-007"]
    if any(x in name for x in ("solenoid", "air-core inductor")):
        return ["VGK-008", "VGK-010"]
    if "toroid" in name:
        return ["VGK-009", "VGK-010"]
    if any(x in name for x in ("inductor", "transformer", "coil")):
        return ["VGK-010"]
    if any(x in name for x in ("loop antenna", "near-field", "nfc", "rfid")):
        return ["VGK-012"]
    if any(x in name for x in ("transmission line", "waveguide")) and "optical" not in name:
        return ["VGK-011"]
    if any(x in name for x in ("trace", "busbar", "conductor", "interconnect")):
        return ["VGK-001"]
    if any(x in name for x in ("heater", "resistor")):
        return ["VGK-035"]
    if "channel" in name or "pipe" in name or "tube" in name:
        return ["VGK-019"]
    if any(x in name for x in ("porous", "wick", "filter")):
        return ["VGK-020"]
    if any(x in name for x in ("cavity", "plenum", "reservoir")):
        return ["VGK-021"]
    if "optical" in domain or any(x in name for x in ("waveplate", "beamsplitter", "thin-film", "mirror")):
        return ["VGK-022", "VGK-023"]
    if "sensor" in domain:
        return ["VGK-026"]
    if "actuation" in domain or any(x in name for x in ("actuator", "motor", "solenoid")):
        return ["VGK-028"]
    if "mechanical" in domain:
        return ["VGK-016", "VGK-017", "VGK-018"]
    if "electrochemical" in domain or "battery" in name or "cell" in name:
        return ["VGK-032"]
    if "semiconductor" in domain or any(x in name for x in ("cpu", "soc", "mcu", "ic ", "logic")):
        return ["VGK-034"]
    if "power" in domain:
        return ["VGK-033"]
    return ["VGK-036"]


def _instance_blockers(instance: dict[str, Any] | None) -> list[str]:
    if not instance:
        return ["exact-instance-not-bound"]
    blockers: list[str] = []
    text_fields = {
        "geometry": f"{instance.get('geometry_revision','')} {instance.get('dimensions_and_tolerances','')}",
        "lots": f"{instance.get('material_stack_and_lots','')} {instance.get('material_passport_refs','')}",
        "tool_calibration": str(instance.get("tool_and_calibration_refs", "")),
    }
    for key, value in text_fields.items():
        u = value.upper()
        if not value.strip() or any(marker in u for marker in ("UNRESOLVED", "NOT YET BOUND", "NOT BOUND", "NOT SELECTED")):
            blockers.append(key)
    if instance.get("physical_state") == "NOT_RUN":
        blockers.append("physical-test-not-run")
    return blockers


def resolve_volumetric_topology(
    record: dict[str, Any],
    *,
    instance: dict[str, Any] | None = None,
    kernel: dict[str, Any] | None = None,
) -> dict[str, Any]:
    kernel = kernel or load_volumetric_kernel()
    iid = instance.get("instance_id") if instance else None
    exact = EXACT_INSTANCE_TOPOLOGY.get(str(iid)) if iid else None
    kernel_ids = list(exact["kernel_ids"]) if exact else _generic_kernel_candidates(record)
    rows = [find_volumetric_kernel(kid, kernel) for kid in kernel_ids]
    blockers = _instance_blockers(instance)

    if exact:
        state = str(exact["state"])
        reason = str(exact["reason"])
    elif len(kernel_ids) == 1:
        state = "ARCHETYPE_TOPOLOGY_CANDIDATE"
        reason = "Generic archetype-to-topology projection only; exact instance geometry controls downstream inference."
    else:
        state = "HOLD_TOPOLOGY_CHOICE"
        reason = "Multiple topology kernels are compatible with the archetype; exact geometry/process context must select one."

    if state == "RESOLVED_SYMBOLIC" and blockers:
        numeric_state = "SYMBOLIC"
    elif state.startswith("HOLD"):
        numeric_state = "HOLD"
    else:
        numeric_state = "SYMBOLIC"

    out = {
        "schema": "CGX-VOLUMETRIC-TOPOLOGY-RESOLUTION/0.1",
        "artifact_id": "UTP-137",
        "instance_id": iid,
        "archetype_id": record.get("ID"),
        "resolution_state": state,
        "numeric_state": numeric_state,
        "candidate_kernel_ids": kernel_ids,
        "compiler_tokens": [row["compiler_token"] for row in rows],
        "topologies": [
            {
                "kernel_id": row["kernel_id"],
                "primitive": row["primitive_basis_class"],
                "topology": row["topology_geometry_family"],
                "governing_form": row["governing_law_matrix_form"],
                "numeric_gate": row["numeric_inference_gate"],
                "process_damage_gate": row["process_damage_preservation_gate"],
                "falsifier": row["verification_falsifier"],
            }
            for row in rows
        ],
        "reason": reason,
        "blockers": blockers,
        "physical_execution": False,
        "authority_boundary": "Topology selection is digital engineering state only. It does not create exact geometry, lot/tool evidence, measured material properties, physical qualification or execution authority.",
    }
    return out
