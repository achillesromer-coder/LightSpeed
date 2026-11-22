"""Exact digital solid metrics, no physical material, density, or Boolean claim."""
from __future__ import annotations

import copy
import json
from fractions import Fraction
from pathlib import Path

from cgx.manufacturing.solid_metrics import (
    exact_nominal_convex_metrics, measure_composite_nominal,
)
from cgx.manufacturing.composition import compile_geometry_composition

PILOT = Path(__file__).resolve().parents[1] / "cgx/manufacturing/printspace_composite_pilot_v0_1.json"


def pilot():
    return json.loads(PILOT.read_text(encoding="utf-8"))


def tetra():
    return {
        "vertices_mm": [[0, 0, 0], [2, 0, 0], [0, 2, 0], [0, 0, 2]],
        "faces": [[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]],
    }


def test_exact_nominal_pilot_volumes_centroid_and_no_mass():
    result = measure_composite_nominal(pilot())
    assert result["state"] == "EXACT_DIGITAL_NOMINAL_ONLY"
    assert result["nominal_sum_volume_mm3_exact"] == "64"
    assert result["volume_weighted_geometric_centroid_mm_exact"] == ["2", "2", "2"]
    parts = {x["instance_id"]: x for x in result["parts"]}
    assert parts["structure"]["volume_mm3_exact"] == "32"
    assert parts["interface"]["volume_mm3_exact"] == "16"
    assert parts["conductive"]["volume_mm3_exact"] == "16"
    assert parts["structure"]["centroid_mm_exact"] == ["2", "2", "1"]
    assert parts["interface"]["centroid_mm_exact"] == ["2", "2", "5/2"]
    assert parts["conductive"]["centroid_mm_exact"] == ["2", "2", "7/2"]
    assert result["union_volume_mm3_exact"] is None
    assert result["mass"] is None
    assert not result["physical_evidence_verified"]
    assert not result["machine_authorised"]


def test_exact_solid_tetra_volume_centroid_translation():
    t = tetra()
    a = exact_nominal_convex_metrics(t["vertices_mm"], t["faces"], [0, 0, 0])
    b = exact_nominal_convex_metrics(t["vertices_mm"], t["faces"], [3, -2, 4])
    assert a["volume_mm3_exact"] == b["volume_mm3_exact"] == "4/3"
    assert a["centroid_mm_exact"] == ["1/2", "1/2", "1/2"]
    assert b["centroid_mm_exact"] == ["7/2", "-3/2", "9/2"]
    assert a["surface_area_mm2_exact_if_rational"] is None
    assert a["mass_computed"] is False
    assert len(a["face_areas"]) == 4


def test_box_area_and_nominal_volume_exact():
    box = pilot()["source_shapes"][0]
    r = exact_nominal_convex_metrics(box["vertices_mm"], box["faces"], [0, 0, 0])
    assert r["volume_mm3_exact"] == "32"
    assert r["surface_area_mm2_exact_if_rational"] == "64"
    assert r["centroid_mm_exact"] == ["2", "2", "1"]
    assert all(Fraction(v["area_squared_mm4_exact"]) > 0 for v in r["face_areas"])


def test_results_reproducible_and_order_invariant():
    a = pilot()
    b = copy.deepcopy(a)
    b["source_shapes"].reverse()
    b["instances"].reverse()
    b["interfaces"].reverse()
    r1, r2 = measure_composite_nominal(a), measure_composite_nominal(b)
    assert r1 == r2


def test_sum_does_not_claim_union_for_overlapping_digital_components():
    p = pilot()
    # Two slabs now spatially overlap; unconnected synthetic geometry is held
    # by the digital composite review unless a supported interface permits it.
    p["instances"][2]["translate_mm"] = [0, 0, 2]
    r = measure_composite_nominal(p)
    assert r["state"] == "HOLD"
    assert r["union_volume_mm3_exact"] is None


def test_t173_not_admitted_cannot_receive_valid_volume_proof():
    p = pilot()
    p["source_shapes"][0]["t173_position"] = 173
    r = measure_composite_nominal(p)
    assert r["state"] == "HOLD"
    assert "UNVERIFIED_DIGITAL_GEOMETRY" in r["hold_codes"]


def test_proposed_geometry_graph_or_transform_mutation_cannot_pass():
    p = pilot()
    projection = compile_geometry_composition(p)
    assert projection["state"] == "REVIEW_ONLY"
    projection["graph"]["instances"][0]["translate_mm"][0] = 99
    assert measure_composite_nominal(p, projection)["state"] == "HOLD"
    fresh = compile_geometry_composition(p)
    p["instances"][0]["translate_mm"][0] = 99
    r = measure_composite_nominal(p, fresh)
    assert r["state"] == "HOLD"
    assert "INSTANCE_TRANSFORM_MISMATCH" in r["hold_codes"]


def test_wrong_face_orientation_fails_before_volume_evaluation():
    t = tetra()
    t["faces"][0].reverse()
    try:
        exact_nominal_convex_metrics(t["vertices_mm"], t["faces"], [0, 0, 0])
    except ValueError:
        pass
    else:
        raise AssertionError("Inward or nonconvex geometry must fail exact volume")


def test_noninteger_translation_cannot_be_rounded():
    t = tetra()
    try:
        exact_nominal_convex_metrics(t["vertices_mm"], t["faces"], [0.5, 0, 0])
    except ValueError:
        pass
    else:
        raise AssertionError("Float translation cannot be silently rounded")


def test_snapshot_does_not_alias_mutable_request_translation_or_vertices():
    p = pilot()
    graph = compile_geometry_composition(p)
    assert graph["state"] == "REVIEW_ONLY"
    before = json.dumps(graph, sort_keys=True)
    p["instances"][0]["translate_mm"][0] = 123
    p["source_shapes"][0]["vertices_mm"][0][0] = 123
    p["source_shapes"][0]["faces"][0][0] = 6
    assert json.dumps(graph, sort_keys=True) == before
