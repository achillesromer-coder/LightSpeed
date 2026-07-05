"""
Logger Service - 99.9% Fidelity System Tracking
LightSpeed Type I Civilization Platform

This service provides comprehensive logging with 99.9% fidelity tracking
of all system operations across all floors. Every action, event, and state
change is logged for audit, debugging, and compliance purposes.

Logging Architecture:
- Centralized logging across all Z-axis floors
- Multi-level logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Structured logging with JSON support
- Single weekly runtime log under the canonical generated tree
- Integration with Merovingian telemetry layer
- Real-time log streaming for Trinity dashboards

Author: LightSpeed Team / ACHILLES
Version: 0.9.5
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import sys
import traceback

# Create logs directory if it doesn't exist
try:
    from core.config.paths import GENERATED_LOGS  # type: ignore
    LOG_DIR = Path(GENERATED_LOGS)
except Exception:
    LOG_DIR = Path(__file__).resolve().parents[4] / "data" / "generated" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def _weekly_log_path(now: datetime | None = None) -> Path:
    stamp = now or datetime.now()
    year, week, _ = stamp.isocalendar()
    return LOG_DIR / f"lightspeed_{year}_W{week:02d}.jsonl"


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Converts log records to JSON for easy parsing and analysis.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Parameters:
            record: Log record to format

        Returns:
            JSON string
        """
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

        # Add extra fields
        if hasattr(record, 'floor'):
            log_data['floor'] = record.floor
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'extra_data'):
            log_data['extra_data'] = record.extra_data

        return json.dumps(log_data)


class FloorLogger:
    """
    Specialized logger for each floor with context tracking.

    Each floor (Neo, Morpheus, etc.) gets its own logger instance
    that automatically tags logs with floor information.
    """

    def __init__(self, floor_name: str, enable_db_logging: bool = True):
        """
        Initialize floor-specific logger.

        Parameters:
            floor_name: Name of floor (Neo, Morpheus, Architect, etc.)
            enable_db_logging: Whether to log to database (Merovingian layer)
        """
        self.floor_name = floor_name
        self.logger = logging.getLogger(f"lightspeed.{floor_name.lower()}")
        self.enable_db_logging = enable_db_logging

        # Set up handlers if not already configured
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """Configure log handlers for this floor."""
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        # Console handler (human-readable)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            f'%(asctime)s [{self.floor_name}] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # Single weekly structured runtime log for all floors.
        file_handler = logging.FileHandler(_weekly_log_path(), encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(file_handler)

    def _log_to_db(self, level: str, message: str, extra_data: Optional[Dict] = None):
        """
        Log to database (Merovingian layer) for centralized tracking.

        Parameters:
            level: Log level
            message: Log message
            extra_data: Additional context
        """
        if not self.enable_db_logging:
            return

        try:
            from .database import get_db
            db = get_db()
            db.log_system_event(
                level=level,
                source=self.floor_name,
                message=message,
                details=extra_data
            )
        except Exception as e:
            # Don't fail the application if DB logging fails
            self.logger.error(f"Failed to log to database: {e}")

    def debug(self, message: str, extra_data: Optional[Dict] = None):
        """Log debug message."""
        extra = {'floor': self.floor_name}
        if extra_data:
            extra['extra_data'] = extra_data
        self.logger.debug(message, extra=extra)

    def info(self, message: str, extra_data: Optional[Dict] = None):
        """Log info message."""
        extra = {'floor': self.floor_name}
        if extra_data:
            extra['extra_data'] = extra_data
        self.logger.info(message, extra=extra)
        self._log_to_db('INFO', message, extra_data)

    def warning(self, message: str, extra_data: Optional[Dict] = None):
        """Log warning message."""
        extra = {'floor': self.floor_name}
        if extra_data:
            extra['extra_data'] = extra_data
        self.logger.warning(message, extra=extra)
        self._log_to_db('WARNING', message, extra_data)

    def error(self, message: str, exc_info: bool = False, extra_data: Optional[Dict] = None):
        """Log error message."""
        extra = {'floor': self.floor_name}
        if extra_data:
            extra['extra_data'] = extra_data
        self.logger.error(message, exc_info=exc_info, extra=extra)
        self._log_to_db('ERROR', message, extra_data)

    def critical(self, message: str, exc_info: bool = False, extra_data: Optional[Dict] = None):
        """Log critical message."""
        extra = {'floor': self.floor_name}
        if extra_data:
            extra['extra_data'] = extra_data
        self.logger.critical(message, exc_info=exc_info, extra=extra)
        self._log_to_db('CRITICAL', message, extra_data)

    def operation(self, operation_name: str, status: str = "started",
                 duration_ms: Optional[float] = None, extra_data: Optional[Dict] = None):
        """
        Log system operation for 99.9% fidelity tracking.

        Parameters:
            operation_name: Name of operation
            status: started, completed, failed
            duration_ms: Duration in milliseconds (for completed operations)
            extra_data: Additional context
        """
        data = {
            'operation': operation_name,
            'status': status,
            'floor': self.floor_name
        }
        if duration_ms is not None:
            data['duration_ms'] = duration_ms
        if extra_data:
            data.update(extra_data)

        message = f"Operation: {operation_name} - {status}"
        if duration_ms:
            message += f" ({duration_ms:.2f}ms)"

        self.info(message, extra_data=data)


# ============================================================================
# GLOBAL LOGGER FACTORY
# ============================================================================

_floor_loggers: Dict[str, FloorLogger] = {}


def get_logger(floor_name: str = "System") -> FloorLogger:
    """
    Get logger for specific floor (singleton per floor).

    Parameters:
        floor_name: Floor name (Neo, Morpheus, Architect, etc.). Defaults to "System".

    Returns:
        FloorLogger instance
    """
    if floor_name not in _floor_loggers:
        _floor_loggers[floor_name] = FloorLogger(floor_name)
    return _floor_loggers[floor_name]


# ============================================================================
# CONVENIENCE LOGGERS FOR EACH FLOOR
# ============================================================================

def get_neo_logger() -> FloorLogger:
    """Get logger for Neo (Z+3): AI Integration."""
    return get_logger("Neo")


def get_morpheus_logger() -> FloorLogger:
    """Get logger for Morpheus (Z+2): Knowledge & File Analysis."""
    return get_logger("Morpheus")


def get_architect_logger() -> FloorLogger:
    """Get logger for Architect (Z+1): Time & Mission Planning."""
    return get_logger("Architect")


def get_construct_logger() -> FloorLogger:
    """Get logger for TheConstruct (Z0): Physics & Simulations."""
    return get_logger("TheConstruct")


def get_oracle_logger() -> FloorLogger:
    """Get logger for Oracle (Z-1): Archives & IP Vault."""
    return get_logger("Oracle")


def get_smith_logger() -> FloorLogger:
    """Get logger for Smith (Z-2): Background Jobs & SOPs."""
    return get_logger("Smith")


def get_merovingian_logger() -> FloorLogger:
    """Get logger for Merovingian (Z-3): Diagnostics & Telemetry."""
    return get_logger("Merovingian")


def get_trinity_logger() -> FloorLogger:
    """Get logger for Trinity: Dashboards."""
    return get_logger("Trinity")


def get_services_logger() -> FloorLogger:
    """Get logger for Services: Shared basement layer."""
    return get_logger("Services")


# ============================================================================
# OPERATION CONTEXT MANAGER (for automatic duration tracking)
# ============================================================================

class LoggedOperation:
    """
    Context manager for automatically logging operation start/end with duration.

    Usage:
        logger = get_neo_logger()
        with LoggedOperation(logger, "process_ai_prompt"):
            # Do work here
            result = ai_model.generate(prompt)
    """

    def __init__(self, logger: FloorLogger, operation_name: str,
                 extra_data: Optional[Dict] = None):
        """
        Initialize logged operation.

        Parameters:
            logger: Floor logger instance
            operation_name: Name of operation
            extra_data: Additional context
        """
        self.logger = logger
        self.operation_name = operation_name
        self.extra_data = extra_data or {}
        self.start_time = None

    def __enter__(self):
        """Log operation start."""
        self.start_time = datetime.now()
        self.logger.operation(self.operation_name, status="started",
                            extra_data=self.extra_data)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log operation completion with duration."""
        duration_ms = (datetime.now() - self.start_time).total_seconds() * 1000

        if exc_type is None:
            # Success
            self.logger.operation(self.operation_name, status="completed",
                                duration_ms=duration_ms, extra_data=self.extra_data)
        else:
            # Failure
            error_data = {**self.extra_data, 'error': str(exc_val)}
            self.logger.operation(self.operation_name, status="failed",
                                duration_ms=duration_ms, extra_data=error_data)
            self.logger.error(f"Operation failed: {self.operation_name}",
                            exc_info=True, extra_data=error_data)

        # Don't suppress exception
        return False


if __name__ == "__main__":
    # Test logging system
    print("Logger Service - 99.9% Fidelity Tracking Test")
    print("=" * 50)

    # Test 1: Neo logger
    print("\nTest 1: Neo (AI) floor logging")
    neo_logger = get_neo_logger()
    neo_logger.info("AI model initialized: Cognigrex v1.0")
    neo_logger.debug("Processing prompt with 150 tokens")
    neo_logger.warning("Token limit approaching (90% used)")

    # Test 2: TheConstruct logger
    print("\nTest 2: TheConstruct (Physics) floor logging")
    construct_logger = get_construct_logger()
    construct_logger.info("Raphael simulation started", extra_data={
        'sim_id': 42,
        'type': 'raphael',
        'mass': 1e30
    })

    # Test 3: Logged operation (automatic duration tracking)
    print("\nTest 3: Automatic operation tracking")
    architect_logger = get_architect_logger()

    with LoggedOperation(architect_logger, "create_mission_plan",
                        extra_data={'project_id': 5, 'phase': 'Phase I'}):
        import time
        time.sleep(0.1)  # Simulate work
        print("  (Simulated work: creating mission plan...)")

    # Test 4: Error logging
    print("\nTest 4: Error logging with traceback")
    try:
        result = 1 / 0
    except Exception as e:
        oracle_logger = get_oracle_logger()
        oracle_logger.error("Failed to process IP asset", exc_info=True,
                          extra_data={'asset_id': 123})

    # Test 5: Check log files
    print("\nTest 5: Log files created")
    log_files = list(LOG_DIR.glob("*.jsonl"))
    print(f"  Log directory: {LOG_DIR}")
    print(f"  Files created: {len(log_files)}")
    for log_file in log_files[:5]:
        print(f"    - {log_file.name}")

    print("\n" + "=" * 50)
    print("Logger service ready - 99.9% fidelity tracking active!")
    print(f"Logs stored in: {LOG_DIR}")
