"""
Cognigrex Training Management
LightSpeed Platform - Neo Floor (Z+3)

Manages AI training data from simulations (Mark III/V, Extraction, Launch).
Tracks training sessions, success rates, and model improvement over time.

Author: LightSpeed Team / ACHILLES
Date: December 9, 2025
"""

from typing import Dict, List, Optional, Literal
import json
from datetime import datetime

from ..services import get_db, EventBus


TrainingType = Literal["mark3", "mark5", "extraction", "launch", "orbital", "supply_chain"]


class TrainingManager:
    """
    Manages Cognigrex AI training data from simulations.

    Features:
    - Record training sessions from simulation runs
    - Track success rates and improvement over time
    - Link training data to specific simulations
    - Analyze training effectiveness by model/type
    - Provide feedback loops for continuous improvement
    """

    def __init__(self):
        self.db = get_db()
        self.event_bus = EventBus()

    def record_training(
        self,
        model_id: int,
        training_type: TrainingType,
        input_data: Dict,
        output_data: Dict,
        success_rate: float,
        simulation_id: Optional[int] = None
    ) -> int:
        """
        Record a training session.

        Args:
            model_id: ID of Cognigrex model being trained
            training_type: Type of training (mark3/mark5/extraction/launch)
            input_data: Input parameters for training
            output_data: Model output/predictions
            success_rate: Success rate (0.0 to 1.0)
            simulation_id: Optional link to specific simulation

        Returns:
            ID of training record

        Example:
            >>> trainer = TrainingManager()
            >>> training_id = trainer.record_training(
            ...     model_id=1,
            ...     training_type="mark3",
            ...     input_data={"asteroid_mass": 1e15, "extraction_rate": 1000},
            ...     output_data={"predicted_efficiency": 0.85, "time_hours": 240},
            ...     success_rate=0.92,
            ...     simulation_id=42
            ... )
        """
        input_json = json.dumps(input_data)
        output_json = json.dumps(output_data)

        query = """
            INSERT INTO cognigrex_training
            (model_id, simulation_id, training_type, input_data, output_data, success_rate)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(
                query,
                (model_id, simulation_id, training_type, input_json, output_json, success_rate)
            )
            training_id = cursor.lastrowid
            conn.commit()

        # Emit event
        self.event_bus.publish('cognigrex.training.recorded', {
            'training_id': training_id,
            'model_id': model_id,
            'training_type': training_type,
            'success_rate': success_rate
        })

        return training_id

    def get_training_history(self, model_id: int, limit: int = 100) -> List[Dict]:
        """Get training history for a model."""
        query = """
            SELECT * FROM cognigrex_training
            WHERE model_id = ?
            ORDER BY trained_at DESC
            LIMIT ?
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (model_id, limit))
            rows = cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    def get_training_by_type(
        self,
        model_id: int,
        training_type: TrainingType,
        limit: int = 50
    ) -> List[Dict]:
        """Get training history filtered by type."""
        query = """
            SELECT * FROM cognigrex_training
            WHERE model_id = ? AND training_type = ?
            ORDER BY trained_at DESC
            LIMIT ?
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (model_id, training_type, limit))
            rows = cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    def get_average_success_rate(
        self,
        model_id: int,
        training_type: Optional[TrainingType] = None
    ) -> float:
        """
        Calculate average success rate for a model.

        Args:
            model_id: Model ID
            training_type: Optional filter by training type

        Returns:
            Average success rate (0.0 to 1.0)
        """
        if training_type:
            query = """
                SELECT AVG(success_rate) FROM cognigrex_training
                WHERE model_id = ? AND training_type = ?
            """
            params = (model_id, training_type)
        else:
            query = """
                SELECT AVG(success_rate) FROM cognigrex_training
                WHERE model_id = ?
            """
            params = (model_id,)

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, params)
            result = cursor.fetchone()

        return result[0] if result and result[0] is not None else 0.0

    def get_improvement_trend(
        self,
        model_id: int,
        training_type: TrainingType,
        window_size: int = 10
    ) -> Dict:
        """
        Calculate improvement trend over time.

        Args:
            model_id: Model ID
            training_type: Training type to analyze
            window_size: Number of recent sessions to compare

        Returns:
            Dict with trend analysis:
            {
                "recent_avg": 0.92,
                "overall_avg": 0.85,
                "improvement": 0.07,
                "trend": "improving"
            }
        """
        # Get recent sessions
        query_recent = """
            SELECT AVG(success_rate) FROM (
                SELECT success_rate FROM cognigrex_training
                WHERE model_id = ? AND training_type = ?
                ORDER BY trained_at DESC
                LIMIT ?
            )
        """

        # Get overall average
        query_overall = """
            SELECT AVG(success_rate) FROM cognigrex_training
            WHERE model_id = ? AND training_type = ?
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query_recent, (model_id, training_type, window_size))
            recent_avg = cursor.fetchone()[0] or 0.0

            cursor = conn.execute(query_overall, (model_id, training_type))
            overall_avg = cursor.fetchone()[0] or 0.0

        improvement = recent_avg - overall_avg

        if improvement > 0.05:
            trend = "improving"
        elif improvement < -0.05:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "recent_avg": round(recent_avg, 4),
            "overall_avg": round(overall_avg, 4),
            "improvement": round(improvement, 4),
            "trend": trend
        }

    def get_training_stats_by_type(self, model_id: int) -> Dict[str, Dict]:
        """
        Get training statistics grouped by type.

        Returns:
            Dict with stats per training type:
            {
                "mark3": {"count": 50, "avg_success": 0.92},
                "extraction": {"count": 30, "avg_success": 0.88},
                ...
            }
        """
        query = """
            SELECT training_type, COUNT(*) as count, AVG(success_rate) as avg_success
            FROM cognigrex_training
            WHERE model_id = ?
            GROUP BY training_type
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (model_id,))
            rows = cursor.fetchall()

        stats = {}
        for row in rows:
            training_type, count, avg_success = row
            stats[training_type] = {
                "count": count,
                "avg_success": round(avg_success, 4) if avg_success else 0.0
            }

        return stats

    def get_simulation_training_data(self, simulation_id: int) -> List[Dict]:
        """Get all training data linked to a specific simulation."""
        query = """
            SELECT * FROM cognigrex_training
            WHERE simulation_id = ?
            ORDER BY trained_at DESC
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (simulation_id,))
            rows = cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    def get_top_performing_models(
        self,
        training_type: TrainingType,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get top performing models for a specific training type.

        Returns:
            List of models with their average success rates
        """
        query = """
            SELECT
                ct.model_id,
                cm.name,
                cm.subtype,
                AVG(ct.success_rate) as avg_success,
                COUNT(*) as training_count
            FROM cognigrex_training ct
            JOIN cognigrex_models cm ON ct.model_id = cm.id
            WHERE ct.training_type = ?
            GROUP BY ct.model_id
            ORDER BY avg_success DESC
            LIMIT ?
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (training_type, limit))
            rows = cursor.fetchall()

        return [
            {
                'model_id': row[0],
                'name': row[1],
                'subtype': row[2],
                'avg_success': round(row[3], 4),
                'training_count': row[4]
            }
            for row in rows
        ]

    def delete_training_data(self, training_id: int) -> bool:
        """Delete a training record."""
        query = "DELETE FROM cognigrex_training WHERE id = ?"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (training_id,))
            conn.commit()
            deleted = cursor.rowcount > 0

        return deleted

    def _row_to_dict(self, row) -> Dict:
        """Convert database row to dictionary."""
        if not row:
            return {}

        return {
            'id': row[0],
            'model_id': row[1],
            'simulation_id': row[2],
            'training_type': row[3],
            'input_data': json.loads(row[4]) if row[4] else {},
            'output_data': json.loads(row[5]) if row[5] else {},
            'success_rate': row[6],
            'trained_at': row[7]
        }
