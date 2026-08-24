import os
import httpx
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from app.config import settings
from app.core.logging import logger

def _get_headers() -> Dict[str, str]:
    if not settings.mireye_api_key or settings.mireye_api_key == "mock-mireye-key":
        raise ValueError("Mireye API key is missing or set to mock. Dynamic tools require a real key.")
    return {
        "Authorization": f"Bearer {settings.mireye_api_key}",
        "Content-Type": "application/json"
    }

@tool
async def query_mireye_fetch(lat: float, lng: float, reason: str, preset: str = "land_cover") -> Dict[str, Any]:
    """
    Fetches structured land-use, terrain, or environmental data from Mireye Earth API for a specific location.
    
    Args:
        lat: Latitude of the point of interest.
        lng: Longitude of the point of interest.
        reason: Explanation of the current uncertainty and why this information is needed.
        preset: The preset to fetch. Valid options MUST be one of: "land_cover", "terrain", "points_of_interest", "utilities", "natural_hazard", "boundaries", "flood_risk".
        
    Returns:
        A dictionary containing the structured fields requested.
    """
    url = f"{settings.mireye_base_url}/fetch"
    logger.info(f"Source Reasoning Agent calling Mireye /fetch for lat={lat}, lng={lng}, preset={preset}")
    
    try:
        headers = _get_headers()
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json={"lat": lat, "lng": lng, "preset": preset}, headers=headers)
            response.raise_for_status()
            return response.json().get("fields", {})
    except ValueError as ve:
        # Return deterministic mock fixture
        return {
            "source": "MOCK",
            "agriculture_percentage": "35%",
            "developed_percentage": "10%",
            "impervious_surface": "5%",
            "note": "This is a deterministic mock fixture for testing."
        }
    except Exception as e:
        logger.error(f"query_mireye_fetch failed: {e}")
        return {"error": f"Failed to fetch data from Mireye API: {e}"}

@tool
async def query_mireye_ask(lat: float, lng: float, query: str, reason: str) -> Dict[str, Any]:
    """
    Asks the Mireye Earth API a complex contextual or spatial question about a location's environment.
    Use this when structural fields from fetch are insufficient (e.g. asking for nearby residential density or specific upstream sources).
    
    Args:
        lat: Latitude of the point of interest.
        lng: Longitude of the point of interest.
        query: The specific question about the environmental or spatial characteristics.
        reason: Explanation of the current uncertainty and why this information is needed.
        
    Returns:
        A dictionary containing the contextual answer from Mireye.
    """
    url = f"{settings.mireye_base_url}/ask"
    logger.info(f"Source Reasoning Agent calling Mireye /ask for lat={lat}, lng={lng}, query='{query}'")
    
    try:
        headers = _get_headers()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json={"lat": lat, "lng": lng, "question": query}, headers=headers)
            response.raise_for_status()
            return response.json()
    except ValueError as ve:
        # Return deterministic mock fixture
        return {
            "source": "MOCK",
            "answer": "Agricultural land-use is highly prevalent upstream, with approximately 35% of the watershed devoted to crop production. There is also a small residential development area adjacent to the river.",
            "note": "This is a deterministic mock fixture for testing."
        }
    except Exception as e:
        logger.error(f"query_mireye_ask failed: {e}")
        return {"error": f"Failed to ask contextual question via Mireye API: {e}"}
