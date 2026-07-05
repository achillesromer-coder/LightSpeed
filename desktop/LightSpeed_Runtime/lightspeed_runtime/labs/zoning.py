from __future__ import annotations

import csv
import json
import math
import os
from collections import Counter, defaultdict
from pathlib import Path

from lightspeed_runtime.units import summarize_zoning_units


STRUCTURED_EXTENSIONS = {".csv", ".json", ".jsonl", ".ecsv"}

FIELD_ALIASES = {
    "object_id": ("object_id", "id", "spkid", "pdes", "designation", "full_name", "name"),
    "name": ("name", "full_name", "designation", "object_name", "target"),
    "semi_major_axis": ("a", "semi_major_axis", "semiMajorAxis", "sma", "au"),
    "eccentricity": ("e", "eccentricity", "ecc"),
    "inclination": ("i", "inclination", "inc"),
    "diameter": ("diameter", "diameter_km", "diameter_mean", "diam_km", "diam"),
    "density": ("density", "bulk_density", "grain_density"),
    "taxonomy": ("taxonomy", "tax_class", "class", "spec_type", "spectral_type", "type"),
    "delta_v": ("delta_v", "delta_v_proxy", "dv", "earth_delta_v", "deltaV"),
    "synodic_period": ("synodic_period", "synodic_period_days", "synodic_days"),
    "moid": ("moid", "earth_moid", "moid_au"),
}


def assign_zone(a: float, e: float, i: float) -> str:
    if a < 1.0:
        radial = "Z1"
    elif a < 2.0:
        radial = "Z2"
    elif a < 2.8:
        radial = "Z3"
    elif a < 3.5:
        radial = "Z4"
    else:
        radial = "Z5"

    inclination = "LowIncl" if i < 10 else "MidIncl" if i < 25 else "HighIncl"
    eccentricity = "LowEcc" if e < 0.1 else "MidEcc" if e < 0.3 else "HighEcc"
    return f"{radial}-{inclination}-{eccentricity}"


def discover_structured_files(root: Path, *, limit: int = 60) -> list[Path]:
    root = Path(root)
    if not root.exists():
        return []
    files: list[Path] = []
    hard_limit = max(limit, 1) * 3
    skip_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__"}
    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in skip_dirs and not name.startswith(".")]
        for filename in sorted(filenames):
            path = Path(current_root) / filename
            if path.suffix.lower() in STRUCTURED_EXTENSIONS:
                files.append(path)
                if len(files) >= hard_limit:
                    break
        if len(files) >= hard_limit:
            break
    files.sort(key=lambda item: (_structured_priority(item), str(item).lower()))
    return files[:limit]


def run_heliocentric_zoning(
    source_path: Path,
    output_dir: Path,
    *,
    source_label: str,
    max_records: int = 2500,
    cluster_target: int = 3,
    top_targets: int = 25,
) -> dict:
    source_path = Path(source_path)
    output_dir = Path(output_dir)
    raw_records = read_structured_records(source_path, max_records=max_records)
    normalized: list[dict] = []
    for index, row in enumerate(raw_records):
        record = normalize_asteroid_record(row, index=index)
        if record is not None:
            normalized.append(record)

    if not normalized:
        sample_keys = sorted(_sample_keys(raw_records))
        raise ValueError(
            "No zoning-ready records found. Required orbital fields are semi-major axis, eccentricity, "
            f"and inclination. Sample keys: {sample_keys[:16]}"
        )

    zone_summaries = _build_zone_summaries(normalized)
    cluster_rows, cluster_assignments = _build_clusters(normalized, cluster_target=cluster_target)
    shortlist = _build_shortlist(normalized, cluster_assignments, top_targets=top_targets)
    gmat_targets = _build_gmat_targets(shortlist)
    gmat_target_batch = _build_gmat_target_batch(
        source_label=source_label,
        source_path=source_path,
        shortlist=shortlist,
        gmat_targets=gmat_targets,
    )
    simulation_parameters = _build_simulation_parameters(
        source_label=source_label,
        source_path=source_path,
        zone_summaries=zone_summaries,
        cluster_rows=cluster_rows,
        shortlist=shortlist,
    )
    unit_validation = summarize_zoning_units(normalized)
    simulation_parameters["unit_validation"] = unit_validation

    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "zones_summary_json": _write_json(output_dir / "zones_summary.json", zone_summaries),
        "clusters_json": _write_json(output_dir / "clusters.json", cluster_rows),
        "targets_shortlist_json": _write_json(output_dir / "targets_shortlist.json", shortlist),
        "simulation_parameters_json": _write_json(output_dir / "simulation_parameters.json", simulation_parameters),
        "gmat_targets_json": _write_json(output_dir / "gmat_targets.json", gmat_targets),
        "gmat_target_batch_json": _write_json(output_dir / "gmat_target_batch.json", gmat_target_batch),
        "zones_summary_csv": _write_csv(output_dir / "zones_summary.csv", zone_summaries),
        "clusters_csv": _write_csv(output_dir / "clusters.csv", cluster_rows),
        "targets_shortlist_csv": _write_csv(output_dir / "targets_shortlist.csv", shortlist),
    }
    parquet_artifacts = _write_optional_parquet(
        output_dir,
        zone_summaries=zone_summaries,
        cluster_rows=cluster_rows,
        shortlist=shortlist,
    )
    artifacts.update(parquet_artifacts)

    metrics = {
        "source_label": source_label,
        "source_path": str(source_path),
        "records_loaded": len(raw_records),
        "records_zoned": len(normalized),
        "zone_count": len(zone_summaries),
        "cluster_count": len(cluster_rows),
        "shortlist_count": len(shortlist),
        "parquet_available": any(key.endswith("_parquet") for key in parquet_artifacts),
        "unit_warning_count": len(unit_validation.get("warnings") or []),
    }

    outputs = [
        {"artifact": "zones_summary", "kind": "zone_summary", "path": artifacts["zones_summary_json"]},
        {"artifact": "clusters", "kind": "cluster_summary", "path": artifacts["clusters_json"]},
        {"artifact": "targets_shortlist", "kind": "targets_shortlist", "path": artifacts["targets_shortlist_json"]},
        {
            "artifact": "simulation_parameters",
            "kind": "simulation_parameters",
            "path": artifacts["simulation_parameters_json"],
        },
        {"artifact": "gmat_targets", "kind": "gmat_targets", "path": artifacts["gmat_targets_json"]},
        {"artifact": "gmat_target_batch", "kind": "gmat_target_batch", "path": artifacts["gmat_target_batch_json"]},
    ]

    summary = {
        "source_label": source_label,
        "source_path": str(source_path),
        "source_provenance_links": [
            {
                "label": "source file",
                "path": str(source_path),
            }
        ],
        "output_dir": str(output_dir),
        "report_path": str(output_dir / "run_summary.json"),
        "zone_count": len(zone_summaries),
        "cluster_count": len(cluster_rows),
        "shortlist_count": len(shortlist),
        "top_zone": zone_summaries[0]["zone_id"] if zone_summaries else None,
        "top_target": shortlist[0]["name"] if shortlist else None,
        "artifacts": artifacts,
        "metrics": metrics,
    }

    _write_json(output_dir / "run_summary.json", summary)
    return {
        "source_path": str(source_path),
        "source_provenance_links": [
            {
                "label": "source file",
                "path": str(source_path),
            }
        ],
        "output_dir": str(output_dir),
        "report_path": str(output_dir / "run_summary.json"),
        "zone_summaries": zone_summaries,
        "clusters": cluster_rows,
        "targets_shortlist": shortlist,
        "simulation_parameters": simulation_parameters,
        "gmat_targets": gmat_targets,
        "gmat_target_batch": gmat_target_batch,
        "artifacts": artifacts,
        "metrics": metrics,
        "unit_validation": unit_validation,
        "outputs": outputs,
    }


def read_structured_records(path: Path, *, max_records: int = 2500) -> list[dict]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in STRUCTURED_EXTENSIONS:
        raise ValueError(f"Unsupported zoning source format: {path.suffix}")
    if suffix in {".csv", ".ecsv"}:
        return _read_csv_records(path, max_records=max_records)
    if suffix == ".jsonl":
        return _read_jsonl_records(path, max_records=max_records)
    return _read_json_records(path, max_records=max_records)


def normalize_asteroid_record(row: dict, *, index: int = 0) -> dict | None:
    a = _coerce_float(_pick_value(row, "semi_major_axis"))
    e = _coerce_float(_pick_value(row, "eccentricity"))
    i = _coerce_float(_pick_value(row, "inclination"))
    if a is None or e is None or i is None:
        return None

    diameter = _coerce_float(_pick_value(row, "diameter"))
    density = _coerce_float(_pick_value(row, "density"))
    taxonomy = _clean_text(_pick_value(row, "taxonomy")) or "unknown"
    delta_v = _coerce_float(_pick_value(row, "delta_v"))
    synodic_period = _coerce_float(_pick_value(row, "synodic_period"))
    moid = _coerce_float(_pick_value(row, "moid"))
    object_id = _clean_text(_pick_value(row, "object_id")) or f"object_{index + 1:05d}"
    name = _clean_text(_pick_value(row, "name")) or object_id

    diameter = diameter if diameter is not None else max(0.1, round(a * 0.4, 4))
    density_proxy = density if density is not None else _density_proxy_from_taxonomy(taxonomy)
    delta_v_proxy = delta_v if delta_v is not None else _estimate_delta_v_proxy(a, e, i, moid=moid)
    synodic_proxy = synodic_period if synodic_period is not None else _estimate_synodic_period_days(a)
    moid_proxy = moid if moid is not None else _estimate_moid_proxy(a, e)
    metal_proxy = _estimate_metal_proxy(taxonomy, density_proxy)
    accessibility_score = _estimate_accessibility(
        delta_v_proxy=delta_v_proxy,
        synodic_period=synodic_proxy,
        moid=moid_proxy,
        inclination=i,
        eccentricity=e,
    )
    zone_id = assign_zone(a, e, i)
    voxel_id = _voxel_id(a, e, i)
    phase_point = _phase_point(a, e, i)

    return {
        "object_id": object_id,
        "name": name,
        "semi_major_axis": round(a, 6),
        "eccentricity": round(e, 6),
        "inclination": round(i, 6),
        "diameter_km": round(diameter, 6),
        "density_proxy": round(density_proxy, 6),
        "taxonomy": taxonomy,
        "metal_proxy": round(metal_proxy, 6),
        "delta_v_proxy": round(delta_v_proxy, 6),
        "synodic_period_days": round(synodic_proxy, 6),
        "moid_proxy": round(moid_proxy, 6),
        "accessibility_score": round(accessibility_score, 6),
        "candidate_score": round((metal_proxy * 0.45) + (accessibility_score * 0.55), 6),
        "zone_id": zone_id,
        "voxel_id": voxel_id,
        "phase_x": phase_point["x"],
        "phase_y": phase_point["y"],
        "phase_z": phase_point["z"],
    }


def _build_zone_summaries(records: list[dict]) -> list[dict]:
    by_zone: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_zone[record["zone_id"]].append(record)

    rows: list[dict] = []
    for zone_id, items in by_zone.items():
        taxonomies = Counter(item["taxonomy"] for item in items if item.get("taxonomy"))
        rows.append(
            {
                "zone_id": zone_id,
                "count": len(items),
                "avg_diameter_km": round(_mean(item["diameter_km"] for item in items), 6),
                "density_mean": round(_mean(item["density_proxy"] for item in items), 6),
                "taxonomy_distribution": dict(taxonomies.most_common(6)),
                "estimated_metal_fraction": round(_mean(item["metal_proxy"] for item in items), 6),
                "accessibility_score": round(_mean(item["accessibility_score"] for item in items), 6),
                "delta_v_proxy": round(_mean(item["delta_v_proxy"] for item in items), 6),
                "top_object": max(items, key=lambda item: item["candidate_score"])["name"],
            }
        )
    rows.sort(key=lambda item: (-item["estimated_metal_fraction"], -item["accessibility_score"], item["zone_id"]))
    return rows


def _build_clusters(records: list[dict], *, cluster_target: int = 3) -> tuple[list[dict], dict[str, str]]:
    cluster_rows: list[dict] = []
    assignments: dict[str, str] = {}
    by_zone: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_zone[record["zone_id"]].append(record)

    for zone_id, items in by_zone.items():
        k = min(max(1, cluster_target), max(1, len(items) // 3))
        labels = _kmeans_cluster(items, k=k)
        grouped: dict[int, list[dict]] = defaultdict(list)
        for record, label in zip(items, labels):
            cluster_name = f"{zone_id}-C{int(label) + 1:02d}"
            assignments[record["object_id"]] = cluster_name
            record["cluster_id"] = cluster_name
            grouped[int(label)].append(record)

        for label, members in grouped.items():
            cluster_name = f"{zone_id}-C{int(label) + 1:02d}"
            cluster_rows.append(
                {
                    "cluster_id": cluster_name,
                    "zone_id": zone_id,
                    "count": len(members),
                    "avg_diameter_km": round(_mean(item["diameter_km"] for item in members), 6),
                    "density_mean": round(_mean(item["density_proxy"] for item in members), 6),
                    "estimated_metal_fraction": round(_mean(item["metal_proxy"] for item in members), 6),
                    "accessibility_score": round(_mean(item["accessibility_score"] for item in members), 6),
                    "centroid_a": round(_mean(item["semi_major_axis"] for item in members), 6),
                    "centroid_e": round(_mean(item["eccentricity"] for item in members), 6),
                    "centroid_i": round(_mean(item["inclination"] for item in members), 6),
                    "top_targets": [item["name"] for item in sorted(members, key=lambda row: row["candidate_score"], reverse=True)[:5]],
                }
            )
    cluster_rows.sort(key=lambda item: (-item["estimated_metal_fraction"], -item["accessibility_score"], item["cluster_id"]))
    return cluster_rows, assignments


def _build_shortlist(records: list[dict], cluster_assignments: dict[str, str], *, top_targets: int = 25) -> list[dict]:
    shortlist = []
    for record in sorted(records, key=lambda item: item["candidate_score"], reverse=True)[:top_targets]:
        payload = dict(record)
        payload["cluster_id"] = cluster_assignments.get(record["object_id"])
        payload["owner_floor"] = "TheConstruct"
        payload["usage_role"] = "simulation_input"
        payload["source_label"] = payload.get("source_label") or payload.get("name") or payload.get("object_id")
        payload["publishability_state"] = "handoff_candidate"
        payload["source_provenance_summary"] = (
            f"Romer-first shortlist from proofed empirical anchors in zone {payload.get('zone_id')}"
            f" and cluster {payload.get('cluster_id') or 'unassigned'}."
        )
        payload["evidence_summary"] = (
            f"score={payload.get('candidate_score')}; accessibility={payload.get('accessibility_score')}; "
            f"delta_v={payload.get('delta_v_proxy')}"
        )
        shortlist.append(payload)
    return shortlist


def _build_gmat_targets(shortlist: list[dict]) -> list[dict]:
    targets: list[dict] = []
    for rank, record in enumerate(shortlist, start=1):
        targets.append(
            {
                "priority_rank": rank,
                "target_id": record["object_id"],
                "name": record["name"],
                "source_label": record.get("source_label") or record.get("name"),
                "owner_floor": "TheConstruct",
                "usage_role": "simulation_input",
                "zone_id": record["zone_id"],
                "cluster_id": record.get("cluster_id"),
                "orbit": {
                    "semi_major_axis": record["semi_major_axis"],
                    "eccentricity": record["eccentricity"],
                    "inclination": record["inclination"],
                },
                "accessibility_score": record["accessibility_score"],
                "delta_v_proxy": record["delta_v_proxy"],
                "candidate_score": record["candidate_score"],
                "evidence_summary": record.get("evidence_summary"),
            }
        )
    return targets


def _build_simulation_parameters(
    *,
    source_label: str,
    source_path: Path,
    zone_summaries: list[dict],
    cluster_rows: list[dict],
    shortlist: list[dict],
) -> dict:
    return {
        "source_label": source_label,
        "owner_floor": "TheConstruct",
        "usage_role": "simulation_input",
        "source_path": str(source_path),
        "source_provenance_summary": f"{source_label} source file retained as provenance for Construct zoning.",
        "operator_notes": "Use proofed empirical anchors and Oracle definitions before expanding scenarios.",
        "visual_layers": [
            {"id": "orbital_rings", "label": "Orbital rings", "type": "banded_orbit_layers"},
            {"id": "asteroid_cloud", "label": "Asteroid cloud", "type": "phase_space_points"},
            {"id": "cluster_overlays", "label": "Cluster overlays", "type": "density_clusters"},
        ],
        "zoning_definition": {
            "radial_bands_au": {
                "Z1": "<1.0",
                "Z2": "1.0-2.0",
                "Z3": "2.0-2.8",
                "Z4": "2.8-3.5",
                "Z5": ">3.5",
            },
            "inclination_bands_deg": {"Low": "0-10", "Mid": "10-25", "High": ">25"},
            "eccentricity_bands": {"Low": "<0.1", "Mid": "0.1-0.3", "High": ">0.3"},
        },
        "summary": {
            "zone_count": len(zone_summaries),
            "cluster_count": len(cluster_rows),
            "candidate_targets": len(shortlist),
            "top_zone": zone_summaries[0]["zone_id"] if zone_summaries else None,
            "top_cluster": cluster_rows[0]["cluster_id"] if cluster_rows else None,
            "top_target": shortlist[0]["name"] if shortlist else None,
        },
    }


def _build_gmat_target_batch(
    *,
    source_label: str,
    source_path: Path,
    shortlist: list[dict],
    gmat_targets: list[dict],
) -> dict:
    top_clusters: list[str] = []
    for record in shortlist:
        cluster_id = str(record.get("cluster_id") or "")
        if cluster_id and cluster_id not in top_clusters:
            top_clusters.append(cluster_id)
        if len(top_clusters) >= 5:
            break
    return {
        "batch_id": f"gmat_batch::{Path(source_path).stem}",
        "source_label": source_label,
        "owner_floor": "TheConstruct",
        "usage_role": "simulation_input",
        "source_path": str(source_path),
        "source_provenance_summary": f"{source_label} source file retained as provenance for GMAT target batch generation.",
        "mission_family": "Romer",
        "selection_rule": "Top shortlisted zoning targets grouped by zone and cluster for GMAT mission setup.",
        "operator_notes": "Targets are derived from proofed empirical inputs and should remain publishable only through Construct and Architect.",
        "cluster_focus": top_clusters,
        "target_count": len(gmat_targets),
        "targets": gmat_targets,
    }


def _read_csv_records(path: Path, *, max_records: int) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        rows = csv.DictReader(handle)
        for row in rows:
            if row:
                records.append(dict(row))
            if len(records) >= max_records:
                break
    return records


def _read_json_records(path: Path, *, max_records: int) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    if isinstance(payload, list):
        return [dict(item) for item in payload[:max_records] if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("records", "results", "items", "data", "objects"):
            value = payload.get(key)
            if isinstance(value, list):
                return [dict(item) for item in value[:max_records] if isinstance(item, dict)]
    raise ValueError(f"JSON zoning source must contain a list-like record payload: {path}")


def _read_jsonl_records(path: Path, *, max_records: int) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                records.append(payload)
            if len(records) >= max_records:
                break
    return records


def _sample_keys(records: list[dict]) -> set[str]:
    keys: set[str] = set()
    for row in records[:10]:
        if isinstance(row, dict):
            keys.update(str(key) for key in row.keys())
    return keys


def _pick_value(row: dict, field_name: str):
    aliases = FIELD_ALIASES[field_name]
    lowered = {str(key).strip().lower(): value for key, value in row.items()}
    for alias in aliases:
        if alias.lower() in lowered:
            return lowered[alias.lower()]
    return None


def _clean_text(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def _density_proxy_from_taxonomy(taxonomy: str) -> float:
    tax = (taxonomy or "").upper()
    if tax.startswith("M"):
        return 5.2
    if tax.startswith("S"):
        return 2.7
    if tax.startswith("C"):
        return 1.7
    if tax.startswith("X"):
        return 3.5
    return 2.4


def _estimate_metal_proxy(taxonomy: str, density_proxy: float) -> float:
    tax = (taxonomy or "").upper()
    base = min(1.0, max(0.0, (density_proxy - 1.0) / 5.0))
    if tax.startswith("M"):
        base = max(base, 0.92)
    elif tax.startswith("X"):
        base = max(base, 0.7)
    elif tax.startswith("S"):
        base = max(base, 0.42)
    elif tax.startswith("C"):
        base = min(base, 0.22)
    return round(min(1.0, max(0.0, base)), 6)


def _estimate_delta_v_proxy(a: float, e: float, i: float, *, moid: float | None = None) -> float:
    moid_term = (moid or _estimate_moid_proxy(a, e)) * 1.7
    return max(2.0, 2.6 + abs(a - 1.0) * 1.9 + e * 3.1 + (i / 12.0) + moid_term)


def _estimate_synodic_period_days(a: float) -> float:
    orbital_period_years = max(a, 0.1) ** 1.5
    delta = abs((1.0 / orbital_period_years) - 1.0)
    if delta <= 1e-6:
        return 5000.0
    return min(5000.0, (1.0 / delta) * 365.25)


def _estimate_moid_proxy(a: float, e: float) -> float:
    perihelion = a * (1.0 - e)
    aphelion = a * (1.0 + e)
    if perihelion <= 1.0 <= aphelion:
        return 0.02 + abs(a - 1.0) * 0.04
    return min(1.5, min(abs(perihelion - 1.0), abs(aphelion - 1.0)))


def _estimate_accessibility(
    *,
    delta_v_proxy: float,
    synodic_period: float,
    moid: float,
    inclination: float,
    eccentricity: float,
) -> float:
    delta_component = 1.0 - min(delta_v_proxy, 12.0) / 12.0
    synodic_component = 1.0 - min(synodic_period, 5000.0) / 5000.0
    moid_component = 1.0 - min(moid, 1.0)
    inclination_component = 1.0 - min(inclination, 45.0) / 45.0
    eccentricity_component = 1.0 - min(eccentricity, 0.8) / 0.8
    score = (
        delta_component * 0.35
        + synodic_component * 0.2
        + moid_component * 0.2
        + inclination_component * 0.15
        + eccentricity_component * 0.1
    )
    return round(min(1.0, max(0.0, score)), 6)


def _phase_point(a: float, e: float, i: float) -> dict[str, float]:
    inclination_radians = math.radians(i)
    return {
        "x": round(a * math.cos(inclination_radians), 6),
        "y": round(a * math.sin(inclination_radians), 6),
        "z": round(e, 6),
    }


def _voxel_id(a: float, e: float, i: float) -> str:
    return f"R{int(a / 0.25):03d}-E{int(e / 0.05):02d}-I{int(i / 5.0):02d}"


def _kmeans_cluster(records: list[dict], *, k: int) -> list[int]:
    if not records:
        return []
    if k <= 1 or len(records) <= 2:
        return [0 for _ in records]

    vectors = [_feature_vector(record) for record in records]
    scaled = _scale_vectors(vectors)
    if len(scaled) <= k:
        return list(range(len(scaled)))

    centers = [list(scaled[index]) for index in _initial_center_indexes(scaled, k)]
    assignments = [0 for _ in scaled]
    for _ in range(12):
        next_assignments = [_nearest_center(vector, centers) for vector in scaled]
        if next_assignments == assignments:
            break
        assignments = next_assignments
        new_centers = []
        for center_index in range(k):
            members = [vector for vector, label in zip(scaled, assignments) if label == center_index]
            if not members:
                new_centers.append(list(centers[center_index]))
                continue
            new_centers.append([_mean(component) for component in zip(*members)])
        centers = new_centers
    return assignments


def _feature_vector(record: dict) -> list[float]:
    return [
        float(record["semi_major_axis"]),
        float(record["eccentricity"]),
        float(record["inclination"]),
        float(record["diameter_km"]),
        float(record["density_proxy"]),
        float(record["accessibility_score"]),
        float(record["metal_proxy"]),
    ]


def _scale_vectors(vectors: list[list[float]]) -> list[list[float]]:
    columns = list(zip(*vectors))
    mins = [min(column) for column in columns]
    maxs = [max(column) for column in columns]
    scaled: list[list[float]] = []
    for vector in vectors:
        scaled.append(
            [
                0.0 if max_value == min_value else (value - min_value) / (max_value - min_value)
                for value, min_value, max_value in zip(vector, mins, maxs)
            ]
        )
    return scaled


def _initial_center_indexes(vectors: list[list[float]], k: int) -> list[int]:
    step = max(1, len(vectors) // k)
    indexes = [min(index * step, len(vectors) - 1) for index in range(k)]
    return sorted(set(indexes + [len(vectors) - 1]))[:k]


def _nearest_center(vector: list[float], centers: list[list[float]]) -> int:
    distances = [_euclidean_distance(vector, center) for center in centers]
    return min(range(len(distances)), key=lambda index: distances[index])


def _euclidean_distance(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def _write_json(path: Path, payload) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def _write_csv(path: Path, rows: list[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return str(path)
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            serialized = {
                key: (json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value)
                for key, value in row.items()
            }
            writer.writerow(serialized)
    return str(path)


def _write_optional_parquet(
    output_dir: Path,
    *,
    zone_summaries: list[dict],
    cluster_rows: list[dict],
    shortlist: list[dict],
) -> dict[str, str]:
    try:
        import pandas as pd  # type: ignore
    except Exception:
        return {}

    artifacts: dict[str, str] = {}
    parquet_targets = {
        "zones_summary_parquet": (zone_summaries, output_dir / "zones_summary.parquet"),
        "clusters_parquet": (cluster_rows, output_dir / "clusters.parquet"),
        "targets_shortlist_parquet": (shortlist, output_dir / "targets_shortlist.parquet"),
    }
    for key, (rows, path) in parquet_targets.items():
        try:
            frame = pd.DataFrame(rows)
            frame.to_parquet(path, index=False)
            artifacts[key] = str(path)
        except Exception:
            continue
    return artifacts


def _mean(values) -> float:
    values = list(values)
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _structured_priority(path: Path) -> tuple[int, str]:
    lowered = path.name.lower()
    keywords = ("asteroid", "rocks", "sbdb", "mpc", "ssodnet", "orbit", "ephemer", "catalog")
    score = 0
    for index, keyword in enumerate(keywords):
        if keyword in lowered:
            score = -10 + index
            break
    return score, lowered
