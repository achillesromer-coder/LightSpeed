from __future__ import annotations

from pathlib import Path
import sys

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime.operator_os import build_operator_os_contract
from lightspeed_runtime.protocol_sequence_registry import (
    build_achilles_external_handoff,
    build_protocol_sequence_registry,
    external_endpoint_registry,
    shared_color_control_protocol,
    write_achilles_external_handoff,
    write_protocol_sequence_registry,
    write_protocol_sequence_report,
    z_direct_cache_preload_protocol,
)
from lightspeed_runtime.web_integration import build_romer_web_integration


def test_shared_color_protocol_is_comprehensive_and_reusable() -> None:
    protocol = shared_color_control_protocol()

    assert protocol["owner_floor"] == "Trinity"
    assert {"hex", "rgb", "rgba", "hsl", "hsv", "alpha", "gradient_stop"} <= set(protocol["inputs"])
    assert {"color_wheel", "rgb_sliders", "gradient_builder", "contrast_checker"} <= set(protocol["controls"])
    assert "widget" in protocol["outputs"]["save_scope"]
    assert "bespoke one-off color editor" in protocol["rule"]


def test_z_direct_cache_preload_protocol_caches_descriptors_not_large_payloads() -> None:
    protocol = z_direct_cache_preload_protocol()

    assert protocol["owner_floor"] == "Smith"
    assert "smart-floor widget descriptors" in protocol["preload_scope"]
    assert "large original files" in protocol["do_not_preload"]
    assert protocol["cache_files"]["Trinity"].endswith("smart_floor_widget_export.json")
    assert {"received", "updated", "completed", "deleted", "declassified", "failed"} == set(protocol["handoff_states"])


def test_external_endpoint_registry_covers_library_web_and_future_go_links() -> None:
    endpoints = external_endpoint_registry()
    folders = {folder["id"]: folder for folder in endpoints["drive_folders"]}
    sheets = {sheet["id"]: sheet for sheet in endpoints["spreadsheet_books"]}
    drive_queues = {queue["id"]: queue for queue in endpoints["drive_queue_contracts"]}

    assert folders["library_base"]["connector_status"] == "accessible"
    assert "GMAT_R2025a" in folders["library_base"]["observed_children"]
    assert folders["web_lightspeed_sheets"]["connector_status"] == "accessible_empty_or_staging"
    assert folders["future_lightspeed_go"]["observed_children"] == ["RAW AI Returns", "Nathaniel Bouwer", "Romer Industries"]
    assert "Device Sync" in sheets["desktop_population"]["tabs_required"]
    assert "Phone Tasks" in sheets["future_lightspeed_go_queue"]["tabs_required"]
    assert drive_queues["future_lightspeed_go_drive_queue"]["connector_status"] == "workbook_materialized"
    assert drive_queues["future_lightspeed_go_drive_queue"]["queue_spreadsheet_id"] == "1f5i4V3FshYHkztv3_HAg0ZofUl0sdcJZcwrlesUlCfM"
    assert "Phone Tasks" in drive_queues["future_lightspeed_go_drive_queue"]["required_tables"]
    assert "payload_ref" in endpoints["webhook_contract"]["payload_fields"]


def test_protocol_sequence_registry_populates_operations_and_rules() -> None:
    registry = build_protocol_sequence_registry(RUNTIME_ROOT)
    sequence_ids = {sequence["id"] for sequence in registry["operation_sequences"]}

    assert registry["owner_floor"] == "Trinity"
    assert {"startup_preload", "project_artifact_workflow", "oracle_ingest_morpheus_proof"} <= sequence_ids
    assert "construct_simulation_flow" in sequence_ids
    assert "external_achilles_handoff" in sequence_ids
    assert registry["shared_protocols"]["condensed_file_policy"]["policy"].startswith("Prefer compact indexed tables")
    assert any("Define a protocol once" in rule for rule in registry["rules"])


def test_achilles_external_handoff_contract_is_safe_for_future_phone_dash() -> None:
    handoff = build_achilles_external_handoff(RUNTIME_ROOT)

    assert handoff["owner_floor"] == "Neo"
    assert handoff["queue_owner"] == "Smith"
    assert handoff["safe_defaults"]["external_writes"] == "approval_required"
    assert "approval_required" in handoff["minimum_phone_dash_fields"]
    assert any(folder["id"] == "future_lightspeed_go" for folder in handoff["drive_folders"])


def test_operator_os_and_web_integration_reference_shared_protocols_and_go() -> None:
    operator = build_operator_os_contract(RUNTIME_ROOT)
    web = build_romer_web_integration(RUNTIME_ROOT)

    assert operator["shared_control_protocols"]["color_control"].endswith("shared_color_control_protocol")
    assert operator["shared_control_protocols"]["z_direct_cache_preload"].endswith("z_direct_cache_preload_protocol")
    assert any(source["id"] == "1PkXMyv26BBvvUbxShTRMTwhnEaK_a1qb" for source in web["drive_sources"])
    assert web["webhook_contract"]["owner_floor"] == "Smith"


def test_protocol_registry_writers_create_trinity_neo_and_dataindex_outputs(tmp_path: Path) -> None:
    registry = write_protocol_sequence_registry(tmp_path)
    handoff = write_achilles_external_handoff(tmp_path)
    report = write_protocol_sequence_report(tmp_path)

    assert Path(registry["contract_path"]).exists()
    assert Path(handoff["contract_path"]).exists()
    assert Path(report["path"]).exists()
    assert registry["external_endpoints"]["drive_folders"][2]["id"] == "future_lightspeed_go"
    assert "Protocol Sequence Refinement" in Path(report["path"]).read_text(encoding="utf-8")
