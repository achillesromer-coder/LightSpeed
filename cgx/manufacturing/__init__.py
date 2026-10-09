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
from .binding import (
    create_witness_coupon_packet,
    resolve_binding_gate,
    resolve_binding_queue,
    validate_lot_passport,
    validate_tool_manifest,
)

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
    "resolve_binding_gate",
    "resolve_binding_queue",
    "validate_lot_passport",
    "validate_tool_manifest",
    "create_witness_coupon_packet",
    "find_volumetric_kernel",
    "load_volumetric_kernel",
    "resolve_volumetric_topology",
]
from .volumetric import (
    find_volumetric_kernel,
    load_volumetric_kernel,
    resolve_volumetric_topology,
)
