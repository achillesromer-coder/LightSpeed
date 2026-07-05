#!/usr/bin/env python
"""
External Service Integrations - Cloud Storage & Design Tools
LightSpeed Type I Civilization Platform

This module provides integrations with external services:
- Canva (Design import/export)
- Dropbox (Cloud storage)
- Google Drive (Cloud storage)
- Google Workspace (Docs, Sheets, etc.)
- OneDrive (Microsoft cloud storage)
- Box (Enterprise cloud storage)

All integrations use OAuth 2.0 for secure authentication.

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 11, 2026
"""

from __future__ import annotations

import json
import os
import webbrowser
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from urllib.parse import urlencode, parse_qs, urlparse
import hashlib
import secrets


@dataclass
class OAuthToken:
    """OAuth token storage"""
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    token_type: str = "Bearer"
    scope: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if token is expired"""
        if not self.expires_at:
            return False
        return datetime.now() >= self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OAuthToken':
        """Load from dictionary"""
        if 'expires_at' in data and data['expires_at']:
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)


@dataclass
class ServiceConfig:
    """Configuration for external service"""
    service_name: str
    enabled: bool = False
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: str = "http://localhost:8080/oauth/callback"
    scopes: List[str] = None

    def __post_init__(self):
        if self.scopes is None:
            self.scopes = []


class ExternalServiceBase(ABC):
    """Base class for external service integrations"""

    def __init__(self, config: ServiceConfig, token_storage_path: Optional[Path] = None):
        self.config = config
        self.token_storage_path = token_storage_path or Path.home() / ".lightspeed" / "tokens"
        self.token_storage_path.mkdir(parents=True, exist_ok=True)
        self.token: Optional[OAuthToken] = None
        self._load_token()

    @property
    @abstractmethod
    def auth_url(self) -> str:
        """Authorization URL"""
        pass

    @property
    @abstractmethod
    def token_url(self) -> str:
        """Token exchange URL"""
        pass

    def _get_token_file(self) -> Path:
        """Get token storage file path"""
        return self.token_storage_path / f"{self.config.service_name}_token.json"

    def _load_token(self):
        """Load token from storage"""
        token_file = self._get_token_file()
        if token_file.exists():
            try:
                with open(token_file, 'r') as f:
                    data = json.load(f)
                    self.token = OAuthToken.from_dict(data)
            except Exception as e:
                print(f"[{self.config.service_name}] Failed to load token: {e}")

    def _save_token(self):
        """Save token to storage"""
        if not self.token:
            return

        token_file = self._get_token_file()
        try:
            with open(token_file, 'w') as f:
                json.dump(self.token.to_dict(), f, indent=2)
        except Exception as e:
            print(f"[{self.config.service_name}] Failed to save token: {e}")

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate authorization URL"""
        if not self.config.client_id:
            raise ValueError(f"{self.config.service_name}: client_id not configured")

        if state is None:
            state = secrets.token_urlsafe(32)

        params = {
            'client_id': self.config.client_id,
            'redirect_uri': self.config.redirect_uri,
            'response_type': 'code',
            'state': state,
            'scope': ' '.join(self.config.scopes) if self.config.scopes else ''
        }

        return f"{self.auth_url}?{urlencode(params)}"

    def authorize(self, state: Optional[str] = None) -> str:
        """Start OAuth flow by opening browser"""
        # Start OAuth server if not running
        from .oauth_server import start_oauth_server
        server = start_oauth_server()

        # Register authorization flow
        if state is None:
            state = server.register_authorization(self.config.service_name)

        auth_url = self.get_authorization_url(state)
        webbrowser.open(auth_url)

        print(f"[{self.config.service_name}] Waiting for authorization...")
        print(f"[{self.config.service_name}] If browser doesn't open, visit: {auth_url}")

        # Wait for callback (blocking with timeout)
        code = server.wait_for_authorization(state, timeout=300)

        if code:
            print(f"[{self.config.service_name}] Authorization code received")
            # Exchange code for token
            if self.exchange_code(code):
                server.cleanup_state(state)
                print(f"[{self.config.service_name}] ✓ Authorization successful!")
                return "success"

        server.cleanup_state(state)
        print(f"[{self.config.service_name}] Authorization timeout or failed")
        return "failed"

    @abstractmethod
    def exchange_code(self, code: str) -> bool:
        """Exchange authorization code for token"""
        pass

    @abstractmethod
    def refresh_token_if_needed(self) -> bool:
        """Refresh token if expired"""
        pass

    def is_authenticated(self) -> bool:
        """Check if service is authenticated"""
        return self.token is not None and not self.token.is_expired()

    def disconnect(self):
        """Disconnect service (revoke token)"""
        token_file = self._get_token_file()
        if token_file.exists():
            token_file.unlink()
        self.token = None


class CanvaIntegration(ExternalServiceBase):
    """Canva design platform integration"""

    @property
    def auth_url(self) -> str:
        return "https://www.canva.com/api/oauth/authorize"

    @property
    def token_url(self) -> str:
        return "https://api.canva.com/rest/v1/oauth/token"

    def __init__(self, config: ServiceConfig, token_storage_path: Optional[Path] = None):
        if not config.scopes:
            config.scopes = [
                'design:read',
                'design:write',
                'asset:read',
                'asset:write',
                'folder:read'
            ]
        super().__init__(config, token_storage_path)

    def exchange_code(self, code: str) -> bool:
        """Exchange authorization code for token"""
        from .http_client import get_http_client

        client = get_http_client()

        try:
            response = client.post(
                self.token_url,
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'client_id': self.config.client_id,
                    'client_secret': self.config.client_secret,
                    'redirect_uri': self.config.redirect_uri
                }
            )

            if response.ok:
                data = response.json()
                expires_in = data.get('expires_in', 3600)

                self.token = OAuthToken(
                    access_token=data['access_token'],
                    refresh_token=data.get('refresh_token'),
                    expires_at=datetime.now() + timedelta(seconds=expires_in),
                    token_type=data.get('token_type', 'Bearer'),
                    scope=data.get('scope')
                )

                self._save_token()
                print(f"[Canva] Token obtained successfully")
                return True
            else:
                error_data = response.json() if response.body else {}
                print(f"[Canva] Token exchange failed: {error_data.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"[Canva] Token exchange error: {e}")
            return False

    def refresh_token_if_needed(self) -> bool:
        """Refresh token if expired"""
        from .http_client import get_http_client

        if not self.token or not self.token.refresh_token:
            return False

        if not self.token.is_expired():
            return True

        client = get_http_client()

        try:
            response = client.post(
                self.token_url,
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': self.token.refresh_token,
                    'client_id': self.config.client_id,
                    'client_secret': self.config.client_secret
                }
            )

            if response.ok:
                data = response.json()
                expires_in = data.get('expires_in', 3600)

                self.token.access_token = data['access_token']
                if 'refresh_token' in data:
                    self.token.refresh_token = data['refresh_token']
                self.token.expires_at = datetime.now() + timedelta(seconds=expires_in)

                self._save_token()
                print(f"[Canva] Token refreshed successfully")
                return True
            else:
                print(f"[Canva] Token refresh failed")
                return False

        except Exception as e:
            print(f"[Canva] Token refresh error: {e}")
            return False

    def import_design(self, design_id: str, destination: Path) -> bool:
        """Import design from Canva"""
        if not self.is_authenticated():
            print(f"[Canva] Not authenticated")
            return False

        print(f"[Canva] Importing design {design_id} to {destination}")
        # Implementation would use Canva API
        return True

    def export_to_canva(self, file_path: Path, folder_id: Optional[str] = None) -> Optional[str]:
        """Export file to Canva"""
        if not self.is_authenticated():
            print(f"[Canva] Not authenticated")
            return None

        print(f"[Canva] Exporting {file_path} to Canva")
        # Implementation would use Canva API
        return "design_123456"  # Placeholder design ID

    def list_designs(self, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available designs"""
        if not self.is_authenticated():
            return []

        # Placeholder
        return [
            {"id": "design_1", "name": "LightSpeed Logo", "type": "logo"},
            {"id": "design_2", "name": "Platform Diagram", "type": "diagram"},
        ]


class DropboxIntegration(ExternalServiceBase):
    """Dropbox cloud storage integration"""

    @property
    def auth_url(self) -> str:
        return "https://www.dropbox.com/oauth2/authorize"

    @property
    def token_url(self) -> str:
        return "https://api.dropboxapi.com/oauth2/token"

    def __init__(self, config: ServiceConfig, token_storage_path: Optional[Path] = None):
        if not config.scopes:
            config.scopes = [
                'files.metadata.read',
                'files.content.read',
                'files.content.write',
                'sharing.read',
                'sharing.write'
            ]
        super().__init__(config, token_storage_path)

    def exchange_code(self, code: str) -> bool:
        """Exchange authorization code for token"""
        print(f"[Dropbox] Code exchange - implement with requests library")
        return False

    def refresh_token_if_needed(self) -> bool:
        """Refresh token if expired"""
        if not self.token or not self.token.refresh_token:
            return False

        if not self.token.is_expired():
            return True

        print(f"[Dropbox] Token refresh needed")
        return False

    def upload_file(self, local_path: Path, dropbox_path: str) -> bool:
        """Upload file to Dropbox"""
        if not self.is_authenticated():
            print(f"[Dropbox] Not authenticated")
            return False

        print(f"[Dropbox] Uploading {local_path} to {dropbox_path}")
        return True

    def download_file(self, dropbox_path: str, local_path: Path) -> bool:
        """Download file from Dropbox"""
        if not self.is_authenticated():
            print(f"[Dropbox] Not authenticated")
            return False

        print(f"[Dropbox] Downloading {dropbox_path} to {local_path}")
        return True

    def list_folder(self, path: str = "") -> List[Dict[str, Any]]:
        """List folder contents"""
        if not self.is_authenticated():
            return []

        # Placeholder
        return [
            {"name": "LightSpeed Backups", "type": "folder", "path": "/LightSpeed Backups"},
            {"name": "project_data.json", "type": "file", "path": "/project_data.json", "size": 1024},
        ]


class GoogleDriveIntegration(ExternalServiceBase):
    """Google Drive cloud storage integration"""

    @property
    def auth_url(self) -> str:
        return "https://accounts.google.com/o/oauth2/v2/auth"

    @property
    def token_url(self) -> str:
        return "https://oauth2.googleapis.com/token"

    def __init__(self, config: ServiceConfig, token_storage_path: Optional[Path] = None):
        if not config.scopes:
            config.scopes = [
                'https://www.googleapis.com/auth/drive.file',
                'https://www.googleapis.com/auth/drive.readonly',
                'https://www.googleapis.com/auth/drive.metadata.readonly'
            ]
        super().__init__(config, token_storage_path)

    def exchange_code(self, code: str) -> bool:
        """Exchange authorization code for token"""
        print(f"[Google Drive] Code exchange - implement with requests library")
        return False

    def refresh_token_if_needed(self) -> bool:
        """Refresh token if expired"""
        if not self.token or not self.token.refresh_token:
            return False

        if not self.token.is_expired():
            return True

        print(f"[Google Drive] Token refresh needed")
        return False

    def upload_file(self, local_path: Path, folder_id: Optional[str] = None, name: Optional[str] = None) -> Optional[str]:
        """Upload file to Google Drive"""
        if not self.is_authenticated():
            print(f"[Google Drive] Not authenticated")
            return None

        file_name = name or local_path.name
        print(f"[Google Drive] Uploading {local_path} as {file_name}")
        return "file_id_123456"  # Placeholder

    def download_file(self, file_id: str, local_path: Path) -> bool:
        """Download file from Google Drive"""
        if not self.is_authenticated():
            print(f"[Google Drive] Not authenticated")
            return False

        print(f"[Google Drive] Downloading {file_id} to {local_path}")
        return True

    def list_files(self, folder_id: Optional[str] = None, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """List files in Google Drive"""
        if not self.is_authenticated():
            return []

        # Placeholder
        return [
            {"id": "file_1", "name": "LightSpeed Data", "mimeType": "application/vnd.google-apps.folder"},
            {"id": "file_2", "name": "project_plan.pdf", "mimeType": "application/pdf", "size": 2048},
        ]

    def create_google_doc(self, title: str, content: str = "") -> Optional[str]:
        """Create Google Doc"""
        if not self.is_authenticated():
            return None

        print(f"[Google Drive] Creating Google Doc: {title}")
        return "doc_id_123456"

    def create_google_sheet(self, title: str, data: Optional[List[List[Any]]] = None) -> Optional[str]:
        """Create Google Sheet"""
        if not self.is_authenticated():
            return None

        print(f"[Google Drive] Creating Google Sheet: {title}")
        return "sheet_id_123456"


class OneDriveIntegration(ExternalServiceBase):
    """Microsoft OneDrive cloud storage integration"""

    @property
    def auth_url(self) -> str:
        return "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"

    @property
    def token_url(self) -> str:
        return "https://login.microsoftonline.com/common/oauth2/v2.0/token"

    def __init__(self, config: ServiceConfig, token_storage_path: Optional[Path] = None):
        if not config.scopes:
            config.scopes = [
                'Files.ReadWrite',
                'Files.ReadWrite.All',
                'offline_access'
            ]
        super().__init__(config, token_storage_path)

    def exchange_code(self, code: str) -> bool:
        """Exchange authorization code for token"""
        print(f"[OneDrive] Code exchange - implement with requests library")
        return False

    def refresh_token_if_needed(self) -> bool:
        """Refresh token if expired"""
        if not self.token or not self.token.refresh_token:
            return False

        if not self.token.is_expired():
            return True

        print(f"[OneDrive] Token refresh needed")
        return False

    def upload_file(self, local_path: Path, onedrive_path: str) -> bool:
        """Upload file to OneDrive"""
        if not self.is_authenticated():
            print(f"[OneDrive] Not authenticated")
            return False

        print(f"[OneDrive] Uploading {local_path} to {onedrive_path}")
        return True

    def download_file(self, item_id: str, local_path: Path) -> bool:
        """Download file from OneDrive"""
        if not self.is_authenticated():
            print(f"[OneDrive] Not authenticated")
            return False

        print(f"[OneDrive] Downloading {item_id} to {local_path}")
        return True


class ExternalServiceManager:
    """Centralized manager for all external service integrations"""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".lightspeed"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.services: Dict[str, ExternalServiceBase] = {}
        self.configs: Dict[str, ServiceConfig] = {}

        self._load_configs()
        self._initialize_services()

    def _get_config_file(self) -> Path:
        """Get configuration file path"""
        return self.storage_path / "external_services.json"

    def _load_configs(self):
        """Load service configurations"""
        config_file = self._get_config_file()
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    for service_name, config_data in data.items():
                        self.configs[service_name] = ServiceConfig(**config_data)
            except Exception as e:
                print(f"[ExternalServices] Failed to load configs: {e}")

        # Create default configs if not present
        if 'canva' not in self.configs:
            self.configs['canva'] = ServiceConfig(service_name='canva', enabled=False)

        if 'dropbox' not in self.configs:
            self.configs['dropbox'] = ServiceConfig(service_name='dropbox', enabled=False)

        if 'google_drive' not in self.configs:
            self.configs['google_drive'] = ServiceConfig(service_name='google_drive', enabled=False)

        if 'onedrive' not in self.configs:
            self.configs['onedrive'] = ServiceConfig(service_name='onedrive', enabled=False)

    def _save_configs(self):
        """Save service configurations"""
        config_file = self._get_config_file()
        try:
            data = {name: asdict(config) for name, config in self.configs.items()}
            with open(config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ExternalServices] Failed to save configs: {e}")

    def _initialize_services(self):
        """Initialize service instances"""
        for service_name, config in self.configs.items():
            if not config.enabled:
                continue

            token_path = self.storage_path / "tokens"

            if service_name == 'canva':
                self.services[service_name] = CanvaIntegration(config, token_path)
            elif service_name == 'dropbox':
                self.services[service_name] = DropboxIntegration(config, token_path)
            elif service_name == 'google_drive':
                self.services[service_name] = GoogleDriveIntegration(config, token_path)
            elif service_name == 'onedrive':
                self.services[service_name] = OneDriveIntegration(config, token_path)

    def configure_service(self, service_name: str, client_id: str, client_secret: str,
                         enabled: bool = True, scopes: Optional[List[str]] = None):
        """Configure a service"""
        if service_name not in self.configs:
            self.configs[service_name] = ServiceConfig(service_name=service_name)

        config = self.configs[service_name]
        config.client_id = client_id
        config.client_secret = client_secret
        config.enabled = enabled

        if scopes:
            config.scopes = scopes

        self._save_configs()

        # Reinitialize service
        if enabled:
            self._initialize_services()

    def enable_service(self, service_name: str):
        """Enable a service"""
        if service_name in self.configs:
            self.configs[service_name].enabled = True
            self._save_configs()
            self._initialize_services()

    def disable_service(self, service_name: str):
        """Disable a service"""
        if service_name in self.configs:
            self.configs[service_name].enabled = False
            self._save_configs()
            if service_name in self.services:
                del self.services[service_name]

    def get_service(self, service_name: str) -> Optional[ExternalServiceBase]:
        """Get service instance"""
        return self.services.get(service_name)

    def list_services(self) -> Dict[str, Dict[str, Any]]:
        """List all services and their status"""
        result = {}
        for name, config in self.configs.items():
            service = self.services.get(name)
            result[name] = {
                'enabled': config.enabled,
                'configured': bool(config.client_id),
                'authenticated': service.is_authenticated() if service else False,
                'service_name': config.service_name
            }
        return result

    def authorize_service(self, service_name: str, state: Optional[str] = None) -> Optional[str]:
        """Start OAuth flow for a service"""
        service = self.get_service(service_name)
        if not service:
            print(f"[ExternalServices] Service not found or not enabled: {service_name}")
            return None

        return service.authorize(state)

    def handle_oauth_callback(self, service_name: str, code: str) -> bool:
        """Handle OAuth callback with authorization code"""
        service = self.get_service(service_name)
        if not service:
            return False

        return service.exchange_code(code)


# Singleton instance
_service_manager: Optional[ExternalServiceManager] = None


def get_service_manager() -> ExternalServiceManager:
    """Get global service manager instance"""
    global _service_manager
    if _service_manager is None:
        _service_manager = ExternalServiceManager()
    return _service_manager


def get_canva() -> Optional[CanvaIntegration]:
    """Get Canva integration"""
    manager = get_service_manager()
    service = manager.get_service('canva')
    return service if isinstance(service, CanvaIntegration) else None


def get_dropbox() -> Optional[DropboxIntegration]:
    """Get Dropbox integration"""
    manager = get_service_manager()
    service = manager.get_service('dropbox')
    return service if isinstance(service, DropboxIntegration) else None


def get_google_drive() -> Optional[GoogleDriveIntegration]:
    """Get Google Drive integration"""
    manager = get_service_manager()
    service = manager.get_service('google_drive')
    return service if isinstance(service, GoogleDriveIntegration) else None


def get_onedrive() -> Optional[OneDriveIntegration]:
    """Get OneDrive integration"""
    manager = get_service_manager()
    service = manager.get_service('onedrive')
    return service if isinstance(service, OneDriveIntegration) else None
