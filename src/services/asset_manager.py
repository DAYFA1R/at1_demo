"""
Asset management service for finding, caching, and organizing assets.
"""

import os
import hashlib
from pathlib import Path
from typing import Optional, List
import shutil


class AssetManager:
  """Handles finding, caching, and organizing campaign assets."""

  def __init__(self, assets_dir: str = "./assets", cache_dir: str = "./.cache"):
    """
    Initialize the asset manager.

    Args:
      assets_dir: Directory containing existing assets
      cache_dir: Directory for caching generated assets
    """
    self.assets_dir = Path(assets_dir)
    self.cache_dir = Path(cache_dir)

    # Ensure directories exist
    self.assets_dir.mkdir(parents=True, exist_ok=True)
    self.cache_dir.mkdir(parents=True, exist_ok=True)

    # Track processed assets to avoid duplicates
    self._processed = set()

  def find_existing_asset(self, product_name: str, asset_paths: List[str]) -> Optional[Path]:
    """
    Find an existing asset for a product.

    Searches in the following order:
    1. Explicit paths provided in asset_paths
    2. Common naming patterns in assets directory

    Args:
      product_name: Name of the product
      asset_paths: List of explicit asset paths to check

    Returns:
      Path to the asset if found, None otherwise
    """
    # First check explicit paths
    for path_str in asset_paths:
      path = Path(path_str)

      # Try relative to assets dir if path doesn't exist as-is
      if not path.exists():
        path = self.assets_dir / path_str

      if path.exists() and self._is_valid_image(path):
        print(f"✓ Found existing asset for '{product_name}': {path}")
        return path

    # Fallback: search by product name patterns
    safe_name = product_name.lower().replace(' ', '_').replace('/', '_')
    search_patterns = [
      f"{safe_name}.*",
      f"*{safe_name}*",
    ]

    for pattern in search_patterns:
      matches = list(self.assets_dir.glob(f"**/{pattern}"))
      # Filter for valid image files
      valid_matches = [m for m in matches if self._is_valid_image(m)]

      if valid_matches:
        # Return first match
        asset_path = valid_matches[0]
        print(f"✓ Found asset via search for '{product_name}': {asset_path}")
        return asset_path

    print(f"✗ No existing assets found for '{product_name}'")
    return None

  def _is_valid_image(self, path: Path) -> bool:
    """
    Check if a file is a valid image based on extension.

    Args:
      path: Path to check

    Returns:
      True if file appears to be an image
    """
    if not path.is_file():
      return False

    valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    return path.suffix.lower() in valid_extensions

  def cache_asset(self, source_path: Path, product_name: str) -> Path:
    """
    Copy an asset to the cache directory.

    Args:
      source_path: Path to the source asset
      product_name: Name of the product (for organizing cache)

    Returns:
      Path to the cached asset
    """
    # Create a cache key based on product name and file content
    cache_key = self._get_cache_key(product_name, str(source_path))
    cached_filename = f"{cache_key}{source_path.suffix}"
    cached_path = self.cache_dir / cached_filename

    # Copy if not already cached
    if not cached_path.exists():
      shutil.copy2(source_path, cached_path)
      print(f"  Cached asset: {cached_path.name}")

    return cached_path

  def save_generated_asset(self, image_data: bytes, product_name: str, suffix: str = ".png") -> Path:
    """
    Save a generated asset to the cache.

    Args:
      image_data: Raw image data
      product_name: Name of the product
      suffix: File extension (default: .png)

    Returns:
      Path to the saved asset
    """
    import time

    # Create unique filename
    safe_name = product_name.lower().replace(' ', '_').replace('/', '_')
    timestamp = int(time.time())
    filename = f"generated_{safe_name}_{timestamp}{suffix}"

    output_path = self.cache_dir / filename

    with open(output_path, 'wb') as f:
      f.write(image_data)

    print(f"  Saved generated asset: {output_path.name}")
    return output_path

  def _get_cache_key(self, product_name: str, content: str) -> str:
    """
    Generate a cache key for consistent asset naming.

    Args:
      product_name: Name of the product
      content: Additional content for uniqueness

    Returns:
      12-character hash for cache key
    """
    content_str = f"{product_name}:{content}"
    return hashlib.md5(content_str.encode()).hexdigest()[:12]

  def organize_output(self, campaign_id: str, product_name: str,
                      aspect_ratio_name: str, source_path: Path,
                      output_dir: str = "./output") -> Path:
    """
    Copy an asset to its final organized location in the output directory.

    Args:
      campaign_id: ID of the campaign
      product_name: Name of the product
      aspect_ratio_name: Name of the aspect ratio (e.g., "1x1", "9x16")
      source_path: Path to the source asset
      output_dir: Base output directory

    Returns:
      Path to the organized asset
    """
    safe_product_name = product_name.lower().replace(' ', '_').replace('/', '_')

    # Create organized path: output/campaign_id/product_name/aspect_ratio/
    output_path = (
      Path(output_dir) /
      campaign_id /
      safe_product_name /
      aspect_ratio_name
    )
    output_path.mkdir(parents=True, exist_ok=True)

    # Determine output filename
    final_path = output_path / f"{aspect_ratio_name}.jpg"

    # Copy to final location
    shutil.copy2(source_path, final_path)

    return final_path

  def get_cache_stats(self) -> dict:
    """
    Get statistics about cached assets.

    Returns:
      Dictionary with cache statistics
    """
    if not self.cache_dir.exists():
      return {'total_files': 0, 'total_size_mb': 0}

    files = list(self.cache_dir.glob('*'))
    total_size = sum(f.stat().st_size for f in files if f.is_file())

    return {
      'total_files': len(files),
      'total_size_mb': round(total_size / (1024 * 1024), 2)
    }
