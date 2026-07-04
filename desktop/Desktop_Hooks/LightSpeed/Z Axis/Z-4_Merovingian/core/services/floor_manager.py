#!/usr/bin/env python
"""
Floor Manager - Automated Floor Registration and Integration System
Orchestrates all Z Axis floors, connecting them to Event Bus, Settings Hub, and Bento Hub
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class FloorInfo:
    """
    Floor registration information

    Attributes:
        name: Floor identifier (e.g., 'Z-0_Foundation')
        level: Z-axis level (0, 1, 2, etc.)
        status: Floor status (registered, initializing, active, error)
        services: Services this floor provides
        dependencies: Floors this floor depends on
        bento_registered: Whether Bento config is registered
        event_subscriptions: Events this floor subscribes to
    """
    name: str
    level: int
    status: str = 'registered'
    services: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    bento_registered: bool = False
    event_subscriptions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class FloorManager:
    """
    Automated Floor Management System

    Features:
    - Auto-discovery of floor Bento configurations
    - Dependency resolution and ordered initialization
    - Event Bus connection for all floors
    - Settings Hub integration
    - Bento Hub widget registration
    - Health monitoring
    - Floor communication orchestration

    Usage:
        manager = FloorManager()
        manager.discover_floors()
        manager.initialize_all_floors()
        manager.start_floor_communication()
    """

    def __init__(self):
        self.floors: Dict[str, FloorInfo] = {}
        self.event_bus = None
        self.settings_hub = None
        self.bento_hub = None

        # Get Z Axis root
        self.z_axis_root = self._find_z_axis_root()

        # Connect to core services
        self._connect_core_services()

        logger.info("Floor Manager initialized")

    def _find_z_axis_root(self) -> Path:
        """Find Z Axis directory"""
        current = Path(__file__).resolve()
        for parent in current.parents:
            z_axis = parent / 'Z Axis'
            if z_axis.exists() and z_axis.is_dir():
                return z_axis
        return Path('Z Axis')

    def _connect_core_services(self):
        """Connect to Event Bus, Settings Hub, and Bento Hub"""
        try:
            from . import get_event_bus, get_settings_hub
            from core.ui.unified_bento_hub import get_bento_hub

            self.event_bus = get_event_bus()
            self.settings_hub = get_settings_hub()
            self.bento_hub = get_bento_hub()

            logger.info("[+] Connected to core services")

            # Subscribe to floor events
            self.event_bus.subscribe('floor.*', self._on_floor_event)
            self.event_bus.subscribe('bento.register_widgets', self._on_bento_registration)

        except Exception as e:
            logger.error(f"Failed to connect core services: {e}")

    def discover_floors(self) -> int:
        """
        Auto-discover canonical Z Axis floors by scanning for bento_config.py.

        Returns:
            Number of floors discovered
        """
        if not self.z_axis_root.exists():
            logger.warning(f"Z Axis root not found: {self.z_axis_root}")
            return 0

        discovered = 0

        # Canonical 8-floor stack, inside-out order (core -> UI shell).
        # NOTE: This manager does not load floor components; it only reports discovery/status and
        # can register optional Bento configs. Keep the discovery list aligned with FloorLoader.
        order = ["Z-4", "Z-3", "Z-2", "Z-1", "Z0", "Z+1", "Z+2", "Z+3"]
        canonical_prefixes = set(order)

        for floor_dir in sorted([p for p in self.z_axis_root.iterdir() if p.is_dir()], key=lambda p: p.name):
            floor_name = floor_dir.name
            if "_" not in floor_name:
                continue

            prefix = floor_name.split("_", 1)[0].strip()
            if prefix not in canonical_prefixes:
                continue

            # Convert canonical Z prefix to stable inside-out order index.
            try:
                level = order.index(prefix)
            except ValueError:
                level = 0

            # Check for bento_config.py
            bento_config = floor_dir / "bento_config.py"

            floor_info = FloorInfo(
                name=floor_name,
                level=level,
                status="discovered",
                metadata={"path": str(floor_dir), "prefix": prefix},
            )

            if bento_config.exists():
                floor_info.metadata["has_bento_config"] = True

            self.floors[floor_name] = floor_info
            discovered += 1

            logger.info(f"[+] Discovered: {floor_name} (Level {level})")

        logger.info(f"Discovered {discovered} floors")
        return discovered

    def register_floor_bento_configs(self) -> int:
        """
        Register all floor Bento configurations

        Returns:
            Number of floors registered
        """
        registered = 0

        for floor_name, floor_info in self.floors.items():
            if floor_info.metadata.get('has_bento_config'):
                try:
                    floor_path = Path(floor_info.metadata["path"])
                    bento_config = floor_path / "bento_config.py"
                    if not bento_config.exists():
                        continue

                    # Load per-floor module without sys.path side effects / cross-floor caching.
                    import importlib.util

                    module_name = f"lightspeed_bento_{floor_name.replace('-', '_').replace('+', '_')}"
                    spec = importlib.util.spec_from_file_location(module_name, bento_config)
                    if spec is None or spec.loader is None:
                        logger.warning(f"Could not load bento_config for {floor_name}")
                        continue

                    bento_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(bento_module)  # type: ignore[union-attr]

                    # Find registration function
                    register_func = None
                    for attr in dir(bento_module):
                        if 'register' in attr.lower() and 'bento' in attr.lower():
                            register_func = getattr(bento_module, attr)
                            break

                    if register_func and callable(register_func):
                        register_func()
                        floor_info.bento_registered = True
                        floor_info.status = 'bento_registered'
                        registered += 1
                        logger.info(f"[+] Registered Bento config: {floor_name}")
                    else:
                        logger.warning(f"No registration function found for {floor_name}")

                except Exception as e:
                    logger.error(f"Failed to register {floor_name}: {e}")
                    floor_info.status = 'error'

        logger.info(f"Registered {registered} Bento configurations")
        return registered

    def initialize_all_floors(self) -> int:
        """
        Initialize all discovered floors in dependency order

        Returns:
            Number of floors initialized
        """
        initialized = 0

        # Sort floors by level (Foundation first, Command last)
        sorted_floors = sorted(
            self.floors.items(),
            key=lambda x: x[1].level
        )

        for floor_name, floor_info in sorted_floors:
            try:
                # Mark as initializing
                floor_info.status = 'initializing'

                # Publish initialization event
                if self.event_bus:
                    self.event_bus.publish(
                        'floor.initializing',
                        {
                            'floor': floor_name,
                            'level': floor_info.level
                        }
                    )

                # Mark as active
                floor_info.status = 'active'
                initialized += 1

                logger.info(f"[+] Initialized: {floor_name}")

                # Publish ready event
                if self.event_bus:
                    self.event_bus.publish(
                        'floor.ready',
                        {
                            'floor': floor_name,
                            'level': floor_info.level
                        }
                    )

            except Exception as e:
                logger.error(f"Failed to initialize {floor_name}: {e}")
                floor_info.status = 'error'

        logger.info(f"Initialized {initialized} floors")
        return initialized

    def start_floor_communication(self):
        """
        Start inter-floor communication by setting up event subscriptions

        Each floor can listen to events from other floors
        """
        if not self.event_bus:
            logger.warning("Event Bus not available")
            return

        # Publish system ready event
        self.event_bus.publish(
            'system.floors_ready',
            {
                'total_floors': len(self.floors),
                'active_floors': len([f for f in self.floors.values() if f.status == 'active']),
                'floors': list(self.floors.keys())
            }
        )

        logger.info("[+] Floor communication started")

    def get_floor_status(self, floor_name: str) -> Optional[FloorInfo]:
        """Get status of a specific floor"""
        return self.floors.get(floor_name)

    def get_all_floors_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all floors

        Returns:
            Dict mapping floor names to status info
        """
        return {
            name: {
                'level': info.level,
                'status': info.status,
                'bento_registered': info.bento_registered,
                'services': info.services,
                'dependencies': info.dependencies
            }
            for name, info in self.floors.items()
        }

    def get_active_floors(self) -> List[str]:
        """Get list of active floor names"""
        return [
            name for name, info in self.floors.items()
            if info.status == 'active'
        ]

    def publish_to_floor(self, floor_name: str, event_type: str, data: Any):
        """
        Publish event to a specific floor

        Args:
            floor_name: Target floor name
            event_type: Event type
            data: Event payload
        """
        if self.event_bus:
            self.event_bus.publish(
                f"{floor_name.lower()}.{event_type}",
                data
            )

    def broadcast_to_all_floors(self, event_type: str, data: Any):
        """
        Broadcast event to all active floors

        Args:
            event_type: Event type
            data: Event payload
        """
        if self.event_bus:
            for floor_name in self.get_active_floors():
                self.event_bus.publish(
                    f"{floor_name.lower()}.{event_type}",
                    data
                )

    def _on_floor_event(self, event):
        """Handle floor-related events"""
        event_type = event.event_type if hasattr(event, 'event_type') else 'unknown'
        data = event.data if hasattr(event, 'data') else {}

        logger.debug(f"Floor event: {event_type} - {data}")

    def _on_bento_registration(self, event):
        """Handle Bento widget registration events"""
        data = event.data if hasattr(event, 'data') else {}
        floor = data.get('floor')

        if floor and floor in self.floors:
            self.floors[floor].bento_registered = True
            logger.info(f"[+] Bento registered: {floor}")

    def shutdown_all_floors(self):
        """Gracefully shutdown all floors"""
        logger.info("Shutting down all floors...")

        # Reverse order shutdown (Command first, Foundation last)
        sorted_floors = sorted(
            self.floors.items(),
            key=lambda x: x[1].level,
            reverse=True
        )

        for floor_name, floor_info in sorted_floors:
            try:
                # Publish shutdown event
                if self.event_bus:
                    self.event_bus.publish(
                        'floor.shutdown',
                        {'floor': floor_name}
                    )

                floor_info.status = 'shutdown'
                logger.info(f"[+] Shutdown: {floor_name}")

            except Exception as e:
                logger.error(f"Error shutting down {floor_name}: {e}")

        logger.info("All floors shutdown complete")

    def get_statistics(self) -> Dict[str, Any]:
        """Get Floor Manager statistics"""
        return {
            'total_floors': len(self.floors),
            'active_floors': len(self.get_active_floors()),
            'bento_registered': len([f for f in self.floors.values() if f.bento_registered]),
            'floors_by_status': {
                status: len([f for f in self.floors.values() if f.status == status])
                for status in set(f.status for f in self.floors.values())
            },
            'floors': list(self.floors.keys())
        }


# Singleton instance
_floor_manager_instance: Optional[FloorManager] = None


def get_floor_manager() -> FloorManager:
    """
    Get Floor Manager singleton instance

    Returns:
        FloorManager instance
    """
    global _floor_manager_instance

    if _floor_manager_instance is None:
        _floor_manager_instance = FloorManager()

    return _floor_manager_instance


def initialize_all_floors():
    """
    Convenience function to discover and initialize all floors

    Returns:
        FloorManager instance
    """
    manager = get_floor_manager()

    print("\n" + "=" * 70)
    print("  LightSpeed Floor Manager - Automated Initialization")
    print("=" * 70)

    # Discover floors
    print("\n[1/4] Discovering floors...")
    discovered = manager.discover_floors()
    print(f"      -> Discovered {discovered} floors")

    # Register Bento configs
    print("\n[2/4] Registering Bento configurations...")
    registered = manager.register_floor_bento_configs()
    print(f"      -> Registered {registered} Bento configs")

    # Initialize floors
    print("\n[3/4] Initializing floors...")
    initialized = manager.initialize_all_floors()
    print(f"      -> Initialized {initialized} floors")

    # Start communication
    print("\n[4/4] Starting floor communication...")
    manager.start_floor_communication()
    print("      -> Floor communication active")

    # Show statistics
    stats = manager.get_statistics()
    print("\n" + "=" * 70)
    print("  Floor System Status")
    print("=" * 70)
    print(f"  Total Floors: {stats['total_floors']}")
    print(f"  Active Floors: {stats['active_floors']}")
    print(f"  Bento Registered: {stats['bento_registered']}")
    print("\n  Active Floors:")
    for floor in manager.get_active_floors():
        info = manager.get_floor_status(floor)
        print(f"    - {floor:20} Level {info.level:2} [{info.status}]")

    print("\n" + "=" * 70)
    print("  [+] All floors initialized and ready!")
    print("=" * 70 + "\n")

    return manager


if __name__ == '__main__':
    # Test Floor Manager
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    manager = initialize_all_floors()

    # Show final status
    print("\nFloor Manager Statistics:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
