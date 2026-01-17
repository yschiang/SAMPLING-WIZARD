# BE_V1_2_STRATEGY_PLAN.md
**Sampling Wizard — L3 Strategy Governance + Registry + v1.2 Strategy Expansion Plan**

**Goal:** Extend L3 sampling strategies safely **without contract drift** and without breaking FE.  
**Method:** Execute in the order **4 → 2 → 3**:

- **(4)** ProcessContext `allowed_strategy_set` (product governance)
- **(2)** Minimal Strategy Registry (engineering scalability)
- **(3)** Add 2–3 new strategies (feature value)

**Non-negotiables (apply to every PR):**
- **No OpenAPI changes** (`api/openapi.yaml` frozen)
- **No endpoint changes** (no add/remove/rename)
- **Deterministic outputs** for identical inputs
- **L4 must not mutate L3 outputs** (already guarded; must remain)
- **Warnings vs errors** per baseline:
  - Non-blocking: HTTP 200 + `warnings[]`
  - Blocking: 4xx/5xx with `ErrorResponse`

---

## 0) Scope & Assumptions

### In-scope
- L3 strategy governance and scalability
- L3 algorithm additions
- Tests + fixtures + golden path validation
- Catalog adjustments **only if schema already supports it** (same response envelope)

### Out-of-scope
- Any contract/schema changes
- L4 scoring improvements
- L5 translation changes (unless a new strategy triggers an existing constraint path)
- Auth/RBAC/SSO

---

## 1) Target Deliverables

By the end of this plan:

1) **ProcessContext returns `allowed_strategy_set`** and BE enforces it.  
2) L3 uses a **minimal strategy registry** (no algorithm logic in route handlers).  
3) At least **3 strategies** available (including existing `CENTER_EDGE`):
   - `CENTER_EDGE` (existing, migrated into registry)
   - `EDGE_ONLY` (new)
   - `GRID_UNIFORM` (new)
   - `ZONE_RING_N` (new, parameterized rings/zone-based)

---

## 2) PR Breakdown (4 → 2 → 3)

### PR-A (v1.0) — Strategy Allowlist Governance (4)
**Intent:** Product governance first: UI only shows valid strategies; BE rejects invalid usage.

#### Scope (what changes)
- Ensure `ProcessContext.allowed_strategy_set` is populated via catalog data.
- Enforce in `/v1/sampling/preview`:
  - if `strategy_id` not in allowlist → **4xx ErrorResponse** (e.g., 409/422 per existing standard).

#### Must NOT change
- OpenAPI
- Response shapes
- L3 selection logic behavior (CENTER_EDGE may remain as-is for this PR)

#### Expected files touched (examples)
- `backend/data/catalog/*` (if catalog is file-driven; if still hardcoded, adjust the same source)
- `backend/src/server/routes/sampling.py` (or equivalent router layer)
- `backend/src/models/*` (only if needed for internal validation; no schema changes)

#### Tests
- Unit: `strategy_id` not allowed → 4xx ErrorResponse (stable code/message)
- Unit: allowed strategy passes
- Regression: existing golden path still works

#### Acceptance Criteria
- FE can hide disallowed strategies without hardcoding.
- BE rejects disallowed strategies deterministically.
- All tests green.

---

### PR-B (v1.1) — Minimal Strategy Registry (2)
**Intent:** Create the “highway” for adding strategies safely, without building a heavy framework.

#### Minimal Registry Definition (do this, nothing more)
- `strategy_id → engine` mapping (dictionary/registry)
- One engine per module (testable)
- A single interface signature used by all engines
- Shared utilities for:
  - deterministic ordering
  - mask filtering
  - min/max enforcement
  - trace metadata

✅ Avoid:
- DI containers
- dynamic plugin loading
- reflection
- complex configuration DSL

#### Proposed folder layout
```
backend/src/engines/l3/
  __init__.py
  registry.py               # maps id -> engine callable
  common.py                 # shared deterministic helpers
  strategies/
    center_edge.py          # existing behavior moved here
    edge_only.py            # later
    grid_uniform.py         # later
    zone_ring_n.py          # later
```

#### Interface (conceptual)
- `select_points(request_ctx) -> SamplingOutput`
- `request_ctx` includes resolved:
  - `WaferMapSpec`
  - `ProcessContext`
  - `ToolProfile`
  - strategy params

#### Scope (what changes)
- Move existing `CENTER_EDGE` logic out of routes and into `strategies/center_edge.py`
- Add `registry.py` dispatch
- Routes call registry + common validators
- Keep behavior identical (or prove changes are intentional via golden fixtures)

#### Must NOT change
- Endpoint request/response envelopes
- Any semantics not explicitly declared in PR description

#### Tests
- Regression/golden: CENTER_EDGE output remains the same for fixed inputs
- Unit: registry dispatch selects correct engine
- Determinism: same input → same output (repeat N times)
- Mask filtering + min/max enforcement remain correct

#### Acceptance Criteria
- Route handler contains **no selection algorithm** (only validation + dispatch).
- CENTER_EDGE works unchanged (or change is explained + approved).
- Clean path for adding new strategies with small PRs.

---

### PR-C Series (v1.2) — Add New Strategies (3)
**Intent:** Add real strategies one-by-one, each as a small PR.

#### PR-C1 — `EDGE_ONLY`
**Definition**
- Prefer outer ring points only (as defined by wafer grid / radius buckets).
- Deterministic ordering (e.g., angle-sorted or fixed scan order).
- Apply `valid_die_mask` filtering.
- Enforce min/max via common utility.

**Tests**
- Determinism test
- Mask filtering test
- Edge-support constraint handling (warning/error per existing policy)

**Acceptance**
- FE can select EDGE_ONLY when allowed by ProcessContext
- Outputs deterministic and schema-correct

---

#### PR-C2 — `GRID_UNIFORM`
**Definition**
- Uniform grid sampling over valid die set:
  - Use deterministic stride selection (e.g., pick every k-th die in sorted order)
  - Or generate grid intersections mapped to nearest valid die deterministically
- Apply mask filtering first, then selection
- Enforce min/max via common utility

**Tests**
- Determinism test
- Coverage sanity (non-empty, not all clustered)
- Min/max enforcement

**Acceptance**
- Produces evenly distributed points across wafer (basic)
- Deterministic and FE unchanged

---

#### PR-C3 — `ZONE_RING_N` (parameterized)
**Definition**
- Divide wafer into N rings/zones (N from strategy params; default 3).
- Allocate points per ring deterministically:
  - e.g., fixed distribution (center:1, middle:x, edge:y) or proportional to area
- Select within each ring via deterministic ordering
- Apply mask filtering
- Enforce min/max overall (after ring allocation)

**Tests**
- Determinism test with parameter variations
- Ring allocation stable
- Works for N=3 default

**Acceptance**
- Adds a flexible “engineer-friendly” zone-based strategy
- Still deterministic and schema-correct

---

## 3) Determinism & Ordering Policy (Must be explicit)

To avoid accidental drift, define a single ordering policy in `common.py` and reuse it:

### Recommended canonical point ordering
1) Sort by **radius bucket** (center → edge)
2) Within bucket, sort by **angle** (atan2) ascending
3) Tie-break by `(die_x, die_y)` ascending

Alternative deterministic ordering is acceptable, but must be:
- documented
- consistent across strategies (unless strategy requires otherwise)
- covered by tests/fixtures

---

## 4) Mask Filtering & Constraints Handling (Shared)

### Mask filtering (L1)
- Always apply `WaferMapSpec.valid_die_mask` filtering **before** final selection.

### Constraints (L2 + ToolProfile)
- `min_sampling_points` / `max_sampling_points` enforced deterministically.
- Policy (warning vs error) must match existing BE baseline:
  - Truncation to max: usually **warning**
  - Too few points after filtering: usually **error** (unless baseline says warning)

> If any policy is unclear in the current baseline, create a **proposal:v1** issue, do not “guess”.

---

## 5) FE/BE Coordination Contract (No blocking)

### FE expectations
- FE only renders strategies returned from allowlist.
- FE does not hardcode strategy ids except display labels.

### BE expectations
- BE enforces allowlist strictly.
- New strategies are added behind the same endpoint and schema.

### Shared fixtures (recommended)
Create `backend/tests/fixtures/` (or `api/examples/`) with:
- golden request payloads (tech/process/tool/strategy)
- expected outputs for each strategy (snapshot-like)

This becomes the shared “golden path” across FE + BE.

---

## 6) Release / Tagging Suggestions

- `v1.0-strategy-allowlist` (PR-A)
- `v1.1-l3-strategy-registry` (PR-B)
- `v1.2-strategies-edge-grid-zone` (PR-C series)

---

## 7) Architect Gate Checklist (for these PRs)

### Contract safety
- [ ] OpenAPI unchanged
- [ ] No endpoint changes
- [ ] No envelope/field rename

### Governance correctness (PR-A)
- [ ] allowlist present in ProcessContext
- [ ] BE rejects disallowed strategy with correct ErrorResponse

### Registry correctness (PR-B)
- [ ] Algorithms moved out of routes
- [ ] CENTER_EDGE behavior preserved (or approved change)
- [ ] Determinism tests exist

### Strategy PRs (PR-C*)
- [ ] One strategy per PR
- [ ] Deterministic ordering documented
- [ ] Mask filtering + min/max enforced
- [ ] Tests updated + golden path remains green

---

## 8) “Proposal:v1” Handling (when uncertain)

If BE finds ambiguity (e.g., warnings vs errors rules for a new strategy):
- Create GitHub issue tagged: `proposal:v1`
- Include:
  - problem statement
  - affected endpoints/UX
  - recommended policy
  - test expectations

Do **not** implement ad-hoc behavior without architect approval.
