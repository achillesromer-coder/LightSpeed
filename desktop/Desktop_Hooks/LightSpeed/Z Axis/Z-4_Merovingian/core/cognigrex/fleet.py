"""
Cognigrex Fleet Management
LightSpeed Platform - Neo Floor (Z+3)

Manages fleet configurations and formations for multi-AI operations.
Coordinates Cognigrex units in various formations for missions.

Author: LightSpeed Team / ACHILLES
Date: December 9, 2025
"""

from typing import Dict, List, Optional, Literal
import json
from datetime import datetime

from ..services import get_db, EventBus


FormationType = Literal["line", "wedge", "ring", "lattice", "sphere", "custom"]


class FleetManager:
    """
    Manages Cognigrex fleet configurations and formations.

    Features:
    - Create fleet configurations for missions
    - Define formations (line, wedge, ring, lattice)
    - Track unit counts by subtype
    - Assign fleets to missions
    - Monitor fleet status
    """

    def __init__(self):
        self.db = get_db()
        self.event_bus = EventBus()

    def create_fleet(
        self,
        mission_id: Optional[int],
        formation_type: FormationType,
        formation_params: Dict,
        collector_count: int = 0,
        processor_count: int = 0,
        relay_count: int = 0,
        surveyor_count: int = 0,
        status: str = "forming"
    ) -> int:
        """
        Create a new fleet configuration.

        Args:
            mission_id: Optional mission ID to assign fleet
            formation_type: Type of formation (line/wedge/ring/lattice/sphere)
            formation_params: Formation-specific parameters (angles, distances, etc.)
            collector_count: Number of Collector units
            processor_count: Number of Processor units
            relay_count: Number of Relay units
            surveyor_count: Number of Surveyor units
            status: Fleet status (forming/ready/deployed/completed)

        Returns:
            Fleet ID

        Example:
            >>> fleet_mgr = FleetManager()
            >>> fleet_id = fleet_mgr.create_fleet(
            ...     mission_id=1,
            ...     formation_type="wedge",
            ...     formation_params={
            ...         "apex_angle": 60,
            ...         "spacing_km": 100,
            ...         "depth_km": 500
            ...     },
            ...     collector_count=3,
            ...     processor_count=2,
            ...     relay_count=1,
            ...     surveyor_count=1
            ... )
        """
        total_units = collector_count + processor_count + relay_count + surveyor_count
        params_json = json.dumps(formation_params)

        query = """
            INSERT INTO cognigrex_fleet
            (mission_id, formation_type, formation_params, total_units,
             collector_count, processor_count, relay_count, surveyor_count, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(
                query,
                (mission_id, formation_type, params_json, total_units,
                 collector_count, processor_count, relay_count, surveyor_count, status)
            )
            fleet_id = cursor.lastrowid
            conn.commit()

        # Emit event
        self.event_bus.publish('cognigrex.fleet.created', {
            'fleet_id': fleet_id,
            'mission_id': mission_id,
            'formation_type': formation_type,
            'total_units': total_units,
            'status': status
        })

        return fleet_id

    def get_fleet(self, fleet_id: int) -> Optional[Dict]:
        """Get fleet configuration by ID."""
        query = "SELECT * FROM cognigrex_fleet WHERE id = ?"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (fleet_id,))
            row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_dict(row)

    def get_fleets_by_mission(self, mission_id: int) -> List[Dict]:
        """Get all fleets assigned to a mission."""
        query = "SELECT * FROM cognigrex_fleet WHERE mission_id = ? ORDER BY created_at"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (mission_id,))
            rows = cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    def get_fleets_by_status(self, status: str) -> List[Dict]:
        """Get all fleets with a specific status."""
        query = "SELECT * FROM cognigrex_fleet WHERE status = ? ORDER BY created_at DESC"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (status,))
            rows = cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    def update_fleet_status(self, fleet_id: int, status: str) -> bool:
        """
        Update fleet status.

        Status options:
        - forming: Fleet being assembled
        - ready: Ready for deployment
        - deployed: On active mission
        - completed: Mission completed
        - disbanded: Fleet disbanded
        """
        query = """
            UPDATE cognigrex_fleet
            SET status = ?, updated_at = datetime('now')
            WHERE id = ?
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (status, fleet_id))
            conn.commit()
            updated = cursor.rowcount > 0

        if updated:
            self.event_bus.publish('cognigrex.fleet.status_changed', {
                'fleet_id': fleet_id,
                'new_status': status,
                'timestamp': datetime.now().isoformat()
            })

        return updated

    def update_formation_params(self, fleet_id: int, formation_params: Dict) -> bool:
        """Update fleet formation parameters."""
        params_json = json.dumps(formation_params)

        query = """
            UPDATE cognigrex_fleet
            SET formation_params = ?, updated_at = datetime('now')
            WHERE id = ?
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (params_json, fleet_id))
            conn.commit()
            updated = cursor.rowcount > 0

        return updated

    def assign_to_mission(self, fleet_id: int, mission_id: int) -> bool:
        """Assign fleet to a mission."""
        query = """
            UPDATE cognigrex_fleet
            SET mission_id = ?, updated_at = datetime('now')
            WHERE id = ?
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (mission_id, fleet_id))
            conn.commit()
            updated = cursor.rowcount > 0

        if updated:
            self.event_bus.publish('cognigrex.fleet.assigned', {
                'fleet_id': fleet_id,
                'mission_id': mission_id
            })

        return updated

    def get_fleet_composition_summary(self, fleet_id: int) -> Dict:
        """
        Get summary of fleet composition.

        Returns:
            Dict with unit counts and percentages
        """
        fleet = self.get_fleet(fleet_id)
        if not fleet:
            return {}

        total = fleet['total_units']
        if total == 0:
            return {
                'total_units': 0,
                'composition': {}
            }

        return {
            'total_units': total,
            'composition': {
                'Collector': {
                    'count': fleet['collector_count'],
                    'percentage': round(fleet['collector_count'] / total * 100, 1)
                },
                'Processor': {
                    'count': fleet['processor_count'],
                    'percentage': round(fleet['processor_count'] / total * 100, 1)
                },
                'Relay': {
                    'count': fleet['relay_count'],
                    'percentage': round(fleet['relay_count'] / total * 100, 1)
                },
                'Surveyor': {
                    'count': fleet['surveyor_count'],
                    'percentage': round(fleet['surveyor_count'] / total * 100, 1)
                }
            }
        }

    def get_all_active_fleets(self) -> List[Dict]:
        """Get all fleets that are ready or deployed."""
        query = """
            SELECT * FROM cognigrex_fleet
            WHERE status IN ('ready', 'deployed')
            ORDER BY created_at DESC
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query)
            rows = cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    def calculate_formation_coordinates(
        self,
        formation_type: FormationType,
        formation_params: Dict,
        unit_count: int
    ) -> List[Dict]:
        """
        Calculate 3D coordinates for units in formation.

        Args:
            formation_type: Type of formation
            formation_params: Formation parameters
            unit_count: Number of units to position

        Returns:
            List of coordinate dicts: [{"x": 0, "y": 0, "z": 0, "unit_index": 0}, ...]

        This is a placeholder - full implementation would use actual orbital mechanics
        """
        coordinates = []

        if formation_type == "line":
            spacing = formation_params.get("spacing_km", 100)
            for i in range(unit_count):
                coordinates.append({
                    "x": i * spacing,
                    "y": 0,
                    "z": 0,
                    "unit_index": i
                })

        elif formation_type == "wedge":
            spacing = formation_params.get("spacing_km", 100)
            apex_angle = formation_params.get("apex_angle", 60)
            # Simplified wedge formation
            for i in range(unit_count):
                row = int(i ** 0.5)
                col = i - row ** 2
                coordinates.append({
                    "x": row * spacing,
                    "y": col * spacing - row * spacing / 2,
                    "z": 0,
                    "unit_index": i
                })

        elif formation_type == "ring":
            radius = formation_params.get("radius_km", 500)
            for i in range(unit_count):
                angle = 2 * 3.14159 * i / unit_count
                coordinates.append({
                    "x": radius * (angle ** 0.5),  # Simplified
                    "y": radius * angle,
                    "z": 0,
                    "unit_index": i
                })

        elif formation_type == "lattice":
            spacing = formation_params.get("spacing_km", 100)
            grid_size = int(unit_count ** (1/3)) + 1
            for i in range(unit_count):
                x = (i // (grid_size * grid_size)) * spacing
                y = ((i // grid_size) % grid_size) * spacing
                z = (i % grid_size) * spacing
                coordinates.append({
                    "x": x,
                    "y": y,
                    "z": z,
                    "unit_index": i
                })

        elif formation_type == "sphere":
            radius = formation_params.get("radius_km", 500)
            # Fibonacci sphere distribution (simplified)
            for i in range(unit_count):
                phi = 3.14159 * (3.0 - 5.0 ** 0.5) * i
                y = 1 - (i / (unit_count - 1)) * 2
                r = (1 - y * y) ** 0.5
                coordinates.append({
                    "x": r * (phi ** 0.5) * radius,  # Simplified
                    "y": y * radius,
                    "z": r * phi * radius,
                    "unit_index": i
                })

        return coordinates

    def delete_fleet(self, fleet_id: int) -> bool:
        """Delete a fleet configuration."""
        query = "DELETE FROM cognigrex_fleet WHERE id = ?"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (fleet_id,))
            conn.commit()
            deleted = cursor.rowcount > 0

        if deleted:
            self.event_bus.publish('cognigrex.fleet.deleted', {
                'fleet_id': fleet_id
            })

        return deleted

    def _row_to_dict(self, row) -> Dict:
        """Convert database row to dictionary."""
        if not row:
            return {}

        return {
            'id': row[0],
            'mission_id': row[1],
            'formation_type': row[2],
            'formation_params': json.loads(row[3]) if row[3] else {},
            'total_units': row[4],
            'collector_count': row[5],
            'processor_count': row[6],
            'relay_count': row[7],
            'surveyor_count': row[8],
            'status': row[9],
            'created_at': row[10],
            'updated_at': row[11] if len(row) > 11 else None
        }
