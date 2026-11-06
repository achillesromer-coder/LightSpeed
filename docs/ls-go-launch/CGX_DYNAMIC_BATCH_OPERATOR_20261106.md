# CGX dynamic batch review | 2026-11-06

Scope: the **single Cognigrex.cgx parent Family Set** and existing review PR #206. This utility is an operational reduction of Remote Desktop calls, not a second LightSpeed runtime, DataSpace server, CGX authority resolver or mint tool.

Run after an isolated review branch receives a mass source fold:

\`\`\`shell
python cgx/bootstrap/cgx_dynamic_batch.py --base <previous-commit-sha> --mode plan
python cgx/bootstrap/cgx_dynamic_batch.py --base <previous-commit-sha> --mode verify
\`\`\`

The runner derives changed paths using the original Git commit ancestry and maps them into a **fixed command allowlist**, executes tests sequentially in one host process, and emits a JSON verification receipt. It does not interpolate shell commands, fetch secrets, update branches, install dependencies, change the canonical store, sign, mint or deploy. Failures stop the batch. Commands are bounded to 180 seconds each. The caller is responsible for reviewing output and approval. It will not run in a dirty worktree.

Source folds from PR #218 (UniSpace facet), #220 (permissioned/adaptive R3 view) and #222 (host-owned evidence IDs) are additive review inputs. Their independent source branch ancestry is preserved via original blob SHAs. They do **not** replace the existing LOAD.cgx resolver, FileSpace rights, DataSpace 2-node authority or UniSpace products. The R3 modules are presentation planners, not server-verifiable authorization issuers; they must not become native admission without independent binding.

Readiness: DATA/FILE/LOAD review lanes may be tested and used locally, but a loopback listener or a signed-looking caller receipt never satisfies issuer, revocation, two-node DBR or public publication rights. Source-only tests do not approve release. Maintain the 40% remote call reserve and 1 GiB free-RAM floor.

G01 rights, G02 issuer, G03 root signing, G04 2-node DBR, G05 mint, G06 effectful connector permissions, G07 public release: **HOLD**, pending independently verifiable proofs.
