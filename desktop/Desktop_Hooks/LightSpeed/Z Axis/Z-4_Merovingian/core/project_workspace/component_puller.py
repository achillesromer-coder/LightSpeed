"""
Component Puller - v5.1.2
Component discovery and integration from active Z-axis smart floors.

This module discovers, validates, and integrates components from all Z-floors
into project workspaces with automatic dependency resolution and configuration.

Author: LightSpeed Team
Date: April 8, 2026
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import importlib

from .workspace_types import (
    Z_FLOOR_COMPONENTS,
    WorkspaceType,
    get_component_contract_workspace_type_values,
    normalize_workspace_type_value,
)
from .workspace_creator import WorkspaceComponent, SphericalPosition
from .category_positions import get_category_default_position


ALL_WORKSPACE_TYPE_VALUES = {workspace_type.value for workspace_type in WorkspaceType}


# ==============================================================================
# Component Metadata
# ==============================================================================

class ComponentCapability(Enum):
    """Component capability types"""
    VISUALIZATION = "visualization"
    DATA_PROCESSING = "data_processing"
    AI_INTELLIGENCE = "ai_intelligence"
    SIMULATION = "simulation"
    DOCUMENTATION = "documentation"
    AUTOMATION = "automation"
    MONITORING = "monitoring"
    PLANNING = "planning"
    STORAGE = "storage"


@dataclass
class ComponentMetadata:
    """Complete metadata for a component"""
    component_id: str
    name: str
    z_floor: str
    category: str
    capabilities: List[ComponentCapability]
    description: str
    version: str = "1.0.0"

    # Dependencies
    requires_components: List[str] = field(default_factory=list)
    requires_z_floors: List[str] = field(default_factory=list)
    requires_python_packages: List[str] = field(default_factory=list)

    # Configuration
    config_schema: Dict[str, Any] = field(default_factory=dict)
    default_config: Dict[str, Any] = field(default_factory=dict)

    # Integration
    python_module: Optional[str] = None
    entry_point: Optional[str] = None
    ui_class: Optional[str] = None

    # Compatibility
    compatible_workspace_types: List[WorkspaceType] = field(default_factory=list)
    min_grid_size: Tuple[int, int] = (6, 6)

    # Status
    enabled: bool = True
    tested: bool = False

    def compatible_workspace_type_values(self) -> List[str]:
        """Return normalized compatibility values with contract-backed narrowing."""
        configured_values: List[str] = []
        seen: set[str] = set()

        for workspace_type in self.compatible_workspace_types:
            value = normalize_workspace_type_value(workspace_type)
            if value not in seen:
                seen.add(value)
                configured_values.append(value)

        contract_values = get_component_contract_workspace_type_values(self.component_id)
        if contract_values and (not configured_values or set(configured_values) == ALL_WORKSPACE_TYPE_VALUES):
            return contract_values

        return configured_values

    def supports_workspace_type(self, workspace_type: Any) -> bool:
        """Return whether the component supports the requested workspace type."""
        try:
            requested_value = normalize_workspace_type_value(workspace_type)
        except TypeError:
            return False
        return requested_value in self.compatible_workspace_type_values()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'component_id': self.component_id,
            'name': self.name,
            'z_floor': self.z_floor,
            'category': self.category,
            'capabilities': [c.value for c in self.capabilities],
            'description': self.description,
            'version': self.version,
            'requires_components': self.requires_components,
            'requires_z_floors': self.requires_z_floors,
            'requires_python_packages': self.requires_python_packages,
            'config_schema': self.config_schema,
            'default_config': self.default_config,
            'python_module': self.python_module,
            'entry_point': self.entry_point,
            'ui_class': self.ui_class,
            'compatible_workspace_types': self.compatible_workspace_type_values(),
            'min_grid_size': self.min_grid_size,
            'enabled': self.enabled,
            'tested': self.tested
        }


# ==============================================================================
# Component Registry
# ==============================================================================

class ComponentRegistry:
    """
    Central registry of available components across active Z-axis floors.

    Discovers, validates, and provides access to components from all Z-floors.
    """

    def __init__(self, z_axis_root: Optional[Path] = None):
        """
        Initialize component registry

        Args:
            z_axis_root: Root path to Z Axis directory
        """
        self.z_axis_root = z_axis_root or Path("Z Axis")
        self.components: Dict[str, ComponentMetadata] = {}
        self.z_floor_map: Dict[str, List[str]] = {}
        self.category_map: Dict[str, List[str]] = {}

        # Load component definitions
        self._initialize_component_metadata()

    def _initialize_component_metadata(self):
        """Initialize metadata for all known components"""
        # Component metadata definitions based on Z_FLOOR_COMPONENTS
        component_definitions = {
            # Z-4 Merovingian (System Health)
            'health_monitor': ComponentMetadata(
                component_id='health_monitor',
                name='System Health Monitor',
                z_floor='Z-4_Merovingian',
                category='system_health',
                capabilities=[ComponentCapability.MONITORING],
                description='Real-time system health monitoring with auto-healing',
                python_module='Z_Axis.Z-4_Merovingian.components.system_metrics',
                ui_class='SystemMetricsGUI',
                compatible_workspace_types=[WorkspaceType.ENGINEERING, WorkspaceType.SIMULATION],
                default_config={'refresh_rate': 5, 'alert_threshold': 90}
            ),
            'diagnostic_panel': ComponentMetadata(
                component_id='diagnostic_panel',
                name='System Diagnostics',
                z_floor='Z-4_Merovingian',
                category='system_health',
                capabilities=[ComponentCapability.MONITORING],
                description='Detailed system diagnostics and troubleshooting',
                python_module='Z_Axis.Z-4_Merovingian.components.merovingian_portal_glass',
                ui_class='MerovingianPortalGlass',
                compatible_workspace_types=[WorkspaceType.ENGINEERING]
            ),
            'performance_tracker': ComponentMetadata(
                component_id='performance_tracker',
                name='Performance Tracker',
                z_floor='Z-4_Merovingian',
                category='system_health',
                capabilities=[ComponentCapability.MONITORING],
                description='Profiler-backed performance tracking for runtime hotspots',
                python_module='Z_Axis.Z-4_Merovingian.components.performance_profiler',
                ui_class='PerformanceProfilerGUI',
                compatible_workspace_types=[WorkspaceType.SIMULATION, WorkspaceType.ENGINEERING]
            ),

            # Z-3 Smith (Automation)
            'job_scheduler': ComponentMetadata(
                component_id='job_scheduler',
                name='Job Scheduler',
                z_floor='Z-3_Smith',
                category='automation',
                capabilities=[ComponentCapability.AUTOMATION],
                description='Schedule and manage background jobs',
                python_module='Z_Axis.Z-3_Smith.components.workflow_scheduler',
                ui_class='WorkflowScheduler',
                compatible_workspace_types=[WorkspaceType.DATA_SCIENCE, WorkspaceType.ANALYSIS],
                default_config={'max_concurrent_jobs': 5}
            ),
            'workflow_designer': ComponentMetadata(
                component_id='workflow_designer',
                name='Workflow Designer',
                z_floor='Z-3_Smith',
                category='automation',
                capabilities=[ComponentCapability.AUTOMATION],
                description='Interactive workflow inspection and refinement surface',
                python_module='Z_Axis.Z-3_Smith.components.workflow_debugger',
                ui_class='WorkflowDebugger',
                compatible_workspace_types=[WorkspaceType.ANALYSIS, WorkspaceType.DATA_SCIENCE, WorkspaceType.COLLABORATION],
                requires_components=['job_scheduler']
            ),
            'task_queue_monitor': ComponentMetadata(
                component_id='task_queue_monitor',
                name='Task Queue Monitor',
                z_floor='Z-3_Smith',
                category='automation',
                capabilities=[ComponentCapability.AUTOMATION, ComponentCapability.MONITORING],
                description='Monitor inter-floor task queues and pending automation work',
                python_module='Z_Axis.Z-3_Smith.components.smith_task_queue',
                ui_class='SmithTaskQueue',
                compatible_workspace_types=[WorkspaceType.ANALYSIS, WorkspaceType.DATA_SCIENCE, WorkspaceType.COLLABORATION]
            ),

            # Z-2 Oracle (Knowledge Storage)
            'document_vault': ComponentMetadata(
                component_id='document_vault',
                name='Document Vault',
                z_floor='Z-2_Oracle',
                category='knowledge_storage',
                capabilities=[ComponentCapability.STORAGE, ComponentCapability.DOCUMENTATION],
                description='Document ingestion and archive access surface for Oracle knowledge stores',
                python_module='Z_Axis.Z-2_Oracle.components.oracle_ui_panel',
                ui_class='OracleUIPanel',
                compatible_workspace_types=list(WorkspaceType),  # All workspace types
                default_config={'encryption_enabled': True}
            ),
            'knowledge_graph': ComponentMetadata(
                component_id='knowledge_graph',
                name='Knowledge Graph',
                z_floor='Z-1_Morpheus',
                category='knowledge_discovery',
                capabilities=[ComponentCapability.AI_INTELLIGENCE],
                description='Interactive knowledge graph visualization and exploration',
                python_module='Z_Axis.Z-1_Morpheus.database.models.knowledge_graph',
                entry_point='KnowledgeGraphNode',
                compatible_workspace_types=[WorkspaceType.RESEARCH, WorkspaceType.DOCUMENTATION, WorkspaceType.ANALYSIS, WorkspaceType.COLLABORATION],
                requires_python_packages=['networkx', 'plotly']
            ),
            'archive_browser': ComponentMetadata(
                component_id='archive_browser',
                name='Archive Browser',
                z_floor='Z-1_Morpheus',
                category='knowledge_discovery',
                capabilities=[ComponentCapability.STORAGE, ComponentCapability.DOCUMENTATION],
                description='Browse archived conversations and imported research artifacts',
                python_module='Z_Axis.Z-1_Morpheus.components.chat_archive_browser',
                ui_class='ChatArchiveBrowser',
                compatible_workspace_types=[WorkspaceType.DOCUMENTATION]
            ),
            'documentation_browser': ComponentMetadata(
                component_id='documentation_browser',
                name='Documentation Browser',
                z_floor='Z-1_Morpheus',
                category='knowledge_discovery',
                capabilities=[ComponentCapability.DOCUMENTATION],
                description='Markdown-first documentation preview and editing surface',
                python_module='Z_Axis.Z-1_Morpheus.components.rich_text_editor',
                ui_class='MarkdownPreview',
                compatible_workspace_types=[WorkspaceType.DOCUMENTATION]
            ),

            # Z0 TheConstruct (Physics & Simulation)
            'physics_simulator': ComponentMetadata(
                component_id='physics_simulator',
                name='Physics Simulator',
                z_floor='Z0_TheConstruct',
                category='simulation_physics',
                capabilities=[ComponentCapability.SIMULATION],
                description='General physics simulation engine',
                python_module='Z_Axis.Z0_TheConstruct.components.physics_sim',
                compatible_workspace_types=[WorkspaceType.SIMULATION, WorkspaceType.ENGINEERING, WorkspaceType.MISSION_PLANNING],
                requires_python_packages=['numpy', 'scipy']
            ),
            'gmat_launcher': ComponentMetadata(
                component_id='gmat_launcher',
                name='GMAT Mission Analysis',
                z_floor='Z0_TheConstruct',
                category='simulation_physics',
                capabilities=[ComponentCapability.SIMULATION],
                description='NASA GMAT orbital mechanics and mission planning',
                python_module='Z_Axis.Z0_TheConstruct.tools.GMAT.GMAT_R2025a.api.load_gmat',
                compatible_workspace_types=[WorkspaceType.MISSION_PLANNING, WorkspaceType.SIMULATION, WorkspaceType.ENGINEERING],
                default_config={'windowed_mode': True}
            ),
            'raphael_engine': ComponentMetadata(
                component_id='raphael_engine',
                name='Raphael Physics Engine',
                z_floor='Z0_TheConstruct',
                category='simulation_physics',
                capabilities=[ComponentCapability.SIMULATION],
                description='Advanced physics engine with Theory of Everything framework',
                python_module='core.physics.raphael.Raphael_Runner',
                compatible_workspace_types=[WorkspaceType.RESEARCH, WorkspaceType.SIMULATION, WorkspaceType.ENGINEERING],
                requires_python_packages=['numpy', 'matplotlib']
            ),
            '3d_visualization': ComponentMetadata(
                component_id='3d_visualization',
                name='3D Visualization',
                z_floor='Z0_TheConstruct',
                category='simulation_physics',
                capabilities=[ComponentCapability.VISUALIZATION],
                description='3D scene rendering with Z-layer support',
                python_module='Z_Axis.Z0_TheConstruct.components.visualization_3d',
                compatible_workspace_types=[WorkspaceType.ENGINEERING, WorkspaceType.SIMULATION, WorkspaceType.MISSION_PLANNING],
                requires_python_packages=['numpy']
            ),

            # Z+1 Architect (Planning & Goals)
            'okr_tracker': ComponentMetadata(
                component_id='okr_tracker',
                name='OKR Tracker',
                z_floor='Z+1_Architect',
                category='planning_goals',
                capabilities=[ComponentCapability.PLANNING],
                description='Objectives and Key Results tracking',
                python_module='Z_Axis.Z+1_Architect.components.progress_widget',
                ui_class='DBTaskBoard',
                compatible_workspace_types=[WorkspaceType.COLLABORATION, WorkspaceType.MISSION_PLANNING]
            ),
            'mission_planner': ComponentMetadata(
                component_id='mission_planner',
                name='Mission Planner',
                z_floor='Z+1_Architect',
                category='planning_goals',
                capabilities=[ComponentCapability.PLANNING],
                description='Mission planning and timeline management',
                python_module='Z_Axis.Z+1_Architect.components.mission_planner',
                compatible_workspace_types=[WorkspaceType.MISSION_PLANNING, WorkspaceType.ENGINEERING, WorkspaceType.SIMULATION]
            ),
            'timeline_view': ComponentMetadata(
                component_id='timeline_view',
                name='Timeline View',
                z_floor='Z+1_Architect',
                category='planning_goals',
                capabilities=[ComponentCapability.PLANNING],
                description='Timeline-oriented progress visualization for plans and simulations',
                python_module='Z_Axis.Z+1_Architect.components.progress_widget',
                ui_class='TimelineProgress',
                compatible_workspace_types=[WorkspaceType.SIMULATION, WorkspaceType.MISSION_PLANNING]
            ),
            'milestone_tracker': ComponentMetadata(
                component_id='milestone_tracker',
                name='Milestone Tracker',
                z_floor='Z+1_Architect',
                category='planning_goals',
                capabilities=[ComponentCapability.PLANNING],
                description='Checklist-style milestone tracking for mission and collaboration work',
                python_module='Z_Axis.Z+1_Architect.components.progress_widget',
                ui_class='TaskChecklist',
                compatible_workspace_types=[WorkspaceType.COLLABORATION, WorkspaceType.MISSION_PLANNING]
            ),

            # Z+2 Neo (AI & Intelligence)
            'cognigrex_ai': ComponentMetadata(
                component_id='cognigrex_ai',
                name='Cognigrex AI Research Assistant',
                z_floor='Z+2_Neo',
                category='ai_intelligence',
                capabilities=[ComponentCapability.AI_INTELLIGENCE],
                description='AI-powered research assistance with Ollama integration',
                python_module='Z_Axis.Z+2_Neo.components.cognigrex_foundation',
                entry_point='CognigrexFoundation',
                compatible_workspace_types=[WorkspaceType.RESEARCH, WorkspaceType.DATA_SCIENCE, WorkspaceType.ANALYSIS],
                requires_python_packages=['ollama'],
                default_config={'default_model': 'llama3.2', 'temperature': 0.7}
            ),
            'model_trainer': ComponentMetadata(
                component_id='model_trainer',
                name='Model Trainer',
                z_floor='Z+2_Neo',
                category='ai_intelligence',
                capabilities=[ComponentCapability.DATA_PROCESSING, ComponentCapability.AI_INTELLIGENCE],
                description='Training workflow surface for fine-tuning and evaluation runs',
                python_module='Z_Axis.Z+2_Neo.components.ai_training',
                ui_class='AITrainingGUI',
                compatible_workspace_types=[WorkspaceType.DATA_SCIENCE, WorkspaceType.ANALYSIS]
            ),
            'data_analyzer': ComponentMetadata(
                component_id='data_analyzer',
                name='Data Analyzer',
                z_floor='Z+2_Neo',
                category='ai_intelligence',
                capabilities=[ComponentCapability.DATA_PROCESSING, ComponentCapability.AI_INTELLIGENCE],
                description='AI-powered data analysis and insights',
                python_module='Z_Axis.Z+2_Neo.components.data_analyzer',
                compatible_workspace_types=[WorkspaceType.DATA_SCIENCE, WorkspaceType.ANALYSIS, WorkspaceType.RESEARCH],
                requires_python_packages=['pandas', 'numpy', 'scikit-learn']
            ),

            # Z+3 Trinity (UI & Visualization)
            'widget_gallery': ComponentMetadata(
                component_id='widget_gallery',
                name='Widget Gallery',
                z_floor='Z+3_Trinity',
                category='ui_visualization',
                capabilities=[ComponentCapability.VISUALIZATION],
                description='Browse and add widgets to workspace',
                python_module='Z_Axis.Z+3_Trinity.ui.widget_registry',
                compatible_workspace_types=list(WorkspaceType)
            ),
            'theme_manager': ComponentMetadata(
                component_id='theme_manager',
                name='Theme Manager',
                z_floor='Z+3_Trinity',
                category='ui_visualization',
                capabilities=[ComponentCapability.VISUALIZATION],
                description='Theme customization and preview surface for Trinity-managed workspaces',
                python_module='Z_Axis.Z+3_Trinity.components.theme_switcher',
                ui_class='ThemeDesigner',
                compatible_workspace_types=[WorkspaceType.DOCUMENTATION, WorkspaceType.ANALYSIS, WorkspaceType.DATA_SCIENCE]
            ),
            'chart_renderer': ComponentMetadata(
                component_id='chart_renderer',
                name='Chart Renderer',
                z_floor='Z+3_Trinity',
                category='ui_visualization',
                capabilities=[ComponentCapability.VISUALIZATION],
                description='Interactive chart rendering (line, bar, scatter, etc.)',
                python_module='Z_Axis.Z+3_Trinity.components.analytics_dashboard',
                ui_class='MetricChart',
                compatible_workspace_types=[WorkspaceType.ANALYSIS, WorkspaceType.DATA_SCIENCE, WorkspaceType.RESEARCH],
                requires_python_packages=['matplotlib', 'plotly']
            ),
            'tabby_code_assist': ComponentMetadata(
                component_id='tabby_code_assist',
                name='Tabby Code Assistant',
                z_floor='Z+3_Trinity',
                category='ui_visualization',
                capabilities=[ComponentCapability.AI_INTELLIGENCE],
                description='AI code completion with Tabby',
                python_module='Z_Axis.Z+3_Trinity.tools.Tabby.integration',
                compatible_workspace_types=[WorkspaceType.DATA_SCIENCE, WorkspaceType.ENGINEERING],
                default_config={'self_hosted': True}
            ),
        }

        # Register all components
        for comp_id, metadata in component_definitions.items():
            self.register_component(metadata)

    def register_component(self, metadata: ComponentMetadata):
        """Register a component in the registry"""
        self.components[metadata.component_id] = metadata

        # Update floor mapping
        if metadata.z_floor not in self.z_floor_map:
            self.z_floor_map[metadata.z_floor] = []
        self.z_floor_map[metadata.z_floor].append(metadata.component_id)

        # Update category mapping
        if metadata.category not in self.category_map:
            self.category_map[metadata.category] = []
        self.category_map[metadata.category].append(metadata.component_id)

    def get_component(self, component_id: str) -> Optional[ComponentMetadata]:
        """Get component metadata by ID"""
        return self.components.get(component_id)

    def list_components(
        self,
        z_floor: Optional[str] = None,
        category: Optional[str] = None,
        capability: Optional[ComponentCapability] = None,
        workspace_type: Optional[Any] = None
    ) -> List[ComponentMetadata]:
        """List components with optional filtering"""
        components = list(self.components.values())

        if z_floor:
            components = [c for c in components if c.z_floor == z_floor]

        if category:
            components = [c for c in components if c.category == category]

        if capability:
            components = [c for c in components if capability in c.capabilities]

        if workspace_type:
            components = [c for c in components if c.supports_workspace_type(workspace_type)]

        return components

    def get_components_by_floor(self, z_floor: str) -> List[ComponentMetadata]:
        """Get all components from a Z-floor"""
        component_ids = self.z_floor_map.get(z_floor, [])
        return [self.components[cid] for cid in component_ids]

    def validate_dependencies(self, component_id: str) -> Tuple[bool, List[str]]:
        """
        Validate component dependencies

        Returns:
            (dependencies_met, missing_components)
        """
        metadata = self.get_component(component_id)
        if not metadata:
            return False, [component_id]

        missing = []

        # Check component dependencies
        for required_comp in metadata.requires_components:
            if required_comp not in self.components:
                missing.append(required_comp)

        return len(missing) == 0, missing


# ==============================================================================
# Component Puller
# ==============================================================================

class ComponentPuller:
    """
    Component pulling from the active Z-axis floor registry.

    Discovers available components, resolves dependencies, and integrates
    them into project workspaces.
    """

    def __init__(self, registry: Optional[ComponentRegistry] = None):
        """
        Initialize component puller

        Args:
            registry: Component registry (creates new if not provided)
        """
        self.registry = registry or ComponentRegistry()

    def discover_compatible_components(
        self,
        workspace_type: Any,
        required_z_floors: Optional[List[str]] = None
    ) -> List[ComponentMetadata]:
        """
        Discover components compatible with workspace type

        Args:
            workspace_type: Type of workspace
            required_z_floors: Optional list of Z-floors to restrict search

        Returns:
            List of compatible component metadata
        """
        components = self.registry.list_components(workspace_type=workspace_type)

        if required_z_floors:
            components = [c for c in components if c.z_floor in required_z_floors]

        return sorted(components, key=lambda c: (c.z_floor, c.component_id))

    def pull_component(
        self,
        component_id: str,
        position: Optional[SphericalPosition] = None,
        config: Optional[Dict[str, Any]] = None,
        validate_dependencies: bool = True
    ) -> Tuple[bool, Optional[WorkspaceComponent], List[str]]:
        """
        Pull a component for integration into workspace

        Args:
            component_id: Component to pull
            position: Optional spherical position (auto-assigned if None)
            config: Optional component configuration
            validate_dependencies: Whether to validate dependencies

        Returns:
            (success, workspace_component, missing_dependencies)
        """
        # Get component metadata
        metadata = self.registry.get_component(component_id)
        if not metadata:
            return False, None, [f"Component '{component_id}' not found"]

        # Check if enabled
        if not metadata.enabled:
            return False, None, [f"Component '{component_id}' is disabled"]

        # Validate dependencies
        if validate_dependencies:
            deps_met, missing = self.registry.validate_dependencies(component_id)
            if not deps_met:
                return False, None, missing

        # Auto-assign position if not provided
        if position is None:
            position = self._auto_assign_position(metadata)

        # Merge config with defaults
        final_config = {**metadata.default_config, **(config or {})}

        # Create workspace component
        workspace_component = WorkspaceComponent(
            component_id=metadata.component_id,
            component_name=metadata.name,
            z_floor=metadata.z_floor,
            category=metadata.category,
            position=position,
            config=final_config
        )

        return True, workspace_component, []

    def _auto_assign_position(self, metadata: ComponentMetadata) -> SphericalPosition:
        """Auto-assign position based on component category"""
        return get_category_default_position(metadata.category)

    def pull_multiple_components(
        self,
        component_ids: List[str],
        auto_resolve_dependencies: bool = True
    ) -> Dict[str, Tuple[bool, Optional[WorkspaceComponent], List[str]]]:
        """
        Pull multiple components at once

        Args:
            component_ids: List of component IDs to pull
            auto_resolve_dependencies: Automatically include dependencies

        Returns:
            Dictionary mapping component_id to (success, component, missing_deps)
        """
        results = {}
        components_to_pull = set(component_ids)

        # Resolve dependencies if requested
        if auto_resolve_dependencies:
            for comp_id in list(components_to_pull):
                metadata = self.registry.get_component(comp_id)
                if metadata:
                    components_to_pull.update(metadata.requires_components)

        # Pull each component
        for comp_id in components_to_pull:
            results[comp_id] = self.pull_component(comp_id, validate_dependencies=True)

        return results

    def check_python_dependencies(self, component_id: str) -> Tuple[bool, List[str]]:
        """
        Check if Python package dependencies are installed

        Returns:
            (all_installed, missing_packages)
        """
        metadata = self.registry.get_component(component_id)
        if not metadata:
            return False, [f"Component '{component_id}' not found"]

        missing_packages = []

        for package in metadata.requires_python_packages:
            try:
                importlib.import_module(package)
            except ImportError:
                missing_packages.append(package)

        return len(missing_packages) == 0, missing_packages


# ==============================================================================
# Convenience Functions
# ==============================================================================

def create_component_puller() -> ComponentPuller:
    """Create component puller with default registry"""
    return ComponentPuller()


def discover_components_for_workspace(workspace_type: WorkspaceType) -> List[ComponentMetadata]:
    """Discover compatible components for workspace type"""
    puller = create_component_puller()
    return puller.discover_compatible_components(workspace_type)
