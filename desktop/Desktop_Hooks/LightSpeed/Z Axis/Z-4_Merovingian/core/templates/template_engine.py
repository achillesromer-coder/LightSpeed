"""
Template Engine - Smart Floor Template System
Merovingian Floor (Z-4) - Core Template Management

Centralized template system that generates floor-specific components,
services, and portals. Templates live in Merovingian and are deployed
to floors via Z Direct with floor-specific tailoring.

Features:
- Template generation from base patterns
- Floor-specific customization via Z Direct
- Skinning and theming system
- Version control and rollback
- Template validation and testing

Author: LightSpeed Team
Version: 0.9.5
Date: 2026-01-12
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
import re

logger = logging.getLogger(__name__)


# Floor definitions from Z Direct manifests
FLOORS = {
    "Merovingian": {"z_level": -4, "dir": "Z-4_Merovingian", "color": "#00DDFF"},
    "Smith": {"z_level": -3, "dir": "Z-3_Smith", "color": "#00FF88"},
    "Oracle": {"z_level": -2, "dir": "Z-2_Oracle", "color": "#FF8800"},
    "Morpheus": {"z_level": -1, "dir": "Z-1_Morpheus", "color": "#8800FF"},
    "TheConstruct": {"z_level": 0, "dir": "Z0_TheConstruct", "color": "#FF00FF"},
    "Architect": {"z_level": 1, "dir": "Z+1_Architect", "color": "#00FFFF"},
    "Neo": {"z_level": 2, "dir": "Z+2_Neo", "color": "#FFFF00"},
    "Trinity": {"z_level": 3, "dir": "Z+3_Trinity", "color": "#FF0088"}
}


@dataclass
class TemplateMetadata:
    """Metadata for template"""
    name: str
    type: str  # component, service, portal, tool
    version: str
    author: str
    created: str
    description: str
    variables: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)


class TemplateEngine:
    """
    Central template generation and deployment engine

    Manages all LightSpeed templates from Merovingian (Z-4) and deploys
    them to other floors via Z Direct with floor-specific customization.
    """

    def __init__(self, lightspeed_root: Path):
        """Initialize template engine"""
        self.lightspeed_root = Path(lightspeed_root)
        self.z_axis_root = self.lightspeed_root / "Z Axis"
        self.merovingian_dir = self.z_axis_root / "Z-4_Merovingian"
        self.templates_dir = self.merovingian_dir / "core" / "templates"

        # Template cache
        self.templates: Dict[str, str] = {}
        self.metadata: Dict[str, TemplateMetadata] = {}

        # Ensure directories exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Load templates
        self._load_templates()

        logger.info("Template Engine initialized")

    def _load_templates(self):
        """Load all templates from disk"""
        template_files = list(self.templates_dir.glob("*.template"))

        for template_file in template_files:
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract metadata from template header
                metadata = self._extract_metadata(content)
                template_name = template_file.stem

                self.templates[template_name] = content
                self.metadata[template_name] = metadata

                logger.info(f"Loaded template: {template_name}")

            except Exception as e:
                logger.error(f"Failed to load template {template_file}: {e}")

    def _extract_metadata(self, template_content: str) -> TemplateMetadata:
        """Extract metadata from template header comments"""
        # Find metadata in template header
        metadata_pattern = r'/\*\*\s*TEMPLATE_METADATA\s*({.*?})\s*\*/'
        match = re.search(metadata_pattern, template_content, re.DOTALL)

        if match:
            metadata_json = match.group(1)
            metadata_dict = json.loads(metadata_json)
            return TemplateMetadata(**metadata_dict)

        # Default metadata if none found
        return TemplateMetadata(
            name="unknown",
            type="component",
            version="0.9.5",
            author="LightSpeed Team",
            created=datetime.now().isoformat(),
            description="No description"
        )

    def generate(
        self,
        template_name: str,
        floor_name: str,
        variables: Dict[str, Any],
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate code from template with floor-specific customization

        Parameters:
            template_name: Name of template to use
            floor_name: Target floor name (e.g., "Neo", "Trinity")
            variables: Variables to substitute in template
            output_path: Optional output file path

        Returns:
            Generated code as string
        """
        if template_name not in self.templates:
            raise ValueError(f"Template not found: {template_name}")

        # Get template content
        template = self.templates[template_name]

        # Add floor-specific variables from Z Direct
        floor_vars = self._load_floor_variables(floor_name)
        all_variables = {**floor_vars, **variables}

        # Perform substitution
        generated = self._substitute_variables(template, all_variables)

        # Save to file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(generated)
            logger.info(f"Generated file: {output_path}")

        return generated

    def _load_floor_variables(self, floor_name: str) -> Dict[str, Any]:
        """
        Load floor-specific variables from Z Direct manifest

        Parameters:
            floor_name: Floor name (e.g., "Neo")

        Returns:
            Dictionary of floor variables
        """
        if floor_name not in FLOORS:
            logger.warning(f"Unknown floor: {floor_name}")
            return {}

        floor_info = FLOORS[floor_name]
        floor_dir = self.z_axis_root / floor_info["dir"]
        manifest_path = floor_dir / "Z Direct" / "floor_manifest.json"

        # Load manifest
        if not manifest_path.exists():
            logger.warning(f"Floor manifest not found: {manifest_path}")
            return {}

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            # Return floor variables
            return {
                'FLOOR_NAME': floor_name,
                'FLOOR_DIR': floor_info["dir"],
                'Z_LEVEL': floor_info["z_level"],
                'FLOOR_COLOR': floor_info["color"],
                'FLOOR_DESCRIPTION': manifest.get('description', ''),
                'FLOOR_VERSION': manifest.get('version', '0.9.5'),
                'FLOOR_SERVICES': manifest.get('services', {}),
                'FLOOR_DEPENDENCIES': manifest.get('dependencies', []),
                'FLOOR_DEPENDENTS': manifest.get('dependents', [])
            }

        except Exception as e:
            logger.error(f"Failed to load floor manifest: {e}")
            return {}

    def _substitute_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Substitute variables in template

        Supports:
        - Simple: {VARIABLE_NAME}
        - Conditional: {?VARIABLE_NAME}content{/VARIABLE_NAME}
        - Loop: {#VARIABLE_NAME}content{/VARIABLE_NAME}

        Parameters:
            template: Template content
            variables: Variables to substitute

        Returns:
            Template with variables substituted
        """
        result = template

        # Simple variable substitution
        for key, value in variables.items():
            pattern = r'\{' + re.escape(key) + r'\}'
            if isinstance(value, (list, dict)):
                value = json.dumps(value, indent=2)
            result = re.sub(pattern, str(value), result)

        # Handle lowercase variants (e.g., {component_name} from {COMPONENT_NAME})
        for key, value in variables.items():
            if key.isupper():
                lowercase_key = key.lower()
                pattern = r'\{' + re.escape(lowercase_key) + r'\}'
                if isinstance(value, (list, dict)):
                    value_str = json.dumps(value, indent=2)
                else:
                    value_str = str(value).lower() if isinstance(value, str) else str(value)
                result = re.sub(pattern, value_str, result)

        return result

    def deploy_to_floor(
        self,
        template_name: str,
        floor_name: str,
        component_name: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Deploy template to specific floor

        Parameters:
            template_name: Template to deploy
            floor_name: Target floor
            component_name: Name of component to create
            variables: Additional variables (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            floor_info = FLOORS.get(floor_name)
            if not floor_info:
                logger.error(f"Unknown floor: {floor_name}")
                return False

            # Determine output path based on template type
            metadata = self.metadata.get(template_name)
            if not metadata:
                logger.error(f"Template metadata not found: {template_name}")
                return False

            floor_dir = self.z_axis_root / floor_info["dir"]

            # Choose directory based on template type
            type_dirs = {
                'component': 'components',
                'service': 'core/services',
                'portal': 'components',
                'tool': 'tools'
            }

            output_dir = floor_dir / type_dirs.get(metadata.type, 'components')
            output_path = output_dir / f"{component_name}.py"

            # Prepare variables
            deploy_variables = variables or {}
            deploy_variables['COMPONENT_NAME'] = component_name

            # Generate and save
            self.generate(
                template_name=template_name,
                floor_name=floor_name,
                variables=deploy_variables,
                output_path=output_path
            )

            logger.info(f"Deployed {template_name} to {floor_name}: {output_path}")

            # Record deployment in Z Direct
            self._record_deployment(floor_name, template_name, component_name, output_path)

            return True

        except Exception as e:
            logger.error(f"Failed to deploy template: {e}", exc_info=True)
            return False

    def _record_deployment(
        self,
        floor_name: str,
        template_name: str,
        component_name: str,
        output_path: Path
    ):
        """Record template deployment in Z Direct"""
        floor_info = FLOORS.get(floor_name)
        if not floor_info:
            return

        floor_dir = self.z_axis_root / floor_info["dir"]
        deployments_file = floor_dir / "Z Direct" / "template_deployments.json"

        # Load existing deployments
        deployments = []
        if deployments_file.exists():
            try:
                with open(deployments_file, 'r', encoding='utf-8') as f:
                    deployments = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load deployments: {e}")

        # Add new deployment
        deployments.append({
            'template': template_name,
            'component': component_name,
            'output_path': str(output_path.relative_to(self.z_axis_root)),
            'deployed_at': datetime.now().isoformat(),
            'version': '0.9.5'
        })

        # Save deployments
        try:
            deployments_file.parent.mkdir(parents=True, exist_ok=True)
            with open(deployments_file, 'w', encoding='utf-8') as f:
                json.dump(deployments, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save deployments: {e}")

    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List all available templates

        Returns:
            List of template information dictionaries
        """
        templates_list = []

        for name, metadata in self.metadata.items():
            templates_list.append({
                'name': name,
                'type': metadata.type,
                'version': metadata.version,
                'description': metadata.description,
                'variables': metadata.variables,
                'requirements': metadata.requirements
            })

        return templates_list

    def create_template(
        self,
        name: str,
        type: str,
        content: str,
        metadata: Optional[TemplateMetadata] = None
    ) -> bool:
        """
        Create new template

        Parameters:
            name: Template name
            type: Template type (component, service, portal, tool)
            content: Template content
            metadata: Optional template metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            template_path = self.templates_dir / f"{name}.template"

            # Create metadata if not provided
            if not metadata:
                metadata = TemplateMetadata(
                    name=name,
                    type=type,
                    version="0.9.5",
                    author="LightSpeed Team",
                    created=datetime.now().isoformat(),
                    description=f"{name} template"
                )

            # Add metadata header to template
            metadata_header = f"""/**
TEMPLATE_METADATA
{{
    "name": "{metadata.name}",
    "type": "{metadata.type}",
    "version": "{metadata.version}",
    "author": "{metadata.author}",
    "created": "{metadata.created}",
    "description": "{metadata.description}"
}}
*/

"""

            full_content = metadata_header + content

            # Save template
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(full_content)

            # Add to cache
            self.templates[name] = full_content
            self.metadata[name] = metadata

            logger.info(f"Created template: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create template: {e}", exc_info=True)
            return False


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize engine
    lightspeed_root = Path(__file__).parents[4]
    engine = TemplateEngine(lightspeed_root)

    # List templates
    print("\nAvailable Templates:")
    for template in engine.list_templates():
        print(f"  - {template['name']} ({template['type']}): {template['description']}")

    print(f"\n✓ Template Engine initialized with {len(engine.templates)} templates")
