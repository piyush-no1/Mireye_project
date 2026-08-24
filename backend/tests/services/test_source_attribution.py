import pytest
from unittest.mock import patch, MagicMock, AsyncMock
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
        {"tool": "query_mireye_fetch", "id": "call_123", "args": {"lat": 38.0, "lng": -77.0}, "response": json.dumps(mireye_result)}
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
    assert log[0]["result_status"] == "success"

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
