from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lightspeed_runtime.contracts import (
    DatasetManifest,
    EntityRecord,
    ReservoirManifest,
    deterministic_id,
    utc_now_iso,
)
from lightspeed_runtime.storage_paths import catalog_root


FLOOR_DEFINITIONS = [
    ("Z-4_Merovingian", "Merovingian"),
    ("Z-3_Smith", "Smith"),
    ("Z-2_Oracle", "Oracle"),
    ("Z-1_Morpheus", "Morpheus"),
    ("Z0_TheConstruct", "TheConstruct"),
    ("Z+1_Architect", "Architect"),
    ("Z+2_Neo", "Neo"),
    ("Z+3_Trinity", "Trinity"),
]


def default_entity_registry_path(root: Path) -> Path:
    return catalog_root(root) / "entity_registry.json"


def dataset_manifest_root(root: Path) -> Path:
    return catalog_root(root) / "dataset_manifests"


def default_dataset_manifest_index_path(root: Path) -> Path:
    return dataset_manifest_root(root) / "dataset_manifest_index.json"


def read_entity_registry(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_entity_registry_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _canonical_dataset_role(asset_class: str, scientific_role: str) -> str:
    if scientific_role in {"macro_mapping", "micro_validation", "reference_imagery", "mission_reference"}:
        return "reference"
    if asset_class in {"structured_dataset", "model_asset"}:
        return "simulation_input"
    return "reference"


def _unit_system_for_path(relative_path: str) -> str:
    text = relative_path.lower().replace("\\", "/")
    if any(marker in text for marker in ("orbital", "ephemer", "gmat", "asteroid", "gravity", "shape", "lidar")):
        return "scientific_mixed"
    return "mixed"


def _uncertainty_for_record(record: dict) -> str:
    role = str(record.get("dataset_role", "")).strip().lower()
    if role in {"macro_mapping", "micro_validation"}:
        return "review_required"
    return "not_assessed"


def _provenance_summary(*parts: str) -> str:
    values = [str(part).strip() for part in parts if str(part).strip()]
    return "; ".join(values)


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _build_floor_entities() -> list[dict]:
    entities: list[dict] = []
    for floor_id, title in FLOOR_DEFINITIONS:
        record = EntityRecord(
            entity_id=deterministic_id("floor", floor_id),
            entity_kind="floor",
            title=title,
            owner_floor=title,
            lifecycle_state="canonical",
            validation_state="verified",
            provenance={"source": "lightspeed_runtime", "floor_id": floor_id},
            status="active",
            path_ref=f"Z Axis/{floor_id}",
            tags=["z_axis", "smart_floor"],
        )
        entities.append(record.to_dict())
    return entities


def _build_agent_entities() -> list[dict]:
    return [
        EntityRecord(
            entity_id=deterministic_id("agent", "achilles"),
            entity_kind="agent",
            title="Achilles",
            owner_floor="Neo",
            lifecycle_state="canonical",
            validation_state="verified",
            provenance={"summary": "Primary governed operator persona for LightSpeed."},
            status="active",
            tags=["operator", "approval_gated", "primary"],
        ).to_dict(),
        EntityRecord(
            entity_id=deterministic_id("agent", "cognigrex"),
            entity_kind="agent",
            title="Cognigrex",
            owner_floor="Neo",
            lifecycle_state="canonical",
            validation_state="verified",
            provenance={"summary": "Distributed execution body under Achilles oversight."},
            status="active",
            tags=["swarm", "oversight", "execution"],
        ).to_dict(),
    ]


def _upsert_entity(entities: list[dict], entity: dict) -> None:
    entity_id = str(entity.get("entity_id") or "")
    if not entity_id:
        return
    for index, existing in enumerate(entities):
        if str(existing.get("entity_id") or "") == entity_id:
            entities[index] = entity
            return
    entities.append(entity)


def _workspace_entity_bundle(workspace_snapshots: list[dict] | None) -> list[dict]:
    snapshots = workspace_snapshots or []
    entities: list[dict] = []
    project_ids: set[str] = set()
    for snapshot in snapshots:
        workspace = snapshot.get("workspace") or {}
        workspace_id = str(workspace.get("workspace_id") or "").strip()
        project_id = str(workspace.get("project_id") or "").strip()
        if not workspace_id:
            continue

        if project_id and project_id not in project_ids:
            project_ids.add(project_id)
            _upsert_entity(
                entities,
                EntityRecord(
                    entity_id=deterministic_id("project", project_id),
                    entity_kind="project",
                    title=project_id,
                    owner_floor="Architect",
                    lifecycle_state="active",
                    validation_state="tracked",
                    provenance={"workspace_ids": [workspace_id]},
                    status=str(workspace.get("status") or "active"),
                    tags=["project", "governed"],
                ).to_dict(),
            )

        workspace_entity_id = deterministic_id("workspace", workspace_id)
        _upsert_entity(
            entities,
            EntityRecord(
                entity_id=workspace_entity_id,
                entity_kind="workspace",
                title=workspace_id,
                owner_floor=str(workspace.get("active_floor") or "Architect"),
                lifecycle_state="active",
                validation_state="tracked",
                provenance={
                    "project_id": project_id,
                    "approvals_pending": int(workspace.get("approvals_pending", 0) or 0),
                },
                status=str(workspace.get("status") or "active"),
                related_entities=[deterministic_id("project", project_id)] if project_id else [],
                tags=["workspace", "runtime"],
                metadata={
                    "selected_assets": list(workspace.get("selected_assets") or []),
                    "run_ids": list(workspace.get("run_ids") or []),
                    "action_ids": list(workspace.get("action_ids") or []),
                },
            ).to_dict(),
        )

        for run in snapshot.get("latest_runs") or []:
            run_id = str(run.get("run_id") or "").strip()
            if not run_id:
                continue
            _upsert_entity(
                entities,
                EntityRecord(
                    entity_id=run_id,
                    entity_kind="run",
                    title=str(run.get("scenario_id") or run.get("lab_type") or run_id),
                    owner_floor="TheConstruct",
                    lifecycle_state=str(run.get("status") or "queued"),
                    validation_state="tracked",
                    provenance={
                        "workspace_id": workspace_id,
                        "project_id": project_id,
                        "engine": run.get("engine"),
                    },
                    status=str(run.get("status") or "queued"),
                    related_entities=[workspace_entity_id] + ([deterministic_id("project", project_id)] if project_id else []),
                    tags=["run", str(run.get("lab_type") or "lab")],
                    metadata={
                        "dataset_refs": list(run.get("dataset_refs") or []),
                        "parameter_set": run.get("parameter_set") or {},
                        "metrics": run.get("metrics") or {},
                        "published": bool(run.get("published", False)),
                    },
                ).to_dict(),
            )
            for output in run.get("outputs") or []:
                path_ref = str(output.get("path") or "").strip()
                artifact_id = deterministic_id("artifact", run_id, path_ref or str(output.get("artifact") or "output"))
                _upsert_entity(
                    entities,
                    EntityRecord(
                        entity_id=artifact_id,
                        entity_kind="artifact",
                        title=str(output.get("artifact") or output.get("kind") or Path(path_ref).name or artifact_id),
                        owner_floor="TheConstruct",
                        lifecycle_state="derived",
                        validation_state="tracked",
                        provenance={"run_id": run_id, "workspace_id": workspace_id},
                        status="available",
                        path_ref=path_ref or None,
                        related_entities=[run_id, workspace_entity_id],
                        tags=[str(output.get("kind") or "artifact")],
                    ).to_dict(),
                )

        for action in snapshot.get("actions") or []:
            action_id = str(action.get("action_id") or "").strip()
            if not action_id:
                continue
            _upsert_entity(
                entities,
                EntityRecord(
                    entity_id=action_id,
                    entity_kind="action",
                    title=str(action.get("action_type") or action_id),
                    owner_floor="Neo",
                    lifecycle_state=str(action.get("approval_state") or "pending"),
                    validation_state="tracked",
                    provenance={
                        "workspace_id": workspace_id,
                        "project_id": project_id,
                        "target_scope": action.get("target_scope"),
                    },
                    status=str(action.get("approval_state") or "pending"),
                    related_entities=[workspace_entity_id] + ([deterministic_id("project", project_id)] if project_id else []),
                    tags=["action", "achilles"],
                    metadata={
                        "requires_approval": bool(action.get("requires_approval", True)),
                        "result_ref": action.get("result_ref"),
                        "audit_ref": action.get("audit_ref"),
                    },
                ).to_dict(),
            )
            if action.get("requires_approval", True):
                approval_id = deterministic_id("approval", action_id)
                _upsert_entity(
                    entities,
                    EntityRecord(
                        entity_id=approval_id,
                        entity_kind="approval",
                        title=f"Approval for {action.get('action_type', action_id)}",
                        owner_floor="Architect",
                        lifecycle_state=str(action.get("approval_state") or "pending"),
                        validation_state="tracked",
                        provenance={
                            "action_id": action_id,
                            "workspace_id": workspace_id,
                            "audit_ref": action.get("audit_ref"),
                        },
                        status=str(action.get("approval_state") or "pending"),
                        related_entities=[action_id, workspace_entity_id],
                        tags=["approval", "governance"],
                    ).to_dict(),
                )

        manifest = snapshot.get("latest_publish_manifest") or {}
        if manifest:
            _upsert_entity(
                entities,
                EntityRecord(
                    entity_id=deterministic_id("artifact", workspace_id, "publish_manifest"),
                    entity_kind="artifact",
                    title=f"{workspace_id} publish manifest",
                    owner_floor="Architect",
                    lifecycle_state="publish_output",
                    validation_state="tracked",
                    provenance={"workspace_id": workspace_id, "project_id": project_id},
                    status="available",
                    related_entities=[workspace_entity_id] + ([deterministic_id("project", project_id)] if project_id else []),
                    tags=["publish", "manifest"],
                ).to_dict(),
            )

        package = snapshot.get("latest_package_metadata") or {}
        if package:
            files = package.get("files") or {}
            _upsert_entity(
                entities,
                EntityRecord(
                    entity_id=deterministic_id("artifact", workspace_id, "package_metadata"),
                    entity_kind="artifact",
                    title=f"{workspace_id} package metadata",
                    owner_floor="Architect",
                    lifecycle_state="publish_output",
                    validation_state="tracked",
                    provenance={"workspace_id": workspace_id, "project_id": project_id},
                    status="available",
                    path_ref=str(files.get("package_metadata") or ""),
                    related_entities=[workspace_entity_id] + ([deterministic_id("project", project_id)] if project_id else []),
                    tags=["publish", "package"],
                ).to_dict(),
            )
    return entities


def build_entity_registry(
    root: Path,
    manifests: list[ReservoirManifest],
    *,
    empirical_catalog: dict | None = None,
    knowns_registry: dict | None = None,
    workspace_snapshots: list[dict] | None = None,
    curated_tables: dict | None = None,
    columnar_handoff: dict | None = None,
) -> tuple[dict, dict]:
    root = Path(root)
    empirical_catalog = empirical_catalog or {}
    knowns_registry = knowns_registry or {}
    curated_tables = curated_tables or {}
    columnar_handoff = columnar_handoff or {}

    entity_records: list[dict] = _build_floor_entities()
    entity_records.extend(_build_agent_entities())
    entity_records.extend(_workspace_entity_bundle(workspace_snapshots))
    dataset_manifests: list[dict] = []

    source_entity_ids: dict[str, str] = {}
    for manifest in manifests:
        entity_id = deterministic_id("source", manifest.source_id, manifest.root_path)
        source_entity_ids[manifest.source_id] = entity_id
        entity_records.append(
            EntityRecord(
                entity_id=entity_id,
                entity_kind="source",
                title=manifest.source_id,
                owner_floor=manifest.floor_owner or "Oracle",
                lifecycle_state="mounted",
                validation_state="indexed" if manifest.index_status == "indexed" else "pending",
                provenance={
                    "root_path": manifest.root_path,
                    "source_type": manifest.source_type,
                    "classification": manifest.classification,
                    "trusted_documents": manifest.trusted_documents,
                },
                status="active",
                path_ref=manifest.root_path,
                tags=[manifest.classification, manifest.source_type],
                metadata={
                    "source_label": manifest.source_id,
                    "owner_floor": manifest.floor_owner or "Oracle",
                    "usage_role": "source_proofing",
                    "source_type_definition": manifest.source_type,
                    "source_provenance_summary": _provenance_summary(
                        manifest.source_type,
                        manifest.classification,
                        f"{len(manifest.trusted_documents)} trusted document(s)",
                    ),
                    "workspace_tags": manifest.workspace_tags,
                    "project_tags": manifest.project_tags,
                },
            ).to_dict()
        )

    for theme in knowns_registry.get("themes", []) or []:
        theme_key = str(theme.get("theme_key") or theme.get("title") or "").strip()
        if not theme_key:
            continue
        entity_records.append(
            EntityRecord(
                entity_id=deterministic_id("knowledge", theme_key),
                entity_kind="knowledge_theme",
                title=str(theme.get("title") or theme_key),
                owner_floor="Oracle",
                lifecycle_state="curated",
                validation_state="proofed",
                provenance={"theme_key": theme_key, "category": theme.get("category")},
                status="active",
                source_refs=list(theme.get("source_ids") or []),
                tags=[str(theme.get("category") or "knowledge")],
                metadata={
                    "summary": theme.get("summary"),
                    "match_count": theme.get("match_count", 0),
                    "definition_basis": theme.get("definition_basis"),
                    "definition_confidence": theme.get("definition_confidence"),
                },
            ).to_dict()
        )

    for table in curated_tables.get("tables") or []:
        table_name = str(table.get("table_name") or "").strip()
        if not table_name:
            continue
        entity_records.append(
            EntityRecord(
                entity_id=deterministic_id("table", table_name),
                entity_kind="table",
                title=table_name,
                owner_floor="Oracle",
                lifecycle_state="curated",
                validation_state="tracked",
                provenance={"manifest_path": table.get("manifest_path")},
                status="available",
                path_ref=str(table.get("json_path") or table.get("csv_path") or ""),
                tags=["datatable", str(table.get("actual_format") or "json")],
                metadata={
                    "row_count": int(table.get("row_count", 0) or 0),
                    "preferred_format": table.get("preferred_format"),
                    "actual_format": table.get("actual_format"),
                    "source_provenance_summary": _provenance_summary(
                        str(table.get("preferred_format") or ""),
                        str(table.get("actual_format") or ""),
                        str(table.get("manifest_path") or ""),
                    ),
                    "csv_path": table.get("csv_path"),
                    "json_path": table.get("json_path"),
                    "parquet_path": table.get("parquet_path"),
                },
            ).to_dict()
        )

    for table in columnar_handoff.get("tables") or []:
        table_name = str(table.get("table_name") or "").strip()
        if not table_name:
            continue
        entity_records.append(
            EntityRecord(
                entity_id=deterministic_id("artifact", "columnar_handoff", table_name),
                entity_kind="artifact",
                title=f"{table_name} columnar handoff",
                owner_floor="Oracle",
                lifecycle_state="derived",
                validation_state="tracked",
                provenance={"bundle_path": columnar_handoff.get("bundle_path")},
                status="available",
                path_ref=str(columnar_handoff.get("bundle_path") or ""),
                tags=["columnar_handoff", "artifact"],
                metadata={
                    "row_count": int(table.get("row_count", 0) or 0),
                    "columns": list(table.get("columns") or []),
                },
            ).to_dict()
        )

    dataset_records = empirical_catalog.get("dataset_table") or []
    dataset_manifest_index: list[dict] = []
    for record in dataset_records[:80]:
        absolute_path = Path(str(record.get("absolute_path") or ""))
        if not absolute_path.exists() or not absolute_path.is_file():
            continue

        relative_path = str(record.get("relative_path") or absolute_path.name)
        source_id = str(record.get("source_id") or "unknown_source")
        asset_class = str(record.get("asset_class") or "structured_dataset")
        scientific_role = str(record.get("dataset_role") or "general_empirical")
        role = _canonical_dataset_role(asset_class, scientific_role)
        dataset_id = deterministic_id("dataset", source_id, relative_path)
        source_entity_id = source_entity_ids.get(source_id)
        hash_sha256 = _hash_file(absolute_path)
        title = absolute_path.stem.replace("_", " ").replace("-", " ").strip() or absolute_path.name

        manifest = DatasetManifest(
            dataset_id=dataset_id,
            title=title,
            source_id=source_id,
            owner_floor="Oracle",
            role=role,
            lifecycle_state="curated" if role in {"reference", "simulation_input"} else "derived",
            validation_state="pending",
            absolute_path=str(absolute_path),
            relative_path=relative_path,
            file_format=(absolute_path.suffix.lower().lstrip(".") or "unknown"),
            media_type=asset_class,
            size_bytes=int(record.get("size_bytes") or absolute_path.stat().st_size),
            hash_sha256=hash_sha256,
            schema_version="1.0",
            unit_system=_unit_system_for_path(relative_path),
            uncertainty_summary=_uncertainty_for_record(record),
            scientific_role=scientific_role,
            provenance={
                "source_entity_id": source_entity_id,
                "source_id": source_id,
                "priority": record.get("priority", 0),
            },
            tags=[role, scientific_role, asset_class],
            related_entities=[item for item in [source_entity_id] if item],
        )
        dataset_dict = manifest.to_dict()
        dataset_manifests.append(dataset_dict)
        dataset_manifest_index.append(
            {
                "dataset_id": dataset_id,
                "title": title,
                "role": role,
                "scientific_role": scientific_role,
                "manifest_path": str(dataset_manifest_root(root) / f"{dataset_id}.json"),
            }
        )
        entity_records.append(
            EntityRecord(
                entity_id=dataset_id,
                entity_kind="dataset",
                title=title,
                owner_floor="Oracle",
                lifecycle_state=dataset_dict["lifecycle_state"],
                validation_state=dataset_dict["validation_state"],
                provenance=dataset_dict["provenance"],
                status="active",
                path_ref=str(absolute_path),
                source_refs=[source_id],
                related_entities=dataset_dict["related_entities"],
                tags=dataset_dict["tags"],
                metadata={
                    "role": role,
                    "scientific_role": scientific_role,
                    "source_label": source_id,
                    "owner_floor": "Oracle",
                    "usage_role": role,
                    "source_type": asset_class,
                    "source_provenance_summary": _provenance_summary(
                        role,
                        scientific_role,
                        asset_class,
                    ),
                    "file_format": dataset_dict["file_format"],
                    "unit_system": dataset_dict["unit_system"],
                    "uncertainty_summary": dataset_dict["uncertainty_summary"],
                },
            ).to_dict()
        )

    registry_payload = {
        "generated_at": utc_now_iso(),
        "registry_path": str(default_entity_registry_path(root)),
        "report_path": str(default_entity_registry_path(root)),
        "dataset_manifest_index_path": str(default_dataset_manifest_index_path(root)),
        "entity_count": len(entity_records),
        "dataset_manifest_count": len(dataset_manifests),
        "entity_kinds": {
            kind: sum(1 for item in entity_records if item.get("entity_kind") == kind)
            for kind in sorted({str(item.get("entity_kind")) for item in entity_records})
        },
        "entities": entity_records,
        "summary": (
            f"Canonical entity registry with {len(entity_records)} entities and "
            f"{len(dataset_manifests)} governed dataset manifests."
        ),
    }
    manifest_payload = {
        "generated_at": registry_payload["generated_at"],
        "manifest_root": str(dataset_manifest_root(root)),
        "manifest_index_path": str(default_dataset_manifest_index_path(root)),
        "report_path": str(default_dataset_manifest_index_path(root)),
        "manifest_count": len(dataset_manifests),
        "items": dataset_manifests,
        "index": dataset_manifest_index,
    }
    return registry_payload, manifest_payload


def write_entity_registry(
    root: Path,
    manifests: list[ReservoirManifest],
    *,
    empirical_catalog: dict | None = None,
    knowns_registry: dict | None = None,
    workspace_snapshots: list[dict] | None = None,
    curated_tables: dict | None = None,
    columnar_handoff: dict | None = None,
    output_path: Path | None = None,
) -> dict:
    root = Path(root)
    destination = output_path or default_entity_registry_path(root)
    registry_payload, manifest_payload = build_entity_registry(
        root,
        manifests,
        empirical_catalog=empirical_catalog,
        knowns_registry=knowns_registry,
        workspace_snapshots=workspace_snapshots,
        curated_tables=curated_tables,
        columnar_handoff=columnar_handoff,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(registry_payload, indent=2), encoding="utf-8")

    manifest_root = dataset_manifest_root(root)
    manifest_root.mkdir(parents=True, exist_ok=True)
    for item in manifest_payload["items"]:
        manifest_path = manifest_root / f"{item['dataset_id']}.json"
        manifest_path.write_text(json.dumps(item, indent=2), encoding="utf-8")
    default_dataset_manifest_index_path(root).write_text(
        json.dumps(
            {
                "generated_at": manifest_payload["generated_at"],
                "manifest_root": manifest_payload["manifest_root"],
                "manifest_count": manifest_payload["manifest_count"],
                "items": manifest_payload["index"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return registry_payload
