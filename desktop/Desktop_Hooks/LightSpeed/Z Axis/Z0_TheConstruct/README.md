# TheConstruct Floor

**Z-Level:** 0
**Version:** 5.1.2
**Status:** Active smart floor

TheConstruct owns LightSpeed holospace, scenario labs, scientific calculators,
simulation presets, heliocentric zoning outputs, and GMAT target-batch artifacts.
The active UI coordinator is the root floor module `Z Axis/TheConstruct.py`; this
folder holds the owned components, libraries, and generated lab state.

## Canonical Ownership

- `components/`: holospace dashboards, 3D visualization, and project workspace panels.
- `data/labs/`: scenario-lab runs, knowns promoted into simulation context, and simulation presets.
- `physics_calculators.py`: active Raphael-style physics calculator library used by the Construct UI and Trinity context actions.
- `dimensions_library.py`: physical-dimension and unit reference library.
- `tools/`: floor-local dependency and component-linking utilities kept for bounded Construct operations.

## Current Runtime Flow

Oracle supplies proofed knowns and empirical anchors. Neo proposes bounded simulation
projects through Achilles. TheConstruct builds or previews scenario runs, and
Architect packages approved artifacts for publish. Smith handles queued execution
state when simulation work is staged rather than run immediately.

## Reduction Policy

Do not add duplicate floor-local entrypoints here. Add new user-facing behavior to
the root coordinator or runtime bridge first, then keep floor-local files focused on
libraries, components, presets, and owned lab data.
