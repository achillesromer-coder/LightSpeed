from __future__ import annotations

import json
from pathlib import Path

from lightspeed_runtime.contracts import validate_contract_payload, utc_now_iso
from lightspeed_runtime.storage_paths import datatables_root

try:
    import pandas as pd
except Exception:  # pragma: no cover - optional dependency
    pd = None

try:
    import pandera as pa
except Exception:  # pragma: no cover - optional dependency
    pa = None


def validation_root(root: Path) -> Path:
    return datatables_root(root) / "validation"


def analytics_root(root: Path) -> Path:
    return datatables_root(root) / "analytics"


def default_table_validation_report_path(root: Path) -> Path:
    return validation_root(root) / "table_validation_report.json"


def default_bellcurve_overlay_path(root: Path) -> Path:
    return analytics_root(root) / "bellcurve_overlay.json"


def _load_rows(table: dict) -> list[dict]:
    json_path = Path(str(table.get("json_path") or ""))
    if not json_path.exists():
        return []
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _manual_table_check(table_name: str, rows: list[dict]) -> dict:
    required = {
        "empirical_dataset_table": {"title", "source_id", "confidence_score", "uncertainty_summary"},
        "knowns_theme_table": {"title", "category", "confidence_score", "uncertainty_summary"},
    }.get(table_name, set())
    columns = set(rows[0].keys()) if rows else set(required)
    missing = sorted(required - columns)
    confidence_range_errors = 0
    for row in rows:
        score = row.get("confidence_score")
        try:
            value = float(score)
            if value < 0.0 or value > 1.0:
                confidence_range_errors += 1
        except Exception:
            confidence_range_errors += 1
    success = not missing and confidence_range_errors == 0
    return {
        "table_name": table_name,
        "engine": "python_fallback",
        "success": success,
        "row_count": len(rows),
        "missing_columns": missing,
        "confidence_range_errors": confidence_range_errors,
        "summary": (
            f"{table_name} validated with fallback checks."
            if success
            else f"{table_name} has missing columns or invalid confidence scores."
        ),
    }


def _pandera_table_check(table_name: str, rows: list[dict]) -> dict:
    if pa is None or pd is None:
        return _manual_table_check(table_name, rows)
    if table_name == "empirical_dataset_table":
        schema = pa.DataFrameSchema(
            {
                "title": pa.Column(str),
                "source_id": pa.Column(str),
                "confidence_score": pa.Column(float, checks=pa.Check.in_range(0.0, 1.0)),
                "uncertainty_summary": pa.Column(str),
            },
            coerce=True,
            strict=False,
        )
    elif table_name == "knowns_theme_table":
        schema = pa.DataFrameSchema(
            {
                "title": pa.Column(str),
                "category": pa.Column(str),
                "confidence_score": pa.Column(float, checks=pa.Check.in_range(0.0, 1.0)),
                "uncertainty_summary": pa.Column(str),
            },
            coerce=True,
            strict=False,
        )
    else:
        return _manual_table_check(table_name, rows)
    try:
        frame = pd.DataFrame(rows) if rows else pd.DataFrame(columns=list(schema.columns.keys()))
        schema.validate(frame)
        return {
            "table_name": table_name,
            "engine": "pandera",
            "success": True,
            "row_count": len(rows),
            "missing_columns": [],
            "confidence_range_errors": 0,
            "summary": f"{table_name} validated with Pandera schema checks.",
        }
    except Exception as exc:
        return {
            "table_name": table_name,
            "engine": "pandera",
            "success": False,
            "row_count": len(rows),
            "missing_columns": [],
            "confidence_range_errors": 1,
            "summary": str(exc),
        }


def build_table_validation_report(root: Path, *, curated_tables: dict | None = None) -> dict:
    root = Path(root)
    curated_tables = curated_tables or {}
    tables = []
    for table in curated_tables.get("tables") or []:
        table_name = str(table.get("table_name") or "")
        rows = _load_rows(table)
        result = _pandera_table_check(table_name, rows)
        result["path"] = table.get("manifest_path")
        tables.append(result)
    return {
        "generated_at": utc_now_iso(),
        "report_path": str(default_table_validation_report_path(root)),
        "table_count": len(tables),
        "passed_count": sum(1 for item in tables if item.get("success")),
        "failed_count": sum(1 for item in tables if not item.get("success")),
        "engine": "pandera" if pa is not None and pd is not None else "python_fallback",
        "tables": tables,
        "summary": f"Validated {len(tables)} curated table(s) for confidence and uncertainty readiness.",
    }


def write_table_validation_report(root: Path, *, curated_tables: dict | None = None, output_path: Path | None = None) -> dict:
    root = Path(root)
    destination = output_path or default_table_validation_report_path(root)
    payload = build_table_validation_report(root, curated_tables=curated_tables)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _histogram(values: list[float]) -> list[dict]:
    bins = [(0.0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 1.01)]
    results = []
    for start, end in bins:
        count = sum(1 for value in values if start <= value < end)
        results.append({"start": start, "end": min(end, 1.0), "count": count})
    return results


def build_bellcurve_overlay(root: Path, *, curated_tables: dict | None = None, knowns_registry: dict | None = None) -> dict:
    root = Path(root)
    curated_tables = curated_tables or {}
    knowns_registry = knowns_registry or {}
    datasets = []
    themes = []
    for table in curated_tables.get("tables") or []:
        table_name = str(table.get("table_name") or "")
        rows = _load_rows(table)
        if table_name == "empirical_dataset_table":
            datasets = rows
        elif table_name == "knowns_theme_table":
            themes = rows
    dataset_scores = [float(item.get("confidence_score", 0.0) or 0.0) for item in datasets]
    theme_scores = [float(item.get("confidence_score", 0.0) or 0.0) for item in themes]
    bellcurve = knowns_registry.get("bellcurve_overlay", {}) or {}
    return {
        "generated_at": utc_now_iso(),
        "overlay_path": str(default_bellcurve_overlay_path(root)),
        "dataset_confidence_histogram": _histogram(dataset_scores),
        "theme_confidence_histogram": _histogram(theme_scores),
        "knowns_center_of_gravity": bellcurve.get("center_of_gravity", []),
        "knowns_center_count": len(bellcurve.get("center", []) or []),
        "knowns_edge_count": len(bellcurve.get("edge", []) or []),
        "summary": "Reusable bell-curve and confidence overlays generated for curated datasets and doctrine themes.",
    }


def write_bellcurve_overlay(root: Path, *, curated_tables: dict | None = None, knowns_registry: dict | None = None, output_path: Path | None = None) -> dict:
    root = Path(root)
    destination = output_path or default_bellcurve_overlay_path(root)
    payload = build_bellcurve_overlay(root, curated_tables=curated_tables, knowns_registry=knowns_registry)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build_publish_checkpoint(
    *,
    manifest: dict,
    latest_runs: list[dict],
    metadata: dict | None = None,
    table_validation: dict | None = None,
) -> dict:
    checks = []
    checks.append({"name": "workspace_id_present", "success": bool(manifest.get("workspace_id"))})
    checks.append({"name": "project_id_present", "success": bool(manifest.get("project_id"))})
    checks.append({"name": "summary_blocks_present", "success": bool(manifest.get("summary_blocks"))})
    checks.append({"name": "latest_runs_present", "success": bool(latest_runs)})
    checks.append(
        {
            "name": "table_validation_passed",
            "success": bool((table_validation or {}).get("failed_count", 0) == 0),
        }
    )
    checks.append({"name": "metadata_attached", "success": metadata is not None})
    success_count = sum(1 for item in checks if item["success"])
    status = "passed" if success_count == len(checks) else "failed"
    contract_validation = validate_contract_payload("publish_manifest", manifest)
    return {
        "generated_at": utc_now_iso(),
        "engine": "great_expectations" if False else "python_checkpoint",
        "status": status,
        "expectation_count": len(checks),
        "success_count": success_count,
        "checks": checks,
        "contract_validation": contract_validation,
        "summary": f"Publish checkpoint {status} with {success_count}/{len(checks)} expectations satisfied.",
    }
