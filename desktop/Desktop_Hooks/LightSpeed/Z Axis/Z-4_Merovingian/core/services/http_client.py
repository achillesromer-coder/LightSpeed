#!/usr/bin/env python
"""
HTTP Client - Lightweight HTTP request wrapper
LightSpeed Type I Civilization Platform

Provides HTTP client for external API integrations without external dependencies.
Uses urllib for Python standard library compatibility.

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 11, 2026
"""

from __future__ import annotations

import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Dict, Optional, Any, Union
from dataclasses import dataclass


@dataclass
class HTTPResponse:
    """HTTP response wrapper"""
    status_code: int
    headers: Dict[str, str]
    body: Union[str, bytes]
    url: str

    def json(self) -> Any:
        """Parse JSON response"""
        if isinstance(self.body, bytes):
            return json.loads(self.body.decode('utf-8'))
        return json.loads(self.body)

    def text(self) -> str:
        """Get response as text"""
        if isinstance(self.body, bytes):
            return self.body.decode('utf-8')
        return self.body

    @property
    def ok(self) -> bool:
        """Check if request was successful"""
        return 200 <= self.status_code < 300


class HTTPClient:
    """Lightweight HTTP client using urllib"""

    def __init__(self, default_headers: Optional[Dict[str, str]] = None):
        self.default_headers = default_headers or {}

    def _build_request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[Dict, str, bytes]] = None,
        json_data: Optional[Dict] = None
    ) -> urllib.request.Request:
        """Build HTTP request"""

        # Merge headers
        req_headers = {**self.default_headers}
        if headers:
            req_headers.update(headers)

        # Handle JSON data
        encoded_data = None
        if json_data is not None:
            encoded_data = json.dumps(json_data).encode('utf-8')
            req_headers['Content-Type'] = 'application/json'
        elif data is not None:
            if isinstance(data, dict):
                encoded_data = urllib.parse.urlencode(data).encode('utf-8')
                req_headers['Content-Type'] = 'application/x-www-form-urlencoded'
            elif isinstance(data, str):
                encoded_data = data.encode('utf-8')
            else:
                encoded_data = data

        # Create request
        req = urllib.request.Request(url, data=encoded_data, method=method)

        # Add headers
        for key, value in req_headers.items():
            req.add_header(key, value)

        return req

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[Dict, str, bytes]] = None,
        json: Optional[Dict] = None,
        timeout: int = 30
    ) -> HTTPResponse:
        """Make HTTP request"""

        req = self._build_request(url, method, headers, data, json)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                body = response.read()
                response_headers = dict(response.headers)

                return HTTPResponse(
                    status_code=response.status,
                    headers=response_headers,
                    body=body,
                    url=response.url
                )

        except urllib.error.HTTPError as e:
            # HTTP error responses
            body = e.read()
            return HTTPResponse(
                status_code=e.code,
                headers=dict(e.headers),
                body=body,
                url=e.url
            )

        except urllib.error.URLError as e:
            # Network errors
            raise ConnectionError(f"Failed to connect to {url}: {e.reason}")

    def get(self, url: str, **kwargs) -> HTTPResponse:
        """HTTP GET request"""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> HTTPResponse:
        """HTTP POST request"""
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> HTTPResponse:
        """HTTP PUT request"""
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> HTTPResponse:
        """HTTP DELETE request"""
        return self.request("DELETE", url, **kwargs)

    def patch(self, url: str, **kwargs) -> HTTPResponse:
        """HTTP PATCH request"""
        return self.request("PATCH", url, **kwargs)


def get_http_client(default_headers: Optional[Dict[str, str]] = None) -> HTTPClient:
    """Get HTTP client instance"""
    return HTTPClient(default_headers)


# Example usage
if __name__ == "__main__":
    # Test HTTP client
    client = HTTPClient()

    # GET request
    print("Testing GET request...")
    try:
        response = client.get("https://api.github.com/zen")
        print(f"Status: {response.status_code}")
        print(f"Body: {response.text()[:100]}...")
    except Exception as e:
        print(f"Error: {e}")

    # POST request with JSON
    print("\nTesting POST request...")
    try:
        response = client.post(
            "https://httpbin.org/post",
            json={"key": "value", "test": True}
        )
        print(f"Status: {response.status_code}")
        if response.ok:
            data = response.json()
            print(f"Echo: {data.get('json')}")
    except Exception as e:
        print(f"Error: {e}")
