"""
LightSpeed Test Configuration - pytest fixtures and shared resources
====================================================================

Provides:
- Path resolution for all Z-Axis floors
- Database fixtures (isolated test DB)
- Event bus fixtures (clean per-test)
- Mock services for isolated testing
- Template scenario fixtures

Author: LightSpeed Team / ACHILLES
Version: 5.1.2
"""

import pytest
import sys
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import json

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

# Resolve LightSpeed root from tests directory
TESTS_DIR = Path(__file__).parent
LIGHTSPEED_ROOT = TESTS_DIR.parent
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"
SPLIT_RUNTIME_ROOT = (LIGHTSPEED_ROOT.parent.parent / "LightSpeed_Runtime").resolve()

# Add necessary paths for imports
sys.path.insert(0, str(LIGHTSPEED_ROOT))
if SPLIT_RUNTIME_ROOT.exists():
    sys.path.insert(0, str(SPLIT_RUNTIME_ROOT))
sys.path.insert(0, str(Z_AXIS_ROOT / "Z-4_Merovingian"))
sys.path.insert(0, str(Z_AXIS_ROOT / "Z-4_Merovingian" / "core"))
sys.path.insert(0, str(Z_AXIS_ROOT / "Z-4_Merovingian" / "core" / "services"))

# Floor paths dictionary for test access
FLOOR_PATHS = {
    "Z+3_Trinity": Z_AXIS_ROOT / "Z+3_Trinity",
    "Z+2_Neo": Z_AXIS_ROOT / "Z+2_Neo",
    "Z+1_Architect": Z_AXIS_ROOT / "Z+1_Architect",
    "Z0_TheConstruct": Z_AXIS_ROOT / "Z0_TheConstruct",
    "Z-1_Morpheus": Z_AXIS_ROOT / "Z-1_Morpheus",
    "Z-2_Oracle": Z_AXIS_ROOT / "Z-2_Oracle",
    "Z-3_Smith": Z_AXIS_ROOT / "Z-3_Smith",
    "Z-4_Merovingian": Z_AXIS_ROOT / "Z-4_Merovingian",
}

# Canonical floor configuration (Z+3 to Z-4)
CANONICAL_FLOORS = {
    "Z+3_Trinity": {"z_level": 3, "color": "#FF1493", "role": "UI Layer"},
    "Z+2_Neo": {"z_level": 2, "color": "#00FF00", "role": "AI Orchestration"},
    "Z+1_Architect": {"z_level": 1, "color": "#DAA520", "role": "Planning"},
    "Z0_TheConstruct": {"z_level": 0, "color": "#808080", "role": "3D Environment"},
    "Z-1_Morpheus": {"z_level": -1, "color": "#4B0082", "role": "Knowledge Base"},
    "Z-2_Oracle": {"z_level": -2, "color": "#00008B", "role": "IP Vault"},
    "Z-3_Smith": {"z_level": -3, "color": "#006400", "role": "Automation"},
    "Z-4_Merovingian": {"z_level": -4, "color": "#8B0000", "role": "Core Services"},
}


# ============================================================================
# PYTEST FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def lightspeed_root() -> Path:
    """Return LightSpeed root directory."""
    return LIGHTSPEED_ROOT


@pytest.fixture(scope="session")
def z_axis_root() -> Path:
    """Return Z Axis root directory."""
    return Z_AXIS_ROOT


@pytest.fixture(scope="session")
def floor_paths() -> Dict[str, Path]:
    """Return dictionary of floor paths."""
    return FLOOR_PATHS


@pytest.fixture(scope="session")
def canonical_floors() -> Dict[str, Dict[str, Any]]:
    """Return canonical floor configuration."""
    return CANONICAL_FLOORS


@pytest.fixture(scope="function")
def temp_test_dir():
    """Create a temporary directory for test artifacts."""
    temp_dir = tempfile.mkdtemp(prefix="lightspeed_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def mock_database(temp_test_dir):
    """Create an isolated test database."""
    import sqlite3

    db_path = temp_test_dir / "test_lightspeed.db"
    conn = sqlite3.connect(str(db_path))

    # Create minimal schema for testing
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            role TEXT DEFAULT 'user',
            clearance INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            floor TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            source_floor TEXT,
            target_floor TEXT,
            data TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS simulations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            simulation_type TEXT,
            parameters TEXT,
            results TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS z_direct_staging (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_floor TEXT NOT NULL,
            target_floor TEXT,
            object_type TEXT,
            object_data TEXT,
            status TEXT DEFAULT 'staged',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Insert default admin user
        INSERT INTO users (username, role, clearance) VALUES ('admin', 'Administrator', 5);
    """)
    conn.commit()

    yield {"path": db_path, "connection": conn}

    conn.close()


@pytest.fixture(scope="function")
def mock_event_bus():
    """Create an isolated event bus for testing."""
    class MockEventBus:
        def __init__(self):
            self.subscribers = {}
            self.event_history = []

        def subscribe(self, event_type: str, handler):
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(handler)

        def unsubscribe(self, event_type: str, handler):
            if event_type in self.subscribers:
                self.subscribers[event_type].remove(handler)

        def publish(self, event_type: str, data: dict = None):
            event = {
                "type": event_type,
                "data": data or {},
                "timestamp": __import__("datetime").datetime.now().isoformat()
            }
            self.event_history.append(event)

            # Wildcard subscribers
            for pattern, handlers in self.subscribers.items():
                if pattern == event_type or pattern == "*" or (
                    pattern.endswith(".*") and event_type.startswith(pattern[:-2])
                ):
                    for handler in handlers:
                        handler(event)

        def get_history(self, limit: int = 100):
            return self.event_history[-limit:]

        def clear(self):
            self.subscribers.clear()
            self.event_history.clear()

    bus = MockEventBus()
    yield bus
    bus.clear()


@pytest.fixture(scope="function")
def mock_z_direct(temp_test_dir):
    """Create mock Z Direct staging area."""
    z_direct_dir = temp_test_dir / "z_direct"
    z_direct_dir.mkdir()

    # Create floor-specific staging areas
    for floor in CANONICAL_FLOORS:
        floor_dir = z_direct_dir / floor
        floor_dir.mkdir()

        # Create standard Z Direct files
        (floor_dir / "objects.json").write_text("[]")
        (floor_dir / "tasks.json").write_text("[]")
        (floor_dir / "events.jsonl").write_text("")
        (floor_dir / "floor_config.json").write_text(json.dumps({
            "floor_id": floor,
            "z_level": CANONICAL_FLOORS[floor]["z_level"],
            "color": CANONICAL_FLOORS[floor]["color"],
            "role": CANONICAL_FLOORS[floor]["role"]
        }))

    yield z_direct_dir


@pytest.fixture(scope="function")
def simulation_params():
    """Default simulation parameters for testing."""
    return {
        "physics": {
            "schwarzschild_radius": {"mass_kg": 1.989e30},  # Solar mass
            "hawking_temperature": {"mass_kg": 1e10},  # 10 billion kg
            "orbital_velocity": {"mass_kg": 5.972e24, "radius_m": 6.371e6 + 400e3},  # ISS orbit
            "escape_velocity": {"mass_kg": 5.972e24, "radius_m": 6.371e6},  # Earth surface
            "time_dilation": {"velocity_ms": 0.9 * 299792458},  # 90% light speed
            "de_broglie_wavelength": {"mass_kg": 9.109e-31, "velocity_ms": 1e6},  # Electron
        },
        "quantum": {
            "energy_levels": {"n": 2, "Z": 1},  # Hydrogen n=2
            "tunneling_probability": {"barrier_height_eV": 1.0, "barrier_width_nm": 0.1, "particle_energy_eV": 0.5},
        },
        "cosmology": {
            "hubble_distance": {"redshift": 0.1},
            "critical_density": {"hubble_constant_km_s_mpc": 70},
        }
    }


@pytest.fixture(scope="function")
def scenario_templates():
    """Template scenarios for testing."""
    return {
        "data_science": {
            "name": "Data Science Workspace",
            "floors": ["Z+2_Neo", "Z-1_Morpheus", "Z-4_Merovingian"],
            "widgets": ["ai_chat", "file_browser", "data_viewer"],
            "settings": {
                "ai_model": "claude-3",
                "auto_save": True,
                "theme": "dark"
            }
        },
        "physics_simulation": {
            "name": "Physics Simulation Lab",
            "floors": ["Z0_TheConstruct", "Z-4_Merovingian"],
            "widgets": ["simulation_viewer", "parameter_panel", "results_table"],
            "settings": {
                "simulation_mode": "interactive",
                "precision": "high",
                "visualization": "3d"
            }
        },
        "automation_workflow": {
            "name": "Automation Workflow",
            "floors": ["Z-3_Smith", "Z+1_Architect", "Z-4_Merovingian"],
            "widgets": ["task_queue", "workflow_designer", "log_viewer"],
            "settings": {
                "auto_execute": False,
                "retry_attempts": 3,
                "timeout_seconds": 300
            }
        }
    }


# ============================================================================
# HELPER FUNCTIONS FOR TESTS
# ============================================================================

def validate_floor_structure(floor_path: Path) -> Dict[str, Any]:
    """Validate that a floor has the expected structure."""
    result = {
        "exists": floor_path.exists(),
        "is_directory": floor_path.is_dir() if floor_path.exists() else False,
        "has_init": (floor_path / "__init__.py").exists(),
        "has_z_direct": (floor_path / "Z Direct").exists(),
        "has_manifest": (floor_path / "manifest.json").exists() or (floor_path / "floor_manifest.json").exists(),
        "components": [],
        "services": [],
        "issues": []
    }

    if not result["exists"]:
        result["issues"].append(f"Floor directory does not exist: {floor_path}")
        return result

    # Check for common subdirectories
    for subdir in ["components", "services", "tools", "ui", "core"]:
        subdir_path = floor_path / subdir
        if subdir_path.exists() and subdir_path.is_dir():
            py_files = list(subdir_path.glob("*.py"))
            result["components"].extend([f.stem for f in py_files if not f.stem.startswith("_")])

    return result


def import_floor_module(floor_id: str, module_name: str):
    """Safely import a module from a specific floor."""
    try:
        floor_path = FLOOR_PATHS.get(floor_id)
        if not floor_path or not floor_path.exists():
            return None, f"Floor not found: {floor_id}"

        # Add floor to path temporarily
        if str(floor_path) not in sys.path:
            sys.path.insert(0, str(floor_path))

        module = __import__(module_name)
        return module, None
    except ImportError as e:
        return None, str(e)
    except Exception as e:
        return None, str(e)
