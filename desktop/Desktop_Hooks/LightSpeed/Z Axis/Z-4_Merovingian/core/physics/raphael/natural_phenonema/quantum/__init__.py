"""
Quantum Phenomena Package: Unified interactive render for quantum-scale phenomena.
"""

from dash import Dash, dcc, html, Input, Output
from dash.exceptions import PreventUpdate
from .quantum_fluctuations import plot_quantum_fluctuations
from .wave_particle_duality import plot_wave_particle_duality
from .uncertainty_principle import plot_uncertainty_principle

# Initialize Dash App
app = Dash(__name__)

# Phenomena Mapping
PHENOMENA = {
    "Quantum Fluctuations": plot_quantum_fluctuations,
    "Wave-Particle Duality": plot_wave_particle_duality,
    "Uncertainty Principle": plot_uncertainty_principle,
}

# Layout
app.layout = html.Div(
    style={"backgroundColor": "black", "color": "white", "fontFamily": "Arial"},
    children=[
        html.H1("Quantum Phenomena Simulations", style={"textAlign": "center"}),

        # Phenomenon Selection Menu
        html.Div([
            html.Label("Select Phenomenon:"),
            dcc.Dropdown(
                id="phenomenon-selector",
                options=[{"label": name, "value": name} for name in PHENOMENA.keys()],
                value="Quantum Fluctuations",
                style={"backgroundColor": "black", "color": "white"}
            ),
        ], style={"margin": "20px"}),

        # Rendered Visualization
        html.Div([
            dcc.Graph(id="quantum-visualization", style={"height": "75vh"}),
        ]),
    ]
)

# Callbacks
@app.callback(
    Output("quantum-visualization", "figure"),
    [Input("phenomenon-selector", "value")]
)
def update_quantum_visualization(selected_phenomenon):
    if selected_phenomenon is None:
        raise PreventUpdate

    # Generate visualization for selected phenomenon
    plotter = PHENOMENA[selected_phenomenon]
    figure = plotter()

    return figure

# Run App
if __name__ == "__main__":
    app.run_server(debug=True)
