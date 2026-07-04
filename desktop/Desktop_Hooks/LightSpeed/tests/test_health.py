"""
System Health Check Tests
=========================

Startup validation and runtime health check systems.
Ensures all systems are ready for launch and ongoing operation.

Test Categories:
- Startup validation
- Service health checks
- Database connectivity
- File system integrity
- Configuration validation
- Performance baselines

Author: LightSpeed Team / ACHILLES
Version: 5.1.1
"""

import pytest
import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import sqlite3

from tests.conftest import (
    LIGHTSPEED_ROOT, Z_AXIS_ROOT, FLOOR_PATHS, CANONICAL_FLOORS,
    validate_floor_structure
)


# ============================================================================
# HEALTH CHECK CONFIGURATION
# ============================================================================

HEALTH_CHECK_CONFIG = {
    "startup_timeout_seconds": 30,
    "service_timeout_ms": 5000,
    "min_free_disk_mb": 500,
    "max_cpu_percent": 90,
    "max_memory_percent": 90,
    "database_ping_timeout_ms": 1000,
    "event_bus_latency_max_ms": 10,
}

REQUIRED_SERVICES = [
    "event_bus",
    "settings_hub",
    "database",
    "floor_manager",
]

REQUIRED_CONFIG_FILES = [
    "config/lightspeed_config.json",
    "config/settings.json",
    "config/z_direct_template.json",
]

REQUIRED_DIRECTORIES = [
    "Z Axis",
    "config",
    "Z Axis/Z-2_Oracle/data/legacy/ai_logs",
]


# ============================================================================
# HEALTH CHECK RESULTS
# ============================================================================

class HealthCheckResult:
    """Result of a health check."""

    def __init__(self, name: str, passed: bool, message: str = "", duration_ms: float = 0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration_ms = duration_ms
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
        }


# ============================================================================
# TEST CLASSES
# ============================================================================

class TestStartupValidation:
    """Validate system readiness at startup."""

    def test_lightspeed_root_exists(self, lightspeed_root):
        """LightSpeed root directory should exist."""
        assert lightspeed_root.exists(), "LightSpeed root directory not found"

    def test_z_axis_root_exists(self, z_axis_root):
        """Z Axis root directory should exist."""
        assert z_axis_root.exists(), "Z Axis root directory not found"

    def test_required_directories_exist(self, lightspeed_root):
        """Required directories should exist."""
        missing = []
        for dirname in REQUIRED_DIRECTORIES:
            dirpath = lightspeed_root / dirname
            if not dirpath.exists():
                missing.append(dirname)

        assert len(missing) == 0, f"Missing directories: {missing}"

    def test_main_entry_point_exists(self, lightspeed_root):
        """Main entry point (__main__.py) should exist."""
        main_py = lightspeed_root / "__main__.py"
        assert main_py.exists(), "__main__.py not found"

    def test_n_py_exists(self, lightspeed_root):
        """N.py orchestrator should exist."""
        n_py = lightspeed_root / "N.py"
        assert n_py.exists(), "N.py not found"

    def test_version_file_exists(self, lightspeed_root):
        """VERSION file should exist."""
        version = lightspeed_root / "VERSION"
        if not version.exists():
            # May be in a different location
            pytest.skip("VERSION file not in root")
        else:
            content = version.read_text().strip()
            assert len(content) > 0, "VERSION file is empty"


class TestConfigurationValidation:
    """Validate configuration files."""

    def test_lightspeed_config_exists(self, lightspeed_root):
        """Main config file should exist."""
        config_path = lightspeed_root / "config" / "lightspeed_config.json"
        assert config_path.exists(), "lightspeed_config.json not found"

    def test_lightspeed_config_valid_json(self, lightspeed_root):
        """Main config should be valid JSON."""
        config_path = lightspeed_root / "config" / "lightspeed_config.json"
        if not config_path.exists():
            pytest.skip("Config file not found")

        try:
            with open(config_path) as f:
                config = json.load(f)
            assert isinstance(config, dict), "Config should be a dictionary"
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in config: {e}")

    def test_config_has_required_sections(self, lightspeed_root):
        """Config should have required sections."""
        config_path = lightspeed_root / "config" / "lightspeed_config.json"
        if not config_path.exists():
            pytest.skip("Config file not found")

        with open(config_path) as f:
            config = json.load(f)

        required_sections = ["platform", "database", "floors"]
        missing = [s for s in required_sections if s not in config]
        assert len(missing) == 0, f"Missing config sections: {missing}"

    def test_floors_config_valid(self, lightspeed_root):
        """Floor configuration should be valid."""
        config_path = lightspeed_root / "config" / "lightspeed_config.json"
        if not config_path.exists():
            pytest.skip("Config file not found")

        with open(config_path) as f:
            config = json.load(f)

        floors = config.get("floors", {})
        assert len(floors) > 0, "No floors configured"

        for floor_name, floor_config in floors.items():
            assert "enabled" in floor_config, f"Floor {floor_name} missing 'enabled'"
            assert "port" in floor_config, f"Floor {floor_name} missing 'port'"


class TestDatabaseHealth:
    """Test database connectivity and integrity."""

    def test_database_path_configured(self, lightspeed_root):
        """Database path should be configured."""
        config_path = lightspeed_root / "config" / "lightspeed_config.json"
        if not config_path.exists():
            pytest.skip("Config file not found")

        with open(config_path) as f:
            config = json.load(f)

        db_config = config.get("database", {})
        assert "path" in db_config, "Database path not configured"

    def test_mock_database_connection(self, mock_database):
        """Mock database should be accessible."""
        conn = mock_database["connection"]
        cursor = conn.cursor()

        # Test query
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        assert count >= 1, "Expected at least 1 user (admin)"

    def test_mock_database_tables_exist(self, mock_database):
        """Required tables should exist."""
        conn = mock_database["connection"]
        cursor = conn.cursor()

        required_tables = ["users", "tasks", "events", "simulations", "z_direct_staging"]
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]

        missing = [t for t in required_tables if t not in existing_tables]
        assert len(missing) == 0, f"Missing tables: {missing}"


class TestServiceHealth:
    """Test service availability and health."""

    def test_event_bus_singleton(self, floor_paths):
        """Event bus should be singleton."""
        try:
            merovingian = floor_paths.get("Z-4_Merovingian")
            services_path = merovingian / "core" / "services"
            if str(services_path) not in sys.path:
                sys.path.insert(0, str(services_path))

            from event_bus import get_event_bus

            bus1 = get_event_bus()
            bus2 = get_event_bus()
            assert bus1 is bus2, "Event bus should be singleton"
        except ImportError:
            pytest.skip("Event bus not importable")

    def test_event_bus_latency(self, floor_paths):
        """Event bus latency should be within limits."""
        try:
            merovingian = floor_paths.get("Z-4_Merovingian")
            services_path = merovingian / "core" / "services"
            if str(services_path) not in sys.path:
                sys.path.insert(0, str(services_path))

            from event_bus import Event, get_event_bus

            bus = get_event_bus()
            received = []

            def handler(event):
                received.append(time.time())

            bus.subscribe("test.latency", handler)

            start = time.perf_counter()
            bus.publish(Event(type="test.latency", source="health", data={}), async_mode=False)
            elapsed_ms = (time.perf_counter() - start) * 1000

            try:
                max_latency = HEALTH_CHECK_CONFIG["event_bus_latency_max_ms"]
                assert received, "Event bus did not deliver the health-check event"
                assert elapsed_ms < max_latency, f"Event bus latency {elapsed_ms:.2f}ms exceeds {max_latency}ms"
            finally:
                bus.unsubscribe("test.latency", handler)
        except ImportError:
            pytest.skip("Event bus not importable")


class TestFileSystemHealth:
    """Test file system integrity."""

    def test_sufficient_disk_space(self, lightspeed_root):
        """Should have sufficient disk space."""
        import shutil

        total, used, free = shutil.disk_usage(lightspeed_root)
        free_mb = free / (1024 * 1024)

        min_required = HEALTH_CHECK_CONFIG["min_free_disk_mb"]
        assert free_mb >= min_required, f"Insufficient disk space: {free_mb:.0f}MB < {min_required}MB"

    def test_write_permission(self, temp_test_dir):
        """Should have write permission."""
        test_file = temp_test_dir / "write_test.txt"
        try:
            test_file.write_text("test")
            assert test_file.exists(), "Failed to create test file"
            test_file.unlink()
        except Exception as e:
            pytest.fail(f"Write permission error: {e}")

    def test_no_corrupted_json_configs(self, lightspeed_root):
        """All JSON config files should be valid."""
        config_dir = lightspeed_root / "config"
        if not config_dir.exists():
            pytest.skip("Config directory not found")

        corrupted = []
        for json_file in config_dir.glob("*.json"):
            try:
                with open(json_file) as f:
                    json.load(f)
            except json.JSONDecodeError:
                corrupted.append(json_file.name)

        assert len(corrupted) == 0, f"Corrupted JSON files: {corrupted}"


class TestFloorHealth:
    """Test individual floor health."""

    @pytest.mark.parametrize("floor_id", list(CANONICAL_FLOORS.keys()))
    def test_floor_accessible(self, floor_id, floor_paths):
        """Each floor should be accessible."""
        floor_path = floor_paths.get(floor_id)
        assert floor_path is not None, f"Floor path not defined: {floor_id}"
        assert floor_path.exists(), f"Floor not accessible: {floor_id}"

    @pytest.mark.parametrize("floor_id", list(CANONICAL_FLOORS.keys()))
    def test_floor_has_python_files(self, floor_id, floor_paths):
        """Each floor should expose active Python files without walking archives."""
        floor_path = floor_paths.get(floor_id)
        if not floor_path or not floor_path.exists():
            pytest.skip(f"Floor not found: {floor_id}")

        candidate_dirs = [
            floor_path,
            floor_path / "components",
            floor_path / "ui",
            floor_path / "core",
            floor_path / "core" / "services",
        ]
        py_files = []
        for candidate in candidate_dirs:
            if candidate.exists():
                py_files.extend(candidate.glob("*.py"))

        assert len(py_files) > 0, f"No Python files in floor: {floor_id}"


class TestZDirectHealth:
    """Test Z Direct staging system health."""

    def test_z_direct_staging_isolated(self, mock_z_direct):
        """Z Direct staging should be isolated per floor."""
        for floor_id in CANONICAL_FLOORS:
            floor_dir = mock_z_direct / floor_id
            assert floor_dir.exists(), f"Z Direct missing for {floor_id}"

            objects_file = floor_dir / "objects.json"
            assert objects_file.exists(), f"objects.json missing for {floor_id}"

    def test_z_direct_no_cross_contamination(self, mock_z_direct):
        """Z Direct should not have cross-contamination."""
        # Stage data in one floor
        source_floor = "Z+2_Neo"
        source_objects = mock_z_direct / source_floor / "objects.json"

        test_data = [{"id": "test", "source": source_floor}]
        source_objects.write_text(json.dumps(test_data))

        # Verify other floors are clean
        for floor_id in CANONICAL_FLOORS:
            if floor_id != source_floor:
                floor_objects = mock_z_direct / floor_id / "objects.json"
                data = json.loads(floor_objects.read_text())
                assert len(data) == 0, f"Cross-contamination detected in {floor_id}"


class TestPerformanceBaselines:
    """Test performance baselines."""

    def test_json_parse_performance(self):
        """JSON parsing should be fast."""
        # Create a moderately large JSON structure
        data = {
            "items": [{"id": i, "name": f"item_{i}", "value": i * 100} for i in range(1000)]
        }

        json_str = json.dumps(data)

        start = time.time()
        for _ in range(100):
            json.loads(json_str)
        elapsed = time.time() - start

        # Should parse 100 times in under 1 second
        assert elapsed < 1.0, f"JSON parsing too slow: {elapsed:.2f}s for 100 iterations"

    def test_file_read_performance(self, temp_test_dir):
        """File reading should be fast."""
        # Create a test file
        test_file = temp_test_dir / "performance_test.txt"
        content = "x" * 100000  # 100KB
        test_file.write_text(content)

        start = time.time()
        for _ in range(100):
            _ = test_file.read_text()
        elapsed = time.time() - start

        # Should read 100 times in under 1 second
        assert elapsed < 1.0, f"File reading too slow: {elapsed:.2f}s for 100 iterations"


class TestSystemHealthReport:
    """Generate comprehensive health report."""

    def test_generate_health_report(self, lightspeed_root, floor_paths, temp_test_dir):
        """Generate a comprehensive health report."""
        results: List[HealthCheckResult] = []

        # Directory checks
        for dirname in REQUIRED_DIRECTORIES:
            dirpath = lightspeed_root / dirname
            results.append(HealthCheckResult(
                name=f"directory_{dirname}",
                passed=dirpath.exists(),
                message=f"Directory exists" if dirpath.exists() else f"Directory missing"
            ))

        # Floor checks
        for floor_id in CANONICAL_FLOORS:
            floor_path = floor_paths.get(floor_id)
            passed = floor_path is not None and floor_path.exists()
            results.append(HealthCheckResult(
                name=f"floor_{floor_id}",
                passed=passed,
                message="Floor accessible" if passed else "Floor not found"
            ))

        # Summary
        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)
        pass_rate = (passed_count / total_count) * 100 if total_count > 0 else 0

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_checks": total_count,
                "passed": passed_count,
                "failed": total_count - passed_count,
                "pass_rate": pass_rate,
            },
            "results": [r.to_dict() for r in results],
        }

        # Save report
        report_path = temp_test_dir / "health_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        # Assertions
        assert pass_rate >= 80, f"Health check pass rate too low: {pass_rate:.1f}%"
        assert report_path.exists(), "Failed to save health report"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
