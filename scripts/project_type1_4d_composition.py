#!/usr/bin/env python3
"""Project one Type-I primitive from 2D intent into its bounded 3D/4D composition record.

This helper is deterministic and non-authoritative. It never executes a printer, selects
a commercial part, invents material properties, or raises an evidence ceiling.
"""
import argparse
import json
from pathlib import Path

DEFAULT_MATRIX = Path("cgx/component_atlas/type1_4d_composition_matrix_v0_1.json")
VALID_SEEDS = {"SG-0", "SG-1", "SG-N"}


def load_matrix(path=DEFAULT_MATRIX):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    records = data.get("records", [])
    index = {}
    for record in records:
        primitive = record.get("primitive_basis_class")
        if not primitive:
            raise ValueError("Composition record missing primitive_basis_class")
        if primitive in index:
            raise ValueError(f"Duplicate composition primitive: {primitive}")
        index[primitive] = record
    if len(index) != 20:
        raise ValueError(f"Expected 20 primitive basis records, found {len(index)}")
    return data, index


def project(primitive, seed_graph, path=DEFAULT_MATRIX):
    if seed_graph not in VALID_SEEDS:
        raise ValueError(f"Unknown seed graph: {seed_graph}")
    data, index = load_matrix(path)
    if primitive not in index:
        raise ValueError(f"Unknown primitive basis class: {primitive}")
    record = index[primitive]
    seed_key = seed_graph.replace("-", "_")
    route = record.get("seed_routes", {}).get(seed_key)
    if not route:
        raise ValueError(f"Missing {seed_graph} route for primitive {primitive}")
    return {
        "schema": "CGX-TYPE1-4D-COMPOSITION-PROJECTION/0.1",
        "artifact_id": data["artifact_id"],
        "primitive_basis_class": primitive,
        "seed_graph": seed_graph,
        "schematic_2d_intent": record["schematic_2d_intent"],
        "geometry_3d": record["geometry_3d"],
        "state_history_4d": record["state_history_4d"],
        "seed_route": route,
        "engineering_model_route": record["engineering_model_route"],
        "verification": record["verification"],
        "fail_closed": record["fail_closed"],
        "evidence_ceiling": "DIGITAL_COMPOSITION_ONLY / PHYSICAL_NOT_RUN",
        "next_pipeline": [
            "BIND_EXACT_INSTANCE_SOURCE_GEOMETRY_MATERIAL_PROCESS",
            "COMPILE_DIRECTIONAL_STACK_AND_INTERFACES",
            "SELECT_VALID_FIELD_TRANSPORT_MODEL",
            "APPLY_UTP148_MATURITY_INVALIDATION",
            "DEFINE_NEXT_PHYSICAL_WITNESS",
            "DBR_REVIEW_OR_HOLD",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("primitive")
    parser.add_argument("seed_graph", choices=sorted(VALID_SEEDS))
    parser.add_argument("--matrix", default=str(DEFAULT_MATRIX))
    args = parser.parse_args()
    print(json.dumps(project(args.primitive, args.seed_graph, args.matrix), indent=2))


if __name__ == "__main__":
    main()
