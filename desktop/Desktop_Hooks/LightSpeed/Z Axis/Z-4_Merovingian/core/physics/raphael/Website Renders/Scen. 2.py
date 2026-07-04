import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import rcParams

# === Raphael-inspired Path Function ===
def raphael_path(t, seed=0):
    np.random.seed(seed)
    a = 0.3 + 0.1 * np.random.rand()
    b = 0.2 + 0.1 * np.random.rand()
    c = 0.4 + 0.1 * np.random.rand()
    x = np.sin(a * t) + np.cos(b * t)
    y = np.sin(b * t + 1) + np.cos(c * t + 0.5)
    z = np.sin(c * t + 2) + np.cos(a * t)
    return x, y, z

def generate_cloud(center, scale=0.25, count=100):
    return center + np.random.normal(scale=scale, size=(count, 3))

# === Observer System Configuration ===
observer_nodes = [
    {"size": 1.0, "seed": 1}, {"size": 2/3, "seed": 2}, {"size": 2/3, "seed": 3},
    {"size": 1/3, "seed": 4}, {"size": 1/3, "seed": 5}, {"size": 1/3, "seed": 6},
    {"size": 1/4, "seed": 7}, {"size": 1/4, "seed": 8}, {"size": 1/4, "seed": 9},
    {"size": 1/4, "seed": 10}, {"size": 1/4, "seed": 11}, {"size": 1/4, "seed": 12},
    {"size": 1/5, "seed": 13}, {"size": 1/5, "seed": 14}, {"size": 1/5, "seed": 15},
    {"size": 1/5, "seed": 16}, {"size": 1/5, "seed": 17}, {"size": 1/5, "seed": 18},
]

fig = plt.figure(figsize=(12, 10))
ax = fig.add_subplot(111, projection='3d')
plt.style.use("dark_background")
ax.set_xlim(-10, 10)
ax.set_ylim(-10, 10)
ax.set_zlim(-10, 10)
ax.set_title("Raphael N-Body System: Observer Entanglement", fontsize=14)

trajectories = []
clouds = []

for node in observer_nodes:
    traj_line, = ax.plot([], [], [], lw=2 * node["size"], alpha=0.9)
    cloud = ax.scatter([], [], [], s=15 * node["size"], alpha=0.4, color='aqua')
    trajectories.append({"line": traj_line, "data": [], "seed": node["seed"], "scale": node["size"]})
    clouds.append(cloud)

def update(frame):
    t = frame * 0.15
    for i, obj in enumerate(trajectories):
        x, y, z = raphael_path(t, obj["seed"])
        obj["data"].append([x, y, z])
        if len(obj["data"]) > 100:
            obj["data"].pop(0)

        data_np = np.array(obj["data"])
        obj["line"].set_data(data_np[:, 0], data_np[:, 1])
        obj["line"].set_3d_properties(data_np[:, 2])

        center = np.array([x, y, z])
        cloud_points = generate_cloud(center, scale=0.2 * obj["scale"], count=30)
        clouds[i]._offsets3d = (cloud_points[:, 0], cloud_points[:, 1], cloud_points[:, 2])

    return [obj["line"] for obj in trajectories] + clouds

ani = FuncAnimation(fig, update, frames=300, interval=40, blit=False)

# === Optional Export ===
EXPORT = False  # Set True if you want export
EXPORT_FORMAT = "mp4"  # or 'gif'
EXPORT_FILENAME = f"raphael_scenario2.{EXPORT_FORMAT}"
FPS = 24

if EXPORT:
    if EXPORT_FORMAT == "gif":
        writer = PillowWriter(fps=FPS)
    else:
        rcParams['animation.ffmpeg_path'] = 'ffmpeg'
        writer = FFMpegWriter(fps=FPS)
    ani.save(EXPORT_FILENAME, writer=writer)
    print(f"Exported as {EXPORT_FILENAME}")

plt.show()
