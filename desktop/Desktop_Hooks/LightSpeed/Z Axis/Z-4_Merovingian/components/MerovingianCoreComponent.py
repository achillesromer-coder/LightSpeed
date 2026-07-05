"""
MerovingianCoreComponent - Core floor component
Merovingian Floor Component

System Core - Health & Diagnostics

Floor: Merovingian
Z-Level: -4
Author: LightSpeed Team
Version: 1.0.0
Date: 2026-01-13
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)


class MerovingianCoreComponentStatus(Enum):
    """Component operational status"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class MerovingianCoreComponentConfig:
    """Configuration for MerovingianCoreComponent"""
    enabled: bool = True
    auto_start: bool = False
    log_level: str = "INFO"
    cache_enabled: bool = True
    max_retries: int = 3
    timeout_seconds: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MerovingianCoreComponentConfig':
        """Load configuration from dictionary"""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'enabled': self.enabled,
            'auto_start': self.auto_start,
            'log_level': self.log_level,
            'cache_enabled': self.cache_enabled,
            'max_retries': self.max_retries,
            'timeout_seconds': self.timeout_seconds,
            'metadata': self.metadata
        }

    @classmethod
    def from_file(cls, config_path: Path) -> 'MerovingianCoreComponentConfig':
        """Load configuration from JSON file"""
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return cls()

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return cls()

    def save_to_file(self, config_path: Path) -> bool:
        """Save configuration to JSON file"""
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False


@dataclass
class MerovingianCoreComponentMetrics:
    """Performance metrics for MerovingianCoreComponent"""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    average_duration_ms: float = 0.0
    last_operation_time: Optional[str] = None
    uptime_seconds: float = 0.0

    def record_success(self, duration_ms: float):
        """Record successful operation"""
        self.total_operations += 1
        self.successful_operations += 1
        self.average_duration_ms = (
            (self.average_duration_ms * (self.total_operations - 1) + duration_ms)
            / self.total_operations
        )
        self.last_operation_time = datetime.now().isoformat()

    def record_failure(self):
        """Record failed operation"""
        self.total_operations += 1
        self.failed_operations += 1
        self.last_operation_time = datetime.now().isoformat()

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_operations == 0:
            return 0.0
        return (self.successful_operations / self.total_operations) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            'total_operations': self.total_operations,
            'successful_operations': self.successful_operations,
            'failed_operations': self.failed_operations,
            'average_duration_ms': self.average_duration_ms,
            'success_rate': self.success_rate,
            'last_operation_time': self.last_operation_time,
            'uptime_seconds': self.uptime_seconds
        }


class MerovingianCoreComponent:
    """
    Core floor component for Merovingian (System Core - Health & Diagnostics)

    This component provides:
    - Floor initialization
    - Event bus integration
    - State management
    - System health monitoring
    - Diagnostics and telemetry

    Floor Integration:
    - Publishes events to Event Bus: floor.initialized, floor.updated, floor.error, system.health
    - Subscribes to events: system.*, floor.*
    - Depends on: EventBus, Logger, SystemMetrics

    Usage:
        >>> component = MerovingianCoreComponent(lightspeed_root)
        >>> component.initialize()
        >>> result = component.execute()
        >>> health = component.get_status()
    """

    def __init__(
        self,
        lightspeed_root: Path,
        config: Optional[MerovingianCoreComponentConfig] = None,
        event_bus: Optional[Any] = None
    ):
        """
        Initialize MerovingianCoreComponent

        Parameters:
            lightspeed_root: Path to LightSpeed installation
            config: Component configuration (uses defaults if None)
            event_bus: Reference to floor event bus
        """
        self.lightspeed_root = Path(lightspeed_root)
        self.config = config or MerovingianCoreComponentConfig()
        self.event_bus = event_bus

        # State management
        self.status = MerovingianCoreComponentStatus.UNINITIALIZED
        self.metrics = MerovingianCoreComponentMetrics()
        self.start_time = datetime.now()

        # Component-specific paths
        self.floor_dir = self.lightspeed_root / "Z Axis" / "Z-4_Merovingian"
        self.data_dir = self.floor_dir / "data" / "merovingian_core"
        self.cache_dir = self.floor_dir / "cache" / "merovingian_core"
        self.config_dir = self.floor_dir / "config"

        # Ensure directories exist
        self._create_directories()

        # Configure logging
        self._setup_logging()

        logger.info(f"MerovingianCoreComponent instantiated")

    def _create_directories(self):
        """Create required directories"""
        for directory in [self.data_dir, self.cache_dir, self.config_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """Setup component logging"""
        log_level = getattr(logging, self.config.log_level, logging.INFO)
        logger.setLevel(log_level)

    def initialize(self) -> bool:
        """
        Initialize the component

        Returns:
            bool: True if initialization successful
        """
        try:
            self.status = MerovingianCoreComponentStatus.INITIALIZING
            logger.info("Initializing MerovingianCoreComponent...")

            # Load configuration if exists
            config_path = self.config_dir / "merovingian_core.json"
            if config_path.exists():
                self.config = MerovingianCoreComponentConfig.from_file(config_path)

            # Initialize event bus connection if available
            if self.event_bus:
                self._subscribe_to_events()

            # Component-specific initialization
            self._initialize_health_monitoring()
            self._initialize_diagnostics()

            self.status = MerovingianCoreComponentStatus.READY
            logger.info("MerovingianCoreComponent initialized successfully")

            # Publish initialization event
            if self.event_bus:
                self.event_bus.publish('floor.initialized', {
                    'floor': 'Merovingian',
                    'z_level': -4,
                    'component': 'MerovingianCoreComponent',
                    'timestamp': datetime.now().isoformat()
                })

            return True

        except Exception as e:
            self.status = MerovingianCoreComponentStatus.ERROR
            logger.error(f"Failed to initialize: {e}")
            return False

    def _initialize_health_monitoring(self):
        """Initialize system health monitoring"""
        logger.info("Initializing health monitoring...")
        # Health monitoring initialization logic here
        pass

    def _initialize_diagnostics(self):
        """Initialize diagnostics system"""
        logger.info("Initializing diagnostics...")
        # Diagnostics initialization logic here
        pass

    def _subscribe_to_events(self):
        """Subscribe to event bus events"""
        if not self.event_bus:
            return

        # Subscribe to system events
        self.event_bus.subscribe('system.*', self._handle_system_event)
        self.event_bus.subscribe('floor.*', self._handle_floor_event)

    def _handle_system_event(self, event_data: Dict[str, Any]):
        """Handle system events"""
        logger.debug(f"Received system event: {event_data}")

    def _handle_floor_event(self, event_data: Dict[str, Any]):
        """Handle floor events"""
        logger.debug(f"Received floor event: {event_data}")

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute component operation

        Returns:
            dict: Execution result with status and data
        """
        if self.status not in [MerovingianCoreComponentStatus.READY, MerovingianCoreComponentStatus.RUNNING]:
            return {'success': False, 'error': 'Component not ready'}

        try:
            self.status = MerovingianCoreComponentStatus.RUNNING
            start_time = datetime.now()

            # Component execution logic here
            result = self._perform_operation(**kwargs)

            # Record success
            duration = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics.record_success(duration)

            self.status = MerovingianCoreComponentStatus.READY
            return {'success': True, 'result': result}

        except Exception as e:
            self.metrics.record_failure()
            self.status = MerovingianCoreComponentStatus.ERROR
            logger.error(f"Execution failed: {e}")
            return {'success': False, 'error': str(e)}

    def _perform_operation(self, **kwargs) -> Any:
        """Perform component-specific operation"""
        # Operation logic here
        return {'message': 'Operation completed'}

    def get_status(self) -> Dict[str, Any]:
        """
        Get component status

        Returns:
            dict: Current status and metrics
        """
        uptime = (datetime.now() - self.start_time).total_seconds()
        self.metrics.uptime_seconds = uptime

        return {
            'status': self.status.value,
            'metrics': self.metrics.to_dict(),
            'config': self.config.to_dict(),
            'uptime_seconds': uptime
        }

    def pause(self):
        """Pause component execution"""
        if self.status == MerovingianCoreComponentStatus.RUNNING:
            self.status = MerovingianCoreComponentStatus.PAUSED
            logger.info("Component paused")

    def resume(self):
        """Resume component execution"""
        if self.status == MerovingianCoreComponentStatus.PAUSED:
            self.status = MerovingianCoreComponentStatus.READY
            logger.info("Component resumed")

    def stop(self):
        """Stop component"""
        self.status = MerovingianCoreComponentStatus.STOPPED
        logger.info("Component stopped")

    def record_success(self, duration_ms: float = 0.0):
        """Record successful operation"""
        self.metrics.record_success(duration_ms)

    def record_failure(self):
        """Record failed operation"""
        self.metrics.record_failure()

    @classmethod
    def from_dict(cls, data: Dict[str, Any], lightspeed_root: Path) -> 'MerovingianCoreComponent':
        """Create component from dictionary"""
        config = MerovingianCoreComponentConfig.from_dict(data.get('config', {}))
        return cls(lightspeed_root, config)

    @classmethod
    def from_file(cls, file_path: Path, lightspeed_root: Path) -> 'MerovingianCoreComponent':
        """Load component from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data, lightspeed_root)

    def save_to_file(self, file_path: Path) -> bool:
        """Save component state to JSON file"""
        try:
            data = {
                'status': self.status.value,
                'config': self.config.to_dict(),
                'metrics': self.metrics.to_dict()
            }
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save to file: {e}")
            return False


if __name__ == '__main__':
    # Test component
    import sys
    from pathlib import Path

    # Get LightSpeed root
    current_file = Path(__file__).resolve()
    lightspeed_root = current_file.parents[3]

    print("Testing MerovingianCoreComponent...")
    print(f"LightSpeed Root: {lightspeed_root}")

    # Create component
    component = MerovingianCoreComponent(lightspeed_root)

    # Initialize
    if component.initialize():
        print("[OK] Component initialized")

        # Execute
        result = component.execute()
        print(f"[OK] Execution result: {result}")

        # Get status
        status = component.get_status()
        print(f"[OK] Status: {status['status']}")
        print(f"[OK] Success rate: {status['metrics']['success_rate']:.1f}%")
    else:
        print("[ERROR] Failed to initialize component")
