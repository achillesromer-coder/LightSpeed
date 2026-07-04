#!/usr/bin/env python
"""
OAuth Callback Server - Local server for OAuth 2.0 flows
LightSpeed Type I Civilization Platform

Provides local HTTP server at localhost:8080 to handle OAuth callbacks.
Supports multiple concurrent authorization flows with state validation.

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 11, 2026
"""

from __future__ import annotations

import http.server
import socketserver
import threading
import webbrowser
from urllib.parse import urlparse, parse_qs
from typing import Dict, Optional, Callable
import secrets
import time
from datetime import datetime, timedelta


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callbacks"""

    # Class-level storage for callbacks
    pending_states: Dict[str, Dict] = {}
    authorization_codes: Dict[str, str] = {}

    def log_message(self, format: str, *args):
        """Override to suppress default logging"""
        # Custom logging
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[OAuthServer {timestamp}] {format % args}")

    def do_GET(self):
        """Handle GET requests (OAuth callbacks)"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/oauth/callback':
            self._handle_oauth_callback(parsed_path)
        elif parsed_path.path == '/':
            self._send_welcome_page()
        elif parsed_path.path == '/status':
            self._send_status_page()
        else:
            self._send_404()

    def _handle_oauth_callback(self, parsed_path):
        """Handle OAuth callback"""
        query_params = parse_qs(parsed_path.query)

        # Extract parameters
        code = query_params.get('code', [None])[0]
        state = query_params.get('state', [None])[0]
        error = query_params.get('error', [None])[0]

        if error:
            self._send_error_page(error, query_params.get('error_description', ['Unknown error'])[0])
            return

        if not code or not state:
            self._send_error_page('invalid_request', 'Missing code or state parameter')
            return

        # Validate state
        if state not in self.pending_states:
            self._send_error_page('invalid_state', 'Unknown or expired state token')
            return

        # Store authorization code
        self.authorization_codes[state] = code

        # Get service name
        service_name = self.pending_states[state].get('service_name', 'Unknown')

        # Send success page
        self._send_success_page(service_name)

        # Mark state as completed
        self.pending_states[state]['completed'] = True
        self.pending_states[state]['code'] = code

    def _send_welcome_page(self):
        """Send welcome page"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>LightSpeed OAuth Server</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 40px;
            backdrop-filter: blur(10px);
        }
        h1 { color: #fff; font-size: 2.5em; margin-bottom: 10px; }
        .status {
            background: rgba(255, 255, 255, 0.2);
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .running { color: #4ade80; font-weight: bold; }
        a { color: #60a5fa; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .info {
            background: rgba(255, 255, 255, 0.15);
            padding: 10px;
            border-left: 4px solid #60a5fa;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 LightSpeed OAuth Server</h1>
        <div class="status">
            <p class="running">● Server Running</p>
            <p>Ready to handle OAuth callbacks</p>
        </div>
        <div class="info">
            <h3>Server Information</h3>
            <p><strong>Address:</strong> http://localhost:8080</p>
            <p><strong>Callback URL:</strong> http://localhost:8080/oauth/callback</p>
            <p><strong>Status:</strong> <a href="/status">View Status</a></p>
        </div>
        <div class="info">
            <h3>Supported Services</h3>
            <ul>
                <li>🎨 Canva - Design integration</li>
                <li>📦 Dropbox - Cloud storage</li>
                <li>📁 Google Drive - File management</li>
                <li>☁️ OneDrive - Microsoft storage</li>
            </ul>
        </div>
        <p style="margin-top: 30px; opacity: 0.7; font-size: 0.9em;">
            This server handles OAuth 2.0 authorization callbacks for LightSpeed Platform.
            Do not close this window while authorizing services.
        </p>
    </div>
</body>
</html>
"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def _send_success_page(self, service_name: str):
        """Send authorization success page"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Authorization Successful</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 600px;
            margin: 100px auto;
            padding: 20px;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .success-box {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 40px;
            backdrop-filter: blur(10px);
        }}
        .checkmark {{
            font-size: 80px;
            color: #4ade80;
            margin-bottom: 20px;
        }}
        h1 {{ color: #fff; margin-bottom: 10px; }}
        p {{ font-size: 1.1em; opacity: 0.9; }}
        .close-msg {{
            margin-top: 30px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.15);
            border-radius: 8px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="success-box">
        <div class="checkmark">✓</div>
        <h1>Authorization Successful!</h1>
        <p>You've successfully connected <strong>{service_name}</strong> to LightSpeed Platform.</p>
        <div class="close-msg">
            <p>You can now close this window and return to LightSpeed.</p>
        </div>
    </div>
    <script>
        // Auto-close after 3 seconds
        setTimeout(function() {{
            window.close();
        }}, 3000);
    </script>
</body>
</html>
"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def _send_error_page(self, error: str, description: str):
        """Send authorization error page"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Authorization Failed</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 600px;
            margin: 100px auto;
            padding: 20px;
            text-align: center;
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
        }}
        .error-box {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 40px;
            backdrop-filter: blur(10px);
        }}
        .error-icon {{
            font-size: 80px;
            color: #fecaca;
            margin-bottom: 20px;
        }}
        h1 {{ color: #fff; margin-bottom: 10px; }}
        .error-code {{
            font-family: monospace;
            background: rgba(0, 0, 0, 0.3);
            padding: 10px;
            border-radius: 5px;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    <div class="error-box">
        <div class="error-icon">✗</div>
        <h1>Authorization Failed</h1>
        <p>{description}</p>
        <div class="error-code">Error: {error}</div>
        <p style="margin-top: 20px; opacity: 0.8;">Please try again or contact support.</p>
    </div>
</body>
</html>
"""
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def _send_status_page(self):
        """Send server status page"""
        pending_count = len([s for s in self.pending_states.values() if not s.get('completed', False)])
        completed_count = len([s for s in self.pending_states.values() if s.get('completed', False)])

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>OAuth Server Status</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .container {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 40px;
            backdrop-filter: blur(10px);
        }}
        h1 {{ color: #fff; }}
        .stat {{
            display: inline-block;
            margin: 10px 20px;
            padding: 15px 30px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
        }}
        .stat-value {{ font-size: 2em; font-weight: bold; }}
        .stat-label {{ opacity: 0.8; }}
        table {{
            width: 100%;
            margin-top: 20px;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }}
        th {{ background: rgba(255, 255, 255, 0.1); }}
        .status-pending {{ color: #fbbf24; }}
        .status-completed {{ color: #4ade80; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 OAuth Server Status</h1>
        <div style="text-align: center; margin: 30px 0;">
            <div class="stat">
                <div class="stat-value">{pending_count}</div>
                <div class="stat-label">Pending</div>
            </div>
            <div class="stat">
                <div class="stat-value">{completed_count}</div>
                <div class="stat-label">Completed</div>
            </div>
        </div>
        <h3>Active Authorization Flows</h3>
        <table>
            <tr>
                <th>Service</th>
                <th>State</th>
                <th>Status</th>
                <th>Started</th>
            </tr>
            {"".join([f'''
            <tr>
                <td>{state_data.get('service_name', 'Unknown')}</td>
                <td>{state[:8]}...</td>
                <td class="status-{'completed' if state_data.get('completed') else 'pending'}">
                    {'✓ Completed' if state_data.get('completed') else '⏳ Pending'}
                </td>
                <td>{state_data.get('timestamp', 'Unknown')}</td>
            </tr>
            ''' for state, state_data in self.pending_states.items()])}
        </table>
        <p style="margin-top: 20px; opacity: 0.7; font-size: 0.9em;">
            Page auto-refreshes every 5 seconds
        </p>
    </div>
</body>
</html>
"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def _send_404(self):
        """Send 404 page"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>404 Not Found</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center;
            padding: 100px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        h1 { font-size: 4em; margin: 0; }
        p { font-size: 1.2em; opacity: 0.8; }
    </style>
</head>
<body>
    <h1>404</h1>
    <p>Page not found</p>
    <p><a href="/" style="color: #60a5fa;">Return to home</a></p>
</body>
</html>
"""
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())


class OAuthCallbackServer:
    """OAuth callback server manager"""

    def __init__(self, port: int = 8080):
        self.port = port
        self.server: Optional[socketserver.TCPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.running = False

    def start(self):
        """Start the OAuth callback server"""
        if self.running:
            print("[OAuthServer] Server already running")
            return

        try:
            # Create server
            self.server = socketserver.TCPServer(("localhost", self.port), OAuthCallbackHandler)
            self.server.allow_reuse_address = True

            # Run in background thread
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()

            self.running = True
            print(f"[OAuthServer] Started on http://localhost:{self.port}")
            print(f"[OAuthServer] Callback URL: http://localhost:{self.port}/oauth/callback")

        except OSError as e:
            if e.errno == 10048:  # Windows: Address already in use
                print(f"[OAuthServer] Port {self.port} already in use - server may already be running")
                self.running = True  # Assume it's our server
            else:
                raise

    def stop(self):
        """Stop the OAuth callback server"""
        if not self.running:
            return

        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("[OAuthServer] Stopped")

        self.running = False

    def register_authorization(self, service_name: str) -> str:
        """Register a new authorization flow and return state token"""
        state = secrets.token_urlsafe(32)

        OAuthCallbackHandler.pending_states[state] = {
            'service_name': service_name,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'completed': False
        }

        return state

    def wait_for_authorization(self, state: str, timeout: int = 300) -> Optional[str]:
        """Wait for authorization code (blocking)"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if state in OAuthCallbackHandler.pending_states:
                state_data = OAuthCallbackHandler.pending_states[state]
                if state_data.get('completed'):
                    return state_data.get('code')

            time.sleep(0.5)

        return None

    def get_authorization_code(self, state: str) -> Optional[str]:
        """Get authorization code if available (non-blocking)"""
        if state in OAuthCallbackHandler.authorization_codes:
            return OAuthCallbackHandler.authorization_codes[state]
        return None

    def cleanup_state(self, state: str):
        """Clean up completed authorization state"""
        OAuthCallbackHandler.pending_states.pop(state, None)
        OAuthCallbackHandler.authorization_codes.pop(state, None)


# Global server instance
_oauth_server: Optional[OAuthCallbackServer] = None


def get_oauth_server() -> OAuthCallbackServer:
    """Get global OAuth server instance"""
    global _oauth_server
    if _oauth_server is None:
        _oauth_server = OAuthCallbackServer()
    return _oauth_server


def start_oauth_server(port: int = 8080):
    """Start OAuth server"""
    server = get_oauth_server()
    if not server.running:
        server.start()
    return server


def stop_oauth_server():
    """Stop OAuth server"""
    server = get_oauth_server()
    server.stop()


if __name__ == "__main__":
    # Test server
    print("Starting OAuth Callback Server...")
    server = start_oauth_server()

    print("\nServer running. Visit http://localhost:8080")
    print("Press Ctrl+C to stop")

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        stop_oauth_server()
