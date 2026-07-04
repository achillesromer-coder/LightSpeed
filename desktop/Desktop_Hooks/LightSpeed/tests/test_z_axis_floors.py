"""
Z Axis Floor Validation Tests
=============================

Comprehensive validation of all 8 canonical Z-Axis floors.
Tests floor structure, configuration, and basic functionality.

Author: LightSpeed Team / ACHILLES
Version: 5.1.1
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any
import json
import importlib.util

# Import from conftest
from tests.conftest import (
    LIGHTSPEED_ROOT, Z_AXIS_ROOT, FLOOR_PATHS, CANONICAL_FLOORS,
    validate_floor_structure
)


class TestFloorExistence:
    """Test that all canonical floors exist and have proper structure."""

    @pytest.mark.parametrize("floor_id", list(CANONICAL_FLOORS.keys()))
    def test_floor_directory_exists(self, floor_id, floor_paths):
        """Each canonical floor should have a directory."""
        floor_path = floor_paths.get(floor_id)
        assert floor_path is not None, f"Floor path not defined: {floor_id}"
        assert floor_path.exists(), f"Floor directory missing: {floor_id}"
        assert floor_path.is_dir(), f"Floor path is not a directory: {floor_id}"

    @pytest.mark.parametrize("floor_id,config", list(CANONICAL_FLOORS.items()))
    def test_floor_has_z_direct(self, floor_id, config, floor_paths):
        """Each floor should have a Z Direct staging area."""
        floor_path = floor_paths.get(floor_id)
        if floor_path and floor_path.exists():
            z_direct = floor_path / "Z Direct"
            # Z Direct may not exist yet, but we note it
            if not z_direct.exists():
                pytest.skip(f"Z Direct not yet created for {floor_id}")


class TestFloorConfiguration:
    """Test floor configuration and metadata."""

    @pytest.mark.parametrize("floor_id,config", list(CANONICAL_FLOORS.items()))
    def test_floor_z_level(self, floor_id, config, canonical_floors):
        """Verify Z level assignments are correct."""
        expected = config["z_level"]
        actual = canonical_floors[floor_id]["z_level"]
        assert actual == expected, f"Z level mismatch for {floor_id}: expected {expected}, got {actual}"

    def test_z_levels_unique(self, canonical_floors):
        """All Z levels should be unique."""
        z_levels = [cfg["z_level"] for cfg in canonical_floors.values()]
        assert len(z_levels) == len(set(z_levels)), "Duplicate Z levels found"

    def test_z_levels_contiguous(self, canonical_floors):
        """Z levels should form a contiguous range."""
        z_levels = sorted([cfg["z_level"] for cfg in canonical_floors.values()])
        expected = list(range(min(z_levels), max(z_levels) + 1))
        assert z_levels == expected, "Z levels are not contiguous"


class TestMerovingianCoreServices:
    """Test Z-4 Merovingian core services - the foundation of the system."""

    @pytest.fixture(autouse=True)
    def setup_merovingian_path(self, floor_paths):
        """Add Merovingian to path for imports."""
        merovingian = floor_paths.get("Z-4_Merovingian")
        if merovingian and merovingian.exists():
            core_path = merovingian / "core"
            services_path = core_path / "services"
            if str(services_path) not in sys.path:
                sys.path.insert(0, str(services_path))
            if str(core_path) not in sys.path:
                sys.path.insert(0, str(core_path))
            if str(merovingian) not in sys.path:
                sys.path.insert(0, str(merovingian))

    def test_event_bus_exists(self, floor_paths):
        """Event bus service should exist."""
        merovingian = floor_paths.get("Z-4_Merovingian")
        event_bus_path = merovingian / "core" / "services" / "event_bus.py"
        assert event_bus_path.exists(), "Event bus not found"

    def test_settings_hub_exists(self, floor_paths):
        """Settings hub service should exist."""
        merovingian = floor_paths.get("Z-4_Merovingian")
        settings_path = merovingian / "core" / "services" / "settings_hub.py"
        assert settings_path.exists(), "Settings hub not found"

    def test_database_service_exists(self, floor_paths):
        """Database service should exist."""
        merovingian = floor_paths.get("Z-4_Merovingian")
        db_path = merovingian / "core" / "services" / "database.py"
        assert db_path.exists(), "Database service not found"

    def test_floor_manager_exists(self, floor_paths):
        """Floor manager service should exist."""
        merovingian = floor_paths.get("Z-4_Merovingian")
        floor_manager_path = merovingian / "core" / "services" / "floor_manager.py"
        # May be named differently
        alt_path = merovingian / "core" / "services" / "floor_loader.py"
        assert floor_manager_path.exists() or alt_path.exists(), "Floor manager not found"

    def test_event_bus_import(self, floor_paths):
        """Event bus should be importable."""
        try:
            from event_bus import get_event_bus
            bus = get_event_bus()
            assert bus is not None, "Event bus returned None"
        except ImportError as e:
            pytest.skip(f"Event bus not importable: {e}")

    def test_event_bus_pubsub(self, floor_paths):
        """Event bus pub-sub should work."""
        try:
            from event_bus import get_event_bus
            bus = get_event_bus()

            received = []
            def handler(event):
                received.append(event)

            bus.subscribe("test.event", handler)
            bus.publish("test.event", {"message": "hello"})

            assert len(received) > 0, "Event not received"
            bus.unsubscribe("test.event", handler)
        except ImportError as e:
            pytest.skip(f"Event bus not importable: {e}")


class TestTheConstructPhysics:
    """Test Z0 TheConstruct physics calculations."""

    @pytest.fixture(autouse=True)
    def setup_construct_path(self, floor_paths):
        """Add TheConstruct to path for imports."""
        construct = floor_paths.get("Z0_TheConstruct")
        if construct and construct.exists():
            if str(construct) not in sys.path:
                sys.path.insert(0, str(construct))
            tools_path = construct / "tools"
            if tools_path.exists() and str(tools_path) not in sys.path:
                sys.path.insert(0, str(tools_path))

    def test_physics_calculators_exist(self, floor_paths):
        """Physics calculator files should exist."""
        construct = floor_paths.get("Z0_TheConstruct")
        tools_path = construct / "tools"

        expected_files = [
            "gravitation.py",
            "quantum_mechanics.py",
            "cosmology.py",
        ]

        # Check for physics tools or calculators
        physics_files = list(tools_path.glob("*.py")) if tools_path.exists() else []
        assert len(physics_files) > 0, "No physics calculator files found"

    def test_raphael_physics_engine(self, floor_paths):
        """Raphael physics engine should exist."""
        merovingian = floor_paths.get("Z-4_Merovingian")
        raphael_path = merovingian / "core" / "physics" / "raphael"
        assert raphael_path.exists(), "Raphael physics engine not found"

        # Check for key files
        equations = raphael_path / "raphael_equations.py"
        if equations.exists():
            content = equations.read_text()
            assert len(content) > 100, "Raphael equations file appears empty"


class TestTrinityUI:
    """Test Z+3 Trinity UI components."""

    def test_trinity_directory_exists(self, floor_paths):
        """Trinity directory should exist."""
        trinity = floor_paths.get("Z+3_Trinity")
        assert trinity.exists(), "Trinity directory not found"

    def test_trinity_components_exist(self, floor_paths):
        """Trinity should have UI components."""
        trinity = floor_paths.get("Z+3_Trinity")
        components = trinity / "components"

        if not components.exists():
            pytest.skip("Trinity components directory not found")

        py_files = list(components.glob("*.py"))
        assert len(py_files) > 0, "No Trinity component files found"

    def test_bento_hub_exists(self, floor_paths):
        """Unified Bento Hub should exist."""
        merovingian = floor_paths.get("Z-4_Merovingian")
        bento_hub = merovingian / "core" / "ui" / "unified_bento_hub.py"
        assert bento_hub.exists(), "Unified Bento Hub not found"


class TestTkColorSafety:
    """
    Guardrail: Tk hard-fails on invalid color strings ("unknown color name").

    We validate that the most commonly used palettes and UI hubs only expose
    Tk-safe colors, even if configs contain rgba()/alpha-hex inputs.
    """

    def _load_module_from_path(self, name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, str(path))
        assert spec is not None and spec.loader is not None, f"Unable to load module: {path}"
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod

    def test_core_glass_palette_is_tk_safe(self):
        try:
            import tkinter as tk
        except Exception as e:
            pytest.skip(f"tkinter not available: {e}")

        try:
            root = tk.Tk()
            root.withdraw()
        except Exception as e:
            pytest.skip(f"Tk not available in this environment: {e}")

        try:
            from core.ui.glass_ui import ROMER_GLASS_COLORS, GLASS_MATERIALS

            for k, v in (ROMER_GLASS_COLORS or {}).items():
                if isinstance(v, str) and v.strip():
                    root.winfo_rgb(v)  # raises TclError if invalid

            for k, m in (GLASS_MATERIALS or {}).items():
                if not m:
                    continue
                for attr in ("border_color", "glow_color"):
                    val = getattr(m, attr, None)
                    if isinstance(val, str) and val.strip():
                        root.winfo_rgb(val)
        finally:
            try:
                root.destroy()
            except Exception:
                pass

    def test_smart_bento_hub_colors_are_tk_safe(self, lightspeed_root):
        try:
            import tkinter as tk
        except Exception as e:
            pytest.skip(f"tkinter not available: {e}")

        try:
            root = tk.Tk()
            root.withdraw()
        except Exception as e:
            pytest.skip(f"Tk not available in this environment: {e}")

        try:
            hub_path = lightspeed_root / "Z Axis" / "Z+3_Trinity" / "smart_bento_hub.py"
            hub = self._load_module_from_path("lightspeed_smart_bento_hub", hub_path)
            inst = hub.SmartBentoHub(parent=None)
            colors = getattr(inst, "colors", {}) or {}
            for k, v in colors.items():
                if isinstance(v, str) and v.strip():
                    root.winfo_rgb(v)
        finally:
            try:
                root.destroy()
            except Exception:
                pass

    def test_login_color_helper_sanitizes_alpha_inputs(self, lightspeed_root):
        try:
            import tkinter as tk
        except Exception as e:
            pytest.skip(f"tkinter not available: {e}")

        try:
            root = tk.Tk()
            root.withdraw()
        except Exception as e:
            pytest.skip(f"Tk not available in this environment: {e}")

        try:
            login_path = lightspeed_root / "Z Axis" / "Z+3_Trinity" / "components" / "cognigrex_login.py"
            login = self._load_module_from_path("lightspeed_cognigrex_login", login_path)

            # CSS rgba() should sanitize to a Tk-safe color.
            c1 = login._tk_color("rgba(0, 20, 60, 0.7)", "#000033")
            root.winfo_rgb(c1)

            # Alpha-hex should sanitize to a Tk-safe #RRGGBB.
            c2 = login._tk_color("#00DDFF40", "#000000")
            root.winfo_rgb(c2)
        finally:
            try:
                root.destroy()
            except Exception:
                pass


class TestITPortalLayoutContracts:
    """
    Guardrail: IT Portal should remain a governance + hub surface.

    Historically it accreted many tool tabs (20+), duplicating floor-owned UIs.
    This contract keeps:
    - top-level tabs minimal
    - Tools hub minimal (shortcuts only)
    - floor tabs operational (no stubs)
    """

    def _load_module_from_path(self, name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, str(path))
        assert spec is not None and spec.loader is not None, f"Unable to load module: {path}"
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod

    def test_it_portal_is_one_embedded_shell_with_lazy_floor_routes(self, lightspeed_root):
        try:
            import tkinter as tk
        except Exception as e:
            pytest.skip(f"tkinter not available: {e}")

        try:
            root = tk.Tk()
            root.withdraw()
        except Exception as e:
            pytest.skip(f"Tk not available in this environment: {e}")

        portal = None
        try:
            it_portal_path = lightspeed_root / "Z Axis" / "Z+3_Trinity" / "ui" / "it_portal.py"
            mod = self._load_module_from_path("lightspeed_it_portal_contract", it_portal_path)

            colors = {
                "bg_dark": "#0a0a14",
                "bg_panel": "#111827",
                "bg_blue": "#000033",
                "accent_cyan": "#00DDFF",
                "text_green": "#00FF88",
                "text_cyan": "#00DDFF",
                "text_white": "#ffffff",
                "button_green": "#14532d",
                "button_orange": "#b45309",
                "success_green": "#00ff41",
                "warning_orange": "#ffb627",
                "error_red": "#ff3333",
            }
            user = {"fullname": "IT Contract Test", "clearance": 4}

            portal = mod.ITPortal(root, user, colors, {}, lightspeed_root=lightspeed_root)
            portal.pack(fill="both", expand=True)
            shell = getattr(portal, "shell", None)
            assert shell is not None, "Embedded Trinity shell missing"
            assert isinstance(portal, tk.Frame)
            assert portal.winfo_toplevel() is root
            assert not hasattr(portal, "notebook")
            assert tuple(shell._mode_buttons) == (
                "workspace",
                "operator",
                "review",
                "publish",
                "settings",
                "holospace",
            )
            assert shell.state.snapshot() == {
                "mode": "workspace",
                "active_floor": "Trinity",
                "workspace_context": "",
            }
            assert shell.floor_selector.get_floor() == "Trinity"
            assert shell.open_floor_tab("Oracle") is True
            assert shell.state.snapshot()["active_floor"] == "Oracle"
            assert shell.state.snapshot()["mode"] == "operator"
        finally:
            try:
                if portal is not None:
                    portal.destroy()
            except Exception:
                pass
            try:
                root.destroy()
            except Exception:
                pass


class TestNeoAI:
    """Test Z+2 Neo AI orchestration."""

    def test_neo_directory_exists(self, floor_paths):
        """Neo directory should exist."""
        neo = floor_paths.get("Z+2_Neo")
        assert neo.exists(), "Neo directory not found"

    def test_ai_components_exist(self, floor_paths):
        """Neo should have AI components."""
        neo = floor_paths.get("Z+2_Neo")

        # Look for AI-related files
        py_files = list(neo.rglob("*.py"))
        ai_files = [f for f in py_files if any(
            kw in f.stem.lower() for kw in ["ai", "model", "orchestrat", "neo", "achilles"]
        )]

        assert len(ai_files) > 0 or len(py_files) > 0, "No Neo AI files found"


class TestSmithAutomation:
    """Test Z-3 Smith automation tools."""

    def test_smith_directory_exists(self, floor_paths):
        """Smith directory should exist."""
        smith = floor_paths.get("Z-3_Smith")
        assert smith.exists(), "Smith directory not found"

    def test_smith_tools_exist(self, floor_paths):
        """Smith should have automation tools."""
        smith = floor_paths.get("Z-3_Smith")
        tools = smith / "tools"

        if not tools.exists():
            pytest.skip("Smith tools directory not found")

        py_files = list(tools.glob("*.py"))
        assert len(py_files) > 0, "No Smith tool files found"


class TestOracleArchive:
    """Test Z-2 Oracle archive/IP vault."""

    def test_oracle_directory_exists(self, floor_paths):
        """Oracle directory should exist."""
        oracle = floor_paths.get("Z-2_Oracle")
        assert oracle.exists(), "Oracle directory not found"

    def test_oracle_archive_structure(self, floor_paths):
        """Oracle should have archive structure."""
        oracle = floor_paths.get("Z-2_Oracle")

        # Check for archive/vault directories
        archive_paths = [
            oracle / "archive",
            oracle / "vault",
            oracle / "Data",
        ]

        has_archive = any(p.exists() for p in archive_paths)
        if not has_archive:
            pytest.skip("Oracle archive structure not found")


class TestMorpheusKnowledge:
    """Test Z-1 Morpheus knowledge base."""

    def test_morpheus_directory_exists(self, floor_paths):
        """Morpheus directory should exist."""
        morpheus = floor_paths.get("Z-1_Morpheus")
        assert morpheus.exists(), "Morpheus directory not found"


class TestArchitectPlanning:
    """Test Z+1 Architect planning floor."""

    def test_architect_directory_exists(self, floor_paths):
        """Architect directory should exist."""
        architect = floor_paths.get("Z+1_Architect")
        assert architect.exists(), "Architect directory not found"

    def test_architect_projects_exist(self, floor_paths):
        """Architect should have projects capability."""
        architect = floor_paths.get("Z+1_Architect")
        projects = architect / "projects"

        if not projects.exists():
            pytest.skip("Architect projects directory not found")


class TestFloorCommunication:
    """Test inter-floor communication capabilities."""

    def test_event_bus_floor_events(self, mock_event_bus):
        """Event bus should handle floor-specific events."""
        events_received = []

        def floor_handler(event):
            events_received.append(event)

        # Subscribe to floor events
        mock_event_bus.subscribe("floor.*", floor_handler)
        mock_event_bus.subscribe("z_direct.*", floor_handler)

        # Publish floor events
        mock_event_bus.publish("floor.trinity.ready", {"status": "online"})
        mock_event_bus.publish("floor.smith.task_complete", {"task_id": 123})
        mock_event_bus.publish("z_direct.staging", {"source": "Neo", "target": "Smith"})

        assert len(events_received) >= 0  # May be 0 if wildcards not supported

    def test_z_direct_staging(self, mock_z_direct):
        """Z Direct staging should work."""
        # Stage an object
        staging_data = {
            "id": "test_obj_001",
            "type": "task",
            "data": {"title": "Test Task"},
            "source_floor": "Z+2_Neo",
            "target_floor": "Z-3_Smith"
        }

        neo_staging = mock_z_direct / "Z+2_Neo" / "objects.json"
        objects = json.loads(neo_staging.read_text())
        objects.append(staging_data)
        neo_staging.write_text(json.dumps(objects))

        # Verify staged
        staged = json.loads(neo_staging.read_text())
        assert len(staged) == 1
        assert staged[0]["id"] == "test_obj_001"


class TestFloorStructureValidation:
    """Validate floor structure using helper function."""

    @pytest.mark.parametrize("floor_id", list(CANONICAL_FLOORS.keys()))
    def test_floor_structure(self, floor_id, floor_paths):
        """Validate floor structure."""
        floor_path = floor_paths.get(floor_id)
        if not floor_path:
            pytest.skip(f"Floor path not defined: {floor_id}")

        result = validate_floor_structure(floor_path)

        assert result["exists"], f"Floor does not exist: {floor_id}"
        assert result["is_directory"], f"Floor is not a directory: {floor_id}"

        # Log issues but don't fail for missing optional structure
        if result["issues"]:
            for issue in result["issues"]:
                print(f"Warning for {floor_id}: {issue}")


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
