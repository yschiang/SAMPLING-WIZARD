# Backend Test Infrastructure

This directory contains comprehensive test infrastructure for the Sampling Wizard backend.

## Test Structure

### Unit Tests (`unit/`)
- **`test_determinism.py`**: Ensures all endpoints produce identical outputs for identical inputs
- **`test_l4_no_mutation.py`**: Critical architecture guard - verifies L4 never mutates L3 outputs

### E2E Tests (`e2e/`)  
- **`test_golden_path.py`**: Complete end-to-end workflow testing (Preview → Score → Recipe)

### Test Fixtures (`fixtures/`)
- **`golden_requests.json`**: Standard request payloads for deterministic testing

## Running Tests

### Environment Setup
Set `TEST_DETERMINISTIC_TIMESTAMPS=true` for deterministic testing:

```bash
export TEST_DETERMINISTIC_TIMESTAMPS=true
```

### Individual Test Files
```bash
# Determinism tests
TEST_DETERMINISTIC_TIMESTAMPS=true python tests/unit/test_determinism.py

# L4 no-mutation tests  
TEST_DETERMINISTIC_TIMESTAMPS=true python tests/unit/test_l4_no_mutation.py

# E2E golden path tests
TEST_DETERMINISTIC_TIMESTAMPS=true python tests/e2e/test_golden_path.py
```

### All Tests
```bash
# Run all tests (when pytest is available)
TEST_DETERMINISTIC_TIMESTAMPS=true pytest tests/

# Or run individually for now
TEST_DETERMINISTIC_TIMESTAMPS=true python tests/unit/test_determinism.py
TEST_DETERMINISTIC_TIMESTAMPS=true python tests/unit/test_l4_no_mutation.py  
TEST_DETERMINISTIC_TIMESTAMPS=true python tests/e2e/test_golden_path.py
```

## Test Features

### Deterministic Testing
- Fixed timestamps in test mode via `get_deterministic_timestamp()`
- Fixed IDs in test mode via `get_deterministic_id()` 
- Excludes volatile fields from comparison (e.g., `generated_at` timestamps)

### Architecture Guards
- **L4 No-Mutation**: Enhanced tests with deep validation of point preservation
- **Determinism**: Multi-call validation ensures identical inputs → identical outputs
- **Pipeline Consistency**: End-to-end flow maintains data integrity

### Coverage Areas
- ✅ All major API endpoints (`/preview`, `/score`, `/generate`)
- ✅ Error scenarios and edge cases
- ✅ Constraint enforcement validation
- ✅ Cross-endpoint data consistency
- ✅ Architecture invariant preservation

## Test Status

**PR-0 Status: ✅ COMPLETE**
- [x] Determinism tests implemented and passing
- [x] L4 no-mutation test strengthened and passing  
- [x] E2E golden path test implemented and passing
- [x] Golden fixtures established
- [x] Deterministic timestamp/ID handling implemented
- [x] No behavior changes - only infrastructure additions
- [x] All existing functionality preserved

This test infrastructure provides a safe foundation for iterative algorithm development in PR-1 through PR-4.