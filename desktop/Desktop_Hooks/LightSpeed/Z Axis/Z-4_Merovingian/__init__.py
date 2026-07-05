"""Z-4 Merovingian floor package exports.

Merovingian owns LightSpeed core services, compact activity tables, telemetry,
audit evidence, finalization reports, closure readiness, and quality output.
The active UI coordinator is ``Z Axis/Merovingian.py``.
"""

from pathlib import Path

__version__ = "5.1.2"
__floor_name__ = "Merovingian"
__z_level__ = -4
__owner__ = "core_services_and_evidence"

# Core services are exported from the core.services module
try:
    from core.services import (
        initialize_services,
        shutdown_services,
        get_db,
        get_event_bus,
        get_storage,
        get_logger,
        get_performance_monitor,
        get_cache_manager,
        get_websocket_server,
        get_service_manager,
        monitor_performance,
        MetricType
    )

    __all__ = [
        'initialize_services',
        'shutdown_services',
        'get_db',
        'get_event_bus',
        'get_storage',
        'get_logger',
        'get_performance_monitor',
        'get_cache_manager',
        'get_websocket_server',
        'get_service_manager',
        'monitor_performance',
        'MetricType'
    ]
except ImportError:
    __all__ = []
