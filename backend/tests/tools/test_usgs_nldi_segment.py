import pytest
from app.tools.usgs_nldi_tool import fetch_river_segment_flowline, trace_network

@pytest.mark.asyncio
async def test_fetch_river_segment_flowline():
    # Ohio River from Point A (near Cincinnati, OH) to Point B (near Neville, OH)
    start_lat, start_lng = 38.90, -84.30
    end_lat, end_lng = 38.78, -84.22
    
    res = await fetch_river_segment_flowline(start_lat, start_lng, end_lat, end_lng, "Ohio River")
    assert res is not None
    assert "features" in res
    assert len(res["features"]) > 0
    geom = res["features"][0]["geometry"]
    assert geom["type"] == "LineString"
    assert len(geom["coordinates"]) >= 2
    assert res["features"][0]["properties"].get("segment_mode") is True

@pytest.mark.asyncio
async def test_trace_network_segment_mode():
    res = await trace_network.ainvoke({
        "comid": "custom",
        "start_lat": 38.90,
        "start_lng": -84.30,
        "end_lat": 38.78,
        "end_lng": -84.22,
        "query_name": "Ohio River"
    })
    assert res is not None
    assert "features" in res
    assert len(res["features"]) > 0
