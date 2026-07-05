"""
Template Scenario Tests
=======================

Tests for template-based workflow scenarios.
Validates that scenarios are correctly configured and executable.

Test Categories:
- Scenario template validation
- Workflow execution
- Floor coordination
- Widget configuration
- Settings propagation

Author: LightSpeed Team / ACHILLES
Version: 5.1.1
"""

# CODEX NOTE (2026-02-06):
# - Scenario layouts are treated as an executable spec for Bento grid placement (4x12).
# - Keep widgets non-overlapping; these tests intentionally fail fast on collisions.

import pytest
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from tests.conftest import (
    LIGHTSPEED_ROOT, Z_AXIS_ROOT, FLOOR_PATHS, CANONICAL_FLOORS
)


# ============================================================================
# SCENARIO DEFINITIONS
# ============================================================================

SCENARIO_CATALOG = {
    "data_science_workspace": {
        "id": "scenario_001",
        "name": "Data Science Workspace",
        "description": "Full data science environment with AI assistance and knowledge base",
        "floors_required": ["Z+2_Neo", "Z-1_Morpheus", "Z-4_Merovingian"],
        "widgets": [
            {"id": "ai_chat", "floor": "Z+2_Neo", "position": (0, 0), "size": (2, 4)},
            {"id": "file_browser", "floor": "Z-1_Morpheus", "position": (2, 0), "size": (2, 3)},
            {"id": "data_viewer", "floor": "Z-4_Merovingian", "position": (0, 4), "size": (4, 4)},
        ],
        "settings": {
            "ai_model": "claude-sonnet-4",
            "auto_save": True,
            "theme": "dark_glass",
            "knowledge_sync": True,
        },
        "services": ["event_bus", "settings_hub", "storage"],
    },
    "physics_simulation_lab": {
        "id": "scenario_002",
        "name": "Physics Simulation Lab",
        "description": "Interactive physics simulation environment",
        "floors_required": ["Z0_TheConstruct", "Z-4_Merovingian"],
        "widgets": [
            {"id": "simulation_3d", "floor": "Z0_TheConstruct", "position": (0, 0), "size": (3, 6)},
            {"id": "parameter_panel", "floor": "Z-4_Merovingian", "position": (3, 0), "size": (1, 3)},
            {"id": "results_chart", "floor": "Z-4_Merovingian", "position": (3, 3), "size": (1, 3)},
            {"id": "console_log", "floor": "Z-4_Merovingian", "position": (0, 6), "size": (4, 2)},
        ],
        "settings": {
            "simulation_mode": "interactive",
            "precision": "high",
            "visualization": "3d",
            "auto_render": True,
        },
        "services": ["event_bus", "physics_tools", "cache_manager"],
    },
    "automation_workflow": {
        "id": "scenario_003",
        "name": "Automation Workflow Designer",
        "description": "Task automation and workflow design environment",
        "floors_required": ["Z-3_Smith", "Z+1_Architect", "Z-4_Merovingian"],
        "widgets": [
            {"id": "workflow_designer", "floor": "Z-3_Smith", "position": (0, 0), "size": (3, 5)},
            {"id": "task_queue", "floor": "Z-3_Smith", "position": (3, 0), "size": (1, 3)},
            # Height trimmed to avoid overlap with the execution log strip at y=5.
            {"id": "project_tree", "floor": "Z+1_Architect", "position": (3, 3), "size": (1, 2)},
            {"id": "execution_log", "floor": "Z-4_Merovingian", "position": (0, 5), "size": (4, 3)},
        ],
        "settings": {
            "auto_execute": False,
            "retry_attempts": 3,
            "timeout_seconds": 300,
            "log_level": "info",
        },
        "services": ["event_bus", "task_runner", "workflow_engine"],
    },
    "knowledge_archive": {
        "id": "scenario_004",
        "name": "Knowledge Archive Browser",
        "description": "Browse and manage knowledge base and IP vault",
        "floors_required": ["Z-1_Morpheus", "Z-2_Oracle", "Z+3_Trinity"],
        "widgets": [
            {"id": "knowledge_search", "floor": "Z-1_Morpheus", "position": (0, 0), "size": (4, 2)},
            {"id": "document_viewer", "floor": "Z-1_Morpheus", "position": (0, 2), "size": (3, 5)},
            {"id": "archive_tree", "floor": "Z-2_Oracle", "position": (3, 2), "size": (1, 5)},
            {"id": "metadata_panel", "floor": "Z+3_Trinity", "position": (0, 7), "size": (4, 1)},
        ],
        "settings": {
            "search_depth": "deep",
            "include_archives": True,
            "preview_mode": "rendered",
            "index_on_add": True,
        },
        "services": ["event_bus", "storage", "database"],
    },
    "full_immersive": {
        "id": "scenario_005",
        "name": "Full Immersive Environment",
        "description": "Complete immersive 3D environment with all floor integration",
        "floors_required": list(CANONICAL_FLOORS.keys()),
        "widgets": [
            {"id": "immersive_view", "floor": "Z0_TheConstruct", "position": (0, 0), "size": (4, 8)},
            {"id": "floor_selector", "floor": "Z+3_Trinity", "position": (0, 8), "size": (2, 4)},
            {"id": "quick_actions", "floor": "Z-4_Merovingian", "position": (2, 8), "size": (2, 4)},
        ],
        "settings": {
            "immersive_mode": True,
            "bento_radius": 1.5,
            "wasd_navigation": True,
            "glassmorphism": True,
        },
        "services": ["event_bus", "settings_hub", "floor_manager", "bento_hub"],
    },
}


# ============================================================================
# TEST CLASSES
# ============================================================================

class TestScenarioStructure:
    """Test that scenarios have valid structure."""

    @pytest.mark.parametrize("scenario_id,scenario", list(SCENARIO_CATALOG.items()))
    def test_scenario_has_required_fields(self, scenario_id, scenario):
        """Each scenario should have required fields."""
        required = ["id", "name", "description", "floors_required", "widgets", "settings"]
        for field in required:
            assert field in scenario, f"Scenario {scenario_id} missing field: {field}"

    @pytest.mark.parametrize("scenario_id,scenario", list(SCENARIO_CATALOG.items()))
    def test_scenario_has_valid_floors(self, scenario_id, scenario, canonical_floors):
        """Scenario floors should be valid canonical floors."""
        for floor in scenario["floors_required"]:
            assert floor in canonical_floors, f"Invalid floor in {scenario_id}: {floor}"

    @pytest.mark.parametrize("scenario_id,scenario", list(SCENARIO_CATALOG.items()))
    def test_scenario_widgets_valid(self, scenario_id, scenario):
        """Scenario widgets should have valid configuration."""
        for widget in scenario["widgets"]:
            assert "id" in widget, f"Widget missing id in {scenario_id}"
            assert "floor" in widget, f"Widget {widget.get('id')} missing floor in {scenario_id}"
            assert "position" in widget, f"Widget {widget.get('id')} missing position in {scenario_id}"
            assert "size" in widget, f"Widget {widget.get('id')} missing size in {scenario_id}"

            # Position and size should be tuples of 2
            assert len(widget["position"]) == 2, f"Position should be (x, y)"
            assert len(widget["size"]) == 2, f"Size should be (width, height)"


class TestScenarioFloorAvailability:
    """Test that required floors exist for scenarios."""

    @pytest.mark.parametrize("scenario_id,scenario", list(SCENARIO_CATALOG.items()))
    def test_required_floors_exist(self, scenario_id, scenario, floor_paths):
        """Required floors for each scenario should exist."""
        missing_floors = []
        for floor in scenario["floors_required"]:
            floor_path = floor_paths.get(floor)
            if not floor_path or not floor_path.exists():
                missing_floors.append(floor)

        assert len(missing_floors) == 0, f"Missing floors for {scenario_id}: {missing_floors}"


class TestScenarioWidgetPlacement:
    """Test widget placement validation."""

    BENTO_GRID = {"cols": 4, "rows": 12}

    @pytest.mark.parametrize("scenario_id,scenario", list(SCENARIO_CATALOG.items()))
    def test_widgets_fit_in_grid(self, scenario_id, scenario):
        """All widgets should fit within Bento grid."""
        for widget in scenario["widgets"]:
            x, y = widget["position"]
            w, h = widget["size"]

            # Check bounds
            assert x >= 0, f"Widget {widget['id']} has negative x position"
            assert y >= 0, f"Widget {widget['id']} has negative y position"
            assert x + w <= self.BENTO_GRID["cols"], f"Widget {widget['id']} exceeds column bounds"
            assert y + h <= self.BENTO_GRID["rows"], f"Widget {widget['id']} exceeds row bounds"

    @pytest.mark.parametrize("scenario_id,scenario", list(SCENARIO_CATALOG.items()))
    def test_no_widget_overlap(self, scenario_id, scenario):
        """Widgets should not overlap."""
        occupied = set()

        for widget in scenario["widgets"]:
            x, y = widget["position"]
            w, h = widget["size"]

            # Check each cell
            for dx in range(w):
                for dy in range(h):
                    cell = (x + dx, y + dy)
                    if cell in occupied:
                        pytest.fail(f"Widget overlap at {cell} in {scenario_id}")
                    occupied.add(cell)


class TestScenarioSettings:
    """Test scenario settings validation."""

    @pytest.mark.parametrize("scenario_id,scenario", list(SCENARIO_CATALOG.items()))
    def test_settings_not_empty(self, scenario_id, scenario):
        """Each scenario should have settings."""
        assert len(scenario["settings"]) > 0, f"Scenario {scenario_id} has no settings"

    @pytest.mark.parametrize("scenario_id,scenario", list(SCENARIO_CATALOG.items()))
    def test_settings_values_valid_types(self, scenario_id, scenario):
        """Settings values should be valid types."""
        valid_types = (str, int, float, bool, list, dict, type(None))
        for key, value in scenario["settings"].items():
            assert isinstance(value, valid_types), f"Invalid setting type for {key} in {scenario_id}"


class TestScenarioServices:
    """Test scenario service requirements."""

    CORE_SERVICES = ["event_bus", "settings_hub", "database", "storage", "cache_manager"]

    @pytest.mark.parametrize("scenario_id,scenario", list(SCENARIO_CATALOG.items()))
    def test_scenario_has_services(self, scenario_id, scenario):
        """Each scenario should specify required services."""
        if "services" in scenario:
            assert len(scenario["services"]) > 0, f"Services list empty for {scenario_id}"

    @pytest.mark.parametrize("scenario_id,scenario", list(SCENARIO_CATALOG.items()))
    def test_event_bus_required(self, scenario_id, scenario):
        """Event bus should be required for all multi-floor scenarios."""
        if len(scenario["floors_required"]) > 1:
            if "services" in scenario:
                assert "event_bus" in scenario["services"], f"Multi-floor scenario {scenario_id} missing event_bus"


class TestScenarioExecution:
    """Test scenario execution simulation."""

    def test_scenario_initialization_flow(self, scenario_templates, mock_event_bus):
        """Test scenario initialization event flow."""
        scenario = scenario_templates["data_science"]

        # Simulate initialization events
        events = []

        def track_event(event):
            events.append(event)

        mock_event_bus.subscribe("scenario.*", track_event)
        mock_event_bus.subscribe("floor.*", track_event)
        mock_event_bus.subscribe("widget.*", track_event)

        # Publish initialization sequence
        mock_event_bus.publish("scenario.loading", {"scenario": scenario["name"]})

        for floor in scenario["floors"]:
            mock_event_bus.publish(f"floor.{floor}.activate", {"scenario": scenario["name"]})

        for widget in scenario["widgets"]:
            mock_event_bus.publish(f"widget.{widget}.register", {"floor": "unknown"})

        mock_event_bus.publish("scenario.ready", {"scenario": scenario["name"]})

        # Check event sequence
        history = mock_event_bus.get_history()
        assert len(history) >= 4, "Expected at least 4 initialization events"

    def test_scenario_settings_propagation(self, scenario_templates, mock_event_bus):
        """Test that scenario settings are propagated."""
        scenario = scenario_templates["data_science"]
        settings_events = []

        def track_settings(event):
            settings_events.append(event)

        mock_event_bus.subscribe("settings.*", track_settings)

        # Publish settings
        for key, value in scenario["settings"].items():
            mock_event_bus.publish("settings.change", {"key": key, "value": value})

        assert len(settings_events) == len(scenario["settings"])


class TestScenarioPersistence:
    """Test scenario save/load functionality."""

    def test_scenario_serialization(self, temp_test_dir):
        """Scenarios should be serializable to JSON."""
        scenario = SCENARIO_CATALOG["data_science_workspace"]

        # Serialize
        json_path = temp_test_dir / "scenario.json"
        with open(json_path, "w") as f:
            json.dump(scenario, f, indent=2)

        # Deserialize
        with open(json_path, "r") as f:
            loaded = json.load(f)

        assert loaded["id"] == scenario["id"]
        assert loaded["name"] == scenario["name"]
        assert len(loaded["widgets"]) == len(scenario["widgets"])

    def test_scenario_catalog_export(self, temp_test_dir):
        """Full scenario catalog should be exportable."""
        catalog_path = temp_test_dir / "scenario_catalog.json"

        with open(catalog_path, "w") as f:
            json.dump(SCENARIO_CATALOG, f, indent=2)

        with open(catalog_path, "r") as f:
            loaded = json.load(f)

        assert len(loaded) == len(SCENARIO_CATALOG)


class TestScenarioValidation:
    """Comprehensive scenario validation."""

    def test_all_scenarios_valid(self):
        """Run comprehensive validation on all scenarios."""
        errors = []

        for scenario_id, scenario in SCENARIO_CATALOG.items():
            # Check ID uniqueness
            ids = [s["id"] for s in SCENARIO_CATALOG.values()]
            if ids.count(scenario["id"]) > 1:
                errors.append(f"Duplicate scenario ID: {scenario['id']}")

            # Check floor dependencies
            for widget in scenario["widgets"]:
                if widget["floor"] not in scenario["floors_required"]:
                    errors.append(f"Widget {widget['id']} on unrequired floor in {scenario_id}")

        assert len(errors) == 0, f"Validation errors: {errors}"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
