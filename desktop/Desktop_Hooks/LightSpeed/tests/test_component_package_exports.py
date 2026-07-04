from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_component_package(module_name: str, init_relative_path: str):
    root = Path(__file__).resolve().parents[1]
    z_axis = root / "Z Axis"
    package_root = root / init_relative_path
    spec = importlib.util.spec_from_file_location(
        module_name,
        package_root / "__init__.py",
        submodule_search_locations=[str(package_root)],
    )
    assert spec and spec.loader

    original_module = sys.modules.get(module_name)
    sys_path_before = list(sys.path)
    try:
        sys.path[:0] = [str(root), str(z_axis), str(package_root.parent)]
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = sys_path_before
        if original_module is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = original_module


def test_component_package_exports_remain_unique_and_live_surface_backed() -> None:
    packages = {
        "Architect": (
            "Z Axis/Z+1_Architect/components",
            {"ArchitectPortalGlass", "DBTaskBoard", "DevToolsPortalGlass", "TaskChecklist", "TimelineProgress"},
            {"TankPortalGlass", "PortalTheme", "DevEnvironment", "DevTool"},
        ),
        "Neo": (
            "Z Axis/Z+2_Neo/components",
            {"AICodeAssistantGUI", "AIContextGUI", "AITrainingGUI", "CognigrexFoundation", "CognigrexGUI", "NEOLabAssistant"},
            {"CompletionRequest", "CompletionResponse", "ContextItem", "TrainingDataset", "ResearchWorkspace"},
        ),
        "Oracle": (
            "Z Axis/Z-2_Oracle/components",
            {"EncyclopediaSystem", "OraclePortalGlass", "OracleSmartFloorIntegrator", "OracleUIPanel", "SmartFloorIngestion"},
            {"PortalTheme", "FileIngestionTask", "ExtractedObject"},
        ),
    }

    for floor_name, (relative_path, required_exports, removed_from_all) in packages.items():
        module = _load_component_package(f"test_{floor_name.lower()}_components_exports", relative_path)
        exported_names = list(module.__all__)

        assert len(exported_names) == len(set(exported_names)), floor_name
        for name in required_exports:
            assert name in exported_names, f"{floor_name}:{name}"
        for name in removed_from_all:
            assert name not in exported_names, f"{floor_name}:{name}"


def test_oracle_component_package_exports_smart_floor_ingestion_once() -> None:
    module = _load_component_package(
        "test_oracle_components_exports_unique",
        "Z Axis/Z-2_Oracle/components",
    )

    assert module.__all__.count("SmartFloorIngestion") == 1


def test_component_packages_keep_compatibility_attributes_without_reexporting_them() -> None:
    architect = _load_component_package(
        "test_architect_components_compatibility_attrs",
        "Z Axis/Z+1_Architect/components",
    )
    assert architect.TankPortalGlass is architect.DevToolsPortalGlass
    assert "TankPortalGlass" not in architect.__all__

    neo = _load_component_package(
        "test_neo_components_compatibility_attrs",
        "Z Axis/Z+2_Neo/components",
    )
    for name in ("CompletionRequest", "CompletionResponse", "ContextItem", "TrainingDataset", "ResearchWorkspace"):
        assert hasattr(neo, name), name
        assert name not in neo.__all__, name

    oracle = _load_component_package(
        "test_oracle_components_compatibility_attrs",
        "Z Axis/Z-2_Oracle/components",
    )
    assert oracle.SmartFloorIngestion.__module__.endswith("oracle_ui_panel")
    for name in ("PortalTheme", "FileIngestionTask", "ExtractedObject"):
        assert hasattr(oracle, name), name
        assert name not in oracle.__all__, name
