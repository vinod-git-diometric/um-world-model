# Gate A.2 — Authoritative linkage and independent validation

**Gate A remains open.** All 11,765 accepted hybrid links agree with the official MassGIS export. A municipal property-card comparison also found no wrong accepted results on its verified subset, but it does not supply 50 independently audited commercial premises. Independent address and parcel precision and recall remain unmeasured at the required scope. The resolver and the Gate A.1 output are unchanged.

## Official MassGIS linkage

The [official Stoneham point archive](https://s3.us-east-1.amazonaws.com/download.massgis.digital.mass.gov/shapefiles/mad/town_exports/addr_pts/AddressPts_M284.zip) returned HTTP 200. Its shapefile has 12,568 records in NAD83 / Massachusetts Mainland (EPSG:26986). The archive, DBF metadata, and XML creation and modified dates identify the November 23, 2026 export. The geometry-service snapshot was acquired November 27, 2026. Its parcel layer contains 8,000 FY2024 tax rows and 46 rows without a reported fiscal year. The fiscal year describes the assessment records, which can differ from the service retrieval date. [MassGIS address specification](https://www.mass.gov/info-details/massgis-data-master-address-data-basic-address-points)

All export rows had one populated, unique `ADDRESS_ID` and a populated `LOC_ID`. All 12,291 live `MASTER_ADDRESS_ID` values joined to the export with the same normalized civic number and street. A further 277 export IDs were absent from the hybrid cohort. Of 6,069 exported distinct `LOC_ID` values, 23 were absent from the parcel snapshot, affecting 278 export records, including 168 of the joined hybrid records. Missing keys may reflect vintage or coverage differences. The data do not establish which explanation applies to every missing parcel.

| Outcome on the frozen 12,291-record hybrid cohort | Records |
| --- | ---: |
| Accepted, exactly the official parcel set | 11,765 |
| Accepted, different official parcel set | 0 |
| Hybrid abstained, official ID present in parcel snapshot | 358 |
| Hybrid abstained, official ID absent from parcel snapshot | 168 |

Of the 358 abstentions with an available official parcel, 246 were uncorroborated building multipoints, 57 fell outside the mapped polygons, and 55 had text–spatial conflicts. Of the 168 absent-key cases, 109 had text–spatial conflicts, 58 were documented multi-property points, and one fell outside the mapped polygons. This identifies which abstentions could benefit from authoritative links and which first need a parcel crosswalk or a newer parcel snapshot. Both address representations are MassGIS products, and the exported links may themselves use spatial containment. The comparison provides upstream consistency evidence. It does not validate independent accuracy.

## Municipal assessor cohort

The [Stoneham Patriot Properties service](https://stoneham.patriotproperties.com/search.asp?clear=1) supported public address and commercial use-code queries. I followed property-card links and captured only civic locations, tax keys, assessment account identifiers, use classes, source URLs, and retrieval hashes in the local cohort. The card's location field was used for premises checks. The owner mailing address was excluded. An inspected card had a 2026 valuation, while the MassGIS tax rows are predominantly FY2024. The two sources share municipal assessor identifiers, and MassGIS documents that its standardized parcels use municipal assessment extracts. Agreement after projection through MassGIS `PROP_ID` therefore does not establish source independence. [MassGIS parcel specification](https://www.mass.gov/info-details/massgis-data-property-tax-parcels)

The audit frame contained 85 distinct normalized civic sites. Twenty-five came from ABCC licensing or the existing directory seed and 60 from the municipal commercial use-code lists. Fourteen sites had an ABCC lead. The municipal frame sampled retail, offices, warehouses, restaurants, condo classes, and properties with multiple matching cards. The selection used a fixed SHA-256 ranking within the leads and assessor frame. It was intentionally scoped to office and retail contexts alongside harder cases. The live Chamber directory and town assessor landing page remained blocked by the proxy. Alcohol-license leads represent a minority of the frame. Tenant counts and unit-level occupancies could not be established systematically from these sources.

I froze the municipal reference before comparing predictions at 08:54 EST on November 27, 2026. The verified subset contained 51 civic sites, including 42 assessor-only and nine external-lead sites. Four of the 51 were parking-only, two had multiple verified cards at the same civic key, and two had recorded condo building types. Twenty-eight of 85 leads had no exact assessor civic result, and six had more than five matching cards and were excluded under the retrieval cap. These exclusions can favor records with simpler address and parcel relationships. Six of the 51 verified sites had an ABCC lead and five had a directory-seed lead, with two overlapping. Only the nine externally led cases had any external premises corroboration, and their parcel labels still depend on the municipal assessor lineage. [ABCC source](https://www.mass.gov/info-details/abcc-active-licenses)

## Measurements and disagreement review

The civic check was an exact normalized number-and-street lookup against the separately read card location. It cannot detect unit or occupant errors, and conditioning on an exact municipal lookup inflates agreement. For parcel comparison, all address records matching the query had to accept the same physical parcel set. The selected physical parcel IDs were projected to the complete set of available municipal tax keys via `PROP_ID`; an unmappable prediction abstained. The table reports Wilson 95% intervals. Excluded cases are outside these descriptive denominators, and the intervals do not account for sampling bias or shared lineage.

| Municipal comparison | Verified sites | Accepted | Correct | Precision (95% CI) | Recall (95% CI) |
| --- | ---: | ---: | ---: | --- | --- |
| Exact civic address | 51 | 49 | 49 | 100% (92.7–100%) | 96.1% (86.8–98.9%) |
| Parcel tax-key set | 51 | 47 | 47 | 100% (92.4–100%) | 92.2% (81.5–96.9%) |
| External-lead subset, civic address | 9 | 9 | 9 | 100% (70.1–100%) | 100% (70.1–100%) |
| External-lead subset, parcel tax-key set | 9 | 9 | 9 | 100% (70.1–100%) | 100% (70.1–100%) |

Two verified retail sites had no exact civic address candidate in the frozen live address data. Two additional sites, a commercial condo/master parcel and a parking class site, had both spatial–text agreement and conflict among distinct address records for the same civic key. The case-level parcel aggregation abstained in both instances. No accepted assessor tax-key set disagreed. The results do not establish recall across true unit-level, multi-tenant, or ambiguous cases. No resolver change was made.

All 12,291 frozen hybrid outputs retained verified MassGIS source references (100%). All 51 verified municipal cohort entries carry card URLs, response hashes, and recorded civic locations and tax keys. Independent commercial validation still requires at least 50 premises with corroborating address evidence and a parcel reference whose lineage can be evaluated separately. The original requirements of at least 95% precision, at least 90% recall for each target, and 100% provenance remain in force.

## Reproducibility

The untouched Gate A.1 hybrid JSONL SHA-256 is `c8edc7f8521d951b7f3d1c868808fa54857faf4f1eefc321b9bdeb374d1cba89`. The local ignored audit directory `data/audit-a2/` contains the official ZIP (SHA-256 `549965cdb7323203c05ad633756c7ff40dd7c1825c50aca26d81e30e19cbb15d`) and frozen extended reference (SHA-256 `cb45b6ee9077eb767c71fccacbbe0177953131003be685719c8c1391d407fa31`). Only aggregate observations are committed. Use `linkage_validation.compare_linkage` on the shapefile attribute export and the Gate A.1 normalized directory, and `assessor_validation.assess_cohort` on the frozen reference and the same directory. Stop at Gate A.2.
