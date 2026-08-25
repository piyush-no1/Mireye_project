import pytest
import json
from unittest.mock import patch, AsyncMock
from langchain_core.messages import AIMessage
from app.agent.state import AssessmentState
from app.agent.nodes.hypothesis_generation_node import hypothesis_generation_node
from app.agent.nodes.targeted_fetch_node import targeted_fetch_node
from app.agent.nodes.evidence_synthesis_node import evidence_synthesis_node
from app.agent.graph import assessment_graph
from app.schemas.assessment import HypothesisGenerationOutput, EvidenceSynthesisOutput

@pytest.fixture
def sample_state():
    return AssessmentState(
        run_id="test-run-123",
        query="Cuyahoga River, OH",
        resolved_location={"matched_name": "Cuyahoga River", "lat": 41.48, "lng": -81.68},
        hydrology={"comid": "123456", "bbox": [-81.70, 41.45, -81.65, 41.50]},
        water_quality_samples=[
            {"characteristic_name": "Phosphorus", "result_value": 0.45, "unit_code": "mg/L"}
        ],
        attains_status=[
            {
                "assessment_unit_id": "OH-01",
                "overall_status": "Not Supporting",
                "uses": [{"use_name": "Recreation", "use_attainment_code_name": "Not Supporting"}],
                "impairments": [{"cause_name": "Nutrients"}],
                "is_primary_path": True
            }
        ],
        polluters=[
            {"facility_name": "Industrial Works LLC", "permit_status": "Effective", "effluent_exceedances": 3}
        ],
        land_risk_points=[
            {"lat": 41.48, "lng": -81.68, "tree_canopy_pct": 22.0, "slope_degrees": 9.5}
        ]
    )

@pytest.mark.asyncio
async def test_hypothesis_generation_fallback(sample_state):
    # Tests deterministic fallback when OpenAI key is unset/mock
    state = await hypothesis_generation_node(sample_state)
    assert state.hypothesis_output is not None
    validated = HypothesisGenerationOutput.model_validate(state.hypothesis_output)
    assert len(validated.hypotheses) > 0
    assert len(validated.hypotheses[0].data_needed_to_confirm) > 0

@pytest.mark.asyncio
async def test_targeted_fetch_node_generic_execution(sample_state):
    sample_state.hypothesis_output = {
        "segment_id": "123456",
        "hypotheses": [
            {
                "hypothesis": "Agricultural runoff and failing septic systems",
                "initial_reasoning": "High nutrient values with low tree canopy.",
                "data_needed_to_confirm": [
                    "What percentage of upstream land within 3km is used for intensive agriculture?",
                    "Are there unsewered residential parcels adjacent to the riparian zone?"
                ]
            }
        ],
        "insufficient_evidence": False
    }

    state = await targeted_fetch_node(sample_state)
    assert len(state.targeted_evidence) == 2
    assert "What percentage of upstream land within 3km is used for intensive agriculture?" in state.targeted_evidence
    assert "Are there unsewered residential parcels adjacent to the riparian zone?" in state.targeted_evidence
    assert len(state.source_investigation_log) == 2

@pytest.mark.asyncio
async def test_evidence_synthesis_node_fallback(sample_state):
    sample_state.hypothesis_output = {
        "segment_id": "123456",
        "hypotheses": [
            {
                "hypothesis": "Agricultural nutrient enrichment",
                "initial_reasoning": "High phosphorus readings.",
                "data_needed_to_confirm": ["Upstream crop density"]
            }
        ],
        "insufficient_evidence": False
    }
    sample_state.targeted_evidence = {
        "Upstream crop density": {"findings": "38% cropland observed upstream"}
    }

    state = await evidence_synthesis_node(sample_state)
    assert state.evidence_synthesis is not None
    validated = EvidenceSynthesisOutput.model_validate(state.evidence_synthesis)
    assert validated.final_cause != ""
    assert validated.confidence in ("high", "medium", "low")
    assert state.source_attribution is not None

@pytest.mark.asyncio
@patch("langchain_openai.ChatOpenAI.ainvoke")
async def test_full_two_stage_with_mocked_llm(mock_ainvoke, sample_state):
    hyp_llm_response = {
        "segment_id": "123456",
        "hypotheses": [
            {
                "hypothesis": "Upstream agricultural nutrient overloading combined with point source effluent",
                "initial_reasoning": "Elevated phosphorus and presence of industrial facilities.",
                "data_needed_to_confirm": [
                    "Are there agricultural drainage ditches draining into this reach?"
                ]
            }
        ],
        "insufficient_evidence": False
    }
    
    synth_llm_response = {
        "segment_id": "123456",
        "final_cause": "Intense agricultural fertilizer runoff exacerbated by low riparian tree canopy.",
        "supporting_evidence": [
            "Phosphorus concentration of 0.45 mg/L exceeds criteria.",
            "Riparian tree canopy is only 22%."
        ],
        "contradicting_evidence": [],
        "confidence": "high",
        "alternative_explanations_considered": [
            "Single industrial facility discharge (ruled secondary due to chemical profile)"
        ],
        "grade_contribution_notes": "Primary nonpoint source driver."
    }

    # First call: hypothesis generation; Second call: evidence synthesis
    mock_ainvoke.side_effect = [
        AIMessage(content=json.dumps(hyp_llm_response)),
        AIMessage(content=json.dumps(synth_llm_response))
    ]

    with patch("app.config.settings.openai_api_key", "sk-test-valid-key"):
        state_after_hyp = await hypothesis_generation_node(sample_state)
        assert state_after_hyp.hypothesis_output["hypotheses"][0]["hypothesis"] == hyp_llm_response["hypotheses"][0]["hypothesis"]

        state_after_fetch = await targeted_fetch_node(state_after_hyp)
        assert "Are there agricultural drainage ditches draining into this reach?" in state_after_fetch.targeted_evidence

        state_after_synth = await evidence_synthesis_node(state_after_fetch)
        assert state_after_synth.evidence_synthesis["confidence"] == "high"
        assert "agricultural fertilizer runoff" in state_after_synth.evidence_synthesis["final_cause"].lower()
