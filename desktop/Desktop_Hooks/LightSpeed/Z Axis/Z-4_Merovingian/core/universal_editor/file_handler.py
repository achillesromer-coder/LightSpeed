"""
File Handler Base Class - V1.0.0
Abstract base class for all file type handlers

Author: LightSpeed Team
Date: December 27, 2025
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import tkinter as tk


# ==============================================================================
# Editor Capabilities
# ==============================================================================

class EditorCapability(Enum):
    """Capabilities that a file handler can provide"""
    READ = "read"
    WRITE = "write"
    SYNTAX_HIGHLIGHT = "syntax_highlight"
    AUTO_COMPLETE = "auto_complete"
    GO_TO_DEFINITION = "go_to_definition"
    FIND_REFERENCES = "find_references"
    FORMAT = "format"
    LINT = "lint"
    PREVIEW = "preview"
    LIVE_PREVIEW = "live_preview"
    SPLIT_VIEW = "split_view"
    FOLD = "fold"
    MINIMAP = "minimap"
    SEARCH = "search"
    REPLACE = "replace"
    UNDO_REDO = "undo_redo"


# ==============================================================================
# Editor Actions
# ==============================================================================

@dataclass
class EditorAction:
    """
    Represents an editor action for toolbars/menus

    Attributes:
        action_id: Unique identifier
        label: Display label
        icon: Icon path (optional)
        callback: Function to call
        shortcut: Keyboard shortcut
        enabled: Whether action is enabled
        tooltip: Tooltip text
    """
    action_id: str
    label: str
    callback: Callable
    icon: Optional[str] = None
    shortcut: Optional[str] = None
    enabled: bool = True
    tooltip: str = ""


# ==============================================================================
# File Handler Base
# ==============================================================================

class FileHandler(ABC):
    """
    Abstract base class for file type handlers

    Each file type (text, code, data, etc.) implements this interface
    to provide editing capabilities specific to that type.
    """

    def __init__(self):
        """Initialize file handler"""
        self.capabilities: List[EditorCapability] = []
        self.supported_extensions: List[str] = []
        self.file_type_name: str = "Unknown"

    # ==========================================================================
    # Abstract Methods - Must be implemented by subclasses
    # ==========================================================================

    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """
        Check if this handler can handle the given file

        Args:
            file_path: Path to file

        Returns:
            True if this handler supports the file type
        """
        pass

    @abstractmethod
    def read_file(self, file_path: Path) -> str:
        """
        Read file content

        Args:
            file_path: Path to file

        Returns:
            File content as string

        Raises:
            IOError: If file cannot be read
        """
        pass

    @abstractmethod
    def write_file(self, file_path: Path, content: str) -> bool:
        """
        Write content to file

        Args:
            file_path: Path to file
            content: Content to write

        Returns:
            True if successful

        Raises:
            IOError: If file cannot be written
        """
        pass

    @abstractmethod
    def create_editor_widget(
        self,
        parent: tk.Widget,
        file_path: Path,
        content: str,
        **kwargs
    ) -> tk.Widget:
        """
        Create the editor widget for this file type

        Args:
            parent: Parent widget
            file_path: Path to file being edited
            content: Initial file content
            **kwargs: Additional options

        Returns:
            Editor widget (Text, Canvas, Frame, etc.)
        """
        pass

    @abstractmethod
    def get_content_from_widget(self, widget: tk.Widget) -> str:
        """
        Extract current content from editor widget

        Args:
            widget: Editor widget

        Returns:
            Current content as string
        """
        pass

    @abstractmethod
    def get_toolbar_actions(self) -> List[EditorAction]:
        """
        Get toolbar actions for this file type

        Returns:
            List of EditorAction objects
        """
        pass

    # ==========================================================================
    # Optional Methods - Can be overridden by subclasses
    # ==========================================================================

    def has_capability(self, capability: EditorCapability) -> bool:
        """
        Check if handler has a specific capability

        Args:
            capability: Capability to check

        Returns:
            True if handler supports this capability
        """
        return capability in self.capabilities

    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get metadata about the file

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file metadata
        """
        try:
            stat = file_path.stat()
            return {
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'extension': file_path.suffix,
                'name': file_path.name,
                'type': self.file_type_name
            }
        except Exception as e:
            return {
                'error': str(e),
                'type': self.file_type_name
            }

    def validate_content(self, content: str) -> tuple[bool, List[str]]:
        """
        Validate file content

        Args:
            content: Content to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        return True, []

    def format_content(self, content: str) -> str:
        """
        Format/prettify content

        Args:
            content: Content to format

        Returns:
            Formatted content
        """
        return content

    def get_syntax_highlighting_config(self) -> Optional[Dict[str, Any]]:
        """
        Get syntax highlighting configuration

        Returns:
            Configuration dict or None if not supported
        """
        return None

    def get_autocomplete_suggestions(
        self,
        content: str,
        cursor_position: int
    ) -> List[str]:
        """
        Get autocomplete suggestions at cursor position

        Args:
            content: Current content
            cursor_position: Cursor position

        Returns:
            List of suggestions
        """
        return []

    def on_content_changed(self, widget: tk.Widget, content: str):
        """
        Called when content changes (for live preview, validation, etc.)

        Args:
            widget: Editor widget
            content: New content
        """
        pass

    def on_save(self, file_path: Path, content: str):
        """
        Called after successful save

        Args:
            file_path: Path to saved file
            content: Saved content
        """
        pass

    def on_close(self):
        """Called when editor is closed"""
        pass

    def search(self, widget: tk.Widget, query: str, case_sensitive: bool = False) -> List[tuple]:
        """
        Search for text in content

        Args:
            widget: Editor widget
            query: Search query
            case_sensitive: Whether search is case-sensitive

        Returns:
            List of (start_pos, end_pos) tuples
        """
        if not isinstance(widget, tk.Text):
            return []

        matches = []
        content = widget.get("1.0", tk.END)

        if not case_sensitive:
            content = content.lower()
            query = query.lower()

        start_idx = 0
        while True:
            start_idx = content.find(query, start_idx)
            if start_idx == -1:
                break

            # Convert to line.column format
            lines = content[:start_idx].split('\n')
            line = len(lines)
            col = len(lines[-1])

            end_idx = start_idx + len(query)
            end_lines = content[:end_idx].split('\n')
            end_line = len(end_lines)
            end_col = len(end_lines[-1])

            matches.append((f"{line}.{col}", f"{end_line}.{end_col}"))
            start_idx = end_idx

        return matches

    def replace(
        self,
        widget: tk.Widget,
        old_text: str,
        new_text: str,
        case_sensitive: bool = False,
        all_occurrences: bool = False
    ) -> int:
        """
        Replace text in content

        Args:
            widget: Editor widget
            old_text: Text to replace
            new_text: Replacement text
            case_sensitive: Whether replacement is case-sensitive
            all_occurrences: Replace all or just first

        Returns:
            Number of replacements made
        """
        if not isinstance(widget, tk.Text):
            return 0

        matches = self.search(widget, old_text, case_sensitive)

        if not matches:
            return 0

        if not all_occurrences:
            matches = [matches[0]]

        # Replace in reverse order to maintain positions
        for start, end in reversed(matches):
            widget.delete(start, end)
            widget.insert(start, new_text)

        return len(matches)


# ==============================================================================
# Handler Registry
# ==============================================================================

class FileHandlerRegistry:
    """
    Registry of all available file handlers

    Manages file type detection and handler selection
    """

    def __init__(self):
        """Initialize registry"""
        self.handlers: List[FileHandler] = []
        self.extension_map: Dict[str, FileHandler] = {}

    def register_handler(self, handler: FileHandler):
        """
        Register a file handler

        Args:
            handler: FileHandler instance
        """
        self.handlers.append(handler)

        # Build extension map
        for ext in handler.supported_extensions:
            self.extension_map[ext.lower()] = handler

    def get_handler(self, file_path: Path) -> Optional[FileHandler]:
        """
        Get appropriate handler for file

        Args:
            file_path: Path to file

        Returns:
            FileHandler instance or None
        """
        # Try extension mapping first (fast)
        ext = file_path.suffix.lower()
        if ext in self.extension_map:
            return self.extension_map[ext]

        # Fall back to can_handle check
        for handler in self.handlers:
            if handler.can_handle(file_path):
                return handler

        return None

    def get_supported_extensions(self) -> List[str]:
        """
        Get list of all supported extensions

        Returns:
            List of file extensions
        """
        return list(self.extension_map.keys())


# ==============================================================================
# Factory Function
# ==============================================================================

def create_handler_registry() -> FileHandlerRegistry:
    """
    Create and populate file handler registry

    Returns:
        FileHandlerRegistry with all handlers registered
    """
    registry = FileHandlerRegistry()

    # Import and register handlers
    try:
        from .text_handler import TextFileHandler
        registry.register_handler(TextFileHandler())
    except ImportError:
        pass

    try:
        from .code_handler import CodeFileHandler
        registry.register_handler(CodeFileHandler())
    except ImportError:
        pass

    try:
        from .data_handler import DataFileHandler
        registry.register_handler(DataFileHandler())
    except ImportError:
        pass

    try:
        from .document_handler import DocumentFileHandler
        registry.register_handler(DocumentFileHandler())
    except ImportError:
        pass

    try:
        from .image_handler import ImageFileHandler
        registry.register_handler(ImageFileHandler())
    except ImportError:
        pass

    try:
        from .latex_handler import LaTeXFileHandler
        registry.register_handler(LaTeXFileHandler())
    except ImportError:
        pass

    try:
        from .notebook_handler import NotebookFileHandler
        registry.register_handler(NotebookFileHandler())
    except ImportError:
        pass

    return registry
