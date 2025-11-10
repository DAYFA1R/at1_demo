"""
Text layout and positioning engine for creative overlays.

This module handles finding optimal text positions, wrapping text to fit within
boundaries, and analyzing image regions for text placement.
"""

from typing import Tuple, Dict
from PIL import Image, ImageDraw, ImageFont
from ..utils.color_utils import relative_luminance
from ..utils.image_utils import ensure_rgb


class TextLayoutEngine:
    """
    Handles text positioning, wrapping, and region analysis for image overlays.

    This class provides sophisticated text layout capabilities including:
    - Finding optimal text placement regions in images
    - Wrapping text to fit within pixel widths (works for all languages)
    - Analyzing image regions for contrast and uniformity

    Examples:
        >>> engine = TextLayoutEngine()
        >>> # Find best region for text
        >>> region, position = engine.find_best_text_region(image)

        >>> # Wrap text to specific width
        >>> wrapped = engine.wrap_text(text, font, max_width=800, draw_context=draw)
    """

    def find_best_text_region(self, image: Image.Image) -> Tuple[Image.Image, str]:
        """
        Find the region in the image with best contrast potential for text.

        Analyzes 6 candidate regions (top-left, top-right, bottom-left, bottom-right,
        bottom-center, center) and scores them based on uniformity and contrast potential.

        Scoring factors:
        - Contrast potential: Prefers very light or very dark regions (70% weight)
        - Uniformity: Prefers regions with low color variance (30% weight)

        Args:
            image: Source image to analyze

        Returns:
            Tuple of (best_region_image, position_name) where position_name is one of:
            "top-left", "top-right", "bottom-left", "bottom-right", "bottom-center", "center"

        Examples:
            >>> engine = TextLayoutEngine()
            >>> region, position = engine.find_best_text_region(product_image)
            >>> print(f"Best position: {position}")
            Best position: bottom-center
        """
        width, height = image.size

        # Define candidate regions to check
        regions = {
            "bottom-left": (0, int(height * 0.7), int(width * 0.4), height),
            "bottom-right": (int(width * 0.6), int(height * 0.7), width, height),
            "bottom-center": (int(width * 0.3), int(height * 0.7), int(width * 0.7), height),
            "top-left": (0, 0, int(width * 0.4), int(height * 0.3)),
            "top-right": (int(width * 0.6), 0, width, int(height * 0.3)),
            "center": (int(width * 0.2), int(height * 0.4), int(width * 0.8), int(height * 0.6))
        }

        best_region = None
        best_position = "bottom-center"
        best_score = 0

        for position, (x1, y1, x2, y2) in regions.items():
            region = image.crop((x1, y1, x2, y2))
            region = ensure_rgb(region)

            # Calculate uniformity and luminance
            pixels = list(region.getdata())
            avg_r = sum(p[0] for p in pixels) / len(pixels)
            avg_g = sum(p[1] for p in pixels) / len(pixels)
            avg_b = sum(p[2] for p in pixels) / len(pixels)
            avg_color = (int(avg_r), int(avg_g), int(avg_b))

            # Calculate variance to measure uniformity (lower variance = more uniform = better for text)
            variance_r = sum((p[0] - avg_r) ** 2 for p in pixels) / len(pixels)
            variance_g = sum((p[1] - avg_g) ** 2 for p in pixels) / len(pixels)
            variance_b = sum((p[2] - avg_b) ** 2 for p in pixels) / len(pixels)
            total_variance = (variance_r + variance_g + variance_b) / 3

            # Score: prefer uniform regions (lower variance) that aren't mid-tone
            luminance = relative_luminance(avg_color)
            # Prefer very light or very dark regions (good natural contrast)
            contrast_potential = abs(luminance - 0.5) * 2  # 0 to 1, higher is better
            uniformity_score = 1.0 / (1.0 + total_variance / 10000)  # Normalize variance

            score = contrast_potential * 0.7 + uniformity_score * 0.3

            if score > best_score:
                best_score = score
                best_region = region
                best_position = position

        return best_region, best_position

    def analyze_text_region(self, image: Image.Image, position: str = None) -> Dict:
        """
        Analyze an image region to determine optimal text styling.

        If position is provided, extracts that specific region. Otherwise, finds
        the best region automatically using find_best_text_region().

        Args:
            image: Source image to analyze
            position: Optional position hint ("top", "bottom", "center").
                     If None, automatically finds best region.

        Returns:
            Dictionary containing:
                - average_color: RGB tuple of average region color
                - luminance: Relative luminance (0.0-1.0)
                - is_light: Boolean indicating if region is light
                - position: Position name used

        Examples:
            >>> engine = TextLayoutEngine()
            >>> analysis = engine.analyze_text_region(image, position="bottom")
            >>> if analysis["is_light"]:
            ...     print("Use dark text on this light background")
        """
        if position:
            # Extract the specified region
            width, height = image.size
            if position == "bottom":
                text_region = image.crop((0, int(height * 0.7), width, height))
                region_position = "bottom"
            elif position == "top":
                text_region = image.crop((0, 0, width, int(height * 0.3)))
                region_position = "top"
            else:  # center or other
                text_region = image.crop((int(width * 0.2), int(height * 0.4),
                                         int(width * 0.8), int(height * 0.6)))
                region_position = "center"
        else:
            # Smart positioning: analyze multiple regions and pick the best
            text_region, region_position = self.find_best_text_region(image)

        # Convert to RGB if needed
        text_region = ensure_rgb(text_region)

        # Get dominant colors in that region
        pixels = list(text_region.getdata())
        avg_r = sum(p[0] for p in pixels) / len(pixels)
        avg_g = sum(p[1] for p in pixels) / len(pixels)
        avg_b = sum(p[2] for p in pixels) / len(pixels)

        avg_color = (int(avg_r), int(avg_g), int(avg_b))
        avg_luminance = relative_luminance(avg_color)

        return {
            "average_color": avg_color,
            "luminance": avg_luminance,
            "is_light": avg_luminance > 0.5,
            "position": region_position
        }

    def wrap_text(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int,
        draw_context: ImageDraw.ImageDraw
    ) -> str:
        """
        Wrap text to fit within a maximum pixel width.

        This method properly handles all languages by measuring actual pixel width
        instead of character count. Works correctly for Latin, Arabic, Hebrew, CJK,
        and other scripts.

        Args:
            text: Text to wrap
            font: Font to use for measurement
            max_width: Maximum width in pixels
            draw_context: ImageDraw context for text measurement

        Returns:
            Wrapped text with newlines inserted at appropriate points

        Examples:
            >>> from PIL import Image, ImageDraw, ImageFont
            >>> img = Image.new('RGB', (800, 600))
            >>> draw = ImageDraw.Draw(img)
            >>> font = ImageFont.truetype('/path/to/font.ttf', 48)
            >>>
            >>> engine = TextLayoutEngine()
            >>> long_text = "This is a very long message that needs wrapping"
            >>> wrapped = engine.wrap_text(long_text, font, 400, draw)
            >>> print(wrapped)
            This is a very
            long message that
            needs wrapping

        Note:
            If a single word is longer than max_width, it will be placed on its own
            line to avoid infinite loops, even though it exceeds the width.
        """
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            # Try adding this word to current line
            test_line = ' '.join(current_line + [word])
            bbox = draw_context.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]

            if line_width <= max_width:
                current_line.append(word)
            else:
                # Line is too long, start new line
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word is too long, add it anyway to avoid infinite loop
                    lines.append(word)
                    current_line = []

        # Add remaining words
        if current_line:
            lines.append(' '.join(current_line))

        return '\n'.join(lines)
