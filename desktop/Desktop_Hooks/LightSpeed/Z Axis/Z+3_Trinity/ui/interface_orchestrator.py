"""
LightSpeed Interface Orchestrator v5.1.2
Central coordination system for all LightSpeed interfaces

Purpose:
This orchestrator is the HEART of the unified system. It coordinates all interfaces,
maintains synchronized state, forwards events, and ensures all components work together
as a single cohesive platform.

What It Does:
- State Management: Maintains shared state (current floor, camera position, active widgets)
- Event Forwarding: Pub/sub pattern connects all interfaces
- Data Synchronization: Database ↔ UI bidirectional sync
- Service Coordination: SmartFloor, Neo AI, Astronomy all accessible
- Interface Bridge: 2D ↔ 3D seamless communication

Architecture:
```
                 Interface Orchestrator
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    ┌───▼────┐     ┌────▼─────┐     ┌────▼────┐
    │EventBus│     │ Database │     │ Trinity │
    └───┬────┘     └────┬─────┘     └────┬────┘
        │               │                │
    ┌───┴───────────────┴────────────────┴───┐
    │                                         │
┌───▼────────┐  ┌──────────┐  ┌──────────┐  │
│Immersive N │  │ Glass UI │  │N.py(Opt) │  │
│(Primary)   │  │ (Style)  │  │ (Compat) │  │
└────────────┘  └──────────┘  └──────────┘  │
                                             │
                    Smart Services ◄─────────┘
                    (SmartFloor, Neo AI, Astronomy)
```

Events Handled:
- floor_changed: User navigates to different Z-floor
- widget_activated: User interacts with widget
- camera_moved: 3D camera position updated
- calculation_executed: Physics/math calculation performed
- widget_created: New widget added to system
- widget_deleted: Widget removed from system
- user_login: User authenticates
- user_logout: User exits

Author: LightSpeed Team
Date: April 8, 2026
Version: 5.1.2
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
import time


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SystemState:
    """Shared system state across all interfaces"""

    # Current floor
    current_floor: str = "Z0_TheConstruct"

    # Camera position (for 3D interface)
    camera_position: Dict[str, float] = field(default_factory=lambda: {
        'x': 0.0,
        'y': 55.0,  # Z0 floor + eye height
        'z': 5.0
    })

    # Camera rotation
    camera_rotation: Dict[str, float] = field(default_factory=lambda: {
        'yaw': 0.0,
        'pitch': 0.0
    })

    # Active widgets
    active_widgets: List[str] = field(default_factory=list)

    # Current user
    user: Optional[Dict[str, Any]] = None

    # UI visibility flags
    ui_overlay_visible: bool = True
    flowchart_visible: bool = False

    # Performance metrics
    fps: float = 60.0
    frame_time: float = 16.0  # ms

    # Last update timestamp
    last_update: float = field(default_factory=time.time)


@dataclass
class FloorDefinition:
    """Definition of a Z-floor"""
    id: str
    name: str
    y_position: float
    color: str
    description: str


# Floor definitions
FLOOR_DEFINITIONS = {
    'Z+3_Trinity': FloorDefinition(
        id='Z+3_Trinity',
        name='Trinity',
        y_position=80.0,
        color='#00FFFF',  # Cyan
        description='Dashboard & UI Layer'
    ),
    'Z+2_Neo': FloorDefinition(
        id='Z+2_Neo',
        name='Neo',
        y_position=70.0,
        color='#FF0080',  # Magenta
        description='AI Integration & Learning'
    ),
    'Z+1_Architect': FloorDefinition(
        id='Z+1_Architect',
        name='Architect',
        y_position=60.0,
        color='#00FF80',  # Green
        description='Mission Planning & Strategy'
    ),
    'Z0_TheConstruct': FloorDefinition(
        id='Z0_TheConstruct',
        name='TheConstruct',
        y_position=50.0,
        color='#FFFF00',  # Yellow
        description='Physics & Simulations (Lobby)'
    ),
    'Z-1_Morpheus': FloorDefinition(
        id='Z-1_Morpheus',
        name='Morpheus',
        y_position=40.0,
        color='#0080FF',  # Blue
        description='Knowledge & Code Analysis'
    ),
    'Z-2_Oracle': FloorDefinition(
        id='Z-2_Oracle',
        name='Oracle',
        y_position=30.0,
        color='#FF8000',  # Orange
        description='Archive & IP Vault'
    ),
    'Z-3_Smith': FloorDefinition(
        id='Z-3_Smith',
        name='Smith',
        y_position=20.0,
        color='#8000FF',  # Purple
        description='Background Tasks & Automation'
    ),
    'Z-4_Merovingian': FloorDefinition(
        id='Z-4_Merovingian',
        name='Merovingian',
        y_position=10.0,
        color='#FF0000',  # Red
        description='Diagnostics & System Health'
    ),
}

# Backward-compatible aliases (legacy floor IDs appear in older docs/configs)
_LEGACY_FLOOR_ALIASES = {
    'Z+3_Neo': 'Z+2_Neo',
    'Z+2_Morpheus': 'Z-1_Morpheus',
    'Z-1_Oracle': 'Z-2_Oracle',
    'Z-2_Smith': 'Z-3_Smith',
    'Z-3_Merovingian': 'Z-4_Merovingian',
    'Z-4_Core': 'Z-4_Merovingian',
    'Z-4_Trinity': 'Z+3_Trinity',
}
for _legacy_id, _canonical_id in _LEGACY_FLOOR_ALIASES.items():
    if _canonical_id in FLOOR_DEFINITIONS:
        FLOOR_DEFINITIONS.setdefault(_legacy_id, FLOOR_DEFINITIONS[_canonical_id])


# ═══════════════════════════════════════════════════════════════════════════
# INTERFACE ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════

class InterfaceOrchestrator:
    """
    Central coordinator for all LightSpeed interfaces

    This is the glue that holds everything together. All interfaces communicate
    through this orchestrator to maintain synchronized state.

    Responsibilities:
    1. State Management: Single source of truth for system state
    2. Event Forwarding: Publishes events to all subscribed interfaces
    3. Data Sync: Keeps database and UIs in sync
    4. Service Access: Provides access to SmartFloor, Neo AI, etc.
    5. Floor Navigation: Coordinates cross-floor transitions
    6. Widget Management: Tracks all widgets across all floors
    """

    def __init__(
        self,
        event_bus,
        database,
        trinity,
        smart_floor=None,
        neo_ai=None
    ):
        """
        Initialize interface orchestrator

        Args:
            event_bus: Event bus for pub/sub messaging
            database: Database manager
            trinity: Trinity settings manager
            smart_floor: SmartFloorLibrary instance (optional)
            neo_ai: NeoLearningEngine instance (optional)
        """
        self.event_bus = event_bus
        self.db = database
        self.trinity = trinity
        self.smart_floor = smart_floor
        self.neo_ai = neo_ai

        # Shared state
        self.state = SystemState()

        # Floor definitions
        self.floors = FLOOR_DEFINITIONS

        # Widget registry (widget_id -> widget_data)
        self.widgets: Dict[str, Dict[str, Any]] = {}

        # Interface instances (for direct communication if needed)
        self.interfaces: Dict[str, Any] = {}

        # Performance monitoring
        self.event_count = 0
        self.last_metrics_time = time.time()

        # Setup event subscriptions
        self._setup_event_handlers()

        print("[Orchestrator] Initialized")
        print(f"[Orchestrator] Starting floor: {self.state.current_floor}")


    # ═══════════════════════════════════════════════════════════════════════
    # EVENT SETUP
    # ═══════════════════════════════════════════════════════════════════════

    def _setup_event_handlers(self):
        """Setup event subscriptions from all interfaces"""

        # Floor navigation events
        self.event_bus.subscribe('floor_changed', self.on_floor_changed)
        self.event_bus.subscribe('floor_transition_requested', self.on_floor_transition_requested)

        # Widget events
        self.event_bus.subscribe('widget_activated', self.on_widget_activated)
        self.event_bus.subscribe('widget_created', self.on_widget_created)
        self.event_bus.subscribe('widget_deleted', self.on_widget_deleted)
        self.event_bus.subscribe('widget_updated', self.on_widget_updated)

        # Camera events (from 3D interface)
        self.event_bus.subscribe('camera_moved', self.on_camera_moved)
        self.event_bus.subscribe('camera_rotated', self.on_camera_rotated)

        # Calculation events (from physics simulations)
        self.event_bus.subscribe('calculation_executed', self.on_calculation_executed)
        self.event_bus.subscribe('calculation_requested', self.on_calculation_requested)

        # User events
        self.event_bus.subscribe('user_login', self.on_user_login)
        self.event_bus.subscribe('user_logout', self.on_user_logout)

        # UI events
        self.event_bus.subscribe('ui_overlay_toggled', self.on_ui_overlay_toggled)
        self.event_bus.subscribe('flowchart_toggled', self.on_flowchart_toggled)

        print("[Orchestrator] Event handlers registered")


    # ═══════════════════════════════════════════════════════════════════════
    # FLOOR NAVIGATION
    # ═══════════════════════════════════════════════════════════════════════

    def on_floor_changed(self, data: Dict[str, Any]):
        """
        Handle floor change event

        This is called when ANY interface changes the current floor.
        Updates shared state and notifies ALL other interfaces.
        """
        floor_id = data.get('floor')
        source = data.get('source', 'unknown')

        if floor_id not in self.floors:
            print(f"[Orchestrator] ⚠ Invalid floor ID: {floor_id}")
            return

        floor = self.floors[floor_id]

        print(f"[Orchestrator] Floor changed: {floor.name} (from {source})")

        # Update shared state
        old_floor = self.state.current_floor
        self.state.current_floor = floor_id

        # Update camera Y position for 3D interface
        self.state.camera_position['y'] = floor.y_position + 5.0  # +5 for eye height

        # Save to Trinity
        self.trinity.save('last_floor.json', {
            'floor': floor_id,
            'timestamp': time.time()
        })

        # Log to database (if available)
        if hasattr(self.db, 'log_floor_visit'):
            self.db.log_floor_visit(floor_id, source)

        # Broadcast to ALL interfaces
        self.event_bus.publish('orchestrator_floor_changed', {
            'floor': floor_id,
            'floor_name': floor.name,
            'old_floor': old_floor,
            'camera_y': self.state.camera_position['y'],
            'floor_color': floor.color,
            'source': source
        })

        self.event_count += 1


    def on_floor_transition_requested(self, data: Dict[str, Any]):
        """Handle request to transition to a floor"""
        floor_id = data.get('floor')
        smooth_transition = data.get('smooth', True)
        duration = data.get('duration', 1.0)

        if floor_id not in self.floors:
            return

        # Trigger floor change
        self.on_floor_changed({
            'floor': floor_id,
            'source': data.get('source', 'request')
        })

        # If smooth transition requested, broadcast transition event
        if smooth_transition:
            self.event_bus.publish('orchestrator_floor_transition', {
                'floor': floor_id,
                'duration': duration,
                'target_camera_y': self.state.camera_position['y']
            })


    # ═══════════════════════════════════════════════════════════════════════
    # WIDGET MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════

    def on_widget_activated(self, data: Dict[str, Any]):
        """
        Handle widget activation

        When user clicks/interacts with a widget in ANY interface,
        this coordinates the response across all systems.
        """
        widget_id = data.get('widget_id')
        source = data.get('source', 'unknown')

        print(f"[Orchestrator] Widget activated: {widget_id} (from {source})")

        # Add to active widgets
        if widget_id not in self.state.active_widgets:
            self.state.active_widgets.append(widget_id)

        # Get widget data
        widget_data = self.widgets.get(widget_id)

        if not widget_data:
            # Try to load from database
            if hasattr(self.db, 'get_widget'):
                widget_data = self.db.get_widget(widget_id)
                if widget_data:
                    self.widgets[widget_id] = widget_data

        # If widget is physics simulation, execute it
        if widget_data and widget_data.get('type') == 'physics_simulation':
            self._execute_physics_simulation(widget_id, widget_data)

        # If widget is document, open it
        elif widget_data and widget_data.get('type') == 'document':
            self._open_document(widget_id, widget_data)

        # If widget is  tool, launch it
        elif widget_data and widget_data.get('type') == 'tool':
            self._launch_tool(widget_id, widget_data)

        # Broadcast activation to all interfaces
        self.event_bus.publish('orchestrator_widget_activated', {
            'widget_id': widget_id,
            'widget_data': widget_data,
            'source': source
        })

        self.event_count += 1


    def on_widget_created(self, data: Dict[str, Any]):
        """Handle new widget creation"""
        widget_id = data.get('widget_id')
        widget_data = data.get('widget_data', {})

        print(f"[Orchestrator] Widget created: {widget_id}")

        # Add to registry
        self.widgets[widget_id] = widget_data

        # Save to database
        if hasattr(self.db, 'save_widget'):
            self.db.save_widget(widget_id, widget_data)

        # Broadcast to all interfaces
        self.event_bus.publish('orchestrator_widget_created', {
            'widget_id': widget_id,
            'widget_data': widget_data
        })


    def on_widget_deleted(self, data: Dict[str, Any]):
        """Handle widget deletion"""
        widget_id = data.get('widget_id')

        if widget_id in self.widgets:
            del self.widgets[widget_id]

        # Remove from active widgets
        if widget_id in self.state.active_widgets:
            self.state.active_widgets.remove(widget_id)

        # Delete from database
        if hasattr(self.db, 'delete_widget'):
            self.db.delete_widget(widget_id)

        # Broadcast
        self.event_bus.publish('orchestrator_widget_deleted', {
            'widget_id': widget_id
        })


    def on_widget_updated(self, data: Dict[str, Any]):
        """Handle widget update"""
        widget_id = data.get('widget_id')
        updates = data.get('updates', {})

        if widget_id in self.widgets:
            self.widgets[widget_id].update(updates)

            # Save to database
            if hasattr(self.db, 'update_widget'):
                self.db.update_widget(widget_id, updates)

            # Broadcast
            self.event_bus.publish('orchestrator_widget_updated', {
                'widget_id': widget_id,
                'widget_data': self.widgets[widget_id]
            })


    # ═══════════════════════════════════════════════════════════════════════
    # CAMERA MANAGEMENT (3D Interface)
    # ═══════════════════════════════════════════════════════════════════════

    def on_camera_moved(self, data: Dict[str, Any]):
        """Update camera position in shared state"""
        self.state.camera_position.update({
            'x': data.get('x', self.state.camera_position['x']),
            'y': data.get('y', self.state.camera_position['y']),
            'z': data.get('z', self.state.camera_position['z'])
        })

        self.state.last_update = time.time()


    def on_camera_rotated(self, data: Dict[str, Any]):
        """Update camera rotation in shared state"""
        self.state.camera_rotation.update({
            'yaw': data.get('yaw', self.state.camera_rotation['yaw']),
            'pitch': data.get('pitch', self.state.camera_rotation['pitch'])
        })


    # ═══════════════════════════════════════════════════════════════════════
    # CALCULATION MANAGEMENT (Physics & Math)
    # ═══════════════════════════════════════════════════════════════════════

    def on_calculation_executed(self, data: Dict[str, Any]):
        """
        Handle calculation execution from any interface

        When physics/math calculation is performed, record it with Neo AI
        and find correlations to suggest related calculations.
        """
        function_name = data.get('function')
        variables = data.get('variables', {})
        result = data.get('result')

        print(f"[Orchestrator] Calculation executed: {function_name}")

        # Record in Neo AI
        if self.neo_ai:
            self.neo_ai.record_execution(function_name, variables, result)

            # Find correlations
            correlations = self.neo_ai.find_correlations(function_name)

            if correlations:
                print(f"[Orchestrator] Neo AI found {len(correlations)} correlations")

                # Broadcast correlations to all interfaces
                self.event_bus.publish('orchestrator_ai_correlations', {
                    'function': function_name,
                    'correlations': correlations,
                    'suggestion': correlations[0] if correlations else None
                })

        self.event_count += 1


    def on_calculation_requested(self, data: Dict[str, Any]):
        """Handle calculation request"""
        function_name = data.get('function')
        variables = data.get('variables', {})

        if not self.smart_floor:
            print(f"[Orchestrator] ⚠ SmartFloor not available, cannot execute {function_name}")
            return

        # Execute via SmartFloor
        result = self.smart_floor.execute_function(function_name, variables)

        # Broadcast result
        self.event_bus.publish('orchestrator_calculation_result', {
            'function': function_name,
            'variables': variables,
            'result': result
        })

        # Also trigger calculation_executed for Neo AI
        self.on_calculation_executed({
            'function': function_name,
            'variables': variables,
            'result': result
        })


    # ═══════════════════════════════════════════════════════════════════════
    # USER MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════

    def on_user_login(self, data: Dict[str, Any]):
        """Handle user login"""
        user_data = data.get('user')
        self.state.user = user_data

        print(f"[Orchestrator] User logged in: {user_data.get('username', 'unknown')}")

        # Load user preferences
        if user_data:
            username = user_data.get('username')
            prefs = self.trinity.load(f'user_prefs_{username}.json')

            # Apply preferences
            if prefs:
                if 'last_floor' in prefs:
                    self.on_floor_changed({
                        'floor': prefs['last_floor'],
                        'source': 'user_preferences'
                    })


    def on_user_logout(self, data: Dict[str, Any]):
        """Handle user logout"""
        if self.state.user:
            # Save preferences
            username = self.state.user.get('username')
            if username:
                self.trinity.save(f'user_prefs_{username}.json', {
                    'last_floor': self.state.current_floor,
                    'camera_position': self.state.camera_position,
                    'logout_time': time.time()
                })

        self.state.user = None
        print("[Orchestrator] User logged out")


    # ═══════════════════════════════════════════════════════════════════════
    # UI STATE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════

    def on_ui_overlay_toggled(self, data: Dict[str, Any]):
        """Handle UI overlay toggle"""
        visible = data.get('visible', not self.state.ui_overlay_visible)
        self.state.ui_overlay_visible = visible

        # Broadcast to all interfaces
        self.event_bus.publish('orchestrator_ui_overlay_changed', {
            'visible': visible
        })


    def on_flowchart_toggled(self, data: Dict[str, Any]):
        """Handle flowchart tree toggle"""
        visible = data.get('visible', not self.state.flowchart_visible)
        self.state.flowchart_visible = visible

        # Broadcast to all interfaces
        self.event_bus.publish('orchestrator_flowchart_changed', {
            'visible': visible
        })


    # ═══════════════════════════════════════════════════════════════════════
    # WIDGET ACTIONS
    # ═══════════════════════════════════════════════════════════════════════

    def _execute_physics_simulation(self, widget_id: str, widget_data: Dict[str, Any]):
        """Execute physics simulation widget"""
        if not self.smart_floor:
            print(f"[Orchestrator] ⚠ SmartFloor not available")
            return

        function_name = widget_data.get('function')
        variables = widget_data.get('variables', {})

        if function_name:
            result = self.smart_floor.execute_function(function_name, variables)

            # Update widget with result
            widget_data['result'] = result

            # Broadcast result
            self.event_bus.publish('orchestrator_simulation_result', {
                'widget_id': widget_id,
                'result': result
            })


    def _open_document(self, widget_id: str, widget_data: Dict[str, Any]):
        """Open document widget"""
        document_path = widget_data.get('path')

        # Broadcast document open event
        self.event_bus.publish('orchestrator_document_open', {
            'widget_id': widget_id,
            'path': document_path
        })


    def _launch_tool(self, widget_id: str, widget_data: Dict[str, Any]):
        """Launch tool widget"""
        tool_name = widget_data.get('tool')

        # Broadcast tool launch event
        self.event_bus.publish('orchestrator_tool_launch', {
            'widget_id': widget_id,
            'tool': tool_name
        })


    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    def get_state(self) -> SystemState:
        """Get current shared state"""
        return self.state


    def get_floor_info(self, floor_id: str) -> Optional[FloorDefinition]:
        """Get information about a floor"""
        return self.floors.get(floor_id)


    def get_all_floors(self) -> Dict[str, FloorDefinition]:
        """Get all floor definitions"""
        return self.floors


    def navigate_to_floor(self, floor_id: str, smooth: bool = True, duration: float = 1.0):
        """Navigate to a specific floor"""
        self.event_bus.publish('floor_transition_requested', {
            'floor': floor_id,
            'smooth': smooth,
            'duration': duration,
            'source': 'orchestrator_api'
        })


    def navigate_to_widget(self, widget_id: str, duration: float = 1.0):
        """Navigate 3D camera to widget position"""
        widget_data = self.widgets.get(widget_id)

        if widget_data and 'position_3d' in widget_data:
            self.event_bus.publish('orchestrator_camera_navigate', {
                'target_position': widget_data['position_3d'],
                'duration': duration,
                'widget_id': widget_id
            })


    def register_interface(self, interface_name: str, interface_instance: Any):
        """Register an interface instance for direct communication"""
        self.interfaces[interface_name] = interface_instance
        print(f"[Orchestrator] Interface registered: {interface_name}")


    def get_interface(self, interface_name: str) -> Optional[Any]:
        """Get registered interface instance"""
        return self.interfaces.get(interface_name)


    # ═══════════════════════════════════════════════════════════════════════
    # METRICS
    # ═══════════════════════════════════════════════════════════════════════

    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator performance metrics"""
        current_time = time.time()
        elapsed = current_time - self.last_metrics_time

        events_per_second = self.event_count / elapsed if elapsed > 0 else 0

        metrics = {
            'event_count': self.event_count,
            'events_per_second': events_per_second,
            'active_widgets': len(self.state.active_widgets),
            'registered_interfaces': len(self.interfaces),
            'current_floor': self.state.current_floor,
            'fps': self.state.fps
        }

        return metrics


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    'InterfaceOrchestrator',
    'SystemState',
    'FloorDefinition',
    'FLOOR_DEFINITIONS'
]
