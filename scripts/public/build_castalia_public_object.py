#!/usr/bin/env python3
"""Build a public-safe 4769 Castalia canonical-object review pack.

The builder retrieves official NASA PDS shape bytes and a timestamped NASA/JPL
SBDB record, preserves source files, exports review formats without changing the
source coordinates/facets, and emits a cryptographic manifest and bounded
receipt. It does not make navigation, trajectory, extraction, safety, mission
selection, impact-risk, or physical-command claims.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import requests
import trimesh

PDS_TAB = "https://sbnarchive.psi.edu/pds4/non_mission/compil.ast.radar.shape-models/data/4769castalia.tab"
PDS_XML = "https://sbnarchive.psi.edu/pds4/non_mission/compil.ast.radar.shape-models/data/4769castalia.xml"
JPL_SBDB = "https://ssd-api.jpl.nasa.gov/sbdb.api?spk=2004769&phys-par=1"
PDS_BUNDLE = "https://pds.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=urn%3Anasa%3Apds%3Acompil.ast.radar.shape-models&version=1.0"
JPL_HISTORY = "https://echo.jpl.nasa.gov/asteroids/4769_Castalia/cast04.html"
JPL_RADAR = "https://echo.jpl.nasa.gov/asteroids/4769_Castalia/cast02.html"
JPL_SHAPE = "https://echo.jpl.nasa.gov/publications/shape_of_castalia_abs.html"
NTRS_SHAPE = "https://ntrs.nasa.gov/citations/19970007014"
SCIENCE_DOI = "https://doi.org/10.1126/science.263.5149.940"

OBJECT_ID = "candidate:asteroid:castalia"
PACK_NAME = "4769_Castalia_Official_Public_Canonical_Object_Pack_v1_0"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def download(session: requests.Session, url: str, path: Path, minimum_bytes: int) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    with session.get(
        url,
        stream=True,
        timeout=(20, 180),
        headers={"User-Agent": "Cognigrex-Castalia-Public-Builder/1.0"},
    ) as response:
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type.lower():
            raise RuntimeError(f"HTML returned instead of source payload: {url}")
        with path.open("wb") as fh:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    fh.write(chunk)
    size = path.stat().st_size
    if size < minimum_bytes:
        raise RuntimeError(f"Payload too small: {path.name} ({size} bytes)")
    return {
        "url": url,
        "path": path.as_posix(),
        "size_bytes": size,
        "sha256": sha256(path),
        "content_type": content_type,
        "retrieved_utc": utc_now(),
    }


def parse_shape(path: Path) -> tuple[np.ndarray, np.ndarray]:
    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if parts[0].lower() == "v":
            vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
        elif parts[0].lower() == "f":
            faces.append([int(parts[1]) - 1, int(parts[2]) - 1, int(parts[3]) - 1])
    v = np.asarray(vertices, dtype=np.float64)
    f = np.asarray(faces, dtype=np.int64)
    if v.shape != (2048, 3):
        raise RuntimeError(f"Expected 2048 vertices, found {v.shape}")
    if f.shape != (4092, 3):
        raise RuntimeError(f"Expected 4092 facets, found {f.shape}")
    if f.min() < 0 or f.max() >= len(v):
        raise RuntimeError("Facet index outside vertex table")
    return v, f


def source_registry(downloads: dict) -> dict:
    return {
        "schema_version": "1.0.0",
        "object_id": OBJECT_ID,
        "reviewed_utc": utc_now(),
        "sources": {
            "pds_shape": {
                "authority": "NASA Planetary Data System Small Bodies Node",
                "identifier": "urn:nasa:pds:compil.ast.radar.shape-models::1.0",
                "doi": "10.26033/vtj1-tb13",
                "role": "Official radar-derived polyhedral shape model and detached PDS4 label",
                "bundle_url": PDS_BUNDLE,
                "tab_url": PDS_TAB,
                "xml_url": PDS_XML,
                "download_receipts": {
                    "tab": downloads["pds_tab"],
                    "xml": downloads["pds_xml"],
                },
            },
            "jpl_sbdb": {
                "authority": "NASA/JPL Solar System Dynamics",
                "role": "Timestamped current orbital and physical-parameter snapshot",
                "url": JPL_SBDB,
                "download_receipt": downloads["jpl_sbdb"],
            },
            "jpl_discovery_history": {
                "authority": "NASA/JPL",
                "role": "Discovery and 1989 observing history",
                "url": JPL_HISTORY,
            },
            "jpl_radar_history": {
                "authority": "NASA/JPL",
                "role": "Delay-Doppler observations, rotational coverage and resolution",
                "url": JPL_RADAR,
            },
            "hudson_ostro_shape": {
                "authority": "NASA/JPL / Science",
                "role": "Peer-reviewed shape-inversion interpretation",
                "url": JPL_SHAPE,
                "ntrs_url": NTRS_SHAPE,
                "doi": "10.1126/science.263.5149.940",
            },
        },
    }


def make_static_review(mesh: trimesh.Trimesh, path: Path) -> None:
    fig = plt.figure(figsize=(14, 11), dpi=190)
    fig.patch.set_facecolor("#010a17")
    views = [(25, 35, "oblique"), (0, 0, "+x"), (0, 90, "+y"), (90, 0, "+z")]
    v = mesh.vertices
    f = mesh.faces
    for idx, (elev, azim, title) in enumerate(views, 1):
        ax = fig.add_subplot(2, 2, idx, projection="3d")
        ax.set_facecolor("#010a17")
        ax.plot_trisurf(
            v[:, 0], v[:, 1], f, v[:, 2],
            color="#00c1b8", edgecolor="#0c5363", linewidth=0.07,
            antialiased=True, shade=True,
        )
        ax.view_init(elev=elev, azim=azim)
        ax.set_box_aspect(mesh.extents)
        ax.set_axis_off()
        ax.set_title(title, color="#e8b237", fontsize=12, pad=6)
    fig.suptitle(
        "4769 CASTALIA · NASA PDS RADAR-DERIVED SHAPE MODEL · ORTHOGRAPHIC REVIEW",
        color="#e8b237", fontsize=16, fontweight="bold",
    )
    fig.text(
        0.5, 0.02,
        "Source coordinates in kilometres · centre of mass origin · principal axes · z-axis spin/north pole",
        color="#b9cbd8", ha="center", fontsize=10,
    )
    plt.tight_layout(rect=(0, 0.04, 1, 0.95))
    plt.savefig(path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def make_interactive(mesh: trimesh.Trimesh, path: Path) -> None:
    v = mesh.vertices
    f = mesh.faces
    fig = go.Figure(data=[go.Mesh3d(
        x=v[:, 0], y=v[:, 1], z=v[:, 2],
        i=f[:, 0], j=f[:, 1], k=f[:, 2],
        color="#00c1b8", opacity=1.0, flatshading=False,
        lighting=dict(ambient=0.35, diffuse=0.7, specular=0.25, roughness=0.65),
        hovertemplate="x=%{x:.4f} km<br>y=%{y:.4f} km<br>z=%{z:.4f} km<extra></extra>",
        name="PDS radar shape",
    )])
    fig.update_layout(
        title="4769 Castalia — NASA PDS Radar-Derived Shape Model",
        paper_bgcolor="#010a17", plot_bgcolor="#010a17",
        font=dict(color="#eef6fa"),
        scene=dict(
            bgcolor="#010a17", aspectmode="data",
            xaxis=dict(title="X (km)", gridcolor="#16384f"),
            yaxis=dict(title="Y (km)", gridcolor="#16384f"),
            zaxis=dict(title="Z (km)", gridcolor="#16384f"),
            camera=dict(eye=dict(x=1.5, y=1.35, z=0.9)),
        ),
        margin=dict(l=0, r=0, t=60, b=0),
    )
    pio.write_html(fig, path, include_plotlyjs=True, full_html=True)


def make_board(stats: dict, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(16, 10), dpi=200)
    fig.patch.set_facecolor("#010a17")
    ax.set_facecolor("#010a17")
    ax.axis("off")
    ax.text(0.03, 0.94, "4769 CASTALIA — PUBLIC CANONICAL OBJECT", color="#e8b237", fontsize=24, fontweight="bold", transform=ax.transAxes)
    ax.text(0.03, 0.895, "Official NASA PDS radar shape · evidence and mission boundaries retained · v1.0.0", color="#b9cbd8", fontsize=13, transform=ax.transAxes)
    cards = [
        (0.03, 0.65, 0.28, 0.17, "IDENTITY", "(4769) Castalia\n1989 PB\nApollo near-Earth asteroid", "#00c1b8"),
        (0.35, 0.65, 0.28, 0.17, "DISCOVERY", "9 Aug 1989\nEleanor F. Helin\nPalomar 18-inch Schmidt", "#e8b237"),
        (0.67, 0.65, 0.30, 0.17, "RADAR FIRST", "First evidence for a\nbifurcated/double-lobed\nsmall Solar System body", "#00eeee"),
        (0.03, 0.41, 0.28, 0.17, "SCIENTIFIC MESH", f"{stats['vertices']:,} vertices\n{stats['faces']:,} triangular facets\nwatertight: {stats['watertight']}", "#00c1b8"),
        (0.35, 0.41, 0.28, 0.17, "MODEL FRAME", "Origin: centre of mass\nAxes: principal axes\nCoordinates: kilometres", "#e8b237"),
        (0.67, 0.41, 0.30, 0.17, "SHAPE RESULT", "Two irregular lobes\ncrevice depth 100–150 m\nradar-inversion model", "#ef8f55"),
    ]
    for x, y, w, h, title, body, color in cards:
        ax.add_patch(plt.Rectangle((x, y), w, h, transform=ax.transAxes, facecolor="#04162d", edgecolor=color, linewidth=2))
        ax.text(x + 0.02, y + h - 0.045, title, color=color, fontsize=13, fontweight="bold", transform=ax.transAxes)
        ax.text(x + 0.02, y + h - 0.09, body, color="#eef6fa", fontsize=11, va="top", transform=ax.transAxes, linespacing=1.4)
    ax.add_patch(plt.Rectangle((0.03, 0.09), 0.94, 0.22, transform=ax.transAxes, facecolor="#071e34", edgecolor="#184f6e", linewidth=2))
    ax.text(0.05, 0.255, "PUBLIC CLAIM BOUNDARY", color="#e8b237", fontsize=14, fontweight="bold", transform=ax.transAxes)
    ax.text(
        0.05, 0.19,
        "Not navigation-grade · not a current ephemeris · not a trajectory or delta-v solution · not a mission selection · "
        "not proof of composition, extractability, structural integrity, proximity safety or operational accessibility.",
        color="#eef6fa", fontsize=12, wrap=True, transform=ax.transAxes,
    )
    ax.text(0.05, 0.12, "Next question: how do Castalia's contact-binary geometry and close-orbit instability alter tagging, approach, extraction and recovery assumptions?", color="#00eeee", fontsize=12, transform=ax.transAxes)
    plt.savefig(path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def build(output: Path) -> Path:
    root = output / PACK_NAME
    if root.exists():
        shutil.rmtree(root)
    for sub in ["source/pds", "source/jpl", "mesh/scientific", "visuals", "metadata", "docs", "validation"]:
        (root / sub).mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    downloads = {
        "pds_tab": download(session, PDS_TAB, root / "source/pds/4769castalia.tab", 200_000),
        "pds_xml": download(session, PDS_XML, root / "source/pds/4769castalia.xml", 5_000),
        "jpl_sbdb": download(session, JPL_SBDB, root / "source/jpl/JPL_SBDB_2004769.json", 500),
    }

    vertices, faces = parse_shape(root / "source/pds/4769castalia.tab")
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False, validate=False)
    if not mesh.is_watertight:
        raise RuntimeError("Official PDS Castalia mesh is not watertight; no repair is permitted")
    if len(mesh.split(only_watertight=False)) != 1:
        raise RuntimeError("Expected one connected component")

    scientific = root / "mesh/scientific"
    mesh.export(scientific / "4769_Castalia_PDS_RadarShape_SourceCoordinates.glb")
    mesh.export(scientific / "4769_Castalia_PDS_RadarShape_SourceCoordinates.obj")
    mesh.export(scientific / "4769_Castalia_PDS_RadarShape_SourceCoordinates.stl")
    mesh.export(scientific / "4769_Castalia_PDS_RadarShape_SourceCoordinates.ply")

    stats = {
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
        "connected_components": int(len(mesh.split(only_watertight=False))),
        "euler_number": int(mesh.euler_number),
        "bounds_km": mesh.bounds.tolist(),
        "extents_km": mesh.extents.tolist(),
        "surface_area_km2": float(mesh.area),
        "signed_volume_km3": float(mesh.volume),
        "absolute_volume_km3": float(abs(mesh.volume)),
        "center_mass_km": mesh.center_mass.tolist(),
        "source_units": "kilometres",
        "source_origin": "centre of mass",
        "source_axes": "principal axes; z-axis spin vector/north pole",
        "coordinates_changed": False,
        "facets_changed": False,
        "smoothing": False,
        "repair": False,
        "decimation": False,
    }
    (root / "metadata/geometry-qa.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")

    sbdb = json.loads((root / "source/jpl/JPL_SBDB_2004769.json").read_text(encoding="utf-8"))
    shortname = sbdb.get("object", {}).get("shortname", "")
    if "4769" not in shortname or "Castalia" not in shortname:
        raise RuntimeError(f"Unexpected JPL record: {shortname!r}")

    registry = source_registry(downloads)
    (root / "metadata/source-registry.json").write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

    object_record = {
        "schema_version": "1.0.0",
        "object_id": OBJECT_ID,
        "public_name": "4769 Castalia",
        "aliases": ["(4769) Castalia", "1989 PB"],
        "object_type": "near_earth_asteroid",
        "orbit_group": sbdb.get("object", {}).get("orbit_class"),
        "discovery": {"date": "1989-08-09", "discoverer": "Eleanor F. Helin", "site": "Palomar Observatory 18-inch Schmidt"},
        "shape_state": {
            "scientific_surface_mesh": True,
            "authority": "NASA PDS Small Bodies Radar Shape Models",
            "model_method": "radar delay-Doppler inversion",
            "double_lobed": True,
            "contact_binary_language": "bifurcated/double-lobed; formation interpretation remains separate from geometry",
        },
        "portfolio_role": "third object in retained Eros → Anteros → Castalia comparison sequence",
        "mission_selected": False,
        "navigation_grade": False,
        "release_state": "PUBLIC_SOURCE_READY_OWNER_REVIEW",
        "jpl_snapshot_retrieved_utc": downloads["jpl_sbdb"]["retrieved_utc"],
        "created_utc": utc_now(),
    }
    (root / "metadata/4769_Castalia_Canonical_Object.json").write_text(json.dumps(object_record, indent=2) + "\n", encoding="utf-8")

    make_static_review(mesh, root / "visuals/4769_Castalia_PDS_RadarShape_Orthographic_Review.png")
    make_interactive(mesh, root / "visuals/4769_Castalia_PDS_RadarShape_Interactive.html")
    make_board(stats, root / "visuals/4769_Castalia_Public_Canonical_Object_Board.png")

    ext = stats["extents_km"]
    dossier = f"""# 4769 Castalia — Public Canonical Object Dossier

**Object ID:** `{OBJECT_ID}`  
**Version:** `1.0.0`  
**State:** `PUBLIC_SOURCE_READY_OWNER_REVIEW`

## Public definition

(4769) Castalia, provisional designation 1989 PB, is an Apollo near-Earth
asteroid discovered by Eleanor F. Helin on 9 August 1989 using Palomar
Observatory's 18-inch Schmidt telescope.

Arecibo and Goldstone radar observations during the August 1989 close approach
provided the first evidence for a bifurcated or double-lobed small Solar System
body. Hudson and Ostro's inversion of the delay-Doppler observations produced a
three-dimensional model with two distinct irregular kilometre-scale lobes and a
crevice approximately 100–150 metres deep.

## Official scientific representation

The included scientific mesh comes from the NASA Planetary Data System Small
Bodies Radar Shape Models bundle:

- bundle identifier: `urn:nasa:pds:compil.ast.radar.shape-models::1.0`;
- DOI: `10.26033/vtj1-tb13`;
- source vertices: **{stats['vertices']:,}**;
- source triangular facets: **{stats['faces']:,}**;
- source coordinate unit: **kilometres**;
- origin: **centre of mass**;
- axes: **principal axes**;
- z-axis: **spin vector / north pole**;
- connected components: **{stats['connected_components']}**;
- watertight: **{stats['watertight']}**;
- extents from the archived coordinates: **{ext[0]:.6f} × {ext[1]:.6f} × {ext[2]:.6f} km**.

The exported GLB, OBJ, STL and PLY retain the PDS source coordinates and facet
connectivity. No smoothing, scaling, repair, decimation or inferred topography
was applied.

## Observation and model boundary

The radar images covered roughly 60% of Castalia's approximately 4.07-hour
rotation during the strongest 22 August 1989 delay-Doppler sequence. The model
is an inversion product, not a direct photograph of every surface point.

The PDS mesh is appropriate for public visualisation, comparative geometry and
source-backed modelling. It is not by itself:

- a current ephemeris or navigation product;
- proof of the body's internal structure or formation history;
- a validated local slope, regolith or landing-hazard map;
- a trajectory, delta-v or close-approach solution;
- proof of extractable composition or resource value;
- a mission, tagging or extraction selection;
- a physical command or safety authorisation.

## Dynamic data policy

The complete NASA/JPL SBDB response is retained in `source/jpl` with retrieval
time and checksum. Orbital and physical parameters must remain attached to that
snapshot, its epoch, uncertainties and authority. Time-dependent mission work
must use approved JPL Horizons or equivalent evidence rather than treating this
mesh as an orbit model.

## Portfolio role

Castalia closes the retained Eros → Anteros → Castalia first-loop comparison:

- Eros: high-evidence full-body mission-derived shape baseline;
- Anteros: evidence-rich but shape-unresolved comparison;
- Castalia: radar-derived double-lobed geometry with strong proximity-dynamics
  implications.

This pack does not select among them. It provides the evidence required for the
next cross-analysis question: how does object geometry alter approach, tagging,
capacity, extraction, safety and recovery assumptions while preserving the
source horizon of each comparison?

## Primary public sources

- NASA PDS Small Bodies Radar Shape Models: {PDS_BUNDLE}
- NASA/JPL discovery history: {JPL_HISTORY}
- NASA/JPL radar observations: {JPL_RADAR}
- Hudson & Ostro shape abstract: {JPL_SHAPE}
- NASA NTRS record: {NTRS_SHAPE}
- Science DOI: {SCIENCE_DOI}
"""
    (root / "docs/4769_Castalia_Public_Dossier.md").write_text(dossier, encoding="utf-8")

    boundary = """# Public use and claim boundary

## Supported

- The archived PDS model has 2,048 vertices and 4,092 triangular facets.
- PDS declares kilometres, centre-of-mass origin and principal axes.
- Radar inversion supports a bifurcated/double-lobed geometry.
- The archived geometry can be used for visualisation and comparative modelling
  when its source, frame, units and limitations remain attached.

## Not supported by the mesh alone

- current orbit or impact risk;
- navigation-grade proximity operations;
- exact unseen topography or local hazard conditions;
- homogeneous density or gravity;
- formation mechanism;
- composition or extractability;
- mission selection, launch or physical execution.

All derived claims must retain their separate assumptions, evidence and review
state. Local output never self-promotes to canon.
"""
    (root / "docs/PUBLIC_USE_AND_CLAIM_BOUNDARY.md").write_text(boundary, encoding="utf-8")

    receipt = {
        "artifact": PACK_NAME,
        "object_id": OBJECT_ID,
        "version": "1.0.0",
        "state": "PUBLIC_SOURCE_READY_OWNER_REVIEW",
        "generated_utc": utc_now(),
        "source_downloads": downloads,
        "geometry": stats,
        "jpl_object": {
            "shortname": shortname,
            "spkid": sbdb.get("object", {}).get("spkid"),
            "orbit_class": sbdb.get("object", {}).get("orbit_class"),
        },
        "hard_boundaries": {
            "mission_selected": False,
            "navigation_grade": False,
            "trajectory_validated": False,
            "extraction_feasible": False,
            "physical_execution_authorised": False,
            "coordinates_changed": False,
            "facets_changed": False,
        },
        "next_gate": "Owner reviews Object 4; then cross-object Eros–Anteros–Castalia first-loop analysis may be generated as a separate artifact.",
    }
    (root / "BUILD_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    readme = """# 4769 Castalia Official Public Canonical Object Pack v1.0

Object 4 in the current public-artifact queue and the third member of the
retained Eros → Anteros → Castalia comparison sequence.

Start with:

1. `visuals/4769_Castalia_Public_Canonical_Object_Board.png`
2. `visuals/4769_Castalia_PDS_RadarShape_Interactive.html`
3. `docs/4769_Castalia_Public_Dossier.md`
4. `mesh/scientific/4769_Castalia_PDS_RadarShape_SourceCoordinates.glb`

The pack contains public NASA PDS/JPL source evidence only. It is not a mission,
navigation, extraction, safety or physical-command authorization.
"""
    (root / "README.md").write_text(readme, encoding="utf-8")

    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            files.append({
                "path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    manifest = {
        "schema_version": "1.0.0",
        "pack_id": "public-pack:4769-castalia-canonical-object:1.0.0",
        "object_id": OBJECT_ID,
        "generated_utc": utc_now(),
        "state": "PUBLIC_SOURCE_READY_OWNER_REVIEW",
        "official_scientific_mesh_included": True,
        "owner_release_required": True,
        "file_count": len(files),
        "files": files,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # Immediate internal readback.
    check = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    for record in check["files"]:
        path = root / record["path"]
        if path.stat().st_size != record["size_bytes"] or sha256(path) != record["sha256"]:
            raise RuntimeError(f"Manifest mismatch: {record['path']}")
    trimesh.load(scientific / "4769_Castalia_PDS_RadarShape_SourceCoordinates.glb", force="scene")
    trimesh.load(scientific / "4769_Castalia_PDS_RadarShape_SourceCoordinates.obj", force="mesh")
    trimesh.load(scientific / "4769_Castalia_PDS_RadarShape_SourceCoordinates.stl", force="mesh")

    zip_path = output / f"{PACK_NAME}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=f"{PACK_NAME}/{path.relative_to(root).as_posix()}")
    (output / f"{PACK_NAME}.zip.sha256").write_text(f"{sha256(zip_path)}  {zip_path.name}\n", encoding="utf-8")
    return zip_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = build(args.output.resolve())
    print(json.dumps({
        "artifact": result.as_posix(),
        "size_bytes": result.stat().st_size,
        "sha256": sha256(result),
        "state": "PUBLIC_SOURCE_READY_OWNER_REVIEW",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
