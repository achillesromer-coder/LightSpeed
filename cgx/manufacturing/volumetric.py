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
    """Resolve archetype-level topology candidates without inventing exact geometry.

    Specific reusable topology kernels are preferred when the component name/domain
    makes the topology class clear. VGK-036 is retained for genuinely coupled or
    implementation-dependent assemblies rather than used as a generic catch-all.
    """
    name = str(record.get("Component Archetype", "")).lower()
    domain = str(record.get("Domain", "")).lower()

    # Exact/simple geometry families first.
    if "via" in name or "vertical interconnect" in name or "plated through-hole" in name:
        return ["VGK-002"]
    if "parallel-plate capacitor" in name:
        return ["VGK-003"]
    if "multilayer capacitor" in name:
        return ["VGK-004"]
    if "coax" in name and "capac" in name:
        return ["VGK-005"]
    if "spherical" in name and "capac" in name:
        return ["VGK-006"]
    if "capacitive touch" in name or "capacitive proximity" in name or "capacitive level" in name:
        return ["VGK-026"]
    if "capacitive pressure sensor" in name:
        return ["VGK-026", "VGK-017"]
    if "capacitor" in name:
        return ["VGK-003", "VGK-007"]

    # Acoustic/piezoelectric wave devices are not generic structural assemblies.
    if (
        "acoustic" in domain
        or any(x in name for x in (
            "quartz crystal", "saw resonator", "baw", "fbar", "piezo",
            "microphone", "buzzer", "ultrasonic", "helmholtz",
        ))
    ):
        return ["VGK-038"]

    # RF topology. Quasi-TEM paths remain VGK-011; radiating/scattering geometries
    # use the full-wave field kernel. Lumped/mixed networks intentionally remain 036.
    if domain == "rf/communications":
        if "optical ring" in name:
            return ["VGK-022"]
        if any(x in name for x in ("microstrip resonator", "stripline", "directional coupler", "power divider", "power combiner")):
            return ["VGK-011"]
        if any(x in name for x in (
            "dipole antenna", "monopole antenna", "helical antenna", "patch antenna",
            "pifa", "slot antenna", "yagi", "horn antenna", "full-wave",
            "rf shielded resonant enclosure",
        )):
            return ["VGK-037"]
        if "rectenna" in name:
            return ["VGK-037", "VGK-034"]
        if "ferrite circulator" in name or "ferrite isolator" in name:
            return ["VGK-010", "VGK-037"]
        if any(x in name for x in (
            "low-noise amplifier", "rf power amplifier", "mixer", "frequency converter",
            "rf switch", "rf attenuator", "rf phase shifter", "rf detector",
            "receiver front-end", "transmitter front-end", "radio transceiver",
            "frequency multiplier", "frequency divider", "local oscillator", "dds synthesizer",
        )):
            return ["VGK-034"]
        if any(x in name for x in ("loop antenna", "near-field", "nfc", "rfid")):
            return ["VGK-012"]
        # LC resonators, diplexers/duplexers, matching networks and tuners are
        # implementation-dependent multi-primitive networks by default.
        return ["VGK-036"]

    # Distributed electrical packaging and conductors.
    if domain == "electrical/packaging":
        if any(x in name for x in ("stripline", "coaxial line", "twisted pair", "twinax")):
            return ["VGK-011"]
        if "coaxial / rf connector" in name:
            return ["VGK-011", "VGK-029"]
        if any(x in name for x in ("ground plane", "contact pad", "land-grid")):
            return ["VGK-001"]
        if "faraday" in name or "shield enclosure" in name:
            return ["VGK-037", "VGK-018"]
        if "cable gland" in name:
            return ["VGK-025", "VGK-029"]
        if "conduit" in name or "raceway" in name:
            return ["VGK-018", "VGK-029"]
        if any(x in name for x in ("connector", "terminal block", "spring/contact")):
            return ["VGK-001", "VGK-029"]
        if any(x in name for x in ("solder joint", "conductive adhesive", "flip-chip bump")):
            return ["VGK-001", "VGK-018"]
        # Rigid/flex PCB stacks and compound packaging transitions are genuinely
        # multi-region assemblies until exact layer/stack geometry is selected.
        return ["VGK-036"]

    # Magnetic field and actuator families.
    if any(x in name for x in ("solenoid", "air-core inductor")):
        return ["VGK-008", "VGK-010"]
    if "toroid" in name:
        return ["VGK-009", "VGK-010"]
    if any(x in name for x in ("ferrite bead", "common-mode choke", "inductor", "transformer", "coil", "permanent magnet", "flux concentrator", "pole piece")):
        return ["VGK-010"]
    if "electromagnet" in name:
        return ["VGK-028"]

    # Non-RF transmission/wave paths.
    if "waveguide" in name and "optical" not in name:
        return ["VGK-037"]
    if "transmission line" in name:
        return ["VGK-011"]
    if any(x in name for x in ("trace", "busbar", "conductor", "interconnect", "grounding", "bonding strap")):
        return ["VGK-001"]

    # Resistive/thermal-electrical elements and simple electrical sensors.
    if any(x in name for x in ("ntc thermistor", "ptc thermistor", "rtd element", "resistive leak sensor")):
        return ["VGK-035"]
    if "piezoresistive pressure" in name:
        return ["VGK-035", "VGK-017"]
    if any(x in name for x in ("heater", "resistor")):
        return ["VGK-035"]
    if "potentiometer" in name or "rheostat" in name:
        return ["VGK-035", "VGK-018"]
    if "varistor" in name or "mov" in name:
        return ["VGK-031"]

    # Sensors: map the primary transduction/field topology, retaining exact seed
    # boundaries where fabrication is not independently qualified.
    if domain == "sensing":
        if any(x in name for x in ("accelerometer", "gyroscope")):
            return ["VGK-034", "VGK-017"]
        if any(x in name for x in ("magnetometer", "hall-effect", "inductive proximity", "fluxgate")):
            return ["VGK-010"]
        if "humidity capacitive" in name:
            return ["VGK-026", "VGK-024"]
        if any(x in name for x in ("electrochemical gas", "ph electrode", "dissolved-oxygen", "ion-selective")):
            return ["VGK-024"]
        if "mos gas" in name:
            return ["VGK-034", "VGK-024"]
        if "conductivity sensor" in name:
            return ["VGK-001", "VGK-024"]
        if "thermal mass-flow" in name:
            return ["VGK-039", "VGK-015"]
        if any(x in name for x in ("thermopile", "bolometer")):
            return ["VGK-015", "VGK-035"]
        if any(x in name for x in (
            "optical encoder", "time-of-flight", "lidar", "ndir", "optical interrupter",
            "ambient-light", "color sensor", "uv photodetector", "optical particulate",
            "turbidity", "optical-density", "scintillation",
        )):
            return ["VGK-022", "VGK-034"]
        if "radar sensor" in name:
            return ["VGK-037", "VGK-034"]
        if "geiger" in name:
            return ["VGK-034"]
        if "thermocouple" in name:
            return ["VGK-001"]
        return ["VGK-036"]

    # Fluid/thermal: canonical simple channels retain VGK-019; complex geometries
    # use VGK-039 rather than forcing the laminar circular-channel equation.
    if domain == "fluid/thermal":
        if any(x in name for x in ("heat sink", "thermal interface", "radiator / heat-rejection")):
            return ["VGK-013", "VGK-015"]
        if "vapor chamber" in name:
            return ["VGK-021", "VGK-015"]
        if any(x in name for x in ("cold plate", "heat exchanger")):
            return ["VGK-039", "VGK-015"]
        if "peltier" in name or "tec module" in name:
            return ["VGK-034", "VGK-015"]
        if "membrane separator" in name:
            return ["VGK-024", "VGK-025"]
        if any(x in name for x in ("packed", "catalyst bed")):
            return ["VGK-020", "VGK-024"]
        if "phase-change thermal" in name:
            return ["VGK-015"]
        if any(x in name for x in ("porous", "wick", "filter")):
            return ["VGK-020"]
        if any(x in name for x in ("cavity", "plenum", "reservoir")):
            return ["VGK-021"]
        if "channel" in name or "pipe" in name or "tube" in name:
            return ["VGK-019"]
        if any(x in name for x in (
            "nozzle", "orifice", "venturi", "tesla valve", "check valve",
            "needle", "proportional valve", "pump", "manifold", "cyclone",
            "droplet", "sparger", "diffuser",
        )):
            return ["VGK-039"]
        return ["VGK-036"]

    # Protection/switching resolves the physical protection region rather than
    # pretending a part-level safety device alone constitutes a full safety case.
    if domain == "protection/switching":
        if "grounding" in name or "bonding strap" in name:
            return ["VGK-001"]
        if any(x in name for x in ("esd protection diode", "solid-state relay", "photomos")):
            return ["VGK-034", "VGK-031"]
        if "membrane switch" in name:
            return ["VGK-001", "VGK-017"]
        if any(x in name for x in ("fuse", "thermal cutoff", "thermal fuse")):
            return ["VGK-035", "VGK-031"]
        return ["VGK-031"]

    # Energy collection/conversion remains mechanism-specific.
    if domain == "energy":
        if "inductive wireless power" in name:
            return ["VGK-010", "VGK-033"]
        if "capacitive wireless power" in name:
            return ["VGK-007", "VGK-033"]
        if "ambient rf energy" in name:
            return ["VGK-037", "VGK-033"]
        if "solar hull" in name or "photovoltaic" in name:
            return ["VGK-034", "VGK-033"]
        if "power-conditioning" in name or "storage bus" in name:
            return ["VGK-033", "VGK-032"]

    if "optical" in domain or any(x in name for x in ("waveplate", "beamsplitter", "thin-film", "mirror")):
        return ["VGK-022", "VGK-023"]
    if "actuation" in domain or any(x in name for x in ("actuator", "motor")):
        return ["VGK-028"]
    if "mechanical" in domain:
        return ["VGK-016", "VGK-017", "VGK-018"]
    if "electrochemical" in domain or "battery" in name or "cell" in name:
        return ["VGK-032"]
    if "semiconductor" in domain or any(x in name for x in ("cpu", "soc", "mcu", "ic ", "logic")):
        return ["VGK-034"]
    if "power" in domain:
        return ["VGK-033"]

    # Deliberate final fallback: genuine compound/implementation-dependent assembly.
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