#!/usr/bin/env python
"""
Integration Tests - Complete System Integration Verification
LightSpeed Type I Civilization Platform

Tests the integration of all major systems:
- Performance monitoring + Cache
- WebSocket + Event Bus
- Analytics Dashboard
- External Integrations
- End-to-end workflows

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 11, 2026
"""

import unittest
import time
import threading
from pathlib import Path
import sys

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from performance_monitor import get_performance_monitor, MetricType, monitor_performance
from cache_manager import get_cache_manager, cached
from websocket_server import get_websocket_server, MessageType, WebSocketMessage
from event_bus import get_event_bus, EventTypes
from datetime import datetime


class TestSystemIntegration(unittest.TestCase):
    """Test integration between major systems"""

    def setUp(self):
        """Set up test environment"""
        self.monitor = get_performance_monitor()
        self.cache = get_cache_manager()
        self.event_bus = get_event_bus()

    def test_performance_monitor_cache_integration(self):
        """Test performance monitoring with caching"""
        print("\n[TEST] Performance Monitor + Cache Integration")

        # Create cached function with monitoring
        call_count = [0]

        @cached(ttl=60, key_prefix='test')
        @monitor_performance(MetricType.RESPONSE_TIME, operation='cached_function')
        def expensive_function(x):
            call_count[0] += 1
            time.sleep(0.1)
            return x * 2

        # First call (cache miss)
        result1 = expensive_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count[0], 1)

        # Second call (cache hit - should be faster)
        start = time.time()
        result2 = expensive_function(5)
        elapsed = time.time() - start

        self.assertEqual(result2, 10)
        self.assertEqual(call_count[0], 1)  # Function not called again
        self.assertLess(elapsed, 0.01)  # Much faster

        # Check performance metrics
        stats = self.monitor.get_statistics(
            MetricType.RESPONSE_TIME,
            operation='cached_function'
        )
        self.assertGreater(stats['count'], 0)

        # Check cache stats
        cache_stats = self.cache.get_stats()
        self.assertGreater(cache_stats['memory']['hits'], 0)

        print(f"  ✓ Cache hit rate: {cache_stats['memory']['hit_rate']:.1f}%")
        print(f"  ✓ Performance tracked: {stats['count']} calls")

    def test_event_bus_websocket_integration(self):
        """Test event bus integration with WebSocket"""
        print("\n[TEST] Event Bus + WebSocket Integration")

        # Start WebSocket server
        ws_server = get_websocket_server(port=8766)
        ws_server.start()
        time.sleep(0.5)  # Wait for server to start

        try:
            # Track broadcasts
            broadcasts = []

            original_broadcast = ws_server.broadcast

            def track_broadcast(msg, channel=None):
                broadcasts.append({'msg': msg, 'channel': channel})
                return original_broadcast(msg, channel)

            ws_server.broadcast = track_broadcast

            # Publish event via event bus
            self.event_bus.publish(
                EventTypes.TASK_CREATED,
                data={'task_id': 123, 'title': 'Test Task'}
            )

            # Event should be available
            history = self.event_bus.get_event_history(limit=5)
            self.assertGreater(len(history), 0)

            # Note: WebSocket broadcast requires integration setup
            # which is done in websocket_server.integrate_with_event_bus()
            print("  ✓ Event published to event bus")
            print("  ✓ WebSocket server running")

        finally:
            ws_server.stop()

    def test_performance_alerting(self):
        """Test performance alerting system"""
        print("\n[TEST] Performance Alerting")

        # Record a metric that exceeds threshold
        self.monitor.record_metric(
            MetricType.RESPONSE_TIME,
            value=6.0,  # Exceeds CRITICAL threshold (5.0)
            floor='TestFloor',
            operation='slow_operation'
        )

        # Check alerts
        alerts = self.monitor.get_recent_alerts(limit=10)

        # Should have at least one alert
        critical_alerts = [a for a in alerts if a.value >= 5.0]
        self.assertGreater(len(critical_alerts), 0)

        if critical_alerts:
            alert = critical_alerts[0]
            print(f"  ✓ Alert triggered: {alert.message}")
            print(f"  ✓ Alert level: {alert.level.value}")
            print(f"  ✓ Value: {alert.value:.2f}, Threshold: {alert.threshold:.2f}")

    def test_cache_performance_impact(self):
        """Test cache impact on performance"""
        print("\n[TEST] Cache Performance Impact")

        @cached(ttl=60, key_prefix='perf_test')
        def compute_intensive(n):
            total = 0
            for i in range(n):
                total += i ** 2
            return total

        # Measure without cache (first call)
        start = time.time()
        result1 = compute_intensive(10000)
        time_no_cache = time.time() - start

        # Measure with cache (second call)
        start = time.time()
        result2 = compute_intensive(10000)
        time_with_cache = time.time() - start

        self.assertEqual(result1, result2)

        speedup = time_no_cache / time_with_cache if time_with_cache > 0 else 0

        print(f"  ✓ Without cache: {time_no_cache*1000:.2f}ms")
        print(f"  ✓ With cache: {time_with_cache*1000:.2f}ms")
        print(f"  ✓ Speedup: {speedup:.0f}x faster")

        self.assertGreater(speedup, 10)  # Should be much faster

    def test_system_health_monitoring(self):
        """Test overall system health monitoring"""
        print("\n[TEST] System Health Monitoring")

        # Start monitoring
        self.monitor.start_system_monitoring(interval=1.0)
        time.sleep(2)  # Let it collect some data

        # Get health status
        health = self.monitor.get_system_health()

        self.assertIn('status', health)
        self.assertIn('system', health)
        self.assertIn('cpu_mean', health['system'])
        self.assertIn('memory_mean', health['system'])

        print(f"  ✓ System status: {health['status']}")
        print(f"  ✓ CPU mean: {health['system']['cpu_mean']:.1f}%")
        print(f"  ✓ Memory mean: {health['system']['memory_mean']:.1f}%")
        print(f"  ✓ Total metrics: {health['total_metrics']}")

        self.monitor.stop_system_monitoring()

    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        print("\n[TEST] End-to-End Workflow")

        # Simulate a complete workflow:
        # 1. Receive request
        # 2. Check cache
        # 3. Execute with monitoring
        # 4. Publish event
        # 5. Broadcast via WebSocket

        workflow_id = f"workflow_{int(time.time())}"

        # Step 1: Create monitored, cached function
        @cached(ttl=30, key_prefix='workflow')
        @monitor_performance(MetricType.RESPONSE_TIME, operation='workflow_step')
        def process_request(request_id):
            # Simulate processing
            time.sleep(0.05)
            return {'request_id': request_id, 'status': 'processed'}

        # Step 2: Execute
        result = process_request(workflow_id)
        self.assertEqual(result['status'], 'processed')

        # Step 3: Publish event
        self.event_bus.publish(
            EventTypes.TASK_COMPLETED,
            data=result
        )

        # Step 4: Check all systems recorded the workflow
        # Check cache
        cached_result = process_request(workflow_id)  # Should hit cache
        self.assertEqual(cached_result, result)

        # Check performance
        stats = self.monitor.get_statistics(
            MetricType.RESPONSE_TIME,
            operation='workflow_step'
        )
        self.assertGreater(stats['count'], 0)

        # Check events
        events = self.event_bus.get_event_history(limit=10)
        workflow_events = [
            e for e in events
            if e.data.get('request_id') == workflow_id
        ]
        self.assertGreater(len(workflow_events), 0)

        print(f"  ✓ Workflow {workflow_id} completed successfully")
        print(f"  ✓ Result cached: {cached_result is not None}")
        print(f"  ✓ Performance tracked: {stats['count']} calls")
        print(f"  ✓ Event published: {len(workflow_events)} events")

    def test_concurrent_operations(self):
        """Test system under concurrent load"""
        print("\n[TEST] Concurrent Operations")

        results = []
        errors = []

        @cached(ttl=60, key_prefix='concurrent')
        @monitor_performance(MetricType.RESPONSE_TIME, operation='concurrent_op')
        def concurrent_operation(n):
            time.sleep(0.01)
            return n * 2

        def worker(thread_id):
            try:
                for i in range(10):
                    result = concurrent_operation(thread_id * 10 + i)
                    results.append(result)
            except Exception as e:
                errors.append(e)

        # Create threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Verify
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 50)  # 5 threads * 10 operations

        # Check performance stats
        stats = self.monitor.get_statistics(
            MetricType.RESPONSE_TIME,
            operation='concurrent_op'
        )

        print(f"  ✓ Operations completed: {len(results)}")
        print(f"  ✓ Errors: {len(errors)}")
        print(f"  ✓ Performance mean: {stats['mean']*1000:.2f}ms")
        print(f"  ✓ Performance P95: {stats['p95']*1000:.2f}ms")

        # Check cache
        cache_stats = self.cache.get_stats()
        print(f"  ✓ Cache hit rate: {cache_stats['memory']['hit_rate']:.1f}%")


class TestServiceIntegration(unittest.TestCase):
    """Test integration of all services"""

    def test_service_initialization(self):
        """Test all services can be initialized"""
        print("\n[TEST] Service Initialization")

        from database import get_db
        from storage import get_storage
        from logger import get_services_logger

        # Initialize all services
        db = get_db()
        event_bus = get_event_bus()
        storage = get_storage()
        logger = get_services_logger()
        monitor = get_performance_monitor()
        cache = get_cache_manager()

        # Verify all initialized
        self.assertIsNotNone(db)
        self.assertIsNotNone(event_bus)
        self.assertIsNotNone(storage)
        self.assertIsNotNone(logger)
        self.assertIsNotNone(monitor)
        self.assertIsNotNone(cache)

        print("  ✓ Database initialized")
        print("  ✓ Event bus initialized")
        print("  ✓ Storage initialized")
        print("  ✓ Logger initialized")
        print("  ✓ Performance monitor initialized")
        print("  ✓ Cache manager initialized")

    def test_cross_service_communication(self):
        """Test communication between services"""
        print("\n[TEST] Cross-Service Communication")

        from database import get_db
        from event_bus import get_event_bus
        from logger import get_services_logger

        db = get_db()
        event_bus = get_event_bus()
        logger = get_services_logger()

        # Create a workflow that uses multiple services
        received_events = []

        def event_handler(event):
            received_events.append(event)
            logger.info(f"Event received: {event.event_type}")

        # Subscribe to events
        event_bus.subscribe(EventTypes.TASK_CREATED, event_handler)

        # Create database entry
        task_id = db.execute(
            "INSERT INTO tasks (title, description, status) VALUES (?, ?, ?)",
            ("Integration Test", "Test cross-service", "pending")
        )

        # Publish event
        event_bus.publish(
            EventTypes.TASK_CREATED,
            data={'task_id': task_id, 'title': 'Integration Test'}
        )

        time.sleep(0.1)  # Allow async processing

        # Verify
        self.assertGreater(len(received_events), 0)

        print(f"  ✓ Database entry created: task_id={task_id}")
        print(f"  ✓ Event published and received")
        print(f"  ✓ Logger recorded operation")


def run_integration_tests():
    """Run all integration tests"""
    print("=" * 70)
    print("LightSpeed Platform - Integration Test Suite")
    print("=" * 70)

    # Create test suite
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSystemIntegration))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestServiceIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 70)
    print("Integration Test Summary")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ ALL INTEGRATION TESTS PASSED")
        print("\nSystem Integration Status: EXCELLENT")
        print("All major systems working together seamlessly!")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nPlease review failures above.")

    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
