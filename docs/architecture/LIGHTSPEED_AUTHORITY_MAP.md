# LightSpeed Authority Map

## System Boundaries

| Boundary | Authority | Permitted content | Prohibited content |
| --- | --- | --- | --- |
| Operator namespace | `D:\LightSpeed_Consolidated` | Stable launch paths, operator tooling, projects and junctioned runtime surfaces | Treating a junction as an independent copy or backup |
| Physical backing | `C:\LightSpeed_Consolidated` | Executable runtime, SQLite machine state, local models, empirical inputs, bounded recovery evidence, secrets, active data and Git worktrees | Running it as a competing second LightSpeed installation |
| Drive | Approved LightSpeed folders and workbooks | Approved inter-platform knowledge, human-review projections, landing files, links, classifications, and receipts | Secrets, model weights, raw runtime state, unrestricted empirical data, or The Construct memory |
| Git | Canonical LightSpeed repository | Source, tests, configuration, schemas, manifests, architecture documents, and public-safe queue summaries | Runtime databases, logs, archives, virtual environments, model weights, empirical datasets, secrets, or restricted payloads |

The interactive Desktop runtime never invokes Git directly. Reviewed source is
promoted from the canonical Git worktree through the maintenance/launch layer.
Neo reconciles approved local and Drive state through explicit manifests and
receipts. A Git commit is a publication action, not a runtime persistence
mechanism.

## Canonical Storage Topology

`D:\LightSpeed_Consolidated` is the path operators and launchers use.
`C:\LightSpeed_Consolidated` currently stores the physical content for the
junctioned `Agents`, `Apps`, `Desktop_Hooks`, `LightSpeed_Runtime`, `Logs`,
`Sources`, `venv`, migration and worktree surfaces. Removing either side of a
junction does not create or remove a second copy; backup proof must point to a
different physical store such as a verified remote Git object or approved Drive
artifact. The desktop shortcut targets the D-side launcher.

## Neo And Floor Topology

Neo owns the `N. LightSpeed` Drive landing and the cross-floor index. Persistent
Drive workbooks exist for Trinity, Architect, Morpheus, Oracle, Smith, and
Merovingian. Each fact has one owning floor; other floors link to that record
rather than duplicate it.

The Construct is Desktop-bound, receives no Drive memory workbook, and is not an
inter-platform knowledge surface. Achilles and Athene remain under LS GO.
Athene receives only material approved for public release.

## Classification Rules

Every synchronized or shared record has a release class and an evidence grade.
Release classes are:

- `Public`: suitable for Git, LS GO, LS Web, and Athene after review.
- `Internal`: permitted on the canonical Desktop and approved Drive locations,
  but not in public Git payloads.
- `Restricted`: limited to specifically approved local or Drive owners; never
  enters public Git or Athene.
- `Secret`: local secret storage only; never enters Drive or Git.

Evidence grades are `Known`, `Derived`, `Hypothesis`, `Conceptual Model`, and
`Requires Validation`. Derived and speculative material must retain its source
link, owner, review status, and next validation action. Evidence grade never
overrides release class.

Source synchronization is allowlist-only. Configuration publication names each
stable contract file explicitly; directories containing personal, setup,
runtime, generated, receipt, credential, token, or secret state are never
recursive roots. Mandatory deny patterns apply even to approved extensions.
Paths must be relative, contained, free of blocked runtime segments and reparse
points, and use an approved extension. Z-floor source is admitted file by file
only after release classification. Source files and manifests use guarded
temporary files with destination revalidation immediately before atomic
replacement. Manifests carry relative paths, SHA-256 hashes, and byte sizes;
they carry no secret or unrestricted runtime payload.

## Two-Copy Policy

No cleanup, replacement, quarantine expiry, or historical-root retirement may
remove the last recoverable instance. Before removal:

1. Classify the artifact and identify its owning authority.
2. Record the path, byte size, SHA-256 digest, disposition, and second-copy
   location in a manifest.
3. Verify two independent recoverable copies with matching digests.
4. Quarantine first, then remove only under the applicable retention rule.

A junction, shortcut, manifest, source link, or second path to the same physical
storage is not a second copy. Git qualifies only for committed and remotely
verified source that is allowed in Git. Drive qualifies only after upload and
re-read verification. Restricted, secret, model, database, and empirical
artifacts require an approved non-Git recovery copy.
