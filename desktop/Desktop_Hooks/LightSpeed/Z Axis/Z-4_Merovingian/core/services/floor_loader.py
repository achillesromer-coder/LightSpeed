"""
Floor Loader - Dynamic component discovery and loading for Z-floors

Loads components based on _FLOOR_MANIFEST.json files.
Implements Clean Code principles with proper dependency injection.

Author: LightSpeed Team
Date: December 19, 2025
Version: 0.9.5
"""

import json
import importlib
import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ComponentInfo:
    """Component metadata from manifest"""
    id: str
    name: str
    description: str
    module: str
    class_name: str
    enabled: bool
    source_file: str
    phase: int
    priority: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class FloorManifest:
    """Floor manifest data"""
    floor_name: str
    floor_id: str
    z_level: int
    version: str
    description: str
    color: str
    icon: str
    components: List[ComponentInfo]
    dependencies: List[str]
    capabilities: List[str]
    smart_floor: Dict[str, bool]
    goals: List[Dict[str, Any]]
    initialization_order: int
    inside_out_position: str
    created: str
    updated: str


class FloorLoader:
    """Loads and manages Z-floor components"""

    def __init__(self, lightspeed_root: Optional[Path] = None):
        if lightspeed_root is None:
            lightspeed_root = self._find_lightspeed_root(Path(__file__).resolve())

        self.lightspeed_root = Path(lightspeed_root)
        self.z_axis_dir = self.lightspeed_root / "Z Axis"
        self.manifests: Dict[str, FloorManifest] = {}
        self.loaded_components: Dict[str, Any] = {}
        self.floor_instances: Dict[str, Any] = {}

        # Ensure imports work regardless of entrypoint
        if str(self.lightspeed_root) not in sys.path:
            sys.path.insert(0, str(self.lightspeed_root))
        if self.z_axis_dir.exists() and str(self.z_axis_dir) not in sys.path:
            sys.path.insert(0, str(self.z_axis_dir))

    def _safe_console_text(self, value: Any) -> str:
        """
        Return a string that won't crash when printed on Windows consoles that
        use legacy encodings (e.g., cp1252).
        """
        text = "" if value is None else str(value)
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        try:
            text.encode(encoding)
            return text
        except Exception:
            try:
                return text.encode(encoding, errors="replace").decode(encoding, errors="replace")
            except Exception:
                return ""

    def _find_lightspeed_root(self, start: Path) -> Path:
        start = start.resolve()
        for candidate in (start, *start.parents):
            try:
                if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
                    return candidate
            except Exception:
                continue
        return start

    def _safe_module_name(self, value: str) -> str:
        safe = re.sub(r"[^0-9a-zA-Z_]+", "_", value or "").strip("_")
        return safe or "module"

    def _load_module_from_file(self, file_path: Path, module_name_hint: str) -> Optional[ModuleType]:
        if not file_path.exists():
            return None

        module_name = f"lightspeed_dynamic_{self._safe_module_name(module_name_hint)}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            print(f"[FloorLoader] Failed loading module from file: {file_path} ({e})")
            return None

    def load_floor_manifest(self, floor_name: str) -> Optional[FloorManifest]:
        """Load floor manifest from JSON file"""
        manifest_path = self.z_axis_dir / floor_name / "_FLOOR_MANIFEST.json"

        if not manifest_path.exists():
            print(f"[FloorLoader] No manifest found for {floor_name} at {manifest_path}")
            return None

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Parse components
            components = []
            for comp_data in data.get('components', []):
                components.append(ComponentInfo(
                    id=comp_data['id'],
                    name=comp_data['name'],
                    description=comp_data['description'],
                    module=comp_data['module'],
                    class_name=comp_data['class'],
                    enabled=comp_data.get('enabled', True),
                    source_file=comp_data.get('source_file', ''),
                    phase=comp_data.get('phase', 1),
                    priority=comp_data.get('priority'),
                    metadata=comp_data.get('metadata', {})
                ))

            manifest = FloorManifest(
                floor_name=data['floor_name'],
                floor_id=data['floor_id'],
                z_level=data['z_level'],
                version=data['version'],
                description=data['description'],
                color=data['color'],
                icon=data['icon'],
                components=components,
                dependencies=data.get('dependencies', []),
                capabilities=data.get('capabilities', []),
                smart_floor=data.get('smart_floor', {}),
                goals=data.get('goals', []),
                initialization_order=data.get('initialization_order', 0),
                inside_out_position=data.get('inside_out_position', ''),
                created=data.get('created', ''),
                updated=data.get('updated', '')
            )

            self.manifests[floor_name] = manifest
            print(f"[FloorLoader] Loaded manifest for {floor_name} ({len(components)} components)")
            return manifest

        except Exception as e:
            print(f"[FloorLoader] Error loading manifest for {floor_name}: {e}")
            return None

    def load_all_manifests(self) -> Dict[str, FloorManifest]:
        """Load manifests for all Z-floors"""
        z_axis_dir = self.z_axis_dir

        if not z_axis_dir.exists():
            print(f"[FloorLoader] Z Axis directory not found: {z_axis_dir}")
            return {}

        # Find all floor directories with manifests
        floor_dirs = [
            d for d in z_axis_dir.iterdir()
            if d.is_dir() and d.name.startswith('Z') and (d / "_FLOOR_MANIFEST.json").exists()
        ]

        for floor_dir in floor_dirs:
            floor_name = floor_dir.name
            self.load_floor_manifest(floor_name)

        print(f"[FloorLoader] Loaded {len(self.manifests)} floor manifests")
        return self.manifests

    def load_component(
        self,
        component_info: ComponentInfo,
        dependencies: Optional[Dict[str, Any]] = None,
        floor_dir: Optional[Path] = None,
    ) -> Optional[Any]:
        """Load a single component class"""
        def _try_load_from_file(file_path: Path) -> Optional[Any]:
            module_from_file = self._load_module_from_file(
                file_path=file_path,
                module_name_hint=f"{component_info.id}_{component_info.class_name}",
            )
            if module_from_file is None:
                return None
            try:
                component_class = getattr(module_from_file, component_info.class_name)
                print(f"[FloorLoader] Loaded component (file): {component_info.name} ({file_path})")
                self.loaded_components[component_info.id] = component_class
                return component_class
            except AttributeError:
                print(
                    f"[FloorLoader] Class not found in file for {component_info.name}: "
                    f"{component_info.class_name}"
                )
                return None

        try:
            # Import module
            module = importlib.import_module(component_info.module)

            # Get class
            component_class = getattr(module, component_info.class_name)

            print(f"[FloorLoader] Loaded component: {component_info.name} ({component_info.module}.{component_info.class_name})")

            # Store class (not instance - that's created when needed)
            self.loaded_components[component_info.id] = component_class

            return component_class

        except ImportError as e:
            # Fallback: use source_file when module path isn't importable (e.g., Z_Axis.* or invalid names)
            file_path: Optional[Path] = None

            if component_info.source_file:
                candidate = (self.lightspeed_root / component_info.source_file).resolve()
                if candidate.exists():
                    file_path = candidate

            # If manifest source_file is stale, try resolving within the floor directory.
            if file_path is None and floor_dir is not None and floor_dir.exists():
                module_leaf = (component_info.module or "").split(".")[-1].strip()
                candidates = []
                if module_leaf:
                    candidates.append(f"{module_leaf}.py")
                if component_info.id:
                    candidates.append(f"{component_info.id}.py")

                for fname in candidates:
                    match = next(floor_dir.rglob(fname), None)
                    if match is not None:
                        file_path = match.resolve()
                        break

            if file_path is not None:
                return _try_load_from_file(file_path)

            print(f"[FloorLoader] Import error for {component_info.name}: {e}")
            print(f"[FloorLoader]   Module: {component_info.module}")
            print(f"[FloorLoader]   Source: {component_info.source_file}")
            return None

        except AttributeError as e:
            # Module imported, but expected attribute/class missing; fall back to source_file.
            file_path: Optional[Path] = None

            if component_info.source_file:
                candidate = (self.lightspeed_root / component_info.source_file).resolve()
                if candidate.exists():
                    file_path = candidate

            if file_path is None and floor_dir is not None and floor_dir.exists():
                module_leaf = (component_info.module or "").split(".")[-1].strip()
                candidates = []
                if module_leaf:
                    candidates.append(f"{module_leaf}.py")
                if component_info.id:
                    candidates.append(f"{component_info.id}.py")

                for fname in candidates:
                    match = next(floor_dir.rglob(fname), None)
                    if match is not None:
                        file_path = match.resolve()
                        break

            if file_path is not None:
                loaded = _try_load_from_file(file_path)
                if loaded is not None:
                    return loaded

            print(f"[FloorLoader] Class not found for {component_info.name}: {e}")
            print(f"[FloorLoader]   Looking for class: {component_info.class_name}")
            return None

        except Exception as e:
            print(f"[FloorLoader] Error loading {component_info.name}: {e}")
            return None

    def load_floor_components(self, floor_name: str, dependencies: Optional[Dict[str, Any]] = None) -> Dict[str, Type]:
        """Load all components for a floor"""
        if floor_name not in self.manifests:
            manifest = self.load_floor_manifest(floor_name)
            if not manifest:
                return {}
        else:
            manifest = self.manifests[floor_name]

        loaded = {}
        floor_dir = self.z_axis_dir / floor_name
        for component_info in manifest.components:
            if not component_info.enabled:
                print(f"[FloorLoader] Skipping disabled component: {component_info.name}")
                continue

            component_class = self.load_component(component_info, dependencies, floor_dir=floor_dir)
            if component_class:
                loaded[component_info.id] = component_class

        print(f"[FloorLoader] Loaded {len(loaded)}/{len(manifest.components)} components for {floor_name}")
        return loaded

    def initialize_floor(self, floor_name: str, dependencies: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize a floor with all its components"""
        print(f"\n[FloorLoader] Initializing floor: {floor_name}")

        # Load manifest
        if floor_name not in self.manifests:
            manifest = self.load_floor_manifest(floor_name)
            if not manifest:
                print(f"[FloorLoader] Failed to load manifest for {floor_name}")
                return False
        else:
            manifest = self.manifests[floor_name]

        # Load dependencies first
        print(f"[FloorLoader] Loading {len(manifest.dependencies)} dependencies...")
        for dep in manifest.dependencies:
            try:
                importlib.import_module(dep)
                print(f"[FloorLoader]   [OK] {dep}")
            except ImportError as e:
                print(f"[FloorLoader]   [MISS] {dep}: {e}")

        # Load components
        loaded_components = self.load_floor_components(floor_name, dependencies)

        # Initialize floor runner (if available)
        try:
            floor_module = None

            # Preferred: top-level runner module in `Z Axis/` named after manifest floor_name.
            runner_name = manifest.floor_name
            runner_path = self.z_axis_dir / f"{runner_name}.py"

            if runner_path.exists():
                floor_module = self._load_module_from_file(runner_path, runner_name)
                if floor_module is None:
                    try:
                        floor_module = importlib.import_module(runner_name)
                    except Exception:
                        floor_module = None

            if floor_module is not None:
                if hasattr(floor_module, 'initialize'):
                    try:
                        result = floor_module.initialize(components=loaded_components, dependencies=dependencies)
                    except TypeError:
                        try:
                            result = floor_module.initialize(dependencies=dependencies)
                        except TypeError:
                            result = floor_module.initialize()
                    print(f"[FloorLoader] Floor initialization returned: {result}")
                self.floor_instances[floor_name] = floor_module
            else:
                print(f"[FloorLoader] No floor runner found for {manifest.floor_name}; components only.")

            print(f"[FloorLoader] [OK] {floor_name} initialized")
            return True

        except Exception as e:
            print(f"[FloorLoader] Error initializing {floor_name}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def initialize_all_floors_inside_out(
        self,
        dependencies: Optional[Dict[str, Any]] = None,
        *,
        enabled_floor_names: Optional[List[str]] = None,
        boot_floor_names: Optional[List[str]] = None,
        deferred_floor_names: Optional[List[str]] = None,
        manual_only_floor_names: Optional[List[str]] = None,
        return_details: bool = False,
    ) -> bool | Dict[str, Any]:
        """Initialize all floors in inside-out order"""
        print("\n" + "=" * 60)
        print("INITIALIZING ALL Z-FLOORS (INSIDE-OUT)")
        print("=" * 60)

        # Load all manifests
        self.load_all_manifests()

        allowlist = None
        if enabled_floor_names is not None:
            allowlist = {str(name).strip() for name in enabled_floor_names if str(name).strip()}
        bootset = {str(name).strip() for name in (boot_floor_names or []) if str(name).strip()}
        deferred = {str(name).strip() for name in (deferred_floor_names or []) if str(name).strip()}
        manual_only = {str(name).strip() for name in (manual_only_floor_names or []) if str(name).strip()}

        # Sort by explicit launch profile first, then by z_level for any remainder.
        floors_sorted = sorted(self.manifests.items(), key=lambda kv: kv[1].z_level)
        if bootset:
            boot_order_index = {name: index for index, name in enumerate(boot_floor_names or [])}
            boot_rows = [item for item in floors_sorted if item[1].floor_name in bootset]
            boot_rows.sort(key=lambda kv: boot_order_index.get(kv[1].floor_name, len(boot_order_index)))
            remainder = [item for item in floors_sorted if item[1].floor_name not in bootset]
            floors_sorted = boot_rows + remainder

        attempted = 0
        success_count = 0
        skipped_disabled: List[str] = []
        skipped_deferred: List[str] = []
        skipped_manual: List[str] = []
        skipped_not_in_profile: List[str] = []
        initialized_floors: List[str] = []
        failed_floors: List[str] = []
        for floor_folder, manifest in floors_sorted:
            if allowlist is not None and manifest.floor_name not in allowlist:
                print(f"[FloorLoader] Skipping disabled floor: {manifest.floor_name} ({floor_folder})")
                skipped_disabled.append(manifest.floor_name)
                continue

            if manifest.floor_name in manual_only:
                print(f"[FloorLoader] Deferring manual-heavy floor: {manifest.floor_name} ({floor_folder})")
                skipped_manual.append(manifest.floor_name)
                continue

            if manifest.floor_name in deferred and manifest.floor_name not in bootset:
                print(f"[FloorLoader] Deferring staged floor: {manifest.floor_name} ({floor_folder})")
                skipped_deferred.append(manifest.floor_name)
                continue

            if bootset and manifest.floor_name not in bootset:
                print(f"[FloorLoader] Skipping non-profile floor: {manifest.floor_name} ({floor_folder})")
                skipped_not_in_profile.append(manifest.floor_name)
                continue

            attempted += 1
            print("\n" + "-" * 60)
            icon = self._safe_console_text(manifest.icon)
            print(f"Floor: {icon} {manifest.floor_name} ({manifest.floor_id})")
            print(f"Folder: {floor_folder}")
            print(f"Position: {manifest.inside_out_position}")
            print(f"Components: {len(manifest.components)}")
            print("-" * 60)

            if self.initialize_floor(floor_folder, dependencies):
                success_count += 1
                initialized_floors.append(manifest.floor_name)
            else:
                failed_floors.append(manifest.floor_name)

        print("\n" + "=" * 60)
        print(f"FLOOR INITIALIZATION COMPLETE: {success_count}/{attempted} floors")
        print("=" * 60 + "\n")

        details = {
            "success": attempted == 0 or success_count == attempted,
            "attempted": attempted,
            "initialized_floors": initialized_floors,
            "failed_floors": failed_floors,
            "skipped_disabled": skipped_disabled,
            "skipped_deferred": skipped_deferred,
            "skipped_manual": skipped_manual,
            "skipped_not_in_profile": skipped_not_in_profile,
        }
        if return_details:
            return details
        return bool(details["success"])

    def get_component_class(self, component_id: str) -> Optional[Type]:
        """Get a loaded component class by ID"""
        return self.loaded_components.get(component_id)

    def get_floor_manifest(self, floor_name: str) -> Optional[FloorManifest]:
        """Get floor manifest"""
        return self.manifests.get(floor_name)

    def get_floor_status(self, floor_name: str) -> Dict[str, Any]:
        """Get status of a floor"""
        if floor_name not in self.manifests:
            return {'error': 'Floor not found'}

        manifest = self.manifests[floor_name]

        return {
            'floor_name': manifest.floor_name,
            'floor_id': manifest.floor_id,
            'z_level': manifest.z_level,
            'initialized': floor_name in self.floor_instances,
            'components_total': len(manifest.components),
            'components_loaded': len([c for c in manifest.components if c.id in self.loaded_components]),
            'capabilities': manifest.capabilities,
            'smart_floor_enabled': manifest.smart_floor
        }

    def get_all_floors_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all floors"""
        return {
            floor_name: self.get_floor_status(floor_name)
            for floor_name in self.manifests.keys()
        }


# ============================================================================
# Standalone Testing
# ============================================================================

if __name__ == "__main__":
    from pathlib import Path

    # Get LightSpeed root
    lightspeed_root = Path(__file__).parent.parent.parent.resolve()
    print(f"LightSpeed Root: {lightspeed_root}")

    # Create loader
    loader = FloorLoader(lightspeed_root)

    # Test: Load Merovingian manifest
    print("\n" + "=" * 60)
    print("TEST: Load Merovingian Manifest")
    print("=" * 60)

    manifest = loader.load_floor_manifest("Z-4_Merovingian")
    if manifest:
        print(f"\n✓ Manifest loaded successfully!")
        print(f"Floor: {manifest.floor_name} ({manifest.floor_id})")
        print(f"Z-Level: {manifest.z_level}")
        print(f"Components: {len(manifest.components)}")
        for comp in manifest.components:
            print(f"  - {comp.name} ({comp.id})")
    else:
        print("\n✗ Failed to load manifest")

    # Test: Load all manifests
    print("\n" + "=" * 60)
    print("TEST: Load All Manifests")
    print("=" * 60)

    all_manifests = loader.load_all_manifests()
    print(f"\n✓ Loaded {len(all_manifests)} manifests")

    # Test: Get status
    print("\n" + "=" * 60)
    print("TEST: Get All Floors Status")
    print("=" * 60)

    status = loader.get_all_floors_status()
    import json
    print(json.dumps(status, indent=2))
