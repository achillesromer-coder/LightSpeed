"""
LightSpeed Physics Modules
TheConstruct Layer - Z-Axis Level 0
Core physics simulations and equations
"""

__version__ = "0.9.5"
__author__ = "LightSpeed Team"

from .raphael_equations import (
    calculate_raphael_equations,
    raphael_equations_oval,
    calculate_big_bang_raphael_equations,
    raphael_equation,
)

from .big_bang_simulation import (
    generate_big_bang_simulation,
    plot_big_bang,
    fractal_refinement,
)

from .orbital_mechanics import (
    calculate_schwarzschild_radius,
    calculate_orbital_density,
    plot_atomic_orbitals,
    generate_orbital_mesh,
    plot_orbital,
)

from .quantum_mechanics import (
    evolve_quantum_state,
    radial_distribution,
    update_orbital_visualization,
)

__all__ = [
    # Raphael Equations
    'calculate_raphael_equations',
    'raphael_equations_oval',
    'calculate_big_bang_raphael_equations',
    'raphael_equation',

    # Big Bang Simulation
    'generate_big_bang_simulation',
    'plot_big_bang',
    'fractal_refinement',

    # Orbital Mechanics
    'calculate_schwarzschild_radius',
    'calculate_orbital_density',
    'plot_atomic_orbitals',
    'generate_orbital_mesh',
    'plot_orbital',

    # Quantum Mechanics
    'evolve_quantum_state',
    'radial_distribution',
    'update_orbital_visualization',
]
