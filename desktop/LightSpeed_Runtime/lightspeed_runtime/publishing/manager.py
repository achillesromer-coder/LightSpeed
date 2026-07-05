from __future__ import annotations

import json
from pathlib import Path

from lightspeed_runtime.analytics_validation import build_publish_checkpoint
from lightspeed_runtime.contracts import WorkspacePublishManifest, utc_now_iso


class PublishingManager:
    def create_workspace_manifest(
        self,
        workspace_id: str,
        project_id: str,
        summary_blocks: list[dict],
        artifacts: list[dict],
        visualizations: list[dict],
        latest_runs: list[dict],
        links: list[dict],
        visibility: str = "internal",
        status: str = "ready",
        ) -> WorkspacePublishManifest:
        return WorkspacePublishManifest(
            workspace_id=workspace_id,
            project_id=project_id,
            published_at=utc_now_iso(),
            status=status,
            summary_blocks=list(summary_blocks),
            artifacts=list(artifacts),
            visualizations=list(visualizations),
            latest_runs=list(latest_runs),
            links=list(links),
            visibility=visibility,
        )

    def export_workspace_package(
        self,
        output_dir: Path,
        *,
        manifest: dict,
        reservoir_snapshot: dict,
        latest_runs: list[dict],
        metadata: dict | None = None,
        extra_files: dict[str, dict] | None = None,
        table_validation: dict | None = None,
    ) -> dict:
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = {
            "manifest": output_dir / "workspace_manifest.json",
            "reservoir_snapshot": output_dir / "reservoir_snapshot.json",
            "latest_runs": output_dir / "latest_runs.json",
            "publish_checkpoint": output_dir / "publish_checkpoint.json",
            "governed_bundle": output_dir / "governed_bundle.json",
            "package_metadata": output_dir / "package_metadata.json",
        }
        paths["manifest"].write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        paths["reservoir_snapshot"].write_text(json.dumps(reservoir_snapshot, indent=2), encoding="utf-8")
        paths["latest_runs"].write_text(json.dumps(latest_runs, indent=2), encoding="utf-8")
        checkpoint = build_publish_checkpoint(
            manifest=manifest,
            latest_runs=latest_runs,
            metadata=metadata,
            table_validation=table_validation,
        )
        paths["publish_checkpoint"].write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")
        governed_bundle = {
            "bundle_shape_version": "1.0",
            "governance_floor": "Architect",
            "workspace_id": manifest.get("workspace_id"),
            "project_id": manifest.get("project_id"),
            "status": manifest.get("status", "ready"),
            "visibility": manifest.get("visibility", "internal"),
            "required_files": [
                "workspace_manifest.json",
                "reservoir_snapshot.json",
                "latest_runs.json",
                "publish_checkpoint.json",
                "package_metadata.json",
            ],
            "optional_roots": ["generated/"],
            "artifact_count": len(manifest.get("artifacts") or []),
            "latest_run_count": len(latest_runs),
            "checkpoint_status": checkpoint.get("status"),
            "interchange_contract": "workspace_publish_manifest + publish_checkpoint + package_metadata",
        }
        paths["governed_bundle"].write_text(json.dumps(governed_bundle, indent=2), encoding="utf-8")
        payload = {
            "exported_at": utc_now_iso(),
            "files": {key: str(path) for key, path in paths.items()},
            "publish_checkpoint": checkpoint,
            "governed_bundle": governed_bundle,
        }
        if extra_files:
            exports_dir = output_dir / "generated"
            exports_dir.mkdir(parents=True, exist_ok=True)
            generated_paths: dict[str, str] = {}
            for name, content in extra_files.items():
                file_path = exports_dir / f"{name}.json"
                file_path.write_text(json.dumps(content, indent=2), encoding="utf-8")
                generated_paths[name] = str(file_path)
            payload["generated_files"] = generated_paths
        if metadata:
            payload["metadata"] = metadata
        paths["package_metadata"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload
