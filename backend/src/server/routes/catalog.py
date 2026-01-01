from typing import List
from fastapi import APIRouter, HTTPException, Query
from ...models.catalog import (
    TechListResponse,
    WaferMapListResponse,
    ProcessOptionsResponse,
    ProcessContextResponse,
    ToolOptionsResponse,
    ToolProfileResponse,
)
from ...models.enums import Mode

router = APIRouter()

@router.get("/techs", response_model=TechListResponse)
async def list_techs():
    # Static placeholder data for v0
    return TechListResponse(techs=["28nm", "14nm", "7nm"])

@router.get("/wafer-maps", response_model=WaferMapListResponse)
async def list_wafer_maps(tech: str = Query(...)):
    # Placeholder static data aligned with OpenAPI
    return WaferMapListResponse(wafer_maps=[
        {"wafer_map_id": f"{tech}_standard", "tech": tech, "description": f"Standard {tech} wafer map"}
    ])

@router.get("/process-options", response_model=ProcessOptionsResponse)
async def list_process_options(tech: str = Query(...)):
    return ProcessOptionsResponse(process_options=[
        {
            "process_step": "LITHO",
            "intents": ["UNIFORMITY", "THICKNESS"],
            "modes": ["INLINE", "OFFLINE"]
        },
        {
            "process_step": "ETCH",
            "intents": ["CD_CONTROL", "PROFILE"],
            "modes": ["INLINE", "MONITOR"]
        }
    ])

@router.get("/process-context", response_model=ProcessContextResponse)
async def get_process_context(
    tech: str = Query(...),
    step: str = Query(...),
    intent: str = Query(...),
    mode: Mode = Query(...)
):
    # Derive criticality and constraints based on inputs
    criticality = "HIGH" if step == "LITHO" else "MEDIUM"
    min_points = 5 if criticality == "HIGH" else 3
    max_points = 25 if mode == "INLINE" else 50

    return ProcessContextResponse(process_context={
        "process_step": step,
        "measurement_intent": intent,
        "mode": mode,
        "criticality": criticality,
        "min_sampling_points": min_points,
        "max_sampling_points": max_points,
        "allowed_strategy_set": ["CENTER_EDGE"],
        "version": "1.0"
    })

@router.get("/tool-options", response_model=ToolOptionsResponse)
async def list_tool_options(
    tech: str = Query(...),
    step: str = Query(...),
    intent: str = Query(...)
):
    return ToolOptionsResponse(tool_options=[
        {"tool_type": "OPTICAL_METROLOGY", "vendor": "ASML", "model": "YieldStar"},
        {"tool_type": "SEM", "vendor": "AMAT", "model": "eSEM"}
    ])

@router.get("/tool-profile", response_model=ToolProfileResponse)
async def get_tool_profile(
    toolType: str = Query(...),
    vendor: str = Query(None),
    model: str = Query(None)
):
    # Tool capability based on type
    if toolType == "OPTICAL_METROLOGY":
        max_points = 49
        edge_supported = True
    else:  # SEM
        max_points = 25
        edge_supported = False

    return ToolProfileResponse(tool_profile={
        "tool_type": toolType,
        "vendor": vendor or "DEFAULT",
        "model": model,
        "coordinate_system_supported": ["DIE_GRID", "MM"],
        "max_points_per_wafer": max_points,
        "edge_die_supported": edge_supported,
        "ordering_required": False,
        "recipe_format": {"type": "JSON", "version": "1.0"},
        "forbidden_regions": [],
        "version": "1.0"
    })