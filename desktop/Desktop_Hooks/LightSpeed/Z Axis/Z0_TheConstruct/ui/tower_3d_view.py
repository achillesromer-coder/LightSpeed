"""
3D Tower Visualization System
LightSpeed Type I Civilization Platform

Interactive 3D tower showing all Z-floors with:
- Floor expansion with knowledge/objects
- Drag-and-drop widgets and tools
- Workflow creation and linking
- Progress tracking visualization
- User/AI activity indicators
- Interactive floor management

Author: LightSpeed Team
Version: 0.9.5
Date: December 23, 2025
"""

import tkinter as tk
from tkinter import ttk, Canvas
from typing import Dict, List, Optional, Tuple, Any
import json
from pathlib import Path
from datetime import datetime

class Floor3DObject:
    """Represents an object within a 3D floor."""

    def __init__(self, object_id: str, object_type: str, data: Dict[str, Any]):
        """
        Initialize floor object.

        Args:
            object_id: Unique identifier
            object_type: Type (widget, tool, workflow, document, etc.)
            data: Object data
        """
        self.id = object_id
        self.type = object_type
        self.data = data
        self.position = data.get('position', {'x': 0, 'y': 0, 'z': 0})
        self.connections = data.get('connections', [])
        self.created_at = data.get('created_at', datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'type': self.type,
            'data': self.data,
            'position': self.position,
            'connections': self.connections,
            'created_at': self.created_at
        }


class Floor3DView:
    """3D representation of a single floor."""

    def __init__(self, floor_name: str, z_level: str, emoji: str):
        """
        Initialize floor view.

        Args:
            floor_name: Floor name (e.g., "Merovingian")
            z_level: Z-axis level (e.g., "Z-4")
            emoji: Floor emoji
        """
        self.floor_name = floor_name
        self.z_level = z_level
        self.emoji = emoji
        self.objects: Dict[str, Floor3DObject] = {}
        self.expanded = False
        self.users_active: List[str] = []
        self.ai_active: List[str] = []

    def add_object(self, obj: Floor3DObject):
        """Add object to floor."""
        self.objects[obj.id] = obj
        self.expanded = len(self.objects) > 0

    def remove_object(self, object_id: str):
        """Remove object from floor."""
        if object_id in self.objects:
            del self.objects[object_id]
            self.expanded = len(self.objects) > 0

    def get_progress(self) -> float:
        """Calculate floor progress (0.0 to 1.0)."""
        # Progress based on number of objects and connections
        object_count = len(self.objects)
        connection_count = sum(len(obj.connections) for obj in self.objects.values())

        if object_count == 0:
            return 0.0

        # Weight: objects 70%, connections 30%
        return min(1.0, (object_count * 0.7 + connection_count * 0.3) / 10.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'floor_name': self.floor_name,
            'z_level': self.z_level,
            'emoji': self.emoji,
            'objects': {oid: obj.to_dict() for oid, obj in self.objects.items()},
            'expanded': self.expanded,
            'users_active': self.users_active,
            'ai_active': self.ai_active,
            'progress': self.get_progress()
        }


class Tower3DVisualization:
    """
    Interactive 3D tower visualization.

    Features:
    - All 9 Z-floors in vertical stack
    - Floors expand with knowledge/objects
    - Drag-and-drop interface
    - Workflow creation and linking
    - Progress visualization
    - User/AI activity indicators
    """

    def __init__(self, parent: tk.Widget):
        """
        Initialize 3D tower view.

        Args:
            parent: Parent widget
        """
        self.parent = parent
        self.floors: Dict[str, Floor3DView] = {}
        self.selected_floor: Optional[str] = None
        self.selected_object: Optional[str] = None
        self.dragging = False
        self.drag_start = None

        # Initialize floors
        self._initialize_floors()

        # Create UI
        self._create_ui()

    def _initialize_floors(self):
        """Initialize all floor views."""
        floor_config = [
            ("Merovingian", "Z-4", "🏥"),
            ("Smith", "Z-3", "🤖"),
            ("Oracle", "Z-2", "📚"),
            ("Morpheus", "Z-1", "🧠"),
            ("TheConstruct", "Z0", "🌐"),
            ("Architect", "Z+1", "📐"),
            ("Neo", "Z+2", "🤖"),
            ("Trinity", "Z+3", "🎨"),
        ]

        for name, level, emoji in floor_config:
            self.floors[name] = Floor3DView(name, level, emoji)

    def _create_ui(self):
        """Create visualization UI."""
        # Main container
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, pady=(10, 5))

        ttk.Label(
            title_frame,
            text="🏢 LightSpeed Tower - 3D Interactive View",
            font=("Arial", 16, "bold")
        ).pack(side=tk.LEFT, padx=10)

        # Controls
        control_frame = ttk.Frame(title_frame)
        control_frame.pack(side=tk.RIGHT, padx=10)

        ttk.Button(
            control_frame,
            text="Add Widget",
            command=self._add_widget_dialog
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            control_frame,
            text="Create Workflow",
            command=self._create_workflow_dialog
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            control_frame,
            text="Save Layout",
            command=self._save_layout
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            control_frame,
            text="Simulate Activity",
            command=self._simulate_activity
        ).pack(side=tk.LEFT, padx=2)

        # Main content area (split view)
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left panel - Tower visualization
        tower_frame = ttk.LabelFrame(content_frame, text="Tower View", padding=10)
        tower_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Canvas for drawing tower
        self.canvas = Canvas(
            tower_frame,
            bg="#1e1e1e",
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind mouse events for interaction
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

        # Right panel - Floor details
        details_frame = ttk.LabelFrame(content_frame, text="Floor Details", padding=10)
        details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        details_frame.config(width=300)

        # Floor info display
        self.floor_info_text = tk.Text(
            details_frame,
            height=20,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.floor_info_text.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # Floor GUI access button
        self.floor_gui_button = ttk.Button(
            details_frame,
            text="Open Floor GUI",
            command=lambda: self._open_floor_gui(self.selected_floor) if self.selected_floor else None,
            state=tk.DISABLED
        )
        self.floor_gui_button.pack(fill=tk.X)

        # Bottom panel - Progress indicators
        progress_frame = ttk.LabelFrame(self.main_frame, text="Progress Overview", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.progress_labels = {}
        for floor_name in self.floors.keys():
            floor_progress_frame = ttk.Frame(progress_frame)
            floor_progress_frame.pack(fill=tk.X, pady=2)

            ttk.Label(
                floor_progress_frame,
                text=f"{floor_name}:",
                width=15
            ).pack(side=tk.LEFT)

            progress = ttk.Progressbar(
                floor_progress_frame,
                mode='determinate',
                length=200
            )
            progress.pack(side=tk.LEFT, padx=5)

            label = ttk.Label(floor_progress_frame, text="0%")
            label.pack(side=tk.LEFT)

            self.progress_labels[floor_name] = (progress, label)

        # Initial render
        self._render_tower()

    def _render_tower(self):
        """Render the 3D tower visualization."""
        self.canvas.delete("all")

        width = self.canvas.winfo_width() or 600
        height = self.canvas.winfo_height() or 800

        # Draw tower from bottom to top
        floor_height = height / 9
        floor_width = 200

        # Center X position
        center_x = width / 2

        # Draw floors in order (bottom to top)
        y_pos = height - floor_height

        for floor_name in ["Merovingian", "Smith", "Oracle", "Morpheus", "TheConstruct",
                          "Architect", "Neo", "Trinity"]:
            floor = self.floors[floor_name]

            # Floor base color
            if floor.expanded:
                fill_color = "#0a84ff"  # Blue when expanded
                outline_color = "#00d4ff"
            else:
                fill_color = "#2d2f36"  # Gray when empty
                outline_color = "#38383a"

            # Draw floor rectangle
            x1 = center_x - floor_width / 2
            x2 = center_x + floor_width / 2
            y1 = y_pos
            y2 = y_pos + floor_height - 10

            floor_rect = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=fill_color,
                outline=outline_color,
                width=2,
                tags=("floor", floor_name)
            )

            # Floor label
            self.canvas.create_text(
                center_x, y_pos + floor_height / 2 - 5,
                text=f"{floor.emoji} {floor.z_level} {floor.floor_name}",
                fill="#ffffff",
                font=("Arial", 10, "bold"),
                tags=("floor_label", floor_name)
            )

            # Object count
            if floor.expanded:
                obj_count = len(floor.objects)
                self.canvas.create_text(
                    center_x, y_pos + floor_height / 2 + 15,
                    text=f"{obj_count} objects",
                    fill="#00ff88",
                    font=("Arial", 8),
                    tags=("floor_count", floor_name)
                )

                # Draw objects as small circles
                if obj_count > 0:
                    obj_x_offset = -80
                    obj_positions = {}  # Store positions for connection drawing

                    for i, obj in enumerate(list(floor.objects.values())[:5]):  # Show max 5
                        obj_x = center_x + obj_x_offset + (i * 35)
                        obj_y = y_pos + floor_height / 2

                        # Color based on object type
                        obj_color = "#00ff88"  # Default green
                        if obj.type == "Workflow":
                            obj_color = "#ff00ff"  # Magenta for workflows
                        elif obj.type == "Tool":
                            obj_color = "#ffaa00"  # Orange for tools
                        elif obj.type == "Document":
                            obj_color = "#00aaff"  # Blue for documents

                        self.canvas.create_oval(
                            obj_x - 8, obj_y - 8,
                            obj_x + 8, obj_y + 8,
                            fill=obj_color,
                            outline=obj_color,
                            tags=("object", floor_name, obj.id)
                        )

                        obj_positions[obj.id] = (obj_x, obj_y)

                    # Draw connection lines between linked objects
                    for obj in list(floor.objects.values())[:5]:
                        if obj.connections and obj.id in obj_positions:
                            x1, y1 = obj_positions[obj.id]
                            for connected_id in obj.connections:
                                if connected_id in obj_positions:
                                    x2, y2 = obj_positions[connected_id]
                                    # Draw arrow from obj to connected
                                    self.canvas.create_line(
                                        x1, y1, x2, y2,
                                        fill="#ffff00",  # Yellow connection
                                        width=2,
                                        arrow=tk.LAST,
                                        tags=("connection", floor_name)
                                    )

            # Users/AI indicators
            if floor.users_active:
                self.canvas.create_text(
                    x2 + 20, y_pos + 10,
                    text="👤" * len(floor.users_active),
                    fill="#00d4ff",
                    font=("Arial", 10),
                    tags=("users", floor_name)
                )

            if floor.ai_active:
                self.canvas.create_text(
                    x2 + 20, y_pos + 30,
                    text="🤖" * len(floor.ai_active),
                    fill="#ff00ff",
                    font=("Arial", 10),
                    tags=("ai", floor_name)
                )

            y_pos -= floor_height

        # Update progress bars
        self._update_progress_bars()

    def _update_progress_bars(self):
        """Update progress bar displays."""
        for floor_name, (progress_bar, label) in self.progress_labels.items():
            floor = self.floors[floor_name]
            progress_value = floor.get_progress() * 100

            progress_bar['value'] = progress_value
            label.config(text=f"{int(progress_value)}%")

    def _on_canvas_click(self, event):
        """Handle canvas click."""
        # Find clicked floor
        clicked = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)

        for item in clicked:
            tags = self.canvas.gettags(item)
            if "floor" in tags:
                # Get floor name
                for tag in tags:
                    if tag in self.floors:
                        self.selected_floor = tag
                        self._show_floor_details(tag)
                        break

    def _on_canvas_drag(self, event):
        """Handle dragging objects between floors."""
        if not self.dragging:
            # Check if we're clicking on an object
            clicked = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
            for item in clicked:
                tags = self.canvas.gettags(item)
                if "object" in tags:
                    self.dragging = True
                    self.drag_start = (event.x, event.y)
                    # Store object info from tags
                    for tag in tags:
                        if tag.startswith("widget_"):
                            self.selected_object = tag
                            break
                    break

        if self.dragging and self.drag_start:
            # Move the object with cursor
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]

            # Find the object canvas item
            for item in self.canvas.find_withtag("object"):
                tags = self.canvas.gettags(item)
                if self.selected_object in tags:
                    self.canvas.move(item, dx, dy)
                    self.drag_start = (event.x, event.y)
                    break

    def _on_canvas_release(self, event):
        """Handle drag release and object transfer between floors."""
        if self.dragging and self.selected_object:
            # Find which floor the object was dropped on
            clicked = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
            target_floor = None

            for item in clicked:
                tags = self.canvas.gettags(item)
                if "floor" in tags:
                    for tag in tags:
                        if tag in self.floors:
                            target_floor = tag
                            break
                    break

            # If dropped on a different floor, transfer object
            if target_floor and self.selected_floor and target_floor != self.selected_floor:
                # Find the object in source floor
                source_floor = self.floors[self.selected_floor]
                for obj_id, obj in source_floor.objects.items():
                    if obj_id == self.selected_object:
                        # Transfer to target floor
                        self.floors[target_floor].add_object(obj)
                        source_floor.remove_object(obj_id)

                        # Show confirmation
                        from tkinter import messagebox
                        messagebox.showinfo(
                            "Object Moved",
                            f"Moved {obj.type} from {self.selected_floor} to {target_floor}"
                        )

                        # Re-render tower
                        self._render_tower()
                        break

        self.dragging = False
        self.selected_object = None
        self.drag_start = None

    def _show_floor_details(self, floor_name: str):
        """Show detailed information about a floor."""
        floor = self.floors[floor_name]

        self.floor_info_text.delete("1.0", tk.END)

        info = f"""FLOOR: {floor.emoji} {floor.floor_name}
Z-Level: {floor.z_level}
Status: {'Expanded' if floor.expanded else 'Empty'}
Objects: {len(floor.objects)}
Progress: {int(floor.get_progress() * 100)}%

Active Users: {len(floor.users_active)}
Active AI: {len(floor.ai_active)}

OBJECTS:
"""

        for obj in floor.objects.values():
            info += f"\n  • {obj.type}: {obj.id}"
            if obj.connections:
                info += f" → {len(obj.connections)} links"

        # Add workflow chains
        workflows = [obj for obj in floor.objects.values() if obj.type == "Workflow"]
        if workflows:
            info += f"\n\nWORKFLOWS: {len(workflows)}"
            for wf in workflows:
                chain_length = len(wf.data.get('chain', []))
                info += f"\n  • {wf.data.get('name', wf.id)} ({chain_length} steps)"

        self.floor_info_text.insert("1.0", info)

        # Enable GUI button
        if hasattr(self, 'floor_gui_button'):
            self.floor_gui_button.config(state=tk.NORMAL)

    def _open_floor_gui(self, floor_name: str):
        """Open floor-specific GUI interface."""
        from tkinter import messagebox

        floor_gui_map = {
            "Merovingian": "Diagnostic Dashboard",
            "Smith": "Task Scheduler",
            "Oracle": "Archive Manager",
            "Morpheus": "Knowledge Base",
            "TheConstruct": "Simulation Engine",
            "Architect": "Mission Planner",
            "Neo": "AI Assistant Interface",
            "Trinity": "Settings & Theme Editor",
        }

        gui_name = floor_gui_map.get(floor_name, "Unknown GUI")

        messagebox.showinfo(
            f"{floor_name} GUI",
            f"Opening {gui_name} for {floor_name} floor...\n\n" +
            f"This will launch the specialized interface for this floor's functions."
        )

    def _add_widget_dialog(self):
        """Show dialog to add widget to floor."""
        if not self.selected_floor:
            from tkinter import messagebox
            messagebox.showwarning("No Floor Selected", "Please click on a floor first")
            return

        # Create dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add Widget to Floor")
        dialog.geometry("400x300")

        ttk.Label(dialog, text=f"Add widget to {self.selected_floor}:").pack(pady=10)

        ttk.Label(dialog, text="Widget Type:").pack()
        widget_type_var = tk.StringVar(value="Data Display")
        widget_type = ttk.Combobox(
            dialog,
            textvariable=widget_type_var,
            values=["Data Display", "Chart", "Control Panel", "Workflow Node", "Document", "Tool"]
        )
        widget_type.pack(pady=5)

        ttk.Label(dialog, text="Widget Name:").pack()
        widget_name = ttk.Entry(dialog)
        widget_name.pack(pady=5)

        def add_widget():
            obj_id = f"widget_{len(self.floors[self.selected_floor].objects) + 1}"
            obj = Floor3DObject(
                obj_id,
                widget_type_var.get(),
                {
                    'name': widget_name.get(),
                    'position': {'x': 0, 'y': 0, 'z': 0}
                }
            )

            self.floors[self.selected_floor].add_object(obj)
            self._render_tower()
            dialog.destroy()

        ttk.Button(dialog, text="Add", command=add_widget).pack(pady=10)

    def _create_workflow_dialog(self):
        """Show dialog to create workflow linking objects together."""
        if not self.selected_floor:
            from tkinter import messagebox
            messagebox.showwarning("No Floor Selected", "Please click on a floor first")
            return

        floor = self.floors[self.selected_floor]
        if len(floor.objects) == 0:
            from tkinter import messagebox
            messagebox.showwarning("No Objects", "Add objects to the floor first")
            return

        # Create dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title("Create Workflow")
        dialog.geometry("500x400")

        ttk.Label(dialog, text="Create Workflow Chain:", font=("Arial", 12, "bold")).pack(pady=10)
        ttk.Label(dialog, text=f"Floor: {self.selected_floor}").pack()

        # Workflow name
        ttk.Label(dialog, text="Workflow Name:").pack(pady=(10, 0))
        workflow_name = ttk.Entry(dialog, width=40)
        workflow_name.pack(pady=5)

        # Object selection for workflow chain
        ttk.Label(dialog, text="Select objects to link (in order):").pack(pady=(10, 0))

        # Listbox for object selection
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        obj_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=10)
        obj_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=obj_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        obj_listbox.config(yscrollcommand=scrollbar.set)

        # Populate with floor objects
        object_ids = []
        for obj in floor.objects.values():
            obj_listbox.insert(tk.END, f"{obj.type}: {obj.id}")
            object_ids.append(obj.id)

        def create_workflow():
            selected_indices = obj_listbox.curselection()
            if len(selected_indices) < 2:
                from tkinter import messagebox
                messagebox.showwarning("Invalid Selection", "Select at least 2 objects to link")
                return

            # Create workflow chain by linking objects
            prev_obj_id = None
            for idx in selected_indices:
                current_obj_id = object_ids[idx]
                if prev_obj_id:
                    # Add connection from previous to current
                    prev_obj = floor.objects[prev_obj_id]
                    if current_obj_id not in prev_obj.connections:
                        prev_obj.connections.append(current_obj_id)

                prev_obj_id = current_obj_id

            # Create workflow object
            workflow_obj = Floor3DObject(
                f"workflow_{len(floor.objects) + 1}",
                "Workflow",
                {
                    'name': workflow_name.get() or "Unnamed Workflow",
                    'chain': [object_ids[i] for i in selected_indices],
                    'created_at': datetime.now().isoformat()
                }
            )
            floor.add_object(workflow_obj)

            from tkinter import messagebox
            messagebox.showinfo(
                "Workflow Created",
                f"Created workflow linking {len(selected_indices)} objects"
            )

            self._render_tower()
            dialog.destroy()

        ttk.Button(dialog, text="Create Workflow", command=create_workflow).pack(pady=10)

    def _save_layout(self):
        """Save current tower layout."""
        layout_data = {
            'floors': {name: floor.to_dict() for name, floor in self.floors.items()},
            'saved_at': datetime.now().isoformat()
        }

        try:
            from core.config.paths import CONSTRUCT_ROOT as _CONSTRUCT_ROOT  # type: ignore
            layout_path = Path(_CONSTRUCT_ROOT) / "data" / "tower_layout.json"
        except Exception:
            layout_path = Path(__file__).resolve().parent / "data" / "tower_layout.json"
        layout_path.parent.mkdir(parents=True, exist_ok=True)

        with open(layout_path, 'w') as f:
            json.dump(layout_data, f, indent=2)

        from tkinter import messagebox
        messagebox.showinfo("Layout Saved", f"Tower layout saved to {layout_path}")

    def load_layout(self, layout_path: str = None):
        """Load tower layout from file."""
        if layout_path is None:
            try:
                from core.config.paths import CONSTRUCT_ROOT as _CONSTRUCT_ROOT  # type: ignore
                layout_path = Path(_CONSTRUCT_ROOT) / "data" / "tower_layout.json"
            except Exception:
                layout_path = Path(__file__).resolve().parent / "data" / "tower_layout.json"
        else:
            layout_path = Path(layout_path)

        if not layout_path.exists():
            return

        with open(layout_path, 'r') as f:
            layout_data = json.load(f)

        # Restore floors
        for floor_name, floor_data in layout_data['floors'].items():
            if floor_name in self.floors:
                floor = self.floors[floor_name]

                # Restore objects
                for obj_id, obj_data in floor_data['objects'].items():
                    obj = Floor3DObject(obj_id, obj_data['type'], obj_data['data'])
                    floor.add_object(obj)

                floor.users_active = floor_data.get('users_active', [])
                floor.ai_active = floor_data.get('ai_active', [])

        self._render_tower()

    def _simulate_activity(self):
        """Simulate user and AI activity on random floors for demonstration."""
        import random

        # Clear existing activity
        for floor in self.floors.values():
            floor.users_active = []
            floor.ai_active = []

        # Add random user activity
        active_floors = random.sample(list(self.floors.keys()), k=random.randint(2, 5))
        for floor_name in active_floors:
            user_count = random.randint(1, 3)
            self.floors[floor_name].users_active = [f"User{i}" for i in range(user_count)]

        # Add random AI activity
        ai_floors = random.sample(list(self.floors.keys()), k=random.randint(1, 4))
        for floor_name in ai_floors:
            ai_systems = random.choice([
                ["Ollama"],
                ["Claude"],
                ["Ollama", "Claude"],
                ["Neo AI"]
            ])
            self.floors[floor_name].ai_active = ai_systems

        self._render_tower()

        from tkinter import messagebox
        messagebox.showinfo(
            "Activity Simulated",
            f"Added users to {len(active_floors)} floors\n" +
            f"Added AI to {len(ai_floors)} floors"
        )


def show_tower_3d_view(parent: tk.Widget):
    """
    Show 3D tower visualization.

    Args:
        parent: Parent widget

    Usage:
        from core.ui.tower_3d_view import show_tower_3d_view
        show_tower_3d_view(root_window)
    """
    # Create window
    window = tk.Toplevel(parent)
    window.title("LightSpeed Tower - 3D View")
    window.geometry("1200x900")

    # Create visualization
    tower_view = Tower3DVisualization(window)

    # Try to load existing layout
    tower_view.load_layout()

    return tower_view


if __name__ == "__main__":
    # Test the 3D tower view
    root = tk.Tk()
    root.withdraw()

    show_tower_3d_view(root)

    root.mainloop()
