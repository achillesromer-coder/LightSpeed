import numpy as np
import pyvista as pv
from pyvistaqt import BackgroundPlotter
import threading
import time

# Window configuration
plotter = BackgroundPlotter()
plotter.window_size = [1280, 720]
plotter.set_background("black")
plotter.add_text("Quantum Foam Simulation", font_size=10)

# Simulation dimensions
nx, ny, nz = 80, 80, 80
x = np.linspace(-1, 1, nx)
y = np.linspace(-1, 1, ny)
z = np.linspace(-1, 1, nz)
X, Y, Z = np.meshgrid(x, y, z, indexing="ij")

# Raphael-like synthetic energy distribution equation
def raphael_equation(x, y, z, t):
    f = np.sin(10 * np.pi * x + t) * np.cos(10 * np.pi * y + t)
    G = np.exp(-((x ** 2 + y ** 2 + z ** 2) * 10)) * np.sin(t)
    psi_4 = np.sin(2 * np.pi * z + t)
    psi_5 = np.cos(2 * np.pi * (x + y + z) + t)
    return f + G + psi_4 + psi_5

# Initial values
t = 0.0
dt = 0.1
base_blobs = raphael_equation(X, Y, Z, t)

# Create structured grid
grid = pv.StructuredGrid()
grid.points = np.c_[X.ravel(order="F"), Y.ravel(order="F"), Z.ravel(order="F")]
grid.dimensions = np.array(base_blobs.shape)  # (nx, ny, nz)
grid.point_data["values"] = base_blobs.flatten(order="F")

# Volume rendering
actor = plotter.add_volume(grid, scalars="values", cmap="coolwarm", opacity="sigmoid", shade=True)

# Camera controls
def move_camera(direction):
    pos = plotter.camera_position[0]
    if direction == "w":
        plotter.camera_position = [(pos[0], pos[1], pos[2] + 0.05), *plotter.camera_position[1:]]
    elif direction == "s":
        plotter.camera_position = [(pos[0], pos[1], pos[2] - 0.05), *plotter.camera_position[1:]]
    elif direction == "a":
        plotter.camera_position = [(pos[0] - 0.05, pos[1], pos[2]), *plotter.camera_position[1:]]
    elif direction == "d":
        plotter.camera_position = [(pos[0] + 0.05, pos[1], pos[2]), *plotter.camera_position[1:]]
    elif direction == "Left":
        plotter.camera.azimuth(-5)
    elif direction == "Right":
        plotter.camera.azimuth(5)
    elif direction == "Up":
        plotter.camera.elevation(5)
    elif direction == "Down":
        plotter.camera.elevation(-5)

for key in ["w", "a", "s", "d", "Up", "Down", "Left", "Right"]:
    plotter.add_key_event(key, lambda key=key: move_camera(key))

# Live update loop
def live_update():
    global t
    while plotter.app_running:
        t += dt
        updated = raphael_equation(X, Y, Z, t)
        grid.point_data["values"] = updated.flatten(order="F")
        actor.prop.mapper.scalar_range = [updated.min(), updated.max()]
        time.sleep(0.05)

threading.Thread(target=live_update, daemon=True).start()

# Export functionality
def export_video():
    print("[INFO] Exporting simulation to quantum_foam_loop.mp4...")
    plotter.open_movie("quantum_foam_loop.mp4", framerate=24)
    for _ in range(96):  # ~4 seconds at 24 FPS
        plotter.write_frame()
        plotter.update()
        time.sleep(1 / 24)
    plotter.close()

plotter.add_key_event("e", export_video)
plotter.add_text("Press 'E' to export 4s loop as MP4", position="lower_right", font_size=8)

# Start the UI
plotter.show()
