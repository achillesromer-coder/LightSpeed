# Mark III v0.3 — original-layout print and plating development reference

This directory supersedes v0.2.2 **for design review** after reconciliation of the owner-supplied original Mark III drawings and the wider ACHILLES/Römer corpus. The v0.2.2 package remains a valid prior generic-serviceability receipt; v0.3 restores the original bilateral body/arm architecture and original component zoning.

## Authority and boundaries

- Canonical Twin: `Mark_III_Digital_Twin_v0_1.xlsx`
- Canonical Drive file ID: `1-6Jxye14_pQICcu_WxFmZIxnE2pDfHS2`
- GitHub issue: `#32`
- Draft stacked PR: `#33`
- Branch: `execution/mark-iii-serviceable-reference-2026-08-05`
- Base lineage: sealed Luke II commit `4cbba640bf8f1589f542ec164016c4f39b4c85e1`

The workbook is an in-place replacement candidate. No parallel authoritative Twin may be created.

## Restored original-layout configuration

- canonical body envelope preserved at `0.75 m × 0.32 m × 0.32 m`;
- six angular body sectors and three axial print/service zones: 18 removable shell panels;
- original upper control/comms, middle energy and lower field/resonator zoning;
- 18 compact body solenoid envelopes: three per sector;
- 25 replaceable resonator sockets: one central, six surrounding, twelve peripheral and six support;
- two interleaved spiral buses plus Flower-of-Life role bands, enabling A-only, B-only, paired, alternating and swept test configurations;
- isolated control power, four capacitor-cell envelopes in two trays, controller/DSP, sensors, comms and damping placeholders;
- bilateral eight-link segmented arms with spool/motor/lock interfaces, joint placeholders, three quarantined coil references per link, cable chains and octagonal collector pads;
- six-segment central probe mast and instrument head;
- eight interlocking coupling latches and 1/2/4/8/18-module illustrative arrays.

Material-specific resonance, gas/xenon effects, graphene-filled coil effects, field strength and extraction performance are not validated and remain quarantined.

## Print and plating development package

Every shell panel has a pre-plate substrate, nominal plating allowance, mask lands, insert bosses, drain sleeve, assembly datum and service/removal correspondence. The 18-part reference print kit includes shell/service panels, resonator tray, split sector rail, split solenoid shell, mounts, coupler quadrant, energy/control trays, arm and probe parts, collector pad, a witness-coupon tree, alignment/plating jig and display assemblies.

The reference bed is `280 × 280 × 40 mm`; every STL is watertight, winding-consistent and fits by orientation. This is a **manufacturing-development reference**, not a production release.

## Qualification sequence

1. CAD/datum and interface review.
2. Printer, material-lot, raster/wall and mechanical coupon qualification.
3. Serialised article print, pre/post sanding dimensional inspection and insert testing.
4. Sealing/activation/seed/plating qualification on representative witness coupons by a competent external plater.
5. Low-energy subassembly integration with electrical isolation and harness inspection.
6. Structural, mechanism-life, vibration/shock, thermal-vacuum/outgassing, flammability, corrosion, EMI/EMC and low-energy RFS/EMFF testing.

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

## Controlled local invariants

- named nodes: `764`;
- physical nodes: `480`;
- all nodes watertight and winding-consistent;
- resonators: `25`;
- body solenoids: `18`;
- print references: `18`;
- GLB round-trip: `764 / 764`;
- semantic geometry SHA-256: `8ae71a80a820b3a583b2d76c9b75a46a823840109601074e89c262f8ce824205`;
- canonical component-manifest SHA-256: `dfbb3cd373d4f8771d6f3655ec420dbd61a27445b9e5c029e274a51dcc451a3b`.

## Release boundary

No validated extraction/separation, resonant material response, field strength, current, energy safety, pressure/gas system, thermal performance, EMI/EMC, corrosion life, arm load/torque, structural strength, flight readiness, manufacturing release or deployment approval is authorised.
