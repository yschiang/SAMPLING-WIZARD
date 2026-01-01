from typing import List, Optional
from pydantic import BaseModel
from .enums import Mode, Criticality, CoordinateSystem
from .base import WaferMapSpec

class TechListResponse(BaseModel):
    techs: List[str]

class WaferMapSummary(BaseModel):
    wafer_map_id: str
    tech: str
    description: str

class WaferMapListResponse(BaseModel):
    wafer_maps: List[WaferMapSummary]

class ProcessOption(BaseModel):
    process_step: str
    intents: List[str]
    modes: List[Mode]

class ProcessOptionsResponse(BaseModel):
    process_options: List[ProcessOption]

class ProcessContext(BaseModel):
    process_step: str
    measurement_intent: str
    mode: Mode
    criticality: Criticality
    min_sampling_points: int
    max_sampling_points: int
    allowed_strategy_set: List[str]
    version: str

class ProcessContextResponse(BaseModel):
    process_context: ProcessContext

class ToolOption(BaseModel):
    tool_type: str
    vendor: str
    model: Optional[str] = None

class ToolOptionsResponse(BaseModel):
    tool_options: List[ToolOption]

class RecipeFormat(BaseModel):
    type: str  # JSON, CSV, TEXT
    version: str

class ToolProfile(BaseModel):
    tool_type: str
    vendor: str
    model: Optional[str] = None
    coordinate_system_supported: List[CoordinateSystem]
    max_points_per_wafer: int
    edge_die_supported: bool
    ordering_required: bool
    recipe_format: RecipeFormat
    forbidden_regions: Optional[List[dict]] = []
    version: str

class ToolProfileResponse(BaseModel):
    tool_profile: ToolProfile