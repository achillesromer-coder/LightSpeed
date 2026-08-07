# Mark III v0.3.3 — original-layout print, plating and propulsion-interface development reference

This directory supersedes v0.3.2 **for current design review** after a closure sweep against the owner-supplied original Mark III drawing. v0.3.3 retains the qualified bilateral body/arm architecture, multifunction resonator matrix and manufacturing-development controls, and closes two omissions: the source drawing's propulsion/refillable-reservoir interface callout and a stale PR identifier in the interactive viewer.

## Authority and boundaries

- Canonical Twin: `Mark_III_Digital_Twin_v0_1.xlsx`
- Canonical Drive file ID: `1-6Jxye14_pQICcu_WxFmZIxnE2pDfHS2`
- GitHub issue: `#32`
- Draft stacked PR: `#34`
- Branch: `execution/mark-iii-original-layout-v0.3-2026-08-05`
- Base lineage: sealed Luke II commit `4cbba640bf8f1589f542ec164016c4f39b4c85e1`

The workbook remains an in-place replacement candidate. No parallel authoritative Twin may be created.

## Original-layout configuration

- canonical body envelope preserved at `0.75 m × 0.32 m × 0.32 m`;
- six angular body sectors and three axial print/service zones: 18 removable shell panels;
- upper control/comms, middle energy and lower field/resonator zoning;
- 18 compact body-solenoid envelopes: three per sector;
- 25 replaceable resonator sockets: one central, six surrounding, twelve peripheral and six support;
- two interleaved spiral buses plus Flower-of-Life role bands, enabling A-only, B-only, paired, alternating and swept test configurations;
- isolated control-power allocation, four capacitor-cell envelopes, controller/DSP, sensors, comms and damping placeholders;
- bilateral eight-link segmented arms with spool/motor/lock interfaces, joint placeholders, three quarantined coil references per link, cable chains and collector pads;
- six-segment central probe mast and instrument head;
- eight interlocking coupling latches and 1/2/4/8/18-module illustrative arrays.

### v0.3.3 closure refinements

The original drawing explicitly calls out movement from thrusters plus a refillable fuel reservoir. v0.3.3 restores this **only as non-operational interface/allocation geometry**:

- four external propulsion/attitude-control interface envelopes;
- one internal unpressurised reservoir-allocation envelope;
- one refill/service-port allocation;
- four reservoir-to-interface and one refill-route spatial reservations;
- one printable generic propulsion-interface mount;
- one printable reservoir-cradle reference.

No propellant, pressure, nozzle, valve, feed-system, thrust, impulse, thermal or operational propulsion value is assigned or authorised. These are packaging, routing and servicing references pending a selected propulsion architecture and specialist qualification.

## Print and plating development package

Every shell panel has a pre-plate substrate, nominal plating allowance, mask lands, insert bosses, drain sleeve, assembly datum and service/removal correspondence. The **20-part** reference print kit includes shell/service panels, resonator tray, split sector rail, split solenoid shell, mounts, coupler quadrant, energy/control trays, arm and probe parts, collector pad, propulsion-interface mount, reservoir cradle, witness-coupon tree, alignment/plating jig and display assemblies.

The reference bed is `280 × 280 × 40 mm`; every STL is watertight, winding-consistent and fits by orientation. This is a **manufacturing-development reference**, not a production, pressure-system, propulsion or deployment release.

## Qualification sequence

1. CAD/datum and interface review.
2. Printer, material-lot, raster/wall and mechanical coupon qualification.
3. Serialised article print, pre/post sanding dimensional inspection and insert testing.
4. Sealing/activation/seed/plating qualification on representative witness coupons by a competent external plater.
5. Low-energy subassembly integration with electrical isolation and harness inspection.
6. Inert propulsion-interface fit/routing/service review without pressure or energisation.
7. Structural, mechanism-life, vibration/shock, thermal-vacuum/outgassing, flammability, corrosion, EMI/EMC and low-energy RFS/EMFF testing.

NASA-STD-6030, NASA-STD-6033, NASA-HDBK-5026, ISO/ASTM 52910, ASTM F3529, ECSS-Q-ST-70-02C and applicable NASA material/process standards are planning references only; this package does not claim compliance or certification.

## Local regeneration

```bash
python -m pip install -r requirements.txt
python -m unittest discover -v -s . -p "test_mark_iii*.py"
python mark_iii_parametric.py --parameters mark_iii_parameters.json --out-dir generated
python mark_iii_dimensional_audit.py --parameters mark_iii_parameters.json --out-dir generated
python mark_iii_serviceability_audit.py --parameters mark_iii_parameters.json --out-dir generated
python mark_iii_manufacturing_audit.py --parameters mark_iii_parameters.json --out-dir generated
python mark_iii_glb_roundtrip_audit.py --parameters mark_iii_parameters.json --glb generated/mark_iii_assembly.glb --output generated/mark_iii_glb_roundtrip_audit.json
python mark_iii_interactive.py --glb generated/mark_iii_assembly.glb --manifest generated/mark_iii_component_manifest.json --parameters mark_iii_parameters.json --verification generated/mark_iii_verification.json --serviceability generated/mark_iii_serviceability_audit.json --roundtrip generated/mark_iii_glb_roundtrip_audit.json --manufacturing generated/mark_iii_manufacturing_audit.json --output generated/mark_iii_interactive.html
```

## Qualified invariants

- tests: `21 / 21` passed locally and on the clean GitHub runner;
- named nodes: `786`;
- physical nodes: `486`;
- all nodes watertight and winding-consistent;
- resonators: `25`;
- body solenoids: `18`;
- propulsion interface envelopes: `4`;
- reservoir allocations: `1`;
- print references: `20`;
- GLB round-trip: `786 / 786`;
- semantic geometry SHA-256: `205912a4f248db9a444f30f5b258d78285dc5799e657b684af82e4fe1474a339`;
- canonical component-manifest SHA-256: `7e5638ef12b6d5861c7664c623b54aa485749cb4405a11becdd326339f61ca7e`.

Clean-runner source/workflow qualification passed on Actions run `31135554203` / run `68`, artifact `8977793544`, digest `sha256:521f1b175d6a7aad9ff97079aa70cb220ee237330ac600342bfd081175ebc51d`.

## Release boundary

No validated extraction/separation, resonant material response, field strength, current, energy safety, pressure/gas system, propulsion, thermal performance, EMI/EMC, corrosion life, arm load/torque, structural strength, flight readiness, manufacturing release or deployment approval is authorised.
