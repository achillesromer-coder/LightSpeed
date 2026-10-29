# Git.CGX live-source implementation handoff — 29 October 2026

This branch is the **source-review handoff**, not the standalone Git.CGX repository, website, native CGX or authoritative DBR.

### Working package
- Source: `Git.CGX_LIVE_Source_Repository.zip` — 44 files, SHA-256 `6a6ac0db808da5b0c4b1463b552bfd8e97861cf095c7ec899fab5df410b95f7f`.
- Public static: `Git.CGX_LIVE_Public_Web.zip` — 17 static files, SHA-256 `2175af87dd2316ab1810b5898bc6f2c84dc37158c895e9a4e69bafea84afad53`.
- Verified in original isolated build: 37/37 Node tests, 13-route Chromium injected-source smoke, 390px mobile overflow checks, strict public static allowlist.
- **Synthetic** five-repository metadata ingest + repeat verified: 5 hash-chain entries on first pass; zero entries on unchanged repeat. Real GitHub Actions job **has not run**; source package not uploaded to GitHub.
- `Git.cgx` is a *single latest-qualified review entry*, not a native executable carrier. Git commits and hashes remain temporal provenance; no rolling user-visible product version required.

### Five *verified publicly accessible* source owners
`achillesromer-coder/LightSpeed`, `NCNBOUWER/Raphael`, `achillesromer-coder/Romer-MPL`, `achillesromer-coder/Operations`, `achillesromer-coder/Data`.

### New source modules in portable repository
- `scripts/lib/live-corpus-core.mjs`: allowlisted, fail-closed metadata projection, strict aggregate schema, SHA-256 hash-chain/idempotence.
- `scripts/sync-public-corpus.mjs`: public GitHub repository/branch/tree metadata read; preview/read-only or `--write` guarded local candidate updates. Does **not** import original file contents, full histories or private repos.
- `registry/public_corpus_sources.json`, `registry/public_corpus_snapshot.json`, `registry/reason_log.json`, `registry/migration_queue.json`, `registry/capability_intents.json`.
- `.github/workflows/public-corpus-live.yml`: six-hour scheduled metadata check with evidence artifact and an isolated **PR only** if owner sets `CGX_CORPUS_PR_ENABLED=true` in actual Git.CGX repository. No auto-merge/retire/publish.
- `docs/LIVE_GOVERNANCE.md`, `docs/TAILORING_AND_SEARCH.md`: public/private split, sources, source→semantic→release gates, future local user-tailored search and review record.

### Required separate owner action
Create a publicly readable `achillesromer-coder/Git.CGX` repository under an authenticated account with admin/source rights. Connected GitHub API tool does not support `create_repository`; `get_repo` returned NOT_FOUND. The owner can then import **the complete source ZIP** and enable GitHub Actions/Pages separately. After that, exact source readback, GitHub CI, first *actual* Git metadata scan, zero-private-payload audit and owner-reviewed source metadata PR are required before calling it hosted/live.

### Preserved barriers
Keep private CGX carriers, GPT conversation shard bodies, original source identity, sensitive meshes, host paths, credentials, current RootAuthority, signed native DBR and protected repo histories out of public distribution. #51 #154 #158 #161 remain separate. All historical source owners active until verified source/history/rights/consumer parity and explicit owner decision. No native admission, source deletion, repository archive, external send or physical execution by these actions.
