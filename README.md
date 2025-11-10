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

```bash
python src/main.py examples/sample_campaign.json
```

## Requirements

- Python 3.9+
- OpenAI API key with DALL-E 3 access

## Development Status

🚧 Work in progress - building components incrementally
