#!/usr/bin/env python3
"""Create Castalia public pack v1.1 from the verified v1.0 build.

Presentation-only supersession:
- replaces unsupported "contact-binary" shorthand with source-backed
  "bifurcated/double-lobed" wording;
- converts ephemeral CI paths in receipts to portable pack-relative paths;
- records supersession and source-byte invariance;
- rebuilds the public board, manifest, ZIP and checksum.

Official PDS/JPL source bytes and all scientific mesh coordinates/facets remain
unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt

V10_NAME = "4769_Castalia_Official_Public_Canonical_Object_Pack_v1_0"
V11_NAME = "4769_Castalia_Official_Public_Canonical_Object_Pack_v1_1"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def make_board(stats: dict, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(16, 10), dpi=200)
    fig.patch.set_facecolor("#010a17")
    ax.set_facecolor("#010a17")
    ax.axis("off")
    ax.text(0.03, 0.94, "4769 CASTALIA — PUBLIC CANONICAL OBJECT", color="#e8b237", fontsize=24, fontweight="bold", transform=ax.transAxes)
    ax.text(0.03, 0.895, "Official NASA PDS radar shape · evidence and mission boundaries retained · v1.1.0", color="#b9cbd8", fontsize=13, transform=ax.transAxes)
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
    ax.text(
        0.05, 0.12,
        "Next question: how does Castalia's bifurcated/double-lobed geometry alter tagging, approach, extraction and recovery assumptions?",
        color="#00eeee", fontsize=12, transform=ax.transAxes,
    )
    plt.savefig(path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def normalize_receipt_paths(value: object) -> object:
    if isinstance(value, dict):
        result = {k: normalize_receipt_paths(v) for k, v in value.items()}
        url = result.get("url")
        if isinstance(url, str):
            if url.endswith("4769castalia.tab"):
                result["path"] = "source/pds/4769castalia.tab"
            elif url.endswith("4769castalia.xml"):
                result["path"] = "source/pds/4769castalia.xml"
            elif "sbdb.api" in url:
                result["path"] = "source/jpl/JPL_SBDB_2004769.json"
        return result
    if isinstance(value, list):
        return [normalize_receipt_paths(v) for v in value]
    return value


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    output = args.output.resolve()
    source = output / V10_NAME
    target = output / V11_NAME
    if not source.exists():
        raise SystemExit(f"missing verified v1.0 folder: {source}")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)

    source_hashes = {
        rel: sha256(target / rel)
        for rel in [
            "source/pds/4769castalia.tab",
            "source/pds/4769castalia.xml",
            "source/jpl/JPL_SBDB_2004769.json",
            "mesh/scientific/4769_Castalia_PDS_RadarShape_SourceCoordinates.glb",
            "mesh/scientific/4769_Castalia_PDS_RadarShape_SourceCoordinates.obj",
            "mesh/scientific/4769_Castalia_PDS_RadarShape_SourceCoordinates.stl",
            "mesh/scientific/4769_Castalia_PDS_RadarShape_SourceCoordinates.ply",
        ]
    }

    registry_path = target / "metadata/source-registry.json"
    registry = normalize_receipt_paths(json.loads(registry_path.read_text(encoding="utf-8")))
    registry["reviewed_utc"] = now()
    write_json(registry_path, registry)

    object_path = target / "metadata/4769_Castalia_Canonical_Object.json"
    obj = json.loads(object_path.read_text(encoding="utf-8"))
    obj["version"] = "1.1.0"
    shape = obj["shape_state"]
    shape.pop("contact_binary_language", None)
    shape["interpretation_boundary"] = (
        "Bifurcated/double-lobed geometry is supported; formation as a contact binary is not asserted by this pack."
    )
    obj["supersedes"] = {
        "artifact": V10_NAME,
        "reason": "Public wording and receipt portability correction; scientific source and mesh bytes unchanged.",
    }
    obj["created_utc"] = now()
    write_json(object_path, obj)

    dossier_path = target / "docs/4769_Castalia_Public_Dossier.md"
    dossier = dossier_path.read_text(encoding="utf-8")
    dossier = dossier.replace("**Version:** `1.0.0`", "**Version:** `1.1.0`")
    dossier_path.write_text(dossier, encoding="utf-8")

    stats = json.loads((target / "metadata/geometry-qa.json").read_text(encoding="utf-8"))
    make_board(stats, target / "visuals/4769_Castalia_Public_Canonical_Object_Board.png")

    supersession = f"""# Geometry QA and v1.1 supersession

## Supersession

This pack supersedes `{V10_NAME}` at the public-presentation layer.

The v1.0 scientific sources and mesh were valid. The independent circle-back
identified two public-fidelity corrections:

1. a board question used `contact-binary` as shorthand where the directly
   supported wording is `bifurcated/double-lobed`;
2. source receipts exposed ephemeral GitHub runner paths instead of portable
   pack-relative paths.

## Scientific invariance

The following source and mesh hashes are unchanged from v1.0:

```json
{json.dumps(source_hashes, indent=2)}
```

No source coordinate, facet, scale, frame, smoothing, repair, decimation or
scientific interpretation was altered.
"""
    (target / "docs/GEOMETRY_QA_AND_SUPERSESSION.md").write_text(supersession, encoding="utf-8")

    receipt_path = target / "BUILD_RECEIPT.json"
    receipt = normalize_receipt_paths(json.loads(receipt_path.read_text(encoding="utf-8")))
    receipt["artifact"] = V11_NAME
    receipt["version"] = "1.1.0"
    receipt["generated_utc"] = now()
    receipt["supersedes"] = {
        "artifact": V10_NAME,
        "corrections": [
            "Use bifurcated/double-lobed rather than contact-binary shorthand.",
            "Use portable pack-relative receipt paths rather than ephemeral runner paths.",
        ],
        "scientific_source_and_mesh_bytes_changed": False,
        "invariant_hashes": source_hashes,
    }
    write_json(receipt_path, receipt)

    readme_path = target / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    readme = readme.replace("Pack v1.0", "Pack v1.1")
    readme += "\nThis version supersedes v1.0 for public presentation; official source and scientific mesh bytes are unchanged.\n"
    readme_path.write_text(readme, encoding="utf-8")

    # No ephemeral runner paths may remain.
    for path in target.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".md", ".txt"}:
            if "/home/runner/" in path.read_text(encoding="utf-8", errors="ignore"):
                raise RuntimeError(f"ephemeral path remains: {path}")

    files = []
    for path in sorted(target.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            files.append({
                "path": path.relative_to(target).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    manifest = {
        "schema_version": "1.0.0",
        "pack_id": "public-pack:4769-castalia-canonical-object:1.1.0",
        "object_id": "candidate:asteroid:castalia",
        "generated_utc": now(),
        "state": "PUBLIC_SOURCE_READY_OWNER_REVIEW",
        "official_scientific_mesh_included": True,
        "owner_release_required": True,
        "supersedes": V10_NAME,
        "scientific_source_and_mesh_bytes_changed": False,
        "file_count": len(files),
        "files": files,
    }
    write_json(target / "manifest.json", manifest)

    for record in manifest["files"]:
        path = target / record["path"]
        if path.stat().st_size != record["size_bytes"] or sha256(path) != record["sha256"]:
            raise RuntimeError(f"manifest mismatch: {record['path']}")

    zip_path = output / f"{V11_NAME}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(target.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=f"{V11_NAME}/{path.relative_to(target).as_posix()}")
    (output / f"{V11_NAME}.zip.sha256").write_text(f"{sha256(zip_path)}  {zip_path.name}\n", encoding="utf-8")
    print(json.dumps({
        "artifact": zip_path.as_posix(),
        "size_bytes": zip_path.stat().st_size,
        "sha256": sha256(zip_path),
        "state": "PUBLIC_SOURCE_READY_OWNER_REVIEW",
        "scientific_bytes_changed": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
