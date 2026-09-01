import pytest
from app.services.geometry import simplify_geometry

def test_river_linestring_geometry():
    river_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [-77.25, 38.99],
                [-77.24, 38.98],
                [-77.23, 38.97],
                [-77.22, 38.96],
                [-77.21, 38.95],
                [-77.20, 38.94],
                [-77.19, 38.93],
                [-77.18, 38.92],
                [-77.17, 38.91],
                [-77.16, 38.90],
                [-77.15, 38.89],
                [-77.14, 38.88]
            ]
        }
    }
    
    result = simplify_geometry(river_geojson)
    assert result["waterbody_type"] == "river"
    assert len(result["bank_points"]) == 10
    assert result["bbox"] == [-77.25, 38.88, -77.14, 38.99]
    print("RIVER TEST PASSED:", result["waterbody_type"], len(result["bank_points"]))

def test_pond_lake_polygon_geometry():
    # Square pond polygon
    pond_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-77.30, 38.90],
                            [-77.20, 38.90],
                            [-77.20, 39.00],
                            [-77.30, 39.00],
                            [-77.30, 38.90]
                        ]
                    ]
                }
            }
        ]
    }
    
    result = simplify_geometry(pond_geojson, center_lat=38.95, center_lng=-77.25)
    assert result["waterbody_type"] == "pond_lake"
    # Should contain shoreline perimeter points + 1 centroid deep water point
    assert len(result["bank_points"]) == 6  # 5 vertices + 1 centroid point
    assert result["center"]["lat"] == 38.94
    assert result["center"]["lng"] == -77.26
    print("POND / LAKE TEST PASSED:", result["waterbody_type"], len(result["bank_points"]), result["center"])
