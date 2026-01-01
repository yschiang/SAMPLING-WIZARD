# User Flow Specification
## Sampling & Recipe Generation Wizard (v0)

Reference baseline:
- `sampling_architecture_full.md`

---

## 0. Purpose & Scope

### Purpose
Define the **user-facing workflow (Wizard)** for generating sampling points and tool recipes, aligned to L1–L5 responsibilities.

Focus:
- User actions and decision flow
- UI states and transitions
- Validation, warnings, and error handling

### Scope (v0)
- Single-wafer, single-recipe generation
- Non-adaptive baseline (no auto feedback loop)
- UI flow only (no backend implementation details)

---

## 1. Persona & Goals

### Primary Persona
Process Engineer / Tool Engineer

### Goals
- Generate sampling points aligned with process risk and tool capability
- Understand sampling quality before recipe generation
- Export a validated tool recipe

### Non-Goals
- Manual die-level point editing
- SPC/control-chart interaction
- Multi-wafer aggregation

---

## 2. Wizard Overview

### Happy Path (Step Flow)
Start
→ Step 1: Select Tech
→ Step 2: Select Process Context
→ Step 3: Select Tool Type
→ Step 4: Select Sampling Strategy
→ Step 5: Preview Sampling & Scoring
→ Step 6: Generate & Review Recipe
→ Finish

Design principle:
- Early steps define context (L1 / L2 / L2b)
- Middle steps perform decision (L3)
- Later steps evaluate and translate (L4 / L5)

---

## 2.1 Wizard → L1–L5 Architecture Mapping

The Wizard is a **projection of the architecture**, not a separate decision system.

### Mapping Diagram (Text)
- Step 1: Select Tech → **L1 WaferMapSpec**
- Step 2: Select Process Context → **L2 ProcessContext**
- Step 3: Select Tool Type → **L2b ToolProfile**
- Step 4: Select Sampling Strategy → **L3 SamplingStrategy** (Decision Layer)
- Step 5: Preview Sampling & Scoring → **L3 SamplingOutput (read-only)** + **L4 SamplingScoreReport** (Evaluation Layer)
- Step 6: Generate & Review Recipe → **L5 RecipeTranslator** (Translation Layer)

### Responsibility Alignment Rules (Critical)
1. Only Step 4/5 triggers selection (L3). (Step 4 chooses strategy; Step 5 executes preview.)
2. Step 5 scoring (L4) emits warnings **without mutating** sampling output.
3. Recipe generation (L5) occurs only in Step 6.
4. Upstream changes invalidate downstream outputs.

---

## 3. Step-by-Step User Flow

### Step 1 — Select Tech
**Purpose**: establish technology baseline determining available wafer maps and downstream options.

Inputs:
- Tech

System:
- Load WaferMapSpec list (L1)
- Filter valid ProcessContext options

Errors:
- No available wafer map → blocking

---

### Step 2 — Select Process Context
**Purpose**: define manufacturing intent and risk boundary (L2).

Inputs:
- Process Step
- Measurement Intent
- Mode (INLINE / OFFLINE / MONITOR)

Derived (read-only):
- Criticality
- Min/Max sampling points

Errors:
- Invalid combination → blocking
- Unsupported for selected Tech → blocking

---

### Step 3 — Select Tool Type
**Purpose**: define execution constraints (L2b).

Inputs:
- Tool Type
- Optional Tool Model / Vendor

UI:
- Tool capability summary (max points, edge support, coordinate system)

Warnings (non-blocking):
- Tool limitation may reduce coverage

---

### Step 4 — Select Sampling Strategy
**Purpose**: choose how sampling points are selected (L3 strategy selection).

Inputs:
- Strategy (filtered by L2 allowed_strategy_set)
- Strategy params (optional)

Validation:
- Strategy not allowed → blocking

---

### Step 5 — Preview Sampling & Scoring
**Purpose**: provide decision transparency before recipe generation.

System actions:
1) Execute L3 selection → SamplingOutput
2) Execute L4 evaluation → SamplingScoreReport

UI:
- Wafer map overlay (selected points)
- Score panel (coverage/statistical/risk/overall)
- Warnings list

Rules:
- Warnings do NOT auto-modify sampling
- User explicitly confirms to proceed

---

### Step 6 — Generate & Review Recipe
**Purpose**: translate approved sampling points into tool-executable recipe (L5).

System:
- Execute RecipeTranslator.translate()

UI:
- Recipe preview (read-only)
- Translation notes
- Export options (JSON / CSV if supported)

Errors:
- Translation failure or constraint violation → blocking with explanation

---

## 4. Wizard State Model

Primary states:
- Idle
- SelectingTech
- SelectingProcess
- SelectingTool
- SelectingStrategy
- PreviewingSampling
- GeneratingRecipe
- Completed

Rules:
- Cannot skip steps
- Back navigation preserves context
- Any upstream change invalidates downstream results

---

## 5. Validation & Error Semantics

Blocking errors:
- Invalid Tech/Process/Tool combination
- No valid WaferMapSpec
- Strategy not permitted by ProcessContext
- Recipe translation constraint violations (if not handled as truncation in v0)

Non-blocking warnings:
- Reduced edge coverage
- Tool-induced truncation
- Marginal statistical sufficiency

Warnings are informative only and never auto-correct decisions.

---

## 6. Explicit Non-Goals (UI)

- Manual die-level editing
- Auto-fixing sampling based on score
- Multi-wafer batch generation

---

## 7. References
- Architecture: `sampling_architecture_full.md`
- Scaffold: `docs/prototype_scaffold.md`
