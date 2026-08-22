import pytest
from app.tools.usgs_nwis_tool import get_usgs_nwis_telemetry

@pytest.mark.asyncio
async def test_get_usgs_nwis_telemetry():
    res = await get_usgs_nwis_telemetry.ainvoke({"bbox": [-77.26, 38.99, -77.24, 39.01]})
    assert isinstance(res, list)
    assert len(res) > 0
    assert "site_id" in res[0]
