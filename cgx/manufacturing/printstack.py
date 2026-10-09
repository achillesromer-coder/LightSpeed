from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .compiler import compile_assembly, compile_component

SCHEMA = "CGX-PRINTABLE-4D-COMPONENT/0.1"
STACK_SCHEMA = "CGX-PRINTABLE-4D-STACK/0.1"
CATALOGUE_SCHEMA = "CGX-PRINTABLE-4D-CATALOGUE/0.1"

BASE_SCOPE_KEYS = {
    "geometry",
    "material",
    "process",
    "process_environment",
    "metrology",
    "provenance",
}

_UNRESOLVED = (
    "UNRESOLVED",
    "NOT YET BOUND",
    "NOT BOUND",
    "NOT YET SELECTED",
    "NOT SELECTED",
    "TO BE BOUND",
    "TO BE SELECTED",
)


def _slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip())
    return value.strip("-").lower() or "unnamed"


def _hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _split_semicolon(value: Any) -> list[str]:
    return [part.strip() for part in str(value or "").split(";") if part.strip()]


def _is_bound(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    upper = text.upper()
    return not any(marker in upper for marker in _UNRESOLVED)


def _print_path(strategy: str) -> str:
    return {
        "PRINTED_FUNCTIONAL": "DIRECT_OR_MULTI-MATERIAL_PRINT_PATH",
        "HYBRID_SEED": "PRINT_PLUS_SEED_INSERT_PATH",
        "STRUCTURAL_FORM": "STRUCTURAL_FORM_OR_DEPOSITION_PATH",
        "FLUIDIC_PROCESS": "SEALED_FLUIDIC_FORM_PATH",
        "ELECTROCHEMICAL_PROCESS": "QUALIFIED_ELECTROCHEMICAL_STACK_PATH",
        "ARCHETYPE_ONLY": "SOURCE_AND_PROCESS_BINDING_REQUIRED",
    }.get(strategy, "SOURCE_AND_PROCESS_BINDING_REQUIRED")


def _binding_slots(instance: dict[str, Any] | None) -> list[dict[str, Any]]:
    fields = [
        ("source", "source_locator_or_hash"),
        ("geometry_revision", "geometry_revision"),
        ("dimensions_tolerances", "dimensions_and_tolerances"),
        ("material_lots", "material_stack_and_lots"),
        ("material_passports", "material_passport_refs"),
        ("tool_calibration", "tool_and_calibration_refs"),
        ("configuration_hash", "configuration_hash"),
        ("source_hashes", "source_hashes"),
    ]
    out = []
    for slot, field in fields:
        value = instance.get(field) if instance else None
        out.append(
            {
                "slot": slot,
                "field": field,
                "state": "BOUND" if _is_bound(value) else "OPEN",
                "value": value if _is_bound(value) else None,
            }
        )
    return out


def compile_printable_component(
    record: dict[str, Any],
    *,
    instance: dict[str, Any] | None = None,
    simulation: dict[str, Any] | None = None,
    build_id: str | None = None,
    horizon: str = "H-TERR-SITE",
    required_scopes: list[str] | None = None,
    process_conditions: list[str] | None = None,
    parameter_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    component_ir = compile_component(
        record,
        instance=instance,
        simulation=simulation,
        build_id=build_id,
        horizon=horizon,
        required_scopes=required_scopes,
        process_conditions=process_conditions,
        parameter_overrides=parameter_overrides,
    )
    topology = component_ir["volumetric_topology"]
    iid = instance.get("instance_id") if instance else None
    packet_id = _slug(iid or build_id or record["ID"])

    geometry_slots = [
        {
            "name": name,
            "state": "OPEN_EXACT_VALUE" if not instance or not _is_bound(instance.get("dimensions_and_tolerances")) else "BOUND_IN_INSTANCE_GEOMETRY",
        }
        for name in _split_semicolon(record.get("Geometric Parameters"))
    ]

    topologies = topology.get("topologies", [])
    process_damage_gates = sorted({
        row.get("process_damage_gate")
        for row in topologies
        if row.get("process_damage_gate")
    })
    falsifiers = sorted({
        row.get("falsifier")
        for row in topologies
        if row.get("falsifier")
    })

    stages = []
    for index, op in enumerate(component_ir["operations"], start=1):
        stages.append(
            {
                "stage": index,
                "operation_id": op["id"],
                "opcode": op["opcode"],
                "tool_family": op.get("tool_family"),
                "environment_signature": op.get("environment_signature"),
                "depends_on": op.get("depends_on", []),
                "process_damage_gates": process_damage_gates,
                "physical_execution": False,
            }
        )

    optional_scopes = {
        key: reason
        for key, reason in component_ir["scope_decision"]["included"].items()
        if key not in BASE_SCOPE_KEYS
    }

    if instance is None:
        packet_state = "CATALOGUE_TEMPLATE"
    elif component_ir["execution_state"] == "BUILD_READY":
        packet_state = "BUILD_READY_MACHINE_NEUTRAL"
    elif str(topology.get("resolution_state", "")).startswith("HOLD"):
        packet_state = "HOLD_TOPOLOGY_OR_UPSTREAM"
    else:
        packet_state = "PRINTABLE_PACKET_DRAFT_HOLD"

    packet = {
        "schema": SCHEMA,
        "artifact_id": "UTP-138",
        "cgx_uri": f"cgx://manufacturing/print-packet/{packet_id}",
        "archetype": {
            "id": record["ID"],
            "name": record.get("Component Archetype"),
            "domain": record.get("Domain"),
            "family": record.get("Family"),
            "primary_function": record.get("Primary Function"),
            "scale_band": record.get("Scale Band"),
        },
        "instance_id": iid,
        "manufacturing_ir_ref": component_ir["cgx_uri"],
        "manufacturing_configuration_hash": component_ir["configuration_hash"],
        "recipe_ref": component_ir["recipe_uri"],
        "print_path": _print_path(component_ir["process_strategy"]),
        "packet_state": packet_state,
        "topology": {
            "resolution_state": topology.get("resolution_state"),
            "numeric_state": topology.get("numeric_state"),
            "kernel_ids": topology.get("candidate_kernel_ids", []),
            "compiler_tokens": topology.get("compiler_tokens", []),
            "regions": [
                {
                    "region_role": "FUNCTIONAL_OR_STRUCTURAL_REGION",
                    "kernel_id": row.get("kernel_id"),
                    "primitive": row.get("primitive"),
                    "topology": row.get("topology"),
                    "governing_form": row.get("governing_form"),
                    "numeric_gate": row.get("numeric_gate"),
                }
                for row in topologies
            ],
        },
        "geometry": {
            "baseline": record.get("Baseline Geometry"),
            "parameter_slots": geometry_slots,
            "instance_geometry_binding": instance.get("dimensions_and_tolerances") if instance and _is_bound(instance.get("dimensions_and_tolerances")) else None,
            "revision": instance.get("geometry_revision") if instance and _is_bound(instance.get("geometry_revision")) else None,
        },
        "materials": {
            "catalogue_candidate_stack": record.get("Typical Material Stack"),
            "exact_instance_lots": instance.get("material_stack_and_lots") if instance and _is_bound(instance.get("material_stack_and_lots")) else None,
            "passport_refs": instance.get("material_passport_refs") if instance and _is_bound(instance.get("material_passport_refs")) else None,
        },
        "interfaces": {
            "ports": record.get("Ports / Interfaces"),
            "topology_boundaries": [
                row.get("boundary_interface_conditions")
                for row in topologies
                if row.get("boundary_interface_conditions")
            ],
        },
        "four_d_state": {
            "declared_fields": _split_semicolon(record.get("4D Fields")),
            "consequential_optional_scopes": optional_scopes,
            "horizon": horizon,
            "process_conditions": list(process_conditions or []),
            "history_state": "DIGITAL_PLAN_ONLY / PHYSICAL_NOT_RUN",
            "rule": "Only scopes that can materially change feasibility, state, acceptance or safety are solved; exact evidence may add consequential scopes.",
        },
        "sequence": stages,
        "preservation": {
            "damage_gates": process_damage_gates,
            "rule": "A later operation may proceed only if earlier regions remain inside their qualified damage envelope or an explicit qualified preservation/barrier/alternate sequence is present.",
        },
        "verification": {
            "catalogue_acceptance_tests": record.get("Acceptance Tests"),
            "topology_falsifiers": falsifiers,
            "failure_modes": record.get("Failure Modes"),
        },
        "binding_slots": _binding_slots(instance),
        "blockers": component_ir["blockers"],
        "machine_program": {
            "state": "EMITTABLE_ONLY_AFTER_BUILD_READY_AND_EXACT_MACHINE_BINDING",
            "physical_execution": False,
        },
        "evidence": {
            "catalogue_state": record.get("Evidence State"),
            "source_authority_class": record.get("Source Authority Class"),
            "instance_binding_progress": component_ir.get("binding_progress"),
            "physical_state": instance.get("physical_state") if instance else "NOT_RUN",
        },
        "authority_boundary": "This packet is a machine-neutral printable 4D plan. It does not invent geometry, lots, material properties, calibration, certification or hardware authority, and it cannot raise the owner evidence ceiling.",
    }
    packet["packet_hash"] = _hash({k: v for k, v in packet.items() if k != "packet_hash"})
    return packet


def compile_printable_stack(
    component_specs: list[dict[str, Any]],
    *,
    stack_id: str,
    relations: list[dict[str, str]] | None = None,
    horizon: str = "H-TERR-SITE",
) -> dict[str, Any]:
    component_irs: list[dict[str, Any]] = []
    packets: list[dict[str, Any]] = []

    for index, spec in enumerate(component_specs, start=1):
        record = spec["record"]
        instance = spec.get("instance")
        build_id = spec.get("build_id") or f"{stack_id}-{index:03d}-{record['ID']}"
        ir = compile_component(
            record,
            instance=instance,
            simulation=spec.get("simulation"),
            build_id=build_id,
            horizon=spec.get("horizon", horizon),
            required_scopes=spec.get("required_scopes"),
            process_conditions=spec.get("process_conditions"),
            parameter_overrides=spec.get("parameter_overrides"),
        )
        component_irs.append(ir)
        packets.append(
            compile_printable_component(
                record,
                instance=instance,
                simulation=spec.get("simulation"),
                build_id=build_id,
                horizon=spec.get("horizon", horizon),
                required_scopes=spec.get("required_scopes"),
                process_conditions=spec.get("process_conditions"),
                parameter_overrides=spec.get("parameter_overrides"),
            )
        )

    assembly = compile_assembly(component_irs, build_id=stack_id, relations=relations)
    ready = all(packet["packet_state"] == "BUILD_READY_MACHINE_NEUTRAL" for packet in packets)
    stack = {
        "schema": STACK_SCHEMA,
        "artifact_id": "UTP-138",
        "cgx_uri": f"cgx://manufacturing/print-stack/{_slug(stack_id)}",
        "horizon": horizon,
        "component_packet_refs": [packet["cgx_uri"] for packet in packets],
        "component_packet_hashes": [packet["packet_hash"] for packet in packets],
        "child_recipe_refs": assembly["child_recipe_refs"],
        "recipe_bodies_duplicated": False,
        "coupled_4d_kernel": "VGK-036",
        "dependencies": assembly["dependencies"],
        "schedule": assembly["schedule"],
        "optimization": assembly["optimization"],
        "stack_state": "BUILD_READY_MACHINE_NEUTRAL" if ready and assembly["execution_state"] == "BUILD_READY" else "HOLD",
        "machine_program_state": "EMITTABLE_ONLY_AFTER_ALL_CHILD_AND_INTERFACE_GATES_PASS",
        "physical_execution": False,
        "authority_boundary": "Whole-stack scheduling reuses child recipes and may optimize compatible tool/environment transitions, but it cannot bypass any child, interface, preservation, safety, evidence or owner gate.",
    }
    stack["stack_hash"] = _hash({k: v for k, v in stack.items() if k != "stack_hash"})
    return stack


def compile_printable_catalogue(atlas: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for record in atlas["records"]:
        packet = compile_printable_component(record)
        rows.append(
            {
                "archetype_id": record["ID"],
                "domain": record.get("Domain"),
                "family": record.get("Family"),
                "name": record.get("Component Archetype"),
                "print_path": packet["print_path"],
                "packet_state": packet["packet_state"],
                "topology_kernel_ids": packet["topology"]["kernel_ids"],
                "topology_tokens": packet["topology"]["compiler_tokens"],
                "geometry_parameter_slots": [slot["name"] for slot in packet["geometry"]["parameter_slots"]],
                "candidate_material_stack": packet["materials"]["catalogue_candidate_stack"],
                "ports_interfaces": packet["interfaces"]["ports"],
                "consequential_optional_scopes": sorted(packet["four_d_state"]["consequential_optional_scopes"]),
                "operation_sequence": [stage["opcode"] for stage in packet["sequence"]],
                "acceptance_tests": packet["verification"]["catalogue_acceptance_tests"],
                "failure_modes": packet["verification"]["failure_modes"],
                "evidence_state": packet["evidence"]["catalogue_state"],
                "source_authority_class": packet["evidence"]["source_authority_class"],
                "physical_execution": False,
            }
        )

    out = {
        "schema": CATALOGUE_SCHEMA,
        "artifact_id": "UTP-138",
        "source_catalogue": "CGA / 27_CGX_Component_Geometry_Atlas_v0_1",
        "archetype_count": len(rows),
        "rule": "This is a derived projection over the canonical component atlas and shared compiler. It is not a second engineering/evidence catalogue.",
        "records": rows,
        "authority_boundary": "Catalogue-template compilation creates no exact instance, lot, geometry, calibration, physical execution or certification.",
    }
    out["catalogue_hash"] = _hash({k: v for k, v in out.items() if k != "catalogue_hash"})
    return out
