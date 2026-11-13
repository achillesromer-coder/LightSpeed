#!/usr/bin/env python3
"""Create Castalia public pack v1.2 from the corrected v1.1 pack.

Adds a canonical sorted-JSON digest for the dynamic JPL SBDB snapshot so that
semantic equality can be distinguished from harmless JSON key-order changes.
The original raw JPL bytes remain preserved and separately hashed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

V11_NAME = "4769_Castalia_Official_Public_Canonical_Object_Pack_v1_1"
V12_NAME = "4769_Castalia_Official_Public_Canonical_Object_Pack_v1_2"
EXPECTED_CANONICAL_JPL_SHA256 = "a7cddcd529a61b3264326298fd29cdda2998e62d2eea6125b027f1ccc2ae4e77"


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    output = args.output.resolve()
    source = output / V11_NAME
    target = output / V12_NAME
    if not source.exists():
        raise SystemExit(f"missing verified v1.1 folder: {source}")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)

    jpl_path = target / "source/jpl/JPL_SBDB_2004769.json"
    raw = jpl_path.read_bytes()
    parsed = json.loads(raw)
    canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    canonical_sha = hashlib.sha256(canonical).hexdigest()
    if canonical_sha != EXPECTED_CANONICAL_JPL_SHA256:
        raise RuntimeError(
            "JPL snapshot semantics changed from the reviewed baseline; hold for evidence review: "
            + canonical_sha
        )
    normalization = {
        "schema_version": "1.0.0",
        "object_id": "candidate:asteroid:castalia",
        "source": "source/jpl/JPL_SBDB_2004769.json",
        "retrieved_raw_sha256": hashlib.sha256(raw).hexdigest(),
        "canonical_json_method": "UTF-8 JSON, recursively sorted object keys, compact separators, arrays retained in source order",
        "canonical_json_sha256": canonical_sha,
        "reviewed_baseline_canonical_json_sha256": EXPECTED_CANONICAL_JPL_SHA256,
        "semantic_baseline_match": True,
        "note": "Raw JSON byte hashes may differ when the API changes object-key serialization order; the raw source is still preserved for provenance.",
        "generated_utc": now(),
    }
    write_json(target / "metadata/jpl-snapshot-normalization.json", normalization)

    obj_path = target / "metadata/4769_Castalia_Canonical_Object.json"
    obj = json.loads(obj_path.read_text(encoding="utf-8"))
    obj["version"] = "1.2.0"
    obj["jpl_snapshot_semantic_digest"] = canonical_sha
    obj["supersedes"] = {
        "artifact": V11_NAME,
        "reason": "Adds raw-versus-canonical JPL JSON digest semantics; scientific PDS source and mesh geometry unchanged.",
    }
    obj["created_utc"] = now()
    write_json(obj_path, obj)

    dossier_path = target / "docs/4769_Castalia_Public_Dossier.md"
    dossier = dossier_path.read_text(encoding="utf-8").replace("**Version:** `1.1.0`", "**Version:** `1.2.0`")
    dossier += """

## JPL snapshot comparison

The raw NASA/JPL SBDB response is preserved exactly as retrieved. Because JSON
object-key order is not semantically significant, this pack also records a
canonical sorted-JSON SHA-256. That digest permits later runs to distinguish a
real data change from harmless serialization-order differences.
"""
    dossier_path.write_text(dossier, encoding="utf-8")

    supersession_path = target / "docs/GEOMETRY_QA_AND_SUPERSESSION.md"
    supersession = supersession_path.read_text(encoding="utf-8")
    supersession += f"""

## v1.2 JPL serialization clarification

The previously delivered v1.0 and v1.1 workflow runs produced different raw
SHA-256 values for the JPL JSON while parsing to equal JSON objects. Both have
canonical sorted-JSON SHA-256:

`{canonical_sha}`

This is a serialization-order difference, not an orbital or physical-data
change. PDS source and every scientific mesh format remain byte-identical.
"""
    supersession_path.write_text(supersession, encoding="utf-8")

    receipt_path = target / "BUILD_RECEIPT.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["artifact"] = V12_NAME
    receipt["version"] = "1.2.0"
    receipt["generated_utc"] = now()
    receipt["supersedes"] = {
        "artifact": V11_NAME,
        "correction": "Distinguish raw JPL serialization hash from canonical semantic JSON hash.",
        "pds_source_and_scientific_mesh_bytes_changed": False,
        "jpl_raw_snapshot_preserved": True,
        "jpl_canonical_json_sha256": canonical_sha,
        "jpl_semantic_baseline_match": True,
    }
    write_json(receipt_path, receipt)

    readme_path = target / "README.md"
    readme = readme_path.read_text(encoding="utf-8").replace("Pack v1.1", "Pack v1.2")
    readme += "\nv1.2 adds a canonical semantic digest for the timestamped JPL JSON snapshot.\n"
    readme_path.write_text(readme, encoding="utf-8")

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
        "pack_id": "public-pack:4769-castalia-canonical-object:1.2.0",
        "object_id": "candidate:asteroid:castalia",
        "generated_utc": now(),
        "state": "PUBLIC_SOURCE_READY_OWNER_REVIEW",
        "official_scientific_mesh_included": True,
        "owner_release_required": True,
        "supersedes": V11_NAME,
        "pds_source_and_scientific_mesh_bytes_changed": False,
        "jpl_canonical_json_sha256": canonical_sha,
        "file_count": len(files),
        "files": files,
    }
    write_json(target / "manifest.json", manifest)

    for record in manifest["files"]:
        path = target / record["path"]
        if path.stat().st_size != record["size_bytes"] or sha256(path) != record["sha256"]:
            raise RuntimeError(f"manifest mismatch: {record['path']}")

    zip_path = output / f"{V12_NAME}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(target.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=f"{V12_NAME}/{path.relative_to(target).as_posix()}")
    (output / f"{V12_NAME}.zip.sha256").write_text(f"{sha256(zip_path)}  {zip_path.name}\n", encoding="utf-8")
    print(json.dumps({
        "artifact": zip_path.as_posix(),
        "size_bytes": zip_path.stat().st_size,
        "sha256": sha256(zip_path),
        "state": "PUBLIC_SOURCE_READY_OWNER_REVIEW",
        "jpl_canonical_json_sha256": canonical_sha,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
