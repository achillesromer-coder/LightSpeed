#!/usr/bin/env python3
"""Review and correct the representation layer of a materialized Eros pack.

The official source bytes remain unchanged. This stage:
- identifies the NASA STL as two printable assembly halves;
- removes only PDS vertices unused by the plate table;
- retains source coordinates without scaling, smoothing or repair;
- prohibits direct NASA/PDS shape-error claims without assembly/registration;
- emits a compact review pack and bounded receipt.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import trimesh

SOURCE_ROOT = Path(os.environ.get("EROS_OUTPUT", "eros_materialized")).resolve()
ROOT = Path(os.environ.get("EROS_REVIEW_OUTPUT", "eros_review_v1_2")).resolve()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def export_set(mesh: trimesh.Trimesh, stem: Path) -> dict:
    stem.parent.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for extension in ("glb", "obj", "stl", "ply"):
        path = stem.with_suffix("." + extension)
        mesh.export(path)
        outputs[path.name] = {
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
    return outputs


def mesh_record(mesh: trimesh.Trimesh) -> dict:
    return {
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "connected_components": int(mesh.body_count),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "euler_number": int(mesh.euler_number),
        "bounds": np.asarray(mesh.bounds).tolist(),
        "extents": np.asarray(mesh.extents).tolist(),
        "centroid": np.asarray(mesh.centroid).tolist(),
    }


def main() -> int:
    if ROOT.exists():
        shutil.rmtree(ROOT)
    for folder in (ROOT / "mesh/scientific", ROOT / "mesh/printable", ROOT / "metadata", ROOT / "docs"):
        folder.mkdir(parents=True, exist_ok=True)

    nasa_path = SOURCE_ROOT / "source/nasa/NASA_Asteroid_433_Eros.stl"
    pds_table = SOURCE_ROOT / "source/pds/extracted/ver64q.tab"
    pds_label = SOURCE_ROOT / "source/pds/extracted/ver64q.xml"
    pds_kernel = SOURCE_ROOT / "source/pds/extracted/eros_alex.tpc.txt"
    receipt_path = SOURCE_ROOT / "metadata/materialization-receipt.json"
    for required in (nasa_path, pds_table, pds_label, pds_kernel, receipt_path):
        if not required.exists():
            raise RuntimeError(f"Missing materialized input: {required}")

    source_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if source_receipt.get("state") != "MATERIALIZED_OFFICIAL_SOURCE_READY_FOR_REVIEW":
        raise RuntimeError("Unexpected source materialization state")

    # PDS: use the declared plate table and remove only vertices unused by it.
    lines = [line for line in pds_table.read_text(encoding="utf-8").splitlines() if line.strip()]
    counts = lines[0].split()
    vertex_count, face_count = int(counts[-2]), int(counts[-1])
    vertices = np.array([[float(v) for v in line.split()[-3:]] for line in lines[1:1 + vertex_count]])
    faces = np.array([[int(v) for v in line.split()[-3:]] for line in lines[1 + vertex_count:1 + vertex_count + face_count]], dtype=np.int64)
    if faces.min() == 1:
        faces -= 1
    pds_raw = trimesh.Trimesh(vertices=vertices, faces=faces, process=False, validate=False)
    referenced = int(len(np.unique(faces.reshape(-1))))
    pds_mesh = pds_raw.copy()
    pds_mesh.remove_unreferenced_vertices()
    if len(pds_mesh.vertices) != referenced or len(pds_mesh.faces) != 49152:
        raise RuntimeError("PDS referenced-vertex or plate count drift")
    if not pds_mesh.is_watertight or pds_mesh.body_count != 1:
        raise RuntimeError("PDS full body must be one watertight component")

    # NASA: the official STL is a two-half printable layout.
    nasa_layout = trimesh.load_mesh(nasa_path, process=True, validate=False)
    halves = sorted(nasa_layout.split(only_watertight=False), key=lambda item: float(item.centroid[1]))
    if len(halves) != 2 or not all(item.is_watertight for item in halves):
        raise RuntimeError("NASA printable two-half classification failed")

    outputs = {
        "scientific": export_set(
            pds_mesh,
            ROOT / "mesh/scientific/433_Eros_PDS_Gaskell_Q64_FullBody_SourceCoordinates",
        ),
        "nasa_layout": export_set(
            nasa_layout,
            ROOT / "mesh/printable/433_Eros_NASA_Printable_Two_Half_Layout_SourceCoordinates",
        ),
        "nasa_halves": {},
    }
    for label, half in zip(("A", "B"), halves):
        outputs["nasa_halves"][label] = export_set(
            half,
            ROOT / f"mesh/printable/433_Eros_NASA_Printable_Half_{label}_SourceCoordinates",
        )

    qa = {
        "schema_version": "1.2.0",
        "object_id": "candidate:asteroid:eros",
        "state": "REPRESENTATION_QA_COMPLETE",
        "source_materialization_receipt": source_receipt["receipt_id"],
        "scientific_primary": {
            "source": "NASA PDS Gaskell V1.1 Q=64 vertex-facet product",
            "declared_vertices": vertex_count,
            "declared_faces": face_count,
            "referenced_vertices": referenced,
            "unused_duplicate_vertices_removed": vertex_count - referenced,
            "mesh": mesh_record(pds_mesh),
            "coordinate_units": {
                "label_state": "NOT_EXPLICITLY_DECLARED_IN_ver64q.xml",
                "policy": "Retain source numeric coordinates; do not rewrite the label.",
            },
            "coordinate_change": False,
            "facet_change": False,
            "silent_scaling": False,
            "silent_repair": False,
        },
        "nasa_printable": {
            "classification": "TWO_WATERTIGHT_PRINTABLE_ASSEMBLY_HALVES_IN_ONE_LAYOUT",
            "source_layout": mesh_record(nasa_layout),
            "half_A": mesh_record(halves[0]),
            "half_B": mesh_record(halves[1]),
            "scientific_full_body": False,
            "assembly_transform_asserted": False,
        },
        "comparison": {
            "direct_shape_error_score": "NOT_COMPUTED",
            "reason": "Printable halves lack an established assembly, scale and registration transform relative to the PDS body-fixed model.",
        },
        "hard_boundaries": {
            "navigation_grade": False,
            "mission_selected": False,
            "trajectory_solution": False,
            "extraction_feasibility": False,
            "silent_scaling": False,
            "silent_repair": False,
        },
        "outputs": outputs,
    }
    (ROOT / "metadata/representation-qa.json").write_text(json.dumps(qa, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/README.md").write_text(
        "# 433 Eros representation review v1.2\n\n"
        "Scientific primary: NASA PDS Gaskell Q=64 full-body mesh.\n\n"
        "Printable reference: NASA STL containing two watertight assembly halves.\n\n"
        "The review removes only PDS vertices unused by every plate. It performs no "
        "coordinate change, scaling, smoothing, assembly or mesh repair. The PDS "
        "vertex XML does not explicitly declare coordinate units, so source numeric "
        "values are retained without relabelling. This is not navigation-grade and "
        "does not select Eros for a mission.\n",
        encoding="utf-8",
    )

    files = []
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and path.name != "review-manifest.json":
            files.append({
                "path": path.relative_to(ROOT).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    manifest = {
        "schema_version": "1.2.0",
        "pack_id": "public-pack:433-eros-representation-review:1.2.0",
        "object_id": "candidate:asteroid:eros",
        "generated_utc": utc_now(),
        "state": "REPRESENTATION_QA_COMPLETE",
        "scientific_primary": "NASA PDS Gaskell Q=64",
        "nasa_printable_components": 2,
        "fabricated_mesh": False,
        "navigation_grade": False,
        "mission_selected": False,
        "silent_scaling": False,
        "silent_repair": False,
        "file_count": len(files),
        "files": files,
    }
    (ROOT / "review-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    archive = ROOT.parent / "433_Eros_Representation_Review_v1_2.zip"
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zip_file:
        for path in sorted(ROOT.rglob("*")):
            if path.is_file():
                zip_file.write(path, arcname=f"{ROOT.name}/{path.relative_to(ROOT).as_posix()}")
    checksum = archive.with_suffix(archive.suffix + ".sha256")
    checksum.write_text(f"{sha256(archive)}  {archive.name}\n", encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "archive": archive.name,
        "archive_sha256": sha256(archive),
        "scientific_vertices": len(pds_mesh.vertices),
        "scientific_faces": len(pds_mesh.faces),
        "nasa_halves": len(halves),
        "state": qa["state"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
