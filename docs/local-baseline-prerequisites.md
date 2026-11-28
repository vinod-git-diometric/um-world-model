# Local baseline prerequisite receipt

Status: the user explicitly authorized the 55 exact hosts below on 2026-11-28 and accepted the Python patch difference. The local baseline is complete; see the [census results](../reports/phase-2/digital-readiness-census.md). Gate A remains formally open.

- Checkout: `codex/stoneham-gate-a`, `2d3f463d8d39028a0d03f9e622a88f02ff524d12`; source, tests and pyproject unchanged from experiment checkpoint `c531643`.
- Migration located at repository-relative `stoneham-migration/`, not `~/stoneham-migration`.
- All six files passed the supplied SHA256SUMS. The four required data checksums also match the original handoff; exact bytes restored to their original paths. No cohort or physical graph rebuild.
- Frozen groups: 60 locations, one shared-site companion, three separate controls.
- Python: installed 3.12.16 versus reference 3.12.14. All 37 installed constrained distributions match their supplied versions; three source-reconstruction dependencies are absent (table below). No dependency changes made. This is a documented environment deviation, not an exact environment replay.
- Regression suite: 36 passed in 3.27 seconds using `.venv/bin/python -m pytest -q`.
- The virtual environment has no pip module; dependency comparison used `importlib.metadata` directly.
- `data/` and the migration directory are ignored; no raw data is tracked. Migration directory exclusion added to protect its checksum and checklist files as well.

| Package | Constraint | Installed |
| --- | --- | --- |
| et_xmlfile | 2.0.0 | NOT INSTALLED |
| openpyxl | 3.1.5 | NOT INSTALLED |
| xlrd | 2.0.2 | NOT INSTALLED |

These spreadsheet readers are needed only to rebuild discovery inputs, which this frozen baseline does not do. Connectivity was tested from the agent execution environment. Sandboxed probes were unsuccessful; an explicitly approved execution outside that sandbox reached all three representative hosts. The Book Oasis page returned 200, Body Mind Systems robots returned 308, and Rapid Liquors robots returned 200 followed by a homepage 301. Redirects were deferred. Private preflight receipts and the successful preflight transport log were retained. Source terms must be respected; authorization does not override robots restrictions.

## Approved host policy

The approved application configuration is `data/phase21/readiness-local-authorized-hosts.json`, copied byte for byte from `data/phase21/readiness-local-proposed-hosts.json`. It contains 55 exact hosts: the 52 checklist hosts used by non-platform frozen leads, plus three control URL variants present in the frozen manifest (`gaetanosfood.com`, `patinadstore.com`, `www.thebookoasis.com`). The staging host is excluded. Historical acquisition hosts and eight platform/transaction hosts unnecessary for this baseline are excluded. Redirects remain deferred; no automatic redirect following or capability-path crawling is authorized by this proposal.

Authorization and its checksum are recorded privately in `data/phase21/local-authorization.json`. The unchanged module entry point ran with the handoff arguments through a private standard-library `runpy` wrapper that enabled HTTPX/httpcore debug logging and checked input hashes before and after execution. No monkey-patching, retriever changes, parser changes, dependency installation, redirect following, or cohort substitution occurred.

Approved configuration SHA-256: `72b227b38ca60c142ff87ed705e77062fc39b484ede17f4567f18fd15f0ff1e6`.

```text
amysbodytherapy.com
bodymindsystems.com
ceramicapaintstudio.com
christinessweetshoppe.com
coughlinenvironmental.com
eyogamoves.com
gaetanosfood.com
jandbbutcher.com
littlecaesars.com
mathiacaconstruction.com
mcsweeneyproperties.com
nancysnailsandspa.com
naturalfoodexchange.com
nobilityhilltavern.com
patinadstore.com
pawsclub.com
pawwsitivelyclean.com
pignonescafe.com
redlotusnailsnspa.com
stonehamchiropractic.com
stores.truevalue.com
thebookoasis.com
thedirtydoodle.com
theenergybarre.com
thestonescommonhouse.com
thewinecellarsma.com
www.andersonbryantfuneralhome.com
www.arborsassistedliving.com
www.bankofamerica.com
www.bennysdrycleaners.com
www.bostonphotorental.com
www.bostonprolotherapy.com
www.cabralbeauty.com
www.carquest.com
www.ceramicapaintstudio.com
www.evvivatrattoria.com
www.flynnfence.com
www.gaetanosfood.com
www.patinadstore.com
www.prometheushomeservices.com
www.rapidliquors.com
www.redstonedental.com
www.redstoneliquors.com
www.shamelesswolf.com
www.signaturestyle.com
www.stonehamaccounting.com
www.stonehamdentalcare.com
www.stonehammadentist.com
www.tenderloveandcare.me
www.thebookoasis.com
www.thedirtydoodle.com
www.thestonescommonhouse.com
www.westernunion.com
www.xfinity.com
www.ymcametronorth.org
```
