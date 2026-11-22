"""Exact rational *digital* volume/centroid for existing reviewed convex meshes.

This is a read-only computation on the CGX composition. It is NOT a CAD Boolean
union, manufacturing tolerance evaluation, real density/mass analysis, FEM,
toolpath, material-volume prediction, or physical metrology. Shape geometry
comes from the already bounded integer convex mesh verifier.
"""
from __future__ import annotations

from fractions import Fraction
from math import isqrt
from typing import Any

from tools.verify_unispace_product import canonical_integer_mesh_review
from .composition import compile_geometry_composition, digest

SCHEMA = "CGX-PRINTSPACE-NOMINAL-SOLID-METRICS/0.1"
MAX_REGIONS = 24


def _fraction(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _dot(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]


def _cross(a: tuple[int, int, int], b: tuple[int, int, int]) -> tuple[int, int, int]:
    return (a[1]*b[2]-a[2]*b[1],
            a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def _rational_sqrt(x: Fraction) -> str | None:
    n, d = isqrt(x.numerator), isqrt(x.denominator)
    if n*n == x.numerator and d*d == x.denominator:
        return _fraction(Fraction(n, d))
    return None


def exact_nominal_convex_metrics(vertices: Any, faces: Any, offset: Any) -> dict:
    """Exactly evaluate one convex solid (mm units) and its *translated* centroid.

    Signed tetrahedra about coordinate origin give volume and first moments:
    V = sum(det(a,b,c))/6; C_j = sum(det(a,b,c)*(a_j+b_j+c_j))/
    (4*sum(det(a,b,c))). The existing convex verifier enforces outward loops.
    """
    if (type(offset) is not list or len(offset) != 3 or
            any(type(x) is not int or abs(x) > 1_000_000 for x in offset)):
        raise ValueError("UNSUPPORTED_EXACT_TRANSLATION")
    verified = canonical_integer_mesh_review(vertices, faces)
    p = [tuple(int(v) for v in vertex) for vertex in vertices]
    det_total = 0
    moments = [0, 0, 0]
    surface = Fraction(0)
    face_areas: list[dict[str, str | int | None]] = []
    for fi, face in enumerate(faces):
        a = p[face[0]]
        face_area_vector_twice = (0, 0, 0)
        for j in range(1, len(face)-1):
            b, c = p[face[j]], p[face[j+1]]
            determinant = _dot(a, _cross(b, c))
            det_total += determinant
            for axis in range(3):
                moments[axis] += determinant * (a[axis]+b[axis]+c[axis])
            ab, ac = tuple(b[k]-a[k] for k in range(3)), tuple(c[k]-a[k] for k in range(3))
            t = _cross(ab, ac)
            face_area_vector_twice = tuple(face_area_vector_twice[k] + t[k] for k in range(3))
        squared = Fraction(_dot(face_area_vector_twice, face_area_vector_twice), 4)
        if squared <= 0:
            raise ValueError("INVALID_POLYGON_FACE_AREA")
        area = _rational_sqrt(squared)
        if area is not None:
            surface += Fraction(area)
        face_areas.append({
            "face_index": fi,
            "area_squared_mm4_exact": _fraction(squared),
            "area_mm2_rational_if_available": area,
        })
    if det_total != verified["metrics"]["six_times_volume"] or det_total <= 0:
        raise ValueError("INVALID_EXACT_VOLUME_INVARIANT")
    centroid = [Fraction(moments[k], 4*det_total) + offset[k] for k in range(3)]
    volume = Fraction(det_total, 6)
    return {
        "shape_sha256": verified["sha256"],
        "volume_mm3_exact": _fraction(volume),
        "centroid_mm_exact": [_fraction(c) for c in centroid],
        "surface_area_mm2_exact_if_rational": _fraction(surface) if all(x["area_mm2_rational_if_available"] is not None for x in face_areas) else None,
        "face_areas": face_areas,
        "convex_verified_digital": True,
        "units": "mm",
        "density_bound": False,
        "mass_computed": False,
        "boolean_union_computed": False,
    }


def measure_composite_nominal(request: Any, projection: Any = None) -> dict:
    """Measure each exact component; never conflate sum with union volume."""
    def hold(reason):
        return {
            "schema": SCHEMA, "state": "HOLD", "hold_codes": [reason],
            "nominal_sum_volume_mm3_exact": None,
            "union_volume_mm3_exact": None,
            "mass": None,
            "physical_evidence_verified": False,
            "machine_authorised": False,
        }

    if not isinstance(request, dict):
        return hold("MISSING_COMPOSITE_INPUT")
    reviewed = compile_geometry_composition(request) if projection is None else projection
    if (not isinstance(reviewed, dict) or reviewed.get("state") != "REVIEW_ONLY"
            or reviewed.get("machine_authorised") is not False
            or reviewed.get("mint_authorised") is not False
            or not isinstance(reviewed.get("graph"), dict)
            or reviewed.get("geometry_composite_hash") != digest(reviewed["graph"])):
        return hold("UNVERIFIED_DIGITAL_GEOMETRY")
    source_shapes = request.get("source_shapes")
    requested_instances = request.get("instances")
    instances = reviewed["graph"].get("instances")
    if (not isinstance(source_shapes, list) or not isinstance(requested_instances, list)
            or not isinstance(instances, list) or len(instances) != len(requested_instances)
            or not 1 <= len(instances) <= MAX_REGIONS):
        return hold("MISSING_SOURCE_GEOMETRY")
    source_map = {x.get("shape_id"): x for x in source_shapes if isinstance(x, dict)}
    placement = {x.get("instance_id"): x for x in requested_instances if isinstance(x, dict)}
    if len(source_map) != len(source_shapes) or len(placement) != len(requested_instances):
        return hold("AMBIGUOUS_SOURCE_OR_PLACEMENT")
    entries = []
    volumes = []
    weighted = [Fraction(0)]*3
    for node in instances:
        iid = node.get("instance_id")
        spec = placement.get(iid)
        if not isinstance(spec, dict) or node.get("shape_id") != spec.get("shape_id"):
            return hold("INSTANCE_SOURCE_REF_MISMATCH")
        source = source_map.get(node["shape_id"])
        if not isinstance(source, dict) or node.get("translate_mm") != spec.get("translate_mm"):
            return hold("INSTANCE_TRANSFORM_MISMATCH")
        try:
            result = exact_nominal_convex_metrics(source.get("vertices_mm"), source.get("faces"), spec["translate_mm"])
        except (ValueError, KeyError, IndexError, TypeError, ZeroDivisionError, OverflowError):
            return hold("EXACT_SOLID_GEOMETRY_NOT_ADMITTED")
        if node.get("shape_sha256") != result["shape_sha256"]:
            return hold("SOURCE_SHAPE_HASH_MISMATCH")
        volume = Fraction(result["volume_mm3_exact"])
        volumes.append(volume)
        for axis in range(3):
            weighted[axis] += volume*Fraction(result["centroid_mm_exact"][axis])
        entries.append({
            "instance_id": iid,
            "shape_id": node["shape_id"],
            "material_slot": node["material_slot"],
            "shape_sha256": result["shape_sha256"],
            "volume_mm3_exact": result["volume_mm3_exact"],
            "centroid_mm_exact": result["centroid_mm_exact"],
            "surface_area_mm2_exact_if_rational": result["surface_area_mm2_exact_if_rational"],
            "density_g_cm3": None,
            "mass_g": None,
            "phase_or_cure_response": None,
        })
    # Exact sum is volume with multiplicity, not a claim of a Boolean union.
    total = sum(volumes, Fraction(0))
    if total <= 0:
        return hold("NONPOSITIVE_NOMINAL_VOLUME")
    if reviewed["graph"].get("manufacturing_ir_ref") != request.get("manufacturing_ir_ref"):
        return hold("IR_REF_CHANGED")
    return {
        "schema": SCHEMA, "state": "EXACT_DIGITAL_NOMINAL_ONLY",
        "hold_codes": ["BOOLEAN_UNION_NOT_COMPUTED", "DENSITY_AND_PHYSICAL_MASS_UNBOUND"],
        "geometry_composite_hash": reviewed["geometry_composite_hash"],
        "nominal_sum_volume_mm3_exact": _fraction(total),
        "volume_weighted_geometric_centroid_mm_exact": [_fraction(x/total) for x in weighted],
        "union_volume_mm3_exact": None,
        "mass": None,
        "parts": entries,
        "physical_evidence_verified": False,
        "machine_authorised": False,
        "mint_authorised": False,
    }
