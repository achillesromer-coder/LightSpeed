"""
Atomic Phenomena Package: Unified interactive render for atomic-scale phenomena.
"""

from dash import Dash, dcc, html, Input, Output
from dash.exceptions import PreventUpdate
from .atomic_orbitals import plot_atomic_orbitals
from .atomic_elemental_interactive_table import plot_elemental_table

# Initialize Dash App
app = Dash(__name__)

# Phenomena Mapping
PHENOMENA = {
    "Atomic Orbitals": lambda: plot_atomic_orbitals(n=2, l=1, m=0),
    "Elemental Table Visualization": plot_elemental_table,
}

# Layout
app.layout = html.Div(
    style={"backgroundColor": "black", "color": "white", "fontFamily": "Arial"},
    children=[
        html.H1("Atomic Phenomena Simulations", style={"textAlign": "center"}),

        # Phenomenon Selection Menu
        html.Div([
            html.Label("Select Phenomenon:"),
            dcc.Dropdown(
                id="phenomenon-selector",
                options=[{"label": name, "value": name} for name in PHENOMENA.keys()],
                value="Atomic Orbitals",
                style={"backgroundColor": "black", "color": "white"}
            ),
        ], style={"margin": "20px"}),

        # Rendered Visualization
        html.Div([
            dcc.Graph(id="atomic-visualization", style={"height": "75vh"}),
        ]),
    ]
)

# Callbacks
@app.callback(
    Output("atomic-visualization", "figure"),
    [Input("phenomenon-selector", "value")]
)
def update_atomic_visualization(selected_phenomenon):
    if selected_phenomenon is None:
        raise PreventUpdate

    # Generate visualization for selected phenomenon
    plotter = PHENOMENA[selected_phenomenon]
    figure = plotter()

    return figure

# Run App
if __name__ == "__main__":
    app.run_server(debug=True)
