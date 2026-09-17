# CGX Composition v0.1

A CGX filespace may contain or reference other independently identified CGX filespaces.

Child modes:
- **EMBED** — child carrier bytes are physically included; child identity remains independent.
- **REFERENCE** — locator/object identity is retained without requiring a fixed child state.
- **PIN** — relationship requires the recorded exact child Object_ID + state/content/DBR roots.
- **TRACK** — relationship follows the currently authorised state of the child and must generate a parent state transition when refreshed.

The parent never absorbs the child identity. Parent topology stores a child descriptor and aggregate summary. Embedded child verification checks child Object_ID and content root against the descriptor before use.
