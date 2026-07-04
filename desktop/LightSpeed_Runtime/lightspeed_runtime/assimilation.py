from __future__ import annotations

import json
import shutil
from pathlib import Path

from lightspeed_runtime.storage_paths import (
    active_generated_root,
    canonical_runtime_config_path,
    construct_reservoir_root,
    datatables_root,
    encyclopedia_root,
    ensure_generated_layout,
    ingestion_root,
    legacy_operations_w6_generated_root,
    legacy_runtime_bundle_root,
    legacy_w6_generated_root,
    library_root,
    logs_root,
    oracle_reservoir_root,
    operations_root,
    publish_root,
    quality_root,
    resolve_runtime_config_path,
    reports_root,
    runtime_exports_root,
    smith_root,
)


def default_assimilation_report_path(root: Path) -> Path:
    return runtime_exports_root(root) / "smart_floor_assimilation.json"


def default_assimilation_migration_path(root: Path) -> Path:
    return runtime_exports_root(root) / "smart_floor_migration.json"


def default_legacy_rehome_path(root: Path) -> Path:
    return runtime_exports_root(root) / "legacy_root_rehome.json"


def default_external_root_assimilation_path(root: Path) -> Path:
    return runtime_exports_root(root) / "external_root_assimilation.json"


def _runtime_config_path(root: Path) -> Path:
    return canonical_runtime_config_path(root)


def _load_runtime_config(root: Path) -> tuple[Path, dict]:
    path = resolve_runtime_config_path(root)
    if not path.exists():
        legacy_candidates = [
            root / "config" / "runtime" / "runtime_reservoirs.json",
            root / "config" / "runtime_reservoirs.json",
        ]
        for candidate in legacy_candidates:
            if candidate.exists():
                path = candidate
                break
        else:
            return path, {"sources": []}
    try:
        return path, json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return path, {"sources": []}


def _write_runtime_config(root: Path, payload: dict) -> Path:
    path = _runtime_config_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _external_source_bases(root: Path) -> list[Path]:
    root = Path(root)
    candidates: list[Path] = []
    shell_parent = root.parent
    project_root = root.parents[1] if len(root.parents) > 1 else shell_parent
    drive_workspace_root = root.parents[2] if len(root.parents) > 2 else Path(root.anchor)
    drive_root = Path(root.anchor)
    for candidate in (project_root, drive_workspace_root, shell_parent, drive_root):
        resolved = Path(candidate)
        if resolved not in candidates:
            candidates.append(resolved)
    return candidates


def _resolve_external_source(root: Path, *relative_parts: str) -> Path:
    bases = _external_source_bases(root)
    for base in bases:
        candidate = base.joinpath(*relative_parts)
        if candidate.exists():
            return candidate
    return bases[0].joinpath(*relative_parts)


def build_external_root_assimilation_plan(root: Path) -> dict:
    root = Path(root)
    outer_roots = _external_source_bases(root)
    oracle_reservoirs = oracle_reservoir_root(root)
    construct_reservoirs = construct_reservoir_root(root)
    smith_legacy = smith_root(root) / "legacy"
    plan = {
        "outer_root": str(outer_roots[0]),
        "search_roots": [str(candidate) for candidate in outer_roots],
        "targets": [
            {
                "label": "2026 doctrine bundle",
                "source": str(_resolve_external_source(root, "2026 Documents")),
                "target": str(oracle_reservoirs / "2026 Documents"),
                "source_ids": ["docs_2026_master", "notebooklm_2026"],
                "owner": "Oracle",
            },
            {
                "label": "ACHILLES file processor archive",
                "source": str(_resolve_external_source(root, "ACHILLES_FileProcessor_v2.0.0")),
                "target": str(smith_legacy / "ACHILLES_FileProcessor_v2.0.0"),
                "source_ids": ["achilles_fileprocessor_archive"],
                "owner": "Smith",
            },
            {
                "label": "Empirical data bundle",
                "source": str(_resolve_external_source(root, "Library", "Empirical Data")),
                "target": str(construct_reservoirs / "Library" / "Empirical Data"),
                "source_ids": ["library_empirical_data"],
                "owner": "TheConstruct",
            },
            {
                "label": "Web calculators",
                "source": str(_resolve_external_source(root, "Library", "web Calculators")),
                "target": str(construct_reservoirs / "Library" / "web Calculators"),
                "source_ids": ["library_calculators"],
                "owner": "TheConstruct",
            },
            {
                "label": "General library reference",
                "source": str(_resolve_external_source(root, "Library")),
                "target": str(oracle_reservoirs / "Library"),
                "source_ids": ["library_reference_general"],
                "owner": "Oracle",
            },
            {
                "label": "LightSpeed reference library",
                "source": str(_resolve_external_source(root, "LightSpeed_Reference_Library")),
                "target": str(oracle_reservoirs / "LightSpeed_Reference_Library"),
                "source_ids": ["lightspeed_reference_library"],
                "owner": "Oracle",
            },
        ],
    }
    return plan


def assimilate_external_roots(root: Path, *, output_path: Path | None = None) -> dict:
    root = Path(root)
    ensure_generated_layout(root)
    plan = build_external_root_assimilation_plan(root)
    moved_paths: list[dict] = []
    conflicts: list[dict] = []
    missing: list[str] = []
    removed_empty_parents: list[str] = []

    for item in plan["targets"]:
        source = Path(item["source"])
        target = Path(item["target"])
        if not source.exists():
            missing.append(str(source))
            continue
        _merge_move_tree(source, target, moved_paths=moved_paths, conflicts=conflicts)

    removal_relatives = [
        ("Library",),
        ("2026 Documents",),
        ("ACHILLES_FileProcessor_v2.0.0",),
        ("LightSpeed_Reference_Library",),
    ]
    for base in _external_source_bases(root):
        for parts in removal_relatives:
            candidate = base.joinpath(*parts)
            try:
                if candidate.exists() and not any(candidate.iterdir()):
                    candidate.rmdir()
                    removed_empty_parents.append(str(candidate))
            except Exception:
                continue

    _loaded_config_path, config_payload = _load_runtime_config(root)
    sources = list(config_payload.get("sources") or [])
    root_updates = {
        "docs_2026_master": str(oracle_reservoir_root(root) / "2026 Documents"),
        "notebooklm_2026": str(oracle_reservoir_root(root) / "2026 Documents" / "Notebook" / "NoteBookLM"),
        "achilles_fileprocessor_archive": str(smith_root(root) / "legacy" / "ACHILLES_FileProcessor_v2.0.0"),
        "library_empirical_data": str(construct_reservoir_root(root) / "Library" / "Empirical Data"),
        "library_calculators": str(construct_reservoir_root(root) / "Library" / "web Calculators"),
        "lightspeed_reference_library": str(oracle_reservoir_root(root) / "LightSpeed_Reference_Library"),
    }
    updated_source_ids: list[str] = []
    for source in sources:
        source_id = str(source.get("source_id") or "")
        if source_id in root_updates:
            source["root_path"] = root_updates[source_id]
            updated_source_ids.append(source_id)

    if not any(str(item.get("source_id") or "") == "library_reference_general" for item in sources):
        sources.append(
            {
                "source_id": "library_reference_general",
                "root_path": str(oracle_reservoir_root(root) / "Library"),
                "source_type": "reference_library",
                "classification": "reference",
                "floor_owner": "Oracle",
                "workspace_tags": ["romer", "achilles"],
                "project_tags": ["Romer", "Reference"],
                "trusted_documents": ["Library", "Physics", "BioChem"],
                "extractors": ["pdf", "text", "image"],
            }
        )
        updated_source_ids.append("library_reference_general")

    config_payload["sources"] = sources
    config_path = _write_runtime_config(root, config_payload)

    payload = {
        "outer_root": plan["outer_root"],
        "target_count": len(plan["targets"]),
        "moved_count": len(moved_paths),
        "moved_paths": moved_paths,
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "missing_sources": missing,
        "removed_empty_parents": removed_empty_parents,
        "config_path": str(config_path),
        "updated_source_ids": updated_source_ids,
        "oracle_reservoir_root": str(oracle_reservoir_root(root)),
        "construct_reservoir_root": str(construct_reservoir_root(root)),
        "smith_legacy_root": str(smith_root(root) / "legacy"),
    }
    destination = output_path or default_external_root_assimilation_path(root)
    payload["report_path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build_assimilation_report(root: Path, *, manifests: list[dict] | None = None) -> dict:
    root = Path(root)
    ensure_generated_layout(root)
    data_generated = active_generated_root(root)
    operations_dir = root / "operations"
    w6_dir = root / "w6"
    smith_legacy_dir = smith_root(root) / "legacy"
    merovingian_legacy_runtime = legacy_runtime_bundle_root(root)
    payload = {
        "root": str(root),
        "external_source_count": len(manifests or []),
        "external_sources": manifests or [],
        "smart_floor_roots": {
            "oracle": str(root / "Z Axis" / "Z-2_Oracle"),
            "construct": str(root / "Z Axis" / "Z0_TheConstruct"),
            "architect": str(root / "Z Axis" / "Z+1_Architect"),
            "neo": str(root / "Z Axis" / "Z+2_Neo"),
            "smith": str(root / "Z Axis" / "Z-3_Smith"),
            "merovingian": str(root / "Z Axis" / "Z-4_Merovingian"),
        },
        "canonical_output_roots": {
            "oracle_ingestion": str(ingestion_root(root)),
            "oracle_library": str(library_root(root)),
            "oracle_encyclopedia": str(encyclopedia_root(root)),
            "oracle_datatables": str(datatables_root(root)),
            "architect_publish": str(publish_root(root)),
            "construct_labs": str(root / "Z Axis" / "Z0_TheConstruct" / "data" / "labs"),
            "merovingian_runtime_exports": str(runtime_exports_root(root)),
            "merovingian_reports": str(reports_root(root)),
            "merovingian_logs": str(logs_root(root)),
            "merovingian_quality": str(quality_root(root)),
            "smith_operations": str(operations_root(root)),
        },
        "legacy_roots": {
            "data_generated": {"path": str(data_generated), "present": data_generated.exists()},
            "root_w6": {"path": str(w6_dir), "present": w6_dir.exists()},
            "root_operations_w6": {"path": str(operations_dir / "w6"), "present": (operations_dir / "w6").exists()},
            "smith_legacy": {"path": str(smith_legacy_dir), "present": smith_legacy_dir.exists()},
            "smith_legacy_w6_data": {
                "path": str(legacy_w6_generated_root(root)),
                "present": legacy_w6_generated_root(root).exists(),
            },
            "smith_legacy_operations_w6_data": {
                "path": str(legacy_operations_w6_generated_root(root)),
                "present": legacy_operations_w6_generated_root(root).exists(),
            },
            "merovingian_legacy_runtime_bundle": {
                "path": str(merovingian_legacy_runtime),
                "present": merovingian_legacy_runtime.exists(),
            },
        },
        "reference_roots": {
            "tests_dir": {"path": str(root / "tests"), "present": (root / "tests").exists()},
        },
        "notes": [
            "data/generated is a flat legacy compatibility root only; runtime layout no longer creates it by default.",
            "Oracle owns ingestion, library, encyclopedia, and datatable proofing.",
            "TheConstruct owns simulation and lab outputs.",
            "Architect owns publish packages and workspace exports.",
            "Smith owns operational registries and legacy ingest mirrors, including rehomed w6-era trees.",
            "Merovingian owns runtime exports, reports, logs, quality outputs, and the legacy runtime reference bundle.",
            "Root-level w6 and operations/w6 should be emptied and removed after rehome verification.",
        ],
    }
    return payload


def write_assimilation_report(root: Path, *, manifests: list[dict] | None = None, output_path: Path | None = None) -> dict:
    root = Path(root)
    path = output_path or default_assimilation_report_path(root)
    payload = build_assimilation_report(root, manifests=manifests)
    payload["report_path"] = str(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _copy_tree_contents(source: Path, target: Path, *, copied_files: list[str]) -> None:
    if not source.exists():
        return
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        destination = target / relative
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and destination.read_bytes() == path.read_bytes():
            continue
        shutil.copy2(path, destination)
        copied_files.append(str(destination))


def _merge_move_tree(source: Path, target: Path, *, moved_paths: list[dict], conflicts: list[dict]) -> None:
    if not source.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.move(str(source), str(target))
        moved_paths.append({"source": str(source), "target": str(target), "mode": "move"})
        return

    for child in sorted(source.iterdir(), key=lambda item: item.name):
        destination = target / child.name
        if child.is_dir():
            _merge_move_tree(child, destination, moved_paths=moved_paths, conflicts=conflicts)
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            try:
                if destination.read_bytes() == child.read_bytes():
                    child.unlink()
                    moved_paths.append({"source": str(child), "target": str(destination), "mode": "deduplicated"})
                    continue
            except Exception:
                pass
            conflicts.append({"source": str(child), "target": str(destination)})
            continue

        shutil.move(str(child), str(destination))
        moved_paths.append({"source": str(child), "target": str(destination), "mode": "move"})

    try:
        if not any(source.iterdir()):
            source.rmdir()
    except Exception:
        pass


def rehome_legacy_roots(root: Path, *, output_path: Path | None = None) -> dict:
    root = Path(root)
    ensure_generated_layout(root)

    sources = {
        root / "w6": smith_root(root) / "legacy" / "w6",
        root / "operations" / "w6": smith_root(root) / "legacy" / "operations_w6",
        root / "canonical_runtime": legacy_runtime_bundle_root(root),
    }
    moved_paths: list[dict] = []
    conflicts: list[dict] = []
    missing: list[str] = []
    removed_empty_parents: list[str] = []

    for source, target in sources.items():
        if not source.exists():
            missing.append(str(source))
            continue
        _merge_move_tree(source, target, moved_paths=moved_paths, conflicts=conflicts)

    for candidate in (root / "operations", root / "w6"):
        try:
            if candidate.exists() and not any(candidate.iterdir()):
                candidate.rmdir()
                removed_empty_parents.append(str(candidate))
        except Exception:
            continue

    payload = {
        "sources": {str(source): str(target) for source, target in sources.items()},
        "moved_count": len(moved_paths),
        "moved_paths": moved_paths,
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "missing_sources": missing,
        "removed_empty_parents": removed_empty_parents,
        "legacy_w6_root": str(legacy_w6_generated_root(root)),
        "legacy_operations_w6_root": str(legacy_operations_w6_generated_root(root)),
        "legacy_runtime_bundle_root": str(legacy_runtime_bundle_root(root)),
    }
    destination = output_path or default_legacy_rehome_path(root)
    payload["report_path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def migrate_smart_floor_outputs(root: Path, *, output_path: Path | None = None) -> dict:
    root = Path(root)
    ensure_generated_layout(root)
    copied_files: list[str] = []

    legacy_generated = active_generated_root(root)
    segment_map = {
        legacy_generated / "ingestion": ingestion_root(root),
        legacy_generated / "labs": root / "Z Axis" / "Z0_TheConstruct" / "data" / "labs",
        legacy_generated / "publish": publish_root(root),
        legacy_generated / "reports": reports_root(root),
        legacy_generated / "logs": logs_root(root),
        legacy_generated / "runtime_exports": runtime_exports_root(root),
    }
    for source, target in segment_map.items():
        _copy_tree_contents(source, target, copied_files=copied_files)

    latest_results = root / "tests" / "latest_test_results.json"
    if latest_results.exists():
        quality_target = quality_root(root) / "latest_test_results.json"
        quality_target.parent.mkdir(parents=True, exist_ok=True)
        if not quality_target.exists() or quality_target.read_bytes() != latest_results.read_bytes():
            shutil.copy2(latest_results, quality_target)
            copied_files.append(str(quality_target))

    operations_registry = {
        "smith_operations_root": str(operations_root(root)),
        "legacy_operations_root": str(root / "operations"),
        "legacy_w6_root": str(root / "w6"),
        "rehomed_legacy_operations_root": str(legacy_operations_w6_generated_root(root)),
        "rehomed_legacy_w6_root": str(legacy_w6_generated_root(root)),
        "legacy_operations_present": (root / "operations").exists(),
        "legacy_w6_present": (root / "w6").exists(),
        "status": "legacy_reference_only",
    }
    registry_path = operations_root(root) / "legacy_operations_registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(operations_registry, indent=2), encoding="utf-8")
    copied_files.append(str(registry_path))

    report = {
        "legacy_generated_root": str(legacy_generated),
        "copied_file_count": len(copied_files),
        "copied_files": copied_files,
        "operations_registry": str(registry_path),
        "targets": {str(key): str(value) for key, value in segment_map.items()},
    }
    destination = output_path or default_assimilation_migration_path(root)
    report["migration_report_path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
