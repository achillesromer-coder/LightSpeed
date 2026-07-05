import numpy as np
import plotly.graph_objects as go
from fractal_expansion import generate_fractal_3d

def generate_supply_chain_nodes(num_nodes=100):
    """
    Generates interplanetary supply chain nodes using fractals.
    """
    x, y, z = generate_fractal_3d(levels=3, num_points=num_nodes)
    return x, y, z

def simulate_resource_transfer(start_node, end_node, num_steps):
    """
    Simulates resource transfer between two nodes in the supply chain.
    """
    x = np.linspace(start_node[0], end_node[0], num_steps)
    y = np.linspace(start_node[1], end_node[1], num_steps)
    z = np.linspace(start_node[2], end_node[2], num_steps)
    return x, y, z

def visualize_supply_chain():
    """
    Visualizes interplanetary supply chain with dynamic resource transfers.
    """
    x, y, z = generate_supply_chain_nodes(num_nodes=50)

    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=x, y=y, z=z,
        mode="markers",
        marker=dict(size=5, color="blue", opacity=0.8),
        name="Supply Nodes"
    ))

    # Add resource transfer between two random nodes
    start_node = (x[0], y[0], z[0])
    end_node = (x[10], y[10], z[10])
    transfer_x, transfer_y, transfer_z = simulate_resource_transfer(start_node, end_node, num_steps=20)

    fig.add_trace(go.Scatter3d(
        x=transfer_x, y=transfer_y, z=transfer_z,
        mode="lines",
        line=dict(color="red", width=4),
        name="Resource Transfer"
    ))

    fig.update_layout(
        title="Interplanetary Supply Chain Simulation",
        scene=dict(
            xaxis=dict(title="X-axis"),
            yaxis=dict(title="Y-axis"),
            zaxis=dict(title="Z-axis"),
        ),
        margin=dict(l=0, r=0, b=0, t=30),
    )
    fig.show()

# Example usage
if __name__ == "__main__":
    visualize_supply_chain()
