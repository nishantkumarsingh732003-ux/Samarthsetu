# Legacy rule pack (pre-Phase 1)

`legacy-rule-pack.yaml` is the flat rule sketch from the original scaffold. It is kept
because its rule IDs and operator vocabulary are a useful starting point, but it does
NOT satisfy the CLAUDE.md contract: no provenance block, no `severity`, no
`message_i18n`, no `suggest_instead` redirect, and no `needs_verification` markers.

Phase 1 replaces it with one file per scheme family under `packages/rules/schemes/`.
