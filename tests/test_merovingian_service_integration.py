"""Deterministic Merovingian service integration checks.

The superseded test opened a real WebSocket listener, initialized shared
database singletons and started monitor threads. Under the live soft-launch
topology it could leave a background resource running and never let pytest
terminate. These checks exercise the service boundary with in-memory fixtures
only: no port, live database, supervisor or healthy Merovingian process is
touched.
"""

from __future__ import annotations

from pathlib import Path
import sys


SERVICES_ROOT = (
    Path(__file__).resolve().parents[1]
    / "desktop"
    / "Desktop_Hooks"
    / "LightSpeed"
    / "Z Axis"
    / "Z-4_Merovingian"
    / "core"
    / "services"
)
sys.path.insert(0, str(SERVICES_ROOT))

from cache_manager import LRUCache
from event_bus import Event, EventBus


def test_event_bus_to_cache_round_trip_is_synchronous_and_bounded() -> None:
    bus = EventBus(max_history=4)
    cache = LRUCache(max_size=4, max_bytes=4096)
    received: list[str] = []

    def store_artifact(event: Event) -> None:
        cache.set(event.data["key"], event.data["value"], ttl=30)
        received.append(event.type)

    bus.subscribe("artifact.ready", store_artifact, floor="Merovingian")
    bus.publish(
        Event(
            type="artifact.ready",
            source="Smith",
            data={"key": "receipt-1", "value": {"status": "pass"}},
        ),
        async_mode=False,
    )

    assert received == ["artifact.ready"]
    assert cache.get("receipt-1") == {"status": "pass"}
    assert len(bus.get_event_history(limit=10)) == 1


def test_event_history_and_cache_capacity_remain_bounded() -> None:
    bus = EventBus(max_history=3)
    cache = LRUCache(max_size=2, max_bytes=4096)

    for index in range(5):
        cache.set(f"key-{index}", index)
        bus.publish(
            Event(
                type="health.sample",
                source="Merovingian",
                data={"index": index},
            ),
            async_mode=False,
        )

    history = bus.get_event_history(limit=10)
    assert [event.data["index"] for event in history] == [4, 3, 2]
    assert cache.get("key-0") is None
    assert cache.get("key-4") == 4
