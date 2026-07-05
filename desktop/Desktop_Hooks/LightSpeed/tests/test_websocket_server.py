from __future__ import annotations

import asyncio
import json

import websockets

from core.services.websocket_server import WebSocketServer


def test_websocket_server_accepts_client_and_subscription() -> None:
    async def exercise_server() -> None:
        server = WebSocketServer(host="127.0.0.1", port=0)
        await server._start_server()
        assert server.server is not None
        port = server.server.sockets[0].getsockname()[1]

        try:
            async with websockets.connect(f"ws://127.0.0.1:{port}") as client:
                welcome = json.loads(await asyncio.wait_for(client.recv(), timeout=2))
                assert welcome["type"] == "status"
                assert welcome["data"]["status"] == "connected"

                await client.send(
                    json.dumps(
                        {
                            "type": "subscribe",
                            "data": {"channel": "system.health"},
                            "timestamp": "2026-07-03T00:00:00Z",
                        }
                    )
                )
                response = json.loads(await asyncio.wait_for(client.recv(), timeout=2))
                assert response["data"] == {
                    "action": "subscribed",
                    "channel": "system.health",
                }
        finally:
            server.server.close()
            await server.server.wait_closed()

    asyncio.run(exercise_server())
