"""
Shared category-position defaults for Construct workspaces.

This keeps non-UI layout defaults in one place so the component registry and
the spherical layout bridge do not drift.
"""

from .workspace_creator import SphericalPosition


CATEGORY_DEFAULT_POSITIONS = {
    "system_health": SphericalPosition(0, 30, 0.9),
    "simulation_physics": SphericalPosition(0, 0, 0.8),
    "ai_intelligence": SphericalPosition(45, 0, 0.8),
    "ui_visualization": SphericalPosition(0, -30, 0.9),
    "data_processing": SphericalPosition(-45, 0, 0.7),
    "knowledge_storage": SphericalPosition(180, 0, 0.6),
    "knowledge_discovery": SphericalPosition(-90, 0, 0.7),
    "planning_goals": SphericalPosition(90, 0, 0.7),
    "automation": SphericalPosition(-135, 0, 0.6),
    "monitoring": SphericalPosition(135, 0, 0.6),
}


def get_category_default_position(category: str) -> SphericalPosition:
    """Return a detached default position for the given component category."""
    position = CATEGORY_DEFAULT_POSITIONS.get(category, SphericalPosition(0, 0, 0.7))
    return SphericalPosition(position.theta, position.phi, position.depth)
