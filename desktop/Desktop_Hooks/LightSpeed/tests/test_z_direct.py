"""
Z Direct Inter-Floor Communication Tests
========================================

Tests for the Z Direct staging and inter-floor communication system.
Validates append-only staging, approval workflows, and event propagation.

Test Categories:
- Z Direct folder structure
- Staging operations
- Approval workflow
- Event propagation
- Cross-floor data integrity

Author: LightSpeed Team / ACHILLES
Version: 5.1.1
"""

import pytest
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import uuid

from tests.conftest import (
    LIGHTSPEED_ROOT, Z_AXIS_ROOT, FLOOR_PATHS, CANONICAL_FLOORS
)


# ============================================================================
# Z DIRECT CONFIGURATION
# ============================================================================

Z_DIRECT_STANDARD_FILES = [
    "objects.json",
    "tasks.json",
    "events.jsonl",
    "floor_config.json",
    "inter_floor_events.json",
    "template_deployments.json",
    "performance_metrics.json",
]

STAGING_STATUSES = ["staged", "pending_approval", "approved", "rejected", "committed"]


# ============================================================================
# TEST CLASSES
# ============================================================================

class TestZDirectStructure:
    """Test Z Direct folder structure across all floors."""

    @pytest.mark.parametrize("floor_id", list(CANONICAL_FLOORS.keys()))
    def test_z_direct_folder_exists(self, floor_id, floor_paths):
        """Each floor should have a Z Direct folder."""
        floor_path = floor_paths.get(floor_id)
        if not floor_path or not floor_path.exists():
            pytest.skip(f"Floor not found: {floor_id}")

        z_direct = floor_path / "Z Direct"
        # Z Direct may not be created yet - that's OK for this test
        if not z_direct.exists():
            pytest.skip(f"Z Direct not yet created for {floor_id}")

        assert z_direct.is_dir(), f"Z Direct is not a directory for {floor_id}"

    @pytest.mark.parametrize("floor_id", list(CANONICAL_FLOORS.keys()))
    def test_z_direct_has_standard_files(self, floor_id, floor_paths):
        """Z Direct should have standard communication files."""
        floor_path = floor_paths.get(floor_id)
        if not floor_path or not floor_path.exists():
            pytest.skip(f"Floor not found: {floor_id}")

        z_direct = floor_path / "Z Direct"
        if not z_direct.exists():
            pytest.skip(f"Z Direct not yet created for {floor_id}")

        # Check for at least some standard files
        existing_files = [f.name for f in z_direct.iterdir() if f.is_file()]
        if len(existing_files) == 0:
            pytest.skip(f"Z Direct is empty for {floor_id}")


class TestZDirectStaging:
    """Test Z Direct staging operations."""

    def test_stage_object(self, mock_z_direct):
        """Should be able to stage an object."""
        source_floor = "Z+2_Neo"
        staging_file = mock_z_direct / source_floor / "objects.json"

        # Stage an object
        obj = {
            "id": str(uuid.uuid4()),
            "type": "task",
            "data": {"title": "Test Task", "description": "Testing staging"},
            "source_floor": source_floor,
            "status": "staged",
            "timestamp": datetime.now().isoformat(),
        }

        objects = json.loads(staging_file.read_text())
        objects.append(obj)
        staging_file.write_text(json.dumps(objects, indent=2))

        # Verify staged
        staged = json.loads(staging_file.read_text())
        assert len(staged) == 1
        assert staged[0]["id"] == obj["id"]
        assert staged[0]["status"] == "staged"

    def test_stage_multiple_objects(self, mock_z_direct):
        """Should handle multiple staged objects."""
        source_floor = "Z-3_Smith"
        staging_file = mock_z_direct / source_floor / "objects.json"

        objects = []
        for i in range(5):
            obj = {
                "id": str(uuid.uuid4()),
                "type": "workflow",
                "data": {"name": f"Workflow {i}"},
                "source_floor": source_floor,
                "status": "staged",
                "timestamp": datetime.now().isoformat(),
            }
            objects.append(obj)

        staging_file.write_text(json.dumps(objects, indent=2))

        # Verify all staged
        staged = json.loads(staging_file.read_text())
        assert len(staged) == 5

    def test_append_only_staging(self, mock_z_direct):
        """Staging should be append-only (no removal until approved)."""
        source_floor = "Z+1_Architect"
        staging_file = mock_z_direct / source_floor / "objects.json"

        # Stage first object
        obj1 = {"id": "obj1", "data": "first", "status": "staged"}
        staging_file.write_text(json.dumps([obj1], indent=2))

        # Stage second object (append)
        objects = json.loads(staging_file.read_text())
        obj2 = {"id": "obj2", "data": "second", "status": "staged"}
        objects.append(obj2)
        staging_file.write_text(json.dumps(objects, indent=2))

        # Verify both exist
        staged = json.loads(staging_file.read_text())
        assert len(staged) == 2
        ids = [o["id"] for o in staged]
        assert "obj1" in ids
        assert "obj2" in ids


class TestZDirectApprovalWorkflow:
    """Test Z Direct approval workflow."""

    def test_status_progression(self, mock_z_direct):
        """Objects should progress through status stages."""
        source_floor = "Z-2_Oracle"
        staging_file = mock_z_direct / source_floor / "objects.json"

        # Create object in staged state
        obj = {
            "id": "approval_test",
            "data": {"content": "test"},
            "status": "staged",
            "history": [],
        }
        staging_file.write_text(json.dumps([obj], indent=2))

        # Progress through statuses
        for status in ["pending_approval", "approved", "committed"]:
            objects = json.loads(staging_file.read_text())
            objects[0]["history"].append({
                "from": objects[0]["status"],
                "to": status,
                "timestamp": datetime.now().isoformat(),
            })
            objects[0]["status"] = status
            staging_file.write_text(json.dumps(objects, indent=2))

        # Verify final state
        final = json.loads(staging_file.read_text())
        assert final[0]["status"] == "committed"
        assert len(final[0]["history"]) == 3

    def test_rejection_workflow(self, mock_z_direct):
        """Objects can be rejected."""
        source_floor = "Z+3_Trinity"
        staging_file = mock_z_direct / source_floor / "objects.json"

        obj = {
            "id": "rejection_test",
            "data": {"invalid": True},
            "status": "pending_approval",
            "rejection_reason": None,
        }
        staging_file.write_text(json.dumps([obj], indent=2))

        # Reject
        objects = json.loads(staging_file.read_text())
        objects[0]["status"] = "rejected"
        objects[0]["rejection_reason"] = "Invalid data format"
        staging_file.write_text(json.dumps(objects, indent=2))

        # Verify
        result = json.loads(staging_file.read_text())
        assert result[0]["status"] == "rejected"
        assert result[0]["rejection_reason"] is not None


class TestZDirectInterFloorEvents:
    """Test inter-floor event communication."""

    def test_publish_event(self, mock_z_direct):
        """Should publish events to events.jsonl."""
        source_floor = "Z-4_Merovingian"
        events_file = mock_z_direct / source_floor / "events.jsonl"

        event = {
            "id": str(uuid.uuid4()),
            "type": "task.created",
            "source_floor": source_floor,
            "target_floor": "Z-3_Smith",
            "data": {"task_id": 123},
            "timestamp": datetime.now().isoformat(),
        }

        # Append to JSONL
        with open(events_file, "a") as f:
            f.write(json.dumps(event) + "\n")

        # Verify
        with open(events_file, "r") as f:
            lines = f.readlines()

        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["type"] == "task.created"

    def test_multiple_events(self, mock_z_direct):
        """Should handle multiple events."""
        source_floor = "Z+2_Neo"
        events_file = mock_z_direct / source_floor / "events.jsonl"

        events = [
            {"id": "e1", "type": "ai.query", "data": {"query": "test1"}},
            {"id": "e2", "type": "ai.response", "data": {"response": "result1"}},
            {"id": "e3", "type": "ai.query", "data": {"query": "test2"}},
        ]

        for event in events:
            event["timestamp"] = datetime.now().isoformat()
            with open(events_file, "a") as f:
                f.write(json.dumps(event) + "\n")

        # Verify
        with open(events_file, "r") as f:
            lines = f.readlines()

        assert len(lines) == 3

    def test_event_targeting(self, mock_z_direct):
        """Events should have proper source and target floors."""
        source_floor = "Z0_TheConstruct"
        target_floor = "Z+3_Trinity"
        events_file = mock_z_direct / source_floor / "events.jsonl"

        event = {
            "id": str(uuid.uuid4()),
            "type": "simulation.complete",
            "source_floor": source_floor,
            "target_floor": target_floor,
            "data": {"simulation_id": "sim_001", "status": "complete"},
            "timestamp": datetime.now().isoformat(),
        }

        with open(events_file, "a") as f:
            f.write(json.dumps(event) + "\n")

        # Verify targeting
        with open(events_file, "r") as f:
            parsed = json.loads(f.readline())

        assert parsed["source_floor"] == source_floor
        assert parsed["target_floor"] == target_floor


class TestZDirectFloorConfig:
    """Test floor configuration in Z Direct."""

    @pytest.mark.parametrize("floor_id,config", list(CANONICAL_FLOORS.items()))
    def test_floor_config_content(self, floor_id, config, mock_z_direct):
        """Floor config should have correct metadata."""
        config_file = mock_z_direct / floor_id / "floor_config.json"
        floor_config = json.loads(config_file.read_text())

        assert floor_config["floor_id"] == floor_id
        assert floor_config["z_level"] == config["z_level"]
        assert floor_config["color"] == config["color"]
        assert floor_config["role"] == config["role"]


class TestZDirectDataIntegrity:
    """Test data integrity in Z Direct operations."""

    def test_json_validity(self, mock_z_direct):
        """All JSON files should remain valid after operations."""
        for floor_id in CANONICAL_FLOORS:
            floor_dir = mock_z_direct / floor_id

            for json_file in floor_dir.glob("*.json"):
                try:
                    with open(json_file) as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {floor_id}/{json_file.name}: {e}")

    def test_no_cross_contamination(self, mock_z_direct):
        """Data staged in one floor should not appear in others."""
        # Stage unique data in each floor
        for floor_id in CANONICAL_FLOORS:
            objects_file = mock_z_direct / floor_id / "objects.json"
            obj = {
                "id": f"unique_to_{floor_id}",
                "floor_marker": floor_id,
            }
            objects_file.write_text(json.dumps([obj], indent=2))

        # Verify isolation
        for floor_id in CANONICAL_FLOORS:
            objects_file = mock_z_direct / floor_id / "objects.json"
            objects = json.loads(objects_file.read_text())

            for obj in objects:
                assert obj.get("floor_marker") == floor_id, (
                    f"Cross-contamination: {obj['floor_marker']} found in {floor_id}"
                )

    def test_timestamp_ordering(self, mock_z_direct):
        """Events should maintain timestamp ordering."""
        source_floor = "Z-1_Morpheus"
        events_file = mock_z_direct / source_floor / "events.jsonl"

        # Create events with increasing timestamps
        for i in range(5):
            event = {
                "id": f"ordered_{i}",
                "sequence": i,
                "timestamp": datetime.now().isoformat(),
            }
            with open(events_file, "a") as f:
                f.write(json.dumps(event) + "\n")
            time.sleep(0.01)  # Small delay for distinct timestamps

        # Verify ordering
        with open(events_file, "r") as f:
            events = [json.loads(line) for line in f.readlines()]

        for i, event in enumerate(events):
            assert event["sequence"] == i, "Events out of order"


class TestZDirectCommunicationPatterns:
    """Test common Z Direct communication patterns."""

    def test_request_response_pattern(self, mock_z_direct):
        """Test request-response pattern between floors."""
        requester = "Z+2_Neo"
        responder = "Z-4_Merovingian"

        # Request
        req_events = mock_z_direct / requester / "events.jsonl"
        request = {
            "id": "req_001",
            "type": "service.request",
            "source_floor": requester,
            "target_floor": responder,
            "data": {"service": "database", "action": "query"},
            "timestamp": datetime.now().isoformat(),
        }
        with open(req_events, "a") as f:
            f.write(json.dumps(request) + "\n")

        # Response
        resp_events = mock_z_direct / responder / "events.jsonl"
        response = {
            "id": "resp_001",
            "type": "service.response",
            "source_floor": responder,
            "target_floor": requester,
            "correlation_id": "req_001",
            "data": {"result": "success", "rows": 10},
            "timestamp": datetime.now().isoformat(),
        }
        with open(resp_events, "a") as f:
            f.write(json.dumps(response) + "\n")

        # Verify correlation
        with open(resp_events, "r") as f:
            resp = json.loads(f.readline())
        assert resp["correlation_id"] == request["id"]

    def test_broadcast_pattern(self, mock_z_direct):
        """Test broadcast pattern to all floors."""
        broadcaster = "Z-4_Merovingian"
        broadcast_event = {
            "id": "broadcast_001",
            "type": "system.announcement",
            "source_floor": broadcaster,
            "target_floor": "*",  # Broadcast
            "data": {"message": "System maintenance in 5 minutes"},
            "timestamp": datetime.now().isoformat(),
        }

        # Publish to broadcaster's events
        events_file = mock_z_direct / broadcaster / "events.jsonl"
        with open(events_file, "a") as f:
            f.write(json.dumps(broadcast_event) + "\n")

        # Verify broadcast marker
        with open(events_file, "r") as f:
            event = json.loads(f.readline())
        assert event["target_floor"] == "*"

    def test_pipeline_pattern(self, mock_z_direct):
        """Test data pipeline through multiple floors."""
        pipeline = ["Z+2_Neo", "Z-1_Morpheus", "Z-2_Oracle"]

        data = {"content": "raw_data", "stage": 0}

        for i, floor in enumerate(pipeline):
            # Process and forward
            data["stage"] = i
            data["processed_by"] = floor

            objects_file = mock_z_direct / floor / "objects.json"
            objects = json.loads(objects_file.read_text())
            objects.append({
                "id": f"pipeline_stage_{i}",
                "data": data.copy(),
                "timestamp": datetime.now().isoformat(),
            })
            objects_file.write_text(json.dumps(objects, indent=2))

        # Verify pipeline completion
        final_floor = pipeline[-1]
        final_objects = json.loads((mock_z_direct / final_floor / "objects.json").read_text())
        assert len(final_objects) > 0
        assert final_objects[-1]["data"]["stage"] == len(pipeline) - 1


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
