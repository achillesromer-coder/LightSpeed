"""Bounded test-only SQLite atomic nonce proof; never touches native owner DBR."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "scripts/printspace_r0_sqlite_reference_ledger.py"
SCHEMA = "CGX-PRINTSPACE-R0-NONCE-INSERT-REQUEST/0.1"


def command(db: Path, action: str, payload: dict | None = None):
    return subprocess.run(
        [sys.executable, str(LEDGER), action, "--db", str(db)],
        cwd=ROOT, capture_output=True, text=True,
        input=json.dumps(payload) if payload is not None else None,
        timeout=10, check=False,
    )


def item(nonce: str = "a" * 64) -> dict:
    return {
        "schema": SCHEMA, "nonce_digest_sha256": nonce,
        "review_receipt_sha256": "b" * 64,
        "product_facet_sha256": "sha256:" + "c" * 64,
        "plan_sha256": "d" * 64, "expires_at_seconds": 1800000060,
    }


def test_sqlite_reference_atomic_restart_and_multiworker_conflict():
    with tempfile.TemporaryDirectory(prefix="cgx-r0-ref-") as tmp:
        db = Path(tmp) / "reference.sqlite"
        assert command(db, "init").returncode == 0
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: command(db, "consume", item()), range(12)))
        assert all(x.returncode == 0 for x in results)
        states = [json.loads(x.stdout)["state"] for x in results]
        assert states.count("INSERTED") == 1
        assert states.count("ALREADY_PRESENT") == 11
        # Different subprocess, after all prior connections closed.
        assert json.loads(command(db, "consume", item()).stdout)["state"] == "ALREADY_PRESENT"


def test_sqlite_reference_declines_unbound_and_privileged_ledger_fields():
    with tempfile.TemporaryDirectory(prefix="cgx-r0-ref-") as tmp:
        db = Path(tmp) / "reference.sqlite"
        assert command(db, "init").returncode == 0
        bad = item()
        bad["native_admitted"] = True
        r = command(db, "consume", bad)
        assert r.returncode != 0 and r.stdout == ""
        bad = item()
        bad["product_facet_sha256"] = "c" * 64
        assert command(db, "consume", bad).returncode != 0
        assert json.loads(command(db, "consume", item()).stdout)["state"] == "INSERTED"
