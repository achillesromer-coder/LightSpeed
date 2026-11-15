from __future__ import annotations

"""Bounded operator controls for LightSpeed Runtime productization.

This module intentionally manages only named runtime slots under one managed
root. It does not expose arbitrary command execution, arbitrary delete paths,
canonical promotion, or public-release authority.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
INSTALLER = REPO_ROOT / "tools" / "install_lightspeed_runtime.ps1"
DEFAULT_MANAGED_ROOT = REPO_ROOT / "State" / "Install" / "managed-runtime"
PROFILES = {"core", "api", "data", "validation", "dev", "desktop"}
ACTIONS = {"status", "configure", "install", "update", "rollback"}
SLOT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,47}$")
MARKER_NAME = ".lightspeed-managed-runtime.json"
CONFIG_NAME = "runtime-config.json"


class RuntimeProductizationError(ValueError):
    """Raised when a managed-runtime request violates the bounded contract."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise RuntimeProductizationError(f"expected object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _git_head() -> str:
    return subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        text=True,
    ).strip()


def _managed_root() -> Path:
    value = os.environ.get("LIGHTSPEED_RUNTIME_MANAGED_ROOT")
    return Path(value).expanduser() if value else DEFAULT_MANAGED_ROOT


def _reject_redirected_directory(path: Path, label: str) -> None:
    """Reject symlinks and Windows junction/reparse directories before file access.

    On Windows, junctions can have the reparse attribute without reporting as
    Path.is_symlink(). 0x400 is FILE_ATTRIBUTE_REPARSE_POINT.
    """
    try:
        metadata = path.lstat()
    except (FileNotFoundError, NotADirectoryError):
        return
    if (getattr(metadata, "st_file_attributes", 0) & 0x400) or path.is_symlink():
        raise RuntimeProductizationError(
            f"{label} must not be a symlink or Windows reparse point"
        )


def _reject_redirected_ancestors(path: Path, label: str) -> None:
    """Fail closed on redirected ancestors, not only the managed-root leaf.

    This is a preflight check, not an atomic guarantee against filesystem
    races; target-host acceptance must separately test reparse/TOCTOU cases.
    """
    if not path.is_absolute() or ".." in path.parts:
        raise RuntimeProductizationError(
            f"{label} must be an absolute path without parent traversal"
        )
    for ancestor in reversed(path.parents):
        _reject_redirected_directory(ancestor, f"{label} ancestor")
    _reject_redirected_directory(path, label)


def _safe_slot(slot: str) -> str:
    slot = str(slot or "").strip()
    if not SLOT_RE.fullmatch(slot):
        raise RuntimeProductizationError(
            "slot must match ^[A-Za-z0-9][A-Za-z0-9_.-]{0,47}$"
        )
    # Windows device aliases and trailing dots are not distinct filesystem slots.
    # Reject before constructing any managed path or receipt identifier.
    if slot.endswith(".") or re.fullmatch(
        r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:[.].*)?",
        slot,
        flags=re.IGNORECASE,
    ):
        raise RuntimeProductizationError(
            "slot uses a Windows-reserved device name or trailing dot"
        )
    return slot


def _paths(slot: str) -> dict[str, Path]:
    slot = _safe_slot(slot)
    root = _managed_root()
    slot_dir = root / slot
    _reject_redirected_ancestors(root, "managed root")
    _reject_redirected_directory(slot_dir, "managed slot")
    # Nested runtime and receipt paths must not redirect outside the managed root.
    _reject_redirected_directory(slot_dir / "venv", "managed venv")
    _reject_redirected_directory(slot_dir / "venv" / "Scripts", "managed venv scripts")
    # Leaf files can also redirect outside the managed slot (not only directories).
    _reject_redirected_directory(slot_dir / MARKER_NAME, "managed marker")
    _reject_redirected_directory(slot_dir / CONFIG_NAME, "managed config")
    _reject_redirected_directory(slot_dir / "venv" / "Scripts" / "python.exe", "managed python")
    receipt_root = root / "_receipts"
    _reject_redirected_directory(receipt_root, "receipt root")
    return {
        "root": root,
        "slot_dir": slot_dir,
        "venv": slot_dir / "venv",
        "marker": slot_dir / MARKER_NAME,
        "config": slot_dir / CONFIG_NAME,
        "receipt_root": receipt_root,
    }


def _marker(slot: str, profile: str) -> dict[str, Any]:
    return {
        "schema": "LIGHTSPEED-MANAGED-RUNTIME-MARKER/0.1",
        "slot": slot,
        "profile": profile,
        "repo_root": str(REPO_ROOT),
        "source_head": _git_head(),
        "created_utc": _now(),
        "authority": "digital-runtime-slot-only",
    }


def _load_slot_config(paths: dict[str, Path]) -> dict[str, Any] | None:
    path = paths["config"]
    return _read_json(path) if path.exists() else None


def _select_profile(paths: dict[str, Path], profile: str | None) -> str:
    if profile:
        profile = str(profile).strip().lower()
        if profile not in PROFILES:
            raise RuntimeProductizationError(
                f"profile must be one of: {', '.join(sorted(PROFILES))}"
            )
        return profile
    config = _load_slot_config(paths)
    if config and config.get("profile") in PROFILES:
        return str(config["profile"])
    return "core"


def _require_confirmed(action: str, confirmed: bool) -> None:
    if action != "status" and confirmed is not True:
        raise RuntimeProductizationError(f"{action} requires confirmed=true")


def _validate_marker(paths: dict[str, Path], slot: str) -> dict[str, Any]:
    # Recheck root and slot immediately before trusting a marker.
    _reject_redirected_ancestors(paths["root"], "managed root")
    _reject_redirected_directory(paths["slot_dir"], "managed slot")
    marker_path = paths["marker"]
    if not marker_path.exists():
        raise RuntimeProductizationError(
            f"managed marker missing for slot '{slot}'; refusing mutation"
        )
    marker = _read_json(marker_path)
    if marker.get("schema") != "LIGHTSPEED-MANAGED-RUNTIME-MARKER/0.1":
        raise RuntimeProductizationError("managed marker schema mismatch")
    if marker.get("slot") != slot:
        raise RuntimeProductizationError("managed marker slot mismatch")
    # A matching slot/schema alone cannot establish managed ownership.
    # Keep the local marker a bounded ownership signal, never a host lease.
    if marker.get("authority") != "digital-runtime-slot-only":
        raise RuntimeProductizationError("managed marker authority mismatch")
    if not isinstance(marker.get("profile"), str) or marker["profile"] not in PROFILES:
        raise RuntimeProductizationError("managed marker profile invalid")
    return marker


def _operator_receipt(
    paths: dict[str, Path],
    *,
    slot: str,
    action: str,
    profile: str | None,
    status: str,
    detail: dict[str, Any],
) -> Path:
    _reject_redirected_ancestors(paths["root"], "managed root")
    _reject_redirected_directory(paths["receipt_root"], "receipt root")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    receipt = paths["receipt_root"] / f"{slot}-{action}-{stamp}.json"
    _write_json(
        receipt,
        {
            "schema": "LIGHTSPEED-RUNTIME-OPERATOR-RECEIPT/0.1",
            "slot": slot,
            "action": action,
            "profile": profile,
            "status": status,
            "generated_utc": _now(),
            "source_head": _git_head(),
            "managed_root": str(paths["root"]),
            "slot_root": str(paths["slot_dir"]),
            "authority": "digital-runtime-management-only",
            "canonical_promotion": False,
            "public_release": False,
            "detail": detail,
        },
    )
    return receipt


def runtime_productization_status(slot: str = "default") -> dict[str, Any]:
    slot = _safe_slot(slot)
    paths = _paths(slot)
    # Status is diagnostic and read-only. Malformed or foreign slot configs
    # are not trusted as configured; preserve their bytes for investigation.
    try:
        config = _load_slot_config(paths)
    except (RuntimeProductizationError, OSError, ValueError, UnicodeError):
        config = None
    if config and (
        config.get("schema") != "LIGHTSPEED-RUNTIME-SLOT-CONFIG/0.1"
        or config.get("slot") != slot
        or not isinstance(config.get("profile"), str)
        or config.get("profile") not in PROFILES
        or config.get("authority") != "digital-runtime-config-only"
    ):
        config = None
    # A corrupt ownership marker must never make status appear installed.
    # Status is read-only; keep invalid marker bytes untouched for diagnosis.
    try:
        marker = _read_json(paths["marker"]) if paths["marker"].exists() else None
    except (RuntimeProductizationError, OSError, ValueError, UnicodeError):
        marker = None
    python_path = paths["venv"] / "Scripts" / "python.exe"
    receipts = []
    if paths["receipt_root"].exists():
        receipts = sorted(
            (
                str(path)
                for path in paths["receipt_root"].glob(f"{_safe_slot(slot)}-*.json")
            ),
            reverse=True,
        )[:20]
    # Presence of python.exe alone is not proof of managed installation.
    # Keep status read-only and fail closed on absent/invalid ownership evidence.
    try:
        validated_marker = _validate_marker(paths, slot)
        managed_ownership_valid = True
    except (RuntimeProductizationError, OSError, ValueError, TypeError):
        managed_ownership_valid = False
        validated_marker = None
    return {
        "schema": "LIGHTSPEED-RUNTIME-PRODUCTIZATION-STATUS/0.1",
        "slot": _safe_slot(slot),
        "source_head": _git_head(),
        "managed_root": str(paths["root"]),
        "slot_root": str(paths["slot_dir"]),
        "managed_marker": marker is not None,
        "configured": config is not None,
        "profile": (config or {}).get("profile") or (validated_marker or {}).get("profile"),
        "installed": managed_ownership_valid and python_path.is_file(),
        "python": str(python_path),
        "recent_receipts": receipts,
        "authority": "status-only",
    }


def _configure(paths: dict[str, Path], slot: str, profile: str) -> dict[str, Any]:
    # Do not adopt a pre-existing unmarked directory: a later rollback would
    # otherwise delete unrelated files after this method minted a marker.
    slot_dir = paths["slot_dir"]
    _reject_redirected_ancestors(paths["root"], "managed root")
    _reject_redirected_directory(slot_dir, "managed slot")
    if slot_dir.exists():
        _validate_marker(paths, slot)
    else:
        slot_dir.mkdir(parents=True, exist_ok=False)
        _write_json(paths["marker"], _marker(slot, profile))
    payload = {
        "schema": "LIGHTSPEED-RUNTIME-SLOT-CONFIG/0.1",
        "slot": slot,
        "profile": profile,
        "source_head": _git_head(),
        "updated_utc": _now(),
        "authority": "digital-runtime-config-only",
    }
    _write_json(paths["config"], payload)
    return payload


def _run_installer_process(
    paths: dict[str, Path],
    *,
    profile: str,
    action: str,
) -> dict[str, Any]:
    _reject_redirected_ancestors(paths["root"], "managed root")
    _reject_redirected_directory(paths["venv"], "managed venv")
    _reject_redirected_directory(paths["venv"] / "Scripts", "managed venv scripts")
    _reject_redirected_directory(paths["receipt_root"], "receipt root")
    if not INSTALLER.exists():
        raise RuntimeProductizationError(f"installer missing: {INSTALLER}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    install_receipt = (
        paths["receipt_root"] / f"{paths['slot_dir'].name}-{action}-installer-{stamp}.json"
    )
    install_receipt.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "powershell",
        "-NoProfile",
        # Inherit effective host policy; never request a process-level bypass.
        "-File",
        str(INSTALLER),
        "-Profile",
        profile,
        "-VenvPath",
        str(paths["venv"]),
        "-ReceiptPath",
        str(install_receipt),
    ]
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeProductizationError(
            f"installer failed ({completed.returncode}): "
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )
    if not install_receipt.exists():
        raise RuntimeProductizationError("installer completed without receipt")
    return {
        "installer_receipt": str(install_receipt),
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "returncode": completed.returncode,
    }


def manage_runtime_productization(
    action: str,
    *,
    slot: str = "default",
    profile: str | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    action = str(action or "").strip().lower()
    if action not in ACTIONS:
        raise RuntimeProductizationError(
            f"action must be one of: {', '.join(sorted(ACTIONS))}"
        )
    slot = _safe_slot(slot)
    paths = _paths(slot)
    if action == "status":
        return runtime_productization_status(slot)

    _require_confirmed(action, confirmed)
    selected_profile = _select_profile(paths, profile)

    if action == "configure":
        configured = _configure(paths, slot, selected_profile)
        receipt = _operator_receipt(
            paths,
            slot=slot,
            action=action,
            profile=selected_profile,
            status="PASS",
            detail={"config": configured},
        )
        return {
            "status": "PASS",
            "action": action,
            "slot": slot,
            "profile": selected_profile,
            "receipt": str(receipt),
            "state": runtime_productization_status(slot),
        }

    if action == "install":
        if (paths["venv"] / "Scripts" / "python.exe").exists():
            raise RuntimeProductizationError(
                f"slot '{slot}' is already installed; use update"
            )
        _configure(paths, slot, selected_profile)
        detail = _run_installer_process(
            paths, profile=selected_profile, action=action
        )
        receipt = _operator_receipt(
            paths,
            slot=slot,
            action=action,
            profile=selected_profile,
            status="PASS",
            detail=detail,
        )
        return {
            "status": "PASS",
            "action": action,
            "slot": slot,
            "profile": selected_profile,
            "receipt": str(receipt),
            "state": runtime_productization_status(slot),
        }

    if action == "update":
        _validate_marker(paths, slot)
        if not (paths["venv"] / "Scripts" / "python.exe").exists():
            raise RuntimeProductizationError(
                f"slot '{slot}' is not installed; use install"
            )
        _configure(paths, slot, selected_profile)
        detail = _run_installer_process(
            paths, profile=selected_profile, action=action
        )
        receipt = _operator_receipt(
            paths,
            slot=slot,
            action=action,
            profile=selected_profile,
            status="PASS",
            detail=detail,
        )
        return {
            "status": "PASS",
            "action": action,
            "slot": slot,
            "profile": selected_profile,
            "receipt": str(receipt),
            "state": runtime_productization_status(slot),
        }

    if action == "rollback":
        _validate_marker(paths, slot)
        before = runtime_productization_status(slot)
        if paths["slot_dir"].exists():
            shutil.rmtree(paths["slot_dir"])
        receipt = _operator_receipt(
            paths,
            slot=slot,
            action=action,
            profile=before.get("profile"),
            status="PASS",
            detail={
                "removed_slot_root": str(paths["slot_dir"]),
                "slot_exists_after": paths["slot_dir"].exists(),
            },
        )
        return {
            "status": "PASS",
            "action": action,
            "slot": slot,
            "receipt": str(receipt),
            "state": runtime_productization_status(slot),
        }

    raise AssertionError("unreachable")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=sorted(ACTIONS))
    parser.add_argument("--slot", default="default")
    parser.add_argument("--profile", choices=sorted(PROFILES))
    parser.add_argument("--confirmed", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = manage_runtime_productization(
            args.action,
            slot=args.slot,
            profile=args.profile,
            confirmed=args.confirmed,
        )
    except Exception as exc:
        sys.stdout.write(
            json.dumps(
                {
                    "ok": False,
                    "error": type(exc).__name__,
                    "message": str(exc),
                },
                ensure_ascii=False,
            )
            + "\n"
        )
        return 2
    sys.stdout.write(json.dumps({"ok": True, "result": result}, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
