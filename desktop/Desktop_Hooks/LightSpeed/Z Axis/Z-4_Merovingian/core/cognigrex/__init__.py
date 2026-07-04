"""
Cognigrex - Distributed AI System
LightSpeed Platform - Neo Floor (Z+3)

Cognigrex is the distributed AI foundation for space-based operations:
- 4 Subtypes: Collector, Processor, Relay, Surveyor
- Formation configurations: line, wedge, ring, lattice
- Integration with terrestrial AI to form ACHILLES
- Trained in simulations (Mark III/V, Extraction, Launch)
- Distributed storage across space and terrestrial nodes

This module provides:
- Model management and configuration
- Training data tracking
- Fleet coordination
- Multi-AI communication
"""

from .models import CognigrexManager, CognigrexSubtype
from .training import TrainingManager
from .fleet import FleetManager

__all__ = [
    'CognigrexManager',
    'CognigrexSubtype',
    'TrainingManager',
    'FleetManager',
]
