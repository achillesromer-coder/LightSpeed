# Local two-process CGX genesis attestation (review-only)

This module extends the **existing** genesis-only development service; it is not a new root, DBR, authority, chain or scheduler.

**Purpose:** an exact genesis source identity and read-only capability challenge signed by two separately generated Ed25519 *local review* identities. Neither key is a RootAuthority, mint issuer, custody credential or independent validator. Processes on one BouwerBase host share the same trust boundary; this is not two-node DBR qualification.

## Boundary

* Python source: `cgx/bootstrap/cgxGenesisPeerReview.py`; source dependency: `cryptography==48.0.0`, pinned for GitHub review CI.
* Local service copy: `C:\CGX\Cognigrex\Runtime\Devnet\cgxGenesisPeerReview.py`, only after exact committed Git blob validation.
* Genesis A: existing `C:\CGX\Cognigrex\State\Review\EmptyGenesisDevnet\genesis.json`. Genesis B: independent read-only copy with identical canonical digest in a separate `PeerReview\NodeB` private review path, not a new parent or chain.
* Two independently generated review keys: `review_node_a` and `review_node_b` in local, private, owner-access restricted `PeerReview\keys`. Never commit, copy into a public web directory, or treat these as production security keys. Keep their exact public pins outside Git as private reviewer receipts. Inspect file ACLs before any continued deployment.
* Server B accepts **only** exactly pinned client A's Ed25519-signed 20-second `genesis.readonly` request. A pins B's public key and independently verifies B's Ed25519-signed response, scope, challenge nonce, expiry, chain and genesis digest. A source readback is repeated after successful response. Nonces are held in a bounded replay cache.
* B binds only `127.0.0.1:18842`, GET `/health`, POST `/attest`. All other paths and transaction methods are denied. No listener is ever started on another interface.
* No signed RootAuthority, issuer, token, Object_ID admission, consensus, validator/finality vote, operational lease, credential delegation, independent DBR, network transport beyond loopback, or mint transaction exists. These remain **HOLD**.

## Manual operator lifecycle (only after CI)

1. Verify exact committed source hashes and pristine local test fixture. Use Python 3.11 and the pinned cryptography dependency.
2. Refuse existing keys/state/occupied 18842. Create review identities exclusively, record public key pins and restrictive ACLs. Do not use any existing issuer/root-authority keys.
3. Copy the original genesis bytes to Node B under a separate local private review path, checking identical SHA-256 and exact `genesis_sha256`; do not edit original genesis.
4. Start B as a separate Python process with its private review key and explicitly pinned A public key. Run A's probe with its own key, independent original genesis path and pinned B public key.
5. Verify signed proof in A, check exact digest, nonces, expiry, false authority flags, read-only endpoints and deny unknown public key, replay, changed genesis, invalid scope and transaction endpoints.
6. Record source commit, public-key fingerprints, source digests, PID/creation time, resulting review proof and failures in **private** host receipts. Do not put private keys, raw ACLs or source content into Git or public UniSpace.
7. Stop/rollback only by comparing current PID, executable path, command and creation time against receipt; keep original source and audit records. Do not delete or auto-promote into native DBR.

This is a bounded **local authenticated-read rehearsal**. An independent node on a separately administered host/network with distinct owner/issuer/DBR evidence and signed approvals is still required before claiming decentralisation.
