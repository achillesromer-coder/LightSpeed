"""Bounded one-call CGX review batch: read-only checks, no merge/mint/deploy.

Run after updating an isolated review worktree:
  python cgx/bootstrap/cgx_dynamic_batch.py --base <previous_sha> --mode plan
  python cgx/bootstrap/cgx_dynamic_batch.py --base <previous_sha> --mode verify

The runner selects approved tests from exact Git path families, uses argv arrays
(no shell interpolation), enforces a timeout per job, and emits a JSON receipt.
It never copies sources, changes refs, runs model-supplied commands or publishes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "CGX-BOUNDED-DYNAMIC-BATCH-REVIEW/0.1"
SHA = re.compile(r"^[0-9a-f]{7,40}$")
PATH = re.compile(r"^[A-Za-z0-9._/-]+$")
ALLOWED_PREFIXES = (
    ".github/workflows/", "apps/lightspeed-go/", "cgx/",
    "desktop/LightSpeed_Runtime/", "docs/", "scripts/", "tests/",
)
ORDER = (
    "git-index", "source-manifest", "load-registry",
    "core-node", "facet-node", "load-python", "host-evidence",
    "public-guard", "app-check", "app-vitest", "product-package",
)
TIMEOUT_SECONDS = 180


def allowed_path(path: str) -> bool:
    return (
        isinstance(path, str) and bool(PATH.fullmatch(path))
        and len(path) <= 240 and not path.startswith("/")
        and all(piece not in ("", ".", "..") for piece in path.split("/"))
        and (path in ("desktop/source-manifest.json", "tools/cgx_setup_windows.ps1")
             or any(path.startswith(prefix) for prefix in ALLOWED_PREFIXES))
        and not path.startswith("apps/lightspeed-go/dist/")
        and not path.startswith("apps/lightspeed-go/node_modules/")
    )


def choose_lanes(paths: list[str]) -> tuple[str, ...]:
    if not isinstance(paths, list) or not paths or len(paths) > 300:
        raise ValueError("EMPTY_OR_UNBOUNDED_DELTA")
    if len(paths) != len(set(paths)) or not all(allowed_path(p) for p in paths):
        raise ValueError("UNQUALIFIED_OR_DUPLICATE_SOURCE_PATH")
    lanes = {"git-index", "source-manifest", "load-registry"}
    for path in paths:
        if path.startswith("cgx/") or path.startswith("scripts/"):
            lanes.update(("core-node", "load-python"))
        if path.startswith("cgx/review/") or "cgxFacetProjection" in path or path.startswith("tests/test_unispace_"):
            lanes.add("facet-node")
        if path.startswith("desktop/LightSpeed_Runtime/"):
            lanes.add("host-evidence")
        if path.startswith("apps/lightspeed-go/"):
            lanes.update(("app-check", "app-vitest"))
        if path.startswith("apps/lightspeed-go/scripts/package_unispace") or path.startswith("apps/lightspeed-go/scripts/test_package_unispace"):
            lanes.add("product-package")
        if path.startswith("apps/lightspeed-go/public/") or "public_bundle" in path:
            lanes.add("public-guard")
    # Every batch includes publication isolation and object-policy negatives.
    lanes.update(("public-guard", "facet-node"))
    return tuple(name for name in ORDER if name in lanes)


def git_output(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), *args], text=True, timeout=45, stderr=subprocess.DEVNULL
    ).strip()


def delta_from_base(base: str) -> tuple[str, list[str]]:
    if not SHA.fullmatch(base):
        raise ValueError("INVALID_BASE_SHA")
    head = git_output("rev-parse", "HEAD")
    if subprocess.run(
        ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", base, head],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=45,
        check=False,
    ).returncode != 0:
        raise ValueError("BASE_IS_NOT_ANCESTOR")
    raw = git_output("diff", "--name-only", "--diff-filter=AM", base, head)
    return head, raw.splitlines() if raw else []


def test_commands(lanes: tuple[str, ...]) -> list[tuple[str, list[str], Path]]:
    py = sys.executable
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm") or "npm"
    node = shutil.which("node") or "node"
    app = ROOT / "apps/lightspeed-go"
    def tests(*patterns: str) -> list[str]:
        found = {p.relative_to(ROOT).as_posix()
                 for pattern in patterns for p in ROOT.glob(pattern) if p.is_file()}
        return sorted(found)
    jobs = []
    if "git-index" in lanes:
        jobs.append(("git-index", ["git", "diff", "--check", "HEAD"], ROOT))
    if "source-manifest" in lanes:
        jobs.append(("source-manifest", [py, "cgx/bootstrap/cgxManifestIntegrityReview.py"], ROOT))
    if "load-registry" in lanes:
        jobs.append(("load-registry", [node, "cgx/load_minimum/refreshLoadRegistry.mjs", "--check"], ROOT))
    if "core-node" in lanes:
        filenames = tests("cgx/bootstrap/*.test.mjs", "cgx/load_minimum/*.test.mjs")
        if not filenames:
            raise ValueError("CORE_TEST_DISCOVERY_EMPTY")
        jobs.append(("core-node", [node, "--test", *filenames], ROOT))
    if "facet-node" in lanes:
        filenames = tests("cgx/review/*.test.mjs", "tests/test_unispace_permissioned_projection.mjs")
        if not filenames:
            raise ValueError("FACET_TEST_DISCOVERY_EMPTY")
        jobs.append(("facet-node", [node, "--test", *filenames], ROOT))
    if "load-python" in lanes:
        jobs.append(("load-python", [py, "-m", "unittest", "discover", "-s",
                                    "cgx/load_minimum", "-p", "test_*.py"], ROOT))
    if "host-evidence" in lanes:
        jobs.append(("host-evidence", [py, "-m", "pytest", "-q",
                                     "desktop/LightSpeed_Runtime/tests/test_host_owned_receipts.py"], ROOT))
    if "public-guard" in lanes:
        jobs.append(("public-guard", [py, "-m", "unittest", "discover", "-s",
                                     "tests", "-p", "test_cgx_public_bundle_guard.py"], ROOT))
    if "app-check" in lanes:
        jobs.append(("app-check", [npm, "run", "check"], app))
    if "app-vitest" in lanes:
        jobs.append(("app-vitest", [npm, "test", "--", "--run",
                                     "tests/unispace-public.test.mjs",
                                     "tests/unispace-domains.test.mjs",
                                     "tests/owner-progress.test.mjs",
                                     "tests/unispace-offline-selector-negative.test.mjs",
                                     "src/cgxFacetProjection.test.mjs",
                                     "src/cgxFirstSpacesReview.test.mjs",
                                     "src/cgxLoadBatchDraft.test.mjs"], app))
    if "product-package" in lanes:
        jobs.append(("product-package", [py, "-m", "unittest", "discover", "-s",
                     "apps/lightspeed-go/scripts", "-p", "test_package_unispace*.py"], ROOT))
    return jobs


def run_batch(base: str, mode: str) -> dict:
    head, changed = delta_from_base(base)
    lanes = choose_lanes(changed)
    jobs = test_commands(lanes)
    receipt = {
        "schema": SCHEMA, "mode": mode, "head_sha": head, "base_sha": base,
        "changed_paths": changed, "selected_lanes": list(lanes),
        "command_ids": [item[0] for item in jobs],
        "command_source": "FIXED_ALLOWLIST_NO_MODEL_COMMANDS",
        "native_admitted": False, "signed_issuer_verified": False,
        "two_node_dbr_verified": False, "minted": False, "deployed": False,
        "public_release_authorized": False, "canonical_mutation": False,
        "jobs": [], "result": "PLAN_ONLY" if mode == "plan" else "PENDING",
    }
    if mode == "plan":
        return receipt
    # Reject a dirty source checkout: staged/untracked work is not tested implicitly.
    if git_output("status", "--porcelain"):
        receipt["result"] = "HOLD_DIRTY_WORKTREE"
        return receipt
    for ident, argv, cwd in jobs:
        start = time.monotonic()
        try:
            result = subprocess.run(
                argv, cwd=cwd, text=False, capture_output=True,
                timeout=TIMEOUT_SECONDS, check=False, shell=False,
            )
            ok = result.returncode == 0
            entry = {"id": ident, "pass": ok, "exit_code": result.returncode,
                     "elapsed_ms": round((time.monotonic() - start) * 1000),
                     "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
                     "stderr_sha256": hashlib.sha256(result.stderr).hexdigest()}
        except (OSError, subprocess.TimeoutExpired) as exc:
            entry = {"id": ident, "pass": False,
                     "error_class": type(exc).__name__,
                     "elapsed_ms": round((time.monotonic() - start) * 1000)}
            ok = False
        receipt["jobs"].append(entry)
        if not ok:
            receipt["result"] = "HOLD_VALIDATION_FAILED"
            return receipt
    receipt["result"] = "SOURCE_REVIEW_TESTS_PASSED_NOT_NATIVE_ADMITTED"
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="ancestor Git SHA, hex only")
    parser.add_argument("--mode", choices=("plan", "verify"), default="plan")
    args = parser.parse_args()
    try:
        receipt = run_batch(args.base, args.mode)
    except (ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        receipt = {"schema": SCHEMA, "result": "HOLD",
                   "error_class": type(exc).__name__, "native_admitted": False}
    print(json.dumps(receipt, sort_keys=True, indent=2))
    return 0 if receipt["result"] in (
        "PLAN_ONLY", "SOURCE_REVIEW_TESTS_PASSED_NOT_NATIVE_ADMITTED") else 2


if __name__ == "__main__":
    raise SystemExit(main())
