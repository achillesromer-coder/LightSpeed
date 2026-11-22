"""Bounded PrintSpace process review gate OVER the canonical CGX manufacturing IR.

This compiler neither reads a machine nor trusts input receipts as external proof.
Review success is never a manufacturing, certification, mint or release authority.
The canonical cgx.manufacturing compiler is not replaced by this overlay.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

SCHEMA = "CGX-PRINTSPACE-REVIEW-INPUT/0.1"
OPERATIONS = frozenset({"PREPARE", "DEPOSIT", "PAUSE", "CLEAN", "PURGE", "DRY", "CURE", "INSPECT", "PLACE_COMPONENT", "BOND", "ENCAPSULATE", "ACTIVATE", "VERIFY", "READBACK"})
ATMOSPHERES = frozenset({"AMBIENT", "CONTROLLED_GAS", "DRY", "VACUUM", "PRESSURE"})
TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,79}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")


def _id(x: Any) -> bool:
    return isinstance(x, str) and bool(TOKEN.fullmatch(x))


def _text(x: Any) -> bool:
    return isinstance(x, str) and bool(x.strip()) and len(x) <= 1024


def _number(x: Any, *, positive: bool = False) -> bool:
    return type(x) in (int, float) and math.isfinite(x) and (x > 0 if positive else x >= 0)


def _graph(operations: list[dict], report) -> tuple[list[dict], dict[str, set[str]]]:
    by_id: dict[str, dict] = {}
    for index, item in enumerate(operations):
        if not isinstance(item, dict) or not _id(item.get("id")):
            report("INVALID_OPERATION", f"operations[{index}]", "Missing or invalid operation ID")
            continue
        key = item["id"]
        if key in by_id:
            report("DUPLICATE_OPERATION", key, "Operation IDs must be unique")
        else:
            by_id[key] = item
    dependencies: dict[str, set[str]] = {}
    children = {k: set() for k in by_id}
    for key, item in by_id.items():
        deps = item.get("depends_on", [])
        if not isinstance(deps, list) or any(not _id(d) for d in deps) or len(set(deps)) != len(deps):
            report("INVALID_DEPENDENCY", key, "Dependencies must be unique operation IDs")
            deps = []
        dependencies[key] = set()
        for d in deps:
            if d not in by_id or d == key:
                report("UNKNOWN_DEPENDENCY", key, f"Invalid predecessor: {d}")
            else:
                dependencies[key].add(d)
                children[d].add(key)
    indegree = {k: len(v) for k, v in dependencies.items()}
    ready = sorted(k for k, n in indegree.items() if n == 0)
    result: list[dict] = []
    while ready:
        key = ready.pop(0)
        result.append(by_id[key])
        for child in sorted(children[key]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
                ready.sort()
    if len(result) != len(by_id):
        report("CYCLIC_PROCESS", "operations", "Dependency cycle prevents topological scheduling")
        return [], {}
    memo: dict[str, set[str]] = {}
    for key in by_id:
        memo[key] = set()  # computed below using acyclic topological ordering
    for item in result:
        key = item["id"]
        memo[key] = set(dependencies[key])
        for parent in dependencies[key]:
            memo[key].update(memo[parent])
    return result, memo


def compile_review(packet: dict) -> dict:
    """Return a stable, read-only plan. No external evidence or rights are verified."""
    if not isinstance(packet, dict):
        raise TypeError("Input must be a JSON object")
    try:
        canonical_input = json.dumps(packet, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError):
        return {"schema": "CGX-PRINTSPACE-REVIEW-RESULT/0.1", "input_sha256": None,
                "article_id": None, "manufacturing_ir_ref": None, "state": "HOLD", "ordered_operations": [],
                "findings": [{"code": "NONCANONICAL_INPUT", "subject": "input", "detail": "Only finite, serialisable JSON input is accepted"}],
                "evidence_status": "DECLARED_NOT_INDEPENDENTLY_VERIFIED",
                "physical_machine_authorised": False, "mint_authorised": False,
                "commercial_release_authorised": False}
    fingerprint = hashlib.sha256(canonical_input.encode()).hexdigest()
    findings: list[dict[str, str]] = []
    def hold(code: str, subject: str, detail: str) -> None:
        finding = {"code": code, "subject": subject, "detail": detail}
        if finding not in findings:
            findings.append(finding)
    if packet.get("schema") != SCHEMA:
        hold("SCHEMA_MISMATCH", "schema", "Unsupported input schema")
    ir_ref = packet.get("manufacturing_ir_ref")
    if not _text(ir_ref) or not ir_ref.startswith("cgx://manufacturing/build/"):
        hold("CANONICAL_IR_REFERENCE", "manufacturing_ir_ref", "Existing CGX manufacturing IR build URI required")
    if not _id(packet.get("article_id")):
        hold("ARTICLE_ID", "article_id", "Stable article ID required")
    if not _text(packet.get("source_revision")):
        hold("SOURCE_REVISION", "source_revision", "Bind to an exact authority source revision")

    geometry = packet.get("geometry") if isinstance(packet.get("geometry"), dict) else {}
    pos = geometry.get("catalogue_position")
    if type(pos) is not int or not 1 <= pos <= 173:
        hold("GEOMETRY_NOT_ADMITTED", "geometry.catalogue_position", "Only numbered T173 candidates 1-173; 174 reserved")
    for field in ("source_id", "units", "coordinate_frame", "admission_receipt", "rights_ref"):
        if not _text(geometry.get(field)):
            hold("GEOMETRY_SOURCE", "geometry." + field, "Geometry needs traceable exact-source metadata")
    if not isinstance(geometry.get("sha256"), str) or not DIGEST.fullmatch(geometry["sha256"]):
        hold("GEOMETRY_HASH", "geometry.sha256", "64-digit lowercase SHA256 required")
    if not _number(geometry.get("minimum_feature_mm"), positive=True):
        hold("GEOMETRY_FEATURE", "geometry.minimum_feature_mm", "Positive feature size required")

    rights = packet.get("rights") if isinstance(packet.get("rights"), dict) else {}
    if rights.get("status") not in ("CLEARED", "RESTRICTED", "UNKNOWN"):
        hold("RIGHTS_STATUS", "rights", "Rights status must be explicit")
    if rights.get("status") != "CLEARED" and (packet.get("publication_requested") or packet.get("commercial_release_requested")):
        hold("RIGHTS_BLOCK", "rights", "No publication or sale without cleared rights")
    if not _text(rights.get("licence_ref")):
        hold("RIGHTS_PROVENANCE", "rights.licence_ref", "Rights reference required even for private work")

    machine = packet.get("machine") if isinstance(packet.get("machine"), dict) else {}
    if machine.get("safety_control") != "INDEPENDENT_C0":
        hold("C0_NOT_INDEPENDENT", "machine.safety_control", "Independent C0 must be specified")
    if machine.get("physical_state") not in ("NOT_BUILT", "UNQUALIFIED", "BUILT", "QUALIFIED"):
        hold("MACHINE_STATE", "machine.physical_state", "Explicit physical state required")
    tools = machine.get("tool_ids")
    if not isinstance(tools, list) or any(not _id(t) for t in tools) or len(tools) != len(set(tools)):
        hold("MACHINE_TOOLS", "machine.tool_ids", "Exact tool IDs required")
        tools = []
    if machine.get("initial_atmosphere") not in ATMOSPHERES:
        hold("INITIAL_ATMOSPHERE", "machine.initial_atmosphere", "Explicit initial environment required")
    if not _number(machine.get("minimum_feature_mm"), positive=True):
        hold("MACHINE_RESOLUTION", "machine.minimum_feature_mm", "Calibrated or specified minimum feature required")
    elif _number(geometry.get("minimum_feature_mm"), positive=True) and geometry["minimum_feature_mm"] < machine["minimum_feature_mm"]:
        hold("RESOLUTION_EXCEEDED", "geometry", "Requested feature below machine stated minimum")

    lots = packet.get("material_lots")
    if not isinstance(lots, dict):
        hold("MATERIAL_LOTS", "material_lots", "Material lot dictionary required")
        lots = {}
    for lid, lot in lots.items():
        if not _id(lid) or not isinstance(lot, dict) or not _text(lot.get("passport_ref")):
            hold("MATERIAL_PASSPORT", str(lid), "Lot identity and material passport required")
    edges = packet.get("interfaces")
    if not isinstance(edges, list):
        hold("INTERFACE_LIST", "interfaces", "Directed interfaces must be an array")
        edges = []
    edge_by_id: dict[str, dict] = {}
    for e in edges:
        if not isinstance(e, dict) or not _id(e.get("id")):
            hold("INTERFACE_ID", "interfaces", "Invalid interface record")
            continue
        eid = e["id"]
        if eid in edge_by_id:
            hold("DUPLICATE_INTERFACE", eid, "Duplicate interface ID")
        else:
            edge_by_id[eid] = e
        if (not isinstance(e.get("predecessor_lot"), str) or e["predecessor_lot"] not in lots
                or not isinstance(e.get("successor_lot"), str) or e["successor_lot"] not in lots):
            hold("INTERFACE_LOT", eid, "Interface lots must be declared")
        if e.get("status") != "QUALIFIED" or not _text(e.get("evidence_ref")) or not _text(e.get("process_revision")):
            hold("INTERFACE_UNQUALIFIED", eid, "Only an explicitly receipt-bound directed edge may enter the review route")

    ops = packet.get("operations")
    if not isinstance(ops, list) or len(ops) > 512:
        hold("OPERATIONS_INVALID", "operations", "Expected at most 512 operations")
        ops = []
    if not ops:
        hold("EMPTY_PROCESS", "operations", "At least one review operation required")
    ordered, ancestors = _graph(ops, hold)
    by_id = {op["id"]: op for op in ordered}
    atmosphere_out: dict[str, str | None] = {}
    for op in ordered:
        key, kind = op["id"], op.get("kind")
        deps = [d for d in op.get("depends_on", []) if d in atmosphere_out] if isinstance(op.get("depends_on", []), list) else []
        incoming_states = {atmosphere_out[d] for d in deps} if deps else {machine.get("initial_atmosphere")}
        if len(incoming_states) != 1 or None in incoming_states:
            hold("AMBIGUOUS_ATMOSPHERE", key, "Branches entering an operation disagree on environmental state")
            atmosphere_in = None
        else:
            atmosphere_in = next(iter(incoming_states))
        atmosphere_out[key] = op.get("target_atmosphere") if kind == "PURGE" and op.get("target_atmosphere") in ATMOSPHERES else atmosphere_in
        if not isinstance(kind, str) or kind not in OPERATIONS:
            hold("UNKNOWN_OPERATION", key, "Unsupported operation kind")
            continue
        if kind in ("DEPOSIT", "CURE", "PLACE_COMPONENT", "BOND") and op.get("tool_id") not in tools:
            hold("UNAVAILABLE_TOOL", key, "Tool is absent from machine capability declaration")
        if kind == "DEPOSIT":
            lot = op.get("material_lot_id")
            if not isinstance(lot, str) or lot not in lots:
                hold("UNBOUND_MATERIAL", key, "Deposit lot is unknown")
            predecessor = op.get("on_material_lot_id")
            if predecessor is not None:
                interface_ref = op.get("interface_id")
                edge = edge_by_id.get(interface_ref) if isinstance(interface_ref, str) else None
                if edge is None or edge.get("predecessor_lot") != predecessor or edge.get("successor_lot") != lot:
                    hold("DIRECTIONAL_INTERFACE", key, "Exact predecessor\u2192successor interface required; reverse is independent")
                on_id = op.get("on_operation_id")
                actual_parent = by_id.get(on_id) if isinstance(on_id, str) else None
                if (not actual_parent or actual_parent.get("kind") != "DEPOSIT"
                        or actual_parent.get("material_lot_id") != predecessor
                        or on_id not in ancestors.get(key, ())):
                    hold("PREDECESSOR_NOT_DEPOSITED", key, "Exact source deposition operation and dependency required")
            g = op.get("gradient")
            if g is not None:
                if not isinstance(g, dict) or any(not _text(g.get(field)) for field in ("composition_law_ref", "spatial_field_ref", "coupon_receipt")) or not _number(g.get("minimum_feature_mm"), positive=True):
                    hold("GRADIENT_UNQUALIFIED", key, "Spatial law, mixing coupon and minimum feature required")
                elif _number(machine.get("minimum_feature_mm"), positive=True) and g["minimum_feature_mm"] < machine["minimum_feature_mm"]:
                    hold("GRADIENT_RESOLUTION", key, "Gradient sub-feature below machine minimum")
        if kind == "PURGE":
            mode = op.get("target_atmosphere")
            if mode not in ATMOSPHERES or any(not _text(op.get(f)) for f in ("sensor_calibration_ref", "transition_receipt")):
                hold("ATMOSPHERE_TRANSITION", key, "Explicit mode, calibration and receipt required")
            if mode == "CONTROLLED_GAS":
                if not _number(op.get("measured_o2_ppm")) or not _number(op.get("maximum_o2_ppm")) or op["measured_o2_ppm"] > op["maximum_o2_ppm"]:
                    hold("OXYGEN_BUDGET", key, "Measured oxygen must satisfy source-bound limit")
            if mode in ("VACUUM", "PRESSURE") and not _text(op.get("chamber_rating_ref")):
                hold("UNRATED_CHAMBER", key, "Vacuum/pressure requires a documented rated chamber")
        if kind == "DEPOSIT":
            desired = op.get("required_atmosphere", "AMBIENT")
            if not isinstance(desired, str) or desired not in ATMOSPHERES or desired != atmosphere_in:
                hold("MISSING_ATMOSPHERE", key, "Effective environment at deposition differs from required state")
        if kind == "ENCAPSULATE":
            if not _text(op.get("barrier_ref")):
                hold("ENCAPSULATION_BARRIER", key, "Barrier source required")
            post_id = op.get("post_seal_test_id")
            post = by_id.get(post_id) if isinstance(post_id, str) else None
            if not post or post.get("kind") != "VERIFY" or post.get("test_type") != "POST_SEAL" or key not in ancestors.get(post["id"], set()) or not _text(post.get("evidence_ref")):
                hold("POST_SEAL_TEST", key, "An explicit dependent post-seal verification is required")
        if kind == "ACTIVATE" and op.get("stimulus") == "EM":
            field = op.get("field")
            if not isinstance(field, dict) or any(not _number(field.get(f), positive=True) for f in ("frequency_hz", "bandwidth_hz", "power_w", "exposure_s")) or any(not _text(field.get(f)) for f in ("calibration_ref", "safety_envelope_ref")):
                hold("EM_DOSE_UNBOUND", key, "Frequency, bandwidth, power, exposure and safety evidence required")
            elif field["bandwidth_hz"] > field["frequency_hz"] * 2:
                hold("EM_BANDWIDTH", key, "Unbounded bandwidth in activation design")
    return {
        "schema": "CGX-PRINTSPACE-REVIEW-RESULT/0.1",
        "input_sha256": fingerprint,
        "article_id": packet.get("article_id") if _id(packet.get("article_id")) else None,
        "manufacturing_ir_ref": ir_ref if _text(ir_ref) and ir_ref.startswith("cgx://manufacturing/build/") else None,
        "state": "HOLD" if findings else "REVIEW_ONLY",
        "ordered_operations": [x["id"] for x in ordered],
        "findings": sorted(findings, key=lambda x: (x["code"], x["subject"], x["detail"])),
        "evidence_status": "DECLARED_NOT_INDEPENDENTLY_VERIFIED",
        "physical_machine_authorised": False,
        "mint_authorised": False,
        "commercial_release_authorised": False,
    }


def main() -> int:
    import argparse
    from pathlib import Path
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path)
    args = p.parse_args()
    doc = json.loads(args.input.read_text(encoding="utf-8"))
    print(json.dumps(compile_review(doc), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

def review_existing_manufacturing_ir(manufacturing_ir: dict, packet: dict, *, geometry_composition: dict | None = None) -> dict:
    """Bind the read-only PrintSpace preflight to one *actual* canonical CGX IR.

    The standalone compile_review() is useful for proposed processes; this entry
    point additionally checks the existing component compiler's exact URI,
    configuration SHA256 and unresolved instance gates. It is NOT a verified
    material, geometry, tool, lease, source signature or production receipt.
    """
    from .compiler import SCHEMA as CANONICAL_IR_SCHEMA, _canonical_hash

    result = compile_review(packet)
    findings = list(result["findings"])

    def hold(code: str, subject: str, detail: str) -> None:
        finding = {"code": code, "subject": subject, "detail": detail}
        if finding not in findings:
            findings.append(finding)

    result["binding_proof"] = {
        "state": "DECLARATIONS_AND_LOCAL_HASH_ONLY",
        "trusted_external_receipt": False,
        "canonical_ir_hash_matched": False,
        "canonical_ir_uri_matched": False,
        "real_instance_evidence_verified": False,
    }
    if not isinstance(manufacturing_ir, dict):
        hold("CANONICAL_IR_MISSING", "manufacturing_ir", "Actual canonical manufacturing IR object required")
    else:
        uri = manufacturing_ir.get("cgx_uri")
        raw_hash = manufacturing_ir.get("configuration_hash")
        if manufacturing_ir.get("schema") != CANONICAL_IR_SCHEMA:
            hold("CANONICAL_IR_SCHEMA", "manufacturing_ir.schema", "Unexpected canonical IR schema")
        if not isinstance(uri, str) or packet.get("manufacturing_ir_ref") != uri:
            hold("CANONICAL_IR_URI_MISMATCH", "manufacturing_ir.cgx_uri", "Review must reference the exact emitted CGX build URI")
        else:
            result["binding_proof"]["canonical_ir_uri_matched"] = True
        if (not isinstance(raw_hash, str) or not DIGEST.fullmatch(raw_hash)):
            hold("CANONICAL_IR_HASH_MISSING", "manufacturing_ir.configuration_hash", "Exact canonical configuration hash required")
        else:
            try:
                computed = _canonical_hash({key: value for key, value in manufacturing_ir.items() if key != "configuration_hash"})
            except (ValueError, TypeError):
                computed = None
            if computed != raw_hash or packet.get("manufacturing_ir_configuration_hash") != raw_hash:
                hold("CANONICAL_IR_HASH_MISMATCH", "manufacturing_ir.configuration_hash", "Recompute canonical IR and match exact frozen review input")
            else:
                result["binding_proof"]["canonical_ir_hash_matched"] = True
        if manufacturing_ir.get("physical_execution") is not False:
            hold("CANONICAL_IR_EXECUTION", "manufacturing_ir.physical_execution", "Canonical machine-neutral IR must not execute hardware")
        operations = manufacturing_ir.get("operations")
        if not isinstance(operations, list) or any(not isinstance(op, dict) or op.get("physical_execution") is not False for op in operations):
            hold("CANONICAL_IR_OPERATION_EXECUTION", "manufacturing_ir.operations", "All canonical operation nodes must remain non-executing")
        if not isinstance(manufacturing_ir.get("instance_ref"), str) or not manufacturing_ir["instance_ref"]:
            hold("EXACT_CGXI_UNBOUND", "manufacturing_ir.instance_ref", "Canonical instance identity missing")
        if manufacturing_ir.get("binding_progress") != "BUILD_READY" or manufacturing_ir.get("execution_state") != "BUILD_READY":
            hold("CANONICAL_INSTANCE_NOT_READY", "manufacturing_ir.binding_progress", "Existing manufacturing compiler has not closed exact-instance gates")
        blockers = manufacturing_ir.get("blockers")
        if not isinstance(blockers, list) or blockers:
            hold("CANONICAL_IR_BLOCKERS", "manufacturing_ir.blockers", "Canonical IR has unresolved consequential blockers")
        if manufacturing_ir.get("compile_state") != "DIGITAL_PLAN":
            hold("CANONICAL_IR_COMPILE_STATE", "manufacturing_ir.compile_state", "Unexpected canonical digital state")

    # Same canonical build hash anchors both process and geometry. No new
    # compiler/master/LOAD source, and no geometry check grants physical proof.
    if geometry_composition is not None:
        from .composition import compile_geometry_composition
        geometry = compile_geometry_composition(geometry_composition)
        result["geometry_projection"] = {
            "state": geometry["state"],
            "graph_sha256": geometry.get("geometry_composite_hash"),
            "load_h0": geometry.get("load_h0"),
            "hold_codes": geometry["hold_codes"],
            "source_and_material_evidence_verified": False,
            "native_load_admitted": False,
        }
        if geometry["state"] != "REVIEW_ONLY":
            hold("GEOMETRY_COMPOSITION_HOLD", "geometry_composition", "Exact geometry review has unresolved source or topology gates")
        geo_ref = geometry_composition.get("manufacturing_ir_ref") if isinstance(geometry_composition, dict) else None
        geo_hash = geometry_composition.get("manufacturing_ir_configuration_hash") if isinstance(geometry_composition, dict) else None
        if (not isinstance(manufacturing_ir, dict) or
            geo_ref != manufacturing_ir.get("cgx_uri")):
            hold("GEOMETRY_IR_URI_MISMATCH", "geometry_composition.manufacturing_ir_ref", "Geometry must match this exact existing CGX build URI")
        if (not isinstance(manufacturing_ir, dict) or
            geo_hash != manufacturing_ir.get("configuration_hash")):
            hold("GEOMETRY_IR_HASH_MISMATCH", "geometry_composition.manufacturing_ir_configuration_hash", "Geometry must bind to exact canonical IR configuration hash")
    result["findings"] = sorted(findings, key=lambda x: (x["code"], x["subject"], x["detail"]))
    result["state"] = "HOLD" if findings else "REVIEW_ONLY"
    result["physical_machine_authorised"] = False
    result["mint_authorised"] = False
    result["commercial_release_authorised"] = False
    return result
