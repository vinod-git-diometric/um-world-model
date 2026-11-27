# Stoneham digital readiness census — experimental sample

**Phase 2.1 stopped for review with its live targets still unmet.** The Overture HTTPS rerun reproduced the previously reviewed data byte for byte. All 60 frozen civic sites received an automated disposition. Within that cohort, zero merchant sites, independently corroborated premises, or complete capability assessments were verified. The active policy excluded the merchant hosts for 46 sites, and 14 had no usable first-party URL lead. The three known controls ran separately. Gate A remains formally open.

## Reproducible Places acquisition

The previous live results at `b9c78fb` and the `physical-1.0` graph are preserved. The physical graph SHA-256 remains `6c3f1dc18d360a6a01b64f9d9b59ca5d2510d2d5ba438c5ede8105f3876a4456`. The official Overture Arrow S3 client reached the pinned index but could not resolve the regional S3 hostname for `HeadObject` in the managed runtime. The reproducible acquisition uses the same catalog and the authorized official regional HTTPS host with the runtime proxy. It accepts only paths under the pinned Places prefix and checks the object ETag, `Content-Range`, byte counts and SHA-256 of each range. It selects row groups using bbox statistics, and the existing Phase 2.1 evaluator applies the official MassGIS Stoneham polygon. [Prior live results](business-first-discovery-results.md) · [Pinned STAC index](https://stac.overturemaps.org/2026-11-18.0/collections.parquet)

| Acquisition receipt | Measured |
| --- | --- |
| Release | `2026-11-18.0` |
| STAC index SHA-256 | `1291c9621e79c3fa65a029621ce2474fb235dbcc10aa18e7a7f323dff3f10b1c` |
| GeoJSON sequence SHA-256 | `51646bb42dae8ab21ffede156b09c6219efaccbe1b1d64eca06146cc63580b99` |
| Boundary SHA-256 | `783bee9074e53a6d4b0d573e19df8985f593572f978073e4e841ca3d52ae20fd` |
| Files and row groups | One Places object, groups 111, 122, 145 and 148 |
| Output | 1,658 bbox rows; the prior run classified 1,340 as in town, 992 as commercial candidate rows and 944 as distinct provisional nonoverlap civic/name keys |
| Transfer and compute | 10 ranges totaling 8,358,532 bytes plus 152,222 index bytes; 12.31 s wall, 1.05 s process CPU, 260 MiB peak RSS |

## Frozen cohort and acceptance

Case selection used a fixed hash order after civic eligibility checks. No merchant retrieval outcome influenced selection. The 20 remaining original URL leads represented **19 distinct civic sites**, since two leads share one civic address with unresolved units. Both leads were retained and evaluated separately. An eleventh difficult site kept the primary location denominator at 60. The 11 difficult sites all have multiple physical units in the graph, and ten have multiple Places names at the civic key. These are challenge indicators. They do not establish current multi-tenancy or duplication.

| Stratum | Distinct sites | First-party host outside allowlist | No usable first-party lead |
| --- | ---: | ---: | ---: |
| Original leads | 19 | 17 | 2 |
| Places nonoverlap, with website lead | 20 | 20 | 0 |
| Places nonoverlap, without website lead | 10 | 0 | 10 |
| Difficult civic sites | 11 | 9 | 2 |
| **Total** | **60** | **46** | **14** |

The second original lead at a shared civic site also had no approved host. It stays outside the 60-site denominator. The frozen cohort SHA-256 is `08a99fafd2f56e31e11c6f1f10ee5cb88af67d0d192a9668ad96ebaaa395d7d3`. It records input hashes and location-disjoint strata. The sample intentionally includes hard cases and excludes the previously reported closed-review queue. It is unsuitable for estimating town-wide prevalence.

| Original Phase 2.1 target | This run |
| --- | --- |
| Evaluate the original 70 | Prior run checked 70 against discovery sources; the remaining 20 URL leads were attempted or dispositioned here, at 19 civic sites |
| Independently corroborate 50 advertised locations | 0/60 new; the previous three controls remain corroborated advertised premises |
| Verify 30 merchant sites | 0/60 new; two of the three controls passed live deterministic identity and civic checks |
| Complete 30 digital capability assessments | 0/60; the three prior scoped manual control reviews remain available |
| At least 90% parcel linkage among corroborated locations | No eligible cohort denominator; 2/2 automated control corroborations linked, and the prior manual sample retained 3/3 |
| 100% provenance | All 60 census rows and the companion have linked source IDs and the frozen input hashes. Each fetched page has a timestamp, URL and snapshot SHA-256. There are no new cohort merchant-field claims |

All 60 census levels are **Unknown**. L0 is reserved for a confirmed business without a verified website, so a blocked URL or missing lead cannot qualify. The rate of verified duplicates and the rate of verified stale listings are **unmeasured**. No selected site had the narrow duplicate GERS-key flag. Thirteen of the 19 original civic representatives had only stale-flagged evidence in the prior graph. Those flags indicate evidence age or an undated lead and do not establish that a merchant moved or closed.

## Merchant automation and sample opportunity view

The retriever uses bounded public HTTPS GET requests, an explicit host allowlist, robots checks and per-host pacing. It declines redirected or unapproved destinations, excludes obvious third-party listing platforms as first-party identity evidence, and does not submit forms. The extractor checks exact names against page titles, headings and JSON-LD, then checks locality and civic address. It records structured hours, available public offering evidence, forms and linked capabilities, with the field context tied to a hashed page capture. A verified site plus the separate, hashed Chamber civic listing can corroborate a premise. Unresolved units, incompatible structured addresses, alias interpretation, hosted transaction links, and missing lead evidence remain review cases.

Maturity is L0 for a confirmed business without a verified website, L1 for a verified informational site, L2 for an observed online catalog or menu, L3 for an observed third-party transaction pathway, and L4 for an observed first-party transaction pathway. An advertised transaction link does not establish L3 or L4. This automation detects links and form affordances and records structured evidence. Separate review is still needed for JavaScript-dependent pathways, checkout ownership, location-specific ordering, and ambiguous identity.

| Priority and public merchant sample | Evidence-backed maturity | Next verification |
| --- | --- | --- |
| 1. The Book Oasis | Automated homepage L1. Prior review found a book inquiry form and linked curated book lists, audiobook and gift-card destinations. | Confirm the shopping and gift-card journeys and distinguish external checkout from the local site. [Merchant](https://thebookoasis.com/) |
| 2. Patina'd | Automated homepage L1; prior review supports L2 from the priced shop catalog and visible product cart control. | Verify a first-party checkout pathway without placing an order. [Catalog](https://www.patinadstore.com/shop) |
| 3. Gaetano's | Automated identity **Unknown** due to the expanded site name. Prior human review supports L2 from the priced menu and corroborated civic address. | Confirm the name alias and distinguish advertised ChowNow ordering and OpenTable reservations from observed paths. [Merchant](https://www.gaetanosfood.com/) |

These priorities select inexpensive evidence checks with clear next actions. They imply neither merchant need nor a sales opportunity. For the 60-site cohort, the priority queue is 46 scope-limited host reviews, then 14 source discovery/manual identity cases, with unresolved unit and multi-name flags carried into review. All 60 have unknown readiness.

## Unit economics and access

- **Autonomous completion:** 0/60. All 60 required an access or discovery follow-up. This is a 100% intervention requirement, consisting of 46 policy blockers and 14 missing usable first-party leads. It measures this run's access and verification constraints, not the extractor's performance once pages can be reached. The companion and controls are reported separately.
- **Merchant execution:** the 60-site policy/discovery triage took about 0.0014 s in total and issued no merchant requests. Including the companion and the three controls, the process took 3.64 s wall and 0.65 s CPU with 115 MiB peak RSS. Six HTTP GETs, all for the controls (robots and page), transferred 113,028 body bytes counted by the client. The control cases took 0.94–1.45 s individually. These are not per-site full assessment times.
- **Observed cost:** $0 in metered API spend. No external AI services, paid search, form submissions or purchases were used. The report does not estimate unobserved hosting charges.
- **Planning estimate:** budget 10–20 minutes of human work per site for a full 60-site pass, or 10–20 hours. At an assumed $30–$60 per hour, the labor range is $300–$1,200. A monthly change-triggered refresh of 9–18 sites at 5–10 minutes each is approximately 0.75–3 hours or $23–$180 at the same rates. These scenarios exclude publishing/access delays and difficult in-person verification. The completed run provides insufficient throughput evidence for extrapolating a full-town acquisition budget.

The prior merchant allowlist request had not been published into the running policy. I added 28 exact, identified cohort hosts to that pending draft, preserving its existing rules and omitting an Overture-provided staging host. Publication and any redirect permissions still require review. No new tool or process attempted to bypass the managed policy. The Chamber member directory's earlier upstream 503 remains a separate source issue.

## Reproduction and retained evidence

From the checkout with `business-first` and `dev` extras installed, use fresh ignored output paths:

```sh
python -m um_world_model.overture_https data/phase21/stoneham.geojson data/phase21/census-replay
python -m um_world_model.readiness_cohort data/phase2/build-3 \
  data/phase21/live-final-v2.json data/phase21/live/baseline-lead-audit-v2.json \
  data/phase21/readiness-replay-cohort.json
python -m um_world_model.merchant_readiness data/phase21/readiness-cohort.json \
  data/phase21/readiness-authorized-hosts.json data/phase21/readiness-replay \
  --prior-reviews data/phase21/live/merchant-reviews-v2.json \
  --physical data/phase2/build-3/physical-1.0.json
```

Use the frozen manifest for retries and supply only currently authorized hostnames. The measured receipt is under `data/phase21/census-overture-measured`, and the merchant audit and captures are under `data/phase21/readiness-final`. The committed report contains aggregate results and three public commercial controls. No raw snapshots or restricted row-level data are committed. Work stopped for architectural review.
