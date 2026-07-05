import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# Initialize Dash app
app = Dash(__name__)

# Raphael equation for spacetime visualization
def raphael_equation(t, spin, acc_rate):
    curvature = np.exp(-np.abs(t)) * spin * acc_rate
    density = np.sin(t) * acc_rate
    forces = np.gradient(curvature) * acc_rate
    return curvature, density, forces

# Adjust grid size dynamically to match array size
def calculate_grid_size(array):
    grid_size = int(np.sqrt(array.size))
    if grid_size**2 != array.size:
        grid_size = int(np.floor(np.sqrt(array.size)))
    return grid_size

# Create interactive map visualization
def create_interactive_map(curvature, density, forces):
    grid_size = calculate_grid_size(curvature)
    curvature = curvature[: grid_size**2].reshape((grid_size, grid_size))
    density = density[: grid_size**2].reshape((grid_size, grid_size))
    forces = forces[: grid_size**2].reshape((grid_size, grid_size))

    fig = go.Figure()

    fig.add_trace(
        go.Surface(
            z=curvature,
            colorscale="Viridis",
            showscale=True,
            opacity=0.8,
            name="Spacetime Curvature",
        )
    )

    fig.add_trace(
        go.Surface(
            z=density + 0.1,
            colorscale="YlOrRd",
            showscale=False,
            opacity=0.5,
            name="Energy Density",
        )
    )

    fig.add_trace(
        go.Surface(
            z=forces - 0.1,
            colorscale="Cividis",
            showscale=False,
            opacity=0.5,
            name="Dynamic Forces",
        )
    )

    fig.update_layout(
        title="Interactive Raphael Equation Visualization",
        scene=dict(
            xaxis_title="Time",
            yaxis_title="Energy",
            zaxis_title="Curvature",
        ),
        margin=dict(l=0, r=0, b=0, t=30),
    )
    return fig

# Dynamic hologram visualization
def create_dynamic_hologram(t, spin, acc_rate):
    curvature, density, forces = raphael_equation(t, spin, acc_rate)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter3d(
            x=t,
            y=np.sin(t) * acc_rate,
            z=np.log(np.abs(curvature + 1)),
            mode="markers",
            marker=dict(size=5, color=t, colorscale="Plasma", opacity=0.7),
            name="Dynamic Electromagnetic Emissions",
        )
    )

    fig.add_trace(
        go.Mesh3d(
            x=np.sin(t),
            y=np.cos(t),
            z=curvature,
            opacity=0.5,
            color="rgb(100,200,200)",
            name="Spacetime Curvature Mesh",
        )
    )

    fig.update_layout(
        title="Dynamic Holographic Black Hole Visualization",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Curvature",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
        ),
        margin=dict(l=0, r=0, b=0, t=30),
    )
    return fig

# Live-play visualization
def create_live_play(t, spin, acc_rate):
    curvature, density, forces = raphael_equation(t, spin, acc_rate)

    fig = go.Figure()

    # Add dark matter/dark energy
    dark_matter = np.abs(np.cos(t)) * curvature
    dark_energy = np.abs(np.sin(t)) * density

    fig.add_trace(
        go.Scatter3d(
            x=t,
            y=dark_matter,
            z=dark_energy,
            mode="lines",
            line=dict(color="purple", width=3),
            name="Dark Matter/Energy",
        )
    )

    # Add baryonic matter dynamics
    baryonic_x, baryonic_y = np.meshgrid(np.linspace(-2, 2, 100), np.linspace(-2, 2, 100))
    baryonic_t = t[:100]  # Ensure t matches baryonic grid size
    baryonic_z = np.abs(np.sin(baryonic_x**2 + baryonic_y**2 - baryonic_t[:, None, None]))

    fig.add_trace(
        go.Surface(
            x=baryonic_x,
            y=baryonic_y,
            z=baryonic_z[0],
            colorscale="Oranges",
            opacity=0.7,
            name="Baryonic Matter",
        )
    )

    fig.update_layout(
        title="Live-Play Raphael Equation Visualization",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Density",
        ),
        margin=dict(l=0, r=0, b=0, t=30),
    )
    return fig

# App layout
app.layout = html.Div(
    [
        html.H1("6D Tessellated Spacetime Black Hole Visualization"),
        html.Div(
            [
                html.Label("Spin Parameter:"),
                dcc.Slider(id="spin-slider", min=0, max=1, step=0.1, value=0.5),
                html.Label("Accretion Rate:"),
                dcc.Slider(id="accretion-slider", min=0, max=1, step=0.1, value=0.5),
            ],
            style={"width": "48%", "display": "inline-block"},
        ),
        dcc.Graph(id="interactive-map"),
        dcc.Graph(id="dynamic-hologram"),
        dcc.Graph(id="live-play"),
    ]
)

# Callback
@app.callback(
    [
        Output("interactive-map", "figure"),
        Output("dynamic-hologram", "figure"),
        Output("live-play", "figure"),
    ],
    [Input("spin-slider", "value"), Input("accretion-slider", "value")],
)
def update_visualizations(spin, acc_rate):
    t = np.linspace(-10, 10, 500)
    curvature, density, forces = raphael_equation(t, spin, acc_rate)
    return (
        create_interactive_map(curvature, density, forces),
        create_dynamic_hologram(t, spin, acc_rate),
        create_live_play(t, spin, acc_rate),
    )


if __name__ == "__main__":
    app.run_server(debug=True)
