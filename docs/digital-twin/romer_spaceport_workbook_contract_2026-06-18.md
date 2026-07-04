# Römer Spaceport Digital Twin Workbook Contract - 2026-06-18

This contract keeps the Squarespace/LS Go embed and the workbook aligned. The public surface should read a workbook export in this shape rather than hard-coding future facility detail.

## Workbook Tabs

- `site_zones`: radial zones, center point, radius, restoration mode, and public label.
- `facilities`: building/pad records, footprint, elevation, foundation rule, release status, and route page slug.
- `rooms_spaces`: room-level records keyed to `facility_id`, floor, function, dimensions, and access class.
- `roads_tracks`: charcoal road geometry, dotted centerline rules, ChainHill tracks, and crane-assist notes.
- `pads_exhaust`: pad type, hardstand diameter, tower/flame-trench notes, exhaust direction, and unresolved safety offsets.
- `eco_restoration`: internal gardens, active band biome pockets, passive restoration sectors, and monitoring notes.
- `standards_evidence`: cited standards, evidence source, applicability, status, reviewer, and approval gate.
- `viewer_toggles`: palette mode, grid visibility, label density, and touch/mouse control defaults.
- `known_unknowns`: unresolved values such as runway orientation, water volume, Falcon pad dimensions, and propellant offsets.

## Frontend Contract

- The LS Go embed exposes one simplified site-twin panel, not a separate page forest.
- The top-level viewer shows radial zones, X-layout pads, roads, ChainHill, mission control, and status summaries.
- Per-building pages can be generated later from `facilities` and `rooms_spaces`, but must remain data-driven.
- Safety-critical values remain `known-unknown` until reviewed; the UI should label them as such instead of presenting false precision.

