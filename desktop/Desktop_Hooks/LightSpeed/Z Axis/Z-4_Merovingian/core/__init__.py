"""
LightSpeed Core - Unified Platform Foundation
Version: 0.9.5
Date: December 21, 2025

Consolidated from: Cognigrex Core + core modules
This is THE unified core for all LightSpeed platform functionality.

Architecture:
- services/     - Core integration systems (FloorLoader, Data Accumulation, Smart Expansion, PhysicsTools)
- ai/           - AI systems (Ollama connector, AI tools)
- ui/           - User interface components and widgets
- api/          - API management and endpoints
- workflows/    - Workflow engine and designer
- project_manager/ - Project management tools

Clean Code Principle: Single consolidated core, no duplication
"""

__version__ = "0.9.5"
__author__ = "LightSpeed Team / Römer Industries"

# Services - Core Integration Systems
from .services import (
    initialize_services,
    shutdown_services,
    get_db,
    get_event_bus,
    get_storage,
)

from .services.floor_loader import FloorLoader
from .services.data_accumulation_engine import DataAccumulationEngine, DataType, DataObject
from .services.smart_floor_expansion import SmartFloorExpansionEngine, CapabilityType
from .services.function_registry import FunctionLibraryRegistry, get_registry

# AI Systems
from .ai.ollama_connector import OllamaConnector, OllamaConfig
from .ai.ai_tools import AITools

# Physics Tools (consolidated)
from .services.physics_tools import (
    PhysicsTools,
    get_physics_tools,
    calculate_raphael_equations,
    generate_big_bang_simulation,
    calculate_schwarzschild_radius,
)

# User Preferences
from .services.user_preferences import UserPreferences, get_user_preferences

# Template System
from .services.template_system import (
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

# All exported symbols
__all__ = [
    # Version info
    '__version__',
    '__author__',

    # Services
    'initialize_services',
    'shutdown_services',
    'get_db',
    'get_event_bus',
    'get_storage',
    'FloorLoader',
    'DataAccumulationEngine',
    'DataType',
    'DataObject',
    'SmartFloorExpansionEngine',
    'CapabilityType',
    'FunctionLibraryRegistry',
    'get_registry',

    # AI
    'OllamaConnector',
    'OllamaConfig',
    'AITools',

    # Physics Tools
    'PhysicsTools',
    'get_physics_tools',
    'calculate_raphael_equations',
    'generate_big_bang_simulation',
    'calculate_schwarzschild_radius',

    # User Preferences
    'UserPreferences',
    'get_user_preferences',

    # Template System
    'BaseTemplate',
    'DocumentTemplate',
    'UITemplate',
    'TestTemplate',
    'QRCodeTemplate',
    'TableTemplate',
    'ImageTemplate',
    'ThemeTemplate',
    'VenvSetupTemplate',
    'TemplateRegistry',
    'get_template_registry',
]

# Module information for introspection
CORE_MODULES = {
    'services': 'Core integration systems (DB, EventBus, Storage, PhysicsTools, UserPreferences, TemplateSystem)',
    'ai': 'AI systems and connectors (Ollama, Achilles, tools)',
    'ui': 'User interface components and widgets (TemplateManager, SettingsManager)',
    'api': 'API management and endpoints',
    'workflows': 'Workflow engine and designer',
    'project_manager': 'Project management and file handling',
}

def get_core_info():
    """Get information about core modules"""
    return {
        'version': __version__,
        'modules': CORE_MODULES,
        'total_modules': len(CORE_MODULES)
    }
