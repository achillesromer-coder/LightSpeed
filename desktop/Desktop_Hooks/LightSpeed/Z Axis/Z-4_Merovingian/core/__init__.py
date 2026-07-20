"""LightSpeed core package.

The essential runtime is intentionally small: database, event bus, storage and
service lifecycle. Optional AI, physics, template, expansion and analysis
systems are loaded only when explicitly requested. This prevents one missing
optional dependency from disabling Merovingian, Architect, LS Desktop or the
LS GO loopback bridge.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__version__ = "1.0.0"
__author__ = "LightSpeed Team / Römer Industries"

from .services import (  # noqa: E402
    get_db,
    get_event_bus,
    get_storage,
    initialize_services,
    shutdown_services,
)

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "FloorLoader": (".services.floor_loader", "FloorLoader"),
    "DataAccumulationEngine": (".services.data_accumulation_engine", "DataAccumulationEngine"),
    "DataType": (".services.data_accumulation_engine", "DataType"),
    "DataObject": (".services.data_accumulation_engine", "DataObject"),
    "SmartFloorExpansionEngine": (".services.smart_floor_expansion", "SmartFloorExpansionEngine"),
    "CapabilityType": (".services.smart_floor_expansion", "CapabilityType"),
    "FunctionLibraryRegistry": (".services.function_registry", "FunctionLibraryRegistry"),
    "get_registry": (".services.function_registry", "get_registry"),
    "OllamaConnector": (".ai.ollama_connector", "OllamaConnector"),
    "OllamaConfig": (".ai.ollama_connector", "OllamaConfig"),
    "AITools": (".ai.ai_tools", "AITools"),
    "PhysicsTools": (".services.physics_tools", "PhysicsTools"),
    "get_physics_tools": (".services.physics_tools", "get_physics_tools"),
    "calculate_raphael_equations": (".services.physics_tools", "calculate_raphael_equations"),
    "generate_big_bang_simulation": (".services.physics_tools", "generate_big_bang_simulation"),
    "calculate_schwarzschild_radius": (".services.physics_tools", "calculate_schwarzschild_radius"),
    "UserPreferences": (".services.user_preferences", "UserPreferences"),
    "get_user_preferences": (".services.user_preferences", "get_user_preferences"),
    "BaseTemplate": (".services.template_system", "BaseTemplate"),
    "DocumentTemplate": (".services.template_system", "DocumentTemplate"),
    "UITemplate": (".services.template_system", "UITemplate"),
    "TestTemplate": (".services.template_system", "TestTemplate"),
    "QRCodeTemplate": (".services.template_system", "QRCodeTemplate"),
    "TableTemplate": (".services.template_system", "TableTemplate"),
    "ImageTemplate": (".services.template_system", "ImageTemplate"),
    "ThemeTemplate": (".services.template_system", "ThemeTemplate"),
    "VenvSetupTemplate": (".services.template_system", "VenvSetupTemplate"),
    "TemplateRegistry": (".services.template_system", "TemplateRegistry"),
    "get_template_registry": (".services.template_system", "get_template_registry"),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attribute = target
    try:
        value = getattr(import_module(module_name, __name__), attribute)
    except Exception as exc:  # optional capability failure must not break core import
        raise ImportError(f"Optional LightSpeed capability {name!r} is unavailable: {exc}") from exc
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LAZY_EXPORTS))


CORE_MODULES = {
    "services": "Essential database, event bus, storage and runtime lifecycle",
    "ai": "Optional local AI systems and connectors",
    "ui": "Optional user-interface components",
    "api": "Optional API management and endpoints",
    "workflows": "Optional workflow engine and designer",
    "project_manager": "Project management and file handling",
}


def get_core_info() -> dict[str, Any]:
    return {
        "version": __version__,
        "modules": CORE_MODULES,
        "total_modules": len(CORE_MODULES),
        "essential_runtime": ["database", "event_bus", "storage"],
        "optional_loading": "lazy",
    }


__all__ = [
    "__version__",
    "__author__",
    "get_db",
    "get_event_bus",
    "get_storage",
    "initialize_services",
    "shutdown_services",
    "get_core_info",
    *_LAZY_EXPORTS.keys(),
]
