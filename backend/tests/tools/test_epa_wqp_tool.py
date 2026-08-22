import pytest
from app.tools.epa_wqp_tool import get_epa_water_quality

@pytest.mark.asyncio
async def test_get_epa_water_quality():
    res = await get_epa_water_quality.ainvoke({"bbox": [-77.26, 38.99, -77.24, 39.01]})
    assert isinstance(res, list)
    assert len(res) > 0
    assert "characteristic_name" in res[0]
