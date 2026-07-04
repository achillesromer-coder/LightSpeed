#!/usr/bin/env python
"""
Launch Path Validation - LightSpeed V0.9.5
Validates that all critical user-facing features are production-ready (no placeholders)

Tests:
1. Core services (database, event_bus, logger, storage)
2. Service registry integrity
3. Main UI components (no "coming soon" in critical paths)
4. Universal Editor handlers
5. Floor portals accessibility

Author: LightSpeed Team
Date: December 28, 2025
"""

import sys
from pathlib import Path
import json
import importlib
import re

# Add LightSpeed root to path
def _find_lightspeed_root() -> Path:
    here = Path(__file__).resolve()
    for cand in (here, *here.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return here.parents[3]


LIGHTSPEED_ROOT = _find_lightspeed_root()
sys.path.insert(0, str(LIGHTSPEED_ROOT))
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"
if Z_AXIS_ROOT.exists():
    sys.path.insert(0, str(Z_AXIS_ROOT))
    try:
        for floor_dir in sorted(Z_AXIS_ROOT.iterdir(), key=lambda p: p.name.lower()):
            if floor_dir.is_dir() and (floor_dir / "_FLOOR_MANIFEST.json").exists():
                sys.path.insert(0, str(floor_dir))
    except Exception:
        pass

def test_core_services():
    """Test all 4 core infrastructure services"""
    print("\n[TEST 1] Core Services")
    print("-" * 60)

    services = {
        'database': 'core.services.database',
        'event_bus': 'core.services.event_bus',
        'logger': 'core.services.logger',
        'storage': 'core.services.storage'
    }

    results = []
    for name, module_path in services.items():
        try:
            mod = importlib.import_module(module_path)
            # Test singleton getters
            if name == 'database':
                instance = mod.get_db()
                tables = instance.get_all_tables()
                result = f"[OK] {name}: {len(tables)} tables"
            elif name == 'event_bus':
                instance = mod.get_event_bus()
                stats = instance.get_stats()
                result = f"[OK] {name}: {stats['enabled']}"
            elif name == 'logger':
                instance = mod.get_logger('Validation')
                result = f"[OK] {name}: operational"
            elif name == 'storage':
                instance = mod.get_storage()
                stats = instance.get_storage_stats()
                result = f"[OK] {name}: {stats['total_files']} files"

            results.append(result)
            print(f"  {result}")
        except Exception as e:
            results.append(f"[X] {name}: {str(e)[:50]}")
            print(f"  [X] {name}: {str(e)[:50]}")

    return all('[OK]' in r for r in results)


def test_service_registry():
    """Test service registry configuration"""
    print("\n[TEST 2] Service Registry")
    print("-" * 60)

    registry_path = LIGHTSPEED_ROOT / "Z Axis" / "Z0_TheConstruct" / "Config" / "service_registry.json"

    try:
        with open(registry_path) as f:
            registry = json.load(f)

        enabled = [name for name, cfg in registry.items() if cfg.get('enabled', False)]
        total = len(registry)

        print(f"  Total services: {total}")
        print(f"  Enabled: {len(enabled)} ({len(enabled)/total*100:.0f}%)")

        # Test enabled services can be imported
        errors = []
        for name in enabled:
            config = registry[name]
            try:
                importlib.import_module(config['module'])
            except ImportError as e:
                errors.append(f"{name}: {str(e)[:40]}")

        if errors:
            print(f"  Import errors: {len(errors)}")
            for err in errors[:3]:
                print(f"    - {err}")
            return False
        else:
            print(f"  [OK] All {len(enabled)} enabled services importable")
            return True

    except Exception as e:
        print(f"  [X] Registry error: {e}")
        return False


def test_ui_placeholders():
    """Check critical UI files for placeholders"""
    print("\n[TEST 3] UI Placeholders (Critical Path)")
    print("-" * 60)

    critical_files = [
        "N.py",
        # Floor-native core (Merovingian owns the system core package)
        "Z Axis/Z-4_Merovingian/core/universal_editor/universal_editor.py",
        "Z Axis/Z-4_Merovingian/core/universal_editor/image_handler.py",
        "Z Axis/Z-4_Merovingian/core/universal_editor/latex_handler.py",
        # UI layer now lives inside the Z Axis floors (Trinity owns UI).
        # Keep legacy path checks as optional fallbacks.
        "Z Axis/Z+3_Trinity/ui/data_objectifier_ui.py",
        "Z Axis/Z0_TheConstruct/components/construct_dashboard_glass.py",
        "Z Axis/Z+3_Trinity/components/trinity_portal_glass.py"
    ]

    placeholder_patterns = [
        r'coming soon',
        r'pass\s*#\s*TODO',
        r'NotImplementedError\(',
        r'raise NotImplementedError'
    ]

    all_clean = True
    for filepath in critical_files:
        full_path = LIGHTSPEED_ROOT / filepath
        if not full_path.exists():
            print(f"  [!] {filepath}: FILE NOT FOUND")
            continue

        content = full_path.read_text(encoding='utf-8', errors='ignore')

        found_placeholders = []
        for pattern in placeholder_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                found_placeholders.append(f"{pattern}: {len(matches)}")

        if found_placeholders:
            print(f"  [X] {filepath}:")
            for placeholder in found_placeholders:
                print(f"      {placeholder}")
            all_clean = False
        else:
            print(f"  [OK] {filepath}")

    return all_clean


def test_universal_editor_handlers():
    """Test Universal Editor file type handlers"""
    print("\n[TEST 4] Universal Editor Handlers")
    print("-" * 60)

    handlers = [
        'text_handler',
        'code_handler',
        'data_handler',
        'document_handler',
        'image_handler',
        'latex_handler',
        'notebook_handler'
    ]

    all_ok = True
    for handler in handlers:
        try:
            mod = importlib.import_module(f'core.universal_editor.{handler}')
            # Check for handler class
            classes = [name for name in dir(mod) if 'Handler' in name and not name.startswith('_')]
            if classes:
                print(f"  [OK] {handler}: {classes[0]}")
            else:
                print(f"  [!] {handler}: no Handler class found")
        except ImportError as e:
            print(f"  [X] {handler}: {str(e)[:40]}")
            all_ok = False

    return all_ok


def test_floor_portals():
    """Test Z-floor portal accessibility"""
    print("\n[TEST 5] Floor Portal Components")
    print("-" * 60)

    floors = {
        'Z+3_Trinity': 'trinity_portal_glass.py',
        'Z0_TheConstruct': 'construct_dashboard_glass.py',
        'Z+2_Neo': 'neo_lab_assistant_glass.py',
        'Z+1_Architect': 'architect_portal_glass.py',
        'Z-1_Morpheus': 'morpheus_portal_glass.py',
        'Z-2_Oracle': 'oracle_portal_glass.py',
        'Z-3_Smith': 'smith_portal_glass.py',
        'Z-4_Merovingian': 'merovingian_portal_glass.py',
    }

    all_accessible = True
    for floor_name, portal_file in floors.items():
        portal_path = LIGHTSPEED_ROOT / "Z Axis" / floor_name / "components" / portal_file

        if portal_path.exists():
            # Check file size (should be substantial if implemented)
            size_kb = portal_path.stat().st_size / 1024
            if size_kb > 5:  # At least 5KB
                print(f"  [OK] {floor_name}: {size_kb:.1f} KB")
            else:
                print(f"  [!] {floor_name}: {size_kb:.1f} KB (may be stub)")
        else:
            print(f"  [X] {floor_name}: portal not found")
            all_accessible = False

    return all_accessible


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("LightSpeed V0.9.5 - Launch Path Validation")
    print("=" * 60)

    results = {
        'Core Services': test_core_services(),
        'Service Registry': test_service_registry(),
        'UI Placeholders': test_ui_placeholders(),
        'Universal Editor': test_universal_editor_handlers(),
        'Floor Portals': test_floor_portals()
    }

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "[OK] PASS" if passed else "[X] FAIL"
        print(f"  {status:8s} {test_name}")

    total_passed = sum(results.values())
    total_tests = len(results)

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n[SUCCESS] All validation tests passed - Launch path is production-ready!")
        return 0
    else:
        print(f"\n[WARNING] {total_tests - total_passed} test(s) failed - Review above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
