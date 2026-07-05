"""
Atomic Emission Spectra: Render spectral lines based on quantum transitions.
"""

import numpy as np
import plotly.graph_objects as go

# Spectral lines for elements (nm)
EMISSION_SPECTRA = {
    "H": [656.3, 486.1, 434.0, 410.2],  # Balmer series
    "He": [587.6, 447.1, 402.6, 381.9],  # Helium lines
    "Li": [670.8, 610.4, 497.2],  # Lithium lines
    # Add elements up to 118
}


def render_emission_spectrum(element):
    """
    Render emission spectrum for the selected element.
    """
    if element not in EMISSION_SPECTRA:
        raise ValueError("Element not found in emission spectrum data.")

    wavelengths = EMISSION_SPECTRA[element]
    intensities = np.random.uniform(0.5, 1.0, len(wavelengths))  # Simulate intensity variation

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=wavelengths,
        y=intensities,
        mode="markers+lines",
        marker=dict(size=10, color=wavelengths, colorscale="Viridis"),
        line=dict(width=2)
    ))

    fig.update_layout(
        title=f"Emission Spectrum for {element}",
        xaxis=dict(title="Wavelength (nm)", range=[min(wavelengths) - 50, max(wavelengths) + 50]),
        yaxis=dict(title="Intensity (a.u.)"),
        paper_bgcolor="black",
        font=dict(color="white")
    )
    return fig


if __name__ == "__main__":
    element = "H"
    fig = render_emission_spectrum(element)
    fig.show()
