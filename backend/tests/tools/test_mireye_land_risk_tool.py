import pytest
from app.tools.mireye_land_risk_tool import get_mireye_land_risk

@pytest.mark.asyncio
async def test_get_mireye_land_risk():
    res = await get_mireye_land_risk.ainvoke({"points": [{"lat": 38.995, "lng": -77.255}]})
    assert isinstance(res, list)
    assert len(res) > 0
    assert "slope_degrees" in res[0]
