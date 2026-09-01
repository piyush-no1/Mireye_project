import pytest
from app.agent.state import AssessmentState
from app.agent.nodes.geocode_node import geocode_node
from app.agent.nodes.hydrology_node import hydrology_node
from app.agent.nodes.spatial_translation_node import spatial_translation_node
from app.agent.nodes.industrial_specialist_node import industrial_specialist_node
from app.agent.nodes.agricultural_specialist_node import agricultural_specialist_node
from app.agent.nodes.master_orchestration_node import master_orchestration_node
from app.agent.graph import assessment_graph

@pytest.mark.asyncio
async def test_industrial_specialist_node_unit():
    state = AssessmentState(
        run_id="test-ind-1",
        query="Test Waterway",
        resolved_location={"lat": 38.995, "lng": -77.248, "matched_name": "Test Waterway"},
        hydrology={"bbox": [-77.3, 38.9, -77.2, 39.0], "comid": "12345"},
        polluters=[
            {"source_id": "FAC1", "facility_name": "Test Plant", "lat": 38.99, "lng": -77.25, "permit_status": "Effective", "effluent_exceedances": 3, "quarters_in_noncompliance": 2}
        ]
    )
    res = await industrial_specialist_node(state)
    assert res.industrial_analysis is not None
    assert "risk_score" in res.industrial_analysis
    assert "risk_rating" in res.industrial_analysis

@pytest.mark.asyncio
async def test_agricultural_specialist_node_unit():
    state = AssessmentState(
        run_id="test-agri-1",
        query="Test Farm Creek",
        resolved_location={"lat": 38.995, "lng": -77.248, "matched_name": "Test Farm Creek"},
        hydrology={"bbox": [-77.3, 38.9, -77.2, 39.0], "comid": "12345"},
        water_quality_samples=[
            {"monitoring_location_id": "S1", "characteristic_name": "Nitrate", "result_value": 12.5, "unit_code": "mg/L"}
        ]
    )
    res = await agricultural_specialist_node(state)
    assert res.agricultural_analysis is not None
    assert "risk_score" in res.agricultural_analysis
    assert "risk_rating" in res.agricultural_analysis

@pytest.mark.asyncio
async def test_master_orchestration_node_unit():
    state = AssessmentState(
        run_id="test-orch-1",
        query="Test River Corridor",
        resolved_location={"lat": 38.995, "lng": -77.248, "matched_name": "Test River Corridor"},
        industrial_analysis={"risk_score": 75, "risk_rating": "D", "chemical_signature_match": "NPDES Violations"},
        agricultural_analysis={"risk_score": 40, "risk_rating": "B", "nutrient_signature_match": "Moderate Runoff"}
    )
    res = await master_orchestration_node(state)
    assert res.master_synthesis is not None
    assert "dominant_pollution_vector" in res.master_synthesis
    assert res.risk_summary is not None
    assert res.risk_summary["rating"] in ["A", "B", "C", "D", "F"]

@pytest.mark.asyncio
async def test_complete_graph_execution():
    state = AssessmentState(
        run_id="test-full-graph-1",
        query="Potomac River",
        input_lat=38.995,
        input_lng=-77.248
    )
    res = await assessment_graph.ainvoke(state)
    status = res.get("status") if isinstance(res, dict) else res.status
    ind = res.get("industrial_analysis") if isinstance(res, dict) else res.industrial_analysis
    agri = res.get("agricultural_analysis") if isinstance(res, dict) else res.agricultural_analysis
    synth = res.get("master_synthesis") if isinstance(res, dict) else res.master_synthesis
    risk = res.get("risk_summary") if isinstance(res, dict) else res.risk_summary

    assert status in ["completed", "assessment_completed"]
    assert ind is not None
    assert agri is not None
    assert synth is not None
    assert risk is not None
