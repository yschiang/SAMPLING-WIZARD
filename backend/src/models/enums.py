from enum import Enum

class Mode(str, Enum):
    INLINE = "INLINE"
    OFFLINE = "OFFLINE"
    MONITOR = "MONITOR"

class Criticality(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class CoordinateSystem(str, Enum):
    DIE_GRID = "DIE_GRID"
    MM = "MM"
    SHOT = "SHOT"

class ErrorType(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONSTRAINT_ERROR = "CONSTRAINT_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"