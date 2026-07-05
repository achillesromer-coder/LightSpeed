#!/usr/bin/env python
"""
Template Deployment Script - Deploy Templates to All Floors
Uses Merovingian Template Engine to generate floor-specific components

This script deploys base templates from Merovingian (Z-4) to all floors
via Z Direct, with floor-specific customization and skinning.

Author: LightSpeed Team
Version: 0.9.5
Date: 2026-01-12
"""

from pathlib import Path
import sys
import json
import logging

# Setup paths
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _find_lightspeed_root(start: Path) -> Path:
    start = start.resolve()
    for cand in (start, *start.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return start.parent


LIGHTSPEED_ROOT = _find_lightspeed_root(Path(__file__))
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"
MEROVINGIAN_DIR = Z_AXIS_ROOT / "Z-4_Merovingian"

# Add to path
sys.path.insert(0, str(MEROVINGIAN_DIR))

# Import template engine
from core.templates.template_engine import TemplateEngine, FLOORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


# Template deployment configurations
DEPLOYMENTS = [
    # Floor-specific portal glass components
    {
        'template': 'portal_glass',
        'floors': ['Smith', 'Oracle', 'Morpheus', 'TheConstruct', 'Architect', 'Neo', 'Trinity'],
        'component_name_pattern': '{floor_name}_portal_glass',
        'variables': {
            'SECTION_1': 'Overview',
            'SECTION_1_DESCRIPTION': 'Floor status and metrics',
            'SECTION_2': 'Operations',
            'SECTION_2_DESCRIPTION': 'Floor-specific operations',
            'SECTION_3': 'Settings',
            'SECTION_3_DESCRIPTION': 'Configuration and preferences',
            'FLOOR_DESCRIPTION': 'Floor operations portal'
        }
    },

    # Core components for each floor
    {
        'template': 'component',
        'floors': ['Smith', 'Oracle', 'Morpheus', 'TheConstruct', 'Architect', 'Neo', 'Trinity'],
        'component_name_pattern': '{floor_name}CoreComponent',
        'variables': {
            'COMPONENT_DESCRIPTION': 'Core floor component',
            'FEATURE_1': 'Floor initialization',
            'FEATURE_2': 'Event bus integration',
            'FEATURE_3': 'State management',
            'EVENT_TYPES': 'floor.initialized, floor.updated, floor.error',
            'SUBSCRIBED_EVENTS': 'system.*',
            'DEPENDENCIES': 'EventBus, Logger'
        }
    },

    # Merovingian services (deployed to Merovingian itself)
    {
        'template': 'service',
        'floors': ['Merovingian'],
        'component_name_pattern': 'TemplateDeployment',
        'variables': {
            'SERVICE_NAME': 'TemplateDeployment',
            'SERVICE_DESCRIPTION': 'Template deployment and management service',
            'SERVICE_TYPE': 'System',
            'FEATURE_1': 'Automatic template deployment',
            'FEATURE_2': 'Version management',
            'FEATURE_3': 'Rollback capabilities',
            'DEPENDENCY_1': 'TemplateEngine',
            'DEPENDENCY_2': 'EventBus'
        }
    }
]


def deploy_all_templates(engine: TemplateEngine, dry_run: bool = False):
    """
    Deploy all configured templates to their target floors

    Parameters:
        engine: Template engine instance
        dry_run: If True, only simulate deployment
    """
    total_deployments = 0
    successful_deployments = 0
    failed_deployments = 0

    print("=" * 70)
    print("LightSpeed Template Deployment")
    print("=" * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE DEPLOYMENT'}")
    print()

    for deployment_config in DEPLOYMENTS:
        template_name = deployment_config['template']
        floors = deployment_config['floors']
        component_pattern = deployment_config['component_name_pattern']
        base_variables = deployment_config['variables']

        print(f"\nDeploying template: {template_name}")
        print(f"  Target floors: {', '.join(floors)}")

        for floor_name in floors:
            total_deployments += 1

            # Generate component name
            component_name = component_pattern.format(
                floor_name=floor_name,
                floor_name_lower=floor_name.lower()
            )

            # Merge base variables with floor-specific ones
            variables = base_variables.copy()

            print(f"\n  [{floor_name}] Deploying {component_name}...")

            if dry_run:
                print(f"    [DRY RUN] Would deploy to: {floor_name}")
                successful_deployments += 1
                continue

            try:
                # Deploy template
                success = engine.deploy_to_floor(
                    template_name=template_name,
                    floor_name=floor_name,
                    component_name=component_name,
                    variables=variables
                )

                if success:
                    print(f"    [OK] Successfully deployed")
                    successful_deployments += 1
                else:
                    print(f"    [FAIL] Deployment failed")
                    failed_deployments += 1

            except Exception as e:
                print(f"    [ERROR] {e}")
                logger.error(f"Deployment error: {e}", exc_info=True)
                failed_deployments += 1

    # Summary
    print("\n" + "=" * 70)
    print("Deployment Summary")
    print("=" * 70)
    print(f"Total deployments: {total_deployments}")
    print(f"Successful: {successful_deployments}")
    print(f"Failed: {failed_deployments}")
    print(f"Success rate: {(successful_deployments/total_deployments*100):.1f}%")

    return successful_deployments == total_deployments


def update_floor_init_files(engine: TemplateEngine):
    """
    Update __init__.py files in each floor to export new components

    Parameters:
        engine: Template engine instance
    """
    print("\n" + "=" * 70)
    print("Updating Floor __init__.py Files")
    print("=" * 70)

    for floor_name, floor_info in FLOORS.items():
        print(f"\n[{floor_name}] Updating exports...")

        floor_dir = Z_AXIS_ROOT / floor_info["dir"]
        components_dir = floor_dir / "components"
        init_file = components_dir / "__init__.py"

        if not components_dir.exists():
            print(f"  [SKIP] Components directory not found")
            continue

        try:
            # Find all Python files in components
            component_files = list(components_dir.glob("*.py"))
            component_files = [f for f in component_files if f.name != "__init__.py"]

            # Extract component class names
            exports = []
            for comp_file in component_files:
                # Read file and find class definitions
                try:
                    with open(comp_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Find classes
                    import re
                    classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
                    exports.extend(classes)

                except Exception as e:
                    logger.error(f"Error reading {comp_file}: {e}")

            # Update __init__.py
            if exports:
                init_content = f'''"""
{floor_name} Floor - Components Package

Auto-generated exports for {floor_name} floor components.
Generated: {Path(__file__).parent.stem}

Author: LightSpeed Team
Version: 0.9.5
"""

__version__ = "0.9.5"
__floor__ = "{floor_name}"
__z_level__ = {floor_info["z_level"]}

# Component exports
__all__ = {exports}

# Import components
'''

                for export in exports:
                    # Find module name
                    module_name = None
                    for comp_file in component_files:
                        with open(comp_file, 'r', encoding='utf-8') as f:
                            if f"class {export}" in f.read():
                                module_name = comp_file.stem
                                break

                    if module_name:
                        init_content += f"from .{module_name} import {export}\n"

                # Write __init__.py
                with open(init_file, 'w', encoding='utf-8') as f:
                    f.write(init_content)

                print(f"  [OK] Exported {len(exports)} components")
            else:
                print(f"  [SKIP] No components found")

        except Exception as e:
            print(f"  [ERROR] {e}")
            logger.error(f"Error updating __init__.py: {e}", exc_info=True)


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Deploy templates to Z-Axis floors")
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Simulate deployment without creating files"
    )
    parser.add_argument(
        '--no-init-update',
        action='store_true',
        help="Skip updating __init__.py files"
    )
    parser.add_argument(
        '--floor',
        type=str,
        help="Deploy to specific floor only"
    )

    args = parser.parse_args()

    # Initialize template engine
    print("Initializing Template Engine...")
    engine = TemplateEngine(LIGHTSPEED_ROOT)
    print(f"[OK] Loaded {len(engine.templates)} templates from Merovingian\n")

    # Filter deployments if specific floor requested
    if args.floor:
        for config in DEPLOYMENTS:
            config['floors'] = [f for f in config['floors'] if f == args.floor]

    # Deploy templates
    success = deploy_all_templates(engine, dry_run=args.dry_run)

    # Update __init__.py files
    if not args.dry_run and not args.no_init_update:
        update_floor_init_files(engine)

    # Final status
    print("\n" + "=" * 70)
    if success:
        print("[SUCCESS] All templates deployed successfully!")
    else:
        print("[PARTIAL] Some deployments failed")
    print("=" * 70)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
