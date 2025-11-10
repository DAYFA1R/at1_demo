"""Debug script to analyze color detection in pre-overlay vs final images."""

from pathlib import Path
from PIL import Image
from src.validators.brand_compliance import BrandComplianceValidator

# Brand colors from beauty_middle_east campaign
BRAND_COLORS = ["#E84393", "#FD79A8", "#FDCB6E"]

# Test files
CAMPAIGN_DIR = Path("output/campaign_e2304a47/campaign_e2304a47/argan_oil_serum/en")
PRE_OVERLAY = CAMPAIGN_DIR / ".1x1_pre_overlay.jpg"
FINAL = CAMPAIGN_DIR / "1x1.jpg"

print("=" * 80)
print("COLOR DETECTION DEBUG")
print("=" * 80)
print(f"\nBrand colors: {BRAND_COLORS}")
print(f"\nPre-overlay file: {PRE_OVERLAY}")
print(f"Final file: {FINAL}")

# Initialize validator
validator = BrandComplianceValidator(brand_colors=BRAND_COLORS)

print("\n" + "=" * 80)
print("ANALYZING PRE-OVERLAY IMAGE (without gradient)")
print("=" * 80)

# Check pre-overlay
if PRE_OVERLAY.exists():
    pre_result = validator.validate_colors(PRE_OVERLAY)
    print(f"\nChecked: {pre_result.get('checked')}")
    print(f"Compliant: {pre_result.get('compliant')}")
    print(f"Brand color coverage: {pre_result.get('brand_color_coverage')}%")
    print(f"Average similarity: {pre_result.get('average_similarity')}%")

    print("\nDominant colors detected:")
    for color_info in pre_result.get('dominant_colors', []):
        print(f"  {color_info['color']}: {color_info['coverage']}%")

    print("\nBrand color matches:")
    for match in pre_result.get('brand_matches', []):
        print(f"  Image color {match['image_color']} matches brand {match['brand_color']}")
        print(f"    Similarity: {match['similarity']}%, Coverage: {match['coverage']}%")
else:
    print("ERROR: Pre-overlay file not found!")

print("\n" + "=" * 80)
print("ANALYZING FINAL IMAGE (with gradient)")
print("=" * 80)

# Check final
if FINAL.exists():
    final_result = validator.validate_colors(FINAL)
    print(f"\nChecked: {final_result.get('checked')}")
    print(f"Compliant: {final_result.get('compliant')}")
    print(f"Brand color coverage: {final_result.get('brand_color_coverage')}%")
    print(f"Average similarity: {final_result.get('average_similarity')}%")

    print("\nDominant colors detected:")
    for color_info in final_result.get('dominant_colors', []):
        print(f"  {color_info['color']}: {color_info['coverage']}%")

    print("\nBrand color matches:")
    for match in final_result.get('brand_matches', []):
        print(f"  Image color {match['image_color']} matches brand {match['brand_color']}")
        print(f"    Similarity: {match['similarity']}%, Coverage: {match['coverage']}%")
else:
    print("ERROR: Final file not found!")

print("\n" + "=" * 80)
print("EXTRACTING RAW COLORS FROM PRE-OVERLAY IMAGE")
print("=" * 80)

# Get raw dominant colors directly
if PRE_OVERLAY.exists():
    with Image.open(PRE_OVERLAY) as img:
        dominant = validator.extract_dominant_colors(img, count=10)
        print("\nTop 10 dominant colors:")
        for color_rgb, percentage in dominant:
            hex_color = validator._rgb_to_hex(color_rgb)
            print(f"  {hex_color} (RGB{color_rgb}): {percentage}%")

            # Check distance to each brand color
            for brand_hex in BRAND_COLORS:
                brand_rgb = validator._hex_to_rgb([brand_hex])[0]
                distance = validator._color_distance(color_rgb, brand_rgb)
                similarity = max(0, 100 - (distance / 4.41))
                if similarity >= 70:  # Only show close matches
                    print(f"    -> {similarity:.1f}% similar to brand color {brand_hex}")

print("\n" + "=" * 80)
