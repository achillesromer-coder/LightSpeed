"""
Smart Floor Expansion System - Self-expanding floor capabilities

Allows each Z-floor to autonomously expand its tools, programming, and capabilities
using floor AI systems. Each floor can:

- Generate new tools based on accumulated data
- Create test suites automatically
- Build visualizations from data
- Export capabilities to other floors
- Learn from usage patterns
- Commit improvements to the project

This creates a self-improving system where floors grow smarter with use.

Author: LightSpeed Team
Date: December 20, 2025
Version: 0.9.5
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


# ============================================================================
# Capability Types
# ============================================================================

class CapabilityType(Enum):
    """Types of capabilities floors can develop"""
    TOOL = "tool"                   # New processing tool
    ANALYZER = "analyzer"           # Data analysis capability
    GENERATOR = "generator"         # Data/code generator
    VISUALIZER = "visualizer"       # Visualization capability
    EXPORTER = "exporter"           # Export format handler
    TESTER = "tester"              # Test execution capability
    VALIDATOR = "validator"         # Data validation
    TRANSFORMER = "transformer"     # Data transformation


@dataclass
class FloorCapability:
    """A capability developed by a floor"""
    id: str
    name: str
    capability_type: CapabilityType
    floor_id: str                  # Which floor created it
    description: str
    code: str                      # Python code implementing capability
    inputs: List[Dict[str, str]]   # Expected inputs
    outputs: List[Dict[str, str]]  # Generated outputs
    usage_count: int
    success_rate: float
    created_at: str
    last_used: Optional[str]
    metadata: Dict[str, Any]


# ============================================================================
# Smart Floor Expansion Engine
# ============================================================================

class SmartFloorExpansionEngine:
    """
    Engine for autonomous floor capability expansion

    Each floor uses its AI to:
    1. Analyze accumulated data patterns
    2. Identify capability gaps
    3. Generate new tools/functions
    4. Test and validate new capabilities
    5. Share successful capabilities system-wide
    """

    def __init__(self, lightspeed_root: Path):
        self.lightspeed_root = lightspeed_root
        self.capabilities: Dict[str, FloorCapability] = {}
        # Floor-native config location (Merovingian owns core.* services).
        # Legacy fallback: `<root>/data/floor_capabilities.json` (deprecated).
        self.capabilities_path = (
            Path(lightspeed_root)
            / "Z Axis"
            / "Z-4_Merovingian"
            / "core"
            / "config"
            / "floor_capabilities.json"
        )
        self.legacy_capabilities_path = Path(lightspeed_root) / "data" / "floor_capabilities.json"
        self.floor_ais: Dict[str, Any] = {}  # Floor AI instances

        # Load existing capabilities
        self._load_capabilities()

    def _load_capabilities(self):
        """Load saved capabilities"""
        source_path = self.capabilities_path
        if not source_path.exists() and self.legacy_capabilities_path.exists():
            source_path = self.legacy_capabilities_path

        if source_path.exists():
            try:
                with open(source_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for cap_id, cap_data in data.items():
                        cap_data['capability_type'] = CapabilityType(cap_data['capability_type'])
                        self.capabilities[cap_id] = FloorCapability(**cap_data)
                print(f"[SmartExpansion] Loaded {len(self.capabilities)} capabilities")
            except Exception as e:
                print(f"[SmartExpansion] Error loading capabilities: {e}")

    def _save_capabilities(self):
        """Save capabilities to disk"""
        os.makedirs(os.path.dirname(self.capabilities_path), exist_ok=True)

        serializable = {}
        for cap_id, cap in self.capabilities.items():
            cap_dict = asdict(cap)
            cap_dict['capability_type'] = cap.capability_type.value
            serializable[cap_id] = cap_dict

        with open(self.capabilities_path, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, indent=2)

    def register_floor_ai(self, floor_id: str, ai_instance: Any):
        """Register a floor's AI system"""
        self.floor_ais[floor_id] = ai_instance
        print(f"[SmartExpansion] Registered AI for {floor_id}")

    def create_capability(
        self,
        floor_id: str,
        name: str,
        capability_type: CapabilityType,
        description: str,
        code: str,
        inputs: List[Dict[str, str]],
        outputs: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> FloorCapability:
        """
        Create a new floor capability

        Args:
            floor_id: Floor creating the capability
            name: Capability name
            capability_type: Type of capability
            description: What it does
            code: Python code implementing the capability
            inputs: Expected inputs (name, type, description)
            outputs: Generated outputs (name, type, description)
            metadata: Additional metadata

        Returns:
            Created capability
        """
        cap_id = f"{floor_id}_{capability_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        capability = FloorCapability(
            id=cap_id,
            name=name,
            capability_type=capability_type,
            floor_id=floor_id,
            description=description,
            code=code,
            inputs=inputs,
            outputs=outputs,
            usage_count=0,
            success_rate=0.0,
            created_at=datetime.now().isoformat(),
            last_used=None,
            metadata=metadata or {}
        )

        self.capabilities[cap_id] = capability
        self._save_capabilities()

        print(f"[SmartExpansion] {floor_id} created capability: {name}")
        return capability

    def execute_capability(
        self,
        capability_id: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a capability

        Args:
            capability_id: ID of capability to execute
            input_data: Input data matching capability's inputs

        Returns:
            Execution result
        """
        capability = self.capabilities.get(capability_id)
        if not capability:
            return {'success': False, 'error': 'Capability not found'}

        try:
            # Create execution environment
            exec_globals = {
                'input_data': input_data,
                'result': {}
            }

            # Execute capability code
            exec(capability.code, exec_globals)

            # Update statistics
            capability.usage_count += 1
            capability.last_used = datetime.now().isoformat()

            # Calculate success rate
            if exec_globals.get('result', {}).get('success', False):
                capability.success_rate = (
                    (capability.success_rate * (capability.usage_count - 1) + 1.0) /
                    capability.usage_count
                )
            else:
                capability.success_rate = (
                    (capability.success_rate * (capability.usage_count - 1)) /
                    capability.usage_count
                )

            self._save_capabilities()

            print(f"[SmartExpansion] Executed: {capability.name}")
            return exec_globals.get('result', {'success': True})

        except Exception as e:
            print(f"[SmartExpansion] Execution error: {e}")
            return {'success': False, 'error': str(e)}

    def generate_tool_from_pattern(
        self,
        floor_id: str,
        data_pattern: Dict[str, Any],
        ai_instance: Optional[Any] = None
    ) -> Optional[FloorCapability]:
        """
        Use floor AI to generate a new tool based on data patterns

        Args:
            floor_id: Floor generating the tool
            data_pattern: Pattern observed in accumulated data
            ai_instance: Optional AI instance (uses registered if not provided)

        Returns:
            Generated capability or None
        """
        # Use registered AI or provided one
        ai = ai_instance or self.floor_ais.get(floor_id)
        if not ai:
            print(f"[SmartExpansion] No AI available for {floor_id}")
            return None

        # Generate capability based on pattern
        # This is a simplified version - real implementation would use LLM
        pattern_type = data_pattern.get('type', 'unknown')

        if pattern_type == 'repeated_transformation':
            # Generate a transformer
            name = f"Auto-generated Transformer: {data_pattern.get('name', 'Unknown')}"
            code = self._generate_transformer_code(data_pattern)
            inputs = [{'name': 'data', 'type': 'any', 'description': 'Input data'}]
            outputs = [{'name': 'transformed', 'type': 'any', 'description': 'Transformed data'}]

            return self.create_capability(
                floor_id=floor_id,
                name=name,
                capability_type=CapabilityType.TRANSFORMER,
                description=f"Auto-generated transformer for {pattern_type}",
                code=code,
                inputs=inputs,
                outputs=outputs,
                metadata={'auto_generated': True, 'pattern': data_pattern}
            )

        elif pattern_type == 'validation_need':
            # Generate a validator
            name = f"Auto-generated Validator: {data_pattern.get('name', 'Unknown')}"
            code = self._generate_validator_code(data_pattern)
            inputs = [{'name': 'data', 'type': 'any', 'description': 'Data to validate'}]
            outputs = [{'name': 'valid', 'type': 'bool', 'description': 'Validation result'},
                      {'name': 'errors', 'type': 'list', 'description': 'Validation errors'}]

            return self.create_capability(
                floor_id=floor_id,
                name=name,
                capability_type=CapabilityType.VALIDATOR,
                description=f"Auto-generated validator for {pattern_type}",
                code=code,
                inputs=inputs,
                outputs=outputs,
                metadata={'auto_generated': True, 'pattern': data_pattern}
            )

        return None

    def _generate_transformer_code(self, pattern: Dict[str, Any]) -> str:
        """Generate code for a transformer capability"""
        # Simplified code generation - real version would use LLM
        transformation = pattern.get('transformation', 'identity')

        code_template = f"""
# Auto-generated transformer for {pattern.get('name', 'Unknown')}
def transform(data):
    # Apply transformation: {transformation}
    try:
        # Add transformation logic here
        result['success'] = True
        result['transformed'] = data  # Placeholder
    except Exception as e:
        result['success'] = False
        result['error'] = str(e)

transform(input_data.get('data'))
"""
        return code_template

    def _generate_validator_code(self, pattern: Dict[str, Any]) -> str:
        """Generate code for a validator capability"""
        # Simplified code generation
        rules = pattern.get('rules', [])

        code_template = f"""
# Auto-generated validator for {pattern.get('name', 'Unknown')}
def validate(data):
    errors = []
    # Validation rules: {rules}

    # Add validation logic here

    result['success'] = len(errors) == 0
    result['valid'] = len(errors) == 0
    result['errors'] = errors

validate(input_data.get('data'))
"""
        return code_template

    def share_capability(self, capability_id: str, target_floors: List[str]):
        """Share a capability with other floors"""
        capability = self.capabilities.get(capability_id)
        if not capability:
            print(f"[SmartExpansion] Capability not found: {capability_id}")
            return

        for floor_id in target_floors:
            # Create shared capability instance
            shared_id = f"{floor_id}_shared_{capability_id}"
            shared_cap = FloorCapability(
                id=shared_id,
                name=f"[Shared] {capability.name}",
                capability_type=capability.capability_type,
                floor_id=floor_id,
                description=f"Shared from {capability.floor_id}: {capability.description}",
                code=capability.code,
                inputs=capability.inputs,
                outputs=capability.outputs,
                usage_count=0,
                success_rate=0.0,
                created_at=datetime.now().isoformat(),
                last_used=None,
                metadata={'shared_from': capability.floor_id, 'original_id': capability_id}
            )

            self.capabilities[shared_id] = shared_cap
            print(f"[SmartExpansion] Shared {capability.name} with {floor_id}")

        self._save_capabilities()

    def get_floor_capabilities(self, floor_id: str) -> List[FloorCapability]:
        """Get all capabilities for a floor (owned + shared)"""
        return [
            cap for cap in self.capabilities.values()
            if cap.floor_id == floor_id
        ]

    def get_capability_report(self) -> Dict[str, Any]:
        """Generate report on system-wide capabilities"""
        report = {
            'total_capabilities': len(self.capabilities),
            'by_floor': {},
            'by_type': {},
            'top_performers': [],
            'auto_generated': 0
        }

        # Count by floor
        for cap in self.capabilities.values():
            floor = cap.floor_id
            if floor not in report['by_floor']:
                report['by_floor'][floor] = 0
            report['by_floor'][floor] += 1

            # Count by type
            cap_type = cap.capability_type.value
            if cap_type not in report['by_type']:
                report['by_type'][cap_type] = 0
            report['by_type'][cap_type] += 1

            # Count auto-generated
            if cap.metadata.get('auto_generated'):
                report['auto_generated'] += 1

        # Top performers
        sorted_caps = sorted(
            self.capabilities.values(),
            key=lambda c: (c.success_rate, c.usage_count),
            reverse=True
        )
        report['top_performers'] = [
            {
                'name': cap.name,
                'floor': cap.floor_id,
                'success_rate': cap.success_rate,
                'usage_count': cap.usage_count
            }
            for cap in sorted_caps[:10]
        ]

        return report


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    from pathlib import Path

    lightspeed_root = Path(__file__).parent.parent.parent.resolve()
    engine = SmartFloorExpansionEngine(lightspeed_root)

    print("\n" + "=" * 60)
    print("SMART FLOOR EXPANSION ENGINE TEST")
    print("=" * 60)

    # Test: Create a capability
    print("\n[TEST] Creating capability...")
    cap = engine.create_capability(
        floor_id="Z+2_Neo",
        name="Data Quality Analyzer",
        capability_type=CapabilityType.ANALYZER,
        description="Analyzes dataset quality and completeness",
        code="""
# Analyze data quality
data = input_data.get('data', {})
result['success'] = True
result['quality_score'] = 0.95
result['completeness'] = 0.87
""",
        inputs=[{'name': 'data', 'type': 'dict', 'description': 'Dataset to analyze'}],
        outputs=[{'name': 'quality_score', 'type': 'float', 'description': 'Quality score'},
                {'name': 'completeness', 'type': 'float', 'description': 'Completeness score'}]
    )

    # Test: Execute capability
    print("\n[TEST] Executing capability...")
    result = engine.execute_capability(
        cap.id,
        {'data': {'records': 100, 'fields': 5}}
    )
    print(f"Result: {result}")

    # Test: Generate capability from pattern
    print("\n[TEST] Generating capability from pattern...")
    pattern = {
        'type': 'validation_need',
        'name': 'Email Validation',
        'rules': ['must_contain_@', 'must_have_domain']
    }
    auto_cap = engine.generate_tool_from_pattern("Z-4_Merovingian", pattern)
    if auto_cap:
        print(f"Generated: {auto_cap.name}")

    # Test: Capability report
    print("\n[TEST] Capability Report:")
    report = engine.get_capability_report()
    print(json.dumps(report, indent=2))

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
