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

## Acceptance invariants

| Invariant | SHA-256 / value | Gate |
|---|---|---|
| Canonical parameter bytes | `505a077cb1461718d3078eb17a62c51ca1c0d1d9f4a15ccf11bc11e91ec49b1f` | Exact |
| Semantic named geometry | `18b61fb32815cb3237fb62e49d8f46e91e7f57468a1749cbc8bd5ecd9ef0295f` | Exact at 1×10⁻⁸ m quantisation |
| Portable 1:100 STL | `8f1dbbc530e8e3bba67f74b48cf12eff545128b5d19192d905e2f10e00927861` | Exact |
| Dimensional-audit CSV | `4d7d4c743b4c24acc2c7c5e7e47e5b0c6d753209bec396011a12fbd02cd65825` | Exact |
| Named nodes | `96` | Exact |
| Watertight / winding-consistent nodes | `96 / 96` | Exact |
| Test suite | `10 / 10` | Required |

### GLB hash scope

The 1:1 GLB is required to contain the accepted named semantic geometry, but its
raw container SHA is a build receipt rather than a cross-platform acceptance
invariant. The controlled package build produced
`3238db7ebf2148786d8060b751825b218eb6b04c44a57adb14f617d40a2fa182`;
the pinned clean Linux runner produced
`c87030bd5329dc7b6b912b877dccdff697de83836156fd747b949b07ae03e073`.
Both contained 96 accepted nodes and the same portable STL/audit evidence.
Exporter ordering or metadata must not be mistaken for a geometry change.

`luke_ii_geometry_fingerprint.py` removes that ambiguity by hashing sorted named,
oriented triangles after fixed-point quantisation. Cyclic face-index changes do
not alter the fingerprint; reversed winding, changed topology, changed node names
or changed coordinates do.

Generated binary and audit outputs remain workflow artifacts or controlled package
assets. They are not committed as repository bloat or treated as approval records.

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

1. Pass the unit, portable-hash, semantic-fingerprint and dimensional-audit checks.
2. Inspect the named 1:1 GLB assembly in Blender or equivalent CAD software.
3. Record dimensional findings against the audit node and review gate.
4. Replace provisional values only with source-backed engineering review.
5. Synchronise the existing Drive workbook in place and verify its unchanged ID.
6. Keep publication and merge gates closed until the evidence state is accepted.
