import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

def generate_raphael_quantum_foam(size=30, time=0):
    x, y, z = np.mgrid[:size, :size, :size]
    foam = (
        np.sin(0.2 * x + time) * np.cos(0.2 * y + time) * np.sin(0.2 * z + time) +
        np.cos(0.1 * x * y + time) * np.sin(0.1 * y * z + time) +
        np.sin(0.15 * x * z + time)
    )
    return foam

grid_size = 30
initial_time = 0
foam_data = generate_raphael_quantum_foam(grid_size, initial_time)
x, y, z = np.mgrid[:grid_size, :grid_size, :grid_size]
coords = np.vstack((x.flatten(), y.flatten(), z.flatten()))

app = Dash(__name__)
app.title = "Raphael Quantum Foam – Scenario 1"

app.layout = html.Div([
    html.H2("Quantum Foam – Scenario 1 (Raphael Equation)", style={"textAlign": "center"}),
    dcc.Graph(id='quantum-foam-graph'),
    dcc.Slider(id='time-slider', min=0, max=20, step=0.1, value=0,
               tooltip={"placement": "bottom", "always_visible": True}),
])

@app.callback(
    Output('quantum-foam-graph', 'figure'),
    [Input('time-slider', 'value')]
)
def update_graph(time):
    foam = generate_raphael_quantum_foam(grid_size, time)
    values = foam.flatten()
    scatter = go.Scatter3d(
        x=coords[0], y=coords[1], z=coords[2],
        mode='markers',
        marker=dict(
            size=2,
            color=values,
            colorscale='Viridis',
            opacity=0.8,
            colorbar=dict(title="Field Intensity")
        )
    )
    layout = go.Layout(
        scene=dict(
            xaxis=dict(title='X'),
            yaxis=dict(title='Y'),
            zaxis=dict(title='Z')
        ),
        margin=dict(l=0, r=0, b=0, t=30)
    )
    return go.Figure(data=[scatter], layout=layout)

if __name__ == '__main__':
    app.run_server(debug=True)
