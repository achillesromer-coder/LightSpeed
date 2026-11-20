# COIN / Web4 protocol canonical topology — 2026-07-29

## Purpose

This public-safe record points to the owner-controlled canonical protocol artifact without publishing the proprietary protocol source into the public LightSpeed repository.

## Source-of-truth split

- **Google Drive**: canonical artifact, manifest, build receipt, checksum, compile-assurance instructions and owner decision/readback.
- **Git**: public-safe topology, validation rules, code interfaces that have been separately approved for publication, and tests.
- **Desktop**: private/local implementation, compilation, simulation and security validation.
- **LS GO**: owner review, approval, hold and release decisions.

## Canonical Drive artifact

- Folder title: `Cognigrex Web4 Protocol Fileset v0.1`
- Folder ID: `13QOVYc6WPW3D9hCelMEsu7ZOcXaPDhpX`
- Parent Project Receipts folder ID: `1FlIjBrt3vQG67Jh37aWGf2cVEa6OmXZX`
- Archive ID: `1tZizmq__mFluwlSM0LHwAkMhW0NRmS9f`
- Manifest ID: `1ExuuSa67t2Rq-td78RREQrd49VgWwYJN`
- Build receipt ID: `1v62Ev6g1B-E5v4m5jjJEJ5GiWCRIdAXP`
- Checksum file ID: `1zbnAnYrFWlSfLt-oip8toh1GEtPbD8A5`
- Canon receipt ID: `1uM6xwMTDw8sKtd-9W8OmwSAThO9YoqUfdCEmbwF1pGM`
- Archive SHA-256: `fa23f1c0e193bde6d10470b00dd416da28015b7d664e58dc7eb38695c5196f1e`

The Drive folder was read back after upload. The archive size recorded by Drive is 143,933 bytes.

## Private compile-assurance queue

The next queue is represented in Drive folder `1xl-HI6gSS3E4zNmSvSQY-FalSITkE_ML` by three read-back native documents:

- canonical handoff: `1YChM6SGVJ9cpTyJSi6YxNEjTyO4uz4PtTB_Ke2fhqyM`;
- Codex private compile prompt: `1ureExwweNRIR-OekuSut-5tJX2rAoaIjREq3n4Sxb8k`;
- compile receipt contract and hard gates: `1gi4o61hilqz87VioT5KQ9XPVnQs49CbPEesE3xBHMDc`.

This queue contains no protocol source or deployment credentials. It requires a private/local builder, exact source verification, redacted receipts and an owner/Drive readback gate.

## Exact dependency baseline

- Solidity `0.8.36+commit.8a079791`;
- official compiler file `soljson-v0.8.36+commit.8a079791.js`;
- compiler SHA-256 `704877a592467d7de651ec5377ea6e3c676ae71d31f325401957d41bedfaa0d8`;
- OpenZeppelin Contracts `5.6.1` at official release tag `v5.6.1`;
- Foundry and `forge-std` must be pinned explicitly in the private compile receipt.

The current sandbox registry returned 404 for the pinned OpenZeppelin package. That is a dependency-environment block, not a successful compile and not evidence that the official release is absent.

## Current implementation posture

COIN means **Cognigrex Operations Integrity Network**. The canonical v0.1 artifact contains an internal, permissioned and append-only operations-integrity design covering evidence, objects, identities, tasks, capacity, governance, receipts, DBR, RAC, Smart Licence, MSD registry, mission-command authorisation and integrity anchors.

The canonical artifact does **not** authorise or activate:

- a public token, sale or market listing;
- transfer, redemption, yield, profit or ownership rights;
- customer custody, exchange, payment or stored value;
- public-chain value settlement or a bridge;
- DAO or fractionalisation activation;
- autonomous legally binding commitments;
- physical mission execution;
- publication of personal, sensitive, controlled or proprietary technical data.

Historical value-layer templates remain disabled and outside the default build.

## Validation state

The artifact receipt records successful schema, local ledger/SDK, static Solidity-policy and negative-feature-gate checks. Solidity bytecode compilation remains pending because the current package gateway did not provide the pinned OpenZeppelin dependency. This is a build-environment dependency failure, not a successful compile.

The private compile receipt must fail or hold on source checksum drift, dependency substitution, compile/invariant failure, a high or critical security finding, secret or personal-data detection, public network use, a prohibited feature or missing rollback.

## Git publication boundary

The LightSpeed repository is public. Therefore the complete source fileset is not added by this topology update. Any direct source publication requires a separate owner release decision, export-control review, legal classification and security review. Until then, Git stores only the minimum topology required to locate, verify and route the canonical artifact.

## Next queued work

1. Materialise the canonical archive into the approved private/local Desktop workspace.
2. Verify its exact size, SHA-256 and manifest.
3. Install the exact dependency baseline in an isolated network-enabled builder.
4. Compile with Solidity 0.8.36 and OpenZeppelin Contracts 5.6.1.
5. Run Foundry/property tests, static analysis, secret scanning, ABI/bytecode hashing and manual security review.
6. Perform only an ephemeral local-chain rehearsal using ephemeral keys.
7. Return a redacted compile/security receipt through LS GO.
8. Do not deploy, merge public protocol source or activate value functionality without a later explicit owner decision.

## Type-1 CGX Chain source bridge — 2026-11-11

This *existing COIN/DBR lineage* remains the basis for any later Type-1 CGX Chain. Do not mint a competing chain, object root, economic token or independent semantic database. The permissioned, source-preserving FileSpace/DataSpace network has separate semantic, cryptographic and empirical validation concerns; cryptographic agreement cannot validate a scientific claim.

The additive [Type-1 readiness record](./CGX_TYPE1_CHAIN_READINESS_REVIEW_20261111.json) is guarded by [the fail-closed verifier](../../scripts/validate_cgx_type1_chain_review.py) and [negative tests](../../tests/test_cgx_type1_chain_review.py). All 14 native/peer/security acceptance items remain **HOLD**. A successful source-review CI run verifies refusal semantics only, not network consensus, signed DBR finality, installed root/lease, compiled contracts or independent peers.

**Current owner direction:** retain existing Google Drive sharing until a proven decentralised replacement and a separately accepted cutover/rollback; do not confuse link accessibility with private ACL. Drive is still the canonical COIN source provider at this stage. Avoid replicating restricted R0 material, secrets or private citations into this public repo or an untrusted peer. No ACL mutation, source relocation or public release is authorised by this review bridge.

**Minimum next engineering slice:** reuse the existing `CGX-NODE-EXCHANGE-CONTRACT/0.1`, the native root/DBR registrar and issue [#161](https://github.com/achillesromer-coder/LightSpeed/issues/161); independently attest two distinct devices (not two local drives or model processes), verify their current key/issuer/revocation, test one authorised hash-checked interrupted/resumed transfer, reject replay/fork/conflict/unauthorised access, and obtain receiver-side DBR readback. Then exercise one permissioned UniSpace Object_ID select/save/reopen and negative access test, preserving issue [#158](https://github.com/achillesromer-coder/LightSpeed/issues/158) public/static privacy HOLD. Only after these pass consider private release, then independently review any public chain or economic function.

## Verified private-source integrity and offline chain gates — 2026-11-11

An authenticated read of the **existing Drive-owned archive** returned the original 143,933-byte v0.1 fileset. Its SHA-256 matches the pinned `fa23f1c0…95c5196f1e` historical source. The ZIP has 179 entries (including directories), 143 internally manifested payload files plus the manifest itself, 143/143 exact listed size/hash matches and a passing ZIP CRC check. The unmodified original archive's offline checks passed: 24 JSON schemas, five local ledger/SDK tests, 35 default Solidity static checks and disabled production/value gates. This establishes source integrity and isolated behavior only; it does not establish signed native DBR finality, independent peers, private ACL acceptance or contract compilation.

The existing source-level Type-1 gate and added offline archive preflight are now tested in CI using synthetic fixtures only. The CI test runs include 10 Type-1 refusal tests and 13 archive/manifest negative tests. The canonical archive bytes are **not** uploaded into GitHub Actions or included in this public repository.

A separate **owner-private ledger security hardening candidate** has been evaluated and tested against a temporary copy of the same original archive. Its code, negative tests and any sensitive implementation observations remain OFF public Git pending controlled private integration, independent key/issuer and rollback review. An isolated hardening patch passing local tests is not a host install, signed ledger consensus or authorised private release.

**Next implementation gate:** verify the private patch and issuer/key compatibility on the authorised owner host; complete pinned private Solidity dependency install, compile and Foundry tests; then exercise the existing node-exchange contract with two independently authenticated physical nodes and signed receiver-side DBR readback, before any sharing cutover, public value functionality or claimed Type-1 Chain launch. **Drive sharing remains unchanged by owner direction.**

### Private offline hardening v2 — compatibility and recovery review

A second **owner-private** candidate patch was applied to a fresh copy of the exact historical COIN v0.1 archive and the complete offline suite passed: 24 schema definitions; **14/14** signed-ledger/SDK tests, including key-rotation, stale-lock, partial-record, concurrent-writer and CLI authority refusal cases; and 35 static Solidity policy checks. The original archive and Drive sharing were not changed. The patch and ledger implementation remain outside this public repository. No authorised key provider, durable transaction recovery, multi-node DBR finality or Solidity compilation/deployment was established. **Do not install this private candidate without separate native owner/issuer and rollback acceptance.**

### Private offline hardening v3 — signed-only operations and snapshot consistency

The privately retained v3 hardening candidate was independently reapplied to the **exact pinned historical v0.1 archive** and re-tested offline: **19/19** ledger/SDK tests, 24 schema definitions, 35 static Solidity sources and all disabled production/value feature gates pass. Source-level changes additionally make unsigned/structural inspection read-only, refuse authenticated snapshot output for stale journal state, reject overwriting existing snapshots and flush signed journal/snapshot data before reporting success. This candidate remains a private patch and carries an explicit non-deployment/issuer hold; the historical Drive archive, shared permissions, installed host, native DBR and node identities remain unchanged.

**Still required:** reconcile live accepted key/issuer and revocation authority; Windows filesystem-lock/crash recovery acceptance; backed-up restore and protected consumer parity; signed two-device receiver readback and replay/finality checks; pinned private Solidity compilation and independent security review. Passing isolated archive tests must not be presented as production-chain finality or a deployed Type-1 network.
