"""
Project Workspace System - v5.1.2

Construct scenario workspace contract backed by Merovingian core services.
This package exposes the active workspace creator, component puller,
layout bridge, and schema validator without reviving old standalone UI shells.
"""

from .workspace_creator import (
    ProjectWorkspace,
    ProjectWorkspaceCreator,
    WorkspaceComponent,
    SphericalPosition,
    SphericalLayout,
    SchemaDefinition,
    Bibliography,
    ProjectIndex,
)
from .workspace_types import (
    WorkspaceType,
    WorkspaceStatus,
    WorkspaceTypeConfig,
    WorkspaceTemplate,
    get_workspace_config,
    get_template,
    list_templates_by_type,
    get_component_contract_workspace_type_values,
    normalize_workspace_type_value,
)
from .component_puller import (
    ComponentCapability,
    ComponentMetadata,
    ComponentPuller,
    ComponentRegistry,
    create_component_puller,
    discover_components_for_workspace,
)
from .spherical_layout import (
    LayoutMode,
    LayoutPreset,
    WorkspaceSphericalLayout,
    create_workspace_layout,
)
from .schema_validator import (
    SchemaValidator,
    ValidationIssue,
    ValidationLevel,
    ValidationReport,
    create_schema_validator,
    validate_bibtex_entry,
    validate_dublin_core,
    validate_ieee_metadata,
)

__all__ = [
    'ProjectWorkspace',
    'ProjectWorkspaceCreator',
    'WorkspaceComponent',
    'SphericalPosition',
    'SphericalLayout',
    'SchemaDefinition',
    'Bibliography',
    'ProjectIndex',
    'WorkspaceType',
    'WorkspaceStatus',
    'WorkspaceTypeConfig',
    'WorkspaceTemplate',
    'get_workspace_config',
    'get_template',
    'list_templates_by_type',
    'get_component_contract_workspace_type_values',
    'normalize_workspace_type_value',
    'ComponentCapability',
    'ComponentMetadata',
    'ComponentPuller',
    'ComponentRegistry',
    'create_component_puller',
    'discover_components_for_workspace',
    'LayoutMode',
    'LayoutPreset',
    'WorkspaceSphericalLayout',
    'create_workspace_layout',
    'SchemaValidator',
    'ValidationIssue',
    'ValidationLevel',
    'ValidationReport',
    'create_schema_validator',
    'validate_bibtex_entry',
    'validate_dublin_core',
    'validate_ieee_metadata',
]

__version__ = "5.1.2"
__author__ = 'LightSpeed Team'
__date__ = 'April 8, 2026'
