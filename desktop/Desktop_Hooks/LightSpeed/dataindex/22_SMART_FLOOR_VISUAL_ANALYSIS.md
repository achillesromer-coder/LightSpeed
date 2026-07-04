# Smart Floor Visual Analysis

Generated: 2026-04-13T21:51:00+00:00

This pass consolidates floor Python analysis, manifest summaries, Bento widgets, chart/map contracts, simulation hooks, and smoke checks into one Trinity-owned visual catalog.

## Floor Coverage

| Floor | Z | Source lines | Widgets | Charts | 3D maps | Tools | Sim hooks | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Trinity | 3 | 729 | 4 | 2 | 2 | 2 | 2 | pass |
| Neo | 2 | 1020 | 4 | 2 | 2 | 2 | 2 | pass |
| Smith | -3 | 906 | 4 | 2 | 2 | 2 | 2 | pass |
| Merovingian | -4 | 727 | 4 | 2 | 2 | 2 | 2 | pass |
| Morpheus | -1 | 900 | 4 | 2 | 2 | 2 | 2 | pass |
| Oracle | -2 | 1769 | 4 | 2 | 2 | 2 | 2 | pass |
| Architect | 1 | 1122 | 4 | 2 | 2 | 2 | 2 | pass |
| TheConstruct | 0 | 788 | 4 | 2 | 2 | 3 | 2 | pass |

## Fidelity Checks

| Floor | Check | Status |
| --- | --- | --- |
| Smith | Smith receipt and resumable handoff flow | pass |
| Smith | Smith dependency approval gate | pass |
| Merovingian | Merovingian diagnostics, performance, and release clean flow | pass |
| Merovingian | Merovingian smoke replay and release dry-run flow | pass |
| Morpheus | Morpheus proof queue, comparison, and confidence flow | pass |
| Oracle | Oracle originals, dictionary, and proof handoff | pass |
| TheConstruct | TheConstruct zoning grid and cluster flow | pass |
| TheConstruct | TheConstruct GMAT target export flow | pass |
| TheConstruct | TheConstruct ephemeris replay flow | pass |

## Operating Notes

- Heavy maps, charts, dependency checks, and simulations are descriptor-backed and lazy-loaded until visible or explicitly opened.
- Oracle holds originals and derived components; Morpheus proofs claims; Smith routes receipts; Merovingian visualizes diagnostics and release health.
- TheConstruct owns heliocentric zoning, cluster overlays, GMAT batches, ephemerides, and replayable simulation artifacts.
- Trinity exposes the shared settings, theme/background builder, project wall, Z-floor dropdown, and artifact preview language.
