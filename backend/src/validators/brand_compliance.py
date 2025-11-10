"""
Brand compliance validation for creative assets.
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import Counter

from PIL import Image
import colorsys

from ..utils.color_utils import hex_to_rgb, rgb_to_hex, color_distance
from ..utils.image_utils import ensure_rgb


class BrandComplianceValidator:
  """Validates creative assets meet brand guidelines."""

  def __init__(self, brand_colors: Optional[List[str]] = None,
               logo_path: Optional[str] = None,
               color_tolerance: int = 25):
    """
    Initialize the brand compliance validator.

    Args:
      brand_colors: List of brand colors in hex format (e.g., ["#FF0000"])
      logo_path: Path to brand logo file
      color_tolerance: Color matching tolerance (0-100, lower = stricter)
                      Default 25 means colors must be 75% similar to count
    """
    self.brand_colors = self._parse_brand_colors(brand_colors or [])
    self.logo_path = Path(logo_path) if logo_path else None
    self.color_tolerance = color_tolerance

  def _parse_brand_colors(self, hex_colors: List[str]) -> List[Tuple[int, int, int]]:
    """
    Convert hex colors to RGB tuples.

    Args:
      hex_colors: List of hex color strings

    Returns:
      List of RGB tuples
    """
    rgb_colors = []
    for hex_color in hex_colors:
      try:
        rgb_colors.append(hex_to_rgb(hex_color))
      except ValueError:
        # Skip invalid colors
        continue
    return rgb_colors

  def extract_dominant_colors(self, image: Image.Image, count: int = 5) -> List[Tuple]:
    """
    Extract dominant colors from an image.

    Args:
      image: PIL Image object
      count: Number of dominant colors to extract

    Returns:
      List of (color_rgb, percentage) tuples
    """
    # Resize for faster processing
    img = image.copy()
    img.thumbnail((150, 150))

    # Convert to RGB if needed
    if img.mode != 'RGB':
      img = img.convert('RGB')

    # Use color quantization to reduce to a palette of distinct colors
    # This groups similar colors together instead of counting every pixel shade
    quantized = img.quantize(colors=32, method=2)  # 32 colors, max coverage method

    # Convert back to RGB to get the palette colors
    quantized_rgb = quantized.convert('RGB')

    # Get all pixels from quantized image
    pixels = list(quantized_rgb.getdata())

    # Count color occurrences
    color_counts = Counter(pixels)

    # Get most common colors
    total_pixels = len(pixels)
    dominant = []

    for color, count_val in color_counts.most_common(count):
      percentage = (count_val / total_pixels) * 100
      dominant.append((color, round(percentage, 2)))

    return dominant

  def validate_colors(self, image_path: Path) -> Dict:
    """
    Check if image colors align with brand palette.

    Args:
      image_path: Path to image file

    Returns:
      Dictionary with color validation results
    """
    if not self.brand_colors:
      return {
        "checked": False,
        "reason": "No brand colors configured"
      }

    with Image.open(image_path) as img:
      dominant_colors = self.extract_dominant_colors(img, count=5)

    # Check if any dominant colors match brand colors
    # Track which image colors we've already matched to avoid double-counting
    matches = []
    matched_image_colors = set()

    for dom_color, percentage in dominant_colors:
      dom_hex = rgb_to_hex(dom_color)

      # Find best matching brand color for this image color
      best_match = None
      best_similarity = 0

      for brand_color in self.brand_colors:
        distance = color_distance(dom_color, brand_color)
        # Normalize distance to 0-100 scale
        similarity = max(0, 100 - (distance / 4.41))

        if similarity >= (100 - self.color_tolerance) and similarity > best_similarity:
          best_similarity = similarity
          best_match = {
            "image_color": dom_hex,
            "brand_color": rgb_to_hex(brand_color),
            "similarity": round(similarity, 1),
            "coverage": percentage
          }

      # Add best match if found and not already matched
      if best_match and dom_hex not in matched_image_colors:
        matches.append(best_match)
        matched_image_colors.add(dom_hex)

    # Calculate overall compliance
    if matches:
      total_coverage = sum(m["coverage"] for m in matches)
      avg_similarity = sum(m["similarity"] for m in matches) / len(matches)
      compliant = total_coverage >= 20  # At least 20% brand colors
    else:
      total_coverage = 0
      avg_similarity = 0
      compliant = False

    return {
      "checked": True,
      "compliant": compliant,
      "dominant_colors": [
        {"color": rgb_to_hex(c), "coverage": p}
        for c, p in dominant_colors
      ],
      "brand_matches": matches,
      "brand_color_coverage": round(total_coverage, 1),
      "average_similarity": round(avg_similarity, 1)
    }

  def validate_text_readability(self, image_path: Path) -> Dict:
    """
    Check text overlay meets readability standards.

    Args:
      image_path: Path to image file

    Returns:
      Dictionary with readability validation results
    """
    # Basic implementation: check if image has good contrast areas
    with Image.open(image_path) as img:
      if img.mode != 'RGB':
        img = img.convert('RGB')

      # Sample bottom portion where text usually is
      width, height = img.size
      bottom_region = img.crop((0, int(height * 0.7), width, height))

      # Calculate average brightness
      grayscale = bottom_region.convert('L')
      pixels = list(grayscale.getdata())
      avg_brightness = sum(pixels) / len(pixels)

      # Check if there's sufficient contrast potential
      # Dark background = good for white text
      # Light background = good for dark text
      # Widened range to be less strict - most brightnesses work with proper gradient scrim
      readable = avg_brightness < 130 or avg_brightness > 145

    return {
      "checked": True,
      "readable": readable,
      "text_area_brightness": round(avg_brightness, 1),
      "recommendation": "White text" if avg_brightness < 128 else "Dark text"
    }

  def validate_creative(self, image_path: Path) -> Dict:
    """
    Run full brand compliance validation.

    Args:
      image_path: Path to image file

    Returns:
      Complete compliance report
    """
    color_check = self.validate_colors(image_path)
    readability_check = self.validate_text_readability(image_path)

    # Calculate overall score
    score = 0
    max_score = 0

    # Color compliance (50 points)
    max_score += 50
    if color_check.get("checked"):
      if color_check.get("compliant"):
        score += 50
      else:
        # Partial credit based on coverage
        score += color_check.get("brand_color_coverage", 0) * 2.5

    # Readability (50 points)
    max_score += 50
    if readability_check.get("readable"):
      score += 50

    overall_score = round((score / max_score) * 100, 1) if max_score > 0 else 0
    compliant = overall_score >= 70  # 70% threshold

    return {
      "compliant": compliant,
      "overall_score": overall_score,
      "checks": {
        "colors": color_check,
        "readability": readability_check
      },
      "summary": self._generate_summary(overall_score, color_check, readability_check)
    }

  def validate_creative_split(self, pre_overlay_path: Path, final_path: Path) -> Dict:
    """
    Run split brand compliance validation.

    This method checks brand colors on the pre-overlay image (without gradient scrim)
    and text readability on the final image (with gradient scrim), giving us
    accurate compliance scores for both aspects.

    Args:
      pre_overlay_path: Path to image before text overlay (for color checking)
      final_path: Path to final image with overlay (for readability checking)

    Returns:
      Complete compliance report
    """
    # Check brand colors on the original image (no gradient interference)
    color_check = self.validate_colors(pre_overlay_path)

    # Check text readability on the final image (with gradient for contrast)
    readability_check = self.validate_text_readability(final_path)

    # Calculate overall score
    score = 0
    max_score = 0

    # Color compliance (50 points)
    max_score += 50
    if color_check.get("checked"):
      if color_check.get("compliant"):
        score += 50
      else:
        # Partial credit based on coverage
        score += color_check.get("brand_color_coverage", 0) * 2.5

    # Readability (50 points)
    max_score += 50
    if readability_check.get("readable"):
      score += 50

    overall_score = round((score / max_score) * 100, 1) if max_score > 0 else 0
    compliant = overall_score >= 70  # 70% threshold

    return {
      "compliant": compliant,
      "overall_score": overall_score,
      "checks": {
        "colors": color_check,
        "readability": readability_check
      },
      "summary": self._generate_summary(overall_score, color_check, readability_check)
    }

  def _generate_summary(self, score: float, color_check: Dict,
                        readability_check: Dict) -> str:
    """Generate human-readable summary."""
    if score >= 90:
      return "Excellent brand compliance"
    elif score >= 70:
      return "Good brand compliance"
    elif score >= 50:
      return "Acceptable - minor improvements needed"
    else:
      issues = []
      if not color_check.get("compliant"):
        issues.append("brand colors")
      if not readability_check.get("readable"):
        issues.append("text readability")
      return f"Needs improvement: {', '.join(issues)}"
