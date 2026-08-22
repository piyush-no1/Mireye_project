import pytest
from app.tools.epa_echo_tool import get_epa_echo_polluters

@pytest.mark.asyncio
async def test_get_epa_echo_polluters():
    res = await get_epa_echo_polluters.ainvoke({"bbox": [-77.26, 38.99, -77.24, 39.01]})
    assert isinstance(res, list)
    assert len(res) > 0
    assert "facility_name" in res[0]
