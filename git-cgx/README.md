# Git.CGX — public static review transfer (source-only)

This isolated branch is a **review handoff**, not the Git.CGX repository, a CGX root or a live website.

The portable Git.CGX v0.1.0 package was built and tested independently from original public-safe code. Its ZIP SHA-256s, 16 curated review-node scope, eight routes, CI contract, and transfer/rights requirements are recorded in [GIT_CGX_REVIEW_TRANSFER.json](./GIT_CGX_REVIEW_TRANSFER.json).

**Status:** 12/12 Node source tests passed, 8 browser routes and mobile responsiveness verified in a controlled local harness. Four static assets are packaged through a deny-by-default allowlist with SHA-256 release receipts. The GitHub repository-creation operation is not exposed by the connected account tools and no new Git.CGX repository has been confirmed.

The actual full source package remains an owner-downloadable ZIP from the originating ChatGPT conversation; it is **not embedded in this branch or accessible to GitHub Actions yet**. Use the ZIP to create the Git.CGX repository, then verify each source file and CI result before enabling GitHub Pages.

**Owner gating:** Do not publish original CGX carriers, GPT export shards, private Vite review/catalogue assets, session keys, native RootAuthority/DBR receipts or credentials. Git-hosted Actions checks only source/build integrity, **not** a signed node handshake, real peer, native integration or execution authority.

Related work: [public synthetic viewer #174](https://github.com/achillesromer-coder/LightSpeed/pull/174), [deny-by-default build #188](https://github.com/achillesromer-coder/LightSpeed/pull/188), [private asset hold #158](https://github.com/achillesromer-coder/LightSpeed/issues/158), [native exchange #161](https://github.com/achillesromer-coder/LightSpeed/issues/161) and [unified bootstrap #206](https://github.com/achillesromer-coder/LightSpeed/pull/206).

This branch MUST NOT be merged into production LightSpeed as a substitute for a separate public repo, release/rights approval or independently accepted native CGX.
