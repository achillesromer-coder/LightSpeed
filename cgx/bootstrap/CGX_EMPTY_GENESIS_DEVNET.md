# CGX empty-genesis local devnet — review-only deployment

This is a **single-node, genesis-only, read-only development service** inside the existing CGX bootstrap architecture. It is not an independent blockchain, consensus network, mint issuer, operational DBR, decentralised DataSpace, source licence, authority lease, or public deployment. The parent stays `cgx:root:cognigrex`; `LOAD.cgx` remains sole resolver.

## Host layout

* Source: `cgx/bootstrap/cgxEmptyGenesisDevnet.py` (Git-authored on the existing review branch).
* Installed local copy: `C:\CGX\Cognigrex\Runtime\Devnet\cgxEmptyGenesisDevnet.py` (a deployment copy only; verify its SHA-256 against the committed source before every launch).
* Review-only state: `C:\CGX\Cognigrex\State\Review\EmptyGenesisDevnet\genesis.json`.
* Loopback-only HTTP: `127.0.0.1:18841`, endpoints `/health`, `/status`, `/genesis`; all non-GET methods return **405**. No public bind, wallet, token, Object_ID mint, transaction submission, private-source retrieval, DBR or multi-node API exists.

## Acceptance / lifecycle

1. Fetch the exact current reviewed Git commit. Run Python 3.11 unit tests and the full bootstrap/LOAD regression suite; require hosted CI before asserting code-reviewed.
2. Check the installed copy is byte-identical to the committed source. Inspect whether port 18841 and the state file already exist; do not overwrite either or terminate another owner process.
3. Exclusively initialise genesis once, then verify it twice. Genesis contains exactly **zero transactions, zero objects, zero mints, zero accounts**; deterministic SHA-256, no configured issuer, no signature, no consensus.
4. Launch only the local Python process under the existing CGX runtime root. Perform unauthenticated loopback GET readback of `/health`, `/status` and `/genesis`, and reject POST `/mint`, DELETE, private paths, bad hashes or changed block counts. Capture process identity and source version in a private receipt.
5. Use source-review results only. Rights/ACL, signed RootAuthority, issuer, independent DBR, inter-node consistency, consensus/finality and live UniSpace production reopening remain **HOLD**. This local devnet must not satisfy a native-gate checklist by itself.
6. Rollback: stop only the PID whose exact command line and installed digest match the recorded service; leave original genesis and audit receipts intact. Never delete without separate owner-approved archive/recovery proof.

A future CGX Type-1 contract may supersede this **test harness** after a real native protocol, independent validators, authentication, key custody, revocation and audited consensus are defined. Do not substitute an EVM or ERC-1155 contract merely because this harness runs.
