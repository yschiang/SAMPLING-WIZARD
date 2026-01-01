# Git Message Format Guide
## Sampling Wizard Project Standards

### **Format Template**
```
<type>(<role>): <short milestone-level summary>

[Optional body with Context/Scope/Invariants/Notes]
```

---

## **Allowed Roles**

| Role | Description | Responsibility |
|------|-------------|----------------|
| `arch` | Architecture, contracts, baselines, invariants | Baseline docs, OpenAPI, L1-L5 boundaries |
| `be` | Backend implementation (Claude BE agent) | L3/L4/L5 logic, catalog, tests |
| `fe` | Frontend implementation (Gemini) | Wizard UI, components, user flow |
| `audit` | Audit / verification only | Contract compliance, invariant validation |

---

## **Allowed Types**

| Type | Description | Use Case |
|------|-------------|----------|
| `feat` | New capability / milestone | L3 strategy, wizard step, new endpoint |
| `fix` | Bug fix (no scope expansion) | Broken logic, validation errors |
| `refactor` | Internal restructure (no behavior change) | Code organization, performance |
| `docs` | Documentation only | README updates, guides, specs |
| `test` | Tests only (incl. invariant guards) | Unit tests, e2e tests, guards |
| `chore` | Tooling, config, CI, repo hygiene | Dependencies, build, linting |

---

## **Message Examples**

### **Architecture Changes**
```
feat(arch): add L4 scoring invariant validation

Context:
- Enforce L4 never mutates L3 outputs (non-negotiable guard)

Scope: 
- Add deep equality validation in test suite
- Document invariant in backend guide

Invariants:
- L4 read-only guarantee preserved
- OpenAPI schema unchanged
```

### **Backend Implementation**
```
feat(be): implement L3 CENTER_EDGE deterministic strategy  

Context:
- Replace placeholder with real geometric selection algorithm

Scope:
- Ring-based candidate generation (center, inner, outer)
- Valid die mask filtering (edge exclusion)
- Deterministic truncation for tool constraints

Invariants:
- Same inputs produce same outputs (testing requirement)
- No mutation of input parameters
- L2 min/max constraints respected

Notes:
- No OpenAPI changes
- FE can continue using existing preview endpoint
```

### **Frontend Implementation**
```
feat(fe): M4 wizard step navigation and state management

Context: 
- Implement stepper component per frontend spec

Scope:
- Step 1-6 navigation with validation gates
- State invalidation rules (upstream changes clear downstream)
- Progress persistence in browser session

Invariants:
- UI never modifies sampling points (read-only L3 outputs)
- No auto-fixing based on warnings
- Backend contract usage unchanged
```

### **Bug Fixes**
```
fix(be): L5 coordinate conversion edge case handling

Context:
- Tool recipe generation failed for points near wafer edge

Scope:
- Add boundary validation before coordinate conversion
- Return translation notes for dropped points

Invariants:
- L5 translation-only responsibility preserved
- No changes to L3 point selection logic
```

### **Documentation**
```
docs(arch): add PR review checklist for invariants

Context:
- Ensure architectural boundaries are maintained across PRs

Scope:
- L4 no-mutation checklist
- OpenAPI compatibility verification
- Contract drift prevention
```

---

## **Commit Body Format (Recommended)**

For `be` and `arch` roles, use structured body:

```
<type>(<role>): <summary>

Context:
- Why this change exists (architectural intent)

Scope: 
- What is included / excluded
- Specific components affected

Invariants:
- Which architectural guards are preserved
- Which boundaries are maintained

Notes:
- No OpenAPI changes
- No FE contract impact
- Other relevant information
```

---

## **Commit Rules**

### **1. One Commit = One Milestone**
- ✅ `feat(be): implement L3 CENTER_EDGE strategy` 
- ❌ `feat(be): implement L3 and L4 and fix catalog bugs`

### **2. Role Separation**
- ✅ Separate commits for FE and BE changes
- ❌ Mixed `feat(fe+be): add preview with backend logic`

### **3. Contract Stability**
- ✅ Document when OpenAPI is unchanged
- ❌ Silent OpenAPI modifications

### **4. Missing Features**
- ✅ Log v1 proposals for missing capabilities  
- ❌ Patch missing requirements silently

---

## **Validation Examples**

### **✅ Good Messages**
```
feat(be): L4 ring-based coverage scoring
fix(fe): wizard step validation state sync  
chore(arch): add backend test CI workflow
test(be): L4 deterministic output validation
docs(fe): update component integration guide
refactor(be): extract coordinate conversion utilities
```

### **❌ Bad Messages**  
```
feat: add stuff                    # Missing role
feat(be): fix things and add L3    # Mixed scope  
update(fe): change UI              # Invalid type
feat(dev): implement features      # Invalid role
wip: work in progress             # Not milestone-complete
```

---

## **PR Requirements**

- **One PR = One commit** (squash merge)
- **Commit message = PR title** 
- **PR description** includes full commit body format
- **Architecture changes** require `arch` role review
- **Contract changes** require explicit version bump discussion

---

## **Role-Specific Guidelines**

### **Architecture (`arch`)**
- Focus on cross-team impact
- Document invariant preservation  
- OpenAPI changes require explicit discussion
- Baseline document updates

### **Backend (`be`)**  
- L3/L4/L5 implementation milestones
- Catalog and validation logic
- Test coverage for architectural guards
- Performance and determinism

### **Frontend (`fe`)**
- Wizard step implementations
- Component milestones per spec
- User flow validation
- Backend API integration

### **Audit (`audit`)**
- Contract compliance verification
- Invariant validation
- Cross-team integration testing
- Architecture boundary enforcement