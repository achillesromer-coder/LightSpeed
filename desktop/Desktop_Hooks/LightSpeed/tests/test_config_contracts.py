from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = ROOT / "config"


def _load_config(relative_path: str) -> dict:
    return json.loads((CONFIG_ROOT / relative_path).read_text(encoding="utf-8"))


def test_core_versions_and_schema_contracts_align() -> None:
    settings = _load_config("settings.json")
    lightspeed = _load_config("lightspeed_config.json")
    unified = _load_config("unified_config.json")
    user = _load_config("user_config.json")
    setup = _load_config("cognigrex_setup_state.json")

    assert settings["app_version"] == "5.1.2"
    assert lightspeed["platform"]["version"] == "5.1.2"
    assert unified["system"]["version"] == "5.1.2"
    assert user["version"] == "5.1.2"
    assert setup["version"] == "5.1.2"

    assert settings["config_schema_version"] == "2026.04.finalization"
    assert lightspeed["config_schema_version"] == "2026.04.finalization"
    assert unified["config_schema_version"] == "2026.04.finalization"
    assert user["profile_contract_version"] == "2026.04.finalization"
    assert setup["setup_contract_version"] == "2026.04.finalization"


def test_settings_and_logging_paths_are_floor_owned() -> None:
    settings = _load_config("settings.json")
    unified = _load_config("unified_config.json")

    assert settings["db_path"].startswith("Z Axis/")
    assert settings["log_file_path"].startswith("Z Axis/Z-4_Merovingian/")
    assert settings["activity_table_path"].startswith("Z Axis/Z-4_Merovingian/")
    assert settings["approval_ledger_path"].startswith("Z Axis/Z+1_Architect/")

    assert unified["database"]["path"].startswith("Z Axis/Z-4_Merovingian/")
    assert unified["trinity_storage"]["base_path"].startswith("Z Axis/Z+3_Trinity/")


def test_unified_config_uses_canonical_floor_ids() -> None:
    unified = _load_config("unified_config.json")
    expected = {
        "Z+3_Trinity",
        "Z+2_Neo",
        "Z+1_Architect",
        "Z0_TheConstruct",
        "Z-1_Morpheus",
        "Z-2_Oracle",
        "Z-3_Smith",
        "Z-4_Merovingian",
    }

    assert set(unified["z_floors"]) == expected
    for floor_id, record in unified["z_floors"].items():
        assert record["canonical_id"] == floor_id


def test_api_bridge_uses_folder_url_not_api_key() -> None:
    apis = _load_config("apis.json")["apis"]
    drive = apis["google_drive"]

    assert drive["api_key"] == ""
    assert drive["config"]["folder_id"] == "1clPyKU1C_Prd-a4g-Cbl2RZQybLL2oag"
    assert drive["config"]["shared_folder_url"].startswith("https://drive.google.com/drive/folders/")


def test_runtime_reservoirs_are_proofed() -> None:
    reservoirs = _load_config("runtime/runtime_reservoirs.json")
    sources = reservoirs["sources"]

    assert reservoirs["catalog_policy"]["default_view"] == "curated_first"
    assert reservoirs["catalog_policy"]["raw_sources_secondary"] is True
    assert sources
    for source in sources:
        assert source["source_label"]
        assert source["definition"]
        assert source["operator_notes"]
        assert source["classification"]
        assert source["floor_owner"]


def test_curated_function_catalogs_are_compact() -> None:
    user = _load_config("user_config.json")
    registry = _load_config("function_registry.json")

    grouped = user["detected_functions"]
    total_user_entries = sum(len(items) for items in grouped.values())
    assert total_user_entries <= 12

    functions = registry["functions"]
    libraries = registry["libraries"]
    assert "core_floor_loader" in functions
    assert "core_smart_floor_expansion" in functions
    assert any(entry.get("floor") == "Oracle" for entry in functions.values())
    assert any(entry.get("floor") == "Merovingian" for entry in functions.values())
    assert len(libraries) >= 10
    assert libraries["numpy"]["available"] is True
    assert libraries["duckdb"]["description"] == "Local analytical query engine"


def test_ui_contracts_prefer_function_first_surfaces() -> None:
    z_direct = _load_config("z_direct_template.json")
    theme = _load_config("premium_theme_config.json")

    assert z_direct["interaction_contract"]["search_access"] == "ctrl_s"
    assert z_direct["interaction_contract"]["settings_access"] == "visible_page_menu_or_ctrl_shift_s"
    assert "grouped_actions" in z_direct["function_first_design"]["build_capabilities_as"]
    assert z_direct["operator_os_project_contract"]["landing_page"] == "project_bento_dashboard"
    assert "smart_preview_tiles" in z_direct["operator_os_project_contract"]["component_set_contents"]
    assert theme["operator_surface_contract"]["blank_pages_allowed"] is False
    assert theme["operator_surface_contract"]["search_shortcut"] == "Ctrl+S"
    assert theme["accessibility"]["settings_shortcut"] == "Ctrl+Shift+S"
    assert "uploaded_environment_reference" in theme["editable_backgrounds"]["inputs"]
