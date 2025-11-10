"""
Main orchestration pipeline for campaign creative generation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from PIL import Image

from ..models.campaign import CampaignBrief, Product
from ..services.asset_manager import AssetManager
from ..services.image_generator import ImageGenerator
from ..processors.creative_composer import CreativeComposer
from ..validators.content_moderator import ContentModerator
from ..validators.brand_compliance import BrandComplianceValidator
from ..services.creative_copywriter import CreativeCopywriter


class CampaignPipeline:
  """Orchestrates the entire campaign creative generation process."""

  def __init__(self, output_dir: str = "./output", enable_copywriting: bool = True):
    """
    Initialize the campaign pipeline.

    Args:
      output_dir: Base directory for output files
      enable_copywriting: Enable AI copywriting optimization
    """
    self.output_dir = Path(output_dir)
    self.output_dir.mkdir(parents=True, exist_ok=True)
    self.enable_copywriting = enable_copywriting

    # Initialize services
    self.asset_manager = AssetManager()
    self.image_generator = ImageGenerator()
    self.composer = CreativeComposer()
    self.content_moderator = ContentModerator()
    self.brand_validator = None  # Initialized per campaign with brand colors
    self.copywriter = CreativeCopywriter() if enable_copywriting else None

    # Report data for tracking
    self.report_data = {
      "start_time": datetime.now().isoformat(),
      "products_processed": [],
      "assets_generated": 0,
      "assets_reused": 0,
      "variations_created": 0,
      "errors": [],
      "warnings": [],
      "content_moderation": {},
      "compliance_summary": {}
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

    # Step 1: AI Copywriting optimization (if enabled)
    if self.copywriter and self.enable_copywriting:
      print("✍️  Generating optimized campaign messages...")
      try:
        copy_results = self.copywriter.generate_campaign_copy(brief)
        self.report_data["copywriting"] = copy_results

        # Show original vs optimized
        print(f"   📝 Original: {brief.campaign_message}")
        print(f"   🎯 Optimized: {copy_results['selected_message']}")

        # Show confidence
        confidence = copy_results.get('confidence_score', 0.5)
        print(f"   📊 Confidence: {confidence:.1%}")

        # Show variants if available
        if copy_results.get('optimization', {}).get('variants'):
          print(f"\n   Alternative variants:")
          for i, variant in enumerate(copy_results['optimization']['variants'][:2], 1):
            print(f"   {i}. {variant['text']}")
            print(f"      → {variant.get('reasoning', 'N/A')}")

        # Update brief with optimized message
        original_message = brief.campaign_message
        brief.campaign_message = copy_results['selected_message']
        self.report_data["copywriting"]["original_message"] = original_message

        print(f"\n   ✓ Using optimized message for campaign")
        print()

      except Exception as e:
        print(f"   ⚠️  Copywriting optimization failed: {e}")
        print(f"   → Using original message")
        self.report_data["warnings"].append(f"Copywriting failed: {str(e)}")
        print()

    # Step 2: Content moderation check
    print("🔍 Running content moderation...")
    moderation_result = self.content_moderator.check_campaign_message(
      brief.campaign_message,
      region=brief.target_region
    )
    self.report_data["content_moderation"] = moderation_result

    if not moderation_result["approved"]:
      error_msg = f"Content moderation failed: {len(moderation_result['violations'])} violations"
      print(f"❌ {error_msg}")
      for violation in moderation_result["violations"]:
        print(f"   - {violation['type']}: {violation.get('word', violation.get('term', 'unknown'))}")
      self.report_data["errors"].append(error_msg)

      # Create campaign output dir before generating report
      campaign_output = self.output_dir / brief.campaign_id
      campaign_output.mkdir(parents=True, exist_ok=True)
      self._generate_report(campaign_output, brief)
      return self.report_data

    if moderation_result["warnings"]:
      print(f"⚠️  Content warnings: {len(moderation_result['warnings'])}")
      for warning in moderation_result["warnings"]:
        warn_msg = f"{warning['category']}: {warning['term']}"
        print(f"   - {warn_msg}")
        self.report_data["warnings"].append(warn_msg)

    print(f"✓ Content approved (Risk: {moderation_result['risk_level']})\n")

    # Step 3: Initialize brand validator
    if brief.brand_colors:
      self.brand_validator = BrandComplianceValidator(
        brand_colors=brief.brand_colors,
        logo_path=brief.logo_path
      )
      print(f"✓ Brand compliance checking enabled\n")

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

    # Step 3: Brand compliance check
    compliance_results = {}
    if self.brand_validator:
      print(f"\n🎨 Checking brand compliance...")
      for name, path in variations.items():
        compliance = self.brand_validator.validate_creative(path)
        compliance_results[name] = compliance

        if compliance["overall_score"] < 70:
          warn_msg = f"{product.name}/{name}: Low compliance score {compliance['overall_score']}"
          self.report_data["warnings"].append(warn_msg)
          print(f"  ⚠️  {name}: {compliance['summary']} (Score: {compliance['overall_score']})")
        else:
          print(f"  ✓ {name}: {compliance['summary']} (Score: {compliance['overall_score']})")

    # Track results
    self.report_data["variations_created"] += len(variations)
    product_data = {
      "name": product.name,
      "source": "existing" if product.has_existing_assets() else "generated",
      "variations": list(variations.keys()),
      "output_path": str(product_output)
    }

    if compliance_results:
      product_data["compliance"] = compliance_results

    self.report_data["products_processed"].append(product_data)

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

    # Calculate compliance summary
    if self.brand_validator:
      compliance_scores = []
      for product in self.report_data["products_processed"]:
        if "compliance" in product:
          for ratio_compliance in product["compliance"].values():
            compliance_scores.append(ratio_compliance["overall_score"])

      if compliance_scores:
        avg_compliance = sum(compliance_scores) / len(compliance_scores)
        self.report_data["compliance_summary"] = {
          "enabled": True,
          "average_score": round(avg_compliance, 1),
          "total_checks": len(compliance_scores),
          "all_compliant": all(score >= 70 for score in compliance_scores)
        }

    self.report_data["summary"] = {
      "campaign_id": brief.campaign_id,
      "total_products": total_products,
      "successful_products": successful_products,
      "total_variations": self.report_data["variations_created"],
      "assets_generated": self.report_data["assets_generated"],
      "assets_reused": self.report_data["assets_reused"],
      "success_rate": f"{(successful_products / max(1, total_products) * 100):.1f}%",
      "duration_seconds": self.report_data["duration_seconds"],
      "total_warnings": len(self.report_data["warnings"])
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
