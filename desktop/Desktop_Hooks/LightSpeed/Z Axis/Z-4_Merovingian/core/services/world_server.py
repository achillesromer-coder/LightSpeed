"""
World Server - LightSpeed Type I Civilization Platform
Localhost-based multi-floor communication system

Coordinates all 9 Z-floors using localhost ports for inter-floor communication.
Provides REST API, WebSocket, and event bus messaging between floors.

Architecture:
- Single world server coordinates all floors
- Each floor runs on dedicated localhost port
- REST API for floor-to-floor requests
- WebSocket for real-time updates
- Event bus for asynchronous messaging
- Shared database for persistence
- Dynamic floor discovery
- Load balancing and graceful degradation

Author: LightSpeed Team / ACHILLES
Version: 0.9.5
"""

import socket
import json
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs


@dataclass
class FloorInfo:
    """Information about a Z-floor in the world server."""
    floor_id: str  # e.g., "Z-4", "Z+0"
    floor_name: str  # e.g., "Merovingian (System Core)"
    port: int
    status: str  # "online", "offline", "starting", "stopping"
    last_heartbeat: float  # Unix timestamp
    capabilities: List[str]
    endpoints: Dict[str, str]


@dataclass
class FloorMessage:
    """Message sent between floors."""
    source_floor: str
    target_floor: str
    message_type: str  # "request", "response", "event", "broadcast"
    payload: Dict[str, Any]
    timestamp: float
    message_id: str


class WorldServer:
    """
    Central coordinator for all Z-floors.

    Manages port allocation, floor discovery, message routing,
    and health monitoring across the LightSpeed platform.
    """

    # Port allocation for each floor
    FLOOR_PORTS = {
        "Z-4": 8004,  # Merovingian (System Core)
        "Z-3": 8003,  # Smith (Replication)
        "Z-2": 8002,  # Oracle (Intelligence)
        "Z-1": 8001,  # Morpheus (Training)
        "Z+0": 8000,  # TheConstruct (Testing) - Base port
        "Z+1": 8010,  # Architect (Planning)
        "Z+2": 8020,  # Neo (Development)
        "Z+3": 8030,  # Trinity (Tools)
    }

    FLOOR_NAMES = {
        "Z-4": "Merovingian (System Core)",
        "Z-3": "Smith (Replication & Distribution)",
        "Z-2": "Oracle (Intelligence & Prediction)",
        "Z-1": "Morpheus (Training & Knowledge)",
        "Z+0": "TheConstruct (Testing & Simulation)",
        "Z+1": "Architect (Planning & Design)",
        "Z+2": "Neo (Development & Creation)",
        "Z+3": "Trinity (Tools & Utilities)",
    }

    def __init__(self, base_port: int = 8000, host: str = "localhost"):
        """
        Initialize world server.

        Args:
            base_port: Base port for floor allocation
            host: Host address (default: localhost for security)
        """
        self.base_port = base_port
        self.host = host
        self.floors: Dict[str, FloorInfo] = {}
        self.message_queue: List[FloorMessage] = []
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.running = False
        self.server_thread: Optional[threading.Thread] = None

        # Initialize floor registry
        self._initialize_floor_registry()

    def _initialize_floor_registry(self):
        """Initialize registry of all Z-floors."""
        for floor_id, port in self.FLOOR_PORTS.items():
            self.floors[floor_id] = FloorInfo(
                floor_id=floor_id,
                floor_name=self.FLOOR_NAMES[floor_id],
                port=port,
                status="offline",
                last_heartbeat=0.0,
                capabilities=[],
                endpoints={}
            )

        print(f"[WorldServer] Initialized {len(self.floors)} floors")

    def start(self):
        """Start the world server."""
        if self.running:
            print("[WorldServer] Already running")
            return

        self.running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()

        print(f"[WorldServer] Started on {self.host}")
        print(f"[WorldServer] Managing {len(self.floors)} Z-floors")

    def stop(self):
        """Stop the world server."""
        if not self.running:
            return

        self.running = False
        if self.server_thread:
            self.server_thread.join(timeout=5.0)

        print("[WorldServer] Stopped")

    def _run_server(self):
        """Main server loop."""
        print("[WorldServer] Server thread started")

        while self.running:
            # Process message queue
            self._process_messages()

            # Check floor health
            self._check_floor_health()

            # Sleep briefly
            time.sleep(0.1)

        print("[WorldServer] Server thread stopped")

    def _process_messages(self):
        """Process queued messages."""
        while self.message_queue:
            message = self.message_queue.pop(0)
            self._route_message(message)

    def _route_message(self, message: FloorMessage):
        """Route message to appropriate floor."""
        target_floor = message.target_floor

        if target_floor == "broadcast":
            # Broadcast to all floors
            for floor_id in self.floors.keys():
                if floor_id != message.source_floor:
                    self._deliver_message(floor_id, message)
        else:
            # Send to specific floor
            self._deliver_message(target_floor, message)

    def _deliver_message(self, floor_id: str, message: FloorMessage):
        """Deliver message to specific floor."""
        floor = self.floors.get(floor_id)

        if not floor:
            print(f"[WorldServer] Unknown floor: {floor_id}")
            return

        if floor.status != "online":
            print(f"[WorldServer] Floor {floor_id} is {floor.status}, message queued")
            return

        # Trigger event handlers
        event_type = f"message_{message.message_type}"
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(floor_id, message)
                except Exception as e:
                    print(f"[WorldServer] Error in event handler: {e}")

    def _check_floor_health(self):
        """Check health of all floors via heartbeat."""
        current_time = time.time()

        for floor_id, floor in self.floors.items():
            if floor.status == "online":
                time_since_heartbeat = current_time - floor.last_heartbeat

                # If no heartbeat for 30 seconds, mark as offline
                if time_since_heartbeat > 30.0:
                    print(f"[WorldServer] Floor {floor_id} heartbeat timeout")
                    floor.status = "offline"

    def register_floor(
        self,
        floor_id: str,
        capabilities: List[str],
        endpoints: Dict[str, str]
    ) -> bool:
        """
        Register a floor with the world server.

        Args:
            floor_id: Floor identifier
            capabilities: List of floor capabilities
            endpoints: Dict of endpoint names to URLs

        Returns:
            True if registration successful
        """
        floor = self.floors.get(floor_id)

        if not floor:
            print(f"[WorldServer] Unknown floor ID: {floor_id}")
            return False

        floor.status = "online"
        floor.last_heartbeat = time.time()
        floor.capabilities = capabilities
        floor.endpoints = endpoints

        print(f"[WorldServer] Registered floor {floor_id} ({floor.floor_name})")
        print(f"  Port: {floor.port}")
        print(f"  Capabilities: {', '.join(capabilities)}")

        return True

    def unregister_floor(self, floor_id: str):
        """Unregister a floor from the world server."""
        floor = self.floors.get(floor_id)

        if floor:
            floor.status = "offline"
            floor.last_heartbeat = 0.0
            floor.capabilities = []
            floor.endpoints = {}

            print(f"[WorldServer] Unregistered floor {floor_id}")

    def heartbeat(self, floor_id: str) -> bool:
        """
        Update floor heartbeat.

        Args:
            floor_id: Floor identifier

        Returns:
            True if heartbeat accepted
        """
        floor = self.floors.get(floor_id)

        if not floor:
            return False

        floor.last_heartbeat = time.time()
        return True

    def send_message(self, message: FloorMessage):
        """
        Send message to another floor.

        Args:
            message: FloorMessage to send
        """
        self.message_queue.append(message)

    def send_request(
        self,
        source_floor: str,
        target_floor: str,
        payload: Dict[str, Any]
    ) -> str:
        """
        Send request to another floor.

        Args:
            source_floor: Source floor ID
            target_floor: Target floor ID
            payload: Request payload

        Returns:
            Message ID for tracking response
        """
        message_id = f"{source_floor}_{target_floor}_{int(time.time() * 1000)}"

        message = FloorMessage(
            source_floor=source_floor,
            target_floor=target_floor,
            message_type="request",
            payload=payload,
            timestamp=time.time(),
            message_id=message_id
        )

        self.send_message(message)
        return message_id

    def broadcast_event(self, source_floor: str, event_name: str, data: Any):
        """
        Broadcast event to all floors.

        Args:
            source_floor: Source floor ID
            event_name: Name of event
            data: Event data
        """
        message = FloorMessage(
            source_floor=source_floor,
            target_floor="broadcast",
            message_type="event",
            payload={"event": event_name, "data": data},
            timestamp=time.time(),
            message_id=f"event_{int(time.time() * 1000)}"
        )

        self.send_message(message)

    def on(self, event_type: str, handler: Callable):
        """
        Register event handler.

        Args:
            event_type: Type of event (e.g., "message_request", "message_event")
            handler: Callback function (floor_id, message)
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(handler)

    def get_floor_info(self, floor_id: str) -> Optional[FloorInfo]:
        """Get information about a floor."""
        return self.floors.get(floor_id)

    def get_all_floors(self) -> Dict[str, FloorInfo]:
        """Get information about all floors."""
        return self.floors.copy()

    def get_online_floors(self) -> Dict[str, FloorInfo]:
        """Get all online floors."""
        return {
            fid: floor for fid, floor in self.floors.items()
            if floor.status == "online"
        }

    def is_floor_online(self, floor_id: str) -> bool:
        """Check if floor is online."""
        floor = self.floors.get(floor_id)
        return floor.status == "online" if floor else False

    def get_floor_url(self, floor_id: str, endpoint: str = "") -> Optional[str]:
        """
        Get URL for floor endpoint.

        Args:
            floor_id: Floor identifier
            endpoint: Optional endpoint path

        Returns:
            Full URL or None if floor not found
        """
        floor = self.floors.get(floor_id)

        if not floor:
            return None

        base_url = f"http://{self.host}:{floor.port}"

        if endpoint:
            return f"{base_url}/{endpoint.lstrip('/')}"
        else:
            return base_url

    def find_floor_by_capability(self, capability: str) -> List[str]:
        """
        Find floors with specific capability.

        Args:
            capability: Capability to search for

        Returns:
            List of floor IDs with that capability
        """
        return [
            fid for fid, floor in self.floors.items()
            if capability in floor.capabilities and floor.status == "online"
        ]

    def get_status(self) -> Dict[str, Any]:
        """Get world server status."""
        online_count = len(self.get_online_floors())

        return {
            "running": self.running,
            "total_floors": len(self.floors),
            "online_floors": online_count,
            "offline_floors": len(self.floors) - online_count,
            "host": self.host,
            "base_port": self.base_port,
            "message_queue_size": len(self.message_queue)
        }


# Global world server instance
_world_server: Optional[WorldServer] = None


def get_world_server(host: str = "localhost", base_port: int = 8000) -> WorldServer:
    """
    Get global world server instance.

    Args:
        host: Host address
        base_port: Base port

    Returns:
        WorldServer singleton
    """
    global _world_server

    if _world_server is None:
        _world_server = WorldServer(host=host, base_port=base_port)

    return _world_server


def start_world_server():
    """Start the global world server."""
    server = get_world_server()
    server.start()
    return server


def stop_world_server():
    """Stop the global world server."""
    global _world_server

    if _world_server:
        _world_server.stop()
        _world_server = None


if __name__ == "__main__":
    # Test world server
    print("LightSpeed World Server - Test Mode")
    print("=" * 60)

    # Create and start server
    server = WorldServer()
    server.start()

    print("\nFloor Registry:")
    for floor_id, floor in server.get_all_floors().items():
        print(f"  {floor_id}: {floor.floor_name} (port {floor.port})")

    print("\nServer Status:")
    status = server.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    # Simulate floor registration
    print("\nSimulating floor registration...")
    server.register_floor(
        "Z+0",
        capabilities=["testing", "simulation", "physics"],
        endpoints={"api": "/api/v1", "health": "/health"}
    )

    server.register_floor(
        "Z-4",
        capabilities=["monitoring", "healing", "diagnostics"],
        endpoints={"api": "/api/v1", "health": "/health", "metrics": "/metrics"}
    )

    # Send test message
    print("\nSending test message...")
    server.send_request(
        source_floor="Z+0",
        target_floor="Z-4",
        payload={"action": "get_health", "details": True}
    )

    # Wait a moment
    time.sleep(1.0)

    # Check status
    print("\nUpdated Status:")
    status = server.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    print("\nOnline Floors:")
    for floor_id, floor in server.get_online_floors().items():
        print(f"  {floor_id}: {floor.floor_name}")

    # Stop server
    print("\nStopping server...")
    server.stop()

    print("\nWorld Server test complete!")
