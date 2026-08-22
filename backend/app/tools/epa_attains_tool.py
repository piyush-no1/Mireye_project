import time
import json
import os
from typing import List, Dict, Any
from langchain_core.tools import tool
from app.config import settings
from app.services.http_client import http_client
from app.core.logging import logger, log_tool_call

def load_fixture_attains() -> List[Dict[str, Any]]:
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "..", "tests", "fixtures", "epa_attains_sample.json")
    if os.path.exists(fixture_path):
        with open(fixture_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {
            "assessment_unit_id": "VAW-A03R_POT01A00",
            "overall_status": "Impaired",
            "use_attainment": {
              "recreation": "Fully Supporting",
              "aquatic_life": "Not Supporting"
            },
            "parameters": [
              { "name": "Escherichia coli", "status": "Cause" }
            ],
            "tmdl_projects": [
              { "id": "TMDL-9812", "name": "Potomac River Bacterial TMDL" }
            ]
        }
    ]

@tool
async def get_epa_attains_status(bbox: List[float]) -> List[Dict[str, Any]]:
    """Fetches EPA ATTAINS Clean Water Act assessment unit impairment status."""
    start_time = time.time()
    inputs = {"bbox": bbox}
    
    url = f"{settings.epa_attains_base_url}/assessmentUnits"
    bbox_str = ",".join(str(b) for b in bbox) if bbox and len(bbox) == 4 else "-77.26,38.99,-77.24,39.01"
    
    headers = {"User-Agent": "AquaTraceApp/1.0 (waterbody-pollution-agent)"}
    if settings.epa_attains_api_key:
        headers["X-API-Key"] = settings.epa_attains_api_key
        headers["api_key"] = settings.epa_attains_api_key

    try:
        # Step 1: Query ATTAINS MapServer by bounding box to find Assessment Unit IDs
        map_url = "https://gispub.epa.gov/arcgis/rest/services/OW/ATTAINS_Assessment/MapServer/1/query"
        map_params = {
            "geometry": bbox_str,
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "assessmentunitidentifier,organizationid",
            "returnGeometry": "false",
            "f": "json"
        }
        
        map_resp = await http_client.get(map_url, params=map_params, timeout_override=10.0)
        map_data = map_resp.json()
        
        au_list = []
        for feature in map_data.get("features", []):
            au_id = feature.get("attributes", {}).get("assessmentunitidentifier")
            org_id = feature.get("attributes", {}).get("organizationid")
            if au_id and org_id and not any(a["au_id"] == au_id for a in au_list):
                au_list.append({"au_id": au_id, "org_id": org_id})
                
        # Limit to 5 AUs to prevent huge API requests
        au_list = au_list[:5]
        
        results = []
        # Step 2: Query the Tabular API for each AU ID concurrently
        assessments_url = f"{settings.epa_attains_base_url}/assessments"
        import asyncio
        
        async def fetch_au(au_info):
            api_params = {
                "assessmentUnitIdentifier": au_info["au_id"],
                "organizationId": au_info["org_id"]
            }
            if settings.epa_attains_api_key:
                api_params["api_key"] = settings.epa_attains_api_key
            
            try:
                # Reduce timeout to 5 seconds to fail fast
                resp = await http_client.get(assessments_url, params=api_params, headers=headers, timeout_override=5.0)
                if resp.status_code == 200:
                    return resp.json()
            except Exception:
                pass
            return None

        # Gather all requests concurrently
        tasks = [fetch_au(au_info) for au_info in au_list]
        responses = await asyncio.gather(*tasks)
        
        for data in responses:
            if data:
                items = data.get("items", [])
                for org_item in items:
                    assessments = org_item.get("assessments", [])
                    for au_item in assessments:
                        raw_uses = au_item.get("useAttainments", [])
                        use_dict = {u.get("useName", "Unknown"): u.get("useAttainmentCodeName", "Unknown") for u in raw_uses} if raw_uses else {}
                        
                        results.append({
                            "assessment_unit_id": au_item.get("assessmentUnitIdentifier", "EPA-ATTAINS-AU"),
                            "overall_status": au_item.get("overallStatus", "Impaired"),
                            "use_attainment": use_dict,
                            "parameters": au_item.get("parameters", []),
                            "tmdl_projects": au_item.get("probableSources", [])
                        })
                        
        log_tool_call("get_epa_attains_status", inputs, time.time() - start_time, True)
        return results
    except Exception as e:
        logger.warning(f"EPA ATTAINS live response notice: {e}")

    if settings.epa_attains_api_key == "mock-attains-key":
        results = load_fixture_attains()
        log_tool_call("get_epa_attains_status", inputs, time.time() - start_time, True)
        return results

    log_tool_call("get_epa_attains_status", inputs, time.time() - start_time, True)
    return []
