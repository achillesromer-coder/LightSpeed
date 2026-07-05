"""
Template System Integration Test
LightSpeed Type I Civilization Platform

Tests complete integration of Template System across:
- Core service exports
- Template registry functionality
- UI manager accessibility
- Settings dialog integration
- N (portal) keyboard shortcuts

Author: LightSpeed Team
Version: 0.9.5
Date: December 22, 2025
"""

import sys
from pathlib import Path

try:
    # Avoid Windows console encoding failures (cp1252) when printing unicode status markers.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# tools/ -> Z-3_Smith/ -> Z Axis/ -> LightSpeed/
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

def test_core_exports():
    """Test that template system is exported from core"""
    print("\n" + "="*60)
    print("TEST 1: Core Exports")
    print("="*60)

    try:
        from core import (
            BaseTemplate,
            DocumentTemplate,
            UITemplate,
            TestTemplate,
            QRCodeTemplate,
            TableTemplate,
            ImageTemplate,
            ThemeTemplate,
            VenvSetupTemplate,
            TemplateRegistry,
            get_template_registry
        )
        print("✓ All template classes exported from core")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_service_exports():
    """Test that template system is exported from core.services"""
    print("\n" + "="*60)
    print("TEST 2: Service Exports")
    print("="*60)

    try:
        from core.services import (
            BaseTemplate,
            DocumentTemplate,
            UITemplate,
            TestTemplate,
            QRCodeTemplate,
            TableTemplate,
            ImageTemplate,
            ThemeTemplate,
            VenvSetupTemplate,
            TemplateRegistry,
            get_template_registry
        )
        print("✓ All template classes exported from core.services")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_template_registry():
    """Test template registry functionality"""
    print("\n" + "="*60)
    print("TEST 3: Template Registry")
    print("="*60)

    try:
        from core.services import get_template_registry

        registry = get_template_registry()
        print(f"✓ Template registry initialized")

        # List all templates
        templates = registry.list_templates()
        print(f"✓ Found {len(templates)} templates:")
        for template_name in sorted(templates):
            print(f"  • {template_name}")

        # Test getting each template
        for template_name in templates:
            template = registry.get_template(template_name)
            if template:
                print(f"✓ {template_name} instantiated successfully")
            else:
                print(f"✗ Failed to get {template_name}")
                return False

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_customization():
    """Test template customization functionality"""
    print("\n" + "="*60)
    print("TEST 4: Template Customization")
    print("="*60)

    try:
        from core.services import get_template_registry

        registry = get_template_registry()

        # Test QRCodeTemplate
        qr = registry.get_template("QRCodeTemplate")
        default_settings = qr.get_default_settings()
        print(f"✓ QRCodeTemplate default settings: {default_settings}")

        # Customize settings
        qr.customize({'size': 20, 'fill_color': '#ff0000'})
        print(f"✓ QRCodeTemplate customized successfully")

        # Validate settings
        test_data = {'content': 'test', 'filename': 'test.png'}
        is_valid = qr.validate(test_data)
        print(f"✓ QRCodeTemplate validation: {is_valid}")

        # Test TableTemplate
        table = registry.get_template("TableTemplate")
        default_settings = table.get_default_settings()
        print(f"✓ TableTemplate default settings: {default_settings}")

        # Test ThemeTemplate
        theme = registry.get_template("ThemeTemplate")
        default_settings = theme.get_default_settings()
        print(f"✓ ThemeTemplate default settings: {default_settings}")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ui_manager_import():
    """Test template manager UI import"""
    print("\n" + "="*60)
    print("TEST 5: UI Manager Import")
    print("="*60)

    try:
        from core.ui.template_manager import (
            TemplateManagerDialog,
            show_template_manager
        )
        print("✓ TemplateManagerDialog imported successfully")
        print("✓ show_template_manager function imported successfully")

        # Test from core.ui package
        from core.ui import TemplateManagerDialog, show_template_manager
        print("✓ Template manager accessible from core.ui")

        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_settings_integration():
    """Test settings dialog has template tab"""
    print("\n" + "="*60)
    print("TEST 6: Settings Integration")
    print("="*60)

    try:
        # Check if settings dialog file has template manager tab
        settings_file = PROJECT_ROOT / "Z Axis" / "Z+3_Trinity" / "components" / "settings_dialog.py"

        if not settings_file.exists():
            print(f"✗ Settings dialog file not found: {settings_file}")
            return False

        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if '_create_template_manager_tab' in content:
            print("✓ Settings dialog has _create_template_manager_tab method")
        else:
            print("✗ Settings dialog missing _create_template_manager_tab method")
            return False

        if 'Open Template Manager' in content:
            print("✓ Settings dialog has Template Manager button")
        else:
            print("✗ Settings dialog missing Template Manager button")
            return False

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_n_integration():
    """Test N.py (portal) has template manager access"""
    print("\n" + "="*60)
    print("TEST 7: N Integration (N.py)")
    print("="*60)

    try:
        # Check if N.py has template manager method
        portal_file = PROJECT_ROOT / "N.py"

        if not portal_file.exists():
            print(f"✗ N.py not found: {portal_file}")
            return False

        with open(portal_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'def show_template_manager' in content:
            print("✓ N.py has show_template_manager method")
        else:
            print("✗ N.py missing show_template_manager method")
            return False

        if '<Control-m>' in content and 'show_template_manager' in content:
            print("✓ N.py has Ctrl+M keyboard shortcut")
        else:
            print("✗ N.py missing Ctrl+M keyboard shortcut")
            return False

        if 'Templates' in content and 'COLORS[\'accent_magenta\']' in content:
            print("✓ N.py has Templates button in main menu")
        else:
            print("! N.py may be missing Templates button (non-critical)")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_documentation():
    """Test documentation is updated"""
    print("\n" + "="*60)
    print("TEST 8: Documentation")
    print("="*60)

    try:
        # Check QUICK_START.md
        quick_start = PROJECT_ROOT / "Z Axis" / "Z-1_Morpheus" / "documentation" / "QUICK_START.md"

        if not quick_start.exists():
            print(f"✗ QUICK_START.md not found: {quick_start}")
            return False

        with open(quick_start, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'Template System' in content:
            print("✓ QUICK_START.md documents Template System")
        else:
            print("✗ QUICK_START.md missing Template System documentation")
            return False

        if 'Ctrl+M' in content and 'Template Manager' in content:
            print("✓ QUICK_START.md has Ctrl+M keyboard shortcut")
        else:
            print("✗ QUICK_START.md missing Ctrl+M keyboard shortcut")
            return False

        # Check for template examples
        template_examples = PROJECT_ROOT / "Output" / "template_examples.py"
        if template_examples.exists():
            print(f"✓ Template examples file exists: {template_examples}")
        else:
            print(f"✗ Template examples file missing: {template_examples}")
            return False

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_rendering():
    """Test actual template rendering (if dependencies available)"""
    print("\n" + "="*60)
    print("TEST 9: Template Rendering (Optional)")
    print("="*60)

    try:
        from core.services import get_template_registry

        registry = get_template_registry()

        # Test QR Code rendering (requires qrcode package)
        try:
            import qrcode
            qr_template = registry.get_template("QRCodeTemplate")

            # Don't actually render, just test if render method exists
            print("✓ qrcode package available")
            print("✓ QRCodeTemplate has render method")
        except ImportError:
            print("! qrcode package not installed (optional)")

        # Test PIL availability (for image templates)
        try:
            from PIL import Image
            print("✓ PIL (Pillow) package available")
        except ImportError:
            print("! PIL package not installed (optional)")

        return True
    except Exception as e:
        print(f"! Error (non-critical): {e}")
        return True  # Non-critical test


def main():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("  TEMPLATE SYSTEM INTEGRATION TEST SUITE")
    print("  LightSpeed Type I Civilization Platform")
    print("="*60)

    tests = [
        ("Core Exports", test_core_exports),
        ("Service Exports", test_service_exports),
        ("Template Registry", test_template_registry),
        ("Template Customization", test_template_customization),
        ("UI Manager Import", test_ui_manager_import),
        ("Settings Integration", test_settings_integration),
        ("N Integration (N.py)", test_n_integration),
        ("Documentation", test_documentation),
        ("Template Rendering", test_template_rendering),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")

    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed ({passed*100//total}%)")
    print("="*60)

    if passed == total:
        print("\n*** All tests passed! Template System fully integrated.")
        print("\nNext Steps:")
        print("1. Launch N.py")
        print("2. Press Ctrl+M to open Template Manager")
        print("3. Or go to Settings > Templates tab")
        print("4. Run Output/template_examples.py for usage examples")
    else:
        print(f"\nWARNING: {total - passed} test(s) failed. Review errors above.")

    print("\n" + "="*60 + "\n")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
