import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, callback_context, State
from scipy.constants import G, c
from threading import Timer
import logging

# Constants
HUBBLE_CONSTANT_DEFAULT = 70  # km/s/Mpc
TIME_STEP_DEFAULT = 100  # Million years
UNIVERSE_SIZE_DEFAULT = 1000  # Mpc
DARK_ENERGY_INFLUENCE = 0.7
BARYONIC_MATTER_INFLUENCE = 0.3
SPEED_OF_LIGHT_MPC = c / 1e6  # Speed of light in Mpc/year

# Global Variables for Live Playback
current_step = 0
play_active = False
play_speed = 1.0  # Default playback speed
MAX_STEPS = 1000  # Maximum time steps for simulation

# Initialize Dash App
app = Dash(__name__)
logging.basicConfig(level=logging.INFO)
logging.info("Universal Expansion Simulation Initialized")

# Dash App Layout
app.layout = html.Div(
    html.H1("Interactive Universal Expansion Simulation", style={"textAlign": "center"}),
)


# Raphael Equations for Universal Expansion
def raphael_equations(hubble_constant, universe_size, time_step):
    """Calculate universal expansion metrics using Raphael equations."""
    expansion_velocity = hubble_constant * universe_size
    acceleration_due_to_dark_energy = DARK_ENERGY_INFLUENCE * hubble_constant
    return {
        "Expansion Velocity": expansion_velocity,
        "Dark Energy Acceleration": acceleration_due_to_dark_energy,
        "Time Step": time_step
    }

# Generate Universal Expansion Data
def generate_universal_expansion(hubble_constant, universe_size, time_steps, include_dark_energy=True):
    time = np.linspace(0, time_steps * TIME_STEP_DEFAULT, time_steps)  # Time in millions of years
    size = np.linspace(universe_size, universe_size * 10, time_steps)

    # Apply dark energy influence
    if include_dark_energy:
        size += DARK_ENERGY_INFLUENCE * size * np.log(time + 1)

    velocity = hubble_constant * size
    return time, size, velocity

# Plot Universal Expansion
def plot_universal_expansion(time, size, velocity):
    fig = go.Figure()

    # Main Expansion Curve
    fig.add_trace(
        go.Scatter3d(
            x=time, y=size, z=velocity,
            mode="lines",
            line=dict(color="blue", width=3),
            name="Universal Expansion"
        )
    )

    # Add Overlays for Dark Energy and Baryonic Matter
    fig.add_trace(
        go.Scatter3d(
            x=time, y=size, z=DARK_ENERGY_INFLUENCE * size,
            mode="lines",
            line=dict(color="purple", width=2, dash="dash"),
            name="Dark Energy Influence"
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=time, y=BARYONIC_MATTER_INFLUENCE * size, z=velocity,
            mode="lines",
            line=dict(color="orange", width=2, dash="dot"),
            name="Baryonic Matter Influence"
        )
    )

    fig.update_layout(
        title="Universal Expansion Visualization",
        scene=dict(
            xaxis=dict(title="Time (Million Years)"),
            yaxis=dict(title="Size (Mpc)"),
            zaxis=dict(title="Velocity (km/s)"),
            aspectmode="cube"
        ),
        template="plotly_dark"
    )
    return fig
# Unified Callback to Handle Updates and Playback
@app.callback(
    Output("universal-expansion-graph", "figure"),
    [Input("play-button", "n_clicks"),
     Input("pause-button", "n_clicks"),
     Input("speed-slider", "value"),
     Input("hubble-slider", "value"),
     Input("size-slider", "value"),
     Input("time-slider", "value")],
    prevent_initial_call=True,
)
def unified_update_graph(play_clicks, pause_clicks, speed, hubble_constant, universe_size, time_step):
    """
    Combines updates for universal expansion graph with playback functionality.
    """
    global play_active, play_speed, current_step

    # Determine the triggering event
    ctx = callback_context.triggered[0]["prop_id"].split(".")[0]
    if ctx == "play-button":
        play_active = True
        play_speed = speed
    elif ctx == "pause-button":
        play_active = False

    # Increment current step during live playback
    if play_active:
        current_step = (current_step + int(play_speed)) % MAX_STEPS

    # Generate expansion data for the current state
    time, size, velocity = generate_universal_expansion(hubble_constant, universe_size, MAX_STEPS)

    # Plot data up to the current step
    return plot_universal_expansion(
        time[:current_step],
        size[:current_step],
        velocity[:current_step]
    )
# Update Graph with Raphael Overlays
@app.callback(
    Output("universal-expansion-graph", "figure"),
    [Input("dimension-toggle", "value")],
    [State("hubble-slider", "value"),
     State("size-slider", "value"),
     State("time-slider", "value")],
    prevent_initial_call=True,
)
def update_dimensions(dimensions, hubble_constant, universe_size, time_step):
    """
    Updates the universal expansion graph with Raphael overlays based on dimension toggles.
    """
    global current_step

    # Generate expansion data
    time, size, velocity = generate_universal_expansion(hubble_constant, universe_size, MAX_STEPS)

    # Base graph
    figure = plot_universal_expansion(
        time[:current_step],
        size[:current_step],
        velocity[:current_step]
    )

    # Apply dimensional overlays
    if 5 in dimensions:
        figure.add_trace(
            go.Scatter3d(
                x=time[:current_step],
                y=size[:current_step],
                z=DARK_ENERGY_INFLUENCE * size[:current_step],
                mode="lines",
                line=dict(color="purple", width=2, dash="dash"),
                name="Dark Energy Influence"
            )
        )
    if 6 in dimensions:
        figure.add_trace(
            go.Scatter3d(
                x=time[:current_step],
                y=BARYONIC_MATTER_INFLUENCE * size[:current_step],
                z=velocity[:current_step],
                mode="lines",
                line=dict(color="orange", width=2, dash="dot"),
                name="Baryonic Matter Influence"
            )
        )

    return figure
@app.callback(
    [
        Output("universal-expansion-graph", "figure"),
        Output("raphael-equations", "children"),
    ],
    [
        Input("hubble-slider", "value"),
        Input("size-slider", "value"),
        Input("time-slider", "value"),
        Input("play-button", "n_clicks"),
        Input("pause-button", "n_clicks"),
    ]
)
def update_universal_expansion_graph(hubble_constant, universe_size, time_step, play_clicks, pause_clicks):
    """
    Unified callback to handle graph updates and Raphael equation updates.
    Uses dash.callback_context to distinguish the triggering input.
    """
    global play_active, current_step

    # Identify triggering input
    ctx = callback_context.triggered[0]["prop_id"].split(".")[0]

    # Handle play/pause button inputs
    if ctx == "play-button":
        play_active = True
    elif ctx == "pause-button":
        play_active = False

    # Generate expansion data
    time, size, velocity = generate_universal_expansion(hubble_constant, universe_size, time_step)

    # Generate graph
    figure = plot_universal_expansion(time, size, velocity)

    # Raphael Equations
    raphael_results = raphael_equations(hubble_constant, universe_size, time_step)
    raphael_text = "<br>".join([f"{key}: {value:.2e}" for key, value in raphael_results.items()])

    return figure, f"Raphael Equations:<br>{raphael_text}"

if __name__ == "__main__":
    app.run_server(debug=True)
