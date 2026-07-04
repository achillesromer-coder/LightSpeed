"""
Cognigrex Model Management
LightSpeed Platform - Neo Floor (Z+3)

Manages Cognigrex AI models across space and terrestrial nodes.
Handles model creation, configuration, status tracking, and hierarchical relationships.

Author: LightSpeed Team / ACHILLES
Date: December 9, 2025
"""

from typing import Dict, List, Optional, Literal
from enum import Enum
import json
from datetime import datetime

from ..services import get_db, EventBus


class CognigrexSubtype(str, Enum):
    """Cognigrex AI subtypes with specialized functions."""
    COLLECTOR = "Collector"      # Material collection and sorting
    PROCESSOR = "Processor"       # Refinement and analysis
    RELAY = "Relay"               # Communication and data relay
    SURVEYOR = "Surveyor"         # Surveying, mapping, composition analysis


class CognigrexManager:
    """
    Manages Cognigrex AI models across distributed nodes.

    Features:
    - Create and configure AI models with specific subtypes
    - Track model status and location (space/terrestrial)
    - Manage hierarchical relationships (parent/child models)
    - Query models by subtype, status, or location
    - Emit events for model state changes
    """

    def __init__(self):
        self.db = get_db()
        self.event_bus = EventBus()

    def create_model(
        self,
        name: str,
        subtype: CognigrexSubtype,
        location: str,
        parameters: Optional[Dict] = None,
        parent_model_id: Optional[int] = None,
        status: str = "inactive"
    ) -> int:
        """
        Create a new Cognigrex AI model.

        Args:
            name: Model identifier (e.g., "Collector-Alpha-01")
            subtype: Type of AI unit (Collector/Processor/Relay/Surveyor)
            location: Physical or orbital location
            parameters: JSON dict with model capabilities and config
            parent_model_id: Optional parent model for hierarchical structure
            status: Initial status (inactive/active/training/deployed)

        Returns:
            ID of created model

        Example:
            >>> mgr = CognigrexManager()
            >>> model_id = mgr.create_model(
            ...     name="Collector-Alpha-02",
            ...     subtype=CognigrexSubtype.COLLECTOR,
            ...     location="LEO-Station-2",
            ...     parameters={
            ...         "collection_capacity": "high",
            ...         "range_km": 75000,
            ...         "functions": ["material_collection", "sorting", "transport"]
            ...     }
            ... )
        """
        params_json = json.dumps(parameters) if parameters else None

        query = """
            INSERT INTO cognigrex_models (name, subtype, location, status, parameters, parent_model_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(
                query,
                (name, subtype.value, location, status, params_json, parent_model_id)
            )
            model_id = cursor.lastrowid
            conn.commit()

        # Emit event
        self.event_bus.publish('cognigrex.model.created', {
            'model_id': model_id,
            'name': name,
            'subtype': subtype.value,
            'location': location,
            'status': status
        })

        return model_id

    def get_model(self, model_id: int) -> Optional[Dict]:
        """Get model details by ID."""
        query = "SELECT * FROM cognigrex_models WHERE id = ?"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (model_id,))
            row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_dict(row)

    def update_status(self, model_id: int, status: str) -> bool:
        """
        Update model status.

        Status options:
        - inactive: Not operational
        - training: In training phase
        - active: Operational and ready
        - deployed: On active mission
        - maintenance: Under maintenance
        - error: Error state
        """
        query = """
            UPDATE cognigrex_models
            SET status = ?, updated_at = datetime('now')
            WHERE id = ?
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (status, model_id))
            conn.commit()
            updated = cursor.rowcount > 0

        if updated:
            self.event_bus.publish('cognigrex.model.status_changed', {
                'model_id': model_id,
                'new_status': status,
                'timestamp': datetime.now().isoformat()
            })

        return updated

    def update_location(self, model_id: int, location: str) -> bool:
        """Update model location (for mobile units)."""
        query = """
            UPDATE cognigrex_models
            SET location = ?, updated_at = datetime('now')
            WHERE id = ?
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (location, model_id))
            conn.commit()
            updated = cursor.rowcount > 0

        if updated:
            self.event_bus.publish('cognigrex.model.location_changed', {
                'model_id': model_id,
                'new_location': location
            })

        return updated

    def update_parameters(self, model_id: int, parameters: Dict) -> bool:
        """Update model parameters/configuration."""
        params_json = json.dumps(parameters)

        query = """
            UPDATE cognigrex_models
            SET parameters = ?, updated_at = datetime('now')
            WHERE id = ?
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (params_json, model_id))
            conn.commit()
            updated = cursor.rowcount > 0

        return updated

    def get_models_by_subtype(self, subtype: CognigrexSubtype) -> List[Dict]:
        """Get all models of a specific subtype."""
        query = "SELECT * FROM cognigrex_models WHERE subtype = ? ORDER BY name"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (subtype.value,))
            rows = cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    def get_models_by_status(self, status: str) -> List[Dict]:
        """Get all models with a specific status."""
        query = "SELECT * FROM cognigrex_models WHERE status = ? ORDER BY name"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (status,))
            rows = cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    def get_models_by_location(self, location: str) -> List[Dict]:
        """Get all models at a specific location."""
        query = "SELECT * FROM cognigrex_models WHERE location = ? ORDER BY name"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (location,))
            rows = cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    def get_child_models(self, parent_model_id: int) -> List[Dict]:
        """Get all child models of a parent (hierarchical structure)."""
        query = "SELECT * FROM cognigrex_models WHERE parent_model_id = ? ORDER BY name"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (parent_model_id,))
            rows = cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    def get_all_active_models(self) -> List[Dict]:
        """Get all active models across all locations."""
        query = """
            SELECT * FROM cognigrex_models
            WHERE status IN ('active', 'deployed')
            ORDER BY subtype, name
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query)
            rows = cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    def get_fleet_composition(self) -> Dict[str, int]:
        """
        Get count of models by subtype.

        Returns:
            Dict with counts: {"Collector": 5, "Processor": 3, ...}
        """
        query = """
            SELECT subtype, COUNT(*) as count
            FROM cognigrex_models
            GROUP BY subtype
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query)
            rows = cursor.fetchall()

        return {row[0]: row[1] for row in rows}

    def get_status_summary(self) -> Dict[str, int]:
        """
        Get count of models by status.

        Returns:
            Dict with counts: {"active": 10, "inactive": 5, ...}
        """
        query = """
            SELECT status, COUNT(*) as count
            FROM cognigrex_models
            GROUP BY status
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query)
            rows = cursor.fetchall()

        return {row[0]: row[1] for row in rows}

    def delete_model(self, model_id: int) -> bool:
        """Delete a model (use with caution)."""
        query = "DELETE FROM cognigrex_models WHERE id = ?"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (model_id,))
            conn.commit()
            deleted = cursor.rowcount > 0

        if deleted:
            self.event_bus.publish('cognigrex.model.deleted', {
                'model_id': model_id
            })

        return deleted

    def _row_to_dict(self, row) -> Dict:
        """Convert database row to dictionary."""
        if not row:
            return {}

        return {
            'id': row[0],
            'name': row[1],
            'subtype': row[2],
            'location': row[3],
            'status': row[4],
            'parameters': json.loads(row[5]) if row[5] else {},
            'parent_model_id': row[6],
            'created_at': row[7],
            'updated_at': row[8] if len(row) > 8 else None
        }
