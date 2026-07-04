
# Imports

from dash import Dash
from dash import Input
from dash import Output
from dash import dcc
from dash import html
import numpy
import plotly.graph_objects


# ===== CONSOLIDATED FROM 10 FILES =====

# Merged on: 2025-11-21 17:46:23

# Source files: 10



# Imports

from dash import Dash
from dash import Input
from dash import Output
from dash import dcc
from dash import html
import numpy
import plotly.graph_objects


# ===== CONSOLIDATED FROM 3 FILES =====

# Merged on: 2025-11-17 13:43:28

# Source files: 3


import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# Initialize the app
app = Dash(__name__)

# Raphael equation placeholders and data generation
def raphael_equation(x, y, t, spin, acc_rate):
    curvature = np.sin(x**2 + y**2 - t) * np.exp(-acc_rate * (x**2 + y**2))
    density = np.cos(spin * (x - y)) * np.exp(-t)
    forces = np.abs(np.sin(x * y * t))
    return curvature, density, forces

# Grid for visualization
x = np.linspace(-10, 10, 50)
y = np.linspace(-10, 10, 50)
x, y = np.meshgrid(x, y)

# Layout for UI
app.layout = html.Div([
    html.H1("6D Tessellated Spacetime Black Hole Visualization", style={'text-align': 'center'}),
    html.Div([
        html.Label("Spin Parameter:"),
        dcc.Slider(0, 1, 0.1, value=0.5, id='spin-slider'),
        html.Label("Accretion Rate:"),
        dcc.Slider(0.1, 2, 0.1, value=1, id='accretion-slider'),
        html.Label("Time Progression (t):"),
        dcc.Slider(0, 10, 0.5, value=5, id='time-slider'),
    ], style={'width': '50%', 'display': 'inline-block'}),
    html.Div([
        dcc.Graph(id='main-visualization'),
        dcc.Graph(id='auxiliary-visualization'),
        dcc.Graph(id='live-play-visualization'),
    ], style={'display': 'flex', 'flex-wrap': 'wrap'}),
])

# Callback for updating graphs
@app.callback(
    [Output('main-visualization', 'figure'),
     Output('auxiliary-visualization', 'figure'),
     Output('live-play-visualization', 'figure')],
    [Input('spin-slider', 'value'),
     Input('accretion-slider', 'value'),
     Input('time-slider', 'value')]
)
def update_visualizations(spin, acc_rate, t):
    curvature, density, forces = raphael_equation(x, y, t, spin, acc_rate)

    # Main Visualization
    main_fig = go.Figure(data=go.Surface(z=curvature, x=x, y=y, colorscale='Viridis'))
    main_fig.update_layout(title="Spacetime Curvature Visualization", scene=dict(zaxis_title="Curvature"))

    # Auxiliary Visualization
    aux_fig = go.Figure(data=go.Surface(z=density, x=x, y=y, colorscale='Inferno'))
    aux_fig.update_layout(title="Density and Forces Visualization", scene=dict(zaxis_title="Density"))

    # Live-Play Visualization
    live_fig = go.Figure(data=[
        go.Surface(z=curvature, x=x, y=y, colorscale='Viridis', opacity=0.7),
        go.Surface(z=density, x=x, y=y, colorscale='Inferno', opacity=0.5),
        go.Scatter3d(x=x.flatten(), y=y.flatten(), z=forces.flatten(), mode='lines',
                     line=dict(color='purple', width=2), name="Forces")
    ])
    live_fig.update_layout(title="Dynamic Black Hole Visualization", scene=dict(zaxis_title="Forces"))

    return main_fig, aux_fig, live_fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
