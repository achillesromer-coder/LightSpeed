from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .printstack import compile_printable_component, compile_printable_stack

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path(__file__).with_name("universal_stack_normal_form_contract_v0_1.json")
RADIATIVE_PATH = ROOT / "cgx" / "component_atlas" / "type1_radiative_transport_seed_matrix_v0_1.json"

SCHEMA = "CGX-UNIVERSAL-STACK-NORMAL-FORM/0.1"
ARTIFACT_ID = "UTP-147"


def _slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip())
    return value.strip("-").lower() or "unnamed"


def _hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_stack_normal_form_contract() -> dict[str, Any]:
    doc = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if doc.get("artifact_id") != ARTIFACT_ID:
        raise ValueError(f"normal-form-contract-mismatch:{doc.get('artifact_id')}")
    return doc


def load_radiative_transport_matrix() -> dict[str, Any]:
    doc = json.loads(RADIATIVE_PATH.read_text(encoding="utf-8"))
    if doc.get("artifact_id") != "UTP-146":
        raise ValueError(f"radiative-transport-contract-mismatch:{doc.get('artifact_id')}")
    return doc


def _validate_seed_graph(seed_graph_class: str, seed_refs: list[str]) -> None:
    if seed_graph_class not in {"SG-0", "SG-1", "SG-N"}:
        raise ValueError(f"unknown-seed-graph:{seed_graph_class}")
    count = len(seed_refs)
    if seed_graph_class == "SG-0" and count != 0:
        raise ValueError(f"seed-count-mismatch:SG-0:{count}")
    if seed_graph_class == "SG-1" and count != 1:
        raise ValueError(f"seed-count-mismatch:SG-1:{count}")
    if seed_graph_class == "SG-N" and count < 2:
        raise ValueError(f"seed-count-mismatch:SG-N:{count}")


def _compile_child_packets(
    component_specs: list[dict[str, Any]],
    stack_id: str,
    horizon: str,
) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    for index, spec in enumerate(component_specs, start=1):
        record = spec["record"]
        build_id = spec.get("build_id") or f"{stack_id}-{index:03d}-{record['ID']}"
        packets.append(
            compile_printable_component(
                record,
                instance=spec.get("instance"),
                simulation=spec.get("simulation"),
                build_id=build_id,
                horizon=spec.get("horizon", horizon),
                required_scopes=spec.get("required_scopes"),
                process_conditions=spec.get("process_conditions"),
                parameter_overrides=spec.get("parameter_overrides"),
            )
        )
    return packets


def compile_stack_normal_form(
    component_specs: list[dict[str, Any]],
    *,
    stack_id: str,
    seed_graph_class: str,
    seed_refs: list[str] | None = None,
    field_transport_regimes: list[str] | None = None,
    source_nodes: list[dict[str, Any]] | None = None,
    reference_nodes: list[dict[str, Any]] | None = None,
    coupling_bindings: list[dict[str, Any]] | None = None,
    witness_refs: list[str] | None = None,
    relations: list[dict[str, str]] | None = None,
    interlayer_edges: list[dict[str, Any]] | None = None,
    horizon: str = "H-TERR-SITE",
) -> dict[str, Any]:
    seed_refs = list(seed_refs or [])
    requested_regimes = list(dict.fromkeys(field_transport_regimes or []))
    source_nodes = list(source_nodes or [])
    reference_nodes = list(reference_nodes or [])
    coupling_bindings = list(coupling_bindings or [])
    witness_refs = list(witness_refs or [])
    interlayer_edges = list(interlayer_edges or [])

    _validate_seed_graph(seed_graph_class, seed_refs)

    radiative = load_radiative_transport_matrix()
    known_regimes = {row["id"]: row for row in radiative["field_transport_regimes"]}
    unknown = [regime for regime in requested_regimes if regime not in known_regimes]
    if unknown:
        raise ValueError("unknown-field-transport-regime:" + ",".join(unknown))

    binding_by_regime: dict[str, dict[str, Any]] = {}
    for row in coupling_bindings:
        regime = row.get("regime_id")
        if regime not in known_regimes:
            raise ValueError(f"unknown-coupling-regime:{regime}")
        if regime in binding_by_regime:
            raise ValueError(f"duplicate-coupling-regime:{regime}")
        state = row.get("state", "OPEN_SYMBOLIC")
        if state not in {"OPEN_SYMBOLIC", "SYMBOLIC", "SOLVED", "MEASURED", "HOLD"}:
            raise ValueError(f"invalid-coupling-state:{regime}:{state}")
        if state in {"SOLVED", "MEASURED"}:
            for key in ("model_or_measurement_ref", "matrix_or_result_ref", "validity_ref"):
                if not str(row.get(key) or "").strip():
                    raise ValueError(f"coupling-provenance-missing:{regime}:{state}:{key}")
        binding_by_regime[regime] = dict(row)

    edge_contract = radiative["interlayer_edge_contract"]
    edge_required = tuple(edge_contract["required"])
    allowed_edge_states = set(edge_contract.get("evidence_states", []))
    validated_edges: list[dict[str, Any]] = []
    seen_edge_ids: set[str] = set()
    for edge in interlayer_edges:
        missing = [key for key in edge_required if key not in edge or edge.get(key) in (None, "")]
        if missing:
            raise ValueError(f"interlayer-edge-missing:{edge.get('edge_id','UNNAMED')}:{','.join(missing)}")
        edge_id = str(edge["edge_id"])
        if edge_id in seen_edge_ids:
            raise ValueError(f"duplicate-interlayer-edge:{edge_id}")
        seen_edge_ids.add(edge_id)
        region_from = str(edge["region_from"])
        region_to = str(edge["region_to"])
        if region_from == region_to:
            raise ValueError(f"interlayer-edge-self-loop:{edge_id}")
        expected_direction = f"{region_from}->{region_to}"
        if str(edge["process_direction"]).replace(" ", "") != expected_direction.replace(" ", ""):
            raise ValueError(f"interlayer-direction-mismatch:{edge_id}:{edge['process_direction']}:{expected_direction}")
        regime = str(edge["field_transport_regime"])
        if regime not in known_regimes:
            raise ValueError(f"unknown-interlayer-regime:{edge_id}:{regime}")
        evidence_state = str(edge["evidence_state"])
        if allowed_edge_states and evidence_state not in allowed_edge_states:
            raise ValueError(f"invalid-interlayer-evidence-state:{edge_id}:{evidence_state}")
        validated_edges.append(dict(edge))

    base_stack = compile_printable_stack(
        component_specs,
        stack_id=stack_id,
        relations=relations,
        horizon=horizon,
    )
    child_packets = _compile_child_packets(component_specs, stack_id, horizon)

    blockers: list[str] = []
    for packet in child_packets:
        for blocker in packet.get("blockers", []):
            blockers.append(f"child:{packet['cgx_uri']}:{blocker}")

    if not requested_regimes:
        blockers.append("field-transport-regime-unselected")
    if not source_nodes:
        blockers.append("source-node-unbound")
    if not reference_nodes:
        blockers.append("reference-node-unbound")
    if not witness_refs:
        blockers.append("witness-unbound")
    if len(component_specs) > 1 and not validated_edges:
        blockers.append("interlayer-edge-unbound")
    for edge in validated_edges:
        if edge["evidence_state"] not in {"SOLVED", "MEASURED", "QUALIFIED"}:
            blockers.append(f"interlayer:{edge['edge_id']}:{edge['evidence_state']}")

    field_rows: list[dict[str, Any]] = []
    for regime in requested_regimes:
        contract = known_regimes[regime]
        binding = binding_by_regime.get(regime, {})
        state = binding.get("state", "OPEN_SYMBOLIC")
        if state in {"OPEN_SYMBOLIC", "SYMBOLIC", "HOLD"}:
            blockers.append(f"coupling:{regime}:{state}")
        field_rows.append(
            {
                "regime_id": regime,
                "family": contract["family"],
                "governing": contract["governing"],
                "mutual_contract": contract["mutual"],
                "regime_gate": contract["regime_gate"],
                "witness_contract": contract["witness"],
                "coupling_state": state,
                "model_or_measurement_ref": binding.get("model_or_measurement_ref"),
                "matrix_or_result_ref": binding.get("matrix_or_result_ref"),
            }
        )

    child_refs = [
        {
            "packet_ref": packet["cgx_uri"],
            "packet_hash": packet["packet_hash"],
            "archetype_id": packet["archetype"]["id"],
            "instance_id": packet.get("instance_id"),
            "packet_state": packet["packet_state"],
            "topology_kernel_ids": packet["topology"]["kernel_ids"],
        }
        for packet in child_packets
    ]

    damage_gates = sorted(
        {
            gate
            for packet in child_packets
            for gate in packet.get("preservation", {}).get("damage_gates", [])
            if gate
        }
    )

    ready = (
        base_stack["stack_state"] == "BUILD_READY_MACHINE_NEUTRAL"
        and not blockers
        and all(row["coupling_state"] in {"SOLVED", "MEASURED"} for row in field_rows)
    )

    output = {
        "schema": SCHEMA,
        "artifact_id": ARTIFACT_ID,
        "build_id": "BUILD-080",
        "cgx_uri": f"cgx://manufacturing/stack-normal-form/{_slug(stack_id)}",
        "horizon": horizon,
        "normal_form_state": "NORMALIZED_BUILD_READY_DIGITAL" if ready else "NORMALIZED_DIGITAL_HOLD",
        "intent": {
            "stack_id": stack_id,
            "logical_component_count": len(component_specs),
            "rule": "2D connectivity/function intent does not substitute for frozen 3D region/interface geometry.",
        },
        "children_and_regions": {
            "child_packets": child_refs,
            "base_printable_stack_ref": base_stack["cgx_uri"],
            "base_printable_stack_hash": base_stack["stack_hash"],
            "coupled_4d_kernel": base_stack["coupled_4d_kernel"],
            "rule": "Child recipes remain authoritative and are referenced, never duplicated.",
        },
        "reference_nodes": reference_nodes,
        "seed_graph": {
            "class": seed_graph_class,
            "seed_refs": seed_refs,
            "seed_count": len(seed_refs),
            "rule": radiative["seed_source_contract"][seed_graph_class]["source_rule"],
        },
        "sources_and_receivers": {
            "source_nodes": source_nodes,
            "rule": "Every active, impressed or environmental source and consequential receiver/load relation remains attributable.",
        },
        "field_transport": {
            "regimes": field_rows,
            "distinct_regime_count": len(field_rows),
            "rule": "Distinct field/transport families are selected explicitly; no universal radiation equation is inferred.",
        },
        "interlayer_edges": {
            "edges": validated_edges,
            "edge_count": len(validated_edges),
            "contract": edge_contract,
            "rule": "X->Y and Y->X are separate typed edges. Missing damage, preservation, witness, evidence or authority remains HOLD.",
        },
        "self_mutual_coupling": {
            "bindings": coupling_bindings,
            "interlayer_edge_contract": radiative.get("interlayer_edge_contract"),
            "rule": "Absent self/mutual terms remain OPEN_SYMBOLIC rather than silently zero; off-diagonal terms may be omitted only by sensitivity/evidence.",
        },
        "energy_passivity": {
            "state": "DECLARED_UNVERIFIED",
            "passivity_rule": radiative["linearity_and_energy_rules"]["passivity"],
            "linearity_rule": radiative["linearity_and_energy_rules"]["linear_superposition"],
            "nonlinear_rule": radiative["linearity_and_energy_rules"]["nonlinear_rule"],
            "reciprocity_rule": radiative["linearity_and_energy_rules"]["reciprocity"],
            "balance_rule": radiative["linearity_and_energy_rules"]["balance"],
        },
        "process_sequence": {
            "dependencies": base_stack["dependencies"],
            "schedule": base_stack["schedule"],
            "optimization": base_stack["optimization"],
            "rule": "Scheduling may optimize compatible transitions but cannot bypass child/interface/preservation/safety/evidence gates.",
        },
        "preservation_revision": {
            "damage_gates": damage_gates,
            "revision_rule": "Any consequential geometry/material/process/boundary/seed revision invalidates dependent numeric field/mutual matrices and requires selective solve/readback refresh.",
        },
        "witness_evidence": {
            "witness_refs": witness_refs,
            "minimum_for_seed_class": radiative["witness_minimum"][seed_graph_class.replace("-", "")],
            "child_physical_states": [packet["evidence"]["physical_state"] for packet in child_packets],
            "evidence_ceiling": "DIGITAL_COMPILER_ONLY_UNTIL_EXACT_INSTANCE_AND_WITNESS_PROMOTION",
        },
        "blockers": sorted(set(blockers)),
        "authority": {
            "physical_execution": False,
            "machine_program": False,
            "certification": False,
            "public_release": False,
            "durable_cgx_promotion": False,
            "rule": "Normalization creates no new physical, certification, release, carrier or high-consequence authority.",
        },
        "physical_execution": False,
    }
    output["normal_form_hash"] = _hash({key: value for key, value in output.items() if key != "normal_form_hash"})
    return output
