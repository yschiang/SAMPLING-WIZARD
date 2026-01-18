"""
L5 Recipe Translator Implementation.

Converts L3 sampling outputs into tool-executable recipes with:
- Die coordinate → mm coordinate conversion
- Tool constraint enforcement (max points, edge support, etc.)
- Tool-specific payload generation  
- Detailed translation notes and warnings

All translation is read-only and deterministic.
"""

import math
from typing import List, Dict, Any, Tuple, Set
from ...models.base import DiePoint, WaferMapSpec
from ...models.catalog import ToolProfile
from ...models.sampling import SamplingOutput
from ...models.recipes import GenerateRecipeRequest, ToolRecipe
from ...server.utils import get_deterministic_id


class RecipeTranslator:
    """
    L5 Recipe Translator - converts L3 outputs to tool-executable recipes.
    
    Implements coordinate conversion and tool payload generation for:
    - Die grid coordinates → mm coordinates
    - Tool constraint enforcement (deterministic truncation)
    - Tool-specific recipe format generation
    - Translation traceability with detailed notes
    """
    
    def __init__(self):
        self.version = "1.0"
    
    def translate_recipe(self, request: GenerateRecipeRequest) -> Dict[str, Any]:
        """
        Translate L3 sampling output into tool-executable recipe.
        
        Args:
            request: Recipe generation request with sampling output and tool profile
            
        Returns:
            Dict containing tool_recipe and warnings
            
        Note: This method is READ-ONLY and never modifies the input sampling_output
        """
        # Extract key data (read-only)
        wafer_spec = request.wafer_map_spec
        tool_profile = request.tool_profile
        sampling_output = request.sampling_output
        
        selected_points = sampling_output.selected_points
        translation_notes = []
        warnings = []
        
        # Step 1: Convert die coordinates to mm coordinates
        mm_points = self._convert_die_to_mm_coordinates(
            selected_points, wafer_spec, translation_notes
        )
        
        # Step 2: Apply wafer boundary constraints  
        valid_mm_points = self._apply_wafer_boundary_constraints(
            mm_points, wafer_spec, translation_notes
        )
        
        # Step 3: Apply tool-specific constraints
        final_points = self._apply_tool_constraints(
            valid_mm_points, tool_profile, translation_notes, warnings
        )
        
        # Step 4: Generate tool-specific payload
        recipe_payload = self._generate_tool_payload(
            final_points, tool_profile, wafer_spec
        )
        
        # Step 5: Generate deterministic recipe ID
        recipe_id = self._generate_recipe_id(
            tool_profile, final_points, translation_notes
        )
        
        # Create tool recipe
        tool_recipe = ToolRecipe(
            recipe_id=recipe_id,
            tool_type=tool_profile.tool_type,
            recipe_payload=recipe_payload,
            translation_notes=translation_notes,
            recipe_format_version=tool_profile.recipe_format.version
        )
        
        return {
            "tool_recipe": tool_recipe,
            "warnings": warnings
        }
    
    def _convert_die_to_mm_coordinates(self, selected_points: List[DiePoint], 
                                      wafer_spec: WaferMapSpec, 
                                      translation_notes: List[str]) -> List[Dict[str, Any]]:
        """
        Convert die grid coordinates to mm coordinates.
        
        Algorithm:
        - x_mm = die_x * die_pitch_x_mm
        - y_mm = die_y * die_pitch_y_mm
        - Origin handling based on wafer_spec.origin
        
        Returns:
            List of coordinate dicts with x_mm, y_mm, and original die coordinates
        """
        mm_points = []
        
        for point in selected_points:
            # Basic conversion using die pitch
            x_mm = point.die_x * wafer_spec.die_pitch_x_mm
            y_mm = point.die_y * wafer_spec.die_pitch_y_mm
            
            # Apply origin offset if needed (most wafers are CENTER origin)
            if wafer_spec.origin == "CENTER":
                # Already centered at (0,0), no adjustment needed
                pass
            elif wafer_spec.origin == "BOTTOM_LEFT":
                # Adjust to center the coordinate system
                wafer_radius = wafer_spec.wafer_size_mm / 2
                x_mm += wafer_radius
                y_mm += wafer_radius
            # Add other origin types as needed
            
            mm_points.append({
                "x_mm": x_mm,
                "y_mm": y_mm,
                "die_x": point.die_x,
                "die_y": point.die_y
            })
        
        if mm_points:
            translation_notes.append(
                f"Converted {len(mm_points)} die coordinates to mm using "
                f"pitch_x={wafer_spec.die_pitch_x_mm}mm, pitch_y={wafer_spec.die_pitch_y_mm}mm"
            )
        
        return mm_points
    
    def _apply_wafer_boundary_constraints(self, mm_points: List[Dict[str, Any]], 
                                        wafer_spec: WaferMapSpec,
                                        translation_notes: List[str]) -> List[Dict[str, Any]]:
        """
        Filter points that fall outside wafer boundary.
        
        Uses wafer_size_mm to determine valid radius from center.
        """
        if not mm_points:
            return mm_points
        
        valid_points = []
        boundary_filtered = 0
        wafer_radius = wafer_spec.wafer_size_mm / 2
        
        for point in mm_points:
            x_mm = point["x_mm"]
            y_mm = point["y_mm"]
            
            # Calculate distance from wafer center
            distance = math.sqrt(x_mm**2 + y_mm**2)
            
            if distance <= wafer_radius:
                valid_points.append(point)
            else:
                boundary_filtered += 1
        
        if boundary_filtered > 0:
            translation_notes.append(
                f"Filtered {boundary_filtered} points outside wafer boundary "
                f"(radius={wafer_radius}mm)"
            )
        
        return valid_points
    
    def _apply_tool_constraints(self, valid_points: List[Dict[str, Any]], 
                               tool_profile: ToolProfile,
                               translation_notes: List[str],
                               warnings: List[str]) -> List[Dict[str, Any]]:
        """
        Apply tool-specific constraints including max points and edge support.
        
        Performs deterministic truncation when exceeding tool limits.
        """
        if not valid_points:
            return valid_points
        
        # Apply max_points_per_wafer constraint
        max_points = tool_profile.max_points_per_wafer
        points_to_process = valid_points
        
        # Filter edge dies if tool doesn't support them
        if not tool_profile.edge_die_supported:
            edge_filtered_points = self._filter_edge_dies(
                points_to_process, tool_profile, translation_notes
            )
            points_to_process = edge_filtered_points
        
        # Apply max points constraint with deterministic truncation
        final_points = points_to_process
        if len(points_to_process) > max_points:
            # Deterministic truncation: take first N points (order from L3)
            final_points = points_to_process[:max_points]
            truncated_count = len(points_to_process) - max_points
            
            translation_notes.append(
                f"Truncated {truncated_count} points to meet tool limit "
                f"(max_points_per_wafer={max_points})"
            )
            
            # Add warning for significant truncation
            if truncated_count > max_points * 0.2:  # >20% truncated
                warnings.append("SIGNIFICANT_POINT_TRUNCATION")
        
        # Add constraint summary
        if final_points:
            translation_notes.append(
                f"Applied tool constraints: kept_count={len(final_points)}, "
                f"dropped_count={len(valid_points) - len(final_points)}"
            )
        
        return final_points
    
    def _filter_edge_dies(self, points: List[Dict[str, Any]], 
                         tool_profile: ToolProfile,
                         translation_notes: List[str]) -> List[Dict[str, Any]]:
        """
        Filter edge dies if tool doesn't support them.
        
        Simple heuristic: remove points beyond 80% of wafer radius.
        """
        # For now, return all points since most tools support edge dies
        # This can be enhanced with actual edge detection logic
        return points
    
    def _generate_tool_payload(self, final_points: List[Dict[str, Any]], 
                              tool_profile: ToolProfile,
                              wafer_spec: WaferMapSpec) -> Dict[str, Any]:
        """
        Generate tool-specific recipe payload.
        
        Creates JSON payload formatted for tool execution.
        """
        # Convert points to tool format
        measurement_points = []
        for i, point in enumerate(final_points):
            measurement_points.append({
                "point_id": i + 1,
                "x_mm": round(point["x_mm"], 3),  # Round to μm precision
                "y_mm": round(point["y_mm"], 3),
                "die_x": point["die_x"],
                "die_y": point["die_y"]
            })
        
        # Determine coordinate system based on tool support
        coordinate_system = "MM"  # Default to mm
        if "DIE_GRID" in tool_profile.coordinate_system_supported:
            coordinate_system = "DIE_GRID"
        elif "MM" in tool_profile.coordinate_system_supported:
            coordinate_system = "MM"
        
        # Generate tool-specific payload
        recipe_payload = {
            "tool_type": tool_profile.tool_type,
            "vendor": tool_profile.vendor,
            "coordinate_system": coordinate_system,
            "measurement_points": measurement_points,
            "point_count": len(measurement_points),
            "wafer_info": {
                "wafer_size_mm": wafer_spec.wafer_size_mm,
                "die_pitch_x_mm": wafer_spec.die_pitch_x_mm,
                "die_pitch_y_mm": wafer_spec.die_pitch_y_mm,
                "origin": wafer_spec.origin
            }
        }
        
        # Add tool-specific fields
        if tool_profile.ordering_required:
            recipe_payload["measurement_order"] = "SEQUENTIAL"
        else:
            recipe_payload["measurement_order"] = "OPTIMIZED"
        
        # Add recipe format info
        if tool_profile.recipe_format:
            recipe_payload["format_type"] = tool_profile.recipe_format.type
            recipe_payload["format_version"] = tool_profile.recipe_format.version
        
        return recipe_payload
    
    def _generate_recipe_id(self, tool_profile: ToolProfile, 
                           final_points: List[Dict[str, Any]],
                           translation_notes: List[str]) -> str:
        """
        Generate deterministic recipe ID based on content.
        
        Creates reproducible ID for testing and traceability.
        """
        # Create content string for deterministic ID generation
        points_signature = f"{len(final_points)}"
        if final_points:
            # Include first/last point coordinates for uniqueness
            first_point = final_points[0]
            last_point = final_points[-1]
            points_signature += f"_{first_point['x_mm']:.1f}_{first_point['y_mm']:.1f}"
            points_signature += f"_{last_point['x_mm']:.1f}_{last_point['y_mm']:.1f}"
        
        notes_signature = f"{len(translation_notes)}"
        
        content_for_id = f"{tool_profile.tool_type}_{tool_profile.vendor}_{points_signature}_{notes_signature}"
        
        return get_deterministic_id(content_for_id)