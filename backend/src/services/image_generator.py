"""
Image generation service using OpenAI's DALL-E API.
"""

import os
import time
from pathlib import Path
from typing import Optional
import requests
from openai import OpenAI

from ..models.campaign import Product, CampaignBrief


class ImageGenerator:
  """Handles AI-powered image generation using DALL-E."""

  def __init__(self, api_key: Optional[str] = None):
    """
    Initialize the image generator.

    Args:
      api_key: OpenAI API key (if not provided, reads from env)

    Raises:
      ValueError: If no API key is available
    """
    self.api_key = api_key or os.getenv('OPENAI_API_KEY')

    if not self.api_key:
      raise ValueError(
        "OpenAI API key required! Set OPENAI_API_KEY environment variable "
        "or pass api_key parameter"
      )

    self.client = OpenAI(api_key=self.api_key)

    # Configuration
    self.model = os.getenv('DALLE_MODEL', 'dall-e-3')
    self.quality = os.getenv('DALLE_QUALITY', 'standard')
    self.size = os.getenv('DALLE_SIZE', '1024x1024')

    # Rate limiting to avoid hitting API limits
    self._last_request_time = 0
    self._min_request_interval = 2  # seconds between requests

  def _rgb_to_hsl(self, r: int, g: int, b: int) -> tuple:
    """Convert RGB to HSL color space."""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    diff = max_val - min_val

    # Lightness
    l = (max_val + min_val) / 2.0

    if diff == 0:
      h = s = 0  # achromatic
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

  def _hex_to_color_name(self, hex_color: str) -> str:
    """
    Convert hex color to descriptive color name for better DALL-E understanding.
    Uses HSL color space for robust color categorization.

    Args:
      hex_color: Hex color code (e.g., "#FF0000")

    Returns:
      Color description string
    """
    # Remove # if present
    hex_color = hex_color.lstrip('#')

    try:
      # Convert to RGB
      r = int(hex_color[0:2], 16)
      g = int(hex_color[2:4], 16)
      b = int(hex_color[4:6], 16)

      # Convert to HSL for better color categorization
      h, s, l = self._rgb_to_hsl(r, g, b)

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

    except:
      return hex_color

  def build_prompt(self, product: Product, brief: CampaignBrief) -> str:
    """
    Build an effective DALL-E prompt for product image generation.

    Args:
      product: Product to generate image for
      brief: Campaign brief with context

    Returns:
      Optimized prompt string
    """
    prompt_parts = []

    # Brand colors MUST BE FIRST AND DOMINANT if specified
    if brief.brand_colors and len(brief.brand_colors) > 0:
      # Convert hex to color names for better DALL-E understanding
      color_names = [self._hex_to_color_name(c) for c in brief.brand_colors[:2]]
      primary_color = color_names[0]
      secondary_color = color_names[1] if len(color_names) > 1 else primary_color

      # Make colors THE PRIMARY FOCUS
      prompt_parts.append(f"{primary_color} and {secondary_color} colored product photography")
      prompt_parts.append(f"{product.description} on {primary_color} background")
      prompt_parts.append(f"vibrant {primary_color} and {secondary_color} color palette")
      prompt_parts.append(f"bold {primary_color} tones dominating the image")
    else:
      # No brand colors specified
      prompt_parts.append(f"Professional product photography of {product.description}")

    # Style guidance (secondary to colors)
    prompt_parts.append("clean, modern composition")
    prompt_parts.append("well-lit, high quality")
    prompt_parts.append("social media advertising style")

    # Target audience context (minimal)
    if brief.target_audience:
      prompt_parts.append(f"appealing to {brief.target_audience}")

    # Combine into final prompt
    prompt = ", ".join(prompt_parts)

    # DALL-E 3 has a 4000 character limit, but keep it concise
    if len(prompt) > 1000:
      prompt = prompt[:1000]

    return prompt

  def generate(self, prompt: str, product_name: str) -> Optional[bytes]:
    """
    Generate an image using DALL-E.

    Args:
      prompt: The generation prompt
      product_name: Name of product (for logging)

    Returns:
      Raw image bytes if successful, None otherwise
    """
    # Rate limiting
    self._enforce_rate_limit()

    try:
      print(f"🎨 Generating image for '{product_name}'...")
      print(f"   Prompt: {prompt[:80]}...")

      # Call DALL-E API
      response = self.client.images.generate(
        model=self.model,
        prompt=prompt,
        size=self.size,
        quality=self.quality,
        n=1
      )

      # Get image URL from response
      image_url = response.data[0].url

      # Download the image
      print(f"   Downloading generated image...")
      image_response = requests.get(image_url, timeout=30)
      image_response.raise_for_status()

      image_data = image_response.content

      print(f"✓ Successfully generated image for '{product_name}' ({len(image_data)} bytes)")

      self._last_request_time = time.time()
      return image_data

    except Exception as e:
      print(f"✗ Generation failed for '{product_name}': {str(e)}")
      return None

  def generate_for_product(self, product: Product, brief: CampaignBrief) -> Optional[bytes]:
    """
    Generate an image for a specific product within a campaign.

    Args:
      product: Product to generate image for
      brief: Campaign brief with context

    Returns:
      Raw image bytes if successful, None otherwise
    """
    prompt = self.build_prompt(product, brief)
    return self.generate(prompt, product.name)

  def _enforce_rate_limit(self):
    """Enforce rate limiting between API requests."""
    time_since_last = time.time() - self._last_request_time

    if time_since_last < self._min_request_interval:
      sleep_time = self._min_request_interval - time_since_last
      print(f"   Rate limiting: waiting {sleep_time:.1f}s...")
      time.sleep(sleep_time)

  def test_connection(self) -> bool:
    """
    Test the connection to OpenAI API.

    Returns:
      True if connection successful, False otherwise
    """
    try:
      # Try to list models as a connection test
      self.client.models.list()
      print("✓ OpenAI API connection successful")
      return True
    except Exception as e:
      print(f"✗ OpenAI API connection failed: {str(e)}")
      return False
