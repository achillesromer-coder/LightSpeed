# CGX TRACK Child Semantics v0.1

A `TRACK` relationship follows an authorised living child while preserving child identity. The parent stores the child's Object_ID, observed State_ID/content root/DBR root, and a source locator. Refresh is permitted only when the resolved source has the same Object_ID. A different Object_ID is an identity break, not an update.

`TRACK` differs from:
- `PIN`: exact child state/root required.
- `REFERENCE`: locator/identity known without automatic state following.
- `EMBED`: child carrier physically retained in the parent.

The v0.1 reference implementation performs explicit refresh against a locally addressable child source. Network resolver authority, signatures, leases, multi-source corroboration and semantic merge of changed child interfaces remain later layers.
