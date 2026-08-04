# RFS/EMFF Type-1 Handoff and Workflow - 2026-08-05

## Execution boundary

This package is a bounded screening and planning artifact. It does not claim extraction rate, purity, optimal frequency, energy efficiency, equipment safety, or validated physical capability.

## Current outputs

- Workbook: `C:\Users\acc\Documents\Codex\2026-07-20\blease-run-a-quick-check-through\romer_rfs_emff_type1_analysis_2026-08-05\Romer_RFS_EMFF_Type1_Cognigrex_Workbook_2026-08-05.xlsx`
- Sweep rows: `116640`
- Materials: `4`
- Samples: `12`
- Figures: `4`

## Shorthand equation

`Score = evidence_gate * sample_gate * resonance_alignment * field_factor * concentration_factor * penetration_factor`

Where `penetration_factor = min(1, sqrt(2/(2*pi*f*mu*sigma)) / thickness)` and `resonance_alignment` is a bounded distance from the Project Overview cm^-1 resonance band.

## Critical finding

The Project Overview sample resonance bands are expressed in cm^-1, which correspond to THz optical/IR-scale frequencies. The existing LS runner uses MHz RF/coil sweeps for skin-depth and attenuation. These must remain separate model domains until the applied excitation modality is specified and instrumented.

## Top screening cases

| sample | material | applied cm^-1 | field T | rf MHz | score |
|---|---:|---:|---:|---:|---:|
| 4a | C_graphite | 2800 | 0.5 | 1 | 0.3500 |
| 4b | C_graphite | 2800 | 0.5 | 1 | 0.3500 |
| 4c | C_graphite | 2800 | 0.5 | 1 | 0.3500 |
| 3a | Fe | 200 | 0.5 | 1 | 0.2090 |
| 3b | Fe | 200 | 0.5 | 1 | 0.2090 |
| 3c | Fe | 200 | 0.5 | 1 | 0.2090 |
| 4c | Fe | 200 | 0.5 | 1 | 0.2090 |
| 2a | Nd | 400 | 0.5 | 1 | 0.1803 |

## LS execution workflow

1. Confirm base sample volume, bulk density, moisture, particle-size distribution, and target concentration for each sample ID.
2. Replace placeholder material properties with measured assay/certificate values.
3. Run RFS-domain resonance sweeps in cm^-1/THz-equivalent terms only when the actual excitation modality is defined.
4. Run EMFF-domain MHz/coil sweeps using LS `rfs_emff_runner.py` for skin depth and field penetration comparisons.
5. Attach instrumented repeated raw logs before allowing physical capability language.
6. Promote to canonical LS/web only after Merovingian/Smith gates confirm evidence, artifact hashes, and claim boundaries.

## Z-floor responsibilities

- Z-3 Smith: validate claim gates, math domain, and blocked claims.
- Z-4 Merovingian: register receipts/manifests and enforce bounded work intake.
- Z+3 Trinity: maintain workflow/schema compatibility and operator handoff state.
- Z0 TheConstruct: run bounded simulation jobs and export artifacts.

## Known pinch points

- PDF OCR is not embedded; values were transcribed from rendered pages.
- All alloy/concentration variations remain parametric until sample assays are known.
- Permeability and susceptibility are strongly material-state dependent, especially iron and neodymium.
- Safety and equipment performance require physical instrumentation, not spreadsheet inference.