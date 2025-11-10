"""
Image processing and composition for creating social media creatives.
"""

import platform
from pathlib import Path
from typing import Tuple, Optional, Dict
import textwrap

from PIL import Image, ImageDraw, ImageFont, ImageEnhance

from ..models.campaign import AspectRatio


class CreativeComposer:
  """Handles image resizing, cropping, and text overlay for social creatives."""

  def __init__(self):
    """Initialize the creative composer."""
    self.font_path = self._find_font()

  def _find_font(self, language_code: Optional[str] = None) -> Optional[str]:
    """
    Find a suitable font for text overlays with international script support.

    Searches platform-specific font directories, prioritizing fonts that support
    Arabic, Hebrew, CJK, and other international scripts.

    Args:
      language_code: Optional language code (e.g., 'ar', 'he', 'zh') to prioritize specific fonts

    Returns:
      Path to font file if found, None to use PIL default
    """
    system = platform.system()

    # Check if we need international script support
    needs_arabic = language_code and language_code.startswith(('ar', 'fa', 'ur'))
    needs_hebrew = language_code and language_code.startswith('he')
    needs_cjk = language_code and language_code.startswith(('zh', 'ja', 'ko'))

    font_candidates = []

    if system == "Darwin":  # macOS
      # macOS fonts with international support
      if needs_arabic or needs_hebrew:
        font_candidates.extend([
          "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
          "/Library/Fonts/Arial.ttf",
        ])
      font_candidates.extend([
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
      ])
    elif system == "Windows":
      # Windows fonts with international support
      if needs_arabic:
        font_candidates.extend([
          "C:/Windows/Fonts/arialuni.ttf",
          "C:/Windows/Fonts/tahoma.ttf",
        ])
      if needs_hebrew:
        font_candidates.extend([
          "C:/Windows/Fonts/arialuni.ttf",
          "C:/Windows/Fonts/arial.ttf",
        ])
      font_candidates.extend([
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
      ])
    else:  # Linux / Docker
      # Noto fonts have excellent international support
      if needs_arabic:
        font_candidates.extend([
          "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
          "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
        ])
      if needs_hebrew:
        font_candidates.extend([
          "/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf",
        ])
      if needs_cjk:
        font_candidates.extend([
          "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ])

      # General fonts with good Unicode coverage
      font_candidates.extend([
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
      ])

    for font in font_candidates:
      if Path(font).exists():
        return font

    return None  # Will use PIL default

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
                       position: str = "bottom", language_code: Optional[str] = None) -> Image.Image:
    """
    Add text overlay with semi-transparent background.

    Args:
      image: Source image
      message: Text message to overlay
      position: Position of text ("top", "bottom", "center")
      language_code: Optional language code for font selection (e.g., 'ar', 'he', 'zh')

    Returns:
      Image with text overlay
    """
    # Work on a copy
    img = image.copy().convert('RGBA')

    # Calculate font size based on image dimensions
    # Aim for readable text that scales with image size
    font_size = max(24, min(72, img.width // 15))

    # Load font with language-specific support
    try:
      # Get language-specific font if provided
      font_path = self._find_font(language_code) if language_code else self.font_path
      if font_path:
        font = ImageFont.truetype(font_path, font_size)
      else:
        font = ImageFont.load_default()
    except Exception:
      font = ImageFont.load_default()

    # Create drawing context for measuring text
    draw = ImageDraw.Draw(img)

    # Wrap text to fit within image width
    max_width_chars = img.width // (font_size // 2)
    wrapped_text = textwrap.fill(message, width=max(20, max_width_chars))

    # Get text bounding box
    bbox = draw.textbbox((0, 0), wrapped_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Create semi-transparent overlay
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    # Calculate position
    padding = 30
    text_x = (img.width - text_width) // 2

    if position == "bottom":
      text_y = img.height - text_height - padding * 2
    elif position == "top":
      text_y = padding
    else:  # center
      text_y = (img.height - text_height) // 2

    # Draw background rectangle with rounded corners effect
    rect_bounds = [
      text_x - padding,
      text_y - padding,
      text_x + text_width + padding,
      text_y + text_height + padding
    ]

    # Semi-transparent black background
    overlay_draw.rectangle(rect_bounds, fill=(0, 0, 0, 190))

    # Composite overlay onto image
    img = Image.alpha_composite(img, overlay)

    # Draw text in white
    draw = ImageDraw.Draw(img)
    draw.text((text_x, text_y), wrapped_text, fill=(255, 255, 255, 255), font=font)

    # Convert back to RGB
    return img.convert('RGB')

  def create_variations(self, source_image: Image.Image, message: str,
                       output_dir: Path, product_name: str) -> Dict[str, Path]:
    """
    Create all aspect ratio variations from a source image.

    Args:
      source_image: Source image to process
      message: Campaign message to overlay
      output_dir: Directory to save variations
      product_name: Name of product (for filenames)

    Returns:
      Dictionary mapping aspect ratio names to file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    for aspect_ratio in AspectRatio.all():
      print(f"  Creating {aspect_ratio.display_name} variation...")

      # Smart crop to aspect ratio
      cropped = self.smart_crop(source_image, aspect_ratio.ratio)

      # Resize to target dimensions
      resized = self.resize_to_dimensions(cropped, aspect_ratio.dimensions)

      # Add text overlay
      final = self.add_text_overlay(resized, message, position="bottom")

      # Save with quality optimization
      filename = f"{aspect_ratio.display_name}.jpg"
      output_path = output_dir / filename

      final.save(output_path, quality=95, optimize=True)
      results[aspect_ratio.display_name] = output_path

      print(f"    ✓ Saved: {output_path}")

    return results

  def process_from_path(self, image_path: Path, message: str,
                        output_dir: Path, product_name: str) -> Dict[str, Path]:
    """
    Process an image from a file path.

    Args:
      image_path: Path to source image
      message: Campaign message to overlay
      output_dir: Directory to save variations
      product_name: Name of product

    Returns:
      Dictionary mapping aspect ratio names to file paths
    """
    with Image.open(image_path) as img:
      # Convert to RGB if necessary
      if img.mode != 'RGB':
        img = img.convert('RGB')

      return self.create_variations(img, message, output_dir, product_name)

  def create_localized_variations(self, source_image: Image.Image,
                                 messages: Dict[str, str],
                                 output_dir: Path,
                                 product_name: str) -> Dict[str, Dict[str, Path]]:
    """
    Create variations for multiple languages/localizations.

    Args:
      source_image: Source image to process
      messages: Dictionary of language code to message
      output_dir: Base directory to save variations
      product_name: Name of product

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

        # Add localized text overlay with language-specific font
        final = self.add_text_overlay(resized, message, position="bottom", language_code=lang_code)

        # Save with quality optimization
        filename = f"{aspect_ratio.display_name}.jpg"
        output_path = lang_dir / filename

        final.save(output_path, quality=95, optimize=True)
        lang_results[aspect_ratio.display_name] = output_path

        print(f"    ✓ {aspect_ratio.display_name}: {output_path}")

      results[lang_code] = lang_results

    return results
