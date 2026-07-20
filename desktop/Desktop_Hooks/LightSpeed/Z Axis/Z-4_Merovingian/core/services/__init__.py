"""Essential LightSpeed services with lazy optional capability loading.

Database, event bus, storage and logging must remain available even when an
optional integration, UI package, websocket dependency or physics module is
missing. Optional services are imported only when a caller asks for them.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from .database import DatabaseService, get_db
from .event_bus import EventBus, Event, EventTypes, FloorEventPublisher, get_event_bus
from .storage import StorageService, get_storage
from .logger import (
    FloorLogger,
    LoggedOperation,
    get_logger,
    get_neo_logger,
    get_morpheus_logger,
    get_architect_logger,
    get_construct_logger,
    get_oracle_logger,
    get_smith_logger,
    get_merovingian_logger,
    get_trinity_logger,
    get_services_logger,
)

__version__ = "1.3.0"
__author__ = "LightSpeed Team / ACHILLES"

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "SettingsHub": (".settings_hub", "SettingsHub"),
    "get_settings_hub": (".settings_hub", "get_settings_hub"),
    "FloorManager": (".floor_manager", "FloorManager"),
    "FloorInfo": (".floor_manager", "FloorInfo"),
    "get_floor_manager": (".floor_manager", "get_floor_manager"),
    "initialize_all_floors": (".floor_manager", "initialize_all_floors"),
    "DataspaceService": (".dataspace", "DataspaceService"),
    "get_dataspace": (".dataspace", "get_dataspace"),
    "ArtifactRef": (".dataspace", "ArtifactRef"),
    "ZDirectService": (".dataspace", "ZDirectService"),
    "get_z_direct": (".dataspace", "get_z_direct"),
    "PhysicsTools": (".physics_tools", "PhysicsTools"),
    "get_physics_tools": (".physics_tools", "get_physics_tools"),
    "calculate_raphael_equations": (".physics_tools", "calculate_raphael_equations"),
    "generate_big_bang_simulation": (".physics_tools", "generate_big_bang_simulation"),
    "calculate_schwarzschild_radius": (".physics_tools", "calculate_schwarzschild_radius"),
    "UserPreferences": (".user_preferences", "UserPreferences"),
    "get_user_preferences": (".user_preferences", "get_user_preferences"),
    "BaseTemplate": (".template_system", "BaseTemplate"),
    "DocumentTemplate": (".template_system", "DocumentTemplate"),
    "UITemplate": (".template_system", "UITemplate"),
    "TestTemplate": (".template_system", "TestTemplate"),
    "QRCodeTemplate": (".template_system", "QRCodeTemplate"),
    "TableTemplate": (".template_system", "TableTemplate"),
    "ImageTemplate": (".template_system", "ImageTemplate"),
    "ThemeTemplate": (".template_system", "ThemeTemplate"),
    "VenvSetupTemplate": (".template_system", "VenvSetupTemplate"),
    "TemplateRegistry": (".template_system", "TemplateRegistry"),
    "get_template_registry": (".template_system", "get_template_registry"),
    "PredictiveMaintenanceEngine": (".predictive_maintenance", "PredictiveMaintenanceEngine"),
    "get_predictive_maintenance_engine": (".predictive_maintenance", "get_predictive_maintenance_engine"),
    "WorldServer": (".world_server", "WorldServer"),
    "get_world_server": (".world_server", "get_world_server"),
    "start_world_server": (".world_server", "start_world_server"),
    "stop_world_server": (".world_server", "stop_world_server"),
    "ExternalServiceManager": (".external_integrations", "ExternalServiceManager"),
    "CanvaIntegration": (".external_integrations", "CanvaIntegration"),
    "DropboxIntegration": (".external_integrations", "DropboxIntegration"),
    "GoogleDriveIntegration": (".external_integrations", "GoogleDriveIntegration"),
    "OneDriveIntegration": (".external_integrations", "OneDriveIntegration"),
    "get_service_manager": (".external_integrations", "get_service_manager"),
    "get_canva": (".external_integrations", "get_canva"),
    "get_dropbox": (".external_integrations", "get_dropbox"),
    "get_google_drive": (".external_integrations", "get_google_drive"),
    "get_onedrive": (".external_integrations", "get_onedrive"),
    "PerformanceMonitor": (".performance_monitor", "PerformanceMonitor"),
    "MetricType": (".performance_monitor", "MetricType"),
    "AlertLevel": (".performance_monitor", "AlertLevel"),
    "PerformanceMetric": (".performance_monitor", "PerformanceMetric"),
    "PerformanceAlert": (".performance_monitor", "PerformanceAlert"),
    "get_performance_monitor": (".performance_monitor", "get_performance_monitor"),
    "monitor_performance": (".performance_monitor", "monitor_performance"),
    "CacheManager": (".cache_manager", "CacheManager"),
    "CachePolicy": (".cache_manager", "CachePolicy"),
    "LRUCache": (".cache_manager", "LRUCache"),
    "DiskCache": (".cache_manager", "DiskCache"),
    "get_cache_manager": (".cache_manager", "get_cache_manager"),
    "cached": (".cache_manager", "cached"),
    "WebSocketServer": (".websocket_server", "WebSocketServer"),
    "WebSocketClient": (".websocket_server", "WebSocketClient"),
    "WebSocketMessage": (".websocket_server", "WebSocketMessage"),
    "MessageType": (".websocket_server", "MessageType"),
    "get_websocket_server": (".websocket_server", "get_websocket_server"),
    "start_websocket_server": (".websocket_server", "start_websocket_server"),
    "stop_websocket_server": (".websocket_server", "stop_websocket_server"),
    "integrate_with_event_bus": (".websocket_server", "integrate_with_event_bus"),
    "integrate_with_performance_monitor": (".websocket_server", "integrate_with_performance_monitor"),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attribute = target
    try:
        value = getattr(import_module(module_name, __name__), attribute)
    except Exception as exc:
        raise ImportError(f"Optional service capability {name!r} is unavailable: {exc}") from exc
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LAZY_EXPORTS))


def initialize_services() -> dict[str, Any]:
    """Initialize the essential Merovingian runtime only."""
    try:
        from core.config.paths import initialize_z_floor_structure  # type: ignore
        initialize_z_floor_structure()
    except Exception:
        pass

    db = get_db()
    event_bus = get_event_bus()
    storage = get_storage()
    logger = get_services_logger()
    logger.info("=== LightSpeed Essential Services Initialized ===")
    logger.info(f"Database: {getattr(db, 'db_path', 'unknown')}")
    logger.info(f"Storage: {getattr(storage, 'storage_root', 'unknown')}")
    try:
        logger.info(f"Event Bus: {event_bus.get_stats().get('enabled')}")
    except Exception:
        logger.info("Event Bus: available")
    return {
        "database": db,
        "event_bus": event_bus,
        "storage": storage,
        "logger": logger,
    }


def shutdown_services() -> None:
    logger = get_services_logger()
    logger.info("=== Shutting down LightSpeed Essential Services ===")
    try:
        get_event_bus().disable()
    except Exception:
        pass
    logger.info("Essential services shutdown complete")


_ESSENTIAL_EXPORTS = [
    "DatabaseService", "get_db", "EventBus", "Event", "EventTypes",
    "FloorEventPublisher", "get_event_bus", "StorageService", "get_storage",
    "FloorLogger", "LoggedOperation", "get_logger", "get_neo_logger",
    "get_morpheus_logger", "get_architect_logger", "get_construct_logger",
    "get_oracle_logger", "get_smith_logger", "get_merovingian_logger",
    "get_trinity_logger", "get_services_logger", "initialize_services",
    "shutdown_services",
]

__all__ = [*_ESSENTIAL_EXPORTS, *_LAZY_EXPORTS.keys()]
