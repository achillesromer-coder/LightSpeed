
# Imports

from dash import Dash
from dash import dcc
from dash import html
import dash
import dash_bootstrap_components
import numpy
import plotly.graph_objs
import sympy


# ===== CONSOLIDATED FROM 4 FILES =====

# Merged on: 2025-11-21 17:46:25

# Source files: 4


import numpy as np
import sympy as sp
import plotly.graph_objs as go
import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

# --- Raphael Equations for Spacetime Simulation ---
# Symbolic variables for protons, neutrons, and electrons
p, n, e = sp.symbols('p n e')

# Raphael's equations for strong, weak, and total forces
def calculate_raphael_equations(protons, neutrons, electrons):
    """
    Calculate the forces for a given element using Raphael's equations.
    """
    F_strong = 0.8 * p * n / (p + n)  # Simplified strong force
    F_weak = 0.2 * p * e / (p + e)   # Simplified weak force
    E_total = F_strong + F_weak      # Total energy (sum of forces)

    forces = {
        "Strong Force": F_strong.subs({p: protons, n: neutrons}),
        "Weak Force": F_weak.subs({p: protons, e: electrons}),
        "Total Energy": E_total.subs({p: protons, n: neutrons, e: electrons}),
    }

    return forces

# --- Color Mapping Function ---
def create_correct_colorscale(palette):
    """
    Create a valid Plotly colorscale (list of 2-element lists).
    """
    colorscale = []
    step = 1 / (len(palette) - 1)  # Normalize the range to the number of colors
    for i, color in enumerate(palette):
        color_str = f'rgb({int(color[0])}, {int(color[1])}, {int(color[2])})'
        colorscale.append([i * step, color_str])
    return colorscale

# --- Generate Spacetime Data ---
def generate_3d_visualization_with_corrected_colorscale(mode="curvature", colorscale=None):
    """
    Generate a 3D plot with dynamic color mapping for spacetime features using the corrected colorscale.
    """
    grid_size = 50
    x = np.linspace(-5, 5, grid_size)
    y = np.linspace(-5, 5, grid_size)
    z = np.linspace(-5, 5, grid_size)
    X, Y, Z = np.meshgrid(x, y, z)

    if mode == "curvature":
        values = np.exp(-(X**2 + Y**2 + Z**2))  # Gaussian curvature model
    elif mode == "density":
        values = np.sqrt(X**2 + Y**2 + Z**2)  # Radial density model
    elif mode == "energy":
        values = np.cos(X**2 + Y**2 + Z**2)  # Example energy field

    # Map values to color (simple linear mapping for now)
    color_values = np.clip(values.flatten(), 0, 1)  # Clip values to [0, 1] for color mapping

    # Plotly 3D volume plot with the corrected colorscale
    fig = go.Figure(data=[
        go.Volume(
            x=X.flatten(),
            y=Y.flatten(),
            z=Z.flatten(),
            value=color_values,
            isomin=0.1,
            isomax=0.8,
            opacity=0.3,
            surface_count=17,
            colorscale=colorscale  # Apply the corrected color palette directly
        )
    ])

    fig.update_layout(
        title=f"Spacetime Visualization: {mode.capitalize()}",
        scene=dict(
            xaxis=dict(title="X"),
            yaxis=dict(title="Y"),
            zaxis=dict(title="Z")
        )
    )
    return fig

# --- Dash App for Visualization ---
# Initialize Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

# Side menu with toggle options
def create_side_menu():
    return dbc.Col(
        [
            html.H3("Settings", style={"color": "white"}),
            html.Label("Select Element:", style={"color": "white"}),
            dcc.Dropdown(
                id="element-dropdown",
                options=[{"label": "Hydrogen", "value": "Hydrogen"}, {"label": "Helium", "value": "Helium"}],
                value="Hydrogen",
                style={"backgroundColor": "black", "color": "white"}
            ),
            html.Label("Visualization Mode:", style={"color": "white"}),
            dcc.RadioItems(
                id="visualization-mode",
                options=[
                    {"label": "Curvature", "value": "curvature"},
                    {"label": "Density", "value": "density"},
                    {"label": "Energy", "value": "energy"}
                ],
                value="curvature",
                style={"color": "white"}
            ),
        ],
        width=3,
        style={"padding": "20px", "backgroundColor": "#2C2F33", "borderRight": "2px solid #7289DA"}
    )

# Main graph area
def create_main_graph():
    return dbc.Col(
        [
            dcc.Graph(id="main-visualization", style={"height": "75vh"}),
        ],
        width=9
    )

# Layout
app.layout = html.Div(
    style={"backgroundColor": "black", "color": "white", "height": "100vh"},
    children=[
        html.H1(
            "6D Scientific Visualizer",
            style={"textAlign": "center", "marginBottom": "20px", "color": "#7289DA"}
        ),
        dbc.Row([create_side_menu(), create_main_graph()])
    ]
)

# Callback to update the visualization based on user input
@app.callback(
    dash.dependencies.Output('main-visualization', 'figure'),
    [dash.dependencies.Input('visualization-mode', 'value')]
)
def update_graph(mode):
    color_palette = [
        [0, 0, 255], [255, 0, 0], [0, 255, 0], [255, 255, 0],
        [255, 0, 255], [0, 255, 255], [128, 0, 128], [0, 128, 128],
        [128, 128, 0], [255, 165, 0]  # Sample color palette for testing
    ]

    # Generate the colorscale
    corrected_colorscale = create_correct_colorscale(color_palette)

    # Generate spacetime data and visualization
    fig = generate_3d_visualization_with_corrected_colorscale(mode, corrected_colorscale)

    return fig

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
