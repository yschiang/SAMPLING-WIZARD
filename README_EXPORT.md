# README_EXPORT.md
## Sampling Wizard – v0 Baseline Export Guide

This repository contains the **v0 baseline specification** for the Sampling Wizard.
It is ready to be consumed by **Frontend (Gemini)** and **Backend (Claude)** teams.

---

## 1. What This Is

This export provides a **complete, closed-loop baseline** including:

- Architecture boundaries (L1–L5)
- User flow (Wizard)
- Frontend component specification
- Backend implementation guide
- API contract (OpenAPI)
- Monorepo scaffold

**Status:** Stable v0 baseline  
**Change policy:** No breaking changes without version bump and review.

---

## 2. Who Should Read What (Very Important)

### Frontend (Gemini) – Required Reading Order
1. `docs/user_flow.md`
2. `docs/frontend_component_spec.md`
3. `api/openapi.yaml`

**Frontend responsibilities**
- Implement Wizard UI exactly as specified
- Use mock data aligned with OpenAPI examples
- Do NOT implement sampling logic in UI
- Do NOT auto-correct based on warnings

### Backend (Claude) – Required Reading Order
1. `sampling_architecture_full.md`
2. `docs/backend_implementation_guide.md`
3. `docs/prototype_scaffold.md`
4. `api/openapi.yaml`

**Backend responsibilities**
- Enforce L1–L5 responsibility boundaries
- Implement L3/L4/L5 as isolated endpoints
- Validate inputs strictly
- Emit warnings without mutating upstream outputs

### Baseline Owner
- Guard the baseline
- Review all proposed changes
- Own versioning decisions

---

## 3. Repository Structure (Authoritative)

```text
sampling-wizard-v0-export/
├── README_EXPORT.md
├── sampling_architecture_full.md
├── api/
│   └── openapi.yaml
└── docs/
    ├── user_flow.md
    ├── frontend_component_spec.md
    ├── backend_implementation_guide.md
    └── prototype_scaffold.md
```

---

## 4. Architectural Invariants (DO NOT VIOLATE)

1. Only **L3** selects sampling points.
2. **L4** evaluates only – **no mutation** of L3 outputs.
3. **L5** performs tool-specific translation only.
4. Warnings never change HTTP status.
5. UI never auto-fixes backend decisions.
6. Schemas + OpenAPI are the single source of truth.

---

## 5. API Usage Rules

Frontend calls in this order:
1. `/v1/sampling/preview` (L3)
2. `/v1/sampling/score` (L4)
3. `/v1/recipes/generate` (L5)

---

## 6. Change & Versioning Policy

### Allowed Without Version Bump
- New tech entries / catalog data
- Additional warnings (non-breaking)

### Requires Version Bump (v0 → v1)
- Schema field changes
- Endpoint signature changes
- Responsibility changes for L3/L4/L5
- Introducing adaptive sampling behavior

All changes must be proposed via issue/PR and reviewed by baseline owner.

---

## 7. Common Misunderstandings

❌ “Frontend can tweak sampling points for UX”  
→ No. UI is read-only for L3 outputs.

❌ “Scoring can fix low coverage automatically”  
→ No. L4 evaluates only.

❌ “We can skip preview and go straight to recipe”  
→ No. Preview & scoring are mandatory in Wizard v0.

---

## 8. Definition of Done (v0)

- FE Wizard works end-to-end using mocks
- BE implements all endpoints in OpenAPI
- One E2E flow passes: preview → score → generate recipe
- No contract drift between FE and BE

---

## 9. What Comes Next (v1 Roadmap – Not in v0)

- Adaptive sampling (L4 → L3 feedback loop)
- Multi-wafer aggregation
- Tool-specific recipe variants
- Advanced wafer visualization overlays

---

## 10. Final Note

This baseline exists to:
- Prevent responsibility creep
- Enable parallel FE/BE development
- Make future evolution safe and reviewable

If in doubt, follow the documents, not assumptions.
