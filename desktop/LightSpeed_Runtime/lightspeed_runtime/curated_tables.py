from __future__ import annotations

import json
from pathlib import Path

from lightspeed_runtime.contracts import utc_now_iso
from lightspeed_runtime.storage_paths import datatables_root

try:
    import pandas as pd
except Exception:  # pragma: no cover - environment dependent
    pd = None


def curated_tables_root(root: Path) -> Path:
    return datatables_root(root) / "curated"


def default_curated_tables_index_path(root: Path) -> Path:
    return curated_tables_root(root) / "curated_tables_index.json"


def read_curated_tables_index(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_curated_tables_index_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_csv(path: Path, rows: list[dict]) -> None:
    if pd is not None:
        pd.DataFrame(rows).to_csv(path, index=False)
        return
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    headers = list(rows[0].keys())
    lines = [",".join(headers)]
    for row in rows:
        values = [str(row.get(header, "")).replace(",", ";") for header in headers]
        lines.append(",".join(values))
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_table_bundle(root: Path, table_name: str, rows: list[dict], summary: str) -> dict:
    table_root = curated_tables_root(root)
    table_root.mkdir(parents=True, exist_ok=True)
    csv_path = table_root / f"{table_name}.csv"
    json_path = table_root / f"{table_name}.json"
    parquet_path = table_root / f"{table_name}.parquet"
    manifest_path = table_root / f"{table_name}.manifest.json"

    _write_csv(csv_path, rows)
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    actual_format = "csv"
    parquet_available = False
    fallback_reason = "parquet_engine_unavailable"
    if pd is not None:
        try:
            pd.DataFrame(rows).to_parquet(parquet_path, index=False)
            parquet_available = True
            actual_format = "parquet"
            fallback_reason = ""
        except Exception:
            parquet_available = False

    manifest = {
        "generated_at": utc_now_iso(),
        "table_name": table_name,
        "row_count": len(rows),
        "column_count": len(rows[0].keys()) if rows else 0,
        "columns": list(rows[0].keys()) if rows else [],
        "confidence_columns": [key for key in (rows[0].keys() if rows else []) if "confidence" in key],
        "uncertainty_columns": [key for key in (rows[0].keys() if rows else []) if "uncertainty" in key],
        "preferred_format": "parquet",
        "actual_format": actual_format,
        "parquet_available": parquet_available,
        "fallback_reason": fallback_reason,
        "csv_path": str(csv_path),
        "json_path": str(json_path),
        "parquet_path": str(parquet_path) if parquet_available else None,
        "summary": summary,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {
        "table_name": table_name,
        "manifest_path": str(manifest_path),
        "row_count": manifest["row_count"],
        "actual_format": actual_format,
        "preferred_format": "parquet",
        "csv_path": str(csv_path),
        "json_path": str(json_path),
        "parquet_path": manifest["parquet_path"],
        "fallback_reason": fallback_reason,
    }


def _safe_float(value: object, fallback: float = 0.5) -> float:
    try:
        return float(value)
    except Exception:
        return fallback


def _confidence_band(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def _dataset_uncertainty_summary(item: dict) -> str:
    dataset_role = str(item.get("dataset_role") or "general_empirical")
    asset_class = str(item.get("asset_class") or "")
    if dataset_role == "micro_validation":
        return "low_for_refinement"
    if dataset_role == "macro_mapping":
        return "medium_for_target_screening"
    if asset_class == "structured_dataset":
        return "moderate"
    return "high"


def _build_dataset_rows(empirical_catalog: dict) -> list[dict]:
    rows = []
    for item in empirical_catalog.get("dataset_table") or []:
        record = dict(item)
        title = (
            record.get("title")
            or record.get("label")
            or record.get("relative_path")
            or record.get("source_id")
            or "dataset"
        )
        priority = int(record.get("priority", 0) or 0)
        confidence_score = max(0.0, min(1.0, 0.35 + (priority * 0.1)))
        record["title"] = str(title)
        record["confidence_score"] = round(confidence_score, 3)
        record["confidence_band"] = _confidence_band(confidence_score)
        record["uncertainty_summary"] = _dataset_uncertainty_summary(record)
        record["validation_state"] = "review_ready" if confidence_score >= 0.55 else "needs_review"
        rows.append(record)
    return rows


def _build_theme_rows(knowns_registry: dict) -> list[dict]:
    rows = []
    for item in knowns_registry.get("themes", []) or []:
        support = len(item.get("support_document_paths") or [])
        evidence = len(item.get("evidence") or [])
        score = max(0.0, min(1.0, 0.25 + support * 0.08 + evidence * 0.04))
        rows.append(
            {
                "theme_id": item.get("theme_id"),
                "title": item.get("title"),
                "category": item.get("category"),
                "consensus_band": item.get("consensus_band"),
                "match_count": item.get("match_count", 0),
                "support_count": support,
                "evidence_count": evidence,
                "confidence_score": round(score, 3),
                "confidence_band": _confidence_band(score),
                "uncertainty_summary": "lower_with_more_support" if support >= 2 else "higher_due_to_sparse_support",
                "summary": item.get("summary"),
            }
        )
    return rows


def build_curated_tables_index(root: Path, *, empirical_catalog: dict | None = None, knowns_registry: dict | None = None) -> dict:
    root = Path(root)
    empirical_catalog = empirical_catalog or {}
    knowns_registry = knowns_registry or {}

    dataset_rows = _build_dataset_rows(empirical_catalog)
    theme_rows = _build_theme_rows(knowns_registry)

    tables = [
        _write_table_bundle(
            root,
            "empirical_dataset_table",
            dataset_rows,
            "Curated analytical table for empirical dataset selection and simulation handoff.",
        ),
        _write_table_bundle(
            root,
            "knowns_theme_table",
            theme_rows,
            "Curated analytical table for doctrine and knowns theme review.",
        ),
    ]
    payload = {
        "generated_at": utc_now_iso(),
        "index_path": str(default_curated_tables_index_path(root)),
        "table_count": len(tables),
        "tables": tables,
        "confidence_enabled": True,
        "uncertainty_enabled": True,
        "summary": "Curated analytical tables written for Oracle-owned datatable use with parquet-preferred export semantics.",
    }
    return payload


def write_curated_tables_index(root: Path, *, empirical_catalog: dict | None = None, knowns_registry: dict | None = None, output_path: Path | None = None) -> dict:
    root = Path(root)
    destination = output_path or default_curated_tables_index_path(root)
    payload = build_curated_tables_index(root, empirical_catalog=empirical_catalog, knowns_registry=knowns_registry)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
