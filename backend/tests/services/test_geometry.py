import pytest
from app.services.geometry import simplify_geometry, extract_coords_from_geojson

def test_extract_coords_from_geojson(sample_nldi):
    coords = extract_coords_from_geojson(sample_nldi["flowline_geojson"])
    assert len(coords) == 5
    assert coords[0] == (-77.2600, 38.9900)

def test_simplify_geometry(sample_nldi):
    res = simplify_geometry(sample_nldi["flowline_geojson"])
    assert "bbox" in res
    assert len(res["bbox"]) == 4
    assert res["bbox"][0] <= res["bbox"][2]
    assert res["bbox"][1] <= res["bbox"][3]
    assert "bank_points" in res
    assert len(res["bank_points"]) > 0
