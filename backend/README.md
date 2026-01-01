# Sampling Wizard Backend (v0)

FastAPI backend implementing the L1-L5 architecture for sampling point selection and recipe generation.

## Quick Start

```bash
# 1. Setup environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run development server
uvicorn src.server.main:app --reload --host 0.0.0.0 --port 8080

# 4. Access API
# - Health check: http://localhost:8080/health
# - OpenAPI docs: http://localhost:8080/docs
# - API spec: http://localhost:8080/openapi.json
```

## Architecture

- **L3**: Sampling point selection (deterministic CENTER_EDGE strategy)
- **L4**: Scoring and evaluation (no mutation of L3 outputs)
- **L5**: Recipe translation (die coordinates → tool formats)

## API Endpoints

### Catalog (Steps 1-3)
- `GET /v1/catalog/techs`
- `GET /v1/catalog/wafer-maps?tech=...`
- `GET /v1/catalog/process-context?...`
- `GET /v1/catalog/tool-profile?...`

### Execution
- `POST /v1/sampling/preview` → L3 SamplingOutput + warnings
- `POST /v1/sampling/score` → L4 SamplingScoreReport  
- `POST /v1/recipes/generate` → L5 ToolRecipe + warnings

## Testing

```bash
# Run test script
python test_server.py

# Manual endpoint testing
curl http://localhost:8080/health
curl http://localhost:8080/v1/catalog/techs
```

## Status

✅ **v0 Prototype Complete**
- All OpenAPI endpoints implemented
- Placeholder L3/L4/L5 logic with deterministic outputs
- Ready for BE agent implementation of full logic

## Next Steps (for BE Agent)

See `docs/backend_implementation_guide.md` for the 14-task implementation roadmap.