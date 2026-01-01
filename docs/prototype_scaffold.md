# Prototype Scaffold Specification
## Monorepo Layout + API + Schemas (Claude Backend / Gemini Frontend Alignment)

References:
- sampling_architecture_full.md
- docs/user_flow.md
- docs/frontend_component_spec.md
- api/openapi.yaml

---

## 0. Goals
- Runnable end-to-end flow: Tech → Process → Tool → Strategy → Preview(L3/L4) → Recipe(L5)
- Single source of truth for contracts (OpenAPI + schemas/examples)
- Clear separation between backend decision engine (Claude) and frontend wizard UI (Gemini)

---

## 1. Monorepo Layout (Recommended)

```text
repo/
├── sampling_architecture_full.md
├── docs/
│   ├── user_flow.md
│   ├── frontend_component_spec.md
│   ├── backend_implementation_guide.md
│   └── prototype_scaffold.md
├── api/
│   └── openapi.yaml
├── schemas/                # optional in v0; can be added as code-level schemas later
├── backend/
└── frontend/
```

---

## 2. Contract Strategy
- OpenAPI is the contract between FE and BE.
- Examples (optional next step) should be shared by FE mocks and BE e2e tests.
- Any breaking change requires version bump.

---

## 3. API Surface (v0)

Catalog endpoints (Steps 1–3):
- GET /v1/catalog/techs
- GET /v1/catalog/wafer-maps?tech=...
- GET /v1/catalog/process-options?tech=...
- GET /v1/catalog/process-context?tech=...&step=...&intent=...&mode=...
- GET /v1/catalog/tool-options?tech=...&step=...&intent=...
- GET /v1/catalog/tool-profile?toolType=...&vendor=...&model=...

Execution endpoints:
- POST /v1/sampling/preview  → L3 SamplingOutput + warnings
- POST /v1/sampling/score    → L4 SamplingScoreReport
- POST /v1/recipes/generate  → L5 ToolRecipe + warnings

---

## 4. Definition of Done (Prototype v0)
1. Frontend completes Step 1–6 using mocks aligned to OpenAPI.
2. Backend implements all endpoints in OpenAPI (catalog can be static JSON).
3. One e2e demo passes: preview → score → generate recipe.
