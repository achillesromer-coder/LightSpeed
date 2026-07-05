#!/usr/bin/env python
"""
WebSocket Client - Real-time Client Connection
LightSpeed Type I Civilization Platform

Simple WebSocket client for connecting to LightSpeed WebSocket server
using only standard library (no external dependencies except websockets).

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 11, 2026
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Optional, Callable, Dict, Any
from datetime import datetime


class SimpleWebSocketClient:
    """
    Simple WebSocket client

    Connects to WebSocket server and handles real-time messages.
    Note: Requires websockets library (pip install websockets)
    """

    def __init__(self, url: str = "ws://localhost:8765"):
        self.url = url
        self.websocket = None
        self.running = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None

        # Message handlers
        self.handlers: Dict[str, Callable] = {}

        # Client state
        self.client_id: Optional[str] = None
        self.subscriptions: set = set()

    def connect(self):
        """Connect to WebSocket server"""
        if self.running:
            return

        self.running = True

        # Run client in separate thread
        self.thread = threading.Thread(target=self._run_client, daemon=True)
        self.thread.start()

        logging.info(f"[WebSocketClient] Connecting to {self.url}")

    def disconnect(self):
        """Disconnect from server"""
        if not self.running:
            return

        self.running = False

        if self.loop:
            asyncio.run_coroutine_threadsafe(self._close(), self.loop)

        if self.thread:
            self.thread.join(timeout=5.0)

        logging.info("[WebSocketClient] Disconnected")

    def _run_client(self):
        """Run client (called in thread)"""
        # Create new event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Run connection
        self.loop.run_until_complete(self._connect())

    async def _connect(self):
        """Connect to server"""
        try:
            import websockets

            async with websockets.connect(self.url) as websocket:
                self.websocket = websocket

                # Receive messages
                async for message in websocket:
                    await self._handle_message(message)

        except Exception as e:
            logging.error(f"[WebSocketClient] Connection error: {e}")
            self.running = False

    async def _close(self):
        """Close connection"""
        if self.websocket:
            await self.websocket.close()

    async def _handle_message(self, message: str):
        """Handle incoming message"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')

            # Handle status messages
            if msg_type == 'status' and data.get('data', {}).get('status') == 'connected':
                self.client_id = data.get('data', {}).get('client_id')
                logging.info(f"[WebSocketClient] Connected as {self.client_id}")

            # Call registered handlers
            if msg_type in self.handlers:
                self.handlers[msg_type](data)

        except Exception as e:
            logging.error(f"[WebSocketClient] Error handling message: {e}")

    def on(self, message_type: str, handler: Callable):
        """Register message handler"""
        self.handlers[message_type] = handler

    def subscribe(self, channel: str):
        """Subscribe to channel"""
        if not self.running or not self.loop:
            return

        self.subscriptions.add(channel)

        message = {
            'type': 'subscribe',
            'data': {'channel': channel},
            'timestamp': datetime.now().isoformat()
        }

        asyncio.run_coroutine_threadsafe(
            self._send(json.dumps(message)),
            self.loop
        )

    def unsubscribe(self, channel: str):
        """Unsubscribe from channel"""
        if not self.running or not self.loop:
            return

        self.subscriptions.discard(channel)

        message = {
            'type': 'unsubscribe',
            'data': {'channel': channel},
            'timestamp': datetime.now().isoformat()
        }

        asyncio.run_coroutine_threadsafe(
            self._send(json.dumps(message)),
            self.loop
        )

    def send_command(self, command: str, data: Optional[Dict[str, Any]] = None):
        """Send command to server"""
        if not self.running or not self.loop:
            return

        message = {
            'type': 'command',
            'data': {
                'command': command,
                **(data or {})
            },
            'timestamp': datetime.now().isoformat()
        }

        asyncio.run_coroutine_threadsafe(
            self._send(json.dumps(message)),
            self.loop
        )

    async def _send(self, message: str):
        """Send message to server"""
        if self.websocket:
            await self.websocket.send(message)


if __name__ == "__main__":
    # Test WebSocket client
    logging.basicConfig(level=logging.INFO)

    print("WebSocket Client Test")
    print("=" * 60)

    # Create client
    client = SimpleWebSocketClient()

    # Register handlers
    def on_event(data):
        print(f"\n[EVENT] {data}")

    def on_metric(data):
        print(f"\n[METRIC] {data}")

    def on_response(data):
        print(f"\n[RESPONSE] {data}")

    client.on('event', on_event)
    client.on('metric', on_metric)
    client.on('response', on_response)

    # Connect
    print("\nConnecting to server...")
    client.connect()

    # Wait for connection
    import time
    time.sleep(1)

    # Subscribe to channels
    print("\nSubscribing to channels...")
    client.subscribe('events')
    client.subscribe('metrics')

    # Send test command
    time.sleep(0.5)
    print("\nSending test command...")
    client.send_command('test', {'value': 123})

    # Keep running
    try:
        print("\nClient running. Press Ctrl+C to stop...")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nDisconnecting...")
        client.disconnect()
        print("Disconnected")

    print("\n" + "=" * 60)
    print("Client test complete!")
