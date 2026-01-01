# Sampling Wizard Frontend (v0 Placeholder)

This directory is reserved for the Gemini frontend implementation.

## Required Reading (Gemini Team)

1. `docs/user_flow.md` - Wizard step specification
2. `docs/frontend_component_spec.md` - Component implementation guide  
3. `api/openapi.yaml` - API contract

## Backend Integration

The backend skeleton is available at:
- **Development server**: http://localhost:8080
- **OpenAPI docs**: http://localhost:8080/docs
- **Health check**: http://localhost:8080/health

### Key API Endpoints
```
GET  /v1/catalog/techs
GET  /v1/catalog/wafer-maps?tech=...
GET  /v1/catalog/process-context?...
GET  /v1/catalog/tool-profile?...
POST /v1/sampling/preview
POST /v1/sampling/score  
POST /v1/recipes/generate
```

## Architecture Compliance

✅ **UI is read-only for L3 outputs** - Never modify sampling points
✅ **Warnings never auto-fix** - Display warnings, require user confirmation
✅ **Contract-first** - Use OpenAPI schema for all API interactions
✅ **Step invalidation** - Upstream changes clear downstream results

## Implementation Status

🟡 **Placeholder** - Awaiting Gemini implementation per component spec

## V0 Definition of Done

- [ ] Wizard completes Step 1-6 end-to-end using backend API
- [ ] Step 5 always shows preview + scoring before Step 6
- [ ] Invalidation rules behave exactly as defined
- [ ] Warnings never auto-change backend outputs
- [ ] Recipe is read-only and exportable