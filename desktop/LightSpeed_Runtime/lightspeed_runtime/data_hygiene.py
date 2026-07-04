from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from lightspeed_runtime.storage_paths import (
    active_generated_root,
    all_generated_roots,
    describe_generated_roots,
    ensure_generated_layout,
    ingestion_root,
    legacy_runtime_bundle_root,
    publish_root as generated_publish_root,
    resolve_tool_data_root,
    runtime_exports_root,
)

_RESERVED_GENERATED_DIRS = {"publish", "runtime_exports", "logs", "reports", "ingestion"}


def _safe_load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _normalize_summary_payload(summary: dict) -> dict:
    if not isinstance(summary, dict):
        return {}
    payload = dict(summary)
    tools = dict(payload.get("tools", {}) or {})
    for name in list(tools.keys()):
        if name in _RESERVED_GENERATED_DIRS:
            tools.pop(name, None)
    payload["tools"] = tools
    payload["tool_count"] = len(tools)
    payload["total_manifests"] = sum(
        int((item or {}).get("manifest_count", 0) or 0)
        for item in tools.values()
        if isinstance(item, dict)
    )
    return payload


def default_summary_path(root: Path) -> Path:
    return runtime_exports_root(root) / "data_hygiene_summary.json"


def default_compaction_plan_path(root: Path) -> Path:
    return runtime_exports_root(root) / "compaction_plan.json"


def default_compaction_index_path(root: Path) -> Path:
    return compaction_rollup_root(root) / "index.json"


def archive_workflow_root(root: Path) -> Path:
    return runtime_exports_root(root) / "archive_workflows"


def default_archive_workflow_path(root: Path, tool_name: str = "oracle_ingest_file") -> Path:
    return archive_workflow_root(root) / tool_name / "archive_workflow.json"


def archive_execution_root(root: Path, tool_name: str = "oracle_ingest_file") -> Path:
    return archive_workflow_root(root) / tool_name / "executions"


def default_archive_execution_state_path(root: Path, tool_name: str = "oracle_ingest_file") -> Path:
    return archive_workflow_root(root) / tool_name / "archive_execution_state.json"


def compaction_rollup_root(root: Path) -> Path:
    return runtime_exports_root(root) / "compaction"


def build_generated_data_summary(root: Path, *, sample_limit: int = 3) -> dict:
    root = Path(root)
    ensure_generated_layout(root)
    primary_root = active_generated_root(root)
    tools: dict[str, dict] = {}
    total_manifests = 0
    package_rel_paths: set[str] = set()
    tool_runs: dict[str, dict[str, Path]] = {}
    tool_source_roots: dict[str, set[str]] = {}

    for generated_root in all_generated_roots(root):
        if not generated_root.exists():
            continue
        tool_parent = ingestion_root(root) if generated_root == primary_root else generated_root
        package_root = generated_publish_root(root) if generated_root == primary_root else generated_root / "publish"
        if package_root.exists():
            for package_path in package_root.rglob("package_metadata.json"):
                if package_path.is_file():
                    try:
                        package_rel_paths.add(package_path.relative_to(package_root).as_posix())
                    except Exception:
                        package_rel_paths.add(str(package_path))

        if not tool_parent.exists():
            continue
        for tool_dir in sorted(path for path in tool_parent.iterdir() if path.is_dir() and path.name not in _RESERVED_GENERATED_DIRS):
            run_map = tool_runs.setdefault(tool_dir.name, {})
            source_roots = tool_source_roots.setdefault(tool_dir.name, set())
            source_roots.add(str(tool_dir))
            for manifest_path in sorted(tool_dir.glob("*/manifest.json")):
                run_id = manifest_path.parent.name
                run_map.setdefault(run_id, manifest_path)

    for tool_name, run_map in sorted(tool_runs.items()):
        manifests = [run_map[key] for key in sorted(run_map.keys())]
        total_manifests += len(manifests)
        years: dict[str, int] = {}
        samples: list[dict] = []
        latest_run = ""
        for manifest_path in manifests:
            run_id = manifest_path.parent.name
            year = run_id[:4] if len(run_id) >= 4 and run_id[:4].isdigit() else "unknown"
            years[year] = years.get(year, 0) + 1
            if run_id > latest_run:
                latest_run = run_id
            if len(samples) < sample_limit:
                payload = _safe_load_json(manifest_path)
                samples.append(
                    {
                        "run_id": run_id,
                        "status": payload.get("status", "unknown"),
                        "tool": payload.get("tool") or tool_name,
                    }
                )
        tools[tool_name] = {
            "manifest_count": len(manifests),
            "latest_run": latest_run or None,
            "years": years,
            "sample_runs": samples,
            "source_roots": sorted(tool_source_roots.get(tool_name, set())),
        }

    return {
        "generated_root": str(primary_root),
        **describe_generated_roots(root),
        "tool_count": len(tools),
        "total_manifests": total_manifests,
        "publish_packages": len(package_rel_paths),
        "tools": tools,
    }


def read_generated_data_summary(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_summary_path(root)
    if not path.exists():
        return {}
    payload = _normalize_summary_payload(_safe_load_json(path))
    try:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass
    return payload


def write_generated_data_summary(root: Path, output_path: Path | None = None) -> dict:
    root = Path(root)
    if output_path is None:
        output_path = default_summary_path(root)
    summary = build_generated_data_summary(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def build_compaction_plan(
    root: Path,
    *,
    hygiene_summary: dict | None = None,
    manifest_threshold: int = 1000,
) -> dict:
    root = Path(root)
    summary = hygiene_summary or read_generated_data_summary(root) or build_generated_data_summary(root)
    tools = summary.get("tools", {}) if isinstance(summary, dict) else {}
    recommendations: list[dict] = []

    for tool_name, payload in sorted(tools.items()):
        manifest_count = int(payload.get("manifest_count", 0) or 0)
        years = payload.get("years", {}) or {}
        if manifest_count < manifest_threshold:
            continue
        yearly_counts = [{"year": year, "manifest_count": count} for year, count in sorted(years.items())]
        recommendations.append(
            {
                "tool": tool_name,
                "manifest_count": manifest_count,
                "latest_run": payload.get("latest_run"),
                "yearly_counts": yearly_counts,
                "recommended_action": "write_yearly_rollups_then_review_raw_runs",
                "raw_runs_delete_after_verification": False,
            }
        )

    legacy_bundle = legacy_runtime_bundle_root(root)
    if not legacy_bundle.exists():
        legacy_bundle = root / "canonical_runtime"
    else:
        try:
            if not any(legacy_bundle.iterdir()) and (root / "canonical_runtime").exists():
                legacy_bundle = root / "canonical_runtime"
        except Exception:
            pass
    runtime_package = root / "lightspeed_runtime"
    cache_paths = []
    for candidate in (
        root / ".pytest_cache",
        root / "__pycache__",
        legacy_bundle / "lightspeed_runtime" / "__pycache__",
    ):
        if candidate.exists():
            cache_paths.append(str(candidate))

    return {
        "generated_root": summary.get("generated_root", str(active_generated_root(root))),
        "legacy_generated_roots": summary.get("legacy_generated_roots", []),
        "total_manifests": summary.get("total_manifests", 0),
        "publish_packages": summary.get("publish_packages", 0),
        "canonical_runtime_package": str(runtime_package),
        "legacy_runtime_bundle": str(legacy_bundle),
        "consolidated_index_path": str(default_compaction_index_path(root)),
        "legacy_runtime_bundle_present": legacy_bundle.exists(),
        "duplicate_runtime_package_present": (legacy_bundle / "lightspeed_runtime").exists(),
        "cache_candidates": cache_paths,
        "manifest_threshold": manifest_threshold,
        "recommendations": recommendations,
    }


def read_compaction_plan(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_compaction_plan_path(root)
    if not path.exists():
        return {}
    return _safe_load_json(path)


def write_compaction_plan(root: Path, output_path: Path | None = None, *, manifest_threshold: int = 1000) -> dict:
    root = Path(root)
    if output_path is None:
        output_path = default_compaction_plan_path(root)
    plan = build_compaction_plan(root, manifest_threshold=manifest_threshold)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return plan


def build_compaction_indexes(root: Path, *, hygiene_summary: dict | None = None) -> dict:
    root = Path(root)
    summary = hygiene_summary or read_generated_data_summary(root) or build_generated_data_summary(root)
    output_root = compaction_rollup_root(root)
    tools_payload: list[dict] = []

    for tool_name, payload in sorted((summary.get("tools") or {}).items()):
        years = payload.get("years", {}) or {}
        yearly_counts = [
            {"year": year, "manifest_count": count}
            for year, count in sorted(years.items())
        ]
        tool_root = output_root / tool_name
        tools_payload.append(
            {
                "tool": tool_name,
                "manifest_count": payload.get("manifest_count", 0),
                "latest_run": payload.get("latest_run"),
                "sample_runs": payload.get("sample_runs", []) or [],
                "yearly_counts": yearly_counts,
                "tool_index_path": str(tool_root / "index.json"),
                "year_rollup_paths": [
                    str(tool_root / f"{item['year']}.json")
                    for item in yearly_counts
                ],
            }
        )

    return {
        "generated_root": summary.get("generated_root", str(active_generated_root(root))),
        "compaction_root": str(output_root),
        "summary_path": str(default_summary_path(root)),
        "tool_count": len(tools_payload),
        "tools": tools_payload,
    }


def read_compaction_indexes(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_compaction_index_path(root)
    if not path.exists():
        return {}
    return _safe_load_json(path)


def write_compaction_indexes(root: Path, output_path: Path | None = None) -> dict:
    root = Path(root)
    payload = build_compaction_indexes(root)
    output_root = compaction_rollup_root(root)
    if output_path is None:
        output_path = default_compaction_index_path(root)
    output_root.mkdir(parents=True, exist_ok=True)

    created_files: list[str] = []
    for tool_payload in payload.get("tools", []):
        destination = Path(tool_payload["tool_index_path"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(tool_payload, indent=2), encoding="utf-8")
        created_files.append(str(destination))

    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    created_files.append(str(output_path))
    payload["created_files"] = created_files
    return payload


def build_archive_workflow(
    root: Path,
    *,
    tool_name: str = "oracle_ingest_file",
    batch_size: int = 50000,
    hygiene_summary: dict | None = None,
) -> dict:
    root = Path(root)
    summary = hygiene_summary or read_generated_data_summary(root) or build_generated_data_summary(root)
    tool_payload = dict((summary.get("tools") or {}).get(tool_name) or {})
    output_root = archive_workflow_root(root) / tool_name
    years = tool_payload.get("years", {}) or {}

    year_plans: list[dict] = []
    for year, manifest_count in sorted(years.items()):
        manifest_count = int(manifest_count or 0)
        chunk_count = max(1, (manifest_count + batch_size - 1) // batch_size) if manifest_count else 0
        chunks: list[dict] = []
        for idx in range(chunk_count):
            start_ordinal = idx * batch_size + 1
            end_ordinal = min((idx + 1) * batch_size, manifest_count)
            label = f"{tool_name}_{year}_batch_{idx + 1:03d}"
            chunks.append(
                {
                    "label": label,
                    "batch_number": idx + 1,
                    "start_ordinal": start_ordinal,
                    "end_ordinal": end_ordinal,
                    "target_manifest_path": str(output_root / year / f"{label}.json"),
                    "archive_stub_path": str(output_root / year / f"{label}.zip"),
                }
            )
        year_plans.append(
            {
                "year": year,
                "manifest_count": manifest_count,
                "batch_size": batch_size,
                "chunk_count": chunk_count,
                "year_manifest_path": str(output_root / f"{year}_archive_manifest.json"),
                "chunks": chunks,
            }
        )

    return {
        "tool": tool_name,
        "generated_root": str(active_generated_root(root)),
        "source_tool_root": str(resolve_tool_data_root(root, tool_name)),
        "archive_workflow_root": str(output_root),
        "summary_path": str(default_summary_path(root)),
        "latest_run": tool_payload.get("latest_run"),
        "manifest_count": int(tool_payload.get("manifest_count", 0) or 0),
        "batch_size": batch_size,
        "sample_runs": tool_payload.get("sample_runs", []) or [],
        "year_plans": year_plans,
        "non_destructive": True,
        "raw_run_deletion_allowed": False,
        "recommended_sequence": [
            "refresh_generated_data_summary",
            "write_compaction_plan",
            "write_compaction_indexes",
            "write_archive_workflow",
            "manual_review_before_any_raw_run_pruning",
        ],
    }


def read_archive_workflow(root: Path, output_path: Path | None = None, *, tool_name: str = "oracle_ingest_file") -> dict:
    path = output_path or default_archive_workflow_path(root, tool_name=tool_name)
    if not path.exists():
        return {}
    return _safe_load_json(path)


def write_archive_workflow(
    root: Path,
    output_path: Path | None = None,
    *,
    tool_name: str = "oracle_ingest_file",
    batch_size: int = 50000,
) -> dict:
    root = Path(root)
    payload = build_archive_workflow(root, tool_name=tool_name, batch_size=batch_size)
    if output_path is None:
        output_path = default_archive_workflow_path(root, tool_name=tool_name)
    output_root = archive_workflow_root(root) / tool_name
    output_root.mkdir(parents=True, exist_ok=True)

    created_files: list[str] = []
    for year_payload in payload.get("year_plans", []):
        year_manifest = Path(year_payload["year_manifest_path"])
        year_manifest.parent.mkdir(parents=True, exist_ok=True)
        year_manifest.write_text(json.dumps(year_payload, indent=2), encoding="utf-8")
        created_files.append(str(year_manifest))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    created_files.append(str(output_path))
    payload["created_files"] = created_files
    return payload


def _archive_receipt_path(root: Path, tool_name: str, year: str, label: str) -> Path:
    return archive_execution_root(root, tool_name=tool_name) / year / f"{label}.json"


def build_archive_execution_state(
    root: Path,
    *,
    tool_name: str = "oracle_ingest_file",
    workflow: dict | None = None,
) -> dict:
    root = Path(root)
    payload = workflow or read_archive_workflow(root, tool_name=tool_name) or build_archive_workflow(root, tool_name=tool_name)
    executions_root = archive_execution_root(root, tool_name=tool_name)
    receipts: dict[str, dict] = {}

    if executions_root.exists():
        for receipt_path in sorted(executions_root.rglob("*.json")):
            receipt = _safe_load_json(receipt_path)
            label = str(receipt.get("label") or receipt_path.stem)
            receipts[label] = receipt

    batches: list[dict] = []
    next_batch: dict | None = None
    staged_count = 0
    completed_count = 0

    for year_payload in payload.get("year_plans", []):
        for chunk in year_payload.get("chunks", []):
            label = str(chunk.get("label") or "")
            receipt = receipts.get(label, {})
            status = str(receipt.get("status") or "planned")
            if status == "staged_for_review":
                staged_count += 1
            elif status == "completed":
                completed_count += 1
            batch_payload = {
                "year": year_payload.get("year"),
                "label": label,
                "batch_number": chunk.get("batch_number"),
                "start_ordinal": chunk.get("start_ordinal"),
                "end_ordinal": chunk.get("end_ordinal"),
                "status": status,
                "receipt_path": str(_archive_receipt_path(root, tool_name, str(year_payload.get("year")), label)),
            }
            batches.append(batch_payload)
            if next_batch is None and status == "planned":
                next_batch = batch_payload

    return {
        "tool": tool_name,
        "workflow_path": str(default_archive_workflow_path(root, tool_name=tool_name)),
        "execution_root": str(executions_root),
        "batch_count": len(batches),
        "staged_count": staged_count,
        "completed_count": completed_count,
        "planned_count": max(0, len(batches) - staged_count - completed_count),
        "next_batch": next_batch,
        "batches": batches,
    }


def read_archive_execution_state(
    root: Path,
    output_path: Path | None = None,
    *,
    tool_name: str = "oracle_ingest_file",
) -> dict:
    path = output_path or default_archive_execution_state_path(root, tool_name=tool_name)
    if not path.exists():
        return {}
    return _safe_load_json(path)


def write_archive_execution_state(
    root: Path,
    output_path: Path | None = None,
    *,
    tool_name: str = "oracle_ingest_file",
) -> dict:
    root = Path(root)
    payload = build_archive_execution_state(root, tool_name=tool_name)
    if output_path is None:
        output_path = default_archive_execution_state_path(root, tool_name=tool_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def stage_archive_batch(
    root: Path,
    *,
    tool_name: str = "oracle_ingest_file",
    year: str | None = None,
    batch_number: int | None = None,
) -> dict:
    root = Path(root)
    workflow = read_archive_workflow(root, tool_name=tool_name) or write_archive_workflow(root, tool_name=tool_name)
    execution_state = build_archive_execution_state(root, tool_name=tool_name, workflow=workflow)

    target_chunk = None
    for year_payload in workflow.get("year_plans", []):
        if year is not None and str(year_payload.get("year")) != str(year):
            continue
        for chunk in year_payload.get("chunks", []):
            if batch_number is not None and int(chunk.get("batch_number", 0) or 0) != int(batch_number):
                continue
            receipt_path = _archive_receipt_path(root, tool_name, str(year_payload.get("year")), str(chunk.get("label")))
            receipt = _safe_load_json(receipt_path)
            if receipt.get("status") not in {"staged_for_review", "completed"}:
                target_chunk = (year_payload, chunk)
                break
        if target_chunk is not None:
            break

    if target_chunk is None:
        return {
            "staged": False,
            "reason": "no_available_batch",
            "execution_state": execution_state,
        }

    year_payload, chunk = target_chunk
    label = str(chunk.get("label"))
    receipt_path = _archive_receipt_path(root, tool_name, str(year_payload.get("year")), label)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "tool": tool_name,
        "year": str(year_payload.get("year")),
        "label": label,
        "batch_number": int(chunk.get("batch_number", 0) or 0),
        "status": "staged_for_review",
        "staged_at": datetime.now(timezone.utc).isoformat(),
        "start_ordinal": int(chunk.get("start_ordinal", 0) or 0),
        "end_ordinal": int(chunk.get("end_ordinal", 0) or 0),
        "target_manifest_path": chunk.get("target_manifest_path"),
        "archive_stub_path": chunk.get("archive_stub_path"),
        "non_destructive": True,
        "raw_run_deletion_allowed": False,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    state = write_archive_execution_state(root, tool_name=tool_name)
    return {
        "staged": True,
        "receipt_path": str(receipt_path),
        "receipt": receipt,
        "execution_state": state,
    }


def complete_archive_batch(
    root: Path,
    *,
    tool_name: str = "oracle_ingest_file",
    year: str | None = None,
    batch_number: int | None = None,
) -> dict:
    root = Path(root)
    execution_state = build_archive_execution_state(root, tool_name=tool_name)

    target = None
    for batch in execution_state.get("batches", []):
        if batch.get("status") != "staged_for_review":
            continue
        if year is not None and str(batch.get("year")) != str(year):
            continue
        if batch_number is not None and int(batch.get("batch_number", 0) or 0) != int(batch_number):
            continue
        target = batch
        break

    if target is None:
        return {
            "completed": False,
            "reason": "no_staged_batch",
            "execution_state": execution_state,
        }

    receipt_path = Path(str(target.get("receipt_path") or ""))
    receipt = _safe_load_json(receipt_path)
    receipt["status"] = "completed"
    receipt["completed_at"] = datetime.now(timezone.utc).isoformat()
    receipt["non_destructive"] = True
    receipt["raw_run_deletion_allowed"] = False
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    state = write_archive_execution_state(root, tool_name=tool_name)
    return {
        "completed": True,
        "receipt_path": str(receipt_path),
        "receipt": receipt,
        "execution_state": state,
    }


def complete_archive_batch(
    root: Path,
    *,
    tool_name: str = "oracle_ingest_file",
    year: str | None = None,
    batch_number: int | None = None,
    label: str | None = None,
    note: str | None = None,
) -> dict:
    root = Path(root)
    workflow = read_archive_workflow(root, tool_name=tool_name) or write_archive_workflow(root, tool_name=tool_name)
    _ = workflow  # workflow presence guarantees target structure exists
    executions_root = archive_execution_root(root, tool_name=tool_name)
    target_path: Path | None = None
    target_receipt: dict = {}

    if executions_root.exists():
        for receipt_path in sorted(executions_root.rglob("*.json")):
            receipt = _safe_load_json(receipt_path)
            if str(receipt.get("status") or "") != "staged_for_review":
                continue
            if label is not None and str(receipt.get("label") or "") != str(label):
                continue
            if year is not None and str(receipt.get("year") or "") != str(year):
                continue
            if batch_number is not None and int(receipt.get("batch_number", 0) or 0) != int(batch_number):
                continue
            target_path = receipt_path
            target_receipt = receipt
            break

    if target_path is None:
        state = write_archive_execution_state(root, tool_name=tool_name)
        return {
            "completed": False,
            "reason": "no_staged_batch",
            "execution_state": state,
        }

    target_receipt["status"] = "completed"
    target_receipt["completed_at"] = datetime.now(timezone.utc).isoformat()
    if note:
        target_receipt["completion_note"] = note
    target_path.write_text(json.dumps(target_receipt, indent=2), encoding="utf-8")
    state = write_archive_execution_state(root, tool_name=tool_name)
    return {
        "completed": True,
        "receipt_path": str(target_path),
        "receipt": target_receipt,
        "execution_state": state,
    }


def write_yearly_rollups(root: Path, output_dir: Path | None = None) -> dict:
    root = Path(root)
    summary = read_generated_data_summary(root) or build_generated_data_summary(root)
    output_root = output_dir or compaction_rollup_root(root)
    output_root.mkdir(parents=True, exist_ok=True)
    created: list[str] = []

    for tool_name, payload in sorted((summary.get("tools") or {}).items()):
        years = payload.get("years", {}) or {}
        samples = payload.get("sample_runs", []) or []
        tool_root = output_root / tool_name
        tool_root.mkdir(parents=True, exist_ok=True)
        for year, manifest_count in sorted(years.items()):
            rollup = {
                "tool": tool_name,
                "year": year,
                "manifest_count": manifest_count,
                "latest_run": payload.get("latest_run"),
                "sample_runs": samples[:3],
                "source_summary": str(default_summary_path(root)),
            }
            destination = tool_root / f"{year}.json"
            destination.write_text(json.dumps(rollup, indent=2), encoding="utf-8")
            created.append(str(destination))

    return {
        "output_root": str(output_root),
        "created_files": created,
        "tool_count": len(summary.get("tools", {}) or {}),
    }
