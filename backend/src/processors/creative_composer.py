"""
Image processing and composition for creating social media creatives.

This module orchestrates specialized components to create professional social media
creatives with text overlays, brand-compliant colors, and multi-language support.
"""

from pathlib import Path
from typing import Tuple, Optional, Dict, List

from PIL import Image, ImageDraw, ImageFont

from ..models.campaign import AspectRatio
from ..utils.image_utils import ensure_rgb
from .font_manager import FontManager
from .text_layout_engine import TextLayoutEngine
from .color_analyzer import ColorAnalyzer
from .gradient_renderer import GradientRenderer


class CreativeComposer:
  """
  Orchestrates image processing for creating social media creatives.

  This class coordinates specialized components to produce professional-quality
  social media images with text overlays, brand compliance, and accessibility.

  Components:
    - FontManager: Handles font discovery and loading
    - TextLayoutEngine: Manages text positioning and wrapping
    - ColorAnalyzer: Selects brand-compliant, accessible colors
    - GradientRenderer: Creates professional gradient overlays

  Examples:
    >>> composer = CreativeComposer()
    >>> image = Image.open('product.jpg')
    >>> results = composer.create_variations(
    ...     image,
    ...     "Shop Now - 50% Off",
    ...     output_dir=Path("./output"),
    ...     product_name="Widget",
    ...     brand_colors=["#FF6B35", "#004E89"]
    ... )
  """

  def __init__(self):
    """
    Initialize the creative composer with specialized components.

    Sets up dependency injection for all specialized processors.
    """
    # Initialize specialized components
    self.font_manager = FontManager()
    self.layout_engine = TextLayoutEngine()
    self.color_analyzer = ColorAnalyzer(min_contrast_ratio=7.0)
    self.gradient_renderer = GradientRenderer(max_alpha=150, fade_exponent=2.0)


  def smart_crop(self, image: Image.Image, target_ratio: Tuple[int, int]) -> Image.Image:
    """
    Intelligently crop an image to a target aspect ratio.

    Crops from the center to maintain the focal point.

    Args:
      image: Source image to crop
      target_ratio: Target aspect ratio as (width, height)

    Returns:
      Cropped image
    """
    target_width_ratio, target_height_ratio = target_ratio

    # Get current dimensions
    width, height = image.size
    current_ratio = width / height
    target_ratio_value = target_width_ratio / target_height_ratio

    if abs(current_ratio - target_ratio_value) < 0.01:
      # Already the correct ratio
      return image

    if current_ratio > target_ratio_value:
      # Image is wider than target - crop width
      new_width = int(height * target_ratio_value)
      left = (width - new_width) // 2
      crop_box = (left, 0, left + new_width, height)
    else:
      # Image is taller than target - crop height
      new_height = int(width / target_ratio_value)
      top = (height - new_height) // 2
      crop_box = (0, top, width, top + new_height)

    return image.crop(crop_box)

  def resize_to_dimensions(self, image: Image.Image, dimensions: Tuple[int, int]) -> Image.Image:
    """
    Resize an image to specific dimensions.

    Uses high-quality resampling.

    Args:
      image: Source image
      dimensions: Target dimensions as (width, height)

    Returns:
      Resized image
    """
    return image.resize(dimensions, Image.Resampling.LANCZOS)

  def add_text_overlay(self, image: Image.Image, message: str,
                       position: str = None, language_code: Optional[str] = None,
                       brand_colors: Optional[List[str]] = None) -> Image.Image:
    """
    Add brand-aware text overlay with smart positioning and clean typography.

    Orchestrates the layout engine, color analyzer, font manager, and gradient
    renderer to create professional text overlays.

    Args:
      image: Source image
      message: Text message to overlay
      position: Position hint ("top", "bottom", "center"). If None and brand_colors
               provided, uses smart positioning
      language_code: Optional language code for font selection (e.g., 'ar', 'he', 'zh')
      brand_colors: Optional list of brand colors in hex format for brand-aware text

    Returns:
      Image with text overlay

    Examples:
      >>> composer = CreativeComposer()
      >>> img = Image.open('product.jpg')
      >>> result = composer.add_text_overlay(
      ...     img,
      ...     "Shop Now",
      ...     brand_colors=["#FF6B35", "#004E89"]
      ... )
    """
    # Work on a copy
    img = image.copy().convert('RGBA')

    # Step 1: Analyze text region and select colors using specialized components
    if brand_colors and len(brand_colors) > 0:
      # Delegate to TextLayoutEngine for region analysis
      region_analysis = self.layout_engine.analyze_text_region(image, position)
      # Delegate to ColorAnalyzer for color selection
      colors = self.color_analyzer.select_text_colors(region_analysis, brand_colors)
      # Use the smart position if no specific position was requested
      if not position:
        position = region_analysis["position"]
    else:
      # Fallback to default white text on black background
      colors = {
        "text_color": (255, 255, 255),
        "bg_color": (0, 0, 0),
        "contrast_ratio": 21.0  # Max contrast
      }
      position = position or "bottom"

    # Step 2: Calculate font size and load appropriate font
    # Aim for readable text that scales with image size
    font_size = max(24, min(72, img.width // 15))

    # Delegate to FontManager for font loading
    font = self.font_manager.load_font_with_fallback(font_size, language_code)

    # Step 3: Wrap text and calculate dimensions
    # Create drawing context for measuring text
    draw = ImageDraw.Draw(img)

    # Define padding
    padding = 40  # Comfortable padding from edges

    # Calculate available width for text (leaving padding on both sides)
    max_text_width = img.width - (padding * 2)

    # Delegate to TextLayoutEngine for text wrapping
    wrapped_text = self.layout_engine.wrap_text(message, font, max_text_width, draw)

    # Get text bounding box
    bbox = draw.textbbox((0, 0), wrapped_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Step 4: Adjust font size if text is too large
    max_attempts = 3
    attempt = 0
    while (text_width > max_text_width or text_height > img.height - padding * 4) and attempt < max_attempts:
      font_size = int(font_size * 0.85)  # Reduce by 15%
      # Reload font at smaller size
      font = self.font_manager.load_font_with_fallback(font_size, language_code)

      # Re-wrap with new font size
      wrapped_text = self.layout_engine.wrap_text(message, font, max_text_width, draw)
      bbox = draw.textbbox((0, 0), wrapped_text, font=font)
      text_width = bbox[2] - bbox[0]
      text_height = bbox[3] - bbox[1]
      attempt += 1

    # Step 5: Calculate text position
    # Map positions to coordinates
    if position in ["bottom", "bottom-center"]:
      text_x = (img.width - text_width) // 2
      text_y = img.height - text_height - padding * 2
    elif position == "bottom-left":
      text_x = padding
      text_y = img.height - text_height - padding * 2
    elif position == "bottom-right":
      text_x = img.width - text_width - padding
      text_y = img.height - text_height - padding * 2
    elif position in ["top", "top-center"]:
      text_x = (img.width - text_width) // 2
      text_y = padding
    elif position == "top-left":
      text_x = padding
      text_y = padding
    elif position == "top-right":
      text_x = img.width - text_width - padding
      text_y = padding
    elif position == "center":
      text_x = (img.width - text_width) // 2
      text_y = (img.height - text_height) // 2
    else:  # default to bottom-center
      text_x = (img.width - text_width) // 2
      text_y = img.height - text_height - padding * 2

    # Step 6: Create gradient overlay
    # Delegate to GradientRenderer for creating the scrim
    scrim_color = colors["bg_color"]
    overlay = self.gradient_renderer.create_directional_gradient(
      image_size=img.size,
      text_position=(text_x, text_y),
      text_size=(text_width, text_height),
      scrim_color=scrim_color
    )

    # Composite gradient overlay
    img = Image.alpha_composite(img, overlay)

    # Step 7: Draw text on top of gradient scrim
    draw = ImageDraw.Draw(img)
    text_color_with_alpha = (*colors["text_color"], 255)
    draw.text((text_x, text_y), wrapped_text, fill=text_color_with_alpha, font=font)

    # Log contrast ratio for debugging (optional)
    if brand_colors:
      print(f"    Text overlay contrast ratio: {colors.get('contrast_ratio', 0):.2f}:1")

    # Convert back to RGB
    return img.convert('RGB')

  def create_variations(self, source_image: Image.Image, message: str,
                       output_dir: Path, product_name: str,
                       brand_colors: Optional[List[str]] = None) -> Dict[str, tuple]:
    """
    Create all aspect ratio variations from a source image.

    Args:
      source_image: Source image to process
      message: Campaign message to overlay
      output_dir: Directory to save variations
      product_name: Name of product (for filenames)
      brand_colors: Optional list of brand colors in hex format

    Returns:
      Dictionary mapping aspect ratio names to (final_path, pre_overlay_path) tuples
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    for aspect_ratio in AspectRatio.all():
      print(f"  Creating {aspect_ratio.display_name} variation...")

      # Smart crop to aspect ratio
      cropped = self.smart_crop(source_image, aspect_ratio.ratio)

      # Resize to target dimensions
      resized = self.resize_to_dimensions(cropped, aspect_ratio.dimensions)

      # Save pre-overlay version for brand color compliance checking
      # This preserves the original colors before gradient scrim is applied
      pre_overlay_filename = f".{aspect_ratio.display_name}_pre_overlay.jpg"  # Hidden file
      pre_overlay_path = output_dir / pre_overlay_filename
      resized.save(pre_overlay_path, quality=95, optimize=True)

      # Add text overlay with brand colors and smart positioning
      final = self.add_text_overlay(resized, message, position=None, brand_colors=brand_colors)

      # Save with quality optimization
      filename = f"{aspect_ratio.display_name}.jpg"
      output_path = output_dir / filename

      final.save(output_path, quality=95, optimize=True)
      results[aspect_ratio.display_name] = (output_path, pre_overlay_path)

      print(f"    ✓ Saved: {output_path}")

    return results

  def process_from_path(self, image_path: Path, message: str,
                        output_dir: Path, product_name: str,
                        brand_colors: Optional[List[str]] = None) -> Dict[str, tuple]:
    """
    Process an image from a file path.

    Args:
      image_path: Path to source image
      message: Campaign message to overlay
      output_dir: Directory to save variations
      product_name: Name of product
      brand_colors: Optional list of brand colors in hex format

    Returns:
      Dictionary mapping aspect ratio names to (final_path, pre_overlay_path) tuples
    """
    with Image.open(image_path) as img:
      # Convert to RGB if necessary
      img = ensure_rgb(img)

      return self.create_variations(img, message, output_dir, product_name, brand_colors)

  def create_localized_variations(self, source_image: Image.Image,
                                 messages: Dict[str, str],
                                 output_dir: Path,
                                 product_name: str,
                                 brand_colors: Optional[List[str]] = None) -> Dict[str, Dict[str, Path]]:
    """
    Create variations for multiple languages/localizations.

    Args:
      source_image: Source image to process
      messages: Dictionary of language code to message
      output_dir: Base directory to save variations
      product_name: Name of product
      brand_colors: Optional list of brand colors in hex format

    Returns:
      Nested dictionary: {language: {aspect_ratio: path}}
    """
    results = {}

    for lang_code, message in messages.items():
      # Create language-specific subdirectory
      lang_dir = output_dir / lang_code
      lang_dir.mkdir(parents=True, exist_ok=True)

      print(f"  Creating {lang_code} variations...")

      # Create variations for this language
      lang_results = {}

      for aspect_ratio in AspectRatio.all():
        # Smart crop to aspect ratio
        cropped = self.smart_crop(source_image, aspect_ratio.ratio)

        # Resize to target dimensions
        resized = self.resize_to_dimensions(cropped, aspect_ratio.dimensions)

        # Save pre-overlay version for brand color compliance checking
        pre_overlay_filename = f".{aspect_ratio.display_name}_pre_overlay.jpg"  # Hidden file
        pre_overlay_path = lang_dir / pre_overlay_filename
        resized.save(pre_overlay_path, quality=95, optimize=True)

        # Add localized text overlay with language-specific font, brand colors, and smart positioning
        final = self.add_text_overlay(resized, message, position=None,
                                    language_code=lang_code, brand_colors=brand_colors)

        # Save with quality optimization
        filename = f"{aspect_ratio.display_name}.jpg"
        output_path = lang_dir / filename

        final.save(output_path, quality=95, optimize=True)
        lang_results[aspect_ratio.display_name] = (output_path, pre_overlay_path)

        print(f"    ✓ {aspect_ratio.display_name}: {output_path}")

      results[lang_code] = lang_results

    return results
