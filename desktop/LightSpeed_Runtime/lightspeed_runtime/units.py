from __future__ import annotations

import json
from pathlib import Path

from lightspeed_runtime.contracts import utc_now_iso
from lightspeed_runtime.storage_paths import datatables_root


ZONING_UNIT_SPEC = {
    "semi_major_axis": {"unit": "astronomical_unit", "dimension": "distance"},
    "eccentricity": {"unit": "dimensionless", "dimension": "ratio"},
    "inclination": {"unit": "degree", "dimension": "angle"},
    "diameter_km": {"unit": "kilometer", "dimension": "distance"},
    "density_proxy": {"unit": "g_cm3", "dimension": "density"},
    "metal_proxy": {"unit": "fraction", "dimension": "ratio"},
    "delta_v_proxy": {"unit": "km_s", "dimension": "velocity"},
    "synodic_period_days": {"unit": "day", "dimension": "time"},
    "moid": {"unit": "astronomical_unit", "dimension": "distance"},
    "accessibility_score": {"unit": "fraction", "dimension": "score"},
}

COLUMN_HINTS = {
    "semi_major_axis": ("astronomical_unit", "distance"),
    "semi_major_axis_au": ("astronomical_unit", "distance"),
    "a": ("astronomical_unit", "distance"),
    "moid": ("astronomical_unit", "distance"),
    "moid_au": ("astronomical_unit", "distance"),
    "eccentricity": ("dimensionless", "ratio"),
    "e": ("dimensionless", "ratio"),
    "inclination": ("degree", "angle"),
    "i": ("degree", "angle"),
    "diameter": ("kilometer", "distance"),
    "diameter_km": ("kilometer", "distance"),
    "density": ("g_cm3", "density"),
    "density_proxy": ("g_cm3", "density"),
    "delta_v": ("km_s", "velocity"),
    "delta_v_proxy": ("km_s", "velocity"),
    "synodic_period": ("day", "time"),
    "synodic_period_days": ("day", "time"),
    "metal_proxy": ("fraction", "ratio"),
    "accessibility_score": ("fraction", "score"),
}


def unit_validation_root(root: Path) -> Path:
    return datatables_root(root) / "validation"


def default_unit_validation_path(root: Path) -> Path:
    return unit_validation_root(root) / "unit_validation_report.json"


def read_unit_validation_report(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_unit_validation_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _normalize_column(column: str) -> str:
    return str(column or "").strip().lower().replace(" ", "_")


def infer_column_unit(column: str) -> dict:
    normalized = _normalize_column(column)
    if normalized in COLUMN_HINTS:
        unit, dimension = COLUMN_HINTS[normalized]
        return {"column": column, "expected_unit": unit, "dimension": dimension, "status": "known"}
    return {"column": column, "expected_unit": "unspecified", "dimension": "unknown", "status": "review"}


def summarize_zoning_units(records: list[dict]) -> dict:
    present_columns = sorted({str(key) for row in records[:25] for key in row.keys()})
    checks = []
    warnings = []
    for column, spec in ZONING_UNIT_SPEC.items():
        status = "present" if column in present_columns else "missing"
        checks.append(
            {
                "column": column,
                "expected_unit": spec["unit"],
                "dimension": spec["dimension"],
                "status": status,
            }
        )
        if status == "missing" and column in {"semi_major_axis", "eccentricity", "inclination"}:
            warnings.append(f"Missing critical zoning column: {column}")
    return {
        "observed_columns": present_columns,
        "checks": checks,
        "warnings": warnings,
        "summary": (
            f"Validated {len(present_columns)} observed zoning columns against "
            f"{len(ZONING_UNIT_SPEC)} expected scientific unit hints."
        ),
    }


def build_unit_validation_report(
    root: Path,
    *,
    empirical_catalog: dict | None = None,
    curated_tables: dict | None = None,
    scientific_query: dict | None = None,
) -> dict:
    root = Path(root)
    empirical_catalog = empirical_catalog or {}
    curated_tables = curated_tables or {}
    scientific_query = scientific_query or {}

    dataset_checks = []
    for item in scientific_query.get("queryables") or []:
        columns = list(item.get("columns") or [])
        unit_checks = [infer_column_unit(column) for column in columns]
        dataset_checks.append(
            {
                "query_name": item.get("query_name"),
                "source_id": item.get("source_id"),
                "source_label": item.get("source_label") or item.get("query_name"),
                "owner_floor": item.get("owner_floor") or "Oracle",
                "usage_role": item.get("usage_role") or item.get("canonical_role") or item.get("dataset_role"),
                "canonical_role": item.get("canonical_role"),
                "dataset_role": item.get("dataset_role"),
                "column_count": len(columns),
                "known_unit_count": sum(1 for check in unit_checks if check["status"] == "known"),
                "review_count": sum(1 for check in unit_checks if check["status"] != "known"),
                "validation_summary": f"{sum(1 for check in unit_checks if check['status'] == 'known')} known / {sum(1 for check in unit_checks if check['status'] != 'known')} review",
                "checks": unit_checks,
            }
        )

    table_checks = []
    for table in curated_tables.get("tables") or []:
        manifest_path = Path(str(table.get("manifest_path") or ""))
        manifest = {}
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                manifest = {}
        columns = list(manifest.get("columns") or [])
        table_checks.append(
            {
                "table_name": table.get("table_name"),
                "source_label": table.get("table_name"),
                "owner_floor": "Oracle",
                "usage_role": "curated_table",
                "column_count": len(columns),
                "checks": [infer_column_unit(column) for column in columns],
            }
        )

    return {
        "generated_at": utc_now_iso(),
        "unit_validation_path": str(default_unit_validation_path(root)),
        "dataset_count": len(dataset_checks),
        "table_count": len(table_checks),
        "datasets": dataset_checks,
        "tables": table_checks,
        "summary": (
            f"Unit validation coverage prepared for {len(dataset_checks)} mounted datasets and "
            f"{len(table_checks)} curated tables."
        ),
    }


def write_unit_validation_report(
    root: Path,
    *,
    empirical_catalog: dict | None = None,
    curated_tables: dict | None = None,
    scientific_query: dict | None = None,
    output_path: Path | None = None,
) -> dict:
    root = Path(root)
    destination = output_path or default_unit_validation_path(root)
    payload = build_unit_validation_report(
        root,
        empirical_catalog=empirical_catalog,
        curated_tables=curated_tables,
        scientific_query=scientific_query,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
