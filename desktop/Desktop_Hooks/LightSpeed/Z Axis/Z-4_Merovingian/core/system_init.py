"""
LightSpeed System Initialization
Converts all .txt specifications into working code and initializes complete system
"""

import sys
from pathlib import Path
from typing import Optional

try:
    from core.config.paths import LIGHTSPEED_ROOT, Z_AXIS_ROOT, CONSTRUCT_ROOT  # type: ignore
except Exception:
    # Fallback: walk upwards to find repo root
    _start = Path(__file__).resolve()
    LIGHTSPEED_ROOT = _start.parent
    for _cand in (_start, *_start.parents):
        if (_cand / "N.py").exists() and (_cand / "Z Axis").exists():
            LIGHTSPEED_ROOT = _cand
            break
    Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"
    CONSTRUCT_ROOT = Z_AXIS_ROOT / "Z0_TheConstruct"

# Ensure root + Z axis are importable
sys.path.insert(0, str(LIGHTSPEED_ROOT))
sys.path.insert(0, str(Z_AXIS_ROOT))
sys.path.insert(0, str(CONSTRUCT_ROOT))

from core.config.config_loader import get_config
from core.services.smart_floor_library import SmartFloorLibrary


def initialize_physics_calculators(smart_floor: SmartFloorLibrary) -> int:
    """
    Initialize all physics calculators from Z0_TheConstruct

    Converts physics_calculators.py functions into SmartFloor registry

    Returns:
        Number of functions registered
    """
    try:
        # Import physics calculators module (floor-owned)
        import physics_calculators

        # Register all calculators
        registered_count = 0

        for calc_name, calc_func in physics_calculators.PHYSICS_CALCULATORS.items():
            # Determine category from calculator metadata
            test_result = None
            category = "physics"

            # Execute a test to get result metadata
            try:
                if calc_name == "schwarzschild_radius":
                    test_result = calc_func(1.989e30)  # 1 solar mass
                elif calc_name == "hawking_temperature":
                    test_result = calc_func(1.989e30)
                elif calc_name == "time_dilation":
                    test_result = calc_func(1.989e30, 1e7)
                elif calc_name == "einstein_ring":
                    test_result = calc_func(1e30, 1e20, 1e19)
                elif calc_name == "orbital_velocity":
                    test_result = calc_func(1.989e30, 1.496e11)
                elif calc_name == "escape_velocity":
                    test_result = calc_func(5.972e24, 6.371e6)
                elif calc_name == "quantum_energy":
                    test_result = calc_func(1, 9.109e-31, 1e-9)
                elif calc_name == "tunneling_probability":
                    test_result = calc_func(1e-9, 1e-18, 5e-19, 9.109e-31)
                elif calc_name == "de_broglie_wavelength":
                    test_result = calc_func(9.109e-31, 1e6)
                elif calc_name == "hubble_distance":
                    test_result = calc_func(3e6)
                elif calc_name == "dark_matter_density":
                    test_result = calc_func(1e20, 1e19, 1e-21)
                elif calc_name == "critical_density":
                    test_result = calc_func(2.197e-18)

                if test_result and hasattr(test_result, 'category'):
                    category = test_result.category
            except:
                pass

            # Get default variables from function signature
            import inspect
            sig = inspect.signature(calc_func)
            default_vars = {}

            for param_name, param in sig.parameters.items():
                if param.default != inspect.Parameter.empty:
                    default_vars[param_name] = param.default
                else:
                    # Provide sensible defaults based on param name
                    if param_name == 'mass':
                        default_vars[param_name] = 1.989e30  # Solar mass
                    elif param_name == 'distance' or param_name == 'radius':
                        default_vars[param_name] = 1e7
                    elif param_name == 'n':
                        default_vars[param_name] = 1
                    elif param_name == 'length' or param_name == 'width':
                        default_vars[param_name] = 1e-9
                    elif param_name == 'velocity' or param_name == 'recession_velocity':
                        default_vars[param_name] = 1e6
                    elif param_name.endswith('_density'):
                        default_vars[param_name] = 1e-21
                    elif param_name.endswith('_radius'):
                        default_vars[param_name] = 1e19
                    else:
                        default_vars[param_name] = 1.0

            # Register with SmartFloor
            smart_floor.register_function(
                func_name=f"calculate_{calc_name}",
                category=category,
                floor="Z0_TheConstruct",
                default_vars=default_vars,
                description=f"{calc_name.replace('_', ' ').title()} calculator"
            )

            registered_count += 1

        print(f"[SystemInit] ✓ Registered {registered_count} physics calculators from Z0_TheConstruct")
        return registered_count

    except Exception as e:
        print(f"[SystemInit] ✗ Failed to load physics calculators: {e}")
        return 0


def initialize_mission_planner() -> Optional[object]:
    """
    Initialize Mission Planner from Z+1_Architect

    Converts Strategic Dossier and mission specs into executable planner

    Returns:
        MissionPlanner instance or None
    """
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "Z Axis" / "Z+1_Architect"))
        from mission_planner import MissionPlanner

        planner = MissionPlanner()
        print(f"[SystemInit] ✓ Mission Planner initialized with {len(planner.phases)} phases")
        return planner

    except Exception as e:
        print(f"[SystemInit] ⚠ Mission Planner not available: {e}")
        return None


def initialize_ecosystem_schemas() -> Optional[object]:
    """
    Initialize Romer/EMASSC ecosystem from Z-1_Oracle

    Converts IP licensing and tokenomics specs into data schemas

    Returns:
        EMASCCIPVault instance or None
    """
    try:
        root = Path(__file__).resolve().parents[1]
        candidates = [
            root / "Z Axis" / "Z-2_Oracle" / "ecosystem",
            root / "Z Axis" / "Z-2_Oracle" / "legacy" / "Z-1_Oracle" / "ecosystem",
        ]
        for p in candidates:
            if p.exists():
                sys.path.insert(0, str(p))
                break
        from romer_emassc_schema import EMASCCIPVault

        vault = EMASCCIPVault()
        tech_count = len(vault.technologies)
        print(f"[SystemInit] ✓ EMASSC IP Vault initialized with {tech_count} technologies")
        return vault

    except Exception as e:
        print(f"[SystemInit] ⚠ EMASSC IP Vault not available: {e}")
        return None


def initialize_workflow_engine() -> Optional[object]:
    """
    Initialize Workflow Orchestration from workflow diagrams

    Converts workflow .txt files into state machine orchestration

    Returns:
        MissionWorkflow instance or None
    """
    try:
        sys.path.insert(0, str(Path(__file__).parent / "workflows"))
        from mission_workflow import MissionWorkflow

        workflow = MissionWorkflow(mission_id="MISSION_001")
        print(f"[SystemInit] ✓ Workflow Engine initialized: {workflow.current_state.value}")
        return workflow

    except Exception as e:
        print(f"[SystemInit] ⚠ Workflow Engine not available: {e}")
        return None


def initialize_complete_system() -> dict:
    """
    Initialize complete LightSpeed system

    This function converts ALL .txt documentation into executable code:
    - Configurations → unified_config.json
    - Physics specs → physics_calculators.py → SmartFloor
    - Mission specs → mission_planner.py
    - Business specs → romer_emassc_schema.py
    - Workflow diagrams → mission_workflow.py

    Returns:
        Dictionary with all initialized components
    """
    print("\n" + "=" * 80)
    print("LIGHTSPEED SYSTEM INITIALIZATION")
    print("Converting documentation to executable code")
    print("=" * 80 + "\n")

    components = {}

    # 1. Load configuration
    print("[1/8] Loading unified configuration...")
    try:
        config = get_config()
        components['config'] = config
        print(f"      ✓ Configuration loaded: {config.get('system.version')}")
    except Exception as e:
        print(f"      ✗ Configuration failed: {e}")
        components['config'] = None

    # 2. Initialize SmartFloor Library
    print("[2/8] Initializing SmartFloor Library...")
    try:
        smart_floor = SmartFloorLibrary()
        components['smart_floor'] = smart_floor
        print("      ✓ SmartFloor initialized")
    except Exception as e:
        print(f"      ✗ SmartFloor failed: {e}")
        components['smart_floor'] = None

    # 3. Register physics calculators
    print("[3/8] Registering physics calculators...")
    if components['smart_floor']:
        calc_count = initialize_physics_calculators(components['smart_floor'])
        components['physics_calculators_count'] = calc_count
    else:
        print("      ⚠ Skipped (SmartFloor not available)")
        components['physics_calculators_count'] = 0

    # 4. Initialize Mission Planner
    print("[4/8] Initializing Mission Planner...")
    components['mission_planner'] = initialize_mission_planner()

    # 5. Initialize EMASSC Ecosystem
    print("[5/8] Initializing EMASSC Ecosystem...")
    components['emassc_vault'] = initialize_ecosystem_schemas()

    # 6. Initialize Workflow Engine
    print("[6/8] Initializing Workflow Engine...")
    components['workflow_engine'] = initialize_workflow_engine()

    # 7. Initialize Neo AI Learning Engine
    print("[7/8] Initializing Neo AI...")
    try:
        from core.ai.neo_learning import get_neo_engine
        neo = get_neo_engine()
        components['neo_ai'] = neo
        print("      ✓ Neo AI Learning Engine ready")
    except Exception as e:
        print(f"      ⚠ Neo AI not available: {e}")
        components['neo_ai'] = None

    # 8. Initialize Achilles Assistant
    print("[8/8] Initializing Achilles Assistant...")
    try:
        from core.ai.achilles_assistant import AchillesAssistant
        # Achilles requires orchestrator - will be initialized later
        print("      ⚠ Achilles requires orchestrator (deferred)")
        components['achilles'] = None
    except Exception as e:
        print(f"      ⚠ Achilles not available: {e}")
        components['achilles'] = None

    print("\n" + "=" * 80)
    print("SYSTEM INITIALIZATION COMPLETE")
    print("=" * 80)

    # Summary
    print("\n✓ Components Initialized:")
    for name, component in components.items():
        if component is not None:
            status = "✓" if component else "✗"
            print(f"  {status} {name}")

    print("\n" + "=" * 80 + "\n")

    return components


if __name__ == "__main__":
    # Run initialization
    components = initialize_complete_system()

    # Test SmartFloor if available
    if components.get('smart_floor'):
        print("\nTesting SmartFloor execution...")
        print("-" * 80)

        # Test physics calculator
        try:
            result = components['smart_floor'].execute_function(
                'calculate_schwarzschild_radius',
                {'mass': 1.989e30}  # 1 solar mass
            )
            print(f"✓ Test execution successful: {result}")
        except Exception as e:
            print(f"✗ Test execution failed: {e}")
