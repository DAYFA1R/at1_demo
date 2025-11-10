"""
Color utility functions for hex/RGB/HSL conversions and color analysis.

This module consolidates all color-related operations used throughout the application,
providing a single source of truth for color conversions, distance calculations,
contrast checking, and color naming.
"""

from typing import Tuple


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hex color code to RGB tuple.

    Args:
        hex_color: Hex color code (with or without '#' prefix)
                  Examples: "#FF0000", "00FF00"

    Returns:
        Tuple of (red, green, blue) values (0-255)

    Raises:
        ValueError: If hex_color is not a valid 6-character hex code

    Examples:
        >>> hex_to_rgb("#FF0000")
        (255, 0, 0)
        >>> hex_to_rgb("00FF00")
        (0, 255, 0)
    """
    hex_color = hex_color.lstrip('#')

    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}. Must be 6 characters.")

    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)
    except ValueError as e:
        raise ValueError(f"Invalid hex color: {hex_color}") from e


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """
    Convert RGB tuple to hex color code.

    Args:
        rgb: Tuple of (red, green, blue) values (0-255)

    Returns:
        Hex color code with '#' prefix

    Examples:
        >>> rgb_to_hex((255, 0, 0))
        '#ff0000'
        >>> rgb_to_hex((0, 255, 0))
        '#00ff00'
    """
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """
    Convert RGB to HSL color space.

    HSL (Hue, Saturation, Lightness) is often more intuitive for color
    manipulation than RGB, especially for determining color names and
    categorization.

    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)

    Returns:
        Tuple of (hue, saturation, lightness) where:
        - hue: 0-360 degrees
        - saturation: 0-100 percent
        - lightness: 0-100 percent

    Examples:
        >>> rgb_to_hsl(255, 0, 0)  # Pure red
        (0.0, 100.0, 50.0)
        >>> rgb_to_hsl(128, 128, 128)  # Gray
        (0.0, 0.0, 50.2)
    """
    # Normalize RGB to 0-1 range
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    diff = max_val - min_val

    # Lightness
    l = (max_val + min_val) / 2.0

    if diff == 0:
        h = s = 0  # achromatic (gray)
    else:
        # Saturation
        s = diff / (2.0 - max_val - min_val) if l > 0.5 else diff / (max_val + min_val)

        # Hue
        if max_val == r:
            h = ((g - b) / diff + (6 if g < b else 0)) / 6.0
        elif max_val == g:
            h = ((b - r) / diff + 2) / 6.0
        else:
            h = ((r - g) / diff + 4) / 6.0

    return h * 360, s * 100, l * 100


def hex_to_color_name(hex_color: str) -> str:
    """
    Convert hex color to descriptive color name for better human/AI understanding.

    Uses HSL color space for robust color categorization. This is particularly
    useful for generating DALL-E prompts that understand color descriptions.

    Args:
        hex_color: Hex color code (e.g., "#FF0000")

    Returns:
        Descriptive color name (e.g., "vibrant red", "light blue", "dark gray")

    Examples:
        >>> hex_to_color_name("#FF0000")
        'vibrant red'
        >>> hex_to_color_name("#808080")
        'gray'
        >>> hex_to_color_name("#FFD700")
        'golden'
    """
    # Remove # if present
    hex_color = hex_color.lstrip('#')

    try:
        # Convert to RGB then HSL
        r, g, b = hex_to_rgb(hex_color)
        h, s, l = rgb_to_hsl(r, g, b)

        # Handle achromatic colors (low saturation)
        if s < 10:
            if l < 10:
                return "black"
            elif l < 25:
                return "very dark gray"
            elif l < 45:
                return "dark gray"
            elif l < 65:
                return "gray"
            elif l < 85:
                return "light gray"
            else:
                return "white"

        # Determine base color from hue
        # Hue wheel: Red=0, Orange=30, Yellow=60, Green=120, Cyan=180, Blue=240, Magenta=300
        if h < 15 or h >= 345:
            base_color = "red"
        elif h < 45:
            base_color = "orange"
        elif h < 75:
            base_color = "yellow"
        elif h < 150:
            base_color = "green"
        elif h < 200:
            base_color = "cyan"
        elif h < 245:
            base_color = "blue"
        elif h < 290:
            base_color = "purple"
        elif h < 320:
            base_color = "magenta"
        else:
            base_color = "pink"

        # Add modifiers based on saturation and lightness
        modifiers = []

        # Lightness modifiers
        if l < 20:
            modifiers.append("very dark")
        elif l < 35:
            modifiers.append("dark")
        elif l > 80:
            modifiers.append("very light")
        elif l > 65:
            modifiers.append("light")

        # Saturation modifiers (for mid-range lightness)
        if 30 < l < 70 and s > 80:
            modifiers.append("vibrant")

        # Special cases for better DALL-E understanding
        if base_color == "pink" and l > 60 and s > 70:
            base_color = "hot pink"
            modifiers = []
        elif base_color == "yellow":
            if l > 70:
                base_color = "golden"
                modifiers = []
            elif 40 < l < 70:
                base_color = "golden yellow"
                modifiers = [m for m in modifiers if "dark" not in m]
        elif base_color == "orange":
            if 35 < h < 65 and l > 60:
                base_color = "golden"
                modifiers = []
            elif s > 60 and l < 50:
                base_color = "burnt orange"
                modifiers = []
        elif base_color == "cyan" and h < 180:
            base_color = "teal"

        # Combine modifiers with base color
        if modifiers:
            return " ".join(modifiers) + " " + base_color
        return base_color

    except (ValueError, IndexError):
        # Return original hex if conversion fails
        return hex_color


def color_distance(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
    """
    Calculate perceptual distance between two RGB colors.

    Uses simple Euclidean distance in RGB space. For more accurate perceptual
    distance, consider using Delta E in LAB color space (requires additional library).

    Args:
        color1: First RGB color tuple (0-255, 0-255, 0-255)
        color2: Second RGB color tuple (0-255, 0-255, 0-255)

    Returns:
        Distance value (0-441, where 0 means identical colors)

    Examples:
        >>> color_distance((255, 0, 0), (255, 0, 0))  # Same color
        0.0
        >>> color_distance((0, 0, 0), (255, 255, 255))  # Max distance
        441.67...
    """
    return sum((a - b) ** 2 for a, b in zip(color1, color2)) ** 0.5


def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """
    Calculate relative luminance per WCAG 2.0 guidelines.

    This is used for determining contrast ratios for accessibility compliance.
    The calculation applies gamma correction to match human perception.

    Args:
        rgb: RGB color tuple (0-255, 0-255, 0-255)

    Returns:
        Relative luminance value (0.0-1.0)
        where 0.0 is darkest black and 1.0 is lightest white

    References:
        WCAG 2.0: https://www.w3.org/TR/WCAG20/#relativeluminancedef

    Examples:
        >>> relative_luminance((0, 0, 0))  # Black
        0.0
        >>> relative_luminance((255, 255, 255))  # White
        1.0
    """
    # Normalize to 0-1 range
    r, g, b = [c/255.0 for c in rgb]

    # Apply gamma correction per WCAG spec
    r = r/12.92 if r <= 0.03928 else ((r + 0.055)/1.055) ** 2.4
    g = g/12.92 if g <= 0.03928 else ((g + 0.055)/1.055) ** 2.4
    b = b/12.92 if b <= 0.03928 else ((b + 0.055)/1.055) ** 2.4

    # WCAG luminance formula (weighted for human perception)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def calculate_contrast_ratio(color1: Tuple[int, int, int],
                             color2: Tuple[int, int, int]) -> float:
    """
    Calculate WCAG contrast ratio between two colors.

    Used to ensure text readability against backgrounds. WCAG guidelines:
    - AA (minimum): 4.5:1 for normal text, 3:1 for large text
    - AAA (enhanced): 7:1 for normal text, 4.5:1 for large text

    Args:
        color1: First RGB color (typically foreground/text)
        color2: Second RGB color (typically background)

    Returns:
        Contrast ratio (1.0-21.0, where 21.0 is maximum contrast)

    Examples:
        >>> calculate_contrast_ratio((0, 0, 0), (255, 255, 255))  # Black on white
        21.0
        >>> calculate_contrast_ratio((128, 128, 128), (128, 128, 128))  # Same color
        1.0

    References:
        WCAG 2.0: https://www.w3.org/TR/WCAG20/#contrast-ratiodef
    """
    # Convert to relative luminance
    l1 = relative_luminance(color1)
    l2 = relative_luminance(color2)

    # WCAG contrast formula
    lighter = max(l1, l2)
    darker = min(l1, l2)

    return (lighter + 0.05) / (darker + 0.05)
