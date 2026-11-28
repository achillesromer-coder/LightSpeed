"""Source-index-bound directional interface coupon plans for CGX PrintSpace.

This module consumes the EXISTING canonical geometry composition, immutable
411-row Drive fingerprint projection, and existing manufacturing build identity.
It does not maintain a material database, qualify a lot or tool, re-read Drive,
issue a DBR/rights decision, activate LOAD, or perform physical operations.

An exact convex shared face is a geometric fact for supplied integer geometry.
It is NOT evidence of adhesion, conductivity, bond strength, chemical
compatibility, atmospheric safety, process feasibility, or 4D behaviour.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .composition import digest as geometry_digest

SCHEMA = "CGX-PRINTSPACE-INTERFACE-WITNESS-PLAN/0.1"
RESULT_SCHEMA = "CGX-PRINTSPACE-INTERFACE-WITNESS-REVIEW/0.1"
INDEX_SCHEMA = "CGX-PRINTSPACE-OWNER-MATRIX-PROJECTION/0.1"
MAX_BYTES = 64 * 1024
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
ID = re.compile(r"[A-Za-z][A-Za-z0-9._-]{0,63}\Z")
INDEX_PATH = Path(__file__).with_name("printspace_owner_matrix_projection_v0_1.json")

EVIDENCE_REQUIREMENTS = (
    "OBSERVED_MATERIAL_LOT_PASSPORT_AND_STORAGE",
    "EXACT_DEPOSITION_PROCESS_REVISION",
    "INDEPENDENT_C0_MACHINE_AND_TOOL_CALIBRATION",
    "CONTROLLED_SURFACE_PREPARATION_AND_ATMOSPHERE_HISTORY",
    "CURE_TEMPERATURE_PRESSURE_AND_FIELD_HISTORY",
    "METHOD_FIXTURE_UNCERTAINTY_AND_ACCEPTANCE_CRITERIA",
    "SOURCE_AND_CONTROL_SPECIMEN_IDENTITIES",
    "RAW_WITNESS_RESULTS_AND_INDEPENDENT_REVIEW",
    "SIGNED_OWNER_DBR_RIGHTS_AND_REPRODUCTION_READBACK",
)


def _valid_sha(v: Any) -> bool:
    return isinstance(v, str) and SHA256.fullmatch(v) is not None


def _valid_id(v: Any) -> bool:
    return isinstance(v, str) and ID.fullmatch(v) is not None


def _fingerprint(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=True, sort_keys=True,
                                     separators=(",", ":"), allow_nan=False).encode("ascii")).hexdigest()


def _hold(code: str) -> dict[str, Any]:
    return {
        "schema": RESULT_SCHEMA,
        "state": "HOLD",
        "hold_codes": [code],
        "plan_sha256": None,
        "plan": None,
        "material_interface_qualified": False,
        "evidence_independently_verified": False,
        "machine_authorised": False,
        "native_dbr_written": False,
        "mint_authorised": False,
        "commercial_release_authorised": False,
    }


def plan_interface_witnesses(composition: Any, selections: Any) -> dict[str, Any]:
    """Create independent directional witness requirements, never test results.

    The selections must map exactly one 411-row planning fingerprint per
    composite instance. Those rows do not identify a chemical formulation, a
    bought material lot or a validated directional process. A→B and B→A each
    get their own coupon identity and evidence ledger entry.
    """
    if not isinstance(selections, dict) or not isinstance(composition, dict):
        return _hold("INVALID_PLAN_REQUEST")
    try:
        raw = json.dumps(selections, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False).encode("ascii")
    except (ValueError, TypeError, RecursionError, OverflowError):
        return _hold("NONCANONICAL_PLAN_REQUEST")
    if len(raw) > MAX_BYTES:
        return _hold("PLAN_INPUT_BUDGET")
    if selections.get("schema") != SCHEMA:
        return _hold("PLAN_SCHEMA")
    graph = composition.get("graph")
    if (composition.get("state") != "REVIEW_ONLY" or
        composition.get("machine_authorised") is not False or
        composition.get("mint_authorised") is not False or
        not isinstance(graph, dict) or
        not _valid_sha(composition.get("geometry_composite_hash"))):
        return _hold("GEOMETRY_NOT_REVIEWED")
    if geometry_digest(graph) != composition["geometry_composite_hash"]:
        return _hold("ALTERED_GEOMETRY_GRAPH")
    h0 = composition.get("load_h0")
    if (not isinstance(h0, dict) or h0.get("alias") != "LOAD.cgx"
        or h0.get("native_admitted") is not False or
        h0.get("source_bytes_hydrated") != 0 or
        h0.get("composite_sha256") != composition["geometry_composite_hash"]):
        return _hold("LOAD_H0_NOT_SOURCE_ONLY")
    if selections.get("geometry_composite_hash") != composition["geometry_composite_hash"]:
        return _hold("GEOMETRY_HASH_MISMATCH")
    if selections.get("manufacturing_ir_ref") != graph.get("manufacturing_ir_ref"):
        return _hold("CANONICAL_BUILD_MISMATCH")
    if not _valid_sha(selections.get("manufacturing_ir_configuration_hash")):
        return _hold("CANONICAL_BUILD_HASH_UNBOUND")
    if selections.get("source_scope") != "OWNER_MATRIX_PLANNING_CLASS_ONLY":
        return _hold("MATERIAL_SOURCE_CLAIM_ESCALATION")
    if selections.get("source_revision") != "2026-11-22":
        return _hold("SOURCE_REVISION_NOT_SNAPSHOT")
    if selections.get("evidence_state") != "UNMEASURED":
        return _hold("UNTRUSTED_MEASURED_EVIDENCE")
    for forbidden in ("physical_approval", "authorised", "lot_passports", "signed_dbr",
                      "source_bytes", "receipt", "machine_command", "native_load_lease"):
        if forbidden in selections:
            return _hold("UNAUTHORISED_EVIDENCE_OR_EXECUTION_INPUT")

    try:
        index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _hold("OWNER_MATRIX_INDEX_UNAVAILABLE")
    if (not isinstance(index, dict) or index.get("schema") != INDEX_SCHEMA
        or index.get("status") != "READ_ONLY_FINGERPRINT_INDEX / NO_ENGINEERING_EVIDENCE_PROMOTION"
        or not isinstance(index.get("row_fingerprints"), list)
        or len(index["row_fingerprints"]) != 411
        or not _valid_sha(index.get("projection_sha256"))
        or selections.get("owner_projection_sha256") != index["projection_sha256"]):
        return _hold("OWNER_MATRIX_PROJECTION_MISMATCH")
    records = index["row_fingerprints"]
    digest_rows = [[v.get("sheet_row"), v.get("matrix_id"),
                    v.get("archetype_id"), v.get("directional_sha256")]
                   for v in records if isinstance(v, dict)]
    if len(digest_rows) != 411 or _fingerprint(digest_rows) != index["projection_sha256"]:
        return _hold("OWNER_MATRIX_INDEX_INTEGRITY")
    row_index = {row.get("matrix_id"): row for row in records}
    if len(row_index) != 411:
        return _hold("DUPLICATE_OWNER_MATRIX_ID")

    instances = graph.get("instances")
    edges = graph.get("interfaces")
    if (not isinstance(instances, list) or not 1 <= len(instances) <= 24
        or not isinstance(edges, list) or len(edges) > 64):
        return _hold("GEOMETRY_GRAPH_SHAPE")
    by_instance = {}
    for instance in instances:
        if (not isinstance(instance, dict) or not _valid_id(instance.get("instance_id"))
            or not _valid_id(instance.get("material_slot"))
            or instance["instance_id"] in by_instance):
            return _hold("GEOMETRY_INSTANCE_ID")
        by_instance[instance["instance_id"]] = instance

    chosen = selections.get("region_selections")
    if not isinstance(chosen, list) or len(chosen) != len(by_instance):
        return _hold("UNBOUND_REGION_SELECTION")
    region_map = {}
    for selection in chosen:
        if not isinstance(selection, dict):
            return _hold("REGION_SELECTION_SHAPE")
        if set(selection) != {"instance_id", "material_slot", "matrix_id", "archetype_id", "directional_sha256"}:
            return _hold("UNEXPECTED_MATERIAL_DECLARATION")
        iid = selection.get("instance_id")
        if not _valid_id(iid) or iid not in by_instance or iid in region_map:
            return _hold("DUPLICATE_OR_UNKNOWN_REGION")
        if selection.get("material_slot") != by_instance[iid]["material_slot"]:
            return _hold("MATERIAL_SLOT_MISMATCH")
        owner_row = row_index.get(selection.get("matrix_id"))
        if (not isinstance(owner_row, dict) or
            owner_row.get("archetype_id") != selection.get("archetype_id") or
            owner_row.get("directional_sha256") != selection.get("directional_sha256")):
            return _hold("OWNER_ROW_FINGERPRINT_MISMATCH")
        region_map[iid] = {
            "instance_id": iid, "material_slot": selection["material_slot"],
            "matrix_id": owner_row["matrix_id"],
            "archetype_id": owner_row["archetype_id"],
            "directional_sha256": owner_row["directional_sha256"],
            "planning_basis_class": owner_row["primitive_basis"],
            "original_drive_cells": owner_row["source_cell_range"],
            "lot_passport": "UNBOUND_NO_OBSERVED_LOT",
            "material_compatibility": "NOT_VERIFIED",
        }
    if set(region_map) != set(by_instance):
        return _hold("INCOMPLETE_REGION_COVERAGE")

    if not edges and len(by_instance) > 1:
        return _hold("NO_INTERFACE_EDGES")
    coupon_ids = set()
    planned = []
    directed_seen = set()
    for e in edges:
        if not isinstance(e, dict):
            return _hold("INVALID_INTERFACE_GRAPH")
        src, dst = e.get("from"), e.get("to")
        if not isinstance(src, str) or not isinstance(dst, str) or src not in region_map or dst not in region_map or src == dst:
            return _hold("INTERFACE_ENDPOINT_MISMATCH")
        if (src, dst) in directed_seen:
            return _hold("DUPLICATE_INTERFACE_EDGE")
        directed_seen.add((src, dst))
        contact = e.get("exact_convex_contact")
        if (not isinstance(contact, dict)
            or contact.get("material_interface_qualified") is not False
            or contact.get("boolean_mesh_emitted") is not False
            or e.get("physical_compatibility") != "NOT_VERIFIED"
            or e.get("evidence_state") not in ("UNTESTED", "PROPOSED")):
            return _hold("FALSE_INTERFACE_QUALIFICATION")
        if e.get("kind") in ("CONTACT_CANDIDATE", "INTERLAYER") and contact.get("relation") != "FACE_CONTACT":
            return _hold("NO_FINITE_INTERFACE_FACE")
        if contact.get("relation") == "VOLUME_OVERLAP":
            return _hold("INTERPENETRATING_REGION")
        area = contact.get("face_area_mm2_exact")
        if not isinstance(area, str) or not area.strip() or contact.get("relation") != "FACE_CONTACT":
            return _hold("FACE_AREA_NOT_EXACT")
        routes = []
        for a, b, role in ((src, dst, "SOURCE_TO_TARGET"),
                            (dst, src, "TARGET_TO_SOURCE")):
            token = _fingerprint([composition["geometry_composite_hash"], src, dst, a, b, role])
            coupon_id = "CGX-WITNESS-" + token[:20].upper()
            if coupon_id in coupon_ids:
                return _hold("COUPON_ID_COLLISION")
            coupon_ids.add(coupon_id)
            routes.append({
                "direction": role,
                "source_instance": a, "target_instance": b,
                "source_matrix_id": region_map[a]["matrix_id"],
                "target_matrix_id": region_map[b]["matrix_id"],
                "coupon_candidate_id": coupon_id,
                "target_geometric_face_area_mm2_exact": area,
                "observed_lots": None, "tool_calibration": None,
                "process_revision": None, "environment_cure_history": None,
                "control_specimens": None, "witness_method": None,
                "raw_measurement_receipt": None,
                "verification": "UNMEASURED_NOT_QUALIFIED",
                "required_evidence": list(EVIDENCE_REQUIREMENTS),
            })
        planned.append({
            "interface_from": src, "interface_to": dst,
            "geometry_relation": "FACE_CONTACT",
            "geometric_area_mm2_exact": area,
            "directions": routes,
            "bidirectional_material_compatibility": "NOT_VERIFIED",
            "measurement_authority": "NO_HOST_OR_OWNER_WITNESS_READBACK",
        })
    planned.sort(key=lambda x: (x["interface_from"], x["interface_to"]))
    plan = {
        "schema": RESULT_SCHEMA, "source_revision": index["observed_date"],
        "owner_sheet": index["source"]["sheet"],
        "owner_projection_sha256": index["projection_sha256"],
        "source_status": "OBSERVED_SNAPSHOT_NOT_LIVE_DRIVE_ATTESTATION",
        "manufacturing_ir_ref": graph["manufacturing_ir_ref"],
        "manufacturing_ir_configuration_hash": selections["manufacturing_ir_configuration_hash"],
        "geometry_composite_sha256": composition["geometry_composite_hash"],
        "source_regions": [region_map[k] for k in sorted(region_map)],
        "interfaces": planned,
        "independent_material_evidence": False,
        "rights_and_qualification": "PENDING_OWNER_AND_ACTUAL_COUPONS",
        "load_hydration": "H0_REFERENCE_ONLY",
        "device_state": "NO_PHYSICAL_EXECUTION",
    }
    return {
        "schema": RESULT_SCHEMA,
        "state": "PLAN_READY_UNQUALIFIED",
        "hold_codes": [
            "EXACT_MATERIAL_LOTS_NOT_BOUND",
            "REVERSE_DIRECTION_COUPONS_NOT_MEASURED",
            "INDEPENDENT_TOOL_AND_METHOD_CALIBRATION_MISSING",
            "PARENT_DBR_RIGHTS_AND_EVIDENCE_NOT_VERIFIED",
        ],
        "plan_sha256": _fingerprint(plan),
        "plan": plan,
        "material_interface_qualified": False,
        "evidence_independently_verified": False,
        "machine_authorised": False,
        "native_dbr_written": False,
        "mint_authorised": False,
        "commercial_release_authorised": False,
    }
