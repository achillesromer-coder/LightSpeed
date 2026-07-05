"""
Simulation Systems
LightSpeed Platform - TheConstruct Floor (Z0)

Mark series simulations for asteroid extraction and mission planning:
- Mark III: Small-scale extraction unit with fluid dynamics
- Mark V: Large-scale extraction with asteroid attachment
- Extraction.run: RFS/EMFF extraction simulation with CFD
- Launch.run: Launch trajectory and mission simulation

These simulations integrate with Cognigrex AI for training and optimization.
"""

from .mark3 import Mark3Simulator

# Additional simulators to be implemented:
# from .mark5 import Mark5Simulator
# from .extraction import ExtractionSimulator
# from .launch import LaunchSimulator

__all__ = [
    'Mark3Simulator',
    # 'Mark5Simulator',
    # 'ExtractionSimulator',
    # 'LaunchSimulator',
]
