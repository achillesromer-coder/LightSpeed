"""CGX manufacturing compiler package.

Machine-neutral compile/schedule logic only. Physical execution remains separately gated.
"""

from .compiler import (
    compile_component,
    compile_assembly,
    find_archetype,
    find_instance,
    load_default_atlas,
    load_default_instance_population,
    validate_simulation_result,
)
from .adapter import AdapterError, emit_reference_gcode

__all__ = [
    "compile_component",
    "compile_assembly",
    "find_archetype",
    "find_instance",
    "load_default_atlas",
    "load_default_instance_population",
    "validate_simulation_result",
    "AdapterError",
    "emit_reference_gcode",
]