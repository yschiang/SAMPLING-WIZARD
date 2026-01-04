# FE+BE Integration Test Validation

**Type**: Architecture Gate Requirement  
**Priority**: Critical  
**Assignee**: Frontend Team  
**Reviewer**: Architect Agent  

## Background

With BE v1.1 approved and merged, we need to validate that the Frontend M6 implementation correctly integrates with the real backend engines (L3/L4/L5) instead of mock data.

## Required Integration Test Scope

### 1. **End-to-End Wizard Flow**
- [ ] Step 1-6 complete workflow with real BE endpoints
- [ ] L3 Preview (real CENTER_EDGE sampling)
- [ ] L4 Scoring (real coverage/statistical/risk scoring)  
- [ ] L5 Recipe Generation (real coordinate translation)

### 2. **Error Handling Integration**
- [ ] L3 constraint errors (min/max points)
- [ ] L3 validation errors (disallowed strategy)
- [ ] HTTP 4xx error responses properly handled
- [ ] Warning display for HTTP 200 + warnings[]

### 3. **Contract Compliance Verification**
- [ ] TypeScript types match actual BE response schemas
- [ ] Warning objects display correctly (`{code, message}` format)
- [ ] All OpenAPI fields properly consumed

## Integration Test Requirements

Frontend team must demonstrate:

1. **Live Integration Test Run** against running BE v1.1
   - Start backend: `cd backend && uvicorn src.server.main:app --port 8080`
   - Run FE integration tests or manual workflow
   - Capture outputs showing real data (not mocks)

2. **Error Scenario Testing**
   - Trigger L3 constraint violations
   - Verify proper error display in UI
   - Show HTTP status code handling

3. **Data Flow Verification**
   - Real sampling points from L3 CENTER_EDGE
   - Real scores from L4 (coverage/statistical/risk)
   - Real recipe payloads from L5 translation

## Evidence Required

**Frontend team must attach:**

```bash
# Test output showing real BE integration
npm test -- integration
# OR manual workflow screenshots/logs

# Console logs showing real API responses
# Browser devtools network tab screenshots
# Any error scenarios properly handled
```

**Must demonstrate:**
- No mock data fallbacks during integration
- Proper error handling for 4xx responses  
- Warning display matches OpenAPI contract
- Complete L3→L4→L5 data flow working

## Acceptance Criteria

- [ ] E2E wizard flow completed with real BE v1.1
- [ ] Error scenarios properly handled
- [ ] Contract compliance verified (no type mismatches)
- [ ] Evidence attached showing live integration
- [ ] No mock data used during integration test

## Architecture Gate

This issue serves as the **FE+BE Integration Gate**. 

**Architect Decision Required**: APPROVED / APPROVED WITH CHANGES / BLOCKED

Integration must be verified before FE M7 can proceed.

---

**Created by**: Architect Agent  
**Baseline**: sampling_architecture_full.md, api/openapi.yaml  
**Dependencies**: BE v1.1 merged (#1)