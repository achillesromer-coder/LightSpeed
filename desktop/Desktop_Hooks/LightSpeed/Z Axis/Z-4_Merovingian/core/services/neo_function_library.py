import json
import math
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Callable
from dataclasses import dataclass, field, asdict
from collections import defaultdict


@dataclass
class FunctionRecord:
    name: str
    floor: str
    category: str
    inputs: Dict[str, type]
    outputs: Dict[str, type]
    execution_count: int = 0
    total_execution_time: float = 0.0
    average_result: Optional[float] = None
    result_history: List[Any] = field(default_factory=list)
    correlations: List[str] = field(default_factory=list)


@dataclass
class ExecutionLog:
    function_name: str
    inputs: Dict[str, Any]
    output: Any
    execution_time: float
    timestamp: float
    floor: str
    success: bool


class NeoFunctionLibrary:
    def __init__(self):
        self.functions: Dict[str, FunctionRecord] = {}
        self.execution_logs: List[ExecutionLog] = []
        self.correlation_matrix: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.floor_interactions: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        self._initialize_physics_library()
        self._initialize_floor_functions()

    def _initialize_physics_library(self):
        from core.physics.raphael_renderer_pure import RaphaelEquationComponents
        self.physics = RaphaelEquationComponents()

        physics_functions = [
            ('schwarzschild_radius', 'Z0', 'gravitation', {'mass': float}, {'radius': float}),
            ('hawking_temperature', 'Z0', 'thermodynamics', {'mass': float}, {'temperature': float}),
            ('time_dilation', 'Z0', 'relativity', {'mass': float, 'distance': float}, {'factor': float}),
            ('gravitational_redshift', 'Z0', 'relativity', {'mass': float, 'distance': float, 'wavelength': float}, {'wavelength_observed': float}),
            ('einstein_deflection', 'Z0', 'lensing', {'mass': float, 'impact_parameter': float}, {'angle': float}),
            ('einstein_ring', 'Z0', 'lensing', {'lens_mass': float, 'source_distance': float, 'lens_distance': float}, {'radius': float}),
            ('quantum_energy_level', 'Z0', 'quantum', {'n': int, 'mass': float, 'box_length': float}, {'energy': float}),
            ('wavefunction_box', 'Z0', 'quantum', {'x': float, 'n': int, 'box_length': float}, {'amplitude': float}),
            ('heisenberg_uncertainty', 'Z0', 'quantum', {'delta_x': float}, {'delta_p': float}),
            ('tunneling_probability', 'Z0', 'quantum', {'barrier_width': float, 'barrier_height': float, 'particle_energy': float, 'particle_mass': float}, {'probability': float}),
            ('black_hole_entropy', 'Z0', 'thermodynamics', {'mass': float}, {'entropy': float}),
            ('evaporation_time', 'Z0', 'thermodynamics', {'mass': float}, {'time': float}),
            ('accretion_temperature', 'Z0', 'astrophysics', {'mass': float, 'radius': float, 'accretion_rate': float}, {'temperature': float}),
            ('dark_matter_density', 'Z0', 'cosmology', {'radius': float, 'core_radius': float, 'central_density': float}, {'density': float}),
            ('dark_energy_density', 'Z0', 'cosmology', {'cosmological_constant': float}, {'density': float}),
            ('hubble_expansion', 'Z0', 'cosmology', {'time': float}, {'rate': float}),
            ('wave_amplitude', 'Z0', 'waves', {'distance': float, 'source_strength': float}, {'amplitude': float}),
            ('wave_phase', 'Z0', 'waves', {'distance': float, 'wavelength': float, 'time': float}, {'phase': float}),
            ('wave_interference', 'Z0', 'waves', {'amplitudes': list, 'phases': list}, {'total_amplitude': float}),
            ('fresnel_reflection', 'Z0', 'optics', {'theta_i': float, 'n1': float, 'n2': float}, {'coefficient': float}),
            ('brewster_angle', 'Z0', 'optics', {'n1': float, 'n2': float}, {'angle': float}),
            ('critical_angle', 'Z0', 'optics', {'n1': float, 'n2': float}, {'angle': float}),
        ]

        for func_name, floor, category, inputs, outputs in physics_functions:
            self.register_function(func_name, floor, category, inputs, outputs)

    def _initialize_floor_functions(self):
        floor_functions = {
            'Z+2_Neo': [
                ('ai_inference', 'Z+2', 'ai', {'model': str, 'prompt': str}, {'response': str}),
                ('model_training', 'Z+2', 'ai', {'data': list, 'epochs': int}, {'accuracy': float}),
                ('neural_forward', 'Z+2', 'ai', {'inputs': list, 'weights': list}, {'outputs': list}),
            ],
            'Z-1_Morpheus': [
                ('knowledge_query', 'Z-1', 'knowledge', {'query': str}, {'results': list}),
                ('encyclopedia_lookup', 'Z-1', 'knowledge', {'term': str}, {'definition': str}),
                ('semantic_search', 'Z-1', 'knowledge', {'text': str}, {'matches': list}),
            ],
            'Z+1_Architect': [
                ('workflow_design', 'Z+1', 'design', {'nodes': list, 'edges': list}, {'graph': dict}),
                ('optimization', 'Z+1', 'design', {'objective': str, 'constraints': list}, {'solution': dict}),
                ('pattern_recognition', 'Z+1', 'design', {'data': list}, {'patterns': list}),
            ],
            'Z0_TheConstruct': [
                ('physics_simulation', 'Z0', 'physics', {'system': str, 'parameters': dict}, {'results': dict}),
                ('spacetime_metric', 'Z0', 'physics', {'x': float, 'y': float, 'z': float, 't': float}, {'metric': list}),
            ],
            'Z-2_Oracle': [
                ('image_analysis', 'Z-2', 'vision', {'image_path': str}, {'features': dict}),
                ('object_detection', 'Z-2', 'vision', {'image': Any}, {'objects': list}),
                ('visual_query', 'Z-2', 'vision', {'query': str}, {'matches': list}),
            ],
            'Z-3_Smith': [
                ('task_scheduling', 'Z-3', 'tasks', {'tasks': list, 'resources': dict}, {'schedule': list}),
                ('background_process', 'Z-3', 'tasks', {'process': str, 'priority': int}, {'status': str}),
                ('queue_management', 'Z-3', 'tasks', {'queue': list, 'operation': str}, {'result': Any}),
            ],
            'Z-4_Merovingian': [
                ('user_authentication', 'Z-4', 'security', {'username': str, 'password': str}, {'token': str}),
                ('access_control', 'Z-4', 'security', {'user': str, 'resource': str}, {'granted': bool}),
                ('data_encryption', 'Z-4', 'security', {'data': str, 'key': str}, {'encrypted': str}),
            ],
            'Z+3_Trinity': [
                ('settings_get', 'Z+3', 'config', {'key': str}, {'value': Any}),
                ('settings_set', 'Z+3', 'config', {'key': str, 'value': Any}, {'success': bool}),
                ('config_export', 'Z+3', 'config', {}, {'config': dict}),
            ],
        }

        # Backward-compatible aliases (legacy floor IDs appear in older docs/configs)
        legacy_aliases = {
            'Z+3_Neo': 'Z+2_Neo',
            'Z+2_Morpheus': 'Z-1_Morpheus',
            'Z-1_Oracle': 'Z-2_Oracle',
            'Z-2_Smith': 'Z-3_Smith',
            'Z-3_Merovingian': 'Z-4_Merovingian',
            'Z-4_Trinity': 'Z+3_Trinity',
        }
        for legacy, canonical in legacy_aliases.items():
            if canonical in floor_functions:
                floor_functions.setdefault(legacy, floor_functions[canonical])

        for floor, funcs in floor_functions.items():
            for func_name, floor_id, category, inputs, outputs in funcs:
                self.register_function(func_name, floor_id, category, inputs, outputs)

    def register_function(self, name: str, floor: str, category: str, inputs: Dict[str, type], outputs: Dict[str, type]):
        self.functions[name] = FunctionRecord(
            name=name,
            floor=floor,
            category=category,
            inputs=inputs,
            outputs=outputs
        )

    def execute(self, func_name: str, **kwargs) -> Tuple[bool, Any]:
        if func_name not in self.functions:
            return False, None

        start_time = time.time()
        success = True
        result = None

        try:
            if hasattr(self.physics, func_name):
                method = getattr(self.physics, func_name)
                result = method(**kwargs)
            elif func_name == 'schwarzschild_radius':
                result = self.physics.schwarzschild_radius(kwargs['mass'])
            elif func_name == 'hawking_temperature':
                result = self.physics.black_hole_temperature(kwargs['mass'])
            elif func_name == 'time_dilation':
                result = self.physics.gravitational_time_dilation(kwargs['mass'], kwargs['distance'])
            elif func_name == 'gravitational_redshift':
                result = self.physics.gravitational_redshift(kwargs['mass'], kwargs['distance'], kwargs['wavelength'])
            elif func_name == 'einstein_deflection':
                result = self.physics.einstein_deflection_angle(kwargs['mass'], kwargs['impact_parameter'])
            elif func_name == 'einstein_ring':
                result = self.physics.einstein_ring_radius(kwargs['lens_mass'], kwargs['source_distance'], kwargs['lens_distance'])
            elif func_name == 'quantum_energy_level':
                result = self.physics.quantum_energy_level(kwargs['n'], kwargs['mass'], kwargs['box_length'])
            elif func_name == 'wavefunction_box':
                result = self.physics.wavefunction_particle_in_box(kwargs['x'], kwargs['n'], kwargs['box_length'])
            elif func_name == 'heisenberg_uncertainty':
                result = self.physics.heisenberg_uncertainty(kwargs['delta_x'])
            elif func_name == 'tunneling_probability':
                result = self.physics.quantum_tunneling_probability(kwargs['barrier_width'], kwargs['barrier_height'], kwargs['particle_energy'], kwargs['particle_mass'])
            elif func_name == 'black_hole_entropy':
                result = self.physics.black_hole_entropy(kwargs['mass'])
            elif func_name == 'evaporation_time':
                result = self.physics.black_hole_evaporation_time(kwargs['mass'])
            elif func_name == 'accretion_temperature':
                result = self.physics.accretion_disk_temperature(kwargs['mass'], kwargs['radius'], kwargs['accretion_rate'])
            elif func_name == 'dark_matter_density':
                result = self.physics.dark_matter_density_profile(kwargs['radius'], kwargs['core_radius'], kwargs['central_density'])
            elif func_name == 'dark_energy_density':
                result = self.physics.dark_energy_density(kwargs.get('cosmological_constant', 1.11e-52))
            elif func_name == 'hubble_expansion':
                result = self.physics.universe_expansion_rate(kwargs['time'])
            elif func_name == 'wave_amplitude':
                result = self.physics.wave_amplitude(kwargs['distance'], kwargs['source_strength'])
            elif func_name == 'wave_phase':
                result = self.physics.wave_phase(kwargs['distance'], kwargs['wavelength'], kwargs.get('time', 0.0))
            elif func_name == 'wave_interference':
                result = self.physics.wave_interference(kwargs['amplitudes'], kwargs['phases'])
            elif func_name == 'fresnel_reflection':
                result = self.physics.fresnel_reflection_coefficient(kwargs['theta_i'], kwargs['n1'], kwargs['n2'])
            elif func_name == 'brewster_angle':
                result = self.physics.brewster_angle(kwargs['n1'], kwargs['n2'])
            elif func_name == 'critical_angle':
                result = self.physics.critical_angle(kwargs['n1'], kwargs['n2'])
            else:
                result = f"Function {func_name} not yet implemented"

        except Exception as e:
            success = False
            result = str(e)

        exec_time = time.time() - start_time

        func_record = self.functions[func_name]
        func_record.execution_count += 1
        func_record.total_execution_time += exec_time

        if success and isinstance(result, (int, float)):
            func_record.result_history.append(result)
            if len(func_record.result_history) > 100:
                func_record.result_history.pop(0)
            func_record.average_result = sum(func_record.result_history) / len(func_record.result_history)

        log = ExecutionLog(
            function_name=func_name,
            inputs=kwargs,
            output=result,
            execution_time=exec_time,
            timestamp=time.time(),
            floor=func_record.floor,
            success=success
        )
        self.execution_logs.append(log)

        self._update_correlations(func_name, kwargs, result)
        self._update_floor_interactions(func_record.floor)

        return success, result

    def _update_correlations(self, func_name: str, inputs: Dict[str, Any], result: Any):
        current_func = self.functions[func_name]

        for other_name, other_func in self.functions.items():
            if other_name == func_name:
                continue

            correlation_score = 0.0

            if current_func.category == other_func.category:
                correlation_score += 0.4

            if current_func.floor == other_func.floor:
                correlation_score += 0.3

            input_overlap = set(current_func.inputs.keys()) & set(other_func.inputs.keys())
            if input_overlap:
                correlation_score += 0.3 * len(input_overlap) / max(len(current_func.inputs), len(other_func.inputs))

            if correlation_score > 0.3:
                self.correlation_matrix[func_name][other_name] = correlation_score

                if other_name not in current_func.correlations:
                    current_func.correlations.append(other_name)

    def _update_floor_interactions(self, floor: str):
        recent_logs = self.execution_logs[-10:]
        for log in recent_logs:
            if log.floor != floor:
                self.floor_interactions[floor][log.floor] += 1

    def get_correlations(self, func_name: str) -> List[Tuple[str, float]]:
        if func_name not in self.correlation_matrix:
            return []

        correlations = [
            (other_func, score)
            for other_func, score in self.correlation_matrix[func_name].items()
        ]
        correlations.sort(key=lambda x: x[1], reverse=True)

        return correlations[:10]

    def suggest_next_function(self, func_name: str, result: Any) -> Optional[str]:
        correlations = self.get_correlations(func_name)

        if not correlations:
            return None

        for corr_func, score in correlations:
            if score > 0.5:
                return corr_func

        return correlations[0][0] if correlations else None

    def get_floor_statistics(self, floor: str) -> Dict[str, Any]:
        floor_funcs = [f for f in self.functions.values() if f.floor == floor]

        total_executions = sum(f.execution_count for f in floor_funcs)
        total_time = sum(f.total_execution_time for f in floor_funcs)

        categories = defaultdict(int)
        for f in floor_funcs:
            categories[f.category] += f.execution_count

        interactions = self.floor_interactions.get(floor, {})

        return {
            'floor': floor,
            'function_count': len(floor_funcs),
            'total_executions': total_executions,
            'total_time': total_time,
            'average_time': total_time / max(total_executions, 1),
            'categories': dict(categories),
            'interactions': dict(interactions)
        }

    def export_library(self, path: Optional[Path] = None) -> Dict[str, Any]:
        export_data = {
            'functions': {
                name: {
                    'name': func.name,
                    'floor': func.floor,
                    'category': func.category,
                    'inputs': {k: v.__name__ for k, v in func.inputs.items()},
                    'outputs': {k: v.__name__ for k, v in func.outputs.items()},
                    'execution_count': func.execution_count,
                    'total_execution_time': func.total_execution_time,
                    'average_result': func.average_result,
                    'correlations': func.correlations
                }
                for name, func in self.functions.items()
            },
            'correlation_matrix': {
                func: dict(corrs)
                for func, corrs in self.correlation_matrix.items()
            },
            'floor_interactions': {
                floor: dict(interactions)
                for floor, interactions in self.floor_interactions.items()
            },
            'recent_logs': [
                {
                    'function': log.function_name,
                    'inputs': log.inputs,
                    'output': str(log.output)[:100],
                    'time': log.execution_time,
                    'floor': log.floor,
                    'success': log.success
                }
                for log in self.execution_logs[-100:]
            ]
        }

        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(export_data, f, indent=2)

        return export_data

    def import_library(self, path: Path):
        if not path.exists():
            return

        with open(path, 'r') as f:
            import_data = json.load(f)

        for func_name, func_data in import_data.get('functions', {}).items():
            if func_name in self.functions:
                func = self.functions[func_name]
                func.execution_count = func_data.get('execution_count', 0)
                func.total_execution_time = func_data.get('total_execution_time', 0.0)
                func.average_result = func_data.get('average_result')
                func.correlations = func_data.get('correlations', [])

        for func, corrs in import_data.get('correlation_matrix', {}).items():
            self.correlation_matrix[func] = defaultdict(float, corrs)

        for floor, interactions in import_data.get('floor_interactions', {}).items():
            self.floor_interactions[floor] = defaultdict(int, interactions)


_global_library: Optional[NeoFunctionLibrary] = None


def get_function_library() -> NeoFunctionLibrary:
    global _global_library
    if _global_library is None:
        _global_library = NeoFunctionLibrary()

        library_path = Path(__file__).parent.parent.parent / 'data' / 'neo_function_library.json'
        if library_path.exists():
            _global_library.import_library(library_path)

    return _global_library


def save_function_library():
    library = get_function_library()
    library_path = Path(__file__).parent.parent.parent / 'data' / 'neo_function_library.json'
    library.export_library(library_path)


if __name__ == "__main__":
    library = NeoFunctionLibrary()

    success, result = library.execute('schwarzschild_radius', mass=1.989e30)
    print(f"Schwarzschild radius: {result}")

    success, result = library.execute('hawking_temperature', mass=1.989e30)
    print(f"Hawking temperature: {result}")

    correlations = library.get_correlations('schwarzschild_radius')
    print(f"\nCorrelations for schwarzschild_radius:")
    for func, score in correlations:
        print(f"  {func}: {score:.3f}")

    z0_stats = library.get_floor_statistics('Z0')
    print(f"\nZ0 Statistics: {z0_stats}")

    library.export_library(Path('neo_library_export.json'))
    print("\nLibrary exported to neo_library_export.json")
