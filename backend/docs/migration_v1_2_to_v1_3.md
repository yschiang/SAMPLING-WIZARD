# Migration Guide: v1.2 → v1.3

## Overview

Version 1.3 introduces a major restructuring of strategy configuration with breaking changes to the API. This guide helps you migrate from v1.2 to v1.3.

**Key Changes:**
- `params` → `strategy_config` (breaking change)
- New common parameters for all strategies
- Type-safe validation at API boundary
- Strategy-specific defaults

---

## Breaking Changes

### 1. `params` → `strategy_config`

The flat `params` dict has been replaced with structured `strategy_config` containing `common` and `advanced` sections.

**v1.2 (Deprecated - NO LONGER SUPPORTED):**
```json
{
  "strategy": {
    "strategy_id": "CENTER_EDGE",
    "params": {
      "center_weight": 0.3,
      "ring_count": 4
    }
  }
}
```

**v1.3 (Current):**
```json
{
  "strategy": {
    "strategy_id": "CENTER_EDGE",
    "strategy_config": {
      "common": {
        "edge_exclusion_mm": 30.0,
        "rotation_seed": 45,
        "target_point_count": 15
      },
      "advanced": {
        "center_weight": 0.3,
        "ring_count": 4,
        "radial_spacing": "UNIFORM"
      }
    }
  }
}
```

### 2. Common Parameters

All strategies now support standard parameters in the `common` section:

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `edge_exclusion_mm` | float | [0.0, ∞) | 0.0 | Exclude points within N mm of wafer edge |
| `rotation_seed` | int | [0, 359] | null | Deterministic rotation offset in degrees |
| `target_point_count` | int | [1, ∞) | null | Override strategy default point count |
| `deterministic_seed` | int | [0, ∞) | null | RNG seed for stochastic operations |

**All common parameters are optional.** If not provided, sensible defaults are used.

### 3. Type-Safe Validation

Advanced configs are now validated at the API boundary before strategy execution:

**Error Scenarios:**
- **Unknown fields** → `INVALID_STRATEGY_CONFIG` with clear message
- **Out-of-range values** → `INVALID_STRATEGY_CONFIG` with range info
- **Wrong strategy config** → `INVALID_STRATEGY_CONFIG` indicating mismatch
- **Invalid types** → `INVALID_STRATEGY_CONFIG` with type error

**Example Error Response:**
```json
{
  "error": {
    "code": "INVALID_STRATEGY_CONFIG",
    "message": "center_weight must be between 0.0 and 1.0",
    "type": "VALIDATION_ERROR"
  }
}
```

---

## Migration Checklist

- [ ] Replace `params` with `strategy_config` in all requests
- [ ] Move strategy-specific fields to `strategy_config.advanced`
- [ ] Add common parameters if needed (e.g., `edge_exclusion_mm`, `rotation_seed`)
- [ ] Test API requests against v1.3 endpoint
- [ ] Update client-side types/schemas for `strategy_config`
- [ ] Handle new error code: `INVALID_STRATEGY_CONFIG`
- [ ] Remove v1.2 `params` usage from codebase
- [ ] Update documentation and examples

---

## Migration Examples by Strategy

### CENTER_EDGE

**v1.2:**
```json
{
  "strategy": {
    "strategy_id": "CENTER_EDGE",
    "params": {
      "center_weight": 0.3,
      "ring_count": 4
    }
  }
}
```

**v1.3:**
```json
{
  "strategy": {
    "strategy_id": "CENTER_EDGE",
    "strategy_config": {
      "common": {
        "edge_exclusion_mm": 20.0,
        "rotation_seed": 45,
        "target_point_count": 18
      },
      "advanced": {
        "center_weight": 0.3,
        "ring_count": 4,
        "radial_spacing": "UNIFORM"
      }
    }
  }
}
```

**Notes:**
- `common.target_point_count` overrides default (20 points)
- `advanced.center_weight` controls center vs edge allocation
- `advanced.ring_count` must be 2-5
- `advanced.radial_spacing` options: `UNIFORM`, `EXPONENTIAL`

---

### GRID_UNIFORM

**v1.2:**
```json
{
  "strategy": {
    "strategy_id": "GRID_UNIFORM",
    "params": {
      "grid_pitch_mm": 15.0
    }
  }
}
```

**v1.3:**
```json
{
  "strategy": {
    "strategy_id": "GRID_UNIFORM",
    "strategy_config": {
      "common": {
        "rotation_seed": 90,
        "target_point_count": 25
      },
      "advanced": {
        "grid_pitch_mm": 15.0,
        "grid_alignment": "CENTER",
        "jitter_ratio": 0.0
      }
    }
  }
}
```

**Notes:**
- `common.rotation_seed` applies geometric rotation
- `advanced.grid_pitch_mm` overrides auto-derived spacing
- `advanced.grid_alignment` options: `CENTER`, `CORNER`
- `advanced.jitter_ratio` (0.0-0.3) for sub-die randomization (requires `common.deterministic_seed`)

---

### EDGE_ONLY

**v1.2:**
```json
{
  "strategy": {
    "strategy_id": "EDGE_ONLY",
    "params": {
      "edge_band_width_mm": 15.0
    }
  }
}
```

**v1.3:**
```json
{
  "strategy": {
    "strategy_id": "EDGE_ONLY",
    "strategy_config": {
      "common": {
        "edge_exclusion_mm": 5.0,
        "target_point_count": 12
      },
      "advanced": {
        "edge_band_width_mm": 15.0,
        "angular_spacing_deg": 30.0,
        "prioritize_corners": true
      }
    }
  }
}
```

**Notes:**
- `common.edge_exclusion_mm` shrinks sampling region inward
- `advanced.edge_band_width_mm` (5.0-50.0mm) controls edge zone width
- `advanced.angular_spacing_deg` (15.0-90.0) sets target spacing
- `advanced.prioritize_corners` prioritizes corner regions

---

### ZONE_RING_N

**v1.2:**
```json
{
  "strategy": {
    "strategy_id": "ZONE_RING_N",
    "params": {
      "num_rings": 4,
      "allocation_mode": "AREA_PROPORTIONAL"
    }
  }
}
```

**v1.3:**
```json
{
  "strategy": {
    "strategy_id": "ZONE_RING_N",
    "strategy_config": {
      "common": {
        "rotation_seed": 45,
        "target_point_count": 20
      },
      "advanced": {
        "num_rings": 4,
        "allocation_mode": "AREA_PROPORTIONAL"
      }
    }
  }
}
```

**Notes:**
- `advanced.num_rings` (2-10) sets number of concentric rings
- `advanced.allocation_mode` options: `AREA_PROPORTIONAL`, `UNIFORM`, `EDGE_HEAVY`

---

## Strategy Defaults

When `target_point_count` is null, each strategy uses its own default:

| Strategy | Default Points |
|----------|----------------|
| CENTER_EDGE | 20 |
| GRID_UNIFORM | 30 |
| EDGE_ONLY | 15 |
| ZONE_RING_N | 25 |

These defaults are automatically clamped to `[min_sampling_points, min(max_sampling_points, tool_max)]`.

---

## Backward Compatibility

**IMPORTANT:** v1.2 `params` format is **NOT SUPPORTED** in v1.3.

- Sending `params` will result in it being ignored (since it's not in the schema)
- All clients **MUST** migrate to `strategy_config`
- No automatic translation from v1.2 to v1.3

---

## Testing Your Migration

### 1. Validate Against API

Use the `/v1/sampling/preview` endpoint to test requests:

```bash
curl -X POST http://localhost:8000/v1/sampling/preview \
  -H "Content-Type: application/json" \
  -d @your-request.json
```

**Success (HTTP 200):**
```json
{
  "sampling_output": {
    "sampling_strategy_id": "CENTER_EDGE",
    "selected_points": [...],
    "trace": {...}
  },
  "warnings": []
}
```

**Validation Error (HTTP 400):**
```json
{
  "detail": {
    "error": {
      "code": "INVALID_STRATEGY_CONFIG",
      "message": "edge_exclusion_mm (160.0mm) must be less than wafer radius (150.0mm)",
      "type": "VALIDATION_ERROR"
    }
  }
}
```

### 2. Check OpenAPI Schema

View the interactive API docs at: `http://localhost:8000/docs`

- Browse strategy config schemas
- See examples for each strategy
- Test requests directly in browser

### 3. Verify Error Handling

Test invalid configs to ensure proper error handling:

**Out-of-range value:**
```json
{
  "strategy_config": {
    "advanced": {
      "center_weight": 1.5
    }
  }
}
```

**Expected:** HTTP 400 with `INVALID_STRATEGY_CONFIG` error

---

## Common Migration Issues

### Issue 1: `params` Ignored

**Problem:** Request with `params` succeeds but uses defaults

**Cause:** `params` not in v1.3 schema, silently ignored

**Fix:** Replace `params` with `strategy_config`

---

### Issue 2: Missing Strategy Defaults

**Problem:** Point count different than expected

**Cause:** `target_point_count` null → using strategy default

**Fix:** Set explicit `target_point_count` in `common` section

---

### Issue 3: Validation at Wrong Layer

**Problem:** Errors from strategy, not route

**Cause:** Advanced config not validated at boundary

**Fix:** Already fixed in v1.3 - validation happens at route level

---

## Get Help

**Issues or Questions:**
- GitHub Issues: https://github.com/yschiang/SAMPLING-WIZARD/issues
- Check OpenAPI docs: http://localhost:8000/docs
- Review examples in `tests/fixtures/golden_requests.json`

**Migration Support:**
- See `tests/unit/test_default_resolution.py` for usage examples
- See `tests/integration/test_v1_3_integration.py` for end-to-end examples
- Check strategy catalog: `src/data/catalog/strategies.json`

---

## Summary

v1.3 provides:
- ✅ Structured configuration with `common` + `advanced`
- ✅ Type-safe validation at API boundary
- ✅ Consistent common parameters across all strategies
- ✅ Clear, actionable error messages
- ✅ Strategy-specific defaults

**Action Required:** All v1.2 clients must migrate to v1.3 `strategy_config` format.
