✅ Contract & API

 No changes to api/openapi.yaml (if changed: version bump + explicit approval)

 Endpoint paths/methods unchanged; no extra endpoints added

 Response envelopes match OpenAPI exactly (no extra/missing fields)

 warnings shape matches contract:

Preview + Generate: warnings: [{code, message}]

Score report warnings: as specified in schema (string list)

 Errors return ErrorResponse (no FastAPI default {detail: ...} leaks)

✅ Layer Boundaries (Hard Rules)

 L3: selects points only (may apply constraints; no tool-format translation)

 L4: read-only scoring only

 Does not filter points

 Does not reorder points

 Does not dedupe points

 Does not truncate points

 L5: tool-specific translation only

 coordinate conversion belongs here

 tool formatting belongs here

 any truncation/removal adds translation_notes + warnings

✅ Determinism

 Same input → same L3 selected_points (including ordering)

 Same input → same L4 scores (within exact calculation)

 Same input → same L5 recipe_payload shape + truncation behavior

 No use of unordered set() / random iteration that affects ordering

 Time-based fields (e.g., generated_at) are not used in equality assertions

✅ Tests (Must Protect Invariants)

 Unit test exists/updated for L4 no-mutation (deep equality on L3 output)

 Contract parsing test exists/updated (responses parse into Pydantic models)

 E2E test remains green: preview → score → generate

 Added/changed behavior includes corresponding tests (no untested changes)

✅ Scope Control

 Any “missing requirement” is logged as v1 proposal, not patched into v0 silently

 No cross-layer coupling introduced “for convenience”

 Catalog changes are data-driven (prefer backend/data/catalog/*.json)