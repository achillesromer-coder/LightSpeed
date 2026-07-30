from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any


_EXPORT_FILES = {
    "agent_environment": "agent_environment.json",
    "truth_registry": "truth_registry.json",
    "floor_models": "floor_models.json",
    "deployment_topology": "deployment_topology.json",
    "host_runtime_policy": "host_runtime_policy.json",
    "neo_local_runtime": "neo_local_runtime.json",
    "neo_realisation_runtime": "neo_realisation_runtime.json",
    "upstream_inventory": "upstream_inventory.json",
    "launch_control": "launch_control.json",
    "agent_population": "agent_population.json",
    "input_staging_matrix": "input_staging_matrix.json",
    "floor_stage_population": "floor_stage_population.json",
    "construct_runtime": "construct_runtime.json",
    "presence_roster": "presence_roster.json",
    "workspace_lanes": "workspace_lanes.json",
    "smart_floor_spaces": "smart_floor_spaces.json",
    "gated_build_tasks": "gated_build_tasks.json",
    "web_drive_bridge": "web_drive_bridge.json",
    "backend_frontend_build": "backend_frontend_build_contract.json",
    "floor_environment_realization": "floor_environment_realization_contract.json",
    "local_agent_wakeup": "local_agent_wakeup_contract.json",
    "resource_closure": "resource_closure_contract.json",
    "agentic_launch_queue": "agentic_launch_queue.json",
    "consolidation_queue": "consolidation_queue.json",
    "overlap_bellcurve": "overlap_bellcurve.json",
    "bootstrap_summary": "bootstrap_summary.json",
}


class AgentHomeBridge:
    """Read-only adapter over generated agent-home export files."""

    def __init__(self, export_dir: Path | str) -> None:
        self.export_dir = Path(export_dir)
        self._cache: dict[str, Any] = {}

    @classmethod
    def from_runtime_root(cls, root: Path | str) -> "AgentHomeBridge":
        return cls(Path(root) / "exports" / "agent_home")

    def export_paths(self) -> dict[str, Path]:
        return {name: self.export_dir / filename for name, filename in _EXPORT_FILES.items()}

    def agent_environment(self) -> dict:
        payload = self._load_json("agent_environment")
        if not isinstance(payload, dict):
            raise TypeError("agent_environment export must contain a JSON object")
        return payload

    def truth_registry(self) -> list[dict]:
        payload = self._load_export_or_environment_section("truth_registry")
        return _expect_list(payload, "truth_registry")

    def floor_models(self) -> list[dict]:
        payload = self._load_export_or_environment_section("floor_models")
        return _expect_list(payload, "floor_models")

    def consolidation_queue(self) -> list[dict]:
        payload = self._load_export_or_environment_section("consolidation_queue")
        return _expect_list(payload, "consolidation_queue")

    def deployment_topology(self) -> dict:
        payload = self._load_export_or_environment_section("deployment_topology")
        if not isinstance(payload, dict):
            raise TypeError("deployment_topology export must contain a JSON object")
        return payload

    def host_runtime_policy(self) -> dict:
        payload = self._load_export_or_environment_section("host_runtime_policy")
        if not isinstance(payload, dict):
            raise TypeError("host_runtime_policy export must contain a JSON object")
        return payload

    def neo_local_runtime(self) -> dict:
        payload = self._load_json("neo_local_runtime", required=False)
        if payload is None:
            payload = (self.agent_environment().get("neo_local_runtime") or {})
        if not isinstance(payload, dict):
            raise TypeError("neo_local_runtime export must contain a JSON object")
        return payload

    def neo_realisation_runtime(self) -> dict:
        payload = self._load_export_or_environment_section("neo_realisation_runtime")
        if not isinstance(payload, dict):
            raise TypeError("neo_realisation_runtime export must contain a JSON object")
        return payload

    def upstream_inventory(self) -> dict:
        payload = self._load_export_or_environment_section("upstream_inventory")
        if not isinstance(payload, dict):
            raise TypeError("upstream_inventory export must contain a JSON object")
        return payload

    def launch_control(self) -> dict:
        payload = self._load_export_or_environment_section("launch_control")
        if not isinstance(payload, dict):
            raise TypeError("launch_control export must contain a JSON object")
        return payload

    def agent_population(self) -> dict:
        payload = self._load_json("agent_population", required=False)
        if payload is None:
            payload = (self.agent_environment().get("agent_population") or {})
        if not isinstance(payload, dict):
            raise TypeError("agent_population export must contain a JSON object")
        return payload

    def input_staging_matrix(self) -> dict:
        payload = self._load_json("input_staging_matrix", required=False)
        if payload is None:
            payload = (self.agent_environment().get("input_staging_matrix") or {})
        if not isinstance(payload, dict):
            raise TypeError("input_staging_matrix export must contain a JSON object")
        return payload

    def floor_stage_population(self) -> dict:
        payload = self._load_export_or_environment_section("floor_stage_population")
        if not isinstance(payload, dict):
            raise TypeError("floor_stage_population export must contain a JSON object")
        return payload

    def construct_runtime(self) -> dict:
        payload = self._load_export_or_environment_section("construct_runtime")
        if not isinstance(payload, dict):
            raise TypeError("construct_runtime export must contain a JSON object")
        return payload

    def presence_roster(self) -> dict:
        payload = self._load_export_or_environment_section("presence_roster")
        if not isinstance(payload, dict):
            raise TypeError("presence_roster export must contain a JSON object")
        return payload

    def workspace_lanes(self) -> dict:
        payload = self._load_export_or_environment_section("workspace_lanes")
        if not isinstance(payload, dict):
            raise TypeError("workspace_lanes export must contain a JSON object")
        return payload

    def smart_floor_spaces(self) -> dict:
        payload = self._load_export_or_environment_section("smart_floor_spaces")
        if not isinstance(payload, dict):
            raise TypeError("smart_floor_spaces export must contain a JSON object")
        return payload

    def gated_build_tasks(self) -> dict:
        payload = self._load_export_or_environment_section("gated_build_tasks")
        if not isinstance(payload, dict):
            raise TypeError("gated_build_tasks export must contain a JSON object")
        return payload

    def web_drive_bridge(self) -> dict:
        payload = self._load_json("web_drive_bridge", required=False)
        if payload is None:
            payload = self.agent_environment().get("web_drive_bridge") or {}
        if not isinstance(payload, dict):
            raise TypeError("web_drive_bridge export must contain a JSON object")
        return payload

    def backend_frontend_build(self) -> dict:
        payload = self._load_json("backend_frontend_build", required=False)
        if payload is None:
            payload = (self.agent_environment().get("backend_frontend_build") or {})
        if not isinstance(payload, dict):
            raise TypeError("backend_frontend_build export must contain a JSON object")
        return payload

    def floor_environment_realization(self) -> dict:
        payload = self._load_json("floor_environment_realization", required=False)
        if payload is None:
            payload = (self.agent_environment().get("floor_environment_realization") or {})
        if not isinstance(payload, dict):
            raise TypeError("floor_environment_realization export must contain a JSON object")
        return payload

    def local_agent_wakeup(self) -> dict:
        payload = self._load_json("local_agent_wakeup", required=False)
        if payload is None:
            payload = (self.agent_environment().get("local_agent_wakeup") or {})
        if not isinstance(payload, dict):
            raise TypeError("local_agent_wakeup export must contain a JSON object")
        return payload

    def resource_closure(self) -> dict:
        payload = self._load_json("resource_closure", required=False)
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            raise TypeError("resource_closure export must contain a JSON object")
        return payload

    def agentic_launch_queue(self) -> dict:
        payload = self._load_json("agentic_launch_queue", required=False)
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            raise TypeError("agentic_launch_queue export must contain a JSON object")
        return payload

    def overlap_bellcurve(self) -> dict:
        payload = self._load_export_or_environment_section("overlap_bellcurve")
        if not isinstance(payload, dict):
            raise TypeError("overlap_bellcurve export must contain a JSON object")
        return payload

    def bootstrap_summary(self) -> dict | None:
        payload = self._load_json("bootstrap_summary", required=False)
        if payload is None:
            return None
        if not isinstance(payload, dict):
            raise TypeError("bootstrap_summary export must contain a JSON object")
        return payload

    def floor_model_assignment(self, floor: str) -> dict:
        for item in self.floor_models():
            if item.get("floor") == floor:
                return item
        raise KeyError(f"Unknown floor assignment: {floor}")

    def truth_registry_summary(self) -> dict:
        entries = self.truth_registry()
        by_entry_type = Counter(str(item.get("entry_type") or "unknown") for item in entries)
        by_classification = Counter(str(item.get("classification") or "unknown") for item in entries)
        by_intake_decision = Counter(str(item.get("intake_decision") or "unknown") for item in entries)

        return {
            "total_entries": len(entries),
            "registered_source_count": by_entry_type.get("registered_source", 0),
            "truth_layer_count": by_entry_type.get("truth_layer", 0),
            "publish_eligible_count": sum(1 for item in entries if item.get("publish_eligible")),
            "by_entry_type": dict(sorted(by_entry_type.items())),
            "by_classification": dict(sorted(by_classification.items())),
            "by_intake_decision": dict(sorted(by_intake_decision.items())),
            "active_truth_entries": [
                str(item.get("entry_id"))
                for item in entries
                if item.get("intake_decision") == "active_truth" and item.get("entry_id")
            ],
        }

    def floor_model_summary(self) -> dict:
        assignments = self.floor_models()
        wake_models: dict[str, str] = {}
        try:
            wake_payload = self.local_agent_wakeup()
            for floor_packet in _expect_list(wake_payload.get("floors") or [], "local_agent_wakeup.floors"):
                floor = str(floor_packet.get("floor") or "").strip()
                connection = floor_packet.get("ollama_connection") if isinstance(floor_packet.get("ollama_connection"), dict) else {}
                model = str(connection.get("model") or "").strip()
                if floor and model:
                    wake_models[floor] = model
        except Exception:
            wake_models = {}

        by_provider = Counter(str(item.get("provider") or "unknown") for item in assignments)
        by_workspace_scope = Counter(str(item.get("workspace_scope") or "unknown") for item in assignments)

        return {
            "total_floors": len(assignments),
            "enabled_count": sum(1 for item in assignments if item.get("enabled")),
            "approval_required_count": sum(1 for item in assignments if item.get("approval_required")),
            "by_provider": dict(sorted(by_provider.items())),
            "by_workspace_scope": dict(sorted(by_workspace_scope.items())),
            "by_floor": {
                str(item.get("floor")): {
                    "model": wake_models.get(str(item.get("floor") or ""), item.get("model")),
                    "configured_model": item.get("model"),
                    "active_model_source": (
                        "local_agent_wakeup"
                        if wake_models.get(str(item.get("floor") or ""))
                        else "floor_models"
                    ),
                    "persona": item.get("persona"),
                    "enabled": bool(item.get("enabled")),
                    "workspace_scope": item.get("workspace_scope"),
                    "preferred_light_model": item.get("preferred_light_model"),
                }
                for item in assignments
                if item.get("floor")
            },
        }

    def queue_summary(self, *, top_n: int = 5) -> dict:
        queue = self.consolidation_queue()
        by_priority = Counter(str(item.get("priority") or "unknown") for item in queue)
        by_queue_type = Counter(str(item.get("queue_type") or "unknown") for item in queue)
        by_target_floor = Counter(str(item.get("target_floor") or "unknown") for item in queue)

        return {
            "total_items": len(queue),
            "by_priority": dict(sorted(by_priority.items())),
            "by_queue_type": dict(sorted(by_queue_type.items())),
            "by_target_floor": dict(sorted(by_target_floor.items())),
            "top_items": [
                {
                    "queue_id": item.get("queue_id"),
                    "queue_type": item.get("queue_type"),
                    "priority": item.get("priority"),
                    "target_floor": item.get("target_floor"),
                    "cluster_key": item.get("cluster_key"),
                    "signal_score": item.get("signal_score"),
                }
                for item in queue[: max(0, top_n)]
            ],
        }

    def overlap_summary(self, *, top_n: int = 5) -> dict:
        payload = self.overlap_bellcurve()
        summary = payload.get("summary") or {}
        clusters = _expect_list(payload.get("clusters") or [], "overlap_bellcurve.clusters")

        return {
            "cluster_count": int(summary.get("cluster_count", len(clusters))),
            "consensus_count": int(summary.get("consensus", 0)),
            "converging_count": int(summary.get("converging", 0)),
            "outlier_count": int(summary.get("outlier", 0)),
            "top_clusters": [
                {
                    "cluster_key": item.get("cluster_key"),
                    "cluster_type": item.get("cluster_type"),
                    "bellcurve_position": item.get("bellcurve_position"),
                    "signal_score": item.get("signal_score"),
                    "source_count": item.get("source_count"),
                }
                for item in clusters[: max(0, top_n)]
            ],
        }

    def deployment_topology_summary(self) -> dict:
        payload = self.deployment_topology()
        authoritative_roots = _expect_list(
            payload.get("authoritative_roots") or [],
            "deployment_topology.authoritative_roots",
        )
        reference_roots = _expect_list(
            payload.get("reference_roots") or [],
            "deployment_topology.reference_roots",
        )
        return {
            "topology_id": payload.get("topology_id"),
            "authoritative_root_count": len(authoritative_roots),
            "reference_root_count": len(reference_roots),
            "authoritative_roots": [
                {
                    "label": item.get("label"),
                    "path": item.get("path"),
                    "role": item.get("role"),
                    "exists": bool(item.get("exists")),
                }
                for item in authoritative_roots
            ],
            "reference_roots": [
                {
                    "label": item.get("label"),
                    "path": item.get("path"),
                    "role": item.get("role"),
                    "exists": bool(item.get("exists")),
                }
                for item in reference_roots
            ],
            "migration_policy": payload.get("migration_policy") or {},
            "persistence_budget": payload.get("persistence_budget") or {},
        }

    def host_runtime_policy_summary(self) -> dict:
        payload = self.host_runtime_policy()
        hardware = payload.get("hardware_baseline") or {}
        storage = payload.get("storage_topology") or {}
        limits = payload.get("runtime_limits") or {}
        windows = payload.get("windows_tuning") or {}
        co_running_apps = payload.get("co_running_apps") or {}
        chrome = co_running_apps.get("chrome") or {}
        de_sporte = co_running_apps.get("de_sporte") or {}
        lightspeed_share = _percent_to_share(de_sporte.get("lightspeed_logged_in_percent"), 48)
        remaining_share = _percent_to_share(de_sporte.get("remaining_window_percent"), 52)
        de_sporte_idle_share = remaining_share * _percent_to_share(
            de_sporte.get("idle_persistence_percent_of_remaining_window"),
            80,
        )
        de_sporte_active_share = remaining_share * _percent_to_share(
            de_sporte.get("active_interaction_percent_of_remaining_window"),
            20,
        )
        runtime_total = lightspeed_share + de_sporte_idle_share + de_sporte_active_share
        ram_gb = _positive_float(hardware.get("ram_gb"), 32.0)
        chrome_ram_gb = _positive_float(limits.get("chrome_reserved_ram_gb") or chrome.get("reserved_ram_gb"), 6.0)
        threads = _positive_float(hardware.get("threads"), 16.0)
        chrome_threads = _positive_float(limits.get("chrome_reserved_threads") or chrome.get("reserved_threads"), 4.0)
        firmware_follow_up = _expect_list(
            payload.get("firmware_follow_up") or [],
            "host_runtime_policy.firmware_follow_up",
        )
        return {
            "policy_id": payload.get("policy_id"),
            "cpu": hardware.get("cpu"),
            "ram_gb": hardware.get("ram_gb"),
            "ram_speed_mt_s": hardware.get("ram_speed_mt_s"),
            "gpu": hardware.get("gpu"),
            "windows_root": storage.get("windows_root"),
            "workspace_root": storage.get("workspace_root"),
            "max_floor_boot_parallelism": limits.get("max_floor_boot_parallelism"),
            "max_active_heavy_floors": limits.get("max_active_heavy_floors"),
            "max_concurrent_ollama_jobs": limits.get("max_concurrent_ollama_jobs"),
            "construct_widget_budget": limits.get("construct_widget_budget"),
            "interactive_session_mode": limits.get("interactive_session_mode"),
            "chrome_reserved_ram_gb": limits.get("chrome_reserved_ram_gb") or chrome.get("reserved_ram_gb"),
            "chrome_reserved_threads": limits.get("chrome_reserved_threads") or chrome.get("reserved_threads"),
            "lightspeed_max_resident_ui_panels": limits.get("lightspeed_max_resident_ui_panels"),
            "disk_idle_minutes_ac": windows.get("disk_idle_minutes_ac"),
            "background_pause_on_pressure": windows.get("background_pause_on_pressure"),
            "interactive_browser": windows.get("interactive_browser"),
            "chrome_mode": chrome.get("mode"),
            "de_sporte_mode": de_sporte.get("mode"),
            "firmware_action_count": len(firmware_follow_up),
            "resource_closure": {
                "formula": "sum(normalized_shares) = 1.0",
                "runtime_total": round(runtime_total, 6),
                "runtime_shares": {
                    "lightspeed_resident": round(lightspeed_share, 6),
                    "de_sporte_idle_persistence": round(de_sporte_idle_share, 6),
                    "de_sporte_active_interaction": round(de_sporte_active_share, 6),
                },
                "ram_total": 1.0,
                "ram_shares": {
                    "chrome_reserved": round(min(chrome_ram_gb / ram_gb, 1.0), 6) if ram_gb else 0.0,
                    "system_runtime_remaining": round(max((ram_gb - chrome_ram_gb) / ram_gb, 0.0), 6) if ram_gb else 0.0,
                },
                "thread_total": 1.0,
                "thread_shares": {
                    "chrome_reserved": round(min(chrome_threads / threads, 1.0), 6) if threads else 0.0,
                    "system_runtime_remaining": round(max((threads - chrome_threads) / threads, 0.0), 6) if threads else 0.0,
                },
                "pressure_rules": [
                    "Keep one primary focus surface active.",
                    "Keep heavy Ollama floors manual-gated.",
                    "Avoid dependency installs on D: while free space is below 2 GB.",
                ],
            },
        }

    def agent_population_summary(self) -> dict:
        payload = self.agent_population()
        cross_system_roles = _expect_list(payload.get("cross_system_roles") or [], "agent_population.cross_system_roles")
        floor_assignments = _expect_list(payload.get("floor_assignments") or [], "agent_population.floor_assignments")
        by_floor = {
            str(item.get("floor")): item
            for item in floor_assignments
            if item.get("floor")
        }
        return {
            "contract_id": payload.get("contract_id"),
            "population_rule": payload.get("population_rule"),
            "resident_host_application": payload.get("resident_host_application") or {},
            "cross_system_role_count": len(cross_system_roles),
            "floor_assignment_count": len(floor_assignments),
            "cross_system_roles": [
                {
                    "agent_id": item.get("agent_id"),
                    "display_name": item.get("display_name"),
                    "host_application": item.get("host_application"),
                    "runtime_state": item.get("runtime_state"),
                    "lightspeed_floor": item.get("lightspeed_floor"),
                    "activation_policy": item.get("activation_policy"),
                }
                for item in cross_system_roles
            ],
            "floor_assignments": floor_assignments,
            "by_floor": by_floor,
        }

    def neo_local_runtime_summary(self) -> dict:
        payload = self.neo_local_runtime()
        endpoint_policy = payload.get("endpoint_policy") or {}
        editor_bridge = payload.get("editor_bridge") or {}
        fallback_policy = payload.get("fallback_policy") or {}
        temp_shells = _expect_list(payload.get("temp_shells") or [], "neo_local_runtime.temp_shells")
        available_models = _expect_list(payload.get("available_models") or [], "neo_local_runtime.available_models")
        return {
            "runtime_id": payload.get("runtime_id"),
            "state": payload.get("state"),
            "primary_floor": payload.get("primary_floor"),
            "primary_surface": payload.get("primary_surface"),
            "active_profile": payload.get("active_profile"),
            "provider": endpoint_policy.get("provider"),
            "base_url": endpoint_policy.get("base_url"),
            "healthcheck_path": endpoint_policy.get("healthcheck_path"),
            "local_only": bool(endpoint_policy.get("local_only", True)),
            "auto_start_mode": endpoint_policy.get("auto_start_mode"),
            "standby_when_unavailable": bool(endpoint_policy.get("standby_when_unavailable", True)),
            "max_concurrent_sessions": endpoint_policy.get("max_concurrent_sessions"),
            "available_model_count": len(available_models),
            "available_models": available_models,
            "remote_disabled_by_default": bool(fallback_policy.get("remote_disabled_by_default", True)),
            "editor_surface": editor_bridge.get("surface"),
            "editor_mode": editor_bridge.get("mode"),
            "temp_shell_registry_path": editor_bridge.get("temp_shell_registry_path"),
            "temp_shell_count": len(temp_shells),
            "temp_shells": temp_shells,
            "handoff_contract": payload.get("handoff_contract") or {},
        }

    def de_sporte_runtime_summary(self) -> dict:
        population = self.agent_population()
        resident_host = population.get("resident_host_application") or {}
        root_value = resident_host.get("path")
        root = Path(root_value) if isinstance(root_value, str) and root_value else None
        config_root = root / "Config" if root is not None else None
        data_root = root / "Data" if root is not None else None

        persona_runtime = _read_json_file(config_root / "persona_model_runtime.json") if config_root else {}
        resident_registry = _read_json_file(config_root / "resident_registry.json") if config_root else {}
        overview_sync = _read_json_file(data_root / "Overseer" / "overview_sync.json") if data_root else {}
        phone_dashboard = _read_json_file(data_root / "Overseer" / "phone_dashboard_payload.json") if data_root else {}
        world_shell = _read_json_file(data_root / "World" / "world_shell_state.json") if data_root else {}

        residents = _expect_list(resident_registry.get("residents") or [], "de_sporte_runtime.resident_registry.residents")
        personas = _expect_list(persona_runtime.get("personas") or [], "de_sporte_runtime.persona_model_runtime.personas")
        support_resident_ids = sorted(
            {
                str(item.get("de_sporte_support_resident_id"))
                for item in _expect_list(population.get("floor_assignments") or [], "agent_population.floor_assignments")
                if item.get("de_sporte_support_resident_id")
            }
        )
        support_resident_exports = []
        support_export_count = 0

        for resident_id in support_resident_ids:
            export_payload = (
                _read_json_file(data_root / "Residents" / resident_id / "Exports" / "runtime_export_latest.json")
                if data_root is not None
                else {}
            )
            if export_payload:
                support_export_count += 1
            support_resident_exports.append(
                {
                    "resident_id": resident_id,
                    "current_zone": export_payload.get("current_zone"),
                    "last_message": export_payload.get("last_message"),
                    "focus": (export_payload.get("continuation") or {}).get("next_goal"),
                }
            )

        persona_by_id = {
            str(item.get("persona_id")): item
            for item in personas
            if item.get("persona_id")
        }
        watched_paths = [
            config_root / "persona_model_runtime.json" if config_root else None,
            config_root / "resident_registry.json" if config_root else None,
            data_root / "Overseer" / "overview_sync.json" if data_root else None,
            data_root / "Overseer" / "phone_dashboard_payload.json" if data_root else None,
            data_root / "World" / "world_shell_state.json" if data_root else None,
        ]
        existing_paths = [path for path in watched_paths if isinstance(path, Path) and path.exists()]
        latest_write = max((path.stat().st_mtime for path in existing_paths), default=0.0)

        return {
            "label": resident_host.get("label"),
            "role": resident_host.get("role"),
            "root_path": str(root) if root is not None else None,
            "root_exists": bool(root and root.exists()),
            "config_exists": bool(config_root and config_root.exists()),
            "data_exists": bool(data_root and data_root.exists()),
            "resident_count": len(residents),
            "resident_ids": [str(item.get("resident_id")) for item in residents if item.get("resident_id")],
            "default_query_persona_id": persona_runtime.get("default_query_persona_id"),
            "persona_count": len(personas),
            "raphael_model": persona_by_id.get("raphael", {}).get("primary_model_tag"),
            "achilles_model": persona_by_id.get("achilles", {}).get("primary_model_tag"),
            "neo_model": persona_by_id.get("neo", {}).get("primary_model_tag"),
            "current_zone": (
                overview_sync.get("current_zone")
                or phone_dashboard.get("current_zone")
                or world_shell.get("current_zone")
            ),
            "habitat_anchor": (
                overview_sync.get("habitat_anchor")
                or (phone_dashboard.get("habitation") or {}).get("current_anchor_label")
                or (world_shell.get("habitation") or {}).get("current_anchor_label")
            ),
            "frontier_line": overview_sync.get("frontier_line"),
            "launch_ready": (phone_dashboard.get("launch_readiness") or {}).get("ready_for_population_launch"),
            "bridge_functional": (world_shell.get("bridge") or {}).get("functional"),
            "resident_heartbeat_status": (phone_dashboard.get("resident_heartbeat") or {}).get("status"),
            "support_resident_ids": support_resident_ids,
            "support_export_count": support_export_count,
            "support_residents": support_resident_exports,
            "last_synced_at": (
                datetime.fromtimestamp(latest_write, UTC).isoformat() if latest_write else None
            ),
        }

    def neo_realisation_summary(self) -> dict:
        payload = self.neo_realisation_runtime()
        waves = _expect_list(payload.get("waves") or [], "neo_realisation_runtime.waves")
        training_loops = _expect_list(
            payload.get("training_loops") or [],
            "neo_realisation_runtime.training_loops",
        )
        current_wave_id = payload.get("current_wave_id")
        current_wave = next(
            (item for item in waves if item.get("wave_id") == current_wave_id),
            waves[0] if waves else {},
        )
        return {
            "runtime_id": payload.get("runtime_id"),
            "state": payload.get("state"),
            "mentorship_mode": payload.get("mentorship_mode"),
            "approval_mode": payload.get("approval_mode"),
            "operator_role": payload.get("operator_role"),
            "knowledge_policy": payload.get("knowledge_policy"),
            "guardrails": payload.get("guardrails") or [],
            "wave_count": len(waves),
            "active_wave_count": sum(1 for item in waves if item.get("state") == "active"),
            "training_loop_count": len(training_loops),
            "current_wave_id": current_wave.get("wave_id") or current_wave_id,
            "current_wave_label": current_wave.get("label"),
            "current_wave_state": current_wave.get("state"),
            "current_wave_task_count": len(current_wave.get("task_refs") or []),
            "current_wave_training_loop_count": len(current_wave.get("training_loop_ids") or []),
            "current_wave": current_wave,
            "waves": waves,
            "training_loops": training_loops,
        }

    def upstream_inventory_summary(self) -> dict:
        payload = self.upstream_inventory()
        github = payload.get("github") or {}
        drive = payload.get("drive") or {}
        web = payload.get("web") or {}
        local_review = payload.get("local_review_queue") or {}
        repos = _expect_list(github.get("repos") or [], "upstream_inventory.github.repos")
        roots = _expect_list(drive.get("roots") or [], "upstream_inventory.drive.roots")
        spreadsheets = _expect_list(drive.get("spreadsheets") or [], "upstream_inventory.drive.spreadsheets")
        routes = _expect_list(web.get("routes") or [], "upstream_inventory.web.routes")
        review_queue_path = local_review.get("path")
        return {
            "inventory_id": payload.get("inventory_id"),
            "mode": payload.get("mode"),
            "connected_repo_count": sum(1 for item in repos if item.get("state") == "connected_live"),
            "declared_repo_count": len(repos),
            "repo_names": [str(item.get("repository_full_name")) for item in repos if item.get("repository_full_name")],
            "drive_root_count": len(roots),
            "drive_roots": [
                {
                    "id": item.get("root_id"),
                    "label": item.get("label"),
                    "state": item.get("state"),
                    "item_count": len(item.get("children") or []) if isinstance(item.get("children"), list) else 0,
                }
                for item in roots
            ],
            "spreadsheet_count": len(spreadsheets),
            "spreadsheet_labels": [str(item.get("label")) for item in spreadsheets if item.get("label")],
            "web_route_count": len(routes),
            "web_routes": [str(item.get("route")) for item in routes if item.get("route")],
            "review_queue_path": review_queue_path,
            "review_queue_exists": bool(isinstance(review_queue_path, str) and review_queue_path and Path(review_queue_path).exists()),
            "notes": payload.get("notes") or [],
        }

    def launch_control_summary(self) -> dict:
        payload = self.launch_control()
        sequence = _expect_list(payload.get("initialisation_sequence") or [], "launch_control.initialisation_sequence")
        blockers = _expect_list(payload.get("blockers") or [], "launch_control.blockers")
        readiness_checks = _expect_list(payload.get("readiness_checks") or [], "launch_control.readiness_checks")
        next_actions = _expect_list(payload.get("next_actions") or [], "launch_control.next_actions")
        manual_gates = _expect_list(payload.get("manual_gates") or [], "launch_control.manual_gates")
        co_runner = payload.get("co_runner") or {}

        def _state_done(value: Any) -> bool:
            lowered = str(value or "").lower()
            return lowered in {"ready", "passed", "complete", "connected", "active", "functional", "live"}

        def _row_label(item: Any, *, primary: str, fallback: str) -> str:
            if isinstance(item, dict):
                return str(item.get(primary) or item.get(fallback) or item)
            return str(item)

        handoff_path = co_runner.get("handoff_path")
        snapshot_path = co_runner.get("channel_snapshot_path")
        return {
            "control_id": payload.get("control_id"),
            "gate": payload.get("gate"),
            "state": payload.get("state"),
            "current_focus": payload.get("current_focus"),
            "launch_targets": payload.get("launch_targets") or [],
            "sequence_total": len(sequence),
            "sequence_ready_count": sum(1 for item in sequence if _state_done(item.get("state"))),
            "readiness_total": len(readiness_checks),
            "readiness_ready_count": sum(1 for item in readiness_checks if _state_done(item.get("state"))),
            "blocker_count": len(blockers),
            "blockers": [_row_label(item, primary="label", fallback="blocker_id") for item in blockers],
            "next_actions": [_row_label(item, primary="label", fallback="action_id") for item in next_actions],
            "manual_gates": [_row_label(item, primary="label", fallback="gate_id") for item in manual_gates],
            "co_runner": {
                "host_application": co_runner.get("host_application"),
                "state": co_runner.get("state"),
                "channel_snapshot_path": snapshot_path,
                "channel_snapshot_exists": bool(isinstance(snapshot_path, str) and snapshot_path and Path(snapshot_path).exists()),
                "handoff_path": handoff_path,
                "handoff_exists": bool(isinstance(handoff_path, str) and handoff_path and Path(handoff_path).exists()),
            },
        }

    def input_staging_summary(self) -> dict:
        payload = self.input_staging_matrix()
        floor_rows = _expect_list(payload.get("floors") or [], "input_staging_matrix.floors")
        total_components = 0
        live_component_count = 0
        by_floor: dict[str, dict] = {}
        rows: list[dict] = []

        for item in floor_rows:
            floor = str(item.get("floor") or "")
            components = _expect_list(item.get("components") or [], f"input_staging_matrix.floors[{floor}].components")
            rendered_components = []
            path_exists_count = 0
            for component in components:
                path_value = component.get("path")
                exists = bool(isinstance(path_value, str) and path_value and Path(path_value).exists())
                rendered_components.append(
                    {
                        "component_id": component.get("component_id"),
                        "label": component.get("label"),
                        "component_type": component.get("component_type"),
                        "status": component.get("status"),
                        "path": path_value,
                        "path_exists": exists,
                    }
                )
                total_components += 1
                if exists:
                    live_component_count += 1
                    path_exists_count += 1

            row = {
                "floor": floor,
                "space_id": item.get("space_id"),
                "status": item.get("status"),
                "component_count": len(rendered_components),
                "path_exists_count": path_exists_count,
                "component_ids": [
                    str(component.get("component_id"))
                    for component in rendered_components
                    if component.get("component_id")
                ],
                "components": rendered_components,
            }
            rows.append(row)
            if floor:
                by_floor[floor] = row

        return {
            "matrix_id": payload.get("matrix_id"),
            "policy": payload.get("policy"),
            "shared_rules": payload.get("shared_rules") or [],
            "floor_count": len(rows),
            "total_components": total_components,
            "live_component_count": live_component_count,
            "floors": rows,
            "by_floor": by_floor,
        }

    def floor_stage_population_summary(self) -> dict:
        payload = self.floor_stage_population()
        profiles = payload.get("floor_profiles") or {}
        if not isinstance(profiles, dict):
            raise TypeError("floor_stage_population.floor_profiles must contain a JSON object")
        return {
            "policy_id": payload.get("policy_id"),
            "boot_lane_order": payload.get("boot_lane_order") or [],
            "resident_floors": payload.get("resident_floors") or [],
            "staged_floors": payload.get("staged_floors") or [],
            "manual_heavy_floors": payload.get("manual_heavy_floors") or [],
            "heavy_floor_limit": payload.get("heavy_floor_limit"),
            "floor_count": len(profiles),
            "floor_profiles": profiles,
        }

    def construct_runtime_summary(self) -> dict:
        payload = self.construct_runtime()
        render_modes = _expect_list(payload.get("render_modes") or [], "construct_runtime.render_modes")
        virtual_space_tests = payload.get("virtual_space_tests") or {}
        smoke_lanes = _expect_list(
            virtual_space_tests.get("smoke_lanes") or [],
            "construct_runtime.virtual_space_tests.smoke_lanes",
        )
        manual_lanes = _expect_list(
            virtual_space_tests.get("manual_lanes") or [],
            "construct_runtime.virtual_space_tests.manual_lanes",
        )
        return {
            "profile_id": payload.get("profile_id"),
            "default_surface": payload.get("default_surface"),
            "stage_population_hint": payload.get("stage_population_hint"),
            "theconstruct_model": (payload.get("model_assignment") or {}).get("model"),
            "render_modes": [item.get("mode") for item in render_modes if item.get("mode")],
            "mode_targets": {
                str(item.get("mode")): item.get("target_fps")
                for item in render_modes
                if item.get("mode")
            },
            "max_visible_widgets": (payload.get("resource_guards") or {}).get("max_visible_widgets"),
            "max_live_texture_panels": (payload.get("resource_guards") or {}).get("max_live_texture_panels"),
            "smoke_lane_count": len(smoke_lanes),
            "manual_lane_count": len(manual_lanes),
            "secondary_data_policy": payload.get("secondary_data_policy") or {},
        }

    def presence_roster_summary(self) -> dict:
        payload = self.presence_roster()
        weekly_rotation = _expect_list(payload.get("weekly_rotation") or [], "presence_roster.weekly_rotation")
        overlap_window_count = sum(len(item.get("overlap_windows") or []) for item in weekly_rotation)
        active_days = sum(1 for item in weekly_rotation if item.get("de_sporte_mode") == "active_bias")
        return {
            "roster_id": payload.get("roster_id"),
            "timezone": payload.get("timezone"),
            "schedule_model": payload.get("schedule_model"),
            "lightspeed_logged_in_percent": payload.get("lightspeed_logged_in_percent"),
            "remaining_window_percent": payload.get("remaining_window_percent"),
            "de_sporte_idle_persistence_percent_of_remaining_window": (
                payload.get("de_sporte_idle_persistence_percent_of_remaining_window")
            ),
            "de_sporte_active_percent_of_remaining_window": (
                payload.get("de_sporte_active_percent_of_remaining_window")
            ),
            "cascade_overlap_percent": payload.get("cascade_overlap_percent"),
            "interaction_speed_factor": payload.get("interaction_speed_factor"),
            "callout_policy": payload.get("callout_policy") or {},
            "concurrency_contract": payload.get("concurrency_contract") or {},
            "rotation_day_count": len(weekly_rotation),
            "overlap_window_count": overlap_window_count,
            "active_bias_days": active_days,
            "weekly_rotation": weekly_rotation,
        }

    def workspace_lane_summary(self) -> dict:
        payload = self.workspace_lanes()
        lanes = _expect_list(payload.get("lanes") or [], "workspace_lanes.lanes")
        by_owner_floor = Counter(str(item.get("owner_floor") or "unknown") for item in lanes)
        ready_count = sum(1 for item in lanes if str(item.get("state") or "").startswith("ready"))
        return {
            "lane_set_id": payload.get("lane_set_id"),
            "primary_surface": payload.get("primary_surface"),
            "interface_mode": payload.get("interface_mode"),
            "surface_density": payload.get("surface_density"),
            "approval_input_mode": payload.get("approval_input_mode"),
            "minimum_system_goal": payload.get("minimum_system_goal"),
            "navigation_contract": payload.get("navigation_contract") or [],
            "chrome_safe_mode": bool(payload.get("chrome_safe_mode")),
            "manual_activation_lanes": payload.get("manual_activation_lanes") or [],
            "avoid_patterns": payload.get("avoid_patterns") or [],
            "cognigrex_spine": payload.get("cognigrex_spine") or {},
            "lane_count": len(lanes),
            "ready_lane_count": ready_count,
            "by_owner_floor": dict(sorted(by_owner_floor.items())),
            "lanes": [
                {
                    "lane_id": item.get("lane_id"),
                    "label": item.get("label"),
                    "owner_floor": item.get("owner_floor"),
                    "state": item.get("state"),
                    "surface": item.get("surface"),
                    "approval_required": bool(item.get("approval_required")),
                    "attached_floor_count": len(item.get("attached_floors") or []),
                }
                for item in lanes
            ],
        }

    def smart_floor_space_summary(self) -> dict:
        payload = self.smart_floor_spaces()
        spaces = _expect_list(payload.get("spaces") or [], "smart_floor_spaces.spaces")
        ready_count = sum(1 for item in spaces if str(item.get("status") or "").startswith("ready"))
        no_risk_entry_count = sum(1 for item in spaces if item.get("no_risk_entry"))
        return {
            "space_set_id": payload.get("space_set_id"),
            "population_contract": payload.get("population_contract"),
            "default_density": payload.get("default_density"),
            "collapse_policy": payload.get("collapse_policy"),
            "single_interface_goal": payload.get("single_interface_goal"),
            "space_count": len(spaces),
            "ready_count": ready_count,
            "no_risk_entry_count": no_risk_entry_count,
            "spaces": [
                {
                    "space_id": item.get("space_id"),
                    "floor": item.get("floor"),
                    "label": item.get("label"),
                    "space_type": item.get("space_type"),
                    "status": item.get("status"),
                    "default_view": item.get("default_view"),
                    "no_risk_entry": bool(item.get("no_risk_entry")),
                }
                for item in spaces
            ],
        }

    def gated_build_task_summary(self, *, top_n: int = 8) -> dict:
        payload = self.gated_build_tasks()
        tasks = _expect_list(payload.get("tasks") or [], "gated_build_tasks.tasks")
        by_owner_floor = Counter(str(item.get("owner_floor") or "unknown") for item in tasks)
        by_lane = Counter(str(item.get("lane_id") or "unknown") for item in tasks)
        by_state = Counter(str(item.get("state") or "unknown") for item in tasks)
        ready_count = sum(1 for item in tasks if str(item.get("state") or "").startswith("ready"))
        return {
            "task_set_id": payload.get("task_set_id"),
            "default_state": payload.get("default_state"),
            "execution_mode": payload.get("execution_mode"),
            "approval_policy": payload.get("approval_policy") or {},
            "total_tasks": len(tasks),
            "ready_count": ready_count,
            "by_owner_floor": dict(sorted(by_owner_floor.items())),
            "by_lane": dict(sorted(by_lane.items())),
            "by_state": dict(sorted(by_state.items())),
            "top_tasks": [
                {
                    "task_id": item.get("task_id"),
                    "owner_floor": item.get("owner_floor"),
                    "lane_id": item.get("lane_id"),
                    "priority": item.get("priority"),
                    "state": item.get("state"),
                    "risk_level": item.get("risk_level"),
                }
                for item in tasks[: max(0, top_n)]
            ],
        }

    def web_drive_bridge_summary(self) -> dict:
        payload = self.web_drive_bridge()
        routes = _expect_list(payload.get("squarespace_routes") or [], "web_drive_bridge.squarespace_routes")
        log_rows = _expect_list(
            payload.get("squarespace_implementation_log") or [],
            "web_drive_bridge.squarespace_implementation_log",
        )
        embed = payload.get("squarespace_embed_source") or {}
        unconfirmed = [
            row
            for row in log_rows
            if "UNCONFIRMED" in {
                str(row.get("page_exists") or ""),
                str(row.get("embed_pasted") or ""),
                str(row.get("desktop_preview") or ""),
                str(row.get("mobile_preview") or ""),
            }
            or "PENDING" in {
                str(row.get("desktop_preview") or ""),
                str(row.get("mobile_preview") or ""),
            }
        ]
        partial = [
            row
            for row in log_rows
            if str(row.get("page_exists") or "") == "SEEN_SCREENSHOT"
            or str(row.get("embed_pasted") or "") == "PARTIAL_RENDER_SEEN"
        ]
        return {
            "site_base_url": payload.get("site_base_url"),
            "owner_floor": payload.get("owner_floor"),
            "desktop_operator_floor": payload.get("desktop_operator_floor"),
            "publish_owner_floor": payload.get("publish_owner_floor"),
            "contract_path": payload.get("contract_path"),
            "source_workbook_id": embed.get("id"),
            "source_workbook_title": embed.get("title"),
            "copy_cell": embed.get("copy_cell"),
            "source_status": embed.get("status"),
            "gate": embed.get("gate"),
            "boundary": embed.get("boundary"),
            "route_count": len(routes),
            "implementation_rows": len(log_rows),
            "unconfirmed_count": len(unconfirmed),
            "partial_seen_count": len(partial),
            "unconfirmed_routes": [str(row.get("route")) for row in unconfirmed if row.get("route")],
            "partial_seen_routes": [str(row.get("route")) for row in partial if row.get("route")],
            "blocked_actions": embed.get("blocked_actions") or [],
        }

    def agentic_launch_queue_summary(self, *, top_n: int = 10) -> dict:
        payload = self.agentic_launch_queue()
        if not payload:
            return {
                "queue_id": None,
                "state": "not_exported",
                "task_count": 0,
                "ready_count": 0,
                "manual_heavy_count": 0,
                "by_floor": {},
                "by_state": {},
                "by_priority": {},
                "by_type": {},
                "top_tasks": [],
                "mirrors": {},
            }
        tasks = _expect_list(payload.get("tasks") or [], "agentic_launch_queue.tasks")
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        return {
            "queue_id": payload.get("queue_id"),
            "state": payload.get("state"),
            "purpose": payload.get("purpose"),
            "task_count": int(summary.get("task_count", len(tasks))),
            "ready_count": int(summary.get("ready_count", 0)),
            "manual_heavy_count": int(summary.get("manual_heavy_count", 0)),
            "floor_count": int(summary.get("floor_count", 0)),
            "by_floor": summary.get("by_floor") or {},
            "by_state": summary.get("by_state") or {},
            "by_priority": summary.get("by_priority") or {},
            "by_type": summary.get("by_type") or {},
            "policy": payload.get("policy") or {},
            "mirrors": payload.get("mirrors") or {},
            "top_tasks": [
                {
                    "task_id": item.get("task_id"),
                    "task_type": item.get("task_type"),
                    "owner_floor": item.get("owner_floor"),
                    "priority": item.get("priority"),
                    "state": item.get("state"),
                    "model": item.get("model"),
                    "manual_heavy": bool(item.get("manual_heavy")),
                }
                for item in tasks[: max(0, top_n)]
            ],
        }

    def backend_frontend_build_summary(self, *, top_n: int = 8) -> dict:
        payload = self.backend_frontend_build()
        floors = _expect_list(payload.get("floors") or [], "backend_frontend_build.floors")
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        by_floor = {
            str(item.get("floor")): item
            for item in floors
            if item.get("floor")
        }
        return {
            "contract_id": payload.get("contract_id"),
            "purpose": payload.get("purpose"),
            "policy": payload.get("policy") or {},
            "floor_count": summary.get("floor_count", len(floors)),
            "backend_enabled_count": summary.get(
                "backend_enabled_count",
                sum(1 for item in floors if (item.get("backend") or {}).get("enabled")),
            ),
            "frontend_enabled_count": summary.get(
                "frontend_enabled_count",
                sum(1 for item in floors if (item.get("frontend") or {}).get("enabled")),
            ),
            "agent_count": summary.get("agent_count"),
            "ready_task_count": summary.get("ready_task_count"),
            "launch_gate": summary.get("launch_gate"),
            "floors": floors[: max(0, top_n)],
            "by_floor": by_floor,
        }

    def floor_environment_realization_summary(self, *, top_n: int = 8) -> dict:
        payload = self.floor_environment_realization()
        floors = _expect_list(payload.get("floors") or [], "floor_environment_realization.floors")
        cross_system_agents = _expect_list(
            payload.get("cross_system_agents") or [],
            "floor_environment_realization.cross_system_agents",
        )
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        by_floor = {
            str(item.get("floor")): item
            for item in floors
            if item.get("floor")
        }
        return {
            "contract_id": payload.get("contract_id"),
            "purpose": payload.get("purpose"),
            "realization_order": payload.get("realization_order"),
            "outside_in_order": payload.get("outside_in_order") or [],
            "runtime_boot_order": payload.get("runtime_boot_order") or [],
            "policy": payload.get("policy") or {},
            "floor_count": summary.get("floor_count", len(floors)),
            "floor_models_confirmed": summary.get("floor_models_confirmed"),
            "cross_system_agent_count": summary.get("cross_system_agent_count", len(cross_system_agents)),
            "cross_system_models_confirmed": summary.get("cross_system_models_confirmed"),
            "ready_task_count": summary.get("ready_task_count"),
            "launch_gate": summary.get("launch_gate"),
            "floors": floors[: max(0, top_n)],
            "by_floor": by_floor,
            "cross_system_agents": cross_system_agents,
        }

    def local_agent_wakeup_summary(self, *, top_n: int = 8) -> dict:
        payload = self.local_agent_wakeup()
        floors = _expect_list(payload.get("floors") or [], "local_agent_wakeup.floors")
        source_inventory = payload.get("source_inventory") if isinstance(payload.get("source_inventory"), dict) else {}
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        by_floor = {
            str(item.get("floor")): item
            for item in floors
            if item.get("floor")
        }
        return {
            "contract_id": payload.get("contract_id"),
            "purpose": payload.get("purpose"),
            "generated_at": payload.get("generated_at"),
            "source_root": payload.get("source_root"),
            "source_root_exists": bool(payload.get("source_root_exists")),
            "policy": payload.get("policy") or {},
            "ollama": payload.get("ollama") or {},
            "floor_count": summary.get("floor_count", len(floors)),
            "ollama_enabled_floor_count": summary.get("ollama_enabled_floor_count"),
            "resident_floor_count": summary.get("resident_floor_count"),
            "staged_floor_count": summary.get("staged_floor_count"),
            "manual_heavy_floor_count": summary.get("manual_heavy_floor_count"),
            "source_top_level_count": summary.get("source_top_level_count", source_inventory.get("top_level_count", 0)),
            "source_file_sample_count": summary.get("source_file_sample_count", source_inventory.get("sampled_file_count", 0)),
            "assimilation_draw_path_count": summary.get("assimilation_draw_path_count"),
            "chat_ready_floor_count": summary.get("chat_ready_floor_count"),
            "buildout_stage_count": summary.get("buildout_stage_count"),
            "ui_simplification_state": summary.get("ui_simplification_state"),
            "wake_sequence": payload.get("wake_sequence") or [],
            "floors": floors[: max(0, top_n)],
            "by_floor": by_floor,
            "ui_simplification": payload.get("ui_simplification") or {},
            "buildout_phase": payload.get("buildout_phase") or {},
        }

    def local_agent_receipt_summary(self) -> dict:
        payload = self.local_agent_wakeup()
        receipt_sources = self._local_agent_receipt_sources(payload)
        receipts: list[dict[str, Any]] = []
        by_floor: dict[str, list[dict[str, Any]]] = {}

        for source in receipt_sources:
            source_path = source["path"]
            source_payload = _read_json_file(source_path)
            source_receipts = source_payload.get("local_agent_receipts") if source_payload else None
            if not isinstance(source_receipts, list):
                continue
            for index, receipt in enumerate(source_receipts):
                if not isinstance(receipt, dict):
                    continue
                floor = str(
                    receipt.get("floor")
                    or receipt.get("owner_floor")
                    or receipt.get("target_floor")
                    or source.get("default_floor")
                    or "Neo"
                )
                row = {
                    "receipt_id": (
                        receipt.get("receipt_id")
                        or receipt.get("task_id")
                        or receipt.get("artifact_id")
                        or f"{source['source_id']}_{index + 1}"
                    ),
                    "floor": floor,
                    "source_id": source["source_id"],
                    "source_path": str(source_path),
                    "status": receipt.get("status") or receipt.get("state") or source_payload.get("state"),
                    "run_id": receipt.get("run_id") or source_payload.get("contract_id"),
                    "artifact_type": receipt.get("artifact_type") or "local_agent_receipt",
                    "summary": receipt.get("summary") or receipt.get("message") or receipt.get("label"),
                    "next_action": receipt.get("next_action") or source_payload.get("next_action"),
                    "raw": receipt,
                }
                receipts.append(row)
                by_floor.setdefault(floor, []).append(row)

        return {
            "receipt_count": len(receipts),
            "source_count": len(receipt_sources),
            "sources": [
                {
                    "source_id": item["source_id"],
                    "path": str(item["path"]),
                    "exists": item["path"].exists(),
                }
                for item in receipt_sources
            ],
            "by_floor": by_floor,
            "receipts": receipts,
        }

    def smart_floor_artifact_summary(self, *, source_top_n: int = 5) -> dict:
        payload = self.local_agent_wakeup()
        floors = _expect_list(payload.get("floors") or [], "local_agent_wakeup.floors")
        buildout_phase = payload.get("buildout_phase") if isinstance(payload.get("buildout_phase"), dict) else {}
        receipt_summary = self.local_agent_receipt_summary()
        receipt_by_floor = receipt_summary.get("by_floor") or {}
        stage_rows = _expect_list(buildout_phase.get("stages") or [], "local_agent_wakeup.buildout_phase.stages")
        current_stage = next(
            (item for item in stage_rows if item.get("state") in {"ready", "ready_attach_only", "ready_no_risk_seed"}),
            stage_rows[0] if stage_rows else {},
        )

        artifacts: list[dict[str, Any]] = []
        by_floor: dict[str, dict[str, Any]] = {}
        for order, floor_packet in enumerate(floors, start=1):
            floor = str(floor_packet.get("floor") or f"floor_{order}")
            agent = floor_packet.get("agent") if isinstance(floor_packet.get("agent"), dict) else {}
            connection = floor_packet.get("ollama_connection") if isinstance(floor_packet.get("ollama_connection"), dict) else {}
            activation = floor_packet.get("activation") if isinstance(floor_packet.get("activation"), dict) else {}
            draw = floor_packet.get("assimilation_draw") if isinstance(floor_packet.get("assimilation_draw"), dict) else {}
            priority_paths = _expect_list(draw.get("priority_paths") or [], f"local_agent_wakeup.floors.{floor}.priority_paths")
            chat = floor_packet.get("ai_chat_enablement") if isinstance(floor_packet.get("ai_chat_enablement"), dict) else {}
            floor_receipts = receipt_by_floor.get(floor) or []
            first_source = priority_paths[0] if priority_paths else {}
            packet_path = floor_packet.get("packet_path")
            packet_exists = bool(isinstance(packet_path, str) and packet_path and Path(packet_path).exists())
            receipt_status = "receipt_backed" if floor_receipts else "packet_staged"
            artifact = {
                "floor": floor,
                "agent": agent.get("label") or agent.get("agent_id") or floor,
                "agent_id": agent.get("agent_id"),
                "model": connection.get("model"),
                "artifact_type": "smart_floor_wakeup_packet",
                "source_path": first_source.get("path"),
                "source_relative_path": first_source.get("relative_path"),
                "source_draw_count": len(priority_paths),
                "source_draws": [
                    {
                        "name": item.get("name"),
                        "relative_path": item.get("relative_path"),
                        "path": item.get("path"),
                        "kind": item.get("kind"),
                        "priority_score": item.get("priority_score"),
                    }
                    for item in priority_paths[: max(0, source_top_n)]
                ],
                "packet_path": packet_path,
                "provenance": {
                    "source_root": draw.get("source_root") or payload.get("source_root"),
                    "routing_rule": draw.get("routing_rule"),
                    "packet_exists": packet_exists,
                    "source_policy": "attach_only",
                    "receipt_count": len(floor_receipts),
                    "receipt_status": receipt_status,
                    "receipt_ids": [item.get("receipt_id") for item in floor_receipts if item.get("receipt_id")],
                },
                "status": activation.get("wake_state") or chat.get("state") or receipt_status,
                "activation_mode": activation.get("mode"),
                "buildout_stage": {
                    "phase_id": buildout_phase.get("phase_id"),
                    "phase_state": buildout_phase.get("state"),
                    "stage_id": current_stage.get("stage_id"),
                    "stage_state": current_stage.get("state"),
                    "stage_goal": current_stage.get("goal"),
                },
                "next_action": floor_packet.get("next_safe_action") or chat.get("next_action"),
                "routing_target": {
                    "entry_surface": chat.get("entry_surface") or (payload.get("ui_simplification") or {}).get("entry_surface"),
                    "chat_modes": chat.get("chat_modes") or [],
                    "target_floor": floor,
                    "full_floor_drill_in": "explicit_only",
                },
            }
            artifacts.append(artifact)
            by_floor[floor] = artifact

        return {
            "contract_id": payload.get("contract_id"),
            "generated_at": payload.get("generated_at"),
            "artifact_type": "smart_floor_artifact_summary",
            "floor_count": len(floors),
            "artifact_count": len(artifacts),
            "receipt_count": receipt_summary.get("receipt_count", 0),
            "buildout_phase_state": buildout_phase.get("state"),
            "ui_entry_surface": (payload.get("ui_simplification") or {}).get("entry_surface"),
            "artifacts": artifacts,
            "by_floor": by_floor,
            "receipt_summary": receipt_summary,
        }

    def floor_alignment_summary(self) -> dict:
        floor_models = self.floor_model_summary()
        population = self.agent_population_summary()
        staging = self.input_staging_summary()
        stage = self.floor_stage_population_summary()
        lanes = self.workspace_lane_summary()
        spaces = self.smart_floor_space_summary()
        tasks = self.gated_build_task_summary(top_n=64)

        display_order = list(stage.get("boot_lane_order") or [])
        lane_rows = _expect_list(lanes.get("lanes") or [], "workspace_lanes.summary.lanes")
        space_rows = _expect_list(spaces.get("spaces") or [], "smart_floor_spaces.summary.spaces")
        task_rows = _expect_list(tasks.get("top_tasks") or [], "gated_build_tasks.summary.top_tasks")
        stage_profiles = stage.get("floor_profiles") or {}
        floor_entries: dict[str, dict[str, Any]] = {}

        known_floors = set(display_order)
        known_floors.update((floor_models.get("by_floor") or {}).keys())
        known_floors.update(str(item.get("owner_floor")) for item in lane_rows if item.get("owner_floor"))
        known_floors.update(str(item.get("floor")) for item in space_rows if item.get("floor"))
        known_floors.update(str(item.get("owner_floor")) for item in task_rows if item.get("owner_floor"))

        for floor in sorted(item for item in known_floors if item):
            model = (floor_models.get("by_floor") or {}).get(floor) or {}
            stage_profile = stage_profiles.get(floor) or {}
            floor_lanes = [item for item in lane_rows if item.get("owner_floor") == floor]
            floor_spaces = [item for item in space_rows if item.get("floor") == floor]
            floor_tasks = [item for item in task_rows if item.get("owner_floor") == floor]
            population_assignment = (population.get("by_floor") or {}).get(floor) or {}
            staging_row = (staging.get("by_floor") or {}).get(floor) or {}
            ready_task_count = sum(1 for item in floor_tasks if str(item.get("state") or "").startswith("ready"))
            ready_space_count = sum(1 for item in floor_spaces if str(item.get("status") or "").startswith("ready"))
            primary_space = floor_spaces[0] if floor_spaces else {}
            activation_mode = stage_profile.get("population_mode") or "unknown"
            primary_status = (
                primary_space.get("status")
                or ("ready_for_population" if ready_task_count else "planned")
            )
            floor_entries[floor] = {
                "floor": floor,
                "model": model.get("model"),
                "persona": model.get("persona"),
                "workspace_scope": model.get("workspace_scope"),
                "enabled": bool(model.get("enabled")),
                "population_mode": activation_mode,
                "boot_priority": stage_profile.get("boot_priority"),
                "stage_reason": stage_profile.get("reason"),
                "assigned_agent_id": population_assignment.get("assigned_agent_id"),
                "assigned_agent_label": population_assignment.get("assigned_agent_label"),
                "resident_host_application": population_assignment.get("resident_host_application"),
                "de_sporte_support_resident_id": population_assignment.get("de_sporte_support_resident_id"),
                "support_state": population_assignment.get("support_state"),
                "primary_status": primary_status,
                "primary_space": {
                    "space_id": primary_space.get("space_id"),
                    "label": primary_space.get("label"),
                    "status": primary_space.get("status"),
                    "default_view": primary_space.get("default_view"),
                },
                "lane_count": len(floor_lanes),
                "space_count": len(floor_spaces),
                "task_count": len(floor_tasks),
                "ready_space_count": ready_space_count,
                "ready_task_count": ready_task_count,
                "staging_component_count": staging_row.get("component_count", 0),
                "live_component_count": staging_row.get("path_exists_count", 0),
                "component_ids": staging_row.get("component_ids") or [],
                "components": staging_row.get("components") or [],
                "lanes": floor_lanes,
                "spaces": floor_spaces,
                "tasks": floor_tasks,
            }

        for floor in floor_entries:
            if floor not in display_order:
                display_order.append(floor)

        return {
            "display_order": display_order,
            "total_floors": len(floor_entries),
            "floors": floor_entries,
        }

    def summary(self) -> dict:
        environment = self.agent_environment()
        return {
            "profile_id": environment.get("profile_id"),
            "generated_at": environment.get("generated_at"),
            "truth_registry": self.truth_registry_summary(),
            "floor_models": self.floor_model_summary(),
            "deployment_topology": self.deployment_topology_summary(),
            "host_runtime_policy": self.host_runtime_policy_summary(),
            "neo_local_runtime": self.neo_local_runtime_summary(),
            "de_sporte_runtime": self.de_sporte_runtime_summary(),
            "neo_realisation_runtime": self.neo_realisation_summary(),
            "upstream_inventory": self.upstream_inventory_summary(),
            "launch_control": self.launch_control_summary(),
            "agent_population": self.agent_population_summary(),
            "input_staging_matrix": self.input_staging_summary(),
            "floor_stage_population": self.floor_stage_population_summary(),
            "construct_runtime": self.construct_runtime_summary(),
            "presence_roster": self.presence_roster_summary(),
            "workspace_lanes": self.workspace_lane_summary(),
            "smart_floor_spaces": self.smart_floor_space_summary(),
            "gated_build_tasks": self.gated_build_task_summary(),
            "web_drive_bridge": self.web_drive_bridge_summary(),
            "agentic_launch_queue": self.agentic_launch_queue_summary(),
            "backend_frontend_build": self.backend_frontend_build_summary(top_n=16),
            "floor_environment_realization": self.floor_environment_realization_summary(top_n=16),
            "local_agent_wakeup": self.local_agent_wakeup_summary(top_n=16),
            "resource_closure": self.resource_closure(),
            "smart_floor_artifacts": self.smart_floor_artifact_summary(source_top_n=5),
            "floor_alignment": self.floor_alignment_summary(),
            "consolidation_queue": self.queue_summary(),
            "overlap_bellcurve": self.overlap_summary(),
        }

    def _local_agent_receipt_sources(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        shell_root_value = payload.get("shell_root")
        if not isinstance(shell_root_value, str) or not shell_root_value:
            return []

        shell_root = Path(shell_root_value)
        return [
            {
                "source_id": "trinity_buildout_contract",
                "path": shell_root / "config" / "buildout_phase_contract.json",
                "default_floor": "Trinity",
            },
            {
                "source_id": "neo_active_task",
                "path": (
                    shell_root
                    / "Z Axis"
                    / "Z+2_Neo"
                    / "data"
                    / "temp_shells"
                    / "active_tasks"
                    / "local_agent_wakeup_2026_05_29.json"
                ),
                "default_floor": "Neo",
            },
            {
                "source_id": "neo_buildout_handoff",
                "path": shell_root / "Z Axis" / "Z+2_Neo" / "data" / "actions" / "buildout_phase_handoff.json",
                "default_floor": "Neo",
            },
            {
                "source_id": "smith_buildout_queue",
                "path": shell_root / "Z Axis" / "Z-3_Smith" / "data" / "staging" / "buildout_phase_queue.json",
                "default_floor": "Smith",
            },
        ]

    def _load_export_or_environment_section(self, name: str) -> Any:
        payload = self._load_json(name, required=False)
        if payload is not None:
            return payload

        environment = self.agent_environment()
        if name not in environment:
            raise FileNotFoundError(f"Missing agent-home export section '{name}' in {self.export_dir}")
        return environment[name]

    def _load_json(self, name: str, *, required: bool = True) -> Any:
        if name in self._cache:
            return self._cache[name]

        try:
            filename = _EXPORT_FILES[name]
        except KeyError as exc:
            raise KeyError(f"Unknown agent-home export: {name}") from exc

        path = self.export_dir / filename
        if not path.exists():
            if required:
                raise FileNotFoundError(f"Missing agent-home export: {path}")
            return None

        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        self._cache[name] = payload
        return payload


def _expect_list(payload: Any, label: str) -> list[dict]:
    if not isinstance(payload, list):
        raise TypeError(f"{label} export must contain a JSON array")
    return payload


def _positive_float(value: Any, default: float) -> float:
    try:
        parsed = float(value)
        return parsed if parsed > 0 else default
    except Exception:
        return default


def _percent_to_share(value: Any, default_percent: float) -> float:
    try:
        parsed = float(value)
    except Exception:
        parsed = default_percent
    return max(parsed, 0.0) / 100.0


def _read_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return payload
