import numpy as np
import plotly.graph_objects as go

def generate_quantum_fluctuations(num_points=1000):
    """
    Simulates quantum fluctuations at the Planck scale.
    """
    x = np.random.normal(0, 1, num_points) * 1e-35  # Planck length perturbations
    y = np.random.normal(0, 1, num_points) * 1e-35
    z = np.random.normal(0, 1, num_points) * 1e-35
    energy_density = np.random.normal(0, 1, num_points) ** 2  # Random energy fluctuations

    return x, y, z, energy_density

def visualize_quantum_fluctuations(num_points=1000):
    """
    Visualizes quantum fluctuations using a 3D scatter plot.
    """
    x, y, z, energy_density = generate_quantum_fluctuations(num_points)

    fig = go.Figure(data=go.Scatter3d(
        x=x, y=y, z=z,
        mode='markers',
        marker=dict(size=3, color=energy_density, colorscale='Viridis', opacity=0.7),
    ))
    fig.update_layout(
        title="Quantum Fluctuations",
        scene=dict(
            xaxis=dict(title="X (Planck Length)"),
            yaxis=dict(title="Y (Planck Length)"),
            zaxis=dict(title="Z (Planck Length)"),
            bgcolor="black"
        ),
        paper_bgcolor="black",
        font=dict(color="white")
    )
    fig.show()

# Example usage
if __name__ == "__main__":
    visualize_quantum_fluctuations()
