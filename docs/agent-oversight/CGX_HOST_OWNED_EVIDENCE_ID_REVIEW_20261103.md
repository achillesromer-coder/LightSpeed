# CGX / LS — Host-owned evidence ID response contract (review)

**Scope:** Source-only implementation, not runtime activation, training, or native object admission. The semantic parent remains `cgx:root:cognigrex`, with the runtime owned by `LS.cgx`. This branch is based on current GitHub `main`, not the older BouwerBase installed checkout.

## Problem and approach
The local Neo strict-response pilot failed because the model repeated unescaped Windows paths in JSON. Repeating a full path, SHA and quote is unnecessary: those are already host-known, source-verified fields.

The proposed adapter limits model output to `floor_summary`, `blocker`, and an allowlisted `evidence_ids` array. The host reconstructs the path, exact SHA-256 and literal quote from immutable bindings. The host separately supplies the approved output route. Unknown/duplicate IDs, changed source bytes, invalid JSON, incomplete output, missing summary and unsupported fields all fail closed.

## Reproducible qualification
- BouwerBase review directory: `D:\LightSpeed\State\Review\CGX_UNISPACE_MINT_PREP_20261103`.
- 11 local pytest cases passed before review-branch publication.
- One live `qwen3:4b` loopback request succeeded using an independently hash-verified native-state review receipt; `num_ctx=2048`, `num_predict=180`, measured prompt/completion tokens 326/44, wall clock 70.219 s.
- Live receipt: `NEO_HOST_OWNED_LIVE_PROOF_20261103T043528Z.json`; state `CONTRACT_VALIDATED_REVIEW_ONLY`.
- That pilot summary chose the quote `"write_operations": 0` and was **not** independently accepted as a complete semantic assessment of native mint readiness. Passing the response contract does not certify the content.

## Remaining before enabling in the installed runner
1. Smith: review this isolated adapter and its tests, including path/symlink race and source excerpt bounds.
2. Oracle/Morpheus: add source relevance criteria and task-specific factual evidence checks. Do not equate a literal quote with a valid inference.
3. Neo: integrate into `local_floor_runner.py` behind a default-off source-qualified policy and verify one-model/one-worker resources, hash recheck, sink route and receipt ledger.
4. Merovingian: reproduce the earlier 8192-context Ollama HTTP 500 separately; no silent retries when server outcome uncertain.
5. Achilles: independently sign the rights/ACL/lease and native DBR requirements before any CGX promotion.
6. Reconcile merged PR #217 and open bootstrap/family dependencies (#206/#214/#215) before any installed-package change.

**Forbidden here:** native mint, DB mutation, scheduler creation, public release, private corpus export, unlicensed training, and autonomous external dispatch.
