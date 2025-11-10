"""
FastAPI application for Creative Automation Pipeline.

Provides REST API endpoints for campaign processing.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ConfigDict
from dotenv import load_dotenv
import shutil

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

# Uploads directory for user-provided images
UPLOADS_DIR = Path("./uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory storage for campaign status (POC only)
campaign_store: Dict[str, Dict[str, Any]] = {}

# In-memory storage for campaign progress updates (POC only)
progress_store: Dict[str, list] = {}


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

  # Handle nested campaign directory structure
  nested_campaign_dir = output_path / campaign_id
  if nested_campaign_dir.exists() and nested_campaign_dir.is_dir():
    output_path = nested_campaign_dir

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
  # Try to get from campaign store first
  if campaign_id in campaign_store:
    output_path = Path(campaign_store[campaign_id]["output_path"])
  else:
    # Fall back to filesystem scan for campaigns created before API started
    output_path = OUTPUT_DIR / campaign_id
    if not output_path.exists():
      raise HTTPException(status_code=404, detail="Campaign not found")

  # Handle nested campaign directory structure
  nested_campaign_dir = output_path / campaign_id
  if nested_campaign_dir.exists() and nested_campaign_dir.is_dir():
    output_path = nested_campaign_dir

  file_path = output_path / product / language / filename

  if not file_path.exists():
    raise HTTPException(status_code=404, detail="Asset not found")

  return FileResponse(file_path, media_type="image/jpeg")


@app.get("/api/campaigns/{campaign_id}/assets/{product}/{filename}")
async def get_asset_file_no_lang(campaign_id: str, product: str, filename: str):
  """Serve a specific asset file (no language subdirectory)."""
  # Try to get from campaign store first
  if campaign_id in campaign_store:
    output_path = Path(campaign_store[campaign_id]["output_path"])
  else:
    # Fall back to filesystem scan for campaigns created before API started
    output_path = OUTPUT_DIR / campaign_id
    if not output_path.exists():
      raise HTTPException(status_code=404, detail="Campaign not found")

  # Handle nested campaign directory structure
  nested_campaign_dir = output_path / campaign_id
  if nested_campaign_dir.exists() and nested_campaign_dir.is_dir():
    output_path = nested_campaign_dir

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


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
  """
  Upload a product image to use in campaigns.

  Returns the path to the uploaded file that can be used in existing_assets.
  """
  # Validate file type
  if not file.content_type or not file.content_type.startswith("image/"):
    raise HTTPException(status_code=400, detail="File must be an image")

  # Generate unique filename
  file_extension = Path(file.filename).suffix
  unique_filename = f"{uuid.uuid4().hex}{file_extension}"
  file_path = UPLOADS_DIR / unique_filename

  # Save uploaded file
  try:
    with file_path.open("wb") as buffer:
      shutil.copyfileobj(file.file, buffer)
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

  return {
    "filename": unique_filename,
    "original_filename": file.filename,
    "path": f"/api/uploads/{unique_filename}",
    "absolute_path": str(file_path.absolute())
  }


@app.get("/api/uploads/{filename}")
async def get_uploaded_file(filename: str):
  """Serve an uploaded file."""
  file_path = UPLOADS_DIR / filename

  if not file_path.exists():
    raise HTTPException(status_code=404, detail="File not found")

  return FileResponse(file_path, media_type="image/jpeg")


@app.get("/api/generated-images")
async def list_generated_images():
  """
  List all previously generated images from past campaigns.

  Returns a list of images that can be reused as existing_assets.
  """
  generated_images = []

  # Scan all campaign output directories
  for campaign_dir in OUTPUT_DIR.iterdir():
    if not campaign_dir.is_dir():
      continue

    campaign_id = campaign_dir.name

    # Handle nested campaign directory structure
    scan_dir = campaign_dir
    nested_campaign_dir = campaign_dir / campaign_id
    if nested_campaign_dir.exists() and nested_campaign_dir.is_dir():
      scan_dir = nested_campaign_dir

    # Scan for product images
    for product_dir in scan_dir.iterdir():
      if not product_dir.is_dir() or product_dir.name == "__pycache__":
        continue

      product_name = product_dir.name

      # Look for source images (DALL-E generated, before variations)
      source_image = product_dir / "source.jpg"
      if source_image.exists():
        generated_images.append({
          "campaign_id": campaign_id,
          "product": product_name,
          "filename": "source.jpg",
          "url": f"/api/campaigns/{campaign_id}/assets/{product_name}/source.jpg",
          "absolute_path": str(source_image.absolute()),
          "created_at": datetime.fromtimestamp(source_image.stat().st_mtime).isoformat()
        })

  # Sort by creation time (newest first)
  generated_images.sort(key=lambda x: x["created_at"], reverse=True)

  return {
    "total": len(generated_images),
    "images": generated_images
  }


if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=8000)
