"""Pure combinatorial geometry proof for regular convex dodecahedron.

This does not interpret arbitrary Wikipedia prose, derive a physical mesh,
certify Euclidean vertex coordinates, or verify a native CGX hyper-address.
"""
from __future__ import annotations

def solve_regular_polyhedron_incidence(*, faces: int, edges_per_face: int,
                                      faces_meeting_at_vertex: int) -> dict:
    if any(type(x) is not int or x < 3 for x in (faces, edges_per_face, faces_meeting_at_vertex)):
        raise ValueError("INVALID_INCIDENCE")
    # In a closed 2-manifold every edge belongs to 2 faces.
    incident_edges = faces * edges_per_face
    if incident_edges % 2:
        raise ValueError("EDGE_INCIDENCE_NONINTEGRAL")
    edges = incident_edges // 2
    # Each vertex is incident to q edges for a convex regular polyhedron.
    incident_vertices = 2 * edges
    if incident_vertices % faces_meeting_at_vertex:
        raise ValueError("VERTEX_INCIDENCE_NONINTEGRAL")
    vertices = incident_vertices // faces_meeting_at_vertex
    euler = vertices - edges + faces
    if euler != 2:
        raise ValueError("SPHERICAL_EULER_MISMATCH")
    return {
        "model": "CONVEX_REGULAR_POLYHEDRON_TOPOLOGY",
        "assumptions": [
            "orientable closed convex polyhedral surface (sphere topology)",
            "all faces have equal edge count",
            "all vertices have equal degree",
            "every edge belongs to exactly two faces",
        ],
        "input": {"faces": faces, "edges_per_face": edges_per_face,
                  "faces_meeting_at_vertex": faces_meeting_at_vertex},
        "derived": {"faces": faces, "edges": edges, "vertices": vertices,
                    "euler_characteristic": euler},
        "proof": ["p*F=2*E", "q*V=2*E", "V-E+F=2"],
        "evidence_class": "MATHEMATICAL_INCIDENCE_IDENTITY_ONLY",
        "source_xml_admitted": False,
        "euclidean_coordinates_derived": False,
        "scientific_measurement": False,
        "native_cgx_object_id": None,
        "dbr_readback": False,
    }

def regular_dodecahedron_topology() -> dict:
    return solve_regular_polyhedron_incidence(
        faces=12, edges_per_face=5, faces_meeting_at_vertex=3
    )
