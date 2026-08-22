import pytest
from app.tools.usgs_nldi_tool import get_usgs_comid, trace_network

@pytest.mark.asyncio
async def test_get_usgs_comid():
    res = await get_usgs_comid.ainvoke({"lat": 38.9986, "lng": -77.2538})
    assert "comid" in res
    assert res["comid"] != ""

@pytest.mark.asyncio
async def test_trace_network():
    res = await trace_network.ainvoke({"comid": "4567891", "direction": "both"})
    assert isinstance(res, dict)
    assert "type" in res
