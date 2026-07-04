from __future__ import annotations

from pathlib import Path

from lightspeed_runtime.contracts import LabRunContract, stable_id, utc_now_iso
from lightspeed_runtime.labs.zoning import run_heliocentric_zoning


class LabManager:
    def __init__(self) -> None:
        self._runs: dict[str, LabRunContract] = {}

    def create_run(
        self,
        lab_type: str,
        scenario_id: str,
        dataset_refs: list[str],
        parameter_set: dict,
        engine: str,
    ) -> LabRunContract:
        run = LabRunContract(
            run_id=stable_id("run"),
            lab_type=lab_type,
            scenario_id=scenario_id,
            dataset_refs=list(dataset_refs),
            parameter_set=dict(parameter_set),
            engine=engine,
        )
        run.mark_running()
        self._runs[run.run_id] = run
        return run

    def complete_run(self, run_id: str, metrics: dict, outputs: list[dict]) -> LabRunContract:
        run = self._runs[run_id]
        run.outputs = list(outputs)
        run.mark_completed(metrics=metrics)
        return run

    def get_run(self, run_id: str) -> LabRunContract:
        return self._runs[run_id]

    def execute_heliocentric_zoning(
        self,
        run_id: str,
        *,
        source_path: str | Path,
        output_dir: str | Path,
        source_label: str,
        max_records: int = 2500,
        cluster_target: int = 3,
        top_targets: int = 25,
    ) -> dict:
        run = self._runs[run_id]
        result = run_heliocentric_zoning(
            Path(source_path),
            Path(output_dir),
            source_label=source_label,
            max_records=max_records,
            cluster_target=cluster_target,
            top_targets=top_targets,
        )
        run.outputs = list(result["outputs"])
        run.mark_completed(metrics=result["metrics"])
        return {
            "run": run.to_dict(),
            "source_path": result["source_path"],
            "output_dir": result["output_dir"],
            "artifacts": result["artifacts"],
            "zone_summaries": result["zone_summaries"],
            "clusters": result["clusters"],
            "targets_shortlist": result["targets_shortlist"],
            "simulation_parameters": result["simulation_parameters"],
            "gmat_targets": result["gmat_targets"],
            "gmat_target_batch": result["gmat_target_batch"],
            "metrics": result["metrics"],
            "unit_validation": result.get("unit_validation", {}),
        }

    def generate_gmat_manifest(self, run: LabRunContract, mission_name: str) -> dict:
        return {
            "artifact": "GMAT Bundle Manifest",
            "version": "1.0",
            "bundle": {
                "mission_name": mission_name,
                "run_id": run.run_id,
                "scenario_id": run.scenario_id,
                "lab_type": run.lab_type,
            },
            "contents": {
                "dataset_refs": run.dataset_refs,
                "parameter_set": run.parameter_set,
                "outputs": run.outputs,
            },
            "provenance": {
                "engine": run.engine,
                "generated_at": utc_now_iso(),
            },
            "execution": {
                "status": run.status,
                "metrics": run.metrics,
            },
        }

    def build_operator_simulation_context(
        self,
        *,
        workspace_id: str,
        project_id: str,
        query: str,
        knowns_payload: dict,
        empirical_payload: dict,
        dataset_catalog: list[dict],
        limit: int = 5,
    ) -> dict:
        center = knowns_payload.get("bellcurve_overlay", {}) or {}
        empirical_headlines = empirical_payload.get("headline_knowns") or []
        empirical_summary = empirical_payload.get("headline_knowns_summary") or {}
        dataset_slice = dataset_catalog[:limit]
        priority_queue = [
            {
                "priority": 1,
                "action": "Review proofed doctrine",
                "reason": "Use knowns and mission overlay as the starting point for operator context.",
                "evidence": center.get("center_of_gravity", [])[:3],
            },
            {
                "priority": 2,
                "action": "Inspect empirical anchors",
                "reason": "Confirm the compact empirical layer before selecting a target dataset.",
                "evidence": [item.get("headline") for item in empirical_headlines[:3] if item.get("headline")],
            },
            {
                "priority": 3,
                "action": "Select a structured dataset",
                "reason": "Choose the next zoning or scenario source from mounted structured inputs.",
                "evidence": [item.get("label") for item in dataset_slice],
            },
            {
                "priority": 4,
                "action": "Run the scenario lab",
                "reason": "Execute zoning, clustering, and GMAT-ready batch generation from the selected source.",
                "evidence": ["heliocentric_zoning_grid"],
            },
            {
                "priority": 5,
                "action": "Approve and publish",
                "reason": "Promote completed outputs into the governed workspace package path.",
                "evidence": ["Trinity approval gate", "Romer publish package"],
            },
        ]
        return {
            "workspace_id": workspace_id,
            "project_id": project_id,
            "query": query,
            "scenario_id": "heliocentric_zoning_grid",
            "priority_queue": priority_queue[:limit],
            "knowns_center": center.get("center_of_gravity", [])[:3],
            "empirical_headline_count": len(empirical_headlines),
            "empirical_headline_summary": empirical_summary,
            "recommended_dataset_count": len(empirical_payload.get("recommended_datasets", [])),
            "dataset_labels": [item.get("label") for item in dataset_slice],
            "dataset_catalog_count": len(dataset_catalog),
        }

    def list_runs(self) -> list[dict]:
        return [run.to_dict() for run in self._runs.values()]
