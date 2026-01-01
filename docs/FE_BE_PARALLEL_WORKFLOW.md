# FE & BE Parallel Development Workflow
## Real-world Coworking Guidance for Sampling Wizard

### **Real-world Practice: FE & BE Parallel vs Staged?**

In mature teams: **parallel development** — but only after the architect creates a **"stable seam."**

That seam is exactly what we've built: **OpenAPI + skeleton + invariants.**

---

## **Common Real-world Models**

### **Model 1 — Contract-first Parallel (Our Approach)**

**Best when**: UI depends on backend but algorithms/data can evolve.

**Process**:
- ✅ **Architect defines**: docs + OpenAPI + invariants  
- ✅ **BE ships**: walking skeleton (schema-correct stubs)
- ✅ **FE ships**: real UI against stable endpoints
- 🔄 **BE iterates**: replace internals behind the contract

**Why it works**: FE builds against a stable envelope; BE improves behavior without breaking FE.

**Pattern used**: High-scale orgs for platform-like work.

---

### **Model 2 — BE-first then FE (Staged)**

**Best when**: UI is thin, backend complexity dominates, or integration cost is low.

**Process**:
- BE implements real core first
- FE starts later with fewer "placeholder surprises"

**Downside**: FE idle time, late UX feedback, more churn when UI needs different shapes.

---

### **Model 3 — FE Mock Server / BFF First**

**Best when**: FE needs freedom + fast iteration; backend is slow.

**Process**:
- FE builds with a mock server or BFF layer  
- BE later integrates

**Downside**: Drift risk unless OpenAPI contract is strictly shared.

---

## **Ideal Cowork Workflow (Post-Skeleton)**

### **1. Architect "Freezes the Seam" ✅**

**We've established**:
- ✅ OpenAPI is authoritative (`api/openapi.yaml`)
- ✅ L3/L4/L5 boundaries enforced  
- ✅ Warnings vs errors rules defined
- ✅ Determinism expectations set
- ✅ Backend skeleton serves valid responses

### **2. FE Builds End-to-End on the Seam**

**FE treats backend as**:
- **Stable schema** (OpenAPI-compliant responses)
- **Evolving semantics** (logic gets better over time)

**FE focus**:
- State transitions (wizard steps 1-6)
- UX (wafer map visualization, score displays)
- Error/warning display
- User flow validation

**FE development approach**:
```bash
# FE develops against live backend
npm run dev  # Frontend dev server
# Backend running: http://localhost:8080
```

### **3. BE Replaces Placeholders Behind the Seam**

**BE focus**:
- Correctness improvements inside L3/L4/L5
- Catalog realism (static JSON → real data)
- Validation logic
- Tool constraints
- Test coverage

**BE development approach**:
```bash
# BE improves logic without breaking contract
uvicorn backend.src.server.main:app --reload --port 8080
# FE continues working with evolving backend
```

### **4. Sync Points (Coordination Without Blocking)**

**Weekly or per-milestone sync**, not constant back-and-forth:

**FE milestone acceptance**: "UI works with current responses"
**BE milestone acceptance**: "No contract drift + invariants preserved"

**Missing data/fields** = logged as **v1 proposal**, not patched ad-hoc

**Sync meeting agenda**:
- FE: UI milestone demo + any missing data needs
- BE: Logic milestone demo + contract compliance
- Architect: Review proposals, sequence v1 decisions

### **5. Tight Coordination Required: Examples/Fixtures**

**Shared golden path**: `api/examples/*.json`

**FE usage**:
- Mock/fallback data for development
- Snapshot tests for component validation

**BE usage**:
- E2E test fixtures
- Response validation examples

**Example structure**:
```
api/examples/
├── catalog_techs_response.json
├── sampling_preview_request.json  
├── sampling_preview_response.json
├── score_report_response.json
└── tool_recipe_response.json
```

---

## **Role Responsibilities During Parallel Work**

### **Frontend (Gemini) Team**
- ✅ Implement wizard steps 1-6 per `docs/frontend_component_spec.md`
- ✅ Use live backend endpoints (not mocks)
- ✅ Handle warnings without auto-correction
- ✅ Follow invalidation rules (upstream changes clear downstream)
- ❌ Never modify sampling points (read-only L3 outputs)

### **Backend (Claude) Team**  
- ✅ Implement real L3/L4/L5 logic per 14-task roadmap
- ✅ Maintain OpenAPI compliance (no schema drift)
- ✅ Preserve architectural invariants (L4 no-mutation)
- ✅ Replace placeholders with deterministic logic
- ❌ No OpenAPI changes without explicit arch approval

### **Architect**
**No longer building features.** Focus on:
- ✅ Enforce contract stability (no drift)
- ✅ Enforce invariants (especially L4 no-mutation)  
- ✅ Sequence work to avoid overbuilding
- ✅ Resolve proposals into v1/v2 decisions
- ✅ Review PRs for boundary violations

---

## **Coordination Examples**

### **✅ Good Parallel Work**
```
FE: feat(fe): wizard step 3 tool selection with capability display
BE: feat(be): implement L3 CENTER_EDGE deterministic algorithm  
```
**Result**: FE gets better tool selection UX, BE provides real logic, both work independently

### **❌ Bad Coordination**
```
FE: "Backend doesn't return edge_support field"
BE: "Just added edge_support, updating OpenAPI"
```
**Problem**: Contract drift without arch review

**Better approach**:
```
FE: "Log v1 proposal: need edge_support in tool_profile"
Arch: "Add to v1 backlog, FE use mock for now"  
BE: "Continue L3 implementation per roadmap"
```

---

## **Success Metrics**

### **FE Success**
- ✅ Wizard completes steps 1-6 end-to-end
- ✅ UI handles all warning scenarios gracefully
- ✅ No API integration surprises

### **BE Success**  
- ✅ Real logic passes all tests
- ✅ OpenAPI compliance maintained
- ✅ Architectural invariants preserved

### **Overall Success**
- ✅ FE can switch from any placeholder to real backend seamlessly
- ✅ Backend improvements don't break FE
- ✅ Team velocity sustained (no blocking dependencies)

---

## **Common Pitfalls & Solutions**

| Pitfall | Solution |
|---------|----------|
| FE blocked by missing data | Use examples/*.json + log v1 proposal |
| BE changes break FE | Enforce OpenAPI compliance testing |
| Constant FE ↔ BE coordination | Weekly sync + shared examples |
| Feature creep during parallel work | Architect sequences + v1 proposals |
| Contract drift | Git hooks + arch review required |

---

## **Next Steps**

1. **FE Team**: Start wizard implementation against live backend
2. **BE Team**: Begin 14-task roadmap (L3 → L4 → L5)  
3. **Weekly Sync**: Milestone demos + v1 proposal review
4. **Shared Examples**: Create `api/examples/` for golden path
5. **Contract Guards**: Set up OpenAPI compliance CI

**The stable seam enables both teams to move fast without breaking each other.**