# Asteroid Cluster Sequence Operations Scaffold

## Status

This scaffold is an LS operations workspace path for the asteroid workbook. It is intended to be deployable once connected to the chosen web/app runtime, but it contains no secret values and performs no deployment by itself.

## Canon source

Workbook:
https://docs.google.com/spreadsheets/d/148UObDgK_YsqHDbIkJo89yDvyDcgySTE4wQMEVGwga8/edit

Primary workbook surfaces:

- `System Operating Register`
- `Credential Reference Register`
- `Mining Capacity Model`
- `Cluster Sequence Optimiser`
- `Mission 1 Source Capture`
- `Mission 1 Scenario Matrix`
- `Appendix & Log`
- `Publish Review Queue`

## LS role split

| Surface | Role |
|---|---|
| LS Desktop | CPU / analysis / Neo persistence |
| LS Go | Control and review |
| romer.industries | Public/front-facing outputs |
| romer.industries/operations | Operations workspaces, tools and consoles |
| GitHub | Operational RAM, routing, schema and code |
| Drive | Durable source, workbook and portfolio layer |
| Cognigrex | Cross-analysis host under LightSpeed |

## Initial workspace panels

The `/operations` workspace should expose these panels first:

1. Cluster sequence table
2. Mining capacity model
3. Source capture status
4. Conflict and missing-field queue
5. Publish review queue
6. Credential reference status with no secret values

## Data contract

Read from reviewed exports or API/database mirrors of:

- `Cluster Sequence Optimiser`
- `Mining Capacity Model`
- `Mission 1 Source Capture`
- `Appendix & Log`
- `Publish Review Queue`

## Guardrails

- Do not place secret values in this repository.
- Use deployment provider environment variables or secret references.
- Keep Drive as canonical durable workbook/source surface until a database mirror is active.
- Keep Git as routing and implementation memory, not as the only store.
- Queue public-facing material through `Publish Review Queue`.

## Next implementation steps

1. Add data-loader module once export/API path is confirmed.
2. Add dashboard components for capacity, cluster sequence and source capture status.
3. Add read-only operations route under `/operations`.
4. Add write-back only after audit and queue logic exist.
