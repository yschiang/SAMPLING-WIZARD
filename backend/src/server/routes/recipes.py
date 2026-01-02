import uuid
from fastapi import APIRouter
from ...models.recipes import GenerateRecipeRequest, GenerateRecipeResponse
from ..utils import get_deterministic_id

router = APIRouter()

@router.post("/generate", response_model=GenerateRecipeResponse)
async def generate_recipe(request: GenerateRecipeRequest):
    # L5 translation: die coordinates → tool coordinates (placeholder)
    wafer_spec = request.wafer_map_spec
    tool_profile = request.tool_profile
    points = request.sampling_output.selected_points

    # Convert die_x/die_y to mm coordinates
    recipe_points = []
    translation_notes = []

    for point in points:
        x_mm = point.die_x * wafer_spec.die_pitch_x_mm
        y_mm = point.die_y * wafer_spec.die_pitch_y_mm

        # Check if within wafer boundary (simplified)
        distance = (x_mm**2 + y_mm**2)**0.5
        if distance <= wafer_spec.wafer_size_mm / 2:
            recipe_points.append({"x_mm": x_mm, "y_mm": y_mm})
        else:
            translation_notes.append(f"Point ({point.die_x},{point.die_y}) outside wafer boundary")

    # Apply tool constraints
    max_points = tool_profile.max_points_per_wafer
    if len(recipe_points) > max_points:
        truncated_count = len(recipe_points) - max_points
        recipe_points = recipe_points[:max_points]
        translation_notes.append(f"Truncated {truncated_count} points due to tool limit")

    # Generate tool-specific payload
    recipe_payload = {
        "tool_type": tool_profile.tool_type,
        "coordinate_system": "MM",
        "measurement_points": recipe_points,
        "ordering": "SEQUENTIAL" if tool_profile.ordering_required else "NONE"
    }

    # Generate deterministic recipe ID based on content for testing
    content_for_id = f"{tool_profile.tool_type}_{len(recipe_points)}_{len(translation_notes)}"
    recipe_id = get_deterministic_id(content_for_id)
    
    return GenerateRecipeResponse(
        tool_recipe={
            "recipe_id": recipe_id,
            "tool_type": tool_profile.tool_type,
            "recipe_payload": recipe_payload,
            "translation_notes": translation_notes,
            "recipe_format_version": tool_profile.recipe_format.version
        },
        warnings=[]
    )