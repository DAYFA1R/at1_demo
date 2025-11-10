"""
Utility modules for common operations across the application.

This package consolidates frequently-used functions for color manipulation,
string processing, image handling, AI response parsing, and path operations.
"""

from .color_utils import (
    hex_to_rgb,
    rgb_to_hex,
    rgb_to_hsl,
    hex_to_color_name,
    color_distance,
    relative_luminance,
    calculate_contrast_ratio,
)

from .string_utils import (
    to_safe_filename,
    sanitize_filename,
    truncate_text,
)

from .image_utils import (
    ensure_rgb,
    validate_image_dimensions,
    get_aspect_ratio,
)

from .ai_utils import (
    extract_json_from_markdown,
    parse_json_response,
    count_tokens_estimate,
    truncate_to_tokens,
)

from .path_utils import (
    ensure_dir,
    resolve_campaign_path,
    get_campaign_output_dir,
)

__all__ = [
    # Color utilities
    'hex_to_rgb',
    'rgb_to_hex',
    'rgb_to_hsl',
    'hex_to_color_name',
    'color_distance',
    'relative_luminance',
    'calculate_contrast_ratio',
    # String utilities
    'to_safe_filename',
    'sanitize_filename',
    'truncate_text',
    # Image utilities
    'ensure_rgb',
    'validate_image_dimensions',
    'get_aspect_ratio',
    # AI utilities
    'extract_json_from_markdown',
    'parse_json_response',
    'count_tokens_estimate',
    'truncate_to_tokens',
    # Path utilities
    'ensure_dir',
    'resolve_campaign_path',
    'get_campaign_output_dir',
]
