import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

# Simulation parameters
grid_size = 50
time_steps = 100
omega = 0.15
k = 0.25
A = 1.0

def generate_scenario2_data(t):
    x = np.linspace(-5, 5, grid_size)
    y = np.linspace(-5, 5, grid_size)
    z = np.linspace(-5, 5, grid_size)
    X, Y, Z = np.meshgrid(x, y, z)

    wave = A * np.sin(k * X - omega * t) * np.exp(-0.1 * (X**2 + Y**2 + Z**2))
    pressure = np.gradient(wave, axis=0) + np.gradient(wave, axis=1) + np.gradient(wave, axis=2)

    return X.flatten(), Y.flatten(), Z.flatten(), wave.flatten(), pressure[0].flatten()

# Initialize Dash app
app = Dash(__name__)
app.title = "Raphael Scenario 2 Simulation"

app.layout = html.Div(style={'backgroundColor': 'black', 'color': 'white'}, children=[
    html.H2("Scenario 2: Oscillation of Bound/Unbound Energy and Now Frame", style={'textAlign': 'center'}),
    dcc.Graph(id='scenario2-graph', style={'height': '90vh'}),
    html.Div([
        html.Label("Time Step", style={'marginTop': '10px'}),
        dcc.Slider(id='time-slider', min=0, max=time_steps, step=1, value=0),
    ], style={'margin': '20px'})
])

@app.callback(
    Output('scenario2-graph', 'figure'),
    [Input('time-slider', 'value')]
)
def update_scene(t):
    x, y, z, values, pressure = generate_scenario2_data(t)

    scatter = go.Scatter3d(
        x=x, y=y, z=z,
        mode='markers',
        marker=dict(
            size=2,
            color=values,
            colorscale='Rainbow',
            opacity=0.8,
            colorbar=dict(title="Energy State")
        )
    )

    layout = go.Layout(
        scene=dict(
            xaxis=dict(title='X'),
            yaxis=dict(title='Y'),
            zaxis=dict(title='Z'),
            bgcolor='black'
        ),
        paper_bgcolor='black',
        plot_bgcolor='black',
        margin=dict(l=0, r=0, b=0, t=40)
    )

    return go.Figure(data=[scatter], layout=layout)

if __name__ == '__main__':
    app.run_server(debug=True)
