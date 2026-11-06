# LOAD manual pre-mint preparation

The existing Objects view now supports a local LOAD reference workflow:

1. Import the existing `CGX-ONE-LOAD-INTAKE/0.17` JSON index, using Choose File or
   Paste local JSON. Files are parsed locally; no provider upload occurs.
2. Search and inspect exact source references, locators, digest claims and owner
   routes. Selecting a reference does not accept its rights or native identity.
3. Select references, choose a bounded batch size, and prepare an unsigned draft.
4. Export the draft. Re-import it to verify the reconstructed plan and policy.

The full existing index contains 996 pointers. At the current source snapshot,
141 carry syntactically valid source hashes; these hashes are not independent
source-byte or rights verification. With 25 entries per batch, the deterministic
plan contains 40 linked batches. Unknown source versions and native Object_IDs
remain null. A receipt locator is retained as a claim, never treated as a digest.

The draft is an off-chain metadata preparation artefact. Chain ID, contract,
ABI digest, issuer, fees, nonce, transaction bytes and signature remain unset.
There is no signing API, RPC connection, broadcaster or automatic launch trigger.
Exact chain binding and fresh independent source/rights/issuer/lease/DBR acceptance
are required before a future contract adapter can construct a transaction.

The existing LOAD leaf/facet bridge continues to own authenticated source
hydration. This view adds neither an Object_ID resolver nor a source store.
The existing `cgx_dynamic_batch.py` runner selects the new browser regressions and
existing packaging suites; no scheduler or execution worker is added.

Manual browser acceptance covered import, inspection, selection, preparation,
download, restore and denial of an edited broadcast flag on a two-reference
slice. Full-index preparation and restore were separately checked in Node.
Native file selection automation was blocked by Chrome extension file-URL
permissions; no permission was changed. Full authenticated native hydration,
issuer/DBR acceptance and deployed/public readiness remain unverified.
