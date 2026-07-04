
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D

# Parameters
grid_size = 500
time_steps = 1000
scale = 3.0

# Raphael Equation-inspired Field Function
def raphael_quantum_fluctuations(x, y, z, t):
    return (np.sin(scale * x * np.cos(t)) +
            np.sin(scale * y * np.sin(t)) +
            np.sin(scale * z * np.cos(t)) +
            np.cos(scale * x * y * z * np.sin(t))) * np.exp(-0.05 * (x**2 + y**2 + z**2))

# Create 3D grid
x = np.linspace(-1, 1, grid_size)
y = np.linspace(-1, 1, grid_size)
z = np.linspace(-1, 1, grid_size)
X, Y, Z = np.meshgrid(x, y, z, indexing="ij")

# Initial field state
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Normalize function
def normalize_field(field):
    return (field - np.min(field)) / (np.max(field) - np.min(field))

# Update function for animation
def update(frame):
    ax.clear()
    t = frame * np.pi * 2 / time_steps
    field = raphael_quantum_fluctuations(X, Y, Z, t)
    field = normalize_field(field)

    threshold = 0.6
    x_vis = X[field > threshold]
    y_vis = Y[field > threshold]
    z_vis = Z[field > threshold]
    color_vals = field[field > threshold]

    img = ax.scatter(x_vis, y_vis, z_vis, c=color_vals, cmap=cm.coolwarm, s=1, alpha=0.9)
    ax.set_title(f"Quantum Foam Field – Raphael Equation\nTime = {frame}")
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_zlim(-1, 1)
    return img,

ani = FuncAnimation(fig, update, frames=time_steps, interval=100)

# Save to file
ani.save("quantum_foam_raphael_equation.mp4", fps=24)

plt.show()
