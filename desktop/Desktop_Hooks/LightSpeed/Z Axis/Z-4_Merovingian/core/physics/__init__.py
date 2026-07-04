"""
LightSpeed Physics Engine
Type I Civilization Platform

Provides advanced physics simulations including:
- Raphael wavefunction reflection calculations
- Light reflectivity and refraction
- Spacetime simulations
- Atomic transitions
- Fractal expansions
- Holographic simulations
- Ecosystem modeling

Author: LightSpeed Team / ACHILLES
Version: 0.9.5
"""

try:
    from .raphael import (
        RaphaelPhysicsEngine,
        WavefunctionCalculator,
        LightReflectivityEngine,
        SpacetimeSimulation,
        get_raphael_engine
    )
    HAS_RAPHAEL = True
except ImportError:
    HAS_RAPHAEL = False
    RaphaelPhysicsEngine = None
    WavefunctionCalculator = None
    LightReflectivityEngine = None
    SpacetimeSimulation = None
    get_raphael_engine = None

__version__ = "0.9.5"
__author__ = "LightSpeed Team / ACHILLES"

__all__ = [
    'RaphaelPhysicsEngine',
    'WavefunctionCalculator',
    'LightReflectivityEngine',
    'SpacetimeSimulation',
    'get_raphael_engine',
    'HAS_RAPHAEL',
]
