from __future__ import annotations

import json
from pathlib import Path

from lightspeed_runtime.contracts import ReservoirManifest, normalize_dataset_role, utc_now_iso
from lightspeed_runtime.storage_paths import library_root


STRUCTURED_EXTENSIONS = {".json", ".jsonl", ".csv", ".tsv", ".xlsx", ".xls", ".parquet"}
MODEL_EXTENSIONS = {".obj", ".stl", ".glb", ".gltf", ".ply", ".dae"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
DOCUMENT_EXTENSIONS = {".pdf", ".md", ".txt", ".doc", ".docx"}
ARCHIVE_EXTENSIONS = {".zip", ".7z", ".rar"}
PRIORITY_MARKERS = (
    "asteroid_strategic_mapping_base_withrocks",
    "asteroids.json",
    "asteroid_mining_concepts",
    "virtual_solar_map",
    "near_a_nlr",
    "hay_a_lidar",
    "eros",
    "bennu",
    "ola_data",
)

SOURCE_TYPE_DEFINITIONS = {
    "dataset_bundle": {
        "source_type_definition": "Mounted bundle of structured empirical datasets and companion reference material.",
        "operator_notes": "Prefer Oracle proofing before reuse in datatables or scenario work.",
        "fallback_description": "Mounted empirical dataset bundle.",
    },
    "empirical_dataset_bundle": {
        "source_type_definition": "Mounted bundle of empirical assets used for cataloging, proofing, and scenario work.",
        "operator_notes": "Keep the bundle mounted and condense only reusable records.",
        "fallback_description": "Mounted empirical dataset bundle.",
    },
    "document_bundle": {
        "source_type_definition": "Document-centered source bundle containing doctrine, notes, or reference prose.",
        "operator_notes": "Proof into knowns or library entries before broad reuse.",
        "fallback_description": "Mounted document bundle.",
    },
    "archive": {
        "source_type_definition": "Historical or non-authoritative material retained for search and provenance.",
        "operator_notes": "Keep searchable as reference only unless proofed into active knowledge.",
        "fallback_description": "Archived reference source.",
    },
}


def _source_type_details(source_type: str) -> dict:
    key = str(source_type or "").strip().lower()
    return SOURCE_TYPE_DEFINITIONS.get(
        key,
        {
            "source_type_definition": "Mounted source with no stronger source-type contract yet.",
            "operator_notes": "Treat as reference evidence until Oracle proofing adds a stronger contract.",
            "fallback_description": "Mounted source bundle.",
        },
    )


def default_empirical_catalog_path(root: Path) -> Path:
    return library_root(root) / "empirical" / "empirical_catalog.json"


def read_empirical_catalog(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_empirical_catalog_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _manifest_text(manifest: ReservoirManifest) -> str:
    bits = [
        manifest.source_id,
        manifest.source_type,
        manifest.classification,
        manifest.floor_owner,
        " ".join(manifest.workspace_tags),
        " ".join(manifest.project_tags),
        " ".join(manifest.trusted_documents),
    ]
    return " ".join(bit for bit in bits if bit).lower()


def _is_empirical_source(manifest: ReservoirManifest) -> bool:
    text = _manifest_text(manifest)
    return any(marker in text for marker in ("empirical", "asteroid", "solar system", "physicslab", "gmat"))


def _asset_class(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in STRUCTURED_EXTENSIONS:
        return "structured_dataset"
    if suffix in MODEL_EXTENSIONS:
        return "model_asset"
    if suffix in IMAGE_EXTENSIONS:
        return "image_asset"
    if suffix in DOCUMENT_EXTENSIONS:
        return "document_asset"
    if suffix in ARCHIVE_EXTENSIONS:
        return "archive_asset"
    return "other_asset"


def _priority(relative_path: str, asset_class: str) -> int:
    name = relative_path.lower().replace("\\", "/")
    score = 0
    if asset_class == "structured_dataset":
        score += 120
    elif asset_class == "document_asset":
        score += 60
    elif asset_class == "model_asset":
        score += 40
    elif asset_class == "image_asset":
        score += 20
    for idx, marker in enumerate(PRIORITY_MARKERS):
        if marker in name:
            score += 200 - idx
    return score


def _dataset_role(relative_path: str, asset_class: str) -> str:
    name = relative_path.lower().replace("\\", "/")
    if any(marker in name for marker in ("rocks", "sbdb", "mpc", "asteroids", "strategic_mapping")):
        return "macro_mapping"
    if any(
        marker in name
        for marker in ("eros", "bennu", "hayabusa", "near", "ola", "lidar", "shape", "gravity", "harmonic")
    ):
        return "micro_validation"
    if asset_class == "model_asset":
        return "simulation_model"
    if asset_class == "image_asset":
        return "reference_imagery"
    if asset_class == "document_asset":
        return "mission_reference"
    return "general_empirical"


def _canonical_role(dataset_role: str, asset_class: str) -> str:
    if dataset_role in {"macro_mapping", "micro_validation", "reference_imagery", "mission_reference"}:
        return normalize_dataset_role("reference")
    if asset_class in {"structured_dataset", "model_asset"}:
        return normalize_dataset_role("simulation_input")
    return normalize_dataset_role("reference")


def build_empirical_catalog(
    root: Path,
    manifests: list[ReservoirManifest],
    *,
    max_highlights_per_source: int = 24,
) -> dict:
    root = Path(root)
    selected = [manifest for manifest in manifests if _is_empirical_source(manifest)]
    sources: list[dict] = []
    highlighted_assets: list[dict] = []
    dataset_table: list[dict] = []
    headline_knowns: list[dict] = []
    class_totals: dict[str, int] = {}
    extension_totals: dict[str, int] = {}
    role_totals: dict[str, int] = {}
    canonical_role_totals: dict[str, int] = {}
    total_files = 0

    for manifest in selected:
        source_root = Path(manifest.root_path)
        if not source_root.exists():
            continue
        source_type_details = _source_type_details(manifest.source_type)
        owner_floor = manifest.floor_owner or "Oracle"

        source_class_counts: dict[str, int] = {}
        source_extension_counts: dict[str, int] = {}
        candidates: list[dict] = []
        file_count = 0

        for path in sorted(item for item in source_root.rglob("*") if item.is_file()):
            file_count += 1
            total_files += 1
            asset_class = _asset_class(path)
            rel = str(path.relative_to(source_root))
            suffix = path.suffix.lower() or "<none>"
            source_class_counts[asset_class] = source_class_counts.get(asset_class, 0) + 1
            source_extension_counts[suffix] = source_extension_counts.get(suffix, 0) + 1
            class_totals[asset_class] = class_totals.get(asset_class, 0) + 1
            extension_totals[suffix] = extension_totals.get(suffix, 0) + 1
            dataset_role = _dataset_role(rel, asset_class)
            canonical_role = _canonical_role(dataset_role, asset_class)
            role_totals[dataset_role] = role_totals.get(dataset_role, 0) + 1
            canonical_role_totals[canonical_role] = canonical_role_totals.get(canonical_role, 0) + 1

            score = _priority(rel, asset_class)
            if asset_class in {"structured_dataset", "document_asset", "model_asset"} or score >= 200:
                record = {
                    "source_id": manifest.source_id,
                    "source_label": manifest.source_id,
                    "owner_floor": owner_floor,
                    "source_type": manifest.source_type,
                    "source_type_definition": source_type_details["source_type_definition"],
                    "operator_notes": source_type_details["operator_notes"],
                    "relative_path": rel,
                    "absolute_path": str(path),
                    "asset_class": asset_class,
                    "dataset_role": dataset_role,
                    "usage_role": canonical_role,
                    "canonical_role": canonical_role,
                    "extension": suffix,
                    "size_bytes": path.stat().st_size,
                    "priority": score,
                }
                candidates.append(record)
                if asset_class == "structured_dataset":
                    dataset_table.append(record)

        candidates.sort(key=lambda item: (-int(item.get("priority", 0)), item.get("relative_path", "")))
        highlights = candidates[:max_highlights_per_source]
        for item in highlights:
            highlighted_assets.append(item)

        sources.append(
            {
                "source_id": manifest.source_id,
                "source_label": manifest.source_id,
                "root_path": manifest.root_path,
                "source_type": manifest.source_type,
                "source_type_definition": source_type_details["source_type_definition"],
                "classification": manifest.classification,
                "owner_floor": owner_floor,
                "usage_role": "empirical_source",
                "operator_notes": source_type_details["operator_notes"],
                "trusted_documents": manifest.trusted_documents,
                "file_count": file_count,
                "class_counts": source_class_counts,
                "extension_counts": source_extension_counts,
                "highlights": highlights,
            }
        )

    highlighted_assets.sort(key=lambda item: (-int(item.get("priority", 0)), item.get("relative_path", "")))
    recommended_datasets = [
        item
        for item in highlighted_assets
        if item.get("asset_class") == "structured_dataset"
    ][:20]
    dataset_table.sort(key=lambda item: (-int(item.get("priority", 0)), item.get("relative_path", "")))
    for item in (recommended_datasets + highlighted_assets[:20]):
        theme = item.get("dataset_role", "general_empirical")
        if any(existing.get("theme") == theme for existing in headline_knowns):
            continue
        headline_knowns.append(
            {
                "theme": theme,
                "source_id": item.get("source_id"),
                "source_label": item.get("source_label") or item.get("source_id"),
                "owner_floor": item.get("owner_floor") or "Oracle",
                "headline": f"{theme.replace('_', ' ').title()} anchor: {item.get('relative_path')}",
                "asset_class": item.get("asset_class"),
                "usage_role": item.get("usage_role") or item.get("canonical_role") or theme,
                "recommended_path": item.get("absolute_path"),
                "operator_notes": item.get("operator_notes") or "Use as a compact empirical anchor after Oracle proofing.",
            }
        )
    clusterable_inputs = [
        item
        for item in dataset_table
        if item.get("dataset_role") in {"macro_mapping", "micro_validation"}
    ][:24]

    payload = {
        "generated_at": utc_now_iso(),
        "catalog_path": str(default_empirical_catalog_path(root)),
        "source_count": len(sources),
        "total_file_count": total_files,
        "class_totals": class_totals,
        "extension_totals": extension_totals,
        "role_totals": role_totals,
        "canonical_role_totals": canonical_role_totals,
        "recommended_datasets": recommended_datasets,
        "dataset_table": dataset_table[:60],
        "clusterable_inputs": clusterable_inputs,
        "headline_knowns": headline_knowns[:12],
        "highlighted_assets": highlighted_assets[:40],
        "sources": sources,
        "source_summary": {
            "labels": [item.get("source_label") for item in sources[:6]],
            "owner_floors": sorted({item.get("owner_floor") or "Oracle" for item in sources}),
            "usage_roles": sorted({item.get("usage_role") or "empirical_source" for item in sources}),
        },
        "clusterable_input_summary": {
            "count": len(clusterable_inputs),
            "labels": [item.get("source_label") or item.get("source_id") for item in clusterable_inputs[:8]],
            "themes": [item.get("dataset_role") for item in clusterable_inputs[:8]],
        },
        "headline_knowns_summary": {
            "count": len(headline_knowns),
            "labels": [item.get("source_label") or item.get("source_id") for item in headline_knowns[:8]],
            "themes": [item.get("theme") for item in headline_knowns[:8]],
        },
        "summary": (
            f"Empirical catalog condensed into {len(sources)} source bundle(s) with "
            f"{len(clusterable_inputs)} clusterable inputs and {len(headline_knowns)} headline knowns."
        ),
    }
    return payload


def write_empirical_catalog(
    root: Path,
    manifests: list[ReservoirManifest],
    *,
    output_path: Path | None = None,
) -> dict:
    root = Path(root)
    destination = output_path or default_empirical_catalog_path(root)
    payload = build_empirical_catalog(root, manifests)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
