"""Read-only reconciliation of draft CGX persistence with the existing native runtime.

Reads exact git objects and current public-safe source files; NEVER imports or runs
the draft family store/supervisor, creates a database, signs a lease, or dispatches.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
REVIEW_HEAD = "028f34e856cc011346beb2a0ff9d5d7f0ef45257"
PREFLIGHT_SOURCE = "cgx/review/persistence_family/CGX_Native_ABI_Preflight.py"
CORE_SOURCE = "cgx/review/persistence_family/CGX_Persistence_Core.py"
SUPERVISOR_SOURCE = "cgx/review/persistence_family/CGX_Family_Supervisor.py"
MAX_SOURCE_BYTES = 1_048_576
HEX40 = re.compile(r"^[a-f0-9]{40}$")
SAFE_PATH = re.compile(r"^[A-Za-z0-9_./-]+$")
SCHEMA = "CGX-PERSISTENCE-ABI-RECONCILIATION/0.1"


class PersistenceReviewError(ValueError):
    pass


def git_blob_id(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def _git(repo: Path, *parts: str, binary: bool = False) -> bytes | str:
    command = ["git", "-C", str(repo), *parts]
    try:
        result = subprocess.run(command, capture_output=True, timeout=12, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PersistenceReviewError("local git source unavailable") from exc
    if result.returncode != 0:
        raise PersistenceReviewError("requested local git object is unavailable")
    if binary:
        if len(result.stdout) > MAX_SOURCE_BYTES:
            raise PersistenceReviewError("source exceeds review byte ceiling")
        return result.stdout
    return result.stdout.decode("utf-8", errors="strict").strip()


def canonical_worktree_blob(repo: Path, relative: str, raw: bytes) -> str:
    """Apply the repository's Git clean filter without writing a Git object.

    On Windows the working tree can contain CRLF even when the committed blob
    (and pinned source contract) is LF. Unknown/unavailable filters fail closed.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "hash-object", "--path", relative, "--stdin"],
            input=raw, capture_output=True, timeout=12, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PersistenceReviewError("canonical Git blob check unavailable") from exc
    digest = result.stdout.decode("ascii", errors="replace").strip()
    if result.returncode or not HEX40.fullmatch(digest):
        raise PersistenceReviewError("Git clean-filter verification failed")
    return digest


def _pin_source(raw: bytes) -> dict[str, Any]:
    try:
        tree = ast.parse(raw.decode("utf-8"))
        literals = {}
        for item in tree.body:
            if not isinstance(item, ast.Assign) or len(item.targets) != 1:
                continue
            target = item.targets[0]
            if isinstance(target, ast.Name) and target.id in {
                "REPO_HEAD", "BLOB_PINS", "OPERATOR_METHODS", "NODE_FUNCS", "LEASE_FIELDS"
            }:
                literals[target.id] = ast.literal_eval(item.value)
    except (SyntaxError, UnicodeError, ValueError, TypeError) as exc:
        raise PersistenceReviewError("invalid pinned review source") from exc
    if not set(literals) == {"REPO_HEAD", "BLOB_PINS", "OPERATOR_METHODS", "NODE_FUNCS", "LEASE_FIELDS"}:
        raise PersistenceReviewError("native preflight is missing required declarations")
    if (not isinstance(literals["REPO_HEAD"], str) or
            not HEX40.fullmatch(literals["REPO_HEAD"])):
        raise PersistenceReviewError("invalid pinned base revision")
    pins = literals["BLOB_PINS"]
    if not isinstance(pins, dict) or len(pins) != 3:
        raise PersistenceReviewError("unexpected native source pin set")
    required = {
        "desktop/LightSpeed_Runtime/lightspeed_runtime/achilles/operator.py",
        "desktop/LightSpeed_Runtime/lightspeed_runtime/node_exchange.py",
        "cgx/domain_templates/execution_lease_contract.json",
    }
    if set(pins) != required or any(type(v) is not str or not HEX40.fullmatch(v) for v in pins.values()):
        raise PersistenceReviewError("unexpected or malformed source paths/hashes")
    for key in ("OPERATOR_METHODS", "NODE_FUNCS", "LEASE_FIELDS"):
        if not isinstance(literals[key], set) or not all(isinstance(x, str) for x in literals[key]):
            raise PersistenceReviewError("invalid review method requirements")
    return literals


def _shape_ok(relative: str, raw: bytes, pins: dict[str, Any]) -> bool:
    try:
        if relative.endswith("/achilles/operator.py"):
            tree = ast.parse(raw.decode("utf-8"))
            cls = next((x for x in tree.body if isinstance(x, ast.ClassDef)
                        and x.name == "AchillesOperator"), None)
            names = {x.name for x in cls.body if isinstance(x, ast.FunctionDef)} if cls else set()
            return pins["OPERATOR_METHODS"] <= names
        if relative.endswith("/node_exchange.py"):
            tree = ast.parse(raw.decode("utf-8"))
            names = {x.name for x in tree.body if isinstance(x, ast.FunctionDef)}
            return pins["NODE_FUNCS"] <= names
        contract = json.loads(raw)
        return (isinstance(contract, dict)
                and pins["LEASE_FIELDS"] <= set(contract.get("required_fields", []))
                and "missing-or-stale-lease-means-no-consequential-execution" in
                    contract.get("invariants", []))
    except (SyntaxError, UnicodeError, ValueError, TypeError, KeyError):
        return False


def review_core_markers(core: bytes, supervisor: bytes) -> dict[str, bool]:
    """Source markers only: no guarantee of caller authentication or safe execution."""
    try:
        c = ast.parse(core.decode("utf-8"))
        s = ast.parse(supervisor.decode("utf-8"))
    except (SyntaxError, UnicodeError) as exc:
        raise PersistenceReviewError("draft persistence source cannot be parsed") from exc
    family = next((x for x in c.body if isinstance(x, ast.ClassDef)
                   and x.name == "FamilyStore"), None)
    supervisor_lock = any(isinstance(x, ast.ClassDef) and
                          x.name == "CoordinatorLock" for x in s.body)
    methods = {x.name for x in family.body if isinstance(x, ast.FunctionDef)} if family else set()
    content_grant_names = {
        "ingest", "occurrences_for_agent", "restore_for_agent", "source_search", "propose"
    }
    string_values = {
        x.value for x in ast.walk(c) if isinstance(x, ast.Constant) and
        isinstance(x.value, str)
    }
    return {
        "separate_review_database_declared": "family.sqlite3" in string_values,
        "source_occurrence_grant_methods_declared": content_grant_names <= methods and
            "content_granted" in core.decode("utf-8"),
        "foreground_coordinator_declared": supervisor_lock,
    }


def reconcile(repo: Path = REPO_ROOT, review_head: str = REVIEW_HEAD) -> dict[str, Any]:
    """Do not infer an execution lease, admission or promotion from source parity."""
    repo = Path(repo).resolve(strict=True)
    if review_head != REVIEW_HEAD or not HEX40.fullmatch(review_head):
        raise PersistenceReviewError("unreviewed or non-pinned persistence revision held")
    preflight = _git(repo, "show", f"{review_head}:{PREFLIGHT_SOURCE}", binary=True)
    core = _git(repo, "show", f"{review_head}:{CORE_SOURCE}", binary=True)
    supervisor = _git(repo, "show", f"{review_head}:{SUPERVISOR_SOURCE}", binary=True)
    pins = _pin_source(preflight)
    head = _git(repo, "rev-parse", "HEAD")
    source = {}
    for relative, expected_blob in sorted(pins["BLOB_PINS"].items()):
        current_path = repo / relative
        if current_path.is_symlink() or not current_path.is_file() or not current_path.resolve().is_relative_to(repo):
            source[relative] = {"parity": False, "contract_shape": False, "reason": "missing_or_linked"}
            continue
        raw = current_path.read_bytes()
        if len(raw) > MAX_SOURCE_BYTES:
            source[relative] = {"parity": False, "contract_shape": False, "reason": "source_budget"}
            continue
        raw_blob = git_blob_id(raw)
        canonical_blob = canonical_worktree_blob(repo, relative, raw)
        head_blob = _git(repo, "rev-parse", f"HEAD:{relative}")
        source[relative] = {
            "expected_blob": expected_blob,
            "canonical_blob": canonical_blob,
            "raw_blob": raw_blob,
            "line_ending_or_filter_normalized": raw_blob != canonical_blob,
            "matches_head_blob": canonical_blob == head_blob,
            "parity": canonical_blob == expected_blob,
            "contract_shape": _shape_ok(relative, raw, pins),
        }
    base_ancestor = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", pins["REPO_HEAD"], "HEAD"],
        capture_output=True, timeout=12, check=False,
    ).returncode == 0
    markers = review_core_markers(core, supervisor)
    parity = bool(source) and all(
        item.get("parity") and item.get("contract_shape") and item.get("matches_head_blob")
        for item in source.values()
    )
    return {
        "schema": SCHEMA,
        "review_commit": review_head,
        "review_preflight_blob": git_blob_id(preflight),
        "observed_head": head,
        "pinned_base": pins["REPO_HEAD"],
        "base_is_ancestor": base_ancestor,
        "native_source_parity": parity,
        "source": source,
        "draft_source_markers": markers,
        "source_contract_readiness": (
            "SOURCE_COMPATIBLE_NATIVE_ADAPTER_REQUIRED" if parity and base_ancestor
            else "HOLD_SOURCE_DRIFT_OR_UNRECONCILED_HISTORY"
        ),
        "native_blockers": [
            "Draft family.sqlite3 must not be installed as a second canonical database",
            "Source role strings are not authenticated; native ACL and per-occurrence grants required",
            "Current authenticated LOAD/FileSpace occurrence ABI and owner lease binding unverified",
            "Signed issuer, revocation and DBR replay must be independently verified",
            "Host singleton CPU/RAM scheduler and rollback must be accepted",
            "Second DataSpace node and network mint remain separate",
        ],
        "draft_store_installed_by_preflight": False,
        "host_runtime_mutated_by_preflight": False,
        "source_bytes_ingested_by_preflight": False,
        "training_performed_by_preflight": False,
        "dispatch_authorized": False,
        "native_mint_authorized": False,
        "public_release_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO_ROOT)
    parser.add_argument("--review-head", default=REVIEW_HEAD)
    parser.add_argument("--strict-parity", action="store_true")
    args = parser.parse_args()
    try:
        receipt = reconcile(args.repo, args.review_head)
    except (PersistenceReviewError, OSError, ValueError) as exc:
        print(json.dumps({"schema": SCHEMA, "source_contract_readiness": "HOLD",
                          "reason": str(exc), "dispatch_authorized": False,
                          "native_mint_authorized": False}))
        return 2
    print(json.dumps(receipt, sort_keys=True, indent=2))
    return 0 if receipt["native_source_parity"] or not args.strict_parity else 1


if __name__ == "__main__":
    raise SystemExit(main())
