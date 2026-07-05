
# Imports

import matplotlib.pyplot
import numpy
import os


# ===== CONSOLIDATED FROM 3 FILES =====

# Merged on: 2025-11-21 17:46:26

# Source files: 3


import os, numpy as np, matplotlib.pyplot as plt
OUT=os.path.join(os.path.dirname(__file__),"..","out"); os.makedirs(OUT,exist_ok=True)
f=np.logspace(1,7,600); resp=np.exp(-((np.log10(f)-5.0)**2)/(2*0.18**2))
plt.semilogx(f,resp); plt.xlabel("Frequency (Hz)"); plt.ylabel("Relative response"); plt.title("Demo Resonance Spectrum"); plt.tight_layout()
plt.savefig(os.path.join(OUT,"demo_resonance.png")); plt.close(); print("ok: demo_resonance.png")