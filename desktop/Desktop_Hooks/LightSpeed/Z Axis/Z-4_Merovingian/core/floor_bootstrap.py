#!/usr/bin/env python
"""
Floor Bootstrap - Standardized Floor Initialization
Provides common initialization pattern for all Z-floors
"""

from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
import sys


class FloorBootstrap:
    """
    Standard initialization and service loading for Z-floors

    Provides:
    - LightSpeed root discovery
    - Core services loading (DB, Event Bus, Storage)
    - Floor state management
    - Bento widget registration
    - Settings registration
    - Event handling helpers

    Usage:
        bootstrap = FloorBootstrap("Trinity", Path(__file__).parent)
        bootstrap.register_bento_widgets(widgets)
        bootstrap.register_settings(settings)
    """

    def __init__(self, floor_name: str, floor_path: Path):
        """
        Initialize floor bootstrap

        Args:
            floor_name: Name of the floor (e.g., "Trinity", "Neo", "Oracle")
            floor_path: Path to the floor directory
        """
        self.floor_name = floor_name
        self.floor_path = Path(floor_path)
        self.lightspeed_root = self._find_root()
        self.services = self._load_services()
        self.state = None

        self._setup_paths()

    def _find_root(self) -> Path:
        """
        Find LightSpeed root directory by searching for N.py

        Returns:
            Path to LightSpeed root directory
        """
        current = self.floor_path
        for parent in current.parents:
            if (parent / 'N.py').exists():
                return parent

        return Path.cwd()

    def _setup_paths(self):
        """Add LightSpeed root to sys.path if not already present"""
        root_str = str(self.lightspeed_root)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)

    def _load_services(self) -> Dict[str, Any]:
        """
        Load core services from Merovingian

        Returns:
            Dictionary with 'db', 'event_bus', 'storage' keys
            Values are None if service unavailable
        """
        services = {
            'db': None,
            'event_bus': None,
            'storage': None
        }

        try:
            from core.services import get_db, get_event_bus, get_storage
            services['db'] = get_db()
            services['event_bus'] = get_event_bus()
            services['storage'] = get_storage()
        except Exception as e:
            print(f"[{self.floor_name}] Core services not available: {e}")

        return services

    def get_service(self, name: str) -> Optional[Any]:
        """
        Get a specific core service

        Args:
            name: Service name ('db', 'event_bus', 'storage')

        Returns:
            Service instance or None if unavailable
        """
        return self.services.get(name)

    def register_bento_widgets(self, widgets: List[Dict[str, Any]]):
        """
        Register floor's Bento widgets with the Bento Hub

        Args:
            widgets: List of widget descriptors with format:
                {
                    'type': str,
                    'title': str,
                    'position': tuple,
                    'size': tuple,
                    'floor': str,
                    'resizable': bool,
                    'min_size': tuple
                }
        """
        event_bus = self.get_service('event_bus')
        if event_bus:
            try:
                event_bus.publish(
                    'bento.register_widgets',
                    {
                        'floor': self.floor_name,
                        'widgets': widgets
                    }
                )
            except Exception as e:
                print(f"[{self.floor_name}] Bento widget registration failed: {e}")

    def register_settings(self, settings: List[Dict[str, Any]]):
        """
        Register floor's settings with the Settings Hub

        Args:
            settings: List of setting descriptors with format:
                {
                    'name': str,
                    'type': str,  # 'TOGGLE', 'SLIDER', 'DROPDOWN', 'COLOR', 'TEXT'
                    'label': str,
                    'description': str,
                    'default': Any,
                    'options': list,  # For DROPDOWN
                    'min': float,  # For SLIDER
                    'max': float,  # For SLIDER
                }
        """
        event_bus = self.get_service('event_bus')
        if event_bus:
            try:
                event_bus.publish(
                    'settings.register_floor',
                    {
                        'floor': self.floor_name,
                        'settings': settings
                    }
                )
            except Exception as e:
                print(f"[{self.floor_name}] Settings registration failed: {e}")

    def publish_event(self, event_type: str, data: Any):
        """
        Publish event to Event Bus

        Args:
            event_type: Event type identifier (e.g., 'floor.ready', 'task.completed')
            data: Event payload (any serializable data)
        """
        event_bus = self.get_service('event_bus')
        if event_bus:
            try:
                event_bus.publish(event_type, data)
            except Exception as e:
                print(f"[{self.floor_name}] Event publish failed: {e}")

    def subscribe_event(self, event_type: str, callback: Callable):
        """
        Subscribe to Event Bus events

        Args:
            event_type: Event type to listen for
            callback: Function to call when event occurs (receives event data)
        """
        event_bus = self.get_service('event_bus')
        if event_bus:
            try:
                event_bus.subscribe(event_type, callback)
            except Exception as e:
                print(f"[{self.floor_name}] Event subscribe failed: {e}")

    def set_state(self, state: Any):
        """
        Set floor state object

        Args:
            state: Floor-specific state object (typically FloorState class instance)
        """
        self.state = state

    def get_state(self) -> Any:
        """
        Get floor state object

        Returns:
            Floor state or None if not set
        """
        return self.state

    def get_db_session(self):
        """
        Get database session

        Returns:
            SQLAlchemy session or None if DB unavailable
        """
        db = self.get_service('db')
        if db and hasattr(db, 'get_session'):
            return db.get_session()
        return None

    def store_data(self, key: str, data: Any):
        """
        Store data using Storage service

        Args:
            key: Storage key
            data: Data to store
        """
        storage = self.get_service('storage')
        if storage and hasattr(storage, 'set'):
            try:
                storage.set(key, data)
            except Exception as e:
                print(f"[{self.floor_name}] Storage failed: {e}")

    def retrieve_data(self, key: str) -> Optional[Any]:
        """
        Retrieve data from Storage service

        Args:
            key: Storage key

        Returns:
            Stored data or None if not found or Storage unavailable
        """
        storage = self.get_service('storage')
        if storage and hasattr(storage, 'get'):
            try:
                return storage.get(key)
            except Exception as e:
                print(f"[{self.floor_name}] Retrieval failed: {e}")
        return None

    def announce_ready(self):
        """Announce that floor is ready (publish 'floor.ready' event)"""
        self.publish_event(
            'floor.ready',
            {
                'floor': self.floor_name,
                'path': str(self.floor_path),
                'services_available': all(v is not None for v in self.services.values())
            }
        )

    def get_config_path(self, filename: str) -> Path:
        """
        Get path to floor-specific config file

        Args:
            filename: Config filename (e.g., 'settings.json')

        Returns:
            Path to config file in floor directory
        """
        return self.floor_path / 'config' / filename

    def get_data_path(self, filename: str) -> Path:
        """
        Get path to floor-specific data file

        Args:
            filename: Data filename

        Returns:
            Path to data file in floor directory
        """
        return self.floor_path / 'data' / filename


def create_bootstrap(floor_name: str, floor_file: Path) -> FloorBootstrap:
    """
    Convenience function to create floor bootstrap

    Args:
        floor_name: Name of the floor
        floor_file: Path to floor's main .py file (use Path(__file__))

    Returns:
        Initialized FloorBootstrap instance

    Usage:
        bootstrap = create_bootstrap("Trinity", Path(__file__))
    """
    return FloorBootstrap(floor_name, floor_file.parent)
