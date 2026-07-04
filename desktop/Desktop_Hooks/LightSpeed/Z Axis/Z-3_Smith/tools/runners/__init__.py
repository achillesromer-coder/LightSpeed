"""
Smith Tool Runners
==================

This package contains all tool runners for the LightSpeed platform.
Each runner is responsible for executing specific simulation/analysis tools.

Runners:
- GMAT: General Mission Analysis Tool (orbital mechanics)
- RFS_EMFF: RF/EM Field Analysis (electromagnetic simulations)
- Energy: Solar Hull / Free Flow Energy Analysis
- MagLev: Magnetic Levitation Simulations
- Propulsion: Advanced Propulsion Systems

All runners follow the standard pattern:
1. Validate input against schema
2. Execute tool/simulation
3. Generate results
4. Create manifest.json
5. Publish completion event
6. Return result path

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 19, 2026
"""

from pathlib import Path
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

# Add Z-4 to path for core services
Z_AXIS_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Z_AXIS_ROOT / "Z-4_Merovingian"))

try:
    from core.services import get_db, get_event_bus, get_storage, get_logger
except ImportError:
    print("[Smith Runners] Warning: Core services not available")
    get_db = get_event_bus = get_storage = get_logger = lambda: None


class BaseRunner:
    """
    Base class for all tool runners.
    Provides common functionality for validation, logging, and manifest creation.
    """

    def __init__(self, tool_name: str, version: str = "1.0.0"):
        self.tool_name = tool_name
        self.version = version
        self.run_id = str(uuid.uuid4())[:8]
        self.timestamp = datetime.now().isoformat()

        # Initialize core services
        try:
            self.db = get_db()
            self.event_bus = get_event_bus()
            self.storage = get_storage()
            self.logger = get_logger()
        except:
            self.db = None
            self.event_bus = None
            self.storage = None
            self.logger = None

        # Setup output directory
        self.output_dir = self._setup_output_directory()

    def _setup_output_directory(self) -> Path:
        """Create output directory for this run"""
        base_dir = Z_AXIS_ROOT.parent / "operations" / "w6" / "data" / self.tool_name / self.run_id
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    def validate_input(self, params: Dict[str, Any], schema_path: Path) -> tuple[bool, Optional[str]]:
        """
        Validate input parameters against JSON schema

        Returns:
            (valid, error_message)
        """
        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)

            # Simple validation - check required fields
            required = schema.get('required', [])
            for field in required:
                if field not in params:
                    return False, f"Missing required field: {field}"

            return True, None
        except Exception as e:
            return False, f"Schema validation error: {str(e)}"

    def create_manifest(self, params: Dict[str, Any], results: Dict[str, Any],
                       status: str = "success", error: Optional[str] = None) -> Path:
        """
        Create manifest.json for this run

        Args:
            params: Input parameters
            results: Output results
            status: "success" or "error"
            error: Error message if status is "error"

        Returns:
            Path to manifest file
        """
        manifest = {
            "tool": self.tool_name,
            "version": self.version,
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "status": status,
            "input": params,
            "output": results if status == "success" else {},
            "error": error,
            "output_directory": str(self.output_dir),
            "files": list(self.output_dir.glob("*")) if self.output_dir.exists() else []
        }

        manifest_path = self.output_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        if self.logger:
            self.logger.info(f"[{self.tool_name}] Manifest created: {manifest_path}")

        return manifest_path

    def publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish event to event bus"""
        if self.event_bus:
            event_data = {
                "tool": self.tool_name,
                "run_id": self.run_id,
                **data
            }
            self.event_bus.publish(f"tool.{event_type}", event_data, floor="Smith")

    def log_to_database(self, status: str, duration: float, params: Dict[str, Any]):
        """Log run to database"""
        if self.db:
            try:
                # This assumes a jobs table exists - will be created by schema
                # For now, just pass if table doesn't exist
                pass
            except:
                pass

    def save_result_file(self, filename: str, content: str):
        """Save a result file to the output directory"""
        file_path = self.output_dir / filename
        with open(file_path, 'w') as f:
            f.write(content)

        if self.logger:
            self.logger.info(f"[{self.tool_name}] Result file saved: {file_path}")

        return file_path

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main run method - override in subclasses

        Args:
            params: Input parameters (already validated)

        Returns:
            Results dictionary
        """
        raise NotImplementedError("Subclasses must implement run()")


__all__ = [
    'BaseRunner',
]
