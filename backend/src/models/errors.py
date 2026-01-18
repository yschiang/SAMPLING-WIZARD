"""
Error models and exception classes for proper HTTP error handling.
"""

from typing import Optional
from pydantic import BaseModel
from enum import Enum


class ErrorType(str, Enum):
    """Standard error type categories."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    CONSTRAINT_ERROR = "CONSTRAINT_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorCode(str, Enum):
    """Standard error codes for L3 sampling issues."""
    # Validation errors (4xx)
    INVALID_STRATEGY = "INVALID_STRATEGY"
    INVALID_STRATEGY_CONFIG = "INVALID_STRATEGY_CONFIG"  # v1.3: strategy config validation
    DISALLOWED_STRATEGY = "DISALLOWED_STRATEGY"
    INVALID_DIE_COORDINATES = "INVALID_DIE_COORDINATES"
    INVALID_WAFER_SPEC = "INVALID_WAFER_SPEC"
    INVALID_CONSTRAINTS = "INVALID_CONSTRAINTS"
    
    # Constraint errors (4xx)
    INSUFFICIENT_VALID_DIES = "INSUFFICIENT_VALID_DIES"
    CANNOT_MEET_MIN_POINTS = "CANNOT_MEET_MIN_POINTS"
    
    # Internal errors (5xx)
    STRATEGY_EXECUTION_FAILED = "STRATEGY_EXECUTION_FAILED"


class WarningCode(str, Enum):
    """Standard warning codes for L3 sampling issues (non-blocking)."""
    POINTS_TRUNCATED_TO_MAX = "POINTS_TRUNCATED_TO_MAX"
    EDGE_DIES_FILTERED = "EDGE_DIES_FILTERED"
    CONSTRAINT_ADJUSTED = "CONSTRAINT_ADJUSTED"


class ErrorDetail(BaseModel):
    """Error detail structure matching OpenAPI schema."""
    code: str
    message: str
    type: str


class ErrorResponse(BaseModel):
    """Error response structure matching OpenAPI schema."""
    error: ErrorDetail


class SamplingError(Exception):
    """Base exception for L3 sampling errors."""
    
    def __init__(self, code: ErrorCode, message: str, error_type: ErrorType, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
    
    def to_error_response(self) -> ErrorResponse:
        """Convert to API error response format."""
        return ErrorResponse(
            error=ErrorDetail(
                code=self.code.value,
                message=self.message,
                type=self.error_type.value
            )
        )


class ValidationError(SamplingError):
    """Validation error (400 status code)."""
    
    def __init__(self, code: ErrorCode, message: str):
        super().__init__(code, message, ErrorType.VALIDATION_ERROR, 400)


class ConstraintError(SamplingError):
    """Constraint error (400 status code)."""
    
    def __init__(self, code: ErrorCode, message: str):
        super().__init__(code, message, ErrorType.CONSTRAINT_ERROR, 400)


class InternalError(SamplingError):
    """Internal error (500 status code)."""
    
    def __init__(self, code: ErrorCode, message: str):
        super().__init__(code, message, ErrorType.INTERNAL_ERROR, 500)