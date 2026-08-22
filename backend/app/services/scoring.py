import json
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.core.logging import logger, log_diagnostic_event

def compute_deterministic_risk_summary(
    attains_status: List[Dict[str, Any]],
    polluters: List[Dict[str, Any]],
    water_samples: List[Dict[str, Any]],
    land_risk_points: List[Dict[str, Any]],
    telemetry: Optional[List[Dict[str, Any]]] = None,
    attains_summary: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Computes a deterministic waterbody pollution risk categorical rating (A-F).
    """
    risk_factors = []
    mitigating_factors = []

    # 1. ATTAINS
    impaired_count = sum(1 for a in attains_status if a.get("overall_status") in ("Impaired", "Not Supporting"))
    if impaired_count > 0:
        risk_factors.append(f"CWA Section 303(d) Impaired status detected ({impaired_count} unit(s)).")
    else:
        mitigating_factors.append("No active ATTAINS impairments detected.")

    # 2. NPDES Point-Source Violations
    total_exceedances = sum(p.get("effluent_exceedances", 0) for p in polluters)
    noncompliant_quarters = sum(p.get("quarters_in_noncompliance", 0) for p in polluters)
    if total_exceedances > 0 or noncompliant_quarters > 0:
        risk_factors.append(f"Active point-source exceedances ({total_exceedances}) and noncompliance quarters ({noncompliant_quarters}).")
    else:
        mitigating_factors.append("No documented point-source effluent violations.")

    # 3. Water Quality Chemical Samples
    for sample in water_samples:
        char = sample.get("characteristic_name", "").lower()
        val = sample.get("result_value")
        if val is not None:
            if "dissolved oxygen" in char and val < 6.0:
                risk_factors.append(f"Low dissolved oxygen detected: {val} {sample.get('unit_code')}.")
            elif "nitrate" in char and val > 5.0:
                risk_factors.append(f"Elevated nitrate level: {val} {sample.get('unit_code')}.")
            elif "lead" in char and val > 0.001:
                risk_factors.append(f"Heavy metal (Lead) trace detected: {val} {sample.get('unit_code')}.")

    # 4. Land Risk
    if land_risk_points:
        avg_slope = sum(p.get("slope_degrees", 0.0) for p in land_risk_points) / len(land_risk_points)
        avg_canopy = sum(p.get("tree_canopy_pct", 0.0) for p in land_risk_points) / len(land_risk_points)
        avg_ndvi_change = sum(p.get("ndvi_change_5y", 0.0) for p in land_risk_points) / len(land_risk_points)

        if avg_slope > 12.0:
            risk_factors.append(f"High riparian bank slope ({avg_slope:.1f}°) increases erosion risk.")
        if avg_canopy < 40.0:
            risk_factors.append(f"Low tree canopy coverage ({avg_canopy:.1f}%) reduces natural buffer capacity.")
        if avg_ndvi_change < -0.05:
            risk_factors.append(f"5-year vegetation loss detected (NDVI delta: {avg_ndvi_change:.2f}).")

    risk_count = len(risk_factors)
    
    if risk_count == 0:
        label = "Low Risk"
        rating = "A"
    elif risk_count <= 2:
        label = "Limited Risk"
        rating = "B"
    elif risk_count <= 4:
        label = "Moderate Risk"
        rating = "C"
    elif risk_count <= 6:
        label = "High Risk"
        rating = "D"
    else:
        label = "Critical Risk"
        rating = "F"

    notes = "Deterministic multi-source evaluation complete based on fallback rules."

    return {
        "rating": rating,
        "label": label,
        "risk_factors": risk_factors,
        "mitigating_factors": mitigating_factors,
        "temporal_assessment": "Current snapshot with historical context.",
        "spatial_assessment": "Aggregated across resolved points.",
        "data_limitations": "Deterministic fallback. LLM reasoning unavailable.",
        "notes": notes,
        "scoring_engine": "deterministic_rules"
    }

async def reason_and_score_with_openai(
    query: str,
    attains_status: List[Dict[str, Any]],
    polluters: List[Dict[str, Any]],
    water_samples: List[Dict[str, Any]],
    land_risk_points: List[Dict[str, Any]],
    telemetry: Optional[List[Dict[str, Any]]] = None,
    attains_summary: Optional[Dict[str, Any]] = None,
    run_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Uses OpenAI LLM Reasoning Agent to analyze all collected environmental & hydrologic data,
    perform multi-factor synthesis, and return structured JSON containing overall_score, label, and reasoning notes.
    """
    # Fallback to deterministic rules if mock key is configured
    if not settings.openai_api_key or settings.openai_api_key == "mock-openai-key":
        logger.info("OPENAI_API_KEY is mock/unset. Using deterministic scoring engine fallback.")
        log_diagnostic_event("Stage 5 — Aggregation & Reasoning", "OpenAI Reasoning Agent", "WARNING", {"message": "Using deterministic rules fallback due to mock OpenAI API key"}, run_id=run_id)
        return compute_deterministic_risk_summary(attains_status, polluters, water_samples, land_risk_points, telemetry, attains_summary)

    data_payload = {
        "query": query,
        "attains_status": attains_status,
        "attains_summary": attains_summary,
        "polluters": polluters,
        "water_quality_samples": water_samples,
        "land_risk_points": land_risk_points,
        "telemetry": telemetry or []
    }

    system_prompt = (
        "You are an expert environmental water body assessment AI reasoning agent.\n"
        "Analyze the multi-source data collected for a US water body. Make a stable, evidence-grounded, independently reasoned A-F categorical assessment.\n\n"
        "## 1. Separate evidence by type\n"
        "- Regulatory/impairment evidence: ATTAINS assessment status, designated-use, impairment causes, affected uses, sources, TMDLs, historical cycles.\n"
        "- Current water-quality evidence: chemical measurements, DO, pH, nitrate, metals, dates.\n"
        "- Point-source evidence: NPDES facilities, permit status, effluent exceedances, noncompliance.\n"
        "- Hydrological evidence: streamflow, gage height, telemetry.\n"
        "- Watershed/landscape evidence: slope, elevation, land-cover, tree canopy, NDVI, flood-zone.\n"
        "DO NOT treat these categories as interchangeable. (e.g., Flood-zone A is not evidence of pollution. Good chemistry does not erase documented persistent impairment.)\n\n"
        "## 2. Force temporal & spatial reasoning\n"
        "Distinguish between Historical (first listed in 2000), Persistent (across cycles), New (most recent cycle only), and Current (recent measurements).\n"
        "Do not infer a trend when history is insufficient.\n"
        "Spatially, distinguish whether impairment is localized to one Assessment Unit or widespread. Never blindly aggregate units.\n\n"
        "## 3. Evidence quality rules\n"
        "- Missing/null values are NOT evidence of good conditions.\n"
        "- Identify conflicting measurements and reduce confidence.\n"
        "- Do not treat stale measurements as current.\n"
        "- Regulatory causes (e.g. PCBs in ATTAINS) mean documented impairment. Do not invent concentrations.\n"
        "- Land cover/NDVI are contextual vulnerability, not direct pollution measurements.\n\n"
        "## 4. Evidence balancing\n"
        "Explicitly identify Risk-increasing evidence (persistent impairment, multiple causes, point-source violations) AND Risk-reducing/mitigating evidence (Fully Supporting units, favorable chemistry, stable hydrology).\n\n"
        "## 5. A-F Rubric\n"
        "A -> Low Risk: Little meaningful impairment. Mostly supporting, no persistent impairment, favorable current chemistry.\n"
        "B -> Limited Risk: Some concerns, but limited, localized, historical, or weakly supported.\n"
        "C -> Moderate Risk: Meaningful concerns documented, but not severe/pervasive. One or more impaired uses, mixture of supporting/impaired.\n"
        "D -> High Risk: Multiple significant impairments. Multiple uses/causes impaired persistently, ecological+recreational impacts.\n"
        "F -> Critical Risk: Severe, widespread, or acute environmental degradation. Do NOT assign F merely for historical contamination.\n\n"
        "## 6. Output Rules\n"
        "Do NOT output any numerical score or fake quantitative precision. Do NOT map letters to numbers (e.g. C=50). Do NOT mention a 0-100 score. The rating is categorical.\n"
        "Provide evidence traceability in your factors (e.g., \"Persistent PCB impairment (ATTAINS, first listed 2006)\"). Do NOT invent unsupported environmental claims.\n"
        "Return ONLY a valid JSON object matching this schema exactly:\n"
        "{\n"
        '  "rating": "A" | "B" | "C" | "D" | "F",\n'
        '  "label": "Low Risk" | "Limited Risk" | "Moderate Risk" | "High Risk" | "Critical Risk",\n'
        '  "risk_factors": ["string"],\n'
        '  "mitigating_factors": ["string"],\n'
        '  "temporal_assessment": "string",\n'
        '  "spatial_assessment": "string",\n'
        '  "data_limitations": "string",\n'
        '  "notes": "string"\n'
        "}"
    )

    try:
        llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.2,
            timeout=settings.openai_request_timeout_seconds
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Analyze this environmental dataset and compute categorical risk:\n{json.dumps(data_payload, indent=2)}")
        ]
        
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        
        # Clean markdown code block markers if present
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("\n", 1)[0].replace("json", "").strip()

        parsed = json.loads(content)
        parsed["rating"] = str(parsed.get("rating", "C"))
        parsed["label"] = str(parsed.get("label", "Moderate Risk"))
        parsed["risk_factors"] = list(parsed.get("risk_factors", []))
        parsed["mitigating_factors"] = list(parsed.get("mitigating_factors", []))
        parsed["temporal_assessment"] = str(parsed.get("temporal_assessment", ""))
        parsed["spatial_assessment"] = str(parsed.get("spatial_assessment", ""))
        parsed["data_limitations"] = str(parsed.get("data_limitations", ""))
        parsed["notes"] = str(parsed.get("notes", "Analytical reasoning complete."))
        parsed["scoring_engine"] = "openai_reasoning_agent"

        log_diagnostic_event(
            stage="Stage 5 — Aggregation & Reasoning",
            component="OpenAI Reasoning Agent",
            status="SUCCESS",
            details={"rating": parsed["rating"], "label": parsed["label"]},
            run_id=run_id
        )
        return parsed

    except Exception as e:
        logger.error(f"OpenAI reasoning agent failed: {e}. Falling back to deterministic scoring.")
        log_diagnostic_event(
            stage="Stage 5 — Aggregation & Reasoning",
            component="OpenAI Reasoning Agent",
            status="FAILED",
            details={"error": str(e)},
            run_id=run_id
        )
        return compute_deterministic_risk_summary(attains_status, polluters, water_samples, land_risk_points, telemetry, attains_summary)
