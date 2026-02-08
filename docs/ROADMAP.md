# ARAS Self-Evolution Roadmap

This roadmap lists staged upgrades to grow ARAS into a stronger local assistant over time.
It is designed for automated iteration (every 7 minutes) while keeping verification and
snapshots in place.

## Phase 1 (Foundations)
- Expand verification cases to cover more intents and safety checks.
- Add modular skills under `ARAS/modules/` with unit-level verification stubs.
- Introduce dataset ingestion metadata (size, license, source) and validation.

## Phase 2 (Learning Loop)
- Add an offline training queue that uses datasets in `datasets/`.
- Track training runs in logs and link them to brain improvements.
- Add model versioning to keep old checkpoints for rollback.

## Phase 3 (Tooling & Evaluation)
- Add offline evaluation scripts (accuracy, regression checks).
- Extend the dashboard to show training metrics and regression status.
- Implement guarded auto-rollback if verification fails.

## Phase 4 (Capabilities)
- Add structured memory modules and retrieval for long-term context.
- Expand skill modules with deterministic tests.
- Allow optional web ingestion with strict allowlists and size limits.
