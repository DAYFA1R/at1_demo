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

## Features

- **Multi-product support** - Process 2+ products per campaign
- **Asset management** - Reuse existing assets or generate new ones with DALL-E
- **Multiple formats** - Create 3 aspect ratios (1:1, 9:16, 16:9)
- **Text overlays** - Automatic campaign message placement
- **Smart prompts** - Context-aware generation based on region and audience
- **JSON/YAML support** - Flexible campaign brief formats
- **Detailed reporting** - JSON reports with processing statistics

## Output Structure

```
output/
└── {campaign_id}/
    ├── campaign_report.json
    ├── {product_1}/
    │   ├── 1x1.jpg
    │   ├── 9x16.jpg
    │   └── 16x9.jpg
    └── {product_2}/
        ├── 1x1.jpg
        ├── 9x16.jpg
        └── 16x9.jpg
```

## Requirements

- Python 3.9+
- OpenAI API key with DALL-E 3 access

## Key Design Decisions

- **Asset reuse first**: Always checks for existing assets before generating
- **Smart cropping**: Center-based cropping maintains focal points across ratios
- **Rate limiting**: Built-in delays to respect API limits
- **Error resilience**: Continues processing even if individual products fail
- **Organized output**: Clear directory structure by campaign and product
