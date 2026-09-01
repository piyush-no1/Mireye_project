import pytest
from app.tools.epa_attains_tool import get_epa_attains_status

@pytest.mark.asyncio
async def test_get_epa_attains_status():
    res = await get_epa_attains_status.ainvoke({"bbox": [-77.26, 38.99, -77.24, 39.01]})
    units = res.get("assessment_units", []) if isinstance(res, dict) else res
    assert isinstance(units, list)
    assert len(units) > 0
    assert "overall_status" in units[0]
