# Creative Automation Pipeline for Social Campaigns

A proof-of-concept tool that automates creative asset generation for social ad campaigns with DALL-E.

## Project Structure

```
creative-automation-pipeline/
├── src/
│   ├── models/          # Data models (Campaign, Product, AspectRatio)
│   ├── services/        # Asset management and GenAI services
│   ├── processors/      # Image processing and composition
│   ├── pipeline/        # Main orchestration logic
│   └── utils/           # Utility functions
├── config/              # Configuration files
├── assets/              # Input assets and brand resources
│   ├── templates/       # Template assets
│   └── brand/          # Brand logos, fonts, etc.
├── examples/            # Example campaign briefs
├── output/              # Generated campaign assets
└── .cache/             # Temporary generated assets

```

## Setup

1. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

## Usage

### Basic Usage

Run the pipeline with a campaign brief:

```bash
python -m src.main examples/sample_campaign.json
```

**With custom output directory:**
```bash
python -m src.main examples/sample_campaign.json -o ./my_output
```

**With verbose logging:**
```bash
python -m src.main examples/sample_campaign.json -v
```

### Campaign Brief Format

The pipeline supports both JSON and YAML formats.

**Example JSON** (`examples/sample_campaign.json`):
```json
{
  "campaign_id": "holiday_2024",
  "products": [
    {
      "name": "Premium Coffee Blend",
      "description": "Artisan roasted coffee beans",
      "existing_assets": ["products/coffee.jpg"]
    }
  ],
  "target_region": "North America",
  "target_audience": "Health-conscious millennials aged 25-40",
  "campaign_message": "Discover your perfect morning ritual",
  "brand_colors": ["#2E7D32", "#FFFFFF"],
  "logo_path": null
}
```

**Example YAML** (`examples/sample_campaign.yaml`):
```yaml
campaign_id: summer_2024
products:
  - name: Premium Protein Powder
    description: Plant-based protein powder
    existing_assets: []
target_region: Europe
target_audience: Active lifestyle enthusiasts aged 20-35
campaign_message: Fuel your journey with natural energy
```

### Example Campaigns

- `examples/sample_campaign.json` - Basic campaign (generates both products)
- `examples/sample_campaign.yaml` - YAML format example
- `examples/campaign_with_assets.json` - Mix of existing and generated assets
- `examples/test_moderation_fail.json` - Campaign contains failing guidelines

## Features

### Core Features
- **Multi-product support** - Process 2+ products per campaign
- **Asset management** - Reuse existing assets or generate new ones with DALL-E
- **Multiple formats** - Create 3 aspect ratios (1:1, 9:16, 16:9)
- **Text overlays** - Automatic campaign message placement
- **Smart prompts** - Context-aware generation based on region and audience
- **JSON/YAML support** - Flexible campaign brief formats
- **Detailed reporting** - JSON reports with processing statistics

### Quality & Compliance
- **Content moderation** - Automatically checks campaign messages for prohibited words and regulated terms
- **Brand compliance** - Validates generated creatives against brand color palette and readability standards
- **Risk assessment** - Categorizes content as low/medium/high risk
- **Compliance scoring** - Scores each creative 0-100 for brand alignment

### AI-Powered Optimization
- **Message optimization** - Uses GPT-4 to optimize campaign messages for target audiences
- **Persona analysis** - Extracts values and emotional triggers from audience demographics
- **A/B test variants** - Generates multiple message approaches for testing
- **Localization** - Automatically translates and culturally adapts messages for different regions
- **Multi-language export** - Creates separate image sets with localized text for each language

## Content Moderation & Brand Compliance

The pipeline automatically validates all campaigns for quality and compliance:

**Content Moderation:**
- Checks campaign messages before generation
- Blocks prohibited words (e.g., "guaranteed", "miracle", "no-risk")
- Warns on regulated terms requiring disclaimers (e.g., health claims, superlatives)
- Stops pipeline if violations detected, saving API costs

**Brand Compliance:**
- Validates brand color usage in generated creatives
- Checks text readability and contrast
- Scores each creative 0-100 for compliance
- Provides actionable feedback in reports

To enable brand compliance, include `brand_colors` in your campaign brief:
```json
{
  "brand_colors": ["#2E7D32", "#FFFFFF"],
  "logo_path": "assets/brand/logo.png"
}
```

## AI Copywriting & Localization

The pipeline automatically optimizes messages and creates localized versions:

**Message Optimization:**
- Analyzes target audience demographics and psychographics
- Generates messages that appeal to audience values and emotional triggers
- Adapts tone for regional preferences (e.g., sophisticated for Europe, direct for North America)
- Creates A/B test variants with different messaging approaches

**Automatic Localization:**
- Detects target region and suggests appropriate languages
- Generates culturally-adapted translations (not just literal)
- Creates separate image folders for each language
- Maintains message effectiveness across all languages

This feature works automatically with existing campaign briefs - no changes needed!

## Output Structure

With localization enabled (automatic for multi-language regions):
```
output/
└── {campaign_id}/
    ├── campaign_report.json        # Includes copywriting & localization data
    ├── {product_1}/
    │   ├── en/                     # English versions
    │   │   ├── 1x1.jpg
    │   │   ├── 9x16.jpg
    │   │   └── 16x9.jpg
    │   ├── de-DE/                  # German versions
    │   │   ├── 1x1.jpg
    │   │   ├── 9x16.jpg
    │   │   └── 16x9.jpg
    │   └── fr-FR/                  # French versions
    │       ├── 1x1.jpg
    │       ├── 9x16.jpg
    │       └── 16x9.jpg
    └── {product_2}/
        └── ... (same structure)
```

Single-language regions default to `en/` folder only.

## Requirements

- Python 3.9+
- OpenAI API key with DALL-E 3 access

## Key Design Decisions

- **Asset reuse first**: Always checks for existing assets before generating
- **Smart cropping**: Center-based cropping maintains focal points across ratios
- **Rate limiting**: Built-in delays to respect API limits
- **Validate early**: Content moderation runs before generation to catch issues early
- **Optimize intelligently**: AI analyzes audience before generating messages
- **Localize automatically**: Creates multi-language versions for global regions
- **Quality gates**: Brand compliance scoring ensures consistent output
- **Error resilience**: Continues processing even if individual products fail
- **Organized output**: Clear directory structure by campaign/product/language
- **Audit trail**: All optimizations and validations tracked in detailed JSON reports
