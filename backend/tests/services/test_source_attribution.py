import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import unittest.mock
from app.services.source_attribution import run_source_attribution
from app.config import settings
import json
from langchain_core.messages import AIMessage, ToolMessage

@pytest.fixture
def mock_openai_key():
    old_key = settings.openai_api_key
    settings.openai_api_key = "test-key"
    yield
    settings.openai_api_key = old_key

@pytest.fixture
def no_openai_key():
    old_key = settings.openai_api_key
    settings.openai_api_key = "mock-openai-key"
    yield
    settings.openai_api_key = old_key

def create_mock_response(json_output, tool_calls=None):
    messages = []
    
    if tool_calls:
        # Add mock tool calls and responses
        for tc in tool_calls:
            ai_msg = AIMessage(content="", tool_calls=[{"name": tc["tool"], "id": tc["id"], "args": tc.get("args", {})}])
            tool_msg = ToolMessage(content=tc["response"], tool_call_id=tc["id"], name=tc["tool"])
            messages.extend([ai_msg, tool_msg])
            
    final_msg = AIMessage(content=json.dumps(json_output))
    messages.append(final_msg)
    
    return {"messages": messages}

@pytest.mark.asyncio
async def test_run_source_attribution_skips_when_no_key(no_openai_key):
    res, log = await run_source_attribution(
        query="Test River",
        attains_status=[],
        polluters=[],
        water_samples=[],
        land_risk_points=[]
    )
    assert "impairments" in res
    assert "overall_source_reasoning" in res
    assert log == []
    assert res["overall_source_reasoning"] == "Agent disabled."

@pytest.mark.asyncio
@patch("app.services.source_attribution.create_source_reasoning_agent")
async def test_clean_corridor(mock_agent_factory, mock_openai_key):
    # Setup mock agent
    mock_agent = AsyncMock()
    mock_agent_factory.return_value = mock_agent
    
    clean_json = {
        "impairments": [],
        "major_source_findings": ["No primary path impairments found."],
        "source_data_gaps": [],
        "overall_source_reasoning": "The corridor is clean."
    }
    
    mock_agent.ainvoke.return_value = create_mock_response(clean_json)
    
    res, log = await run_source_attribution(
        query="Clean River",
        attains_status=[],
        polluters=[],
        water_samples=[],
        land_risk_points=[]
    )
    
    assert len(res["impairments"]) == 0
    assert len(log) == 0

@pytest.mark.asyncio
@patch("app.services.source_attribution.create_source_reasoning_agent")
async def test_dynamic_mireye_investigation(mock_agent_factory, mock_openai_key):
    mock_agent = AsyncMock()
    mock_agent_factory.return_value = mock_agent
    
    mireye_result = {
        "source": "MOCK",
        "agriculture_percentage": "35%",
        "developed_percentage": "10%"
    }
    
    json_output = {
        "impairments": [{
            "impairment": "Nutrients",
            "affected_uses": ["Aquatic Life"],
            "sources": [{
                "source_type": "Nonpoint",
                "source_name": "Agriculture",
                "source_id": None,
                "latitude": None,
                "longitude": None,
                "geography_type": "watershed",
                "geography_id": "upstream-huc",
                "relationship_to_primary_path": "upstream",
                "attribution": "LIKELY",
                "confidence": "MEDIUM",
                "supporting_evidence": ["Mireye indicates 35% upstream agriculture"],
                "contradicting_evidence": [],
                "evidence_sources": ["Mireye"]
            }]
        }],
        "major_source_findings": ["Upstream agriculture is a likely contributor."],
        "source_data_gaps": [],
        "overall_source_reasoning": "Based on Mireye fetch, agriculture is dominant."
    }
    
    # Simulate one Mireye fetch tool loop
    mock_agent.ainvoke.return_value = create_mock_response(json_output, tool_calls=[
        {"tool": "query_mireye_fetch", "id": "call_123", "args": {"lat": 38.0, "lng": -77.0, "reason": "Need to confirm agriculture"}, "response": json.dumps(mireye_result)}
    ])
    
    res, log = await run_source_attribution(
        query="Impaired River",
        attains_status=[{"is_primary_path": True}],
        polluters=[],
        water_samples=[],
        land_risk_points=[]
    )
    
    assert len(res["impairments"]) == 1
    assert res["impairments"][0]["sources"][0]["source_name"] == "Agriculture"
    assert len(log) == 1
    assert log[0]["tool"] == "query_mireye_fetch"
    assert log[0]["reason"] == "Need to confirm agriculture"
    assert log[0]["result_status"] == "success"
    
    # Verify recursion limit is passed to ainvoke
    mock_agent.ainvoke.assert_called_with(unittest.mock.ANY, config={"recursion_limit": 15})

@pytest.mark.asyncio
@patch("app.services.source_attribution.create_source_reasoning_agent")
async def test_nearby_context_trap(mock_agent_factory, mock_openai_key):
    mock_agent = AsyncMock()
    mock_agent_factory.return_value = mock_agent
    
    json_output = {
        "impairments": [],
        "major_source_findings": ["Only nearby assessments are impaired, primary path is clean."],
        "source_data_gaps": [],
        "overall_source_reasoning": "No sources to attribute as primary path is clean."
    }
    
    mock_agent.ainvoke.return_value = create_mock_response(json_output)
    
    res, log = await run_source_attribution(
        query="Trap River",
        attains_status=[{"is_primary_path": False, "status": "Impaired"}], # Should be ignored by LLM
        polluters=[],
        water_samples=[],
        land_risk_points=[]
    )
    
    assert len(res["impairments"]) == 0

@pytest.mark.asyncio
@patch("app.services.source_attribution.create_source_reasoning_agent")
async def test_max_calls_enforcement(mock_agent_factory, mock_openai_key):
    mock_agent = AsyncMock()
    mock_agent_factory.return_value = mock_agent
    
    from langgraph.errors import GraphRecursionError
    
    mock_agent.ainvoke.side_effect = GraphRecursionError("Recursion limit exceeded")
    
    res, log = await run_source_attribution(
        query="Infinite Loop River",
        attains_status=[{"is_primary_path": True, "status": "Impaired"}],
        polluters=[],
        water_samples=[],
        land_risk_points=[]
    )
    
    # Verify the fallback mechanism caught it
    assert "Error running source attribution" in res["overall_source_reasoning"]
    assert len(log) == 0


@pytest.mark.asyncio
@patch("app.services.source_attribution.create_source_reasoning_agent")
async def test_mireye_discovery_power_industrial(mock_agent_factory, mock_openai_key):
    mock_agent = AsyncMock()
    mock_agent_factory.return_value = mock_agent
    
    mireye_result = {"source": "Mireye", "infrastructure": ["Coal Power Plant"]}
    json_output = {
        "impairments": [{"impairment": "Thermal", "affected_uses": [], "sources": [{"source_type": "Point", "source_name": "Coal Power Plant", "source_id": None, "latitude": None, "longitude": None, "geography_type": "point", "geography_id": None, "relationship_to_primary_path": "upstream", "attribution": "POSSIBLE", "confidence": "MEDIUM", "supporting_evidence": ["Mireye found a power plant upstream"], "contradicting_evidence": [], "evidence_sources": ["Mireye"]}]}],
        "major_source_findings": ["Thermal impairment possibly due to power plant."],
        "source_data_gaps": [],
        "overall_source_reasoning": "Mireye discovered a power plant."
    }
    
    mock_agent.ainvoke.return_value = create_mock_response(json_output, tool_calls=[
        {"tool": "query_mireye_fetch", "id": "call_pwr", "args": {"reason": "check industrial infrastructure"}, "response": json.dumps(mireye_result)}
    ])
    
    res, log = await run_source_attribution(query="Thermal River", attains_status=[{"is_primary_path": True, "status": "Impaired"}], polluters=[], water_samples=[], land_risk_points=[])
    
    assert res["impairments"][0]["sources"][0]["source_name"] == "Coal Power Plant"
    assert log[0]["tool"] == "query_mireye_fetch"

@pytest.mark.asyncio
@patch("app.services.source_attribution.create_source_reasoning_agent")
async def test_mireye_discovery_disconnected_source(mock_agent_factory, mock_openai_key):
    mock_agent = AsyncMock()
    mock_agent_factory.return_value = mock_agent
    
    mireye_result = {"source": "Mireye", "facility": "Chemical Plant", "location": "Downstream"}
    json_output = {
        "impairments": [{"impairment": "Toxins", "affected_uses": [], "sources": [{"source_type": "Industrial", "source_name": "Chemical Plant", "source_id": None, "latitude": None, "longitude": None, "geography_type": "point", "geography_id": None, "relationship_to_primary_path": "downstream", "attribution": "UNSUPPORTED", "confidence": "HIGH", "supporting_evidence": [], "contradicting_evidence": ["Facility is downstream from impairment"], "evidence_sources": ["Mireye"]}]}],
        "major_source_findings": ["Chemical plant found but is downstream."],
        "source_data_gaps": [],
        "overall_source_reasoning": "Downstream facility excluded."
    }
    
    mock_agent.ainvoke.return_value = create_mock_response(json_output, tool_calls=[
        {"tool": "query_mireye_fetch", "id": "call_disc", "args": {"reason": "investigate infrastructure"}, "response": json.dumps(mireye_result)}
    ])
    
    res, log = await run_source_attribution(query="Toxin River", attains_status=[{"is_primary_path": True, "status": "Impaired"}], polluters=[], water_samples=[], land_risk_points=[])
    
    assert res["impairments"][0]["sources"][0]["attribution"] == "UNSUPPORTED"
    assert "downstream" in res["impairments"][0]["sources"][0]["relationship_to_primary_path"].lower()

@pytest.mark.asyncio
@patch("app.services.source_attribution.create_source_reasoning_agent")
async def test_mireye_discovery_competing_sources(mock_agent_factory, mock_openai_key):
    mock_agent = AsyncMock()
    mock_agent_factory.return_value = mock_agent
    
    mireye_result = {"source": "Mireye", "facility": "Upstream Factory"}
    json_output = {
        "impairments": [{"impairment": "Metals", "affected_uses": [], "sources": [{"source_type": "Industrial", "source_name": "Upstream Factory", "source_id": None, "latitude": None, "longitude": None, "geography_type": "point", "geography_id": None, "relationship_to_primary_path": "upstream", "attribution": "LIKELY", "confidence": "HIGH", "supporting_evidence": ["Mireye identified factory", "ECHO confirms violation"], "contradicting_evidence": [], "evidence_sources": ["Mireye", "ECHO"]}]}],
        "major_source_findings": ["Upstream factory confirmed by ECHO."],
        "source_data_gaps": [],
        "overall_source_reasoning": "ECHO validated Mireye discovery."
    }
    
    mock_agent.ainvoke.return_value = create_mock_response(json_output, tool_calls=[
        {"tool": "query_mireye_fetch", "id": "call_comp", "args": {"reason": "check facilities"}, "response": json.dumps(mireye_result)}
    ])
    
    res, log = await run_source_attribution(query="Metal River", attains_status=[{"is_primary_path": True, "status": "Impaired"}], polluters=[{"facility_name": "Upstream Factory"}], water_samples=[], land_risk_points=[])
    
    assert res["impairments"][0]["sources"][0]["attribution"] == "LIKELY"
    assert "ECHO" in res["impairments"][0]["sources"][0]["evidence_sources"]

@pytest.mark.asyncio
@patch("app.services.source_attribution.create_source_reasoning_agent")
async def test_mireye_discovery_oil_gas(mock_agent_factory, mock_openai_key):
    mock_agent = AsyncMock()
    mock_agent_factory.return_value = mock_agent
    
    mireye_result = {"source": "Mireye", "infrastructure": ["Pipeline compressor station"]}
    json_output = {
        "impairments": [{"impairment": "Petroleum", "affected_uses": [], "sources": [{"source_type": "Point", "source_name": "Pipeline compressor station", "source_id": None, "latitude": None, "longitude": None, "geography_type": "point", "geography_id": None, "relationship_to_primary_path": "upstream", "attribution": "POSSIBLE", "confidence": "MEDIUM", "supporting_evidence": ["Mireye found oil/gas infrastructure upstream"], "contradicting_evidence": [], "evidence_sources": ["Mireye"]}]}],
        "major_source_findings": ["Petroleum impairment possibly due to compressor station."],
        "source_data_gaps": [],
        "overall_source_reasoning": "Mireye discovered oil and gas infrastructure."
    }
    
    mock_agent.ainvoke.return_value = create_mock_response(json_output, tool_calls=[
        {"tool": "query_mireye_fetch", "id": "call_oil", "args": {"reason": "check oil and gas infrastructure"}, "response": json.dumps(mireye_result)}
    ])
    
    res, log = await run_source_attribution(query="Oil River", attains_status=[{"is_primary_path": True, "status": "Impaired"}], polluters=[], water_samples=[], land_risk_points=[])
    
    assert res["impairments"][0]["sources"][0]["source_name"] == "Pipeline compressor station"
    assert log[0]["tool"] == "query_mireye_fetch"

@pytest.mark.asyncio
@patch("app.services.source_attribution.create_source_reasoning_agent")
async def test_mireye_discovery_legacy_contamination(mock_agent_factory, mock_openai_key):
    mock_agent = AsyncMock()
    mock_agent_factory.return_value = mock_agent
    
    mireye_result = {"source": "Mireye", "infrastructure": ["Superfund site"]}
    json_output = {
        "impairments": [{"impairment": "Heavy Metals", "affected_uses": [], "sources": [{"source_type": "Legacy", "source_name": "Superfund site", "source_id": None, "latitude": None, "longitude": None, "geography_type": "polygon", "geography_id": None, "relationship_to_primary_path": "adjacent", "attribution": "LIKELY", "confidence": "HIGH", "supporting_evidence": ["Mireye found Superfund site adjacent to river"], "contradicting_evidence": [], "evidence_sources": ["Mireye"]}]}],
        "major_source_findings": ["Heavy metals impairment likely due to Superfund site."],
        "source_data_gaps": [],
        "overall_source_reasoning": "Mireye discovered legacy contamination."
    }
    
    mock_agent.ainvoke.return_value = create_mock_response(json_output, tool_calls=[
        {"tool": "query_mireye_fetch", "id": "call_legacy", "args": {"reason": "check legacy contamination"}, "response": json.dumps(mireye_result)}
    ])
    
    res, log = await run_source_attribution(query="Metal River", attains_status=[{"is_primary_path": True, "status": "Impaired"}], polluters=[], water_samples=[], land_risk_points=[])
    
    assert res["impairments"][0]["sources"][0]["source_name"] == "Superfund site"
    assert log[0]["tool"] == "query_mireye_fetch"

@pytest.mark.asyncio
@patch("app.services.source_attribution.create_source_reasoning_agent")
async def test_mireye_discovery_wastewater_crosscheck(mock_agent_factory, mock_openai_key):
    mock_agent = AsyncMock()
    mock_agent_factory.return_value = mock_agent
    
    mireye_result = {"source": "Mireye", "infrastructure": ["Wastewater treatment plant"]}
    json_output = {
        "impairments": [{"impairment": "E. coli", "affected_uses": [], "sources": [{"source_type": "Point", "source_name": "Wastewater treatment plant", "source_id": None, "latitude": None, "longitude": None, "geography_type": "point", "geography_id": None, "relationship_to_primary_path": "upstream", "attribution": "POSSIBLE", "confidence": "MEDIUM", "supporting_evidence": ["Mireye found WWTP upstream"], "contradicting_evidence": [], "evidence_sources": ["Mireye"]}]}],
        "major_source_findings": ["E. coli impairment possibly due to WWTP."],
        "source_data_gaps": [],
        "overall_source_reasoning": "Mireye discovered wastewater infrastructure."
    }
    
    mock_agent.ainvoke.return_value = create_mock_response(json_output, tool_calls=[
        {"tool": "query_mireye_fetch", "id": "call_waste", "args": {"reason": "check wastewater infrastructure"}, "response": json.dumps(mireye_result)}
    ])
    
    res, log = await run_source_attribution(query="Bacteria River", attains_status=[{"is_primary_path": True, "status": "Impaired"}], polluters=[], water_samples=[], land_risk_points=[])
    
    assert res["impairments"][0]["sources"][0]["source_name"] == "Wastewater treatment plant"
    assert log[0]["tool"] == "query_mireye_fetch"

@pytest.mark.asyncio
@patch("app.services.source_attribution.create_source_reasoning_agent")
async def test_mireye_discovery_parcel_ownership(mock_agent_factory, mock_openai_key):
    mock_agent = AsyncMock()
    mock_agent_factory.return_value = mock_agent
    
    mireye_result = {"source": "Mireye", "parcel_owner": "Industrial Corp LLC"}
    json_output = {
        "impairments": [{"impairment": "Toxins", "affected_uses": [], "sources": [{"source_type": "Point", "source_name": "Industrial Corp LLC Facility", "source_id": None, "latitude": None, "longitude": None, "geography_type": "point", "geography_id": None, "relationship_to_primary_path": "upstream", "attribution": "POSSIBLE", "confidence": "LOW", "supporting_evidence": ["Mireye identified parcel ownership as Industrial Corp LLC"], "contradicting_evidence": [], "evidence_sources": ["Mireye"]}]}],
        "major_source_findings": ["Toxins impairment possibly due to Industrial Corp LLC facility."],
        "source_data_gaps": [],
        "overall_source_reasoning": "Mireye identified parcel ownership."
    }
    
    mock_agent.ainvoke.return_value = create_mock_response(json_output, tool_calls=[
        {"tool": "query_mireye_fetch", "id": "call_parcel", "args": {"reason": "check parcel ownership"}, "response": json.dumps(mireye_result)}
    ])
    
    res, log = await run_source_attribution(query="Toxin River", attains_status=[{"is_primary_path": True, "status": "Impaired"}], polluters=[], water_samples=[], land_risk_points=[])
    
    assert res["impairments"][0]["sources"][0]["source_name"] == "Industrial Corp LLC Facility"
    assert log[0]["tool"] == "query_mireye_fetch"

@pytest.mark.asyncio
@patch("app.services.source_attribution.create_source_reasoning_agent")
async def test_mireye_discovery_natural_groundwater(mock_agent_factory, mock_openai_key):
    mock_agent = AsyncMock()
    mock_agent_factory.return_value = mock_agent
    
    mireye_result = {"source": "Mireye", "hazards": ["Karst susceptibility"]}
    json_output = {
        "impairments": [{"impairment": "Pathogens", "affected_uses": [], "sources": [{"source_type": "Natural", "source_name": "Karst groundwater pathway", "source_id": None, "latitude": None, "longitude": None, "geography_type": "region", "geography_id": None, "relationship_to_primary_path": "within_watershed", "attribution": "POSSIBLE", "confidence": "LOW", "supporting_evidence": ["Mireye identified Karst susceptibility"], "contradicting_evidence": [], "evidence_sources": ["Mireye"]}]}],
        "major_source_findings": ["Pathogens impairment possibly due to Karst groundwater pathway."],
        "source_data_gaps": [],
        "overall_source_reasoning": "Mireye discovered natural groundwater hazards."
    }
    
    mock_agent.ainvoke.return_value = create_mock_response(json_output, tool_calls=[
        {"tool": "query_mireye_fetch", "id": "call_natural", "args": {"reason": "check groundwater hazards"}, "response": json.dumps(mireye_result)}
    ])
    
    res, log = await run_source_attribution(query="Pathogen River", attains_status=[{"is_primary_path": True, "status": "Impaired"}], polluters=[], water_samples=[], land_risk_points=[])
    
    assert res["impairments"][0]["sources"][0]["source_name"] == "Karst groundwater pathway"
    assert log[0]["tool"] == "query_mireye_fetch"

@pytest.mark.asyncio
@patch("app.services.source_attribution.create_source_reasoning_agent")
async def test_mireye_discovery_poi_based(mock_agent_factory, mock_openai_key):
    mock_agent = AsyncMock()
    mock_agent_factory.return_value = mock_agent
    
    mireye_result = {"source": "Mireye", "POIs": ["Gas station"]}
    json_output = {
        "impairments": [{"impairment": "Petroleum", "affected_uses": [], "sources": [{"source_type": "Point", "source_name": "Gas station", "source_id": None, "latitude": None, "longitude": None, "geography_type": "point", "geography_id": None, "relationship_to_primary_path": "adjacent", "attribution": "POSSIBLE", "confidence": "LOW", "supporting_evidence": ["Mireye identified a gas station adjacent to river"], "contradicting_evidence": [], "evidence_sources": ["Mireye"]}]}],
        "major_source_findings": ["Petroleum impairment possibly due to adjacent gas station."],
        "source_data_gaps": [],
        "overall_source_reasoning": "Mireye discovered POI."
    }
    
    mock_agent.ainvoke.return_value = create_mock_response(json_output, tool_calls=[
        {"tool": "query_mireye_fetch", "id": "call_poi", "args": {"reason": "check POIs"}, "response": json.dumps(mireye_result)}
    ])
    
    res, log = await run_source_attribution(query="Petroleum River", attains_status=[{"is_primary_path": True, "status": "Impaired"}], polluters=[], water_samples=[], land_risk_points=[])
    
    assert res["impairments"][0]["sources"][0]["source_name"] == "Gas station"
    assert log[0]["tool"] == "query_mireye_fetch"

@pytest.mark.asyncio
@patch("app.services.source_attribution.create_source_reasoning_agent")
async def test_mireye_discovery_epa_validation(mock_agent_factory, mock_openai_key):
    mock_agent = AsyncMock()
    mock_agent_factory.return_value = mock_agent
    
    mireye_result = {"source": "Mireye", "facility": "Upstream Factory"}
    json_output = {
        "impairments": [{"impairment": "Metals", "affected_uses": [], "sources": [{"source_type": "Industrial", "source_name": "Upstream Factory", "source_id": "ECHO-123", "latitude": None, "longitude": None, "geography_type": "point", "geography_id": None, "relationship_to_primary_path": "upstream", "attribution": "DOCUMENTED", "confidence": "HIGH", "supporting_evidence": ["Mireye identified factory", "ECHO confirms violation and links to ATTAINS"], "contradicting_evidence": [], "evidence_sources": ["Mireye", "ECHO", "ATTAINS"]}]}],
        "major_source_findings": ["Upstream factory validated by EPA ECHO."],
        "source_data_gaps": [],
        "overall_source_reasoning": "ECHO and ATTAINS validated Mireye discovery."
    }
    
    mock_agent.ainvoke.return_value = create_mock_response(json_output, tool_calls=[
        {"tool": "query_mireye_fetch", "id": "call_epa_val", "args": {"reason": "check facilities"}, "response": json.dumps(mireye_result)}
    ])
    
    res, log = await run_source_attribution(query="Metal River", attains_status=[{"is_primary_path": True, "status": "Impaired"}], polluters=[{"facility_name": "Upstream Factory", "source_id": "ECHO-123"}], water_samples=[], land_risk_points=[])
    
    assert res["impairments"][0]["sources"][0]["attribution"] == "DOCUMENTED"
    assert "ECHO" in res["impairments"][0]["sources"][0]["evidence_sources"]
