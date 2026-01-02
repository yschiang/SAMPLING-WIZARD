# BE v1.1 Split Plan
Walking Skeleton → Real Deterministic Logic

Status:
- FE: M6 complete (Preview → Score → Generate Recipe end-to-end UI)
- BE: v0 walking skeleton (schema-correct placeholder behavior)

Objective:
Replace placeholder internals with real, deterministic implementations
without any OpenAPI / contract drift.

This document is authoritative for BE v1 execution.

---

## 0. Non-Negotiable Rules

### Contract & API
- Do not change api/openapi.yaml
- Do not add/remove endpoints
- Do not rename fields or response envelopes
- All responses must remain schema-correct

### Layer Invariants (L3 / L4 / L5)
- L3: selects points only
- L4: scores only and MUST NOT mutate L3 outputs
  - no reorder
  - no dedupe
  - no filter
  - no truncate
  - no rewriting point values
- L5: translates to tool recipe only

### Response Semantics
- Non-blocking issues → HTTP 200 + warnings[]
- Blocking issues → ErrorResponse (4xx / 5xx)
- Deterministic outputs for identical inputs

---

## 1. Working Agreement

### PR Policy
- One PR = one concern
- Each PR must declare:
  1) Layer(s) impacted
  2) Invariants asserted
  3) Tests added / updated
  4) Explicit behavior changes (if any)

### Seam Freeze
- FE: bugfix only
- BE: replace internals behind frozen seam
- Any missing data / ambiguity → GitHub issue tagged proposal:v1
- No ad-hoc patches without architect approval

---

## 2. Roadmap Overview (Split PR Plan)

### PR-0 — Test Harness + Golden Path
(No intentional behavior change)

Goal:
Make the repo safe for iterative algorithm changes.

Deliverables:
- Determinism tests
- Strengthened L4 no-mutation test
- E2E happy path: preview → score → generate
- Required golden fixtures under backend/tests/fixtures/

Notes on determinism:
- generated_at timestamps must be fixed, excluded, or deterministic

Acceptance Criteria:
- No intentional behavior change
- Only minimal fixes allowed to enable testing
- CI green

---

### PR-1 — L3 Real Sampling Engine (CENTER_EDGE)

CENTER_EDGE v1 Minimal Spec:
- Always include center die (0,0)
- Deterministic ring definition (document chosen metric)
- Deterministic candidate ordering
- Apply valid_die_mask
- Enforce min/max sampling points

Acceptance Criteria:
- Deterministic preview output
- FE unchanged

---

### PR-2 — L3 Policy Hardening

Warning vs Error Policy:
- Disallowed strategy → 4xx
- Invalid die coordinate → 4xx
- Cannot meet min after mask → 4xx
- Truncation to max → 200 + warnings[]

---

### PR-3 — L4 Real Scoring Engine

Rules:
- Compute coverage/statistical/risk/overall scores
- Scores bounded 0..1
- Emit warnings only
- No mutation of L3 outputs

---

### PR-4 — L5 Real Recipe Translation Engine

Rules:
- Deterministic coordinate conversion
- Enforce tool constraints deterministically
- translation_notes must include reason, dropped_count, kept_count

---

### PR-5 — Catalog Realism (Optional)

- Move to static JSON catalog
- Response shape must remain stable

---

## 3. Architect Gate Points

Architect approval required for:
- Warning vs error semantics change
- Behavior impacting FE flow
- Any contract change proposal

---

## 4. Definition of Done

BE v1 complete when:
- PR-0 → PR-4 merged
- Deterministic E2E passes
- No contract drift
- FE unchanged
