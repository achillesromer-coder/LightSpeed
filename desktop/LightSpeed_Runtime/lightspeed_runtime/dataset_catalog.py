from __future__ import annotations

import json
from pathlib import Path

from lightspeed_runtime.contracts import deterministic_id, utc_now_iso
from lightspeed_runtime.storage_paths import catalog_root


SOURCE_TYPE_FALLBACKS = {
    "dataset_bundle": "Mounted empirical dataset bundle.",
    "empirical_dataset_bundle": "Mounted empirical dataset bundle.",
    "document_bundle": "Mounted document bundle for doctrine and reference proofing.",
    "archive": "Historical reference bundle retained for search and provenance.",
}


def default_dataset_catalog_path(root: Path) -> Path:
    return catalog_root(root) / "dataset_catalog_shell.json"


def read_dataset_catalog_shell(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_dataset_catalog_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _keyword_tokens(record: dict) -> list[str]:
    tokens = {
        str(record.get("source_id") or "").strip(),
        str(record.get("source_label") or "").strip(),
        str(record.get("owner_floor") or "").strip(),
        str(record.get("usage_role") or "").strip(),
        str(record.get("dataset_role") or "").strip(),
        str(record.get("canonical_role") or "").strip(),
        str(record.get("asset_class") or "").strip(),
        str(record.get("source_type") or "").strip(),
        str(record.get("extension") or "").strip().lstrip("."),
    }
    relative_path = str(record.get("relative_path") or "")
    for part in relative_path.replace("\\", "/").split("/"):
        cleaned = part.replace("_", " ").replace("-", " ").strip()
        if cleaned:
            tokens.add(cleaned)
    return sorted(token for token in tokens if token)


def _guess_target_name(relative_path: str) -> str:
    lower = relative_path.lower()
    if "eros" in lower:
        return "Eros"
    if "psyche" in lower:
        return "Psyche"
    if "bennu" in lower:
        return "Bennu"
    if "didymos" in lower:
        return "Didymos"
    return "Unknown"


def _mission_refinement_profile(record: dict) -> dict:
    relative_path = str(record.get("relative_path") or "")
    lower = relative_path.lower()
    dataset_role = str(record.get("dataset_role") or "")
    is_refinement = dataset_role == "micro_validation" or any(
        token in lower for token in ("pds", "gravity", "shape", "harmonic", "eros", "psyche", "refinement")
    )
    if not is_refinement:
        return {}
    target_name = _guess_target_name(relative_path)
    return {
        "profile_type": "pds4_like",
        "processing_level": "refinement",
        "investigation_area": "planetary_science",
        "discipline_area": ["small_bodies", "geophysics", "resource_characterization"],
        "product_class": "Product_Observational" if record.get("asset_class") == "structured_dataset" else "Product_Ancillary",
        "target_identification": {
            "target_name": target_name,
            "target_type": "asteroid" if target_name != "Unknown" else "small_body",
        },
        "reference_type": "micro_validation",
        "required_fields": [
            "investigation_area",
            "discipline_area",
            "target_identification",
            "processing_level",
            "product_class",
        ],
    }


def _source_type_description(record: dict) -> str:
    source_type = str(record.get("source_type") or "").strip().lower()
    return str(record.get("source_type_definition") or SOURCE_TYPE_FALLBACKS.get(source_type) or "Mounted source bundle.")


def _distribution(record: dict) -> dict:
    extension = str(record.get("extension") or "").lstrip(".") or "bin"
    return {
        "title": str(record.get("relative_path") or record.get("title") or "dataset"),
        "format": extension,
        "href": str(record.get("absolute_path") or ""),
        "media_type": f"application/{extension}" if extension not in {"csv", "json", "txt"} else f"text/{extension}",
    }


def _query_access(record: dict, queryable_lookup: dict[str, dict], query_layer: dict) -> dict:
    queryable = queryable_lookup.get(str(record.get("absolute_path") or "")) or queryable_lookup.get(
        str(record.get("relative_path") or "")
    )
    if not queryable:
        return {}
    return {
        "protocol": "tap_like",
        "language": "sql_filter",
        "query_name": queryable.get("query_name"),
        "preferred_engine": query_layer.get("preferred_engine"),
        "supported_filter_ops": query_layer.get("supported_filter_ops") or ["eq", "contains", "gte", "lte"],
        "example": f"SELECT * FROM {queryable.get('query_name')} WHERE confidence_score >= 0.5 LIMIT 25",
    }


def build_dataset_catalog_shell(
    root: Path,
    *,
    empirical_catalog: dict | None = None,
    scientific_query: dict | None = None,
    entity_registry: dict | None = None,
) -> dict:
    root = Path(root)
    empirical_catalog = empirical_catalog or {}
    scientific_query = scientific_query or {}
    entity_registry = entity_registry or {}
    queryable_lookup = {}
    for item in scientific_query.get("queryables") or []:
        absolute_path = str(item.get("absolute_path") or "")
        relative_path = str(item.get("relative_path") or "")
        if absolute_path:
            queryable_lookup[absolute_path] = item
        if relative_path:
            queryable_lookup[relative_path] = item

    datasets = []
    mission_refinement_count = 0
    for record in empirical_catalog.get("dataset_table") or []:
        owner_floor = str(record.get("owner_floor") or "Oracle")
        usage_role = str(record.get("usage_role") or record.get("canonical_role") or record.get("dataset_role") or "reference")
        source_label = str(record.get("source_label") or record.get("source_id") or "dataset")
        title = (
            record.get("title")
            or record.get("label")
            or record.get("relative_path")
            or record.get("source_id")
            or "dataset"
        )
        metadata_profile = _mission_refinement_profile(record)
        if metadata_profile:
            mission_refinement_count += 1
        datasets.append(
            {
                "dataset_id": deterministic_id(
                    "dataset_catalog",
                    str(record.get("source_id") or ""),
                    str(record.get("relative_path") or ""),
                ),
                "title": str(title),
                "description": (
                    f"{usage_role} dataset owned by {owner_floor}; source {source_label} mounted at "
                    f"{record.get('relative_path')}."
                ),
                "catalog_profile": "stac_dcat_shell",
                "owner_floor": owner_floor,
                "usage_role": usage_role,
                "source_label": source_label,
                "source_id": record.get("source_id"),
                "source_type": record.get("source_type"),
                "source_type_definition": _source_type_description(record),
                "source_provenance_summary": (
                    f"{source_label} owned by {owner_floor}; {usage_role} records are cataloged for Oracle use."
                ),
                "relative_path": record.get("relative_path"),
                "absolute_path": record.get("absolute_path"),
                "asset_class": record.get("asset_class"),
                "dataset_role": record.get("dataset_role"),
                "canonical_role": record.get("canonical_role"),
                "keywords": _keyword_tokens(record),
                "themes": [
                    str(record.get("dataset_role") or ""),
                    str(record.get("canonical_role") or ""),
                    owner_floor,
                    usage_role,
                    str(record.get("asset_class") or ""),
                ],
                "validation": {
                    "confidence_score": record.get("confidence_score"),
                    "confidence_band": record.get("confidence_band"),
                    "uncertainty_summary": record.get("uncertainty_summary"),
                    "validation_state": record.get("validation_state", "review_ready"),
                },
                "query_access": _query_access(record, queryable_lookup, scientific_query),
                "distributions": [_distribution(record)],
                "metadata_profile": metadata_profile,
            }
        )

    dataset_entity_count = len(entity_registry.get("dataset_entities") or [])
    query_template_count = len(scientific_query.get("query_templates") or [])
    payload = {
        "generated_at": utc_now_iso(),
        "catalog_path": str(default_dataset_catalog_path(root)),
        "report_path": str(default_dataset_catalog_path(root)),
        "catalog_id": "oracle-dataset-catalog",
        "catalog_profile": "stac_dcat_shell",
        "profiles": ["DCAT-like", "STAC-like", "PDS4-like for mission refinement"],
        "dataset_count": len(datasets),
        "dataset_entity_count": dataset_entity_count,
        "mission_refinement_count": mission_refinement_count,
        "query_template_count": query_template_count,
        "datasets": datasets,
        "summary": (
            f"Oracle dataset catalog shell with {len(datasets)} datasets, "
            f"{mission_refinement_count} mission-refinement profiles, and {query_template_count} query templates."
        ),
    }
    return payload


def write_dataset_catalog_shell(
    root: Path,
    *,
    empirical_catalog: dict | None = None,
    scientific_query: dict | None = None,
    entity_registry: dict | None = None,
    output_path: Path | None = None,
) -> dict:
    root = Path(root)
    destination = output_path or default_dataset_catalog_path(root)
    payload = build_dataset_catalog_shell(
        root,
        empirical_catalog=empirical_catalog,
        scientific_query=scientific_query,
        entity_registry=entity_registry,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
