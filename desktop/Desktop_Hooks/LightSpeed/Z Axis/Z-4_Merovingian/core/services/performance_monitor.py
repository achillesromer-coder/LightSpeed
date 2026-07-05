#!/usr/bin/env python
"""
Performance Monitor - Real-time System Analytics
LightSpeed Type I Civilization Platform

Comprehensive performance monitoring system that tracks:
- Response times for all operations
- Memory and CPU usage
- Event bus throughput
- Database query performance
- API endpoint latencies
- Floor-specific metrics
- Automatic alerts and thresholds

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 11, 2026
"""

from __future__ import annotations

import time
import psutil
import threading
import functools
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque
from enum import Enum
import json
from pathlib import Path


class MetricType(Enum):
    """Types of metrics tracked"""
    RESPONSE_TIME = "response_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    EVENT_COUNT = "event_count"
    DATABASE_QUERY = "database_query"
    API_LATENCY = "api_latency"
    CACHE_HIT_RATE = "cache_hit_rate"
    ERROR_RATE = "error_rate"


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Single performance metric data point"""
    metric_type: MetricType
    value: float
    timestamp: datetime
    floor: Optional[str] = None
    operation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """Performance alert triggered by threshold"""
    level: AlertLevel
    message: str
    metric_type: MetricType
    value: float
    threshold: float
    timestamp: datetime
    floor: Optional[str] = None


class MetricAggregator:
    """Aggregates metrics for statistical analysis"""

    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.samples: deque = deque(maxlen=max_samples)

    def add_sample(self, value: float):
        """Add a sample value"""
        self.samples.append(value)

    def get_statistics(self) -> Dict[str, float]:
        """Calculate statistics from samples"""
        if not self.samples:
            return {
                'count': 0,
                'min': 0.0,
                'max': 0.0,
                'mean': 0.0,
                'median': 0.0,
                'p95': 0.0,
                'p99': 0.0
            }

        sorted_samples = sorted(self.samples)
        count = len(sorted_samples)

        return {
            'count': count,
            'min': sorted_samples[0],
            'max': sorted_samples[-1],
            'mean': sum(sorted_samples) / count,
            'median': sorted_samples[count // 2],
            'p95': sorted_samples[int(count * 0.95)] if count > 0 else 0.0,
            'p99': sorted_samples[int(count * 0.99)] if count > 0 else 0.0
        }


class PerformanceMonitor:
    """
    Central performance monitoring system

    Tracks system-wide performance metrics and provides
    real-time analytics, alerting, and reporting.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".lightspeed" / "performance"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Metric storage
        self.metrics: List[PerformanceMetric] = []
        self.alerts: List[PerformanceAlert] = []

        # Aggregators per metric type
        self.aggregators: Dict[str, MetricAggregator] = defaultdict(MetricAggregator)

        # Thresholds for alerts
        self.thresholds: Dict[MetricType, Dict[AlertLevel, float]] = {
            MetricType.RESPONSE_TIME: {
                AlertLevel.WARNING: 1.0,  # seconds
                AlertLevel.ERROR: 3.0,
                AlertLevel.CRITICAL: 5.0
            },
            MetricType.MEMORY_USAGE: {
                AlertLevel.WARNING: 70.0,  # percentage
                AlertLevel.ERROR: 85.0,
                AlertLevel.CRITICAL: 95.0
            },
            MetricType.CPU_USAGE: {
                AlertLevel.WARNING: 70.0,  # percentage
                AlertLevel.ERROR: 85.0,
                AlertLevel.CRITICAL: 95.0
            },
            MetricType.ERROR_RATE: {
                AlertLevel.WARNING: 1.0,  # percentage
                AlertLevel.ERROR: 5.0,
                AlertLevel.CRITICAL: 10.0
            }
        }

        # System monitoring
        self.process = psutil.Process()
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None

        # Performance history (last 24 hours)
        self.max_history_age = timedelta(hours=24)

        # Lock for thread safety
        self.lock = threading.Lock()

    def record_metric(self, metric_type: MetricType, value: float,
                     floor: Optional[str] = None, operation: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            floor=floor,
            operation=operation,
            metadata=metadata or {}
        )

        with self.lock:
            self.metrics.append(metric)

            # Add to aggregator
            key = f"{metric_type.value}:{floor or 'global'}:{operation or 'all'}"
            self.aggregators[key].add_sample(value)

            # Check thresholds
            self._check_thresholds(metric)

            # Clean old metrics
            self._clean_old_metrics()

    def _check_thresholds(self, metric: PerformanceMetric):
        """Check if metric exceeds thresholds"""
        if metric.metric_type not in self.thresholds:
            return

        thresholds = self.thresholds[metric.metric_type]

        # Check from highest to lowest severity
        for level in [AlertLevel.CRITICAL, AlertLevel.ERROR, AlertLevel.WARNING]:
            if level in thresholds and metric.value >= thresholds[level]:
                alert = PerformanceAlert(
                    level=level,
                    message=f"{metric.metric_type.value} exceeded {level.value} threshold",
                    metric_type=metric.metric_type,
                    value=metric.value,
                    threshold=thresholds[level],
                    timestamp=metric.timestamp,
                    floor=metric.floor
                )

                with self.lock:
                    self.alerts.append(alert)

                # Trigger alert handler
                self._handle_alert(alert)
                break

    def _handle_alert(self, alert: PerformanceAlert):
        """Handle performance alert"""
        # Log alert
        print(f"[PerformanceMonitor] [{alert.level.value.upper()}] {alert.message}")
        print(f"  Value: {alert.value:.2f}, Threshold: {alert.threshold:.2f}")
        if alert.floor:
            print(f"  Floor: {alert.floor}")

        # Could publish to event bus for dashboard display
        try:
            from .event_bus import get_event_bus, EventTypes
            event_bus = get_event_bus()
            event_bus.publish(
                EventTypes.SYSTEM_ALERT,
                {
                    'level': alert.level.value,
                    'message': alert.message,
                    'metric_type': alert.metric_type.value,
                    'value': alert.value,
                    'threshold': alert.threshold,
                    'floor': alert.floor
                }
            )
        except:
            pass

    def _clean_old_metrics(self):
        """Remove metrics older than max_history_age"""
        cutoff_time = datetime.now() - self.max_history_age

        with self.lock:
            self.metrics = [m for m in self.metrics if m.timestamp > cutoff_time]
            self.alerts = [a for a in self.alerts if a.timestamp > cutoff_time]

    def get_statistics(self, metric_type: MetricType,
                      floor: Optional[str] = None,
                      operation: Optional[str] = None) -> Dict[str, float]:
        """Get statistics for specific metric"""
        key = f"{metric_type.value}:{floor or 'global'}:{operation or 'all'}"

        with self.lock:
            if key in self.aggregators:
                return self.aggregators[key].get_statistics()

        return {
            'count': 0,
            'min': 0.0,
            'max': 0.0,
            'mean': 0.0,
            'median': 0.0,
            'p95': 0.0,
            'p99': 0.0
        }

    def get_recent_metrics(self, metric_type: Optional[MetricType] = None,
                          floor: Optional[str] = None,
                          limit: int = 100) -> List[PerformanceMetric]:
        """Get recent metrics with optional filtering"""
        with self.lock:
            filtered = self.metrics

            if metric_type:
                filtered = [m for m in filtered if m.metric_type == metric_type]

            if floor:
                filtered = [m for m in filtered if m.floor == floor]

            # Return most recent first
            return sorted(filtered, key=lambda m: m.timestamp, reverse=True)[:limit]

    def get_recent_alerts(self, level: Optional[AlertLevel] = None,
                         limit: int = 50) -> List[PerformanceAlert]:
        """Get recent alerts"""
        with self.lock:
            filtered = self.alerts

            if level:
                filtered = [a for a in filtered if a.level == level]

            return sorted(filtered, key=lambda a: a.timestamp, reverse=True)[:limit]

    def start_system_monitoring(self, interval: float = 5.0):
        """Start continuous system monitoring"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_system,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        print(f"[PerformanceMonitor] System monitoring started (interval: {interval}s)")

    def stop_system_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        print("[PerformanceMonitor] System monitoring stopped")

    def _monitor_system(self, interval: float):
        """Background system monitoring"""
        while self.monitoring:
            try:
                # CPU usage
                cpu_percent = self.process.cpu_percent(interval=0.1)
                self.record_metric(MetricType.CPU_USAGE, cpu_percent)

                # Memory usage
                memory_info = self.process.memory_info()
                memory_percent = self.process.memory_percent()
                self.record_metric(
                    MetricType.MEMORY_USAGE,
                    memory_percent,
                    metadata={
                        'rss_mb': memory_info.rss / (1024 * 1024),
                        'vms_mb': memory_info.vms / (1024 * 1024)
                    }
                )

            except Exception as e:
                print(f"[PerformanceMonitor] Monitoring error: {e}")

            time.sleep(interval)

    def get_floor_performance(self, floor: str) -> Dict[str, Any]:
        """Get performance summary for specific floor"""
        metrics_by_type = {}

        for metric_type in MetricType:
            stats = self.get_statistics(metric_type, floor=floor)
            if stats['count'] > 0:
                metrics_by_type[metric_type.value] = stats

        # Recent alerts for floor
        floor_alerts = [a for a in self.alerts if a.floor == floor]
        recent_alerts = sorted(floor_alerts, key=lambda a: a.timestamp, reverse=True)[:10]

        return {
            'floor': floor,
            'metrics': metrics_by_type,
            'recent_alerts': [
                {
                    'level': a.level.value,
                    'message': a.message,
                    'timestamp': a.timestamp.isoformat()
                }
                for a in recent_alerts
            ]
        }

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        # Count alerts by level in last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_alerts = [a for a in self.alerts if a.timestamp > one_hour_ago]

        alerts_by_level = {level.value: 0 for level in AlertLevel}
        for alert in recent_alerts:
            alerts_by_level[alert.level.value] += 1

        # Current system metrics
        cpu_stats = self.get_statistics(MetricType.CPU_USAGE)
        memory_stats = self.get_statistics(MetricType.MEMORY_USAGE)

        # Determine overall health
        health_status = "healthy"
        if alerts_by_level['critical'] > 0:
            health_status = "critical"
        elif alerts_by_level['error'] > 5:
            health_status = "degraded"
        elif alerts_by_level['warning'] > 10:
            health_status = "warning"

        return {
            'status': health_status,
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_mean': cpu_stats.get('mean', 0.0),
                'cpu_p95': cpu_stats.get('p95', 0.0),
                'memory_mean': memory_stats.get('mean', 0.0),
                'memory_p95': memory_stats.get('p95', 0.0)
            },
            'alerts_last_hour': alerts_by_level,
            'total_metrics': len(self.metrics),
            'total_alerts': len(self.alerts)
        }

    def export_report(self, output_path: Optional[Path] = None) -> Path:
        """Export performance report to JSON"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.storage_path / f"performance_report_{timestamp}.json"

        report = {
            'generated_at': datetime.now().isoformat(),
            'system_health': self.get_system_health(),
            'statistics': {},
            'recent_alerts': [
                {
                    'level': a.level.value,
                    'message': a.message,
                    'metric_type': a.metric_type.value,
                    'value': a.value,
                    'timestamp': a.timestamp.isoformat()
                }
                for a in self.get_recent_alerts(limit=100)
            ]
        }

        # Add statistics for each metric type
        for metric_type in MetricType:
            stats = self.get_statistics(metric_type)
            if stats['count'] > 0:
                report['statistics'][metric_type.value] = stats

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"[PerformanceMonitor] Report exported to {output_path}")
        return output_path


def monitor_performance(metric_type: MetricType = MetricType.RESPONSE_TIME,
                       floor: Optional[str] = None,
                       operation: Optional[str] = None):
    """
    Decorator to monitor function performance

    Usage:
        @monitor_performance(MetricType.RESPONSE_TIME, floor='Neo')
        def my_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error_occurred = False

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error_occurred = True
                raise
            finally:
                elapsed = time.time() - start_time

                # Record response time
                monitor = get_performance_monitor()
                monitor.record_metric(
                    metric_type,
                    elapsed,
                    floor=floor,
                    operation=operation or func.__name__,
                    metadata={'error': error_occurred}
                )

        return wrapper
    return decorator


# Singleton instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


if __name__ == "__main__":
    # Test performance monitoring
    print("Performance Monitor Test")
    print("=" * 60)

    monitor = get_performance_monitor()

    # Start system monitoring
    print("\nStarting system monitoring...")
    monitor.start_system_monitoring(interval=1.0)

    # Simulate some operations
    print("\nSimulating operations...")

    @monitor_performance(MetricType.RESPONSE_TIME, floor='Neo', operation='ai_request')
    def simulate_ai_request():
        time.sleep(0.5)

    @monitor_performance(MetricType.DATABASE_QUERY, floor='Architect', operation='load_tasks')
    def simulate_db_query():
        time.sleep(0.1)

    # Run simulations
    for i in range(10):
        simulate_ai_request()
        simulate_db_query()

        # Simulate some errors
        if i % 3 == 0:
            monitor.record_metric(
                MetricType.ERROR_RATE,
                2.5,
                floor='Oracle',
                operation='prediction'
            )

    # Wait for system monitoring
    time.sleep(3)

    # Get statistics
    print("\n\nPerformance Statistics:")
    print("-" * 60)

    ai_stats = monitor.get_statistics(
        MetricType.RESPONSE_TIME,
        floor='Neo',
        operation='ai_request'
    )
    print(f"\nNeo AI Request Stats:")
    print(f"  Count: {ai_stats['count']}")
    print(f"  Mean: {ai_stats['mean']:.3f}s")
    print(f"  P95: {ai_stats['p95']:.3f}s")
    print(f"  P99: {ai_stats['p99']:.3f}s")

    db_stats = monitor.get_statistics(
        MetricType.DATABASE_QUERY,
        floor='Architect',
        operation='load_tasks'
    )
    print(f"\nArchitect Database Query Stats:")
    print(f"  Count: {db_stats['count']}")
    print(f"  Mean: {db_stats['mean']:.3f}s")
    print(f"  P95: {db_stats['p95']:.3f}s")

    # System health
    print("\n\nSystem Health:")
    print("-" * 60)
    health = monitor.get_system_health()
    print(f"Status: {health['status']}")
    print(f"CPU Mean: {health['system']['cpu_mean']:.1f}%")
    print(f"Memory Mean: {health['system']['memory_mean']:.1f}%")
    print(f"Alerts (last hour): {health['alerts_last_hour']}")

    # Recent alerts
    print("\n\nRecent Alerts:")
    print("-" * 60)
    alerts = monitor.get_recent_alerts(limit=5)
    for alert in alerts:
        print(f"[{alert.level.value.upper()}] {alert.message}")
        print(f"  Value: {alert.value:.2f}, Threshold: {alert.threshold:.2f}")

    # Export report
    print("\n\nExporting report...")
    report_path = monitor.export_report()
    print(f"Report saved to: {report_path}")

    # Stop monitoring
    monitor.stop_system_monitoring()

    print("\n" + "=" * 60)
    print("Performance monitoring system ready!")
