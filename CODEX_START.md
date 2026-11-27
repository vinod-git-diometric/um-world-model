# Codex task: Phase 0 and Phase 1

Read AGENTS.md and the experiment charter. Work on a separate branch. Execute Phase 0 and Phase 1, not just propose code. Verify sources and schema against actual responses. Freeze an independently audited reference set before evaluating; the seed CSV is discovery input, not ground truth. If 50 cases cannot be audited, report exactly how many and label the result exploratory.

Implement CLI commands for source listing, town ingestion, normalization, resolution and evaluation. Preserve raw data locally with hash and manifest; no raw residential/owner data committed. Test exact matches, suffixes, units, multiple parcels, shared addresses, nulls, pagination, source failures, idempotence. Run unit tests offline and run real source ingestion with permitted outbound HTTPS. Generate a sanitized benchmark report with numerator/denominator, precision, recall, unresolved cases, source failures, reproducibility instructions, and provenance completeness. Do not report precision from source agreement alone.

Open a PR including results and stop at Gate A. If network or permissions block execution, report the exact failure and what remains untested. Do not build a UI or proceed to Phase 2 without review.
