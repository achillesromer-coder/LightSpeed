import sys
import os

# Adding natural_phenomena and Simulations directories to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))  # Root directory where Raphael_Runner.py is located
natural_phenomena_path = os.path.join(project_root, 'natural_phenomena')
simulations_path = os.path.join(project_root, 'Simulations')

sys.path.append(natural_phenomena_path)
sys.path.append(simulations_path)

# Now you can import your modules
from time_dynamics import evolve_quantum_state, cosmic_expansion
from data_io import save_simulation_state, load_simulation_state
from visualization_tools import generate_heatmap
from system_interaction import ecosystem_to_climate_feedback
from fractal_expansion import generate_fractal_3d
from simulation_controller import run_simulation

from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import random
from dash.dependencies import Input, Output
import plotly.graph_objects as go

# Initialize Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])


# Load Screen: Random Background Simulation
def create_load_screen():
    x, y, z = generate_fractal_3d(levels=random.randint(2, 5), num_points=500)
    fig = go.Figure(data=go.Scatter3d(
        x=x, y=y, z=z,
        mode='markers',
        marker=dict(size=2, color=z, colorscale="Viridis", opacity=0.8)
    ))
    fig.update_layout(
        title="Initializing Raphael System...",
        paper_bgcolor="black",
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False)
        ),
        margin=dict(l=0, r=0, b=0, t=30),
        font=dict(color="white")
    )
    return fig


# Layout for the app
app.layout = html.Div(
    style={"backgroundColor": "black", "color": "white", "height": "100vh"},
    children=[
        # Loading Screen Div
        dcc.Graph(
            id="loading-screen",
            figure=create_load_screen(),
            style={"height": "80vh"}
        ),
        html.Div(id="loading-text", children="Loading... Please wait.",
                 style={"textAlign": "center", "color": "#7289DA", "fontSize": "24px"}),

        # Main Menu Div (hidden by default, appears after loading)
        html.Div(id="main-menu", style={"display": "none"},
                 children=[
                     html.H1("Raphael Unified Simulator",
                             style={"textAlign": "center", "marginBottom": "20px", "color": "#7289DA"}),

                     html.Label("Select a Phenomenon:", style={"color": "white"}),
                     dcc.Dropdown(
                         id="phenomenon-dropdown",
                         options=[
                             {"label": "Atomic", "value": "atomic"},
                             {"label": "Cosmic", "value": "cosmic"},
                             {"label": "Galactic", "value": "galactic"},
                             {"label": "Quantum", "value": "quantum"},
                             {"label": "Stellar", "value": "stellar"},
                         ],
                         value="atomic",
                         style={"backgroundColor": "black", "color": "white"}
                     ),

                     html.Label("OR, Simulate an N-Body Problem:", style={"color": "white"}),
                     dcc.Dropdown(
                         id="n-body-dropdown",
                         options=[
                             {"label": "Atomic Scale", "value": "atomic_n"},
                             {"label": "Cosmic Scale", "value": "cosmic_n"},
                             {"label": "Galactic Scale", "value": "galactic_n"},
                         ],
                         value=None,
                         style={"backgroundColor": "black", "color": "white"}
                     ),
                     html.Div(
                         dcc.Graph(id="main-visualization", style={"height": "75vh"}),
                         style={"marginTop": "20px"}
                     )
                 ])
    ]
)


# App Callbacks
@app.callback(
    [Output("main-menu", "style"),
     Output("loading-screen", "style"),
     Output("loading-text", "style")],
    Input("loading-screen", "figure")
)
def show_main_menu(_):
    # Once the loading screen is finished, show the main menu
    return {"display": "block"}, {"display": "none"}, {"display": "none"}


@app.callback(
    Output("main-visualization", "figure"),
    [Input("phenomenon-dropdown", "value"),
     Input("n-body-dropdown", "value")]
)
def update_main_visualization(phenomenon, n_body):
    if n_body:
        # Run N-Body Simulation for selected scale
        x, y, z = generate_fractal_3d(levels=5, num_points=1000)
        fig = go.Figure(data=go.Scatter3d(
            x=x, y=y, z=z,
            mode='markers',
            marker=dict(size=4, color=z, colorscale="Inferno", opacity=0.7)
        ))
        fig.update_layout(
            title=f"N-Body Simulation: {n_body.replace('_n', '')} Scale",
            paper_bgcolor="black",
            font=dict(color="white")
        )
    else:
        # Render chosen phenomenon
        if phenomenon == "atomic":
            x, y, z = generate_fractal_3d(levels=4, num_points=1000)
            title = "Atomic Level Visualization"
        elif phenomenon == "cosmic":
            x, y, z, _ = cosmic_expansion(time_step=random.randint(1, 100), num_points=1000)
            title = "Cosmic Expansion Visualization"
        elif phenomenon == "galactic":
            x, y, z = generate_fractal_3d(levels=6, num_points=1000)
            title = "Galactic Structures"
        elif phenomenon == "quantum":
            x, y, z, density = evolve_quantum_state(time_step=random.randint(1, 100), num_points=1000)
            title = "Quantum State Evolution"
        elif phenomenon == "stellar":
            x, y, z = generate_fractal_3d(levels=3, num_points=800)
            title = "Stellar Dynamics"
        else:
            x, y, z = generate_fractal_3d(levels=3, num_points=800)
            title = "Default Fractal Simulation"

        fig = go.Figure(data=go.Scatter3d(
            x=x, y=y, z=z,
            mode='markers',
            marker=dict(size=3, color=z, colorscale="Viridis", opacity=0.8)
        ))
        fig.update_layout(
            title=title,
            paper_bgcolor="black",
            scene=dict(
                xaxis=dict(title="X-axis"),
                yaxis=dict(title="Y-axis"),
                zaxis=dict(title="Z-axis"),
            ),
            margin=dict(l=0, r=0, b=0, t=30),
            font=dict(color="white")
        )

    return fig


# Main Execution
if __name__ == "__main__":
    app.run_server(debug=True)
