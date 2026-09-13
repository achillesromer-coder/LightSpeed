"""Build review-only OBJ assets for the ACHILLES Digital Twin Atrium.

SOURCE_DERIVED geometry is reconstructed from traceable source dimensions.
INTERACTION_PROXY geometry is for interactive review only and MUST NOT be used
as manufacturing, structural, safety, performance, approval, deployment, or
empirical evidence. Dependencies are pinned in this directory's requirements.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import trimesh


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "assets" / "models"
DEFAULT_MANIFEST = REPO_ROOT / "data" / "digital-twin" / "generated_mesh_manifest_v1.json"


def box(extents, centre=(0, 0, 0)):
    mesh = trimesh.creation.box(extents=extents)
    mesh.apply_translation(centre)
    return mesh


def cylinder(radius, height, centre=(0, 0, 0), axis="z", sections=24):
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    if axis == "x":
        mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    elif axis == "y":
        mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    elif axis != "z":
        raise ValueError(f"unsupported cylinder axis: {axis}")
    mesh.apply_translation(centre)
    return mesh


def torus(major_radius, minor_radius, centre=(0, 0, 0)):
    mesh = trimesh.creation.torus(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_sections=36,
        minor_sections=12,
    )
    mesh.apply_translation(centre)
    return mesh


def cone(radius, height, centre=(0, 0, 0)):
    mesh = trimesh.creation.cone(radius=radius, height=height, sections=32)
    mesh.apply_translation(centre)
    return mesh


def combine(*parts):
    return trimesh.util.concatenate(parts)


def watchtower_bounds(x0, y0, z0, x1, y1, z1):
    return box(
        (x1 - x0, y1 - y0, z1 - z0),
        ((x0 + x1) / 2 - 700, (y0 + y1) / 2 - 400, (z0 + z1) / 2),
    )


def build_meshes():
    """Build meshes in stable manifest order."""
    meshes = {}
    meshes["solar_hull"] = combine(
        *[box((5 * scale, 3 * scale, 0.1), (0, 0, z)) for z, scale in [(-0.30, 1), (-0.18, 0.96), (-0.06, 0.92), (0.06, 0.88), (0.18, 0.84), (0.30, 0.80)]]
    )
    meshes["free_flow_batteries"] = combine(
        box((5.2, 3.6, 2.2)),
        *[cylinder(0.45, 1.7, (x, y, 0)) for x in (-1.6, 0, 1.6) for y in (-1, 0, 1)],
    )
    meshes["free_flow_capacitors"] = combine(
        box((5.5, 3.2, 0.3), (0, 0, -1)),
        *[cylinder(0.5, 2, (x, 0, 0)) for x in (-1.8, -0.6, 0.6, 1.8)],
    )
    meshes["free_flow_solenoid_stack"] = combine(
        *[torus(1.8, 0.18, (0, 0, z)) for z in (-1.4, -0.7, 0, 0.7, 1.4)],
        cylinder(0.35, 4),
    )
    meshes["rfs_emff"] = combine(
        cylinder(0.28, 5), torus(1.6, 0.18, (0, 0, -1)),
        torus(1.6, 0.18, (0, 0, 1)), box((4.5, 4.5, 0.25), (0, 0, -2.3)),
    )
    meshes["mark_1p"] = combine(
        box((5, 3, 2)), box((4.2, 2.2, 0.2), (0, 0, 1.1)),
        *[cylinder(0.45, 1.4, (x, 0, 1.5)) for x in (-1.4, 0, 1.4)],
    )
    meshes["mark_i"] = combine(
        cylinder(2, 4.5, axis="x"), cylinder(0.45, 1.4, (0, 0, 2.1)),
        cylinder(0.45, 1.4, (0, 0, -2.1)), box((5.5, 3.5, 0.3), (0, 0, -2.2)),
    )
    # Avoid arm-count semantics while the exact current source remains gated.
    meshes["mark_iii"] = combine(
        box((4.5, 4.5, 1), (0, 0, -1.2)), box((4, 4, 1)),
        box((3.5, 3.5, 1), (0, 0, 1.2)), cylinder(0.5, 4),
    )
    meshes["luke_family"] = combine(torus(3, 0.35), torus(2.2, 0.22), cylinder(0.35, 2.2))
    meshes["maglev_luke_iv"] = combine(
        cone(4.2, 2.2, (0, 0, -0.8)), torus(4.5, 0.25, (0, 0, 0.4)),
        torus(3.3, 0.18, (0, 0, 0.8)), box((11, 11, 0.3), (0, 0, -2)),
    )
    meshes["embedded_bio_blocks"] = combine(
        *[box((1.2, 1.6, 0.8), (x, y, 0)) for x in (-1.5, 0, 1.5) for y in (-1, 1)]
    )
    meshes["second_cycle"] = combine(
        cylinder(1.5, 0.7), cylinder(0.15, 3, (0, 0, -1.7)),
        *[cone(0.25, 1.3, (1.1 * math.cos(a), 1.1 * math.sin(a), 0.85)) for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)],
    )
    meshes["watchtower"] = combine(
        watchtower_bounds(682.368435, 388.22801, -4.9, 704.695125, 410.928449, 13.3),
        watchtower_bounds(690.762816, 397.709183, 13.3, 695.055237, 402.07346, 68.3),
        watchtower_bounds(687.796253, 394.358546, 68.3, 698.461964, 405.202802, 76.62),
        watchtower_bounds(677.189889, 393.771598, 0, 697.718664, 442.644649, 9.1),
        watchtower_bounds(681.214722, 366.815892, 0, 728.529076, 398.792178, 9.1),
    )
    # A 48-space site-neutral proxy, not the final InterSol room/site layout.
    meshes["intersol"] = combine(
        *[box((5.2, 4.2, 2.6), (column * 5.8 - 20.3, row * 4.8 - 12, 1.3)) for row in range(6) for column in range(8)]
    )
    meshes["m1_elevated_bypass"] = combine(
        box((1000, 23.5, 2), (0, 11.75, 0)), box((1000, 23.5, 2), (0, 38.75, 0)),
        box((1000, 57, 1.5), (0, 24.999, -1.25)), box((1000, 52, 4.45), (0, 25.25, -0.025)),
    )
    meshes["romer_spaceport"] = combine(
        box((40, 75, 22), (0, 0, 11)), box((32, 32, 6), (85, 0, 3)),
        box((18, 18, 18), (85, 0, 15)), box((240, 4, 1), (0, 70, 0.5)),
    )
    return meshes


REPRESENTATION_CLASSES = {
    "watchtower": "SOURCE_DERIVED_GEOMETRY",
    "m1_elevated_bypass": "SOURCE_DERIVED_GEOMETRY",
    "romer_spaceport": "SOURCE_DERIVED_PARTIAL",
}


def display_path(path):
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def generate_assets(output_root, manifest_output):
    output_root.mkdir(parents=True, exist_ok=True)
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    manifest = []
    for twin_id, mesh in build_meshes().items():
        output = output_root / f"{twin_id}.obj"
        obj = trimesh.exchange.obj.export_obj(mesh, include_normals=True, include_texture=False).rstrip() + "\n"
        output.write_text(obj, encoding="utf-8", newline="\n")
        manifest.append({
            "twin_id": twin_id,
            "file": display_path(output),
            "format": "OBJ",
            "representation_class": REPRESENTATION_CLASSES.get(twin_id, "INTERACTION_PROXY"),
            "units": "m",
            "vertices": int(len(mesh.vertices)),
            "faces": int(len(mesh.faces)),
            "watertight": bool(mesh.is_watertight),
            "size_bytes": output.stat().st_size,
            "sha256": sha256(output),
        })
    receipt = {
        "schema": "achilles_generated_mesh_receipt_v1",
        "generator": "tools/digital-twin/build_atrium_viewer_meshes.py",
        "dependencies": {"numpy": np.__version__, "trimesh": trimesh.__version__},
        "assets": manifest,
    }
    manifest_output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifest


def parse_args(arguments: Iterable[str] | None = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--manifest-output", type=Path, default=DEFAULT_MANIFEST)
    return parser.parse_args(arguments)


def main(arguments: Iterable[str] | None = None):
    args = parse_args(arguments)
    manifest = generate_assets(args.output_root, args.manifest_output)
    print(json.dumps({
        "generated": len(manifest),
        "output_root": display_path(args.output_root),
        "manifest": display_path(args.manifest_output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
