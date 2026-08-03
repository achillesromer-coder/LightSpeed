# Luke II source-reconciled parametric reference

This directory is the executable geometry source for Luke II under the existing
`Z0_TheConstruct/orbital` authority. It does not create a parallel design master.

## Canonical state

- Canonical Twin: `Luke_LukeII_Apostle_Toroidal_EMF_Digital_Twin_v0_1.xlsx`
- Canonical Drive file ID: `1BGwPdfafqVKwh3AS5fwvkhIImBmfPdMU`
- Geometry status: `PASS_REFERENCE_GEOMETRY`
- Engineering status: reference geometry only; not flight certified, human rated,
  pressure-vessel certified, or released for manufacture

The existing Drive workbook must be replaced in place. Do not upload a duplicate
Twin workbook. The current Drive operation is blocked by file-specific app
write authorisation and is tracked in PR #30.

## Reproduce the reference outputs

From this directory:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -v -s . -p "test_luke_ii*.py"
python luke_ii_parametric.py \
  --parameters luke_ii_parameters.json \
  --out-dir ./generated
python luke_ii_dimensional_audit.py \
  --parameters luke_ii_parameters.json \
  --out-dir ./audit
```

Expected deterministic outputs:

| Output | SHA-256 |
|---|---|
| `luke_ii_assembly.glb` | `3238db7ebf2148786d8060b751825b218eb6b04c44a57adb14f617d40a2fa182` |
| `luke_ii_reference_1to100.stl` | `8f1dbbc530e8e3bba67f74b48cf12eff545128b5d19192d905e2f10e00927861` |
| `luke_ii_verification.json` | `238f3740aed070cf17653fd2da6f4fc29bfc177c2afe6b5d27a3e3e6fd7aad25` |
| `luke_ii_dimensional_audit.csv` | `4d7d4c743b4c24acc2c7c5e7e47e5b0c6d753209bec396011a12fbd02cd65825` |
| `luke_ii_dimensional_audit_summary.json` | `1c9d870ba38952a18afb5f21791c84bff0aa73562e7d23aa03ad8189595d401a` |

Generated binary and audit outputs remain workflow artifacts or controlled package
assets; they are not committed as repository bloat or treated as approval records.

## Dimensional review register

`luke_ii_dimensional_audit.py` inventories all 96 named geometry nodes with:

- component family and evidence state;
- mandatory engineering-review gate;
- minimum and maximum coordinates, extents and centroid in metres;
- vertices, faces, signed geometric volume, watertight state and winding state;
- an open engineering-review status for every node.

The audit deliberately classifies field-guide nodes as illustrative rather than
physical field evidence, payload nodes as sequence illustrations, docking collars
as provisional interfaces and damping nodes as requiring specialist gas/pressure
hazard review.

## Source-state discipline

Parameter states in `luke_ii_parameters.json` are authoritative for interpretation:

- `LEGACY_SURROGATE_SOURCE`: inherited geometry surrogate, not measured hardware;
- `SOURCE_ALIGNED_TOPOLOGY`: aligned to reviewed project sources;
- `DERIVED_TARGET`: calculated reference target, not source fact;
- `PROVISIONAL_REFERENCE`: required to make the reference inspectable, pending review;
- `QUARANTINED_UNVERIFIED_NOT_USED_FOR_GEOMETRY_OR_CAPABILITY`: excluded from active capability claims.

The inherited one-million-ampere and five-tesla simulation values remain
quarantined. No capture, controlled-return, redistribution, field-strength,
thermal, shielding, gas-handling, pressure-shell or crew-safety capability is
validated by this model.

## Review sequence

1. Run the unit, deterministic-hash and dimensional-audit checks.
2. Inspect the named 1:1 GLB assembly in Blender or equivalent CAD software.
3. Record dimensional findings against the audit node and review gate.
4. Replace provisional values only with source-backed engineering review.
5. Synchronise the existing Drive workbook in place and verify its unchanged ID.
6. Keep publication and merge gates closed until the evidence state is accepted.
