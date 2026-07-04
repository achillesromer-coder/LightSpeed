"""
LightSpeed V0.9.5 - Configuration Module
Centralized configuration for the entire platform

Author: LightSpeed Team
Version: 0.9.5
Date: January 3, 2026
"""

from .paths import (
    LIGHTSPEED_ROOT,
    Z_AXIS_ROOT,
    # Neo (Z+3)
    NEO_ROOT, NEO_AGENT, NEO_CONTEXT, NEO_COORDINATION,
    # Morpheus (Z+2)
    MORPHEUS_ROOT, MORPHEUS_ENCYCLOPEDIA, MORPHEUS_LIBRARY, MORPHEUS_DOCS, MORPHEUS_KNOWLEDGE,
    # Architect (Z+1)
    ARCHITECT_ROOT, ARCHITECT_TOOLS, ARCHITECT_PLANNING, ARCHITECT_PROJECTS,
    # TheConstruct (Z0)
    CONSTRUCT_ROOT, CONSTRUCT_PHYSICS, CONSTRUCT_SIMULATIONS, CONSTRUCT_RENDER,
    # Oracle (Z-1)
    ORACLE_ROOT, ORACLE_ARCHIVE, ORACLE_LIBRARY, ORACLE_IMMERSIVE,
    # Smith (Z-2)
    SMITH_ROOT, SMITH_LOGS, SMITH_TASKS, SMITH_NEO_INTEGRATION, SMITH_SMART_FLOOR,
    # Merovingian (Z-3)
    MEROVINGIAN_ROOT, MEROVINGIAN_DATA, MEROVINGIAN_PROFILES, MEROVINGIAN_OPTIMIZATION,
    # Trinity (Z-4)
    TRINITY_ROOT, TRINITY_SETTINGS, TRINITY_THEMES, TRINITY_PORTAL_CONFIG, TRINITY_UI_CONFIG,
    TRINITY_ENVIRONMENT, TRINITY_OUTPUT,
    # Utilities
    resolve_path, ensure_path, migrate_legacy_path, initialize_z_floor_structure,
)

__all__ = [
    'LIGHTSPEED_ROOT', 'Z_AXIS_ROOT',
    'NEO_ROOT', 'MORPHEUS_ROOT', 'ARCHITECT_ROOT', 'CONSTRUCT_ROOT',
    'ORACLE_ROOT', 'SMITH_ROOT', 'MEROVINGIAN_ROOT', 'TRINITY_ROOT',
    'resolve_path', 'ensure_path', 'migrate_legacy_path', 'initialize_z_floor_structure',
]
