"""
Image processing utility functions.

This module provides common PIL/Pillow image operations used throughout
the application, ensuring consistency in image handling.
"""

from PIL import Image
from typing import Tuple


def ensure_rgb(image: Image.Image) -> Image.Image:
    """
    Ensure image is in RGB mode.

    Many image operations require RGB mode. This function converts
    RGBA, grayscale, or other modes to RGB for consistent processing.

    Args:
        image: PIL Image object in any mode

    Returns:
        PIL Image object in RGB mode

    Examples:
        >>> from PIL import Image
        >>> img = Image.new('RGBA', (100, 100))
        >>> rgb_img = ensure_rgb(img)
        >>> rgb_img.mode
        'RGB'

    Note:
        - RGBA images: Alpha channel is composited against white background
        - Grayscale: Converted to RGB with identical R, G, B values
        - Other modes: Converted using PIL's default conversion
    """
    if image.mode != 'RGB':
        return image.convert('RGB')
    return image


def validate_image_dimensions(
    image: Image.Image,
    min_width: int = 100,
    min_height: int = 100,
    max_width: int = 10000,
    max_height: int = 10000
) -> bool:
    """
    Validate image dimensions are within acceptable ranges.

    Args:
        image: PIL Image object to validate
        min_width: Minimum acceptable width in pixels
        min_height: Minimum acceptable height in pixels
        max_width: Maximum acceptable width in pixels
        max_height: Maximum acceptable height in pixels

    Returns:
        True if dimensions are valid, False otherwise

    Examples:
        >>> from PIL import Image
        >>> img = Image.new('RGB', (1920, 1080))
        >>> validate_image_dimensions(img)
        True
        >>> tiny_img = Image.new('RGB', (50, 50))
        >>> validate_image_dimensions(tiny_img, min_width=100, min_height=100)
        False
    """
    width, height = image.size

    if width < min_width or height < min_height:
        return False

    if width > max_width or height > max_height:
        return False

    return True


def get_aspect_ratio(image: Image.Image) -> Tuple[int, int]:
    """
    Calculate the aspect ratio of an image as simplified integers.

    Args:
        image: PIL Image object

    Returns:
        Tuple of (width_ratio, height_ratio) in simplified form

    Examples:
        >>> from PIL import Image
        >>> img = Image.new('RGB', (1920, 1080))
        >>> get_aspect_ratio(img)
        (16, 9)
        >>> square = Image.new('RGB', (1000, 1000))
        >>> get_aspect_ratio(square)
        (1, 1)
    """
    from math import gcd

    width, height = image.size
    divisor = gcd(width, height)

    return (width // divisor, height // divisor)
