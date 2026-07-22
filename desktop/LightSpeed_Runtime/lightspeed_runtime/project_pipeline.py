from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import shutil
import sys
import time
from typing import Any, Iterable

SCHEMA_VERSION = "lightspeed-project-routing-v1"
REVIEW_SCHEMA = "lightspeed-go-project-review-v1"

FLOOR_ROOTS = {
    "Architect": "Z+1_Architect",
    "Neo": "Z+2_Neo",
    "Trinity": "Z+3_Trinity",
    "Morpheus": "Z-1_Morpheus",
    "Oracle": "Z-2_Oracle",
    "Smith": "Z-3_Smith",
    "Merovingian": "Z-4_Merovingian",
    "TheConstruct": "Z0_TheConstruct",
}


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _memory_snapshot() -> tuple[int, int]:
    """Return total and available physical memory using only the standard library."""
    if os.name == "nt":
        import ctypes

        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.ullTotalPhys), int(status.ullAvailPhys)
        raise OSError("GlobalMemoryStatusEx failed")

    page_size = int(os.sysconf("SC_PAGE_SIZE"))
    total = page_size * int(os.sysconf("SC_PHYS_PAGES"))
    available = page_size * int(os.sysconf("SC_AVPHYS_PAGES"))
    return total, available


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        for attempt in range(8):
            try:
                temporary.replace(path)
                return
            except PermissionError:
                # Antivirus, indexers, Explorer and bridge readers can briefly
                # retain a Windows handle that denies the atomic replacement.
                # Keep the prior complete JSON visible and retry the commit.
                if attempt == 7:
                    raise
                time.sleep(0.05 * (attempt + 1))
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def _append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def _read_jsonl(path: Path, limit: int = 200) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    rows: list[dict[str, Any]] = []
    for line in lines[-max(1, min(limit, 2000)) :]:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _slug(value: str) -> str:
    result = "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
    while "--" in result:
        result = result.replace("--", "-")
    return result[:72] or "project"


def _windows_absolute(value: str) -> bool:
    return bool(PureWindowsPath(value).drive)


@dataclass(frozen=True)
class ProjectRoot:
    root_id: str
    path: Path
    authority: str
    writable: bool


class ProjectPipeline:
    """Merovingian-owned project inventory, evidence and GO review pipeline.

    Project source content is read-only here. The pipeline writes compact runtime
    receipts, a project registry, cleanup candidates and GO review decisions only.
    It never deletes, archives, publishes or mutates workbooks.
    """

    def __init__(self, shell_root: Path | str):
        self.shell_root = Path(shell_root).resolve()
        self.config_path = self.shell_root / "config" / "project_routing.json"
        self.config = _read_json(self.config_path)
        self.merovingian_root = self.shell_root / "Z Axis" / "Z-4_Merovingian"
        self.runtime_exports = self.merovingian_root / "data" / "runtime_exports"
        self.registry_path = self.runtime_exports / "project_registry.json"
        self.registry_state_path = self.runtime_exports / "project_registry_state.json"
        self.health_path = self.runtime_exports / "merovingian_health.json"
        self.floor_health_path = self.runtime_exports / "agent_floor_health.json"
        self.cleanup_path = self.runtime_exports / "cleanup_candidates.json"
        go_config = self.config.get("go_review") if isinstance(self.config.get("go_review"), dict) else {}
        self.review_queue_path = self._resolve_shell_path(
            str(go_config.get("queue_path") or "Z Axis/Z-4_Merovingian/data/runtime_exports/go_review_queue.jsonl")
        )
        self.review_decisions_path = self._resolve_shell_path(
            str(go_config.get("decision_path") or "Z Axis/Z-4_Merovingian/data/runtime_exports/go_review_decisions.jsonl")
        )
        self._last_refresh_monotonic = 0.0
        self._cached_registry: dict[str, Any] = {}

    def _resolve_shell_path(self, value: str) -> Path:
        if not value:
            return self.shell_root
        candidate = Path(value)
        if candidate.is_absolute() or _windows_absolute(value):
            return candidate
        return self.shell_root / candidate

    def _scan_policy(self) -> dict[str, Any]:
        value = self.config.get("scan_policy")
        return value if isinstance(value, dict) else {}

    def _resource_guard(self) -> dict[str, Any]:
        value = self.config.get("resource_guard")
        return value if isinstance(value, dict) else {}

    def _disk_health(self) -> dict[str, Any]:
        guard = self._resource_guard()
        configured = [str(item) for item in guard.get("volume_paths") or [] if str(item).strip()]
        paths = configured or [str(self.shell_root)]
        warning_percent = float(guard.get("warning_disk_percent") or 85)
        critical_percent = float(guard.get("critical_disk_percent") or 95)
        minimum_free_bytes = int(guard.get("minimum_free_bytes") or 0)
        previous = _read_json(self.health_path)
        previous_rows = {
            str(item.get("path")): item
            for item in ((previous.get("details") or {}).get("disks") or [])
            if isinstance(item, dict) and item.get("path")
        }
        previous_time = None
        try:
            previous_time = datetime.fromisoformat(str(previous.get("generated_utc")).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            pass
        sample_seconds = (
            max(1.0, (datetime.now(UTC) - previous_time).total_seconds())
            if previous_time is not None else None
        )

        rows: list[dict[str, Any]] = []
        for value in paths:
            path = Path(value)
            try:
                usage = shutil.disk_usage(path)
            except OSError as exc:
                rows.append({
                    "path": value,
                    "state": "critical",
                    "available": False,
                    "error": f"{type(exc).__name__}:{exc}",
                })
                continue
            used_percent = (usage.used / usage.total * 100.0) if usage.total else 0.0
            state = "pass"
            if used_percent >= critical_percent or (minimum_free_bytes and usage.free < minimum_free_bytes):
                state = "critical"
            elif used_percent >= warning_percent or (
                minimum_free_bytes and usage.free < minimum_free_bytes * 2
            ):
                state = "warning"
            prior = previous_rows.get(value) or {}
            growth = usage.used - int(prior.get("used_bytes") or usage.used)
            hours_to_warning = None
            if sample_seconds and growth > 0 and usage.total:
                warning_used = int(usage.total * warning_percent / 100.0)
                remaining = max(0, warning_used - usage.used)
                bytes_per_second = growth / sample_seconds
                hours_to_warning = round(remaining / bytes_per_second / 3600.0, 2) if bytes_per_second else None
            rows.append({
                "path": value,
                "volume": path.anchor or value,
                "available": True,
                "state": state,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "used_percent": round(used_percent, 2),
                "growth_bytes_since_previous": growth if sample_seconds else None,
                "sample_seconds": round(sample_seconds, 1) if sample_seconds else None,
                "estimated_hours_to_warning": hours_to_warning,
            })
        overall = "critical" if any(row.get("state") == "critical" for row in rows) else (
            "warning" if any(row.get("state") == "warning" for row in rows) else "pass"
        )
        return {
            "schema_version": "lightspeed-volume-health-v1",
            "state": overall,
            "warning_disk_percent": warning_percent,
            "critical_disk_percent": critical_percent,
            "minimum_free_bytes": minimum_free_bytes,
            "volumes": rows,
        }

    def _memory_health(self) -> dict[str, Any]:
        guard = self._resource_guard()
        warning_free_percent = float(guard.get("warning_free_memory_percent") or 15)
        critical_free_percent = float(guard.get("critical_free_memory_percent") or 8)
        minimum_free_bytes = int(guard.get("minimum_free_memory_bytes") or 2 * 1024**3)
        try:
            total_bytes, free_bytes = _memory_snapshot()
        except (OSError, ValueError) as exc:
            return {
                "available": False,
                "state": "warning",
                "error": f"{type(exc).__name__}:{exc}",
                "warning_free_percent": warning_free_percent,
                "critical_free_percent": critical_free_percent,
                "minimum_free_bytes": minimum_free_bytes,
            }

        free_percent = (free_bytes / total_bytes * 100.0) if total_bytes else 0.0
        state = "pass"
        if free_percent <= critical_free_percent or free_bytes < minimum_free_bytes:
            state = "critical"
        elif free_percent <= warning_free_percent or free_bytes < minimum_free_bytes * 2:
            state = "warning"
        return {
            "available": True,
            "state": state,
            "total_bytes": total_bytes,
            "free_bytes": free_bytes,
            "used_bytes": max(0, total_bytes - free_bytes),
            "free_percent": round(free_percent, 2),
            "used_percent": round(100.0 - free_percent, 2),
            "warning_free_percent": warning_free_percent,
            "critical_free_percent": critical_free_percent,
            "minimum_free_bytes": minimum_free_bytes,
        }

    def _resource_health(self) -> dict[str, Any]:
        disks = self._disk_health()
        memory = self._memory_health()
        states = {str(disks.get("state")), str(memory.get("state"))}
        state = "critical" if "critical" in states else ("warning" if "warning" in states else "pass")
        return {
            "schema_version": "lightspeed-resource-health-v2",
            "state": state,
            "work_intake": "hold_heavy" if state == "critical" else (
                "bounded_only" if state == "warning" else "normal"
            ),
            "bounded_work_allowed": state != "critical",
            "heavy_work_allowed": state == "pass",
            "warning_disk_percent": disks["warning_disk_percent"],
            "critical_disk_percent": disks["critical_disk_percent"],
            "minimum_free_bytes": disks["minimum_free_bytes"],
            "volumes": disks["volumes"],
            "memory": memory,
        }

    def agent_floor_health(
        self,
        *,
        services: dict[str, bool],
        event_bus_enabled: bool,
    ) -> dict[str, Any]:
        neo_queue = self.shell_root / "Z Axis" / "Z+2_Neo" / "data" / "actions" / "ls_go_command_queue.jsonl"
        for queue_path in (neo_queue, self.review_queue_path, self.review_decisions_path):
            queue_path.parent.mkdir(parents=True, exist_ok=True)
            queue_path.touch(exist_ok=True)
        shared_services = all(bool(services.get(name)) for name in ("database", "event_bus", "storage"))
        floors: list[dict[str, Any]] = []
        for floor, directory in FLOOR_ROOTS.items():
            root = self.shell_root / "Z Axis" / directory
            markers = [root / "_FLOOR_MANIFEST.json", root / "__init__.py", root / "Z Direct"]
            missing = [str(path) for path in markers if not path.exists()]
            if not shared_services:
                missing.append("shared_services")
            floors.append({
                "floor": floor,
                "root": str(root),
                "state": "operational" if not missing else "degraded",
                "execution_model": "asynchronous_shared_queue",
                "markers_present": len(markers) - len([item for item in markers if not item.exists()]),
                "markers_required": len(markers),
                "missing": missing,
            })
        transport = {
            "event_bus_enabled": event_bus_enabled,
            "neo_queue_path": str(neo_queue),
            "neo_queue_writable": neo_queue.is_file() and os.access(neo_queue, os.W_OK),
            "go_review_queue_path": str(self.review_queue_path),
            "go_review_queue_available": self.review_queue_path.is_file(),
            "go_decision_path": str(self.review_decisions_path),
            "go_decision_available": self.review_decisions_path.is_file(),
            "coordination_mode": "independent_observers_shared_state",
        }
        operational_count = sum(item["state"] == "operational" for item in floors)
        aligned = (
            operational_count == len(FLOOR_ROOTS)
            and event_bus_enabled
            and transport["neo_queue_writable"]
            and transport["go_review_queue_available"]
            and transport["go_decision_available"]
        )
        return {
            "schema_version": "lightspeed-agent-floor-health-v1",
            "generated_utc": utc_now_iso(),
            "state": "operational" if aligned else "degraded",
            "operational_count": operational_count,
            "floor_count": len(FLOOR_ROOTS),
            "floors": floors,
            "transport": transport,
        }

    def _ignored_dirs(self) -> set[str]:
        return {str(item) for item in (self._scan_policy().get("ignored_directories") or [])}

    def _ignored_files(self) -> set[str]:
        return {str(item) for item in (self._scan_policy().get("ignored_files") or [])}

    def project_roots(self) -> list[ProjectRoot]:
        rows: list[ProjectRoot] = []
        for item in self.config.get("project_roots") or []:
            if not isinstance(item, dict):
                continue
            value = item.get("path")
            if not isinstance(value, str) or not value.strip():
                continue
            rows.append(
                ProjectRoot(
                    root_id=str(item.get("root_id") or _slug(value)),
                    path=self._resolve_shell_path(value),
                    authority=str(item.get("authority") or "reference"),
                    writable=bool(item.get("writable", False)),
                )
            )

        external = self.config.get("external_project_roots") or {}
        if isinstance(external, dict):
            variable = str(external.get("environment_variable") or "LIGHTSPEED_PROJECT_ROOTS")
            separator = str(external.get("separator") or ";")
            for index, value in enumerate(os.environ.get(variable, "").split(separator), start=1):
                value = value.strip()
                if value:
                    rows.append(
                        ProjectRoot(
                            root_id=f"external-{index}",
                            path=Path(value),
                            authority=str(external.get("authority") or "external_reference"),
                            writable=bool(external.get("writable", False)),
                        )
                    )

        unique: list[ProjectRoot] = []
        seen: set[str] = set()
        for row in rows:
            key = os.path.normcase(os.path.abspath(str(row.path)))
            if key not in seen:
                seen.add(key)
                unique.append(row)
        return unique

    def _scan_project(self, root: ProjectRoot, path: Path, budget: list[int]) -> dict[str, Any]:
        ignored_dirs = self._ignored_dirs()
        ignored_files = self._ignored_files()
        per_project_limit = max(1, int(self._scan_policy().get("max_files_per_project") or 50_000))
        file_count = 0
        significant_count = 0
        total_bytes = 0
        latest_mtime = 0.0
        truncated = False
        fingerprint = hashlib.sha256()
        placeholder_names = {
            ".gitkeep", "notes.md", "checklist.md",
            "requirements.txt", "config.json", "config.yaml",
        }

        for current, directories, filenames in os.walk(path):
            directories[:] = [name for name in directories if name not in ignored_dirs]
            current_path = Path(current)
            for filename in sorted(filenames):
                if budget[0] <= 0 or file_count >= per_project_limit:
                    truncated = True
                    directories[:] = []
                    break
                if filename in ignored_files:
                    continue
                target = current_path / filename
                try:
                    stat = target.stat()
                except OSError:
                    continue
                budget[0] -= 1
                file_count += 1
                total_bytes += int(stat.st_size)
                latest_mtime = max(latest_mtime, float(stat.st_mtime))
                relative = target.relative_to(path).as_posix()
                fingerprint.update(relative.encode("utf-8", errors="replace"))
                fingerprint.update(str(int(stat.st_size)).encode("ascii"))
                fingerprint.update(str(int(stat.st_mtime_ns)).encode("ascii"))
                if filename.lower() not in placeholder_names or int(stat.st_size) > 256:
                    significant_count += 1
            if truncated:
                break

        metadata = _read_json(path / "project.json")
        project_id = f"{_slug(path.name)}-{hashlib.sha1(str(path).encode('utf-8')).hexdigest()[:8]}"
        if file_count == 0:
            condition = "empty"
        elif significant_count == 0:
            condition = "scaffold_only"
        else:
            condition = "active"
        return {
            "project_id": project_id,
            "name": path.name,
            "path": str(path),
            "root_id": root.root_id,
            "authority": root.authority,
            "writable": root.writable,
            "condition": condition,
            "scan_truncated": truncated,
            "file_count": file_count,
            "significant_file_count": significant_count,
            "size_bytes": total_bytes,
            "latest_modified_utc": (
                datetime.fromtimestamp(latest_mtime, UTC).isoformat(timespec="seconds")
                if latest_mtime else None
            ),
            "fingerprint": fingerprint.hexdigest(),
            "metadata": {
                "type": metadata.get("type"),
                "status": metadata.get("status"),
                "description": metadata.get("description"),
                "version": metadata.get("version"),
            },
        }

    def scan_projects(self) -> dict[str, Any]:
        total_limit = max(1000, int(self._resource_guard().get("max_project_scan_files") or 200_000))
        budget = [total_limit]
        projects: list[dict[str, Any]] = []
        roots: list[dict[str, Any]] = []
        global_truncated = False
        for root in self.project_roots():
            root_exists = root.path.is_dir()
            roots.append({
                "root_id": root.root_id,
                "path": str(root.path),
                "authority": root.authority,
                "writable": root.writable,
                "exists": root_exists,
            })
            if not root_exists:
                continue
            try:
                children = [item for item in root.path.iterdir() if item.is_dir() and not item.name.startswith(".")]
            except OSError:
                continue
            for child in sorted(children, key=lambda item: item.name.lower()):
                if budget[0] <= 0:
                    global_truncated = True
                    break
                projects.append(self._scan_project(root, child, budget))
            if budget[0] <= 0:
                global_truncated = True
                break

        name_groups: dict[str, list[dict[str, Any]]] = {}
        for project in projects:
            name_groups.setdefault(str(project["name"]).lower(), []).append(project)
        duplicate_names = [
            {
                "name": group[0]["name"],
                "project_ids": [item["project_id"] for item in group],
                "paths": [item["path"] for item in group],
                "authorities": [item["authority"] for item in group],
            }
            for group in name_groups.values() if len(group) > 1
        ]

        return {
            "schema_version": SCHEMA_VERSION,
            "generated_utc": utc_now_iso(),
            "shell_root": str(self.shell_root),
            "roots": roots,
            "projects": projects,
            "summary": {
                "root_count": len(roots),
                "available_root_count": sum(1 for item in roots if item["exists"]),
                "project_count": len(projects),
                "active_count": sum(1 for item in projects if item["condition"] == "active"),
                "empty_count": sum(1 for item in projects if item["condition"] == "empty"),
                "scaffold_only_count": sum(1 for item in projects if item["condition"] == "scaffold_only"),
                "duplicate_name_group_count": len(duplicate_names),
                "truncated_project_count": sum(1 for item in projects if item["scan_truncated"]),
                "scan_truncated": global_truncated,
                "scanned_file_count": total_limit - budget[0],
                "scan_file_limit": total_limit,
                "total_size_bytes": sum(int(item["size_bytes"]) for item in projects),
            },
            "duplicate_names": duplicate_names,
        }

    def _archive_candidates(self, registry: dict[str, Any]) -> list[dict[str, Any]]:
        cleanup_config = self.config.get("cleanup_policy") or {}
        never_patterns = [str(item) for item in cleanup_config.get("never_delete_patterns") or []]
        max_hash_bytes = int(self._scan_policy().get("max_hash_bytes") or 1_073_741_824)
        max_archives = max(10, int(self._resource_guard().get("max_archive_inventory") or 2000))
        max_hashes = max(1, int(self._resource_guard().get("max_archive_hashes") or 100))
        ignored_dirs = self._ignored_dirs()
        archive_suffixes = {".zip", ".7z", ".tar", ".gz", ".bz2", ".rar"}
        archives: list[dict[str, Any]] = []
        hash_budget = max_hashes
        truncated = False

        for project in registry.get("projects") or []:
            project_path = Path(str(project.get("path") or ""))
            if not project_path.is_dir():
                continue
            for current, directories, filenames in os.walk(project_path):
                directories[:] = [name for name in directories if name not in ignored_dirs]
                for filename in sorted(filenames):
                    if len(archives) >= max_archives:
                        truncated = True
                        break
                    target = Path(current) / filename
                    if target.suffix.lower() not in archive_suffixes:
                        continue
                    try:
                        stat = target.stat()
                    except OSError:
                        continue
                    checksum = None
                    hash_state = "not_hashed_budget_or_size"
                    if hash_budget > 0 and int(stat.st_size) <= max_hash_bytes:
                        digest = hashlib.sha256()
                        try:
                            with target.open("rb") as stream:
                                for block in iter(lambda: stream.read(1024 * 1024), b""):
                                    digest.update(block)
                            checksum = digest.hexdigest()
                            hash_state = "hashed"
                            hash_budget -= 1
                        except OSError:
                            hash_state = "unreadable"
                    archives.append({
                        "candidate_class": "archive_inventory",
                        "path": str(target),
                        "project_id": project.get("project_id"),
                        "size_bytes": int(stat.st_size),
                        "sha256": checksum,
                        "hash_state": hash_state,
                        "protected_by_pattern": any(fnmatch.fnmatch(target.name, pattern) for pattern in never_patterns),
                        "action": "retain_pending_classification",
                    })
                if truncated:
                    break
            if truncated:
                break

        by_checksum: dict[str, list[dict[str, Any]]] = {}
        for archive in archives:
            checksum = archive.get("sha256")
            if checksum:
                by_checksum.setdefault(str(checksum), []).append(archive)
        duplicates = [
            {
                "candidate_class": "duplicate_archive_checksum",
                "sha256": checksum,
                "paths": [row["path"] for row in rows],
                "sizes": [row["size_bytes"] for row in rows],
                "action": "review_canonical_retention_before_quarantine",
            }
            for checksum, rows in by_checksum.items() if len(rows) > 1
        ]
        if truncated:
            archives.append({
                "candidate_class": "archive_inventory_limit",
                "limit": max_archives,
                "action": "continue_in_next_bounded_pass",
            })
        return [*archives, *duplicates]

    def scan_cleanup_candidates(self, registry: dict[str, Any]) -> dict[str, Any]:
        candidates: list[dict[str, Any]] = []
        generated_roots = [
            self.runtime_exports,
            self.merovingian_root / "data" / "logs",
            self.merovingian_root / "data" / "cache",
            self.merovingian_root / "data" / "temp",
        ]
        for root in generated_roots:
            if not root.is_dir():
                continue
            for target in root.rglob("*"):
                if target in {self.registry_path, self.health_path, self.cleanup_path, self.registry_state_path}:
                    continue
                try:
                    if target.is_file() and target.stat().st_size == 0:
                        candidates.append({
                            "candidate_class": "empty_generated_file",
                            "path": str(target),
                            "size_bytes": 0,
                            "action": "quarantine_only_after_reference_scan_and_approval",
                        })
                    elif target.is_dir() and not any(target.iterdir()):
                        candidates.append({
                            "candidate_class": "empty_generated_directory",
                            "path": str(target),
                            "action": "quarantine_only_after_reference_scan_and_approval",
                        })
                except OSError:
                    continue

        for project in registry.get("projects") or []:
            if project.get("condition") in {"empty", "scaffold_only"}:
                candidates.append({
                    "candidate_class": f"project_{project.get('condition')}",
                    "project_id": project.get("project_id"),
                    "path": project.get("path"),
                    "file_count": project.get("file_count"),
                    "size_bytes": project.get("size_bytes"),
                    "action": "review_merge_or_retire; no automatic deletion",
                })
        candidates.extend(self._archive_candidates(registry))
        return {
            "schema_version": "lightspeed-cleanup-evidence-v1",
            "generated_utc": utc_now_iso(),
            "automatic_deletion": False,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "required_proof": (self.config.get("cleanup_policy") or {}).get("required_proof") or [],
        }

    def resolve_drive_receipt_root(self) -> tuple[Path, str]:
        config = self.config.get("drive_writeback") or {}
        relative = Path(str(config.get("relative_receipt_path") or "LightSpeed/Project Receipts"))
        variables = [str(item) for item in config.get("root_environment_variables") or []]
        candidates: list[tuple[Path, str]] = []
        for variable in variables:
            value = os.environ.get(variable)
            if value:
                candidates.append((Path(value).expanduser() / relative, f"environment:{variable}"))

        home = Path.home()
        candidates.extend([
            (home / "My Drive" / relative, "drive_for_desktop_detected"),
            (home / "Google Drive" / "My Drive" / relative, "drive_for_desktop_detected"),
        ])
        if os.name == "nt":
            candidates.extend((Path(f"{drive}:/My Drive") / relative, "drive_for_desktop_detected") for drive in "GHI")

        for candidate, mode in candidates:
            try:
                if candidate.parent.is_dir():
                    candidate.mkdir(parents=True, exist_ok=True)
                    return candidate, mode
            except OSError:
                continue

        fallback = self._resolve_shell_path(str(
            config.get("local_fallback_path")
            or "Z Axis/Z-4_Merovingian/data/runtime_exports/drive_outbox"
        ))
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback, "local_outbox_pending_drive_sync"

    def _queue_review_packet(
        self,
        *,
        title: str,
        summary: str,
        project_ids: list[str],
        artifact_paths: list[str],
        event_type: str,
    ) -> dict[str, Any]:
        created = utc_now_iso()
        seed = f"{created}|{event_type}|{'|'.join(project_ids)}|{'|'.join(artifact_paths)}"
        review_id = f"LSGO-REVIEW-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16].upper()}"
        packet = {
            "schema_version": REVIEW_SCHEMA,
            "review_id": review_id,
            "created_utc": created,
            "source": "LightSpeed Desktop / Merovingian",
            "target": "LS GO",
            "oversight_floor": "Achilles",
            "routing_floor": "Neo",
            "owner": "Nathaniel Bouwer",
            "event_type": event_type,
            "title": title,
            "summary": summary,
            "project_ids": project_ids,
            "artifact_paths": artifact_paths,
            "state": "pending_review",
            "allowed_decisions": ["approve", "hold", "reject"],
            "proof_required": True,
            "public_safe": False,
        }
        _append_jsonl(self.review_queue_path, packet)
        drive_root, drive_mode = self.resolve_drive_receipt_root()
        drive_path = drive_root / f"{review_id}.json"
        _write_json(drive_path, {**packet, "drive_writeback_mode": drive_mode})
        return {**packet, "drive_receipt_path": str(drive_path), "drive_writeback_mode": drive_mode}

    def _project_changes(self, previous: dict[str, Any], current: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        previous_map = {
            str(item.get("project_id")): item for item in previous.get("projects") or []
            if isinstance(item, dict) and item.get("project_id")
        }
        current_map = {
            str(item.get("project_id")): item for item in current.get("projects") or []
            if isinstance(item, dict) and item.get("project_id")
        }
        return {
            "added": [item for key, item in current_map.items() if key not in previous_map],
            "removed": [item for key, item in previous_map.items() if key not in current_map],
            "changed": [
                item for key, item in current_map.items()
                if key in previous_map and item.get("fingerprint") != previous_map[key].get("fingerprint")
            ],
        }

    def essential_health(self, registry: dict[str, Any]) -> dict[str, Any]:
        # ``core`` is the Merovingian package, not a package at the Desktop
        # shell root.  Add its parent explicitly so an installed runtime works
        # the same way as a repository checkout and CI environment.
        if str(self.merovingian_root) not in sys.path:
            sys.path.insert(0, str(self.merovingian_root))
        service_states = {"database": False, "event_bus": False, "storage": False}
        details: dict[str, Any] = {}
        errors: list[str] = []
        event_bus_enabled = False
        try:
            from core.services import initialize_services  # type: ignore

            services = initialize_services()
            db = services.get("database")
            event_bus = services.get("event_bus")
            storage = services.get("storage")
            service_states = {
                "database": db is not None,
                "event_bus": event_bus is not None,
                "storage": storage is not None,
            }
            if db is not None:
                try:
                    details["database_path"] = str(getattr(db, "db_path", ""))
                    details["database_table_count"] = len(db.get_all_tables())
                except Exception as exc:
                    errors.append(f"database_probe:{type(exc).__name__}")
            if event_bus is not None:
                try:
                    details["event_bus"] = event_bus.get_stats()
                    event_bus_enabled = bool(details["event_bus"].get("enabled"))
                except Exception as exc:
                    errors.append(f"event_bus_probe:{type(exc).__name__}")
            if storage is not None:
                try:
                    details["storage_root"] = str(storage.storage_root)
                    details["storage_stats"] = storage.get_storage_stats()
                except Exception as exc:
                    errors.append(f"storage_probe:{type(exc).__name__}")
        except Exception as exc:
            errors.append(f"essential_services:{type(exc).__name__}:{exc}")

        resources = self._resource_health()
        details["resource_guard"] = resources
        details["disks"] = resources["volumes"]
        if resources["volumes"]:
            details["disk"] = resources["volumes"][0]

        floor_health = self.agent_floor_health(
            services=service_states,
            event_bus_enabled=event_bus_enabled,
        )
        details["agent_floors"] = floor_health

        drive_root, drive_mode = self.resolve_drive_receipt_root()
        details["drive_writeback"] = {"path": str(drive_root), "mode": drive_mode}
        return {
            "schema_version": "lightspeed-merovingian-health-v1",
            "generated_utc": utc_now_iso(),
            "status": "pass" if (
                all(service_states.values())
                and resources["state"] != "critical"
                and floor_health["state"] == "operational"
            ) else "degraded",
            "services": service_states,
            "details": details,
            "project_summary": registry.get("summary") or {},
            "errors": errors,
            "web_frontend_in_scope": False,
        }

    def refresh(self, *, force: bool = False, queue_changes: bool = True) -> dict[str, Any]:
        refresh_seconds = int(self._scan_policy().get("registry_refresh_seconds") or 60)
        if not force and self._cached_registry and time.monotonic() - self._last_refresh_monotonic < refresh_seconds:
            return self._cached_registry

        previous = _read_json(self.registry_state_path)
        registry = self.scan_projects()
        cleanup = self.scan_cleanup_candidates(registry)
        health = self.essential_health(registry)
        _write_json(self.registry_path, registry)
        _write_json(self.cleanup_path, cleanup)
        _write_json(self.health_path, health)
        _write_json(self.floor_health_path, (health.get("details") or {}).get("agent_floors") or {})

        changes = self._project_changes(previous, registry) if previous else {"added": [], "removed": [], "changed": []}
        review_packet = None
        if queue_changes and previous and any(changes.values()):
            affected = [*changes["added"], *changes["removed"], *changes["changed"]]
            review_packet = self._queue_review_packet(
                title="Review LightSpeed project registry change",
                summary=(
                    f"Project registry changed: {len(changes['added'])} added, "
                    f"{len(changes['changed'])} modified, {len(changes['removed'])} removed."
                ),
                project_ids=[str(item.get("project_id")) for item in affected if item.get("project_id")],
                artifact_paths=[
                    str(self.registry_path),
                    str(self.cleanup_path),
                    str(self.health_path),
                    str(self.floor_health_path),
                ],
                event_type="project_registry_change",
            )

        _write_json(self.registry_state_path, {
            "schema_version": SCHEMA_VERSION,
            "generated_utc": registry["generated_utc"],
            "projects": registry.get("projects") or [],
            "last_review_id": review_packet.get("review_id") if review_packet else previous.get("last_review_id"),
        })
        registry.update({
            "health": health,
            "cleanup_summary": {
                "candidate_count": cleanup.get("candidate_count", 0),
                "automatic_deletion": False,
            },
            "changes": {key: [item.get("project_id") for item in value] for key, value in changes.items()},
            "review_packet": review_packet,
        })
        self._cached_registry = registry
        self._last_refresh_monotonic = time.monotonic()
        return registry

    def queue_project_work_receipt(
        self,
        *,
        project_id: str,
        summary: str,
        artifact_paths: Iterable[str] = (),
    ) -> dict[str, Any]:
        return self._queue_review_packet(
            title=f"Review project work: {project_id}",
            summary=summary,
            project_ids=[project_id],
            artifact_paths=[str(item) for item in artifact_paths],
            event_type="project_work_receipt",
        )

    def list_reviews(self, limit: int = 100) -> list[dict[str, Any]]:
        decisions = {
            str(item.get("review_id")): item for item in _read_jsonl(self.review_decisions_path, limit=2000)
            if item.get("review_id")
        }
        rows = list(reversed(_read_jsonl(self.review_queue_path, limit=limit)))
        result: list[dict[str, Any]] = []
        for row in rows:
            output = row.copy()
            decision = decisions.get(str(row.get("review_id")))
            if decision:
                output["state"] = str(decision.get("decision") or "reviewed")
                output["decision"] = decision
            result.append(output)
        return result

    def decide_review(self, review_id: str, decision: str, note: str = "") -> dict[str, Any]:
        allowed = set((self.config.get("go_review") or {}).get("allowed_decisions") or [])
        if decision not in allowed:
            raise ValueError(f"Unsupported review decision: {decision}")
        review = next((item for item in self.list_reviews(limit=1000) if item.get("review_id") == review_id), None)
        if review is None:
            raise KeyError(review_id)
        receipt = {
            "schema_version": "lightspeed-go-review-decision-v1",
            "review_id": review_id,
            "decision": decision,
            "note": " ".join(note.split())[:1000],
            "decided_utc": utc_now_iso(),
            "decided_by": "Nathaniel Bouwer / Achilles GO gate",
            "applies_external_write": False,
        }
        _append_jsonl(self.review_decisions_path, receipt)
        drive_root, drive_mode = self.resolve_drive_receipt_root()
        _write_json(drive_root / f"{review_id}_{decision}.json", {**receipt, "drive_writeback_mode": drive_mode})
        return receipt
