from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import shutil
import sys
from datetime import datetime, timezone


HERE = pathlib.Path(__file__).resolve()
SMITH_ROOT = HERE.parents[1]
RUNNER_PATH = SMITH_ROOT / "tools" / "rfs_emff_runner.py"
REPO_ROOT = HERE.parents[6]
LIGHTSPEED_RUNTIME_ROOT = REPO_ROOT / "desktop" / "LightSpeed_Runtime"
if str(LIGHTSPEED_RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(LIGHTSPEED_RUNTIME_ROOT))
RECEIPT_PATH = REPO_ROOT / "w3-runtime-persistence-receipt.json"
RECEIPT_DIR = REPO_ROOT / "w3-runtime-receipt"

EXPECTED_FILE_ID = "1OfpojKyX7gefk7c0-2NL3xm-ZnohhJI5"
EXPECTED_SHA256 = "05b34a9fb912dd9f349479b5f3480048f96c7871daa67798f29cee021aa559e6"


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_runner():
    spec = importlib.util.spec_from_file_location("w3_runtime_runner", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load runner: {RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    started_at = datetime.now(timezone.utc).isoformat()
    runner = load_runner()
    runner._force_merovingian_core_package()
    from core.services import get_db  # type: ignore

    db = get_db()
    db.ensure_schema()

    payload = {
        "material": "Cu",
        "frequencies_mhz": [1, 2],
        "field_strength_tesla": [0.1],
        "thickness_m": 0.01,
        "tags": ["w3", "runtime-persistence", "ci-receipt"],
    }
    artifacts, manifest_fields = runner.run(payload)

    job_id = int(manifest_fields["job_id"])
    run_dir = pathlib.Path(manifest_fields["run_dir"]).resolve()
    manifest_path = pathlib.Path(manifest_fields["manifest_path"]).resolve()
    result_path = run_dir / "result.json"

    assert result_path.is_file(), result_path
    assert manifest_path.is_file(), manifest_path

    result_json = json.loads(result_path.read_text(encoding="utf-8"))
    manifest_json = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_job = manifest_json.get("job") or {}

    manifest_inputs = manifest_json.get("inputs") or []
    matching_inputs = [
        item for item in manifest_inputs
        if isinstance(item, dict)
        and item.get("file_id") == EXPECTED_FILE_ID
        and item.get("sha256") == EXPECTED_SHA256
    ]
    assert len(matching_inputs) == 1, manifest_inputs
    assert manifest_job.get("id") == job_id, manifest_job
    assert manifest_job.get("status") == "completed", manifest_job

    job_rows = db.execute_query("SELECT * FROM jobs WHERE id = ?", (job_id,))
    assert len(job_rows) == 1, job_rows
    job_row = job_rows[0]
    metadata = json.loads(job_row.get("metadata_json") or "{}")
    ledger_inputs = metadata.get("inputs") or []
    ledger_matches = [
        item for item in ledger_inputs
        if isinstance(item, dict)
        and item.get("file_id") == EXPECTED_FILE_ID
        and item.get("sha256") == EXPECTED_SHA256
    ]
    assert len(ledger_matches) == 1, ledger_inputs

    artifact_rows = db.execute_query(
        "SELECT kind, name, path, sha256, size_bytes, media_type FROM artifacts WHERE job_id = ? ORDER BY id",
        (job_id,),
    )
    kinds = [row.get("kind") for row in artifact_rows]
    assert "result" in kinds, artifact_rows
    assert "manifest" in kinds, artifact_rows

    result_sha = sha256_file(result_path)
    manifest_sha = sha256_file(manifest_path)
    result_ledger = next(row for row in artifact_rows if row.get("kind") == "result")
    manifest_ledger = next(row for row in artifact_rows if row.get("kind") == "manifest")
    assert result_ledger.get("sha256") == result_sha, result_ledger
    assert manifest_ledger.get("sha256") == manifest_sha, manifest_ledger

    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(result_path, RECEIPT_DIR / "result.json")
    shutil.copy2(manifest_path, RECEIPT_DIR / "manifest.json")

    finished_at = datetime.now(timezone.utc).isoformat()
    receipt = {
        "classification": "CI_RUNTIME_PERSISTENCE_RECEIPT_NOT_DEPLOYED_LIVE_RUNTIME",
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "job_id": job_id,
        "tool_key": manifest_fields.get("tool_key"),
        "status": manifest_fields.get("status"),
        "rows": manifest_fields.get("rows"),
        "run_dir": str(run_dir),
        "manifest_path": str(manifest_path),
        "database_path": str(getattr(db, "db_path", "")),
        "schema_bootstrap": "DatabaseService.ensure_schema",
        "canonical_source": matching_inputs[0],
        "ledger_metadata_inputs": ledger_inputs,
        "result": {
            "path": str(result_path),
            "sha256": result_sha,
            "size_bytes": result_path.stat().st_size,
            "job_id_readback": result_json.get("job_id"),
            "status_readback": result_json.get("status"),
        },
        "manifest": {
            "path": str(manifest_path),
            "sha256": manifest_sha,
            "size_bytes": manifest_path.stat().st_size,
            "job_id_readback": manifest_job.get("id"),
            "status_readback": manifest_job.get("status"),
            "inputs": manifest_inputs,
        },
        "artifact_ledger": artifact_rows,
        "assertions": {
            "canonical_drive_id_persisted_in_job_metadata": True,
            "canonical_drive_sha256_persisted_in_job_metadata": True,
            "canonical_drive_id_persisted_in_manifest": True,
            "canonical_drive_sha256_persisted_in_manifest": True,
            "manifest_job_identity_matches_ledger_job": True,
            "manifest_status_completed": True,
            "result_artifact_hash_matches_ledger": True,
            "manifest_artifact_hash_matches_ledger": True,
        },
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
