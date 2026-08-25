import pytest
from app.tools.epa_attains_tool import get_epa_attains_status

@pytest.mark.asyncio
async def test_get_epa_attains_status():
    res = await get_epa_attains_status.ainvoke({"bbox": [-77.26, 38.99, -77.24, 39.01]})
    if isinstance(res, dict):
        assert "assessment_units" in res
        units = res["assessment_units"]
    else:
        assert isinstance(res, list)
        units = res
    assert len(units) > 0
    assert "overall_status" in units[0]

