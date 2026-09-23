# Manual vs pre-tailored child-filespace build

| Domain | Minimal/manual | Pre-tailored |
| --- | ---: | ---: |
| Römer | 23,419 B / 23 tracked | 45,378 B / 38 tracked |
| Eco | 23,337 B / 23 tracked | 45,281 B / 38 tracked |
| EMASSC | 23,479 B / 23 tracked | 45,454 B / 38 tracked |

All six generated carriers verified before packaging.

The manual method receives an external additions pack containing the same reusable profile/config paths. A simulated manual application produced hash parity with the pre-tailored profile set for all three domains.

Use **minimal/manual** when teaching CGX construction, auditing every installed profile, regulated setup, or deliberately bespoke deployments.

Use **pre-tailored** for normal Römer/Eco/EMASSC operation: it avoids repeated configuration while remaining a data-empty child filespace whose runtime/support resources hydrate from the trusted CGX master.

The comparison is about setup method, not competing object authority.
