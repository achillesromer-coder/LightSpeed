from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "CGX-INTERFACE-BINDING/0.1"
GRAPH_SCHEMA = "CGX-INTERFACE-GRAPH/0.1"
DEFAULT_LIBRARY = Path(__file__).resolve().parents[1] / "component_atlas" / "type1_interface_operator_kernel_v0_1.json"


def _hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_interface_operator_library(path: str | Path | None = None) -> dict[str, Any]:
    payload = json.loads(Path(path or DEFAULT_LIBRARY).read_text(encoding="utf-8"))
    if payload.get("schema") != "CGX-TYPE1-INTERFACE-OPERATOR-KERNEL/0.1":
        raise ValueError("unsupported-interface-library-schema")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("empty-interface-library")
    return payload


def find_interface_operator(operator_id: str, library: dict[str, Any] | None = None) -> dict[str, Any]:
    library = library or load_interface_operator_library()
    matches = [row for row in library["records"] if row.get("Operator ID") == operator_id]
    if len(matches) != 1:
        raise KeyError(f"interface-operator-resolution:{operator_id}:{len(matches)}")
    return matches[0]


def compile_interface_binding(
    operator_id: str,
    *,
    region_a: str,
    region_b: str,
    direction: str = "A_TO_B",
    bindings: dict[str, Any] | None = None,
    library: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compile one explicit region-to-region interface without inventing evidence.

    The operator supplies the boundary-law family and process/preservation contract.
    Exact numeric use remains conditional on attributable geometry/material/process
    state plus an explicitly validated model regime. Direction is retained exactly;
    A->B never creates B->A authority.
    """
    if direction not in {"A_TO_B", "B_TO_A"}:
        raise ValueError(f"unsupported-interface-direction:{direction}")
    if not str(region_a).strip() or not str(region_b).strip():
        raise ValueError("interface-regions-required")
    if region_a == region_b:
        raise ValueError("interface-regions-must-differ")

    row = find_interface_operator(operator_id, library=library)
    bindings = dict(bindings or {})
    blockers: list[str] = []

    source_refs = bindings.get("source_or_measurement_refs")
    if not isinstance(source_refs, list) or not source_refs or any(not str(x).strip() for x in source_refs):
        blockers.append("source-or-measurement-refs-open")
    if not str(bindings.get("geometry_ref") or "").strip():
        blockers.append("geometry-ref-open")
    if not str(bindings.get("process_state_ref") or "").strip():
        blockers.append("process-state-ref-open")
    if bindings.get("regime_validated") is not True:
        blockers.append("model-regime-not-validated")

    evidence_state = str(row.get("Evidence State") or "")
    authority_hold = "HOLD" in evidence_state.upper() or "CERTIFICATION-GATED" in evidence_state.upper()
    if authority_hold:
        blockers.append("operator-authority-evidence-hold")

    if authority_hold:
        state = "AUTHORITY_HOLD"
    elif blockers:
        state = "SYMBOLIC/HOLD"
    else:
        state = "NUMERIC_IF_BOUND"

    body = {
        "schema": SCHEMA,
        "artifact_id": "UTP-141",
        "operator_id": operator_id,
        "compiler_token": row.get("Compiler Token"),
        "interface_class": row.get("Interface Class"),
        "region_a": region_a,
        "region_b": region_b,
        "direction": direction,
        "state": state,
        "boundary_law": row.get("Boundary / Jump Law"),
        "numeric_gate": row.get("Numeric Inference Gate"),
        "formation_rule": row.get("X→Y Formation / Directionality Rule"),
        "preservation_gate": row.get("Process / Damage / Preservation Gate"),
        "state_history_variables": row.get("4D State / History Variables"),
        "cross_domain_couplings": row.get("Cross-Domain Couplings"),
        "verification_falsifier": row.get("Verification / Falsifier"),
        "fallback": row.get("Fallback / Higher-Fidelity Route"),
        "evidence_state": evidence_state,
        "bindings": bindings,
        "blockers": sorted(set(blockers)),
        "physical_execution": False,
        "authority_boundary": "Interface compilation selects a domain-valid boundary contract only. It cannot create source properties, qualification, certification, BUILD_READY, physical execution or release authority.",
    }
    body["interface_hash"] = _hash({k: v for k, v in body.items() if k != "interface_hash"})
    return body


def compile_interface_graph(
    edges: list[dict[str, Any]] | None,
    *,
    library: dict[str, Any] | None = None,
) -> dict[str, Any]:
    library = library or load_interface_operator_library()
    compiled = [
        compile_interface_binding(
            edge["operator_id"],
            region_a=edge["region_a"],
            region_b=edge["region_b"],
            direction=edge.get("direction", "A_TO_B"),
            bindings=edge.get("bindings"),
            library=library,
        )
        for edge in (edges or [])
    ]
    if not compiled:
        state = "NO_EXPLICIT_INTERFACES"
    elif all(edge["state"] == "NUMERIC_IF_BOUND" for edge in compiled):
        state = "INTERFACES_BOUND_FOR_DIGITAL_COMPILE"
    else:
        state = "HOLD"

    out = {
        "schema": GRAPH_SCHEMA,
        "artifact_id": "UTP-141",
        "state": state,
        "edge_count": len(compiled),
        "edges": compiled,
        "physical_execution": False,
        "rule": "Each stack edge declares exactly one reusable interface operator and explicit direction. Unresolved or authority-gated interface evidence holds the stack; reverse direction is never inferred.",
    }
    out["graph_hash"] = _hash({k: v for k, v in out.items() if k != "graph_hash"})
    return out
