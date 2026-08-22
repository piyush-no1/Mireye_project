import pytest
from app.tools.mireye_geocode_tool import geocode_location

@pytest.mark.asyncio
async def test_geocode_location():
    res = await geocode_location.ainvoke({"query": "Potomac River near Great Falls"})
    assert "lat" in res
    assert "lng" in res
    assert "matched_name" in res
    assert res["lat"] != 0.0
