"""Read-only CGX cross-chat continuity checkpoint from exact committed Git bytes.

This extends the existing bounded review runner. No remote-provider queries,
source export, local registry, issuer, scheduler, admission or mutation.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "CGX-CROSS-CHAT-COMMITTED-CHECKPOINT/0.1"
PATHS = (
    "cgx/bootstrap/README.md",
    "cgx/bootstrap/open_threads_execution_register.json",
    "cgx/bootstrap/cgxPhaseAcceptance_v01.json",
    "cgx/review/manual_intake_prepopulation_v01.review.json",
)
REQUIRED_HOLDS = (
    "G01_source_rights", "G02_native_issuer", "G03_signed_RootAuthority",
    "G04_independent_two_node_DBR", "G05_exact_native_mint",
    "G06_effectful_connector_access", "G07_public_release",
    "source_deletion", "storage_migration",
)


def _require(cond: bool, code: str) -> None:
    if not cond:
        raise ValueError(code)


def from_committed_sources(files: dict[str, bytes], head: str) -> dict:
    _require(len(head) == 40 and all(c in "0123456789abcdef" for c in head),
             "COMMIT_SHA_INVALID")
    _require(all(k in files and isinstance(files[k], bytes) for k in PATHS),
             "MISSING_COMMITTED_CONTRACT")
    try:
        readme = files[PATHS[0]].decode("utf-8")
        register = json.loads(files[PATHS[1]])
        phase = json.loads(files[PATHS[2]])
        intake = json.loads(files[PATHS[3]])
    except (ValueError, UnicodeDecodeError, TypeError) as exc:
        raise ValueError("CONTRACT_PARSE_HOLD") from exc
    _require("Cross-chat / cross-platform continuity and approval boundaries"
             in readme, "CONTINUITY_READ_ORDER_MISSING")
    _require(register.get("source_repo") == "achillesromer-coder/LightSpeed"
             and register.get("state") == "SOURCE_REVIEW_ONLY",
             "OPEN_THREADS_NOT_REVIEW_ONLY")
    _require(phase.get("schema") == "CGX-PHASE-ACCEPTANCE-REVIEW-GRAMMAR/0.1"
             and phase.get("parent") == "cgx:root:cognigrex"
             and phase.get("state") == "SOURCE_ONLY_REVIEW_NOT_CANONICAL",
             "ROOT_OR_PHASE_AUTHORITY_CONFLICT")
    design = phase.get("premint_integration_design_v01", {})
    _require(design.get("canonical_parent") == "cgx:root:cognigrex"
             and design.get("sole_resolver") == "LOAD.cgx"
             and design.get("status") == "APPROVED_DESIGN_ONLY__NO_NATIVE_OR_PUBLIC_AUTHORITY",
             "REVIEW_DESIGN_ESCALATION_HOLD")
    gates = design.get("authority_gate_status", {})
    _require(all(gates.get(k) == "HOLD" for k in REQUIRED_HOLDS),
             "UNQUALIFIED_AUTHORITY_RELEASE_HOLD")
    states = intake.get("states", {})
    _require(intake.get("schema") == "CGX-MANUAL-INTAKE-PREPOPULATION-REVIEW/0.1"
             and intake.get("canonical_parent") == "cgx:root:cognigrex"
             and intake.get("sole_load_resolver") == "LOAD.cgx"
             and states.get("native_mint") == "HOLD"
             and states.get("independent_dbr") == "HOLD"
             and states.get("public_release") == "HOLD"
             and states.get("automatic_deletion") is False
             and intake.get("duplicates", {}).get("deletion_eligible") == 0,
             "SOURCE_INTAKE_ADMISSION_OR_DELETE_HOLD")
    count = intake.get("intake", {}).get("records_reviewed")
    _require(type(count) is int and count >= 0, "INVALID_INTAKE_RECORD_COUNT")
    _require(isinstance(intake.get("source_receipt_sha256"), str)
             and len(intake["source_receipt_sha256"]) == 64
             and all(c in "0123456789abcdef" for c in intake["source_receipt_sha256"]),
             "SOURCE_RECEIPT_POINTER_INVALID")
    return {
        "schema": SCHEMA, "state": "COMMITTED_SOURCE_CHECKPOINT_ONLY",
        "commit_sha": head,
        "canonical_parent": "cgx:root:cognigrex", "sole_resolver": "LOAD.cgx",
        "contract_blob_sha256": {
            k: hashlib.sha256(files[k]).hexdigest() for k in PATHS
        },
        "intake_as_of_source_receipt_sha256": intake["source_receipt_sha256"],
        "intake_review_entries_at_receipt": count,
        "native_mint": False, "source_deletion": False, "deployment": False,
        "signing": False, "independent_dbr_verified": False,
        "all_documentary_authority_holds": True,
        "live_remote_head_verified": False,
        "installed_runtime_verified": False,
        "current_private_acl_verified": False,
        "note": "Historical committed source and gate snapshot only; fetch latest GitHub head, owner receipts, independent private rights/DBR and live runtime before acting",
    }


def _git(repo: Path, *argv: str) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(repo), *argv], timeout=20, stderr=subprocess.DEVNULL
    )


def checkpoint(repo: Path = ROOT) -> dict:
    head = _git(repo, "rev-parse", "HEAD").decode("ascii").strip()
    files = {p: _git(repo, "show", f"HEAD:{p}") for p in PATHS}
    result = from_committed_sources(files, head)
    result["working_tree_clean"] = not bool(_git(repo, "status", "--porcelain"))
    result["readback_source"] = "LOCAL_GIT_HEAD_BLOB_EXACT_NOT_LIVE_PROVIDER"
    return result


def main() -> int:
    try:
        result = checkpoint()
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        result = {"schema": SCHEMA, "state": "HOLD",
                  "error_class": type(exc).__name__,
                  "native_mint": False, "deployment": False,
                  "source_deletion": False}
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["state"] == "COMMITTED_SOURCE_CHECKPOINT_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
