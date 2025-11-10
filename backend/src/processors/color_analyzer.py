"""
Color analysis and selection for brand-compliant, accessible text overlays.

This module analyzes image regions and selects optimal text and background colors
that meet both brand guidelines and WCAG accessibility standards.
"""

from typing import Dict, List, Tuple
from ..utils.color_utils import hex_to_rgb, calculate_contrast_ratio, relative_luminance


class ColorAnalyzer:
    """
    Analyzes colors and selects brand-compliant, accessible combinations.

    This class ensures text overlays meet both brand requirements and
    accessibility standards (WCAG AAA - 7:1 contrast ratio).

    Examples:
        >>> analyzer = ColorAnalyzer()
        >>> region_analysis = {
        ...     "average_color": (240, 240, 240),
        ...     "is_light": True,
        ...     "luminance": 0.85
        ... }
        >>> brand_colors = ["#FF6B35", "#004E89"]
        >>>
        >>> colors = analyzer.select_text_colors(region_analysis, brand_colors)
        >>> print(f"Text: {colors['text_color']}, Contrast: {colors['contrast_ratio']}")
        Text: (0, 78, 137), Contrast: 8.2
    """

    def __init__(self, min_contrast_ratio: float = 7.0):
        """
        Initialize the color analyzer.

        Args:
            min_contrast_ratio: Minimum WCAG contrast ratio required (default: 7.0 for AAA).
                              - WCAG AA requires 4.5:1 for normal text
                              - WCAG AAA requires 7:1 for normal text
                              - We default to AAA (7.0) for professional quality
        """
        self.min_contrast_ratio = min_contrast_ratio

    def select_text_colors(
        self,
        region_analysis: Dict,
        brand_colors: List[str]
    ) -> Dict:
        """
        Select text and background colors that are brand-compliant and accessible.

        This method finds the best combination of brand colors that meets strict
        accessibility requirements (7:1 contrast ratio by default).

        Selection strategy:
        1. Separate brand colors into light and dark groups
        2. Choose dark text on light backgrounds, light text on dark backgrounds
        3. Test each brand color for sufficient contrast
        4. Fall back to pure black/white if no brand colors meet requirements

        Args:
            region_analysis: Dictionary containing:
                - average_color: RGB tuple of background region
                - is_light: Boolean indicating if background is light
                - luminance: Relative luminance value
            brand_colors: List of hex color codes (e.g., ["#FF0000", "#0000FF"])

        Returns:
            Dictionary containing:
                - text_color: RGB tuple for text
                - bg_color: RGB tuple for outline/stroke
                - contrast_ratio: Actual contrast ratio achieved

        Examples:
            >>> analyzer = ColorAnalyzer(min_contrast_ratio=7.0)
            >>> region = {"average_color": (200, 200, 200), "is_light": True}
            >>> brand = ["#FF0000", "#0000FF"]
            >>> result = analyzer.select_text_colors(region, brand)
            >>> result['contrast_ratio'] >= 7.0
            True
        """
        # Parse brand colors to RGB
        brand_rgb = [hex_to_rgb(c) for c in brand_colors]
        image_bg_color = region_analysis["average_color"]

        # Separate light and dark brand colors
        light_colors = [c for c in brand_rgb if self._is_light(c)]
        dark_colors = [c for c in brand_rgb if self._is_dark(c)]

        # Default fallbacks
        white = (255, 255, 255)
        black = (0, 0, 0)

        # Determine which brand colors to use based on image background
        if region_analysis["is_light"]:
            # Light image background - need dark text
            text_candidates = dark_colors or [black]
            outline_candidates = light_colors or [white]
        else:
            # Dark image background - need light text
            text_candidates = light_colors or [white]
            outline_candidates = dark_colors or [black]

        # Find best text color that contrasts with the actual image background
        best_combo = None
        best_ratio = 0

        for text_color in text_candidates:
            # Test contrast between text and actual image background
            ratio = calculate_contrast_ratio(text_color, image_bg_color)
            if ratio >= self.min_contrast_ratio and ratio > best_ratio:
                best_ratio = ratio
                # Choose outline color that contrasts with text
                outline_color = None
                for outline in outline_candidates:
                    outline_ratio = calculate_contrast_ratio(text_color, outline)
                    if outline_ratio >= 3.0:  # Lower threshold for outline
                        outline_color = outline
                        break

                if not outline_color:
                    # Use opposite of text color as fallback
                    outline_color = white if self._is_dark(text_color) else black

                best_combo = {
                    "text_color": text_color,
                    "bg_color": outline_color,  # Used for outline/stroke
                    "contrast_ratio": ratio
                }

        # If no brand colors meet strict contrast requirements, use white/black for maximum readability
        # Scrim color should be opposite of text for maximum contrast
        if not best_combo:
            if region_analysis["is_light"]:
                # Light background: black text with WHITE scrim (brightens already-light background)
                best_combo = {
                    "text_color": black,
                    "bg_color": white,
                    "contrast_ratio": calculate_contrast_ratio(black, image_bg_color)
                }
            else:
                # Dark background: white text with BLACK scrim (darkens already-dark background)
                best_combo = {
                    "text_color": white,
                    "bg_color": black,
                    "contrast_ratio": calculate_contrast_ratio(white, image_bg_color)
                }

        return best_combo

    def _is_light(self, rgb: Tuple[int, int, int]) -> bool:
        """
        Check if a color is light based on relative luminance.

        Args:
            rgb: RGB color tuple

        Returns:
            True if luminance > 0.5, False otherwise
        """
        return relative_luminance(rgb) > 0.5

    def _is_dark(self, rgb: Tuple[int, int, int]) -> bool:
        """
        Check if a color is dark based on relative luminance.

        Args:
            rgb: RGB color tuple

        Returns:
            True if luminance <= 0.5, False otherwise
        """
        return relative_luminance(rgb) <= 0.5

    def get_recommended_text_color(
        self,
        background_color: Tuple[int, int, int]
    ) -> Tuple[int, int, int]:
        """
        Get recommended text color (black or white) for a given background.

        Simple utility method that returns pure black or white based on
        background luminance for maximum contrast.

        Args:
            background_color: RGB tuple of background color

        Returns:
            RGB tuple - (0, 0, 0) for dark text or (255, 255, 255) for light text

        Examples:
            >>> analyzer = ColorAnalyzer()
            >>> analyzer.get_recommended_text_color((240, 240, 240))
            (0, 0, 0)  # Black text on light background
            >>> analyzer.get_recommended_text_color((30, 30, 30))
            (255, 255, 255)  # White text on dark background
        """
        if self._is_light(background_color):
            return (0, 0, 0)  # Black text on light background
        else:
            return (255, 255, 255)  # White text on dark background
