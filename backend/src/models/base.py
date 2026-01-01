from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Warning(BaseModel):
    code: str
    message: str

class ErrorDetail(BaseModel):
    code: str
    message: str
    type: str  # ErrorType enum value
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail

class DiePoint(BaseModel):
    die_x: int
    die_y: int

class ValidDieMask(BaseModel):
    type: str  # EDGE_EXCLUSION or EXPLICIT_LIST
    radius_mm: Optional[float] = None
    valid_die_list: Optional[List[DiePoint]] = None

class WaferMapSpec(BaseModel):
    wafer_size_mm: float
    die_pitch_x_mm: float
    die_pitch_y_mm: float
    origin: str  # CENTER
    notch_orientation_deg: float
    coordinate_system: str  # CoordinateSystem enum value
    valid_die_mask: ValidDieMask
    version: str