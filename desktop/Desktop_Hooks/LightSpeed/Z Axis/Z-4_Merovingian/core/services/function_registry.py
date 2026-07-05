#!/usr/bin/env python
"""
Function & Library Registry - Centralized Access Management
Provides IT portal with complete access to all available functions and libraries

This registry consolidates:
- Installed Python libraries with versions and locations
- LightSpeed functions across all Z-floors
- Component capabilities and tools
- Integration points for external services
- Dynamic function discovery and invocation

Clean Code: Single source of truth for function/library access
Version: 0.9.5
Date: December 20, 2025
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import importlib
import importlib.util
import inspect
import sys


def _resolve_lightspeed_root(candidate: Optional[Path] = None) -> Path:
    """Resolve the LightSpeed application root from any nested service path."""
    start = (candidate or Path(__file__)).resolve()
    if start.is_file():
        start = start.parent

    for path in (start, *start.parents):
        if (path / "N.py").exists() and (path / "Z Axis").exists():
            return path

    # Fallback for the canonical service location:
    # LightSpeed/Z Axis/Z-4_Merovingian/core/services/function_registry.py
    return Path(__file__).resolve().parents[4]


class FunctionCategory(Enum):
    """Function categories for organization"""
    DATA_PROCESSING = "data_processing"
    VISUALIZATION = "visualization"
    AI_ML = "ai_ml"
    DATABASE = "database"
    API = "api"
    TESTING = "testing"
    AUTOMATION = "automation"
    UI_WIDGETS = "ui_widgets"
    FLOOR_OPERATIONS = "floor_operations"
    SYSTEM = "system"


@dataclass
class LibraryInfo:
    """Information about an installed library"""
    name: str
    available: bool
    version: str = "unknown"
    location: str = "unknown"
    description: str = ""
    dependencies: List[str] = field(default_factory=list)


@dataclass
class FunctionInfo:
    """Information about a LightSpeed function"""
    id: str
    name: str
    category: FunctionCategory
    floor: str
    module: str
    description: str = ""
    parameters: List[Dict[str, str]] = field(default_factory=list)
    returns: str = ""
    example: str = ""
    callable_ref: Optional[Callable] = None


class FunctionLibraryRegistry:
    """
    Central registry for all functions and libraries

    Responsibilities:
    - Discover and catalog installed libraries
    - Scan Z-floors for available functions
    - Provide search and access to functions
    - Enable dynamic function invocation
    - Settings panel integration for IT portal
    """

    def __init__(self, lightspeed_root: Path):
        self.lightspeed_root = _resolve_lightspeed_root(lightspeed_root)
        self.libraries: Dict[str, LibraryInfo] = {}
        self.functions: Dict[str, FunctionInfo] = {}

        # Load cached registry if available
        self._load_cache()

    def scan_all(self):
        """Scan for all libraries and functions"""
        print("[FunctionRegistry] Scanning system...")
        self.scan_libraries()
        self.scan_functions()
        self._save_cache()
        print(f"[FunctionRegistry] Found {len(self.libraries)} libraries, {len(self.functions)} functions")

    def scan_libraries(self):
        """Scan for installed Python libraries"""
        common_libraries = [
            # Data Science
            ('numpy', 'Numerical computing library'),
            ('pandas', 'Data manipulation and analysis'),
            ('scipy', 'Scientific computing'),
            ('sklearn', 'Machine learning toolkit'),
            ('matplotlib', 'Plotting and visualization'),
            ('seaborn', 'Statistical data visualization'),

            # Web & API
            ('requests', 'HTTP library'),
            ('flask', 'Web framework'),
            ('fastapi', 'Modern API framework'),

            # Database
            ('sqlalchemy', 'SQL toolkit'),
            ('psycopg2', 'PostgreSQL adapter'),
            ('pymongo', 'MongoDB driver'),
            ('redis', 'Redis client'),

            # Testing & Quality
            ('pytest', 'Testing framework'),
            ('black', 'Code formatter'),
            ('pylint', 'Code analyzer'),
            ('mypy', 'Static type checker'),

            # Async & Task Queue
            ('asyncio', 'Asynchronous I/O'),
            ('celery', 'Distributed task queue'),

            # GUI
            ('tkinter', 'GUI toolkit'),
            ('PIL', 'Image processing'),

            # LightSpeed specific
            ('ollama', 'Ollama AI integration'),
        ]

        for lib_name, description in common_libraries:
            spec = importlib.util.find_spec(lib_name)

            if spec is not None:
                try:
                    mod = importlib.import_module(lib_name)
                    version = getattr(mod, '__version__', 'unknown')
                    location = spec.origin if spec.origin else 'unknown'

                    self.libraries[lib_name] = LibraryInfo(
                        name=lib_name,
                        available=True,
                        version=version,
                        location=location,
                        description=description
                    )
                except Exception as e:
                    self.libraries[lib_name] = LibraryInfo(
                        name=lib_name,
                        available=False,
                        description=description
                    )
            else:
                self.libraries[lib_name] = LibraryInfo(
                    name=lib_name,
                    available=False,
                    description=description
                )

    def scan_functions(self):
        """Scan Z-floors for available functions"""
        # Scan floor manifests
        z_axis_path = self.lightspeed_root / "Z Axis"
        if not z_axis_path.exists():
            return

        for floor_path in z_axis_path.iterdir():
            if not floor_path.is_dir() or not floor_path.name.startswith('Z'):
                continue

            manifest_path = floor_path / "_FLOOR_MANIFEST.json"
            if not manifest_path.exists():
                continue

            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)

                floor_name = manifest.get('floor_name', 'Unknown')
                components = manifest.get('components', [])

                for comp in components:
                    comp_id = comp.get('id', 'unknown')
                    module_path = comp.get('module', '')
                    category_str = comp.get('category', 'data_processing')

                    # Map category string to enum
                    try:
                        category = FunctionCategory(category_str)
                    except:
                        category = FunctionCategory.DATA_PROCESSING

                    func_info = FunctionInfo(
                        id=f"{floor_name.lower()}_{comp_id}",
                        name=comp_id.replace('_', ' ').title(),
                        category=category,
                        floor=floor_name,
                        module=module_path,
                        description=comp.get('description', f'{comp_id} from {floor_name}')
                    )

                    self.functions[func_info.id] = func_info

            except Exception as e:
                print(f"[FunctionRegistry] Error scanning {floor_path.name}: {e}")

        # Scan core services
        self._scan_core_services()

    def _scan_core_services(self):
        """Scan core services for functions"""
        core_path = self.lightspeed_root / "Z Axis" / "Z-4_Merovingian" / "core" / "services"
        if not core_path.exists():
            return

        for py_file in core_path.glob("*.py"):
            if py_file.name.startswith('_'):
                continue

            module_name = py_file.stem

            # Register key services
            service_functions = {
                'floor_loader': ('FloorLoader', 'Dynamic Z-floor component discovery'),
                'data_accumulation_engine': ('DataAccumulationEngine', 'Universal data object management'),
                'smart_floor_expansion': ('SmartFloorExpansionEngine', 'Autonomous capability development'),
            }

            if module_name in service_functions:
                class_name, description = service_functions[module_name]

                func_info = FunctionInfo(
                    id=f"core_{module_name}",
                    name=class_name,
                    category=FunctionCategory.FLOOR_OPERATIONS,
                    floor="Core",
                    module=f"core.services.{module_name}",
                    description=description
                )

                self.functions[func_info.id] = func_info

    def get_library(self, name: str) -> Optional[LibraryInfo]:
        """Get library information"""
        return self.libraries.get(name)

    def get_function(self, func_id: str) -> Optional[FunctionInfo]:
        """Get function information"""
        return self.functions.get(func_id)

    def search_functions(
        self,
        query: str = "",
        category: Optional[FunctionCategory] = None,
        floor: Optional[str] = None
    ) -> List[FunctionInfo]:
        """Search functions by query, category, or floor"""
        results = []

        for func in self.functions.values():
            # Category filter
            if category and func.category != category:
                continue

            # Floor filter
            if floor and func.floor != floor:
                continue

            # Query filter
            if query:
                query_lower = query.lower()
                if (query_lower in func.name.lower() or
                    query_lower in func.description.lower() or
                    query_lower in func.id.lower()):
                    results.append(func)
            else:
                results.append(func)

        return results

    def get_available_libraries(self) -> List[LibraryInfo]:
        """Get list of available libraries"""
        return [lib for lib in self.libraries.values() if lib.available]

    def get_unavailable_libraries(self) -> List[LibraryInfo]:
        """Get list of unavailable libraries"""
        return [lib for lib in self.libraries.values() if not lib.available]

    def get_functions_by_category(self) -> Dict[FunctionCategory, List[FunctionInfo]]:
        """Group functions by category"""
        categorized = {cat: [] for cat in FunctionCategory}

        for func in self.functions.values():
            categorized[func.category].append(func)

        return categorized

    def get_functions_by_floor(self) -> Dict[str, List[FunctionInfo]]:
        """Group functions by Z-floor"""
        by_floor = {}

        for func in self.functions.values():
            if func.floor not in by_floor:
                by_floor[func.floor] = []
            by_floor[func.floor].append(func)

        return by_floor

    def get_summary(self) -> Dict[str, Any]:
        """Get registry summary"""
        available_libs = len([l for l in self.libraries.values() if l.available])
        total_libs = len(self.libraries)

        return {
            'libraries': {
                'total': total_libs,
                'available': available_libs,
                'unavailable': total_libs - available_libs
            },
            'functions': {
                'total': len(self.functions),
                'by_category': {
                    cat.value: len([f for f in self.functions.values() if f.category == cat])
                    for cat in FunctionCategory
                }
            }
        }

    def export_to_json(self, output_path: Path):
        """Export registry to JSON"""
        data = {
            'libraries': {
                name: {
                    'available': lib.available,
                    'version': lib.version,
                    'location': lib.location,
                    'description': lib.description
                }
                for name, lib in self.libraries.items()
            },
            'functions': {
                func_id: {
                    'name': func.name,
                    'category': func.category.value,
                    'floor': func.floor,
                    'module': func.module,
                    'description': func.description
                }
                for func_id, func in self.functions.items()
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def _load_cache(self):
        """Load cached registry"""
        cache_path = self.lightspeed_root / "config" / "function_registry.json"
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Support the canonical exported shape and older flat cache files.
                libraries = data.get("libraries", data)
                for name, lib_data in libraries.items():
                    if isinstance(lib_data, dict) and 'available' in lib_data:
                        self.libraries[name] = LibraryInfo(
                            name=name,
                            available=lib_data.get('available', False),
                            version=lib_data.get('version', 'unknown'),
                            location=lib_data.get('location', 'unknown'),
                            description=lib_data.get('description', '')
                        )

                for func_id, func_data in data.get("functions", {}).items():
                    if not isinstance(func_data, dict):
                        continue
                    try:
                        category = FunctionCategory(func_data.get("category", "data_processing"))
                    except ValueError:
                        category = FunctionCategory.DATA_PROCESSING
                    self.functions[func_id] = FunctionInfo(
                        id=func_id,
                        name=func_data.get("name", func_id.replace("_", " ").title()),
                        category=category,
                        floor=func_data.get("floor", "Unknown"),
                        module=func_data.get("module", ""),
                        description=func_data.get("description", ""),
                    )
            except Exception as e:
                print(f"[FunctionRegistry] Cache load error: {e}")

    def _save_cache(self):
        """Save registry to cache"""
        cache_path = self.lightspeed_root / "config" / "function_registry.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        self.export_to_json(cache_path)


def get_service_registry_path(lightspeed_root: Optional[Path] = None) -> Path:
    """
    Return the canonical service registry path.

    The registry lives under TheConstruct config because it bridges floors/services.
    """
    if lightspeed_root is None:
        lightspeed_root = _resolve_lightspeed_root()
    return lightspeed_root / "Z Axis" / "Z0_TheConstruct" / "Config" / "service_registry.json"


def load_service_registry(lightspeed_root: Optional[Path] = None) -> Dict[str, Any]:
    """Load `service_registry.json` (no validation; raises on malformed JSON)."""
    path = get_service_registry_path(lightspeed_root)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_service_registry(
    lightspeed_root: Optional[Path] = None,
    *,
    include_disabled: bool = True,
) -> Dict[str, Any]:
    """
    Validate service registry entries by attempting to import their modules.

    Returns a structured status payload suitable for CLI/GUI display.
    """
    if lightspeed_root is None:
        lightspeed_root = _resolve_lightspeed_root()

    registry_path = get_service_registry_path(lightspeed_root)
    status: Dict[str, Any] = {
        "path": str(registry_path),
        "exists": registry_path.exists(),
        "total": 0,
        "enabled": 0,
        "import_ok": 0,
        "import_fail": 0,
        "enabled_floors": [],
        "entries": {},
    }

    if not registry_path.exists():
        return status

    # Ensure imports work regardless of entrypoint.
    z_axis_dir = lightspeed_root / "Z Axis"
    for candidate in (lightspeed_root, z_axis_dir):
        candidate_str = str(candidate)
        if candidate.exists() and candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)

    registry = load_service_registry(lightspeed_root)
    status["total"] = len(registry)

    for name, cfg in registry.items():
        enabled = bool(cfg.get("enabled", False))
        entry_type = cfg.get("type", "unknown")
        module = cfg.get("module")

        if enabled:
            status["enabled"] += 1
            if entry_type == "floor":
                status["enabled_floors"].append(name)
        elif not include_disabled:
            continue

        entry_status = {
            "type": entry_type,
            "module": module,
            "enabled": enabled,
            "import_ok": False,
            "error": None,
        }

        if not module:
            entry_status["error"] = "missing module field"
            status["import_fail"] += 1
            status["entries"][name] = entry_status
            continue

        try:
            importlib.import_module(module)
            entry_status["import_ok"] = True
            status["import_ok"] += 1
        except Exception as e:
            entry_status["error"] = str(e)
            status["import_fail"] += 1

        status["entries"][name] = entry_status

    status["enabled_floors"].sort()
    return status


# Module-level instance
_registry: Optional[FunctionLibraryRegistry] = None


def get_registry(lightspeed_root: Optional[Path] = None) -> FunctionLibraryRegistry:
    """Get global function/library registry instance"""
    global _registry

    if _registry is None:
        if lightspeed_root is None:
            lightspeed_root = _resolve_lightspeed_root()
        _registry = FunctionLibraryRegistry(lightspeed_root)
        _registry.scan_all()

    return _registry


# Testing
if __name__ == "__main__":
    from pathlib import Path

    root = _resolve_lightspeed_root()
    registry = FunctionLibraryRegistry(root)

    print("\n" + "=" * 70)
    print("FUNCTION & LIBRARY REGISTRY TEST")
    print("=" * 70)

    print("\nScanning system...")
    registry.scan_all()

    # Summary
    summary = registry.get_summary()
    print(f"\n[SUMMARY]")
    print(f"  Libraries:  {summary['libraries']['available']}/{summary['libraries']['total']} available")
    print(f"  Functions:  {summary['functions']['total']} total")

    # Show available libraries
    print(f"\n[AVAILABLE LIBRARIES]")
    for lib in registry.get_available_libraries()[:10]:
        print(f"  {lib.name:15s} v{lib.version:10s} - {lib.description}")

    # Show functions by category
    print(f"\n[FUNCTIONS BY CATEGORY]")
    for cat, funcs in registry.get_functions_by_category().items():
        if funcs:
            print(f"  {cat.value:20s}: {len(funcs)} functions")

    # Show functions by floor
    print(f"\n[FUNCTIONS BY Z-FLOOR]")
    for floor, funcs in registry.get_functions_by_floor().items():
        print(f"  {floor:15s}: {len(funcs)} functions")

    print("\n" + "=" * 70)
