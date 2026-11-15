# UniSpace UOS full-product integration and PUBLIC release gate
Status: **PRIVATE INTEGRATION ZIP BUILT · PUBLIC RELEASE NOT ACCEPTED**

## Product levels
| Profile | Status | Included |
| --- | --- | --- |
| UniSpace shell v0.1.0 | Local review candidate | Compiled frontend, 12-file public CGX viewer, 11-node source-design lattice, CCC plan and checksums |
| UOS native integration v0.1.0 | Local PRIVATE source integration candidate | Everything above, **104 Git-index-bound Python runtime modules** and 3 requirements manifests |
| Signed/public UOS release | **NOT BUILT / HOLD** | Requires qualified installers, independently accepted native host+DBR, tested signed release, privacy/licence evidence and reviewed provider admission |

The second profile exists to integrate *existing* native modules, not create a second
Grex, LOAD, Alexandria, CCC network or owner agent. It contains **no packaged
Python interpreter, installed dependency wheels, live keys, source data, device
handshakes, authenticated FileSpace client lease, or independent DBR nodes**.

Local source-import smoke: 3/3 core Python modules loaded from the ZIP on BouwerBase (contracts, bridge_health and cgx_capability_registry). This is not installed runtime acceptance.

Source: `apps/lightspeed-go/scripts/package_unispace_uos_integration.py`;
preexisting shell packer: `apps/lightspeed-go/scripts/package_unispace_premint.py`.
All source bytes come from the actual Git index; Python modules are syntax parsed.
ZIP entries are SHA-256 bound with deterministic timestamp and readback. A
`UOS_INTEGRATION_MANIFEST.json` declares unresolved release blockers. This
is neither an IP title certificate nor permission to distribute source.

## Eight gates that must be independently evidenced
1. **IP/source** — component-level copyright/license + asset rights, including
   redistributable third-party dependency licences and UI materials.
2. **Root native identity and mint** — signed issuer, RootAuthority, revocation,
   user-reviewed exact mint transaction, network fees and signing scopes.
3. **DBR** — distinct authenticated nodes, signed lease, independent read/write,
   retrieval and revocation. Two logical schemas on one process do not count.
4. **FileSpace/DataSpace** — rights-filtered dynamic source retrieval, persisted
   state, exact R0/typed R1/R2 claims and permission negatives.
5. **OS distribution** — real signed Windows/macOS/Linux packages, idempotent
   installation, upgrades, rollback, local user approval and malware scanning.
6. **CCC/skills** — installed tool verification (not mere registry labels),
   scoped capability grant, owner receipts, safety interlocks, watchdog and
   resource budgets. No duplicate Achilles/Neo workers.
7. **Security and network** — public HTTP privacy #158, authentic handshake,
   user/device ACL, offline/online switching, range and other-user denial,
   audited remote execution, and source/deletion policy.
8. **Acceptance** — executable end-to-end user workflow, UI, error recovery,
   accessibility, service restart and reproducible binaries/test receipts on
   supported platform combinations.

A source import smoke test is **not** native acceptance: it proves neither
installed runtimes nor operational networking. An inconclusive test stays HOLD.

## Founder sequence
Review GUI aesthetics/controls, source model and object cards -> manual design
export (not mint consent) -> exact LOAD/CCC rights + provider qualification ->
separately approved issuer and DBR -> primary family/first-space manual mint ->
CCC systems and tools/sources registry -> Grex scientific/engineering operations ->
licensed/public-domain fiction/game/Interdimensional Hang and UOS converters.

Keep LOAD.cgx and Alexandria external to UniSpace's consumer ZIP: they are
dependent native services rather than a duplicated packaging root. Consumer
shorthand/fractal arrangement here represents a deterministic graph and
selective-hydration contract, **not verified geometric code compression**.

## Resource and archival policy
Continue operating the existing five owner automations/agents; no new background
workers created by packaging. Preserve **at least 5,205** monthly Remote
Desktop calls, with provider percentage rounding acknowledged. Desktop owner
GUI stays loopback-only. No repository, Drive, FileSpace or source/archive
deletion before independent source-migration, rollback and owner review.

## Local outputs
- `C:\Cognigrex\State\Review\UNISPACE_PRODUCT_CANDIDATE_20261106\UniSpace_0.1.0_preMint.zip` — 20-file shell archive.
- `C:\Cognigrex\State\Review\UNISPACE_UOS_INTEGRATION_20261106\UniSpace_UOS_0.1.0_private_integration.zip` — 130-file private integration archive.
- Both have same-named `.receipt.json` SHA-256 verification files.
- Do not point a public hosting platform at either ZIP until all release gates are independently accepted.
