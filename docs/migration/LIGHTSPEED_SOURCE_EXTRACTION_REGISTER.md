# LightSpeed Historical Source Extraction Register

Generated from the completed physical-file inventory on 2026-07-05. Junctions
and symbolic links were not followed.

## Authority

- Canonical runtime: `C:\LightSpeed_Consolidated`
- Historical review output:
  `C:\LightSpeed_Consolidated\Sources\Historical LightSpeed`
- Detailed inventory:
  `C:\LightSpeed_Consolidated\_migration\historical_inventory\lightspeed_inventory_20260705T020812Z.jsonl`
- Machine summary: `data/migration/source_roots.json`
- Inventory SHA-256:
  `856FA00C04394AB739B6646DA122E93FCCBC8A7BA57F0382C790A031C51E1BC0`
- Summary SHA-256:
  `EB832B04F59CB8F0367F24170C65A60FDAE87D6021B8C583F42989FDA0A63A05`

## Totals

| Measure | Result |
| --- | ---: |
| Physical files inventoried | 620,474 |
| Bytes inventoried | 151,262,329,743 |
| GiB inventoried | 140.874 |
| Canonical source/document hashes | 13,236 |
| Historical unique hashes | 14,933 |
| Generated/archive files aggregated | 601,314 |
| Aggregate records written | 274 |
| Detailed inventory records | 19,683 |
| Review candidates | 203 |
| Newly extracted this run | 60 |
| Review output files after reconciliation | 203 |
| Review output bytes | 17,273,663 |
| Read errors | 249 |
| Scan duration | 3,642.572 seconds |

The first unbounded attempt was stopped after it reproduced the legacy
one-record-per-manifest problem. The completed pass aggregates generated and
archive streams by root, owner, classification, and extension while retaining
exact counts, bytes, date bounds, and sample paths. Source, document, model,
database, dataset, and other integrity-sensitive records retain file-level
metadata and checksums.

## Roots

| Root | Files | Bytes | Extract candidates | Existing references | Inventory only | Newly copied |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `C:\Cognigrex\LightSpeed Consolidated` | 13 | 130,882 | 9 | 2 | 2 | 0 |
| `C:\Users\acc\Desktop\LightSpeed Consolidated` | 619,995 | 151,072,698,181 | 179 | 16,632 | 603,184 | 45 |
| `C:\LightSpeed_Isolated` | 377 | 45,497,829 | 4 | 2 | 371 | 4 |
| `C:\Users\acc\Desktop\EMC^2; LightSpeed` | 89 | 144,002,851 | 11 | 48 | 30 | 11 |
| `C:\Users\acc\Desktop\EMC^^2; LightSpeed` | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | **620,474** | **151,262,329,743** | **203** | **16,684** | **603,587** | **60** |

## Classifications

| Classification | Files | Disposition |
| --- | ---: | --- |
| Archive | 598,048 | Aggregated inventory only |
| Source | 13,134 | Hash, compare, and extract unique candidates |
| Other | 4,396 | File-level integrity inventory |
| Generated | 3,266 | Aggregated inventory only |
| Document | 1,463 | Hash, compare, and extract unique candidates |
| Model | 104 | File-level integrity inventory; never Git |
| Dataset | 47 | File-level integrity inventory; never Git |
| Database | 16 | File-level integrity inventory; never Git |

## Error Boundary

All 249 errors are `WinError 3` records from the Desktop historical root. Their
paths are 260-293 characters long; 206 are under the legacy Hubble archive.
These entries were discovered during physical traversal but could not be
opened through the current Windows long-path policy. They remain unresolved
inventory exceptions and were not interpreted as missing evidence.

## Retirement Gate

No historical root is approved for deletion by this pass. Retirement requires:

1. Resolve or deliberately waive all 249 long-path exceptions.
2. Verify a second independent recoverable copy for empirical data, models,
   databases, and datasets.
3. Review the 203 extracted source/document candidates against current
   canonical code.
4. Record a deletion receipt per retired root.

The completed inventory and extraction are evidence for review, not permission
to remove the source roots.
