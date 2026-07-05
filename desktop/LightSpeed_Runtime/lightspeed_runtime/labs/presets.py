from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from lightspeed_runtime.storage_paths import labs_root


def default_simulation_presets_path(root: Path) -> Path:
    return labs_root(root) / "simulation_presets.json"


def _select_assets(empirical_payload: dict, *, role: str, limit: int = 5) -> list[dict]:
    assets: list[dict] = []
    for item in empirical_payload.get("clusterable_inputs") or []:
        if item.get("dataset_role") == role:
            assets.append(item)
    for item in empirical_payload.get("recommended_datasets") or []:
        if item.get("dataset_role") == role and item not in assets:
            assets.append(item)
    return assets[:limit]


def _asset_refs(items: list[dict]) -> list[dict]:
    refs: list[dict] = []
    for item in items:
        refs.append(
            {
                "source_id": item.get("source_id"),
                "source_label": item.get("source_label") or item.get("source_id"),
                "owner_floor": item.get("owner_floor") or "Oracle",
                "usage_role": item.get("usage_role") or item.get("canonical_role") or item.get("dataset_role"),
                "dataset_role": item.get("dataset_role"),
                "canonical_role": item.get("canonical_role"),
                "priority": item.get("priority"),
                "source_type_definition": item.get("source_type_definition"),
                "source_provenance_summary": item.get("source_provenance_summary"),
                "provenance_links": [
                    {
                        "label": "source file",
                        "path": item.get("absolute_path"),
                        "relative_path": item.get("relative_path"),
                    }
                ]
                if item.get("absolute_path")
                else [],
            }
        )
    return refs


def build_simulation_presets(root: Path, empirical_payload: dict) -> dict:
    macro_mapping = _select_assets(empirical_payload, role="macro_mapping", limit=6)
    micro_validation = _select_assets(empirical_payload, role="micro_validation", limit=6)
    simulation_model = _select_assets(empirical_payload, role="simulation_model", limit=6)
    general_empirical = _select_assets(empirical_payload, role="general_empirical", limit=6)
    uncertainty_assets = [
        item
        for item in (empirical_payload.get("recommended_datasets") or [])[:24]
        if "uncertainty" in str(item.get("relative_path", "")).lower()
        or "sensitivity" in str(item.get("relative_path", "")).lower()
    ][:5]

    presets = [
        {
            "preset_id": "romer_heliocentric_zoning",
            "label": "Romer Heliocentric Zoning",
            "owner_floor": "TheConstruct",
            "operator_floor": "Neo",
            "scenario_id": "heliocentric_zoning_grid",
            "purpose": "Macro-map asteroid zoning, clusters, shortlist targets, and GMAT batch candidates.",
            "primary_dataset_role": "macro_mapping",
            "recommended_inputs": _asset_refs(macro_mapping),
            "default_parameters": {"max_records": 2500, "cluster_target": 3, "top_targets": 25},
            "publish_chain": ["TheConstruct run", "Architect publish snapshot", "Neo approval context"],
        },
        {
            "preset_id": "romer_target_refinement",
            "label": "Romer Target Refinement",
            "owner_floor": "TheConstruct",
            "operator_floor": "Morpheus",
            "scenario_id": "target_micro_validation",
            "purpose": "Use PDS-like mission/refinement assets after zoning selects discrete targets.",
            "primary_dataset_role": "micro_validation",
            "recommended_inputs": _asset_refs(micro_validation),
            "default_parameters": {"target_count": 10, "validation_depth": "mission_asset_metadata"},
            "publish_chain": ["Morpheus review", "TheConstruct refinement", "Architect package note"],
        },
        {
            "preset_id": "romer_uncertainty_overlay",
            "label": "Romer Uncertainty Overlay",
            "owner_floor": "Oracle",
            "operator_floor": "TheConstruct",
            "scenario_id": "confidence_overlay",
            "purpose": "Overlay uncertainty, bell-curve, and sensitivity context on derived target tables.",
            "primary_dataset_role": "general_empirical",
            "recommended_inputs": _asset_refs(uncertainty_assets or general_empirical),
            "default_parameters": {"confidence_band": "center_near_edge", "show_histogram": True},
            "publish_chain": ["Oracle validation", "TheConstruct overlay", "Architect checkpoint"],
        },
        {
            "preset_id": "romer_model_bridge",
            "label": "Romer Model Bridge",
            "owner_floor": "TheConstruct",
            "operator_floor": "Smith",
            "scenario_id": "simulation_model_bridge",
            "purpose": "Route compact simulation-model inputs through Smith for bounded long-running lab jobs.",
            "primary_dataset_role": "simulation_model",
            "recommended_inputs": _asset_refs(simulation_model),
            "default_parameters": {"job_router": "smith", "resumable": True},
            "publish_chain": ["Smith job", "TheConstruct run", "Merovingian telemetry"],
        },
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "preset_path": str(default_simulation_presets_path(root)),
        "report_path": str(default_simulation_presets_path(root)),
        "owner_floor": "TheConstruct",
        "reference_project": "Romer",
        "source_label": "Romer simulation presets",
        "source_catalog": empirical_payload.get("catalog_path"),
        "source_provenance_links": (
            [
                {
                    "label": "empirical catalog",
                    "path": empirical_payload.get("catalog_path"),
                }
            ]
            if empirical_payload.get("catalog_path")
            else []
        ),
        "source_provenance_summary": "Romer presets are derived from mounted empirical and proofed Oracle-ready sources.",
        "source_count": empirical_payload.get("source_count", 0),
        "proofed_source_count": len(empirical_payload.get("clusterable_inputs") or []),
        "role_totals": empirical_payload.get("role_totals", {}),
        "preset_count": len(presets),
        "presets": presets,
        "summary": (
            "Romer-first simulation presets derived from empirical and proofed sources so Construct, Neo, Smith, and "
            "Architect share one compact scenario handoff model."
        ),
    }


def read_simulation_presets(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_simulation_presets_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_simulation_presets(root: Path, empirical_payload: dict, output_path: Path | None = None) -> dict:
    destination = output_path or default_simulation_presets_path(root)
    payload = build_simulation_presets(root, empirical_payload)
    payload["preset_path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
