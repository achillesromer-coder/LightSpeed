# Local Runner Queue — 2026-06-07

Result label: `LOCAL_RUNNER_QUEUE_POPULATED__DRY_RUN_FIRST`

| Queue ID | Owner | Target | Action | Mode | Success receipt |
|---|---|---|---|---|---|
| `LR-01` | Merovingian | LightSpeed + De Sporte | Verify process/health/evidence state and report blockers | dry-run | `merovingian_health_receipt_2026-06-07.json` |
| `LR-02` | Trinity | `Z+3_Trinity` | Confirm compact operator shell, one active floor, queue visibility | dry-run | `trinity_shell_receipt_2026-06-07.json` |
| `LR-03` | Neo | `Z+2_Neo` | Confirm Ollama endpoint, selected model, and one-session policy | dry-run | `neo_ollama_receipt_2026-06-07.json` |
| `LR-04` | Smith | `Z-3_Smith` | Route queued tasks into gated receipts, no execution escalation | dry-run | `smith_queue_receipt_2026-06-07.json` |
| `LR-05` | Oracle | `Z-2_Oracle` | Attach source groups and provenance tables without promotion | dry-run | `oracle_source_attach_receipt_2026-06-07.json` |
| `LR-06` | Morpheus | `Z-1_Morpheus` | Review overlaps, duplicates, contradictions, and promotion candidates | dry-run | `morpheus_review_receipt_2026-06-07.json` |
| `LR-07` | Architect | `Z+1_Architect` | Maintain gates for repo, Drive, web, and public claims | dry-run | `architect_gate_receipt_2026-06-07.json` |
| `LR-08` | TheConstruct | `Z0_TheConstruct` | Prepare scenario/data-space checklist only; no heavy render launch | dry-run | `construct_manual_heavy_receipt_2026-06-07.json` |
| `LR-09` | Achilles | Cross-system | Compact current run into handoff and verify no blocked workflow activated | dry-run | `achilles_compaction_receipt_2026-06-07.json` |
| `LR-10` | Athene | Online/deferred | Define public overlay prerequisites; do not hook public UI yet | planning-only | `athene_overlay_gate_receipt_2026-06-07.json` |

## Runner policy

- Default command behavior must remain dry-run unless an operator explicitly passes an execution gate.
- Use `D:\LightSpeed_Consolidated\LightSpeed_Runtime\exports\agent_home_2026_06_07_ingestion_run` as the current source of runner context.
- Use `D:\LightSpeed_Consolidated\Agents\Achilles\99_outputs_for_review` for review outputs.
- Use De Sporte as the co-runner/overseer companion, not as a replacement LightSpeed shell.
- Keep `.env`, credentials, OAuth secrets, tokens, and private keys path-level only.
