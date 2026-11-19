# UniSpace

UniSpace is a local-first workspace for tracing a source through a specialist's
review and back to the evidence behind a result. The downloadable `.cgx`
reference lets a reviewer verify the archive offline. The November release
candidate connects the agent catalogue, carrier families and task checkpoints
to one LightSpeed runtime. Its review interface derives each role's controls
from the registered capabilities and shows which actions need approval.

The [native integration and launch record](../docs/architecture/UNISPACE_CGX_NATIVE_OPERATIONAL_LINK_20261118.md)
describes what an operator can verify in source, what requires installation,
and which capabilities still need live acceptance. Network identity, LOAD,
physical print and autonomous agent scheduling remain development targets.

This is the product entry folder. `CGX.cgx` is the exact owner-designated S91
product reference, published with explicit owner permission. It contains the
existing archive, specifications, implementation, tests and frontier records.
The carrier's licence and third-party notices remain unchanged.

From the repository root, verify it without running embedded code:

```text
python tools/verify_unispace_product.py
```

The verifier checks the exact outer hash, ZIP integrity and tracked member hashes.
It does not establish signed ancestry, runtime acceptance, semantic admission or
completion of the product. The carrier remains a pre-alpha reference snapshot.
Product source development is in `apps/lightspeed-go`; LightSpeed remains the
operational toolkit in `desktop/LightSpeed_Runtime`. `product.json` connects
these existing sources without duplicating them into another runtime.

On the owner host, `C:\UniSpace` is the primary folder entry for `C:\CGX`.
Existing compatibility paths remain in place. `Cognigrex.cgx` is the operational
S92 carrier; the product S91 snapshot does not replace it. D-drive LightSpeed
runtime bindings, local models, databases, intake and oversight stay host-local.
The published carrier does not contain the subsequent local intake corpus.

LOAD/Alexandria, UniSpace and UniGO dedicated child carriers remain pending
construction and acceptance. Existing frontier states in the carrier are
historical evidence to reconcile, not newly executed work. Packaging this file
does not activate plugins, install applications or clear runtime holds.
