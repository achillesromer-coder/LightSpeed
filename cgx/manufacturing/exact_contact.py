"""Bounded exact convex-polyhedron contact classifier for PrintSpace review.

Coordinates and translations are integer millimetres, with exact rational
segment-plane intersections. It describes geometric intersection only: no
solid boolean mesh, toolpath, tolerancing, chemistry, adhesion, machine access,
Raphael facet admission, or source/rights authentication is performed.
"""
from __future__ import annotations

from fractions import Fraction
from math import gcd, isqrt
from typing import Any

from tools.verify_unispace_product import exact_convex_mesh_review

MAX_FACES = 64
MAX_EDGES = 192
MAX_EDGE_FACE_WORK = 12000
MAX_INTERSECTION_VERTICES = 2048


class ContactHold(ValueError):
    """Mesh or computational envelope is not admitted for exact contact review."""


def dot(a: tuple, b: tuple):
    return sum(x * y for x, y in zip(a, b))


def sub(a: tuple, b: tuple):
    return tuple(x - y for x, y in zip(a, b))


def cross(a: tuple, b: tuple):
    return (a[1]*b[2]-a[2]*b[1],
            a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def _wire_geometry(shape: dict, offset: list[int]) -> tuple[list[tuple], list[tuple], list[tuple]]:
    if (not isinstance(shape, dict) or
        type(offset) is not list or len(offset) != 3 or
        any(type(v) is not int or abs(v) > 1_000_000 for v in offset)):
        raise ContactHold("INVALID_OR_UNBOUNDED_GEOMETRY")
    vertices, faces = shape.get("vertices_mm"), shape.get("faces")
    try:
        exact_convex_mesh_review(vertices, faces)
    except (ValueError, TypeError, IndexError, KeyError, OverflowError, RecursionError) as exc:
        raise ContactHold("UNVERIFIED_CONVEX_GEOMETRY") from exc
    if len(faces) > MAX_FACES:
        raise ContactHold("EXACT_CONTACT_COMPLEXITY_BUDGET")
    points = [tuple(row[i] + offset[i] for i in range(3)) for row in vertices]
    planes = []
    edges = set()
    for face in faces:
        v0, v1, v2 = (points[face[i]] for i in range(3))
        normal = cross(sub(v1, v0), sub(v2, v0))
        planes.append((normal, dot(normal, v0)))  # outward: n·p <= d
        for i, j in zip(face, face[1:] + face[:1]):
            edges.add(tuple(sorted((i, j))))
    if len(edges) > MAX_EDGES:
        raise ContactHold("EXACT_CONTACT_COMPLEXITY_BUDGET")
    return points, planes, [(points[i], points[j]) for i, j in sorted(edges)]


def _inside(point: tuple, planes: list[tuple]) -> bool:
    return all(dot(normal, point) <= d for normal, d in planes)


def _clip_candidates(edges: list[tuple], other_planes: list[tuple],
                     all_planes: list[tuple], output: set) -> None:
    for start, end in edges:
        direction = sub(end, start)
        for normal, d in other_planes:
            denominator = dot(normal, direction)
            if denominator == 0:
                continue
            t = Fraction(d - dot(normal, start), denominator)
            if t < 0 or t > 1:
                continue
            point = tuple(Fraction(start[i]) + t * direction[i] for i in range(3))
            if _inside(point, all_planes):
                output.add(point)
                if len(output) > MAX_INTERSECTION_VERTICES:
                    raise ContactHold("EXACT_CONTACT_VERTEX_BUDGET")


def _affine_dimension(points: list[tuple]) -> tuple[int, list[tuple]]:
    origin = points[0]
    basis = []
    for point in points[1:]:
        v = sub(point, origin)
        if v == (0, 0, 0):
            continue
        if not basis:
            basis.append(v)
        elif len(basis) == 1 and cross(basis[0], v) != (0, 0, 0):
            basis.append(v)
        elif len(basis) == 2 and dot(cross(basis[0], basis[1]), v) != 0:
            basis.append(v)
        if len(basis) == 3:
            break
    return len(basis), basis


def _hull_projected_area_sq(points: list[tuple], basis: list[tuple]) -> Fraction:
    n = cross(basis[0], basis[1])
    drop = max(range(3), key=lambda i: abs(n[i]))
    keep = [i for i in range(3) if i != drop]
    projected = sorted({(p[keep[0]], p[keep[1]]) for p in points})

    def turn(a, b, c):
        return ((b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0]))

    bottom = []
    for p in projected:
        while len(bottom) > 1 and turn(bottom[-2], bottom[-1], p) <= 0:
            bottom.pop()
        bottom.append(p)
    top = []
    for p in reversed(projected):
        while len(top) > 1 and turn(top[-2], top[-1], p) <= 0:
            top.pop()
        top.append(p)
    hull = bottom[:-1] + top[:-1]
    area_projected = Fraction(abs(sum(a[0]*b[1]-a[1]*b[0]
                             for a, b in zip(hull, hull[1:]+hull[:1]))), 2)
    normal_norm_squared = sum(component*component for component in n)
    return Fraction(area_projected * area_projected * normal_norm_squared, n[drop]*n[drop])


def _fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else str(value)


def _normalised_plane(normal: tuple, d: int) -> tuple[tuple, int]:
    scale = gcd(gcd(abs(normal[0]), abs(normal[1])), abs(normal[2]))
    return tuple(v//scale for v in normal), d//scale


def _shared_face_normals(a_planes, b_planes, points) -> list[list[int]]:
    normals = set()
    for normal, d in a_planes:
        norm, dist = _normalised_plane(normal, d)
        if all(dot(normal, p) == d for p in points):
            for nb, db in b_planes:
                opposite, opposite_d = _normalised_plane(nb, db)
                if norm == tuple(-v for v in opposite) and dist == -opposite_d:
                    normals.add(norm)
    return [list(n) for n in sorted(normals)]


def exact_convex_contact(shape_a: dict[str, Any], offset_a: list[int],
                         shape_b: dict[str, Any], offset_b: list[int]) -> dict[str, Any]:
    """Exact geometric classification for two *bounded* convex integer meshes.

    The contact dimension is the affine rank of all intersection vertices;
    edge/face/point contacts have zero shared 3D volume. The area-squared field
    is rational and exact even for oblique planes with irrational area.
    """
    points_a, planes_a, edges_a = _wire_geometry(shape_a, offset_a)
    points_b, planes_b, edges_b = _wire_geometry(shape_b, offset_b)
    if len(edges_a)*len(planes_b) + len(edges_b)*len(planes_a) > MAX_EDGE_FACE_WORK:
        raise ContactHold("EXACT_CONTACT_COMPLEXITY_BUDGET")
    bounds_a = [(min(p[i] for p in points_a), max(p[i] for p in points_a)) for i in range(3)]
    bounds_b = [(min(p[i] for p in points_b), max(p[i] for p in points_b)) for i in range(3)]
    if any(bounds_a[i][1] < bounds_b[i][0] or bounds_b[i][1] < bounds_a[i][0] for i in range(3)):
        return _result("DISJOINT", 0, None)
    both_planes = planes_a + planes_b
    intersection = {tuple(map(Fraction, p)) for p in points_a if _inside(p, planes_b)}
    intersection.update(tuple(map(Fraction, p)) for p in points_b if _inside(p, planes_a))
    _clip_candidates(edges_a, planes_b, both_planes, intersection)
    _clip_candidates(edges_b, planes_a, both_planes, intersection)
    if not intersection:
        return _result("DISJOINT", 0, None)
    vertices = sorted(intersection)
    dimension, basis = _affine_dimension(vertices)
    relation = {0:"POINT_CONTACT", 1:"EDGE_CONTACT", 2:"FACE_CONTACT", 3:"VOLUME_OVERLAP"}[dimension]
    out = _result(relation, len(vertices), dimension)
    if dimension == 0:
        out["contact_point_mm"] = [_fraction_text(v) for v in vertices[0]]
    if dimension == 1:
        v0 = vertices[0]
        squared = max(sum((p[i]-v0[i])**2 for i in range(3)) for p in vertices)
        out["line_length_squared_mm2"] = _fraction_text(Fraction(squared))
    if dimension == 2:
        squared_area = _hull_projected_area_sq(vertices, basis)
        out["face_area_squared_mm4"] = _fraction_text(squared_area)
        pn, pd = isqrt(squared_area.numerator), isqrt(squared_area.denominator)
        if pn*pn == squared_area.numerator and pd*pd == squared_area.denominator:
            out["face_area_mm2_exact"] = _fraction_text(Fraction(pn, pd))
        out["directed_face_normals_from_a_to_b"] = _shared_face_normals(planes_a, planes_b, vertices)
    return out


def _result(relation: str, count: int, dimension: int | None) -> dict[str, Any]:
    return {
        "schema":"CGX-PRINTSPACE-EXACT-CONVEX-CONTACT/0.1",
        "relation":relation,
        "intersection_affine_dimension":dimension,
        "intersection_vertex_count":count,
        "integer_mm_rational_exact":True,
        "source_rights_authenticated":False,
        "material_interface_qualified":False,
        "physical_adhesion_verified":False,
        "boolean_mesh_emitted":False,
        "machine_execution_authorised":False,
    }