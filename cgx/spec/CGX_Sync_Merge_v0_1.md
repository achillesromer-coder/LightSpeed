# CGX Branch and Semantic Merge v0.1

## Branch model
A branch is a non-canonical working overlay rooted at a canonical State_ID/content root. It stores base path hashes and proposed operations while immutable source/proposed bytes are retained in the content-addressed blob store. Creating or editing a branch does not alter the canonical content root.

## Three-way merge
At merge, each touched path is compared as Base / Current / Proposed.
- If Current still equals Base, Proposed can apply.
- If Current already equals Proposed, the operation is satisfied.
- If both changed, the handler attempts a type-aware merge where one exists.
- Otherwise the path remains an explicit conflict.

## JSON semantic baseline
The v0.1 implementation recursively merges JSON objects. Independent key changes are combined. Competing changes to the same scalar/key are reported with field paths such as `$.a`; no last-writer-wins fallback is applied.

## Scope
This proves the merge grammar, not complete universal semantic merge. XLSX cells/formulas, documents, graph entities, CAD constraints, code ASTs and domain objects require registered type-specific merge handlers later.
