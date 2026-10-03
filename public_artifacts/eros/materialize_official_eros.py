#!/usr/bin/env python3
"""Materialize official public 433 Eros assets with source/derived separation.

This script downloads only public NASA/PDS/JPL sources. It performs no mission
selection, navigation analysis, silent scaling, smoothing, repair, or proprietary
Cognigrex protocol publication.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = Path(os.environ.get("EROS_OUTPUT", "eros_materialized")).resolve()
SOURCE = ROOT / "source"
DERIVED = ROOT / "derived"
META = ROOT / "metadata"
VISUALS = ROOT / "visuals"
DOCS = ROOT / "docs"

NASA_STL = (
    "https://raw.githubusercontent.com/nasa/NASA-3D-Resources/master/"
    "3D%20Printing/Asteroid%20433%20Eros/Asteroid%20433%20Eros.stl"
)
NASA_PNG = (
    "https://raw.githubusercontent.com/nasa/NASA-3D-Resources/master/"
    "3D%20Printing/Asteroid%20433%20Eros/Asteroid%20433%20Eros.png"
)
PDS_ZIP = (
    "https://sbnarchive.psi.edu/pds4/non_mission/"
    "gaskell.ast-eros.shape-model_V1_1.zip"
)
JPL_SBDB = "https://ssd-api.jpl.nasa.gov/sbdb.api?spk=2000433&phys-par=1"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def download(url: str, path: Path, minimum: int) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers={"User-Agent": "Cognigrex-Eros-Public-Materializer/1.1"})
    with urlopen(req, timeout=240) as response, path.open("wb") as out:
        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type.lower():
            raise RuntimeError(f"HTML returned for binary/data source: {url}")
        shutil.copyfileobj(response, out, length=1024 * 1024)
    size = path.stat().st_size
    if size < minimum:
        raise RuntimeError(f"Suspiciously small payload {path.name}: {size}")
    return {
        "url": url,
        "path": path.relative_to(ROOT).as_posix(),
        "size_bytes": size,
        "sha256": sha256(path),
        "content_type": content_type,
        "retrieved_utc": utc_now(),
    }


def mesh_stats(mesh: trimesh.Trimesh, source_units: str) -> dict:
    return {
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "bounds_source_units": np.asarray(mesh.bounds).tolist(),
        "extents_source_units": np.asarray(mesh.extents).tolist(),
        "centroid_source_units": np.asarray(mesh.centroid).tolist(),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "euler_number": int(mesh.euler_number),
        "source_units": source_units,
        "silent_scaling": False,
        "silent_repair": False,
    }


def numeric_tokens(line: str) -> list[str]:
    return line.strip().replace(",", " ").split()


def parse_pds_vertex_facet(path: Path) -> tuple[trimesh.Trimesh, dict]:
    lines = [line for line in path.read_text(encoding="utf-8", errors="strict").splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("Empty PDS vertex-facet file")

    first = numeric_tokens(lines[0])
    start = 1
    if len(first) >= 2:
        try:
            vertex_count, face_count = int(first[-2]), int(first[-1])
        except ValueError as exc:
            raise RuntimeError(f"Unrecognised PDS counts row: {lines[0]!r}") from exc
    elif len(lines) >= 2:
        try:
            vertex_count, face_count = int(first[-1]), int(numeric_tokens(lines[1])[-1])
            start = 2
        except ValueError as exc:
            raise RuntimeError("Unrecognised PDS count records") from exc
    else:
        raise RuntimeError("Missing PDS count records")

    expected = start + vertex_count + face_count
    if len(lines) < expected:
        raise RuntimeError(
            f"PDS record underflow: got {len(lines)}, expected at least {expected} "
            f"for {vertex_count} vertices and {face_count} faces"
        )

    vertices = []
    for line in lines[start : start + vertex_count]:
        tokens = numeric_tokens(line)
        if len(tokens) < 3:
            raise RuntimeError(f"Bad vertex row: {line!r}")
        vertices.append([float(tokens[-3]), float(tokens[-2]), float(tokens[-1])])

    faces = []
    for line in lines[start + vertex_count : start + vertex_count + face_count]:
        tokens = numeric_tokens(line)
        if len(tokens) < 3:
            raise RuntimeError(f"Bad plate row: {line!r}")
        faces.append([int(tokens[-3]), int(tokens[-2]), int(tokens[-1])])

    vertices_np = np.asarray(vertices, dtype=np.float64)
    faces_np = np.asarray(faces, dtype=np.int64)
    if faces_np.min() == 1:
        faces_np -= 1
    if faces_np.min() < 0 or faces_np.max() >= vertex_count:
        raise RuntimeError(
            f"PDS face index outside vertex table: min={faces_np.min()} max={faces_np.max()} "
            f"vertex_count={vertex_count}"
        )

    mesh = trimesh.Trimesh(vertices=vertices_np, faces=faces_np, process=False, validate=False)
    return mesh, {
        "counts_row": lines[0],
        "declared_vertices": vertex_count,
        "declared_faces": face_count,
        "parsed_lines": expected,
        "trailing_nonempty_lines": max(0, len(lines) - expected),
    }


def export_mesh(mesh: trimesh.Trimesh, prefix: Path) -> dict:
    prefix.parent.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for suffix in ("glb", "obj", "stl", "ply"):
        path = prefix.with_suffix("." + suffix)
        mesh.export(path)
        outputs[path.name] = {"size_bytes": path.stat().st_size, "sha256": sha256(path)}
    return outputs


def render_mesh(mesh: trimesh.Trimesh, path: Path, title: str, max_faces: int = 22000) -> None:
    faces = np.asarray(mesh.faces)
    if len(faces) > max_faces:
        indices = np.linspace(0, len(faces) - 1, max_faces, dtype=int)
        faces = faces[indices]
    tris = np.asarray(mesh.vertices)[faces]
    fig = plt.figure(figsize=(12, 8), dpi=180)
    fig.patch.set_facecolor("#010a17")
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#010a17")
    poly = Poly3DCollection(tris, linewidths=0.02, alpha=1.0)
    poly.set_facecolor("#8a7968")
    poly.set_edgecolor("#1c1511")
    ax.add_collection3d(poly)
    bounds = np.asarray(mesh.bounds)
    centre = bounds.mean(axis=0)
    radius = float(np.max(bounds[1] - bounds[0]) / 2.0)
    for setter, value in ((ax.set_xlim, centre[0]), (ax.set_ylim, centre[1]), (ax.set_zlim, centre[2])):
        setter(value - radius, value + radius)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=23, azim=35)
    ax.set_axis_off()
    ax.set_title(title, color="#e8b237", fontsize=15, pad=18, fontweight="bold")
    plt.tight_layout(pad=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def normalised_copy(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    copy = mesh.copy()
    copy.apply_translation(-copy.bounds.mean(axis=0))
    maximum = float(np.max(copy.extents))
    if maximum <= 0:
        raise RuntimeError("Cannot normalise zero-size mesh")
    copy.apply_scale(2.0 / maximum)
    return copy


def comparison_visual(nasa_mesh: trimesh.Trimesh, pds_mesh: trimesh.Trimesh, path: Path) -> None:
    a = normalised_copy(nasa_mesh)
    b = normalised_copy(pds_mesh)
    a.apply_translation([-1.35, 0, 0])
    b.apply_translation([1.35, 0, 0])
    fig = plt.figure(figsize=(14, 7), dpi=180)
    fig.patch.set_facecolor("#010a17")
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#010a17")
    for mesh, colour in ((a, "#9b826c"), (b, "#00a99d")):
        faces = np.asarray(mesh.faces)
        if len(faces) > 16000:
            faces = faces[np.linspace(0, len(faces) - 1, 16000, dtype=int)]
        poly = Poly3DCollection(np.asarray(mesh.vertices)[faces], linewidths=0.01, alpha=0.98)
        poly.set_facecolor(colour)
        poly.set_edgecolor("#171717")
        ax.add_collection3d(poly)
    ax.text(-1.35, 0, 1.35, "NASA PRINTABLE STL", color="#e8b237", ha="center", fontsize=10, fontweight="bold")
    ax.text(1.35, 0, 1.35, "PDS GASKELL Q=64", color="#00eee8", ha="center", fontsize=10, fontweight="bold")
    ax.text(0, 0, -1.55, "NORMALISED VISUAL COMPARISON ONLY — SOURCE UNITS RETAINED SEPARATELY", color="#b9cbd8", ha="center", fontsize=8)
    ax.set_xlim(-2.6, 2.6); ax.set_ylim(-1.6, 1.6); ax.set_zlim(-1.7, 1.7)
    ax.set_box_aspect((2.0, 1.15, 1.15))
    ax.view_init(elev=22, azim=34)
    ax.set_axis_off()
    ax.set_title("433 EROS — OFFICIAL REPRESENTATION CROSS-CHECK", color="#e8b237", fontsize=15, pad=16, fontweight="bold")
    plt.tight_layout(pad=0)
    plt.savefig(path, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


def main() -> int:
    if ROOT.exists():
        shutil.rmtree(ROOT)
    for folder in (SOURCE, DERIVED, META, VISUALS, DOCS):
        folder.mkdir(parents=True, exist_ok=True)

    downloads = {}
    downloads["nasa_stl"] = download(NASA_STL, SOURCE / "nasa" / "NASA_Asteroid_433_Eros.stl", 8_000_000)
    downloads["nasa_preview"] = download(NASA_PNG, SOURCE / "nasa" / "NASA_Asteroid_433_Eros.png", 50_000)
    downloads["pds_bundle"] = download(PDS_ZIP, SOURCE / "pds" / "gaskell.ast-eros.shape-model_V1_1.zip", 70_000_000)
    downloads["jpl_sbdb"] = download(JPL_SBDB, SOURCE / "jpl" / "JPL_SBDB_2000433.json", 1_000)

    pds_zip = SOURCE / "pds" / "gaskell.ast-eros.shape-model_V1_1.zip"
    extract = SOURCE / "pds" / "extracted"
    extract.mkdir(parents=True, exist_ok=True)
    wanted_suffixes = (
        "/data/vertex/ver64q.tab",
        "/data/vertex/ver64q.xml",
        "/document/eros_alex.tpc.txt",
        "/document/icqmodel.txt",
        "/document/bundle_description.txt",
        "/bundle_gaskell.ast-eros.shape-model.xml",
    )
    extracted = {}
    with zipfile.ZipFile(pds_zip) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"Corrupt PDS ZIP member: {bad}")
        for member in archive.namelist():
            if member.endswith(wanted_suffixes):
                destination = extract / Path(member).name
                with archive.open(member) as source, destination.open("wb") as out:
                    shutil.copyfileobj(source, out)
                extracted[destination.name] = {
                    "archive_member": member,
                    "size_bytes": destination.stat().st_size,
                    "sha256": sha256(destination),
                }
    for required in ("ver64q.tab", "ver64q.xml", "eros_alex.tpc.txt", "icqmodel.txt"):
        if required not in extracted:
            raise RuntimeError(f"Required PDS member missing: {required}")

    jpl = json.loads((SOURCE / "jpl" / "JPL_SBDB_2000433.json").read_text(encoding="utf-8"))
    if jpl.get("object", {}).get("shortname") != "433 Eros":
        raise RuntimeError(f"Unexpected JPL object: {jpl.get('object')}")

    nasa_mesh = trimesh.load_mesh(SOURCE / "nasa" / "NASA_Asteroid_433_Eros.stl", process=False, validate=False)
    if not isinstance(nasa_mesh, trimesh.Trimesh) or len(nasa_mesh.faces) < 100_000:
        raise RuntimeError("NASA STL geometry is missing or unexpectedly small")
    pds_mesh, pds_parse = parse_pds_vertex_facet(extract / "ver64q.tab")
    if len(pds_mesh.faces) < 40_000:
        raise RuntimeError("PDS Q=64 geometry is unexpectedly small")

    nasa_outputs = export_mesh(nasa_mesh, DERIVED / "nasa_visual" / "433_Eros_NASA_Printable_SourceCoordinates")
    pds_outputs = export_mesh(pds_mesh, DERIVED / "pds_scientific" / "433_Eros_PDS_Gaskell_Q64_SourceCoordinates")
    render_mesh(nasa_mesh, VISUALS / "433_Eros_NASA_STL_Preview.png", "433 EROS — NASA PRINTABLE STL")
    render_mesh(pds_mesh, VISUALS / "433_Eros_PDS_Gaskell_Q64_Preview.png", "433 EROS — NASA PDS GASKELL Q=64")
    comparison_visual(nasa_mesh, pds_mesh, VISUALS / "433_Eros_Official_Representation_Comparison.png")

    elements = {item["name"]: item for item in jpl.get("orbit", {}).get("elements", [])}
    phys = {item["name"]: item for item in jpl.get("phys_par", [])}
    jpl_summary = {
        "retrieved_utc": downloads["jpl_sbdb"]["retrieved_utc"],
        "signature": jpl.get("signature"),
        "object": jpl.get("object"),
        "orbit": {
            "orbit_id": jpl.get("orbit", {}).get("orbit_id"),
            "epoch": jpl.get("orbit", {}).get("epoch"),
            "solution_date": jpl.get("orbit", {}).get("soln_date"),
            "condition_code": jpl.get("orbit", {}).get("condition_code"),
            "elements": elements,
        },
        "physical_parameters": phys,
        "navigation_grade": False,
    }
    (META / "JPL_SBDB_snapshot_summary.json").write_text(json.dumps(jpl_summary, indent=2) + "\n", encoding="utf-8")

    receipt = {
        "schema_version": "1.0.0",
        "receipt_id": "EROS-MATERIALIZATION-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "created_utc": utc_now(),
        "object_id": "candidate:asteroid:eros",
        "state": "MATERIALIZED_OFFICIAL_SOURCE_READY_FOR_REVIEW",
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "trimesh": trimesh.__version__,
            "numpy": np.__version__,
            "matplotlib": matplotlib.__version__,
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_ref": os.environ.get("GITHUB_REF"),
        },
        "downloads": downloads,
        "pds_extracted": extracted,
        "geometry": {
            "nasa_printable_stl": mesh_stats(nasa_mesh, "NASA printable model units; scale statement is external to STL"),
            "pds_gaskell_q64": mesh_stats(pds_mesh, "kilometres per PDS vertex-table label"),
            "pds_parse": pds_parse,
        },
        "generated": {
            "nasa_visual": nasa_outputs,
            "pds_scientific": pds_outputs,
            "visuals": {
                path.name: {"size_bytes": path.stat().st_size, "sha256": sha256(path)}
                for path in sorted(VISUALS.glob("*.png"))
            },
        },
        "jpl_object": {
            "shortname": jpl["object"]["shortname"],
            "spkid": jpl["object"]["spkid"],
            "orbit_class": jpl["object"].get("orbit_class"),
            "orbit_id": jpl.get("orbit", {}).get("orbit_id"),
            "epoch": jpl.get("orbit", {}).get("epoch"),
        },
        "scientific_shape_source_retrieved": True,
        "nasa_visual_source_retrieved": True,
        "navigation_grade": False,
        "mission_selected": False,
        "silent_scaling": False,
        "silent_repair": False,
        "normalised_comparison_is_derived_visual_only": True,
        "next_gate": "Review source labels, frame, dimensions, hashes and cross-representation differences before public release or mission use.",
    }
    (META / "materialization-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    (DOCS / "README.md").write_text(
        "# 433 Eros Official Materialised Public Pack\n\n"
        "This pack contains official NASA, NASA PDS and NASA/JPL public sources, "
        "plus clearly separated derived format conversions and previews.\n\n"
        "The NASA printable STL and PDS Gaskell Q=64 mesh retain their original "
        "source coordinates. The side-by-side comparison is normalised for visual "
        "inspection only. No source mesh was silently scaled, repaired or smoothed.\n\n"
        "This is not navigation-grade, does not select Eros for a mission, and does "
        "not establish trajectory, extraction, safety or operational feasibility.\n",
        encoding="utf-8",
    )

    files = []
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and path.name != "asset-manifest.json":
            files.append({
                "path": path.relative_to(ROOT).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    manifest = {
        "schema_version": "1.0.0",
        "pack_id": "public-pack:433-eros-official-materialized:1.1.0",
        "object_id": "candidate:asteroid:eros",
        "generated_utc": utc_now(),
        "state": receipt["state"],
        "official_source_files_present": True,
        "fabricated_mesh_present": False,
        "mission_selected": False,
        "navigation_grade": False,
        "silent_scaling": False,
        "silent_repair": False,
        "file_count": len(files),
        "files": files,
    }
    (ROOT / "asset-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # Final self-check.
    if receipt["navigation_grade"] or receipt["mission_selected"] or receipt["silent_scaling"] or receipt["silent_repair"]:
        raise RuntimeError("Safety boundary drift")
    for record in manifest["files"]:
        path = ROOT / record["path"]
        if path.stat().st_size != record["size_bytes"] or sha256(path) != record["sha256"]:
            raise RuntimeError(f"Manifest mismatch: {record['path']}")

    archive = ROOT.parent / "433_Eros_Official_Materialized_Public_Pack_v1_1.zip"
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(ROOT.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=f"{ROOT.name}/{path.relative_to(ROOT).as_posix()}")
    checksum = archive.with_suffix(archive.suffix + ".sha256")
    checksum.write_text(f"{sha256(archive)}  {archive.name}\n", encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "archive": archive.name,
        "archive_size_bytes": archive.stat().st_size,
        "archive_sha256": sha256(archive),
        "nasa_faces": len(nasa_mesh.faces),
        "pds_faces": len(pds_mesh.faces),
        "manifest_files": manifest["file_count"],
        "state": receipt["state"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
