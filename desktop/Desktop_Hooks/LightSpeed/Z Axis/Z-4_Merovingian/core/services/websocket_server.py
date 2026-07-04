#!/usr/bin/env python
"""
WebSocket Server - Real-time Communication Layer
LightSpeed Type I Civilization Platform

WebSocket server for real-time bidirectional communication:
- Event streaming to connected clients
- Live performance metrics updates
- Floor status notifications
- Collaborative features support
- Message broadcasting

Uses native asyncio with websockets library for high performance.

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 11, 2026
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Set, Optional, Any, Callable
from enum import Enum
import websockets
from websockets.asyncio.server import Server, ServerConnection, serve


class MessageType(Enum):
    """WebSocket message types"""
    EVENT = "event"
    METRIC = "metric"
    ALERT = "alert"
    STATUS = "status"
    COMMAND = "command"
    RESPONSE = "response"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    type: MessageType
    data: Any
    timestamp: str
    client_id: Optional[str] = None
    channel: Optional[str] = None

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps({
            'type': self.type.value,
            'data': self.data,
            'timestamp': self.timestamp,
            'client_id': self.client_id,
            'channel': self.channel
        })

    @classmethod
    def from_json(cls, json_str: str) -> 'WebSocketMessage':
        """Parse from JSON string"""
        data = json.loads(json_str)
        return cls(
            type=MessageType(data['type']),
            data=data['data'],
            timestamp=data['timestamp'],
            client_id=data.get('client_id'),
            channel=data.get('channel')
        )


class WebSocketClient:
    """Connected WebSocket client"""

    def __init__(self, websocket: ServerConnection, client_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.subscriptions: Set[str] = set()
        self.metadata: Dict[str, Any] = {}
        self.connected_at = datetime.now()

    async def send(self, message: WebSocketMessage):
        """Send message to client"""
        try:
            await self.websocket.send(message.to_json())
        except Exception as e:
            logging.error(f"Error sending to client {self.client_id}: {e}")

    def subscribe(self, channel: str):
        """Subscribe to channel"""
        self.subscriptions.add(channel)

    def unsubscribe(self, channel: str):
        """Unsubscribe from channel"""
        self.subscriptions.discard(channel)

    def is_subscribed(self, channel: str) -> bool:
        """Check if subscribed to channel"""
        return channel in self.subscriptions


class WebSocketServer:
    """
    Real-time WebSocket server

    Manages WebSocket connections and provides real-time event streaming,
    metrics updates, and bidirectional communication.
    """

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port

        # Connected clients
        self.clients: Dict[str, WebSocketClient] = {}

        # Message handlers
        self.handlers: Dict[MessageType, Callable] = {
            MessageType.SUBSCRIBE: self._handle_subscribe,
            MessageType.UNSUBSCRIBE: self._handle_unsubscribe,
            MessageType.COMMAND: self._handle_command
        }

        # Server state
        self.server: Optional[Server] = None
        self.running = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None

        # Statistics
        self.stats = {
            'total_connections': 0,
            'messages_sent': 0,
            'messages_received': 0,
            'errors': 0
        }

    def start(self):
        """Start WebSocket server in background thread"""
        if self.running:
            return

        self.running = True

        # Run server in separate thread
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()

        logging.info(f"[WebSocketServer] Started on {self.host}:{self.port}")

    def stop(self):
        """Stop WebSocket server"""
        if not self.running:
            return

        self.running = False

        if self.loop:
            # Schedule server shutdown
            asyncio.run_coroutine_threadsafe(self._shutdown(), self.loop)

        if self.thread:
            self.thread.join(timeout=5.0)

        logging.info("[WebSocketServer] Stopped")

    def _run_server(self):
        """Run WebSocket server (called in thread)"""
        # Create new event loop for this thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Start server
        self.loop.run_until_complete(self._start_server())
        self.loop.run_forever()

    async def _start_server(self):
        """Start WebSocket server"""
        self.server = await serve(
            self._handle_connection,
            self.host,
            self.port
        )

    async def _shutdown(self):
        """Shutdown server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # Close all client connections
        for client in list(self.clients.values()):
            await client.websocket.close()

        self.loop.stop()

    async def _handle_connection(self, websocket: ServerConnection):
        """Handle new WebSocket connection"""
        # Generate client ID
        client_id = f"client_{self.stats['total_connections']}"
        self.stats['total_connections'] += 1

        # Create client
        client = WebSocketClient(websocket, client_id)
        self.clients[client_id] = client

        logging.info(f"[WebSocketServer] Client connected: {client_id}")

        # Send welcome message
        welcome = WebSocketMessage(
            type=MessageType.STATUS,
            data={
                'status': 'connected',
                'client_id': client_id,
                'server': 'LightSpeed WebSocket Server',
                'version': '1.0.0'
            },
            timestamp=datetime.now().isoformat(),
            client_id=client_id
        )
        await client.send(welcome)

        try:
            # Handle messages
            async for message in websocket:
                await self._handle_message(client, message)

        except websockets.exceptions.ConnectionClosed:
            logging.info(f"[WebSocketServer] Client disconnected: {client_id}")

        except Exception as e:
            logging.error(f"[WebSocketServer] Error handling client {client_id}: {e}")
            self.stats['errors'] += 1

        finally:
            # Remove client
            del self.clients[client_id]

    async def _handle_message(self, client: WebSocketClient, message: str):
        """Handle incoming message from client"""
        try:
            self.stats['messages_received'] += 1

            # Parse message
            msg = WebSocketMessage.from_json(message)

            # Get handler
            handler = self.handlers.get(msg.type)

            if handler:
                await handler(client, msg)
            else:
                logging.warning(f"[WebSocketServer] No handler for message type: {msg.type}")

        except Exception as e:
            logging.error(f"[WebSocketServer] Error handling message: {e}")
            self.stats['errors'] += 1

            # Send error response
            error_msg = WebSocketMessage(
                type=MessageType.RESPONSE,
                data={'error': str(e)},
                timestamp=datetime.now().isoformat(),
                client_id=client.client_id
            )
            await client.send(error_msg)

    async def _handle_subscribe(self, client: WebSocketClient, message: WebSocketMessage):
        """Handle subscription request"""
        channel = message.data.get('channel')

        if channel:
            client.subscribe(channel)

            # Send confirmation
            response = WebSocketMessage(
                type=MessageType.RESPONSE,
                data={
                    'action': 'subscribed',
                    'channel': channel
                },
                timestamp=datetime.now().isoformat(),
                client_id=client.client_id
            )
            await client.send(response)

            logging.info(f"[WebSocketServer] Client {client.client_id} subscribed to {channel}")

    async def _handle_unsubscribe(self, client: WebSocketClient, message: WebSocketMessage):
        """Handle unsubscription request"""
        channel = message.data.get('channel')

        if channel:
            client.unsubscribe(channel)

            # Send confirmation
            response = WebSocketMessage(
                type=MessageType.RESPONSE,
                data={
                    'action': 'unsubscribed',
                    'channel': channel
                },
                timestamp=datetime.now().isoformat(),
                client_id=client.client_id
            )
            await client.send(response)

            logging.info(f"[WebSocketServer] Client {client.client_id} unsubscribed from {channel}")

    async def _handle_command(self, client: WebSocketClient, message: WebSocketMessage):
        """Handle command from client"""
        command = message.data.get('command')

        logging.info(f"[WebSocketServer] Command from {client.client_id}: {command}")

        # Send acknowledgment
        response = WebSocketMessage(
            type=MessageType.RESPONSE,
            data={
                'command': command,
                'status': 'received'
            },
            timestamp=datetime.now().isoformat(),
            client_id=client.client_id
        )
        await client.send(response)

    def broadcast(self, message: WebSocketMessage, channel: Optional[str] = None):
        """Broadcast message to all clients (or channel subscribers)"""
        if not self.running or not self.loop:
            return

        asyncio.run_coroutine_threadsafe(
            self._broadcast(message, channel),
            self.loop
        )

    async def _broadcast(self, message: WebSocketMessage, channel: Optional[str] = None):
        """Async broadcast implementation"""
        for client in list(self.clients.values()):
            # Check subscription
            if channel and not client.is_subscribed(channel):
                continue

            await client.send(message)
            self.stats['messages_sent'] += 1

    def send_to_client(self, client_id: str, message: WebSocketMessage):
        """Send message to specific client"""
        if not self.running or not self.loop:
            return

        client = self.clients.get(client_id)
        if client:
            asyncio.run_coroutine_threadsafe(
                client.send(message),
                self.loop
            )
            self.stats['messages_sent'] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        return {
            'running': self.running,
            'host': self.host,
            'port': self.port,
            'connected_clients': len(self.clients),
            'total_connections': self.stats['total_connections'],
            'messages_sent': self.stats['messages_sent'],
            'messages_received': self.stats['messages_received'],
            'errors': self.stats['errors']
        }

    def get_connected_clients(self) -> List[Dict[str, Any]]:
        """Get list of connected clients"""
        return [
            {
                'client_id': client.client_id,
                'subscriptions': list(client.subscriptions),
                'connected_at': client.connected_at.isoformat()
            }
            for client in self.clients.values()
        ]


# Integration with event bus
def integrate_with_event_bus():
    """Integrate WebSocket server with event bus"""
    try:
        from .event_bus import get_event_bus, EventTypes

        ws_server = get_websocket_server()
        event_bus = get_event_bus()

        # Subscribe to all events and broadcast to WebSocket clients
        def broadcast_event(event):
            message = WebSocketMessage(
                type=MessageType.EVENT,
                data={
                    'event_type': event.event_type,
                    'data': event.data,
                    'floor': event.floor,
                    'timestamp': event.timestamp.isoformat()
                },
                timestamp=datetime.now().isoformat(),
                channel='events'
            )
            ws_server.broadcast(message, channel='events')

        # Subscribe to key event types
        for event_type in EventTypes:
            event_bus.subscribe(event_type.value, broadcast_event)

        logging.info("[WebSocketServer] Integrated with event bus")

    except Exception as e:
        logging.error(f"[WebSocketServer] Failed to integrate with event bus: {e}")


def integrate_with_performance_monitor():
    """Integrate WebSocket server with performance monitor"""
    try:
        from .performance_monitor import get_performance_monitor

        ws_server = get_websocket_server()
        monitor = get_performance_monitor()

        # Create periodic task to broadcast metrics
        async def broadcast_metrics():
            while ws_server.running:
                # Get system health
                health = monitor.get_system_health()

                message = WebSocketMessage(
                    type=MessageType.METRIC,
                    data=health,
                    timestamp=datetime.now().isoformat(),
                    channel='metrics'
                )

                await ws_server._broadcast(message, channel='metrics')

                # Wait 5 seconds
                await asyncio.sleep(5)

        # Schedule task
        if ws_server.loop:
            asyncio.run_coroutine_threadsafe(broadcast_metrics(), ws_server.loop)

        logging.info("[WebSocketServer] Integrated with performance monitor")

    except Exception as e:
        logging.error(f"[WebSocketServer] Failed to integrate with performance monitor: {e}")


# Singleton instance
_websocket_server: Optional[WebSocketServer] = None


def get_websocket_server(host: str = "localhost", port: int = 8765) -> WebSocketServer:
    """Get global WebSocket server"""
    global _websocket_server
    if _websocket_server is None:
        _websocket_server = WebSocketServer(host=host, port=port)
    return _websocket_server


def start_websocket_server(host: str = "localhost", port: int = 8765) -> WebSocketServer:
    """Start WebSocket server"""
    server = get_websocket_server(host, port)
    server.start()
    return server


def stop_websocket_server():
    """Stop WebSocket server"""
    global _websocket_server
    if _websocket_server:
        _websocket_server.stop()


if __name__ == "__main__":
    # Test WebSocket server
    logging.basicConfig(level=logging.INFO)

    print("WebSocket Server Test")
    print("=" * 60)

    # Start server
    print("\nStarting WebSocket server...")
    server = start_websocket_server()

    print(f"Server running on ws://{server.host}:{server.port}")
    print("\nYou can connect using:")
    print("  - Browser: new WebSocket('ws://localhost:8765')")
    print("  - Python: websockets.connect('ws://localhost:8765')")

    # Simulate broadcasting
    import time

    try:
        print("\nBroadcasting test messages...")

        for i in range(5):
            time.sleep(2)

            message = WebSocketMessage(
                type=MessageType.EVENT,
                data={'test': f'message_{i}', 'value': i},
                timestamp=datetime.now().isoformat(),
                channel='test'
            )

            server.broadcast(message)
            print(f"Broadcasted message {i}")

        # Show stats
        print("\nServer Statistics:")
        stats = server.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # Keep running
        print("\nServer running. Press Ctrl+C to stop...")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nStopping server...")
        stop_websocket_server()
        print("Server stopped")

    print("\n" + "=" * 60)
    print("WebSocket server test complete!")
