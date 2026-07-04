#!/usr/bin/env python
"""
Test Suite - Core Services
LightSpeed Type I Civilization Platform

Comprehensive tests for core services:
- Database
- Event Bus
- Storage
- Logger
- External Integrations
- OAuth Server

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 11, 2026
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import sys

# Add paths
_z_axis_root = Path(__file__).resolve().parents[2]  # .../LightSpeed/Z Axis
sys.path.insert(0, str(_z_axis_root / "Z-4_Merovingian"))

from core.services import (
    get_db, get_event_bus, get_storage, get_logger,
    get_service_manager, Event
)


class TestDatabase(unittest.TestCase):
    """Test database service"""

    def setUp(self):
        """Set up test database"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"

    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_task(self):
        """Test task creation"""
        db = get_db()
        task_id = db.create_task("Test Task", "Description", project_id=1)

        self.assertIsNotNone(task_id)
        self.assertIsInstance(task_id, int)

        # Verify task exists
        task = db.get_task(task_id)
        self.assertEqual(task['title'], "Test Task")
        self.assertEqual(task['description'], "Description")

    def test_update_task(self):
        """Test task update"""
        db = get_db()
        task_id = db.create_task("Original", "Original desc", project_id=1)

        # Update task
        db.update_task(task_id, status="in_progress", title="Updated")

        task = db.get_task(task_id)
        self.assertEqual(task['title'], "Updated")
        self.assertEqual(task['status'], "in_progress")

    def test_interfloor_task(self):
        """Test inter-floor task creation"""
        db = get_db()

        task_id = db.create_interfloor_task(
            source_floor="trinity",
            target_floor="neo",
            task_type="ai_analysis",
            payload={"test": True},
            priority="high"
        )

        self.assertIsNotNone(task_id)

        # Verify task
        tasks = db.get_interfloor_tasks_by_floor("neo")
        self.assertGreater(len(tasks), 0)


class TestEventBus(unittest.TestCase):
    """Test event bus service"""

    def setUp(self):
        """Set up event bus"""
        self.event_bus = get_event_bus()
        self.received_events = []

    def tearDown(self):
        """Clean up subscriptions"""
        self.event_bus.disable()

    def test_publish_subscribe(self):
        """Test basic pub/sub"""
        def handler(event):
            self.received_events.append(event)

        # Subscribe
        self.event_bus.subscribe("test.event", handler)

        # Publish
        self.event_bus.publish("test.event", {"data": "value"})

        # Verify
        import time
        time.sleep(0.1)  # Allow async processing

        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].topic, "test.event")
        self.assertEqual(self.received_events[0].data['data'], "value")

    def test_pattern_matching(self):
        """Test wildcard pattern matching"""
        def handler(event):
            self.received_events.append(event)

        # Subscribe to pattern
        self.event_bus.subscribe("floor.*", handler)

        # Publish multiple events
        self.event_bus.publish("floor.ready", {})
        self.event_bus.publish("floor.shutdown", {})
        self.event_bus.publish("other.event", {})

        import time
        time.sleep(0.1)

        # Should receive only floor.* events
        self.assertEqual(len(self.received_events), 2)

    def test_unsubscribe(self):
        """Test unsubscribe"""
        def handler(event):
            self.received_events.append(event)

        self.event_bus.subscribe("test.event", handler)
        self.event_bus.publish("test.event", {})

        import time
        time.sleep(0.1)
        self.assertEqual(len(self.received_events), 1)

        # Unsubscribe
        self.event_bus.unsubscribe("test.event", handler)

        # Publish again
        self.event_bus.publish("test.event", {})
        time.sleep(0.1)

        # Should still be 1 (not 2)
        self.assertEqual(len(self.received_events), 1)


class TestStorage(unittest.TestCase):
    """Test storage service"""

    def setUp(self):
        """Set up storage"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = get_storage()

    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_store_file(self):
        """Test file storage"""
        # Create test file
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("Test content")

        # Store file
        file_id = self.storage.store_file(
            test_file,
            floor="test_floor",
            namespace="test",
            metadata={"key": "value"}
        )

        self.assertIsNotNone(file_id)

        # Verify file can be retrieved
        stored_path = self.storage.get_file_path(file_id)
        self.assertTrue(stored_path.exists() if stored_path else False)

    def test_list_files(self):
        """Test file listing"""
        # Store multiple files
        for i in range(3):
            test_file = Path(self.temp_dir) / f"file_{i}.txt"
            test_file.write_text(f"Content {i}")
            self.storage.store_file(test_file, floor="test", namespace="files")

        # List files
        files = self.storage.list_files(floor="test", namespace="files")
        self.assertGreaterEqual(len(files), 3)


class TestExternalIntegrations(unittest.TestCase):
    """Test external service integrations"""

    def test_service_manager_initialization(self):
        """Test service manager"""
        manager = get_service_manager()
        self.assertIsNotNone(manager)

        # List services
        services = manager.list_services()
        self.assertIn('canva', services)
        self.assertIn('dropbox', services)
        self.assertIn('google_drive', services)

    def test_service_configuration(self):
        """Test service configuration"""
        manager = get_service_manager()

        # Configure service
        manager.configure_service(
            service_name='canva',
            client_id='test_client_id',
            client_secret='test_secret',
            enabled=False  # Don't actually enable
        )

        # Verify configuration
        services = manager.list_services()
        self.assertTrue(services['canva']['configured'])

    def test_oauth_token_serialization(self):
        """Test OAuth token save/load"""
        from core.services.external_integrations import OAuthToken

        # Create token
        token = OAuthToken(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=datetime.now(),
            token_type="Bearer",
            scope="read write"
        )

        # Serialize
        data = token.to_dict()
        self.assertEqual(data['access_token'], "test_access")
        self.assertIn('expires_at', data)

        # Deserialize
        token2 = OAuthToken.from_dict(data)
        self.assertEqual(token2.access_token, token.access_token)
        self.assertEqual(token2.refresh_token, token.refresh_token)


class TestOAuthServer(unittest.TestCase):
    """Test OAuth callback server"""

    def test_server_start_stop(self):
        """Test server lifecycle"""
        from core.services.oauth_server import OAuthCallbackServer

        server = OAuthCallbackServer(port=8081)  # Use different port

        # Start server
        server.start()
        self.assertTrue(server.running)

        # Stop server
        server.stop()
        self.assertFalse(server.running)

    def test_state_registration(self):
        """Test authorization state management"""
        from core.services.oauth_server import OAuthCallbackServer

        server = OAuthCallbackServer(port=8081)

        # Register authorization
        state = server.register_authorization("test_service")
        self.assertIsNotNone(state)
        self.assertGreater(len(state), 16)  # Should be a secure token


class TestHTTPClient(unittest.TestCase):
    """Test HTTP client"""

    def test_http_client_creation(self):
        """Test HTTP client instantiation"""
        from core.services.http_client import get_http_client

        client = get_http_client()
        self.assertIsNotNone(client)

    def test_build_request(self):
        """Test request building"""
        from core.services.http_client import HTTPClient

        client = HTTPClient()
        req = client._build_request(
            url="https://example.com/api",
            method="POST",
            headers={"Custom": "Header"},
            json_data={"key": "value"}
        )

        self.assertEqual(req.get_method(), "POST")
        self.assertIn("application/json", req.headers.get("Content-type", ""))


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestEventBus))
    suite.addTests(loader.loadTestsFromTestCase(TestStorage))
    suite.addTests(loader.loadTestsFromTestCase(TestExternalIntegrations))
    suite.addTests(loader.loadTestsFromTestCase(TestOAuthServer))
    suite.addTests(loader.loadTestsFromTestCase(TestHTTPClient))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
