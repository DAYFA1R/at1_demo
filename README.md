# Creative Automation Pipeline

An AI-powered platform for automating social media campaign creative generation with DALL-E image generation, AI copywriting, multi-language localization, and brand compliance validation.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Backend Components](#backend-components)
- [API Endpoints](#api-endpoints)
- [Frontend Components](#frontend-components)
- [Features](#features)
- [Design Philosophy](#design-philosophy)
- [Configuration](#configuration)
- [Development](#development)

---

## Overview

This platform automates the creation of social media advertising creatives by:

1. **Generating or reusing product images** using DALL-E 3 or uploaded assets
2. **Optimizing campaign messages** with GPT-4 for target audiences
3. **Creating localized variations** for different languages and regions
4. **Validating content** against brand guidelines and compliance rules
5. **Producing multi-format assets** optimized for different social platforms (1:1, 9:16, 16:9)

**Key Technologies:**
- **Backend**: Python 3.11, FastAPI, OpenAI API (DALL-E 3, GPT-4), Pillow
- **Frontend**: React, Vite, Tailwind CSS
- **Infrastructure**: Docker, Docker Compose

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key with DALL-E 3 and GPT-4 access

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd at1_demo
   ```

2. **Configure environment**:
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env and add your OPENAI_API_KEY
   ```

3. **Start the application**:
   ```bash
   docker compose up --build
   ```

4. **Access the application**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### First Campaign

1. Navigate to http://localhost:5173
2. Fill out the campaign form:
   - Add 2+ products with descriptions (minimum 2 required)
   - Set target region and audience
   - Enter campaign message
   - (Optional) Add brand colors for compliance checking
3. Click "Generate Campaign"
4. View generated assets in the gallery once processing completes

---

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Campaign    │  │ Asset       │  │ Progress    │          │
│  │ Form        │  │ Gallery     │  │ Dashboard   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└───────────────────────────┬─────────────────────────────────┘
                            │ REST API
┌───────────────────────────▼─────────────────────────────────┐
│                   Backend (FastAPI + Python)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Pipeline Orchestrator                   │   │
│  │  Coordinates the entire campaign processing flow     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │ Services   │  │ Processors │  │ Validators │             │
│  ├────────────┤  ├────────────┤  ├────────────┤             │
│  │• Image Gen │  │• Creative  │  │• Content   │             │
│  │• Copywriter│  │  Composer  │  │  Moderator │             │
│  │• Asset Mgr │  │            │  │• Brand     │             │
│  │            │  │            │  │  Compliance│             │
│  └────────────┘  └────────────┘  └────────────┘             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Data Models                       │   │
│  │  Campaign, Product, AspectRatio, CampaignBrief       │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  OpenAI API   │
                    │  • DALL-E 3   │
                    │  • GPT-4      │
                    └───────────────┘
```

### Data Flow

```
1. User submits campaign brief via frontend
                ↓
2. API validates and queues campaign for processing
                ↓
3. Orchestrator executes pipeline:
   a. Content moderation check
   b. AI copywriting optimization
   c. Localization for target regions
   d. Product image generation/retrieval
   e. Creative composition (aspect ratios + text overlays)
   f. Brand compliance validation
                ↓
4. Assets saved to organized directory structure
                ↓
5. Frontend displays results in gallery
```

---

## Project Structure

```
at1_demo/
├── backend/                    # Python FastAPI backend
│   ├── src/
│   │   ├── models/            # Data models (Campaign, Product, etc.)
│   │   ├── services/          # Core services
│   │   │   ├── image_generator.py      # DALL-E integration
│   │   │   ├── creative_copywriter.py  # GPT-4 copywriting
│   │   │   └── asset_manager.py        # Asset storage
│   │   ├── processors/        # Image processing
│   │   │   └── creative_composer.py    # Aspect ratios, text overlays
│   │   ├── validators/        # Quality & compliance
│   │   │   ├── content_moderator.py    # Content safety
│   │   │   └── brand_compliance.py     # Brand guideline validation
│   │   ├── pipeline/          # Orchestration
│   │   │   └── orchestrator.py         # Main pipeline coordinator
│   │   └── main.py            # CLI entry point
│   ├── api.py                 # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile
│   ├── output/                # Generated campaign assets
│   └── uploads/               # User-uploaded images
│
├── frontend/                   # React Vite frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── CampaignForm.jsx        # Campaign creation form
│   │   │   ├── AssetGallery.jsx        # Asset viewer
│   │   │   └── ProgressDashboard.jsx   # Processing status
│   │   ├── App.jsx            # Main application
│   │   └── main.jsx           # Entry point
│   ├── package.json           # Node dependencies
│   └── Dockerfile
│
├── examples/                   # Example campaign briefs
│   ├── fitness_asia_pacific.json
│   ├── sample_campaign.json
│   └── sample_campaign.yaml
│
├── docker-compose.yml         # Multi-container orchestration
└── README.md
```

---

## Backend Components

### 1. Pipeline Orchestrator
**File**: `backend/src/pipeline/orchestrator.py`

The central coordinator that executes the campaign processing pipeline in sequential stages.

**Key Methods**:
- `process_campaign(brief)` - Main entry point
- `_process_product(product, brief, output_dir)` - Per-product processing
- `_get_or_generate_asset(product, brief)` - Asset acquisition strategy
- `_generate_report(output_dir, brief)` - JSON report generation

**Pipeline Stages**:
1. AI copywriting optimization (if enabled)
2. Content moderation check
3. Brand validator initialization
4. Product processing (images + variations)
5. Brand compliance validation
6. Report generation

---

### 2. Services

#### Image Generator
**File**: `backend/src/services/image_generator.py`

Integrates with OpenAI's DALL-E 3 API for product image generation.

**Key Features**:
- Hex-to-color-name conversion for better DALL-E understanding
- Brand color-focused prompt engineering
- Rate limiting to respect API quotas
- Automatic image download and storage

**Key Methods**:
- `build_prompt(product, brief)` - Creates optimized DALL-E prompts emphasizing brand colors
- `generate(prompt, product_name)` - Calls DALL-E API
- `generate_for_product(product, brief)` - High-level generation wrapper

**Prompt Strategy**:
```python
# Example output for green brand color:
"green and green colored product photography,
 Eco-friendly yoga mat on green background,
 vibrant green color palette,
 bold green tones dominating the image,
 clean modern composition..."
```

#### Creative Copywriter
**File**: `backend/src/services/creative_copywriter.py`

Uses GPT-4 to optimize campaign messages for target audiences and create localizations.

**Key Features**:
- Psychographic persona analysis
- Message optimization for regional preferences
- A/B test variant generation
- Automatic localization with cultural adaptation

**Key Methods**:
- `analyze_audience(audience, region)` - Extract values and triggers
- `optimize_message(message, persona)` - Generate optimized variants
- `select_best_message(original, variants, persona)` - Choose optimal message
- `generate_localizations(message, region)` - Create region-specific translations

#### Asset Manager
**File**: `backend/src/services/asset_manager.py`

Manages storage and retrieval of both user-uploaded and AI-generated images.

**Key Features**:
- Asset existence checking
- Path resolution for existing assets
- Generated asset storage with unique IDs
- Organized directory structure

**Key Methods**:
- `find_existing_asset(product_name, asset_paths)` - Locate existing images
- `save_generated_asset(image_data, product_name)` - Store DALL-E outputs

---

### 3. Processors

#### Creative Composer
**File**: `backend/src/processors/creative_composer.py`

Transforms source images into design-ready advertising creatives with brand-aware text overlays, smart positioning, and smooth gradient scrims.

**Key Features**:
- **Smart Positioning Algorithm**: Analyzes 6 candidate regions to find optimal text placement based on uniformity and contrast
- **Brand-Aware Text Colors**: Uses campaign brand colors with WCAG AAA (7:1) contrast compliance
- **Edge-Based Gradient Scrims**: Smooth directional vignettes (Netflix/Apple TV+ style) that fade from edge to transparent
- **WCAG Compliance**: Calculates relative luminance and contrast ratios per accessibility guidelines
- **International Font Support**: Arabic, Hebrew, CJK languages with appropriate font selection
- **Smart Center Cropping**: Maintains focal points across aspect ratios
- **High-Quality Resampling**: LANCZOS algorithm for professional image quality

**Supported Aspect Ratios**:
- **1:1 (Square)**: 1080x1080 - Instagram feed, Facebook
- **9:16 (Vertical)**: 1080x1920 - Instagram Stories, TikTok
- **16:9 (Horizontal)**: 1920x1080 - YouTube, Facebook video

**Key Methods**:
- `smart_crop(image, target_ratio)` - Intelligent center cropping
- `_find_best_text_region(image)` - Analyzes 6 regions to find optimal text placement
- `calculate_contrast_ratio(color1, color2)` - WCAG contrast calculation
- `select_text_colors(region_analysis, brand_colors)` - Brand-aware color selection with 7:1 threshold
- `add_text_overlay(image, message, position, language_code, brand_colors)` - Brand-aware text with gradient scrim
- `create_variations(source_image, message, output_dir, product_name, brand_colors)` - Generate all aspect ratios
- `create_localized_variations(source_image, messages, output_dir, product_name, brand_colors)` - Multi-language variations

---

### 4. Validators

#### Content Moderator
**File**: `backend/src/validators/content_moderator.py`

Validates campaign messages against advertising standards and regulations.

**Validation Rules**:
- **Prohibited words**: Blocks claims like "guaranteed", "miracle", "no-risk"
- **Regulated terms**: Warns about health claims, superlatives requiring disclaimers
- **Regional sensitivities**: Checks region-specific restricted terms

**Risk Levels**:
- **Low**: Clean content, no issues
- **Medium**: Contains warnings but processable
- **High**: Contains violations, blocks processing

**Key Methods**:
- `check_text(text, region)` - Validate message content
- `check_campaign_message(message, region)` - Campaign-specific check

#### Brand Compliance Validator
**File**: `backend/src/validators/brand_compliance.py`

Ensures generated creatives meet brand guidelines.

**Validation Checks**:
1. **Color Compliance**: Validates brand color usage (requires ≥20% coverage)
   - Uses color quantization to group similar colors
   - Configurable tolerance (default: 75% similarity)
   - Matches image colors to brand palette

2. **Text Readability**: Checks text overlay contrast
   - Analyzes brightness in text regions
   - Recommends white or dark text

**Scoring**:
- 0-100 scale
- ≥70 = Compliant
- 50-69 = Acceptable with improvements
- <50 = Needs improvement

**Key Methods**:
- `extract_dominant_colors(image, count)` - Extract color palette with quantization
- `validate_colors(image_path)` - Check brand color alignment
- `validate_text_readability(image_path)` - Check text contrast
- `validate_creative(image_path)` - Full compliance report

**Color Quantization**:
Groups similar pixel colors together using PIL's quantization algorithm (32-color palette) to produce meaningful percentages instead of thousands of tiny fragments.

---

### 5. Data Models
**File**: `backend/src/models/campaign.py`

#### Campaign Brief
Represents a campaign configuration.

**Fields**:
- `campaign_id`: Unique identifier
- `products`: List of Product objects (minimum 2 required)
- `target_region`: Geographic target (e.g., "Europe", "Asia Pacific")
- `target_audience`: Demographic/psychographic description
- `campaign_message`: Core message text
- `brand_colors`: List of hex colors (e.g., ["#00B894", "#FFFFFF"])
- `logo_path`: Optional brand logo path

**Note**: AI copywriting optimization is controlled via the API request (`enable_copywriting` parameter), not as a model field.

#### Product
Represents a product to be featured.

**Fields**:
- `name`: Product name
- `description`: Detailed description for DALL-E
- `existing_assets`: List of paths to existing images

#### AspectRatio
Defines social media aspect ratio specifications.

**Predefined Ratios**:
- `SQUARE`: 1080x1080 (1:1 ratio)
- `PORTRAIT`: 1080x1920 (9:16 ratio)
- `LANDSCAPE`: 1920x1080 (16:9 ratio)

---

## API Endpoints

### Campaign Processing

#### `POST /api/campaigns/process`
Create and process a new campaign.

**Request Body**:
```json
{
  "campaign_id": "summer_2024", // not used, debating if I still want it in
  "products": [
    {
      "name": "Yoga Mat",
      "description": "Eco-friendly yoga mat",
      "existing_assets": []
    }
  ],
  "target_region": "North America",
  "target_audience": "Health-conscious millennials",
  "campaign_message": "Find your balance",
  "brand_colors": ["#00B894", "#FFFFFF"],
  "enable_copywriting": true
}
```

**Response**:
```json
{
  "campaign_id": "summer_2024",
  "status": "processing",
  "message": "Campaign queued for processing"
}
```

---

#### `GET /api/campaigns/{campaign_id}/status`
Get campaign processing status.

**Response**:
```json
{
  "campaign_id": "summer_2024",
  "status": "completed",
  "created_at": "2025-11-10T10:00:00",
  "report": {
    "summary": {
      "total_products": 2,
      "successful_products": 2,
      "total_variations": 6,
      "assets_generated": 1,
      "assets_reused": 1
    },
    "copywriting": {
      "selected_message": "Discover your inner peace",
      "confidence_score": 0.85
    },
    "compliance_summary": {
      "average_score": 85.5,
      "all_compliant": true
    }
  }
}
```

---

#### `GET /api/campaigns/{campaign_id}/assets`
List all generated assets for a campaign.

**Response**:
```json
{
  "campaign_id": "summer_2024",
  "total_assets": 6,
  "assets": [
    {
      "product": "yoga_mat",
      "language": "en",
      "aspect_ratio": "1x1",
      "url": "/api/campaigns/summer_2024/assets/yoga_mat/en/1x1.jpg"
    }
  ]
}
```

---

#### `GET /api/campaigns`
List all campaigns.

**Response**:
```json
{
  "total": 5,
  "campaigns": [
    {
      "campaign_id": "summer_2024",
      "status": "completed",
      "created_at": "2025-11-10T10:00:00"
    }
  ]
}
```

---

### Asset Management

#### `GET /api/campaigns/{campaign_id}/assets/{product}/{language}/{filename}`
Serve a localized asset file.

**Example**: `/api/campaigns/summer_2024/assets/yoga_mat/en/1x1.jpg`

---

#### `GET /api/campaigns/{campaign_id}/assets/{product}/{filename}`
Serve an asset file (no language subdirectory).

**Example**: `/api/campaigns/summer_2024/assets/yoga_mat/source.jpg`

**Note**: Falls back to filesystem if campaign not in memory (handles server restarts).

---

#### `POST /api/upload`
Upload a product image for use in campaigns.

**Request**: Multipart form data with `file` field

**Response**:
```json
{
  "filename": "yoga_mat_abc123.jpg",
  "url": "/api/uploads/yoga_mat_abc123.jpg",
  "path": "uploads/yoga_mat_abc123.jpg"
}
```

---

#### `GET /api/uploads/{filename}`
Serve an uploaded image.

---

#### `GET /api/generated-images`
List all previously generated images from past campaigns for reuse.

**Response**:
```json
{
  "total": 10,
  "images": [
    {
      "campaign_id": "summer_2024",
      "product": "yoga_mat",
      "filename": "source.jpg",
      "url": "/api/campaigns/summer_2024/assets/yoga_mat/source.jpg",
      "created_at": "2025-11-10T10:00:00"
    }
  ]
}
```

**Use Case**: Browse and reuse DALL-E generated images without re-generating.

---

### Health Check

#### `GET /`
API health check and welcome message.

---

## Frontend Components

### CampaignForm
**File**: `frontend/src/components/CampaignForm.jsx`

Interactive form for creating new campaigns.

**Features**:
- Dynamic product management (minimum 2 products, can add more)
- Brand color picker with visual preview
- Asset upload with drag-and-drop
- Browse previously generated images modal
- Real-time form validation
- Campaign submission

**State Management**:
- Form data (products, message, colors, region, audience)
- Upload modal state
- Generated images browser state

---

### AssetGallery
**File**: `frontend/src/components/AssetGallery.jsx`

Displays generated campaign assets organized by product and language.

**Features**:
- Tabbed navigation by product
- Language filter dropdown
- Aspect ratio tabs (1:1, 9:16, 16:9)
- Full-screen image viewer
- Download individual assets
- Download all assets as ZIP
- Brand compliance score badges
- Copywriting details display

**Visual Elements**:
- Green badge (≥70): Compliant
- Yellow badge (50-69): Acceptable
- Red badge (<50): Needs improvement

---

### ProgressDashboard
**File**: `frontend/src/components/ProgressDashboard.jsx`

Real-time campaign processing status.

**Features**:
- Status badge (Processing/Completed/Failed)
- Progress metrics:
  - Products processed
  - Variations created
  - Assets generated vs reused
- Error display
- Processing duration
- Auto-refresh every 3 seconds during processing

---

## Features

### Core Capabilities

#### 1. Flexible Asset Strategy
- **Reuse existing assets**: Upload product images to avoid regeneration costs
- **AI generation**: DALL-E 3 creates product photography on-demand
- **Mixed approach**: Combine uploaded and generated assets per campaign
- **Multi-product campaigns**: Process 2+ products per campaign (minimum 2 required)

#### 2. Multi-Language Localization
Automatically creates language-specific variations:

**Supported Regions**:
- **North America**: English
- **Europe**: English, German, French, Spanish, Italian
- **Asia Pacific**: English, Japanese, Korean, Chinese
- **Middle East**: English, Arabic

**Features**:
- Cultural adaptation (not literal translation)
- Language-specific font selection (Noto fonts for Arabic/Hebrew/CJK)
- Separate directories per language
- Right-to-left text support

#### 3. AI Copywriting Optimization
GPT-4 analyzes audiences and optimizes messages:

**Optimization Process**:
1. Extract demographic and psychographic traits
2. Generate message variants with different approaches:
   - Aspirational
   - Problem-solution
   - Social proof
   - Benefit-focused
3. Select best variant based on audience alignment
4. Generate A/B test alternatives

**Example**:
```
Original: "Try our new product"
Optimized: "Unlock your potential with science-backed wellness"
Reasoning: Appeals to health-conscious millennials' values of
           self-improvement and evidence-based solutions
```

#### 4. Brand Compliance Validation

**Color Compliance**:
- Extracts dominant colors using quantization (groups similar shades)
- Matches against brand palette with configurable tolerance
- Requires ≥20% brand color coverage
- Reports similarity scores and coverage percentages

**Text Readability**:
- Analyzes brightness in text overlay regions
- Ensures sufficient contrast for legibility
- Recommends white or dark text based on background

**Scoring System**:
- 0-100 composite score
- Detailed breakdown by check type
- Actionable recommendations

#### 5. Content Moderation

**Pre-generation validation** saves API costs by blocking problematic content early.

**Checks**:
- Prohibited claims (guaranteed, miracle, cure)
- Health claims requiring disclaimers
- Superlatives needing substantiation
- Regional sensitivities

**Risk Levels**:
- **Low**: Passes all checks
- **Medium**: Contains warnings
- **High**: Contains violations (blocks processing)

---

## Design Philosophy

### 1. Fail Fast, Validate Early
Content moderation runs **before** expensive DALL-E calls to catch issues early and avoid wasted API costs.

### 2. Asset Reuse Over Regeneration
Always check for existing assets before generating new ones:
- Saves API costs
- Faster processing
- Consistent brand imagery

### 3. Progressive Enhancement
Each stage adds value:
1. Base message → AI optimization
2. Single language → Multi-language localization
3. Source image → Multiple aspect ratios
4. Raw creative → Brand compliance validation

### 4. Graceful Degradation
- Missing brand colors? Skips compliance checks
- Copywriting disabled? Uses original message
- Product generation fails? Continues with others

### 5. Organized, Predictable Output
```
campaign_id/
├── product_name/
│   ├── source.jpg          # Original DALL-E output (no text)
│   ├── en/                 # English variations
│   │   ├── 1x1.jpg
│   │   ├── 9x16.jpg
│   │   └── 16x9.jpg
│   ├── de-DE/              # German variations
│   └── ...
└── campaign_report.json     # Complete audit trail
```

### 6. Transparency Through Reporting
Every campaign generates a detailed JSON report:
- Original vs optimized messages
- Localization suggestions
- Brand compliance scores
- Processing metrics
- Errors and warnings

### 7. Color Science Over Brute Force
Brand compliance uses **color quantization** to group similar shades instead of counting individual pixels, producing meaningful compliance scores.

### 8. Stateless API, Filesystem Persistence
- In-memory `campaign_store` for active campaigns
- Automatic filesystem fallback for old campaigns
- Survives server restarts gracefully

---

## Configuration

### Environment Variables

Create `backend/.env`:

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional - DALL-E Configuration
DALLE_MODEL=dall-e-3           # Model version (default: dall-e-3)
DALLE_QUALITY=standard          # standard or hd (default: standard)
DALLE_SIZE=1024x1024           # Image dimensions (default: 1024x1024)
```

### Brand Colors

Specify in campaign brief as hex codes:

```json
{
  "brand_colors": ["#00B894", "#6C5CE7", "#FFFFFF"]
}
```

**Tips**:
- Use distinctive colors (avoid pure white/gray)
- 2-3 colors recommended
- Primary brand color should be first

---

## Development

### Running Locally (without Docker)

#### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add OPENAI_API_KEY
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

### CLI Usage (Standalone)

Process campaigns directly via CLI:

```bash
cd backend
source venv/bin/activate
python -m src.main examples/fitness_asia_pacific.json
```

**Options**:
- `-o, --output`: Custom output directory
- `-v, --verbose`: Verbose logging

### Docker Commands

```bash
# Build and start
docker compose up --build

# Start in background
docker compose up -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Restart services
docker compose restart backend

# Rebuild after code changes
docker compose build backend
docker compose restart backend

# Stop all services
docker compose down

# Clean everything (including volumes)
docker compose down -v
```

### Project Ports

- **Frontend**: 5173
- **Backend API**: 8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)

---

## Output Structure

### Generated Assets

```
backend/output/
└── {campaign_id}/
    ├── campaign_report.json
    ├── {product_1}/
    │   ├── source.jpg              # Original DALL-E (no text)
    │   ├── en/
    │   │   ├── 1x1.jpg             # Square + text
    │   │   ├── 9x16.jpg            # Story + text
    │   │   └── 16x9.jpg            # Video + text
    │   ├── de-DE/                  # German
    │   ├── fr-FR/                  # French
    │   └── ...
    └── {product_2}/
        └── ...
```

### Campaign Report

Example `campaign_report.json`:

```json
{
  "start_time": "2025-11-10T10:00:00",
  "end_time": "2025-11-10T10:02:30",
  "duration_seconds": 150,
  "summary": {
    "campaign_id": "summer_2024",
    "total_products": 2,
    "successful_products": 2,
    "total_variations": 6,
    "assets_generated": 1,
    "assets_reused": 1,
    "success_rate": "100.0%"
  },
  "copywriting": {
    "original_message": "Try our new yoga mat",
    "selected_message": "Find your balance with sustainable wellness",
    "confidence_score": 0.85,
    "optimization": {
      "variants": [...]
    },
    "localizations": {
      "suggestions": {
        "en": "Find your balance with sustainable wellness",
        "de-DE": "Finden Sie Ihr Gleichgewicht mit nachhaltiger Wellness",
        "fr-FR": "Trouvez votre équilibre avec le bien-être durable"
      }
    }
  },
  "content_moderation": {
    "approved": true,
    "risk_level": "low",
    "violations": [],
    "warnings": []
  },
  "compliance_summary": {
    "enabled": true,
    "average_score": 85.5,
    "total_checks": 6,
    "all_compliant": true
  },
  "products_processed": [
    {
      "name": "Yoga Mat",
      "source": "generated",
      "variations": ["1x1", "9x16", "16x9"],
      "languages": ["en", "de-DE", "fr-FR"],
      "total_files": 9,
      "compliance": {
        "1x1": {
          "compliant": true,
          "overall_score": 85.0,
          "checks": {
            "colors": {
              "brand_color_coverage": 26.5,
              "average_similarity": 80.8
            },
            "readability": {
              "readable": true
            }
          }
        }
      }
    }
  ]
}
```

---

## Troubleshooting

### Common Issues

**"Module not found" errors**:
```bash
docker compose build backend --no-cache
docker compose restart backend
```

**CJK fonts not rendering**:
- Fonts are installed in Docker image at `/usr/share/fonts/opentype/noto/`
- Rebuild backend if missing: `docker compose build backend`

**Brand compliance showing 0%**:
- Ensure using distinctive colors (not white/gray)
- Check DALL-E is using brand colors in prompts
- Verify tolerance setting (default: 25 = 75% similarity)

**API quota exceeded**:
- Upload product images instead of generating
- Use "Browse Generated Images" to reuse existing DALL-E outputs
- Check OpenAI usage dashboard

**Images not loading in gallery**:
- Ensure backend is running: `docker compose ps`
- Check browser console for CORS errors
- Verify output directory exists: `ls backend/output/`

---

## Example Campaign Briefs

### fitness_asia_pacific.json
Multi-product wellness campaign targeting Asia Pacific with brand colors.

### sample_campaign.json
Basic campaign demonstrating core features.

### sample_campaign.yaml
YAML format example with copywriting optimization.

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (both backend and frontend)
5. Submit a pull request

---

## License

[Your License Here]
