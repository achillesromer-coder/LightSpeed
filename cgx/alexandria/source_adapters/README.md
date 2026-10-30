# LOAD / Alexandria — Wikimedia and traditional source federation (review)

**Status:** scoped source-only prototype, not a native CGX/CCC install, not a Wikipedia knowledge mirror and not a verified full article ingestion.

## Native owner alignment

This directory adds a *source adapter* compatible with the existing CGX family:
- One parent: `Cognigrex.cgx`.
- Alexandria activation: existing `LOAD.cgx` (the alias requires native Object_ID lookup and DBR admission).
- Shared CCC capability namespace: `Cognigrex.cgx:/ccc`. The phrase `CCC.cgx` is only an unverified friendly naming candidate; do **not** mint a duplicate root or install competing plugin.
- Child domains remain `Romer.cgx`, `Eco.cgx`, `EMASSC.cgx`, subordinate `LS.cgx`.
- FileSpace holds source identity, R0 exact bytes/revisions/rights, and typed R1/R2 semantics; DataSpace transports only authorised sparse envelopes and host-proven receipts.

## First Wikipedia slice

Use a verified MediaWiki XML export from [Wikimedia content current/history](https://wikitech.wikimedia.org/wiki/MediaWiki_Content_File_Exports). This adapter handles *one locally provided original export segment* of at most 60 MiB and projects namespace-0 pages:
- page identity `wikimedia:enwiki:page:<id>`, distinct source revision `...:revision:<id>`;
- original segment SHA-256 and exact *decoded text* SHA-256 as different proof types;
- title, timestamp, redirect reference, lexical link candidates (unverified);
- a loss ledger, optional 12-way **non-authoritative** view selector, and zero canonical mint/DBR authority.

The adapter does **not** interpret infobox templates, resolve Wikidata QIDs, infer truth, calculate physical CAD coordinates, copy page text into the review projection, or fetch a URL. Neither raw XML nor third-party page prose is committed here. To run on an authenticated host, preserve original XML with source/version/hash/licence and pass a bounded source path to the converter through an existing CGX native ingestion capability. This is not a replacement for the current first-file registry or a production CLI.

The source bibliography and geometry missing-field matrix are in `traditional_source_bibliography.json`. In particular, the regular dodecahedron's **12 faces, 30 edges, 20 vertices** describes mathematical/combinatorial shape geometry; it is not evidence that a SHA-selected UI face proves the native CGX hypergeometric address or stores encyclopedia bytes.

## Example (local operator-owned path only)

~~~python
from wikimedia_source_projection import project_xml_segment
r = project_xml_segment('/path/to/verified-export-part.xml',
                        project='enwiki',
                        source_uri='https://dumps.wikimedia.org/other/...')
print(r['summary'], r['source']['sha256'])
~~~

Do not run against an unapproved source or treat the output as a native acceptance receipt. Full dump processing requires streaming verified source segments, catalogue batching, stable source/version/family mapping, licence reconciliation, authority and DBR, plus loss/round-trip and human review.

## Verified boundary and rights

Wikipedia page text is generally CC BY-SA with attribution/share-alike obligations; each media file can have different rights, and Wikidata structured data has separate terms. Backed-up Wayback pages are **not** inherently public domain or open source. Freely accessible does not imply free-to-republish; code licences and data licences require separate qualified contracts.

The provider docs also offer public rate-limited MediaWiki REST/Action APIs and full/current historical exports. Wikimedia Enterprise is an optional high-volume feed requiring credentialed access; no token or account is created or copied here. Wayback timestamps are temporal **source references**, not legal rights or independent verification.

## Source-only regression tests

~~~sh
python -m unittest discover -s cgx/alexandria/source_adapters -p 'test_*.py' -v
~~~

A deterministic CI job runs this suite on PRs. Successful source-only tests are not full-corpus acceptance or an installed solver/renderer. The ongoing five domain automations should use the bibliography for discovery but request an exact original R0 snapshot before each conversion and maintain the security/publication holds #158, #161 and #209.
