"""
LightSpeed V0.9.5 - Unified Component Registry
Cross-floor, cross-project component access system

Purpose:
- Central registry for all UI components
- Categorized organization (display, input, data, visualization, simulation, navigation)
- Accessible from any Z-floor or project
- Version tracking and component discovery

Author: LightSpeed Team
Version: 0.9.5
Date: January 3, 2026
"""

from typing import Dict, List, Type, Optional, Any, Callable
from pathlib import Path
import inspect


class ComponentInfo:
    """Metadata for a registered component"""

    def __init__(self, name: str, component_class: Type, category: str,
                 version: str = "1.0.0", description: str = ""):
        self.name = name
        self.component_class = component_class
        self.category = category
        self.version = version
        self.description = description
        self.file_path = inspect.getfile(component_class) if hasattr(component_class, '__module__') else None

    def __repr__(self):
        return f"<Component: {self.name} v{self.version} [{self.category}]>"


class ComponentRegistry:
    """
    Global registry for all LightSpeed UI components.

    Accessible from any Z-floor (Neo, Morpheus, Oracle, Smith, etc.) or any project.

    Categories:
    - display: Cards, panels, stat displays
    - input: Buttons, search bars, filters, forms
    - data: Lists, tables, trees, file browsers
    - visualization: Charts, graphs, progress bars, meters
    - simulation: Physics launchers, result viewers, parameter forms
    - navigation: Tabs, breadcrumbs, menus, floor selectors

    Usage:
        from core.ui.components.registry import ComponentRegistry

        # Get a component
        ProgressBar = ComponentRegistry.get('ProgressBar')
        progress = ProgressBar(parent, mode='determinate')

        # List components by category
        viz_components = ComponentRegistry.list_by_category('visualization')

        # Get all components
        all_components = ComponentRegistry.get_all()
    """

    _components: Dict[str, ComponentInfo] = {}
    _categories: Dict[str, List[str]] = {
        'display': [],
        'input': [],
        'data': [],
        'visualization': [],
        'simulation': [],
        'navigation': []
    }
    _initialized = False

    @classmethod
    def register(cls, name: str, component_class: Type, category: str,
                 version: str = "1.0.0", description: str = "") -> None:
        """
        Register a component in the global registry.

        Args:
            name: Component name (e.g., 'ProgressBar', 'LayeredCard')
            component_class: The component class
            category: Component category (display, input, data, visualization, simulation, navigation)
            version: Component version (default: "1.0.0")
            description: Brief description of the component
        """
        if category not in cls._categories:
            raise ValueError(f"Invalid category '{category}'. Must be one of: {list(cls._categories.keys())}")

        info = ComponentInfo(name, component_class, category, version, description)
        cls._components[name] = info

        if name not in cls._categories[category]:
            cls._categories[category].append(name)

    @classmethod
    def get(cls, name: str) -> Optional[Type]:
        """
        Get a component class by name.

        Args:
            name: Component name

        Returns:
            Component class or None if not found
        """
        info = cls._components.get(name)
        return info.component_class if info else None

    @classmethod
    def get_info(cls, name: str) -> Optional[ComponentInfo]:
        """
        Get component metadata.

        Args:
            name: Component name

        Returns:
            ComponentInfo or None if not found
        """
        return cls._components.get(name)

    @classmethod
    def list_by_category(cls, category: str) -> List[str]:
        """
        List all component names in a category.

        Args:
            category: Category name

        Returns:
            List of component names
        """
        return cls._categories.get(category, []).copy()

    @classmethod
    def get_all(cls) -> Dict[str, Type]:
        """
        Get all registered components.

        Returns:
            Dictionary mapping component names to classes
        """
        return {name: info.component_class for name, info in cls._components.items()}

    @classmethod
    def get_all_info(cls) -> Dict[str, ComponentInfo]:
        """
        Get all component metadata.

        Returns:
            Dictionary mapping component names to ComponentInfo
        """
        return cls._components.copy()

    @classmethod
    def list_categories(cls) -> List[str]:
        """
        Get all available categories.

        Returns:
            List of category names
        """
        return list(cls._categories.keys())

    @classmethod
    def count(cls) -> int:
        """
        Get total number of registered components.

        Returns:
            Component count
        """
        return len(cls._components)

    @classmethod
    def count_by_category(cls, category: str) -> int:
        """
        Get number of components in a category.

        Args:
            category: Category name

        Returns:
            Component count in category
        """
        return len(cls._categories.get(category, []))

    @classmethod
    def search(cls, query: str) -> List[str]:
        """
        Search for components by name (case-insensitive).

        Args:
            query: Search query

        Returns:
            List of matching component names
        """
        query_lower = query.lower()
        return [name for name in cls._components.keys() if query_lower in name.lower()]

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        Check if a component is registered.

        Args:
            name: Component name

        Returns:
            True if registered, False otherwise
        """
        return name in cls._components

    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        Unregister a component (use with caution).

        Args:
            name: Component name

        Returns:
            True if unregistered, False if not found
        """
        if name not in cls._components:
            return False

        info = cls._components[name]
        del cls._components[name]

        if name in cls._categories[info.category]:
            cls._categories[info.category].remove(name)

        return True

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry stats
        """
        return {
            'total_components': cls.count(),
            'categories': cls.list_categories(),
            'by_category': {cat: cls.count_by_category(cat) for cat in cls.list_categories()},
            'initialized': cls._initialized
        }

    @classmethod
    def print_registry(cls) -> None:
        """Print formatted registry contents (for debugging)"""
        print("=" * 70)
        print("LIGHTSPEED COMPONENT REGISTRY")
        print("=" * 70)
        print(f"\nTotal Components: {cls.count()}\n")

        for category in sorted(cls.list_categories()):
            components = cls.list_by_category(category)
            print(f"\n{category.upper()} ({len(components)}):")
            for name in sorted(components):
                info = cls.get_info(name)
                print(f"  - {name} v{info.version}")
                if info.description:
                    print(f"    {info.description}")

        print("\n" + "=" * 70)


# Convenience function for quick access
def get_component(name: str) -> Optional[Type]:
    """
    Quick access to get a component class.

    Args:
        name: Component name

    Returns:
        Component class or None
    """
    return ComponentRegistry.get(name)


# Export public API
__all__ = ['ComponentRegistry', 'ComponentInfo', 'get_component']
