"""
Path utility functions for filesystem operations.

This module provides common path operations used throughout the application,
particularly for campaign directory management and file organization.
"""

from pathlib import Path
from typing import Optional


def ensure_dir(path: Path, *subdirs) -> Path:
    """
    Ensure directory exists, creating parents if needed.

    Args:
        path: Base directory path
        *subdirs: Optional subdirectory components to join to path

    Returns:
        Full path to the created/verified directory

    Examples:
        >>> ensure_dir(Path('./output'))
        PosixPath('./output')

        >>> ensure_dir(Path('./output'), 'campaign_123', 'product_a')
        PosixPath('./output/campaign_123/product_a')
    """
    full_path = path.joinpath(*subdirs) if subdirs else path
    full_path.mkdir(parents=True, exist_ok=True)
    return full_path


def resolve_campaign_path(base_path: Path, campaign_id: str) -> Optional[Path]:
    """
    Resolve the actual campaign directory, handling nested structures.

    Some campaigns have nested directory structures (e.g., output/campaign_id/campaign_id)
    while others are flat (output/campaign_id). This function handles both cases.

    Args:
        base_path: Base output directory (e.g., ./output)
        campaign_id: Campaign identifier

    Returns:
        Resolved campaign directory path, or None if not found

    Examples:
        >>> # Handles flat structure
        >>> resolve_campaign_path(Path('./output'), 'campaign_123')
        PosixPath('./output/campaign_123')

        >>> # Handles nested structure
        >>> # If ./output/campaign_123/campaign_123 exists, returns nested path
        >>> resolve_campaign_path(Path('./output'), 'campaign_123')
        PosixPath('./output/campaign_123/campaign_123')
    """
    # Check for nested structure first
    nested_path = base_path / campaign_id / campaign_id
    if nested_path.exists() and nested_path.is_dir():
        return nested_path

    # Fall back to flat structure
    flat_path = base_path / campaign_id
    if flat_path.exists():
        return flat_path

    # Campaign not found
    return None


def get_campaign_output_dir(
    campaign_id: str,
    base_dir: str = "./output"
) -> Path:
    """
    Get the output directory path for a campaign.

    Args:
        campaign_id: Campaign identifier
        base_dir: Base output directory (default: "./output")

    Returns:
        Path to campaign output directory

    Examples:
        >>> get_campaign_output_dir('campaign_123')
        PosixPath('./output/campaign_123')

        >>> get_campaign_output_dir('campaign_456', base_dir='./my_output')
        PosixPath('./my_output/campaign_456')
    """
    return Path(base_dir) / campaign_id
