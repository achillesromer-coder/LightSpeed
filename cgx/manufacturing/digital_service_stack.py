"""Canonical CGX PrintSpace *digital* service envelope and reverse trace.

Assembles the EXISTING manufacturing compiler, exact convex composition,
nominal geometry, owner-matrix source class selection, independent bidirectional
coupon planning, process preflight and LOAD H0 projection. This is a read-only
orchestration/view, not another manufacturing compiler, DBR, agent, root,
R1-R3 LOAD hydration, finite-element solver, device driver or material database.

The reverse validator must be supplied original objects again, not just a
self-consistent bundle. It recomputes every stage and walks dependencies from
release gate back to source and geometry. It cannot authenticate external
source bodies, licence signatures, host attestations or empirical measurements.
"""
from __future__ import annotations

import json
import re
from typing import Any

from .compiler import SCHEMA as IR_SCHEMA, _canonical_hash
from .composition import compile_geometry_composition, digest
from .solid_metrics import measure_composite_nominal
from .interface_qualification import plan_interface_witnesses
from .review_gate import review_existing_manufacturing_ir

SCHEMA = "CGX-PRINTSPACE-DIGITAL-SERVICE-STACK/0.1"
BACKTRACE_SCHEMA = "CGX-PRINTSPACE-DIGITAL-SERVICE-BACKTRACE/0.1"
MAX_INPUT_BYTES = 1024 * 1024
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
BUILD_URI = re.compile(r"cgx://manufacturing/build/[A-Za-z0-9._-]{1,128}\Z")
STAGE_ORDER = (
    "R0_SOURCE",
    "G0_NOMINAL_SOLIDS",
    "G1_EXACT_CONTACT",
    "M0_MATERIAL_ARCHETYPES",
    "I0_DIRECTIONAL_INTERFACES",
    "P0_MANUFACTURING_IR",
    "P1_PROCESS_REVIEW",
    "E0_ENVIRONMENT_CONTROL",
    "Q0_WITNESS_COUPONS",
    "S0_FUNCTIONAL_SERVICE_SCOPES",
    "L0_LOAD_H0",
    "A0_AUTHORITY_HOLD",
)
DEPS = {
    "R0_SOURCE": (),
    "G0_NOMINAL_SOLIDS": ("R0_SOURCE",),
    "G1_EXACT_CONTACT": ("G0_NOMINAL_SOLIDS",),
    "M0_MATERIAL_ARCHETYPES": ("R0_SOURCE", "G0_NOMINAL_SOLIDS"),
    "I0_DIRECTIONAL_INTERFACES": ("G1_EXACT_CONTACT", "M0_MATERIAL_ARCHETYPES"),
    "P0_MANUFACTURING_IR": ("R0_SOURCE", "G1_EXACT_CONTACT"),
    "P1_PROCESS_REVIEW": ("P0_MANUFACTURING_IR", "I0_DIRECTIONAL_INTERFACES"),
    "E0_ENVIRONMENT_CONTROL": ("P1_PROCESS_REVIEW",),
    "Q0_WITNESS_COUPONS": ("I0_DIRECTIONAL_INTERFACES", "E0_ENVIRONMENT_CONTROL"),
    "S0_FUNCTIONAL_SERVICE_SCOPES": ("G0_NOMINAL_SOLIDS", "M0_MATERIAL_ARCHETYPES", "P1_PROCESS_REVIEW", "Q0_WITNESS_COUPONS"),
    "L0_LOAD_H0": ("R0_SOURCE", "G1_EXACT_CONTACT", "Q0_WITNESS_COUPONS"),
    "A0_AUTHORITY_HOLD": ("P0_MANUFACTURING_IR", "E0_ENVIRONMENT_CONTROL", "Q0_WITNESS_COUPONS", "S0_FUNCTIONAL_SERVICE_SCOPES", "L0_LOAD_H0"),
}
OWNERS = {
    "R0_SOURCE": "Owner Drive source / existing canonical geometry",
    "G0_NOMINAL_SOLIDS": "cgx.manufacturing.solid_metrics",
    "G1_EXACT_CONTACT": "cgx.manufacturing.composition / exact_contact",
    "M0_MATERIAL_ARCHETYPES": "owner 411-row hash projection",
    "I0_DIRECTIONAL_INTERFACES": "cgx.manufacturing.composition",
    "P0_MANUFACTURING_IR": "cgx.manufacturing.compiler",
    "P1_PROCESS_REVIEW": "cgx.manufacturing.review_gate",
    "E0_ENVIRONMENT_CONTROL": "cgx.manufacturing.review_gate",
    "Q0_WITNESS_COUPONS": "cgx.manufacturing.interface_qualification",
    "S0_FUNCTIONAL_SERVICE_SCOPES": "existing canonical CGX IR scope decision",
    "L0_LOAD_H0": "existing LOAD.cgx source-review alias / FileSpace",
    "A0_AUTHORITY_HOLD": "Achilles / parent DBR / independent C0 owner",
}
HOLD_REASONS = (
    "NATIVE_SOURCE_AND_RIGHTS_NOT_ADMITTED",
    "ACTUAL_MATERIAL_LOTS_NOT_OBSERVED",
    "DIRECTIONAL_COUPON_MEASUREMENTS_NOT_WITNESSED",
    "PHYSICAL_TOOL_CALIBRATION_NOT_VERIFIED",
    "BOOLEANS_DENSITIES_AND_FUNCTIONAL_PARAMETERS_UNRESOLVED",
    "PARENT_DBR_NATIVE_AUTHORITY_NOT_ISSUED",
)


def _hold(code: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA, "state": "HOLD_DIGITAL_INPUT",
        "hold_codes": [code], "manifest_sha256": None, "layers": [],
        "digital_reference_checks": False, "real_source_body_authenticated": False,
        "physically_qualified": False, "native_dbr_written": False,
        "machine_authorised": False, "mint_authorised": False,
        "commercial_release_authorised": False,
    }


def _jsonable_limited(*args: Any) -> bool:
    try:
        raw = json.dumps(args, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False).encode("ascii")
        return len(raw) <= MAX_INPUT_BYTES
    except (TypeError, ValueError, RecursionError, OverflowError):
        return False


def compile_digital_service_stack(manufacturing_ir: Any, geometry_request: Any,
                                  interface_selections: Any, process_packet: Any = None) -> dict:
    """Bottom-up deterministic provenance DAG, NOT a machine/physical build."""
    if (not isinstance(manufacturing_ir, dict) or not isinstance(geometry_request, dict)
            or not isinstance(interface_selections, dict)
            or (process_packet is not None and not isinstance(process_packet, dict))):
        return _hold("SERVICE_INPUT_SCHEMA")
    if not _jsonable_limited(manufacturing_ir, geometry_request, interface_selections, process_packet):
        return _hold("SERVICE_INPUT_NONCANONICAL_OR_OVERSIZE")
    if manufacturing_ir.get("schema") != IR_SCHEMA:
        return _hold("CANONICAL_IR_SCHEMA")
    uri = manufacturing_ir.get("cgx_uri")
    ir_sha = manufacturing_ir.get("configuration_hash")
    if not isinstance(uri, str) or BUILD_URI.fullmatch(uri) is None:
        return _hold("CANONICAL_IR_URI_INVALID")
    if not isinstance(ir_sha, str) or SHA256.fullmatch(ir_sha) is None:
        return _hold("CANONICAL_IR_HASH_INVALID")
    if _canonical_hash({k: v for k, v in manufacturing_ir.items() if k != "configuration_hash"}) != ir_sha:
        return _hold("CANONICAL_IR_TAMPERED")
    if (manufacturing_ir.get("physical_execution") is not False
            or not isinstance(manufacturing_ir.get("operations"), list)
            or any(not isinstance(op, dict) or op.get("physical_execution") is not False
                   for op in manufacturing_ir["operations"])):
        return _hold("PHYSICAL_EXECUTION_IN_DIGITAL_IR")
    if (geometry_request.get("manufacturing_ir_ref") != uri
            or geometry_request.get("manufacturing_ir_configuration_hash") != ir_sha):
        return _hold("GEOMETRY_BUILD_REF_STALE")
    if (interface_selections.get("manufacturing_ir_ref") != uri
            or interface_selections.get("manufacturing_ir_configuration_hash") != ir_sha):
        return _hold("WITNESS_BUILD_REF_STALE")

    geometry = compile_geometry_composition(geometry_request)
    if geometry.get("state") != "REVIEW_ONLY":
        return _hold("DIGITAL_GEOMETRY_NOT_REVIEWABLE")
    metrics = measure_composite_nominal(geometry_request, geometry)
    if metrics.get("state") != "EXACT_DIGITAL_NOMINAL_ONLY":
        return _hold("EXACT_NOMINAL_METRICS_UNRESOLVED")
    witness = plan_interface_witnesses(geometry, interface_selections)
    if witness.get("state") != "PLAN_READY_UNQUALIFIED":
        return _hold("SOURCE_BOUND_WITNESS_PLAN_UNRESOLVED")
    plan = witness["plan"]
    if (plan["manufacturing_ir_ref"] != uri
            or plan["manufacturing_ir_configuration_hash"] != ir_sha
            or plan["geometry_composite_sha256"] != geometry["geometry_composite_hash"]
            or metrics["geometry_composite_hash"] != geometry["geometry_composite_hash"]):
        return _hold("INTER_STAGE_SOURCE_REF_DRIFT")

    # The existing review gate is the only process review; a source-class plan
    # can never create actual material, geometry, tool or C0 evidence.
    process_result = (review_existing_manufacturing_ir(
        manufacturing_ir, process_packet,
        geometry_composition=geometry_request,
        interface_selections=interface_selections,
    ) if process_packet is not None else None)
    if process_result is not None and (process_result.get("physical_machine_authorised") is not False
                                      or process_result.get("mint_authorised") is not False
                                      or process_result.get("commercial_release_authorised") is not False):
        return _hold("PROCESS_AUTHORITY_ESCALATION")

    source_shapes = geometry["graph"]["shape_catalogue"]
    regions = plan["source_regions"]
    interfaces = geometry["graph"]["interfaces"]
    routes = [r for e in plan["interfaces"] for r in e["directions"]]
    if (len(routes) != 2*len(interfaces)
            or len({r["coupon_candidate_id"] for r in routes}) != len(routes)
            or any(r["raw_measurement_receipt"] is not None for r in routes)):
        return _hold("WITNESS_EVIDENCE_OR_DIRECTION_COLLISION")
    if any(e["physical_compatibility"] != "NOT_VERIFIED" for e in interfaces):
        return _hold("PHYSICAL_COMPATIBILITY_CLAIM")
    scopes = manufacturing_ir.get("scope_decision")
    if not isinstance(scopes, dict) or not isinstance(scopes.get("included"), dict):
        return _hold("CANONICAL_SERVICE_SCOPES_INVALID")
    included = sorted(scopes["included"])
    if not all(isinstance(k, str) and isinstance(scopes["included"][k], str) for k in included):
        return _hold("CANONICAL_SERVICE_SCOPES_INVALID")

    data = {
        "R0_SOURCE": {"shape_keys": [x["sha256"] for x in source_shapes],
                      "shape_source_refs": [x["source_ref"] for x in source_shapes],
                      "owner_projection_sha256": plan["owner_projection_sha256"],
                      "vgk_kernel_sha256": geometry["graph"]["kernel_library_sha256"],
                      "source_status": "OWNER_SNAPSHOT_AND_DIGITAL_REFERENCE_ONLY"},
        "G0_NOMINAL_SOLIDS": {"metrics_sha256": digest(metrics),
                              "nominal_sum_volume_mm3_exact": metrics["nominal_sum_volume_mm3_exact"],
                              "geometric_centroid_mm_exact": metrics["volume_weighted_geometric_centroid_mm_exact"],
                              "union_volume_mm3_exact": None, "mass_g": None},
        "G1_EXACT_CONTACT": {"geometry_sha256": geometry["geometry_composite_hash"],
                             "shape_count": len(source_shapes),
                             "region_count": len(geometry["graph"]["instances"]),
                             "directed_contact_geometry": [
                                 {"from": e["from"], "to": e["to"],
                                  "relation": e["exact_convex_contact"]["relation"],
                                  "area_mm2_exact": e["exact_convex_contact"].get("face_area_mm2_exact")}
                                 for e in interfaces],
                             "boolean_union": "NOT_CALCULATED"},
        "M0_MATERIAL_ARCHETYPES": {"owner_projection_sha256": plan["owner_projection_sha256"],
                                  "region_matrix_ids": [r["matrix_id"] for r in regions],
                                  "row_sha256s": [r["directional_sha256"] for r in regions],
                                  "material_lot_passports": "NONE_OBSERVED"},
        "I0_DIRECTIONAL_INTERFACES": {"graph_sha256": geometry["geometry_composite_hash"],
                                     "directions_are_distinct": True,
                                     "interface_count": len(interfaces),
                                     "material_compatibility": "UNQUALIFIED"},
        "P0_MANUFACTURING_IR": {"cgx_uri": uri, "configuration_sha256": ir_sha,
                                "existing_compiler": IR_SCHEMA, "physical_execution": False,
                                "instance_ref": manufacturing_ir.get("instance_ref"),
                                "instance_binding_progress": manufacturing_ir.get("binding_progress")},
        "P1_PROCESS_REVIEW": {
            "process_packet_sha256": digest(process_packet) if process_packet is not None else None,
            "existing_gate_state": process_result["state"] if process_result is not None else "MISSING_PROCESS_PACKET",
            "finding_codes": sorted({x["code"] for x in process_result["findings"]})
                if process_result is not None else ["PROCESS_PACKET_NOT_BOUND"],
            "external_process_evidence": "NOT_INDEPENDENTLY_VERIFIED"},
        "E0_ENVIRONMENT_CONTROL": {
            "process_review": "DECLARATION_ONLY" if process_result is not None else "UNBOUND",
            "temperature_pressure_atmosphere_actual": None,
            "oxygen_moisture_history_actual": None,
            "em_exposure_history_actual": None,
            "independent_c0_confirmation": None},
        "Q0_WITNESS_COUPONS": {
            "plan_sha256": witness["plan_sha256"],
            "directional_coupon_ids": sorted(x["coupon_candidate_id"] for x in routes),
            "coupon_count": len(routes),
            "measurement_receipts": None, "independent_bidirectional_results": False},
        "S0_FUNCTIONAL_SERVICE_SCOPES": {
            "scopes_from_canonical_ir": included,
            "scope_reasons_sha256": digest(scopes["included"]),
            "electrical_conductivity": None, "mechanical_modulus": None,
            "dielectric_response": None, "thermal_history_response": None,
            "functional_4d_actuation": None, "model_or_solver_calibration": None,
            "status": "PHYSICAL_PARAMETERS_UNBOUND"},
        "L0_LOAD_H0": {"alias": geometry["load_h0"]["alias"],
                       "composite_identity": geometry["load_h0"]["identity"],
                       "source_bytes_hydrated": 0,
                       "parent": geometry["load_h0"]["parent_filespace"],
                       "child": geometry["load_h0"]["child_filespace"],
                       "native_admitted": False},
        "A0_AUTHORITY_HOLD": {"source_rights_signatures": None,
                              "independent_actual_material_evidence": None,
                              "parent_dbr_receipt": None, "separate_c0_permission": None,
                              "machine_authorised": False, "mint_authorised": False,
                              "commercial_release_authorised": False},
    }
    status = {
        "R0_SOURCE": "SOURCE_SNAPSHOT_ONLY",
        "G0_NOMINAL_SOLIDS": "DIGITAL_REVIEW",
        "G1_EXACT_CONTACT": "DIGITAL_REVIEW",
        "M0_MATERIAL_ARCHETYPES": "ARCHETYPE_ONLY",
        "I0_DIRECTIONAL_INTERFACES": "PHYSICAL_UNQUALIFIED",
        "P0_MANUFACTURING_IR": "NON_EXECUTABLE_IR",
        "P1_PROCESS_REVIEW": "DECLARED_NOT_MEASURED" if process_result is not None else "UNBOUND",
        "E0_ENVIRONMENT_CONTROL": "UNBOUND",
        "Q0_WITNESS_COUPONS": "PLANNED_UNMEASURED",
        "S0_FUNCTIONAL_SERVICE_SCOPES": "UNPARAMETERISED",
        "L0_LOAD_H0": "NONHYDRATING_SOURCE_REFERENCE",
        "A0_AUTHORITY_HOLD": "RELEASE_AND_DEVICE_HOLD",
    }
    by_name: dict[str, dict] = {}
    layers = []
    for layer_id in STAGE_ORDER:
        deps = list(DEPS[layer_id])
        if any(d not in by_name for d in deps):
            return _hold("INVALID_OR_CYCLIC_SERVICE_DEPENDENCIES")
        core = {
            "id": layer_id,
            "depends_on": [{"id": dep, "sha256": by_name[dep]["node_sha256"]} for dep in deps],
            "source_owner": OWNERS[layer_id],
            "state": status[layer_id],
            "payload_sha256": digest(data[layer_id]),
        }
        core["node_sha256"] = digest(core)
        by_name[layer_id] = core
        layers.append(core)

    envelope = {
        "schema": SCHEMA,
        "state": "DIGITAL_STACK_REVIEW_ONLY_PHYSICAL_HOLD",
        "input_sha256s": {
            "manufacturing_ir": digest(manufacturing_ir),
            "geometry_request": digest(geometry_request),
            "interface_selections": digest(interface_selections),
            "process_packet": digest(process_packet) if process_packet is not None else None,
        },
        "canonical_ir": {"uri": uri, "configuration_sha256": ir_sha},
        "geometry_sha256": geometry["geometry_composite_hash"],
        "nominal_geometry_sha256": digest(metrics),
        "witness_plan_sha256": witness["plan_sha256"],
        "region_count": len(regions),
        "distinct_source_shapes": len(source_shapes),
        "interface_count": len(interfaces),
        "independent_witness_candidates": len(routes),
        "selected_service_scopes": included,
        "service_scope_not_empirically_modelled": True,
        "nominal_sum_volume_mm3_exact": metrics["nominal_sum_volume_mm3_exact"],
        "physical_union_volume_mm3": None,
        "mass_and_density": None,
        "layers": layers,
        "reverse_replay_order": list(reversed(STAGE_ORDER)),
        "hold_codes": list(HOLD_REASONS) + (
            ["PROCESS_PACKET_NOT_BOUND"] if process_result is None else ["PROCESS_DECLARATIONS_NOT_INDEPENDENTLY_ATTESTED"]
        ),
        "digital_reference_checks": True,
        "real_source_body_authenticated": False,
        "physically_qualified": False,
        "native_dbr_written": False,
        "machine_authorised": False,
        "mint_authorised": False,
        "commercial_release_authorised": False,
        "load_mode": "H0_NONHYDRATING",
    }
    envelope["manifest_sha256"] = digest(envelope)
    return envelope


def verify_digital_service_stack_backwards(bundle: Any, manufacturing_ir: Any,
                                           geometry_request: Any, interface_selections: Any,
                                           process_packet: Any = None) -> dict:
    """Recompile original inputs, then verify every stage in REVERSE dependency order.

    Not a proof of external source authenticity or measured physics. No
    witness claims can be accepted merely because a self-hashed bundle exists.
    """
    expected = compile_digital_service_stack(
        manufacturing_ir, geometry_request, interface_selections, process_packet
    )
    if not isinstance(bundle, dict) or expected["state"] != "DIGITAL_STACK_REVIEW_ONLY_PHYSICAL_HOLD":
        return {"schema": BACKTRACE_SCHEMA, "state": "HOLD", "mismatch_layers": list(STAGE_ORDER),
                "reason": "INPUT_OR_BUNDLE_NOT_REPLAYABLE",
                "machine_authorised": False, "evidence_verified": False}
    if not isinstance(bundle.get("layers"), list):
        return {"schema": BACKTRACE_SCHEMA, "state": "HOLD", "mismatch_layers": list(STAGE_ORDER),
                "reason": "MISSING_SERVICE_LAYERS",
                "machine_authorised": False, "evidence_verified": False}
    given = {x.get("id"): x for x in bundle["layers"] if isinstance(x, dict) and isinstance(x.get("id"), str)}
    if len(given) != len(STAGE_ORDER) or len(bundle["layers"]) != len(STAGE_ORDER):
        mismatch = list(STAGE_ORDER)
    else:
        expected_by_id = {x["id"]: x for x in expected["layers"]}
        mismatch = [
            name for name in reversed(STAGE_ORDER)
            if given.get(name) != expected_by_id[name]
        ]
    # The original exact input manifest is also required: any extra, removed,
    # reordered or authority-escalation field makes strict comparison fail.
    top_level_match = bundle == expected
    return {
        "schema": BACKTRACE_SCHEMA,
        "state": "PASS_DIGITAL_ONLY" if not mismatch and top_level_match else "HOLD",
        "mismatch_layers": mismatch,
        "source_replay_manifest_sha256": expected["manifest_sha256"],
        "declared_manifest_sha256": bundle.get("manifest_sha256"),
        "manifest_matched": top_level_match,
        "reverse_order": list(reversed(STAGE_ORDER)),
        "external_source_bodies_or_rights_authenticated": False,
        "physical_measurements_verified": False,
        "machine_authorised": False,
        "native_dbr_written": False,
        "mint_authorised": False,
        "commercial_release_authorised": False,
    }
