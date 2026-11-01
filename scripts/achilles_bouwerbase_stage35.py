#!/usr/bin/env python3
"""Achilles bounded BouwerBase Stage35 executor.

Runs only pinned, already-reviewed CGX fixture suites on the existing Windows
managed Python. Never installs, starts a bridge, changes execution policy,
writes the native database, mints an Object_ID, or imports sources. Any host
readback change is a HOLD, not a deployment permission.

GitHub review source != local execution. A receipt exists only after this script
actually runs on the authorised Windows host and writes its exclusive result.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
import zipfile

SCHEMA = "CGX-ACHILLES-ISOLATED-ACCEPTANCE/35.1"
STAGE34_SCHEMA = "CGX-ACHILLES-DEPLOYMENT-CANDIDATE/34.0"
BUNDLE_SCHEMA = "CGX-LS-GO-STAGED-SOURCE-PACKAGE/0.1"
FAMILY_COMMIT = "124262b61fdbb5e181f1c21d064182cd21f74adb"
ROOT_OBJECT = "cgx:phase-a:42d99b46c0d322f08b59b7b7"
R0_SHA = "722558c274416c8e3d7e555575fb7fa43e0538aca72d6875ee06bb1486175db5"
MAX_INPUT_BYTES = 5 * 1024 * 1024
MAX_ARCHIVE_BYTES = 15 * 1024 * 1024
MAX_MEMBER_BYTES = 2 * 1024 * 1024
TEST_SELECTIONS = (
    ("family_ingestion", ("tests/test_cgx_family_ingestion.py",)),
    ("owner_bridge", ("tests/test_ls_go_bridge.py", "-k", "cgx_family_oversight or cgx_root_review_preflight")),
)


class Stage35Hold(RuntimeError):
    """Preflight or acceptance failed closed."""


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalized(raw: bytes) -> str:
    return raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise Stage35Hold("REVIEW_RECEIPT_MISSING_OR_SIZE_HOLD")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise Stage35Hold("REVIEW_RECEIPT_INVALID")
    return value


def git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ("git", "-C", str(repo), *args),
        capture_output=True, timeout=30, check=False,
    )
    if result.returncode != 0:
        raise Stage35Hold("REVIEW_GIT_SOURCE_UNAVAILABLE")
    return result.stdout


def check_git(repo: Path) -> None:
    head = git(repo, "rev-parse", "HEAD").decode().strip()
    # The review job itself may be a descendant of the exact family source.
    ancestor = subprocess.run(
        ("git", "-C", str(repo), "merge-base", "--is-ancestor", FAMILY_COMMIT, head),
        capture_output=True, timeout=30, check=False,
    )
    if ancestor.returncode != 0 or git(repo, "status", "--porcelain", "--untracked-files=no").strip():
        raise Stage35Hold("REVIEW_WORKTREE_NOT_EXACT_DESCENDANT_OR_DIRTY")


def check_bundle(repo: Path, receipt: dict[str, Any], bundle: Path) -> None:
    source = receipt.get("source_bundle") or {}
    if (not bundle.is_file() or bundle.stat().st_size > MAX_ARCHIVE_BYTES
            or source.get("sha256") != digest(bundle.read_bytes())
            or source.get("readback_pass") is not True):
        raise Stage35Hold("STAGE34_BUNDLE_HASH_HOLD")
    proofs = receipt.get("source_proofs")
    if not isinstance(proofs, list) or len(proofs) != 5:
        raise Stage35Hold("STAGE34_SOURCE_COUNT_HOLD")
    expected_paths = {
        "desktop/LightSpeed_Runtime/lightspeed_runtime/cgx_family_ingestion.py",
        "desktop/LightSpeed_Runtime/lightspeed_runtime/ls_go_bridge.py",
        "apps/lightspeed-go/src/main.ts",
        "apps/lightspeed-go/src/desktopBridge.ts",
        "apps/lightspeed-go/src/cgxFamilyOversight.ts",
    }
    if {entry.get("path") for entry in proofs} != expected_paths:
        raise Stage35Hold("STAGE34_UNEXPECTED_SOURCE_SET")
    declared = {"manifest.json"}
    with zipfile.ZipFile(bundle, "r") as archive:
        if any(x.file_size > MAX_MEMBER_BYTES or x.is_dir() for x in archive.infolist()):
            raise Stage35Hold("STAGE34_ARCHIVE_MEMBER_SIZE_HOLD")
        for proof in proofs:
            path = proof.get("path")
            sha = proof.get("git_blob_content_sha256")
            if not isinstance(path, str) or ".." in Path(path).parts:
                raise Stage35Hold("STAGE34_ARCHIVE_PATH_HOLD")
            member = "source/" + path
            declared.add(member)
            packed = archive.read(member)
            if digest(packed) != sha:
                raise Stage35Hold("STAGE34_PACKED_SOURCE_HASH_HOLD")
            # Git bytes, not a mutable local editor copy, establish source identity.
            git_raw = git(repo, "show", FAMILY_COMMIT + ":" + path)
            if packed != git_raw:
                raise Stage35Hold("STAGE34_PACKED_SOURCE_GIT_DRIFT")
        if set(archive.namelist()) != declared:
            raise Stage35Hold("STAGE34_ARCHIVE_UNEXPECTED_MEMBER")
        manifest = json.loads(archive.read("manifest.json"))
        if (manifest.get("schema") != BUNDLE_SCHEMA
                or manifest.get("state") != "REVIEW_ONLY_NOT_INSTALLED"
                or manifest.get("source_commit") != FAMILY_COMMIT):
            raise Stage35Hold("STAGE34_ARCHIVE_MANIFEST_HOLD")


def native_snapshot(db: Path) -> dict[str, Any]:
    if not db.is_file():
        raise Stage35Hold("CANONICAL_DB_MISSING")
    try:
        con = sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True, timeout=4)
        con.execute("PRAGMA query_only=ON")
        try:
            return {
                "parent": con.execute(
                    "SELECT state FROM canonical_objects WHERE object_id=?",
                    (ROOT_OBJECT,),
                ).fetchall(),
                "r0": con.execute(
                    "SELECT state,content_sha256 FROM object_representations "
                    "WHERE object_id=? AND representation_type='R0_source'",
                    (ROOT_OBJECT,),
                ).fetchall(),
                "review_count": con.execute(
                    "SELECT COUNT(*) FROM representation_review_packets "
                    "WHERE object_id=?", (ROOT_OBJECT,),
                ).fetchone()[0],
            }
        finally:
            con.close()
    except sqlite3.Error as exc:
        raise Stage35Hold("CANONICAL_DB_READ_ONLY_FAILURE") from exc


def file_snapshot(core: Path, frontend: Path) -> dict[str, str | None]:
    paths = (
        core / "lightspeed_runtime/ls_go_bridge.py",
        core / "lightspeed_runtime/cgx_family_ingestion.py",
        frontend / "index.html",
    )
    return {str(p): digest(p.read_bytes()) if p.is_file() else None for p in paths}


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


def bridge_status() -> dict[str, Any]:
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    result: dict[str, Any] = {}
    for key, path in (("status", "/api/v1/status"), ("family", "/api/v1/cgx/family-oversight")):
        request = Request(
            "http://127.0.0.1:8765" + path,
            headers={"Accept": "application/json"}, method="GET",
        )
        try:
            with opener.open(request, timeout=3) as response:
                if key == "status":
                    body = response.read(65537)
                    if len(body) > 65536:
                        raise Stage35Hold("BRIDGE_STATUS_OVERSIZE")
                    data = json.loads(body)
                    result[key] = "LS_GO_VERIFIED" if data.get("bridge") == "ls-go" else "UNRECOGNISED_SERVICE"
                else:
                    # Never consume a private endpoint's response without authentication.
                    result[key] = response.status
        except HTTPError as exc:
            result[key] = exc.code
        except (OSError, URLError, ValueError) as exc:
            raise Stage35Hold("BRIDGE_LOOPBACK_UNREACHABLE") from exc
    return result


def run(
    *,
    repo: Path,
    stage34_file: Path,
    bundle: Path,
    downloads: Path,
    core: Path,
    frontend: Path,
    db: Path,
    python: Path,
) -> dict[str, Any]:
    if os.name != "nt":
        raise Stage35Hold("WINDOWS_ONLY_HOST_EXECUTION")
    if not python.is_file() or not downloads.is_dir():
        raise Stage35Hold("MANAGED_PYTHON_OR_OWNER_RECEIPT_DIRECTORY_MISSING")
    check_git(repo)
    stage34 = read_json(stage34_file)
    if (stage34.get("schema") != STAGE34_SCHEMA
            or stage34.get("state") != "STAGED_REVIEW_ONLY_NOT_DEPLOYED"
            or stage34.get("source_commit") != FAMILY_COMMIT
            or stage34.get("database_snapshot_unchanged") is not True
            or (stage34.get("effects") or {}).get("canonical_db_writes") != 0
            or (stage34.get("effects") or {}).get("service_restarts") != 0):
        raise Stage35Hold("STAGE34_NOT_ACCEPTED")
    check_bundle(repo, stage34, bundle)

    runtime = repo / "desktop/LightSpeed_Runtime"
    if not runtime.is_dir():
        raise Stage35Hold("REVIEW_RUNTIME_SOURCE_MISSING")
    test_relpaths = (
        "desktop/LightSpeed_Runtime/tests/test_cgx_family_ingestion.py",
        "desktop/LightSpeed_Runtime/tests/test_ls_go_bridge.py",
    )
    for relative in test_relpaths:
        p = repo / relative
        if not p.is_file() or normalized(git(repo, "show", FAMILY_COMMIT + ":" + relative)) != normalized(p.read_bytes()):
            raise Stage35Hold("REVIEW_TEST_SOURCE_DRIFT")

    before_db = native_snapshot(db)
    before_files = file_snapshot(core, frontend)
    before_bridge = bridge_status()
    if (before_db["parent"] != [("candidate",)]
            or before_db["r0"] != [("candidate", R0_SHA)]
            or before_db["review_count"] != 0
            or before_bridge != {"status": "LS_GO_VERIFIED", "family": 404}):
        raise Stage35Hold("LIVE_HOST_STATE_DRIFT_BEFORE_TEST")

    results: list[dict[str, Any]] = []
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    with tempfile.TemporaryDirectory(prefix="CGX_STAGE35_FIXTURE_", dir=str(downloads)) as scratch:
        env = os.environ.copy()
        for key in ("LIGHTSPEED_CANONICAL_ROOT", "LIGHTSPEED_RUNTIME_ROOT", "LIGHTSPEED_SHELL_ROOT",
                    "LIGHTSPEED_ROOT", "CGX_FAMILY_IDENTITY_REGISTRY", "CGX_LOAD_SOURCE_REGISTRY"):
            env.pop(key, None)
        env.update({
            "PYTHONPATH": str(runtime),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "LIGHTSPEED_REPRESENTATION_EDGE_ENABLED": "0",
            "TMP": scratch,
            "TEMP": scratch,
            "TMPDIR": scratch,
        })
        for suite, selection in TEST_SELECTIONS:
            command = [str(python), "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *selection]
            try:
                p = subprocess.run(command, cwd=runtime, env=env, capture_output=True,
                                   text=True, errors="replace", timeout=180)
                log = (p.stdout + "\n" + p.stderr)[-100000:]
                rc = p.returncode
            except (OSError, subprocess.TimeoutExpired) as exc:
                log, rc = type(exc).__name__, 99
            match = re.search(r"(\d+) passed", log)
            tests_passed = int(match.group(1)) if match else 0
            log_path = downloads / f"CGX_STAGE35_{suite}_{stamp}.txt"
            with log_path.open("x", encoding="utf-8") as file:
                file.write(log)
            results.append({
                "suite": suite, "exit_code": rc, "passed": tests_passed,
                "accepted": rc == 0 and tests_passed > 0,
                "log_filename": log_path.name,
                "log_sha256": digest(log_path.read_bytes()),
            })

    after_db, after_files, after_bridge = native_snapshot(db), file_snapshot(core, frontend), bridge_status()
    unchanged = before_db == after_db and before_files == after_files and before_bridge == after_bridge
    passed = all(suite["accepted"] for suite in results) and unchanged
    receipt = {
        "schema": SCHEMA,
        "state": "ISOLATED_TESTS_PASS_NOT_DEPLOYED" if passed else "HOLD_TEST_OR_HOST_DRIFT",
        "family_git_commit": FAMILY_COMMIT,
        "stage34_receipt_sha256": digest(stage34_file.read_bytes()),
        "source_bundle_sha256": digest(bundle.read_bytes()),
        "tests": results,
        "parent_state": before_db["parent"][0][0],
        "review_rows_before": before_db["review_count"],
        "target_native_rows_unchanged": before_db == after_db,
        "installed_files_unchanged": before_files == after_files,
        "running_bridge_unchanged": before_bridge == after_bridge,
        "family_endpoint_current_status": after_bridge.get("family"),
        "effects": {
            "production_db_writes_requested_by_this_step": 0, "production_file_copies": 0,
            "service_restarts": 0, "object_ids_minted": 0, "git_merges": 0,
            "native_parent_promoted": False, "public_release": False,
        },
        "next_gate": "SIGNED_MANAGED_DEPLOYMENT_AND_OWNER_SESSION_READBACK" if passed else "HOLD_REVIEW_TEST_LOGS",
    }
    receipt_path = downloads / f"CGX_ACHILLES_STAGE35_{stamp}.json"
    with receipt_path.open("x", encoding="utf-8") as file:
        json.dump(receipt, file, indent=2)
        file.write("\n")
    if read_json(receipt_path)["schema"] != SCHEMA:
        raise Stage35Hold("LOCAL_RECEIPT_READBACK_FAILURE")
    receipt["receipt_filename"] = receipt_path.name
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Achilles Stage35 local isolated test; not a deployment tool")
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--stage34", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--downloads", type=Path, required=True)
    parser.add_argument("--core", type=Path, default=Path("D:/LightSpeed/Core"))
    parser.add_argument("--frontend", type=Path, default=Path("D:/LightSpeed/Apps/lightspeed-go/dist"))
    parser.add_argument("--database", type=Path, default=Path("D:/LightSpeed/Data/db/lightspeed_unified.db"))
    parser.add_argument("--managed-python", type=Path, default=Path("D:/LightSpeed/Environment/Scripts/python.exe"))
    args = parser.parse_args()
    try:
        result = run(
            repo=args.repo, stage34_file=args.stage34, bundle=args.bundle,
            downloads=args.downloads, core=args.core, frontend=args.frontend,
            db=args.database, python=args.managed_python,
        )
    except (Stage35Hold, OSError, ValueError, json.JSONDecodeError, KeyError, zipfile.BadZipFile) as exc:
        print(json.dumps({"schema": SCHEMA, "state": "HOLD", "reason": type(exc).__name__,
                          "detail": str(exc)[:180]}))
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["state"] == "ISOLATED_TESTS_PASS_NOT_DEPLOYED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
