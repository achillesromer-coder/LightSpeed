"""
Universal Editor System - V1.0.0
Multi-format file editor with spherical UI integration

Supports:
- Text files (TXT, MD, etc.)
- Code files (Python, JavaScript, Java, C++, etc.)
- Data files (JSON, YAML, CSV, XML)
- Documents (PDF preview, DOCX)
- Images (view and annotate)
- CAD files (preview)
- LaTeX (with live preview)
- Jupyter notebooks

Features:
- Monaco Editor integration for code
- Language Server Protocol (LSP) support
- Syntax highlighting for 50+ languages
- Real-time preview
- Spherical UI layout
- Context-aware toolbars
- Multi-file editing
- Split view support

Author: LightSpeed Team
Date: December 27, 2025
"""

from .universal_editor import (
    UniversalEditor,
    EditorSession,
    create_editor
)

from .file_handler import (
    FileHandler,
    EditorCapability
)

from .text_handler import TextFileHandler
from .code_handler import CodeFileHandler
from .data_handler import DataFileHandler
from .document_handler import DocumentFileHandler

__all__ = [
    # Main editor
    'UniversalEditor',
    'EditorSession',
    'create_editor',

    # File handlers
    'FileHandler',
    'EditorCapability',
    'TextFileHandler',
    'CodeFileHandler',
    'DataFileHandler',
    'DocumentFileHandler',
]
