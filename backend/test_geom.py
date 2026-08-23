import requests

url = 'https://gispub.epa.gov/arcgis/rest/services/OW/ATTAINS_Assessment/MapServer/1/query'
params = {
    'geometry': '-77.26,38.99,-77.24,39.01',
    'geometryType': 'esriGeometryEnvelope',
    'inSR': '4326',
    'spatialRel': 'esriSpatialRelIntersects',
    'outFields': 'assessmentunitidentifier,organizationid',
    'returnGeometry': 'true',
    'f': 'geojson'
}
r = requests.get(url, params=params)
data = r.json()
print(f'Keys: {data.keys()}')
print(f'Feature count: {len(data.get("features", []))}')
if data.get("features"):
    print("Feature keys:", data["features"][0].keys())
    print("Geometry type:", data["features"][0].get("geometry", {}).get("type"))
    print("Properties:", data["features"][0].get("properties"))
