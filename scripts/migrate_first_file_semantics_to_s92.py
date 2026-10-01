#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any

ALLOWED_DELTA_PREFIXES = (
    "graph/cells/",
    "graph/objects/",
    "graph/relations/",
    "proof/intake/",
    "sources/intake/",
    "queue/bridge_proposals/",
)
ALLOWED_DELTA_EXACT = {"semantic/intake_index.json"}
IGNORED_GENERATED_PREFIXES = ("events/", "store/blobs/")
CARRIERS = {
    "romer": "Romer.cgx",
    "eco": "Eco.cgx",
    "emassc": "EMASSC.cgx",
    "lightspeed": "LS.cgx",
}


class FirstFileMigrationError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def zip_names(path: Path) -> set[str]:
    with zipfile.ZipFile(path, "r") as z:
        return set(z.namelist())


def semantic_delta_paths(s91_base: Path, s91_intake: Path) -> tuple[list[str], list[str]]:
    added = sorted(zip_names(s91_intake) - zip_names(s91_base))
    allowed: list[str] = []
    ignored: list[str] = []
    unexpected: list[str] = []
    for rel in added:
        if rel in ALLOWED_DELTA_EXACT or rel.startswith(ALLOWED_DELTA_PREFIXES):
            allowed.append(rel)
        elif rel.startswith(IGNORED_GENERATED_PREFIXES):
            ignored.append(rel)
        else:
            unexpected.append(rel)
    if unexpected:
        raise FirstFileMigrationError(
            "unexpected S91 intake delta paths: " + ", ".join(unexpected)
        )
    return allowed, ignored


def relation_ids(obj: Any) -> set[str]:
    out: set[str] = set()
    if isinstance(obj, dict):
        if isinstance(obj.get("id"), str):
            out.add(obj["id"])
        for value in obj.values():
            out |= relation_ids(value)
    elif isinstance(obj, list):
        for value in obj:
            out |= relation_ids(value)
    return out


def _read_zip_json(z: zipfile.ZipFile, rel: str) -> dict[str, Any]:
    return json.loads(z.read(rel).decode("utf-8"))


def _validate_relations(
    *,
    intake_path: Path,
    delta_paths: list[str],
    current_registry: dict[str, Any],
) -> list[str]:
    admitted = relation_ids(current_registry)
    seen: list[str] = []
    with zipfile.ZipFile(intake_path, "r") as z:
        for rel in delta_paths:
            if not rel.startswith("graph/relations/"):
                continue
            record = _read_zip_json(z, rel)
            relation_type = str((record.get("record") or {}).get("relation_type") or "").strip()
            if not relation_type:
                raise FirstFileMigrationError(f"relation type missing: {rel}")
            if relation_type not in admitted:
                raise FirstFileMigrationError(
                    f"relation type not admitted by current S92 registry: {relation_type} ({rel})"
                )
            seen.append(relation_type)
    return sorted(set(seen))


def _update_intake_queue(root: Path, migrated_source_refs: list[str]) -> None:
    queue_path = root / "queue" / "first_file_intake.json"
    if not queue_path.exists():
        return
    payload = json.loads(queue_path.read_text(encoding="utf-8"))
    for item in payload.get("items", []):
        if not isinstance(item, dict):
            continue
        ref = item.get("source_drive_id")
        if ref and str(ref) in migrated_source_refs:
            item["status"] = "assimilated-s91-proven-delta"
            item["migration"] = "S91 proven semantic delta -> S92 successor"
            item["auto_commit"] = False
    payload["last_migration"] = "S91_PROVEN_FIRST_FILE_DELTA_TO_S92"
    queue_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def migrate_one(
    *,
    domain: str,
    s91_base: Path,
    s91_intake: Path,
    s92_source: Path,
    output: Path,
    runtime_python: Path,
) -> dict[str, Any]:
    if str(runtime_python) not in sys.path:
        sys.path.insert(0, str(runtime_python))
    import cgx_kernel as kernel  # type: ignore

    delta_paths, ignored = semantic_delta_paths(s91_base, s91_intake)
    workspace = kernel.open_workspace(s92_source)
    try:
        registry = kernel.load_json(workspace.root, "semantic/relation_registry.json", {}) or {}
        relation_types = _validate_relations(
            intake_path=s91_intake,
            delta_paths=delta_paths,
            current_registry=registry,
        )
        source_refs: list[str] = []
        with zipfile.ZipFile(s91_intake, "r") as intake_zip:
            for rel in delta_paths:
                if rel.startswith("sources/intake/"):
                    source = _read_zip_json(intake_zip, rel)
                    drive_id = source.get("source_drive_id") or source.get("drive_file_id")
                    if drive_id:
                        source_refs.append(str(drive_id))

            migration_receipt = {
                "schema": "CGX-FIRST-FILE-S91-TO-S92-MIGRATION/0.1",
                "domain": domain,
                "source_semantic_proof": {
                    "s91_base_carrier_sha256": sha256_file(s91_base),
                    "s91_intake_carrier_sha256": sha256_file(s91_intake),
                    "semantic_delta_paths": delta_paths,
                    "ignored_generated_paths": ignored,
                    "relation_types": relation_types,
                },
                "s92_input": {
                    "carrier_sha256": sha256_file(s92_source),
                    "semantic_object_id": (
                        kernel.load_json(workspace.root, "identity/domain.json", {}) or {}
                    ).get("semantic_object_id"),
                    "carrier_instance_object_id": (
                        kernel.load_json(workspace.root, "cgx/bootstrap.json", {}) or {}
                    ).get("object_id"),
                },
                "authority": {
                    "native_source_authority_preserved": True,
                    "conversion_class": "R2_RECONSTRUCTED",
                    "physical_or_empirical_promotion": False,
                    "canonical_mutation_scope": "bounded semantic/proof/source delta only",
                },
            }

            def operation() -> None:
                for rel in delta_paths:
                    target = workspace.root / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(intake_zip.read(rel))
                proof_path = workspace.root / "proof" / "intake" / "s91_to_s92_migration_receipt.json"
                proof_path.parent.mkdir(parents=True, exist_ok=True)
                proof_path.write_text(
                    json.dumps(migration_receipt, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                _update_intake_queue(workspace.root, source_refs)

            result = kernel.mutate(
                workspace.root,
                "first-file-semantic-migration",
                f"Migrated proven S91 first-file semantic delta into S92 {domain} child",
                operation,
                {
                    "domain": domain,
                    "conversion_class": "R2_RECONSTRUCTED",
                    "source_refs": sorted(set(source_refs)),
                    "semantic_delta_path_count": len(delta_paths),
                },
            )
        verify = kernel.verify(workspace.root)
        if not verify.get("ok"):
            raise FirstFileMigrationError(
                "S92 post-migration verifier failed: " + ";".join(verify.get("errors", []))
            )
        kernel.write_carrier(workspace.root, output)
    finally:
        workspace.close()

    reopened = kernel.open_workspace(output)
    try:
        packed_verify = kernel.verify(reopened.root)
        bootstrap = kernel.load_json(reopened.root, "cgx/bootstrap.json", {}) or {}
        domain_identity = kernel.load_json(reopened.root, "identity/domain.json", {}) or {}
    finally:
        reopened.close()
    if not packed_verify.get("ok"):
        raise FirstFileMigrationError(
            "packed-reopen verifier failed: " + ";".join(packed_verify.get("errors", []))
        )
    return {
        "domain": domain,
        "file": output.name,
        "semantic_object_id": domain_identity.get("semantic_object_id"),
        "carrier_instance_object_id": bootstrap.get("object_id"),
        "sha256": sha256_file(output),
        "verify": "PASS",
        "packed_reopen_verify": "PASS",
        "tracked_objects": packed_verify.get("tracked"),
        "content_root": packed_verify.get("computed_content_root"),
        "topology_snapshot_hash": packed_verify.get("topology_snapshot_hash"),
        "relation_types": relation_types,
        "semantic_delta_path_count": len(delta_paths),
        "ignored_generated_path_count": len(ignored),
        "result": result,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--s91-base-dir", required=True, type=Path)
    parser.add_argument("--s91-intake-dir", required=True, type=Path)
    parser.add_argument("--s92-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--runtime-python", required=True, type=Path)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Any] = {}
    for domain, filename in CARRIERS.items():
        outputs[domain] = migrate_one(
            domain=domain,
            s91_base=args.s91_base_dir / filename,
            s91_intake=args.s91_intake_dir / filename,
            s92_source=args.s92_dir / filename,
            output=args.out_dir / filename,
            runtime_python=args.runtime_python,
        )

    receipt = {
        "schema": "CGX-S92-FIRST-FILE-MIGRATION-RECEIPT/0.1",
        "status": "LOCAL_MIGRATION_VERIFIED / DURABLE_PERSISTENCE_OPEN",
        "source_boundary": "S91 proven semantic delta only; native source authority retained",
        "outputs": outputs,
    }
    receipt["receipt_sha256"] = hashlib.sha256(stable_json(receipt)).hexdigest()
    receipt_path = args.out_dir / "S92_FIRST_FILE_MIGRATION_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
