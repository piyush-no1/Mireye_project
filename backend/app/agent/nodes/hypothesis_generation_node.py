import json
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.state import AssessmentState
from app.schemas.assessment import HypothesisGenerationOutput, HypothesisItem
from app.config import settings
from app.core.logging import logger, log_diagnostic_event

SYSTEM_PROMPT = """You are an EXPERT ENVIRONMENTAL SCIENTIST and POLLUTION HYPOTHESIS GENERATOR.

Given baseline water quality, regulatory impairments, industrial polluters, stream telemetry, and satellite land risk data for a specific river corridor/segment, your task is to propose one or more free-text hypotheses explaining the root cause(s) of pollution and ecological risk.

CRITICAL INSTRUCTIONS:
1. Propose one or more free-text hypotheses based on the provided empirical baseline evidence.
2. You are NOT limited to any fixed list of categories. Any examples mentioned in passing (such as agriculture, industrial discharge, municipal wastewater, urban stormwater runoff, construction runoff, streambank erosion, natural mineral deposits, etc.) are strictly ILLUSTRATIVE ONLY, not exhaustive.
3. For each proposed hypothesis:
   - State the hypothesis clearly in `hypothesis`.
   - Provide your `initial_reasoning` connecting the specific data points (e.g. specific lab exceedances, permit violations, low dissolved oxygen, lack of riparian canopy, terrain slope).
   - Specify `data_needed_to_confirm`: a list of plain, natural-language questions/queries describing what ADDITIONAL spatial, terrain, land use, or infrastructure data would help confirm or deny this hypothesis. (Do NOT use schema field names or database column names — use clear natural language questions/queries).
4. If there is insufficient evidence to form any plausible hypothesis, set `insufficient_evidence: true`.

OUTPUT FORMAT:
Respond with a JSON object strictly matching this schema:
{
  "segment_id": "<segment or run id>",
  "hypotheses": [
    {
      "hypothesis": "<Descriptive hypothesis statement>",
      "initial_reasoning": "<Reasoning referencing baseline evidence>",
      "data_needed_to_confirm": [
        "<Natural language query for additional evidence 1>",
        "<Natural language query for additional evidence 2>"
      ]
    }
  ],
  "insufficient_evidence": false
}

Respond ONLY with valid JSON.
"""

def _build_baseline_payload(state: AssessmentState) -> Dict[str, Any]:
    # Strip heavy geometries to keep prompt token-efficient
    attains_clean = []
    for au in state.attains_status:
        au_copy = dict(au)
        au_copy.pop("geometry", None)
        attains_clean.append(au_copy)

    return {
        "segment_id": state.hydrology.get("comid", state.run_id) if state.hydrology else state.run_id,
        "query": state.query,
        "is_segment_mode": getattr(state, "is_segment_mode", False),
        "attains_status": attains_clean,
        "attains_summary": state.attains_summary,
        "polluters": state.polluters,
        "water_quality_samples": state.water_quality_samples,
        "land_risk_points": state.land_risk_points,
        "telemetry": state.telemetry
    }

async def hypothesis_generation_node(state: AssessmentState) -> AssessmentState:
    """
    Hypothesis Generation Node:
    Formulates one or more free-text hypotheses and specifies natural-language
    data requirements needed to confirm or refute each hypothesis.
    """
    stage_name = "Stage 5a — Hypothesis Generation"
    if state.status in ("failed", "needs_clarification"):
        return state

    baseline_data = _build_baseline_payload(state)
    segment_id = str(baseline_data["segment_id"])

    # Fallback if OpenAI key is not provided
    if not settings.openai_api_key or settings.openai_api_key == "mock-openai-key":
        logger.info("OPENAI_API_KEY is mock/unset. Using deterministic fallback for hypothesis generation.")
        fallback_output = HypothesisGenerationOutput(
            segment_id=segment_id,
            hypotheses=[
                HypothesisItem(
                    hypothesis="Mixed upstream watershed runoff and localized point-source discharge",
                    initial_reasoning="Baseline data shows proximity to permitted discharge facilities and compromised riparian buffers.",
                    data_needed_to_confirm=[
                        "What is the upstream agricultural and impervious surface land cover within 5km?",
                        "Are there documented municipal or industrial wastewater discharge points immediately upstream?"
                    ]
                )
            ],
            insufficient_evidence=False
        )
        state.hypothesis_output = fallback_output.model_dump()
        state.execution_log.append({
            "stage": stage_name,
            "component": "hypothesis_generation_node",
            "status": "SUCCESS",
            "mode": "deterministic_fallback",
            "hypotheses_count": len(fallback_output.hypotheses)
        })
        log_diagnostic_event(stage_name, "hypothesis_generation_node", "SUCCESS", {"mode": "fallback", "hypotheses": state.hypothesis_output}, run_id=state.run_id)
        return state

    try:
        llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.2,
            timeout=settings.openai_request_timeout_seconds
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Analyze this baseline environmental dataset and generate hypotheses:\n{json.dumps(baseline_data, indent=2)}")
        ]

        response = await llm.ainvoke(messages)
        raw_text = response.content.strip()

        # Clean markdown codeblocks if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[-1].rsplit("\n", 1)[0].replace("json", "").strip()

        parsed_json = json.loads(raw_text)
        if "segment_id" not in parsed_json:
            parsed_json["segment_id"] = segment_id

        output_model = HypothesisGenerationOutput.model_validate(parsed_json)
        state.hypothesis_output = output_model.model_dump()

        state.execution_log.append({
            "stage": stage_name,
            "component": "hypothesis_generation_node",
            "status": "SUCCESS",
            "hypotheses_count": len(output_model.hypotheses),
            "insufficient_evidence": output_model.insufficient_evidence
        })

        log_diagnostic_event(
            stage=stage_name,
            component="hypothesis_generation_node",
            status="SUCCESS",
            details={
                "raw_llm_output": raw_text,
                "parsed_hypotheses": state.hypothesis_output
            },
            run_id=state.run_id
        )

    except Exception as e:
        logger.error(f"Hypothesis Generation Node failed: {e}")
        state.errors.append({
            "stage": stage_name,
            "tool": "hypothesis_generation_node",
            "message": str(e)
        })
        # Graceful fallback so pipeline proceeds
        fallback_output = HypothesisGenerationOutput(
            segment_id=segment_id,
            hypotheses=[
                HypothesisItem(
                    hypothesis="Unresolved multi-source nonpoint and point runoff",
                    initial_reasoning=f"Automated reasoning encountered an exception: {e}. Evaluating general corridor characteristics.",
                    data_needed_to_confirm=[
                        "What are the prominent land uses and infrastructure characteristics along this corridor?"
                    ]
                )
            ],
            insufficient_evidence=False
        )
        state.hypothesis_output = fallback_output.model_dump()
        state.execution_log.append({
            "stage": stage_name,
            "component": "hypothesis_generation_node",
            "status": "FAILED_FALLBACK",
            "error": str(e)
        })
        log_diagnostic_event(stage_name, "hypothesis_generation_node", "FAILED", {"error": str(e)}, run_id=state.run_id)

    return state
