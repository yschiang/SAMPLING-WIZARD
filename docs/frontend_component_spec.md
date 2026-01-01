# Frontend Component Specification
## Sampling & Recipe Generation Wizard (Gemini Implementation Guide) – v0

References:
- `sampling_architecture_full.md`
- `docs/user_flow.md`
- `api/openapi.yaml`

---

## 0. Principles (Must Follow)

1. Wizard is a projection of L1–L5; do not implement decision logic in UI.
2. Only backend L3 selects sampling points.
3. L4 returns warnings/scores without mutating points.
4. L5 is the only place for tool-specific recipe translation.
5. Upstream changes invalidate downstream outputs (UI must reset correctly).

---

## 1. UI Information Architecture

### Route
- `/wizard` (single-page wizard with stepper)

### Layout
- Stepper (6 steps)
- Context Summary panel (Tech / Process / Tool / Strategy)
- Main step content area
- Validation & Warnings panel (persistent)

---

## 2. Wizard State (Frontend)

### Types
- `WizardStep`: SelectTech | SelectProcessContext | SelectToolType | SelectSamplingStrategy | PreviewSamplingAndScoring | GenerateAndReviewRecipe

### State Shape (recommended)
- Inputs: tech, processContext, tool, strategy
- Derived/fetched: waferMaps, processOptions, toolOptions, strategyOptions
- Outputs: samplingOutput (L3), samplingScore (L4), toolRecipe (L5)
- UI: isLoading, blockingError, warnings[]

### Invalidation Rules
- change tech → clear process/tool/strategy/L3/L4/L5
- change process → clear tool/strategy/L3/L4/L5
- change tool → clear strategy/L3/L4/L5
- change strategy → clear L3/L4/L5
- re-run preview → overwrite L3/L4
- generate recipe → overwrite L5

---

## 3. Shared Components

### 3.1 WizardStepper
- shows progress and allows back navigation to completed steps
- forward navigation only via step CTA buttons

### 3.2 ContextSummaryPanel
- shows current selections
- provides "edit" jump back to relevant step

### 3.3 ValidationPanel
- displays blockingError and warnings
- provides retry actions for transient API failures

---

## 4. Step Components

### Step 1 — Select Tech (`StepSelectTech`)
UI:
- tech selector
- Next disabled until selection

API:
- GET `/v1/catalog/techs`
- GET `/v1/catalog/wafer-maps?tech=...`
- GET `/v1/catalog/process-options?tech=...`

---

### Step 2 — Select Process Context (`StepSelectProcessContext`)
UI:
- process step, intent, mode selectors
- derived fields: criticality, min/max points

API:
- GET `/v1/catalog/process-context?tech=...&step=...&intent=...&mode=...`
- GET `/v1/catalog/tool-options?tech=...&step=...&intent=...`

---

### Step 3 — Select Tool Type (`StepSelectToolType`)
UI:
- tool list/cards
- capability summary (max points, edge support, coordinate systems)

API:
- GET `/v1/catalog/tool-profile?toolType=...&vendor=...&model=...`

---

### Step 4 — Select Sampling Strategy (`StepSelectSamplingStrategy`)
UI:
- strategy cards (filtered by L2 allowed_strategy_set)
- optional params form
- CTA: Preview Sampling

No sampling execution here until user clicks preview.

---

### Step 5 — Preview Sampling & Scoring (`StepPreviewSamplingAndScoring`)
UI:
- wafer map viewer overlay points (read-only)
- scoring panel (coverage/statistical/risk/overall)
- warning list
- CTA: Generate Recipe

API (on Preview/Re-run):
1) POST `/v1/sampling/preview` → L3 SamplingOutput + warnings
2) POST `/v1/sampling/score` → L4 SamplingScoreReport

Rules:
- warnings do not auto-modify points
- explicit user confirmation required before Step 6

Subcomponent: `WaferMapViewer`
- renders wafer + selected points
- supports tooltip
- no point editing

---

### Step 6 — Generate & Review Recipe (`StepGenerateAndReviewRecipe`)
UI:
- read-only recipe preview (JSON viewer)
- translation notes
- export buttons (JSON; CSV optional)

API:
- POST `/v1/recipes/generate` → L5 ToolRecipe + warnings

---

## 5. Acceptance Criteria (Prototype v0)
1. Wizard completes Step 1–6 end-to-end using mocks aligned to OpenAPI.
2. Step 5 always shows preview + scoring before Step 6.
3. Invalidation rules behave exactly as defined.
4. Warnings never auto-change backend outputs.
5. Recipe is read-only and exportable.
