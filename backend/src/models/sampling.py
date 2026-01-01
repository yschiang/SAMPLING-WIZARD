from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from .base import DiePoint, Warning, WaferMapSpec
from .catalog import ProcessContext, ToolProfile

class SamplingTrace(BaseModel):
    strategy_version: str
    generated_at: str

class SamplingOutput(BaseModel):
    sampling_strategy_id: str
    selected_points: List[DiePoint]
    point_tags: Optional[List[str]] = None
    trace: SamplingTrace

class StrategySelection(BaseModel):
    strategy_id: str
    params: Optional[Dict[str, Any]] = None

class SamplingPreviewRequest(BaseModel):
    wafer_map_spec: WaferMapSpec
    process_context: ProcessContext
    tool_profile: ToolProfile
    strategy: StrategySelection

class SamplingPreviewResponse(BaseModel):
    sampling_output: SamplingOutput
    warnings: List[Warning]

class SamplingScoreRequest(BaseModel):
    wafer_map_spec: WaferMapSpec
    process_context: ProcessContext
    tool_profile: ToolProfile
    sampling_output: SamplingOutput

class SamplingScoreReport(BaseModel):
    coverage_score: float
    statistical_score: float
    risk_alignment_score: float
    overall_score: float
    warnings: List[str]
    version: str

class SamplingScoreResponse(BaseModel):
    score_report: SamplingScoreReport