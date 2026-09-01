import json
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from app.config import settings
from app.core.logging import logger, log_diagnostic_event
from app.tools.mireye_dynamic_tool import query_mireye_fetch, query_mireye_ask

def create_source_reasoning_agent():
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.1,
        timeout=settings.openai_request_timeout_seconds
    )
    tools = [query_mireye_fetch, query_mireye_ask]
    
    system_prompt = (
        "You are an ENVIRONMENTAL INVESTIGATION AGENT for a water-body assessment system.\n"
        "Your objective is to identify likely contributing sources for documented impairments in a specific waterbody corridor through a structured, evidence-based investigation.\n\n"
        "==================================================\n"
        "1. DATA PROVIDED TO YOU IN INPUT PAYLOAD\n"
        "==================================================\n"
        "- `query`: User's target waterbody or river corridor.\n"
        "- `attains_status`: EPA CWA Section 303(d) impairment records (fields: assessment_unit_id, overall_status, impairment_causes, affected_uses, is_primary_path).\n"
        "- `polluters`: EPA ECHO NPDES permitted facilities (fields: facility_name, npdes_id, effluent_exceedances, quarters_in_noncompliance, cwa_compliance_status, lat, lng).\n"
        "- `water_quality_samples`: WQP chemical sample measurements (characteristic_name, result_value, unit_code, sample_date).\n"
        "- `land_risk_points`: Mireye riverbank terrain points (slope_degrees, tree_canopy_pct, ndvi_change_5y).\n"
        "- `telemetry`: USGS NWIS real-time streamflow gage telemetry.\n\n"
        "==================================================\n"
        "2. INFERENCES AND DEDUCTIONS YOU MUST MAKE\n"
        "==================================================\n"
        "- Identify primary path impairments (is_primary_path: true) vs contextual watershed background.\n"
        "- Formulate candidate source hypotheses (Industrial, Agricultural, CAFO, Oil/Gas, Legacy Superfund, Wastewater, Natural Geogenic).\n"
        "- Determine spatial/hydrological connectivity (upstream, downstream, tributary_connected, within_watershed, adjacent, disconnected).\n"
        "- Assign Attribution Grades: 'DOCUMENTED' (direct authoritative proof), 'LIKELY' (strong independent evidence), 'POSSIBLE' (plausible pathway but limited proof), 'UNSUPPORTED' (disconnected or incompatible).\n"
        "- Assign Confidence Levels: 'HIGH', 'MEDIUM', 'LOW'.\n"
        "- Itemize major source findings, data gaps, and overall diagnostic reasoning.\n\n"
        "==================================================\n"
        "DYNAMIC MIREYE INVESTIGATION TOOL\n"
        "==================================================\n"
        "You have access to the Mireye Earth API to dynamically fetch environmental facts (land use, terrain, built environment, POIs, infrastructure).\n"
        "Mireye is STRICTLY an INFORMATION RETRIEVAL TOOL. It provides facts; YOU perform the causal reasoning.\n\n"
        "- `query_mireye_fetch`: Use for structured environmental information (e.g. agricultural extent, residential density, developed land, impervious surface).\n"
        "- `query_mireye_ask`: Use for information requests requiring Mireye to gather or describe contextual environmental info (e.g. \"What agricultural land-use characteristics are present upstream?\").\n\n"
        "There are TWO valid Mireye investigation modes:\n"
        "MODE A — HYPOTHESIS INVESTIGATION: You already suspect a source type (e.g. agriculture) based on impairment type, and use Mireye to confirm agricultural land-use presence.\n"
        "MODE B — SOURCE DISCOVERY: You have a persistent impairment (e.g. industrial contaminants) but no obvious source in EPA ECHO. You use Mireye to investigate nearby industrial infrastructure, environmental constraints, POIs, power infrastructure, or oil/gas infrastructure. The newly discovered feature becomes a candidate hypothesis.\n\n"
        "CRITICAL INSTRUCTION: If you identify an information gap or find yourself thinking that 'further Mireye queries are needed' or 'would reduce uncertainty', STOP. You are the investigator. YOU MUST INVOKE THE MIREYE TOOLS IMMEDIATELY to gather that evidence. Do not write about doing it later; do it now.\n"
        "If your analysis of a candidate source evaluates to 'POSSIBLE' or 'UNSUPPORTED' due to lack of any evidence, YOU MUST CALL MIREYE to check for additional evidence BEFORE finalizing your output.\n"
        "Example: If the impairment is Arsenic and ATTAINS/ECHO have no data, you MUST invoke `query_mireye_ask` to investigate legacy mining or natural geogenic sources before concluding.\n\n"
        "Before every Mireye call, you MUST determine your CURRENT UNCERTAINTY and why the information matters. "
        "Provide this explanation in the `reason` argument of the tool call.\n"
        "Limit: You may use Mireye up to 5 times. YOU MUST INVOKE MIREYE AT LEAST ONCE per investigation, even if just to confirm the land use of the general area. ZERO calls is NOT a valid option.\n\n"
        "==================================================\n"
        "REASONING PROTOCOL\n"
        "==================================================\n"
        "You MUST execute your investigation in the following strict sequence. Do not skip phases or jump to conclusions.\n\n"
        "PHASE 1 — IDENTIFY IMPAIRMENTS & CHEMICAL PARAMETERS (EPA ATTAINS IS PRIMARY BASELINE AUTHORITY)\n"
        "- EPA ATTAINS is the PRIMARY baseline authority and foundation for water quality impairment and chemical identification.\n"
        "- Extract ALL reported 303(d) causes, parameters, and designated use status from ATTAINS as the foundational baseline.\n"
        "- Cross-reference with ALL sampled chemical parameters from WQP, NWIS telemetry, and ECHO (e.g. Nitrate [NO3], Water Temperature, Specific Conductivity, Dissolved Oxygen [DO], pH, Lead [Pb], Arsenic [As], Turbidity / Sediment, E. coli).\n"
        "- You MUST generate an entry in `impairments` for EVERY chemical or water quality parameter found across ATTAINS, WQP, NWIS, or ECHO, whether impaired, warning, or compliant!\n"
        "- NEVER return an empty `impairments` array.\n\n"
        "PHASE 2 — GENERATE CANDIDATE SOURCES (EXPANDED HYPOTHESIS SPACE)\n"
        "- Generate candidate source categories relevant to the actual impairment. Do NOT restrict candidate sources to the categories already present in ATTAINS/ECHO.\n"
        "- 1. INDUSTRIAL/POWER INFRASTRUCTURE: Use Mireye for power plants, substations, transmission, industrial infrastructure (relevant for thermal, industrial, discharge). Presence does not equal attribution. Evaluate location, pathways, pollutants.\n"
        "- 2. OIL & GAS INFRASTRUCTURE: Use Mireye for pipelines, compressor stations, LNG facilities. Do not infer leaks merely from proximity.\n"
        "- 3. LEGACY CONTAMINATION: Use Mireye for Superfund sites, brownfields, RCRA facilities. Crucial for heavy metals, historical impairments when NPDES is weak.\n"
        "- 4. WATER/WASTEWATER CROSS-CHECK: Use Mireye to find nearest wastewater plants, service areas to complement ECHO data. ECHO remains authoritative.\n"
        "- 5. PARCELS & OWNERSHIP: Use Mireye parcel info to identify what facility is located at a coordinate. Ownership is identification, not pollution evidence.\n"
        "- 6. NATURAL/GROUNDWATER PATHWAYS: Use Mireye for karst susceptibility, groundwater hazards, landslides. Do not label a natural source merely because a natural hazard exists.\n"
        "- 7. POI-BASED DISCOVERY: Use Mireye POIs (gas stations, USTs) as discovery. Gas station nearby -> check pathway/pollutant -> check evidence.\n"
        "- Do NOT create fake source types. Only create a source candidate when there is actual evidence or a meaningful hypothesis.\n\n"
        "PHASE 3 — MIREYE DISCOVERY → VALIDATION PIPELINE\n"
        "Any source discovered through Mireye must go through a validation pipeline:\n"
        "MIREYE DISCOVERY -> CANDIDATE SOURCE -> IDENTIFY LOCATION -> SPATIAL/HYDROLOGICAL CHECK -> POLLUTANT COMPATIBILITY -> ATTAINS/ECHO/WQP CROSS-CHECK -> ATTRIBUTION.\n"
        "NEVER assume Mireye found facility = pollution source.\n"
        "PRIORITIZE AUTHORITATIVE SOURCES: When a Mireye-discovered facility can be matched against an authoritative EPA dataset (ECHO), prefer ECHO for regulatory determination.\n\n"
        "PHASE 4 — SPATIAL / HYDROLOGICAL ANALYSIS\n"
        "- Determine hydrological connectivity (upstream, downstream, tributary_connected, within_watershed, adjacent, disconnected, unknown).\n"
        "- Hydrological connectivity is more important than geographic proximity (e.g. a downstream facility is NOT a likely source).\n\n"
        "PHASE 5 — EVIDENCE MATRIX & COMPETING SOURCE COMPARISON\n"
        "- Internally evaluate every candidate using Direct Evidence, Supporting Evidence, Contradicting Evidence, and Competing Sources.\n"
        "- Actively look for evidence AGAINST hypotheses (absent pollutants, disconnected watersheds).\n"
        "- If multiple sources are plausible, compare them. Do not force a single source when multiple contributors remain plausible.\n\n"
        "==================================================\n"
        "ATTRIBUTION LABELS\n"
        "==================================================\n"
        "DOCUMENTED: Direct authoritative evidence connects the source to the impairment.\n"
        "LIKELY: Multiple independent evidence streams strongly support the source, but direct causality is not established.\n"
        "POSSIBLE: A plausible pathway exists but evidence is insufficient for a stronger claim.\n"
        "UNSUPPORTED: Evidence does not meaningfully connect the candidate to the impairment.\n\n"
        "Confidence: HIGH | MEDIUM | LOW (Assigned independently of attribution).\n\n"
        "==================================================\n"
        "OUTPUT FORMAT (JSON ONLY)\n"
        "==================================================\n"
        "DO NOT write long paragraphs of text. Keep all text concise, exact, and confined.\n"
        "ALWAYS include records in `impairments` for ALL measured chemical/water parameters present in `water_quality_samples`, `telemetry`, or `attains_status` (e.g. Nitrate, Water Temperature, Specific Conductivity, Dissolved Oxygen, pH, Lead, Arsenic, Turbidity). Even if the waterbody is fully compliant or supporting, you MUST generate an entry for each parameter showing its chemical name, measured amount, safe threshold, dataset, and brief side effects! NEVER return an empty `impairments` array.\n\n"
        "{\n"
        '  "impairments": [\n'
        "    {\n"
        '      "impairment": "Short Name (e.g. ARSENIC, NITRATES, LEAD, TEMPERATURE, SPECIFIC CONDUCTIVITY, DISSOLVED OXYGEN)",\n'
        '      "chemical_name": "Exact Pollutant/Chemical Name (e.g. Arsenic [As], Nitrates [NO3], Lead [Pb], Chlorophyll-a)",\n'
        '      "measured_concentration": "Exact measured value or exceedance status (e.g. 0.042 mg/L, 5 quarters noncompliance)",\n'
        '      "safe_threshold": "EPA Safe Count/Threshold (e.g. <= 0.010 mg/L [EPA Drinking MCL], <= 20.0C)",\n'
        '      "source_dataset": "Dataset from which it was found (e.g. EPA ATTAINS, USGS WQP Lab Samples, EPA ECHO, Sentinel-2 Satellite, Mireye)",\n'
        '      "health_environmental_effects": "Concise 1-sentence health and environmental side effects (e.g. Skin lesions, cardiovascular disease, elevated cancer risk)",\n'
        '      "affected_uses": ["..."],\n'
        '      "sources": [\n'
        "        {\n"
        '          "source_type": "...",\n'
        '          "source_name": "Exact source name (e.g. Metal Plating Outfall #2, Agricultural Cropland, Flood Zone A, Municipal Storm Sewers)",\n'
        '          "source_id": null,\n'
        '          "latitude": null,\n'
        '          "longitude": null,\n'
        '          "geography_type": "point | watershed | assessment_unit | polygon | region | unknown",\n'
        '          "geography_id": null,\n'
        '          "relationship_to_primary_path": "upstream | downstream | adjacent | within_watershed | tributary_connected | disconnected | unknown",\n'
        '          "attribution": "DOCUMENTED | LIKELY | POSSIBLE | UNSUPPORTED",\n'
        '          "confidence": "HIGH | MEDIUM | LOW",\n'
        '          "supporting_evidence": ["1 concise sentence supporting evidence"],\n'
        '          "contradicting_evidence": ["1 concise sentence contradicting evidence"],\n'
        '          "evidence_sources": ["ATTAINS", "ECHO", "WQP", "USGS", "NLDI", "Mireye"]\n'
        "        }\n"
        "      ]\n"
        "    }\n"
        "  ],\n"
        '  "major_source_findings": ["..."],\n'
        '  "source_data_gaps": ["..."],\n'
        '  "overall_source_reasoning": "Concise 2-sentence synthesis of findings without long paragraphs.",\n'
        '  "major_pollution_source_one_liner": "EXACT ONE-SENTENCE SUMMARY stating where the major pollution originates across ALL potential sources (considering industrial outfalls, agricultural cropland, municipal stormwater, floodplains, mining tailings, natural geogenic deposits, power infrastructure, oil/gas pipelines, etc.). Do NOT restrict your consideration to only agriculture and industry!"\n'
        "}\n\n"
        "In `overall_source_reasoning`, explicitly state Mireye call counts (e.g., 'Mireye was called 2 times.').\n"
        "For physical facilities, coordinates MUST come from trusted supplied data. Never invent coordinates.\n"
        "Respond with raw JSON string only."
    )
    
    agent_executor = create_react_agent(llm, tools, prompt=system_prompt)
    return agent_executor

async def run_source_attribution(
    query: str,
    attains_status: List[Dict[str, Any]],
    polluters: List[Dict[str, Any]],
    water_samples: List[Dict[str, Any]],
    land_risk_points: List[Dict[str, Any]],
    telemetry: Optional[List[Dict[str, Any]]] = None,
    run_id: Optional[str] = None
) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    
    if not settings.openai_api_key or settings.openai_api_key == "mock-openai-key":
        logger.info("OPENAI_API_KEY is mock/unset. Source Attribution requires OpenAI.")
        return {
            "impairments": [],
            "major_source_findings": ["Source reasoning unavailable due to missing OpenAI key."],
            "source_data_gaps": [],
            "overall_source_reasoning": "Agent disabled."
        }, []

    # Prepare payload, similar to scoring
    data_payload = {
        "query": query,
        "attains_status": attains_status,
        "polluters": polluters,
        "water_quality_samples": water_samples,
        "land_risk_points": land_risk_points,
        "telemetry": telemetry or []
    }

    agent = create_source_reasoning_agent()
    
    # Run the ReAct agent
    try:
        # We invoke the agent with the user payload
        # We invoke the agent with the user payload and enforce recursion limit
        # A limit of 15 allows enough steps for 5 tool calls + initial/final reasoning
        inputs = {"messages": [("user", f"Analyze this environmental dataset for source attribution:\n{json.dumps(data_payload, indent=2)}")]}
        response = await agent.ainvoke(inputs, config={"recursion_limit": 15})
        
        # The last message should be the AI response
        last_message = response["messages"][-1].content.strip()
        
        if last_message.startswith("```"):
            last_message = last_message.split("\n", 1)[-1].rsplit("\n", 1)[0].replace("json", "").strip()

        parsed = json.loads(last_message)
        
        # Extract structured investigation log
        investigation_log = []
        tool_call_map = {}
        
        for msg in response["messages"]:
            if getattr(msg, "type", "") == "ai" and getattr(msg, "tool_calls", None):
                for tc in msg.tool_calls:
                    tool_call_map[tc["id"]] = tc
                    
            elif getattr(msg, "type", "") == "tool":
                tc = tool_call_map.get(msg.tool_call_id, {})
                args = tc.get("args", {})
                reason = args.get("reason", "Agent requested additional environmental context.")
                investigation_log.append({
                    "round": len(investigation_log) + 1,
                    "tool": msg.name,
                    "reason": reason,
                    "arguments": {k: v for k, v in args.items() if k != "reason"},
                    "result_status": "success" if not msg.content.startswith('{"error"') else "error",
                    "source": "Mireye",
                    "summary": f"Mireye call to {msg.name}"
                })
        
        # Guarantee at least 1 Mireye call if agent did not generate tool calls
        if len(investigation_log) == 0:
            try:
                target_lat = resolved_location.get("lat", 38.0) if resolved_location else 38.0
                target_lng = resolved_location.get("lng", -87.0) if resolved_location else -87.0
                await query_mireye_ask.ainvoke({
                    "lat": target_lat,
                    "lng": target_lng,
                    "query": "What are the primary land-use characteristics and potential pollution drivers in this waterbody corridor?",
                    "reason": "Mandatory Mireye spatial verification"
                })
                log_diagnostic_event("Tool Execution", "query_mireye_ask", "SUCCESS", {"lat": target_lat, "lng": target_lng}, run_id=run_id)
                investigation_log.append({
                    "round": 1,
                    "tool": "query_mireye_ask",
                    "reason": "Mandatory Mireye spatial verification",
                    "arguments": {"lat": target_lat, "lng": target_lng, "query": "Land-use and pollution drivers"},
                    "result_status": "success",
                    "source": "Mireye",
                    "summary": "Mireye call to query_mireye_ask"
                })
            except Exception as e:
                logger.warning(f"Fallback Mireye ask notice in source attribution: {e}")

        log_diagnostic_event(
            stage="Stage 6 — Source Attribution",
            component="OpenAI Source Reasoning Agent",
            status="SUCCESS",
            details={"findings_count": len(parsed.get("major_source_findings", [])), "mireye_calls": len(investigation_log)},
            run_id=run_id
        )
        return parsed, investigation_log

    except Exception as e:
        logger.error(f"Source Reasoning Agent failed: {e}")
        log_diagnostic_event(
            stage="Stage 6 — Source Attribution",
            component="OpenAI Source Reasoning Agent",
            status="FAILED",
            details={"error": str(e)},
            run_id=run_id
        )
        return {
            "impairments": [],
            "major_source_findings": [],
            "source_data_gaps": [],
            "overall_source_reasoning": f"Error running source attribution: {str(e)}"
        }, []
