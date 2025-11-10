"""
Data models for campaign briefs and related entities.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from enum import Enum
from pathlib import Path


class AspectRatio(Enum):
  """Social media aspect ratios with their dimensions."""

  SQUARE = ("1x1", (1, 1), (1080, 1080))
  PORTRAIT = ("9x16", (9, 16), (1080, 1920))
  LANDSCAPE = ("16x9", (16, 9), (1920, 1080))

  def __init__(self, name: str, ratio: Tuple[int, int], dimensions: Tuple[int, int]):
    self._name = name
    self._ratio = ratio
    self._dimensions = dimensions

  @property
  def display_name(self) -> str:
    """Human-readable name for the aspect ratio."""
    return self._name

  @property
  def ratio(self) -> Tuple[int, int]:
    """The aspect ratio as a tuple (width, height)."""
    return self._ratio

  @property
  def dimensions(self) -> Tuple[int, int]:
    """Target pixel dimensions (width, height)."""
    return self._dimensions

  @classmethod
  def all(cls) -> List['AspectRatio']:
    """Get all available aspect ratios."""
    return [cls.SQUARE, cls.PORTRAIT, cls.LANDSCAPE]


@dataclass
class Product:
  """Represents a product in a campaign."""

  name: str
  description: str
  existing_assets: List[str] = field(default_factory=list)

  # Track generated assets during processing
  generated_assets: Dict[str, str] = field(default_factory=dict)

  def has_existing_assets(self) -> bool:
    """Check if product has any existing assets."""
    return len(self.existing_assets) > 0

  def get_safe_name(self) -> str:
    """Get a filesystem-safe version of the product name."""
    return self.name.lower().replace(' ', '_').replace('/', '_')

  @classmethod
  def from_dict(cls, data: dict) -> 'Product':
    """Create a Product instance from a dictionary."""
    return cls(
      name=data['name'],
      description=data['description'],
      existing_assets=data.get('existing_assets', [])
    )


@dataclass
class CampaignBrief:
  """Represents a complete campaign brief with all requirements."""

  campaign_id: str
  products: List[Product]
  target_region: str
  target_audience: str
  campaign_message: str

  # Optional brand configuration
  brand_colors: List[str] = field(default_factory=list)
  logo_path: Optional[str] = None

  def __post_init__(self):
    """Validate the campaign brief after initialization."""
    if not self.campaign_id:
      raise ValueError("campaign_id is required")

    if not self.products or len(self.products) < 2:
      raise ValueError("At least 2 products are required")

    if not self.campaign_message:
      raise ValueError("campaign_message is required")

  def get_product_count(self) -> int:
    """Get the number of products in this campaign."""
    return len(self.products)

  def get_output_path(self, base_dir: str = "./output") -> Path:
    """Get the output directory path for this campaign."""
    return Path(base_dir) / self.campaign_id

  @classmethod
  def from_dict(cls, data: dict) -> 'CampaignBrief':
    """
    Create a CampaignBrief instance from a dictionary.

    Args:
      data: Dictionary containing campaign brief data

    Returns:
      CampaignBrief instance

    Raises:
      ValueError: If required fields are missing
    """
    # Parse products
    products_data = data.get('products', [])
    products = [Product.from_dict(p) for p in products_data]

    return cls(
      campaign_id=data.get('campaign_id', ''),
      products=products,
      target_region=data.get('target_region', ''),
      target_audience=data.get('target_audience', ''),
      campaign_message=data.get('campaign_message', ''),
      brand_colors=data.get('brand_colors', []),
      logo_path=data.get('logo_path')
    )

  def to_dict(self) -> dict:
    """Convert the campaign brief back to a dictionary."""
    return {
      'campaign_id': self.campaign_id,
      'products': [
        {
          'name': p.name,
          'description': p.description,
          'existing_assets': p.existing_assets,
        }
        for p in self.products
      ],
      'target_region': self.target_region,
      'target_audience': self.target_audience,
      'campaign_message': self.campaign_message,
      'brand_colors': self.brand_colors,
      'logo_path': self.logo_path
    }
