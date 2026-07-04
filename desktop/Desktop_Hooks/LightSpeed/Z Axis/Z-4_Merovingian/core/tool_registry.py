#!/usr/bin/env python
"""
Universal Tool Registry - Central Registration for All LightSpeed Tools
Consolidates tool discovery and management across all Z-floors
"""

from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ToolCategory(Enum):
    """Tool categories for organization and filtering"""
    DOCUMENT_PROCESSING = "document_processing"
    AI_ASSISTANT = "ai_assistant"
    WORKFLOW_AUTOMATION = "workflow_automation"
    DATABASE_MANAGEMENT = "database_management"
    UI_DESIGN = "ui_design"
    PHYSICS_SIMULATION = "physics_simulation"
    CODE_COMPLETION = "code_completion"
    ANALYTICS = "analytics"
    FILE_MANAGEMENT = "file_management"
    SCHEMA_MANAGEMENT = "schema_management"
    VISUALIZATION = "visualization"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    SECURITY = "security"
    NETWORKING = "networking"


class ToolStatus(Enum):
    """Tool availability status"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    LOADING = "loading"
    ERROR = "error"
    DEPRECATED = "deprecated"


@dataclass
class ToolDescriptor:
    """
    Complete description of a tool

    Attributes:
        name: Tool identifier (unique within floor)
        floor: Floor name where tool resides
        category: Tool category
        path: Absolute or relative path to tool
        description: User-facing description
        entry_point: Callable to launch tool
        requires_gpu: Whether tool needs GPU
        requires_network: Whether tool needs network access
        requires_services: List of required services (db, event_bus, storage)
        version: Tool version string
        author: Tool author/maintainer
        status: Current tool status
        config: Additional configuration dict
        dependencies: List of Python package dependencies
        icon: Path to tool icon (optional)
        shortcuts: Keyboard shortcuts (optional)
    """
    name: str
    floor: str
    category: ToolCategory
    path: str
    description: str
    entry_point: Callable
    requires_gpu: bool = False
    requires_network: bool = False
    requires_services: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = "LightSpeed Team"
    status: ToolStatus = ToolStatus.AVAILABLE
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    icon: Optional[str] = None
    shortcuts: List[str] = field(default_factory=list)

    def get_full_name(self) -> str:
        """Get fully qualified tool name"""
        return f"{self.floor}.{self.name}"

    def is_available(self) -> bool:
        """Check if tool is available for use"""
        return self.status == ToolStatus.AVAILABLE

    def check_dependencies(self) -> bool:
        """
        Check if all required dependencies are installed

        Returns:
            True if all dependencies available
        """
        if not self.dependencies:
            return True

        try:
            for dep in self.dependencies:
                __import__(dep)
            return True
        except ImportError:
            return False


class UniversalToolRegistry:
    """
    Singleton registry for all LightSpeed tools

    Provides:
    - Central tool registration
    - Tool discovery by category/floor/name
    - Tool status management
    - Tool launch coordination
    - Dependency checking
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.tools: Dict[str, ToolDescriptor] = {}
        self._by_category: Dict[ToolCategory, List[ToolDescriptor]] = {}
        self._by_floor: Dict[str, List[ToolDescriptor]] = {}
        self._initialized = True

    def register_tool(self, tool: ToolDescriptor):
        """
        Register a tool in the registry

        Args:
            tool: ToolDescriptor instance

        Raises:
            ValueError: If tool with same full name already registered
        """
        key = tool.get_full_name()

        if key in self.tools:
            raise ValueError(f"Tool {key} already registered")

        self.tools[key] = tool

        if tool.category not in self._by_category:
            self._by_category[tool.category] = []
        self._by_category[tool.category].append(tool)

        if tool.floor not in self._by_floor:
            self._by_floor[tool.floor] = []
        self._by_floor[tool.floor].append(tool)

    def unregister_tool(self, floor: str, name: str):
        """
        Unregister a tool

        Args:
            floor: Floor name
            name: Tool name
        """
        key = f"{floor}.{name}"

        if key not in self.tools:
            return

        tool = self.tools[key]
        del self.tools[key]

        if tool.category in self._by_category:
            self._by_category[tool.category].remove(tool)

        if tool.floor in self._by_floor:
            self._by_floor[tool.floor].remove(tool)

    def get_tool(self, floor: str, name: str) -> Optional[ToolDescriptor]:
        """
        Get tool by floor and name

        Args:
            floor: Floor name
            name: Tool name

        Returns:
            ToolDescriptor or None if not found
        """
        return self.tools.get(f"{floor}.{name}")

    def get_tools_by_category(
        self,
        category: ToolCategory
    ) -> List[ToolDescriptor]:
        """
        Get all tools in a category

        Args:
            category: ToolCategory enum value

        Returns:
            List of tools in category
        """
        return self._by_category.get(category, []).copy()

    def get_tools_by_floor(self, floor: str) -> List[ToolDescriptor]:
        """
        Get all tools from a specific floor

        Args:
            floor: Floor name

        Returns:
            List of tools from floor
        """
        return self._by_floor.get(floor, []).copy()

    def get_all_tools(self) -> List[ToolDescriptor]:
        """
        Get all registered tools

        Returns:
            List of all tools
        """
        return list(self.tools.values())

    def get_available_tools(self) -> List[ToolDescriptor]:
        """
        Get all available tools (status == AVAILABLE)

        Returns:
            List of available tools
        """
        return [t for t in self.tools.values() if t.is_available()]

    def search_tools(
        self,
        query: str,
        category: Optional[ToolCategory] = None,
        floor: Optional[str] = None
    ) -> List[ToolDescriptor]:
        """
        Search tools by query string

        Args:
            query: Search query (matches name or description)
            category: Optional category filter
            floor: Optional floor filter

        Returns:
            List of matching tools
        """
        query_lower = query.lower()
        results = []

        for tool in self.tools.values():
            if category and tool.category != category:
                continue
            if floor and tool.floor != floor:
                continue

            if (query_lower in tool.name.lower() or
                    query_lower in tool.description.lower()):
                results.append(tool)

        return results

    def launch_tool(
        self,
        floor: str,
        name: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Launch a tool by calling its entry point

        Args:
            floor: Floor name
            name: Tool name
            *args: Positional arguments to pass to tool
            **kwargs: Keyword arguments to pass to tool

        Returns:
            Tool return value

        Raises:
            ValueError: If tool not found
            RuntimeError: If tool not available or dependencies missing
        """
        tool = self.get_tool(floor, name)

        if not tool:
            raise ValueError(f"Tool {floor}.{name} not found")

        if not tool.is_available():
            raise RuntimeError(f"Tool {floor}.{name} not available (status: {tool.status})")

        if not tool.check_dependencies():
            raise RuntimeError(f"Tool {floor}.{name} missing dependencies: {tool.dependencies}")

        return tool.entry_point(*args, **kwargs)

    def update_tool_status(
        self,
        floor: str,
        name: str,
        status: ToolStatus
    ):
        """
        Update tool status

        Args:
            floor: Floor name
            name: Tool name
            status: New status
        """
        tool = self.get_tool(floor, name)
        if tool:
            tool.status = status

    def get_categories(self) -> List[ToolCategory]:
        """
        Get all categories with registered tools

        Returns:
            List of categories
        """
        return list(self._by_category.keys())

    def get_floors(self) -> List[str]:
        """
        Get all floors with registered tools

        Returns:
            List of floor names
        """
        return list(self._by_floor.keys())

    def get_tool_count(self) -> int:
        """
        Get total number of registered tools

        Returns:
            Tool count
        """
        return len(self.tools)

    def export_registry(self) -> Dict[str, Any]:
        """
        Export registry as JSON-serializable dict

        Returns:
            Dict with all tool metadata (excluding entry_point)
        """
        return {
            'tool_count': self.get_tool_count(),
            'categories': [c.value for c in self.get_categories()],
            'floors': self.get_floors(),
            'tools': [
                {
                    'name': tool.name,
                    'floor': tool.floor,
                    'category': tool.category.value,
                    'path': tool.path,
                    'description': tool.description,
                    'version': tool.version,
                    'author': tool.author,
                    'status': tool.status.value,
                    'requires_gpu': tool.requires_gpu,
                    'requires_network': tool.requires_network,
                    'requires_services': tool.requires_services,
                    'dependencies': tool.dependencies,
                }
                for tool in self.tools.values()
            ]
        }


def get_tool_registry() -> UniversalToolRegistry:
    """
    Get the singleton tool registry instance

    Returns:
        UniversalToolRegistry instance
    """
    return UniversalToolRegistry()


def register_tool(
    name: str,
    floor: str,
    category: ToolCategory,
    entry_point: Callable,
    **kwargs
) -> ToolDescriptor:
    """
    Convenience function to create and register a tool

    Args:
        name: Tool name
        floor: Floor name
        category: Tool category
        entry_point: Tool entry point callable
        **kwargs: Additional ToolDescriptor fields

    Returns:
        Created ToolDescriptor

    Usage:
        register_tool(
            "enhanced_wizard",
            "Trinity",
            ToolCategory.UI_DESIGN,
            lambda: run_wizard(),
            description="Complete setup wizard"
        )
    """
    path = kwargs.pop('path', f"Z Axis/{floor}/tools/{name}.py")
    description = kwargs.pop('description', f"{name} tool")

    tool = ToolDescriptor(
        name=name,
        floor=floor,
        category=category,
        path=path,
        description=description,
        entry_point=entry_point,
        **kwargs
    )

    registry = get_tool_registry()
    registry.register_tool(tool)

    return tool
