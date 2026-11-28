# Stoneham Phase 2.2A — deterministic acquisition remediation

**The remediation is implemented and measured, but all three intermediate targets remain unmet. Gate A remains formally open. Stop for architectural review before semantic reasoning.**

The final run took place on **2026-11-28, 15:59:47–16:03:51 UTC**. It processed all 60 unchanged locations. Two locations gained retrieval and two lost it; one identity gained verification and one became unavailable under stricter robots parsing. Net cohort retrieval and verification coverage did not improve. Additional pages improved evidence depth and the controls, but did not remove the dominant host-policy, robots and missing-lead constraints.

## Direct comparison with `296642c`

| Cohort outcome | Local baseline | Phase 2.2A final | Change / intermediate target |
| --- | ---: | ---: | --- |
| Locations dispositioned | 60/60 | 60/60 | Same frozen cases |
| Merchant locations retrieved | 22/60 (36.7%) | 22/60 (36.7%) | Net 0; target **35 unmet** |
| Deterministic website identities verified | 11/60 (18.3%) | 11/60 (18.3%) | Net 0; target **20 unmet** |
| Scoped automated assessments | 5/60 (8.3%) | 4/60 (6.7%) | −1; target **15 unmet** |
| Independently corroborated advertised premises, using preserved Chamber evidence | 3/60 | 3/60 | Unchanged |
| Parcel-linked among corroborated premises | 3/3 | 3/3 | Small selected denominator |
| No follow-up reason under script | 2/60 | 1/60 | −1 |
| Follow-up required | 58/60 (96.7%) | 59/60 (98.3%) | +1 |
| Successful cohort page captures, including internal pages | 22 | 93 | +71 |
| Additional relevant pages attempted | 0 | 73 | 71 HTML successes; one 404; one non-HTML response |

There are 49 Unknown and 11 L1 cohort classifications; no cohort L0, L2, L3 or L4 classifications. The baseline's one L2 site is now inaccessible under the stricter robots parser, not disproved as having a catalog. Among verified cohort sites, extracted indicators comprise ten social presences, five marketplace links and four inquiry forms; these overlap. Seven verified sites require transaction-pathway review. No new comprehensive digital assessment or observed ordering/booking/checkout pathway was completed.

The 95% Wilson intervals are 25.6–49.3% for retrieval (22/60), 10.6–29.9% for automated verification (11/60), 2.6–15.9% for scoped completion (4/60), and 43.9–100% for parcel linkage (3/3). These intervals illustrate denominator uncertainty, not town-wide estimates: the deliberately stratified sample is not random. Independently audited identity/address/parcel precision and recall remain **not measured**. Source availability can change between runs; this is a paired cohort comparison, not a controlled causal experiment.

## Failure attribution

The mutually exclusive final location dispositions reconcile to 60:

| Location disposition | Count |
| --- | ---: |
| No usable first-party URL lead | 14 |
| Original staging host outside approved policy | 1 |
| Robots redirect to an unapproved host | 10 |
| Page redirect to an unapproved host | 2 |
| Unsafe page redirect destination | 1 |
| Unsupported robots content/directive | 3 |
| Explicit robots crawl denial | 3 |
| Robots transport failure | 3 |
| Initial merchant page HTTP 404 | 1 |
| Retrieved pages, unresolved identity/civic evidence | 11 |
| Verified, transaction-pathway review | 7 |
| Verified, independent premises review | 3 |
| No follow-up reason | 1 |

The three transport failures are one DNS-resolution error, one connection refusal and one TLS certificate mismatch. TLS verification was not disabled. These are distinct from the three explicit crawl denials and three unsupported-directive decisions. One unsupported response contains a `Content-Signal` extension; abstention reflects unsupported syntax, not an observed negative crawl instruction. No parser exception or program crash occurred. The 11 retrieved-but-unverified locations need evidence review; they are not eleven established false businesses or eleven proven extraction defects.

Across all groups, **183 attempted GETs** comprise 55 robots requests and 128 page requests. There were 180 HTTP responses and three transport failures. Responses include 26 redirects, 151 HTTP 200s and three HTTP 404s. Every successful redirect follow remained inside the approved policy; **zero new hosts were requested**. Rejected destinations and every robots decision retain a separate event in the private ledger. Five cohort locations still have relevant discovered URLs outside the five-additional-page budget; their existence does not imply unobserved capabilities.

## Separate positive controls and companion

| Control | Baseline | Phase 2.2A final |
| --- | --- | --- |
| Gaetano's | Identity unresolved; Unknown | Expanded title-and-logo name plus exact civic verified; L1. Menu pages retrieved, but the scoped catalog parser did not establish L2. |
| Patina'd | Homepage L1 | Identity remains verified; internal `/shop` and product evidence support L2. No cart or checkout action taken. |
| The Book Oasis | Verified L1 | Remains verified L1 after homepage and About-page checks. |

All three controls are now verified, corroborated against the preserved Chamber evidence, and parcel linked. All still advertise pathways requiring review, so none is counted as a scoped completion. They used 16 GET attempts, 11 successful page captures, 361,255 counted body bytes and 6.33 seconds, with eight additional pages. The Patina'd catalog result is a regression success, not a cohort success.

The one shared-site companion separately gained exact identity verification through authored internal pages, plus Chamber corroboration and parcel linkage; it remains L1 with transaction review required. It used nine GET attempts, six successful captures, 182,514 counted bytes and 2.72 seconds. Neither companion nor controls contribute to the 60-location target counts.

## Changed identity evidence review and false-positive risks

Four decision transitions were isolated: two in the cohort (one gain, one now unavailable), one companion gain, and Gaetano's control gain. A private packet contains frozen expected names/civics/units, raw snapshot paths and hashes, relevant page content, historical captures, and access evidence, without the resolver's identity conclusions. A separate inspection outside the resolver supported the three new advertised-site identities: one contact-page exact name/civic match, one About/menu exact name/civic match for the companion, and the control's literal restaurant-name expansion. The lost cohort decision has no current page to adjudicate because its robots extension was unsupported; it is an acquisition abstention, not a reviewed false match.

After user authorization, a separate review agent independently inspected the blinded packet and referenced captures without seeing resolver conclusions or the implementing agent's review. It supported all three newly accepted advertised identities at their frozen civics and left the fourth case unresolved. It additionally found that the historical capture for that unavailable case did not support the frozen unit; historical building-level verification must not be read as unit-level occupancy evidence. All 21 referenced snapshot paths passed the reviewer's hash checks. The independent labels were finalized before reconciliation with resolver decisions and did not change measured outputs.

This is an independent agent review, **not a human reference audit**, and adds no LLM to the acquisition pipeline. It confirms evidence support for these three changed acceptances only; no population precision or false-positive rate is claimed. Legal identity and actual current operation remain unverified for all four reviewed cases.

False-positive risks remain: a first-party page can be stale; title and logo are not independent publishers; multiple locations can share a brand and domain; shared civic addresses do not resolve tenant units; a linked catalog does not establish local inventory; and website branding does not establish a legal entity. The three supported changes give no basis to extrapolate a population error rate. Regression tests explicitly reject sponsor-logo-only identity, arbitrary name extensions, wrong civics, missing/mismatched units and cross-page civic conflicts.

## Execution cost and evidence quality

| Full-run resource, including companion and controls | Baseline | Phase 2.2A final |
| --- | ---: | ---: |
| Attempted GETs | 90 | 183 |
| Counted response-body bytes | 1,481,195 | 6,713,538 |
| Wall seconds | 70.31 | 243.94 |
| CPU seconds | 3.33 | 15.65 |
| Peak RSS | 167.9 MiB | 176.1 MiB |
| Metered acquisition API spend | $0 | $0 |

The cohort alone used 158 GETs, 6,169,769 body bytes and 234.61 seconds. Final versus baseline totals increase by 93 attempted GETs, 5,232,343 counted bytes and 173.64 wall seconds, without net retrieval or identity coverage gain. The final retriever additionally consumes and retains bounded robots/redirect/error bodies; baseline byte counters omitted some of those bodies. Thus the byte delta reflects both expanded acquisition and improved accounting, not an exact like-for-like wire-traffic increase. DNS pinning without connection reuse, more parsing, logging, robots checks and extra pages contribute to elapsed cost.

A diagnostic implementation run is retained separately at `data/phase22a/remediation-20261128T154843Z/`: 181 GETs, 6,651,471 body bytes, 252.32 wall seconds and 15.60 CPU seconds. Adversarial synthetic tests then exposed a sponsor-logo-only acceptance risk and a prefixed-unit parsing issue; mixed-unit evidence was also made conservative before the final rerun. The final run is the reported result, not a selection of best outcomes from both runs. Both live passes together used **364 GET attempts, 13,365,009 counted body bytes and 496.27 wall seconds**. Tests, code/report preparation, reviewer time, Codex usage and local electricity/network costs are not monetized. No paid acquisition API was used.

All 64 row dispositions (60 cohort, one companion, three controls) retain source references and frozen input hashes. All 110 successful HTML page attempts have URLs, timestamps and verified snapshot hashes. All 180 completed HTTP responses have bounded, verified captures, including 52 robots responses; they deduplicate to 152 `.body` files. No body was truncated. Transport failures retain error evidence instead of nonexistent response snapshots. Robots parser/permission decisions link to the exact request events and captured policy bytes. Recorded merchant claims inherit source URLs, retrieval times and snapshot hashes; source vintage is retained where a Last-Modified header exists, otherwise unknown. This improves traceability over the baseline's missing robots bodies without establishing correctness of the underlying claims.

Final private output is `data/phase22a/remediation-20261128T155947Z/`. It includes `audit.json`, `acquisition.jsonl`, `execution-receipt.json`, exact source-module copies, aggregate summaries, the blinded review packet, the implementing agent's inspection and `independent-agent-review.json`. The sibling transport log and all captures remain outside Git.

- Final audit SHA-256: `f8d6f0cd1dd8ccfb8f86f7c81ecd5b175ddc89179e3a6fc1a868761e29503a0b`.
- Independent agent review SHA-256: `ae6ffb40e571fd0c9895672757ce22acdf2a9a8d43e9260b363e12b18a61684e`.
- Acquisition ledger SHA-256: `40ed8b069b9dfd84d1d66a23c058198be0c07d44dee4c3681fe73868e521e439`.
- Executed readiness module SHA-256: `2a541d95f668f5306f8ea46f754b6a8a625dcde57b324cd433641a0c7eade2e2`.
- Executed acquisition module SHA-256: `7cc187ec6730deed3a1a402a9820b373271568bbe802a3c8a35797eced7e579e`.
- Executed identity module SHA-256: `b733e242f7915261874a269710205aa017cb45ce8956e2ae73b929aa46015f05`.


## Scope and invariants

This iteration compares the same frozen 60-location cohort with the local baseline committed at `296642c`. The one shared-site companion and three positive controls remain outside that denominator. No source discovery, cohort substitution, physical-graph change, entity merge, LLM integration, paid search, browser automation, UI, form submission, or transaction was introduced. Historical baseline outputs and the [Digital Readiness Census](digital-readiness-census.md) are preserved.

The approved policy remains the same 55 exact hosts. Its SHA-256 is `72b227b38ca60c142ff87ed705e77062fc39b484ede17f4567f18fd15f0ff1e6`. Unapproved redirect destinations were recorded but not accessed. No new host authorization is inferred from this remediation request.

Input hashes were checked before and after execution:

| Artifact | SHA-256 |
| --- | --- |
| Frozen cohort | `08a99fafd2f56e31e11c6f1f10ee5cb88af67d0d192a9668ad96ebaaa395d7d3` |
| Physical graph | `6c3f1dc18d360a6a01b64f9d9b59ca5d2510d2d5ba438c5ede8105f3876a4456` |
| Prior review ledger | `40c555dd026ec4c80e31e5e75e0edf88b43fc0d7be2ea451cfd5ea5ea6210310` |
| Chamber snapshot | `4a92b0dc102ffddb5d15ff9603d44a4e2c1f72b5fc0247a106304c63393bdcc8` |
| Historical baseline audit | `543b75a2c8bce618856ef6d10e51e5cc2a9d5a3c38b7dd844db0877c20c23575` |

Python remains 3.12.16 with the previously accepted patch-version deviation. No dependencies were installed. All 76 regression tests pass, including the original 36 and 40 new parameterized cases. Ruff checks pass for the changed Python files.

## Deterministic implementation

**Redirects and connection policy.** Robots and merchant-page requests allow at most five redirects per chain. Every hop must use HTTPS and an exact approved DNS hostname; credentials, queries, unsafe action paths, loops and unapproved destinations are rejected before following. The transport validates all DNS answers as public, rejects private/reserved/multicast addresses, and pins the connection to a validated IP while retaining the original Host header and TLS SNI/certificate verification name. It revalidates DNS for every connection, disables environment proxies and connection reuse, and keeps automatic HTTPX redirects disabled. The first sorted public address is attempted; no alternate-IP retries are used. DNS timing still depends on the operating-system resolver.

**Robots.** Each page hop, including same-host redirects to another path, is checked against the destination host's applicable policy. Fetching a robots policy itself is the protocol bootstrap and is not gated recursively by that policy; redirected robots content is applied to the requesting origin. The deterministic parser handles specific user-agent groups, wildcard fallback, longest matching Allow/Disallow rules, end anchors, percent-encoded paths, crawl-delay and request-rate. Pacing above ten seconds is deferred, not ignored. Unknown access directives, invalid syntax, HTML/error content and oversized bodies abstain. Explicit crawl denial, unsupported content, pacing limits, HTTP failures, transport failures and redirect restrictions have separate outcomes.

The private append-only acquisition ledger retains request URLs, timestamps, HTTP outcomes, redirect destinations, selected response metadata, transport errors and robots decisions with links to their evidence events. Bounded response bodies are content-addressed and SHA-256 checked, including robots, redirects and non-200 responses. Robots bodies are capped at 256,000 decoded bytes and pages at 2,000,000; truncated captures are labeled as prefixes and never used for extraction. Cookies, credentials and arbitrary response headers are not copied into the structured evidence ledger. Transport debug logs remain private.

**Page discovery.** At most three original frozen URL candidates and five additional relevant pages are evaluated per merchant. Authored same-host anchors and structured menu/catalog URLs generate candidates; no paths are guessed. Priority is About, Contact, Locations, Menu, Shop, Products, Services, Booking, Ordering, with URL ordering as the deterministic tie-breaker. Discovery is bounded to 200 candidates per parsed page. Fragments, queried/action URLs, transaction endpoints and external-host discovery links are excluded. Additional pages still pass the host, redirect, robots and size checks. The five-page limit bounds selected pages, not the extra robots/redirect HTTP exchanges; request counts report those separately.

**Identity and capabilities.** Exact title, heading or business-structured names plus civic evidence remain the default. A structured `alternateName` must occur on a business entity carrying the exact civic address. A narrow generic suffix expansion, such as “Restaurant,” requires the same expanded name in a title/heading/business record and a logo, plus exact civic evidence. A logo alone cannot verify identity, and arbitrary prefix, substring and fuzzy matches cannot promote a candidate. Explicit unit mismatches, missing expected units, mixed unit evidence and conflicting local civic evidence preserve abstention. Cross-page conflicts veto a previously matched page. These checks concern advertised website identity, not legal-entity identity, current operation or unit-level occupancy.

Catalog evidence can come from named structured Product/Menu records or repeated named, priced product/menu cards. An authored same-host catalog page can inherit website ownership from a separately verified page, but cannot establish a new premises identity or prove availability at that location. All inherited evidence retains its page URL and snapshot hash. Advertised booking/ordering/cart links remain advertisements; no transaction pathway is verified.

The scoped-completion rule remains compatible with the baseline: verified website without advertised transaction pathways requiring review. More pages can reveal such pathways and lower completion counts. This is not a comprehensive digital assessment, and the intermediate target is not relaxed by redefining completion.

## Reproduction and retained artifacts

Run from the repository root with the unchanged private inputs and approved host file, using a fresh ignored directory:

```sh
umask 077
.venv/bin/python -m pytest -q
.venv/bin/python -m um_world_model.merchant_readiness \
  data/phase21/readiness-cohort.json \
  data/phase21/readiness-local-authorized-hosts.json \
  data/phase22a/fresh-authorized-run \
  --prior-reviews data/phase21/live/merchant-reviews-v2.json \
  --physical data/phase2/build-3/physical-1.0.json \
  --page-budget 5 --max-redirects 5
```

The measured run's private wrapper additionally checks input hashes, records source-file hashes, archives the exact executed merchant modules, and enables transport logging. The acquisition ledger can distinguish policy refusal before a request from an attempted request that failed in DNS/TLS/HTTP. Request counters are attempted GETs, not proof that an origin received every request. Transfer counters are client-observed body bytes, not total wire traffic.

## Acceptance and review boundary

The original criteria remain: evaluate all 70 original candidates, independently corroborate at least 50 locations, verify 30 websites, complete 30 digital assessments, achieve 90% parcel linkage among corroborated premises, and preserve 100% assertion provenance. The prior original-70 discovery evaluation remains historical; this is a repeat of the frozen 60-site cohort, not a newly selected 70-site sample. Small, selected corroboration denominators cannot establish parcel reliability.

Gate A remains formally open. Its independent address/parcel precision, recall, coverage and provenance requirements are unchanged. This iteration does not measure legal-entity merge accuracy or prove full-town completeness. Comprehensive capability assessment, independent current-operation checks and remaining access/identity interventions are still required. Stop for architectural review before any semantic-reasoning integration.
