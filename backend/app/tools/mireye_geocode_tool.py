import time
import re
import httpx
from typing import Dict, Any
from langchain_core.tools import tool
from app.config import settings
from app.services.http_client import http_client
from app.core.logging import logger, log_tool_call
from app.core.exceptions import GeocodeNotFoundException

def clean_waterbody_query(query: str) -> str:
    """Replaces natural language locative phrases like ' near ', ' by ' with ', ' for geocoder compatibility."""
    cleaned = re.sub(r'\b(near|by|around|close to|in the vicinity of)\b', ',', query, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

async def geocode_via_nominatim(query: str) -> Dict[str, Any]:
    """Geocodes any free-text US waterbody query using OpenStreetMap Nominatim with query cleaning."""
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "AquaTraceApp/1.0 (waterbody-pollution-agent)"}
    
    # Try exact query first, then cleaned query
    queries_to_try = [query]
    cleaned = clean_waterbody_query(query)
    if cleaned != query:
        queries_to_try.append(cleaned)
    
    # Also try just the main waterbody name if multi-word
    words = query.split()
    if len(words) > 2:
        queries_to_try.append(" ".join(words[:2]))

    async with httpx.AsyncClient(timeout=8.0) as client:
        for q in queries_to_try:
            try:
                resp = await client.get(url, params={"q": q, "format": "json", "limit": 1}, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if data and len(data) > 0:
                        item = data[0]
                        return {
                            "matched_name": item.get("display_name", query),
                            "lat": float(item["lat"]),
                            "lng": float(item["lon"]),
                            "confidence": 0.95
                        }
            except Exception:
                continue

    raise GeocodeNotFoundException(query)

@tool
async def geocode_location(query: str) -> Dict[str, Any]:
    """Geocodes any free-text waterbody query to exact lat, lng, matched_name."""
    start_time = time.time()
    inputs = {"query": query}
    
    if not query or not query.strip():
        log_tool_call("geocode_location", inputs, time.time() - start_time, False, "Empty query")
        raise GeocodeNotFoundException(query)

    # 1. Try Mireye Geocoding API if valid key is set
    if settings.mireye_api_key and settings.mireye_api_key != "mock-mireye-key":
        url = f"{settings.mireye_base_url}/fetch"
        headers = {"Authorization": f"Bearer {settings.mireye_api_key}"}
        try:
            resp = await http_client.post(url, json_data={"address": query}, headers=headers, timeout_override=6.0)
            data = resp.json()
            if data and "lat" in data and "lng" in data:
                result = {
                    "matched_name": data.get("matched_name", query),
                    "lat": float(data["lat"]),
                    "lng": float(data["lng"]),
                    "confidence": float(data.get("confidence", 1.0))
                }
                log_tool_call("geocode_location", inputs, time.time() - start_time, True)
                return result
        except Exception as e:
            logger.warning(f"Mireye address lookup notice: {e}. Trying open waterbody geocoder.")

    # 2. Try Nominatim Geocoder with natural language query cleaning
    try:
        res = await geocode_via_nominatim(query)
        log_tool_call("geocode_location", inputs, time.time() - start_time, True)
        return res
    except Exception as e:
        logger.error(f"Geocoding failed for '{query}': {e}")
        log_tool_call("geocode_location", inputs, time.time() - start_time, False, str(e))
        raise GeocodeNotFoundException(query)
