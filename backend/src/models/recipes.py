from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from .base import Warning, WaferMapSpec
from .catalog import ToolProfile
from .sampling import SamplingOutput, SamplingScoreReport

class GenerateRecipeRequest(BaseModel):
    wafer_map_spec: WaferMapSpec
    tool_profile: ToolProfile
    sampling_output: SamplingOutput
    score_report: Optional[SamplingScoreReport] = None

class ToolRecipe(BaseModel):
    recipe_id: str
    tool_type: str
    recipe_payload: Dict[str, Any]
    translation_notes: List[str]
    recipe_format_version: str

class GenerateRecipeResponse(BaseModel):
    tool_recipe: ToolRecipe
    warnings: List[Warning]