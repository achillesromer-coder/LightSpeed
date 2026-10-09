from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .compiler import (
    _instance_binding_progress,
    _looks_unresolved_instance_value,
    find_instance,
    load_default_instance_population,
)

SCHEMA = "CGX-EXACT-BINDING-RESOLUTION/0.1"
LOT_SCHEMA = "CGX-LOT-PASSPORT/0.1"
TOOL_SCHEMA = "CGX-TOOL-CAPABILITY/0.1"
COUPON_SCHEMA = "CGX-WITNESS-COUPON-PACKET/0.1"

PLACEHOLDER_RE = re.compile(r"(^|\b)(unknown|unresolved|tbd|tbc|not yet bound|not bound|not selected|not yet selected)(\b|$)", re.I)

CURRENT_INSTANCE_GATE_OVERRIDES = {
    "CGXI-P0-SH01-ID-A": "SOURCE_IDENTITY",
    "CGXI-P1-TRACE-001": "LOT_PASSPORT",
    "CGXI-P1-VIA-001": "PROCESS_ROUTE",
    "CGXI-P2-C-001": "LOT_PASSPORT",
    "CGXI-P2-L-001": "LOT_PASSPORT",
    "CGXI-P3-LC-001": "UPSTREAM_EVIDENCE",
}

GATE_ACTIONS = {
    "SOURCE_IDENTITY": {
        "objective": "Bind an attributable exact source or observed on-hand identity before geometry/process qualification.",
        "required_evidence": ["manufacturer/part or material identity", "source/label locator", "source document or observed label hash"],
        "completion_receipt": "source identity receipt linked to the same CGXI",
    },
    "REQUIREMENT_TARGET": {
        "objective": "Declare the functional target that determines geometry, test method and acceptance.",
        "required_evidence": ["target function/value/band/use case", "declared tolerance or acceptance intent", "service/environment assumptions"],
        "completion_receipt": "reviewed requirement-target revision",
    },
    "LOT_PASSPORT": {
        "objective": "Bind exact acquired/on-hand lot identity without inheriting unmeasured source-typical performance.",
        "required_evidence": ["manufacturer/part", "lot/batch observed from label or source", "quantity/unit", "condition/storage", "source hashes"],
        "completion_receipt": "CGX lot passport linked to the CGXI",
    },
    "GEOMETRY": {
        "objective": "Freeze source/tool-compatible geometry, tolerances and datum for the declared test question.",
        "required_evidence": ["geometry revision", "dimensions/tolerances", "datum/reference", "geometry hash", "machine/process envelope used"],
        "completion_receipt": "geometry freeze receipt",
    },
    "PROCESS_ROUTE": {
        "objective": "Select and bind the exact process sequence/settings family before claiming manufacturability.",
        "required_evidence": ["operation sequence", "process conditions", "material compatibility", "cure/post-process route", "prior-layer damage checks"],
        "completion_receipt": "process-route revision linked to source/tool state",
    },
    "TOOL_CALIBRATION": {
        "objective": "Bind actual tool/metrology identity and current capability/calibration evidence.",
        "required_evidence": ["tool identity/config", "capability tokens", "calibration/readback", "uncertainty", "maintenance/condition state"],
        "completion_receipt": "tool/calibration manifest",
    },
    "TEST_METHOD": {
        "objective": "Bind the measurement method, fixture, calibration and uncertainty needed to falsify/accept the declared claim.",
        "required_evidence": ["measurement method", "fixture", "calibration ref", "acceptance/falsifier", "uncertainty plan"],
        "completion_receipt": "witness/test packet revision",
    },
    "HASH_FREEZE": {
        "objective": "Freeze source/configuration hashes after all consequential inputs are bound.",
        "required_evidence": ["source hashes", "geometry/process/tool/material hashes", "configuration hash"],
        "completion_receipt": "frozen configuration receipt",
    },
    "UPSTREAM_EVIDENCE": {
        "objective": "Wait for and consume required measured/qualified parent evidence instead of duplicating or bypassing it.",
        "required_evidence": ["named upstream CGXI/test receipts", "measured values with uncertainty", "configuration/source parity"],
        "completion_receipt": "upstream evidence consumption receipt",
    },
    "TEST_EXECUTION": {
        "objective": "Execute the already-frozen witness packet only under the separate physical execution gate.",
        "required_evidence": ["execution authority", "precheck", "raw readback", "uncertainty", "DBR disposition"],
        "completion_receipt": "physical test DBR",
    },
    "CLOSED": {
        "objective": "No unresolved exact-binding gate detected.",
        "required_evidence": [],
        "completion_receipt": "none",
    },
}


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _placeholder(value: Any) -> bool:
    text = str(value or "").strip()
    return not text or bool(PLACEHOLDER_RE.search(text))


def _contains_unresolved_lot(instance: dict[str, Any]) -> bool:
    fields = (
        instance.get("material_stack_and_lots", ""),
        instance.get("material_passport_refs", ""),
        instance.get("uncertainty", ""),
        instance.get("blocked_by_next_binding", ""),
    )
    text = " ".join(str(x) for x in fields).lower()
    return "lot" in text and any(x in text for x in ("unresolved", "not yet bound", "not bound", "acquire", "passport"))


def _target_unresolved(instance: dict[str, Any]) -> bool:
    text = " ".join(
        str(instance.get(k, ""))
        for k in ("blocked_by_next_binding", "source_locator_or_hash", "uncertainty", "electrical_mechanical_thermal_or_process_ratings")
    ).lower()
    markers = (
        "select target",
        "use case",
        "declare passive band",
        "intended band",
        "band/function",
        "frequency",
    )
    return any(m in text for m in markers)


def _upstream_dependencies(instance: dict[str, Any]) -> list[str]:
    iid = instance.get("instance_id")
    if iid == "CGXI-P3-LC-001":
        return ["CGXI-P2-L-001", "CGXI-P2-C-001"]
    return []


def _process_unresolved(instance: dict[str, Any]) -> bool:
    text = " ".join(
        str(instance.get(k, ""))
        for k in ("manufacturing_or_assembly_route", "blocked_by_next_binding", "uncertainty")
    ).lower()
    return "unresolved" in text and any(m in text for m in ("process", "route", "cure", "via-forming", "forming", "deposition"))


def resolve_binding_gate(instance: dict[str, Any], population: dict[str, Any] | None = None) -> dict[str, Any]:
    iid = instance.get("instance_id", "UNKNOWN")
    progress = _instance_binding_progress(instance)

    if instance.get("binding_state") == "BUILD_READY":
        gate = "CLOSED"
    elif iid in CURRENT_INSTANCE_GATE_OVERRIDES:
        gate = CURRENT_INSTANCE_GATE_OVERRIDES[iid]
    elif _upstream_dependencies(instance):
        gate = "UPSTREAM_EVIDENCE"
    elif progress == "UNBOUND" and _looks_unresolved_instance_value(instance.get("source_locator_or_hash", "")):
        gate = "SOURCE_IDENTITY"
    elif _target_unresolved(instance):
        gate = "REQUIREMENT_TARGET"
    elif _contains_unresolved_lot(instance):
        gate = "LOT_PASSPORT"
    elif _looks_unresolved_instance_value(instance.get("geometry_revision", "")) or _looks_unresolved_instance_value(instance.get("dimensions_and_tolerances", "")):
        gate = "GEOMETRY"
    elif _process_unresolved(instance):
        gate = "PROCESS_ROUTE"
    elif _looks_unresolved_instance_value(instance.get("tool_and_calibration_refs", "")):
        gate = "TOOL_CALIBRATION"
    elif not str(instance.get("acceptance_tests", "")).strip() or not str(instance.get("falsifiers", "")).strip():
        gate = "TEST_METHOD"
    elif _looks_unresolved_instance_value(instance.get("source_hashes", "")) or _looks_unresolved_instance_value(instance.get("configuration_hash", "")):
        gate = "HASH_FREEZE"
    elif instance.get("physical_state") == "NOT_RUN":
        gate = "TEST_EXECUTION"
    else:
        gate = "CLOSED"

    deps = _upstream_dependencies(instance)
    upstream_state: dict[str, str] = {}
    if deps and population:
        for dep in deps:
            row = find_instance(population, dep)
            upstream_state[dep] = row.get("physical_state", "UNKNOWN")

    action = GATE_ACTIONS[gate]
    out = {
        "schema": SCHEMA,
        "instance_id": iid,
        "proof_stage": instance.get("proof_stage"),
        "binding_progress": progress,
        "binding_state": instance.get("binding_state"),
        "physical_state": instance.get("physical_state"),
        "first_open_gate": gate,
        "action_packet": {
            "objective": action["objective"],
            "required_evidence": action["required_evidence"],
            "completion_receipt": action["completion_receipt"],
            "owner_next_binding_text": instance.get("blocked_by_next_binding"),
        },
        "upstream_dependencies": deps,
        "upstream_physical_state": upstream_state,
        "authority_boundary": "This resolution classifies existing owner state only. It does not create evidence, procure material, execute a test, or promote BUILD_READY.",
    }
    out["resolution_hash"] = _canonical_hash({k: v for k, v in out.items() if k != "resolution_hash"})
    return out


def resolve_binding_queue(population: dict[str, Any] | None = None) -> dict[str, Any]:
    population = population or load_default_instance_population()
    rows = [resolve_binding_gate(row, population=population) for row in population["records"]]

    stage_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4, "P5": 5, "P6": 6, "P7": 7, "P8": 8, "P9": 9, "P10": 10}
    gate_rank = {
        "UPSTREAM_EVIDENCE": 0,
        "SOURCE_IDENTITY": 1,
        "REQUIREMENT_TARGET": 2,
        "LOT_PASSPORT": 3,
        "PROCESS_ROUTE": 4,
        "GEOMETRY": 5,
        "TOOL_CALIBRATION": 6,
        "TEST_METHOD": 7,
        "HASH_FREEZE": 8,
        "TEST_EXECUTION": 9,
        "CLOSED": 10,
    }
    rows.sort(key=lambda r: (stage_rank.get(str(r.get("proof_stage")), 99), gate_rank.get(r["first_open_gate"], 99), r["instance_id"]))

    out = {
        "schema": "CGX-INSTANCE-BINDING-QUEUE/0.1",
        "record_count": len(rows),
        "queue": rows,
        "counts_by_gate": {},
        "physical_execution": False,
        "rule": "Dependency/proof-stage order is preserved. The queue identifies the next evidence-producing action and does not itself change owner state.",
    }
    for r in rows:
        out["counts_by_gate"][r["first_open_gate"]] = out["counts_by_gate"].get(r["first_open_gate"], 0) + 1
    out["queue_hash"] = _canonical_hash({k: v for k, v in out.items() if k != "queue_hash"})
    return out


def validate_lot_passport(passport: dict[str, Any]) -> dict[str, Any]:
    required = (
        "kind",
        "manufacturer",
        "part_or_material",
        "lot_or_batch",
        "quantity",
        "unit",
        "received_state",
        "condition",
        "declared_use",
        "disposition",
        "source_hashes",
    )
    blockers = [f"missing:{k}" for k in required if k not in passport or _placeholder(passport.get(k))]
    if isinstance(passport.get("source_hashes"), list):
        if not passport["source_hashes"] or any(_placeholder(x) for x in passport["source_hashes"]):
            blockers.append("invalid:source_hashes")
    else:
        blockers.append("invalid:source_hashes")
    if passport.get("disposition") not in {"ACCEPT_DECLARED_USE", "QUARANTINE", "HOLD"}:
        blockers.append("invalid:disposition")

    body = {
        "schema": LOT_SCHEMA,
        "cgx_uri": f"cgx://{passport.get('kind','material')}/lot/{str(passport.get('lot_or_batch','unbound')).strip()}",
        "passport": passport,
        "blockers": sorted(set(blockers)),
        "lot_identity_bound": not blockers,
        "performance_qualified": False,
        "authority_boundary": "Lot identity/provenance never promotes source-typical or unmeasured performance into qualified instance properties.",
    }
    body["passport_hash"] = _canonical_hash({k: v for k, v in body.items() if k != "passport_hash"})
    return body


def validate_tool_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    required = (
        "tool_id",
        "identity",
        "configuration_hash",
        "supported_operations",
        "capability_envelope",
        "calibration_state",
        "condition",
    )
    blockers = [f"missing:{k}" for k in required if k not in manifest or _placeholder(manifest.get(k))]
    ops = manifest.get("supported_operations")
    if not isinstance(ops, list) or not ops:
        blockers.append("invalid:supported_operations")
    envelope = manifest.get("capability_envelope")
    if not isinstance(envelope, dict) or not envelope:
        blockers.append("invalid:capability_envelope")
    cal = manifest.get("calibration_state")
    calibration_current = cal == "CURRENT"
    if not calibration_current:
        blockers.append(f"calibration:{cal or 'UNRESOLVED'}")
    if calibration_current and _placeholder(manifest.get("calibration_ref")):
        blockers.append("missing:calibration_ref")
    if calibration_current and _placeholder(manifest.get("uncertainty")):
        blockers.append("missing:uncertainty")

    body = {
        "schema": TOOL_SCHEMA,
        "cgx_uri": f"cgx://tool/{manifest.get('tool_id','unbound')}",
        "manifest": manifest,
        "blockers": sorted(set(blockers)),
        "structurally_valid": not any(b.startswith(("missing:", "invalid:")) for b in blockers),
        "qualified_for_bound_operation": not blockers,
        "authority_boundary": "Installed or source-listed hardware is not qualified capability until the actual configuration and applicable calibration/readback are current.",
    }
    body["capability_hash"] = _canonical_hash({k: v for k, v in body.items() if k != "capability_hash"})
    return body


def create_witness_coupon_packet(
    instance: dict[str, Any],
    *,
    geometry: dict[str, Any] | None = None,
    lot_refs: list[str] | None = None,
    process: dict[str, Any] | None = None,
    tool_manifests: list[dict[str, Any]] | None = None,
    measurement_method: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gate = resolve_binding_gate(instance)
    blockers: list[str] = []
    if not geometry or _placeholder(geometry.get("revision")) or _placeholder(geometry.get("geometry_hash")):
        blockers.append("geometry-not-frozen")
    if not lot_refs:
        blockers.append("lot-passport-not-bound")
    if not process or _placeholder(process.get("revision")) or _placeholder(process.get("process_hash")):
        blockers.append("process-not-frozen")

    tool_results = [validate_tool_manifest(x) for x in (tool_manifests or [])]
    if not tool_results or any(not x["qualified_for_bound_operation"] for x in tool_results):
        blockers.append("tool-calibration-not-current")
    if not measurement_method or _placeholder(measurement_method.get("method")) or _placeholder(measurement_method.get("calibration_ref")):
        blockers.append("measurement-method-not-bound")

    packet = {
        "schema": COUPON_SCHEMA,
        "cgx_uri": f"cgx://manufacturing/test/{instance.get('instance_id','unknown').lower()}-witness-v0.1",
        "parent_instance": instance.get("instance_id"),
        "first_open_binding_gate": gate["first_open_gate"],
        "objective": gate["action_packet"]["objective"],
        "geometry": geometry,
        "lot_refs": lot_refs or [],
        "process": process,
        "tool_manifests": [x["cgx_uri"] for x in tool_results],
        "measurement_method": measurement_method,
        "acceptance_tests": instance.get("acceptance_tests"),
        "falsifiers": instance.get("falsifiers"),
        "environment_profile": instance.get("environment_profile"),
        "blockers": sorted(set(blockers)),
        "execution_state": "DIGITAL_PACKET_READY" if not blockers else "HOLD",
        "physical_execution": False,
        "authority_boundary": "DIGITAL_PACKET_READY means prerequisites are structurally bound for review; physical execution remains separately authorised and produces the actual evidence.",
    }
    packet["packet_hash"] = _canonical_hash({k: v for k, v in packet.items() if k != "packet_hash"})
    return packet