# Backend Execution Plan v1.1
**BE Agent Planning Result**

Author: Backend Engineer (BE) Agent  
Date: 2026-01-03  
Baseline Alignment: sampling_architecture_full.md, BE_V1_PLAN.md, api/openapi.yaml, backend_implementation_guide.md

---

## 1. Understanding Check ✅

**Architecture & Responsibilities:**
• **L1 (WaferMapSpec)**: Defines wafer geometry, die pitch, coordinate system, and valid die mask
• **L2 (ProcessContext)**: Defines manufacturing constraints, criticality, min/max sampling points, allowed strategies  
• **L2b (ToolProfile)**: Defines tool execution constraints, coordinate systems, max points per wafer
• **L3 (SamplingStrategy/Output)**: ONLY selects points - applies masks, enforces constraints, deterministic ordering
• **L4 (SamplingScoreReport)**: ONLY scores/evaluates - READ-ONLY, no mutation of L3 outputs whatsoever
• **L5 (ToolRecipe)**: ONLY translates - coordinate conversion, tool payload generation, constraint enforcement

**Critical Invariants:**
• **L4 No-Mutation**: Cannot add/remove/reorder/filter/truncate/modify L3 selected_points in any way
• **Determinism**: Identical inputs must produce identical outputs across all layers
• **Warning vs Error**: Non-blocking issues → HTTP 200 + warnings[]; blocking issues → 4xx/5xx ErrorResponse
• **Contract Freeze**: Zero changes to api/openapi.yaml schemas, fields, endpoints, or response envelopes
• **Layer Separation**: L3 tool-agnostic (except constraints), L5 tool-specific, no cross-layer leakage

**Response Semantics:**
• HTTP 200 + warnings[] for truncation to max, non-critical issues
• HTTP 4xx for disallowed strategy, invalid coordinates, cannot meet min requirements
• Schema-correct responses always, deterministic timestamps or exclusion for testing

---

## 2. Execution Plan (PR-by-PR)

### **PR-0: Test Harness + Golden Path**
**Intent:** Infrastructure for safe iterative development, no intentional behavior change

**Scope:**
- Build comprehensive test infrastructure
- Establish golden fixtures for determinism validation
- Strengthen existing L4 no-mutation test
- Create E2E happy path test

**Files Expected to be Touched:**
- `backend/tests/unit/test_determinism.py` (new)
- `backend/tests/unit/test_l4_no_mutation.py` (strengthen existing)
- `backend/tests/e2e/test_golden_path.py` (new)
- `backend/tests/fixtures/` (new directory + JSON files)
- Minor: timestamp handling in existing routes for deterministic testing

**What Must NOT Change:**
- Any endpoint behavior or business logic
- Response schemas or data structures
- Existing functionality that FE depends on

**Tests to Add:**
- Determinism tests for all major endpoints (same input → same output)
- Enhanced L4 no-mutation guard with deeper validation
- E2E test: preview → score → generate recipe flow
- Golden fixture validation against known good responses

**Acceptance Criteria:**
- Zero intentional behavior changes
- CI green with new test suite
- Golden fixtures established for regression testing
- Deterministic timestamp handling implemented
- L4 no-mutation test strengthened and passing

---

### **PR-1: L3 Real Sampling Engine (CENTER_EDGE only)**
**Intent:** Replace L3 placeholder with deterministic CENTER_EDGE algorithm

**Scope:**
- Implement real CENTER_EDGE sampling strategy
- Apply wafer map valid die mask filtering
- Enforce ProcessContext min/max constraints
- Deterministic candidate generation and ordering

**Files Expected to be Touched:**
- `backend/src/engine/l3/__init__.py` (new)
- `backend/src/engine/l3/center_edge.py` (new)
- `backend/src/engine/l3/base.py` (new - strategy interface)
- `backend/src/server/routes/sampling.py` (preview endpoint only)
- `backend/tests/unit/test_l3_*.py` (new test files)

**What Must NOT Change:**
- OpenAPI contract or response schemas
- L4/L5 behavior or endpoints
- FE compatibility or workflow

**Tests to Add:**
- L3 determinism tests (same input → same output)
- Mask filtering tests (edge exclusion + explicit list)
- Constraint enforcement tests (min/max points)
- Wafer geometry tests (different die pitches/sizes)
- Ring generation and ordering tests

**Acceptance Criteria:**
- Deterministic point selection for identical inputs
- Proper valid_die_mask filtering (EDGE_EXCLUSION, EXPLICIT_LIST)
- Min/max sampling points enforcement
- Center point always included
- FE M4/M5/M6 workflows unchanged
- All existing tests continue to pass

---

### **PR-2: L3 Policy Hardening**
**Intent:** Implement proper warning vs error semantics for L3

**Scope:**
- Implement blocking vs non-blocking error classification
- Add proper HTTP status code handling
- Establish stable warning codes

**Files Expected to be Touched:**
- `backend/src/engine/l3/center_edge.py` (error handling)
- `backend/src/server/routes/sampling.py` (error response logic)
- `backend/src/models/` (error types, warning codes)
- `backend/tests/unit/test_l3_errors.py` (new)

**What Must NOT Change:**
- Basic L3 selection algorithm logic
- Contract schemas or field definitions

**Tests to Add:**
- Error condition tests:
  - Disallowed strategy → 4xx VALIDATION_ERROR
  - Invalid die coordinates → 4xx VALIDATION_ERROR  
  - Cannot meet min_sampling_points → 4xx CONSTRAINT_ERROR
  - Truncation to max_sampling_points → 200 + warnings[]
- Warning code stability tests

**Acceptance Criteria:**
- Correct HTTP status codes for different error types
- Proper ErrorResponse format adherence
- Stable warning codes documented
- Non-blocking issues return 200 + warnings[]
- Blocking issues return appropriate 4xx with ErrorResponse

---

### **PR-3: L4 Real Scoring Engine**
**Intent:** Replace L4 placeholder with real scoring while maintaining strict no-mutation

**Scope:**
- Implement coverage, statistical, risk alignment, and overall scoring
- Ensure read-only evaluation of L3 outputs
- Generate meaningful warnings for scoring issues

**Files Expected to be Touched:**
- `backend/src/engine/l4/__init__.py` (new)
- `backend/src/engine/l4/scorer.py` (new)
- `backend/src/server/routes/sampling.py` (score endpoint only)
- `backend/tests/unit/test_l4_*.py` (new test files)

**What Must NOT Change:**
- L3 outputs (strict read-only requirement)
- Contract schemas or response format
- Point selection or constraint logic

**Tests to Add:**
- L4 scoring algorithm tests
- Enhanced L4 no-mutation tests (deep equality validation)
- Score boundary tests (all scores 0..1)
- Warning generation tests
- Deterministic scoring tests

**Acceptance Criteria:**
- Real coverage/statistical/risk/overall score computation
- All scores bounded between 0.0 and 1.0
- Zero mutation of L3 selected_points (proven by tests)
- Deterministic scoring for identical inputs
- Meaningful warnings for scoring issues
- L4 no-mutation test passes with enhanced validation

---

### **PR-4: L5 Real Recipe Translation Engine**
**Intent:** Replace L5 placeholder with real coordinate conversion and tool payload generation

**Scope:**
- Implement die_x/die_y → coordinate conversion
- Enforce tool constraints deterministically
- Generate proper tool-executable payloads
- Provide detailed translation notes

**Files Expected to be Touched:**
- `backend/src/engine/l5/__init__.py` (new)
- `backend/src/engine/l5/translator.py` (new)
- `backend/src/server/routes/recipes.py` (generate endpoint)
- `backend/tests/unit/test_l5_*.py` (new test files)

**What Must NOT Change:**
- Point selection (L3) or scoring (L4) behavior
- Contract schemas or response format
- Sampling strategy or evaluation logic

**Tests to Add:**
- L5 coordinate conversion tests (die coordinates → mm)
- Tool constraint enforcement tests
- Translation notes validation tests
- Deterministic truncation tests
- Tool payload format tests

**Acceptance Criteria:**
- Proper die_x/die_y → x_mm/y_mm conversion using die_pitch
- Deterministic tool constraint enforcement
- Translation_notes include reason, dropped_count, kept_count
- Tool-executable recipe payload generation
- Deterministic truncation when max_points_per_wafer exceeded
- Warnings for constraint violations

---

## 3. Risk Assessment (Top 5)

### **1. Timestamp Non-Determinism Breaking FE Tests**
**Risk:** `generated_at` timestamps in SamplingTrace could cause FE test failures if they expect deterministic responses

**Impact:** High - Could break existing FE test suites, require FE changes
**Mitigation:** 
- Use fixed timestamps in test environments
- Exclude timestamps from determinism comparisons
- Document timestamp handling approach

### **2. L4 Accidental Mutation During Scoring**
**Risk:** Scoring logic accidentally modifies L3 selected_points (even innocent operations like sorting)

**Impact:** Critical - Violates core architecture invariant
**Mitigation:**
- Deep copy inputs to L4 scoring
- Comprehensive mutation detection tests
- Use immutable data structures where possible
- Enhanced L4 no-mutation test with before/after comparison

### **3. Constraint Interpretation Drift**
**Risk:** L3 and L5 interpreting ToolProfile constraints differently, leading to inconsistent behavior

**Impact:** Medium - Could cause point count mismatches between preview and recipe
**Mitigation:**
- Centralize constraint validation logic
- Explicit integration tests covering constraint edge cases
- Document constraint interpretation clearly
- Cross-layer constraint validation tests

### **4. Error Code Changes Breaking FE Error Handling**
**Risk:** Changing warning codes or error types could break FE error displays even without schema changes

**Impact:** Medium - Could break FE error handling without obvious failures
**Mitigation:**
- Document stable warning/error codes in PR-2
- Test FE integration points with new error handling
- Maintain backward compatibility for warning codes
- Version error/warning code specifications

### **5. Determinism Failures in Production Edge Cases**
**Risk:** Floating point precision, platform differences, or edge case ordering could break determinism

**Impact:** Medium - Could cause inconsistent behavior across environments
**Mitigation:**
- Use integer arithmetic where possible (die coordinates)
- Comprehensive determinism test suite across scenarios
- Fixed ordering for tie-breaking cases
- Platform-independent test validation

---

## 4. Deviations

**No deviations proposed.** 

This execution plan aligns completely with BE_V1_PLAN.md PR-0 through PR-4 structure and intent. All proposed changes stay within the architect-defined boundaries and maintain the non-negotiable rules.

---

## 5. Open Questions

**None.**

All baseline documents provide clear guidance on:
- Layer responsibilities and boundaries
- Contract freeze requirements  
- Warning vs error semantics
- Determinism expectations
- Implementation requirements

The architecture boundaries and constraints are well-defined and sufficient for implementation.

---

## 6. Success Criteria Summary

**BE v1.1 will be complete when:**
- [ ] PR-0: Test infrastructure established, no behavior change, CI green
- [ ] PR-1: L3 CENTER_EDGE real implementation, deterministic, FE unchanged  
- [ ] PR-2: L3 error handling hardened, proper HTTP status codes
- [ ] PR-3: L4 real scoring implementation, no mutation, deterministic
- [ ] PR-4: L5 real translation implementation, coordinate conversion, tool constraints
- [ ] All determinism tests pass consistently
- [ ] No contract drift from api/openapi.yaml
- [ ] FE integration unchanged and working
- [ ] L4 no-mutation invariant maintained throughout

**Definition of Done:** All PRs merged, deterministic E2E passes, zero contract changes, FE workflows preserved.