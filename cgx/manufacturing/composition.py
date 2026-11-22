"""PrintSpace compositional geometry review over existing CGX geometry kernels.

This is a bounded *digital* reference graph. It reuses the UniSpace exact
convex-integer verifier and the existing Type-I VGK library, rather than making
new scientific/physical claims, native LOAD hydration or any mesh CSG union.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from tools.verify_unispace_product import canonical_integer_mesh_review
from .volumetric import load_volumetric_kernel
from .exact_contact import exact_convex_contact, ContactHold

SCHEMA = "CGX-PRINTSPACE-GEOMETRY-COMPOSITION/0.1"
RESULT_SCHEMA = "CGX-PRINTSPACE-COMPOSITION-REVIEW/0.1"
SAFE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
MAX_INSTANCES = 24
MAX_SOURCE_SHAPES = 12
MAX_INTERFACES = 64
MAX_REQUEST_BYTES = 256 * 1024
BUILD_URI = re.compile(r"^cgx://manufacturing/build/[A-Za-z0-9._-]{1,128}$")


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False).encode("ascii")).hexdigest()


def valid_id(value: Any) -> bool:
    return isinstance(value, str) and bool(SAFE_ID.fullmatch(value))


def is_int_vector(value: Any) -> bool:
    return (type(value) is list and len(value) == 3
            and all(type(v) is int and abs(v) <= 1_000_000 for v in value))


def hold(code: str, *, detail: str = "") -> dict:
    return {"schema": RESULT_SCHEMA, "state": "HOLD", "hold_codes": [code],
            "detail": detail, "geometry_composite_hash": None, "load_h0": None,
            "machine_authorised": False, "native_load_admitted": False,
            "mint_authorised": False, "rights_verified": False,
            "physical_evidence_verified": False, "release_authorised": False}


def _aabb(vertices: list[list[int]], offset: list[int]) -> dict:
    return {"min_mm": [min(v[j] + offset[j] for v in vertices) for j in range(3)],
            "max_mm": [max(v[j] + offset[j] for v in vertices) for j in range(3)]}


def _aabb_relation(a: dict, b: dict) -> str:
    # AABBs are necessary spatial filters, never proof of actual mesh contact.
    if any(a["max_mm"][j] < b["min_mm"][j] or b["max_mm"][j] < a["min_mm"][j]
           for j in range(3)):
        return "AABB_DISJOINT"
    if any(a["max_mm"][j] == b["min_mm"][j] or b["max_mm"][j] == a["min_mm"][j]
           for j in range(3)):
        return "AABB_TOUCH_CANDIDATE_NOT_PROVEN"
    return "AABB_OVERLAP_CANDIDATE_NOT_PROVEN"


def compile_geometry_composition(request: dict[str, Any]) -> dict[str, Any]:
    """Review a composite key/resolution DAG; never produce machine instructions.

    Geometry vertices are exact integer millimetres for the initial baseline.
    Operations are composition-by-reference only (not exact CSG or FEM).
    T173 catalogue identities are never admitted by supplied receipt strings.
    """
    if not isinstance(request, dict):
        return hold("INVALID_REQUEST")
    try:
        raw = json.dumps(request, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False).encode("ascii")
    except (ValueError, TypeError, RecursionError, OverflowError):
        return hold("NONCANONICAL_REQUEST")
    if len(raw) > MAX_REQUEST_BYTES:
        return hold("REQUEST_BUDGET")
    if request.get("schema") != SCHEMA or not valid_id(request.get("composite_id")):
        return hold("SCHEMA_OR_ID")
    ref = request.get("manufacturing_ir_ref")
    if not isinstance(ref, str) or BUILD_URI.fullmatch(ref) is None:
        return hold("CANONICAL_MANUFACTURING_REF_REQUIRED")
    if request.get("load_mode") != "H0_REVIEW_ONLY":
        return hold("LOAD_NATIVE_HYDRATION_DENIED")
    library = load_volumetric_kernel()  # existing canonical project-owned source only
    if (not isinstance(library, dict) or
        library.get("schema") != "CGX-TYPE1-VOLUMETRIC-KERNEL/0.1" or
        not isinstance(library.get("records"), list)):
        return hold("VOL_KERNEL_SOURCE_INVALID")
    kernels = {}
    for kernel in library["records"]:
        if not isinstance(kernel, dict) or not valid_id(kernel.get("kernel_id")) or kernel["kernel_id"] in kernels:
            return hold("VOL_KERNEL_SOURCE_INVALID")
        kernels[kernel["kernel_id"]] = kernel
    if not kernels:
        return hold("EMPTY_VOL_KERNELS")
    source_shapes = request.get("source_shapes")
    instances = request.get("instances")
    interfaces = request.get("interfaces")
    if (not isinstance(source_shapes, list) or not 1 <= len(source_shapes) <= MAX_SOURCE_SHAPES or
        not isinstance(instances, list) or not 1 <= len(instances) <= MAX_INSTANCES or
        not isinstance(interfaces, list) or len(interfaces) > MAX_INTERFACES):
        return hold("COMPOSITION_BUDGET_OR_SHAPE")
    admitted = {}
    candidate_t173 = []
    for source in source_shapes:
        if not isinstance(source, dict) or not valid_id(source.get("shape_id")) or source["shape_id"] in admitted:
            return hold("DUPLICATE_OR_INVALID_SHAPE")
        if (source.get("units") != "mm" or not isinstance(source.get("rights_ref"), str) or
            not source["rights_ref"].strip() or not isinstance(source.get("source_ref"), str) or
            not source["source_ref"].strip() or len(source["source_ref"]) > 256):
            return hold("GEOMETRY_UNITS_OR_RIGHTS_UNBOUND")
        if source.get("t173_position") is not None:
            position = source["t173_position"]
            if type(position) is not int or not 1 <= position <= 173:
                return hold("T174_RESERVED_OR_INVALID")
            candidate_t173.append({"shape_id": source["shape_id"],
                                   "t173_position": position,
                                   "state": "UNADMITTED_CATALOGUE_CANDIDATE"})
        try:
            canonical = canonical_integer_mesh_review(source.get("vertices_mm"),
                                                      source.get("faces"))
        except (ValueError, TypeError, KeyError, IndexError, OverflowError, RecursionError) as exc:
            return hold("EXACT_CONVEX_GEOMETRY_INVALID", detail=type(exc).__name__)
        admitted[source["shape_id"]] = {"shape_id": source["shape_id"],
                                        "shape_sha256": canonical["sha256"],
                                        "metrics": canonical["metrics"],
                                        "vertices": [list(v) for v in source["vertices_mm"]],
                                        "faces": [list(face) for face in source["faces"]],
                                        "rights_ref": source["rights_ref"],
                                        "source_ref": source["source_ref"]}
    nodes = {}
    for row in instances:
        if not isinstance(row, dict) or not valid_id(row.get("instance_id")) or row["instance_id"] in nodes:
            return hold("DUPLICATE_OR_INVALID_INSTANCE")
        sid = row.get("shape_id")
        if not isinstance(sid, str) or sid not in admitted or not valid_id(row.get("kernel_id")) or row["kernel_id"] not in kernels:
            return hold("UNRESOLVED_SHAPE_OR_KERNEL")
        if not is_int_vector(row.get("translate_mm")) or not valid_id(row.get("material_slot")):
            return hold("TRANSFORM_OR_MATERIAL_INVALID")
        src = admitted[sid]
        if src["metrics"].get("t173_catalogue_admitted") is not False:
            return hold("UNEXPECTED_GEOMETRY_ADMISSION")
        nodes[row["instance_id"]] = {
            "instance_id": row["instance_id"], "shape_id": sid,
            "shape_sha256": src["shape_sha256"],
            "kernel_id": row["kernel_id"],
            "kernel_sha256": digest(kernels[row["kernel_id"]]), "material_slot": row["material_slot"],
            "translate_mm": list(row["translate_mm"]),
            "bounds_mm": _aabb(src["vertices"], row["translate_mm"]),
        }
    canonical_interfaces = []
    seen_edges = set()
    for edge in interfaces:
        if not isinstance(edge, dict):
            return hold("INVALID_INTERFACE")
        source, target = edge.get("from"), edge.get("to")
        if (not isinstance(source, str) or not isinstance(target, str) or
            source not in nodes or target not in nodes or source == target):
            return hold("UNKNOWN_INTERFACE_ENDPOINT")
        pair = (source, target)
        if pair in seen_edges:
            return hold("DUPLICATE_DIRECTED_INTERFACE")
        seen_edges.add(pair)
        if edge.get("kind") not in ("CONTACT_CANDIDATE", "INTERLAYER", "EMBEDDED", "SEPARATED"):
            return hold("INTERFACE_KIND")
        if edge.get("evidence_state") not in ("UNTESTED", "PROPOSED"):
            return hold("FALSE_QUALIFICATION_ATTEMPT")
        relation = _aabb_relation(nodes[source]["bounds_mm"], nodes[target]["bounds_mm"])
        a = nodes[source]; b = nodes[target]
        mesh_a = admitted[a["shape_id"]]; mesh_b = admitted[b["shape_id"]]
        try:
            contact = exact_convex_contact(
                {"vertices_mm": mesh_a["vertices"], "faces": mesh_a["faces"]}, a["translate_mm"],
                {"vertices_mm": mesh_b["vertices"], "faces": mesh_b["faces"]}, b["translate_mm"])
        except ContactHold as exc:
            return hold(str(exc))
        relation_exact = contact["relation"]
        if edge["kind"] == "CONTACT_CANDIDATE" and relation_exact == "DISJOINT":
            return hold("DECLARED_CONTACT_DISJOINT")
        if edge["kind"] == "SEPARATED" and relation_exact != "DISJOINT":
            return hold("SEPARATION_NOT_DEMONSTRATED_BY_BOUNDS")
        if edge["kind"] == "INTERLAYER" and relation_exact != "FACE_CONTACT":
            return hold("INTERLAYER_NO_FINITE_CONTACT_AREA")
        if edge["kind"] in ("CONTACT_CANDIDATE", "INTERLAYER") and relation_exact == "VOLUME_OVERLAP":
            return hold("UNRESOLVED_INTERPENETRATING_REGIONS")
        if edge["kind"] == "EMBEDDED":
            if relation_exact == "DISJOINT":
                return hold("EMBEDDED_REGIONS_DISJOINT")
            if relation_exact == "VOLUME_OVERLAP":
                return hold("EMBEDDED_BOOLEAN_UNRESOLVED")
        canonical_interfaces.append({"from": source, "to": target,
                                     "kind": edge["kind"], "bounds_relation": relation,
                                     "exact_convex_contact": contact,
                                     "evidence_state": edge["evidence_state"],
                                     "directional_coupon_status": "PENDING_BOTH_DIRECTIONS_INDEPENDENTLY",
                                     "lot_tool_environment_binding": "NOT_VERIFIED",
                                     "interface_qualification_plan": [
                                         "SOURCE_LOT_AND_TOOL_IDENTITY",
                                         "SOURCE_TO_TARGET_DEPOSITION_COUPON",
                                         "TARGET_TO_SOURCE_SEPARATE_COUPON",
                                         "ATMOSPHERE_SURFACE_PREP_AND_CURE_HISTORY",
                                         "MEASURED_INTERFACE_FUNCTION_AND_DAMAGE_READBACK",
                                     ],
                                     "physical_compatibility": "NOT_VERIFIED"})
    if len(nodes) > 1 and not canonical_interfaces:
        return hold("UNCONNECTED_COMPOSITION")
    # Prevent accidental composition through one unrelated (unlinked) region.
    adjacency = {key: set() for key in nodes}
    for edge in canonical_interfaces:
        adjacency[edge["from"]].add(edge["to"])
        adjacency[edge["to"]].add(edge["from"])
    if len(nodes) > 1:
        seen, stack = set(), [next(iter(nodes))]
        while stack:
            key = stack.pop()
            if key in seen:
                continue
            seen.add(key)
            stack.extend(adjacency[key] - seen)
        if len(seen) != len(nodes):
            return hold("DISCONNECTED_COMPONENT_GRAPH")
    used_shapes = sorted({node["shape_id"] for node in nodes.values()})
    if len(used_shapes) != len(admitted):
        return hold("UNUSED_SHAPE_DEFINITION")
    if len(nodes) > 1 and not canonical_interfaces:
        return hold("UNCONNECTED_COMPOSITION")
    graph = {
        "schema": RESULT_SCHEMA,
        "composite_id": request["composite_id"],
        "manufacturing_ir_ref": ref,
        "instances": [nodes[key] for key in sorted(nodes)],
        "interfaces": sorted(canonical_interfaces, key=lambda e:(e["from"], e["to"])),
        "shape_catalogue": [
            {"shape_id": sid, "sha256": admitted[sid]["shape_sha256"],
             "source_rights_ref": admitted[sid]["rights_ref"],
             "source_ref": admitted[sid]["source_ref"]}
            for sid in sorted(used_shapes)
        ],
        "t173_candidates": sorted(candidate_t173, key=lambda e:(e["t173_position"],e["shape_id"])),
        "kernel_source_schema": library["schema"],
        "kernel_source_version": library.get("artifact_id"),
        "kernel_library_sha256": digest(library),
        "physics_validation": "UNQUALIFIED",
        "boolean_union_computed": False,
    }
    composite_hash = digest(graph)
    # LOAD H0 is purely a minimal shorthand/reference envelope; it is not
    # an authenticated Alexandria/host resolution or carrier activation.
    load_h0 = {
        "schema": "CGX-PRINTSPACE-LOAD-H0-REFERENCE/0.1",
        "alias": "LOAD.cgx", "alias_status": "SOURCE_REVIEW_ONLY",
        "parent_filespace": "Cognigrex.cgx", "child_filespace": "Romer.cgx",
        "identity": f"cgx://manufacturing/composite/{composite_hash}",
        "composite_sha256": composite_hash,
        "shape_keys": [e["sha256"] for e in graph["shape_catalogue"]],
        "kernel_keys": sorted({n["kernel_id"] for n in nodes.values()}),
        "hydration": "H0_METADATA_ONLY", "native_admitted": False,
        "source_bytes_hydrated": 0, "network_fetch": False,
        "identity_host_verified": False, "rights_verified": False,
        "private_data_included": False, "public_release_authorised": False,
    }
    state = "HOLD" if candidate_t173 else "REVIEW_ONLY"
    return {"schema": RESULT_SCHEMA, "state": state,
            "hold_codes": ["T173_CANDIDATE_UNADMITTED"] if candidate_t173 else [],
            "geometry_composite_hash": composite_hash,
            "graph": graph, "load_h0": load_h0,
            "machine_authorised": False, "native_load_admitted": False,
            "mint_authorised": False, "rights_verified": False,
            "physical_evidence_verified": False, "release_authorised": False}