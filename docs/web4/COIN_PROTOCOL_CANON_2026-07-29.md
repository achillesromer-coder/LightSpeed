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
