from __future__ import annotations

import csv
import json
from pathlib import Path

from lightspeed_runtime.contracts import utc_now_iso
from lightspeed_runtime.storage_paths import datatables_root

try:
    import duckdb  # type: ignore
except Exception:  # pragma: no cover - environment dependent
    duckdb = None

try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover - environment dependent
    pd = None


STRUCTURED_EXTENSIONS = {".json", ".jsonl", ".csv", ".tsv", ".ecsv"}


def scientific_query_root(root: Path) -> Path:
    return datatables_root(root) / "query"


def default_scientific_query_path(root: Path) -> Path:
    return scientific_query_root(root) / "scientific_query_layer.json"


def read_scientific_query_layer(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_scientific_query_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _available_engines() -> list[str]:
    engines = ["python"]
    if pd is not None:
        engines.insert(0, "pandas")
    if duckdb is not None:
        engines.insert(0, "duckdb")
    return engines


def _preferred_engine() -> str:
    return _available_engines()[0]


def _coerce_float(value) -> float | None:
    try:
        return float(str(value).replace(",", "").strip())
    except Exception:
        return None


def _read_csv_rows(path: Path, *, limit: int) -> list[dict]:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        rows = []
        for index, row in enumerate(reader):
            rows.append(dict(row))
            if index + 1 >= limit:
                break
    return rows


def _read_json_rows(path: Path, *, limit: int) -> list[dict]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(payload, list):
        return [item for item in payload[:limit] if isinstance(item, dict)]
    if isinstance(payload, dict):
        records = payload.get("records") or payload.get("items") or []
        if isinstance(records, list):
            return [item for item in records[:limit] if isinstance(item, dict)]
    return []


def _read_jsonl_rows(path: Path, *, limit: int) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
            if len(rows) >= limit:
                break
    return rows


def _read_rows(path: Path, *, limit: int = 50) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv", ".ecsv"}:
        return _read_csv_rows(path, limit=limit)
    if suffix == ".jsonl":
        return _read_jsonl_rows(path, limit=limit)
    if suffix == ".json":
        return _read_json_rows(path, limit=limit)
    return []


def _read_rows_duckdb(path: Path, *, limit: int = 50) -> list[dict]:
    if duckdb is None:
        return []
    suffix = path.suffix.lower()
    if suffix not in STRUCTURED_EXTENSIONS:
        return []
    connection = duckdb.connect(database=":memory:")
    try:
        if suffix in {".csv", ".ecsv"}:
            query = "SELECT * FROM read_csv_auto(?) LIMIT ?"
            cursor = connection.execute(query, [str(path), limit])
        elif suffix == ".tsv":
            query = "SELECT * FROM read_csv_auto(?, delim='\t') LIMIT ?"
            cursor = connection.execute(query, [str(path), limit])
        else:
            query = "SELECT * FROM read_json_auto(?) LIMIT ?"
            cursor = connection.execute(query, [str(path), limit])
        columns = [item[0] for item in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    except Exception:
        return []
    finally:
        connection.close()


def _sample_columns(rows: list[dict]) -> list[str]:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                columns.append(str(key))
    return columns


def _queryable_dataset_records(empirical_catalog: dict) -> list[dict]:
    rows = empirical_catalog.get("dataset_table") or []
    queryables: list[dict] = []
    for item in rows:
        path = Path(str(item.get("absolute_path") or ""))
        if not path.exists() or not path.is_file() or path.suffix.lower() not in STRUCTURED_EXTENSIONS:
            continue
        sample_rows = _read_rows(path, limit=12)
        queryables.append(
            {
                "dataset_key": f"{item.get('source_id')}::{item.get('relative_path')}",
                "source_id": item.get("source_id"),
                "source_label": item.get("source_label") or item.get("source_id"),
                "owner_floor": item.get("owner_floor") or "Oracle",
                "usage_role": item.get("usage_role") or item.get("canonical_role") or item.get("dataset_role"),
                "relative_path": item.get("relative_path"),
                "absolute_path": str(path),
                "dataset_role": item.get("dataset_role"),
                "canonical_role": item.get("canonical_role"),
                "asset_class": item.get("asset_class"),
                "query_name": path.stem,
                "columns": _sample_columns(sample_rows),
                "sample_row_count": len(sample_rows),
                "sample_rows": sample_rows[:5],
            }
        )
        if len(queryables) >= 48:
            break
    return queryables


def _curated_views(curated_tables: dict) -> list[dict]:
    views: list[dict] = []
    for table in curated_tables.get("tables") or []:
        manifest_path = Path(str(table.get("manifest_path") or ""))
        manifest = {}
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                manifest = {}
        views.append(
            {
                "table_name": table.get("table_name"),
                "manifest_path": str(manifest_path),
                "row_count": int(table.get("row_count", 0) or 0),
                "columns": list(manifest.get("columns") or []),
                "actual_format": table.get("actual_format"),
                "csv_path": table.get("csv_path"),
                "json_path": table.get("json_path"),
                "parquet_path": table.get("parquet_path"),
            }
        )
    return views


def _query_templates(queryables: list[dict], curated_views: list[dict]) -> list[dict]:
    templates: list[dict] = []
    if curated_views:
        first_view = curated_views[0]
        templates.append(
            {
                "template_id": "tap_like_curated_review",
                "protocol": "tap_like",
                "language": "sql_filter",
                "target": first_view.get("table_name"),
                "example": f"SELECT * FROM {first_view.get('table_name')} WHERE confidence_score >= 0.5 LIMIT 25",
                "filters": [{"column": "confidence_score", "op": "gte", "value": 0.5}],
            }
        )
    if queryables:
        first = queryables[0]
        templates.append(
            {
                "template_id": "tap_like_dataset_lookup",
                "protocol": "tap_like",
                "language": "sql_filter",
                "target": first.get("query_name"),
                "example": f"SELECT * FROM {first.get('query_name')} WHERE name CONTAINS 'Psy' LIMIT 25",
                "filters": [{"column": "name", "op": "contains", "value": "Psy"}],
            }
        )
    return templates


def build_scientific_query_layer(
    root: Path,
    *,
    empirical_catalog: dict | None = None,
    curated_tables: dict | None = None,
) -> dict:
    root = Path(root)
    empirical_catalog = empirical_catalog or {}
    curated_tables = curated_tables or {}
    queryables = _queryable_dataset_records(empirical_catalog)
    curated_views = _curated_views(curated_tables)
    named_views = [
        {"view_name": item.get("table_name"), "source": "curated_table"}
        for item in curated_views
    ]
    named_views.extend(
        {"view_name": item.get("query_name"), "source": "mounted_dataset"}
        for item in queryables
    )
    query_templates = _query_templates(queryables, curated_views)
    return {
        "generated_at": utc_now_iso(),
        "query_layer_path": str(default_scientific_query_path(root)),
        "report_path": str(default_scientific_query_path(root)),
        "preferred_engine": _preferred_engine(),
        "available_engines": _available_engines(),
        "query_protocol": "tap_like",
        "query_language": "sql_filter",
        "supported_filter_ops": ["eq", "contains", "gte", "lte"],
        "queryable_count": len(queryables),
        "curated_view_count": len(curated_views),
        "queryables": queryables,
        "curated_views": curated_views,
        "named_views": named_views,
        "query_templates": query_templates,
        "summary": (
            f"Curated-first scientific query layer with {len(curated_views)} curated views and "
            f"{len(queryables)} mounted datasets. Preferred engine: {_preferred_engine()}."
        ),
    }


def write_scientific_query_layer(
    root: Path,
    *,
    empirical_catalog: dict | None = None,
    curated_tables: dict | None = None,
    output_path: Path | None = None,
) -> dict:
    root = Path(root)
    destination = output_path or default_scientific_query_path(root)
    payload = build_scientific_query_layer(
        root,
        empirical_catalog=empirical_catalog,
        curated_tables=curated_tables,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _apply_filters(rows: list[dict], filters: list[dict] | None = None) -> list[dict]:
    if not filters:
        return rows
    matched = rows
    for item in filters:
        column = str(item.get("column") or "")
        op = str(item.get("op") or "eq")
        value = item.get("value")
        if not column:
            continue
        if op == "contains":
            matched = [row for row in matched if str(value).lower() in str(row.get(column, "")).lower()]
        elif op == "gte":
            matched = [
                row
                for row in matched
                if _coerce_float(row.get(column)) is not None and _coerce_float(row.get(column)) >= _coerce_float(value)
            ]
        elif op == "lte":
            matched = [
                row
                for row in matched
                if _coerce_float(row.get(column)) is not None and _coerce_float(row.get(column)) <= _coerce_float(value)
            ]
        else:
            matched = [row for row in matched if str(row.get(column)) == str(value)]
    return matched


def execute_scientific_query(
    root: Path,
    *,
    table_name: str,
    limit: int = 25,
    filters: list[dict] | None = None,
    columns: list[str] | None = None,
    query_layer: dict | None = None,
) -> dict:
    root = Path(root)
    query_layer = query_layer or read_scientific_query_layer(root)
    source_path = ""
    source_kind = ""
    for view in query_layer.get("curated_views") or []:
        if str(view.get("table_name") or "") == table_name:
            source_path = str(view.get("json_path") or view.get("csv_path") or "")
            source_kind = "curated_view"
            break
    if not source_path:
        for item in query_layer.get("queryables") or []:
            if str(item.get("query_name") or "") == table_name:
                source_path = str(item.get("absolute_path") or "")
                source_kind = "mounted_dataset"
                break
    if not source_path:
        raise KeyError(f"Unknown scientific table: {table_name}")

    source = Path(source_path)
    source_label = table_name
    owner_floor = "Oracle"
    usage_role = "simulation_input"
    if source_kind == "curated_view":
        owner_floor = "Oracle"
        usage_role = "curated_table"
    for view in query_layer.get("curated_views") or []:
        if str(view.get("table_name") or "") == table_name:
            source_label = str(view.get("table_name") or table_name)
            break
    for item in query_layer.get("queryables") or []:
        if str(item.get("query_name") or "") == table_name:
            source_label = str(item.get("source_label") or item.get("query_name") or table_name)
            owner_floor = str(item.get("owner_floor") or "Oracle")
            usage_role = str(item.get("usage_role") or item.get("canonical_role") or item.get("dataset_role") or "simulation_input")
            break
    rows = _read_rows_duckdb(source, limit=max(limit * 4, 50))
    if not rows:
        rows = _read_rows(source, limit=max(limit * 4, 50))
    rows = _apply_filters(rows, filters=filters)
    if columns:
        rows = [{key: row.get(key) for key in columns} for row in rows]
    rows = rows[:limit]
    return {
        "table_name": table_name,
        "source_kind": source_kind,
        "source_label": source_label,
        "owner_floor": owner_floor,
        "usage_role": usage_role,
        "source_path": source_path,
        "source_provenance_links": [
            {
                "label": "source record",
                "path": source_path,
                "source_kind": source_kind,
            }
        ],
        "provenance_links": [
            {
                "label": "source record",
                "path": source_path,
                "source_kind": source_kind,
            }
        ],
        "engine": _preferred_engine(),
        "matched_count": len(rows),
        "columns": _sample_columns(rows),
        "rows": rows,
        "summary": f"{source_label} ({source_kind}, {usage_role}) returned {len(rows)} row(s).",
        "provenance_summary": f"{owner_floor} owns {source_label}; see provenance links for the source record.",
    }


def execute_tap_like_query(
    root: Path,
    *,
    request: dict,
    query_layer: dict | None = None,
) -> dict:
    table_name = str(request.get("from") or request.get("table_name") or "")
    if not table_name:
        raise ValueError("tap-like query request requires a target table or view.")
    filters = request.get("where") or request.get("filters") or []
    columns = request.get("select") or request.get("columns")
    limit = int(request.get("limit") or 25)
    result = execute_scientific_query(
        root,
        table_name=table_name,
        limit=limit,
        filters=filters,
        columns=columns,
        query_layer=query_layer,
    )
    result["protocol"] = "tap_like"
    result["request"] = {
        "from": table_name,
        "select": columns or ["*"],
        "where": filters,
        "limit": limit,
    }
    return result
