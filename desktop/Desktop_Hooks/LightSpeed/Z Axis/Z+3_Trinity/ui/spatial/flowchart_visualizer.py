"""
LightSpeed V0.9.11 - Project Flowchart Visualizer
Y-axis folder layout spread across curved 1.5m surface

Features:
- Folders arranged on Y-axis (vertical hierarchy)
- Spread across 1.5m curved UI
- Parent/child tile connections
- Interactive navigation
- Auto-layout algorithms
- Depth-based rendering

Author: LightSpeed Team / ACHILLES
Version: 0.9.11
Date: January 4, 2026
"""

import tkinter as tk
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from pathlib import Path
import json

from .enhanced_bento_grid import EnhancedBentoGrid, BentoTile, TileType
from core.config.paths import LIGHTSPEED_ROOT, Z_AXIS_ROOT


@dataclass
class FlowchartNode:
    """Node in project flowchart"""
    id: str
    label: str
    node_type: str  # 'folder', 'file', 'function', 'class'
    path: Path
    parent_id: Optional[str] = None
    children_ids: List[str] = None
    level: int = 0  # Y-axis level (depth in hierarchy)
    position_index: int = 0  # Position among siblings
    tile: Optional[BentoTile] = None

    def __post_init__(self):
        if self.children_ids is None:
            self.children_ids = []


class FlowchartLayout:
    """
    Layout algorithm for flowchart visualization.

    Positions nodes on Y-axis based on hierarchy and spreads across
    curved 1.5m surface.
    """

    # Layout constants
    Y_SPACING = 150  # pixels between levels
    X_ANGLE_SPREAD = 90.0  # degrees (-45 to 45)
    SIBLING_SPACING = 8.0  # degrees between siblings

    def __init__(self, grid: EnhancedBentoGrid):
        """
        Initialize layout algorithm.

        Args:
            grid: Enhanced Bento grid for positioning
        """
        self.grid = grid

    def layout_tree(self, root_node: FlowchartNode, all_nodes: Dict[str, FlowchartNode]):
        """
        Layout entire tree starting from root.

        Args:
            root_node: Root node of tree
            all_nodes: Dictionary of all nodes by ID
        """
        # First pass: Calculate levels and sibling positions
        self._calculate_levels(root_node, all_nodes, level=0)

        # Second pass: Calculate angles (horizontal spread)
        self._calculate_angles(root_node, all_nodes)

        # Third pass: Create tiles
        self._create_tiles(root_node, all_nodes)

    def _calculate_levels(self, node: FlowchartNode, all_nodes: Dict[str, FlowchartNode], level: int):
        """Recursively calculate Y-axis levels"""
        node.level = level

        # Process children
        for i, child_id in enumerate(node.children_ids):
            if child_id in all_nodes:
                child = all_nodes[child_id]
                child.position_index = i
                self._calculate_levels(child, all_nodes, level + 1)

    def _calculate_angles(self, node: FlowchartNode, all_nodes: Dict[str, FlowchartNode],
                         parent_angle: float = 0.0, sibling_count: int = 1, sibling_index: int = 0):
        """
        Recursively calculate horizontal angles.

        Spreads children evenly within parent's allocated angle range.
        """
        # Calculate this node's angle
        if node.level == 0:
            # Root at center
            angle = 0.0
        else:
            # Spread siblings within parent's range
            if sibling_count == 1:
                angle = parent_angle
            else:
                # Spread range around parent
                spread_range = min(self.SIBLING_SPACING * sibling_count, self.X_ANGLE_SPREAD)
                start_angle = parent_angle - spread_range / 2
                angle = start_angle + (sibling_index * spread_range / (sibling_count - 1))

        # Store angle (will be used for tile position)
        if not hasattr(node, 'angle'):
            node.angle = angle

        # Process children
        child_count = len(node.children_ids)
        for i, child_id in enumerate(node.children_ids):
            if child_id in all_nodes:
                child = all_nodes[child_id]
                self._calculate_angles(child, all_nodes, angle, child_count, i)

    def _create_tiles(self, node: FlowchartNode, all_nodes: Dict[str, FlowchartNode]):
        """Create BentoTile for each node"""
        # Determine tile type
        tile_type = TileType.FOLDER
        if node.node_type == 'file':
            tile_type = TileType.DATASET
        elif node.node_type == 'function':
            tile_type = TileType.FUNCTION
        elif node.node_type == 'class':
            tile_type = TileType.FLOW_NODE

        # Calculate position
        angle = getattr(node, 'angle', 0.0)
        distance = 1.5  # meters (locked radius)
        y_offset = -node.level * (self.Y_SPACING / 200.0)  # Convert pixels to meters (rough)

        # Depth based on level (deeper = more transparent)
        depth = max(0.2, 1.0 - (node.level * 0.15))

        # Create tile
        tile = BentoTile(
            id=node.id,
            type=tile_type,
            label=node.label,
            position=(angle, distance, y_offset),
            size=(180, 100),
            depth=depth,
            parent_tile=node.parent_id,
            data={"path": str(node.path), "node_type": node.node_type}
        )

        node.tile = tile

        # Process children
        for child_id in node.children_ids:
            if child_id in all_nodes:
                child = all_nodes[child_id]
                self._create_tiles(child, all_nodes)


class FlowchartVisualizer:
    """
    Project flowchart visualizer.

    Parses project structure and visualizes as flowchart on curved surface.
    """

    def __init__(self, grid: EnhancedBentoGrid):
        """
        Initialize flowchart visualizer.

        Args:
            grid: Enhanced Bento grid for rendering
        """
        self.grid = grid
        self.layout = FlowchartLayout(grid)

        # Flowchart data
        self.nodes: Dict[str, FlowchartNode] = {}
        self.root_node: Optional[FlowchartNode] = None

    def load_from_directory(self, root_path: Path, max_depth: int = 3,
                           include_files: bool = True):
        """
        Load flowchart from directory structure.

        Args:
            root_path: Root directory to visualize
            max_depth: Maximum depth to traverse
            include_files: Whether to include files (not just folders)
        """
        self.nodes.clear()

        # Create root node
        root_id = self._path_to_id(root_path)
        self.root_node = FlowchartNode(
            id=root_id,
            label=root_path.name,
            node_type='folder',
            path=root_path,
            level=0
        )
        self.nodes[root_id] = self.root_node

        # Recursively build tree
        self._build_tree(root_path, root_id, current_depth=0, max_depth=max_depth,
                        include_files=include_files)

        # Layout and create tiles
        self.layout.layout_tree(self.root_node, self.nodes)

        # Add tiles to grid
        self._add_tiles_to_grid(self.root_node)

        print(f"[FLOWCHART] Loaded {len(self.nodes)} nodes from {root_path}")

    def _build_tree(self, path: Path, parent_id: str, current_depth: int,
                   max_depth: int, include_files: bool):
        """Recursively build flowchart tree"""
        if current_depth >= max_depth:
            return

        try:
            # List directory contents
            items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))

            for item in items:
                # Skip hidden files/folders and __pycache__
                if item.name.startswith('.') or item.name == '__pycache__':
                    continue

                # Skip venv directories
                if item.name in ['venv', '.venv', 'env', 'virtualenv']:
                    continue

                # Determine node type
                if item.is_dir():
                    node_type = 'folder'
                elif item.suffix == '.py':
                    node_type = 'file'
                else:
                    # Skip non-Python files for now
                    if not include_files:
                        continue
                    node_type = 'file'

                # Create node
                node_id = self._path_to_id(item)
                node = FlowchartNode(
                    id=node_id,
                    label=item.name,
                    node_type=node_type,
                    path=item,
                    parent_id=parent_id
                )

                self.nodes[node_id] = node

                # Add to parent's children
                if parent_id in self.nodes:
                    self.nodes[parent_id].children_ids.append(node_id)

                # Recurse into directories
                if item.is_dir():
                    self._build_tree(item, node_id, current_depth + 1,
                                   max_depth, include_files)

        except PermissionError:
            print(f"[FLOWCHART] Permission denied: {path}")

    def _path_to_id(self, path: Path) -> str:
        """Convert path to unique node ID"""
        return f"node_{hash(str(path))}"

    def _add_tiles_to_grid(self, node: FlowchartNode):
        """Recursively add tiles to grid"""
        if node.tile:
            self.grid.add_tile(node.tile)

        # Process children
        for child_id in node.children_ids:
            if child_id in self.nodes:
                self._add_tiles_to_grid(self.nodes[child_id])

    def load_from_z_floors(self):
        """Load flowchart from Z-floor structure"""
        if not Z_AXIS_ROOT.exists():
            print("[FLOWCHART] Z Axis folder not found")
            return

        self.load_from_directory(Z_AXIS_ROOT, max_depth=3, include_files=False)

    def load_from_project_root(self):
        """Load flowchart from project root"""
        self.load_from_directory(LIGHTSPEED_ROOT, max_depth=2, include_files=True)

    def focus_on_node(self, node_id: str):
        """
        Focus camera on specific node.

        Args:
            node_id: Node to focus on
        """
        if node_id not in self.nodes:
            return

        node = self.nodes[node_id]
        if not node.tile:
            return

        # Get tile position
        angle, distance, y_offset = node.tile.position

        # Scroll grid to center this tile
        # Calculate target Y offset
        projection = self.grid.project_to_screen(angle, distance, y_offset)
        if projection:
            _, screen_y, _ = projection
            target_offset = screen_y - self.grid.height // 2

            # Smooth scroll to target
            self.grid.scroll_y(target_offset)

    def expand_node(self, node_id: str):
        """
        Expand node to show children (if collapsed).

        Args:
            node_id: Node to expand
        """
        if node_id not in self.nodes:
            return

        node = self.nodes[node_id]

        # Mark as expanded (would need to track collapse state)
        # For now, just ensure children are visible
        for child_id in node.children_ids:
            if child_id in self.nodes:
                child = self.nodes[child_id]
                if child.tile and child.tile.id not in self.grid.tiles:
                    self.grid.add_tile(child.tile)

        # Re-render connections
        self.grid.render_flowchart_connections()

    def collapse_node(self, node_id: str):
        """
        Collapse node to hide children.

        Args:
            node_id: Node to collapse
        """
        if node_id not in self.nodes:
            return

        node = self.nodes[node_id]

        # Recursively remove children tiles
        self._remove_children_tiles(node)

        # Re-render connections
        self.grid.render_flowchart_connections()

    def _remove_children_tiles(self, node: FlowchartNode):
        """Recursively remove children tiles"""
        for child_id in node.children_ids:
            if child_id in self.nodes:
                child = self.nodes[child_id]

                # Remove tile
                if child.tile and child.tile.id in self.grid.tiles:
                    self.grid.remove_tile(child.tile.id)

                # Recurse
                self._remove_children_tiles(child)

    def find_node_by_path(self, path: Path) -> Optional[FlowchartNode]:
        """
        Find node by file path.

        Args:
            path: Path to find

        Returns:
            FlowchartNode or None
        """
        node_id = self._path_to_id(path)
        return self.nodes.get(node_id)

    def get_node_ancestors(self, node_id: str) -> List[FlowchartNode]:
        """
        Get all ancestors of a node (path to root).

        Args:
            node_id: Node ID

        Returns:
            List of ancestor nodes (root to parent)
        """
        if node_id not in self.nodes:
            return []

        ancestors = []
        current = self.nodes[node_id]

        while current.parent_id:
            if current.parent_id in self.nodes:
                parent = self.nodes[current.parent_id]
                ancestors.insert(0, parent)
                current = parent
            else:
                break

        return ancestors

    def export_flowchart(self, output_path: Path):
        """
        Export flowchart structure to JSON.

        Args:
            output_path: Output file path
        """
        try:
            # Build export data
            data = {
                "root": self.root_node.id if self.root_node else None,
                "nodes": []
            }

            for node in self.nodes.values():
                node_data = {
                    "id": node.id,
                    "label": node.label,
                    "type": node.node_type,
                    "path": str(node.path),
                    "parent": node.parent_id,
                    "children": node.children_ids,
                    "level": node.level,
                    "position": {
                        "angle": getattr(node, 'angle', 0.0),
                        "level": node.level
                    }
                }
                data["nodes"].append(node_data)

            # Write to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"[FLOWCHART] Exported to {output_path}")

        except Exception as e:
            print(f"[FLOWCHART] Export failed: {e}")

    def import_flowchart(self, input_path: Path):
        """
        Import flowchart structure from JSON.

        Args:
            input_path: Input file path
        """
        try:
            with open(input_path, 'r') as f:
                data = json.load(f)

            self.nodes.clear()

            # Recreate nodes
            for node_data in data["nodes"]:
                node = FlowchartNode(
                    id=node_data["id"],
                    label=node_data["label"],
                    node_type=node_data["type"],
                    path=Path(node_data["path"]),
                    parent_id=node_data.get("parent"),
                    children_ids=node_data["children"],
                    level=node_data["level"]
                )

                # Restore angle
                if "position" in node_data and "angle" in node_data["position"]:
                    node.angle = node_data["position"]["angle"]

                self.nodes[node.id] = node

            # Find root
            root_id = data.get("root")
            if root_id and root_id in self.nodes:
                self.root_node = self.nodes[root_id]

                # Create tiles
                self.layout._create_tiles(self.root_node, self.nodes)

                # Add to grid
                self._add_tiles_to_grid(self.root_node)

            print(f"[FLOWCHART] Imported {len(self.nodes)} nodes from {input_path}")

        except Exception as e:
            print(f"[FLOWCHART] Import failed: {e}")


# Export
__all__ = ['FlowchartVisualizer', 'FlowchartNode', 'FlowchartLayout']
