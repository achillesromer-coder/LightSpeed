"""
Z0_TheConstruct GUI Package
Primary 3D immersive interface components

This package contains the unified immersive interface that serves as the
PRIMARY entry point for LightSpeed's 3D environment.
"""

from .immersive_n_integrated import (
    launch_immersive,
    UnifiedImmersiveInterface
)

__all__ = [
    'launch_immersive',
    'UnifiedImmersiveInterface'
]

__version__ = '1.0.0'
