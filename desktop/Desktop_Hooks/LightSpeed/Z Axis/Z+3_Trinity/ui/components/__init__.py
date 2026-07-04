"""
LightSpeed V0.9.5 - UI Components Package
Auto-registration of all components

Accessible from any Z-floor or project:
    from core.ui.components import LayeredCard, ProgressBar
    from core.ui.components.registry import ComponentRegistry

Author: LightSpeed Team
Version: 0.9.5
Date: January 3, 2026
"""

# Import all components
from .layered_card import LayeredCard, LayeredPane, GlassPanel
from .loading import ProgressBar, LoadingSpinner, LoadingOverlay, BackgroundTaskMonitor
from .charts import ChartCard, StatCard, MiniChart, DataTable
from .simulation_launcher import SimulationLauncher, SimulationInfo
from .registry import ComponentRegistry, ComponentInfo, get_component

# Auto-register all components
def _register_all_components():
    """Auto-register all components in the registry"""

    # Display components
    ComponentRegistry.register(
        'LayeredCard', LayeredCard, 'display', '1.1.0',
        'Multi-layer card with glass morphism, shadows, and elevation'
    )
    ComponentRegistry.register(
        'LayeredPane', LayeredPane, 'display', '1.1.0',
        'Container for organizing multiple layered cards'
    )
    ComponentRegistry.register(
        'GlassPanel', GlassPanel, 'display', '1.1.0',
        'Glass morphism panel with semi-transparent background'
    )
    ComponentRegistry.register(
        'StatCard', StatCard, 'display', '1.1.0',
        'Single statistic display with icon and trend'
    )

    # Visualization components
    ComponentRegistry.register(
        'ProgressBar', ProgressBar, 'visualization', '1.1.0',
        'Modern progress bar with determinate/indeterminate modes'
    )
    ComponentRegistry.register(
        'LoadingSpinner', LoadingSpinner, 'visualization', '1.1.0',
        'Animated loading spinner with message'
    )
    ComponentRegistry.register(
        'LoadingOverlay', LoadingOverlay, 'visualization', '1.1.0',
        'Full-window loading screen with progress tracking'
    )
    ComponentRegistry.register(
        'ChartCard', ChartCard, 'visualization', '1.1.0',
        'Layered card with embedded bar/line/pie chart'
    )
    ComponentRegistry.register(
        'MiniChart', MiniChart, 'visualization', '1.1.0',
        'Compact sparkline chart for dashboards'
    )

    # Data components
    ComponentRegistry.register(
        'DataTable', DataTable, 'data', '1.1.0',
        'Enhanced table view with sorting and filtering'
    )
    ComponentRegistry.register(
        'BackgroundTaskMonitor', BackgroundTaskMonitor, 'data', '1.1.0',
        'Monitor for background tasks with progress tracking'
    )

    # Simulation components
    ComponentRegistry.register(
        'SimulationLauncher', SimulationLauncher, 'simulation', '1.1.0',
        'Universal physics simulation launcher for Raphael engine'
    )

    ComponentRegistry._initialized = True


# Run auto-registration on import
_register_all_components()


# Export public API
__all__ = [
    # Display
    'LayeredCard',
    'LayeredPane',
    'GlassPanel',
    'StatCard',

    # Loading
    'ProgressBar',
    'LoadingSpinner',
    'LoadingOverlay',

    # Charts
    'ChartCard',
    'MiniChart',

    # Data
    'DataTable',
    'BackgroundTaskMonitor',

    # Registry
    'ComponentRegistry',
    'ComponentInfo',
    'get_component',
]
