"""
Image processing and composition for creating social media creatives.
"""

import platform
from pathlib import Path
from typing import Tuple, Optional, Dict, List
import textwrap
from collections import Counter

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
          "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
          "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
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

  def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

  def _relative_luminance(self, rgb: Tuple[int, int, int]) -> float:
    """Calculate relative luminance per WCAG guidelines."""
    r, g, b = [c/255.0 for c in rgb]

    # Apply gamma correction
    r = r/12.92 if r <= 0.03928 else ((r + 0.055)/1.055) ** 2.4
    g = g/12.92 if g <= 0.03928 else ((g + 0.055)/1.055) ** 2.4
    b = b/12.92 if b <= 0.03928 else ((b + 0.055)/1.055) ** 2.4

    # WCAG luminance formula
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

  def calculate_contrast_ratio(self, color1: Tuple[int, int, int],
                               color2: Tuple[int, int, int]) -> float:
    """Calculate WCAG contrast ratio between two colors."""
    # Convert to relative luminance
    l1 = self._relative_luminance(color1)
    l2 = self._relative_luminance(color2)

    # WCAG contrast formula
    lighter = max(l1, l2)
    darker = min(l1, l2)

    return (lighter + 0.05) / (darker + 0.05)

  def _is_light(self, rgb: Tuple[int, int, int]) -> bool:
    """Check if a color is light based on luminance."""
    return self._relative_luminance(rgb) > 0.5

  def _is_dark(self, rgb: Tuple[int, int, int]) -> bool:
    """Check if a color is dark based on luminance."""
    return self._relative_luminance(rgb) <= 0.5

  def _extract_text_region(self, image: Image.Image, position: str) -> Image.Image:
    """Extract the region where text will be placed."""
    width, height = image.size

    if position == "bottom":
      # Bottom 30% of image
      region_height = int(height * 0.3)
      return image.crop((0, height - region_height, width, height))
    elif position == "top":
      # Top 30% of image
      region_height = int(height * 0.3)
      return image.crop((0, 0, width, region_height))
    else:  # center
      # Middle 40% of image
      region_height = int(height * 0.4)
      top = int(height * 0.3)
      return image.crop((0, top, width, top + region_height))

  def analyze_text_region(self, image: Image.Image, position: str = None) -> Dict:
    """
    Analyze the image to find the best region for text placement.
    If position is specified, analyzes that specific region.
    Otherwise, finds the region with best natural contrast.
    """
    if position:
      # Use specified position
      text_region = self._extract_text_region(image, position)
      region_position = position
    else:
      # Smart positioning: analyze multiple regions and pick the best
      text_region, region_position = self._find_best_text_region(image)

    # Convert to RGB if needed
    if text_region.mode != 'RGB':
      text_region = text_region.convert('RGB')

    # Get dominant colors in that region
    pixels = list(text_region.getdata())
    avg_r = sum(p[0] for p in pixels) / len(pixels)
    avg_g = sum(p[1] for p in pixels) / len(pixels)
    avg_b = sum(p[2] for p in pixels) / len(pixels)

    avg_color = (int(avg_r), int(avg_g), int(avg_b))
    avg_luminance = self._relative_luminance(avg_color)

    return {
      "average_color": avg_color,
      "luminance": avg_luminance,
      "is_light": avg_luminance > 0.5,
      "position": region_position
    }

  def _find_best_text_region(self, image: Image.Image) -> Tuple[Image.Image, str]:
    """Find the region in the image with best contrast potential for text."""
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
      if region.mode != 'RGB':
        region = region.convert('RGB')

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
      luminance = self._relative_luminance(avg_color)
      # Prefer very light or very dark regions (good natural contrast)
      contrast_potential = abs(luminance - 0.5) * 2  # 0 to 1, higher is better
      uniformity_score = 1.0 / (1.0 + total_variance / 10000)  # Normalize variance

      score = contrast_potential * 0.7 + uniformity_score * 0.3

      if score > best_score:
        best_score = score
        best_region = region
        best_position = position

    return best_region, best_position

  def select_text_colors(self, region_analysis: Dict,
                        brand_colors: List[str]) -> Dict:
    """Select text and outline colors that are brand-compliant and accessible."""

    # Parse brand colors to RGB
    brand_rgb = [self._hex_to_rgb(c) for c in brand_colors]
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
      ratio = self.calculate_contrast_ratio(text_color, image_bg_color)
      if ratio >= 4.5 and ratio > best_ratio:
        best_ratio = ratio
        # Choose outline color that contrasts with text
        outline_color = None
        for outline in outline_candidates:
          outline_ratio = self.calculate_contrast_ratio(text_color, outline)
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

    # If no brand colors meet contrast requirements, fall back to white/black
    if not best_combo:
      if region_analysis["is_light"]:
        best_combo = {
          "text_color": black,
          "bg_color": white,
          "contrast_ratio": self.calculate_contrast_ratio(black, image_bg_color)
        }
      else:
        best_combo = {
          "text_color": white,
          "bg_color": black,
          "contrast_ratio": self.calculate_contrast_ratio(white, image_bg_color)
        }

    return best_combo

  def add_text_overlay(self, image: Image.Image, message: str,
                       position: str = None, language_code: Optional[str] = None,
                       brand_colors: Optional[List[str]] = None) -> Image.Image:
    """
    Add brand-aware text overlay with smart positioning and clean typography.

    Args:
      image: Source image
      message: Text message to overlay
      position: Position hint ("top", "bottom", "center"). If None and brand_colors provided, uses smart positioning
      language_code: Optional language code for font selection (e.g., 'ar', 'he', 'zh')
      brand_colors: Optional list of brand colors in hex format for brand-aware text

    Returns:
      Image with text overlay
    """
    # Work on a copy
    img = image.copy().convert('RGBA')

    # Smart positioning: analyze image to find best natural contrast area
    if brand_colors and len(brand_colors) > 0:
      region_analysis = self.analyze_text_region(image, position)
      colors = self.select_text_colors(region_analysis, brand_colors)
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

    # Calculate position based on smart positioning or specified position
    padding = 40  # Comfortable padding from edges

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

    # Draw clean text directly on image - no effects, just great typography
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
                       brand_colors: Optional[List[str]] = None) -> Dict[str, Path]:
    """
    Create all aspect ratio variations from a source image.

    Args:
      source_image: Source image to process
      message: Campaign message to overlay
      output_dir: Directory to save variations
      product_name: Name of product (for filenames)
      brand_colors: Optional list of brand colors in hex format

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

      # Add text overlay with brand colors and smart positioning
      final = self.add_text_overlay(resized, message, position=None, brand_colors=brand_colors)

      # Save with quality optimization
      filename = f"{aspect_ratio.display_name}.jpg"
      output_path = output_dir / filename

      final.save(output_path, quality=95, optimize=True)
      results[aspect_ratio.display_name] = output_path

      print(f"    ✓ Saved: {output_path}")

    return results

  def process_from_path(self, image_path: Path, message: str,
                        output_dir: Path, product_name: str,
                        brand_colors: Optional[List[str]] = None) -> Dict[str, Path]:
    """
    Process an image from a file path.

    Args:
      image_path: Path to source image
      message: Campaign message to overlay
      output_dir: Directory to save variations
      product_name: Name of product
      brand_colors: Optional list of brand colors in hex format

    Returns:
      Dictionary mapping aspect ratio names to file paths
    """
    with Image.open(image_path) as img:
      # Convert to RGB if necessary
      if img.mode != 'RGB':
        img = img.convert('RGB')

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

        # Add localized text overlay with language-specific font, brand colors, and smart positioning
        final = self.add_text_overlay(resized, message, position=None,
                                    language_code=lang_code, brand_colors=brand_colors)

        # Save with quality optimization
        filename = f"{aspect_ratio.display_name}.jpg"
        output_path = lang_dir / filename

        final.save(output_path, quality=95, optimize=True)
        lang_results[aspect_ratio.display_name] = output_path

        print(f"    ✓ {aspect_ratio.display_name}: {output_path}")

      results[lang_code] = lang_results

    return results
