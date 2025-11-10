"""Debug script to test brand compliance validation."""

from pathlib import Path
from src.validators.brand_compliance import BrandComplianceValidator

# Brand colors from fitness_asia_pacific.json
brand_colors = ["#00B894", "#6C5CE7", "#FFFFFF"]

# Create validator with new default tolerance
print("Testing with tolerance=25 (NEW default, requires 75% similarity)")
validator_new = BrandComplianceValidator(brand_colors=brand_colors, color_tolerance=25)

# Test image
test_image = Path("output/campaign_cf103492/campaign_cf103492/bamboo_yoga_mat/ja/1x1.jpg")

if test_image.exists():
    print(f"\n{'='*70}")
    print(f"Testing image: {test_image}")
    print(f"{'='*70}")

    print("\n--- WITH COLOR QUANTIZATION (grouping similar colors) ---")
    result = validator_new.validate_colors(test_image)
    print(f"Brand color coverage: {result['brand_color_coverage']}%")
    print(f"Average similarity: {result.get('average_similarity', 0)}%")
    print(f"Matches found: {len(result['brand_matches'])}")
    print(f"Compliant: {result.get('compliant', False)}")

    print("\nDominant colors in image (after quantization):")
    for color_info in result['dominant_colors'][:10]:
        print(f"  {color_info['color']} - {color_info['coverage']}%")

    print("\nBrand color matches:")
    for match in result['brand_matches']:
        print(f"  Image: {match['image_color']} → Brand: {match['brand_color']}")
        print(f"    Similarity: {match['similarity']}%, Coverage: {match['coverage']}%")

else:
    print(f"Image not found: {test_image}")
