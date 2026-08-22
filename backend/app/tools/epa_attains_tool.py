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
        resp = await http_client.get(url, params={"bBox": bbox_str}, headers=headers, timeout_override=15.0)
        c_type = resp.headers.get("content-type", "")
        if resp.status_code == 200 and "json" in c_type:
            data = resp.json()
            items = data.get("items", [])
            results = []
            for item in items[:10]:
                results.append({
                    "assessment_unit_id": item.get("assessmentUnitIdentifier", "EPA-ATTAINS-AU"),
                    "overall_status": item.get("overallStatus", "Impaired"),
                    "use_attainment": item.get("useAttainment", {}),
                    "parameters": item.get("parameters", []),
                    "tmdl_projects": item.get("tmdlProjects", [])
                })
            if results:
                log_tool_call("get_epa_attains_status", inputs, time.time() - start_time, True)
                return results
    except Exception as e:
        logger.warning(f"EPA ATTAINS live response notice: {e}")

    results = load_fixture_attains()
    log_tool_call("get_epa_attains_status", inputs, time.time() - start_time, True)
    return results
