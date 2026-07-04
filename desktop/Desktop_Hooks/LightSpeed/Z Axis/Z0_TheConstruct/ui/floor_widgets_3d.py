"""
FLOOR WIDGETS 3D INTEGRATION V0.9.11+
Extends floor_widgets_system.py to render widgets as interactive 3D objects

Integrates:
- Floor Widgets System (1,183 lines)
- Immersive 3D Engine (Windows 97 hills, WASD navigation)
- Z-Axis tower structure

All floor functions become walkable 3D objects in the immersive environment.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

def _find_lightspeed_root() -> Path:
    start = Path(__file__).resolve()
    for cand in (start, *start.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return Path.cwd().resolve()


def _load_module(rel_path: str):
    root = _find_lightspeed_root()
    path = (root / rel_path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    mod_name = f"lightspeed_dynamic_{path.stem}_{abs(hash(str(path)))%1_000_000}"
    spec = spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Import base widget system (Trinity-owned)
try:
    _widgets_mod = _load_module("Z Axis/Z+3_Trinity/ui/floor_widgets_system.py")
    FloorWidget = getattr(_widgets_mod, "FloorWidget")
    WidgetRegistry = getattr(_widgets_mod, "WidgetRegistry")
    WidgetConfig = getattr(_widgets_mod, "WidgetConfig")
    HAS_FLOOR_WIDGETS = True
except Exception as e:
    HAS_FLOOR_WIDGETS = False
    print(f"[Floor Widgets 3D] Base system not available: {e}")

# Import 3D engine (Construct-owned)
try:
    _engine_mod = _load_module("Z Axis/Z0_TheConstruct/ui/immersive_3d_engine.py")
    Interactive3DObject = getattr(_engine_mod, "Interactive3DObject")
    Vector3D = getattr(_engine_mod, "Vector3D")
    FloorType = getattr(_engine_mod, "FloorType")
    Immersive3DEngine = getattr(_engine_mod, "Immersive3DEngine")
    HAS_3D_ENGINE = True
except Exception as e:
    HAS_3D_ENGINE = False
    print(f"[Floor Widgets 3D] 3D engine not available: {e}")


@dataclass
class Widget3DLayout:
    """3D spatial layout for floor widgets"""
    floor: FloorType
    position: Vector3D
    grid_x: int
    grid_y: int
    size_multiplier: float = 1.0


class FloorWidgets3DGenerator:
    """Generate 3D objects from floor widgets"""

    # Map Floor Widgets categories (WidgetCategory.value) to FloorType
    CATEGORY_TO_FLOOR = {
        'ai': FloorType.Z_PLUS_2,          # Neo
        'knowledge': FloorType.Z_MINUS_1,  # Morpheus
        'design': FloorType.Z_PLUS_1,      # Architect
        'physics': FloorType.Z_ZERO,       # TheConstruct
        'visual': FloorType.Z_MINUS_2,     # Oracle
        'task': FloorType.Z_MINUS_3,       # Smith
        'data': FloorType.Z_MINUS_4,       # Merovingian
        'config': FloorType.Z_PLUS_3,      # Trinity
    }

    # Color schemes by floor
    FLOOR_COLORS = {
        FloorType.Z_PLUS_3: "#00D4FF",  # Trinity - Cyan
        FloorType.Z_PLUS_2: "#00FF88",  # Neo - Bright green
        FloorType.Z_PLUS_1: "#FF8C00",  # Architect - Orange
        FloorType.Z_ZERO: "#00FF00",  # TheConstruct - Green
        FloorType.Z_MINUS_1: "#9932CC",  # Morpheus - Purple
        FloorType.Z_MINUS_2: "#FFD700",  # Oracle - Gold
        FloorType.Z_MINUS_3: "#FF3333",  # Smith - Red
        FloorType.Z_MINUS_4: "#8B0000",  # Merovingian - Dark red
        FloorType.N_EXTERNAL: "#2a5a2a",  # N.py - Green hills
    }

    def __init__(self, widget_registry: Optional['WidgetRegistry'] = None):
        self.registry = widget_registry
        self.widget_layouts: Dict[str, Widget3DLayout] = {}

    def generate_floor_layout(self, floor: FloorType, widgets: List['FloorWidget']) -> List[Interactive3DObject]:
        """Generate 3D layout for all widgets on a floor"""
        objects = []

        # Calculate grid layout
        grid_size = math.ceil(math.sqrt(len(widgets)))
        spacing = 5.0  # meters between widgets

        for i, widget in enumerate(widgets):
            grid_x = i % grid_size
            grid_y = i // grid_size

            # Calculate position relative to floor center
            x = (grid_x - grid_size / 2) * spacing
            z = (grid_y - grid_size / 2) * spacing

            # Get floor Y position (from FloorNavigationSystem)
            floor_heights = {
                FloorType.N_EXTERNAL: 0.0,
                FloorType.Z_MINUS_4: 10.0,
                FloorType.Z_MINUS_3: 20.0,
                FloorType.Z_MINUS_2: 30.0,
                FloorType.Z_MINUS_1: 40.0,
                FloorType.Z_ZERO: 50.0,
                FloorType.Z_PLUS_1: 60.0,
                FloorType.Z_PLUS_2: 70.0,
                FloorType.Z_PLUS_3: 80.0,
            }
            y = floor_heights.get(floor, 0.0) + 2.0  # +2m above floor

            # Create 3D object from widget
            obj = self._widget_to_3d_object(widget, Vector3D(x, y, z), floor)
            objects.append(obj)

            # Store layout
            self.widget_layouts[widget.widget_id] = Widget3DLayout(
                floor=floor,
                position=Vector3D(x, y, z),
                grid_x=grid_x,
                grid_y=grid_y
            )

        return objects

    def _widget_to_3d_object(self, widget: 'FloorWidget', position: Vector3D,
                            floor: FloorType) -> Interactive3DObject:
        """Convert FloorWidget to Interactive3DObject"""

        # Determine object type based on widget category
        category = getattr(widget, "category", None)
        category_value = getattr(category, "value", str(category)).lower() if category is not None else ""

        if category_value == "ai":
            object_type = "sphere"  # AI widgets as spheres
            size = (1.5, 1.5, 1.5)
        elif category_value == "physics":
            object_type = "sphere"  # physics/sim widgets as spheres
            size = (2.0, 2.0, 2.0)
        else:
            object_type = "window"
            size = (2.0, 2.0, 0.5) if category_value == "visual" else (1.5, 2.0, 0.5)

        # Get color from floor
        color = self.FLOOR_COLORS.get(floor, "#888888")

        # Create interactive object
        return Interactive3DObject(
            id=f"widget_{widget.widget_id}",
            name=widget.name,
            position=position,
            size=size,
            color=color,
            object_type=object_type,
            floor=floor,
            callback=lambda: self._execute_widget(widget),
            data={
                'widget_id': widget.widget_id,
                'category': widget.category.value,
                'floor_name': widget.floor.value if hasattr(widget.floor, 'value') else str(widget.floor),
                'description': widget.description,
                'inputs': widget.inputs,
                'outputs': widget.outputs,
            }
        )

    def _execute_widget(self, widget: 'FloorWidget'):
        """Execute widget when interacted with in 3D"""
        print(f"[3D Widget] Executing: {widget.name}")
        print(f"[3D Widget] Floor: {widget.floor}")
        print(f"[3D Widget] Category: {widget.category.value}")

        # Execute widget with empty inputs (for now)
        try:
            result = widget.execute({})
            print(f"[3D Widget] Result: {result}")
        except Exception as e:
            print(f"[3D Widget] Error: {e}")

    def generate_all_floor_widgets(self) -> Dict[FloorType, List[Interactive3DObject]]:
        """Generate 3D objects for all registered widgets, organized by floor"""
        if not self.registry:
            print("[Floor Widgets 3D] No registry available")
            return {}

        floor_objects = {}

        # Group widgets by floor
        widgets_by_floor: Dict[FloorType, List[FloorWidget]] = {}

        for widget_id in self.registry.list_widgets():
            widget = self.registry.create_widget(widget_id)
            if widget:
                # Map category to floor
                floor = self.CATEGORY_TO_FLOOR.get(
                    widget.category.value,
                    FloorType.Z_ZERO  # Default to TheConstruct
                )

                if floor not in widgets_by_floor:
                    widgets_by_floor[floor] = []
                widgets_by_floor[floor].append(widget)

        # Generate layouts for each floor
        for floor, widgets in widgets_by_floor.items():
            floor_objects[floor] = self.generate_floor_layout(floor, widgets)

        return floor_objects


class EnhancedFloorEnvironments:
    """Create immersive floor-specific environments"""

    @staticmethod
    def create_floor_features(floor: FloorType) -> List[Interactive3DObject]:
        """Create floor-specific environmental features"""
        features = []

        floor_heights = {
            FloorType.Z_MINUS_4: 10.0,
            FloorType.Z_MINUS_3: 20.0,
            FloorType.Z_MINUS_2: 30.0,
            FloorType.Z_MINUS_1: 40.0,
            FloorType.Z_ZERO: 50.0,
            FloorType.Z_PLUS_1: 60.0,
            FloorType.Z_PLUS_2: 70.0,
            FloorType.Z_PLUS_3: 80.0,
        }

        y = floor_heights.get(floor, 0.0)

        if floor == FloorType.Z_PLUS_2:
            # Neo floor - AI Orchestration
            # Central AI sphere
            features.append(Interactive3DObject(
                id="neo_central_ai",
                name="Neo AI Core",
                position=Vector3D(0.0, y + 5.0, 0.0),
                size=(3.0, 3.0, 3.0),
                color="#00FF88",
                object_type="sphere",
                floor=floor,
                data={'type': 'ai_core', 'pulsing': True}
            ))

        elif floor == FloorType.Z_MINUS_1:
            # Morpheus floor - Knowledge
            # Knowledge library pillars
            for i in range(8):
                angle = math.radians(i * 45)
                x = math.sin(angle) * 8.0
                z = math.cos(angle) * 8.0
                features.append(Interactive3DObject(
                    id=f"knowledge_pillar_{i}",
                    name=f"Knowledge Pillar {i+1}",
                    position=Vector3D(x, y + 3.0, z),
                    size=(1.0, 6.0, 1.0),
                    color="#9932CC",
                    object_type="window",
                    floor=floor,
                    data={'type': 'knowledge_pillar', 'index': i}
                ))

        elif floor == FloorType.Z_ZERO:
            # TheConstruct - Physics/Training
            # Training room grid
            features.append(Interactive3DObject(
                id="construct_grid",
                name="Construct Training Grid",
                position=Vector3D(0.0, y + 0.1, 0.0),
                size=(20.0, 0.1, 20.0),
                color="#00FF00",
                object_type="window",
                floor=floor,
                data={'type': 'training_grid'}
            ))

        elif floor == FloorType.Z_MINUS_2:
            # Oracle floor - Visual Library
            # Oracle's table (center)
            features.append(Interactive3DObject(
                id="oracle_table",
                name="Oracle's Table",
                position=Vector3D(0.0, y + 1.0, 0.0),
                size=(4.0, 1.5, 2.0),
                color="#8B4513",
                object_type="window",
                floor=floor,
                data={'type': 'oracle_table'}
            ))

        elif floor == FloorType.Z_MINUS_3:
            # Smith floor - Background Tasks
            # Task processing nodes
            for i in range(6):
                angle = math.radians(i * 60)
                x = math.sin(angle) * 6.0
                z = math.cos(angle) * 6.0
                features.append(Interactive3DObject(
                    id=f"smith_node_{i}",
                    name=f"Task Node {i+1}",
                    position=Vector3D(x, y + 2.0, z),
                    size=(1.5, 1.5, 1.5),
                    color="#FF3333",
                    object_type="sphere",
                    floor=floor,
                    data={'type': 'task_node', 'node_id': i}
                ))

        elif floor == FloorType.Z_PLUS_3:
            # Trinity floor - UI & Settings Hub
            features.append(Interactive3DObject(
                id="trinity_settings_hub",
                name="Trinity Settings Hub",
                position=Vector3D(0.0, y + 3.0, 0.0),
                size=(4.0, 2.5, 0.6),
                color="#00D4FF",
                object_type="window",
                floor=floor,
                data={'type': 'settings_hub'}
            ))

        elif floor == FloorType.Z_MINUS_4:
            # Merovingian floor - System Core
            features.append(Interactive3DObject(
                id="merovingian_core",
                name="Merovingian Core",
                position=Vector3D(0.0, y + 4.0, 0.0),
                size=(3.0, 3.0, 3.0),
                color="#8B0000",
                object_type="sphere",
                floor=floor,
                data={'type': 'system_core', 'pulsing': True}
            ))

        return features

    @staticmethod
    def create_floor_lighting(floor: FloorType) -> Dict[str, any]:
        """Get lighting configuration for floor"""
        lighting = {
            FloorType.Z_PLUS_3: {'ambient': 0.7, 'color': '#00D4FF'},
            FloorType.Z_PLUS_2: {'ambient': 0.8, 'color': '#00FF88'},
            FloorType.Z_PLUS_1: {'ambient': 0.7, 'color': '#FF8C00'},
            FloorType.Z_ZERO: {'ambient': 1.0, 'color': '#00FF00'},
            FloorType.Z_MINUS_1: {'ambient': 0.6, 'color': '#9932CC'},
            FloorType.Z_MINUS_2: {'ambient': 0.5, 'color': '#FFD700'},
            FloorType.Z_MINUS_3: {'ambient': 0.4, 'color': '#FF3333'},
            FloorType.Z_MINUS_4: {'ambient': 0.3, 'color': '#8B0000'},
            FloorType.N_EXTERNAL: {'ambient': 1.0, 'color': '#87CEEB'},
        }
        return lighting.get(floor, {'ambient': 0.5, 'color': '#FFFFFF'})


def integrate_widgets_with_3d_engine(engine: 'Immersive3DEngine',
                                     widget_registry: Optional['WidgetRegistry'] = None):
    """Integrate floor widgets into 3D engine"""
    if not HAS_FLOOR_WIDGETS or not HAS_3D_ENGINE:
        print("[Floor Widgets 3D] Missing dependencies")
        return

    print("[Floor Widgets 3D] Integrating widgets into 3D environment...")

    # Generate widget 3D objects
    generator = FloorWidgets3DGenerator(widget_registry)
    floor_widgets = generator.generate_all_floor_widgets()

    # Add to engine
    for floor, widgets in floor_widgets.items():
        print(f"[Floor Widgets 3D] Floor {floor.value}: {len(widgets)} widgets")
        engine.objects.extend(widgets)

    # Add floor environmental features
    env_generator = EnhancedFloorEnvironments()
    for floor in FloorType:
        if floor == FloorType.N_EXTERNAL:
            continue  # Skip external ground floor
        features = env_generator.create_floor_features(floor)
        engine.objects.extend(features)
        print(f"[Floor Widgets 3D] Floor {floor.value}: {len(features)} environmental features")

    print(f"[Floor Widgets 3D] Total objects: {len(engine.objects)}")


# Example built-in widgets mapped to 3D objects
BUILTIN_3D_WIDGETS = {
    'ai_chat': {
        'name': 'Achilles AI Chat',
        'floor': FloorType.Z_PLUS_2,
        'position': Vector3D(5.0, 25.0, 0.0),
        'size': (2.0, 3.0, 0.5),
        'color': '#ff1493',
        'type': 'window'
    },
    'knowledge_search': {
        'name': 'Knowledge Search',
        'floor': FloorType.Z_MINUS_1,
        'position': Vector3D(-5.0, -5.0, 0.0),
        'size': (2.5, 2.0, 0.5),
        'color': '#9932CC',
        'type': 'window'
    },
    'workflow_designer': {
        'name': 'Workflow Designer',
        'floor': FloorType.Z_PLUS_1,
        'position': Vector3D(0.0, 15.0, 5.0),
        'size': (3.0, 2.5, 0.5),
        'color': '#FF8C00',
        'type': 'window'
    },
    'physics_sim': {
        'name': 'Physics Simulator',
        'floor': FloorType.Z_ZERO,
        'position': Vector3D(0.0, 5.5, 0.0),
        'size': (2.0, 2.0, 2.0),
        'color': '#00FF00',
        'type': 'sphere'
    },
    'tower_view': {
        'name': 'Tower Blueprint View',
        'floor': FloorType.Z_ZERO,
        'position': Vector3D(0.0, 5.0, -12.0),
        'size': (3.2, 2.2, 0.5),
        'color': '#0ea5e9',
        'type': 'window'
    },
    'oracle_vision': {
        'name': 'Oracle Vision System',
        'floor': FloorType.Z_MINUS_2,
        'position': Vector3D(3.0, -15.0, 3.0),
        'size': (2.0, 2.0, 0.5),
        'color': '#FFD700',
        'type': 'window'
    },
    'task_queue': {
        'name': 'Smith Task Queue',
        'floor': FloorType.Z_MINUS_3,
        'position': Vector3D(-3.0, -25.0, 0.0),
        'size': (2.5, 2.0, 0.5),
        'color': '#FF3333',
        'type': 'window'
    },
    'user_management': {
        'name': 'User Management',
        'floor': FloorType.Z_MINUS_4,
        'position': Vector3D(0.0, -35.0, -3.0),
        'size': (2.0, 2.0, 0.5),
        'color': '#8B0000',
        'type': 'window'
    },
    'settings_hub': {
        'name': 'Trinity Settings Hub',
        'floor': FloorType.Z_PLUS_3,
        'position': Vector3D(0.0, 35.0, 0.0),
        'size': (3.0, 2.5, 0.5),
        'color': '#00D4FF',
        'type': 'window'
    },
}


def create_builtin_3d_widgets() -> List[Interactive3DObject]:
    """Create built-in 3D widgets"""
    widgets = []

    for widget_id, config in BUILTIN_3D_WIDGETS.items():
        widget = Interactive3DObject(
            id=f"builtin_{widget_id}",
            name=config['name'],
            position=config['position'],
            size=config['size'],
            color=config['color'],
            object_type=config['type'],
            floor=config['floor'],
            data={'builtin': True, 'widget_id': widget_id}
        )
        widgets.append(widget)

    return widgets


if __name__ == "__main__":
    print("Floor Widgets 3D Integration System")
    print(f"Floor Widgets Available: {HAS_FLOOR_WIDGETS}")
    print(f"3D Engine Available: {HAS_3D_ENGINE}")

    if HAS_FLOOR_WIDGETS and HAS_3D_ENGINE:
        # Create example widgets
        builtin_widgets = create_builtin_3d_widgets()
        print(f"\nCreated {len(builtin_widgets)} built-in 3D widgets")

        for widget in builtin_widgets:
            print(f"  - {widget.name} @ {widget.floor.value}")
