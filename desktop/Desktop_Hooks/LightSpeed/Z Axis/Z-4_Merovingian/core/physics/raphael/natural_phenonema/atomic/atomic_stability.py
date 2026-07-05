"""
Atomic Stability: Calculate and visualize nuclear stability based on proton-neutron ratio.
"""

import numpy as np
import plotly.graph_objects as go

def calculate_stability(protons, neutrons):
    """
    Calculate nuclear stability based on the proton-neutron ratio.
    """
    ratio = neutrons / protons
    if ratio < 1 or ratio > 1.5:
        return "Unstable"
    elif 1 <= ratio <= 1.5:
        return "Stable"

def plot_stability_range():
    """
    Plot the stability range for protons vs. neutrons.
    """
    protons = np.arange(1, 101)
    neutrons = np.arange(1, 151)

    proton_grid, neutron_grid = np.meshgrid(protons, neutrons)
    stability = np.vectorize(calculate_stability)(proton_grid, neutron_grid)

    fig = go.Figure(data=go.Heatmap(
        z=(stability == "Stable").astype(int),
        x=protons,
        y=neutrons,
        colorscale="Viridis"
    ))

    fig.update_layout(
        title="Nuclear Stability Chart",
        xaxis=dict(title="Protons"),
        yaxis=dict(title="Neutrons"),
        paper_bgcolor="black",
        font=dict(color="white")
    )
    return fig

if __name__ == "__main__":
    fig = plot_stability_range()
    fig.show()
