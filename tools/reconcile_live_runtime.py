#!/usr/bin/env python3
"""Reconcile the installed LightSpeed App/Core runtime with canonical Git bytes.

The transaction is deliberately narrow: it copies only approved, tracked runtime
surfaces, backs up every overwritten file, verifies installed hashes, and writes a
durable receipt outside the live runtime.  It never edits the live database, CGX
carriers, source checkout, credentials, queues, or project data.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import socket
import subprocess
import sys
import uuid


SCHEMA = "LIGHTSPEED-LIVE-RUNTIME-RECONCILIATION/0.1"
DEFAULT_RUNTIME_ROOT = Path(os.environ.get("LIGHTSPEED_CANONICAL_ROOT", r"D:\LightSpeed"))
DEFAULT_RECEIPT_ROOT = Path(r"C:\Cognigrex\Receipts")
SERVICE_PORTS = (4173, 4174, 8080, 8765)
DESKTOP_ALLOWED_SUFFIXES = {
    ".css", ".html", ".js", ".json", ".py", ".toml", ".yaml", ".yml"
}
DESKTOP_EXCLUDED_PARTS = {
    ".pytest_cache", "__pycache__", "data", "logs", "runtime_exports",
    "temp_shells", "tests",
}


@dataclass(frozen=True)
class Mapping:
    source: Path
    target: Path
    source_relative: str
    target_relative: str


def utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


def git_state(repo_root: Path) -> dict[str, object]:
    return {
        "head": run_git(repo_root, "rev-parse", "HEAD"),
        "origin_main": run_git(repo_root, "rev-parse", "origin/main"),
        "branch": run_git(repo_root, "branch", "--show-current"),
        "clean": run_git(repo_root, "status", "--porcelain") == "",
    }


def tracked_files(repo_root: Path) -> list[str]:
    raw = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "-z"],
        check=True,
        capture_output=True,
        timeout=60,
    ).stdout
    return [item.decode("utf-8") for item in raw.split(b"\0") if item]


def _desktop_file_allowed(relative: PurePosixPath) -> bool:
    if any(part.casefold() in DESKTOP_EXCLUDED_PARTS for part in relative.parts):
        return False
    return relative.suffix.casefold() in DESKTOP_ALLOWED_SUFFIXES


# An immutable, hash-verified deployment projection of the existing registry.
# Source files remain canonical in Git; installed Core gets read-only metadata,
# not a second mutable capability registry or a copy of private source blobs.
CGX_CATALOGUE_FIXED = (
    "cgx/domain_templates/plugin_capability_routes.json",
    "cgx/domain_templates/toolkit_registry.json",
    "cgx/domain_templates/achilles_owner_operator_profile.json",
    "cgx/domain_templates/agent_assurance_role_matrix.json",
    "cgx/domain_templates/agent_role_reconciliation.md",
    "plugins/source/selector_shortcalls.json",
    "plugins/source/selector_packages.json",
    "UniSpace/product.json",
)


def catalogue_snapshot_paths(repo_root: Path, tracked: list[str]) -> list[str]:
    present = set(tracked)
    if not set(CGX_CATALOGUE_FIXED).issubset(present):
        # Some isolated test fixtures intentionally contain no CGX catalogue.
        if not present.intersection(CGX_CATALOGUE_FIXED):
            return []
        raise RuntimeError("CGX catalogue requires complete pinned source manifests")
    selected = set(CGX_CATALOGUE_FIXED)
    packages = json.loads(
        (repo_root / "plugins/source/selector_packages.json").read_text(encoding="utf-8")
    )
    skills = packages.get("shared_skills")
    if (not isinstance(skills, list) or not 1 <= len(skills) <= 32
            or len(set(skills)) != len(skills)
            or any(not isinstance(k, str) or not k or
                   any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for ch in k)
                   for k in skills)):
        raise RuntimeError("CGX shared skill source catalogue is not bounded")
    for skill in skills:
        rel = f"plugins/source/core-skills/{skill}/SKILL.md"
        if rel not in present:
            raise RuntimeError(f"CGX skill manifest missing from tracked source: {skill}")
        selected.add(rel)

    selector_data = json.loads(
        (repo_root / "plugins/source/selector_shortcalls.json").read_text(encoding="utf-8")
    )
    floors = {str(f) for profile in selector_data["selectors"].values()
              for f in profile.get("floors", [])}
    covered = set()
    for rel in tracked:
        parts = PurePosixPath(rel).parts
        if (len(parts) == 5 and parts[:3] ==
                ("docs", "agent-ingestion", "local-agent-homes")
                and parts[-1] == "agent_manifest.json"):
            record = json.loads((repo_root / rel).read_text(encoding="utf-8"))
            floor = record.get("lightspeed_floor")
            if floor in floors:
                selected.add(rel)
                covered.add(floor)
    if covered != floors:
        raise RuntimeError("CGX selector floor manifests are incomplete for installation")
    if len(selected) > 64:
        raise RuntimeError("CGX catalogue snapshot exceeds bounded source count")
    return sorted(selected)


def build_mappings(repo_root: Path, runtime_root: Path) -> list[Mapping]:
    mappings: list[Mapping] = []
    prefixes = (
        (
            PurePosixPath("desktop/LightSpeed_Runtime/lightspeed_runtime"),
            PurePosixPath("Core/lightspeed_runtime"),
            lambda _rel: True,
        ),
        (
            PurePosixPath("desktop/Desktop_Hooks/LightSpeed"),
            PurePosixPath("App"),
            _desktop_file_allowed,
        ),
        (
            PurePosixPath("apps/lightspeed-go/dist"),
            PurePosixPath("Apps/lightspeed-go/dist"),
            lambda _rel: True,
        ),
    )
    explicit = {
        PurePosixPath("scripts/run_cognigrex_local_stack.py"):
            PurePosixPath("Automation/run_cognigrex_local_stack.py"),
        PurePosixPath("scripts/ensure_cognigrex_local_stack.py"):
            PurePosixPath("Automation/ensure_cognigrex_local_stack.py"),
        PurePosixPath("tools/run_ls_go_bridge.py"):
            PurePosixPath("Tools/run_ls_go_bridge.py"),
        PurePosixPath("scripts/cgx_assurance_route.py"):
            PurePosixPath("Tools/cgx_preflight/cgx_assurance_route.py"),
        PurePosixPath("scripts/cgx_assurance_preflight.py"):
            PurePosixPath("Tools/cgx_preflight/cgx_assurance_preflight.py"),
        PurePosixPath("scripts/resolve_cgx_extensions.py"):
            PurePosixPath("Tools/cgx_preflight/resolve_cgx_extensions.py"),
        PurePosixPath("scripts/cgx_custodial_preflight.py"):
            PurePosixPath("Tools/cgx_preflight/cgx_custodial_preflight.py"),
        PurePosixPath("cgx/domain_templates/assurance_selection_matrix.json"):
            PurePosixPath("Tools/cgx/domain_templates/assurance_selection_matrix.json"),
        PurePosixPath("cgx/domain_templates/assurance_method_registry.json"):
            PurePosixPath("Tools/cgx/domain_templates/assurance_method_registry.json"),
        PurePosixPath("cgx/domain_templates/custodial_extension_registry.json"):
            PurePosixPath("Tools/cgx/domain_templates/custodial_extension_registry.json"),
        PurePosixPath("cgx/domain_templates/cgp_ies_policy_pack.json"):
            PurePosixPath("Tools/cgx/domain_templates/cgp_ies_policy_pack.json"),
        PurePosixPath("cgx/domain_templates/cgp_ies_domain_adapter_registry.json"):
            PurePosixPath("Tools/cgx/domain_templates/cgp_ies_domain_adapter_registry.json"),
    }

    tracked = tracked_files(repo_root)
    for rel in catalogue_snapshot_paths(repo_root, tracked):
        name = PurePosixPath(rel)
        explicit[name] = PurePosixPath("Core/cgx_catalogue") / name

    for name in tracked:
        source_rel = PurePosixPath(name)
        target_rel: PurePosixPath | None = explicit.get(source_rel)
        if target_rel is None:
            for source_prefix, target_prefix, predicate in prefixes:
                try:
                    remainder = source_rel.relative_to(source_prefix)
                except ValueError:
                    continue
                if predicate(remainder):
                    target_rel = target_prefix / remainder
                break
        if target_rel is None:
            continue
        source = repo_root.joinpath(*source_rel.parts)
        if not source.is_file():
            raise RuntimeError(f"Tracked runtime source is missing: {source_rel}")
        target = runtime_root.joinpath(*target_rel.parts)
        mappings.append(Mapping(source, target, str(source_rel), str(target_rel)))

    duplicates: dict[str, int] = {}
    for mapping in mappings:
        key = os.path.normcase(str(mapping.target.absolute()))
        duplicates[key] = duplicates.get(key, 0) + 1
    collisions = [key for key, count in duplicates.items() if count > 1]
    if collisions:
        raise RuntimeError(f"Runtime target collision: {collisions[0]}")
    return sorted(mappings, key=lambda item: item.target_relative.casefold())


def changed_mappings(mappings: list[Mapping]) -> list[dict[str, object]]:
    changed: list[dict[str, object]] = []
    for mapping in mappings:
        source_hash = sha256_file(mapping.source)
        target_exists = mapping.target.is_file()
        target_hash = sha256_file(mapping.target) if target_exists else None
        if source_hash != target_hash:
            changed.append({
                "mapping": mapping,
                "source_sha256": source_hash,
                "target_sha256_before": target_hash,
                "target_existed": target_exists,
            })
    return changed


def open_service_ports() -> list[int]:
    open_ports: list[int] = []
    for port in SERVICE_PORTS:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                open_ports.append(port)
        except OSError:
            continue
    return open_ports


def write_json_exclusive(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
    if json.loads(path.read_text(encoding="utf-8")) != payload:
        raise RuntimeError(f"Receipt readback mismatch: {path}")


def plan(repo_root: Path, runtime_root: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    state = git_state(repo_root)
    mappings = build_mappings(repo_root, runtime_root)
    changed = changed_mappings(mappings)
    payload: dict[str, object] = {
        "schema": SCHEMA,
        "action": "plan",
        "generated_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "repo_root": str(repo_root),
        "runtime_root": str(runtime_root),
        "git": state,
        "tracked_mapping_count": len(mappings),
        "changed_mapping_count": len(changed),
        "open_service_ports": open_service_ports(),
        "changes": [
            {
                "source": item["mapping"].source_relative,
                "target": item["mapping"].target_relative,
                "source_sha256": item["source_sha256"],
                "target_sha256_before": item["target_sha256_before"],
                "target_existed": item["target_existed"],
            }
            for item in changed
        ],
        "authority": "digital runtime reconciliation only",
        "excluded": [
            "CGX carriers", "SQLite databases", "credentials", "queues",
            "project data", "public release", "physical actuation",
        ],
    }
    return payload, changed


def _atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.cgx-tmp-{uuid.uuid4().hex}")
    shutil.copy2(source, temporary)
    os.replace(temporary, target)


def _restore(changed: list[dict[str, object]], backup_root: Path) -> None:
    for item in reversed(changed):
        mapping: Mapping = item["mapping"]
        backup = backup_root.joinpath(*PurePosixPath(mapping.target_relative).parts)
        if item["target_existed"]:
            if not backup.is_file():
                raise RuntimeError(f"Rollback backup missing: {backup}")
            _atomic_copy(backup, mapping.target)
        elif mapping.target.exists():
            mapping.target.unlink()


def apply_transaction(
    repo_root: Path,
    runtime_root: Path,
    receipt_root: Path,
    *,
    confirmed: bool,
) -> dict[str, object]:
    if not confirmed:
        raise RuntimeError("Apply requires --confirmed")
    payload, changed = plan(repo_root, runtime_root)
    state = payload["git"]
    if state["branch"] != "main" or state["head"] != state["origin_main"] or not state["clean"]:
        raise RuntimeError("Apply requires clean main exactly aligned with origin/main")
    if payload["open_service_ports"]:
        raise RuntimeError(f"Services must be stopped before apply: {payload['open_service_ports']}")

    stamp = utc_stamp()
    backup_root = runtime_root / "Data" / "backups" / f"runtime_reconcile_{stamp}"
    receipt_path = receipt_root / f"LIGHTSPEED_LIVE_RUNTIME_RECONCILIATION_{stamp}.json"
    backup_root.mkdir(parents=True, exist_ok=False)
    for item in changed:
        mapping: Mapping = item["mapping"]
        if item["target_existed"]:
            backup = backup_root.joinpath(*PurePosixPath(mapping.target_relative).parts)
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(mapping.target, backup)
            if sha256_file(backup) != item["target_sha256_before"]:
                raise RuntimeError(f"Backup verification failed: {mapping.target_relative}")

    applied: list[dict[str, object]] = []
    try:
        for item in changed:
            mapping: Mapping = item["mapping"]
            _atomic_copy(mapping.source, mapping.target)
            installed_hash = sha256_file(mapping.target)
            if installed_hash != item["source_sha256"]:
                raise RuntimeError(f"Installed hash mismatch: {mapping.target_relative}")
            applied.append({
                "source": mapping.source_relative,
                "target": mapping.target_relative,
                "sha256": installed_hash,
                "target_existed": item["target_existed"],
            })
    except Exception:
        _restore(changed, backup_root)
        raise

    payload.update({
        "action": "apply",
        "status": "APPLIED_HASH_VERIFIED",
        "backup_root": str(backup_root),
        "receipt_path": str(receipt_path),
        "applied": applied,
        "rollback_command": (
            f'python "{Path(__file__).resolve()}" rollback --confirmed '
            f'--receipt "{receipt_path}"'
        ),
    })
    try:
        write_json_exclusive(receipt_path, payload)
    except Exception:
        _restore(changed, backup_root)
        raise
    return payload


def rollback_transaction(receipt: Path, *, confirmed: bool) -> dict[str, object]:
    if not confirmed:
        raise RuntimeError("Rollback requires --confirmed")
    source_payload = json.loads(receipt.read_text(encoding="utf-8"))
    if source_payload.get("schema") != SCHEMA or source_payload.get("status") != "APPLIED_HASH_VERIFIED":
        raise RuntimeError("Receipt is not an applied runtime reconciliation")
    if open_service_ports():
        raise RuntimeError(f"Services must be stopped before rollback: {open_service_ports()}")
    runtime_root = Path(source_payload["runtime_root"])
    backup_root = Path(source_payload["backup_root"])
    changed: list[dict[str, object]] = []
    for item in source_payload["changes"]:
        target = runtime_root.joinpath(*PurePosixPath(item["target"]).parts)
        changed.append({
            "mapping": Mapping(Path(), target, item["source"], item["target"]),
            "target_existed": item["target_existed"],
        })
    _restore(changed, backup_root)
    for item in source_payload["changes"]:
        target = runtime_root.joinpath(*PurePosixPath(item["target"]).parts)
        expected = item["target_sha256_before"]
        actual = sha256_file(target) if target.is_file() else None
        if actual != expected:
            raise RuntimeError(f"Rollback verification failed: {item['target']}")
    rollback_path = receipt.with_name(receipt.stem + "_ROLLBACK.json")
    result = {
        "schema": SCHEMA,
        "action": "rollback",
        "status": "ROLLBACK_HASH_VERIFIED",
        "generated_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "source_receipt": str(receipt),
        "runtime_root": str(runtime_root),
        "restored_count": len(changed),
        "authority": "digital runtime rollback only",
    }
    write_json_exclusive(rollback_path, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "apply", "rollback"))
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--runtime-root", type=Path, default=DEFAULT_RUNTIME_ROOT)
    parser.add_argument("--receipt-root", type=Path, default=DEFAULT_RECEIPT_ROOT)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--confirmed", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.action == "plan":
            payload, _changed = plan(args.repo_root.resolve(), args.runtime_root.resolve())
        elif args.action == "apply":
            payload = apply_transaction(
                args.repo_root.resolve(), args.runtime_root.resolve(),
                args.receipt_root.resolve(), confirmed=args.confirmed,
            )
        else:
            if args.receipt is None:
                raise RuntimeError("Rollback requires --receipt")
            payload = rollback_transaction(args.receipt.resolve(), confirmed=args.confirmed)
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    print(json.dumps({"ok": True, "result": payload}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
