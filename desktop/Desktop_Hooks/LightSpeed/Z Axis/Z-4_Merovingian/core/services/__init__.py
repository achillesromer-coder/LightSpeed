"""
Core Services - Basement Layer Infrastructure
LightSpeed Type I Civilization Platform

This module provides the foundational services that connect all Z-axis floors:

Services:
- DatabaseService: Unified database access across all floors
- EventBus: Inter-floor communication system
- StorageService: File management and storage
- FloorLogger: 99.9% fidelity logging system
- PhysicsTools: Consolidated physics simulations and calculations
- UserPreferences: Per-user settings and customization
- TemplateSystem: Productive template generators (QR, tables, UI, tests)

The services layer forms the basement/foundation of the tower, providing
shared infrastructure that all floors (Neo, Morpheus, Architect, TheConstruct,
Oracle, Smith, Merovingian, Trinity) rely upon.

Author: LightSpeed Team / ACHILLES
Version: 0.9.5 - Added PhysicsTools umbrella
"""

from .database import DatabaseService, get_db
from .event_bus import (
    EventBus,
    Event,
    EventTypes,
    FloorEventPublisher,
    get_event_bus
)
from .settings_hub import (
    SettingsHub,
    get_settings_hub
)
from .floor_manager import (
    FloorManager,
    FloorInfo,
    get_floor_manager,
    initialize_all_floors
)
from .storage import StorageService, get_storage
from .dataspace import DataspaceService, get_dataspace, ArtifactRef
from .dataspace import ZDirectService, get_z_direct
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
    get_services_logger
)
from .physics_tools import (
    PhysicsTools,
    get_physics_tools,
    calculate_raphael_equations,
    generate_big_bang_simulation,
    calculate_schwarzschild_radius
)
from .user_preferences import UserPreferences, get_user_preferences
from .template_system import (
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
from .predictive_maintenance import (
    PredictiveMaintenanceEngine,
    get_predictive_maintenance_engine,
)
from .world_server import (
    WorldServer,
    get_world_server,
    start_world_server,
    stop_world_server
)
from .external_integrations import (
    ExternalServiceManager,
    CanvaIntegration,
    DropboxIntegration,
    GoogleDriveIntegration,
    OneDriveIntegration,
    get_service_manager,
    get_canva,
    get_dropbox,
    get_google_drive,
    get_onedrive
)
from .performance_monitor import (
    PerformanceMonitor,
    MetricType,
    AlertLevel,
    PerformanceMetric,
    PerformanceAlert,
    get_performance_monitor,
    monitor_performance
)
from .cache_manager import (
    CacheManager,
    CachePolicy,
    LRUCache,
    DiskCache,
    get_cache_manager,
    cached
)
from .websocket_server import (
    WebSocketServer,
    WebSocketClient,
    WebSocketMessage,
    MessageType,
    get_websocket_server,
    start_websocket_server,
    stop_websocket_server,
    integrate_with_event_bus,
    integrate_with_performance_monitor
)

__version__ = "1.2.0"
__author__ = "LightSpeed Team / ACHILLES"

__all__ = [
    # Database
    'DatabaseService',
    'get_db',

    # Event Bus
    'EventBus',
    'Event',
    'EventTypes',
    'FloorEventPublisher',
    'get_event_bus',

    # Settings Hub
    'SettingsHub',
    'get_settings_hub',

    # Floor Manager
    'FloorManager',
    'FloorInfo',
    'get_floor_manager',
    'initialize_all_floors',

    # Storage
    'StorageService',
    'get_storage',

    # Dataspace
    'DataspaceService',
    'get_dataspace',
    'ArtifactRef',
    'ZDirectService',
    'get_z_direct',

    # Logging
    'FloorLogger',
    'LoggedOperation',
    'get_logger',
    'get_neo_logger',
    'get_morpheus_logger',
    'get_architect_logger',
    'get_construct_logger',
    'get_oracle_logger',
    'get_smith_logger',
    'get_merovingian_logger',
    'get_trinity_logger',
    'get_services_logger',

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

    # Predictive Maintenance (Merovingian)
    'PredictiveMaintenanceEngine',
    'get_predictive_maintenance_engine',

    # World Server
    'WorldServer',
    'get_world_server',
    'start_world_server',
    'stop_world_server',

    # External Integrations
    'ExternalServiceManager',
    'CanvaIntegration',
    'DropboxIntegration',
    'GoogleDriveIntegration',
    'OneDriveIntegration',
    'get_service_manager',
    'get_canva',
    'get_dropbox',
    'get_google_drive',
    'get_onedrive',

    # Performance Monitoring
    'PerformanceMonitor',
    'MetricType',
    'AlertLevel',
    'PerformanceMetric',
    'PerformanceAlert',
    'get_performance_monitor',
    'monitor_performance',

    # Cache Management
    'CacheManager',
    'CachePolicy',
    'LRUCache',
    'DiskCache',
    'get_cache_manager',
    'cached',

    # WebSocket Server
    'WebSocketServer',
    'WebSocketClient',
    'WebSocketMessage',
    'MessageType',
    'get_websocket_server',
    'start_websocket_server',
    'stop_websocket_server',
    'integrate_with_event_bus',
    'integrate_with_performance_monitor',
]


def initialize_services():
    """
    Initialize all core services.

    Call this at application startup to ensure all services are ready.

    Returns:
        Dict with service instances
    """
    # Ensure floor-native directory scaffolds exist before services start
    # (idempotent; avoids legacy root folders like `Data/` being recreated).
    try:
        from core.config.paths import initialize_z_floor_structure  # type: ignore

        initialize_z_floor_structure()
    except Exception:
        pass

    db = get_db()
    event_bus = get_event_bus()
    storage = get_storage()
    logger = get_services_logger()

    logger.info("=== LightSpeed Core Services Initialized ===")
    logger.info(f"Database: {db.db_path}")
    logger.info(f"Storage: {storage.storage_root}")
    logger.info(f"Event Bus: {event_bus.get_stats()['enabled']}")

    return {
        'database': db,
        'event_bus': event_bus,
        'storage': storage,
        'logger': logger
    }


def shutdown_services():
    """
    Gracefully shutdown all services.

    Call this before application exit.
    """
    logger = get_services_logger()
    logger.info("=== Shutting down LightSpeed Core Services ===")

    # Clean up resources
    event_bus = get_event_bus()
    event_bus.disable()

    logger.info("Core services shutdown complete")


if __name__ == "__main__":
    # Test services integration
    print("Core Services Integration Test")
    print("=" * 50)

    # Initialize all services
    print("\nInitializing services...")
    services = initialize_services()

    print("\n✓ Services initialized:")
    for name, service in services.items():
        print(f"  - {name}: {type(service).__name__}")

    # Test inter-service communication
    print("\nTest: Inter-service communication")

    # Create event publisher for TheConstruct
    publisher = FloorEventPublisher('TheConstruct', services['event_bus'])

    # Subscribe Trinity dashboard to simulation events
    def on_simulation_complete(event: Event):
        logger = get_trinity_logger()
        logger.info(f"Dashboard: Simulation completed - {event.data}")

    services['event_bus'].subscribe(
        EventTypes.SIMULATION_COMPLETED,
        on_simulation_complete,
        floor='Trinity'
    )

    # Publish simulation event
    publisher.publish(
        EventTypes.SIMULATION_COMPLETED,
        data={'sim_id': 100, 'type': 'raphael', 'status': 'success'}
    )

    import time
    time.sleep(0.1)  # Allow async processing

    # Get stats
    print("\nService Statistics:")
    eb_stats = services['event_bus'].get_stats()
    print(f"  Event Bus: {eb_stats['total_subscribers']} subscribers, "
          f"{eb_stats['history_size']} events")

    storage_stats = services['storage'].get_storage_stats()
    print(f"  Storage: {storage_stats['total_files']} files, "
          f"{storage_stats['total_size_mb']:.2f} MB")

    db_tables = services['database'].get_all_tables()
    print(f"  Database: {len(db_tables)} tables")

    # Shutdown
    print("\nShutting down services...")
    shutdown_services()

    print("\n" + "=" * 50)
    print("Core services ready to support all floors!")
