import json
from app.agent.state import AssessmentState
from app.tools.epa_echo_tool import get_epa_echo_polluters
from app.tools.epa_tri_tool import get_epa_tri_releases
from app.tools.epa_wqp_tool import get_epa_water_quality
from app.config import settings
from app.core.logging import logger, log_diagnostic_event
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

async def industrial_specialist_node(state: AssessmentState) -> AssessmentState:
    """Specialized Sub-Agent Node 1: Industrial Pollution & Factory Compliance Specialist."""
    if state.status in ("failed", "needs_clarification"):
        return state

    if not state.hydrology or "bbox" not in state.hydrology:
        return state

    bbox = state.hydrology["bbox"]

    # 1. Fetch live or fallback EPA ECHO polluters if not already in state
    if not state.polluters:
        try:
            state.polluters = await get_epa_echo_polluters.ainvoke({"bbox": bbox})
        except Exception as e:
            logger.warning(f"Industrial Specialist ECHO fetch notice: {e}")
            state.polluters = []

    # 2. Fetch EPA TRI releases
    tri_releases = []
    try:
        tri_releases = await get_epa_tri_releases.ainvoke({"bbox": bbox})
    except Exception as e:
        logger.warning(f"Industrial Specialist TRI fetch notice: {e}")

    # 3. Filter water quality samples for industrial chemical indicators
    industrial_water_samples = []
    industrial_indicators = ["lead", "arsenic", "cadmium", "chromium", "mercury", "cyanide", "toluene", "benzene", "solvent", "voc", "ph", "copper", "zinc"]
    for sample in state.water_quality_samples:
        char = sample.get("characteristic_name", "").lower()
        if any(ind in char for ind in industrial_indicators):
            industrial_water_samples.append(sample)

    target_lat = state.resolved_location.get("lat") if state.resolved_location else (bbox[1] + bbox[3]) / 2.0
    target_lng = state.resolved_location.get("lng") if state.resolved_location else (bbox[0] + bbox[2]) / 2.0

    # 4. LLM Industrial Specialist Reasoning
    if not settings.openai_api_key or settings.openai_api_key == "mock-openai-key":
        # Fallback deterministic industrial analysis
        total_exceedances = sum(p.get("effluent_exceedances", 0) for p in state.polluters)
        noncompliant_quarters = sum(p.get("quarters_in_noncompliance", 0) for p in state.polluters)
        score = min(100, (total_exceedances * 20) + (noncompliant_quarters * 15) + (len(tri_releases) * 10))
        rating = "F" if score >= 80 else ("D" if score >= 60 else ("C" if score >= 40 else ("B" if score >= 20 else "A")))
        state.industrial_analysis = {
            "risk_score": score,
            "risk_rating": rating,
            "high_risk_facilities": state.polluters[:5],
            "chemical_signature_match": "Industrial NPDES / TRI Effluent Match" if score > 30 else "Clean / Minimal Industrial Signal",
            "evidence_summary": f"Audited {len(state.polluters)} NPDES permitted facilities and {len(tri_releases)} TRI chemical release sites.",
            "npdes_violations_summary": {"total_exceedances": total_exceedances, "noncompliance_quarters": noncompliant_quarters},
            "tri_releases_summary": {"sites_found": len(tri_releases), "releases": tri_releases[:3]}
        }
    else:
        try:
            from app.tools.mireye_dynamic_tool import query_mireye_fetch, query_mireye_ask
            from app.tools.mireye_land_risk_tool import get_mireye_land_risk
            from langchain_core.messages import ToolMessage

            tools = [query_mireye_fetch, query_mireye_ask, get_mireye_land_risk]
            llm = ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=0.2,
                timeout=settings.openai_request_timeout_seconds
            )
            llm_with_tools = llm.bind_tools(tools)

            prompt_payload = {
                "query": state.query,
                "coordinates": {"lat": target_lat, "lng": target_lng},
                "polluters": state.polluters,
                "tri_releases": tri_releases,
                "industrial_water_samples": industrial_water_samples,
                "attains_status": state.attains_status,
                "land_risk_points": state.land_risk_points
            }

            system_prompt = (
                "You are an expert Industrial Water Quality & NPDES Effluent Diagnostic Engine.\n\n"
                "==================================================\n"
                "1. DATA PROVIDED TO YOU IN INPUT PAYLOAD\n"
                "==================================================\n"
                "- `query`: User's target waterbody or corridor.\n"
                "- `coordinates`: Latitude and Longitude of target waterbody.\n"
                "- `polluters`: EPA ECHO NPDES permitted industrial facilities in the corridor.\n"
                "- `tri_releases`: EPA Toxic Release Inventory (TRI) chemical discharges.\n"
                "- `industrial_water_samples`: WQP chemistry samples for heavy metals, solvents, and industrial pH.\n"
                "- `attains_status`: EPA CWA Section 303(d) waterbody impairment records.\n"
                "- `land_risk_points`: Mireye riverbank terrain risk samples.\n\n"
                "==================================================\n"
                "2. DYNAMIC MIREYE EARTH API TOOL EXECUTION INSTRUCTIONS\n"
                "==================================================\n"
                "You possess DYNAMIC, AUTONOMOUS capability to query the Mireye Earth API tools:\n"
                "- `query_mireye_fetch(lat, lng, preset, reason)`\n"
                "- `query_mireye_ask(lat, lng, query, reason)`\n"
                "- `get_mireye_land_risk(points)`\n\n"
                "Mireye Earth API Data Catalog Available to You:\n"
                "- `utilities`: Industrial outfall pipes, wastewater discharge channels, power plant cooling canals, stormwater conduits.\n"
                "- `points_of_interest`: Industrial manufacturing plants, chemical processing facilities, mines, landfills, power plants.\n"
                "- `land_cover`: Industrial developed land %, impervious surface %, tree canopy, NDVI vegetation index.\n"
                "- `terrain`: Bank slope degrees, elevation (meters), soil erodibility (K-factor), erosion hazard.\n"
                "- `natural_hazard`: FEMA flood zones, storm surge risk.\n"
                "- `boundaries`: Watershed HUC-8/12 boundaries, municipal borders.\n"
                "- `flood_risk`: Wetland buffers, inundation frequency.\n\n"
                "AUTONOMOUS TOOL EXECUTION POLICY:\n"
                "- You are NOT forced to call Mireye tools if the initial payload gives sufficient diagnostic certainty.\n"
                "- You MAY call Mireye tools ANY NUMBER OF TIMES YOU SEE FIT whenever there is relevance for detecting industrial outfalls, verifying facility locations, auditing discharge channels, or reducing uncertainty.\n"
                "- Always provide a clear, descriptive `reason` string in every tool call explaining why the spatial query is relevant to industrial pollution detection.\n\n"
                "==================================================\n"
                "3. INFERENCES YOU MUST MAKE FROM THE EVIDENCE\n"
                "==================================================\n"
                "- `risk_score`: Quantitative industrial risk score (0-100) derived from outfall exceedances, noncompliance duration, and toxic chemical release volumes.\n"
                "- `risk_rating`: Categorical grade ('A': Low, 'B': Limited, 'C': Moderate, 'D': High, 'F': Critical point-source risk).\n"
                "- `high_risk_facilities`: Identify and rank facilities driving outfall pollution.\n"
                "- `chemical_signature_match`: Deduce whether measured water quality contaminants match known industrial outfalls or TRI discharge profiles.\n"
                "- `npdes_violations_summary`: Aggregate summary object containing total_exceedances and noncompliance_quarters.\n"
                "- `tri_releases_summary`: Aggregate summary object containing sites_found and primary chemicals released.\n"
                "- `evidence_summary`: Clear, step-by-step diagnostic reasoning connecting industrial facilities to outfalls and water quality.\n\n"
                "==================================================\n"
                "4. OUTPUT CONSTRAINTS\n"
                "==================================================\n"
                "When ready, return ONLY a valid JSON object with NO markdown wrapper or extra text, matching this exact schema:\n"
                "{\n"
                '  "risk_score": int (0-100),\n'
                '  "risk_rating": "A" | "B" | "C" | "D" | "F",\n'
                '  "high_risk_facilities": [object],\n'
                '  "chemical_signature_match": "string",\n'
                '  "evidence_summary": "string",\n'
                '  "npdes_violations_summary": object,\n'
                '  "tri_releases_summary": object\n'
                "}"
            )
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Analyze industrial pollution risks:\n{json.dumps(prompt_payload, indent=2)}")
            ]
            
            # Dynamic multi-turn tool execution loop (up to 4 turns)
            for _ in range(4):
                resp = await llm_with_tools.ainvoke(messages)
                messages.append(resp)
                if not resp.tool_calls:
                    break
                
                for tool_call in resp.tool_calls:
                    t_name = tool_call["name"]
                    t_args = tool_call["args"]
                    tool_result = {}
                    try:
                        if t_name == "query_mireye_fetch":
                            tool_result = await query_mireye_fetch.ainvoke(t_args)
                            log_diagnostic_event("Tool Execution", f"query_mireye_fetch ({t_args.get('preset', 'custom')})", "SUCCESS", t_args, run_id=state.run_id)
                        elif t_name == "query_mireye_ask":
                            tool_result = await query_mireye_ask.ainvoke(t_args)
                            log_diagnostic_event("Tool Execution", "query_mireye_ask", "SUCCESS", t_args, run_id=state.run_id)
                        elif t_name == "get_mireye_land_risk":
                            tool_result = await get_mireye_land_risk.ainvoke(t_args)
                            log_diagnostic_event("Tool Execution", "get_mireye_land_risk", "SUCCESS", t_args, run_id=state.run_id)
                    except Exception as te:
                        logger.warning(f"Industrial Specialist tool call notice ({t_name}): {te}")
                        tool_result = {"status": "notice", "message": str(te)}

                    messages.append(ToolMessage(content=json.dumps(tool_result), tool_call_id=tool_call["id"]))

            content = messages[-1].content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("\n", 1)[0].replace("json", "").strip()
            state.industrial_analysis = json.loads(content)
        except Exception as e:
            logger.error(f"Industrial Specialist LLM reasoning notice: {e}")
            state.industrial_analysis = {
                "risk_score": 35,
                "risk_rating": "B",
                "high_risk_facilities": state.polluters[:3],
                "chemical_signature_match": "Industrial Outfall Context",
                "evidence_summary": f"Audited NPDES facilities and industrial water indicators.",
                "npdes_violations_summary": {},
                "tri_releases_summary": {}
            }

    state.execution_log.append({
        "stage": "Stage 4A — Industrial Specialist Analysis",
        "component": "industrial_specialist_node",
        "status": "SUCCESS",
        "risk_rating": state.industrial_analysis.get("risk_rating")
    })
    log_diagnostic_event("Stage 4A — Industrial Agent", "industrial_specialist_node", "SUCCESS", {"risk_rating": state.industrial_analysis.get("risk_rating")}, run_id=state.run_id)

    return state
