# Alexandria — Multilingual Wikimedia R0 intake handoff
**Date:** 2026-10-20 (Australia/Brisbane)  
**Authority:** source-level candidate only; no canonical admission, actual Wikipedia page bytes or owner-host readback

## Why this is a single CGX/CCC extension
The existing CGX `source_envelope_contract`, `file_conversion_contract`, Alexandria R0/R1 candidate, and LightSpeed/UniSpace source-lens remain the owner. The newly added `cgx/portable_node/wikimedia_revision_pair.py` and `scripts/acquire_wikimedia_revision_pair.py` are bounded source adapters, not a second Alexandria database, runtime, network manager, agent or UI.

## Source acquisition procedure (only from an authorised online machine)
The present ChatGPT runtime could not retrieve Wikimedia API response bytes from the official endpoint. Thus **no real Wikimedia revisions have been downloaded, admitted, or verified in this change**; eight adapter tests and five acquisition tests use synthetic, explicitly labelled responses. Run only from a host with approved network and an unshared output path. Never run in a public Vite/Squarespace/Vercel source tree.

Example *operator-controlled* command from the checked-out project root:

```shell
python scripts/acquire_wikimedia_revision_pair.py \
  --item Q42 \
  --as-of-utc 2026-10-20T12:00:00Z \
  --output PRIVATE_OWNER_SOURCE_ROOT/alexandria/wikimedia/Q42-20261020
```

**Q42 is only a requested Wikidata identifier here, not proof of any returned language page.** The script first retrieves official Wikidata sitelinks and then obtains one last revision at/before the UTC cutoff for each of English and French Wikipedia; it rejects conflicting titles, page/revision IDs or Wikidata identities. It writes three exact raw JSON API responses, SHA-256/byte-length manifest, and source-free R1 graph candidate. Existing output paths are refused; no background fetch, global crawl or publication is initiated.

The `wikimedia_revision_pair` adapter handles `action=query&prop=pageprops|revisions`, main-slot wikitext, `pageid`, `revid`, timestamp, `wikibase_item`, and Wikidata `wbgetentities` sitelinks/`lastrevid`. Two pages of one concept keep their separate language revisions, independent titles and hashes. Its relation is `WIKIDATA_SITELINK_ASSOCIATION_NOT_TRANSLATION`, **not a proven translation relationship**. It extracts only bounded **lexical link candidates**. It does not resolve redirects, embedded templates, category membership completeness, backlinks, non-text media, page-local licences or full source histories. Those remain Frontier items.

## Root completeness and licensing
- **R0**: retain exact API response bytes under owner-controlled source custody, source host+parameters, UTC cutoff, byte count and SHA-256, revision permalinks and contributor history links. API JSON SHA-256 proves local byte identity, not independent proof that returned data came from Wikimedia; TLS/provider attestation and repeat fetch are separate checks.
- **R1**: source-free page/revision structure and associations, preserving both original language records, all unknowns and original R0 locators. No full-content reconstruction claim from a compact graph.
- **Licence**: English/French Wikipedia article text is generally CC BY-SA 4.0, subject to page-specific exceptions and attribution/share-alike; Wikidata main-namespace structured sitelinks are CC0. Maintain separate per-record attribution and licence records. Source: Wikimedia Foundation Terms of Use and Wikidata:Copyright. Do not apply the UniSpace product licence to upstream adapted article content without review.
- **Later full-corpus benchmark**: prove the total language/wiki namespace/dump manifest, page count, redirects, per-revision completeness, source-byte recovery and same-content comparison with an independently sourced ZIM baseline; not satisfied by a two-page proof.
- **Native readiness**: `#158` public/private, `#161` two independently signed CGX nodes/receiver readback, owner DBR and exact root authority must pass separately. No physical/SAI/Natural Network qualification is inferred.

## Current reproducible tests
PR #180 exact head is pinned by the issue #40 source receipt rather than a mutable copy of this document. As of the 2026-10-20 CI readback, 16 keyed + 11 archive + 6 reference projection + 14 first catalogue R0/R1 + 8 multilingual pair + 5 acquisition guard + 2 authenticated owner API = **62 focused PASS**; other GitHub source workflows were also green. The two original CC0 engine-catalogue source fixtures remain an independent **real** proof for their catalogue only (46 lines), not for engine source code.

## Next admitted step
From a verified approved R0 capture, attach actual source digest, revision/page IDs, authenticated provider provenance, licences and first cross-language sitelink evidence to the existing CGX source envelope/DBR; compare with one like-for-like officially dated Wikipedia dump manifest. Only then status a true `REAL_WIKIMEDIA_PAGE_R0_VERIFIED`, preserving the two independent page histories. No source bytes in public static `/cgx`, no auto branch merges or releases.
