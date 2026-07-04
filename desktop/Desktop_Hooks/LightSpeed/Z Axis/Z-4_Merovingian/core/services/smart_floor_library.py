"""
LightSpeed Smart Floor Library V1.0.0
Unified function registry with cross-floor amalgamation

Purpose:
The SmartFloor provides amalgamation - all functions registered across all Z-floors
are available everywhere. No manual imports, no floor restrictions. If a function
exists anywhere in the platform, you can call it from anywhere.

Features:
- Automatic function registration by floor
- Cross-floor function discovery
- Execution with performance tracking
- History logging
- Statistics and metrics
- Integration with physics engine (Raphael)

Architecture:
```
SmartFloorLibrary
    ├─> Function Registry (all floors)
    ├─> Execution Engine (runs functions)
    ├─> History Tracker (logs all executions)
    └─> Stats Collector (performance metrics)
```

Usage:
```python
# Register a function
smart_floor.register_function(
    'calculate_schwarzschild_radius',
    category='gravitation',
    floor='Z0_TheConstruct',
    default_vars={'mass': 1.989e30}
)

# Execute from anywhere
result = smart_floor.execute_function(
    'calculate_schwarzschild_radius',
    {'mass': 2.0e30}
)

# Get stats
stats = smart_floor.get_function_stats('calculate_schwarzschild_radius')
```

Author: LightSpeed Team
Date: January 5, 2026
Extracted from: immersive_bento_ui.py
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import time
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class FunctionMetadata:
    """Metadata for registered function"""
    name: str
    category: str
    floor: str
    default_vars: Dict[str, Any]
    execution_count: int = 0
    total_time: float = 0.0
    last_executed: Optional[float] = None
    description: str = ""


@dataclass
class ExecutionRecord:
    """Record of function execution"""
    function: str
    variables: Dict[str, Any]
    result: Any
    execution_time: float
    timestamp: float
    floor: str = ""


# ═══════════════════════════════════════════════════════════════════════════
# SMART FLOOR LIBRARY
# ═══════════════════════════════════════════════════════════════════════════

class SmartFloorLibrary:
    """
    Unified function library across all Z-floors
    Provides amalgamation - all functions callable from anywhere

    The SmartFloor is a key component of the vision: functions are not isolated
    to their floors. Once registered, they're available platform-wide.

    This enables:
    - Cross-floor function calls
    - Automatic resource discovery
    - Unified execution environment
    - Complete amalgamation
    """

    def __init__(self):
        """Initialize Smart Floor Library"""
        self.functions: Dict[str, FunctionMetadata] = {}
        self.execution_history: List[ExecutionRecord] = []
        self.max_history = 10000  # Keep last 10k executions

        # Physics engine integration
        self.physics_engine = None
        self._initialize_physics_engine()

        # AUTO-REGISTER Z0 physics calculators
        self._auto_register_z0_physics()

        print("[SmartFloor] Initialized")


    def _initialize_physics_engine(self):
        """Initialize Raphael physics engine"""
        try:
            from core.physics.raphael_renderer_pure import RaphaelEquationComponents
            self.physics_engine = RaphaelEquationComponents()
            print("[SmartFloor] ✓ Raphael physics engine loaded")
        except ImportError as e:
            print(f"[SmartFloor] ⚠ Physics engine not available: {e}")
            self.physics_engine = None


    # ═══════════════════════════════════════════════════════════════════════
    # FUNCTION REGISTRATION
    # ═══════════════════════════════════════════════════════════════════════

    def register_function(
        self,
        func_name: str,
        category: str,
        floor: str,
        default_vars: Dict[str, Any],
        description: str = ""
    ):
        """
        Register a function in the Smart Floor library

        Args:
            func_name: Unique function identifier
            category: Function category (gravitation, quantum, etc.)
            floor: Z-floor where function originates
            default_vars: Default variable values
            description: Human-readable description
        """
        self.functions[func_name] = FunctionMetadata(
            name=func_name,
            category=category,
            floor=floor,
            default_vars=default_vars,
            description=description
        )

        print(f"[SmartFloor] Registered: {func_name} ({category}) on {floor}")


    def register_batch(self, functions: List[Dict[str, Any]]):
        """Register multiple functions at once"""
        for func_data in functions:
            self.register_function(
                func_data['name'],
                func_data['category'],
                func_data['floor'],
                func_data['default_vars'],
                func_data.get('description', '')
            )

        print(f"[SmartFloor] Batch registered: {len(functions)} functions")


    # ═══════════════════════════════════════════════════════════════════════
    # FUNCTION EXECUTION
    # ═══════════════════════════════════════════════════════════════════════

    def execute_function(self, func_name: str, variables: Dict[str, Any]) -> Any:
        """
        Execute a registered function

        This is the core of amalgamation - any function can be executed
        from anywhere in the platform.

        Args:
            func_name: Function to execute
            variables: Variable values for execution

        Returns:
            Function result
        """
        start_time = time.time()
        result = None

        # Get function metadata
        if func_name not in self.functions:
            print(f"[SmartFloor] ⚠ Function not registered: {func_name}")
            return None

        func_meta = self.functions[func_name]

        # Execute function based on name (physics functions)
        if self.physics_engine:
            result = self._execute_physics_function(func_name, variables)
        else:
            print(f"[SmartFloor] ⚠ Physics engine not available for {func_name}")

        # Record execution
        exec_time = time.time() - start_time

        # Update metadata
        func_meta.execution_count += 1
        func_meta.total_time += exec_time
        func_meta.last_executed = time.time()

        # Add to history
        self.execution_history.append(ExecutionRecord(
            function=func_name,
            variables=variables.copy(),
            result=result,
            execution_time=exec_time,
            timestamp=time.time(),
            floor=func_meta.floor
        ))

        # Trim history if too long
        if len(self.execution_history) > self.max_history:
            self.execution_history = self.execution_history[-self.max_history:]

        print(f"[SmartFloor] Executed: {func_name} ({exec_time*1000:.2f}ms)")

        return result


    def _execute_physics_function(self, func_name: str, variables: Dict[str, Any]) -> Any:
        """Execute physics-specific functions via Raphael engine"""
        if not self.physics_engine:
            return None

        # Map function names to Raphael methods
        physics_functions = {
            'calculate_schwarzschild_radius': lambda v: self.physics_engine.schwarzschild_radius(v['mass']),
            'calculate_hawking_temperature': lambda v: self.physics_engine.black_hole_temperature(v['mass']),
            'calculate_time_dilation': lambda v: self.physics_engine.gravitational_time_dilation(v['mass'], v['distance']),
            'calculate_einstein_ring': lambda v: self.physics_engine.einstein_ring_radius(v['lens_mass'], v['source_dist'], v['lens_dist']),
            'calculate_quantum_energy': lambda v: self.physics_engine.quantum_energy_level(int(v['n']), v['mass'], v['length']),
            'calculate_tunneling': lambda v: self.physics_engine.quantum_tunneling_probability(v['width'], v['height'], v['energy'], v['mass']),
            'calculate_dark_matter_density': lambda v: self.physics_engine.dark_matter_density_profile(v['radius'], v['core_radius'], v['central_density']),
            'calculate_hubble_rate': lambda v: self.physics_engine.universe_expansion_rate(v['time']),
            'calculate_fresnel_reflection': lambda v: self.physics_engine.fresnel_reflection_coefficient(v['angle'], v['n1'], v['n2']),
            'calculate_wave_interference': lambda v: self.physics_engine.wave_interference(v['amps'], v['phases']),
            'calculate_bh_entropy': lambda v: self.physics_engine.black_hole_entropy(v['mass']),
            'calculate_accretion_temp': lambda v: self.physics_engine.accretion_disk_temperature(v['mass'], v['radius'], v['accretion_rate']),
        }

        if func_name in physics_functions:
            try:
                return physics_functions[func_name](variables)
            except Exception as e:
                print(f"[SmartFloor] ✗ Error executing {func_name}: {e}")
                return None

        return None


    # ═══════════════════════════════════════════════════════════════════════
    # DISCOVERY & QUERY
    # ═══════════════════════════════════════════════════════════════════════

    def discover_functions(
        self,
        category: Optional[str] = None,
        floor: Optional[str] = None
    ) -> List[FunctionMetadata]:
        """
        Discover available functions

        Args:
            category: Filter by category (optional)
            floor: Filter by floor (optional)

        Returns:
            List of matching functions
        """
        results = []

        for func_meta in self.functions.values():
            if category and func_meta.category != category:
                continue
            if floor and func_meta.floor != floor:
                continue

            results.append(func_meta)

        return results


    def get_categories(self) -> List[str]:
        """Get all unique categories"""
        categories = set(f.category for f in self.functions.values())
        return sorted(list(categories))


    def get_floors_with_functions(self) -> Dict[str, int]:
        """Get count of functions per floor"""
        floor_counts = {}
        for func_meta in self.functions.values():
            floor_counts[func_meta.floor] = floor_counts.get(func_meta.floor, 0) + 1
        return floor_counts


    # ═══════════════════════════════════════════════════════════════════════
    # STATISTICS & METRICS
    # ═══════════════════════════════════════════════════════════════════════

    def get_function_stats(self, func_name: str) -> Dict[str, Any]:
        """Get statistics for a function"""
        if func_name not in self.functions:
            return {}

        func_meta = self.functions[func_name]

        avg_time = func_meta.total_time / func_meta.execution_count if func_meta.execution_count > 0 else 0

        return {
            'name': func_meta.name,
            'category': func_meta.category,
            'floor': func_meta.floor,
            'execution_count': func_meta.execution_count,
            'total_time': func_meta.total_time,
            'average_time': avg_time,
            'last_executed': func_meta.last_executed,
            'description': func_meta.description
        }


    def get_global_stats(self) -> Dict[str, Any]:
        """Get global library statistics"""
        total_functions = len(self.functions)
        total_executions = sum(f.execution_count for f in self.functions.values())
        total_time = sum(f.total_time for f in self.functions.values())

        return {
            'total_functions': total_functions,
            'total_executions': total_executions,
            'total_time': total_time,
            'history_size': len(self.execution_history),
            'categories': len(self.get_categories()),
            'floors_with_functions': len(self.get_floors_with_functions())
        }


    def get_execution_history(self, limit: int = 100) -> List[ExecutionRecord]:
        """Get recent execution history"""
        return self.execution_history[-limit:]


    def get_most_used_functions(self, limit: int = 10) -> List[FunctionMetadata]:
        """Get most frequently executed functions"""
        sorted_funcs = sorted(
            self.functions.values(),
            key=lambda f: f.execution_count,
            reverse=True
        )
        return sorted_funcs[:limit]


    # ═══════════════════════════════════════════════════════════════════════
    # EXPORT & PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════

    def export_library(self) -> Dict[str, Any]:
        """Export complete library state"""
        return {
            'functions': {
                name: {
                    'category': f.category,
                    'floor': f.floor,
                    'default_vars': f.default_vars,
                    'execution_count': f.execution_count,
                    'total_time': f.total_time,
                    'description': f.description
                }
                for name, f in self.functions.items()
            },
            'execution_history': [
                {
                    'function': r.function,
                    'variables': r.variables,
                    'result': str(r.result),  # Convert to string for JSON
                    'execution_time': r.execution_time,
                    'timestamp': r.timestamp,
                    'floor': r.floor
                }
                for r in self.execution_history[-1000:]  # Last 1000 executions
            ],
            'stats': self.get_global_stats()
        }


    # ═══════════════════════════════════════════════════════════════════════
    # AUTO-REGISTRATION
    # ═══════════════════════════════════════════════════════════════════════

    def _auto_register_z0_physics(self):
        """
        Auto-register all physics calculators from Z0_TheConstruct
        Eliminates need for manual registration
        """
        try:
            import sys
            from pathlib import Path

            # Find Z0_TheConstruct directory (robust against folder migrations)
            try:
                from core.config.paths import CONSTRUCT_ROOT as _CONSTRUCT_ROOT  # type: ignore
                z_axis_path = Path(_CONSTRUCT_ROOT)
            except Exception:
                z_axis_path = Path(__file__).resolve()
                for cand in (z_axis_path, *z_axis_path.parents):
                    if (cand / "N.py").exists() and (cand / "Z Axis").exists():
                        z_axis_path = cand / "Z Axis" / "Z0_TheConstruct"
                        break

            if not z_axis_path.exists():
                print(f"[SmartFloor] ⚠ Z0_TheConstruct not found at {z_axis_path}")
                return

            sys.path.insert(0, str(z_axis_path))

            # Import physics calculators module
            import physics_calculators

            # Register all calculators from the registry
            for calc_name, calc_func in physics_calculators.PHYSICS_CALCULATORS.items():
                # Extract default values from function (use first result as template)
                default_vars = {}

                try:
                    # Get function signature
                    import inspect
                    sig = inspect.signature(calc_func)

                    for param_name in sig.parameters:
                        # Provide sensible defaults based on parameter name
                        if param_name == 'mass':
                            default_vars[param_name] = 1.989e30  # Solar mass
                        elif param_name in ['distance', 'radius']:
                            default_vars[param_name] = 1e7
                        elif param_name == 'n':
                            default_vars[param_name] = 1
                        elif param_name in ['length', 'width']:
                            default_vars[param_name] = 1e-9
                        elif param_name in ['velocity', 'recession_velocity']:
                            default_vars[param_name] = 1e6
                        elif param_name.endswith('_rate'):
                            default_vars[param_name] = 2.197e-18
                        else:
                            default_vars[param_name] = 1.0

                except Exception as e:
                    print(f"[SmartFloor] ⚠ Could not extract params for {calc_name}: {e}")

                # Register function
                self.register_function(
                    func_name=calc_name,
                    category='physics',
                    floor='Z0_TheConstruct',
                    default_vars=default_vars,
                    description=calc_func.__doc__ or f"{calc_name.replace('_', ' ').title()} calculator"
                )

            print(f"[SmartFloor] ✓ Auto-registered {len(physics_calculators.PHYSICS_CALCULATORS)} physics calculators from Z0")

        except ImportError as e:
            print(f"[SmartFloor] ⚠ Could not import physics_calculators: {e}")
        except Exception as e:
            print(f"[SmartFloor] ⚠ Auto-registration failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    'SmartFloorLibrary',
    'FunctionMetadata',
    'ExecutionRecord'
]
