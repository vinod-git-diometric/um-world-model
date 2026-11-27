# Stoneham Phase 2 commercial discovery

**Decision: experimental work under conditional proceed.** This run produced **70 deduplicated business-site candidates from 71 observations**, with 62 parcel links and zero independently confirmed current occupancies. The inventory covers the reachable source programs below. The total number of Stoneham businesses is unknown. Gate A remains formally unmet, and the results do not support a production-readiness claim.

## Physical substrate

The original [Gate A report](../gate-a/live-results.md), [Gate A.1 hybrid results](../gate-a/spatial-resolution-results.md), and [Gate A.2 validation](../gate-a/independent-validation-results.md) and their inputs remain unchanged. The new `physical-1.0` graph binds the November 23, 2026 address archive and its attribute export to the November 27 live geometry manifest and frozen hybrid output by SHA-256. Official `ADDRESS_ID → LOC_ID` is preferred when civic identity, source dates, and parcel references reconcile. The parcel rows retain their own vintage (FY2024 where available). A conflicting hybrid acceptance or multiple incompatible official links produces ambiguity. A missing official parcel remains an unresolved reference. Hybrid acceptance can supply a fallback when the official link is absent and the hybrid parcel is present. The graph retains hybrid reasons and candidate IDs.

The town archive contained 110 geographic records outside Stoneham (identified by `GEOTOWN_ID`). Scoping to 284 yielded 12,458 address nodes, including 167 export-only nodes. Of these, 12,290 have an accepted official link and 168 refer to a parcel absent from the captured layer. None required hybrid fallback on this snapshot. There are 6,319 parcel ID groups carrying 8,046 assessor rows, including stacked records. The resolver does not infer parcel ownership or choose a condominium tax account from the address alone. [MassGIS address documentation](https://www.mass.gov/info-details/massgis-data-master-address-data-basic-address-points)

## Sources and inventory

| Source | Stoneham observations | Distinct source business-site keys | Evidence boundary |
| --- | ---: | ---: | --- |
| ABCC retail licenses | 27 | 27 | Licensed premises and named holders, November 20 workbook |
| ABCC state licenses | 2 | 2 | Licensed premises and named holders, November 20 workbook |
| USDA FNS SNAP retailer locations | 13 | 13 | Authorized stores and program categories |
| Massachusetts licensed child care | 9 | 9 | Current center-based program entries in the source; home-based programs excluded |
| Massachusetts long-term care residences | 4 | 4 | Facility directory listings scoped by municipal address field |
| Existing directory seed | 16 | 16 | Undated, unverified discovery leads from the repository |
| **Total** | **71** | **71 before cross-source resolution** | |

The [MassGIS hospitals layer](https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/Massachusetts_Hospitals/FeatureServer/0) returned zero Stoneham rows. The [municipal assessment cards](https://stoneham.patriotproperties.com/search.asp?clear=1) were reachable and reserved for physical evaluation. Assessment class, owner and mailing address provide no storefront count. Live requests to the Chamber gift-certificate page and member directory, the Massachusetts corporate search, Stoneham business certificates and Board of Health, OpenStreetMap API, Overpass, and the Geofabrik Massachusetts download were denied by the environment proxy. Scoped probes for two first-party chain locator sites also returned proxy 403. No business counts are inferred for those sources. [ABCC workbooks](https://www.mass.gov/info-details/abcc-active-licenses) · [USDA FNS layer](https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services/snap_retailer_location_data/FeatureServer/0) · [Massachusetts child care layer](https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/Licensed_Child_Care_Programs/FeatureServer/0) · [Long-term care layer](https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/Long_Term_Care_Residences/FeatureServer/0)

## Commercial graph and resolution

The `commercial-1.0` graph stores source observations with source row IDs, URLs, timestamps and snapshot hashes, separately from Business, Occupancy, LegalEntity, DigitalProperty and BusinessCategory records. Normalized name, civic address and explicit unit form the conservative business-site key. One cross-source pair merged under this rule. Business-site keys can include aliases and count separate sites of one operator. The 29 legal-entity records are source-scoped ABCC license-holder claims. Registration and operator identity still require a registry crosswalk. Four civic keys retain multiple business or alias candidates. The graph keeps separate businesses and occupancy claims at those sites, supports dated historical occupancy, and retains underlying observations for review. The live inputs supplied no verified history or closure.

| Result | Count |
| --- | ---: |
| Candidate occupancies | 70 / 70 |
| Confirmed current occupancies | 0 / 70 |
| Specific address ID linked | 46 / 70 (65.7%) |
| Multiple address candidates or unit ambiguity | 18 / 70 |
| Explicit source unit unverified | 2 / 70 |
| No exact civic address candidate | 4 / 70 |
| Parcel linked | 62 / 70 (88.6%) |
| Verified digital presence | 0 / 70 |

A parcel can be linked when the remaining civic candidates all resolve to the same parcel set. A license, property classification, retailer authorization or directory entry alone does not confirm current occupancy. The graph flags 29 observations for re-verification (16 undated legacy leads and 13 care listings whose layer edit dates are more than 180 days old at retrieval). Age flags are not closure estimates. The 24 occupancies without a unique confirmed address ID include address and unit ambiguity. Shared civic keys may reflect multi-tenancy, multiple records for one tenant, or unresolved aliases. No inferred conflict was resolved through fuzzy name similarity.

Digital classifications support observed official websites, catalogs, ecommerce, ordering or reservations, and third-party marketplaces. No category had verified evidence on this run. All 70 are marked `no_verified_digital_presence`, a verification status. It does not imply that those businesses lack a website or digital services.

## Held-out evaluation and Gate A

The frozen Gate A.2 municipal frame was held out of commercial ingestion. From its 85 leads, the evaluation excluded 34 with unverified cards, 11 with external leads or discovery overlap, and four parking-only parcels. The remaining 36 sites had separate municipal card labels. Exact civic lookups and municipal tax-key sets each yielded 34 accepted, 34 matching and two unresolved results. Each comparison has 100% observed precision (Wilson 95% interval 89.8–100%) and 94.4% recall (81.9–98.5%). The assessor and MassGIS parcel inputs share municipal lineage, and the civic check is conditioned on assessor verification. These are held-out physical consistency measures. They cannot validate independent address or parcel accuracy or current commercial activity.

An independently corroborated 50-location commercial benchmark remains infeasible on the available evidence. There were zero independently confirmed occupancy labels. All 71 ingested observations retained a source receipt, and the held-out set retained its prior card evidence. These provenance checks do not change the original Gate A criteria of at least 95% precision, at least 90% recall separately for address and parcel resolution, and 100% provenance. No denominator supports a claim of town-wide business-population coverage.

## Maintenance and workload

Refresh ABCC and USDA authorizations monthly and MassGIS and care directories when their publishers release new snapshots. At each refresh, check field mappings, filters, row reconciliation, record recency and identifiers. Record source removals as missing observations until occupancy or closure is corroborated. Audit the older assessment vintage when new parcels or condominium keys appear. If source access changes, start with the Chamber directory and municipal records, then verify first-party operating locations and digital features. A first verification pass over 70 leads at an assumed 5–15 minutes each would take roughly **6–18 person-hours**. A 50-location structured audit at an assumed 15–30 minutes each would take **12.5–25 person-hours**. These planning estimates exclude access delays and field visits, and some work can overlap.

## Reproduction

Install the `dev` and `discovery` extras. Keep the captured raw files local and preserve acquisition times when copying snapshots. From the repository root, with the prepared inputs:

```sh
python -m um_world_model.phase2 \
  data/runs/20261127T133604Z-490a763e/manifest.json \
  data/audit-a2/official-addresses.csv data/audit-a2/AddressPts_M284.zip \
  data/phase2/sources evaluation/benchmark-businesses.csv data/phase2/rebuild \
  --export-vintage 2026-11-23
python -m um_world_model.phase2_evaluate \
  data/audit-a2/frozen-assessor-cohort-extended.json data/phase2/rebuild
```

This run's local JSON graphs are under `data/phase2/build-3`. The source directory contains the two November 20 ABCC workbooks and the scoped ArcGIS JSON query responses plus layer metadata, named by adapter. The ArcGIS captures used exact normalized Stoneham town fields and omitted geometry and contact columns. The frozen assessor reference, raw source snapshots and row-level commercial graph remain outside Git. Work stops at the Phase 2 report for architectural review.
