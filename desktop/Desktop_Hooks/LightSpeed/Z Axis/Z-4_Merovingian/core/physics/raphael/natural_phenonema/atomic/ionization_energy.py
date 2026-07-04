"""
Ionization Energy: Simulates ionization processes for elements and isotopes.
"""

import numpy as np
import plotly.graph_objects as go

# Ionization energy data for elements (eV)
IONIZATION_ENERGY = {
    "H": [13.6],  # Hydrogen
    "He": [24.6, 54.4],  # Helium
    "Li": [5.4, 75.6, 122.4],  # Lithium
    # Add all elements up to 118
    "Og": [15.6],  # Oganesson (estimated)
}


def calculate_ionization_energy(element, level):
    """
    Calculate ionization energy for a given element and ionization level.
    """
    if element not in IONIZATION_ENERGY or level >= len(IONIZATION_ENERGY[element]):
        raise ValueError("Invalid element or ionization level.")
    return IONIZATION_ENERGY[element][level]


def plot_ionization_energy(element):
    """
    Plot ionization energy levels for the selected element.
    """
    if element not in IONIZATION_ENERGY:
        raise ValueError("Element not found in ionization data.")

    energy_levels = IONIZATION_ENERGY[element]
    levels = np.arange(len(energy_levels)) + 1

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=levels,
        y=energy_levels,
        text=[f"{e} eV" for e in energy_levels],
        textposition="auto",
        marker=dict(color="skyblue")
    ))

    fig.update_layout(
        title=f"Ionization Energy Levels for {element}",
        xaxis=dict(title="Ionization Level"),
        yaxis=dict(title="Ionization Energy (eV)"),
        paper_bgcolor="black",
        font=dict(color="white")
    )
    return fig


if __name__ == "__main__":
    element = "H"
    fig = plot_ionization_energy(element)
    fig.show()
