import pytest
from app.services.scoring import compute_deterministic_risk_summary, reason_and_score_with_openai

def test_compute_deterministic_risk_summary_clean():
    res = compute_deterministic_risk_summary(
        attains_status=[],
        polluters=[],
        water_samples=[],
        land_risk_points=[]
    )
    assert res["rating"] == "A"
    assert res["label"] == "Low Risk"

def test_compute_deterministic_risk_summary_impaired(sample_attains, sample_echo, sample_wqp, sample_land_risk):
    res = compute_deterministic_risk_summary(
        attains_status=sample_attains,
        polluters=sample_echo,
        water_samples=sample_wqp,
        land_risk_points=sample_land_risk
    )
    assert res["rating"] in ("B", "C", "D", "F")
    assert res["label"] in ("Limited Risk", "Moderate Risk", "High Risk", "Critical Risk")
    assert any("Impaired" in factor for factor in res["risk_factors"])

@pytest.mark.asyncio
async def test_reason_and_score_with_openai_fallback(sample_attains, sample_echo, sample_wqp, sample_land_risk):
    res = await reason_and_score_with_openai(
        query="Potomac River near Great Falls",
        attains_status=sample_attains,
        polluters=sample_echo,
        water_samples=sample_wqp,
        land_risk_points=sample_land_risk
    )
    assert "rating" in res
    assert "label" in res
    assert "notes" in res
    assert res["rating"] in ("A", "B", "C", "D", "F")
