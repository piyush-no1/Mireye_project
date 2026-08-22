import asyncio
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))
from app.config import settings
from app.services.http_client import http_client

async def main():
    bbox_str = "-83.69,43.01,-83.68,43.02" # Flint River
    
    # 1. MapServer
    map_url = "https://gispub.epa.gov/arcgis/rest/services/OW/ATTAINS_Assessment/MapServer/1/query"
    params1 = {
        "geometry": bbox_str,
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "assessmentunitidentifier,organizationid",
        "returnGeometry": "false",
        "f": "json"
    }
    resp1 = await http_client.get(map_url, params=params1)
    features = resp1.json().get("features", [])
    if not features:
        print("No features found in MapServer")
        return
        
    au_id = features[0]["attributes"]["assessmentunitidentifier"]
    org_id = features[0]["attributes"]["organizationid"]
    print(f"Found AU ID: {au_id}, Org ID: {org_id}")
    
    # 2. Tabular API for assessments (latest cycle)
    api_url = "https://api.epa.gov/attains/assessments"
    params2 = {"organizationId": org_id, "assessmentUnitIdentifier": au_id, "api_key": settings.epa_attains_api_key}
    resp2 = await http_client.get(api_url, params=params2)
    print("Latest assessments status:", resp2.status_code)
    try:
        with open("attains_schema_latest.json", "w") as f:
            json.dump(resp2.json(), f, indent=2)
        print("Wrote latest to attains_schema_latest.json")
    except:
        pass

    # 3. Tabular API for historical
    print("Fetching historical cycles...")
    for cycle in ["2024", "2022", "2020", "2018"]:
        params_hist = {"organizationId": org_id, "assessmentUnitIdentifier": au_id, "reportingCycle": cycle, "api_key": settings.epa_attains_api_key}
        r_hist = await http_client.get(api_url, params=params_hist)
        print(f"Cycle {cycle} status: {r_hist.status_code}")
        if r_hist.status_code == 200:
            count = r_hist.json().get("count", 0)
            print(f"  Count: {count}")
            if count > 0:
                with open(f"attains_schema_{cycle}.json", "w") as f:
                    json.dump(r_hist.json(), f, indent=2)

    # 4. Actions (TMDLs)
    actions_url = "https://api.epa.gov/attains/actions"
    params_act = {"organizationId": org_id, "actionIdentifier": "MI-2020-003", "api_key": settings.epa_attains_api_key}
    r_act = await http_client.get(actions_url, params=params_act)
    print(f"Action MI-2020-003 status: {r_act.status_code}")
    if r_act.status_code == 200:
        with open("attains_action.json", "w") as f:
            json.dump(r_act.json(), f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
