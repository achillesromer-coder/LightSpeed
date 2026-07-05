"""
LightSpeed V0.9.11 - Spatial UI Components Package
Complete 3D spatial interface for LightSpeed platform

Components (V0.9.5 - Original):
- SpatialNavigator: 3D camera movement and Bento grid rendering
- DollhouseMinimap: Breadcrumb navigator with 3D floor visualization
- PortalTransition: Dissolve effects for floor transitions

Components (V0.9.11 - Enhanced):
- EnhancedBentoGrid: 1.5m curved surface with glass morphism
- AddNewWizard: Ollama-powered tile creation
- EnvironmentRenderer: 3D backgrounds from images/videos
- FlowchartVisualizer: Y-axis project structure
- SpatialUIManager: Unified integration

Author: LightSpeed Team / ACHILLES
Version: 0.9.11
Date: January 4, 2026
"""

# Original V0.9.5 components
from .spatial_navigator import (
    SpatialNavigator,
    SpatialPosition,
    BentoCell,
    ZFloorLevel
)

from .dollhouse_minimap import DollhouseMinimap

from .portal_transition import (
    PortalTransition,
    TransitionEffect,
    DissolveAnimation
)

# V0.9.11 Enhanced components
from .enhanced_bento_grid import (
    EnhancedBentoGrid,
    BentoTile,
    TileType
)

from .add_new_wizard import (
    AddNewWizard,
    OllamaClient,
    TileTemplate,
    WizardStep
)

from .environment_renderer import (
    EnvironmentRenderer,
    FakeLidarDepthEstimator,
    DepthPoint,
    EnvironmentLayer
)

from .flowchart_visualizer import (
    FlowchartVisualizer,
    FlowchartNode,
    FlowchartLayout
)

from .spatial_ui_integration import (
    SpatialUIManager,
    launch_spatial_ui
)

__version__ = "0.9.11"

__all__ = [
    # Original V0.9.5
    'SpatialNavigator',
    'SpatialPosition',
    'BentoCell',
    'ZFloorLevel',
    'DollhouseMinimap',
    'PortalTransition',
    'TransitionEffect',
    'DissolveAnimation',

    # V0.9.11 Enhanced
    'EnhancedBentoGrid',
    'BentoTile',
    'TileType',
    'AddNewWizard',
    'OllamaClient',
    'TileTemplate',
    'WizardStep',
    'EnvironmentRenderer',
    'FakeLidarDepthEstimator',
    'DepthPoint',
    'EnvironmentLayer',
    'FlowchartVisualizer',
    'FlowchartNode',
    'FlowchartLayout',
    'SpatialUIManager',
    'launch_spatial_ui',
]
