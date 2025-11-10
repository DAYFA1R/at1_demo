"""
Main orchestration pipeline for campaign creative generation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from PIL import Image
import io

from ..models.campaign import CampaignBrief, Product
from ..services.asset_manager import AssetManager
from ..services.image_generator import ImageGenerator
from ..processors.creative_composer import CreativeComposer


class CampaignPipeline:
  """Orchestrates the entire campaign creative generation process."""

  def __init__(self, output_dir: str = "./output"):
    """
    Initialize the campaign pipeline.

    Args:
      output_dir: Base directory for output files
    """
    self.output_dir = Path(output_dir)
    self.output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize services
    self.asset_manager = AssetManager()
    self.image_generator = ImageGenerator()
    self.composer = CreativeComposer()

    # Report data for tracking
    self.report_data = {
      "start_time": datetime.now().isoformat(),
      "products_processed": [],
      "assets_generated": 0,
      "assets_reused": 0,
      "variations_created": 0,
      "errors": []
    }

  def process_campaign(self, brief: CampaignBrief) -> Dict[str, Any]:
    """
    Process an entire campaign brief.

    Args:
      brief: Campaign brief to process

    Returns:
      Report data dictionary with results
    """
    print(f"\n{'='*70}")
    print(f"  Processing Campaign: {brief.campaign_id}")
    print(f"{'='*70}\n")

    print(f"Target Region: {brief.target_region}")
    print(f"Target Audience: {brief.target_audience}")
    print(f"Campaign Message: {brief.campaign_message}")
    print(f"Products: {brief.get_product_count()}\n")

    campaign_output = self.output_dir / brief.campaign_id
    campaign_output.mkdir(parents=True, exist_ok=True)

    # Process each product
    for idx, product in enumerate(brief.products, 1):
      print(f"\n[{idx}/{len(brief.products)}] Processing: {product.name}")
      print(f"{'─'*70}")

      try:
        self._process_product(product, brief, campaign_output)
      except Exception as e:
        error_msg = f"Failed to process {product.name}: {str(e)}"
        print(f"\n❌ {error_msg}\n")
        self.report_data["errors"].append(error_msg)

    # Generate report
    self._generate_report(campaign_output, brief)

    return self.report_data

  def _process_product(self, product: Product, brief: CampaignBrief,
                       output_dir: Path) -> None:
    """
    Process a single product within a campaign.

    Args:
      product: Product to process
      brief: Campaign brief for context
      output_dir: Output directory for this campaign
    """
    print(f"Description: {product.description}")

    # Step 1: Get base asset (existing or generated)
    asset_path = self._get_or_generate_asset(product, brief)

    if not asset_path:
      raise ValueError(f"Could not obtain asset for {product.name}")

    # Step 2: Create variations for all aspect ratios
    print(f"\n📐 Creating aspect ratio variations...")

    product_output = output_dir / product.get_safe_name()

    with Image.open(asset_path) as img:
      if img.mode != 'RGB':
        img = img.convert('RGB')

      variations = self.composer.create_variations(
        img,
        brief.campaign_message,
        product_output,
        product.name
      )

    # Track results
    self.report_data["variations_created"] += len(variations)
    self.report_data["products_processed"].append({
      "name": product.name,
      "source": "existing" if product.has_existing_assets() else "generated",
      "variations": list(variations.keys()),
      "output_path": str(product_output)
    })

    print(f"\n✅ Completed {product.name}")

  def _get_or_generate_asset(self, product: Product, brief: CampaignBrief) -> Path:
    """
    Get an asset for a product - either existing or newly generated.

    Args:
      product: Product to get asset for
      brief: Campaign brief for context

    Returns:
      Path to the asset
    """
    # Try to find existing asset
    asset_path = self.asset_manager.find_existing_asset(
      product.name,
      product.existing_assets
    )

    if asset_path:
      print(f"📁 Using existing asset")
      self.report_data["assets_reused"] += 1
      return asset_path

    # Generate new asset
    print(f"🎨 No existing asset found - generating with DALL-E...")

    image_data = self.image_generator.generate_for_product(product, brief)

    if not image_data:
      raise ValueError(f"Failed to generate image for {product.name}")

    # Save generated asset
    generated_path = self.asset_manager.save_generated_asset(
      image_data,
      product.name,
      suffix=".png"
    )

    self.report_data["assets_generated"] += 1
    return generated_path

  def _generate_report(self, output_dir: Path, brief: CampaignBrief) -> None:
    """
    Generate a JSON report of the campaign processing.

    Args:
      output_dir: Directory to save report
      brief: Campaign brief that was processed
    """
    self.report_data["end_time"] = datetime.now().isoformat()

    # Calculate duration
    start = datetime.fromisoformat(self.report_data["start_time"])
    end = datetime.fromisoformat(self.report_data["end_time"])
    duration = (end - start).total_seconds()
    self.report_data["duration_seconds"] = round(duration, 2)

    # Add summary statistics
    total_products = len(self.report_data["products_processed"])
    successful_products = total_products - len(self.report_data["errors"])

    self.report_data["summary"] = {
      "campaign_id": brief.campaign_id,
      "total_products": total_products,
      "successful_products": successful_products,
      "total_variations": self.report_data["variations_created"],
      "assets_generated": self.report_data["assets_generated"],
      "assets_reused": self.report_data["assets_reused"],
      "success_rate": f"{(successful_products / max(1, total_products) * 100):.1f}%",
      "duration_seconds": self.report_data["duration_seconds"]
    }

    # Save report
    report_path = output_dir / "campaign_report.json"
    with open(report_path, 'w') as f:
      json.dump(self.report_data, f, indent=2)

    print(f"\n{'='*70}")
    print(f"  Campaign Processing Complete!")
    print(f"{'='*70}")
    print(f"\n📊 Summary:")
    print(f"   Products Processed: {successful_products}/{total_products}")
    print(f"   Variations Created: {self.report_data['variations_created']}")
    print(f"   Assets Generated: {self.report_data['assets_generated']}")
    print(f"   Assets Reused: {self.report_data['assets_reused']}")
    print(f"   Duration: {self.report_data['duration_seconds']}s")

    if self.report_data["errors"]:
      print(f"\n⚠️  Errors: {len(self.report_data['errors'])}")
      for error in self.report_data["errors"]:
        print(f"   - {error}")

    print(f"\n📁 Output: {output_dir}")
    print(f"📄 Report: {report_path}\n")
