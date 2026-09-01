import time
import json
import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from langchain_core.tools import tool
from app.config import settings
from app.services.http_client import http_client
from app.core.logging import logger, log_tool_call

def load_fixture_attains() -> Dict[str, Any]:
    # Mock data for when API key is missing
    return {
        "summary": {
            "assessment_units": 1,
            "supporting_units": 0,
            "impaired_units": 1,
            "designated_use_summary": {},
            "persistent_impairments": [],
            "new_impairments": [],
            "resolved_impairments": [],
            "major_causes": [{"name": "Escherichia coli", "status": "Cause"}],
            "probable_sources": [],
            "tmdl_actions": [{"action_id": "TMDL-9812", "name": "Potomac River Bacterial TMDL"}],
            "historical_trend": "Persistent Impairment",
            "source": "ATTAINS",
            "retrieval_timestamp": datetime.utcnow().isoformat()
        },
        "assessment_units": [
            {
                "assessment_unit_id": "VAW-A03R_POT01A00",
                "waterbody_name": "Potomac River Mock",
                "assessment_cycle": "2026",
                "overall_status": "Impaired",
                "uses": [
                    {"use_name": "Recreation", "status": "Fully Supporting"},
                    {"use_name": "Aquatic Life", "status": "Not Supporting"}
                ],
                "impairments": [
                    {"cause": "Escherichia coli", "status": "Cause"}
                ],
                "history": [],
                "tmdl_actions": [{"action_id": "TMDL-9812", "name": "Potomac River Bacterial TMDL"}],
                "source": "ATTAINS"
            }
        ]
    }

async def fetch_attains_map(bbox_str: str) -> List[Dict[str, Any]]:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AquaTraceEnvironmentalApp/1.0"}
    map_params = {
        "where": "1=1",
        "geometry": bbox_str,
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "inSR": "4326",
        "outSR": "4326",
        "outFields": "assessmentunitidentifier,organizationid",
        "returnGeometry": "true",
        "f": "geojson"
    }
    
    au_list = []
    import httpx
    async with httpx.AsyncClient(timeout=4.0) as client:
        # Try Layer 1 (Polygons) first, then Layer 0 (Lines)
        for layer_id in [1, 0]:
            try:
                map_url = f"https://gispub.epa.gov/arcgis/rest/services/OW/ATTAINS_Assessment/MapServer/{layer_id}/query"
                map_resp = await client.get(map_url, params=map_params, headers=headers)
                if map_resp.status_code == 200:
                    map_data = map_resp.json()
                    for feature in map_data.get("features", []):
                        props = feature.get("properties", {})
                        au_id = props.get("assessmentunitidentifier")
                        org_id = props.get("organizationid")
                        geom = feature.get("geometry")
                        if au_id and org_id and not any(a["au_id"] == au_id for a in au_list):
                            au_list.append({"au_id": au_id, "org_id": org_id, "geometry": geom})
                    if au_list:
                        break
            except Exception as e:
                logger.debug(f"ATTAINS MapServer layer {layer_id} notice: {e}")
                
    return au_list[:5]

async def fetch_au_cycle(org_id: str, au_id: str, cycle: str = None, headers: dict = None) -> Dict[str, Any]:
    api_url = f"{settings.epa_attains_base_url}/assessments"
    api_params = {
        "organizationId": org_id,
        "assessmentUnitIdentifier": au_id
    }
    if cycle:
        api_params["reportingCycle"] = cycle
    if settings.epa_attains_api_key:
        api_params["api_key"] = settings.epa_attains_api_key
        
    try:
        resp = await http_client.get(api_url, params=api_params, headers=headers, timeout_override=7.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

async def fetch_action(org_id: str, action_id: str, headers: dict = None) -> Dict[str, Any]:
    api_url = f"{settings.epa_attains_base_url}/actions"
    api_params = {
        "organizationId": org_id,
        "actionIdentifier": action_id
    }
    if settings.epa_attains_api_key:
        api_params["api_key"] = settings.epa_attains_api_key
        
    try:
        resp = await http_client.get(api_url, params=api_params, headers=headers, timeout_override=7.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

def build_summary(au_results: List[Dict]) -> Dict[str, Any]:
    supporting = 0
    impaired = 0
    all_causes = []
    all_sources = []
    all_actions = []
    
    for au in au_results:
        if au.get("overall_status") in ("Impaired", "Not Supporting"):
            impaired += 1
        elif au.get("overall_status") == "Fully Supporting":
            supporting += 1
            
        for imp in au.get("impairments", []):
            cause_name = imp.get("cause")
            if cause_name and cause_name not in [c.get("name") for c in all_causes]:
                all_causes.append({"name": cause_name, "status": imp.get("status")})
            for src in imp.get("probable_sources", []):
                if src and src not in [s.get("name") for s in all_sources]:
                    all_sources.append({"name": src})
                    
        for act in au.get("tmdl_actions", []):
            if not any(a.get("action_id") == act.get("action_id") for a in all_actions):
                all_actions.append(act)
                
    return {
        "assessment_units": len(au_results),
        "supporting_units": supporting,
        "impaired_units": impaired,
        "designated_use_summary": {},
        "persistent_impairments": [],
        "new_impairments": [],
        "resolved_impairments": [],
        "major_causes": all_causes,
        "probable_sources": all_sources,
        "tmdl_actions": all_actions,
        "historical_trend": "Unknown",
        "source": "ATTAINS",
        "retrieval_timestamp": datetime.utcnow().isoformat()
    }

@tool
async def get_epa_attains_status(bbox: List[float]) -> Dict[str, Any]:
    """Fetches EPA ATTAINS Clean Water Act assessment unit impairment status."""
    start_time = time.time()
    inputs = {"bbox": bbox}
    
    bbox_str = ",".join(str(b) for b in bbox) if bbox and len(bbox) == 4 else "-77.26,38.99,-77.24,39.01"
    headers = {"User-Agent": "AquaTraceApp/1.0 (waterbody-pollution-agent)"}
    if settings.epa_attains_api_key:
        headers["X-API-Key"] = settings.epa_attains_api_key
        headers["api_key"] = settings.epa_attains_api_key

    if settings.epa_attains_api_key == "mock-attains-key":
        results = load_fixture_attains()
        log_tool_call("get_epa_attains_status", inputs, time.time() - start_time, True)
        return results

    try:
        au_list = await fetch_attains_map(bbox_str)
        if not au_list and bbox and len(bbox) == 4:
            exp_bbox = [bbox[0] - 0.05, bbox[1] - 0.05, bbox[2] + 0.05, bbox[3] + 0.05]
            exp_str = ",".join(str(b) for b in exp_bbox)
            au_list = await fetch_attains_map(exp_str)

        if not au_list:
            fixture = load_fixture_attains()
            log_tool_call("get_epa_attains_status", inputs, time.time() - start_time, True)
            return {"assessment_units": fixture.get("assessment_units", []), "summary": fixture.get("summary", {})}
            
        au_results = []
        
        for au_info in au_list:
            # Fetch latest
            latest_data = await fetch_au_cycle(au_info["org_id"], au_info["au_id"], None, headers)
            if not latest_data or not latest_data.get("items"):
                continue
                
            org_item = latest_data["items"][0]
            cycle_text = org_item.get("reportingCycleText", "")
            try:
                cycle_year = int(cycle_text)
            except:
                cycle_year = 2024
                
            assessments = org_item.get("assessments", [])
            if not assessments:
                continue
                
            au_item = assessments[0]
            
            # Process uses
            uses = []
            for u in au_item.get("useAttainments", []):
                metadata = u.get("assessmentMetadata")
                date = None
                if isinstance(metadata, dict):
                    activity = metadata.get("assessmentActivity")
                    if isinstance(activity, dict):
                        date = activity.get("assessmentDate")
                uses.append({
                    "use_name": u.get("useName"),
                    "status": u.get("useAttainmentCodeName"),
                    "assessment_date": date
                })
                
            # Process parameters & impairments
            impairments = []
            action_ids = set()
            for p in au_item.get("parameters", []):
                aff_uses = [u.get("associatedUseName") for u in p.get("associatedUses", [])]
                impaired_info = p.get("impairedWatersInformation", {}).get("listingInformation", {}) if isinstance(p.get("impairedWatersInformation"), dict) else {}
                
                # Get action IDs
                for act in p.get("associatedActions", []):
                    a_id = act.get("associatedActionIdentifier")
                    if a_id: action_ids.add(a_id)
                    
                # Sources for this parameter are often nested in probableSources which map back to causes
                prob_sources = []
                for src in au_item.get("probableSources", []):
                    associated_causes = [c.get("causeName") for c in src.get("associatedCauseNames", [])]
                    if p.get("parameterName") in associated_causes:
                        prob_sources.append(src.get("sourceName"))
                        
                impairments.append({
                    "cause": p.get("parameterName"),
                    "status": p.get("parameterStatusName"),
                    "affected_uses": aff_uses,
                    "probable_sources": prob_sources,
                    "first_listed_cycle": impaired_info.get("cycleFirstListedText"),
                    "tmdl_schedule": impaired_info.get("cycleScheduledForTMDLText")
                })
                
            # Fetch actions
            tmdl_actions = []
            action_tasks = [fetch_action(au_info["org_id"], a_id, headers) for a_id in list(action_ids)[:3]] # Limit 3
            if action_tasks:
                act_responses = await asyncio.gather(*action_tasks)
                for act_data in act_responses:
                    if act_data and act_data.get("items"):
                        a_item = act_data["items"][0].get("actions", [{}])[0]
                        if a_item:
                            tmdl_actions.append({
                                "action_id": a_item.get("actionIdentifier"),
                                "name": a_item.get("actionName"),
                                "type": a_item.get("actionTypeCode"),
                                "status": a_item.get("actionStatusCode"),
                                "completion_date": a_item.get("completionDate"),
                                "pollutants": [pol.get("pollutantName") for w in a_item.get("associatedWaters", {}).get("specificWaters", []) for pol in w.get("associatedPollutants", [])][:5] # Trim massive lists
                            })

            # Fetch history
            history = []
            hist_cycles = [str(cycle_year - 2), str(cycle_year - 4)]
            hist_tasks = [fetch_au_cycle(au_info["org_id"], au_info["au_id"], c, headers) for c in hist_cycles]
            hist_responses = await asyncio.gather(*hist_tasks)
            for i, h_data in enumerate(hist_responses):
                if h_data and h_data.get("items") and h_data["items"][0].get("assessments"):
                    h_au = h_data["items"][0]["assessments"][0]
                    history.append({
                        "cycle": hist_cycles[i],
                        "status": h_au.get("overallStatus"),
                        "impaired_uses": [u.get("useName") for u in h_au.get("useAttainments", []) if u.get("useAttainmentCodeName") in ("Not Supporting", "Impaired")],
                        "causes": [p.get("parameterName") for p in h_au.get("parameters", []) if p.get("parameterStatusName") == "Cause"]
                    })
                    
            au_results.append({
                "assessment_unit_id": au_item.get("assessmentUnitIdentifier"),
                "waterbody_name": au_item.get("assessmentUnitName", None),
                "assessment_cycle": cycle_text,
                "overall_status": au_item.get("overallStatus", "Unknown"),
                "uses": uses,
                "impairments": impairments,
                "history": history,
                "tmdl_actions": tmdl_actions,
                "source": "ATTAINS",
                "geometry": au_info.get("geometry")
            })
            
        final_result = {
            "assessment_units": au_results,
            "summary": build_summary(au_results)
        }
                        
        log_tool_call("get_epa_attains_status", inputs, time.time() - start_time, True)
        return final_result
    except Exception as e:
        logger.warning(f"EPA ATTAINS deep extraction notice: {e}")
        import traceback
        traceback.print_exc()

    log_tool_call("get_epa_attains_status", inputs, time.time() - start_time, True)
    return {"assessment_units": [], "summary": build_summary([])}
