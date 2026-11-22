#!/usr/bin/env python3
"""PrintSpace reproducible PRIVATE software-review RC packager and strict verifier.

This is a release-candidate *digital demonstrator* zip, not a signed release,
licence clearance, native LOAD admission or a machine-control executable.
No network, external downloads, git changes or native DBR writes.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cgx.manufacturing.virtual_factory import validate_catalogue, canonical_digest
from cgx.manufacturing.printspace_cgx import build_bundle, h0_handshake, unpack_lite
from cgx.manufacturing.printspace_host_preflight import prepare_r0_host_review

SCHEMA = "CGX-PRINTSPACE-SOFTWARE-PRIVATE-RC/0.1"
VERSION = "0.1.0-rc.1"
ZIP_NAME = f"PrintSpace_Software_{VERSION}_PRIVATE.zip"
ZIP_DATE = (1980, 1, 1, 0, 0, 0)
MAX_BYTES = 8 * 1024 * 1024
MAX_FILE = 2 * 1024 * 1024
MAX_FILES = 24
ASSETS = {
    "cgx/manufacturing/printspace_studio_v0_1.html": "PrintSpace.Studio.offline.html",
    "cgx/manufacturing/printspace_virtual_factory_catalog_v0_1.json": "data/virtual-factory-catalogue.json",
    "cgx/manufacturing/printspace_cgx_bundle_v0_1.json": "data/cgx-80-facet-bundle.json",
    "cgx/manufacturing/printspace_cgx_h0_v0_1.json": "data/load-lite-h0.json",
    "cgx/manufacturing/printspace_cgx_lite_v0_1.json": "data/lossless-cgx-compatibility-transport.json",
    "cgx/manufacturing/printspace_host_r0_review_v0_1.json": "data/unispace-r0-review-only.json",
    "docs/engineering/PRINTSPACE_VIRTUAL_FACTORY_RELEASE_GATES_2026-11-22.md": "engineering/virtual-factory-release-gates.md",
    "docs/engineering/PRINTSPACE_CGX_FILESPACE_FACETS_2026-11-22.md": "engineering/cgx-filespace-facets.md",
}
MANIFEST = "MANIFEST.json"
SAFETY_FLAGS = (
    "public_distribution_approved", "rights_independently_cleared",
    "source_cad_independently_verified", "real_material_lots_verified",
    "physical_process_qualified", "physical_machine_authorised",
    "native_load_admitted", "native_dbr_written", "mint_authorised",
    "commercial_release_authorised", "printed_phone_functionality_verified",
)
README = """# PrintSpace Studio — private software release candidate 0.1.0-rc.1

**Private owner evaluation only. Not approved for public distribution.**

Open `PrintSpace.Studio.offline.html` directly in a modern browser. No account,
network, server, installer, API key, machine, database or plugin is required.
Orbit/zoom the conceptual printer, choose a diode/board/phone-scale illustrative
assembly, adjust *independent* printer/product scales, inspect the staged digital
process, and export the CGX H0 or symbolic package from the browser UI.

The bundled JSON is a content-addressed **source-only compatibility projection**.
The phone is a hybrid conceptual assembly, not a working printed device. Sizes,
printer envelopes, terrestrial/remote atmosphere, materials and parts are
synthetic. No measured hardware precision, toolpath, functional electronics,
physical material compatibility, native CGX hydration or in-situ qualification
is established by these files. No machine commands exist in this package.

`MANIFEST.json` gives exact bytes and SHA-256 hashes. The companion `.sha256`
file verifies the ZIP bytes but is not a signed publisher attestation. A buyer,
licensee or public visitor must **not** be given this package until the owner
separately approves rights, privacy, security, support, deployment and release.

Use `python scripts/package_printspace_software.py verify <ZIP> --sha256 <SIDECAR>`
from the source repository to validate the archive. See `RELEASE-GATES.md` for
open blockers. This is a private review snapshot, not a production installation.
"""
GATES = """# PrintSpace software RC: fixed proof ceiling and go/no-go

This package is **digital-viewer RC / private evaluation** only. Its deterministic
hashes prove internal consistency, not source origin, signer identity or ownership.

## Verified in this package
- Self-contained offline HTML 3D *conceptual* printer/assembly viewer
- Three nested diode / board / phone demonstration products
- 80 deduplicated symbolic CGX facets with an H0 nonhydrating source index
- Deterministic canonical data graph, source replay and lossless transport
- Eight source-listed files + strict SHA-256 metadata and offline ZIP verification

## Mandatory independent acceptance before public software launch
- Owner-controlled source and licence audit, distribution approval and trademarks
- Authenticated source registry, unique native Object_ID, ACL, signed DBR
- Reviewed UI/content accessibility, threat model, privacy and support plan
- Installer/platform matrix or accepted web distribution, user acceptance tests
- Independently witnessed deployment and post-deploy rollback/readback plan

## Independent physical manufacture / product-performance hold
- Calibrated actual printer geometry, thermal envelope, tooling and C0 safety
- Real material-lot passports and independently witnessed A→B / B→A coupons
- CAD/toolpath and external supplied components, electrical and safety testing
- Environmental terrestrial/remote process qualification and real test reports

Do not infer functioning phone manufacturing from rendered components. Continue
FileSpace software packaging only when PrintSpace software is separately
approved for its specified distribution scope. DataSpace follows FileSpace;
UniSpace launch follows accepted PrintSpace, FileSpace and DataSpace gates.
"""

class ReleaseHold(ValueError):
    pass


def _json(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=True,
                       allow_nan=False) + "\n").encode("utf-8")


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _bool_false(obj: dict, fields: tuple[str, ...], where: str) -> None:
    if any(obj.get(field) is not False for field in fields):
        raise ReleaseHold("UNACCEPTED_AUTHORITY_GATE:" + where)


def _source_bytes(root: Path, rel: str) -> bytes:
    path = root / rel
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ReleaseHold("MISSING_OR_UNSAFE_SOURCE:" + rel)
    if path.stat().st_size > MAX_FILE:
        raise ReleaseHold("SOURCE_SIZE_BUDGET:" + rel)
    return path.read_bytes()


def _verify_canonical_sources(files: dict[str, bytes]) -> dict:
    def get(name: str) -> dict:
        try:
            doc = json.loads(files[name].decode("utf-8"))
            if not isinstance(doc, dict):
                raise ValueError("object required")
            return doc
        except (KeyError, UnicodeDecodeError, ValueError) as exc:
            raise ReleaseHold("INVALID_SOURCE_JSON:" + name) from exc

    catalogue = get("data/virtual-factory-catalogue.json")
    validate_catalogue(catalogue)
    _bool_false(catalogue["attestations"], tuple(catalogue["attestations"]), "CATALOGUE")
    bundle = get("data/cgx-80-facet-bundle.json")
    if build_bundle(catalogue) != bundle or bundle.get("source_catalogue_sha256") != canonical_digest(catalogue):
        raise ReleaseHold("CGX_SOURCE_REPLAY_OR_CATALOGUE_HASH_MISMATCH")
    _bool_false(bundle, ("machine_authorised", "native_load_hydration", "mint_authorised",
                         "commercial_release_authorised"), "CGX_BUNDLE")
    if bundle.get("source_bytes_hydrated") != 0 or len(bundle["objects"]) != 80:
        raise ReleaseHold("CGX_HYDRATION_OR_OBJECT_CARDINALITY")
    h0 = get("data/load-lite-h0.json")
    if h0_handshake(bundle, expected_catalogue_sha256=bundle["source_catalogue_sha256"]) != h0:
        raise ReleaseHold("LOAD_H0_SOURCE_REPLAY")
    _bool_false(h0, ("machine_authorised", "native_admitted"), "LOAD_H0")
    if h0.get("source_bytes_hydrated") != 0:
        raise ReleaseHold("LOAD_H0_PRIVATE_SOURCE_BYTES")
    lite = get("data/lossless-cgx-compatibility-transport.json")
    if unpack_lite(lite, expected_catalogue_sha256=bundle["source_catalogue_sha256"]) != bundle:
        raise ReleaseHold("LOSSLESS_TRANSPORT_ROUNDTRIP")
    _bool_false(lite, ("native_dbr_written", "native_ternary_encoder", "physical_machine_authorised"), "CGX_COMPAT_TRANSPORT")
    r0 = get("data/unispace-r0-review-only.json")
    if prepare_r0_host_review(bundle, catalogue) != r0:
        raise ReleaseHold("R0_SOURCE_REPLAY_OR_NATIVE_ADMISSION")
    _bool_false(r0, ("native_admitted", "native_dbr_written", "machine_authorised",
                     "mint_authorised", "commercial_release_authorised", "trusted_host_authenticated"), "R0")
    if r0.get("source_bytes_hydrated") != 0 or r0.get("candidate_count") != 0:
        raise ReleaseHold("R0_NATIVE_OR_PRIVATE_ESCALATION")
    html = files["PrintSpace.Studio.offline.html"].decode("utf-8")
    if "PrintSpace Studio" not in html or "CGX_BUNDLE" not in html and "bundle_sha256" not in html:
        raise ReleaseHold("OFFLINE_STUDIO_NOT_FOUND")
    if any(re.search(p, html, flags=re.IGNORECASE) for p in (
            r"<script[^>]+\bsrc\s*=", r"<link[^>]+\bhref\s*=",
            r"\bfetch\s*\(", r"\bXMLHttpRequest\b", r"\bWebSocket\b",
            r"<iframe\b", r"https?://")):
        raise ReleaseHold("REMOTE_DEPENDENCY_IN_OFFLINE_STUDIO")
    return {"catalogue_sha256": bundle["source_catalogue_sha256"],
            "bundle_sha256": bundle["bundle_sha256"],
            "r0_plan_sha256": r0["plan_sha256"],
            "symbolic_facets": len(bundle["objects"]),
            "sample_products": len(catalogue["products"]),
            "native_admitted": False, "physical_machine_authorised": False}


def _payload(root: Path) -> tuple[dict[str, bytes], dict]:
    assets = {destination: _source_bytes(root, source) for source, destination in ASSETS.items()}
    reference = _verify_canonical_sources(assets)
    assets["README-START-HERE.md"] = README.encode("utf-8")
    assets["RELEASE-GATES.md"] = GATES.encode("utf-8")
    if len(assets) > MAX_FILES or sum(map(len, assets.values())) > MAX_BYTES:
        raise ReleaseHold("TOTAL_PACKAGING_BUDGET")
    index = [{"path": path, "bytes": len(payload), "sha256": _hash(payload),
              "source": next((key for key, value in ASSETS.items() if value == path), "BUILDER_GENERATED")}
             for path, payload in sorted(assets.items())]
    manifest = {
        "schema": SCHEMA, "version": VERSION, "product": "PrintSpace Studio / CGX digital review",
        "release_state": "PRIVATE_SOFTWARE_RC_REVIEW_ONLY",
        "distribution_scope": "OWNER_PRIVATE_EVALUATION_ONLY",
        "software_release_ready_for_public": False,
        "independent_signing_attestation": False,
        "proof_ceiling": "SYNTHETIC_DIGITAL_DEMONSTRATOR_ONLY",
        "source_reference": reference,
        "safety_flags": {key: False for key in SAFETY_FLAGS},
        "files": index,
        "manifest_hash_not_publisher_signature": True,
    }
    assets[MANIFEST] = _json(manifest)
    return assets, manifest


def _zip(assets: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9, allowZip64=False) as z:
        for name, payload in sorted(assets.items()):
            info = zipfile.ZipInfo(name, ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (0o100644 << 16)
            z.writestr(info, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output.getvalue()


def build(root: Path = ROOT) -> bytes:
    assets, _ = _payload(root)
    return _zip(assets)


def verify(data: bytes, *, sidecar: str | None = None, filename: str | None = None) -> dict:
    if not isinstance(data, bytes) or len(data) > MAX_BYTES:
        raise ReleaseHold("ARCHIVE_BYTE_BUDGET")
    if sidecar is not None:
        if filename is None or sidecar != f"{_hash(data)}  {filename}\n":
            raise ReleaseHold("UNMATCHED_ARCHIVE_SHA256_SIDECAR")
    try:
        with zipfile.ZipFile(io.BytesIO(data), mode="r") as z:
            names = z.namelist()
            if len(names) > MAX_FILES + 1 or len(names) != len(set(names)) or MANIFEST not in names:
                raise ReleaseHold("DUPLICATE_OR_MISSING_ARCHIVE_MEMBERS")
            if any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
                   or name.startswith("./") or "\\" in name or name.endswith("/")
                   or PurePosixPath(name).parts[0] in (".", "") for name in names):
                raise ReleaseHold("UNSAFE_ARCHIVE_MEMBER_PATH")
            if any(i.file_size > MAX_FILE or i.flag_bits & 0x1 or
                   i.compress_type != zipfile.ZIP_DEFLATED for i in z.infolist()):
                raise ReleaseHold("UNSAFE_ARCHIVE_MEMBER")
            if sum(i.file_size for i in z.infolist()) > MAX_BYTES:
                raise ReleaseHold("UNCOMPRESSED_ARCHIVE_BUDGET")
            if z.testzip() is not None:
                raise ReleaseHold("CORRUPT_ARCHIVE_CRC")
            manifest = json.loads(z.read(MANIFEST))
            if manifest.get("schema") != SCHEMA or manifest.get("version") != VERSION:
                raise ReleaseHold("MANIFEST_SCHEMA_OR_VERSION")
            if (manifest.get("release_state") != "PRIVATE_SOFTWARE_RC_REVIEW_ONLY"
                    or manifest.get("software_release_ready_for_public") is not False
                    or manifest.get("independent_signing_attestation") is not False
                    or manifest.get("manifest_hash_not_publisher_signature") is not True
                    or set(manifest.get("safety_flags", {})) != set(SAFETY_FLAGS)
                    or any(x is not False for x in manifest["safety_flags"].values())):
                raise ReleaseHold("MANIFEST_AUTHORITY_ESCALATION")
            files = manifest.get("files")
            if not isinstance(files, list) or len(files) != len(names) - 1:
                raise ReleaseHold("MANIFEST_MEMBER_COUNT")
            expected = set(ASSETS.values()) | {"README-START-HERE.md", "RELEASE-GATES.md"}
            if set(names) != expected | {MANIFEST}:
                raise ReleaseHold("UNEXPECTED_OR_MISSING_RELEASE_MEMBER")
            if [x["path"] for x in files] != sorted(expected):
                raise ReleaseHold("NONCANONICAL_MANIFEST_ORDER")
            payloads = {}
            for row in files:
                name = row["path"]
                body = z.read(name)
                if row.get("bytes") != len(body) or row.get("sha256") != _hash(body):
                    raise ReleaseHold("SOURCE_ASSET_INTEGRITY:" + name)
                payloads[name] = body
            metadata = _verify_canonical_sources(payloads)
            if manifest.get("source_reference") != metadata:
                raise ReleaseHold("MANIFEST_PROVENANCE_MISMATCH")
            if _json(manifest) != z.read(MANIFEST):
                raise ReleaseHold("NONCANONICAL_MANIFEST_JSON")
            return {"state": "PASS_PRIVATE_RC_INTEGRITY_ONLY", "version": VERSION,
                    "file_count": len(names), "sha256": _hash(data),
                    "public_distribution_approved": False, "physical_machine_authorised": False,
                    "native_admitted": False, "integrity_not_publisher_signature": True}
    except (zipfile.BadZipFile, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError,
            OSError, OverflowError, RuntimeError) as exc:
        if isinstance(exc, ReleaseHold):
            raise
        raise ReleaseHold("CORRUPT_OR_INVALID_RELEASE_ARCHIVE") from exc


def write_release(root: Path, out_dir: Path, *, check: bool = False) -> dict:
    data = build(root)
    file = out_dir / ZIP_NAME
    checksum = out_dir / (ZIP_NAME + ".sha256")
    expected_sha = f"{_hash(data)}  {ZIP_NAME}\n"
    if check:
        if not file.is_file() or file.read_bytes() != data or not checksum.is_file() or checksum.read_text() != expected_sha:
            raise ReleaseHold("REPRODUCIBLE_RELEASE_RC_DRIFT")
    else:
        out_dir.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
        checksum.write_text(expected_sha, encoding="utf-8")
    result = verify(data, sidecar=expected_sha, filename=ZIP_NAME)
    return result | {"path": str(file), "sha256_sidecar": str(checksum)}


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=["build", "check", "verify"])
    cli.add_argument("--root", type=Path, default=ROOT)
    cli.add_argument("--out", type=Path, default=ROOT / "dist" / "printspace-private-rc")
    cli.add_argument("--zip", type=Path)
    cli.add_argument("--sha256", type=Path)
    args = cli.parse_args()
    try:
        if args.action == "verify":
            path = args.zip or args.out / ZIP_NAME
            sidecar = args.sha256 or path.with_name(path.name + ".sha256")
            result = verify(path.read_bytes(), sidecar=sidecar.read_text(encoding="utf-8"), filename=path.name)
        else:
            result = write_release(args.root, args.out, check=args.action == "check")
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0
    except (ReleaseHold, OSError) as exc:
        print("PRINTSPACE_RC_HOLD:" + str(exc), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
