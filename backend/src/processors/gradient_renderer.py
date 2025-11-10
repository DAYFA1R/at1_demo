"""
Gradient overlay renderer for enhancing text readability.

This module creates professional-quality gradient scrims (similar to Netflix/
streaming services) that enhance text readability without completely obscuring
the background image.
"""

from typing import Tuple
from PIL import Image


class GradientRenderer:
    """
    Renders directional gradient overlays to enhance text readability.

    Creates smooth, position-aware gradient scrims that fade from the text position
    into the image, ensuring text remains readable while maintaining visual appeal.

    The gradients use an exponential ease-out curve for natural-looking fades,
    similar to professional streaming service overlays (Netflix, HBO, etc.).

    Examples:
        >>> renderer = GradientRenderer()
        >>> # Create gradient for bottom-positioned text
        >>> text_pos = (100, 500)
        >>> text_size = (600, 100)
        >>> scrim_color = (0, 0, 0)  # Black
        >>>
        >>> overlay = renderer.create_directional_gradient(
        ...     image_size=(1080, 1080),
        ...     text_position=text_pos,
        ...     text_size=text_size,
        ...     scrim_color=scrim_color
        ... )
    """

    def __init__(self, max_alpha: int = 150, fade_exponent: float = 2.0):
        """
        Initialize the gradient renderer.

        Args:
            max_alpha: Maximum opacity of the gradient (0-255).
                      Default 150 (~59% opacity) balances readability with aesthetics.
            fade_exponent: Exponential curve steepness for fade effect.
                          Higher values create sharper fades. Default 2.0 for smooth effect.
        """
        self.max_alpha = max_alpha
        self.fade_exponent = fade_exponent

    def create_directional_gradient(
        self,
        image_size: Tuple[int, int],
        text_position: Tuple[int, int],
        text_size: Tuple[int, int],
        scrim_color: Tuple[int, int, int]
    ) -> Image.Image:
        """
        Create a directional gradient overlay based on text position.

        The gradient automatically determines the optimal direction based on which
        edge of the image the text is closest to, then fades from that edge across
        the entire image.

        Gradient characteristics:
        - Uses exponential ease-out curve for natural fade
        - Maximum opacity at text edge (default 59%)
        - Fades smoothly into transparent
        - Direction adapts to text position (top/bottom/left/right)

        Args:
            image_size: Tuple of (width, height) of the image in pixels
            text_position: Tuple of (x, y) coordinates of text top-left corner
            text_size: Tuple of (width, height) of text bounding box
            scrim_color: RGB tuple of the gradient color

        Returns:
            RGBA PIL Image containing the gradient overlay (transparent background)

        Examples:
            >>> renderer = GradientRenderer()
            >>> # Text at bottom of image
            >>> overlay = renderer.create_directional_gradient(
            ...     image_size=(1080, 1080),
            ...     text_position=(200, 900),
            ...     text_size=(600, 80),
            ...     scrim_color=(0, 0, 0)  # Black scrim
            ... )
            >>> # Composite onto image
            >>> img = Image.open('photo.jpg').convert('RGBA')
            >>> result = Image.alpha_composite(img, overlay)
        """
        img_width, img_height = image_size
        text_x, text_y = text_position
        text_width, text_height = text_size

        # Create transparent overlay
        overlay = Image.new('RGBA', image_size, (0, 0, 0, 0))
        pixels = overlay.load()

        # Calculate text center for distance calculations
        text_center_y = text_y + text_height // 2
        text_center_x = text_x + text_width // 2

        # Calculate distances to each edge
        distance_to_top = text_center_y
        distance_to_bottom = img_height - text_center_y
        distance_to_left = text_center_x
        distance_to_right = img_width - text_center_x

        # Find the closest edge - gradient will emanate from there
        min_distance = min(distance_to_top, distance_to_bottom,
                          distance_to_left, distance_to_right)

        # Create gradient from that edge across the entire image dimension
        for y in range(img_height):
            for x in range(img_width):
                # Calculate distance from the edge where text is positioned
                if min_distance == distance_to_top:
                    # Text at top - fade from top down
                    distance_from_edge = y / img_height
                elif min_distance == distance_to_bottom:
                    # Text at bottom - fade from bottom up
                    distance_from_edge = (img_height - y) / img_height
                elif min_distance == distance_to_left:
                    # Text at left - fade from left to right
                    distance_from_edge = x / img_width
                else:
                    # Text at right - fade from right to left
                    distance_from_edge = (img_width - x) / img_width

                # Apply exponential ease-out curve for smooth, natural fade
                # Strongest at text edge, fades into image
                fade = (1.0 - distance_from_edge) ** self.fade_exponent

                # Calculate alpha channel based on fade
                alpha = int(fade * self.max_alpha)

                if alpha > 0:
                    pixels[x, y] = (*scrim_color, alpha)

        return overlay

    def create_vignette(
        self,
        image_size: Tuple[int, int],
        color: Tuple[int, int, int] = (0, 0, 0),
        strength: float = 0.7
    ) -> Image.Image:
        """
        Create a circular vignette overlay.

        Darkens (or lightens) the edges of an image while keeping the center clear.
        Useful for drawing attention to central subjects.

        Args:
            image_size: Tuple of (width, height) of the image
            color: RGB color for the vignette (default: black)
            strength: Vignette strength from 0.0 to 1.0 (default: 0.7)

        Returns:
            RGBA PIL Image containing the vignette overlay

        Examples:
            >>> renderer = GradientRenderer()
            >>> vignette = renderer.create_vignette((1080, 1080), strength=0.5)
            >>> img = Image.open('photo.jpg').convert('RGBA')
            >>> result = Image.alpha_composite(img, vignette)
        """
        width, height = image_size
        overlay = Image.new('RGBA', image_size, (0, 0, 0, 0))
        pixels = overlay.load()

        # Center point
        center_x = width / 2
        center_y = height / 2

        # Maximum distance from center (corner)
        max_distance = ((center_x ** 2) + (center_y ** 2)) ** 0.5

        for y in range(height):
            for x in range(width):
                # Calculate distance from center
                dx = x - center_x
                dy = y - center_y
                distance = (dx ** 2 + dy ** 2) ** 0.5

                # Normalize distance (0 at center, 1 at corners)
                normalized_distance = distance / max_distance

                # Apply exponential curve for smooth vignette
                vignette_amount = normalized_distance ** 2

                # Calculate alpha
                alpha = int(vignette_amount * strength * 255)

                if alpha > 0:
                    pixels[x, y] = (*color, alpha)

        return overlay
