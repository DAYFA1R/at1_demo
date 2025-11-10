"""
Brand compliance validation for creative assets.
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import Counter

from PIL import Image
import colorsys


class BrandComplianceValidator:
  """Validates creative assets meet brand guidelines."""

  def __init__(self, brand_colors: Optional[List[str]] = None,
               logo_path: Optional[str] = None,
               color_tolerance: int = 30):
    """
    Initialize the brand compliance validator.

    Args:
      brand_colors: List of brand colors in hex format (e.g., ["#FF0000"])
      logo_path: Path to brand logo file
      color_tolerance: Color matching tolerance (0-100)
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
      # Remove # if present
      hex_color = hex_color.lstrip('#')
      # Convert to RGB
      try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        rgb_colors.append((r, g, b))
      except (ValueError, IndexError):
        # Skip invalid colors
        continue
    return rgb_colors

  def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex string."""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

  def _color_distance(self, color1: Tuple[int, int, int],
                      color2: Tuple[int, int, int]) -> float:
    """
    Calculate perceptual distance between two colors.

    Uses simple Euclidean distance in RGB space.

    Args:
      color1: First RGB color
      color2: Second RGB color

    Returns:
      Distance value (0-441, where 0 is identical)
    """
    return sum((a - b) ** 2 for a, b in zip(color1, color2)) ** 0.5

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

    # Get all pixels
    pixels = list(img.getdata())

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
    matches = []
    for dom_color, percentage in dominant_colors:
      for brand_color in self.brand_colors:
        distance = self._color_distance(dom_color, brand_color)
        # Normalize distance to 0-100 scale
        similarity = max(0, 100 - (distance / 4.41))

        if similarity >= (100 - self.color_tolerance):
          matches.append({
            "image_color": self._rgb_to_hex(dom_color),
            "brand_color": self._rgb_to_hex(brand_color),
            "similarity": round(similarity, 1),
            "coverage": percentage
          })

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
        {"color": self._rgb_to_hex(c), "coverage": p}
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
      readable = avg_brightness < 100 or avg_brightness > 180

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
