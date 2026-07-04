from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_project_workspace_module(module_name: str, relative_path: str):
    root = Path(__file__).resolve().parents[1]
    z_axis = root / "Z Axis"
    merovingian = z_axis / "Z-4_Merovingian"
    module_path = root / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec and spec.loader

    original_core = sys.modules.get("core")
    original_workspace_package = sys.modules.get("core.project_workspace")
    original_module = sys.modules.get(module_name)

    core_package = sys.modules.setdefault("core", types.ModuleType("core"))
    core_package.__path__ = [str(merovingian / "core")]
    workspace_package = sys.modules.setdefault(
        "core.project_workspace",
        types.ModuleType("core.project_workspace"),
    )
    workspace_package.__path__ = [str(merovingian / "core" / "project_workspace")]

    sys.modules.pop(module_name, None)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    sys_path_before = list(sys.path)
    try:
        sys.path[:0] = [str(root), str(z_axis), str(merovingian)]
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = sys_path_before
        if original_module is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = original_module
        if original_workspace_package is None:
            sys.modules.pop("core.project_workspace", None)
        else:
            sys.modules["core.project_workspace"] = original_workspace_package
        if original_core is None:
            sys.modules.pop("core", None)
        else:
            sys.modules["core"] = original_core

    return module


def _load_contract_modules():
    workspace_types = _load_project_workspace_module(
        "core.project_workspace.workspace_types",
        "Z Axis/Z-4_Merovingian/core/project_workspace/workspace_types.py",
    )
    workspace_creator = _load_project_workspace_module(
        "core.project_workspace.workspace_creator",
        "Z Axis/Z-4_Merovingian/core/project_workspace/workspace_creator.py",
    )
    component_puller = _load_project_workspace_module(
        "core.project_workspace.component_puller",
        "Z Axis/Z-4_Merovingian/core/project_workspace/component_puller.py",
    )
    return workspace_types, workspace_creator, component_puller


def test_workspace_contract_recommendations_are_registry_backed() -> None:
    workspace_types, _, component_puller = _load_contract_modules()
    registry = component_puller.ComponentRegistry()
    registry_ids = set(registry.components)

    missing_by_type = {
        config.workspace_type.value: [
            component_id
            for component_id in config.recommended_components
            if component_id not in registry_ids
        ]
        for config in workspace_types.WORKSPACE_CONFIGS.values()
    }

    assert {name: missing for name, missing in missing_by_type.items() if missing} == {}


def test_workspace_contract_templates_are_registry_backed() -> None:
    workspace_types, _, component_puller = _load_contract_modules()
    registry = component_puller.ComponentRegistry()
    registry_ids = set(registry.components)

    missing_by_template = {
        template_id: [
            item["component_id"]
            for item in template.pre_configured_components
            if item["component_id"] not in registry_ids
        ]
        for template_id, template in workspace_types.WORKSPACE_TEMPLATES.items()
    }

    assert {name: missing for name, missing in missing_by_template.items() if missing} == {}


def test_workspace_contract_recommended_components_match_creator_floor_lookup(tmp_path: Path) -> None:
    workspace_types, workspace_creator, component_puller = _load_contract_modules()
    creator = workspace_creator.ProjectWorkspaceCreator(base_path=tmp_path)
    registry = component_puller.ComponentRegistry()

    mismatches: list[tuple[str, str, str | None, str]] = []
    for config in workspace_types.WORKSPACE_CONFIGS.values():
        for component_id in config.recommended_components:
            metadata = registry.get_component(component_id)
            assert metadata is not None, component_id
            floor_from_creator = creator._find_component_floor(component_id)
            if floor_from_creator != metadata.z_floor:
                mismatches.append(
                    (
                        config.workspace_type.value,
                        component_id,
                        floor_from_creator,
                        metadata.z_floor,
                    )
                )

    assert mismatches == []


def test_workspace_contract_template_components_match_creator_floor_lookup(tmp_path: Path) -> None:
    workspace_types, workspace_creator, component_puller = _load_contract_modules()
    creator = workspace_creator.ProjectWorkspaceCreator(base_path=tmp_path)
    registry = component_puller.ComponentRegistry()

    mismatches: list[tuple[str, str, str | None, str]] = []
    for template_id, template in workspace_types.WORKSPACE_TEMPLATES.items():
        for item in template.pre_configured_components:
            component_id = item["component_id"]
            metadata = registry.get_component(component_id)
            assert metadata is not None, component_id
            floor_from_creator = creator._find_component_floor(component_id)
            if floor_from_creator != metadata.z_floor:
                mismatches.append(
                    (
                        template_id,
                        component_id,
                        floor_from_creator,
                        metadata.z_floor,
                    )
                )

    assert mismatches == []


def test_workspace_contract_live_registry_metadata_stays_on_active_surfaces() -> None:
    _, _, component_puller = _load_contract_modules()
    registry = component_puller.ComponentRegistry()

    expected_metadata = {
        "performance_tracker": (
            "Z_Axis.Z-4_Merovingian.components.performance_profiler",
            "PerformanceProfilerGUI",
        ),
        "task_queue_monitor": (
            "Z_Axis.Z-3_Smith.components.smith_task_queue",
            "SmithTaskQueue",
        ),
        "archive_browser": (
            "Z_Axis.Z-1_Morpheus.components.chat_archive_browser",
            "ChatArchiveBrowser",
        ),
        "documentation_browser": (
            "Z_Axis.Z-1_Morpheus.components.rich_text_editor",
            "MarkdownPreview",
        ),
        "model_trainer": (
            "Z_Axis.Z+2_Neo.components.ai_training",
            "AITrainingGUI",
        ),
        "timeline_view": (
            "Z_Axis.Z+1_Architect.components.progress_widget",
            "TimelineProgress",
        ),
        "milestone_tracker": (
            "Z_Axis.Z+1_Architect.components.progress_widget",
            "TaskChecklist",
        ),
        "theme_manager": (
            "Z_Axis.Z+3_Trinity.components.theme_switcher",
            "ThemeDesigner",
        ),
        "chart_renderer": (
            "Z_Axis.Z+3_Trinity.components.analytics_dashboard",
            "MetricChart",
        ),
    }

    for component_id, (python_module, ui_class) in expected_metadata.items():
        metadata = registry.get_component(component_id)
        assert metadata is not None, component_id
        assert metadata.python_module == python_module
        assert metadata.ui_class == ui_class


def test_workspace_contract_required_floors_cover_registry_backed_components() -> None:
    workspace_types, _, component_puller = _load_contract_modules()
    registry = component_puller.ComponentRegistry()

    missing_by_workspace = {}
    for config in workspace_types.WORKSPACE_CONFIGS.values():
        missing = []
        for component_id in config.recommended_components:
            metadata = registry.get_component(component_id)
            assert metadata is not None, component_id
            if metadata.z_floor not in config.required_z_floors:
                missing.append((component_id, metadata.z_floor))
        if missing:
            missing_by_workspace[config.workspace_type.value] = missing

    missing_by_template = {}
    for template_id, template in workspace_types.WORKSPACE_TEMPLATES.items():
        config = workspace_types.WORKSPACE_CONFIGS[template.workspace_type]
        missing = []
        for item in template.pre_configured_components:
            component_id = item["component_id"]
            metadata = registry.get_component(component_id)
            assert metadata is not None, component_id
            if metadata.z_floor not in config.required_z_floors:
                missing.append((component_id, metadata.z_floor))
        if missing:
            missing_by_template[template_id] = missing

    assert missing_by_workspace == {}
    assert missing_by_template == {}


def test_workspace_contract_registry_filter_normalizes_workspace_type_values() -> None:
    workspace_types, _, component_puller = _load_contract_modules()
    registry = component_puller.ComponentRegistry()

    research_ids = {
        metadata.component_id
        for metadata in registry.list_components(workspace_type=workspace_types.WorkspaceType.RESEARCH)
    }
    research_ids_from_string = {
        metadata.component_id
        for metadata in registry.list_components(workspace_type="research")
    }

    assert research_ids == research_ids_from_string
    assert {
        "cognigrex_ai",
        "data_analyzer",
        "knowledge_graph",
        "document_vault",
        "chart_renderer",
    }.issubset(research_ids)
    assert "gmat_launcher" not in research_ids


def test_workspace_contract_broad_defaults_reduce_only_when_contract_backed() -> None:
    _, _, component_puller = _load_contract_modules()
    registry = component_puller.ComponentRegistry()

    document_vault = registry.get_component("document_vault")
    widget_gallery = registry.get_component("widget_gallery")

    assert document_vault is not None
    assert widget_gallery is not None
    assert set(document_vault.compatible_workspace_type_values()) == {
        "research",
        "engineering",
        "documentation",
        "collaboration",
    }
    assert set(widget_gallery.compatible_workspace_type_values()) == {
        workspace_type.value for workspace_type in component_puller.WorkspaceType
    }


def test_workspace_creator_template_and_recommendations_do_not_duplicate_components(tmp_path: Path) -> None:
    _, workspace_creator, _ = _load_contract_modules()
    creator = workspace_creator.ProjectWorkspaceCreator(base_path=tmp_path)

    workspace = creator.create_workspace(
        name="Research Paper",
        workspace_type=workspace_creator.WorkspaceType.RESEARCH,
        template_id="research_paper",
    )

    component_ids = [component.component_id for component in workspace.components]
    assert len(component_ids) == len(set(component_ids))
    assert "Z+3_Trinity" in workspace.available_z_floors


def test_workspace_creator_syncs_available_floors_for_custom_components(tmp_path: Path) -> None:
    _, workspace_creator, _ = _load_contract_modules()
    creator = workspace_creator.ProjectWorkspaceCreator(base_path=tmp_path)

    workspace = creator.create_workspace(
        name="Collaboration Custom",
        workspace_type=workspace_creator.WorkspaceType.COLLABORATION,
        custom_components=[
            {
                "component_id": "chart_renderer",
                "position": {"theta": 0, "phi": 0, "depth": 0.8},
                "config": {},
            }
        ],
    )

    assert "Z+3_Trinity" in workspace.available_z_floors
