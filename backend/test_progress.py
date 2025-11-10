"""Test script for progress tracking"""

import requests
import time
import json

API_URL = "http://localhost:8000"

def test_campaign_with_progress():
    """Submit a campaign and monitor progress updates."""

    # Test campaign data
    campaign_data = {
        "products": [
            {
                "name": "Test Product 1",
                "description": "A test product for progress tracking",
                "existing_assets": []
            },
            {
                "name": "Test Product 2",
                "description": "Another test product",
                "existing_assets": []
            }
        ],
        "target_region": "North America",
        "target_audience": "Young professionals aged 25-35",
        "campaign_message": "Experience the future of technology",
        "brand_colors": ["#FF6B6B", "#4ECDC4"],
        "enable_copywriting": True
    }

    print("Submitting campaign...")
    response = requests.post(f"{API_URL}/api/campaigns/process", json=campaign_data)

    if response.status_code != 200:
        print(f"Error submitting campaign: {response.text}")
        return

    result = response.json()
    campaign_id = result["campaign_id"]
    print(f"Campaign created: {campaign_id}")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}\n")

    # Monitor progress
    print("Monitoring progress...")
    print("-" * 60)

    last_stage = None
    while True:
        # Check status
        status_response = requests.get(f"{API_URL}/api/campaigns/{campaign_id}/status")
        status = status_response.json()

        # Display latest progress
        if status.get("latest_progress"):
            progress = status["latest_progress"]
            current_stage = progress.get("stage", "")

            # Only print if stage changed
            if current_stage != last_stage:
                print(f"\n[{progress.get('timestamp', '')}]")
                print(f"Stage: {current_stage}")
                print(f"Message: {progress.get('message', '')}")

                # Show additional details if available
                if progress.get("current_product"):
                    print(f"  Product: {progress['current_product']} of {progress.get('total_products', '?')}")
                if progress.get("variations_created"):
                    print(f"  Variations: {progress['variations_created']}")

                last_stage = current_stage

        # Check if completed or failed
        if status["status"] == "completed":
            print("\n" + "=" * 60)
            print("Campaign completed successfully!")
            if status.get("report", {}).get("summary"):
                summary = status["report"]["summary"]
                print(f"  Products: {summary.get('total_products')}")
                print(f"  Variations: {summary.get('total_variations')}")
                print(f"  Generated: {summary.get('assets_generated')}")
                print(f"  Reused: {summary.get('assets_reused')}")
                print(f"  Duration: {summary.get('duration_seconds')}s")
            break

        elif status["status"] == "failed":
            print("\n" + "=" * 60)
            print(f"Campaign failed: {status.get('error')}")
            break

        # Wait before next check
        time.sleep(1)

    # Get all progress updates
    print("\n" + "=" * 60)
    print("Fetching all progress updates...")
    progress_response = requests.get(f"{API_URL}/api/campaigns/{campaign_id}/progress")
    progress_data = progress_response.json()

    print(f"Total updates received: {progress_data['total_updates']}")
    print("\nAll progress stages:")
    for update in progress_data["progress_updates"]:
        print(f"  - [{update['stage']}] {update['message']}")

if __name__ == "__main__":
    test_campaign_with_progress()