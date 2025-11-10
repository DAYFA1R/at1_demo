"""Test color name conversion for all example campaign colors."""

def rgb_to_hsl(r, g, b):
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


def hex_to_color_name_hsl(hex_color):
    """Convert hex color to descriptive name using HSL color space."""
    hex_color = hex_color.lstrip('#')

    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        h, s, l = rgb_to_hsl(r, g, b)

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

        # Determine base color name from hue
        # Hue wheel: Red=0, Orange=30, Yellow=60, Green=120, Cyan=180, Blue=240, Magenta=300
        if h < 15 or h >= 345:
            base_color = "red"
        elif h < 45:
            base_color = "orange"
        elif h < 70:
            base_color = "yellow"
        elif h < 150:
            base_color = "green"
        elif h < 200:
            base_color = "cyan"
        elif h < 260:
            base_color = "blue"
        elif h < 290:
            base_color = "purple"
        elif h < 330:
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
        if 30 < l < 70:
            if s > 80:
                modifiers.append("vibrant")
            elif s < 30:
                modifiers.append("muted")

        # Special cases for better DALL-E understanding
        if base_color == "magenta" and l > 50:
            base_color = "hot pink"
            modifiers = [m for m in modifiers if m not in ["light", "very light"]]
        elif base_color == "pink" and l > 60:
            if s > 70:
                base_color = "hot pink"
            else:
                base_color = "pale pink"
            modifiers = []
        elif base_color == "yellow" and 40 < l < 70:
            if 35 < h < 55:
                base_color = "golden yellow"
            modifiers = [m for m in modifiers if "dark" not in m]
        elif base_color == "cyan":
            if h < 180:
                base_color = "teal"
            else:
                base_color = "cyan"
        elif base_color == "orange" and s > 60 and 40 < l < 65:
            base_color = "burnt orange"
            modifiers = []
        elif base_color == "yellow" and h > 45 and l > 70:
            base_color = "golden"
            modifiers = []

        # Combine modifiers with base color
        if modifiers:
            return " ".join(modifiers) + " " + base_color
        return base_color

    except:
        return hex_color


# All colors from example campaigns
test_colors = [
    ("#000000", "Black"),
    ("#FFFFFF", "White"),
    ("#0066FF", "Blue"),
    ("#00FFCC", "Cyan/Turquoise"),
    ("#1a1a1a", "Very dark gray"),
    ("#00B894", "Teal/Green"),
    ("#6C5CE7", "Purple"),
    ("#FF0080", "Bright pink/magenta"),
    ("#7928CA", "Purple"),
    ("#0070F3", "Blue"),
    ("#C9A86A", "Tan/Beige/Gold"),
    ("#2C2C2C", "Dark gray"),
    ("#F5F5F5", "Light gray"),
    ("#D35400", "Orange"),
    ("#27AE60", "Green"),
    ("#F4D03F", "Yellow"),
    ("#E84393", "Pink"),
    ("#FD79A8", "Light pink"),
    ("#FDCB6E", "Golden yellow"),
]

print("HSL-based color name conversion for all example campaigns:\n")
print(f"{'Hex Color':<10} {'Expected':<25} {'Generated':<30}")
print("=" * 65)

for hex_color, expected in test_colors:
    generated = hex_to_color_name_hsl(hex_color)
    r = int(hex_color.lstrip('#')[0:2], 16)
    g = int(hex_color.lstrip('#')[2:4], 16)
    b = int(hex_color.lstrip('#')[4:6], 16)
    h, s, l = rgb_to_hsl(r, g, b)
    print(f"{hex_color:<10} {expected:<25} {generated:<30} (H:{h:3.0f} S:{s:3.0f} L:{l:3.0f})")
