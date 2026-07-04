"""
Event Bus - Inter-Floor Communication System
LightSpeed Type I Civilization Platform

The Event Bus enables seamless communication between all Z-axis floors,
allowing each specialized layer to publish and subscribe to events without
tight coupling. This forms the nervous system of the ACHILLES platform.

Floor Communication Architecture:
- Neo (Z+3) → Broadcasts AI insights to all floors
- Morpheus (Z+2) → Publishes file analysis events
- Architect (Z+1) → Emits task/mission updates
- TheConstruct (Z0) → Shares simulation results
- Oracle (Z-1) → Notifies IP changes
- Smith (Z-2) → Triggers background jobs
- Merovingian (Z-3) → Broadcasts system health
- Trinity → Aggregates for dashboard display

Author: LightSpeed Team / ACHILLES
Version: 0.9.5
"""

import logging
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """
    Event object passed between floors.

    Attributes:
        type: Event type (e.g., 'file.analyzed', 'task.completed')
        source: Originating floor (Neo, Morpheus, Architect, etc.)
        data: Event payload (any JSON-serializable data)
        timestamp: When event was created
        priority: Event priority (1=critical, 5=low)
        metadata: Additional context
    """
    type: str
    source: str
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    priority: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def topic(self) -> str:
        """Compatibility alias (some callers use `topic` instead of `type`)."""
        return self.type

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            'type': self.type,
            'source': self.source,
            'data': self.data,
            'timestamp': self.timestamp,
            'priority': self.priority,
            'metadata': self.metadata
        }

    def to_json(self) -> str:
        """Serialize event to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary."""
        return cls(**data)


class EventBus:
    """
    Central event bus for inter-floor communication.

    Implements publish-subscribe pattern with:
    - Type-based subscriptions (e.g., subscribe to 'file.*' events)
    - Priority-based delivery
    - Async event handling
    - Event history/audit trail
    - Floor-specific channels
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize event bus.

        Parameters:
            max_history: Maximum events to keep in history
        """
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_history: List[Event] = []
        self._max_history = max_history
        self._lock = threading.Lock()
        self._enabled = True

        logger.info("Event Bus initialized - Inter-floor communication active")

    def subscribe(self, event_type: str, handler: Callable[[Event], None],
                 floor: Optional[str] = None) -> str:
        """
        Subscribe to events of a specific type.

        Parameters:
            event_type: Event type pattern (supports wildcards: 'file.*')
            handler: Callback function to handle events
            floor: Floor name (for logging/debugging)

        Returns:
            Subscription ID (for later unsubscribe)

        Example:
            def on_file_analyzed(event):
                print(f"File analyzed: {event.data['filename']}")

            event_bus.subscribe('file.analyzed', on_file_analyzed, floor='Trinity')
        """
        with self._lock:
            subscription_id = f"{event_type}:{id(handler)}"
            self._subscribers[event_type].append(handler)
            floor_info = f" [{floor}]" if floor else ""
            logger.info(f"Subscribed to '{event_type}'{floor_info}")
            return subscription_id

    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]):
        """
        Unsubscribe from event type.

        Parameters:
            event_type: Event type to unsubscribe from
            handler: Handler function to remove
        """
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(handler)
                    logger.info(f"Unsubscribed from '{event_type}'")
                except ValueError:
                    logger.warning(f"Handler not found for '{event_type}'")

    def publish(self, event: Any, async_mode: bool = True):
        """
        Publish event to all subscribers.

        Primary form:
        - `publish(Event(...), async_mode=True)`

        Compatibility forms (legacy callers across the repository):
        - `publish({'type': 'x', 'source': 'y', 'data': {...}})`
        - `publish('event.type', {'k': 'v'})`  (second argument treated as data payload)

        Parameters:
            event: Event object or compatible payload
            async_mode: If True, handlers run in separate threads. When `event` is a string and
                        the second argument is a dict, this remains the async flag and defaults True.
        """
        if not self._enabled:
            logger.warning("Event bus is disabled, event not published")
            return

        # Normalize event payloads into an `Event` instance.
        # This keeps the platform resilient to mixed call-sites (older floors/portals).
        if isinstance(event, str):
            data = async_mode if isinstance(async_mode, dict) else {}
            async_mode = True if isinstance(async_mode, dict) else async_mode
            event = Event(type=event, source='system', data=data)
        elif isinstance(event, dict):
            # Prefer the canonical dict form (type/source/data) but tolerate partials.
            if 'type' in event and 'source' in event and 'data' in event:
                event = Event.from_dict(event)
            else:
                event = Event(
                    type=str(event.get('type', 'event.unknown')),
                    source=str(event.get('source', 'system')),
                    data=event.get('data') if isinstance(event.get('data'), dict) else {},
                    priority=int(event.get('priority', 3)) if str(event.get('priority', '')).isdigit() else 3,
                    metadata=event.get('metadata') if isinstance(event.get('metadata'), dict) else {},
                )
        elif not isinstance(event, Event):
            logger.error(f"Invalid event payload type: {type(event).__name__}")
            return

        # Add to history
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

        logger.debug(f"Publishing event: {event.type} from {event.source}")

        # Find matching subscribers
        handlers = self._get_matching_handlers(event.type)

        if not handlers:
            logger.debug(f"No subscribers for event type: {event.type}")
            return

        # Deliver to handlers
        for handler in handlers:
            try:
                if async_mode:
                    thread = threading.Thread(target=handler, args=(event,))
                    thread.daemon = True
                    thread.start()
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}", exc_info=True)

    def _get_matching_handlers(self, event_type: str) -> List[Callable]:
        """
        Get all handlers matching event type (supports wildcards).

        Parameters:
            event_type: Event type to match

        Returns:
            List of matching handler functions
        """
        handlers = []

        with self._lock:
            for pattern, pattern_handlers in self._subscribers.items():
                if self._matches_pattern(event_type, pattern):
                    handlers.extend(pattern_handlers)

        return handlers

    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """
        Check if event type matches subscription pattern.

        Supports wildcards:
        - 'file.*' matches 'file.analyzed', 'file.uploaded', etc.
        - '*' matches everything

        Parameters:
            event_type: Actual event type
            pattern: Subscription pattern

        Returns:
            True if matches
        """
        if pattern == '*':
            return True

        if pattern == event_type:
            return True

        if pattern.endswith('.*'):
            prefix = pattern[:-2]
            return event_type.startswith(prefix + '.')

        return False

    def get_event_history(self, event_type: Optional[str] = None,
                         source: Optional[str] = None,
                         limit: int = 100) -> List[Event]:
        """
        Retrieve event history (for debugging/audit).

        Parameters:
            event_type: Filter by event type
            source: Filter by source floor
            limit: Maximum events to return

        Returns:
            List of events (most recent first)
        """
        with self._lock:
            events = list(reversed(self._event_history))

        # Apply filters
        if event_type:
            events = [e for e in events if e.type == event_type]
        if source:
            events = [e for e in events if e.source == source]

        return events[:limit]

    def clear_history(self):
        """Clear event history."""
        with self._lock:
            self._event_history.clear()
        logger.info("Event history cleared")

    def enable(self):
        """Enable event bus."""
        self._enabled = True
        logger.info("Event bus enabled")

    def disable(self):
        """Disable event bus (stops publishing events)."""
        self._enabled = False
        logger.warning("Event bus disabled")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get event bus statistics.

        Returns:
            Dict with stats (subscribers, events, etc.)
        """
        with self._lock:
            total_subscribers = sum(len(handlers) for handlers in self._subscribers.values())
            event_types = list(self._subscribers.keys())

        return {
            'enabled': self._enabled,
            'total_subscribers': total_subscribers,
            'event_types': event_types,
            'history_size': len(self._event_history),
            'max_history': self._max_history
        }


# ============================================================================
# FLOOR-SPECIFIC EVENT HELPERS
# ============================================================================

class FloorEventPublisher:
    """
    Helper class for floor-specific event publishing.

    Each floor can create its own publisher instance for cleaner code.
    """

    def __init__(self, floor_name: str, event_bus: EventBus):
        """
        Initialize floor publisher.

        Parameters:
            floor_name: Name of floor (Neo, Morpheus, etc.)
            event_bus: Event bus instance
        """
        self.floor_name = floor_name
        self.event_bus = event_bus
        logger.info(f"Floor publisher initialized: {floor_name}")

    def publish(self, event_type: str, data: Dict[str, Any],
               priority: int = 3, metadata: Optional[Dict[str, Any]] = None):
        """
        Publish event from this floor.

        Parameters:
            event_type: Event type
            data: Event data
            priority: Event priority (1-5)
            metadata: Additional metadata
        """
        event = Event(
            type=event_type,
            source=self.floor_name,
            data=data,
            priority=priority,
            metadata=metadata or {}
        )
        self.event_bus.publish(event)


# ============================================================================
# STANDARD EVENT TYPES (across all floors)
# ============================================================================

class EventTypes:
    """Standard event type definitions for consistency."""

    # Neo (Z+3): AI Integration
    AI_PROMPT_RECEIVED = "ai.prompt.received"
    AI_RESPONSE_GENERATED = "ai.response.generated"
    COGNIGREX_INSIGHT = "ai.cognigrex.insight"

    # Morpheus (Z+2): File Analysis
    FILE_UPLOADED = "file.uploaded"
    FILE_ANALYZED = "file.analyzed"
    FILE_INDEXED = "file.indexed"

    # Architect (Z+1): Mission Planning
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    MISSION_PHASE_CHANGED = "mission.phase.changed"

    # TheConstruct (Z0): Physics
    SIMULATION_STARTED = "simulation.started"
    SIMULATION_COMPLETED = "simulation.completed"
    SIMULATION_FAILED = "simulation.failed"

    # Oracle (Z-1): IP Vault
    IP_REGISTERED = "ip.registered"
    DOCUMENT_ARCHIVED = "document.archived"
    SEARCH_PERFORMED = "search.performed"

    # Smith (Z-2): Background Jobs
    JOB_SCHEDULED = "job.scheduled"
    JOB_STARTED = "job.started"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"

    # Merovingian (Z-3): Telemetry
    SYSTEM_HEALTH_CHANGED = "system.health.changed"
    ALERT_TRIGGERED = "system.alert.triggered"
    TELEMETRY_RECORDED = "telemetry.recorded"

    # Trinity: Dashboard
    DASHBOARD_UPDATED = "dashboard.updated"
    NOTIFICATION_SENT = "notification.sent"


# Singleton instance
_event_bus = None

def get_event_bus() -> EventBus:
    """
    Get global event bus instance (singleton).

    Returns:
        EventBus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    else:
        # Tests and some CLI utilities may disable the global bus; default behavior of
        # `get_event_bus()` is to return an operational event bus.
        try:
            if not bool(_event_bus.get_stats().get("enabled")):
                _event_bus.enable()
        except Exception:
            pass
    return _event_bus


if __name__ == "__main__":
    # Test event bus
    print("Event Bus - Inter-Floor Communication Test")
    print("=" * 50)

    bus = get_event_bus()

    # Test 1: Subscribe and publish
    print("\nTest 1: Basic pub-sub")

    def on_simulation_complete(event: Event):
        print(f"  [Trinity] Received: {event.type} from {event.source}")
        print(f"  Data: {event.data}")

    bus.subscribe(EventTypes.SIMULATION_COMPLETED, on_simulation_complete, floor='Trinity')

    # TheConstruct publishes simulation result
    construct_publisher = FloorEventPublisher('TheConstruct', bus)
    construct_publisher.publish(
        EventTypes.SIMULATION_COMPLETED,
        data={'sim_id': 42, 'type': 'raphael', 'success': True}
    )

    import time
    time.sleep(0.1)  # Allow async handler to run

    # Test 2: Wildcard subscriptions
    print("\nTest 2: Wildcard subscriptions")

    event_count = {'count': 0}

    def on_any_task_event(event: Event):
        event_count['count'] += 1

    bus.subscribe('task.*', on_any_task_event, floor='Merovingian')

    architect_publisher = FloorEventPublisher('Architect', bus)
    architect_publisher.publish('task.created', {'task_id': 1, 'title': 'Test Task'})
    architect_publisher.publish('task.updated', {'task_id': 1, 'status': 'in_progress'})
    architect_publisher.publish('task.completed', {'task_id': 1, 'success': True})

    time.sleep(0.1)
    print(f"  Received {event_count['count']} task events (expected: 3)")

    # Test 3: Event history
    print("\nTest 3: Event history")
    history = bus.get_event_history(limit=5)
    print(f"  Total events in history: {len(history)}")
    for event in history[:3]:
        print(f"    - {event.type} from {event.source}")

    # Test 4: Stats
    print("\nTest 4: Event bus statistics")
    stats = bus.get_stats()
    print(f"  Enabled: {stats['enabled']}")
    print(f"  Subscribers: {stats['total_subscribers']}")
    print(f"  Event types: {len(stats['event_types'])}")
    print(f"  History size: {stats['history_size']}")

    print("\n" + "=" * 50)
    print("Event bus ready for seamless inter-floor communication!")
