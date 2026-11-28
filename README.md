# United Main World Model

A public-data feasibility experiment for reconstructing Stoneham, Massachusetts' physical and commercial environment. The primary question is whether a provenance-preserving Business -> Occupancy -> Address -> Parcel chain can be constructed accurately, and generalized to Melrose.

Start with [AGENTS.md](AGENTS.md), [CODEX_START.md](CODEX_START.md), and the [experiment charter](docs/experiment-charter.md). This is a bootstrap, not a completed or validated world model.

No UI, production deployment, paid API, or runtime LLM is needed for the initial experiment. Do not publish raw residential address records, individual owner information, secrets, or restricted data in this public repository.

## Phase 0/1 workflow

Python 3.12 and outbound HTTPS to `www.arcgis.com`, `arcgisserver.digital.mass.gov`, and `services1.arcgis.com` are required for ingestion. MassGIS documentation is hosted at `www.mass.gov`. Raw official records and derived Parquet files remain under the ignored `data/` directory.

```bash
export UV_CACHE_DIR=/tmp/umwm-uv-cache
export UV_LINK_MODE=copy
uv venv --python python3.12 .venv
uv pip install --python .venv/bin/python -e '.[dev]'

.venv/bin/umwm status
.venv/bin/umwm sources --phase 1
.venv/bin/umwm ingest-town --town Stoneham --state MA
.venv/bin/umwm normalize
.venv/bin/umwm resolve
.venv/bin/umwm evaluate
```

The ingestion command snapshots ArcGIS item/layer metadata and every query page, records SHA-256 hashes and retrieval times, and reconciles paginated record counts. Normalization verifies those hashes before writing Address and Parcel contracts. Resolution accepts only exact normalized-address links; fuzzy matches are diagnostic candidates and are never promoted automatically.

Evaluation writes sanitized results to `reports/gate-a/`. The supplied 16-row business CSV is discovery input, not ground truth. Precision and recall are reported as not measured unless `--reference` points to an independently audited CSV with `address_id`, `expected_parcel_ids` (pipe-separated for many-to-many links), and `audit_status=audited`. Gate A also requires at least 50 audited cases; an absent or smaller reference set cannot pass.

Run the offline validation suite with:

```bash
.venv/bin/ruff format --check src tests
.venv/bin/ruff check src tests
.venv/bin/python -m pytest -q
```
