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
import threading


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

import cache_manager as cache_module
import performance_monitor as performance_module
from cache_manager import CacheManager, LRUCache, cached
from event_bus import Event, EventBus
from performance_monitor import (
    AlertLevel,
    MetricType,
    PerformanceMonitor,
    monitor_performance,
)


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


def test_performance_recording_returns_updates_statistics_and_alerts(
    tmp_path: Path,
) -> None:
    monitor = PerformanceMonitor(storage_path=tmp_path / "performance")
    monitor._handle_alert = lambda alert: None
    finished = threading.Event()

    def record_critical_metric() -> None:
        monitor.record_metric(
            MetricType.RESPONSE_TIME,
            6.0,
            floor="Merovingian",
            operation="health-check",
        )
        finished.set()

    worker = threading.Thread(target=record_critical_metric, daemon=True)
    worker.start()
    worker.join(timeout=1.0)

    assert finished.is_set(), "record_metric deadlocked while checking thresholds"
    assert not worker.is_alive()
    assert monitor.get_statistics(
        MetricType.RESPONSE_TIME,
        floor="Merovingian",
        operation="health-check",
    ) == {
        "count": 1,
        "min": 6.0,
        "max": 6.0,
        "mean": 6.0,
        "median": 6.0,
        "p95": 6.0,
        "p99": 6.0,
    }
    assert len(monitor.alerts) == 1
    assert monitor.alerts[0].level is AlertLevel.CRITICAL


def test_cached_monitored_function_executes_once_and_records_cache_hit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cache = CacheManager(enable_disk_cache=False)
    monitor = PerformanceMonitor(storage_path=tmp_path / "performance")
    monitor._handle_alert = lambda alert: None
    monkeypatch.setattr(cache_module, "_cache_manager", cache)
    monkeypatch.setattr(performance_module, "_performance_monitor", monitor)
    calls = 0

    @cached(ttl=30, key_prefix="integration")
    @monitor_performance(
        MetricType.RESPONSE_TIME,
        floor="Merovingian",
        operation="bounded-compute",
    )
    def bounded_compute(value: int) -> int:
        nonlocal calls
        calls += 1
        return value * 2

    assert bounded_compute(21) == 42
    assert bounded_compute(21) == 42
    assert calls == 1

    cache_stats = cache.get_stats()["combined"]
    assert cache_stats["hits"] == 1
    assert cache_stats["misses"] == 1
    assert monitor.get_statistics(
        MetricType.RESPONSE_TIME,
        floor="Merovingian",
        operation="bounded-compute",
    )["count"] == 1
