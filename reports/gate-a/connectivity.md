# Stoneham Gate A connectivity status

Gate A is pending. The managed runtime returned HTTP 200 for the MassGIS documentation, the ArcGIS address catalog item, and parcel layer metadata. The catalog resolved the address FeatureServer to `arcgisserver.digital.mass.gov`. The proxy rejected HTTPS CONNECT to that host with 403, including on an approved retry.

The parcel layer exposes `OBJECTID`, `TOWN_ID`, `LOC_ID`, `MAP_PAR_ID`, `PROP_ID`, `SITE_ADDR`, `USE_CODE`, and `FY`. The live `TOWN_ID=284` count query returned 8,046 records. A scoped sample query returned one record with the same town ID. This is a source count and schema check.

The address schema, full address and parcel resolution, and unresolved-case breakdown remain pending. There are zero independently audited reference cases available in this checkout. Address and parcel precision, recall, and provenance completeness remain unmeasured. The 16 seed rows are discovery inputs. The evaluator on this branch scores parcel link sets, so separate address metrics and provenance verification against live snapshots are still required before a Gate A decision.

After granting HTTPS access to the address host, follow the Phase 0/1 workflow in the repository README. Keep raw source records and any private audit evidence out of Git.
