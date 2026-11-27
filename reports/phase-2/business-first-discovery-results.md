# Stoneham Phase 2.1 — Business-first discovery

**The live discovery targets remain unmet.** All 70 baseline candidates received an evidence review disposition. The managed proxy blocked Overture data retrieval, both Chamber pages, and all three merchant positive controls. This run therefore added no independently corroborated premises or verified digital capabilities. The physical graph and Phase 2 baseline at `8667b54` remain unchanged. Gate A is formally unmet.

## Overture Places

The pinned release is **2026-11-18.0**, with Overture schema **v2.0.0** and official Python CLI **2.1.1**. Overture's public website was blocked, so the release notes and Places documentation were read at official docs commit `e4328d1`. The November Places schema uses `taxonomy` and `basic_category`. The release's `confidence` describes confidence in place existence. It cannot confirm present occupancy, hours, or commerce features. Overture documents CDLA-Permissive-2.0 and Apache-2.0 distribution and source-specific attribution, which must be retained as applicable. [Pinned release notes](https://github.com/OvertureMaps/docs/blob/e4328d1/blog/2026-11-18-release-notes.mdx) · [Places guide](https://docs.overturemaps.org/guides/places/) · [Cloud sources](https://docs.overturemaps.org/getting-data/)

The [MassGIS municipality areas service](https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/Massachusetts_Municipalities/FeatureServer/1) returned one valid Stoneham polygon for `TOWN_ID=284` as WGS 84 GeoJSON. Bounds are `-71.1217383966333,42.4439490456726,-71.0752415379305,42.5022508860433`. SHA-256 is `783bee9074e53a6d4b0d573e19df8985f593572f978073e4e841ca3d52ae20fd`. The implementation scopes the official CLI download to that bounding box, then applies exact polygon coverage to exclude neighboring points. It keeps GERS IDs, names, taxonomy, addresses, coordinates, websites, source lineage, confidence and reported operating status. Explicit noncommercial categories are excluded from candidate creation. Unknown categories and reported closures retain separate review dispositions. Candidate overlap uses normalized name and civic address and preserves unit uncertainty. Nonoverlap keys are provisional candidates pending identity verification.

The live extraction command stopped at the STAC HTTPS preflight with a managed CONNECT 403. The documented AWS and Azure data endpoints also returned CONNECT 403. A retry of the AWS endpoint under the approved execution mode returned the same denial. No Places snapshot was acquired.

| Overture result | Outcome |
| --- | --- |
| Total Stoneham places | Unmeasured |
| Noncommercial exclusions and candidate count | Unmeasured |
| Missing names, category, address, website, lineage and confidence | Unmeasured |
| Overlap with the original 70 and net-new candidates | Unmeasured |

Offline fixtures exercised neighbor exclusion, noncommercial filtering, and field retention. The reported table contains no fixture counts.

## Merchant discovery and evidence

The three controls were present in the original directory seed. Phase 2 created source-observation nodes from licenses, authorizations, facility lists, and a directory seed without merchant URLs. It did not have a merchant website discovery/review step. Digital fields in its graph were populated only when explicitly supplied by an observation. That design, combined with blocked merchant and directory endpoints, explains the earlier zero. The URLs supplied for this review were recorded as external leads. Their CONNECT failures reveal neither the live content nor whether the merchant is operating.

| Positive control | Result in the managed runtime |
| --- | --- |
| [The Book Oasis](https://thebookoasis.com/) | CONNECT 403, contents unobserved |
| [Gaetano's](https://www.gaetanosfood.com/) | CONNECT 403, contents unobserved |
| [Patina'd](https://www.patinadstore.com/) | CONNECT 403, contents unobserved |

The remaining 67 records had no verified merchant URL in the available observations, and both Chamber discovery routes were blocked. They received inventory/evidence triage. Individual website searches were not completed for those cases. No identity, advertised location, hours, offering, or transaction claim was extracted from a live merchant page.

Verified field records carry their source URL, lineage, observation timestamp, and a retained snapshot hash checked on import. The review distinguishes a listed business, independently corroborated advertised premises, recent dated operational evidence, explicit merchant occupancy confirmation, conflicting or stale evidence, and unknown status. Corroboration requires different source lineages and hosts and a consistent civic address. A reviewed website can establish a digital presence independently of the occupancy assessment. Hours, offerings and advertised location can be recorded as separate fields. Civic links require corroborated premises, and conflicting addresses or units retain review status.

| Phase 2.1 target | Actual |
| --- | --- |
| Evaluate 70 original candidates | 70/70 evidence triaged; 3 direct URL attempts blocked, 67 without a verified lead |
| 50 independently corroborated locations | 0 newly verified |
| Verify 30 merchant websites | 0 verified |
| Complete 30 digital capability assessments | 0 completed |
| 90% parcel linkage among corroborated businesses | Unmeasured (0 eligible); Phase 2's 62 provisional parcel links remain available |
| 100% evidence provenance | 70/70 case references resolved and all 71 inherited source hashes verified; no live merchant fields to validate |

Forty-two cases remain listed businesses and 28 have only stale source evidence under the baseline's age rules. The completed-assessment distribution has zero observations for official website, catalog, online ordering, ecommerce checkout, booking, inquiry form, marketplace link, and social presence. All eight capability statuses remain unverified across the cohort. A digital capability review must distinguish links or advertisements from observed public transaction pathways. No test purchases, logins or form submissions are required.

## Access, cost, and maintenance

| Needed access | Hostnames tested or needed | Observation |
| --- | --- | --- |
| Pinned Overture download | `stac.overturemaps.org`, `overturemaps-us-west-2.s3.us-west-2.amazonaws.com` | CONNECT 403; allow the documented catalog, regional S3 objects and approved redirects |
| Official Azure distribution | `overturemapswestus2.blob.core.windows.net` | CONNECT 403; optional official alternative |
| Public Overture docs | `docs.overturemaps.org` | CONNECT 403; official GitHub repository readable |
| Chamber member and participating directories | `business.stonehamchamber.org`, `stonehamchamber.org` | CONNECT 403 for both |
| Merchant controls | `thebookoasis.com`, `www.gaetanosfood.com`, `www.patinadstore.com` | CONNECT 403 for all three, including approved retries |
| Official boundary | `services1.arcgis.com` | HTTP 200 |
| DuckDB remote extension download | `extensions.duckdb.org` | CONNECT 403; unused by the chosen Python extraction route |

No billable API, paid search product, or merchant interaction was used. Observed API spend was $0. The scope acquired a 932-byte boundary, a public documentation checkout, and the Python client, with no bulk Places transfer. A future pass needs approved discovery domains, merchant hosts and any required checkout/booking hosts, with each site's terms and crawl policies honored. Add verified site observations one candidate at a time where restrictions require manual review. No policy changes were made.

For planning, 70 original leads at 5–10 minutes each for URL discovery and identity triage require roughly 6–12 person-hours, plus 5–8 hours for 30 capability reviews at 10–15 minutes each. Corroborating 50 premises at 10–20 minutes each would take about 8–17 hours and can overlap initial triage. These are assumptions, excluding net-new candidates and hard cases. Refresh the Overture release monthly, recheck merchant links and features quarterly, and record closures or moves only with dated supporting evidence.

## Reproduction

Install the `dev` and `business-first` extras and keep the project virtual environment on PATH. Store the authorized MassGIS GeoJSON and source captures under ignored `data/phase21/`. Once the existing network policy permits catalog and bucket access, run:

```sh
python -m um_world_model.business_first data/phase21/stoneham.geojson \
  --fetch data/phase21/overture-2026-11-18.0.geojsonseq
python -m um_world_model.business_first data/phase21/stoneham.geojson \
  --graphs data/phase2/build-3 \
  --places data/phase21/overture-2026-11-18.0.geojsonseq \
  --reviews data/phase21/merchant-reviews.json --output data/phase21/next-review.json
```

Omit `--places` for baseline-only triage. The review input is a JSON array of `MerchantReview` objects keyed by business ID, with the reviewed URL, check time, status, and field evidence. Field snapshot paths are relative to the review file and verified against their SHA-256. The observed attempt ledger and row-level outputs are local only. This report contains aggregate results. Work stops at Phase 2.1 for architectural review.
