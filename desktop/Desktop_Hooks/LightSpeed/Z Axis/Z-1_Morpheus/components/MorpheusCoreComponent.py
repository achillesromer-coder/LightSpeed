"""
MorpheusCoreComponent - Core floor component
Morpheus Floor Component

{DETAILED_DESCRIPTION}

Floor: Morpheus
Z-Level: -1
Author: LightSpeed Team
Version: 0.9.5
Date: 2026-01-12
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


class MorpheusCoreComponentStatus(Enum):
    """Component operational status"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class MorpheusCoreComponentConfig:
    """Configuration for MorpheusCoreComponent"""
    enabled: bool = True
    auto_start: bool = False
    log_level: str = "INFO"
    cache_enabled: bool = True
    max_retries: int = 3
    timeout_seconds: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MorpheusCoreComponentConfig':
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
    def from_file(cls, config_path: Path) -> 'MorpheusCoreComponentConfig':
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
class MorpheusCoreComponentMetrics:
    """Performance metrics for MorpheusCoreComponent"""
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


class MorpheusCoreComponent:
    """
    Core floor component

    This component provides:
    - Floor initialization
    - Event bus integration
    - State management

    Floor Integration:
    - Publishes events to Event Bus: floor.initialized, floor.updated, floor.error
    - Subscribes to events: system.*
    - Depends on: EventBus, Logger

    Usage:
        >>> component = MorpheusCoreComponent(lightspeed_root)
        >>> component.initialize()
        >>> result = component.execute()
    """

    def __init__(
        self,
        lightspeed_root: Path,
        config: Optional[MorpheusCoreComponentConfig] = None,
        event_bus: Optional[Any] = None
    ):
        """
        Initialize MorpheusCoreComponent

        Parameters:
            lightspeed_root: Path to LightSpeed installation
            config: Component configuration (uses defaults if None)
            event_bus: Reference to floor event bus
        """
        self.lightspeed_root = Path(lightspeed_root)
        self.config = config or MorpheusCoreComponentConfig()
        self.event_bus = event_bus

        # State management
        self.status = MorpheusCoreComponentStatus.UNINITIALIZED
        self.metrics = MorpheusCoreComponentMetrics()
        self.start_time = datetime.now()

        # Component-specific paths
        self.floor_dir = self.lightspeed_root / "Z Axis" / "Z-1_Morpheus"
        self.data_dir = self.floor_dir / "data" / "morpheuscorecomponent"
        self.cache_dir = self.floor_dir / "cache" / "morpheuscorecomponent"
        self.config_dir = self.floor_dir / "config"

        # Ensure directories exist
        self._create_directories()

        # Configure logging
        self._setup_logging()

        logger.info(f"MorpheusCoreComponent instantiated")

    def _create_directories(self):
        """Create required directories"""
        for directory in [self.data_dir, self.cache_dir, self.config_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """Configure component logging"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logger.setLevel(log_level)

        # Create file handler if not already present
        log_file = self.floor_dir / "logs" / f"morpheuscorecomponent.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logger.addHandler(file_handler)

    def initialize(self) -> bool:
        """
        Initialize component and prepare for operation

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info(f"Initializing MorpheusCoreComponent...")
            self.status = MorpheusCoreComponentStatus.INITIALIZING

            # Load configuration
            config_path = self.config_dir / "morpheuscorecomponent_config.json"
            if config_path.exists():
                self.config = MorpheusCoreComponentConfig.from_file(config_path)
                logger.info("Configuration loaded from file")

            # Check if enabled
            if not self.config.enabled:
                logger.warning(f"MorpheusCoreComponent is disabled in configuration")
                self.status = MorpheusCoreComponentStatus.STOPPED
                return False

            # Perform component-specific initialization
            success = self._initialize_component()

            if success:
                self.status = MorpheusCoreComponentStatus.READY
                logger.info(f"MorpheusCoreComponent initialized successfully")

                # Publish initialization event
                if self.event_bus:
                    self._publish_event(
                        event_type="morpheuscorecomponent.initialized",
                        data={'status': 'ready', 'timestamp': datetime.now().isoformat()}
                    )
            else:
                self.status = MorpheusCoreComponentStatus.ERROR
                logger.error(f"MorpheusCoreComponent initialization failed")

            return success

        except Exception as e:
            logger.error(f"Initialization error: {e}", exc_info=True)
            self.status = MorpheusCoreComponentStatus.ERROR
            return False

    def _initialize_component(self) -> bool:
        """
        Component-specific initialization logic
        Default behavior: lightweight health/status reporter.

        Returns:
            True if successful, False otherwise
        """
        # Morpheus' domain logic lives in `Z Axis/Morpheus.py` and floor components.
        # This core component exists as a stable manifest provider with safe defaults.
        try:
            if self.event_bus and hasattr(self.event_bus, "subscribe"):
                try:
                    self.event_bus.subscribe(
                        "system.health.check",
                        lambda _evt=None: self._publish_event(
                            event_type="morpheuscorecomponent.health.status",
                            data=self.get_status(),
                        ),
                    )
                except TypeError:
                    pass
        except Exception:
            pass
        return True

    def execute(self, *args, **kwargs) -> Any:
        """
        Execute primary component operation

        Returns:
            Operation result
        """
        if self.status != MorpheusCoreComponentStatus.READY:
            logger.error(f"Cannot execute: component status is {self.status.value}")
            return None

        try:
            self.status = MorpheusCoreComponentStatus.RUNNING
            start_time = datetime.now()

            # Perform operation
            result = self._execute_operation(*args, **kwargs)

            # Record metrics
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics.record_success(duration_ms)

            self.status = MorpheusCoreComponentStatus.READY
            logger.info(f"Operation completed in {duration_ms:.2f}ms")

            # Publish completion event
            if self.event_bus:
                self._publish_event(
                    event_type="morpheuscorecomponent.operation_complete",
                    data={
                        'duration_ms': duration_ms,
                        'timestamp': datetime.now().isoformat()
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Execution error: {e}", exc_info=True)
            self.metrics.record_failure()
            self.status = MorpheusCoreComponentStatus.ERROR

            # Publish error event
            if self.event_bus:
                self._publish_event(
                    event_type="morpheuscorecomponent.error",
                    data={'error': str(e), 'timestamp': datetime.now().isoformat()}
                )

            return None

    def _execute_operation(self, *args, **kwargs) -> Any:
        """
        Component-specific operation logic
        Default behavior: small command router (no heavy side-effects).

        Returns:
            Operation result
        """
        operation = kwargs.get("operation") if isinstance(kwargs, dict) else None
        if not operation and args:
            operation = str(args[0])
        operation = (operation or "status").lower().strip()

        if operation in {"status", "get_status", "health"}:
            return self.get_status()
        if operation in {"ping", "noop"}:
            return {"ok": True, "component": "MorpheusCoreComponent", "floor": "Morpheus"}

        return {
            "ok": False,
            "component": "MorpheusCoreComponent",
            "floor": "Morpheus",
            "error": "unknown_operation",
            "operation": operation,
        }

    def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish event to floor event bus"""
        if not self.event_bus:
            return

        try:
            event = {
                'type': event_type,
                'source': 'Morpheus',
                'component': 'MorpheusCoreComponent',
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            try:
                self.event_bus.publish(event_type, event)
            except TypeError:
                self.event_bus.publish(event)
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get component status and metrics

        Returns:
            Dictionary with status information
        """
        self.metrics.uptime_seconds = (datetime.now() - self.start_time).total_seconds()

        return {
            'component': 'MorpheusCoreComponent',
            'floor': 'Morpheus',
            'z_level': -1,
            'status': self.status.value,
            'enabled': self.config.enabled,
            'metrics': self.metrics.to_dict(),
            'uptime_seconds': self.metrics.uptime_seconds
        }

    def pause(self):
        """Pause component operation"""
        if self.status == MorpheusCoreComponentStatus.RUNNING:
            self.status = MorpheusCoreComponentStatus.PAUSED
            logger.info(f"MorpheusCoreComponent paused")

    def resume(self):
        """Resume component operation"""
        if self.status == MorpheusCoreComponentStatus.PAUSED:
            self.status = MorpheusCoreComponentStatus.READY
            logger.info(f"MorpheusCoreComponent resumed")

    def stop(self):
        """Stop component and cleanup resources"""
        try:
            logger.info(f"Stopping MorpheusCoreComponent...")

            # Perform component-specific cleanup
            self._cleanup()

            self.status = MorpheusCoreComponentStatus.STOPPED
            logger.info(f"MorpheusCoreComponent stopped successfully")

            # Publish stop event
            if self.event_bus:
                self._publish_event(
                    event_type="morpheuscorecomponent.stopped",
                    data={'timestamp': datetime.now().isoformat()}
                )

        except Exception as e:
            logger.error(f"Error during stop: {e}", exc_info=True)

    def _cleanup(self):
        """
        Component-specific cleanup logic
        Override this method in implementation
        """
        pass

    def __repr__(self) -> str:
        return f"MorpheusCoreComponent(status={self.status.value}, floor=Morpheus)"


# Example usage
if __name__ == "__main__":
    # Setup logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Example: Create and test component
    lightspeed_root = Path(__file__).parents[3]  # Adjust based on location
    component = MorpheusCoreComponent(lightspeed_root)

    # Initialize
    if component.initialize():
        print(f"✓ MorpheusCoreComponent initialized successfully")

        # Execute operation
        result = component.execute()
        print(f"✓ Operation result: {result}")

        # Get status
        status = component.get_status()
        print(f"✓ Component status: {status}")

        # Stop
        component.stop()
        print(f"✓ MorpheusCoreComponent stopped")
    else:
        print(f"✗ MorpheusCoreComponent initialization failed")
