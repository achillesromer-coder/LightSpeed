"""
Project Workspace Creator - v5.1.2
Construct workspace creation system with Z-axis smart-floor integration.

This is the core engine that creates isolated project environments pulling
components from active Z-floors with spherical layout and standards validation.

Author: LightSpeed Team
Date: April 8, 2026
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum
import json
import shutil

# Floor-native paths (projects belong to Architect; disk is a projection of DB truth)
try:
    from core.config.paths import PROJECTS_ROOT  # type: ignore
except Exception:
    PROJECTS_ROOT = Path("projects")

# Import workspace type definitions
from .workspace_types import (
    WorkspaceType,
    WorkspaceStatus,
    WorkspaceTypeConfig,
    WorkspaceTemplate,
    Z_FLOOR_COMPONENTS,
    WORKSPACE_CONFIGS,
    get_workspace_config,
    get_template
)


# ==============================================================================
# Data Models
# ==============================================================================

@dataclass
class SphericalPosition:
    """3D position in spherical coordinates"""
    theta: float  # Horizontal angle (0-360 deg)
    phi: float    # Vertical angle (-90 to +90 deg)
    depth: float  # Distance from center (0.0-1.0)

    def to_dict(self) -> Dict[str, float]:
        return {'theta': self.theta, 'phi': self.phi, 'depth': self.depth}


@dataclass
class WorkspaceComponent:
    """Component instance in a workspace"""
    component_id: str
    component_name: str
    z_floor: str
    category: str
    position: SphericalPosition
    config: Dict[str, Any] = field(default_factory=dict)
    visible: bool = True
    enabled: bool = True
    loaded_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'component_id': self.component_id,
            'component_name': self.component_name,
            'z_floor': self.z_floor,
            'category': self.category,
            'position': self.position.to_dict(),
            'config': self.config,
            'visible': self.visible,
            'enabled': self.enabled,
            'loaded_at': self.loaded_at.isoformat()
        }


@dataclass
class SphericalLayout:
    """Spherical UI layout configuration"""
    fov: float = 70.0  # Field of view in degrees
    grid_width: int = 8  # Horizontal grid sections
    grid_height: int = 6  # Vertical grid sections
    camera_angle: float = 0.0  # Current camera pan angle
    camera_tilt: float = 0.0   # Current camera tilt
    camera_zoom: float = 1.0   # Zoom level
    background_color: str = '#1a1a1a'
    grid_visible: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SchemaDefinition:
    """Schema definition for data validation"""
    schema_type: str  # 'IEEE', 'NIST', 'STEP', 'Dublin Core', etc.
    version: str
    fields: Dict[str, Any]
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Bibliography:
    """Bibliography management for workspace"""
    entries: List[Dict[str, Any]] = field(default_factory=list)
    style: str = 'IEEE'  # Citation style
    auto_update: bool = True
    last_updated: datetime = field(default_factory=datetime.now)

    def add_entry(self, entry: Dict[str, Any]):
        """Add bibliography entry"""
        self.entries.append(entry)
        self.last_updated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'entries': self.entries,
            'style': self.style,
            'auto_update': self.auto_update,
            'last_updated': self.last_updated.isoformat()
        }


@dataclass
class ProjectIndex:
    """Automatic index generation"""
    subject_index: Dict[str, List[str]] = field(default_factory=dict)
    author_index: Dict[str, List[str]] = field(default_factory=dict)
    term_index: Dict[str, List[str]] = field(default_factory=dict)
    auto_generate: bool = True
    last_generated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'subject_index': self.subject_index,
            'author_index': self.author_index,
            'term_index': self.term_index,
            'auto_generate': self.auto_generate,
            'last_generated': self.last_generated.isoformat()
        }


@dataclass
class ProjectWorkspace:
    """Complete project workspace definition"""
    id: str
    name: str
    workspace_type: WorkspaceType
    description: str = ""
    status: WorkspaceStatus = WorkspaceStatus.ACTIVE

    # Components and layout
    components: List[WorkspaceComponent] = field(default_factory=list)
    spherical_layout: SphericalLayout = field(default_factory=SphericalLayout)

# Z-axis smart-floor integration
    z_components: Dict[str, List[str]] = field(default_factory=dict)
    available_z_floors: List[str] = field(default_factory=list)

    # Standards and compliance
    schemas: List[SchemaDefinition] = field(default_factory=list)
    standards_compliance: Dict[str, bool] = field(default_factory=dict)
    required_standards: List[str] = field(default_factory=list)

    # Bibliography and indexing
    bibliography: Bibliography = field(default_factory=Bibliography)
    index: ProjectIndex = field(default_factory=ProjectIndex)

    # Tools and integrations
    integrated_tools: List[str] = field(default_factory=list)
    tool_configs: Dict[str, Any] = field(default_factory=dict)

    # Filesystem
    workspace_path: Optional[Path] = None
    data_path: Optional[Path] = None
    output_path: Optional[Path] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "LightSpeed User"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize workspace to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'workspace_type': self.workspace_type.value,
            'description': self.description,
            'status': self.status.value,
            'components': [c.to_dict() for c in self.components],
            'spherical_layout': self.spherical_layout.to_dict(),
            'z_components': self.z_components,
            'available_z_floors': self.available_z_floors,
            'schemas': [s.to_dict() for s in self.schemas],
            'standards_compliance': self.standards_compliance,
            'required_standards': self.required_standards,
            'bibliography': self.bibliography.to_dict(),
            'index': self.index.to_dict(),
            'integrated_tools': self.integrated_tools,
            'tool_configs': self.tool_configs,
            'workspace_path': str(self.workspace_path) if self.workspace_path else None,
            'data_path': str(self.data_path) if self.data_path else None,
            'output_path': str(self.output_path) if self.output_path else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by,
            'tags': self.tags,
            'metadata': self.metadata
        }

    def save(self, base_path: Optional[Path] = None):
        """Save workspace configuration to JSON"""
        if base_path is None:
            base_path = self.workspace_path

        if base_path is None:
            raise ValueError("No workspace path specified")

        config_file = Path(base_path) / "workspace.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

        return config_file


# ==============================================================================
# Workspace Creator
# ==============================================================================

class ProjectWorkspaceCreator:
    """
    Main workspace creation engine

    Creates isolated project environments that pull components from all Z-floors
        with spherical layout and standards validation.
    """

    SCHEMA_TEMPLATE_VERSION = "0.9.5"

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize workspace creator

        Args:
            base_path: Base directory for workspaces.
                Default is floor-native under Architect projects:
                `Z Axis/Z+1_Architect/projects/default_company/default_workspace/workspaces/`
        """
        self.base_path = (
            Path(base_path)
            if base_path
            else Path(PROJECTS_ROOT) / "default_company" / "default_workspace" / "workspaces"
        )
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Registry of available components from all Z-floors
        self.z_floor_components = Z_FLOOR_COMPONENTS
        self.component_floor_index = {
            component_id: floor
            for floor, floor_data in self.z_floor_components.items()
            for component_id in floor_data['components']
        }
        self.workspace_configs = WORKSPACE_CONFIGS

        # Workspace registry
        self.workspaces: Dict[str, ProjectWorkspace] = {}

        # Load existing workspaces
        self._load_existing_workspaces()

    def _load_existing_workspaces(self):
        """Load existing workspaces from base_path"""
        if not self.base_path.exists():
            return

        for workspace_dir in self.base_path.iterdir():
            if workspace_dir.is_dir():
                config_file = workspace_dir / "workspace.json"
                if config_file.exists():
                    try:
                        workspace = self.load_workspace(str(config_file))
                        self.workspaces[workspace.id] = workspace
                    except Exception as e:
                        print(f"Warning: Could not load workspace from {config_file}: {e}")

    def create_workspace(
        self,
        name: str,
        workspace_type: WorkspaceType,
        description: str = "",
        template_id: Optional[str] = None,
        custom_components: Optional[List[Dict[str, Any]]] = None
    ) -> ProjectWorkspace:
        """
        Create a new project workspace

        Args:
            name: Workspace name
            workspace_type: Type of workspace
            description: Workspace description
            template_id: Optional template to apply
            custom_components: Optional list of custom components to add

        Returns:
            Created ProjectWorkspace instance
        """
        # Generate workspace ID
        workspace_id = f"ws_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name.lower().replace(' ', '_')}"

        # Get workspace type configuration
        config = get_workspace_config(workspace_type)

        # Create workspace directory structure
        workspace_path = self.base_path / workspace_id
        workspace_path.mkdir(parents=True, exist_ok=True)

        (workspace_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
        (workspace_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
        (workspace_path / "output" / "reports").mkdir(parents=True, exist_ok=True)
        (workspace_path / "output" / "exports").mkdir(parents=True, exist_ok=True)
        (workspace_path / "docs").mkdir(parents=True, exist_ok=True)
        (workspace_path / "schemas").mkdir(parents=True, exist_ok=True)

        # Create workspace instance
        workspace = ProjectWorkspace(
            id=workspace_id,
            name=name,
            workspace_type=workspace_type,
            description=description,
            workspace_path=workspace_path,
            data_path=workspace_path / "data",
            output_path=workspace_path / "output",
            required_standards=config.standards_required,
            available_z_floors=config.required_z_floors,
            spherical_layout=SphericalLayout(
                grid_width=config.default_layout_grid[0],
                grid_height=config.default_layout_grid[1]
            )
        )

        # Apply template if specified
        if template_id:
            template = get_template(template_id)
            if template:
                self._apply_template(workspace, template)

        # Add recommended components
        self._add_recommended_components(workspace, config)

        # Add custom components if provided
        if custom_components:
            for comp_spec in custom_components:
                self.add_component(
                    workspace,
                    comp_spec['component_id'],
                    position=SphericalPosition(**comp_spec.get('position', {'theta': 0, 'phi': 0, 'depth': 0.8})),
                    config=comp_spec.get('config', {})
                )

        self._sync_available_z_floors(workspace)

        # Initialize schemas for required standards
        self._initialize_schemas(workspace)

        # Initialize bibliography
        workspace.bibliography = Bibliography(style=config.standards_required[0] if config.standards_required else 'IEEE')

        # Save workspace
        workspace.save()

        # Register workspace
        self.workspaces[workspace_id] = workspace

        print(f"[WorkspaceCreator] Created workspace: {name} ({workspace_type.value})")
        print(f"  -> Path: {workspace_path}")
        print(f"  -> Components: {len(workspace.components)}")
        print(f"  -> Standards: {', '.join(workspace.required_standards)}")

        return workspace

    @staticmethod
    def _workspace_has_component(workspace: ProjectWorkspace, component_id: str) -> bool:
        """Check whether a workspace already contains a component ID."""
        return any(component.component_id == component_id for component in workspace.components)

    def _sync_available_z_floors(self, workspace: ProjectWorkspace) -> None:
        """Keep available-floor metadata aligned with configured and loaded components."""
        floors: List[str] = []
        seen: set[str] = set()

        def _remember(floor: str) -> None:
            if floor and floor not in seen:
                seen.add(floor)
                floors.append(floor)

        for floor in workspace.available_z_floors:
            _remember(floor)

        config = self.workspace_configs.get(workspace.workspace_type)
        if config is not None:
            for floor in config.required_z_floors:
                _remember(floor)

        for component in workspace.components:
            _remember(component.z_floor)

        workspace.available_z_floors = floors

    def _add_recommended_components(self, workspace: ProjectWorkspace, config: WorkspaceTypeConfig):
        """Add recommended components for workspace type"""
        # Position components in spherical layout
        positions = self._generate_component_positions(len(config.recommended_components))

        for i, component_id in enumerate(config.recommended_components):
            if self._workspace_has_component(workspace, component_id):
                continue

            # Find which Z-floor this component belongs to
            z_floor = self._find_component_floor(component_id)

            if z_floor:
                self.add_component(
                    workspace,
                    component_id,
                    position=positions[i],
                    config={}
                )

    def _generate_component_positions(self, count: int) -> List[SphericalPosition]:
        """Generate evenly distributed positions in spherical space"""
        positions = []

        # Distribute components around the sphere
        theta_step = 360 / max(count, 1)

        for i in range(count):
            theta = i * theta_step
            phi = 0  # Keep on equator by default
            depth = 0.7 + (i % 3) * 0.1  # Vary depth slightly

            positions.append(SphericalPosition(theta, phi, depth))

        return positions

    def _find_component_floor(self, component_id: str) -> Optional[str]:
        """Find which Z-floor a component belongs to"""
        return self.component_floor_index.get(component_id)

    def add_component(
        self,
        workspace: ProjectWorkspace,
        component_id: str,
        position: SphericalPosition,
        config: Optional[Dict[str, Any]] = None
    ) -> WorkspaceComponent:
        """
        Add a component to workspace

        Args:
            workspace: Workspace to add to
            component_id: Component identifier
            position: Position in spherical coordinates
            config: Optional component configuration

        Returns:
            Created WorkspaceComponent instance
        """
        # Find component's Z-floor
        z_floor = self._find_component_floor(component_id)

        if not z_floor:
            raise ValueError(f"Component '{component_id}' not found in any Z-floor")

        # Get category
        category = self.z_floor_components[z_floor]['category']

        # Create component instance
        component = WorkspaceComponent(
            component_id=component_id,
            component_name=component_id.replace('_', ' ').title(),
            z_floor=z_floor,
            category=category,
            position=position,
            config=config or {}
        )

        # Add to workspace
        workspace.components.append(component)

        # Update Z-components mapping
        if z_floor not in workspace.z_components:
            workspace.z_components[z_floor] = []
        workspace.z_components[z_floor].append(component_id)

        self._sync_available_z_floors(workspace)
        workspace.updated_at = datetime.now()

        return component

    def _apply_template(self, workspace: ProjectWorkspace, template: WorkspaceTemplate):
        """Apply template to workspace"""
        print(f"[WorkspaceCreator] Applying template: {template.name}")

        # Add pre-configured components
        for comp_spec in template.pre_configured_components:
            if self._workspace_has_component(workspace, comp_spec['component_id']):
                continue

            pos_data = comp_spec['position']
            position = SphericalPosition(pos_data[0], pos_data[1], pos_data[2])

            self.add_component(
                workspace,
                comp_spec['component_id'],
                position=position,
                config=comp_spec['config']
            )

        # Copy sample files
        for sample_file in template.sample_files:
            try:
                lightspeed_root = Path(__file__).resolve().parents[2]
                src = lightspeed_root / sample_file
                dst = (workspace.workspace_path / sample_file) if workspace.workspace_path else None

                if dst is None:
                    continue

                dst.parent.mkdir(parents=True, exist_ok=True)

                if src.exists() and src.is_file():
                    shutil.copy2(src, dst)
                    print(f"[WorkspaceCreator]   + Sample file: {sample_file}")
                else:
                    # Create an empty placeholder so the workspace is structurally complete.
                    # Record in metadata so the user can populate it later.
                    if not dst.exists():
                        dst.write_text("", encoding="utf-8")
                    missing = workspace.metadata.setdefault("missing_sample_files", [])
                    if sample_file not in missing:
                        missing.append(sample_file)
                    print(f"[WorkspaceCreator]   ! Missing sample file (created empty): {sample_file}")
            except Exception as e:
                print(f"[WorkspaceCreator]   ! Failed sample file '{sample_file}': {e}")

        # Set tutorial path
        if template.tutorial_path:
            workspace.metadata['tutorial_path'] = template.tutorial_path

    def _initialize_schemas(self, workspace: ProjectWorkspace):
        """Initialize schema definitions for required standards"""
        for standard in workspace.required_standards:
            schema = self._create_schema_for_standard(standard)
            if schema:
                workspace.schemas.append(schema)
                workspace.standards_compliance[standard] = False  # Not validated yet

    def _create_schema_for_standard(self, standard: str) -> Optional[SchemaDefinition]:
        """Create schema definition for a standard"""
        schema_templates = {
            'IEEE': SchemaDefinition(
                schema_type='IEEE',
                version=self.SCHEMA_TEMPLATE_VERSION,
                fields={
                    'title': 'string',
                    'author': 'list[string]',
                    'journal': 'string',
                    'year': 'integer',
                    'doi': 'string',
                    'abstract': 'string'
                },
                validation_rules=[
                    {'field': 'year', 'rule': 'range', 'min': 1900, 'max': 2100},
                    {'field': 'doi', 'rule': 'pattern', 'pattern': r'10\.\d{4,}/.*'}
                ],
                required=True
            ),
            'Dublin Core': SchemaDefinition(
                schema_type='Dublin Core',
                version=self.SCHEMA_TEMPLATE_VERSION,
                fields={
                    'dc:title': 'string',
                    'dc:creator': 'string',
                    'dc:subject': 'list[string]',
                    'dc:description': 'string',
                    'dc:date': 'date',
                    'dc:identifier': 'string',
                    'dc:rights': 'string'
                },
                required=True
            ),
            'BibTeX': SchemaDefinition(
                schema_type='BibTeX',
                version=self.SCHEMA_TEMPLATE_VERSION,
                fields={
                    'author': 'string',
                    'title': 'string',
                    'year': 'integer',
                    'journal': 'string',
                    'volume': 'integer',
                    'pages': 'string',
                    'doi': 'string'
                },
                required=True
            ),
            'STEP AP242': SchemaDefinition(
                schema_type='STEP AP242',
                version=self.SCHEMA_TEMPLATE_VERSION,
                fields={
                    'product_definition': 'object',
                    'shape_representation': 'object',
                    'geometric_model': 'object',
                    'material': 'object'
                },
                required=False
            ),
            'NIST SP 800-53': SchemaDefinition(
                schema_type='NIST SP 800-53',
                version='Rev. 5',
                fields={
                    'control_id': 'string',
                    'control_name': 'string',
                    'control_family': 'string',
                    'implementation_status': 'enum[implemented,planned,not_applicable]'
                },
                required=False
            )
        }

        return schema_templates.get(standard)

    def load_workspace(self, config_path: str | Path) -> ProjectWorkspace:
        """Load workspace from configuration file"""
        config_path = Path(config_path)
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Reconstruct workspace
        workspace = ProjectWorkspace(
            id=data['id'],
            name=data['name'],
            workspace_type=WorkspaceType(data['workspace_type']),
            description=data.get('description', ''),
            status=WorkspaceStatus(data.get('status', 'active')),
            workspace_path=Path(data['workspace_path']) if data.get('workspace_path') else None,
            data_path=Path(data['data_path']) if data.get('data_path') else None,
            output_path=Path(data['output_path']) if data.get('output_path') else None,
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            created_by=data.get('created_by', 'LightSpeed User'),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )

        # Reconstruct components
        for comp_data in data.get('components', []):
            position = SphericalPosition(**comp_data['position'])
            component = WorkspaceComponent(
                component_id=comp_data['component_id'],
                component_name=comp_data['component_name'],
                z_floor=comp_data['z_floor'],
                category=comp_data['category'],
                position=position,
                config=comp_data.get('config', {}),
                visible=comp_data.get('visible', True),
                enabled=comp_data.get('enabled', True),
                loaded_at=datetime.fromisoformat(comp_data['loaded_at'])
            )
            workspace.components.append(component)

        # Reconstruct other fields
        workspace.z_components = data.get('z_components', {})
        workspace.available_z_floors = data.get('available_z_floors', [])
        workspace.required_standards = data.get('required_standards', [])
        workspace.standards_compliance = data.get('standards_compliance', {})
        workspace.integrated_tools = data.get('integrated_tools', [])
        workspace.tool_configs = data.get('tool_configs', {})

        # Reconstruct spherical layout
        if 'spherical_layout' in data:
            workspace.spherical_layout = SphericalLayout(**data['spherical_layout'])

        # Reconstruct bibliography
        if 'bibliography' in data:
            bib_data = data['bibliography']
            workspace.bibliography = Bibliography(
                entries=bib_data.get('entries', []),
                style=bib_data.get('style', 'IEEE'),
                auto_update=bib_data.get('auto_update', True),
                last_updated=datetime.fromisoformat(bib_data['last_updated'])
            )

        # Reconstruct schemas
        for schema_data in data.get('schemas', []):
            schema = SchemaDefinition(**schema_data)
            workspace.schemas.append(schema)

        self._sync_available_z_floors(workspace)
        return workspace

    def list_workspaces(self, workspace_type: Optional[WorkspaceType] = None, status: Optional[WorkspaceStatus] = None) -> List[ProjectWorkspace]:
        """List workspaces with optional filtering"""
        workspaces = list(self.workspaces.values())

        if workspace_type:
            workspaces = [ws for ws in workspaces if ws.workspace_type == workspace_type]

        if status:
            workspaces = [ws for ws in workspaces if ws.status == status]

        return workspaces

    def get_workspace(self, workspace_id: str) -> Optional[ProjectWorkspace]:
        """Get workspace by ID"""
        return self.workspaces.get(workspace_id)

    def delete_workspace(self, workspace_id: str, remove_files: bool = False):
        """Delete workspace"""
        workspace = self.workspaces.get(workspace_id)

        if not workspace:
            raise ValueError(f"Workspace '{workspace_id}' not found")

        if remove_files and workspace.workspace_path and workspace.workspace_path.exists():
            shutil.rmtree(workspace.workspace_path)

        del self.workspaces[workspace_id]

        print(f"[WorkspaceCreator] Deleted workspace: {workspace.name}")
