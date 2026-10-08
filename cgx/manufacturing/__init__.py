"""CGX manufacturing compiler package.

Machine-neutral compile/schedule logic only. Physical execution remains separately gated.
"""

from .compiler import (
    compile_component,
    compile_assembly,
    find_archetype,
    load_default_atlas,
    validate_simulation_result,
)
from .adapter import AdapterError, emit_reference_gcode

__all__ = [
    "compile_component",
    "compile_assembly",
    "find_archetype",
    "load_default_atlas",
    "validate_simulation_result",
    "AdapterError",
    "emit_reference_gcode",
]
