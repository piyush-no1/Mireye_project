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
    telemetry: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Computes a deterministic waterbody pollution risk score from 0.0 (Clean/Safe) to 100.0 (Severe Hazard).
    """
    score = 0.0
    notes_list: List[str] = []

    # 1. ATTAINS Regulatory Assessment (up to 35 pts)
    impaired_count = sum(1 for a in attains_status if a.get("overall_status") == "Impaired")
    if impaired_count > 0:
        score += 30.0
        notes_list.append(f"CWA Section 303(d) Impaired status detected ({impaired_count} unit(s)).")

    # 2. NPDES Point-Source Violations (up to 30 pts)
    total_exceedances = sum(p.get("effluent_exceedances", 0) for p in polluters)
    noncompliant_quarters = sum(p.get("quarters_in_noncompliance", 0) for p in polluters)
    if total_exceedances > 0 or noncompliant_quarters > 0:
        pts = min(30.0, (total_exceedances * 5.0) + (noncompliant_quarters * 7.5))
        score += pts
        notes_list.append(f"Active point-source exceedances ({total_exceedances}) and noncompliance quarters ({noncompliant_quarters}).")

    # 3. Water Quality Chemical Samples (up to 20 pts)
    for sample in water_samples:
        char = sample.get("characteristic_name", "").lower()
        val = sample.get("result_value")
        if val is not None:
            if "dissolved oxygen" in char and val < 6.0:
                score += 8.0
                notes_list.append(f"Low dissolved oxygen detected: {val} {sample.get('unit_code')}.")
            elif "nitrate" in char and val > 5.0:
                score += 7.0
                notes_list.append(f"Elevated nitrate level: {val} {sample.get('unit_code')}.")
            elif "lead" in char and val > 0.001:
                score += 10.0
                notes_list.append(f"Heavy metal (Lead) trace detected: {val} {sample.get('unit_code')}.")

    # 4. Land Riparian Erosion & Canopy Risk (up to 15 pts)
    if land_risk_points:
        avg_slope = sum(p.get("slope_degrees", 0.0) for p in land_risk_points) / len(land_risk_points)
        avg_canopy = sum(p.get("tree_canopy_pct", 0.0) for p in land_risk_points) / len(land_risk_points)
        avg_ndvi_change = sum(p.get("ndvi_change_5y", 0.0) for p in land_risk_points) / len(land_risk_points)

        if avg_slope > 12.0:
            score += 5.0
            notes_list.append(f"High riparian bank slope ({avg_slope:.1f}°) increases erosion risk.")
        if avg_canopy < 40.0:
            score += 5.0
            notes_list.append(f"Low tree canopy coverage ({avg_canopy:.1f}%) reduces natural buffer capacity.")
        if avg_ndvi_change < -0.05:
            score += 5.0
            notes_list.append(f"5-year vegetation loss detected (NDVI delta: {avg_ndvi_change:.2f}).")

    final_score = min(100.0, round(score, 1))

    if final_score < 25.0:
        label = "Low Risk"
    elif final_score < 55.0:
        label = "Moderate Risk"
    elif final_score < 80.0:
        label = "High Risk"
    else:
        label = "Critical Risk"

    notes = " ".join(notes_list) if notes_list else "No significant environmental hazard indicators detected."

    return {
        "overall_score": final_score,
        "label": label,
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
        return compute_deterministic_risk_summary(attains_status, polluters, water_samples, land_risk_points, telemetry)

    data_payload = {
        "query": query,
        "attains_status": attains_status,
        "polluters": polluters,
        "water_quality_samples": water_samples,
        "land_risk_points": land_risk_points,
        "telemetry": telemetry or []
    }

    system_prompt = (
        "You are an expert environmental water body assessment AI reasoning agent. "
        "Analyze the multi-source data collected for a US water body (Clean Water Act 303(d) status, NPDES point-source factory violations, "
        "water quality chemistry, riparian bank slopes, tree canopy coverage, and streamflow telemetry). "
        "Perform deep environmental reasoning regarding pollution hazards, runoff risk, and ecological degradation. "
        "Return ONLY a valid JSON object with the following exact keys:\n"
        '{"overall_score": float (0.0 to 100.0), "label": "Low Risk" | "Moderate Risk" | "High Risk" | "Critical Risk", "notes": "analytical reasoning summary string"}'
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
            HumanMessage(content=f"Analyze this environmental dataset and compute risk score:\n{json.dumps(data_payload, indent=2)}")
        ]
        
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        
        # Clean markdown code block markers if present
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("\n", 1)[0].replace("json", "").strip()

        parsed = json.loads(content)
        parsed["overall_score"] = float(parsed.get("overall_score", 0.0))
        parsed["label"] = str(parsed.get("label", "Moderate Risk"))
        parsed["notes"] = str(parsed.get("notes", "Analytical reasoning complete."))
        parsed["scoring_engine"] = "openai_reasoning_agent"

        log_diagnostic_event(
            stage="Stage 5 — Aggregation & Reasoning",
            component="OpenAI Reasoning Agent",
            status="SUCCESS",
            details={"overall_score": parsed["overall_score"], "label": parsed["label"]},
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
        return compute_deterministic_risk_summary(attains_status, polluters, water_samples, land_risk_points, telemetry)
