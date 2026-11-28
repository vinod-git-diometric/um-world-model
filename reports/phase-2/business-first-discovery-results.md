# Stoneham Phase 2.1 — Business-first discovery

## Live rerun on November 27, 2026

The updated policy enabled the pinned Overture Places acquisition and all three merchant controls. **The review targets remain unmet.** The live run independently corroborated three advertised premises, verified their merchant sites, and completed three scoped digital capability reviews. It found 944 distinct provisional Places name-and-civic keys without exact baseline overlap. This figure is a discovery lead count. Gate A and the physical graph remain unchanged.

### Preflight and acquisition

The Overture catalog and release index, AWS regional object listing, Azure container listing, Chamber participating directory, and all three merchant homepages returned HTTP 200. The Chamber member directory returned HTTP 503 twice, with an upstream connection reset. The working Chamber page yielded 19 entries with Stoneham civic-address leads after excluding the listed Winchester address and the entry without a civic address.

The existing `--fetch` command reached the official client, but its native Arrow S3 `HeadObject` failed on DNS resolution. The same authorized AWS HTTPS host accepted ranged reads through the managed proxy. A one-off local acquisition command read the pinned STAC index, selected its sole intersecting Places Parquet object, then read four row groups with intersecting bbox statistics through verified HTTP 206 responses. The 10 ranges transferred 8,358,532 bytes. It selected 1,658 bbox points, and the existing pipeline applied the official Stoneham polygon and candidate rules. The catalog-selected asset, index and release were kept fixed. No production code or access controls changed. [Pinned index](https://stac.overturemaps.org/2026-11-18.0/collections.parquet)

| Live Places result | Count |
| --- | ---: |
| Points screened | 1,658 |
| Outside the official Stoneham polygon | 318 |
| Inside the polygon | 1,340 |
| Business candidate rows | 992 |
| Explicitly noncommercial exclusions | 46 |
| Taxonomy review queue | 273 |
| Reported closed, pending review | 29 |
| Exact baseline overlaps accepted by the pipeline | 16 |
| Ambiguous baseline overlaps | 2 |
| Candidate rows with unresolved identity or civic key | 14 |
| Nonoverlap candidate rows with a civic key | 960 |
| Distinct provisional nonoverlap name-and-civic keys | 944 |

Within the polygon, 259 records lacked websites, 297 lacked reported operating status, and 33 lacked both basic category and taxonomy. No record lacked a primary name, address array, source array or confidence value. Presence of an address array does not imply an unambiguous civic match. Among the 992 business candidate rows, 817 had a website lead. Such leads can point to directories, marketplaces, or shared sites and require identity verification. Places carries explicit source lineage, including upstream Meta and BrightQuery records. No inferred source independence or current operation was credited to a Places listing.

### Merchant controls and baseline discovery

Each control's published identity and Stoneham civic address matched the separate Chamber participating listing. All three corroborated premises linked to the physical graph's parcel results. These are corroborated **advertised** premises. No dated operating event or direct merchant occupancy confirmation was collected.

| Merchant | Observed first-party evidence | Advertised paths still requiring external verification |
| --- | --- | --- |
| [The Book Oasis](https://thebookoasis.com/) | 311 Main Street; store-hours grid; books, gifts and games; curated lists, book inquiry form, Facebook and Instagram links | Bookshop.org and Libro.fm storefront links; Square e-gift card order link |
| [Gaetano's](https://www.gaetanosfood.com/) | 271 Main Street; posted hours; restaurant and catering offerings; priced menu, marketplace and social links | ChowNow delivery and OpenTable reservations |
| [Patina'd](https://www.patinadstore.com/) | 379 Main Street; posted winter hours; vintage and decorative wares; priced product catalog, public Add to Cart control, social links | Checkout untested; no transaction or account action taken |

Of the original 70 candidates, 16 matched a Chamber listing by name and civic key, 18 had a Places name-and-civic match (16 accepted baseline overlaps and two ambiguous cases), and 26 matched either source. Twenty-three had URL leads, including the three verified controls. Forty-four lacked a match in these queried sources and 47 had no URL lead. The 20 other URL leads received no completed first-party review. The 976 additional candidate case records received their Places disposition and provenance. They were not individually reviewed on merchant sites. No list or catalog match was counted as current occupancy.

| Existing target | Live outcome |
| --- | --- |
| Evaluate the original 70 | 70/70 checked against the live discovery sources; 3/70 completed merchant reviews |
| Independently corroborate 50 business locations | 3 advertised premises; 0 merchant-confirmed current occupancies |
| Verify 30 merchant sites | 3 |
| Complete 30 digital assessments | 3 scoped first-party reviews; external transaction paths remain unverified |
| Link 90% of corroborated premises to parcels | 3/3 (100%), with a denominator of three |
| Maintain 100% evidence provenance | 1,046/1,046 case records retain a source observation or pinned Places ID; all 45 reviewed fields validated against retained snapshot hashes |

Observed digital distribution is three official sites, three catalogs, three social presences, two marketplace-link fields, and one inquiry form. Zero ordering, checkout, and booking flows were verified. A public product cart control is evidence of an advertised interaction, with checkout still unobserved. The inherited Phase 2 receipts were preserved. Row-level Places data, HTML and review records remain in ignored local storage.

### One follow-up access request

One additive restricted-network draft was saved for review and publication. It retains the active allowlist and adds 29 exact hosts linked by the original-cohort discovery sources or advertised transaction pages. It covers base and observed www variants where distinct, without adding wildcards. The new rules were not active during this run. Representative merchant and transaction checks returned CONNECT 403, including `bodymindsystems.com`, `www.rapidliquors.com`, `bookshop.org`, `ordering.chownow.com`, and `www.opentable.com`. The Chamber directory is already allowed, so its 503 is an upstream availability issue.

Requested hosts are `bodymindsystems.com`, `ceramicapaintstudio.com`, `christinessweetshoppe.com`, `eyogamoves.com`, `jandbbutcher.com`, `linktr.ee`, `naturalfoodexchange.com`, `nobilityhilltavern.com`, `order.toasttab.com`, `pignonescafe.com`, `redlotusnailsnspa.com`, `thedirtydoodle.com`, `theenergybarre.com`, `thestonescommonhouse.com`, `thewinecellarsma.com`, `www.arborsassistedliving.com`, `www.ceramicapaintstudio.com`, `www.evvivatrattoria.com`, `www.groupon.com`, `www.rapidliquors.com`, `www.redstoneliquors.com`, `www.thedirtydoodle.com`, `www.thestonescommonhouse.com`, `www.ymcametronorth.org`, `bookshop.org`, `squareup.com`, `libro.fm`, `ordering.chownow.com`, and `www.opentable.com`.

No paid API or paid search product was used. The pinned HTTPS ranges transferred 8.36 MB and the retained merchant and Chamber HTML totals 5.35 MB. The existing manual-review and monthly-refresh assumptions below still apply. The data hash is `51646bb42dae8ab21ffede156b09c6219efaccbe1b1d64eca06146cc63580b99` and the STAC index hash is `1291c9621e79c3fa65a029621ce2474fb235dbcc10aa18e7a7f323dff3f10b1c`. The live evaluation is retained under `data/phase21/live-final-v2.json`. Stop for review.

---

## Prior run and methodology (commit `f77f7dd`)

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
