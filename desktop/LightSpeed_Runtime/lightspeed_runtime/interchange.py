from __future__ import annotations

import json
from pathlib import Path

from lightspeed_runtime.contracts import utc_now_iso
from lightspeed_runtime.storage_paths import datatables_root


def default_columnar_handoff_path(root: Path) -> Path:
    return datatables_root(root) / "curated" / "columnar_handoff_bundle.json"


def read_columnar_handoff(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_columnar_handoff_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _columnarize(rows: list[dict]) -> tuple[list[str], dict[str, list]]:
    if not rows:
        return [], {}
    columns = list(rows[0].keys())
    return columns, {column: [row.get(column) for row in rows] for column in columns}


def build_columnar_handoff(root: Path, *, empirical_catalog: dict | None = None, knowns_registry: dict | None = None) -> dict:
    empirical_catalog = empirical_catalog or {}
    knowns_registry = knowns_registry or {}

    dataset_rows = list(empirical_catalog.get("dataset_table") or [])[:40]
    theme_rows = [
        {
            "theme_key": item.get("theme_key"),
            "title": item.get("title"),
            "category": item.get("category"),
            "consensus_band": item.get("consensus_band"),
            "match_count": item.get("match_count", 0),
        }
        for item in (knowns_registry.get("themes") or [])[:20]
    ]
    tables = []
    for name, rows in (
        ("empirical_dataset_table", dataset_rows),
        ("knowns_theme_table", theme_rows),
    ):
        columns, columnar_data = _columnarize(rows)
        tables.append(
            {
                "table_name": name,
                "row_count": len(rows),
                "columns": columns,
                "columnar_data": columnar_data,
            }
        )
    return {
        "generated_at": utc_now_iso(),
        "bundle_path": str(default_columnar_handoff_path(Path(root))),
        "table_count": len(tables),
        "tables": tables,
        "summary": "Columnar handoff bundle for Oracle, Neo, and TheConstruct structured exchange.",
    }


def write_columnar_handoff(root: Path, *, empirical_catalog: dict | None = None, knowns_registry: dict | None = None, output_path: Path | None = None) -> dict:
    destination = output_path or default_columnar_handoff_path(Path(root))
    payload = build_columnar_handoff(
        Path(root),
        empirical_catalog=empirical_catalog,
        knowns_registry=knowns_registry,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
