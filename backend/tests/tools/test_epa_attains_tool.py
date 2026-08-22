import pytest
from app.tools.epa_attains_tool import get_epa_attains_status

@pytest.mark.asyncio
async def test_get_epa_attains_status():
    res = await get_epa_attains_status.ainvoke({"bbox": [-77.26, 38.99, -77.24, 39.01]})
    assert isinstance(res, list)
    assert len(res) > 0
    assert "overall_status" in res[0]
