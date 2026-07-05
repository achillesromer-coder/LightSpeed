from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from lightspeed_runtime.contracts import AchillesActionEnvelope, AssetRecord, LabRunContract
from lightspeed_runtime.domain_registry import get_source_type_definition
from lightspeed_runtime.runtime import LightSpeedRuntime


@dataclass(frozen=True)
class SearchResult:
    asset_id: str
    source_id: str
    relative_path: str
    title: str
    canonical_rank: str
    summary: str
    preview_ref: str | None

    @classmethod
    def from_asset(cls, asset: AssetRecord) -> "SearchResult":
        return cls(
            asset_id=asset.asset_id,
            source_id=asset.source_id,
            relative_path=asset.relative_path,
            title=asset.title,
            canonical_rank=asset.canonical_rank,
            summary=asset.summary,
            preview_ref=asset.preview_ref,
        )

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "source_id": self.source_id,
            "relative_path": self.relative_path,
            "title": self.title,
            "canonical_rank": self.canonical_rank,
            "summary": self.summary,
            "preview_ref": self.preview_ref,
        }


def _knowns_summary(known_documents: list[str]) -> str:
    return (
        f"{len(known_documents)} proofed known document"
        + ("" if len(known_documents) == 1 else "s")
        + (f": {', '.join(known_documents[:5])}" if known_documents else "")
    )


def _classification_operator_usage(classification: str) -> str:
    if classification == "canonical":
        return "Use as high-priority guidance when forming briefs, knowns, and publishable summaries."
    return "Use as supporting material and corroborate before promoting into canonical knowns."


class OracleMorpheusBridge:
    """
    Canonical bridge for Oracle and Morpheus.

    Oracle owns source visibility, provenance, and ingest decisions.
    Morpheus owns search, retrieval, and content-oriented surfacing.
    """

    def __init__(self, runtime: LightSpeedRuntime) -> None:
        self.runtime = runtime

    def search(self, query: str, *, sources: Iterable[str] | None = None, limit: int = 10) -> list[SearchResult]:
        allowed = set(sources or [])
        raw = self.runtime.achilles.retrieve(query, limit=limit * 3)
        results: list[SearchResult] = []
        for item in raw:
            if allowed and item["source_id"] not in allowed:
                continue
            results.append(
                SearchResult(
                    asset_id=item["asset_id"],
                    source_id=item["source_id"],
                    relative_path=item["relative_path"],
                    title=item["title"],
                    canonical_rank=item["canonical_rank"],
                    summary=item["summary"],
                    preview_ref=item.get("preview_ref"),
                )
            )
            if len(results) >= limit:
                break
        return results

    def classify_ingest_view(self, source_id: str) -> dict[str, list[dict]]:
        buckets = {"canonical": [], "reference": [], "archive": []}
        for asset in self.runtime.registry.get_assets(source_id):
            buckets.setdefault(asset.canonical_rank, []).append(SearchResult.from_asset(asset).to_dict())
        return buckets

    def provenance_view(self, asset_id: str) -> dict:
        for manifest in self.runtime.registry.manifests():
            for asset in self.runtime.registry.get_assets(manifest.source_id):
                if asset.asset_id == asset_id:
                    known_documents = list(manifest.trusted_documents)
                    source_type_definition = get_source_type_definition(manifest.source_type)
                    return {
                        "asset": asset.to_dict(),
                        "manifest": manifest.to_dict(),
                        "absolute_path": str(Path(manifest.root_path) / Path(asset.relative_path)),
                        "floor_owner": manifest.floor_owner,
                        "proofed_definition": manifest.definition,
                        "known_documents": known_documents,
                        "knowns_summary": _knowns_summary(known_documents),
                        "source_type_definition": (
                            source_type_definition.summary if source_type_definition else None
                        ),
                        "source_type_operator_usage": (
                            source_type_definition.operator_usage if source_type_definition else None
                        ),
                    }
        raise KeyError(f"Unknown asset id: {asset_id}")

    def asset_preview(self, asset_id: str, *, max_chars: int = 2000) -> dict:
        for manifest in self.runtime.registry.manifests():
            for asset in self.runtime.registry.get_assets(manifest.source_id):
                if asset.asset_id == asset_id:
                    return self.runtime.registry.preview_asset(manifest.source_id, asset_id, max_chars=max_chars)
        raise KeyError(f"Unknown asset id: {asset_id}")

    def source_overview(self, source_id: str) -> dict:
        manifest = next(item for item in self.runtime.registry.manifests() if item.source_id == source_id)
        assets = self.runtime.registry.get_assets(source_id)
        by_rank = {"canonical": 0, "reference": 0, "archive": 0}
        for asset in assets:
            by_rank[asset.canonical_rank] = by_rank.get(asset.canonical_rank, 0) + 1
        known_documents = list(manifest.trusted_documents)
        knowns_summary = _knowns_summary(known_documents)
        source_type_definition = get_source_type_definition(manifest.source_type)
        operator_usage = (
            source_type_definition.operator_usage
            if source_type_definition
            else _classification_operator_usage(manifest.classification)
        )
        return {
            "source_id": source_id,
            "source_label": manifest.source_label,
            "source_type": manifest.source_type,
            "source_type_label": manifest.source_type.replace("_", " ").title(),
            "source_type_definition": source_type_definition.summary if source_type_definition else None,
            "source_type_operator_usage": (
                source_type_definition.operator_usage if source_type_definition else None
            ),
            "classification": manifest.classification,
            "floor_owner": manifest.floor_owner,
            "index_status": manifest.index_status,
            "total_assets": len(assets),
            "by_rank": by_rank,
            "root_path": manifest.root_path,
            "root_exists": True,
            "root_resolution": manifest.root_resolution,
            "definition": manifest.definition,
            "proofed_definition": manifest.definition,
            "known_documents": known_documents,
            "trusted_document_count": len(known_documents),
            "knowns_summary": knowns_summary,
            "operator_notes": manifest.operator_notes,
            "operator_usage": operator_usage,
            "extractors": list(manifest.extractors),
        }

    def source_assets(self, source_id: str, *, canonical_rank: str | None = None, limit: int | None = None) -> list[dict]:
        assets = self.runtime.registry.get_assets(source_id)
        if canonical_rank:
            assets = [asset for asset in assets if asset.canonical_rank == canonical_rank]
        if limit is not None:
            assets = assets[:limit]
        return [SearchResult.from_asset(asset).to_dict() for asset in assets]

    def asset_detail(self, asset_id: str, *, max_chars: int = 2000) -> dict:
        provenance = self.provenance_view(asset_id)
        preview = self.asset_preview(asset_id, max_chars=max_chars)
        asset = provenance["asset"]
        manifest = provenance["manifest"]
        known_documents = list(manifest.get("trusted_documents") or [])
        source_type_definition = get_source_type_definition(str(manifest.get("source_type") or ""))
        operator_usage = (
            source_type_definition.operator_usage
            if source_type_definition
            else _classification_operator_usage(str(manifest.get("classification") or ""))
        )
        return {
            "title": asset.get("title"),
            "source_label": manifest.get("source_label") or manifest.get("source_id"),
            "source_id": asset.get("source_id"),
            "canonical_rank": asset.get("canonical_rank"),
            "source_type_definition": source_type_definition.summary if source_type_definition else None,
            "source_type_operator_usage": (
                source_type_definition.operator_usage if source_type_definition else None
            ),
            "preview_kind": preview.get("preview_kind"),
            "relative_path": asset.get("relative_path"),
            "absolute_path": provenance.get("absolute_path"),
            "root_resolution": manifest.get("root_resolution"),
            "summary": asset.get("summary"),
            "proofed_definition": manifest.get("definition"),
            "known_documents": known_documents,
            "knowns_summary": (
                _knowns_summary(known_documents)
            ),
            "operator_notes": manifest.get("operator_notes"),
            "operator_usage": operator_usage,
            "preview": preview.get("preview"),
        }

    def render_source_overview(self, source_id: str) -> str:
        return format_source_overview(self.source_overview(source_id))

    def render_asset_detail(self, asset_id: str, *, max_chars: int = 2000) -> str:
        return format_asset_detail(self.asset_detail(asset_id, max_chars=max_chars))


class TrinityShellBridge:
    """
    Bridge for Trinity/Architect-facing shell orchestration.
    """

    def __init__(self, runtime: LightSpeedRuntime) -> None:
        self.runtime = runtime

    def open_workspace(self, workspace_id: str, project_id: str, active_floor: str = "Architect") -> dict:
        return self.runtime.ensure_workspace(workspace_id, project_id, active_floor).to_dict()

    def workspace_status(self, workspace_id: str, project_id: str, *, active_floor: str = "Architect") -> dict:
        return self.runtime.workspace_state(workspace_id, project_id, active_floor=active_floor)

    def launch_lab_run(
        self,
        workspace_id: str,
        project_id: str,
        *,
        lab_type: str,
        scenario_id: str,
        dataset_refs: list[str],
        parameter_set: dict,
        engine: str,
    ) -> LabRunContract:
        run = self.runtime.create_lab_run(
            workspace_id,
            project_id,
            lab_type=lab_type,
            scenario_id=scenario_id,
            dataset_refs=dataset_refs,
            parameter_set=parameter_set,
            engine=engine,
        )
        return LabRunContract(**run)

    def complete_lab_run(self, run_id: str, *, metrics: dict, outputs: list[dict]) -> dict:
        return self.runtime.complete_lab_run(run_id, metrics=metrics, outputs=outputs)

    def generate_gmat_manifest(self, workspace_id: str, project_id: str, *, mission_name: str) -> dict:
        return self.runtime.generate_workspace_gmat_manifest(workspace_id, project_id, mission_name=mission_name)

    def zoning_dataset_catalog(self, *, limit_per_source: int = 24) -> list[dict]:
        return self.runtime.structured_dataset_catalog(limit_per_source=limit_per_source)

    def run_heliocentric_zoning(
        self,
        workspace_id: str,
        project_id: str,
        *,
        source_id: str | None = None,
        relative_path: str | None = None,
        source_path: str | None = None,
        scenario_id: str = "heliocentric_zoning_grid",
        max_records: int = 2500,
        cluster_target: int = 3,
        top_targets: int = 25,
    ) -> dict:
        return self.runtime.execute_heliocentric_zoning(
            workspace_id,
            project_id,
            source_id=source_id,
            relative_path=relative_path,
            source_path=source_path,
            scenario_id=scenario_id,
            max_records=max_records,
            cluster_target=cluster_target,
            top_targets=top_targets,
        )

    def publish_workspace(
        self,
        workspace_id: str,
        project_id: str,
        *,
        summary: str,
        artifact_refs: list[dict] | None = None,
    ) -> dict:
        return self.runtime.create_publish_snapshot(
            workspace_id=workspace_id,
            project_id=project_id,
            summary=summary,
            artifact_refs=artifact_refs,
        )

    def export_workspace_package(
        self,
        output_dir: Path,
        *,
        workspace_id: str,
        project_id: str,
        summary: str,
        artifact_refs: list[dict] | None = None,
        metadata: dict | None = None,
    ) -> dict:
        return self.runtime.export_workspace_package(
            output_dir,
            workspace_id=workspace_id,
            project_id=project_id,
            summary=summary,
            artifact_refs=artifact_refs,
            metadata=metadata,
        )


class NeoAchillesBridge:
    """
    Final operator bridge.

    Neo should use this instead of direct unmanaged prompt/action flows.
    """

    def __init__(self, runtime: LightSpeedRuntime, knowledge_bridge: OracleMorpheusBridge | None = None) -> None:
        self.runtime = runtime
        self.knowledge_bridge = knowledge_bridge or OracleMorpheusBridge(runtime)

    def build_operator_brief(self, query: str, *, limit: int = 5) -> dict:
        results = [item.to_dict() for item in self.knowledge_bridge.search(query, limit=limit)]
        knowns = self.runtime.knowns_registry()
        empirical = self.runtime.empirical_catalog()
        dataset_catalog = self.runtime.structured_dataset_catalog(limit_per_source=8)
        priority_queue = self.runtime.labs.build_operator_simulation_context(
            workspace_id="romer",
            project_id="Romer",
            query=query,
            knowns_payload=knowns,
            empirical_payload=empirical,
            dataset_catalog=dataset_catalog,
            limit=5,
        ).get("priority_queue", [])
        return {
            "operator": "Achilles",
            "query": query,
            "retrieval_count": len(results),
            "results": results,
            "priority_queue": priority_queue,
            "knowns_center": (knowns.get("bellcurve_overlay", {}) or {}).get("center_of_gravity", [])[:3],
            "empirical_headline_count": len(empirical.get("headline_knowns", [])),
            "dataset_count": len(dataset_catalog),
        }

    def build_simulation_context(self, workspace: str, query: str = "", *, limit: int = 5) -> dict:
        knowns = self.runtime.knowns_registry()
        empirical = self.runtime.empirical_catalog()
        dataset_catalog = self.runtime.structured_dataset_catalog(limit_per_source=12)
        context = self.runtime.labs.build_operator_simulation_context(
            workspace_id=workspace,
            project_id="Romer",
            query=query,
            knowns_payload=knowns,
            empirical_payload=empirical,
            dataset_catalog=dataset_catalog,
            limit=limit,
        )
        context["operator"] = "Achilles"
        context["retrieval_query"] = query
        return context

    def propose_operator_action(
        self,
        workspace: str,
        target_scope: str,
        action_type: str,
        inputs: dict,
        *,
        requires_approval: bool = True,
    ) -> AchillesActionEnvelope:
        artifact_refs = inputs.get("artifact_refs") if isinstance(inputs, dict) else None
        rationale = ""
        if isinstance(inputs, dict):
            rationale = str(inputs.get("rationale") or inputs.get("summary") or "")
        payload = self.runtime.propose_workspace_action(
            workspace_id=workspace,
            project_id="Romer",
            target_scope=target_scope,
            action_type=action_type,
            inputs=inputs,
            requires_approval=requires_approval,
            source_floor="Neo",
            target_floor=target_scope,
            rationale=rationale,
            artifact_refs=artifact_refs if isinstance(artifact_refs, list) else None,
            prefer_handoff=bool(isinstance(inputs, dict) and inputs.get("force_handoff")),
        )
        return AchillesActionEnvelope(**payload)

    def approve_operator_action(self, workspace: str, action_id: str, *, audit_ref: str | None = None) -> dict:
        return self.runtime.approve_workspace_action(workspace, "Romer", action_id, audit_ref=audit_ref)

    def workspace_status(self, workspace: str) -> dict:
        return self.runtime.workspace_state(workspace, "Romer", active_floor="Neo")


def format_source_overview(overview: dict[str, Any]) -> str:
    by_rank = overview.get("by_rank") or {}
    lines = [
        f"Source: {overview.get('source_label') or overview.get('source_id')}",
        f"Type: {overview.get('source_type_label') or overview.get('source_type')}",
        f"Status: {overview.get('index_status', 'unknown')} | Assets: {overview.get('total_assets', 0)}",
        (
            "Ranks: "
            f"canonical={by_rank.get('canonical', 0)} | "
            f"reference={by_rank.get('reference', 0)} | "
            f"archive={by_rank.get('archive', 0)}"
        ),
    ]
    if overview.get("proofed_definition"):
        lines.append(f"Proofed definition: {overview['proofed_definition']}")
    if overview.get("knowns_summary"):
        lines.append(f"Knowns: {overview['knowns_summary']}")
    if overview.get("operator_notes"):
        lines.append(f"Operator notes: {overview['operator_notes']}")
    if overview.get("operator_usage"):
        lines.append(f"Operator usage: {overview['operator_usage']}")
    if overview.get("root_path"):
        lines.append(f"Root: {overview['root_path']}")
    return "\n".join(lines)


def format_asset_detail(detail: dict[str, Any]) -> str:
    lines = [
        f"Title: {detail.get('title', 'unknown')}",
        f"Source: {detail.get('source_label') or detail.get('source_id')}",
        f"Rank: {detail.get('canonical_rank', 'unknown')}",
    ]
    if detail.get("summary"):
        lines.append(f"Summary: {detail['summary']}")
    if detail.get("proofed_definition"):
        lines.append(f"Proofed definition: {detail['proofed_definition']}")
    if detail.get("knowns_summary"):
        lines.append(f"Knowns: {detail['knowns_summary']}")
    if detail.get("operator_notes"):
        lines.append(f"Operator notes: {detail['operator_notes']}")
    if detail.get("operator_usage"):
        lines.append(f"Operator usage: {detail['operator_usage']}")
    if detail.get("absolute_path"):
        lines.append(f"Path: {detail['absolute_path']}")
    if detail.get("preview"):
        lines.append("Preview:\n" + str(detail["preview"]))
    return "\n".join(lines)
