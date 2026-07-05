"""
Service Registry Validation Script
Tests all restored service imports and identifies operational services.
"""

import sys
import importlib
from pathlib import Path

# Add project root to path
# tools/ -> Z-3_Smith/ -> Z Axis/ -> LightSpeed/
lightspeed_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(lightspeed_root))
z_axis_root = lightspeed_root / "Z Axis"
if z_axis_root.exists():
    sys.path.insert(0, str(z_axis_root))
    try:
        for floor_dir in sorted(z_axis_root.iterdir(), key=lambda p: p.name.lower()):
            if floor_dir.is_dir() and (floor_dir / "_FLOOR_MANIFEST.json").exists():
                sys.path.insert(0, str(floor_dir))
    except Exception:
        pass

# Restored services to validate
RESTORED_SERVICES = {
    # Core Analysis (3 services)
    "ast_analyzer": "core.analysis.ast_analyzer",
    "indexer": "core.analysis.indexer",
    "dependencies": "core.analysis.dependencies",

    # CogniGrex AI System (3 services)
    "cognigrex_models": "core.cognigrex.models",
    "cognigrex_training": "core.cognigrex.training",
    "cognigrex_fleet": "core.cognigrex.fleet",

    # Simulations (1 service)
    "mark3_simulator": "core.simulations.mark3",

    # Physics Modules (4 services)
    "raphael_equations": "core.physics_modules.raphael_equations",
    "orbital_mechanics": "core.physics_modules.orbital_mechanics",
    "quantum_mechanics": "core.physics_modules.quantum_mechanics",
    "big_bang_simulation": "core.physics_modules.big_bang_simulation",

    # Rendering (2 services)
    "hybrid_renderer": "core.rendering.hybrid_renderer",
    "sphere_primitive": "core.rendering.sphere_primitive",
}

def validate_service(service_name: str, module_path: str) -> dict:
    """Validate a single service import."""
    result = {
        "service": service_name,
        "module": module_path,
        "status": "unknown",
        "error": None,
        "classes_found": []
    }

    try:
        # Try to import the module
        module = importlib.import_module(module_path)
        result["status"] = "ok"

        # Find classes in module
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and not attr_name.startswith('_'):
                result["classes_found"].append(attr_name)

        return result

    except ImportError as e:
        result["status"] = "import_error"
        result["error"] = str(e)
        return result

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        return result

def main():
    """Run validation on all restored services."""
    print("[*] LightSpeed Service Validation")
    print("[*] Testing 12 restored services...\n")

    results = []
    success_count = 0
    fail_count = 0

    for service_name, module_path in RESTORED_SERVICES.items():
        print(f"[*] Testing {service_name}...")
        result = validate_service(service_name, module_path)
        results.append(result)

        if result["status"] == "ok":
            print(f"    [OK] Import successful")
            if result["classes_found"]:
                print(f"    [OK] Found classes: {', '.join(result['classes_found'][:3])}")
            success_count += 1
        else:
            print(f"    [ERROR] {result['status']}: {result['error']}")
            fail_count += 1
        print()

    # Summary
    print("=" * 60)
    print(f"[*] VALIDATION SUMMARY")
    print(f"[*] Total Services: {len(RESTORED_SERVICES)}")
    print(f"[OK] Successful: {success_count}")
    print(f"[ERROR] Failed: {fail_count}")
    print("=" * 60)

    # Operational services report
    print("\n[*] OPERATIONAL SERVICES (ready to enable):")
    for result in results:
        if result["status"] == "ok":
            print(f"    - {result['service']}")

    # Failed services report
    if fail_count > 0:
        print("\n[*] FAILED SERVICES (remain disabled):")
        for result in results:
            if result["status"] != "ok":
                print(f"    - {result['service']}: {result['error']}")

    # Return success if all pass
    return fail_count == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
