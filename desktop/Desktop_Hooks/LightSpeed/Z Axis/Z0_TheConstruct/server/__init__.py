"""
LightSpeed Platform - Web Server Module
Provides FastAPI-based web interface with Three.js visualization
"""

from .web_server import create_app, start_server

__all__ = ['create_app', 'start_server']
