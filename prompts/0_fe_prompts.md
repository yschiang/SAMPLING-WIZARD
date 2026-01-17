# Frontend v1 Milestones — Sampling Wizard

This document defines the **Frontend (FE) v1 milestone plan** for the Sampling Wizard, based on the frozen v0 architectural baseline.

v1 focuses on:
- Completing the end-to-end Wizard UX
- Integrating with the backend walking skeleton
- Ensuring FE correctness without embedding domain logic

---

## FE v1 Scope Definition

**Included**
- Full Wizard flow (L1 → L5)
- Backend integration via OpenAPI
- Visualization and UX polish
- Error and warning handling
- Export and preview flows

**Explicitly Excluded**
- Sampling algorithms
- Scoring logic
- Tool translation logic
- Backend contract changes

FE is a **projection layer only**.

---

## FE v1 Milestone Breakdown

Each milestone:
- Is implemented in **one PR = one commit**
- Uses commit format: `feat(fe): <milestone>`
- Produces user-visible value
- Does not require backend algorithm completeness

---

## M1 — App Shell & Routing

**Goal**  
Establish a stable UI container for the Sampling Wizard.

**Deliverables**
- Application layout (header / title / main content)
- Wizard entry route (e.g. `/wizard`)
- Placeholder step pages

**Acceptance Criteria**
- FE app boots successfully
- Wizard route renders consistently
- No business logic implemented

---

## M2 — Wizard Stepper & State Container

**Goal**  
Implement the Wizard state machine and step transitions.

**Deliverables**
- Stepper UI component
- Centralized FE state container
- Step invalidation rules:
  - Upstream changes reset downstream state

**Acceptance Criteria**
- Step navigation works (next / back)
- State resets correctly when Tech / Process changes
- State is serializable and debuggable

---

## M3 — Catalog Fetch Layer (GETs)

**Goal**  
Populate Wizard options from backend catalog APIs.

**Deliverables**
- FE API client for catalog endpoints
- Tech / Process / Tool dropdowns
- Basic error handling for failed GETs

**Acceptance Criteria**
- Data loaded from backend, not hardcoded
- UI reacts to backend data changes
- No invented fields beyond OpenAPI

---

## M3b — Warnings Component (Basic)

**Goal**  
Create a reusable, non-blocking warnings UI.

**Deliverables**
- Warnings list/banner component
- Ability to render warnings from backend responses
- Visual distinction from blocking errors

**Acceptance Criteria**
- Warnings are visible but non-blocking
- Component reusable across Preview / Score / Generate

---

## M4 — Preview (L3) + Wafer Map Rendering

**Goal**  
Allow users to preview sampling results visually.

**Deliverables**
- POST `/v1/sampling/preview` integration
- Wafer map visualization (simple grid / plot acceptable)
- Points list or table
- Preview warnings display

**Acceptance Criteria**
- Preview call succeeds
- Returned points are rendered consistently
- FE does not modify or generate sampling logic

---

## M5 — Score (L4) + Score Panel

**Goal**  
Display sampling quality evaluation.

**Deliverables**
- POST `/v1/sampling/score` integration
- Score panel showing:
  - coverage score
  - statistical score
  - risk alignment score
  - overall score

**Acceptance Criteria**
- Scores render correctly
- No mutation or reordering of points
- Scoring warnings displayed (if present)

---

## M6 — Generate Recipe (L5) + Preview / Export

**Goal**  
Generate and export tool recipe payloads.

**Deliverables**
- POST `/v1/recipes/generate` integration
- Recipe preview (JSON viewer)
- Export / download functionality
- Translation notes and warnings display

**Acceptance Criteria**
- Recipe payload matches backend response exactly
- Export works reliably
- FE does not implement translation logic

---

## M7 — UX Polish & Consistency

**Goal**  
Make the Wizard usable and coherent as a product.

**Deliverables**
- Consistent loading / error / warning states
- Disabled states for invalid steps
- Minor layout and interaction polish

**Acceptance Criteria**
- Smooth end-to-end Wizard flow
- Clear user feedback at every step
- No architectural rule violations

---

## FE v1 Completion Definition

FE v1 is considered **complete** when:
- The full Wizard (L1 → L5) works end-to-end
- All backend endpoints are integrated
- UI correctly renders preview, score, and recipe outputs
- FE remains contract-pure and logic-free

Backend algorithm quality **does not block FE v1 completion**.

---

## Notes for FE Contributors

- Follow `docs/user_flow.md` and `docs/frontend_component_spec.md` strictly
- Use OpenAPI as the single source of truth
- Log missing needs as **v1 proposals**
- Do not patch backend contracts directly

---

## Summary

FE v1 is about **completeness of experience**, not correctness of algorithms.

By following these milestones:
- FE can move fast
- BE can iterate safely
- Architecture remains intact
