# Mark III v0.2 — serviceable modular reference assembly

This directory is the executable source for the Mark III modular/linkable reference under the existing `Z0_TheConstruct` authority. It is stacked above the sealed Luke II branch to preserve interface lineage and does not create a second design master.

## Canonical authority

- Canonical Twin: `Mark_III_Digital_Twin_v0_1.xlsx`
- Canonical Drive file ID: `1-6Jxye14_pQICcu_WxFmZIxnE2pDfHS2`
- GitHub issue: `#32`
- Implementation branch: `execution/mark-iii-serviceable-reference-2026-08-05`
- Base lineage: Luke II sealed commit `4cbba640bf8f1589f542ec164016c4f39b4c85e1`

The workbook in the controlled package is an **in-place replacement candidate**. It must not be uploaded as a parallel authoritative Twin.

## Source-reconciled configuration

The v0.2 reference preserves the Mark III v0.1 source envelope and source component topology:

- canonical module: `0.75 m × Ø0.32 m`;
- provisional source wall: `0.006 m`;
- six angular shell sectors, implemented as 18 replaceable structural panels and six continuous Solar Hull skin sectors;
- front and rear coupling rings with eight source-aligned latches total, alignment keys and power/data bridge references;
- central process tunnel and removable sample cartridge;
- six compact spatial-reference solenoid cartridges;
- four resonator cartridges;
- two capacitor bays, one battery/BMS bay and one controller/DSP bay;
- eight sensor nodes, four damping placeholders and one comms interface;
- four cable trays and routed harness trunks with connector access, bend-space and strain-relief reservations;
- two articulated service/deployment arms with joints, links, actuator housings, spool/tendon interfaces, cable chain and removal envelopes;
- selectable 1-, 2-, 4-, 8- and 18-module array guides.

The six compact solenoid cartridges are a recorded spatial resolution of a source conflict: the Free Flow Mark III scenario's `0.16 m` solenoid length cannot be placed six times axially inside the `0.75 m` module while preserving couplers and service space. The scenario value remains quarantined pending measured BOM and integration evidence.

## Local qualification

```bash
python -m pip install -r requirements.txt
python -m unittest discover -v -s . -p "test_mark_iii*.py"
python mark_iii_parametric.py --parameters mark_iii_parameters.json --out-dir generated
python mark_iii_dimensional_audit.py --parameters mark_iii_parameters.json --out-dir generated
python mark_iii_serviceability_audit.py --parameters mark_iii_parameters.json --out-dir generated
python mark_iii_glb_roundtrip_audit.py \
  --parameters mark_iii_parameters.json \
  --glb generated/mark_iii_assembly.glb \
  --output generated/mark_iii_glb_roundtrip_audit.json
python mark_iii_interactive.py \
  --glb generated/mark_iii_assembly.glb \
  --manifest generated/mark_iii_component_manifest.json \
  --parameters mark_iii_parameters.json \
  --verification generated/mark_iii_verification.json \
  --serviceability generated/mark_iii_serviceability_audit.json \
  --roundtrip generated/mark_iii_glb_roundtrip_audit.json \
  --output generated/mark_iii_interactive.html
```

Current controlled local result:

- tests: `17 / 17` passed;
- named nodes: `339`;
- physical nodes: `192`;
- source module envelope: `0.75 × 0.32 × 0.32 m`;
- source nodes watertight/winding-consistent: `339 / 339`;
- serviceability: `PASS_SERVICEABILITY_REFERENCE_AUDIT`;
- GLB round-trip: `339 / 339` node identities and topology counts matched;
- semantic geometry SHA-256: `8ff2f295d0bebdd9cfb45c1942bda6dfe8dfd6493d7d9861fb97bf91458c2303`;
- canonical component-manifest SHA-256: `9f95b1c5a6e552a626f50a9e2448f45a2cfb8642e65f92b904f0211fee64d813`.

## Interactive review

`mark_iii_interactive.html` embeds the GLB and review data and provides:

- component search and selection metadata;
- evidence-state and subsystem layer toggles;
- exploded view;
- X/Y/Z clipping cutaways;
- transparent service, connector, cable-bend and removal envelopes;
- selectable 1/2/4/8/18 module array guides;
- explicit source conflicts and known unknowns.

Three.js modules load from a CDN, so the viewer library requires network access. Geometry and review data are embedded.

## Print-reference scope

- full module: `1:5`;
- representative panel: `1:3`;
- coupler: `1:2`;
- solenoid cartridge: `1:1`;
- arm assembly: `1:2`.

These are display, spatial-review and assembly-planning references only. They are not manufacturing releases.

## Claim boundaries

No validated extraction/separation performance, field strength, current, efficiency, energy safety, pressure/vacuum safety, thermal performance, human rating, flight readiness, payload handling, arm torque/load/reach, deployment, manufacturing release or public capability promotion is authorized.
