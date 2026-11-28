# Stoneham digital readiness census — experimental sample

## Local frozen baseline — 2026-11-28

**The local baseline completed; acceptance targets remain unmet. Stop for architectural review. Gate A remains formally open.** All 60 original locations received dispositions, with no substitutions or changes to the cohort or physical graph. Twenty-two locations yielded merchant pages; 11 passed the unchanged deterministic name-and-civic verification; three matched the preserved independent Chamber premises evidence and linked to parcels. These are automated evidence checks, not independently audited precision measurements or proof of current operation.

The run began at **14:41:32 UTC** and finished at **14:42:42 UTC**, using checkout `2d3f463` on `codex/stoneham-gate-a`. Source, tests, and package declarations are unchanged from checkpoint `c531643`. The user approved the exact 55-host configuration and the Python 3.12.16 versus 3.12.14 difference. The 37 installed constrained packages match; three unused source-reconstruction spreadsheet dependencies remain absent. All 36 regression tests passed. [Prerequisites and exact approved hosts](../../docs/local-baseline-prerequisites.md).

### Retrieval, verification and readiness

| Cohort measure | Result | 95% Wilson interval |
| --- | ---: | ---: |
| Locations dispositioned | 60/60 | — |
| At least one merchant page retrieved | 22/60 (36.7%) | 25.6–49.3% |
| Passed deterministic website identity and civic checks | 11/60 (18.3%) | 10.6–29.9% |
| Independently corroborated advertised premises using preserved Chamber evidence | 3/60 (5.0%) | 1.7–13.7% |
| Parcel-linked among corroborated premises | 3/3 (100%) | 43.9–100% |
| Script's scoped homepage assessment completed | 5/60 (8.3%) | 3.6–18.1% |
| No follow-up reason under the frozen script | 2/60 (3.3%) | 0.9–11.4% |
| Follow-up required | 58/60 (96.7%) | 88.6–99.1% |

Intervals describe small-denominator uncertainty only; this deliberately stratified, difficult-case sample is not a random town sample. No population inference or independent precision claim follows. Eleven of the 22 retrieved locations passed verification; the other 11 remain identity/civic review cases, not demonstrated false businesses or parser defects. There were no extractor crashes. The baseline did not manually adjudicate aliases, units, or failed matches, so extraction accuracy, identity precision/recall, stale-listing rates, and entity-merge error rates remain unmeasured.

Maturity: **49 Unknown, 10 L1, one L2; zero L0, L3, or L4.** Unknowns include missing leads and inaccessible pages. Among the 11 verified websites the extractor observed 10 social-presence indicators, five marketplace-link indicators, one inquiry-form indicator, and one structured catalog indicator; indicators overlap. Six verified sites advertise transaction pathways requiring review. Those links do not establish observed transactions. Five sites meet the script's narrow homepage completion rule, but these are not five independently audited, comprehensive capability assessments. No new full manual capability assessments were completed.

### Failure attribution and intervention

The following mutually exclusive location dispositions reconcile to 60:

| Disposition | Locations |
| --- | ---: |
| Missing usable first-party URL lead | 14 |
| Explicitly excluded staging host | 1 |
| Robots redirect deferred | 10 |
| Robots returned HTTP 200 but the frozen robots gate rejected access | 3 |
| Transport failure while requesting robots | 3 |
| Homepage redirect deferred: approved destination | 3 |
| Homepage redirect deferred: destination outside approved list | 3 |
| Homepage HTTP 404 | 1 |
| Retrieved page, identity/civic verification unresolved | 11 |
| Verified, transaction-pathway review required | 6 |
| Verified, independent premises review required | 3 |
| No follow-up reason | 2 |

The three transport failures were one DNS-resolution failure, one connection refusal, and one TLS certificate hostname mismatch. TLS verification remained enabled. These are access failures, not extraction failures. The three rejected HTTP-200 robots responses cannot be distinguished retrospectively between rule denial and unsupported robots content from the retained logs; the unchanged retriever does not persist robots bodies. They must not be described as three explicit robots prohibitions.

At attempt level, the cohort has 48 candidate-page dispositions: 22 successful captures, 18 robots-gated attempts, six homepage redirects, one policy exclusion, and one HTTP 404. Of the 18 robots-gated attempts, 12 encountered redirects, three transport failures, and three rejected HTTP-200 robots responses. Two redirect-gated attempts belonged to locations subsequently retrieved through another original frozen URL; therefore attempt and location counts differ. No new URLs, redirected destinations, or substitute locations were introduced.

Across the cohort, companion and controls, the private transport log reconciles **90 GET attempts** to 87 HTTP responses and three transport failures. Robots responses: 39 HTTP 200, ten 301, two 308. Page responses: 28 HTTP 200, five 301, one 308, one 302, one 404. No redirect was followed. Acquisition used the existing bounded GET, exact host allowlist, pacing, TLS verification and robots checks. No forms, purchases, paid APIs, or external research-file uploads were used.

### Separate companion and positive controls

The shared-site companion is outside the 60-location denominator: two successful page captures across four GETs, identity unresolved, Unknown maturity, no corroboration or parcel linkage. The three positive controls also remain separate:

| Control | Local frozen result |
| --- | --- |
| Gaetano's | Pages retrieved; exact identity check unresolved; Unknown. Prior manually reviewed L2 evidence remains historical. |
| Patina'd | Verified homepage L1; Chamber corroborated and parcel linked; transaction-pathway review remains. Prior separately reviewed catalog L2 remains historical. |
| The Book Oasis | Verified homepage L1; Chamber corroborated and parcel linked; transaction-pathway review remains. |

All three controls yielded pages; two passed automated verification and linked to parcels. Controls accounted for four successful captures, one deferred homepage redirect, ten GETs, 161,747 counted body bytes and 2.31 seconds. None met the current script's scoped-assessment completion rule. The baseline did not repeat the prior manual shop/menu reviews or promote their results into new automated classifications.

### Cost and evidence receipts

- Full process: **70.31 seconds wall, 3.33 seconds CPU, 167.9 MiB peak RSS**, 90 GET attempts and 1,481,195 counted body bytes. Logging overhead is included. Timing excludes preflight and report preparation.
- Cohort only: **66.83 seconds**, 76 GET attempts and 1,242,332 counted body bytes. Companion: 0.88 seconds, four GETs and 77,116 bytes. Client counters do not represent all wire traffic: headers, failed/redirect response bodies and network overhead are excluded or incomplete.
- Metered external API spend: **$0**. Human review labor and local electricity/network costs were not metered. The 58/60 follow-up rate is a required-intervention rate, not completed manual labor. Execution required one approved sandbox escalation for preflight and one for the cohort; no case-level manual interventions occurred. Runtime is not a full-assessment cost or a defensible town-wide throughput estimate.
- All **60 cohort rows, one companion and three controls** retain nonempty source references and the frozen input hashes. All **28 successful page attempts** have URL, timestamp, snapshot reference and a verified SHA-256; deduplication yields **26 private HTML snapshots**. The three cohort corroborations reuse the exact checksum-verified Chamber snapshot and prior review ledger. Evidence linkage checks pass for these recorded claims, but independent correctness was not audited. Failed requests have audit/log outcomes, not successful source snapshots; robots bodies are not retained. Thus this does not establish complete raw-response provenance for every network exchange.
- Private output: `data/phase21/readiness-local-20261128T144132Z/`, including `audit.json`, `execution-receipt.json`, and the derived aggregate summary. The sibling `.transport.log` separates HTTP outcomes from transport failures. These artifacts and preflight captures remain ignored by Git.
- Audit SHA-256: `543b75a2c8bce618856ef6d10e51e5cc2a9d5a3c38b7dd844db0877c20c23575`. Transport log SHA-256: `4637f68d27071af29d104ec0ab572b09290f64dbb7590b22d832322047ee1571`.
- Approved host configuration SHA-256: `72b227b38ca60c142ff87ed705e77062fc39b484ede17f4567f18fd15f0ff1e6`. Cohort and graph remain byte-identical before and after execution: `08a99fafd2f56e31e11c6f1f10ee5cb88af67d0d192a9668ad96ebaaa395d7d3` and `6c3f1dc18d360a6a01b64f9d9b59ca5d2510d2d5ba438c5ede8105f3876a4456`.

The original acceptance criteria are unchanged: evaluate all 70 original candidates, independently corroborate at least 50 locations, verify 30 websites, complete 30 digital assessments, achieve 90% parcel linkage among corroborated businesses, and preserve 100% assertion provenance. The prior 70-candidate discovery evaluation is historical; this baseline evaluates its frozen 60-site cohort and separate companion/controls, not a new 70-candidate cohort. Current results are three cohort corroborations, 11 deterministic website passes and five scoped homepage assessments, with no new comprehensive manual assessments. The 3/3 parcel result has too small and selected a denominator to establish reliability. Provenance linkage is verified for recorded merchant claims; access-response retention has the stated limitation. Gate A's independent address/parcel precision and coverage requirements remain open and unmeasured by this baseline. No Gate B, production-readiness, or town-completeness claim is made.

The earlier cloud results below are retained as historical evidence, not the current local outcome. Work stops here for architectural review; no parser, architecture, physical-graph, or cohort change was made.

---

## Post-publication connectivity preflight

**Stopped before the cohort rerun.** Publication was reported, but the active runtime reported current, enforced revision 12. Its effective policy contained only the previous 16 custom hosts. The available configuration showed 73 custom hosts, of which 57 were absent from the effective runtime policy.

The application reads the allowlist passed on the command line. I exported the effective runtime policy to a fresh local JSON file and compared it with the previous audit ledger. It allowed none of the 48 attempted hostnames across the 46 previously blocked civic sites. The refreshed file SHA-256 is `2b9ac6e9a851847088522f69af893c706ea2f26085dd5c1d35fe4e17dbb78ff7`. The frozen cohort SHA-256 remains `08a99fafd2f56e31e11c6f1f10ee5cb88af67d0d192a9668ad96ebaaa395d7d3`.

| HTTPS probe | Result |
| --- | --- |
| `bodymindsystems.com`, `www.rapidliquors.com`, `thewinecellarsma.com`, `www.stonehamdentalcare.com`, `littlecaesars.com` | Managed proxy CONNECT 403 for all five |
| `thebookoasis.com` | HTTP 200 |

**Zero of the 46 blocked sites were eligible for retrieval through the active application and runtime policy.** The five representative failures occurred before merchant content was retrieved, so they are policy failures. Actual origin availability is unknown for sites that could not be reached. There are no new retrieval, identity, civic corroboration, parcel linkage, digital extraction, timing or intervention results for the 60-site cohort.

The prior control run remains the evidence for parser diagnosis. Gaetano's expanded site name failed the exact identity match after a successful fetch. The Book Oasis and Patina'd passed the homepage checks. Patina'd's separately reviewed shop page demonstrated the priced catalog that its homepage-only automated L1 classification missed. This preflight introduced no parser or acquisition changes.

Run the identical frozen cohort in a dedicated local research environment with an authorized merchant host policy. Generate the application allowlist from that environment's enforced policy and confirm representative HTTPS and robots access before running the existing command. Keep outbound requests read-only. Gate A remains open.

---

## Original frozen-cohort run

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
