import json
from app.agent.state import AssessmentState
from app.config import settings
from app.core.logging import logger, log_diagnostic_event
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

async def master_orchestration_node(state: AssessmentState) -> AssessmentState:
    """Master Orchestration & Synthesis Agent Node."""
    if state.status in ("failed", "needs_clarification"):
        return state

    ind_analysis = state.industrial_analysis or {}
    agri_analysis = state.agricultural_analysis or {}

    ind_score = ind_analysis.get("risk_score", 30)
    agri_score = agri_analysis.get("risk_score", 30)

    # 1. Fallback / Deterministic Orchestration
    if not settings.openai_api_key or settings.openai_api_key == "mock-openai-key":
        total = max(1, ind_score + agri_score)
        ind_weight = round((ind_score / total) * 100, 1)
        agri_weight = round((agri_score / total) * 100, 1)

        dominant = "Industrial Point-Source" if ind_weight > 60 else ("Agricultural Non-Point Source" if agri_weight > 60 else "Mixed Dual-Vector")
        combined_score = max(ind_score, agri_score)
        rating = "F" if combined_score >= 80 else ("D" if combined_score >= 60 else ("C" if combined_score >= 40 else ("B" if combined_score >= 20 else "A")))

        state.master_synthesis = {
            "overall_rating": rating,
            "overall_label": f"{rating}-Rated Risk",
            "dominant_pollution_vector": dominant,
            "industrial_weight_pct": ind_weight,
            "agricultural_weight_pct": agri_weight,
            "synthesis_reasoning": f"Synthesized findings from Industrial Specialist (Risk: {ind_score}) and Agricultural Specialist (Risk: {agri_score}). Dominant vector: {dominant}.",
            "remediation_recommendations": [
                "Target NPDES permit enforcement for discharging facilities in river corridor.",
                "Implement agricultural riparian buffer strips to reduce nitrate and sediment runoff.",
                "Increase USGS continuous streamflow monitoring for telemetry anomaly tracking."
            ]
        }
        state.risk_summary = {
            "rating": rating,
            "label": f"{rating}-Rated Risk ({dominant})",
            "risk_factors": [
                f"Industrial Specialist finding: {ind_analysis.get('chemical_signature_match', 'NPDES Audited')}",
                f"Agricultural Specialist finding: {agri_analysis.get('nutrient_signature_match', 'Nutrient Audited')}"
            ],
            "mitigating_factors": ["Multi-agent parallel cross-synthesis completed."],
            "temporal_assessment": "Current multi-agent snapshot evaluation.",
            "spatial_assessment": "Corridor-wide multi-disciplinary synthesis.",
            "data_limitations": "Fallback deterministic synthesis rules applied.",
            "notes": f"Master Orchestration complete. Dominant vector: {dominant}.",
            "scoring_engine": "mixture_of_agents_orchestrator"
        }
    else:
        try:
            llm = ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=0.2,
                timeout=settings.openai_request_timeout_seconds
            )
            data_payload = {
                "query": state.query,
                "resolved_location": state.resolved_location,
                "industrial_specialist_report": ind_analysis,
                "agricultural_specialist_report": agri_analysis,
                "attains_status": state.attains_status,
                "water_quality_samples": state.water_quality_samples,
                "telemetry": state.telemetry
            }
            system_prompt = (
                "You are an authoritative Master Water Quality Diagnostic Synthesis Engine.\n\n"
                "==================================================\n"
                "PRIMARY BASELINE AUTHORITY: EPA ATTAINS\n"
                "==================================================\n"
                "EPA ATTAINS is the PRIMARY baseline authority and foundation for water quality impairment and chemical identification.\n"
                "Use ATTAINS reported Clean Water Act 303(d) causes, parameters, and chemical measurements as the foundational truth for water quality analysis.\n\n"
                "==================================================\n"
                "1. DATA PROVIDED TO YOU IN INPUT PAYLOAD\n"
                "==================================================\n"
                "- `query`: User's target waterbody or river corridor.\n"
                "- `attains_status`: EPA CWA Section 303(d) impairment records (assessment_unit_id, overall_status, impairment_causes, is_primary_path) — PRIMARY BASELINE.\n"
                "- `industrial_analysis`: Industrial point-source outfall audit data.\n"
                "- `agricultural_analysis`: Agricultural non-point source runoff audit data.\n"
                "- `water_quality_samples`: WQP chemical sample measurements.\n"
                "- `telemetry`: USGS NWIS real-time streamflow and gage height telemetry.\n\n"
                "==================================================\n"
                "2. INFERENCES YOU MUST MAKE FROM THE EVIDENCE\n"
                "==================================================\n"
                "- `overall_rating`: Overall categorical grade ('A': Low Risk, 'B': Limited Risk, 'C': Moderate Risk, 'D': High Risk, 'F': Critical Risk).\n"
                "- `overall_label`: Descriptive risk label ('Low Risk' | 'Limited Risk' | 'Moderate Risk' | 'High Risk' | 'Critical Risk').\n"
                "- `dominant_pollution_vector`: Categorize dominant risk source as 'Industrial Point-Source', 'Agricultural Non-Point Source', 'Mixed Dual-Vector', or 'Low Anthropogenic Impact'.\n"
                "- `industrial_weight_pct`: Calculated proportional contribution of industrial point-sources (float 0.0 to 100.0).\n"
                "- `agricultural_weight_pct`: Calculated proportional contribution of agricultural non-point sources (float 0.0 to 100.0).\n"
                "- `synthesis_reasoning`: Concise 2-3 sentence overview highlighting exact chemicals found (with measured values e.g. Nitrate 2.1 mg/L, Temp 21.5°C) and baseline ATTAINS status. DO NOT write long paragraphs!\n"
                "- `remediation_recommendations`: List of actionable, prioritized mitigation steps.\n"
                "- `risk_factors`: List of key evidence items driving environmental risk.\n"
                "- `mitigating_factors`: List of favorable water quality or watershed conditions buffering environmental impact.\n\n"
                "==================================================\n"
                "3. OUTPUT CONSTRAINTS\n"
                "==================================================\n"
                "Return ONLY a valid JSON object with NO markdown wrapper or extra text, matching this exact schema:\n"
                "{\n"
                '  "overall_rating": "A" | "B" | "C" | "D" | "F",\n'
                '  "overall_label": "Low Risk" | "Limited Risk" | "Moderate Risk" | "High Risk" | "Critical Risk",\n'
                '  "dominant_pollution_vector": "Industrial Point-Source" | "Agricultural Non-Point Source" | "Mixed Dual-Vector" | "Low Anthropogenic Impact",\n'
                '  "industrial_weight_pct": float (0-100),\n'
                '  "agricultural_weight_pct": float (0-100),\n'
                '  "synthesis_reasoning": "string",\n'
                '  "remediation_recommendations": ["string"],\n'
                '  "risk_factors": ["string"],\n'
                '  "mitigating_factors": ["string"]\n'
                "}"
            )
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Synthesize specialist agent findings into final assessment:\n{json.dumps(data_payload, indent=2)}")
            ]
            resp = await llm.ainvoke(messages)
            content = resp.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("\n", 1)[0].replace("json", "").strip()
            
            parsed = json.loads(content)
            state.master_synthesis = {
                "overall_rating": parsed.get("overall_rating", "C"),
                "overall_label": parsed.get("overall_label", "Moderate Risk"),
                "dominant_pollution_vector": parsed.get("dominant_pollution_vector", "Mixed Dual-Vector"),
                "industrial_weight_pct": float(parsed.get("industrial_weight_pct", 50.0)),
                "agricultural_weight_pct": float(parsed.get("agricultural_weight_pct", 50.0)),
                "synthesis_reasoning": parsed.get("synthesis_reasoning", "Cross-domain synthesis complete."),
                "remediation_recommendations": parsed.get("remediation_recommendations", [])
            }
            state.risk_summary = {
                "rating": parsed.get("overall_rating", "C"),
                "label": parsed.get("overall_label", "Moderate Risk"),
                "risk_factors": parsed.get("risk_factors", [f"Industrial Risk Score: {ind_score}", f"Agricultural Risk Score: {agri_score}"]),
                "mitigating_factors": parsed.get("mitigating_factors", []),
                "temporal_assessment": "Multi-agent historical and current snapshot synthesis.",
                "spatial_assessment": f"Evaluated across {state.resolved_location.get('matched_name', 'waterbody')}.",
                "data_limitations": "Synthesized from multi-source specialist agents.",
                "notes": f"Master Orchestrator completed synthesis. Dominant vector: {state.master_synthesis['dominant_pollution_vector']}.",
                "scoring_engine": "mixture_of_agents_orchestrator"
            }
        except Exception as e:
            logger.error(f"Master Orchestration LLM synthesis notice: {e}")
            state.master_synthesis = {
                "overall_rating": "C",
                "overall_label": "Moderate Risk",
                "dominant_pollution_vector": "Mixed Dual-Vector",
                "industrial_weight_pct": 50.0,
                "agricultural_weight_pct": 50.0,
                "synthesis_reasoning": f"Synthesized findings from Industrial ({ind_score}) and Agricultural ({agri_score}) agents.",
                "remediation_recommendations": ["Conduct joint industrial and agricultural runoff monitoring."]
            }
            state.risk_summary = {
                "rating": "C",
                "label": "Moderate Risk",
                "risk_factors": [f"Industrial Risk: {ind_score}", f"Agricultural Risk: {agri_score}"],
                "mitigating_factors": [],
                "temporal_assessment": "Snapshot synthesis.",
                "spatial_assessment": "Corridor-wide.",
                "data_limitations": "Fallback orchestrator synthesis.",
                "notes": "Orchestration synthesis fallback complete.",
                "scoring_engine": "mixture_of_agents_orchestrator"
            }

    state.execution_log.append({
        "stage": "Stage 5 — Master Orchestration & Synthesis",
        "component": "master_orchestration_node",
        "status": "SUCCESS",
        "dominant_vector": state.master_synthesis.get("dominant_pollution_vector"),
        "overall_rating": state.master_synthesis.get("overall_rating")
    })
    log_diagnostic_event("Stage 5 — Master Orchestrator", "master_orchestration_node", "SUCCESS", {"dominant_vector": state.master_synthesis.get("dominant_pollution_vector")}, run_id=state.run_id)

    return state
