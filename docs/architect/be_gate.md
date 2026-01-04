# Architect Review Checklist — Planning Output (BE v1)

## How to use
- This checklist is used to review **BE planning output (before coding starts)**.
- Architect produces one of three verdicts:
  - **APPROVED**
  - **APPROVED WITH CHANGES**
  - **BLOCKED**

---

## 0. Submission Completeness

- [ ] Plan lists **PR-0 → PR-4** explicitly
- [ ] Each PR includes:
  - [ ] Scope (what changes)
  - [ ] Must-NOT change
  - [ ] Files expected to be touched
  - [ ] Tests to add/update (unit + e2e)
  - [ ] Acceptance criteria / gates
- [ ] Top 5 risks listed
- [ ] Deviations section present (explicitly “None” if none)
- [ ] Open questions ≤ 5 (if any)

---

## 1. Baseline Compliance (Hard Gates)

### 1.1 Contract Freeze (OpenAPI)
- [ ] Explicit commitment: `api/openapi.yaml` unchanged
- [ ] No new/removed endpoints proposed
- [ ] No renamed fields or envelopes
- [ ] No “change contract first, fix later” language

**BLOCKED if:** Any OpenAPI change is implied or unlabeled.

---

### 1.2 Layer Invariants (L3 / L4 / L5)
- [ ] L3 selects points only
- [ ] L4 scores only and is **read-only**
- [ ] L5 translates only
- [ ] L4 no-mutation explicitly acknowledged:
  - [ ] no reorder
  - [ ] no dedupe
  - [ ] no filter
  - [ ] no truncate
  - [ ] no rewriting point values

**BLOCKED if:** Any plan allows L4 to alter points.

---

### 1.3 Response Semantics (Warnings vs ErrorResponse)
- [ ] Non-blocking → HTTP 200 + `warnings[]`
- [ ] Blocking → ErrorResponse (4xx / 5xx)
- [ ] Policy aligns with `BE_V1_PLAN.md`
- [ ] Any policy change clearly marked as **Deviation Proposal**

**BLOCKED if:** Policy left “to implementation decision”.

---

### 1.4 Determinism
- [ ] Explicit same-input → same-output commitment
- [ ] Determinism strategy defined:
  - [ ] No randomness / seeded ordering
  - [ ] Timestamp handling defined
  - [ ] Fixture-based regression

**BLOCKED if:** Random or time-based behavior is acceptable.

---

## 2. PR Plan Quality Gates

### PR-0 — Test Harness + Golden Path
- [ ] No intentional behavior change
- [ ] Determinism tests included
- [ ] L4 no-mutation test included
- [ ] E2E happy path included
- [ ] Fixtures / golden requests included

---

### PR-1 — L3 Real Sampling (CENTER_EDGE)
- [ ] Scope limited to L3
- [ ] Deterministic ordering defined
- [ ] Ring / distance definition specified
- [ ] `valid_die_mask` applied
- [ ] min/max enforcement defined
- [ ] Tests cover determinism, mask, min/max

---

### PR-2 — L3 Policy Hardening
- [ ] Scope limited to policy consistency
- [ ] Aligns with warning/error table in BE_V1_PLAN.md
- [ ] Tests cover disallowed strategy & invalid input

---

### PR-3 — L4 Real Scoring
- [ ] Scope limited to L4
- [ ] No mutation of L3 outputs
- [ ] Scores bounded 0..1 (if schema expects)
- [ ] Tests: no-mutation + determinism

---

### PR-4 — L5 Recipe Translation
- [ ] Scope limited to L5
- [ ] Tool constraints enforced deterministically
- [ ] `translation_notes` include reason + dropped_count + kept_count
- [ ] Tests: conversion + constraints + e2e

---

## 3. FE Safety (Schema-Stable but UX-Risky Changes)

- [ ] Plan lists FE-impact risks such as:
  - [ ] warning content/volume changes
  - [ ] point ordering changes
  - [ ] catalog option semantics
  - [ ] recipe truncation behavior

**APPROVED WITH CHANGES if:** FE risks not explicitly acknowledged.

---

## 4. Deviation Control

- [ ] Each deviation proposal includes:
  - [ ] What deviates
  - [ ] Why necessary
  - [ ] FE/BE/test impact
  - [ ] Alternative options
  - [ ] Decision owner (architect)

**BLOCKED if:** Deviations are hidden or implicit.

---

## 5. Architect Verdict Template

```
Verdict: APPROVED / APPROVED WITH CHANGES / BLOCKED

✅ Accepted:
- ...

❗ Required changes:
- ...

🔒 Hard gates reminder:
- OpenAPI frozen
- L4 no-mutation
- Warning vs Error policy
- Determinism
```
