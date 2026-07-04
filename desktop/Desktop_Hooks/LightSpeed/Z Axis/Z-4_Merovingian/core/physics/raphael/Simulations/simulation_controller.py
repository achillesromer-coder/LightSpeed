from time_dynamics import evolve_quantum_state, evolve_ecosystem, cosmic_expansion
from data_io import save_simulation_state, load_simulation_state
from visualization_tools import overlay_interactions, generate_heatmap

def run_simulation(params):
    """
    Executes simulation based on provided parameters.
    """
    time_step = params["time_step"]
    scale = params["scale"]
    num_points = params["num_points"]

    # Quantum state evolution
    quantum_x, quantum_y, quantum_z, quantum_density = evolve_quantum_state(time_step, num_points)

    # Ecosystem dynamics
    ecosystem_state = evolve_ecosystem(time_step, params["ecosystem"])

    # Cosmic evolution
    cosmic_x, cosmic_y, cosmic_z, expansion_scale = cosmic_expansion(time_step, num_points)

    # Save state
    save_simulation_state({"quantum": (quantum_x, quantum_y, quantum_z)}, "quantum_state.json")

    # Generate visualizations
    fig = generate_heatmap(quantum_density, quantum_x, quantum_y, "Quantum Density Heatmap")
    return fig
