# Stoneham Gate A live results

**Decision: NOT MET.** Ingestion and the exploratory evaluation completed. The independent audit remains outstanding. Work stops at Gate A.

## Sources and reconciliation

Run `20261127T132415Z-d49fc52c` on November 27, 2026 used the [MassGIS address service](https://arcgisserver.digital.mass.gov/arcgisserver/rest/services/AGOL/MassGIS_Master_Address_Points/FeatureServer/0) and the [MassGIS parcel service](https://services1.arcgis.com/hGdibHYSPO59RG1h/ArcGIS/rest/services/Massachusetts_Property_Tax_Parcels/FeatureServer/0).

| Layer | Stoneham filter | Expected | Retrieved | Pages |
| --- | --- | ---: | ---: | ---: |
| Address points | `GEOGRAPHIC_TOWN_ID=284` | 12,291 | 12,291 | 7 |
| Parcel records | `TOWN_ID=284` | 8,046 | 8,046 | 5 |

Every feature had the expected town ID. Address fields were verified against the live schema, including `MASTER_ADDRESS_ID`, `FULL_NUMBER_STANDARDIZED`, `STREET_NAME`, and `UNIT`. The parcel rows contain 6,319 distinct `LOC_ID` values and 46 missing site addresses. Filters and row counts apply to the observed source snapshot.

## Resolution and evidence

- Exact normalized address accepted for 8,151 of 12,291 address records (66.3%), including 40 accepted results with multiple parcel IDs.
- 4,051 results retained fuzzy candidates for review. The remaining 89 had no candidate above the configured threshold. Together these are 4,140 unresolved results (33.7%).
- All 15 snapshot hashes verified. For each of the 12,291 results, every evidence reference matched its manifest source and hash and contained the referenced source record ID. Parcel evidence uses the source row's `OBJECTID` to distinguish records sharing a parcel ID.
- All 16 discovery-seed entries had exact address candidates. Five had multiple address candidates. Seven had an accepted parcel link, and nine had address candidates only. These are exploratory coverage figures.

## Independent benchmark

Zero independent labels were available. The town website returned a managed proxy 403. Address and parcel precision and recall, confidence intervals, and accuracy thresholds remain unmeasured. Exact string agreement can still produce incorrect or incomplete links. The current evaluator scores parcel link sets given an address ID. Gate A requires a separate address accuracy measurement as well.

## Reproduction

From the repository root with the development environment active, run `umwm ingest-town --town Stoneham --state MA`, `umwm normalize`, `umwm resolve`, then `umwm evaluate --output-dir /tmp/umwm-gate-a`. The manifest and row-level output are stored locally under the ignored `data/` directory. Only aggregate results are published here.
