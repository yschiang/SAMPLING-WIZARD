# FE Integration: v1.3 Strategy Configuration

**Status:** Ready for Review
**Branch:** `dev-v1.3-strategy-config`

## Overview
This PR integrates the v1.3 Strategy Configuration API, exposing the 3 common parameters (`edge_exclusion_mm`, `target_point_count`, `rotation_seed`) in the Wizard UI (Step 4). It also includes the new DOM-based Wafer Map visualization (Step 5).

## Changes

### 1. Strategy Configuration (Step 4)
- **UI:** Added a "Strategy Configuration" panel that appears below the selected strategy card.
- **Controls:**
  - `Target Point Count` (1-1000)
  - `Edge Exclusion (mm)` (0-500)
  - `Rotation Seed` (integer)
- **State:** Managed via `WizardContext` using new `SET_STRATEGY_PARAMS` action.
- **API:** Updated `previewSampling` call to include `params` object in the request body.

### 2. Wafer Map Visualization (Step 5)
- **Component:** Implemented `WaferMap` using CSS Grid (no Canvas).
- **Features:** 
  - 60x60 grid performance optimization (React.memo).
  - Interactive cell selection (click to toggle).
  - Hover tooltips with coordinates.
  - Axes and Values toggles.
  - Discrete color legend.

### 3. Architecture
- **Context:** Updated `WizardContext` reducer to handle strategy parameters and reset them on strategy change.
- **Type Safety:** Verified `SamplingPreviewRequest` matches v1.3 spec.

## Verification Scenarios (Passed)

| Scenario | Description | Result |
| :--- | :--- | :--- |
| **1. Happy Path** | Select strategy, keep defaults, preview. | ✅ Params sent, preview rendered. |
| **2. Edge Exclusion** | Change exclusion to 10mm. | ✅ Param updated, request payload correct. |
| **3. Point Count** | Change target to 500. | ✅ Param updated, request payload correct. |
| **4. Seed** | Change seed to 123. | ✅ Param updated, request payload correct. |
| **5. Invalid Params** | (Simulated) Backend returns 422. | ✅ Error displayed in UI. |
| **6. Missing Context** | Try accessing step without context. | ✅ Redirects/shows empty state. |

## Next Steps
- Architect review of the UI flow.
- Merge to `main` (or feature branch).
