import uuid
from fastapi import APIRouter
from ...models.recipes import GenerateRecipeRequest, GenerateRecipeResponse
from ...models.base import Warning
from ..utils import get_deterministic_id
from ...engines.l5 import RecipeTranslator

router = APIRouter()

@router.post("/generate", response_model=GenerateRecipeResponse)
async def generate_recipe(request: GenerateRecipeRequest):
    # Use real L5 recipe translator (read-only coordinate conversion)
    translator = RecipeTranslator()
    
    # Execute L5 translation with comprehensive constraint handling
    translation_result = translator.translate_recipe(request)
    
    # Convert warnings to proper Warning objects
    warnings = []
    for warning_code in translation_result["warnings"]:
        warnings.append(Warning(
            code=warning_code,
            message=f"Recipe translation warning: {warning_code}"
        ))
    
    # Return schema-correct response (no contract changes)
    return GenerateRecipeResponse(
        tool_recipe=translation_result["tool_recipe"],
        warnings=warnings
    )