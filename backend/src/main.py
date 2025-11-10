#!/usr/bin/env python3
"""
Main entry point for the Creative Automation Pipeline.
"""

import argparse
import json
import sys
from pathlib import Path
import logging

import yaml
from dotenv import load_dotenv

from .models.campaign import CampaignBrief
from .pipeline.orchestrator import CampaignPipeline


def setup_logging(verbose: bool = False):
  """
  Configure logging for the application.

  Args:
    verbose: Enable debug logging if True
  """
  level = logging.DEBUG if verbose else logging.INFO
  logging.basicConfig(
    level=level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
      logging.FileHandler('pipeline.log'),
      logging.StreamHandler()
    ]
  )


def load_brief(brief_path: Path) -> dict:
  """
  Load a campaign brief from JSON or YAML file.

  Args:
    brief_path: Path to the brief file

  Returns:
    Dictionary containing brief data

  Raises:
    ValueError: If file format is not supported
  """
  if not brief_path.exists():
    raise FileNotFoundError(f"Brief file not found: {brief_path}")

  with open(brief_path) as f:
    if brief_path.suffix in ['.yaml', '.yml']:
      return yaml.safe_load(f)
    elif brief_path.suffix == '.json':
      return json.load(f)
    else:
      raise ValueError(f"Unsupported file format: {brief_path.suffix}")


def main():
  """Main entry point."""
  parser = argparse.ArgumentParser(
    description='Creative Automation Pipeline for Social Campaigns',
    epilog='Example: python -m src.main examples/sample_campaign.json'
  )

  parser.add_argument(
    'brief',
    help='Path to campaign brief (JSON or YAML)'
  )

  parser.add_argument(
    '-o', '--output',
    default='./output',
    help='Output directory (default: ./output)'
  )

  parser.add_argument(
    '-v', '--verbose',
    action='store_true',
    help='Enable verbose logging'
  )

  parser.add_argument(
    '--version',
    action='version',
    version='Creative Automation Pipeline v1.0.0'
  )

  args = parser.parse_args()

  # Setup
  load_dotenv()
  setup_logging(args.verbose)

  try:
    print("\n🚀 Creative Automation Pipeline")
    print("=" * 70)

    # Load campaign brief
    print(f"\n📋 Loading campaign brief: {args.brief}")
    brief_data = load_brief(Path(args.brief))
    brief = CampaignBrief.from_dict(brief_data)

    print(f"✓ Brief loaded successfully")

    # Run pipeline
    pipeline = CampaignPipeline(output_dir=args.output)
    report = pipeline.process_campaign(brief)

    # Exit with success
    sys.exit(0)

  except KeyboardInterrupt:
    print("\n\n🛑 Pipeline interrupted by user")
    sys.exit(130)

  except FileNotFoundError as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)

  except ValueError as e:
    print(f"\n❌ Invalid input: {e}")
    sys.exit(1)

  except Exception as e:
    logging.exception("Pipeline failed")
    print(f"\n❌ Pipeline failed: {str(e)}")
    print("   Check pipeline.log for details")
    sys.exit(1)


if __name__ == "__main__":
  main()
