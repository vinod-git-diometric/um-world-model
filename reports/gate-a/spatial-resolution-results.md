# Gate A.1 — Stoneham spatial entity resolution

**Gate A verdict: NOT MET.** Live hybrid coverage increased to 95.7%, and all results traced to verified source records. Independent address and parcel accuracy remains unmeasured. The experiment stops at Gate A.1.

## Sources, existing links and geometry

The MassGIS Basic Address Points download specification defines `LOC_ID` as the identifier of the parcel containing the point. The live Master Address Points FeatureServer and MapServer layer schemas expose `MASTER_ADDRESS_ID`, `SITE_ID`, `UNIT`, `UNIT_TYPE`, and `POINT_TYPE`. Neither exposes `LOC_ID` or an ArcGIS relationship table. No documentation establishes `SITE_ID` as a parcel foreign key. The official `MAD_URLLINKS` catalog returned `AddressPts_M284.zip` for Stoneham, but the proxy rejected HTTPS CONNECT to its `s3.us-east-1.amazonaws.com` download host. The downloadable linkage could not be checked for population, vintage, or correspondence with the live parcel layer. If obtained, it is upstream MassGIS evidence and must stay separate from the independent audit. [Address specification](https://www.mass.gov/info-details/massgis-data-master-address-data-basic-address-points)

MassGIS documents a physical tax parcel linked by `LOC_ID` to potentially many assessor records, with stacked polygons for condominiums. The live parcel service had no relationship table. The resolver groups spatial candidates by parcel ID and keeps each assessor row's `OBJECTID`, `PROP_ID`, `MAP_PAR_ID`, and `POLY_TYPE`. Point unit and site fields stay on the address record. A parcel link does not establish unit-level ownership or a specific condo tax account. [Parcel specification](https://www.mass.gov/info-details/massgis-data-property-tax-parcels)

The v0.1 checkpoint at commit `3783dfb` and [its published results](live-results.md) remain the baseline. Baseline run `20261127T132415Z-d49fc52c` remains local. Its original resolution output SHA-256 is `79c2c2deaf626695bf86208764d92cccddeb1f1ab4c8f942d2ffc654b2c0c519`.

Geometry run `20261127T133604Z-490a763e` retrieved 12,291 address points in seven pages and 8,046 parcel rows in 17 pages, matching both live counts. All features were scoped to Stoneham (284). The service returned point x/y and polygon rings with explicit EPSG:4326 on every geometry page. All 8,046 parcel geometries parsed as valid. Raw local snapshots preserve rings, holes, multipart polygons, and the returned CRS. All 27 snapshot hashes verified.

## Same-snapshot comparison

Both methods ran on the geometry snapshot. Structured matching compares normalized house number and street. The hybrid accepts one strictly containing parcel when structured text and any official link are consistent. A nominally unique interior also requires corroboration for building multipoints (`BMP`). Dissolved multipoints documented as spanning multiple properties (`DBMP`) cannot be resolved to one parcel solely from the supplied point. The method retains conflicting or multiple candidate sets and abstains at exact boundaries. It uses no nearest-neighbor fallback or boundary buffer.

| Metric | Text only | Hybrid |
| --- | ---: | ---: |
| Accepted parcel results | 8,151 / 12,291 (66.3%) | 11,765 / 12,291 (95.7%) |
| Unresolved results | 4,140 | 526 |
| Source-record traceability | 12,291 / 12,291 in v0.1 | 12,291 / 12,291 on this run |
| CLI resolution wall time, one local run | 21.5 s | 4.3 s |

The hybrid recovered 3,831 text abstentions and withheld 217 text acceptances, a net gain of 3,614 records (+29.4 percentage points). The 7,934 results accepted by both methods had identical parcel sets. Hybrid abstentions comprised 246 uncorroborated building multipoints, 164 text/spatial conflicts, 58 documented multi-property points without a defensible single-parcel decision, and 58 points outside mapped parcels. No case was assigned an exact-boundary or distinct-parcel overlap reason. Some conflicts involve multipoint records, so the decision categories are exclusive. Two consecutive hybrid runs produced identical output hashes.

## The original 4,140 unresolved records

All 4,140 IDs were present in the new snapshot. Of these, 2,887 had a street represented in the parcel address index but no matching civic number; 1,253 had no exact street key in that index. A unit was present on 3,114 records. These patterns are consistent with site-address sparsity, alternate street labels, or many address points sharing one parcel site address. They do not identify the cause for each individual row.

| Hybrid evidence for the original cohort | Records |
| --- | ---: |
| Unique interior with no conflicting civic evidence | 3,831 |
| Building multipoint without civic corroboration | 246 |
| Outside mapped polygons | 57 |
| Documented multi-property point | 6 |

All 57 outside-polygon points in this cohort were building multipoints. MassGIS documents that some building multipoint centroids fall on streets, water, or other properties. This gives a specific diagnostic lead without assuming the parcel fabric is wrong.

## Commercial seed and independent audit

The existing seed remained separate from resolver rules. Sixteen of 16 entries had an exact address candidate in both runs, and five had multiple address candidates. Seven had a text-accepted parcel and 16 had a hybrid-accepted parcel across their address candidates. No seed entry had multiple distinct accepted hybrid parcels. These results describe coverage only.

The Stoneham assessor page and AxisGIS returned proxy 403. The state ABCC retail workbook was accessible and contained 27 Stoneham license rows with 27 distinct premise-address strings. The state-level workbook had two rows with an exact Stoneham field. These are candidate premises from an independent licensing source. The workbooks supply no surveyed parcel labels, and the retail filter is biased toward alcohol-licensed businesses. The state food-protection program page was accessible but yielded no verified Stoneham parcel labels. The 50-location independently audited set remains incomplete. The source workbooks are retained locally, outside Git. [ABCC workbooks](https://www.mass.gov/info-details/abcc-active-licenses)

| Independently auditable target | Sample | Precision | Recall | 95% interval |
| --- | ---: | --- | --- | --- |
| Address | 0 | Unmeasured | Unmeasured | Unavailable |
| Parcel | 0 | Unmeasured | Unmeasured | Unavailable |

The separate audit scorer reports exact-set precision over accepted predictions among auditable cases, recall over all auditable cases (including abstentions), and Wilson 95% intervals. The thresholds remain at least 50 independently audited commercial locations, at least 95% precision and at least 90% recall separately for addresses and parcels, and 100% provenance. Source agreement and coverage cannot satisfy the accuracy criteria.

## Reproduction

Install the existing `geo` and `dev` extras. Run `umwm ingest-town --parcel-geometry`, `umwm normalize`, `umwm resolve`, and `umwm resolve-spatial`. Pin each command after ingestion with `--manifest` to reproduce results on a particular snapshot. Run `umwm compare-spatial BASELINE_RESOLUTIONS_JSONL --manifest GEOMETRY_MANIFEST` for the aggregate comparison. Keep raw and row-level outputs under the ignored `data/` path.

Use `umwm score-audit REFERENCE_JSON PREDICTIONS_JSON` with JSON arrays keyed by unique `case_id`. Freeze independently sourced reference rows before prediction. Use canonical address values and parcel ID sets as string arrays under `address` and `parcel`, with corresponding `address_evidence` and `parcel_evidence` in the reference. Omit an unavailable target, and omit an abstained prediction. Report exclusions and justify the source independence and sampling design.
