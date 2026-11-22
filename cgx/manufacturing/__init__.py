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
    load_compound_parent_decompositions,
    resolve_compound_parent_decomposition,
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
    "load_compound_parent_decompositions",
    "resolve_compound_parent_decomposition",
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
# Optional, read-only sequencing preflight over the canonical manufacturing IR.
from .review_gate import compile_review as review_printspace_sequence
__all__.append("review_printspace_sequence")
from .review_gate import review_existing_manufacturing_ir
__all__.append("review_existing_manufacturing_ir")

# Geometric shorthand and a review-only LOAD H0 composition projection.
from .composition import compile_geometry_composition
__all__.append("compile_geometry_composition")

# Exact rational convex contact is a digital geometry classifier, never a machine gate.
from .exact_contact import exact_convex_contact, ContactHold
__all__.extend(["exact_convex_contact", "ContactHold"])

# Planning-only directional witness packets; real lot/tool evidence remains external.
from .interface_qualification import plan_interface_witnesses
__all__.append("plan_interface_witnesses")

# Bounded nominal solid measurements and read-only composite service dependency DAG.
from .solid_metrics import exact_nominal_convex_metrics, measure_composite_nominal
from .digital_service_stack import compile_digital_service_stack, verify_digital_service_stack_backwards
__all__.extend(["exact_nominal_convex_metrics", "measure_composite_nominal",
                "compile_digital_service_stack", "verify_digital_service_stack_backwards"])
