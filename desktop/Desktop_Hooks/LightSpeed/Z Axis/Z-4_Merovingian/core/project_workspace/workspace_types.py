"""
Workspace Type Definitions - v5.1.2
Workspace type contracts for Construct scenario and project shells.

Author: LightSpeed Team
Date: April 8, 2026
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


class WorkspaceType(Enum):
    """Project workspace types"""
    RESEARCH = "research"
    ENGINEERING = "engineering"
    ANALYSIS = "analysis"
    SIMULATION = "simulation"
    DOCUMENTATION = "documentation"
    COLLABORATION = "collaboration"
    MISSION_PLANNING = "mission_planning"
    DATA_SCIENCE = "data_science"


class WorkspaceStatus(Enum):
    """Workspace lifecycle status"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    TEMPLATE = "template"
    SUSPENDED = "suspended"


# ==============================================================================
# Component Categories for Workspaces
# ==============================================================================

# Components available from each Z-floor
Z_FLOOR_COMPONENTS = {
    'Z-4_Merovingian': {
        'category': 'system_health',
        'components': [
            'health_monitor',
            'diagnostic_panel',
            'performance_tracker',
        ]
    },
    'Z-3_Smith': {
        'category': 'automation',
        'components': [
            'job_scheduler',
            'workflow_designer',
            'task_queue_monitor'
        ]
    },
    'Z-2_Oracle': {
        'category': 'knowledge_storage',
        'components': [
            'document_vault',
        ]
    },
    'Z-1_Morpheus': {
        'category': 'knowledge_discovery',
        'components': [
            'knowledge_graph',
            'archive_browser',
            'documentation_browser',
        ]
    },
    'Z0_TheConstruct': {
        'category': 'simulation_physics',
        'components': [
            'physics_simulator',
            'gmat_launcher',
            'raphael_engine',
            '3d_visualization',
        ]
    },
    'Z+1_Architect': {
        'category': 'planning_goals',
        'components': [
            'okr_tracker',
            'mission_planner',
            'timeline_view',
            'milestone_tracker',
        ]
    },
    'Z+2_Neo': {
        'category': 'ai_intelligence',
        'components': [
            'cognigrex_ai',
            'model_trainer',
            'data_analyzer',
        ]
    },
    'Z+3_Trinity': {
        'category': 'ui_visualization',
        'components': [
            'widget_gallery',
            'theme_manager',
            'chart_renderer',
            'tabby_code_assist'
        ]
    }
}


# ==============================================================================
# Workspace Type Configurations
# ==============================================================================

@dataclass
class WorkspaceTypeConfig:
    """Configuration for a workspace type"""
    workspace_type: WorkspaceType
    display_name: str
    description: str
    recommended_components: List[str]  # Component IDs
    required_z_floors: List[str]       # Z-floors that must be accessible
    default_layout_grid: tuple[int, int]  # (width, height) for spherical grid
    standards_required: List[str]      # Which standards apply
    file_types_supported: List[str]    # Primary file types for this workspace
    default_tools: List[str]           # External tools to integrate
    color_scheme: str                  # Primary color for workspace
    icon: str                          # Icon identifier


# Workspace type configurations
WORKSPACE_CONFIGS: Dict[WorkspaceType, WorkspaceTypeConfig] = {
    WorkspaceType.RESEARCH: WorkspaceTypeConfig(
        workspace_type=WorkspaceType.RESEARCH,
        display_name="Research Workspace",
        description="Academic and scientific research with AI assistance, data analysis, and publication tools",
        recommended_components=[
            'cognigrex_ai',
            'data_analyzer',
            'knowledge_graph',
            'document_vault',
            'chart_renderer'
        ],
        required_z_floors=['Z+2_Neo', 'Z-1_Morpheus', 'Z-2_Oracle', 'Z+3_Trinity'],
        default_layout_grid=(8, 6),
        standards_required=['IEEE', 'Dublin Core', 'BibTeX', 'ORCID', 'DOI'],
        file_types_supported=['.pdf', '.tex', '.bib', '.md', '.ipynb', '.csv', '.json'],
        default_tools=['pandoc', 'pdfjs', 'monaco'],
        color_scheme='#0088FE',
        icon='research'
    ),

    WorkspaceType.ENGINEERING: WorkspaceTypeConfig(
        workspace_type=WorkspaceType.ENGINEERING,
        display_name="Engineering Workspace",
        description="CAD, simulations, technical documentation with aerospace standards compliance",
        recommended_components=[
            'physics_simulator',
            '3d_visualization',
            'gmat_launcher',
            'raphael_engine',
            'mission_planner',
            'document_vault',
        ],
        required_z_floors=['Z0_TheConstruct', 'Z+1_Architect', 'Z-2_Oracle'],
        default_layout_grid=(10, 6),
        standards_required=['STEP AP242', 'COLLADA', 'NASA CDF', 'ITAR', 'SPICE'],
        file_types_supported=['.step', '.stl', '.obj', '.dxf', '.dwg', '.py', '.md'],
        default_tools=['threejs', 'monaco', 'gmat', 'raphael'],
        color_scheme='#00C49F',
        icon='engineering'
    ),

    WorkspaceType.ANALYSIS: WorkspaceTypeConfig(
        workspace_type=WorkspaceType.ANALYSIS,
        display_name="Analysis Workspace",
        description="Data analysis, statistics, machine learning with comprehensive tooling",
        recommended_components=[
            'data_analyzer',
            'cognigrex_ai',
            'model_trainer',
            'chart_renderer',
            'knowledge_graph',
            'task_queue_monitor'
        ],
        required_z_floors=['Z+2_Neo', 'Z-3_Smith', 'Z-1_Morpheus', 'Z+3_Trinity'],
        default_layout_grid=(8, 8),
        standards_required=['HDF5', 'NetCDF', 'FITS', 'JSON-LD'],
        file_types_supported=['.csv', '.json', '.hdf5', '.nc', '.fits', '.ipynb', '.py'],
        default_tools=['monaco', 'pdfjs', 'pandoc'],
        color_scheme='#FF8042',
        icon='analysis'
    ),

    WorkspaceType.SIMULATION: WorkspaceTypeConfig(
        workspace_type=WorkspaceType.SIMULATION,
        display_name="Simulation Workspace",
        description="Physics simulations, orbital mechanics, mission scenarios",
        recommended_components=[
            'physics_simulator',
            'gmat_launcher',
            'raphael_engine',
            '3d_visualization',
            'mission_planner',
            'timeline_view',
            'performance_tracker'
        ],
        required_z_floors=['Z0_TheConstruct', 'Z+1_Architect', 'Z-4_Merovingian'],
        default_layout_grid=(12, 6),
        standards_required=['STEP AP242', 'NASA CDF', 'SPICE', 'CCSDS'],
        file_types_supported=['.script', '.py', '.json', '.csv', '.stl', '.obj'],
        default_tools=['gmat', 'raphael', 'threejs', 'monaco'],
        color_scheme='#8884d8',
        icon='simulation'
    ),

    WorkspaceType.DOCUMENTATION: WorkspaceTypeConfig(
        workspace_type=WorkspaceType.DOCUMENTATION,
        display_name="Documentation Workspace",
        description="Technical writing, API docs, user guides with auto-indexing and bibliography",
        recommended_components=[
            'document_vault',
            'knowledge_graph',
            'archive_browser',
            'documentation_browser',
        ],
        required_z_floors=['Z-2_Oracle', 'Z-1_Morpheus', 'Z+3_Trinity'],
        default_layout_grid=(6, 6),
        standards_required=['Dublin Core', 'BibTeX', 'Markdown', 'reStructuredText'],
        file_types_supported=['.md', '.rst', '.tex', '.pdf', '.html', '.docx'],
        default_tools=['pandoc', 'pdfjs', 'monaco'],
        color_scheme='#82ca9d',
        icon='documentation'
    ),

    WorkspaceType.COLLABORATION: WorkspaceTypeConfig(
        workspace_type=WorkspaceType.COLLABORATION,
        display_name="Collaboration Workspace",
        description="Team collaboration with shared resources, task tracking, and communication",
        recommended_components=[
            'task_queue_monitor',
            'workflow_designer',
            'okr_tracker',
            'milestone_tracker',
            'document_vault',
        ],
        required_z_floors=['Z-3_Smith', 'Z+1_Architect', 'Z-2_Oracle'],
        default_layout_grid=(8, 6),
        standards_required=['Dublin Core', 'JSON-LD', 'NIST SP 800-53'],
        file_types_supported=['.md', '.json', '.csv', '.pdf', '.py', '.js'],
        default_tools=['monaco', 'pdfjs', 'pandoc'],
        color_scheme='#ffc658',
        icon='collaboration'
    ),

    WorkspaceType.MISSION_PLANNING: WorkspaceTypeConfig(
        workspace_type=WorkspaceType.MISSION_PLANNING,
        display_name="Mission Planning Workspace",
        description="Space mission planning with GMAT, trajectory analysis, and timeline management",
        recommended_components=[
            'gmat_launcher',
            'mission_planner',
            'timeline_view',
            'milestone_tracker',
            'physics_simulator',
            '3d_visualization',
        ],
        required_z_floors=['Z0_TheConstruct', 'Z+1_Architect'],
        default_layout_grid=(10, 8),
        standards_required=['NASA CDF', 'SPICE', 'CCSDS', 'STEP AP242'],
        file_types_supported=['.script', '.json', '.csv', '.py', '.md'],
        default_tools=['gmat', 'threejs', 'monaco', 'pdfjs'],
        color_scheme='#ff7300',
        icon='mission'
    ),

    WorkspaceType.DATA_SCIENCE: WorkspaceTypeConfig(
        workspace_type=WorkspaceType.DATA_SCIENCE,
        display_name="Data Science Workspace",
        description="ML/AI development, data processing, model training with Cognigrex integration",
        recommended_components=[
            'cognigrex_ai',
            'model_trainer',
            'data_analyzer',
            'chart_renderer',
            'task_queue_monitor'
        ],
        required_z_floors=['Z+2_Neo', 'Z-3_Smith', 'Z+3_Trinity'],
        default_layout_grid=(8, 8),
        standards_required=['HDF5', 'NetCDF', 'JSON-LD', 'Dublin Core'],
        file_types_supported=['.ipynb', '.py', '.csv', '.json', '.hdf5', '.parquet'],
        default_tools=['monaco', 'pdfjs'],
        color_scheme='#a4de6c',
        icon='datascience'
    ),
}


# ==============================================================================
# Workspace Template Definitions
# ==============================================================================

@dataclass
class WorkspaceTemplate:
    """Pre-configured workspace template"""
    id: str
    name: str
    workspace_type: WorkspaceType
    description: str
    pre_configured_components: List[Dict[str, Any]]  # component_id, position, config
    sample_files: List[str]  # Paths to sample files to include
    tutorial_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


# Pre-configured workspace templates
WORKSPACE_TEMPLATES: Dict[str, WorkspaceTemplate] = {
    'lunar_mission': WorkspaceTemplate(
        id='lunar_mission',
        name='Lunar Mission Template',
        workspace_type=WorkspaceType.MISSION_PLANNING,
        description='Pre-configured for lunar orbit insertion and landing trajectory planning',
        pre_configured_components=[
            {'component_id': 'gmat_launcher', 'position': (0, 0, 0.8), 'config': {'default_script': 'lunar_transfer.script'}},
            {'component_id': '3d_visualization', 'position': (90, 0, 0.8), 'config': {'default_view': 'orbital'}},
            {'component_id': 'mission_planner', 'position': (-90, 0, 0.7), 'config': {}},
            {'component_id': 'timeline_view', 'position': (0, -30, 0.9), 'config': {}}
        ],
        sample_files=[
            'templates/missions/lunar/lunar_transfer.script',
            'templates/missions/lunar/mission_overview.md'
        ],
        tutorial_path='tutorials/lunar_mission_planning.md'
    ),

    'research_paper': WorkspaceTemplate(
        id='research_paper',
        name='Research Paper Template',
        workspace_type=WorkspaceType.RESEARCH,
        description='Academic research paper writing with auto-bibliography and data analysis',
        pre_configured_components=[
            {'component_id': 'document_vault', 'position': (0, 0, 0.8), 'config': {}},
            {'component_id': 'cognigrex_ai', 'position': (90, 0, 0.8), 'config': {'mode': 'literature_review'}},
            {'component_id': 'knowledge_graph', 'position': (-90, 0, 0.7), 'config': {}},
            {'component_id': 'chart_renderer', 'position': (0, 30, 0.7), 'config': {}}
        ],
        sample_files=[
            'templates/research/paper_template.md',
            'templates/research/bibliography.bib'
        ],
        tutorial_path='tutorials/academic_writing.md'
    ),

    'cad_engineering': WorkspaceTemplate(
        id='cad_engineering',
        name='CAD Engineering Template',
        workspace_type=WorkspaceType.ENGINEERING,
        description='CAD design and engineering analysis with STEP AP242 compliance',
        pre_configured_components=[
            {'component_id': '3d_visualization', 'position': (0, 0, 0.8), 'config': {'render_mode': 'solid'}},
            {'component_id': 'physics_simulator', 'position': (90, 0, 0.8), 'config': {}},
            {'component_id': 'document_vault', 'position': (-90, 0, 0.7), 'config': {}},
            {'component_id': 'mission_planner', 'position': (180, 0, 0.6), 'config': {}}
        ],
        sample_files=[
            'templates/engineering/sample.step',
            'templates/engineering/design_spec.md'
        ],
        tutorial_path='tutorials/cad_workflow.md'
    ),

    'data_analysis': WorkspaceTemplate(
        id='data_analysis',
        name='Data Analysis Template',
        workspace_type=WorkspaceType.DATA_SCIENCE,
        description='Data science workflow with Jupyter, pandas, and ML model training',
        pre_configured_components=[
            {'component_id': 'data_analyzer', 'position': (0, 0, 0.8), 'config': {}},
            {'component_id': 'model_trainer', 'position': (90, 0, 0.8), 'config': {}},
            {'component_id': 'chart_renderer', 'position': (-90, 0, 0.7), 'config': {}},
            {'component_id': 'cognigrex_ai', 'position': (0, 30, 0.7), 'config': {'mode': 'data_science'}}
        ],
        sample_files=[
            'templates/data_science/analysis_template.ipynb',
            'templates/data_science/sample_data.csv'
        ],
        tutorial_path='tutorials/data_science_workflow.md'
    ),
}


def get_workspace_config(workspace_type: WorkspaceType) -> WorkspaceTypeConfig:
    """Get configuration for a workspace type"""
    return WORKSPACE_CONFIGS[workspace_type]


def get_template(template_id: str) -> Optional[WorkspaceTemplate]:
    """Get workspace template by ID"""
    return WORKSPACE_TEMPLATES.get(template_id)


def list_templates_by_type(workspace_type: WorkspaceType) -> List[WorkspaceTemplate]:
    """List all templates for a given workspace type"""
    return [t for t in WORKSPACE_TEMPLATES.values() if t.workspace_type == workspace_type]


def normalize_workspace_type_value(workspace_type: Any) -> str:
    """Normalize a workspace-type-like object to its contract value."""
    value = getattr(workspace_type, "value", workspace_type)
    if not isinstance(value, str):
        raise TypeError(f"Unsupported workspace type: {workspace_type!r}")
    return value


def get_component_contract_workspace_type_values(component_id: str) -> List[str]:
    """
    Return workspace-type values that actively reference a component.

    Recommended components and template-preconfigured components together define
    the current contract-backed workspace surface for the component.
    """
    values: List[str] = []
    seen: set[str] = set()

    def _remember(workspace_type: WorkspaceType) -> None:
        value = workspace_type.value
        if value not in seen:
            seen.add(value)
            values.append(value)

    for config in WORKSPACE_CONFIGS.values():
        if component_id in config.recommended_components:
            _remember(config.workspace_type)

    for template in WORKSPACE_TEMPLATES.values():
        if any(item.get("component_id") == component_id for item in template.pre_configured_components):
            _remember(template.workspace_type)

    return values
