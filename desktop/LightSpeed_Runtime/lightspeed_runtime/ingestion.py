from __future__ import annotations

import json
from pathlib import Path

from lightspeed_runtime.contracts import ReservoirManifest
from lightspeed_runtime.storage_paths import (
    datatables_root,
    encyclopedia_root,
    ingestion_root,
    knowns_root,
    library_root,
    labs_root,
)


SOURCE_TYPE_FALLBACKS = {
    "dataset_bundle": {
        "definition": "Mounted bundle of structured empirical datasets and companion reference material.",
        "fallback_description": "Mounted empirical dataset bundle.",
        "operator_notes": "Prefer Oracle proofing before reuse in datatables or scenario work.",
    },
    "empirical_dataset_bundle": {
        "definition": "Mounted bundle of empirical assets used for cataloging, proofing, and scenario work.",
        "fallback_description": "Mounted empirical dataset bundle.",
        "operator_notes": "Keep the bundle mounted and condense only reusable records.",
    },
    "document_bundle": {
        "definition": "Document-centered source bundle containing doctrine, notes, or reference prose.",
        "fallback_description": "Mounted document bundle.",
        "operator_notes": "Proof into knowns or library entries before broad reuse.",
    },
    "archive": {
        "definition": "Historical or non-authoritative material retained for search and provenance.",
        "fallback_description": "Archived reference source.",
        "operator_notes": "Keep searchable as reference only unless proofed into active knowledge.",
    },
}


def _source_type_details(source_type: str) -> dict:
    key = str(source_type or "").strip().lower()
    return SOURCE_TYPE_FALLBACKS.get(
        key,
        {
            "definition": "Mounted source with no stronger source-type contract yet.",
            "fallback_description": "Mounted source bundle.",
            "operator_notes": "Treat as reference evidence until Oracle proofing adds a stronger contract.",
        },
    )


def default_ingestion_preparation_path(root: Path) -> Path:
    return ingestion_root(root) / "ingestion_preparation.json"


def read_ingestion_preparation(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_ingestion_preparation_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _classify_destinations(manifest: ReservoirManifest) -> tuple[list[str], list[str]]:
    text = " ".join(
        [
            manifest.source_id,
            manifest.source_type,
            manifest.classification,
            manifest.root_path,
            " ".join(manifest.workspace_tags),
            " ".join(manifest.project_tags),
            " ".join(manifest.trusted_documents),
        ]
    ).lower()

    destinations: list[str] = []
    notes: list[str] = []

    if any(marker in text for marker in ("protocol", "report", "spec", "notebook", "doctrine", "reference")):
        destinations.extend(["library", "encyclopedia_candidates"])
        notes.append("Source reads like doctrine/reference material and should be proofed into library and encyclopedia structures.")

    if any(marker in text for marker in ("achilles", "cognigrex", "architecture", "alignment", "charter", "handoff", "ai_logs", "wizard")):
        destinations.append("knowns")
        notes.append("Source contains operator doctrine or alignment material and should be condensed into the knowns registry before wider proofing; AI logs remain corroboration-only unless proofed into knowns.")

    if any(marker in text for marker in ("dataset", "catalog", "ephemer", "rocks", "asteroid", ".csv", ".json")):
        destinations.append("datatables")
        notes.append("Source contains structured or semi-structured data suitable for datatable extraction and verification.")

    if any(marker in text for marker in ("calculator", "gmat", "raphael", "physics", "scenario", "orbit", "simulation")):
        destinations.append("scenario_lab")
        notes.append("Source is relevant to scenario/lab execution and should be retained for model and calculator integration.")

    if manifest.classification == "archive" or any(marker in text for marker in ("archive", "legacy", "historical")):
        destinations.append("archive_reference")
        notes.append("Source should stay searchable as archive/reference material and not become active doctrine without proofing.")

    if not destinations:
        destinations.append("library")
        notes.append("Defaulted to library proofing because no stronger destination signal was found; keep the source mounted until Oracle proofing completes.")

    # Preserve order but remove duplicates.
    ordered_destinations = list(dict.fromkeys(destinations))
    ordered_notes = list(dict.fromkeys(notes))
    return ordered_destinations, ordered_notes


def _default_floor_owner(manifest: ReservoirManifest, destinations: list[str]) -> str:
    if manifest.floor_owner:
        return manifest.floor_owner
    if "scenario_lab" in destinations:
        return "TheConstruct"
    if "archive_reference" in destinations and "datatables" not in destinations:
        return "Smith"
    return "Oracle"


def build_ingestion_preparation(
    root: Path,
    manifests: list[ReservoirManifest],
    *,
    indexed_counts: dict[str, int] | None = None,
) -> dict:
    root = Path(root)
    indexed_counts = indexed_counts or {}
    sources: list[dict] = []
    destination_counts: dict[str, int] = {}

    for manifest in manifests:
        destinations, notes = _classify_destinations(manifest)
        floor_owner = _default_floor_owner(manifest, destinations)
        source_details = _source_type_details(manifest.source_type)
        for destination in destinations:
            destination_counts[destination] = destination_counts.get(destination, 0) + 1
        sources.append(
            {
                "source_id": manifest.source_id,
                "source_label": manifest.source_id,
                "root_path": manifest.root_path,
                "source_type": manifest.source_type,
                "source_type_definition": source_details["definition"],
                "fallback_description": source_details["fallback_description"],
                "operator_notes": source_details["operator_notes"],
                "classification": manifest.classification,
                "workspace_tags": list(manifest.workspace_tags),
                "project_tags": list(manifest.project_tags),
                "trusted_documents": list(manifest.trusted_documents),
                "floor_owner": floor_owner,
                "usage_role": "source_proofing",
                "index_status": manifest.index_status,
                "last_scan_at": manifest.last_scan_at,
                "indexed_asset_count": int(indexed_counts.get(manifest.source_id, 0) or 0),
                "intended_destinations": destinations,
                "proofing_notes": notes,
                "proofing_sequence": [
                    "verify provenance against source root",
                    "extract stable facts into knowns",
                    "stage approved knowledge into knowns/library/encyclopedia/datatables",
                    "retain non-approved remainder as reference or archive",
                ],
            }
        )

    return {
        "output_root": str(default_ingestion_preparation_path(root).parent),
        "source_count": len(sources),
        "destination_counts": destination_counts,
        "sources": sources,
        "canonical_targets": {
            "library": {
                "owner_floor": "Oracle",
                "path": str(library_root(root)),
                "purpose": "Proofed documents and durable references.",
            },
            "knowns": {
                "owner_floor": "Oracle",
                "path": str(knowns_root(root)),
                "purpose": "Condensed system truths, doctrine overlays, and reusable known-knowns.",
            },
            "encyclopedia_candidates": {
                "owner_floor": "Oracle",
                "path": str(encyclopedia_root(root)),
                "purpose": "Reusable knowledge entries suitable for Oracle encyclopedia volumes.",
            },
            "datatables": {
                "owner_floor": "Oracle",
                "path": str(datatables_root(root)),
                "purpose": "Structured datasets, catalogs, and derived tables.",
            },
            "scenario_lab": {
                "owner_floor": "TheConstruct",
                "path": str(labs_root(root)),
                "purpose": "Physics/calculator/scenario material for TheConstruct and Trinity.",
            },
            "archive_reference": "Historical or non-authoritative searchable material.",
        },
    }


def write_ingestion_preparation(
    root: Path,
    manifests: list[ReservoirManifest],
    *,
    indexed_counts: dict[str, int] | None = None,
    output_path: Path | None = None,
) -> dict:
    root = Path(root)
    payload = build_ingestion_preparation(root, manifests, indexed_counts=indexed_counts)
    destination = output_path or default_ingestion_preparation_path(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
