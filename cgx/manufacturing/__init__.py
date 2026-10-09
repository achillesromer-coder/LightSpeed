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
from .invariants import (
    InvariantInputError,
    axis_force_budget,
    capacitance_density,
    evaluate_invariant,
    retention_ratio,
    resistor_squares,
    rl_winding_baseline,
    rss_uncertainty,
    sheet_path_resistance,
)
from .printstack import (
    compile_printable_catalogue,
    compile_printable_component,
    compile_printable_stack,
)
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
    "compile_printable_catalogue",
    "compile_printable_component",
    "compile_printable_stack",
    "AdapterError",
    "emit_reference_gcode",
    "InvariantInputError",
    "capacitance_density",
    "sheet_path_resistance",
    "resistor_squares",
    "rl_winding_baseline",
    "axis_force_budget",
    "rss_uncertainty",
    "retention_ratio",
    "evaluate_invariant",
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