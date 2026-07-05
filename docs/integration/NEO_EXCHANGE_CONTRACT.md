# Neo Exchange Contract

## Authority

Neo owns Desktop coordination. The local SQLite store is machine authority, Drive
holds approved inter-platform memory, and Git carries only source, schemas,
manifests, and sanitized public projections.

LS GO and LS Web may read `neo_exchange.json`. They do not execute Desktop tasks
and do not read private Drive payloads directly.

## Public Record

Each queue row may contain:

- `id`
- `title`
- `priority`: `critical`, `high`, `normal`, or `low`
- `status`: `queued`, `active`, `review`, `blocked`, or `complete`
- `source`
- `target`
- `created_utc`
- `extensions.icon`
- `extensions.age_label`
- `notes`

The browser normalizer drops every unrecognized field. Local paths, Drive URLs,
private payloads, credentials, tokens, and unrestricted extension objects are
therefore not projected.

## Write Flow

1. LS GO or LS Web records a request in its own governed Drive exchange workbook.
2. Neo reviews the request and records the authoritative state locally.
3. Approved public-safe status is exported to `neo_exchange.json`.
4. Git publishes the static projection.
5. LS GO and LS Web render counts, age, source, target, priority, and status.

Private details remain in Drive under their owning agent or application folder and
are referenced internally by stable IDs. The Construct remains Desktop-only.
