#!/usr/bin/env python3
"""Read-only LS GO singleton health gate for Achilles / existing LightSpeed.

Does not unlink locks, restart consumers, submit jobs, inspect private command
content, or grant owner approval. Windows PID identity is corroborating evidence
only: even a fresh heartbeat never self-authorises task execution.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

SCHEMA = "CGX-ACHILLES-LSGO-CONSUMER-PREFLIGHT/0.1"
CONSUMER_SCHEMA = "lightspeed-ls-go-job-consumer-v1"
MAX_LOCK_BYTES = 16_384


class ConsumerHealthHold(ValueError):
    """Untrusted lock metadata, process identity, or unsupported environment."""


def parse_utc(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ConsumerHealthHold("MISSING_UTC_TIMESTAMP")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ConsumerHealthHold("MALFORMED_UTC_TIMESTAMP") from exc
    if parsed.tzinfo is None:
        raise ConsumerHealthHold("UNZONED_TIMESTAMP")
    return parsed.astimezone(timezone.utc)


def process_snapshot_windows(pid: int) -> dict[str, Any] | None:
    """Bounded fixed PowerShell read-only WMI query; never accepts shell text."""
    if os.name != "nt" or not isinstance(pid, int) or pid <= 0:
        return None
    command = (
        "$p=Get-CimInstance Win32_Process -Filter 'ProcessId = " + str(pid)
        + "' -ErrorAction SilentlyContinue;"
        + "if($p){[pscustomobject]@{pid=$p.ProcessId;name=$p.Name;"
        + "created_utc=$p.CreationDate.ToUniversalTime().ToString('o')}"
        + "|ConvertTo-Json -Compress}"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=9, check=False,
        )
        if result.returncode or not result.stdout.strip():
            return None
        observation = json.loads(result.stdout)
        return observation if isinstance(observation, dict) else None
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None


def inspect_heartbeat(
    lock: dict[str, Any],
    observed: dict[str, Any] | None,
    *,
    now: datetime | None = None,
    stale_seconds: int = 180,
) -> dict[str, Any]:
    if not isinstance(lock, dict) or lock.get("schema_version") != CONSUMER_SCHEMA:
        raise ConsumerHealthHold("CONSUMER_LOCK_SCHEMA_HOLD")
    pid = lock.get("pid")
    if type(pid) is not int or not 1 <= pid <= 2**32 - 1:
        raise ConsumerHealthHold("LOCK_PID_SHAPE_HOLD")
    instant = datetime.now(timezone.utc) if now is None else now
    if instant.tzinfo is None:
        raise ConsumerHealthHold("UNZONED_NOW")
    heartbeat = parse_utc(lock.get("heartbeat_utc"))
    age = (instant.astimezone(timezone.utc) - heartbeat).total_seconds()
    if age < -30:
        raise ConsumerHealthHold("FUTURE_HEARTBEAT_HOLD")
    observation = observed if isinstance(observed, dict) else {}
    name = str(observation.get("name") or "").casefold()
    observed_pid = observation.get("pid")
    creation = observation.get("created_utc")
    birth = parse_utc(creation) if creation else None
    pid_matches = type(observed_pid) is int and observed_pid == pid
    reuse = bool(birth is not None and birth > heartbeat)
    if not pid_matches:
        state = "PROCESS_IDENTITY_UNVERIFIED_HOLD"
    elif reuse:
        state = "PID_REUSED_AFTER_HEARTBEAT_HOLD"
    elif name not in {"python.exe", "pythonw.exe"}:
        state = "NON_CONSUMER_PROCESS_HOLD"
    elif age > stale_seconds:
        state = "STALE_CONSUMER_HEARTBEAT_HOLD"
    elif birth is None:
        state = "PROCESS_BIRTH_UNVERIFIED_HOLD"
    else:
        state = "FRESH_CONSUMER_PROCESS_CANDIDATE_NOT_AUTHORISED"
    return {
        "schema": SCHEMA,
        "state": state,
        "recorded_pid": pid,
        "observed_pid": observed_pid if pid_matches else None,
        "observed_process_name": name or None,
        "heartbeat_age_seconds": round(age, 2),
        "pid_reused": reuse,
        "heartbeat_stale": age > stale_seconds,
        "consumer_execution_authorized": False,
        "process_thread_verified": False,
        "lease_verified": False,
        "owner_approval_verified": False,
        "lock_modified": False,
        "service_restarted": False,
        "job_dispatched": False,
        "next": (
            "Verify singleton thread, exact leases and durable job receipts "
            "through existing host owner controls; do not delete PID-reused "
            "lock or auto-start a second consumer from this preflight."
        ),
    }


def inspect_lock_path(path: Path, *, now: datetime | None = None) -> dict[str, Any]:
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_LOCK_BYTES:
        raise ConsumerHealthHold("CONSUMER_LOCK_FILE_HOLD")
    raw = path.read_bytes()
    try:
        lock = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ConsumerHealthHold("CONSUMER_LOCK_JSON_HOLD") from exc
    observed = process_snapshot_windows(lock.get("pid"))
    result = inspect_heartbeat(lock, observed, now=now)
    result["lock_sha256"] = hashlib.sha256(raw).hexdigest()
    result["process_observation_source"] = (
        "WINDOWS_WMI_READ_ONLY" if observed is not None else "PROCESS_UNVERIFIED"
    )
    return result


def self_test() -> dict[str, Any]:
    now = datetime.fromisoformat("2026-11-01T12:00:00+00:00")
    sample = {"schema_version": CONSUMER_SCHEMA, "pid": 1234,
              "heartbeat_utc": "2026-10-30T04:28:10+00:00"}
    reused = {"pid": 1234, "name": "node.exe",
              "created_utc": "2026-10-30T05:00:00+00:00"}
    assert inspect_heartbeat(sample, reused, now=now)["state"] == "PID_REUSED_AFTER_HEARTBEAT_HOLD"
    old_python = {"pid": 1234, "name": "python.exe",
                  "created_utc": "2026-10-29T00:00:00+00:00"}
    assert inspect_heartbeat(sample, old_python, now=now)["state"] == "STALE_CONSUMER_HEARTBEAT_HOLD"
    assert inspect_heartbeat(sample, None, now=now)["state"] == "PROCESS_IDENTITY_UNVERIFIED_HOLD"
    fresh = dict(sample, heartbeat_utc="2026-11-01T11:59:00+00:00")
    candidate = inspect_heartbeat(fresh, old_python, now=now)
    assert candidate["state"] == "FRESH_CONSUMER_PROCESS_CANDIDATE_NOT_AUTHORISED"
    assert candidate["consumer_execution_authorized"] is False
    try:
        inspect_heartbeat(dict(sample, schema_version="untrusted"), reused, now=now)
    except ConsumerHealthHold as e:
        assert str(e) == "CONSUMER_LOCK_SCHEMA_HOLD"
    else:
        raise AssertionError("untrusted schema accepted")
    try:
        inspect_heartbeat(dict(sample, pid=True), reused, now=now)
    except ConsumerHealthHold as e:
        assert str(e) == "LOCK_PID_SHAPE_HOLD"
    else:
        raise AssertionError("boolean pid accepted")
    assert inspect_heartbeat(sample, {"pid": 1234, "name": "node.exe"}, now=now)["state"] == "NON_CONSUMER_PROCESS_HOLD"
    assert inspect_heartbeat(sample, {"pid": 1234, "name": "python.exe"}, now=now)["state"] == "STALE_CONSUMER_HEARTBEAT_HOLD"
    return {"state": "PASS", "tests": 8, "native_mutation": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--self-test", action="store_true")
    source.add_argument("--lock", type=Path, help="Read-only singleton heartbeat lock")
    args = parser.parse_args()
    try:
        result = self_test() if args.self_test else inspect_lock_path(args.lock)
        print(json.dumps(result, sort_keys=True, indent=2))
    except (ConsumerHealthHold, OSError) as exc:
        print(json.dumps({"state": "HOLD", "reason": str(exc)[:120]}), file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
