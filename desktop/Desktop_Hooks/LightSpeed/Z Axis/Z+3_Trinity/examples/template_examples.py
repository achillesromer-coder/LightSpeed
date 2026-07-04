"""
Template System Usage Examples
LightSpeed Type I Civilization Platform

Demonstrates how to use the Template System to generate:
- QR Codes with custom styling
- Data Tables with custom formatting
- Images with borders and titles
- UI Themes
- Virtual environment setup templates

Author: LightSpeed Team
Version: 0.9.5
Date: December 22, 2025
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.services import (
    get_template_registry,
    QRCodeTemplate,
    TableTemplate,
    ImageTemplate,
    ThemeTemplate,
    VenvSetupTemplate
)


def example_qr_code():
    """Example: Generate customized QR code"""
    print("\n" + "="*60)
    print("EXAMPLE 1: QR Code Generation")
    print("="*60)

    # Get template from registry
    registry = get_template_registry()
    qr_template = registry.get_template("QRCodeTemplate")

    # Customize settings
    qr_template.customize({
        'size': 15,
        'border': 6,
        'fill_color': '#0066cc',
        'back_color': '#ffffff',
        'error_correction': 'H',
        'add_logo': False
    })

    # Generate QR code
    data = {
        'content': 'https://lightspeed-platform.com',
        'filename': 'lightspeed_qr.png'
    }

    try:
        output_path = qr_template.render(data)
        print(f"✓ QR Code generated: {output_path}")
        print(f"  Size: 15x15")
        print(f"  Color: #0066cc on #ffffff")
        print(f"  Error Correction: High")
    except Exception as e:
        print(f"✗ Error: {e}")


def example_data_table():
    """Example: Generate styled data table"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Data Table Generation")
    print("="*60)

    registry = get_template_registry()
    table_template = registry.get_template("TableTemplate")

    # Customize table styling
    table_template.customize({
        'format': 'html',
        'font_family': 'Arial',
        'font_size': 12,
        'header_bg': '#0066cc',
        'header_fg': '#ffffff',
        'row_bg_odd': '#f0f0f0',
        'row_bg_even': '#ffffff',
        'border_color': '#cccccc',
        'border_width': 1
    })

    # Generate table with sample data
    data = {
        'title': 'LightSpeed Platform Statistics',
        'headers': ['Floor', 'Services', 'Status', 'Uptime'],
        'rows': [
            ['Neo (Z-4)', '12', 'Active', '99.9%'],
            ['Morpheus (Z-3)', '8', 'Active', '99.8%'],
            ['Architect (Z-2)', '15', 'Active', '99.9%'],
            ['TheConstruct (Z-1)', '20', 'Active', '100%'],
            ['Oracle (Z0)', '10', 'Active', '99.9%'],
            ['Smith (Z+1)', '6', 'Active', '99.7%'],
            ['Merovingian (Z+2)', '14', 'Active', '99.8%'],
            ['Trinity (Z+3)', '18', 'Active', '99.9%'],
        ],
        'filename': 'platform_stats.html'
    }

    try:
        output_path = table_template.render(data)
        print(f"✓ Data Table generated: {output_path}")
        print(f"  Format: HTML")
        print(f"  Rows: {len(data['rows'])}")
        print(f"  Columns: {len(data['headers'])}")
    except Exception as e:
        print(f"✗ Error: {e}")


def example_image_processing():
    """Example: Process image with borders and title"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Image Processing")
    print("="*60)

    registry = get_template_registry()
    image_template = registry.get_template("ImageTemplate")

    # Customize image processing
    image_template.customize({
        'border_width': 10,
        'border_color': '#0066cc',
        'title': 'LightSpeed Platform',
        'title_font': 'Arial',
        'title_size': 32,
        'title_color': '#ffffff',
        'title_bg': '#0066cc',
        'add_watermark': True,
        'watermark_text': 'LightSpeed © 2025'
    })

    # Note: This example requires an actual image file
    print("  Template configured for image processing:")
    print(f"  - Border: 10px #0066cc")
    print(f"  - Title: 'LightSpeed Platform' (32pt Arial)")
    print(f"  - Watermark: 'LightSpeed © 2025'")
    print("  To use: Provide image_path in data dict")


def example_ui_theme():
    """Example: Create custom UI theme"""
    print("\n" + "="*60)
    print("EXAMPLE 4: UI Theme Generation")
    print("="*60)

    registry = get_template_registry()
    theme_template = registry.get_template("ThemeTemplate")

    # Customize theme
    theme_template.customize({
        'theme_name': 'LightSpeed Matrix',
        'bg_primary': '#0d1117',
        'bg_secondary': '#161b22',
        'bg_tertiary': '#21262d',
        'text_primary': '#c9d1d9',
        'text_secondary': '#8b949e',
        'accent_primary': '#00ff88',
        'accent_secondary': '#00d4ff',
        'border_color': '#30363d',
        'font_family': 'Segoe UI',
        'font_size': 10,
        'code_font': 'Consolas',
        'code_size': 9
    })

    # Generate theme configuration
    data = {
        'theme_name': 'LightSpeed Matrix',
        'filename': 'theme_matrix.json'
    }

    try:
        output_path = theme_template.render(data)
        print(f"✓ UI Theme generated: {output_path}")
        print(f"  Theme: {data['theme_name']}")
        print(f"  Colors: Dark matrix-inspired palette")
        print(f"  Fonts: Segoe UI (UI), Consolas (Code)")
    except Exception as e:
        print(f"✗ Error: {e}")


def example_venv_setup():
    """Example: Create virtual environment setup"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Virtual Environment Setup")
    print("="*60)

    registry = get_template_registry()
    venv_template = registry.get_template("VenvSetupTemplate")

    # Customize venv setup
    venv_template.customize({
        'python_version': '3.10',
        'venv_name': 'lightspeed_env',
        'requirements': [
            'numpy>=1.24.0',
            'scipy>=1.10.0',
            'pillow>=10.0.0',
            'qrcode[pil]>=7.4.0',
            'requests>=2.31.0'
        ],
        'create_activation_script': True,
        'validate_after_creation': True
    })

    # Generate venv setup
    data = {
        'project_name': 'LightSpeed Platform',
        'base_path': Path(__file__).parent.parent,
        'filename': 'venv_setup_report.txt'
    }

    try:
        output_path = venv_template.render(data)
        print(f"✓ Venv Setup completed: {output_path}")
        print(f"  Python: 3.10")
        print(f"  Venv: lightspeed_env")
        print(f"  Requirements: 5 packages")
    except Exception as e:
        print(f"✗ Error: {e}")


def show_template_registry_info():
    """Show information about available templates"""
    print("\n" + "="*60)
    print("TEMPLATE REGISTRY INFORMATION")
    print("="*60)

    registry = get_template_registry()
    templates = registry.list_templates()

    print(f"\nTotal Templates Available: {len(templates)}\n")

    # Group by category
    doc_templates = [t for t in templates if any(x in t for x in ['QRCode', 'Table', 'Image'])]
    ui_templates = [t for t in templates if 'Theme' in t]
    test_templates = [t for t in templates if 'Venv' in t or 'Test' in t]

    print("Document Templates:")
    for template in doc_templates:
        print(f"  • {template}")

    print("\nUI Templates:")
    for template in ui_templates:
        print(f"  • {template}")

    print("\nTest Templates:")
    for template in test_templates:
        print(f"  • {template}")


def main():
    """Run all examples"""
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█  LIGHTSPEED TEMPLATE SYSTEM - USAGE EXAMPLES" + " "*12 + "█")
    print("█  Transform Demos into Production Tools" + " "*19 + "█")
    print("█" + " "*58 + "█")
    print("█"*60)

    # Show registry info
    show_template_registry_info()

    # Run examples
    try:
        example_qr_code()
    except Exception as e:
        print(f"\nQR Code example skipped: {e}")

    try:
        example_data_table()
    except Exception as e:
        print(f"\nData Table example skipped: {e}")

    try:
        example_image_processing()
    except Exception as e:
        print(f"\nImage Processing example skipped: {e}")

    try:
        example_ui_theme()
    except Exception as e:
        print(f"\nUI Theme example skipped: {e}")

    try:
        example_venv_setup()
    except Exception as e:
        print(f"\nVenv Setup example skipped: {e}")

    print("\n" + "="*60)
    print("EXAMPLES COMPLETE")
    print("="*60)
    print("\nNext Steps:")
    print("1. Check the Output/ directory for generated files")
    print("2. Open Settings > Templates in N_UNIFIED.py")
    print("3. Use Template Manager UI for interactive customization")
    print("4. Create your own custom templates")
    print("\n" + "█"*60 + "\n")


if __name__ == "__main__":
    main()
