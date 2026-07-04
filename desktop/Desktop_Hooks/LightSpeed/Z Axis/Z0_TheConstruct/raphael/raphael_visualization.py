
# Imports

from matplotlib.widgets import Button
from matplotlib.widgets import CheckButtons
from matplotlib.widgets import Slider
import matplotlib.pyplot
import numpy


# ===== CONSOLIDATED FROM 4 FILES =====

# Merged on: 2025-11-21 17:46:25

# Source files: 4


import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, CheckButtons

# --- Helper Functions ---
def plot_quantum_decoherence(ax, curvature_intensity=0.1):
    x = np.linspace(-10, 10, 400)
    t = np.linspace(0, 2 * np.pi, 200)
    X, T = np.meshgrid(x, t)
    curvature = curvature_intensity * np.sin(0.5 * X)
    wavefunction = np.sin(X - T) * np.exp(-0.1 * X**2)
    distorted_wavefunction = wavefunction * (1 + curvature)
    ax.clear()
    ax.set_title('Quantum Decoherence due to Spacetime Curvature')
    ax.set_xlabel('Position (x)')
    ax.set_ylabel('Time (t)')
    ax.set_zlabel('Wavefunction Amplitude')
    ax.plot_surface(X, T, distorted_wavefunction, cmap='viridis', edgecolor='none')

def plot_plasma_turbulence(ax, coherence_ratio=0.7):
    np.random.seed(42)
    n_particles = 300
    x = np.random.rand(n_particles) * 10 - 5
    y = np.random.rand(n_particles) * 10 - 5
    for _ in range(100):
        vx1, vy1 = -y / (np.sqrt(x**2 + y**2) + 1e-3), x / (np.sqrt(x**2 + y**2) + 1e-3)
        vx2, vy2 = np.sin(y) + 0.5 * np.random.randn(len(x)), np.cos(x) + 0.5 * np.random.randn(len(y))
        vx = coherence_ratio * vx1 + (1 - coherence_ratio) * vx2
        vy = coherence_ratio * vy1 + (1 - coherence_ratio) * vy2
        x += vx * 0.1
        y += vy * 0.1
    ax.clear()
    ax.scatter(x, y, color='red', s=10, label='Particles')
    ax.set_title('Plasma Turbulence (Coherent vs Turbulent Flow)')
    ax.set_xlabel('x-axis (Position)')
    ax.set_ylabel('y-axis (Position)')

def plot_galactic_rotation(ax, dark_matter_influence=0.3):
    radii = np.linspace(0.1, 20, 400)
    observed_velocity = 1 / np.sqrt(radii + 1) + 0.4
    predicted_velocity = np.sqrt(1 / radii + dark_matter_influence) + 0.3
    ax.clear()
    ax.plot(radii, observed_velocity, label='Observed Rotation', color='red')
    ax.plot(radii, predicted_velocity, label='Predicted (4D Coherence)', color='blue', linestyle='dashed')
    ax.fill_between(radii, observed_velocity, predicted_velocity, color='lightgrey', alpha=0.5, label='Deviation Region')
    ax.set_title('Galactic Rotation Curve')
    ax.set_xlabel('Distance from Galactic Center')
    ax.set_ylabel('Rotation Velocity')
    ax.legend()

def plot_cosmic_expansion(ax, expansion_rate=0.2):
    time_steps = 10
    radii = [1 * (1 + expansion_rate * t) for t in range(time_steps)]
    theta = np.linspace(0, 2 * np.pi, 100)
    ax.clear()
    for radius in radii:
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        ax.plot(x, y, linestyle='dashed', linewidth=2)
    ax.set_title('Accelerated Cosmic Expansion (5D Expansive Field)')
    ax.set_xlabel('X-axis (Cosmic Distance)')
    ax.set_ylabel('Y-axis (Cosmic Distance)')
    ax.set_aspect('equal', adjustable='box')

# --- Main Interactive Application ---
def interactive_visualization():
    fig, ax = plt.subplots(2, 2, figsize=(15, 10))
    plt.subplots_adjust(left=0.1, bottom=0.3)

    # Initial Plots
    plot_quantum_decoherence(ax[0, 0])
    plot_plasma_turbulence(ax[0, 1])
    plot_galactic_rotation(ax[1, 0])
    plot_cosmic_expansion(ax[1, 1])

    # Create Sliders for Interactivity
    ax_curvature = plt.axes([0.15, 0.15, 0.65, 0.03])
    curvature_slider = Slider(ax_curvature, 'Curvature Intensity', 0.05, 0.5, valinit=0.1)

    ax_coherence = plt.axes([0.15, 0.10, 0.65, 0.03])
    coherence_slider = Slider(ax_coherence, 'Coherence Ratio', 0.1, 0.9, valinit=0.7)

    ax_dark_matter = plt.axes([0.15, 0.05, 0.65, 0.03])
    dark_matter_slider = Slider(ax_dark_matter, 'Dark Matter Influence', 0.1, 0.5, valinit=0.3)

    ax_expansion = plt.axes([0.15, 0.02, 0.65, 0.03])
    expansion_slider = Slider(ax_expansion, 'Expansion Rate', 0.05, 0.5, valinit=0.2)

    # Update Functions for Sliders
    def update(val):
        plot_quantum_decoherence(ax[0, 0], curvature_slider.val)
        plot_plasma_turbulence(ax[0, 1], coherence_slider.val)
        plot_galactic_rotation(ax[1, 0], dark_matter_slider.val)
        plot_cosmic_expansion(ax[1, 1], expansion_slider.val)
        fig.canvas.draw_idle()

    # Attach the update function to the sliders
    curvature_slider.on_changed(update)
    coherence_slider.on_changed(update)
    dark_matter_slider.on_changed(update)
    expansion_slider.on_changed(update)

    # Add reset button
    reset_ax = plt.axes([0.8, 0.01, 0.1, 0.04])
    reset_button = Button(reset_ax, 'Reset')

    def reset(event):
        curvature_slider.reset()
        coherence_slider.reset()
        dark_matter_slider.reset()
        expansion_slider.reset()

    reset_button.on_clicked(reset)

    plt.show()

# Run the interactive visualization
if __name__ == "__main__":
    interactive_visualization()
