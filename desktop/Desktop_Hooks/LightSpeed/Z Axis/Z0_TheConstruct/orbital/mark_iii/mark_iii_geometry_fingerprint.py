#!/usr/bin/env python3
"""Cross-platform semantic fingerprint for named Mark III triangle geometry."""
from __future__ import annotations

import hashlib
import struct
from typing import Any

FINGERPRINT_SCHEMA = "mark-iii-semantic-geometry-v1"
QUANTIZATION_SCALE = 100_000_000
QUANTIZATION_METRES = 1.0 / QUANTIZATION_SCALE


def _quantized_point(point: Any, scale: int) -> tuple[int, int, int]:
    return tuple(int(round(float(value) * scale)) for value in point)


def semantic_geometry_fingerprint(scene: Any, scale: int = QUANTIZATION_SCALE) -> str:
    digest = hashlib.sha256()
    digest.update(FINGERPRINT_SCHEMA.encode("ascii") + b"\0")
    digest.update(struct.pack(">Q", scale))
    for node_name in sorted(scene.geometry):
        mesh = scene.geometry[node_name]
        encoded = node_name.encode("utf-8")
        digest.update(struct.pack(">I", len(encoded)))
        digest.update(encoded)
        digest.update(struct.pack(">QQ??", len(mesh.vertices), len(mesh.faces), bool(mesh.is_watertight), bool(mesh.is_winding_consistent)))
        points = [_quantized_point(vertex, scale) for vertex in mesh.vertices]
        triangles: list[tuple[int, ...]] = []
        for face in mesh.faces:
            a, b, c = (points[int(index)] for index in face)
            rotations = (a + b + c, b + c + a, c + a + b)
            triangles.append(min(rotations))
        for triangle in sorted(triangles):
            digest.update(struct.pack(">9q", *triangle))
    return digest.hexdigest()
