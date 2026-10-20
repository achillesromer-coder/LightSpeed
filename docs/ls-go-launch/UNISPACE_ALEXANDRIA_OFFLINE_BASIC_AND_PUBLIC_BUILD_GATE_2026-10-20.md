# UniSpace / Alexandria — Default public build HOLD and Basic offline kit candidate
**20 October 2026 | Source integration candidate | Parent PR #189 | NOT a production merge**

## Outcome
A new CGX/UniSpace public build safety step prevents the known private operator-review catalogue, 411-component atlas, and review meshes/renders from being included in a normal `npm run build` publication candidate.

The site continues to support its localhost `npm run dev` workflow. `npm run build:internal` explicitly preserves the former developer build and MUST NOT be used for publicly hosted output; it can include internal assets. The default `npm run build` and `build:public` now invoke `checkPublicRelease.mjs --phase source`, TypeScript/Vite build and `checkPublicRelease.mjs --phase dist`. Both pre/post checks hold on known static paths or symlinks. The current known 61-file source risk should cause the default build to exit nonzero. This is an intended safety signal, not successful release qualification. No private assets were silently removed or ownership changed.

The existing Objects view's static-URL fetches need authenticated owner-facing delivery/route rewiring before removing or rehoming the data files. This source stage does not pretend that moving 61 assets without permission and resolver testing would be safe. Exposing private content through Vite dev is only acceptable on the loopback development device; never advertise the internal build artifact as a public release.

## Source-only Alexandria Basic ZIP
`cgx/review/alexandria_basic_offline_kit.py` composes a reproducible, self-contained offline review ZIP from the existing four source registries and the generated HTML preview:
- `index.html`: local-only searchable 251-entry reference index with 18 source-linked lessons; external hyperlinks open only on deliberate user action
- `catalogue.json`: 207 legacy game/engine source entries + 31 upstream tool/library entries + 13 official standards/science references, with rights HOLD on all third-party references
- `lessons.json`: 18 unexecuted, synthetic-first lessons, held physical/scientific claims
- `README.txt`: usage, rights, scope and provenance limits
- `manifest.json`: exact SHA-256 and lengths for each of the preceding ZIP members, plus source roots; status `REVIEW_ONLY_NOT_PUBLIC_RELEASE`

The package uses stable ZIP member ordering and fixed timestamps; no third-party code/assets/model weights, personal credentials, private object-review catalogue, live Javascript imports or external fetched data are embedded. Source metadata is not publisher rights verification. Distribution beyond owner review requires source-line audit, content review and offline device tests. The ZIP is **not signed** and has not been validated on independent devices.

Generate a review ZIP:
```sh
python cgx/review/alexandria_basic_offline_kit.py --output /tmp/Alexandria_Basic_Review_2026-10-20.zip
```

## Release and acceptance state
- **#158 remains OPEN:** confirm all internal review assets outside static `public/` and `dist/`, inspect all compiled JS/CSS for private bytes and source URLs, use the existing authenticated owner bridge for Objects, and run real unauthenticated/revoked/cross-tenant HTTP denial checks. The source pattern scan is necessary but not sufficient.
- **#161 remains OPEN:** independent, authenticated two-node FileSpace/DataSpace exchange, revoked grants, CAS/replay, signed root and receiver readback.
- **Rights clearance remains OPEN:** exact upstream SPDX/component/asset licences, trademarks and archival rights need owner review; source-only documents do not make an engine package distributable.
- **Functional user acceptance remains OPEN:** offline browser reopen, performance on lower-resource devices, accessible navigation and exact export/readback on target devices.
- **OS/host deployment remains OPEN:** no C:/D: edits, enrolled plugins, service processes or production Site/Drive mutation in this PR.

## Operational branch policy
Stack after #182 → #184 → #185 → #186 → #187 → #189. Parent remains `Cognigrex.cgx` and only CGX-CCC controls capabilities; historical `Create Your Collective` is a distinct programme. This review branch is designed to stop unsafe publication while enabling the owner to inspect a useful Alexandria offline kit. Do not merge the review stage into public site until #158 is appropriately resolved.
