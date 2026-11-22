#!/usr/bin/env python3
"""Bounded, sequential CGX PrintSpace regression batch with durable receipts.

Only fixed, read-only test commands execute. No device, agent, git mutation,
network, mint, payment, launch, shutdown, or physical control authority exists.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from typing import Any

SCHEMA = "CGX-PRINTSPACE-SEQUENTIAL-REGRESSION/0.1"
# These are existing tests of the canonical manufacturing engine and safe review gate.
SUITES = (
    ("pc01-contract", "tests/test_pc01_printceptor_contract.py"),
    ("geometry-atlas", "tests/test_cgx_component_atlas.py"),
    ("instance-proof", "tests/test_cgx_component_instance_contract.py"),
    ("manufacturing-ir", "tests/test_cgx_manufacturing_compiler.py"),
    ("exact-binding", "tests/test_cgx_exact_binding_bridge.py"),
    ("printable-4d", "tests/test_cgx_printable_4d_stack.py"),
    ("volumetric", "tests/test_cgx_volumetric_kernel.py"),
    ("compound-decomposition", "tests/test_cgx_compound_decomposition.py"),
    ("quantitative-invariants", "tests/test_cgx_quantitative_invariants.py"),
    ("type1-stack", "tests/test_universal_type1_stack_compiler.py"),
    ("equation-kernel", "tests/test_type1_equation_kernel.py"),
    ("owner-matrix-index", "tests/test_printspace_owner_matrix_projection.py"),
    ("pre-dbr-archive", "tests/test_printspace_pre_dbr_archive_register.py"),
    ("geometry-composition", "tests/test_printspace_composition.py"),
    ("exact-convex-contact", "tests/test_printspace_exact_contact.py"),
    ("directional-witness-plan", "tests/test_printspace_interface_witness_plan.py"),
    ("nominal-solid-metrics", "tests/test_printspace_solid_metrics.py"),
    ("digital-service-backtrace", "tests/test_printspace_digital_service_stack.py"),
    ("printspace-review", "tests/test_printspace_review_gate.py"),
)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8")


def commit_json(path: Path, data: dict) -> None:
    """Atomic replace: a crash cannot leave a half-written batch receipt."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".cgx-receipt-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(json_bytes(data))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def git_head(root: Path) -> str | None:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5, check=False)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def fixed_plan(profile: str, python_executable: str = sys.executable) -> list[tuple[str, list[str]]]:
    if profile not in ("printspace", "comprehensive"):
        raise ValueError("Unsupported named test profile")
    selection = SUITES[-5:] if profile == "printspace" else SUITES
    return [(name, [python_executable, "-m", "pytest", "-q", path]) for name, path in selection]


def run_sequence(steps: list[tuple[str, list[str]]], *, root: Path, output: Path,
                 step_limit_s: float, total_limit_s: float, rest_s: float,
                 clock=time.monotonic, sleeper=time.sleep) -> dict[str, Any]:
    """Execute fixed reviewed steps in order and persist a receipt after each one.

    Tests may have side effects in their own fixtures; caller must use approved
    test targets. This function is never a machine or deployment executor.
    """
    if not (root / "cgx" / "manufacturing" / "compiler.py").is_file():
        raise ValueError("Not the expected canonical CGX LightSpeed checkout")
    if not (0 <= rest_s <= 30 and 1 <= step_limit_s <= 1800 and 1 <= total_limit_s <= 7200):
        raise ValueError("Invalid bounded time settings")
    if len(steps) > len(SUITES) or len({n for n, _ in steps}) != len(steps):
        raise ValueError("Duplicate or excessive batch steps")
    output.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + str(os.getpid())
    receipt_path = output / ("printspace-regression-" + run_id + ".json")
    receipt: dict[str, Any] = {
        "schema": SCHEMA, "run_id": run_id, "created_utc": utcnow(),
        "checkout_git_sha": git_head(root),
        "fixed_commands_sha256": sha256(json_bytes({"steps": steps})),
        "state": "RUNNING", "review_authority": "TESTS_ONLY",
        "physical_machine_authorised": False, "mint_authorised": False,
        "commercial_release_authorised": False,
        "no_remote_desktop_calls": True,
        "steps_planned": len(steps), "steps": [],
        "step_timeout_s": step_limit_s, "total_timeout_s": total_limit_s,
    }
    commit_json(receipt_path, receipt)
    start = clock()
    for index, (name, argv) in enumerate(steps, start=1):
        if not isinstance(name, str) or not name.replace("-", "").isalnum():
            raise ValueError("Unsafe stage name")
        if (not isinstance(argv, list) or any(not isinstance(x, str) for x in argv)
                or not argv):
            raise ValueError("Invalid argument vector")
        if clock() - start >= total_limit_s:
            receipt["state"] = "HOLD_TIME_BUDGET"
            receipt["failure_stage"] = name
            commit_json(receipt_path, receipt)
            break
        log = output / f"{run_id}-{index:02}-{name}.log"
        began = utcnow()
        t0 = clock()
        status, rc, note = "ERROR", None, ""
        remaining = max(0.001, total_limit_s - (clock() - start))
        try:
            with log.open("wb") as fh:
                result = subprocess.run(argv, cwd=root, stdin=subprocess.DEVNULL,
                                        stdout=fh, stderr=subprocess.STDOUT,
                                        timeout=min(step_limit_s, remaining), check=False)
                rc = result.returncode
            status = "PASS" if rc == 0 else "FAIL"
        except subprocess.TimeoutExpired:
            status, note = "TIMEOUT", "Step reached its bounded timeout"
        except OSError as exc:
            status, note = "ERROR", type(exc).__name__
        data = log.read_bytes() if log.is_file() else b""
        receipt["steps"].append({
            "index": index, "name": name, "command": argv[1:],
            "status": status, "exit_code": rc, "began_utc": began,
            "ended_utc": utcnow(), "elapsed_s": round(clock() - t0, 3),
            "log_file": log.name, "log_bytes": len(data), "log_sha256": sha256(data),
            "note": note,
        })
        receipt["state"] = "RUNNING" if status == "PASS" else "HOLD_FAILURE"
        if status != "PASS":
            receipt["failure_stage"] = name
        commit_json(receipt_path, receipt)
        if status != "PASS":
            break
        if index < len(steps) and rest_s:
            if clock() - start + rest_s >= total_limit_s:
                receipt["state"] = "HOLD_TIME_BUDGET"
                receipt["failure_stage"] = "rest-before-next-stage"
                commit_json(receipt_path, receipt)
                break
            sleeper(rest_s)
    else:
        receipt["state"] = "PASS_TESTS_ONLY"
        commit_json(receipt_path, receipt)
    receipt["ended_utc"] = utcnow()
    receipt["elapsed_s"] = round(clock() - start, 3)
    receipt["receipt_file"] = receipt_path.name
    commit_json(receipt_path, receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=["printspace", "comprehensive"], default="comprehensive")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, default=Path(tempfile.gettempdir()) / "cgx-printspace-batches")
    parser.add_argument("--step-limit-seconds", type=float, default=240)
    parser.add_argument("--total-limit-seconds", type=float, default=900)
    parser.add_argument("--rest-seconds", type=float, default=1)
    args = parser.parse_args(argv)
    try:
        receipt = run_sequence(fixed_plan(args.profile), root=args.repo.resolve(),
                               output=args.output_dir.resolve(),
                               step_limit_s=args.step_limit_seconds,
                               total_limit_s=args.total_limit_seconds,
                               rest_s=args.rest_seconds)
    except (ValueError, OSError) as exc:
        print("HOLD: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps({k: receipt[k] for k in ("run_id", "state", "steps_planned", "elapsed_s", "receipt_file")}, sort_keys=True))
    return 0 if receipt["state"] == "PASS_TESTS_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())