"""
Tests for centralized default resolution in all strategies (PR-D3 Phase 1).

Verifies that all strategies use resolve_target_point_count() consistently
and that strategy-specific defaults are applied correctly.
"""

import pytest
import os
from src.engines.l3 import get_strategy
from src.models.sampling import SamplingPreviewRequest, StrategySelection
from src.models.base import WaferMapSpec, ValidDieMask
from src.models.catalog import ProcessContext, ToolProfile
from src.models.strategy_config import StrategyConfig, CommonStrategyConfig, STRATEGY_DEFAULT_TARGET_COUNTS


# Test fixtures
@pytest.fixture(autouse=True)
def set_deterministic_env():
    """Set deterministic timestamps for all tests."""
    os.environ["TEST_DETERMINISTIC_TIMESTAMPS"] = "true"
    yield
    # Don't delete - test_determinism.py sets it at module level


@pytest.fixture
def base_wafer_spec():
    """Standard 300mm wafer."""
    return WaferMapSpec(
        wafer_size_mm=300.0,
        die_pitch_x_mm=10.0,
        die_pitch_y_mm=10.0,
        origin="CENTER",
        notch_orientation_deg=0.0,
        coordinate_system="DIE_GRID",
        valid_die_mask=ValidDieMask(type="EDGE_EXCLUSION", radius_mm=140.0),
        version="1.0"
    )


@pytest.fixture
def base_process_context():
    """Standard process context."""
    return ProcessContext(
        process_step="LITHO",
        measurement_intent="UNIFORMITY",
        mode="INLINE",
        criticality="HIGH",
        min_sampling_points=5,
        max_sampling_points=50,
        allowed_strategy_set=["CENTER_EDGE", "GRID_UNIFORM", "EDGE_ONLY", "ZONE_RING_N"],
        version="1.0"
    )


@pytest.fixture
def base_tool_profile():
    """Standard tool profile."""
    return ToolProfile(
        tool_type="OPTICAL_METROLOGY",
        vendor="ASML",
        coordinate_system_supported=["DIE_GRID"],
        max_points_per_wafer=49,
        edge_die_supported=True,
        ordering_required=False,
        recipe_format={"type": "JSON", "version": "1.0"},
        version="1.0"
    )


# =============================================================================
# CENTER_EDGE Default Resolution Tests
# =============================================================================

def test_center_edge_uses_strategy_default_when_null(base_wafer_spec, base_process_context, base_tool_profile):
    """CENTER_EDGE uses strategy default (20) when target_point_count is null."""
    request = SamplingPreviewRequest(
        wafer_map_spec=base_wafer_spec,
        process_context=base_process_context,
        tool_profile=base_tool_profile,
        strategy=StrategySelection(
            strategy_id="CENTER_EDGE",
            strategy_config=StrategyConfig(
                common=CommonStrategyConfig(target_point_count=None)
            )
        )
    )

    strategy = get_strategy("CENTER_EDGE")
    output = strategy.select_points(request)

    # Strategy default is 20, within constraints [5, 49]
    assert len(output.selected_points) == 20


def test_center_edge_uses_explicit_target_count(base_wafer_spec, base_process_context, base_tool_profile):
    """CENTER_EDGE uses explicit target_point_count when provided."""
    request = SamplingPreviewRequest(
        wafer_map_spec=base_wafer_spec,
        process_context=base_process_context,
        tool_profile=base_tool_profile,
        strategy=StrategySelection(
            strategy_id="CENTER_EDGE",
            strategy_config=StrategyConfig(
                common=CommonStrategyConfig(target_point_count=15)
            )
        )
    )

    strategy = get_strategy("CENTER_EDGE")
    output = strategy.select_points(request)

    assert len(output.selected_points) == 15


def test_center_edge_clamps_to_max_sampling_points(base_wafer_spec, base_tool_profile):
    """CENTER_EDGE clamps to max_sampling_points when target exceeds it."""
    process_context = ProcessContext(
        process_step="LITHO",
        measurement_intent="UNIFORMITY",
        mode="INLINE",
        criticality="HIGH",
        min_sampling_points=5,
        max_sampling_points=10,  # Low max
        allowed_strategy_set=["CENTER_EDGE"],
        version="1.0"
    )

    request = SamplingPreviewRequest(
        wafer_map_spec=base_wafer_spec,
        process_context=process_context,
        tool_profile=base_tool_profile,
        strategy=StrategySelection(
            strategy_id="CENTER_EDGE",
            strategy_config=StrategyConfig(
                common=CommonStrategyConfig(target_point_count=50)  # Exceeds max
            )
        )
    )

    strategy = get_strategy("CENTER_EDGE")
    output = strategy.select_points(request)

    # Clamped to max_sampling_points = 10
    assert len(output.selected_points) == 10


def test_center_edge_clamps_to_min_sampling_points(base_wafer_spec, base_tool_profile):
    """CENTER_EDGE clamps to min_sampling_points when target is below it."""
    process_context = ProcessContext(
        process_step="LITHO",
        measurement_intent="UNIFORMITY",
        mode="INLINE",
        criticality="HIGH",
        min_sampling_points=15,  # High min
        max_sampling_points=50,
        allowed_strategy_set=["CENTER_EDGE"],
        version="1.0"
    )

    request = SamplingPreviewRequest(
        wafer_map_spec=base_wafer_spec,
        process_context=process_context,
        tool_profile=base_tool_profile,
        strategy=StrategySelection(
            strategy_id="CENTER_EDGE",
            strategy_config=StrategyConfig(
                common=CommonStrategyConfig(target_point_count=5)  # Below min
            )
        )
    )

    strategy = get_strategy("CENTER_EDGE")
    output = strategy.select_points(request)

    # Clamped to min_sampling_points = 15
    assert len(output.selected_points) == 15


# =============================================================================
# GRID_UNIFORM Default Resolution Tests
# =============================================================================

def test_grid_uniform_uses_strategy_default_when_null(base_wafer_spec, base_process_context, base_tool_profile):
    """GRID_UNIFORM uses strategy default (30) when target_point_count is null."""
    request = SamplingPreviewRequest(
        wafer_map_spec=base_wafer_spec,
        process_context=base_process_context,
        tool_profile=base_tool_profile,
        strategy=StrategySelection(
            strategy_id="GRID_UNIFORM",
            strategy_config=StrategyConfig(
                common=CommonStrategyConfig(target_point_count=None)
            )
        )
    )

    strategy = get_strategy("GRID_UNIFORM")
    output = strategy.select_points(request)

    # Strategy default is 30, within constraints [5, 49]
    assert len(output.selected_points) == 30


def test_grid_uniform_uses_explicit_target_count(base_wafer_spec, base_process_context, base_tool_profile):
    """GRID_UNIFORM uses explicit target_point_count when provided."""
    request = SamplingPreviewRequest(
        wafer_map_spec=base_wafer_spec,
        process_context=base_process_context,
        tool_profile=base_tool_profile,
        strategy=StrategySelection(
            strategy_id="GRID_UNIFORM",
            strategy_config=StrategyConfig(
                common=CommonStrategyConfig(target_point_count=25)
            )
        )
    )

    strategy = get_strategy("GRID_UNIFORM")
    output = strategy.select_points(request)

    assert len(output.selected_points) == 25


def test_grid_uniform_clamps_to_max_sampling_points(base_wafer_spec, base_tool_profile):
    """GRID_UNIFORM clamps to max_sampling_points when target exceeds it."""
    process_context = ProcessContext(
        process_step="LITHO",
        measurement_intent="UNIFORMITY",
        mode="INLINE",
        criticality="HIGH",
        min_sampling_points=5,
        max_sampling_points=12,  # Low max
        allowed_strategy_set=["GRID_UNIFORM"],
        version="1.0"
    )

    request = SamplingPreviewRequest(
        wafer_map_spec=base_wafer_spec,
        process_context=process_context,
        tool_profile=base_tool_profile,
        strategy=StrategySelection(
            strategy_id="GRID_UNIFORM",
            strategy_config=StrategyConfig(
                common=CommonStrategyConfig(target_point_count=50)  # Exceeds max
            )
        )
    )

    strategy = get_strategy("GRID_UNIFORM")
    output = strategy.select_points(request)

    # Clamped to max_sampling_points = 12
    assert len(output.selected_points) == 12


def test_grid_uniform_clamps_to_min_sampling_points(base_wafer_spec, base_tool_profile):
    """GRID_UNIFORM clamps to min_sampling_points when target is below it."""
    process_context = ProcessContext(
        process_step="LITHO",
        measurement_intent="UNIFORMITY",
        mode="INLINE",
        criticality="HIGH",
        min_sampling_points=20,  # High min
        max_sampling_points=50,
        allowed_strategy_set=["GRID_UNIFORM"],
        version="1.0"
    )

    request = SamplingPreviewRequest(
        wafer_map_spec=base_wafer_spec,
        process_context=process_context,
        tool_profile=base_tool_profile,
        strategy=StrategySelection(
            strategy_id="GRID_UNIFORM",
            strategy_config=StrategyConfig(
                common=CommonStrategyConfig(target_point_count=5)  # Below min
            )
        )
    )

    strategy = get_strategy("GRID_UNIFORM")
    output = strategy.select_points(request)

    # Clamped to min_sampling_points = 20
    assert len(output.selected_points) == 20


# =============================================================================
# EDGE_ONLY Default Resolution Tests
# =============================================================================

def test_edge_only_uses_strategy_default_when_null(base_wafer_spec, base_process_context, base_tool_profile):
    """EDGE_ONLY uses strategy default (15) when target_point_count is null."""
    request = SamplingPreviewRequest(
        wafer_map_spec=base_wafer_spec,
        process_context=base_process_context,
        tool_profile=base_tool_profile,
        strategy=StrategySelection(
            strategy_id="EDGE_ONLY",
            strategy_config=StrategyConfig(
                common=CommonStrategyConfig(target_point_count=None)
            )
        )
    )

    strategy = get_strategy("EDGE_ONLY")
    output = strategy.select_points(request)

    # Strategy default is 15, within constraints [5, 49]
    assert len(output.selected_points) == 15


def test_edge_only_uses_explicit_target_count(base_wafer_spec, base_process_context, base_tool_profile):
    """EDGE_ONLY uses explicit target_point_count when provided."""
    request = SamplingPreviewRequest(
        wafer_map_spec=base_wafer_spec,
        process_context=base_process_context,
        tool_profile=base_tool_profile,
        strategy=StrategySelection(
            strategy_id="EDGE_ONLY",
            strategy_config=StrategyConfig(
                common=CommonStrategyConfig(target_point_count=12)
            )
        )
    )

    strategy = get_strategy("EDGE_ONLY")
    output = strategy.select_points(request)

    assert len(output.selected_points) == 12


def test_edge_only_clamps_to_max_sampling_points(base_wafer_spec, base_tool_profile):
    """EDGE_ONLY clamps to max_sampling_points when target exceeds it."""
    process_context = ProcessContext(
        process_step="LITHO",
        measurement_intent="UNIFORMITY",
        mode="INLINE",
        criticality="HIGH",
        min_sampling_points=5,
        max_sampling_points=8,  # Low max
        allowed_strategy_set=["EDGE_ONLY"],
        version="1.0"
    )

    request = SamplingPreviewRequest(
        wafer_map_spec=base_wafer_spec,
        process_context=process_context,
        tool_profile=base_tool_profile,
        strategy=StrategySelection(
            strategy_id="EDGE_ONLY",
            strategy_config=StrategyConfig(
                common=CommonStrategyConfig(target_point_count=50)  # Exceeds max
            )
        )
    )

    strategy = get_strategy("EDGE_ONLY")
    output = strategy.select_points(request)

    # Clamped to max_sampling_points = 8
    assert len(output.selected_points) == 8


def test_edge_only_clamps_to_min_sampling_points(base_wafer_spec, base_tool_profile):
    """EDGE_ONLY clamps to min_sampling_points when target is below it."""
    process_context = ProcessContext(
        process_step="LITHO",
        measurement_intent="UNIFORMITY",
        mode="INLINE",
        criticality="HIGH",
        min_sampling_points=18,  # High min
        max_sampling_points=50,
        allowed_strategy_set=["EDGE_ONLY"],
        version="1.0"
    )

    request = SamplingPreviewRequest(
        wafer_map_spec=base_wafer_spec,
        process_context=process_context,
        tool_profile=base_tool_profile,
        strategy=StrategySelection(
            strategy_id="EDGE_ONLY",
            strategy_config=StrategyConfig(
                common=CommonStrategyConfig(target_point_count=5)  # Below min
            )
        )
    )

    strategy = get_strategy("EDGE_ONLY")
    output = strategy.select_points(request)

    # Clamped to min_sampling_points = 18
    assert len(output.selected_points) == 18


# =============================================================================
# ZONE_RING_N Default Resolution Tests
# =============================================================================

def test_zone_ring_n_uses_strategy_default_when_null(base_wafer_spec, base_process_context, base_tool_profile):
    """ZONE_RING_N uses strategy default (25) when target_point_count is null."""
    request = SamplingPreviewRequest(
        wafer_map_spec=base_wafer_spec,
        process_context=base_process_context,
        tool_profile=base_tool_profile,
        strategy=StrategySelection(
            strategy_id="ZONE_RING_N",
            strategy_config=StrategyConfig(
                common=CommonStrategyConfig(target_point_count=None)
            )
        )
    )

    strategy = get_strategy("ZONE_RING_N")
    output = strategy.select_points(request)

    # Strategy default is 25, within constraints [5, 49]
    assert len(output.selected_points) == 25


def test_zone_ring_n_uses_explicit_target_count(base_wafer_spec, base_process_context, base_tool_profile):
    """ZONE_RING_N uses explicit target_point_count when provided."""
    request = SamplingPreviewRequest(
        wafer_map_spec=base_wafer_spec,
        process_context=base_process_context,
        tool_profile=base_tool_profile,
        strategy=StrategySelection(
            strategy_id="ZONE_RING_N",
            strategy_config=StrategyConfig(
                common=CommonStrategyConfig(target_point_count=20)
            )
        )
    )

    strategy = get_strategy("ZONE_RING_N")
    output = strategy.select_points(request)

    assert len(output.selected_points) == 20


def test_zone_ring_n_clamps_to_max_sampling_points(base_wafer_spec, base_tool_profile):
    """ZONE_RING_N clamps to max_sampling_points when target exceeds it."""
    process_context = ProcessContext(
        process_step="LITHO",
        measurement_intent="UNIFORMITY",
        mode="INLINE",
        criticality="HIGH",
        min_sampling_points=5,
        max_sampling_points=15,  # Low max
        allowed_strategy_set=["ZONE_RING_N"],
        version="1.0"
    )

    request = SamplingPreviewRequest(
        wafer_map_spec=base_wafer_spec,
        process_context=process_context,
        tool_profile=base_tool_profile,
        strategy=StrategySelection(
            strategy_id="ZONE_RING_N",
            strategy_config=StrategyConfig(
                common=CommonStrategyConfig(target_point_count=50)  # Exceeds max
            )
        )
    )

    strategy = get_strategy("ZONE_RING_N")
    output = strategy.select_points(request)

    # Clamped to max_sampling_points = 15
    assert len(output.selected_points) == 15


def test_zone_ring_n_clamps_to_min_sampling_points(base_wafer_spec, base_tool_profile):
    """ZONE_RING_N clamps to min_sampling_points when target is below it."""
    process_context = ProcessContext(
        process_step="LITHO",
        measurement_intent="UNIFORMITY",
        mode="INLINE",
        criticality="HIGH",
        min_sampling_points=22,  # High min
        max_sampling_points=50,
        allowed_strategy_set=["ZONE_RING_N"],
        version="1.0"
    )

    request = SamplingPreviewRequest(
        wafer_map_spec=base_wafer_spec,
        process_context=process_context,
        tool_profile=base_tool_profile,
        strategy=StrategySelection(
            strategy_id="ZONE_RING_N",
            strategy_config=StrategyConfig(
                common=CommonStrategyConfig(target_point_count=5)  # Below min
            )
        )
    )

    strategy = get_strategy("ZONE_RING_N")
    output = strategy.select_points(request)

    # Clamped to min_sampling_points = 22
    assert len(output.selected_points) == 22
