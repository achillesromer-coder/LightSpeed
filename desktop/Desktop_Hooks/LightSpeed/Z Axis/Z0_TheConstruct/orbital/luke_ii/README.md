# Luke II v1.3 — serviceable reference assembly

This directory is the executable Luke/Luke II closure source under the existing `Z0_TheConstruct/orbital` authority. It expands the prior 96-node reference into a panelised, internally connected and maintainability-audited configuration before Mark III execution.

## Current task gate

- GitHub issue: https://github.com/achillesromer-coder/LightSpeed/issues/31
- Draft PR: https://github.com/achillesromer-coder/LightSpeed/pull/30
- Canonical Twin file ID: `1BGwPdfafqVKwh3AS5fwvkhIImBmfPdMU`
- Required sequencing: close Luke interactive/CAD review first; begin Mark III decomposition only after acceptance.

## Source reconciliation

The geometry reconciles the existing Luke/Luke II/Apostle Twin with the Solar Hull, Free Flow solenoid, battery and capacitor packages and the Mark III modular hardware Twin. The four owner-supplied Blender views are treated as external-form references, not dimensional evidence.

Vocabulary remains locked:

- **Luke** — macro/logistics field architecture;
- **Luke II** — telemetry/refinement node;
- **Apostle** — local shielding/stabilisation;
- **Mark III** — upstream modular/linkable field-control platform.

## v1.3 configuration

The generated 1:1 assembly contains **1,357 named nodes**, including:

- 162 physical solar-hull panels plus 30 window apertures distributed over the 16 × 12 panel grid;
- 120 pressure-window layers and 120 serviceable frame parts;
- pressure and service liners, primary attachment frames and removable internal linings;
- 25 connected walkway segments with corresponding egress paths;
- 24 bulkhead parts with open doorway continuity;
- 32 cable-tray segments, component harnesses, connector access and bend-space reservations;
- 265 service-clearance envelopes and 227 removal paths;
- attached field, sensor, resonator, capacitor, battery, damping and habitation references;
- a 23-node Mark III interface-arm decomposition covering collar, joints, links, actuators, end effector and cable chain.

The living-quarter window band follows the owner-defined clock regions and includes three outer transparent layers, an inner pressure pane, frame geometry, service clearance and removal-path references. No transparent pressure-vessel qualification is implied.

## Reproduce and qualify

```bash
python -m pip install -r requirements.txt
python -m unittest discover -v -s . -p "test_luke_ii*.py"
python luke_ii_parametric.py --parameters luke_ii_parameters.json --out-dir generated
python luke_ii_dimensional_audit.py --parameters luke_ii_parameters.json --out-dir generated
python luke_ii_serviceability_audit.py --parameters luke_ii_parameters.json --out-dir generated
python luke_ii_glb_roundtrip_audit.py \
  --parameters luke_ii_parameters.json \
  --glb generated/luke_ii_assembly.glb \
  --output generated/luke_ii_glb_roundtrip_audit.json
python luke_ii_interactive.py \
  --glb generated/luke_ii_assembly.glb \
  --manifest generated/luke_ii_component_manifest.json \
  --parameters luke_ii_parameters.json \
  --verification generated/luke_ii_verification.json \
  --serviceability generated/luke_ii_serviceability_audit.json \
  --roundtrip generated/luke_ii_glb_roundtrip_audit.json \
  --output generated/luke_ii_interactive.html
```

## Acceptance state

- 16/16 local tests passed;
- 1,357/1,357 source nodes watertight and winding-consistent;
- semantic geometry SHA-256: `1e58a8e6c5643c4d7d6320de5740b5451a7919259c9aa7d886285ea9f8a3bf8a` at `1e-8 m` quantisation;
- serviceability audit: `PASS_SERVICEABILITY_REFERENCE_AUDIT`;
- attachment, cable-route, clearance and removal-path graphs resolve;
- walkway maximum centre gap: `0.942236 m` against the `1.05 m` reference limit;
- exported GLB round-trip: 1,357/1,357 node identities and topology counts matched;
- four watertight display-print references fit a 280 mm envelope.

The interactive HTML provides layer toggles, component search, selection details, evidence states, explode control, clipping cutaways, spatial allocations and open-gap review. It loads Three.js modules from a CDN and therefore requires network access for the viewer library; the geometry and review data are embedded.

## Print-reference scope

- full shell: 1:100;
- representative panel: 1:20;
- representative window/frame: 1:20;
- Mark III interface arm: 1:20.

These are display, assembly-planning and spatial-review references only. They are not manufacturing releases. Fasteners, inserts, materials, tolerances, loads, cable gauges and qualified interfaces remain open.

## Claim boundaries

This model is not flight certified, human rated, pressure-vessel certified, electrically or thermally qualified, or released for manufacture. It does not validate payload capture, controlled return, field strength, current, shielding, damping, gas handling, life support, docking loads or Mark III arm performance. Legacy million-ampere and five-tesla values remain quarantined.

## Drive discipline

The workbook in the controlled package is an **in-place replacement candidate** for the existing canonical file ID. Do not upload it as a parallel authoritative Twin. The same-ID update remains dependent on file-specific Drive app authorisation and must be followed by raw read-back verification.
