"""
FastAPI application for Creative Automation Pipeline.

Provides REST API endpoints for campaign processing.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ConfigDict
from dotenv import load_dotenv

from src.models.campaign import CampaignBrief, Product
from src.pipeline.orchestrator import CampaignPipeline

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
  title="Creative Automation Pipeline API",
  description="AI-powered creative asset generation for social campaigns",
  version="1.0.0"
)

# Configure CORS for local React development
app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# Output directory for generated assets
OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# In-memory storage for campaign status (POC only)
campaign_store: Dict[str, Dict[str, Any]] = {}


# Pydantic models for API
class ProductInput(BaseModel):
  model_config = ConfigDict(extra='ignore')

  name: str = Field(..., description="Product name")
  description: str = Field(..., description="Product description")
  existing_assets: list[str] = Field(default_factory=list, description="Paths to existing assets")


class CampaignInput(BaseModel):
  model_config = ConfigDict(extra='ignore')

  products: list[ProductInput] = Field(..., min_length=2, description="List of products (minimum 2)")
  target_region: str = Field(..., description="Target geographic region")
  target_audience: str = Field(..., description="Target audience description")
  campaign_message: str = Field(..., description="Campaign message text")
  brand_colors: list[str] = Field(default_factory=list, description="Brand color hex codes")
  logo_path: Optional[str] = Field(None, description="Path to brand logo")
  enable_copywriting: bool = Field(True, description="Enable AI copywriting optimization")


class CampaignResponse(BaseModel):
  campaign_id: str
  status: str
  message: str


class CampaignStatus(BaseModel):
  campaign_id: str
  status: str
  progress: Optional[Dict[str, Any]] = None
  report: Optional[Dict[str, Any]] = None
  error: Optional[str] = None


# Helper functions
def create_campaign_brief(campaign_id: str, input_data: CampaignInput) -> CampaignBrief:
  """Convert API input to CampaignBrief model."""
  products = [
    Product(
      name=p.name,
      description=p.description,
      existing_assets=p.existing_assets
    )
    for p in input_data.products
  ]

  return CampaignBrief(
    campaign_id=campaign_id,
    products=products,
    target_region=input_data.target_region,
    target_audience=input_data.target_audience,
    campaign_message=input_data.campaign_message,
    brand_colors=input_data.brand_colors,
    logo_path=input_data.logo_path
  )


def process_campaign_task(campaign_id: str, brief: CampaignBrief, enable_copywriting: bool):
  """Background task to process campaign."""
  try:
    # Update status
    campaign_store[campaign_id]["status"] = "processing"
    campaign_store[campaign_id]["started_at"] = datetime.now().isoformat()

    # Initialize pipeline
    output_path = OUTPUT_DIR / campaign_id
    pipeline = CampaignPipeline(
      output_dir=str(output_path),
      enable_copywriting=enable_copywriting
    )

    # Process campaign
    report = pipeline.process_campaign(brief)

    # Update status with results
    campaign_store[campaign_id]["status"] = "completed"
    campaign_store[campaign_id]["completed_at"] = datetime.now().isoformat()
    campaign_store[campaign_id]["report"] = report
    campaign_store[campaign_id]["output_path"] = str(output_path)

  except Exception as e:
    # Update status with error
    campaign_store[campaign_id]["status"] = "failed"
    campaign_store[campaign_id]["error"] = str(e)
    campaign_store[campaign_id]["completed_at"] = datetime.now().isoformat()


# API Endpoints
@app.get("/")
async def root():
  """Health check endpoint."""
  return {
    "service": "Creative Automation Pipeline API",
    "status": "running",
    "version": "1.0.0"
  }


@app.post("/api/campaigns/process", response_model=CampaignResponse)
async def create_campaign(
  campaign_input: CampaignInput,
  background_tasks: BackgroundTasks
):
  """
  Create and process a new campaign.

  Returns immediately with campaign_id while processing happens in background.
  """
  # Generate unique campaign ID
  campaign_id = f"campaign_{uuid.uuid4().hex[:8]}"

  # Create campaign brief
  brief = create_campaign_brief(campaign_id, campaign_input)

  # Initialize campaign status
  campaign_store[campaign_id] = {
    "campaign_id": campaign_id,
    "status": "queued",
    "created_at": datetime.now().isoformat(),
    "brief": {
      "target_region": brief.target_region,
      "target_audience": brief.target_audience,
      "campaign_message": brief.campaign_message,
      "product_count": len(brief.products)
    }
  }

  # Add background task (for POC this runs synchronously but non-blocking)
  background_tasks.add_task(
    process_campaign_task,
    campaign_id,
    brief,
    campaign_input.enable_copywriting
  )

  return CampaignResponse(
    campaign_id=campaign_id,
    status="queued",
    message=f"Campaign {campaign_id} created and queued for processing"
  )


@app.get("/api/campaigns/{campaign_id}/status", response_model=CampaignStatus)
async def get_campaign_status(campaign_id: str):
  """
  Get the current status of a campaign.

  Returns processing status and final report when complete.
  """
  if campaign_id not in campaign_store:
    raise HTTPException(status_code=404, detail="Campaign not found")

  campaign_data = campaign_store[campaign_id]

  return CampaignStatus(
    campaign_id=campaign_id,
    status=campaign_data["status"],
    progress=campaign_data.get("brief"),
    report=campaign_data.get("report"),
    error=campaign_data.get("error")
  )


@app.get("/api/campaigns/{campaign_id}/assets")
async def get_campaign_assets(campaign_id: str):
  """
  Get list of all generated assets for a campaign.

  Returns URLs to access each generated creative.
  """
  if campaign_id not in campaign_store:
    raise HTTPException(status_code=404, detail="Campaign not found")

  campaign_data = campaign_store[campaign_id]

  if campaign_data["status"] != "completed":
    raise HTTPException(
      status_code=400,
      detail=f"Campaign is {campaign_data['status']}, assets not available"
    )

  # Build asset list from output directory
  output_path = Path(campaign_data["output_path"])
  assets = []

  # Scan directory for generated images
  for product_dir in output_path.iterdir():
    if product_dir.is_dir() and product_dir.name != "__pycache__":
      # Check for language subdirectories
      for lang_or_file in product_dir.iterdir():
        if lang_or_file.is_dir():
          # Language subdirectory
          for image_file in lang_or_file.glob("*.jpg"):
            assets.append({
              "product": product_dir.name,
              "language": lang_or_file.name,
              "aspect_ratio": image_file.stem,
              "url": f"/api/campaigns/{campaign_id}/assets/{product_dir.name}/{lang_or_file.name}/{image_file.name}",
              "filename": image_file.name
            })
        elif lang_or_file.suffix == ".jpg":
          # Direct image file (no localization)
          assets.append({
            "product": product_dir.name,
            "language": "en",
            "aspect_ratio": lang_or_file.stem,
            "url": f"/api/campaigns/{campaign_id}/assets/{product_dir.name}/{lang_or_file.name}",
            "filename": lang_or_file.name
          })

  return {
    "campaign_id": campaign_id,
    "total_assets": len(assets),
    "assets": assets
  }


@app.get("/api/campaigns/{campaign_id}/assets/{product}/{language}/{filename}")
async def get_asset_file(campaign_id: str, product: str, language: str, filename: str):
  """Serve a specific asset file."""
  if campaign_id not in campaign_store:
    raise HTTPException(status_code=404, detail="Campaign not found")

  output_path = Path(campaign_store[campaign_id]["output_path"])
  file_path = output_path / product / language / filename

  if not file_path.exists():
    raise HTTPException(status_code=404, detail="Asset not found")

  return FileResponse(file_path, media_type="image/jpeg")


@app.get("/api/campaigns/{campaign_id}/assets/{product}/{filename}")
async def get_asset_file_no_lang(campaign_id: str, product: str, filename: str):
  """Serve a specific asset file (no language subdirectory)."""
  if campaign_id not in campaign_store:
    raise HTTPException(status_code=404, detail="Campaign not found")

  output_path = Path(campaign_store[campaign_id]["output_path"])
  file_path = output_path / product / filename

  if not file_path.exists():
    raise HTTPException(status_code=404, detail="Asset not found")

  return FileResponse(file_path, media_type="image/jpeg")


@app.get("/api/campaigns")
async def list_campaigns():
  """List all campaigns."""
  return {
    "total": len(campaign_store),
    "campaigns": [
      {
        "campaign_id": cid,
        "status": data["status"],
        "created_at": data["created_at"]
      }
      for cid, data in campaign_store.items()
    ]
  }


if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=8000)
