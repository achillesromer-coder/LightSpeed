from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from lightspeed_runtime.contracts import utc_now_iso
from lightspeed_runtime.storage_paths import (
    active_generated_root,
    ingestion_root,
    legacy_operations_w6_generated_root,
    legacy_runtime_bundle_root,
    legacy_w6_generated_root,
    legacy_generated_roots,
    logs_root,
    publish_root,
    quality_root,
    reports_root,
    runtime_exports_root,
    zoning_root,
)

LEGACY_RUNTIME_DIRNAME = "canonical_runtime"
RUNTIME_PACKAGE_DIRNAME = "lightspeed_runtime"


def legacy_runtime_root(root: Path) -> Path:
    canonical = legacy_runtime_bundle_root(root)
    root_legacy = Path(root) / LEGACY_RUNTIME_DIRNAME
    if canonical.exists():
        try:
            if any(canonical.iterdir()):
                return canonical
        except Exception:
            return canonical
    if root_legacy.exists():
        return root_legacy
    return canonical


def legacy_runtime_package_root(root: Path) -> Path:
    return legacy_runtime_root(root) / RUNTIME_PACKAGE_DIRNAME


def live_runtime_package_root(root: Path) -> Path:
    return Path(root) / RUNTIME_PACKAGE_DIRNAME


def legacy_runtime_exports_root(root: Path) -> Path:
    return legacy_runtime_root(root) / "exports"


def default_legacy_audit_path(root: Path) -> Path:
    return runtime_exports_root(root) / "legacy_runtime_audit.json"


def default_cleanup_report_path(root: Path) -> Path:
    return runtime_exports_root(root) / "cleanup_report.json"


def default_legacy_diff_path(root: Path) -> Path:
    return runtime_exports_root(root) / "legacy_runtime_diff.json"


def default_cleanup_candidates_path(root: Path) -> Path:
    return runtime_exports_root(root) / "cleanup_candidates.json"


def default_legacy_sync_path(root: Path) -> Path:
    return runtime_exports_root(root) / "legacy_runtime_sync.json"


def default_legacy_export_cleanup_path(root: Path) -> Path:
    return runtime_exports_root(root) / "legacy_export_cleanup.json"


def default_generated_layout_audit_path(root: Path) -> Path:
    return reports_root(root) / "generated_layout_audit.json"


def default_generated_shell_cleanup_path(root: Path) -> Path:
    return runtime_exports_root(root) / "generated_shell_cleanup.json"


def default_dataindex_audit_path(root: Path) -> Path:
    return runtime_exports_root(root) / "dataindex_audit.json"


def default_dataindex_reduction_path(root: Path) -> Path:
    return reports_root(root) / "dataindex_reduction.json"


DATAINDEX_SUPERSEDED_FILES = {
    "05_FINALIZATION_BACKLOG_50.md": "06_FINALIZATION_BACKLOG_50.md",
    "06_ROOT_CLASSIFICATION_MAP.md": "07_ROOT_CLASSIFICATION_MAP.md",
}

DATAINDEX_GENERATED_FILES = {
    "00_DIRECTORY_TREE.txt",
    "architecture_graph.json",
    "architecture_graph_summary.md",
    "depmap.json",
    "depmap_latest.json",
    "z_axis_index.json",
}


def _inventory_generated_root(root_path: Path, *, sample_limit: int = 3) -> dict:
    root_path = Path(root_path)
    if not root_path.exists():
        return {
            "root": str(root_path),
            "present": False,
            "tool_count": 0,
            "tools": {},
        }

    tools: dict[str, dict] = {}
    for tool_dir in sorted(path for path in root_path.iterdir() if path.is_dir()):
        entries = sorted(tool_dir.iterdir(), key=lambda item: item.name)
        tools[tool_dir.name] = {
            "entry_count": len(entries),
            "sample_entries": [item.name for item in entries[:sample_limit]],
        }

    return {
        "root": str(root_path),
        "present": True,
        "tool_count": len(tools),
        "tools": tools,
    }


def build_generated_layout_audit(root: Path) -> dict:
    root = Path(root)
    canonical_root = ingestion_root(root)
    canonical_generated_root = active_generated_root(root)
    legacy_operations_root = next(
        (path for path in legacy_generated_roots(root) if "operations" in str(path)),
        legacy_operations_w6_generated_root(root),
    )

    canonical = _inventory_generated_root(canonical_root)
    legacy = _inventory_generated_root(legacy_operations_root)

    canonical_tools = canonical.get("tools", {}) or {}
    legacy_tools = legacy.get("tools", {}) or {}
    tool_names = sorted(set(canonical_tools) | set(legacy_tools))
    comparisons: list[dict] = []
    legacy_only_tools: list[str] = []

    for tool_name in tool_names:
        canonical_count = int(((canonical_tools.get(tool_name) or {}).get("entry_count")) or 0)
        legacy_count = int(((legacy_tools.get(tool_name) or {}).get("entry_count")) or 0)
        status = "canonical_only"
        if canonical_count and legacy_count:
            if canonical_count == legacy_count:
                status = "parallel_tree"
            elif legacy_count < canonical_count:
                status = "legacy_partial_mirror"
            else:
                status = "legacy_superset"
        elif legacy_count:
            status = "legacy_only"
            legacy_only_tools.append(tool_name)

        comparisons.append(
            {
                "tool": tool_name,
                "canonical_entries": canonical_count,
                "legacy_operations_entries": legacy_count,
                "status": status,
            }
        )

    recommendations = [
        "Treat Z Axis smart-floor data roots as canonical: Oracle for ingestion, TheConstruct for labs, Architect for publish, Smith for operations, and Merovingian for reports/logs/quality.",
            "Treat data/generated as a flat legacy compatibility shell only when it exists; runtime layout does not create it by default.",
    ]
    if legacy_only_tools:
        recommendations.append(
            f"Legacy-only operations tools remain and need manual review before deletion: {', '.join(sorted(legacy_only_tools))}."
        )
    else:
        recommendations.append("No legacy-only tool roots were found in operations/w6/data; it is a better deletion/archive candidate once manual review is complete.")

    return {
        "canonical_generated_root": str(canonical_generated_root),
        "canonical_ingestion_root": str(canonical_root),
        "legacy_operations_generated_root": str(legacy_operations_root),
        "canonical": canonical,
        "legacy_operations": legacy,
        "comparisons": comparisons,
        "legacy_only_tools": sorted(legacy_only_tools),
        "legacy_operations_can_be_declassified": legacy.get("present", False) and not legacy_only_tools,
        "recommendations": recommendations,
    }


def write_generated_layout_audit(root: Path, output_path: Path | None = None) -> dict:
    root = Path(root)
    if output_path is None:
        output_path = default_generated_layout_audit_path(root)
    payload = build_generated_layout_audit(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build_dataindex_audit(root: Path) -> dict:
    root = Path(root)
    dataindex_root = root / "dataindex"
    docs_to_scan = [
        dataindex_root / "00_DIRECTORY_MAP.md",
        dataindex_root / "00_DIRECTORY_TREE.txt",
        dataindex_root / "01_AI_LOGS_DOCUMENT_TABLE.md",
        dataindex_root / "02_MASTER_BUILD_SPEC_SHEET.md",
        dataindex_root / "03_Z_AXIS_FILESYSTEM_MAP.md",
        dataindex_root / "04_Z_AXIS_CANONICAL_MAP.md",
        dataindex_root / "05_FINALIZATION_BACKLOG_50.md",
        dataindex_root / "06_FINALIZATION_BACKLOG_50.md",
        dataindex_root / "06_ROOT_CLASSIFICATION_MAP.md",
        dataindex_root / "07_ROOT_CLASSIFICATION_MAP.md",
        dataindex_root / "08_SMART_FLOOR_ASSIMILATION.md",
        root / "README.md",
    ]
    legacy_markers = {
        "w6": ("w6",),
        "canonical_runtime": ("canonical_runtime",),
        "data_generated": ("data/generated",),
        "zplus4_firstrun": ("Z+4_FirstRun", "Z+4 FirstRun"),
        "operations_w6": ("operations/w6",),
        "legacy_runtime_bundle": ("legacy_runtime_bundle",),
    }
    report_files: list[dict] = []
    totals = {key: 0 for key in legacy_markers}
    for path in docs_to_scan:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        hit_counts = {}
        for key, needles in legacy_markers.items():
            count = sum(text.count(needle) for needle in needles)
            if count:
                hit_counts[key] = count
                totals[key] += count
        if hit_counts:
            report_files.append(
                {
                    "path": str(path),
                    "hit_counts": hit_counts,
                }
            )
    return {
        "generated_at": str(utc_now_iso()),
        "dataindex_root": str(dataindex_root),
        "file_count": len(docs_to_scan),
        "files_with_hits": report_files,
        "totals": totals,
        "recommendations": [
            "Update dataindex maps so they describe current root ownership without implying deletes that already happened.",
            "Remove obsolete references to `data/generated`, `operations/w6`, and `canonical_runtime` from docs after confirmation.",
            "Keep `Z+4_FirstRun` and legacy bundle language as reference-only until all documentation consumers are aligned.",
        ],
    }


def write_dataindex_audit(root: Path, output_path: Path | None = None) -> dict:
    root = Path(root)
    if output_path is None:
        output_path = default_dataindex_audit_path(root)
    payload = build_dataindex_audit(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build_dataindex_reduction_plan(root: Path) -> dict:
    root = Path(root)
    dataindex_root = root / "dataindex"
    archive_root = reports_root(root) / "dataindex_archive"
    generated_root = reports_root(root) / "dataindex_generated"
    moves: list[dict] = []
    for name, superseded_by in DATAINDEX_SUPERSEDED_FILES.items():
        source = dataindex_root / name
        moves.append(
            {
                "source": str(source),
                "destination": str(archive_root / name),
                "category": "superseded_operator_doc",
                "superseded_by": str(dataindex_root / superseded_by),
                "present": source.exists(),
            }
        )
    for name in sorted(DATAINDEX_GENERATED_FILES):
        source = dataindex_root / name
        moves.append(
            {
                "source": str(source),
                "destination": str(generated_root / name),
                "category": "generated_index_artifact",
                "superseded_by": "",
                "present": source.exists(),
            }
        )
    return {
        "generated_at": utc_now_iso(),
        "dataindex_root": str(dataindex_root),
        "archive_root": str(archive_root),
        "generated_root": str(generated_root),
        "planned_move_count": sum(1 for item in moves if item["present"]),
        "moves": moves,
        "policy": [
            "Keep dataindex as human-facing operator doctrine and canonical maps.",
            "Move superseded docs into Merovingian dataindex_archive.",
            "Move generated tree/graph/dependency indexes into Merovingian dataindex_generated.",
            "Do not delete moved files until follow-up reference checks stay green.",
        ],
    }


def reduce_dataindex_duplication(root: Path, output_path: Path | None = None, *, apply: bool = False) -> dict:
    root = Path(root).resolve()
    report_path = output_path or default_dataindex_reduction_path(root)
    plan = build_dataindex_reduction_plan(root)
    moved: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []
    if apply:
        for item in plan["moves"]:
            source = Path(item["source"])
            destination = Path(item["destination"])
            try:
                resolved_source = source.resolve()
                resolved_destination_parent = destination.parent.resolve() if destination.parent.exists() else destination.parent
                if root not in resolved_source.parents or root not in resolved_destination_parent.parents:
                    skipped.append({**item, "reason": "outside_workspace"})
                    continue
                if not source.exists():
                    skipped.append({**item, "reason": "source_missing"})
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists():
                    if source.read_bytes() == destination.read_bytes():
                        source.unlink()
                        moved.append({**item, "mode": "deduplicated_existing_destination"})
                    else:
                        skipped.append({**item, "reason": "destination_exists_with_different_content"})
                    continue
                shutil.move(str(source), str(destination))
                moved.append({**item, "mode": "moved"})
            except Exception as exc:
                failed.append({**item, "reason": str(exc)})
    payload = {
        **plan,
        "applied": bool(apply),
        "moved_count": len(moved),
        "skipped_count": len(skipped),
        "failed_count": len(failed),
        "moved": moved,
        "skipped": skipped,
        "failed": failed,
        "report_path": str(report_path),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _generated_shell_segment_map(root: Path) -> dict[Path, Path]:
    root = Path(root)
    generated_root = active_generated_root(root)
    return {
        generated_root / "ingestion": ingestion_root(root),
        generated_root / "labs": zoning_root(root).parent,
        generated_root / "publish": publish_root(root),
        generated_root / "reports": reports_root(root),
        generated_root / "logs": logs_root(root),
        generated_root / "runtime_exports": runtime_exports_root(root),
        generated_root / "quality": quality_root(root),
    }


def _merge_jsonl_into_target(source: Path, destination: Path) -> tuple[int, int]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    existing_lines: set[str] = set()
    if destination.exists():
        with destination.open("r", encoding="utf-8", errors="replace") as handle:
            for raw in handle:
                raw = raw.rstrip("\n")
                if raw:
                    existing_lines.add(raw)

    merged_count = 0
    total_source_lines = 0
    with source.open("r", encoding="utf-8", errors="replace") as source_handle:
        new_lines: list[str] = []
        for raw in source_handle:
            raw = raw.rstrip("\n")
            if not raw:
                continue
            total_source_lines += 1
            if raw not in existing_lines:
                existing_lines.add(raw)
                new_lines.append(raw)
        if new_lines:
            with destination.open("a", encoding="utf-8") as target_handle:
                for line in new_lines:
                    target_handle.write(line + "\n")
            merged_count = len(new_lines)
    return merged_count, total_source_lines


def build_generated_shell_cleanup_report(root: Path) -> dict:
    root = Path(root)
    generated_root = active_generated_root(root)
    segment_map = _generated_shell_segment_map(root)
    duplicate_files: list[dict] = []
    missing_canonical: list[dict] = []
    mismatched_files: list[dict] = []
    unmanaged_files: list[str] = []

    if not generated_root.exists():
        return {
            "generated_root": str(generated_root),
            "present": False,
            "duplicate_files": [],
            "duplicate_count": 0,
            "missing_canonical": [],
            "missing_canonical_count": 0,
            "mismatched_files": [],
            "mismatch_count": 0,
            "unmanaged_files": [],
            "unmanaged_count": 0,
        }

    for source in sorted(path for path in generated_root.rglob("*") if path.is_file()):
        segment_source = next((candidate for candidate in segment_map if source.is_relative_to(candidate)), None)
        if segment_source is None:
            unmanaged_files.append(str(source))
            continue
        destination = segment_map[segment_source] / source.relative_to(segment_source)
        if not destination.exists():
            missing_canonical.append(
                {
                    "legacy_path": str(source),
                    "canonical_copy": str(destination),
                    "segment": segment_source.name,
                }
            )
            continue
        try:
            if source.read_bytes() == destination.read_bytes():
                duplicate_files.append(
                    {
                        "legacy_path": str(source),
                        "canonical_copy": str(destination),
                        "segment": segment_source.name,
                    }
                )
            else:
                mismatched_files.append(
                    {
                        "legacy_path": str(source),
                        "canonical_copy": str(destination),
                        "segment": segment_source.name,
                    }
                )
        except Exception:
            mismatched_files.append(
                {
                    "legacy_path": str(source),
                    "canonical_copy": str(destination),
                    "segment": segment_source.name,
                }
            )

    return {
        "generated_root": str(generated_root),
        "present": True,
        "duplicate_files": duplicate_files,
        "duplicate_count": len(duplicate_files),
        "missing_canonical": missing_canonical,
        "missing_canonical_count": len(missing_canonical),
        "mismatched_files": mismatched_files,
        "mismatch_count": len(mismatched_files),
        "unmanaged_files": unmanaged_files,
        "unmanaged_count": len(unmanaged_files),
        "segment_targets": {str(source): str(target) for source, target in segment_map.items()},
    }


def build_legacy_runtime_diff(root: Path) -> dict:
    root = Path(root)
    legacy_package = legacy_runtime_package_root(root)
    canonical_package = live_runtime_package_root(root)
    files: list[dict] = []

    if legacy_package.exists():
        for path in sorted(legacy_package.rglob("*.py")):
            relative = path.relative_to(legacy_package)
            canonical_path = canonical_package / relative
            status = "missing_in_canonical"
            if canonical_path.exists():
                status = "identical" if path.read_bytes() == canonical_path.read_bytes() else "different"
            files.append(
                {
                    "path": str(relative).replace("\\", "/"),
                    "status": status,
                }
            )

    return {
        "legacy_package_root": str(legacy_package),
        "canonical_package_root": str(canonical_package),
        "legacy_file_count": len(files),
        "identical_file_count": sum(1 for item in files if item["status"] == "identical"),
        "different_file_count": sum(1 for item in files if item["status"] == "different"),
        "missing_in_canonical_count": sum(1 for item in files if item["status"] == "missing_in_canonical"),
        "different_files": [item for item in files if item["status"] == "different"],
        "missing_in_canonical_files": [item for item in files if item["status"] == "missing_in_canonical"],
        "files": files,
        "legacy_bundle_removal_ready": all(item["status"] == "identical" for item in files) if files else False,
    }


def write_legacy_runtime_diff(root: Path, output_path: Path | None = None) -> dict:
    root = Path(root)
    if output_path is None:
        output_path = default_legacy_diff_path(root)
    payload = build_legacy_runtime_diff(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build_legacy_runtime_audit(root: Path) -> dict:
    root = Path(root)
    legacy_root = legacy_runtime_root(root)
    package_root = live_runtime_package_root(root)
    reference_hits: list[dict] = []
    source_roots = [
        root / "lightspeed_runtime",
        root / "tests",
    ]
    skip_dirs = {"__pycache__", ".pytest_cache"}

    def _scan_file(path: Path) -> None:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return
        if "canonical_runtime" not in text:
            return
        reference_hits.append(
            {
                "path": str(path),
                "count": text.count("canonical_runtime"),
            }
        )

    for source_root in source_roots:
        if not source_root.exists():
            continue
        for current_root, dirs, files in os.walk(source_root):
            dirs[:] = [entry for entry in dirs if entry not in skip_dirs]
            current_path = Path(current_root)
            for file_name in files:
                if file_name.endswith(".py"):
                    _scan_file(current_path / file_name)

    for source_file in sorted(root.glob("*.py")):
        _scan_file(source_file)

    legacy_package = legacy_runtime_package_root(root)
    legacy_exports = legacy_runtime_exports_root(root)
    return {
        "canonical_package_root": str(package_root),
        "legacy_root": str(legacy_root),
        "legacy_root_present": legacy_root.exists(),
        "legacy_package_present": legacy_package.exists(),
        "legacy_exports_present": legacy_exports.exists(),
        "legacy_package_files": len(list(legacy_package.rglob("*.py"))) if legacy_package.exists() else 0,
        "legacy_export_files": len(list(legacy_exports.rglob("*"))) if legacy_exports.exists() else 0,
        "active_code_references": reference_hits,
        "active_code_reference_count": sum(item["count"] for item in reference_hits),
    }


def write_legacy_runtime_audit(root: Path, output_path: Path | None = None) -> dict:
    root = Path(root)
    if output_path is None:
        output_path = default_legacy_audit_path(root)
    payload = build_legacy_runtime_audit(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _safe_cache_candidates(root: Path) -> list[Path]:
    root = Path(root)
    live_package = live_runtime_package_root(root)
    legacy_package = legacy_runtime_package_root(root)
    relative_dirs = [
        Path("__pycache__"),
        Path("achilles") / "__pycache__",
        Path("labs") / "__pycache__",
        Path("publishing") / "__pycache__",
        Path("reservoirs") / "__pycache__",
        Path("shell") / "__pycache__",
    ]
    candidates = [
        root / ".pytest_cache",
        root / "__pycache__",
        root / "tests" / ".pytest_cache",
        root / "tests" / "__pycache__",
    ]
    candidates.extend(live_package / relative for relative in relative_dirs)
    candidates.extend(legacy_package / relative for relative in relative_dirs)
    seen: set[str] = set()
    unique: list[Path] = []
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def build_cleanup_report(root: Path, *, legacy_audit: dict | None = None, legacy_diff: dict | None = None) -> dict:
    root = Path(root)
    audit = legacy_audit or build_legacy_runtime_audit(root)
    diff = legacy_diff or build_legacy_runtime_diff(root)
    candidates = _safe_cache_candidates(root)
    safe_remove = []
    for candidate in candidates:
        if candidate.exists():
            safe_remove.append(
                {
                    "path": str(candidate),
                    "kind": "cache_dir",
                    "safe_to_remove": True,
                }
            )

    return {
        "legacy_audit": audit,
        "legacy_diff": diff,
        "safe_remove_candidates": safe_remove,
        "legacy_bundle_should_remain_until_manual_review": True,
    }


def write_cleanup_report(root: Path, output_path: Path | None = None) -> dict:
    root = Path(root)
    if output_path is None:
        output_path = default_cleanup_report_path(root)
    payload = build_cleanup_report(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build_cleanup_candidate_report(root: Path) -> dict:
    root = Path(root)
    keep_empty_files = {"__init__.py", ".gitkeep"}
    scan_roots = [
        live_runtime_package_root(root),
        root / "tests",
        root / "config",
        root / "dataindex",
        legacy_runtime_root(root),
    ]
    skipped_roots = [
        root / "Z Axis",
        root / "ai_logs",
        root / "operations",
        root / "data",
        active_generated_root(root),
        legacy_w6_generated_root(root) / "oracle_ingest_file",
        legacy_w6_generated_root(root) / "publish",
        legacy_w6_generated_root(root) / "runtime_exports",
        legacy_operations_w6_generated_root(root),
        root / "w6" / "data" / "oracle_ingest_file",
        root / "operations" / "w6" / "data",
    ]

    empty_files: list[str] = []
    empty_dirs: list[str] = []

    for source_file in sorted(root.glob("*")):
        if source_file.is_file():
            try:
                if source_file.stat().st_size == 0 and source_file.name not in keep_empty_files:
                    empty_files.append(str(source_file))
            except Exception:
                continue
        elif source_file.is_dir():
            try:
                if not any(source_file.iterdir()):
                    empty_dirs.append(str(source_file))
            except Exception:
                continue

    for scan_root in scan_roots:
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*"):
            if path.is_file():
                try:
                    if path.stat().st_size == 0 and path.name not in keep_empty_files:
                        empty_files.append(str(path))
                except Exception:
                    continue
            elif path.is_dir():
                try:
                    if not any(path.iterdir()):
                        empty_dirs.append(str(path))
                except Exception:
                    continue

    legacy_diff = build_legacy_runtime_diff(root)
    legacy_exports = legacy_runtime_exports_root(root)
    duplicate_legacy_exports: list[dict] = []
    if legacy_exports.exists():
        for source in sorted(path for path in legacy_exports.rglob("*") if path.is_file()):
            rel = source.relative_to(legacy_exports)
            destinations = [
                runtime_exports_root(root) / "legacy_bundle" / rel,
                publish_root(root) / "legacy_bundle" / rel,
            ]
            for legacy_root in legacy_generated_roots(root):
                destinations.append(legacy_root / "runtime_exports" / "legacy_bundle" / rel)
                destinations.append(legacy_root / "publish" / "legacy_bundle" / rel)
            for destination in destinations:
                if destination.exists():
                    try:
                        if source.read_bytes() == destination.read_bytes():
                            duplicate_legacy_exports.append(
                                {
                                    "legacy_path": str(source),
                                    "canonical_copy": str(destination),
                                }
                            )
                            break
                    except Exception:
                        continue

    cleanup_report = build_cleanup_report(root, legacy_diff=legacy_diff)
    return {
        "scanned_roots": [str(path) for path in scan_roots if path.exists()],
        "skipped_roots": [str(path) for path in skipped_roots if path.exists()],
        "empty_files": empty_files,
        "empty_file_count": len(empty_files),
        "empty_directories": empty_dirs,
        "empty_directory_count": len(empty_dirs),
        "safe_cache_candidates": cleanup_report.get("safe_remove_candidates", []),
        "identical_legacy_runtime_files": legacy_diff.get("identical_file_count", 0),
        "different_legacy_runtime_files": legacy_diff.get("different_file_count", 0),
        "duplicate_legacy_exports": duplicate_legacy_exports,
        "duplicate_legacy_export_count": len(duplicate_legacy_exports),
    }


def write_cleanup_candidate_report(root: Path, output_path: Path | None = None) -> dict:
    root = Path(root)
    if output_path is None:
        output_path = default_cleanup_candidates_path(root)
    payload = build_cleanup_candidate_report(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def remove_safe_cache_dirs(root: Path) -> dict:
    root = Path(root)
    candidates = _safe_cache_candidates(root)
    removed: list[str] = []
    missing: list[str] = []
    failed: list[dict] = []

    for path in candidates:
        if not path.exists():
            missing.append(str(path))
            continue
        try:
            shutil.rmtree(path)
            removed.append(str(path))
        except Exception as exc:
            failed.append({"path": str(path), "error": str(exc)})

    return {
        "removed": removed,
        "missing": missing,
        "failed": failed,
    }


def sync_legacy_runtime_bundle(root: Path, output_path: Path | None = None) -> dict:
    root = Path(root)
    live_package = live_runtime_package_root(root)
    legacy_package = legacy_runtime_package_root(root)

    if output_path is None:
        output_path = default_legacy_sync_path(root)

    payload: dict = {
        "live_package_root": str(live_package),
        "legacy_package_root": str(legacy_package),
        "live_package_present": live_package.exists(),
        "legacy_package_present": legacy_package.exists(),
        "synced_files": [],
        "synced_count": 0,
        "before_diff": build_legacy_runtime_diff(root),
        "after_diff": {},
        "removal_ready_after_sync": False,
    }

    if not live_package.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    legacy_package.mkdir(parents=True, exist_ok=True)
    for source in sorted(path for path in live_package.rglob("*.py") if path.is_file()):
        relative = source.relative_to(live_package)
        destination = legacy_package / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            try:
                if destination.read_bytes() == source.read_bytes():
                    continue
            except Exception:
                pass
        shutil.copy2(source, destination)
        payload["synced_files"].append(str(relative).replace("\\", "/"))

    payload["synced_count"] = len(payload["synced_files"])
    payload["after_diff"] = build_legacy_runtime_diff(root)
    payload["removal_ready_after_sync"] = bool(payload["after_diff"].get("legacy_bundle_removal_ready"))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def remove_duplicate_legacy_exports(root: Path, output_path: Path | None = None) -> dict:
    root = Path(root)
    legacy_exports = legacy_runtime_exports_root(root)
    if output_path is None:
        output_path = default_legacy_export_cleanup_path(root)

    candidates = build_cleanup_candidate_report(root).get("duplicate_legacy_exports", [])
    removed: list[str] = []
    failed: list[dict] = []
    missing: list[str] = []

    for item in candidates:
        legacy_path = Path(str(item.get("legacy_path", "")))
        if not legacy_path.exists():
            missing.append(str(legacy_path))
            continue
        try:
            legacy_path.unlink()
            removed.append(str(legacy_path))
        except Exception as exc:
            failed.append({"path": str(legacy_path), "error": str(exc)})

    if legacy_exports.exists():
        for directory in sorted((path for path in legacy_exports.rglob("*") if path.is_dir()), reverse=True):
            try:
                if not any(directory.iterdir()):
                    directory.rmdir()
            except Exception:
                continue

    payload = {
        "legacy_exports_root": str(legacy_exports),
        "duplicate_candidates": len(candidates),
        "removed": removed,
        "removed_count": len(removed),
        "missing": missing,
        "failed": failed,
        "cleanup_candidates_after": build_cleanup_candidate_report(root).get("duplicate_legacy_export_count", 0),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def remove_duplicate_generated_shell_files(root: Path, output_path: Path | None = None) -> dict:
    root = Path(root)
    if output_path is None:
        output_path = default_generated_shell_cleanup_path(root)

    report = build_generated_shell_cleanup_report(root)
    removed: list[str] = []
    failed: list[dict] = []
    pruned_directories: list[str] = []
    merged_logs: list[dict] = []
    moved_files: list[dict] = []

    for item in report.get("duplicate_files", []):
        legacy_path = Path(str(item.get("legacy_path", "")))
        if not legacy_path.exists():
            continue
        try:
            legacy_path.unlink()
            removed.append(str(legacy_path))
        except Exception as exc:
            failed.append({"path": str(legacy_path), "error": str(exc)})

    segment_map = _generated_shell_segment_map(root)
    generated_root = active_generated_root(root)
    for source in sorted(path for path in generated_root.rglob("*") if path.is_file()):
        segment_source = next((candidate for candidate in segment_map if source.is_relative_to(candidate)), None)
        if segment_source is None:
            continue
        destination = segment_map[segment_source] / source.relative_to(segment_source)
        if source.suffix.lower() == ".jsonl" and destination.exists():
            try:
                merged_count, source_line_count = _merge_jsonl_into_target(source, destination)
                source.unlink()
                removed.append(str(source))
                merged_logs.append(
                    {
                        "legacy_path": str(source),
                        "canonical_copy": str(destination),
                        "merged_line_count": merged_count,
                        "source_line_count": source_line_count,
                    }
                )
            except Exception as exc:
                failed.append({"path": str(source), "error": str(exc)})
        elif not destination.exists():
            try:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(destination))
                moved_files.append({"legacy_path": str(source), "canonical_copy": str(destination)})
            except Exception as exc:
                failed.append({"path": str(source), "error": str(exc)})

    if generated_root.exists():
        for directory in sorted((path for path in generated_root.rglob("*") if path.is_dir()), key=lambda item: len(item.parts), reverse=True):
            try:
                if not any(directory.iterdir()):
                    directory.rmdir()
                    pruned_directories.append(str(directory))
            except Exception:
                continue
        try:
            if not any(generated_root.iterdir()):
                generated_root.rmdir()
                pruned_directories.append(str(generated_root))
        except Exception:
            pass

    after = build_generated_shell_cleanup_report(root)
    payload = {
        "generated_root": str(generated_root),
        "generated_root_present_after": generated_root.exists(),
        "duplicate_candidates": report.get("duplicate_count", 0),
        "removed": removed,
        "removed_count": len(removed),
        "failed": failed,
        "failed_count": len(failed),
        "merged_logs": merged_logs,
        "merged_log_count": len(merged_logs),
        "moved_files": moved_files,
        "moved_file_count": len(moved_files),
        "pruned_directories": pruned_directories,
        "pruned_directory_count": len(pruned_directories),
        "remaining_duplicate_count": after.get("duplicate_count", 0),
        "remaining_unmanaged_count": after.get("unmanaged_count", 0),
        "remaining_missing_canonical_count": after.get("missing_canonical_count", 0),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
