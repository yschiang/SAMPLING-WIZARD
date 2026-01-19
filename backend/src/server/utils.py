"""
Server utility functions for timestamp handling and other common tasks.
"""
import os
import hashlib
import uuid
from datetime import datetime
from typing import Optional
from ..models.strategy_config import StrategyConfig, validate_and_parse_advanced_config
from ..models.errors import ValidationError, ErrorCode


def get_deterministic_timestamp():
    """
    Get a timestamp that can be deterministic for testing.
    
    In test environments (when TEST_DETERMINISTIC_TIMESTAMPS is set),
    returns a fixed timestamp. Otherwise returns current UTC time.
    
    This enables deterministic testing without affecting production behavior.
    """
    if os.getenv("TEST_DETERMINISTIC_TIMESTAMPS") == "true":
        # Fixed timestamp for deterministic testing
        return "2024-01-01T12:00:00Z"
    else:
        # Real timestamp for production
        return datetime.utcnow().isoformat() + "Z"


def get_deterministic_id(content_hash_input):
    """
    Get an ID that can be deterministic for testing.
    
    In test environments, generates deterministic IDs based on content hash.
    Otherwise generates random UUIDs.
    
    Args:
        content_hash_input: String content to use for deterministic ID generation
    
    Returns:
        String ID that's deterministic in test mode, random in production
    """
    if os.getenv("TEST_DETERMINISTIC_TIMESTAMPS") == "true":
        # Generate deterministic ID based on content hash
        hash_obj = hashlib.md5(content_hash_input.encode())
        # Format as UUID-like string for compatibility
        hash_hex = hash_obj.hexdigest()
        return f"{hash_hex[:8]}-{hash_hex[8:12]}-{hash_hex[12:16]}-{hash_hex[16:20]}-{hash_hex[20:32]}"
    else:
        # Real UUID for production
        return str(uuid.uuid4())


def validate_strategy_config_at_boundary(
    strategy_id: str,
    strategy_config: Optional[StrategyConfig],
    wafer_size_mm: float
) -> None:
    """
    Validate strategy configuration at API boundary (Phase 6).

    Performs two critical validations:
    1. Type-safe advanced config validation (matches strategy)
    2. Business rule validation (edge_exclusion < wafer_radius)

    This ensures validation happens at the correct architectural layer:
    - Route level: Type safety, structural validity, basic business rules
    - Strategy level: Complex business logic, constraint satisfaction

    Args:
        strategy_id: Strategy identifier (e.g., "CENTER_EDGE")
        strategy_config: Optional strategy configuration from request
        wafer_size_mm: Wafer diameter in mm (for radius calculation)

    Raises:
        ValidationError: When validation fails

    Examples:
        >>> # Valid config passes
        >>> validate_strategy_config_at_boundary(
        ...     "CENTER_EDGE",
        ...     StrategyConfig(common=CommonStrategyConfig(edge_exclusion_mm=10.0)),
        ...     300.0  # 300mm wafer
        ... )

        >>> # Invalid advanced config rejected
        >>> validate_strategy_config_at_boundary(
        ...     "CENTER_EDGE",
        ...     StrategyConfig(advanced={"invalid_field": 1}),
        ...     300.0
        ... )
        ValidationError: Unknown field 'invalid_field' in CENTER_EDGE advanced config

        >>> # Edge exclusion >= radius rejected
        >>> validate_strategy_config_at_boundary(
        ...     "CENTER_EDGE",
        ...     StrategyConfig(common=CommonStrategyConfig(edge_exclusion_mm=150.0)),
        ...     300.0  # radius = 150mm
        ... )
        ValidationError: edge_exclusion_mm (150.0mm) must be less than wafer radius (150.0mm)
    """
    if not strategy_config:
        return

    # 1. Type-safe advanced config validation (CRITICAL)
    # This validates that advanced config matches strategy type, has valid fields,
    # correct types, and values within allowed ranges.
    # Currently advanced configs are Dict[str, Any] at Pydantic level - unchecked.
    # This validation ensures type safety at API boundary.
    if strategy_config.advanced:
        # validate_and_parse_advanced_config raises ValidationError if invalid
        validate_and_parse_advanced_config(strategy_id, strategy_config.advanced)

    # 2. Business rule validation (edge exclusion)
    # Validate that edge_exclusion_mm < wafer_radius to prevent excluding entire wafer.
    # This is a fundamental geometric constraint that should be caught early.
    if strategy_config.common:
        edge_exclusion = strategy_config.common.edge_exclusion_mm
        if edge_exclusion > 0:
            wafer_radius = wafer_size_mm / 2.0
            if edge_exclusion >= wafer_radius:
                raise ValidationError(
                    ErrorCode.INVALID_STRATEGY_CONFIG,
                    f"edge_exclusion_mm ({edge_exclusion}mm) must be less than "
                    f"wafer radius ({wafer_radius}mm)"
                )