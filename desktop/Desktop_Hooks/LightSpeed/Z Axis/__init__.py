#!/usr/bin/env python
"""
LightSpeed Z Axis ownership map.

This file is a compact compatibility map for tooling that inspects the
`Z Axis` folder directly. Runtime loading is owned by Merovingian's floor
loader and the root floor coordinator files, not by importing this folder as a
normal Python package.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

__version__ = "5.1.2"

Z_AXIS_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class FloorConfig:
    """Canonical Z-axis floor contract."""

    key: str
    name: str
    z_level: int
    owner_role: str
    entrypoint: str
    data_root: str


FLOORS: dict[str, FloorConfig] = {
    "Z+3_Trinity": FloorConfig(
        key="Z+3_Trinity",
        name="Trinity",
        z_level=3,
        owner_role="Operator portal, setup, settings, and glass/bento UI contracts",
        entrypoint="Trinity.py",
        data_root="Z+3_Trinity/data",
    ),
    "Z+2_Neo": FloorConfig(
        key="Z+2_Neo",
        name="Neo",
        z_level=2,
        owner_role="Neo orchestration console and approval-gated AI actions with Achilles oversight routed from De Sporte",
        entrypoint="Neo.py",
        data_root="Z+2_Neo/data",
    ),
    "Z+1_Architect": FloorConfig(
        key="Z+1_Architect",
        name="Architect",
        z_level=1,
        owner_role="Governance, publish bundles, approvals, and finalization queues",
        entrypoint="Architect.py",
        data_root="Z+1_Architect/data",
    ),
    "Z0_TheConstruct": FloorConfig(
        key="Z0_TheConstruct",
        name="TheConstruct",
        z_level=0,
        owner_role="Holospace, simulations, zoning runs, and scenario labs",
        entrypoint="TheConstruct.py",
        data_root="Z0_TheConstruct/data",
    ),
    "Z-1_Morpheus": FloorConfig(
        key="Z-1_Morpheus",
        name="Morpheus",
        z_level=-1,
        owner_role="Review, proofing, code/document analysis, and curated previews",
        entrypoint="Morpheus.py",
        data_root="Z-1_Morpheus/data",
    ),
    "Z-2_Oracle": FloorConfig(
        key="Z-2_Oracle",
        name="Oracle",
        z_level=-2,
        owner_role="Knowledge catalog, empirical libraries, knowns, datatables, and provenance",
        entrypoint="Oracle.py",
        data_root="Z-2_Oracle/data",
    ),
    "Z-3_Smith": FloorConfig(
        key="Z-3_Smith",
        name="Smith",
        z_level=-3,
        owner_role="Job router, workflow state, tool execution gateway, and automation",
        entrypoint="Smith.py",
        data_root="Z-3_Smith/data",
    ),
    "Z-4_Merovingian": FloorConfig(
        key="Z-4_Merovingian",
        name="Merovingian",
        z_level=-4,
        owner_role="Database, telemetry, compact activity tables, diagnostics, and audit evidence",
        entrypoint="Merovingian.py",
        data_root="Z-4_Merovingian/data",
    ),
}


def get_floor(key_or_name: str) -> Optional[FloorConfig]:
    """Return a floor by canonical key or display name."""
    needle = key_or_name.lower()
    for key, floor in FLOORS.items():
        if key.lower() == needle or floor.name.lower() == needle:
            return floor
    return None


def active_entrypoints() -> dict[str, Path]:
    """Return root-level floor coordinator entrypoints."""
    return {key: Z_AXIS_ROOT / floor.entrypoint for key, floor in FLOORS.items()}


__all__ = ["FLOORS", "FloorConfig", "Z_AXIS_ROOT", "active_entrypoints", "get_floor"]
