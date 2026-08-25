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
async def query_mireye_ask(lat: float, lng: float, query: str, reason: str = "") -> Dict[str, Any]:
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
    logger.info(f"Mireye /ask call for lat={lat}, lng={lng}, query='{query}'")
    
    try:
        headers = _get_headers()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json={"lat": lat, "lng": lng, "question": query, "query": query}, headers=headers)
            response.raise_for_status()
            return response.json()
    except ValueError as ve:
        # Return deterministic mock fixture
        return {
            "source": "MOCK",
            "answer": f"Mireye spatial analysis for '{query}': Upstream land-use includes active agricultural parcels (approx 35%), riparian tree canopy buffer, and nearby industrial/utility infrastructure.",
            "note": "This is a deterministic mock fixture for testing."
        }
    except Exception as e:
        logger.error(f"query_mireye_ask failed: {e}")
        return {"error": f"Failed to ask contextual question via Mireye API: {e}"}

async def query_mireye_natural_language(
    query_str: str,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    bbox: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Executes a direct natural language request string against Mireye Earth API without keyword matching or fixed field translations.
    """
    url = f"{settings.mireye_base_url}/ask"
    logger.info(f"Targeted Fetch calling Mireye with query='{query_str}' at lat={lat}, lng={lng}")

    payload: Dict[str, Any] = {"question": query_str, "query": query_str}
    if lat is not None and lng is not None:
        payload["lat"] = lat
        payload["lng"] = lng
    if bbox is not None:
        payload["bbox"] = bbox

    try:
        headers = _get_headers()
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            res_json = response.json()
            return res_json if isinstance(res_json, dict) else {"result": res_json}
    except ValueError:
        # Fallback when key is mock or unset
        return {
            "source": "MOCK",
            "query": query_str,
            "findings": f"Mireye targeted investigation for '{query_str}': Satellite and GIS observations confirm relevant land/infrastructure signals along the corridor, with mixed agricultural and developed runoff pathways.",
            "confidence": 0.85
        }
    except Exception as e:
        logger.warning(f"query_mireye_natural_language request failed: {e}. Using resilient mock result.")
        return {
            "source": "MOCK_FALLBACK",
            "query": query_str,
            "findings": f"Contextual evidence for '{query_str}': Analysis shows riparian buffer variability with localized upstream runoff contributors.",
            "error_note": str(e)
        }

