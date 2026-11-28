# Stoneham Phase 2.1 local Ubuntu research handoff

This handoff records the stopped execution state. The cloud runtime still blocked all 46 previously blocked sites at its last preflight. The frozen cohort and physical graph were preserved. Gate A remains formally open. The handoff does not authorize new sourcing, broaden the cohort, or change the parser.

## Checkout and Python

- Repository `https://github.com/vinod-git-diometric/um-world-model.git`, branch `codex/stoneham-gate-a`, [draft PR #2](https://github.com/vinod-git-diometric/um-world-model/pull/2).
- Exact experiment checkpoint `c5316436652514bf13ae4fe3f94bc10400ce9b36`. Its parent `e7de178` implements the frozen readiness run. The later handoff commit changes documentation only.
- Observed CPython was **3.12.14**. Use Python 3.12.14 for matching results. The package declares Python 3.12 or newer.

```sh
git clone --branch codex/stoneham-gate-a https://github.com/vinod-git-diometric/um-world-model.git
cd um-world-model
git switch --detach c5316436652514bf13ae4fe3f94bc10400ce9b36
git rev-parse HEAD
python3.12 -VV
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -c /path/to/extracted/ubuntu-python312-constraints.txt -e '.[dev,business-first,discovery]'
python -m pytest -q
command -v jq curl sha256sum
```

Use Ubuntu `git`, `curl`, `jq`, and coreutils. Add `gdal-bin` (for `ogr2ogr`) only if re-deriving MassGIS export attributes, and make `python3.12-venv` available if using Ubuntu's Python packages. Use a trusted Python installation if the Ubuntu distribution does not provide the exact patch release. The archive constraints capture the observed environment, including HTTPX 0.29.0, Shapely 2.2.0, PyArrow 26.0.1, Beautiful Soup 4.15.0, Soup Sieve 4.1.3, Overture Maps 2.1.1 and the spreadsheet readers. `discovery` is required only for rebuilding source inputs. Without the archive constraints, the same editable install uses the compatible version ranges in `pyproject.toml`; record any version differences. Tests at the experiment checkpoint passed 36/36 with the optional research dependencies available.

Use the Codex CLI from the repository root. Install it separately via its supported distribution and authenticate locally if needed. Do not copy any cloud credential files or environment variables into this checkout.

## Exact resume inputs

Keep the following private files under the ignored `data/` tree with the exact relative names. Transfer them through an approved private channel, with access scoped to the research workspace. **They are omitted from the downloadable archive.** The frozen manifest and physical graph may expose residential-linked civic locations. The prior review ledger and Chamber HTML retain source evidence beyond the public aggregate report. The application checks the Chamber snapshot bytes referenced by the review ledger before using prior corroboration.

| File relative to repository root | SHA-256 | Use |
| --- | --- | --- |
| `data/phase21/readiness-cohort.json` | `08a99fafd2f56e31e11c6f1f10ee5cb88af67d0d192a9668ad96ebaaa395d7d3` | Frozen cases, companion, controls, leads, and input hashes |
| `data/phase2/build-3/physical-1.0.json` | `6c3f1dc18d360a6a01b64f9d9b59ca5d2510d2d5ba438c5ede8105f3876a4456` | Authoritative read-only parcel linkage |
| `data/phase21/live/merchant-reviews-v2.json` | `40c555dd026ec4c80e31e5e75e0edf88b43fc0d7be2ea451cfd5ea5ea6210310` | Reviewed premises evidence passed to the existing command |
| `data/phase21/live/chamber2.html` | `4a92b0dc102ffddb5d15ff9603d44a4e2c1f72b5fc0247a106304c63393bdcc8` | Only Chamber snapshot consulted by the current readiness command |

The original and the current policy files are different concepts. The historical runtime revision 12 application export `data/phase21/readiness-runtime-revision-12-hosts.json` hashes to `2b9ac6e9a851847088522f69af893c706ea2f26085dd5c1d35fe4e17dbb78ff7`. It documents the blocked preflight and must not be reused as the local authorized list. A new local host file must reflect the local policy. The preceding audit `data/phase21/readiness-final/audit.json` hashes to `357f690759149af7c7573d8564a4711682e795692caf8785d1d24286cf908d50` and is optional for comparison or checking the 46 previous policy-blocked cases.

## Frozen cohort and reconstruction limits

The cohort was frozen at `2026-11-27T18:24:24.424416+00:00` with release `2026-11-18.0` and seed `stoneham-readiness-2026-11-27-v1`. It contains 19 original URL-led civic sites, 20 Places nonoverlaps with URLs, 10 without URLs, and 11 difficult sites. A companion lead shares one original civic site, so all 20 original leads are preserved across 19 distinct sites. The Book Oasis, Gaetano’s, and Patina’d are three separate controls outside the 60-site denominator. Do not substitute cases when host access fails.

The frozen manifest embeds the exact input hashes below. These four inputs are needed for selection replay or provenance reconstruction. The first three are private row-level artifacts and are not needed to run an already frozen manifest. Keep their checksum-bound copies if follow-up evidence needs to trace back to them.

| Freeze input | SHA-256 |
| --- | --- |
| `data/phase2/build-3/commercial-1.0.json` | `6be0d777c8ecf7b97da67a08a3178570d075ab88fbf08b5dbef09e16ee3e7b57` |
| `data/phase21/live-final-v2.json` | `59631a9bae4df8c011bd7e6c6e39e2266bbc12890e522388eb31390349f479a7` |
| `data/phase21/live/baseline-lead-audit-v2.json` | `fe49a6b9dd6dfca1ae40ee4eb6433ad9e95c46d1b551d54651041ce6a95004af` |
| `data/phase2/build-3/physical-1.0.json` | `6c3f1dc18d360a6a01b64f9d9b59ca5d2510d2d5ba438c5ede8105f3876a4456` |

If all four inputs match, an offline freeze replay can recover the same case selection. It emits a new `frozen_at` timestamp. Compare the rows and input hashes with the original if available. Keep the original file and hash for an exact continuation.

```sh
python -m um_world_model.readiness_cohort data/phase2/build-3 \
  data/phase21/live-final-v2.json data/phase21/live/baseline-lead-audit-v2.json \
  data/phase21/readiness-rebuilt-cohort.json
diff -u <(jq -S 'del(.frozen_at)' data/phase21/readiness-cohort.json) \
        <(jq -S 'del(.frozen_at)' data/phase21/readiness-rebuilt-cohort.json)
```

If neither the exact original manifest nor all four exact freeze inputs can be recovered privately, the historical sample cannot be reconstructed from its hash, aggregate counts or a fresh crawl. Treat any new manifest as a different cohort and stop the exact rerun. The previously observed merchant review decisions also cannot be recreated from hashes. A fresh authorized review would be new evidence with new timestamps and a new snapshot hash. The current code ignores prior Chamber receipt fields after 90 days or when their timestamps are in the future.

## Reproducing source artifacts under separate authorization

The shareable archive includes the public MassGIS Stoneham polygon `stoneham.geojson` and the range-acquisition aggregate receipt `overture-acquisition-receipt.json`. Unpack the polygon to `data/phase21/stoneham.geojson` if source replay is needed. Its SHA-256 is `783bee9074e53a6d4b0d573e19df8985f593572f978073e4e841ca3d52ae20fd`. The receipt SHA-256 is `f7b7e78c2e2ac3a31a4e27559cba1a2b771c9d80d59383226cd6796a2650ee77`.

The following commands describe **future recovery only**. An intact original manifest and graph require no acquisition or rebuilding to resume the cohort. Keep raw records private.

- **Overture.** The managed Arrow S3 client failed on regional bucket DNS during `HeadObject`. The existing HTTPS path used the pinned STAC index and the same official AWS object with verified ranges and ETags. Use authorized access to `stac.overturemaps.org` and `overturemaps-us-west-2.s3.us-west-2.amazonaws.com`. The index SHA-256 is `1291c9621e79c3fa65a029621ce2474fb235dbcc10aa18e7a7f323dff3f10b1c`; the resulting Places sequence is `51646bb42dae8ab21ffede156b09c6219efaccbe1b1d64eca06146cc63580b99`. The acquisition records per-range hashes, asset URL, row groups and ETag.

  ```sh
  python -m um_world_model.overture_https data/phase21/stoneham.geojson data/phase21/local-places-replay
  sha256sum data/phase21/local-places-replay/{collections.parquet,places.geojsonseq,receipt.json}
  ```

- **Physical graph.** Prefer copying the exact compiled graph through the private channel. Offline rebuild requires the preserved MassGIS geometry run `data/runs/20261127T133604Z-490a763e/`, including its manifest, verified raw snapshots and normalized products (including the frozen hybrid output), the Stoneham official address ZIP and CSV, the Phase 2 source snapshots, and the repository seed. The geometry manifest has SHA-256 `22834699d7d022a1f3aff2d553d7d3b2c7e444963796e48c4511cd17abd5b666`; its snapshot hashes are embedded. Frozen `normalized/spatial-resolutions.jsonl` is `c8edc7f8521d951b7f3d1c868808fa54857faf4f1eefc321b9bdeb374d1cba89`. The official ZIP `data/audit-a2/AddressPts_M284.zip` is `549965cdb7323203c05ad633756c7ff40dd7c1825c50aca26d81e30e19cbb15d`, and `data/audit-a2/official-addresses.csv` is `90c4a47e1d4c16aa5b4a47b25f72fc2525e480f99b1fa84c9c1beb2c769a60f9`. Use the original retained timestamps and compare the rebuilt graph to the exact hash. A current download or rewritten timestamp is a new snapshot. [Physical build instructions](../reports/phase-2/commercial-discovery-results.md)

  ```sh
  ogr2ogr -f CSV data/audit-a2/official-addresses-replay.csv \
    "/vsizip/$(realpath data/audit-a2/AddressPts_M284.zip)" \
    -select ADDRESS_ID,LOC_ID,ADDR_PT_ID,EDIT_DATE,GEOTOWN_ID,POINT_TYPE,ADDR_NUM,STREETNAME,UNIT
  sha256sum data/audit-a2/official-addresses-replay.csv
  ```

- **Merchant/Chamber evidence.** Use exact private copies for historical review. The official Chamber participating-business page was reachable at `https://stonehamchamber.org/gift-certificates/participating-businesses/`; the member directory at `https://business.stonehamchamber.org/list` returned an upstream 503. Future authorized capture should record URL, UTC timestamp, HTTP outcome, source lineage and SHA-256. Do not present a fresh capture as the historical receipt. Without compatible prior reviews, omit `--prior-reviews` and label independent premises corroboration as unavailable for the replay.

If the exact physical graph cannot be retained or recovered, the optional `--physical` argument can be left out for a **merchant-only diagnostic**. This precludes the comparable parcel result. Do not substitute an approximated projection or a new geometry run into the original measurement.

## Local merchant host policy and exact resume commands

`merchant-hosts-review.json` in the shareable archive is a checklist of the previous public merchant requests and known control/source hosts. It is **not** an authorization or the application's input format. Review exact hostnames against local research approval, source terms, and effective network controls. Save only approved hosts as a flat JSON array of lowercase DNS names at `data/phase21/readiness-local-authorized-hosts.json`. Include the approved merchant hosts and the three control hosts `thebookoasis.com`, `www.gaetanosfood.com`, and `www.patinadstore.com`. Bare and `www` variants are separate. Do not add wildcards, URLs, tokens or cookies. The listed staging host was intentionally omitted. Redirects are deferred for review even if their destination is already authorized.

Once execution is authorized on the local machine, confirm representative HTTPS and robots access and retain the preflight outcomes. Do not follow redirects to unapproved hosts. Confirm the application's list contains the exact hosts on the approved merchant leads. Use the same local host file for the run and its checksum receipt.

```sh
umask 077
git rev-parse HEAD
git check-ignore data/phase21/readiness-cohort.json
sha256sum -c <<'CHECKSUMS'
08a99fafd2f56e31e11c6f1f10ee5cb88af67d0d192a9668ad96ebaaa395d7d3  data/phase21/readiness-cohort.json
6c3f1dc18d360a6a01b64f9d9b59ca5d2510d2d5ba438c5ede8105f3876a4456  data/phase2/build-3/physical-1.0.json
40c555dd026ec4c80e31e5e75e0edf88b43fc0d7be2ea451cfd5ea5ea6210310  data/phase21/live/merchant-reviews-v2.json
4a92b0dc102ffddb5d15ff9603d44a4e2c1f72b5fc0247a106304c63393bdcc8  data/phase21/live/chamber2.html
CHECKSUMS
jq -e 'type=="array" and all(.[]; type=="string" and test("^[a-z0-9.-]+$"))' \
  data/phase21/readiness-local-authorized-hosts.json
sha256sum data/phase21/readiness-local-authorized-hosts.json
result_dir="data/phase21/readiness-local-$(date -u +%Y%m%dT%H%M%SZ)"
python -m um_world_model.merchant_readiness \
  data/phase21/readiness-cohort.json data/phase21/readiness-local-authorized-hosts.json \
  "$result_dir" --prior-reviews data/phase21/live/merchant-reviews-v2.json \
  --physical data/phase2/build-3/physical-1.0.json
jq '.metrics' "$result_dir/audit.json"
sha256sum data/phase21/readiness-cohort.json data/phase2/build-3/physical-1.0.json
```

Run from the repository root. Stop if any prerequisite checksum fails. The output directory must not already exist. Keep attempt-level states separate: local policy exclusion, proxy denial, HTTP or robots outcomes, successful retrieval with unresolved identity, and extracted evidence requiring human review. Preserve audit JSON and captures privately, retain timestamp, URL and snapshot SHA-256 for each evidence record, and keep the prior graph immutable. An observation at an advertised location does not confirm current operation. Publish aggregate metrics and narrow public evidence references only. Before staging a report, inspect `git status --short` and `git diff --cached --name-only`; never force-add ignored raw data.

## Known limitations and outstanding criteria

- The extractor uses exact normalized names plus a Stoneham civic match. The prior controls showed Gaetano’s expanded site name needed human alias review. The Book Oasis and Patina’d cleared automated homepage checks, but the approved review found Patina’d’s priced catalog on a separate shop page. A homepage-only L1 is not a complete census of merchant capabilities.
- Public lookup uses HTTPS GET, allowlist and robots checks, a small response limit and no redirect following. The extractor cannot prove login-gated or JavaScript-dependent functions, checkout ownership, actual ordering or booking flows, missing unit identities, or current activity. An advertised transaction link alone does not establish L3 or L4. Never submit forms or make purchases. Treat blocked or unsupported records as Unknown rather than L0. Duplicate and stale rates require independent review.
- The explicit acceptance targets remain evaluation of all 70 original candidates, at least 50 independently corroborated locations, 30 verified merchant websites, 30 complete digital capability assessments, 90% parcel linkage among corroborated businesses, and 100% provenance. Only the three control premises were independently corroborated in the prior manual review. The immutable 60-site cohort delivered zero new verified websites, corroborations or completed assessments in the blocked cloud run. Keep controls and the shared-address companion outside the 60-site metric denominator. See the [Digital Readiness Census](../reports/phase-2/digital-readiness-census.md) for the measured preflight and limitations.
- Gate A remains formally open. Preserve the original independent audit requirements and stop after the authorized evaluation report. No production readiness or town-wide completeness is established.
