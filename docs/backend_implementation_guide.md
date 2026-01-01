# Backend Implementation Guide (Claude)
## Sampling Wizard Backend (Prototype v0)

Baseline (must align):
- sampling_architecture_full.md
- docs/user_flow.md
- docs/frontend_component_spec.md
- docs/prototype_scaffold.md
- api/openapi.yaml

---

## 0. Non-Negotiables (Architecture Guards)

1. **L4 MUST NOT mutate L3 output**
   - No adding/removing/reordering points in scoring.
2. **Tool-specific logic MUST stay in L5**
   - L3 selection is tool-agnostic except for applying ToolProfile constraints.
3. **Schema validation is the first gate**
   - Reject invalid payloads with `VALIDATION_ERROR`.
4. **Warnings do not change HTTP status**
   - Use 200 + `warnings[]` for non-blocking cases.
5. **Deterministic outputs**
   - Same inputs produce same outputs (critical for tests).

---

## 1. Recommended Stack (Prototype-friendly)

- FastAPI + Pydantic v2
- Pytest for unit/e2e
- Optional: JSONSchema validation to mirror `/schemas` exactly

---

## 2. Backend Layout (Suggested)

```text
backend/
├── src/
│   ├── server/
│   │   ├── main.py
│   │   └── routes/
│   │       ├── catalog.py
│   │       ├── sampling.py
│   │       └── recipes.py
│   ├── engine/
│   │   ├── l1/  l2/  l2b/  l3/  l4/  l5/
│   │   ├── translators/
│   │   └── validators/
│   └── models/
├── tests/
│   ├── unit/
│   └── e2e/
└── data/
    └── catalog/
```

Keep module boundaries aligned to L1–L5; avoid cross-layer leakage.

---

## 3. Endpoint Implementation Notes

### 3.1 Catalog (Wizard Steps 1–3)
Implement using static JSON for v0:
- GET `/v1/catalog/techs`
- GET `/v1/catalog/wafer-maps?tech=...`
- GET `/v1/catalog/process-options?tech=...`
- GET `/v1/catalog/process-context?...`
- GET `/v1/catalog/tool-options?...`
- GET `/v1/catalog/tool-profile?...`

Return:
- 404 NOT_FOUND if ids missing
- 400 VALIDATION_ERROR if invalid combinations

---

### 3.2 POST `/v1/sampling/preview` (L3 selection only)
Input: L1 + L2 + L2b + StrategySelection  
Output: L3 SamplingOutput + warnings[]

Steps:
1) Validate schema
2) Validate business rules:
   - strategy_id ∈ process_context.allowed_strategy_set
3) Execute L3 selection:
   - `SamplingSelector.select(L1, L2, L2b, strategy)`
4) Return L3 output and any non-blocking warnings

Do not translate to tool coordinates here (that is L5).

---

### 3.3 POST `/v1/sampling/score` (L4 evaluation only)
Input: L1 + L2 + L2b + L3  
Output: L4 SamplingScoreReport

Steps:
1) Validate schema
2) Validate points within L1 valid mask
3) Execute L4 evaluation:
   - `SamplingScorer.evaluate(L1, L2, L2b, L3)`
4) Return score report

**Guard:** L4 must not mutate L3 output.

---

### 3.4 POST `/v1/recipes/generate` (L5 translation)
Input: L1 + L2b + L3 (+ optional L4 for notes)  
Output: L5 ToolRecipe + warnings[]

Steps:
1) Validate schema
2) Enforce ToolProfile constraints deterministically:
   - if max_points exceeded: truncate deterministically + warning + translation_note
3) Translate coordinates:
   - die_x/die_y → x_mm/y_mm via die_pitch
4) Return ToolRecipe payload + translation notes

---

## 4. Prototype Strategy (L3) – CENTER_EDGE (Recommended)

Deterministic candidate offsets:
- (0,0), (±3,0), (0,±3), (±8,0), (0,±8), (±6,±6)

Algorithm:
1) Generate candidates in fixed order
2) Filter by L1 valid mask
3) Apply ToolProfile constraints (edge support / max points) as constraints only
4) Respect L2 min/max:
   - if > max: truncate deterministically
   - if < min: return CONSTRAINT_ERROR (or 200 with warning, but pick one policy and keep consistent)

Output:
- sampling_strategy_id="CENTER_EDGE"
- selected_points[]
- trace: strategy_version + generated_at

---

## 5. Scoring (L4) – Simple Deterministic v0

Required outputs:
- coverage_score, statistical_score, risk_alignment_score, overall_score (0..1)
- warnings[] (strings)
- version

Suggested method:
- coverage: rings hit / 3 (inner/mid/outer)
- statistical: based on n vs min/max
- risk alignment: penalize missing outer ring when criticality=HIGH
- overall: weighted average (fixed weights)

Warnings examples:
- HIGH criticality but no outer-ring hit
- point count near tool max

---

## 6. Error & Warning Conventions

Blocking errors (HTTP 4xx/5xx) use ErrorResponse:
- type: VALIDATION_ERROR / NOT_FOUND / CONSTRAINT_ERROR / INTERNAL_ERROR

Non-blocking warnings return in 200 response body:
- preview: `warnings[]`
- generate recipe: `warnings[]`

Keep warning codes stable for FE handling.

---

## 7. Tests (Must Have)

Unit tests:
- L3 deterministic outputs & valid mask
- L4 non-mutation (deep equality of input points)
- L5 conversion + truncation notes

E2E test:
- preview → score → generate recipe
- asserts non-mutation and constraint behavior

---

## 8. Definition of Done (Backend v0)

- All endpoints in `api/openapi.yaml` implemented
- Unit tests for L3/L4/L5 pass
- One E2E test passes
- Frontend can switch from mocks to real API without contract changes
