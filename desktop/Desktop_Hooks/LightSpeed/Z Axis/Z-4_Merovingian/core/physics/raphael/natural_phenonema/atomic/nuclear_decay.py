"""
Nuclear Decay Simulation
"""

import numpy as np
import plotly.graph_objects as go

# Constants
AVOGADRO_NUMBER = 6.022e23  # Avogadro's number
DECAY_CONSTANT = {
    "Uranium-238": 4.468e9,  # Half-life in years
    "Carbon-14": 5730,       # Half-life in years
    "Iodine-131": 8.0        # Half-life in days
}

def calculate_decay(n0, half_life, time):
    """
    Simulate radioactive decay.

    Parameters:
        n0 (float): Initial number of nuclei.
        half_life (float): Half-life of the isotope.
        time (float): Time elapsed.

    Returns:
        float: Remaining number of nuclei.
    """
    decay_constant = np.log(2) / half_life
    return n0 * np.exp(-decay_constant * time)

def plot_decay(isotope, initial_amount, max_time, steps):
    """
    Visualize the radioactive decay of an isotope over time.

    Parameters:
        isotope (str): Isotope name.
        initial_amount (float): Initial number of nuclei.
        max_time (float): Maximum time for simulation (in years or days).
        steps (int): Number of time steps.

    Returns:
        plotly.graph_objects.Figure: Decay plot.
    """
    times = np.linspace(0, max_time, steps)
    remaining = calculate_decay(initial_amount, DECAY_CONSTANT[isotope], times)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times, y=remaining,
        mode="lines",
        line=dict(color="red", width=3),
        name=f"{isotope} Decay"
    ))

    fig.update_layout(
        title=f"Radioactive Decay of {isotope}",
        xaxis=dict(title="Time (years or days)", gridcolor="gray"),
        yaxis=dict(title="Remaining Nuclei", gridcolor="gray"),
        paper_bgcolor="black",
        plot_bgcolor="black",
        font=dict(color="white")
    )
    return fig

# Example usage
if __name__ == "__main__":
    isotope = "Uranium-238"
    initial_amount = AVOGADRO_NUMBER  # 1 mole of nuclei
    max_time = DECAY_CONSTANT[isotope]  # Half-life in years
    decay_plot = plot_decay(isotope, initial_amount, max_time, steps=500)
    decay_plot.show()
