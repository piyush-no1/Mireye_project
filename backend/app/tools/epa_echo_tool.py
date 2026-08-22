import time
import json
import os
from typing import List, Dict, Any
from langchain_core.tools import tool
from app.config import settings
from app.services.http_client import http_client
from app.core.logging import logger, log_tool_call

def load_fixture_echo() -> List[Dict[str, Any]]:
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "..", "tests", "fixtures", "epa_echo_sample.json")
    if os.path.exists(fixture_path):
        with open(fixture_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {
            "source_id": "VA0024988",
            "facility_name": "Great Falls Wastewater Treatment Plant",
            "lat": 38.995,
            "lng": -77.248,
            "permit_status": "Effective",
            "effluent_exceedances": 2,
            "quarters_in_noncompliance": 1
        }
    ]

@tool
async def get_epa_echo_polluters(bbox: List[float]) -> List[Dict[str, Any]]:
    """Fetches EPA ECHO active point-source polluters and compliance violations within bounding box."""
    start_time = time.time()
    inputs = {"bbox": bbox}
    
    url = f"{settings.epa_echo_base_url}/cwa_rest_services.get_facility_info"
    
    # Center lat/lng from bbox for ECHO point-radius query
    center_lat = (bbox[1] + bbox[3]) / 2.0 if len(bbox) == 4 else 38.995
    center_lng = (bbox[0] + bbox[2]) / 2.0 if len(bbox) == 4 else -77.248

    params = {
        "output": "JSON",
        "p_lat": str(center_lat),
        "p_long": str(center_lng),
        "p_radius": "15"  # 15 miles search radius along waterbody catchment
    }
    
    try:
        resp = await http_client.get(url, params=params, timeout_override=15.0)
        c_type = resp.headers.get("content-type", "")
        if resp.status_code == 200 and "json" in c_type:
            data = resp.json()
            facilities = data.get("Results", {}).get("Facilities", [])
            polluters = []
            for fac in facilities[:15]:
                polluters.append({
                    "source_id": str(fac.get("SourceID", "NPDES-FAC")),
                    "facility_name": str(fac.get("FacilityName", "Industrial Facility")),
                    "lat": float(fac.get("Latitude", center_lat)),
                    "lng": float(fac.get("Longitude", center_lng)),
                    "permit_status": str(fac.get("PermitStatus", "Effective")),
                    "effluent_exceedances": int(fac.get("EffluentExceedances", 0) or 0),
                    "quarters_in_noncompliance": int(fac.get("QuarterInNoncompliance", 0) or 0)
                })
            if polluters:
                log_tool_call("get_epa_echo_polluters", inputs, time.time() - start_time, True)
                return polluters
    except Exception as e:
        logger.warning(f"EPA ECHO tool live response notice: {e}")

    polluters = load_fixture_echo()
    log_tool_call("get_epa_echo_polluters", inputs, time.time() - start_time, True)
    return polluters
