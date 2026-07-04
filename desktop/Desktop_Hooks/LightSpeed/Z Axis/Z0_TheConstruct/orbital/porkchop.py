
# Imports

import matplotlib.pyplot
import numpy
import os


# ===== CONSOLIDATED FROM 3 FILES =====

# Merged on: 2025-11-21 17:46:26

# Source files: 3


import os, numpy as np, matplotlib.pyplot as plt
OUT=os.path.join(os.path.dirname(__file__),"..","out"); os.makedirs(OUT,exist_ok=True)
x=np.linspace(0,1,240); y=np.linspace(0,1,240); X,Y=np.meshgrid(x,y); Z=(X-0.3)**2+(Y-0.6)**2+0.2*np.sin(10*X)*np.cos(8*Y)
CS=plt.contour(X,Y,Z,18); plt.clabel(CS, inline=1, fontsize=8); plt.xlabel("Launch window"); plt.ylabel("Arrival window"); plt.title("Demo Porkchop"); plt.tight_layout()
plt.savefig(os.path.join(OUT,"porkchop_demo.png")); plt.close(); print("ok: porkchop_demo.png")