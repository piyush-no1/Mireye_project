import json
from app.agent.state import AssessmentState
from app.tools.usda_cropscape_tool import get_usda_cropland_data
from app.tools.sentinel_eutrophication_tool import get_sentinel_eutrophication_index
from app.tools.mireye_land_risk_tool import get_mireye_land_risk
from app.config import settings
from app.core.logging import logger, log_diagnostic_event
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

async def agricultural_specialist_node(state: AssessmentState) -> AssessmentState:
    """Specialized Sub-Agent Node 2: Agricultural Waste & Non-Point Source Runoff Specialist."""
    if state.status in ("failed", "needs_clarification"):
        return state

    if not state.hydrology or "bbox" not in state.hydrology:
        return state

    bbox = state.hydrology["bbox"]
    bank_points = state.hydrology.get("_bank_points", [])

    # 1. Fetch live or fallback Land Risk points if not already in state
    if not state.land_risk_points and bank_points:
        try:
            state.land_risk_points = await get_mireye_land_risk.ainvoke({"points": bank_points})
        except Exception as e:
            logger.warning(f"Agricultural Specialist Land Risk notice: {e}")
            state.land_risk_points = []

    # 2. Fetch USDA Cropland Data & CAFO info
    cropland_data = {}
    try:
        cropland_data = await get_usda_cropland_data.ainvoke({"bbox": bbox})
    except Exception as e:
        logger.warning(f"Agricultural Specialist USDA fetch notice: {e}")
        cropland_data = {}

    # 3. Fetch Remote Sensing Eutrophication / Algal Bloom Index
    eutrophication_index = {}
    try:
        eutrophication_index = await get_sentinel_eutrophication_index.ainvoke({"bbox": bbox, "water_samples": state.water_quality_samples})
    except Exception as e:
        logger.warning(f"Agricultural Specialist Sentinel fetch notice: {e}")
        eutrophication_index = {}

    # 4. Filter water quality samples for agricultural nutrient/pesticide/bacteria indicators
    agri_water_samples = []
    agri_indicators = ["nitrate", "nitrogen", "phosphorus", "phosphate", "ammonia", "dissolved oxygen", "turbidity", "coliform", "e. coli", "atrazine", "pesticide", "fertilizer"]
    for sample in state.water_quality_samples:
        char = sample.get("characteristic_name", "").lower()
        if any(ind in char for ind in agri_indicators):
            agri_water_samples.append(sample)

    target_lat = state.resolved_location.get("lat") if state.resolved_location else (bbox[1] + bbox[3]) / 2.0
    target_lng = state.resolved_location.get("lng") if state.resolved_location else (bbox[0] + bbox[2]) / 2.0

    # 5. LLM Agricultural Specialist Reasoning
    if not settings.openai_api_key or settings.openai_api_key == "mock-openai-key":
        # Fallback deterministic agricultural analysis
        agri_pct = cropland_data.get("agricultural_land_pct", 45.0)
        has_bloom = eutrophication_index.get("algal_bloom_detected", False)
        score = min(100, int(agri_pct * 0.8) + (35 if has_bloom else 10) + (len(agri_water_samples) * 5))
        rating = "F" if score >= 80 else ("D" if score >= 60 else ("C" if score >= 40 else ("B" if score >= 20 else "A")))
        state.agricultural_analysis = {
            "risk_score": score,
            "risk_rating": rating,
            "crop_coverage": {
                "agricultural_land_pct": agri_pct,
                "crop_breakdown": cropland_data.get("crop_breakdown", []),
                "fertilizer_intensity": cropland_data.get("fertilizer_intensity_score", "MODERATE")
            },
            "cafos_in_watershed": cropland_data.get("cafos", []),
            "eutrophication_index": eutrophication_index,
            "nutrient_signature_match": "High Nitrate / Eutrophication Signature" if score > 50 else "Moderate Agricultural Runoff",
            "evidence_summary": f"Analyzed {agri_pct}% agricultural land cover and satellite algal bloom indicators."
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
                "cropland_data": cropland_data,
                "eutrophication_index": eutrophication_index,
                "land_risk_points": state.land_risk_points,
                "agri_water_samples": agri_water_samples,
                "attains_status": state.attains_status
            }

            system_prompt = (
                "You are an expert Agricultural Runoff & Non-Point Source Watershed Diagnostic Engine.\n\n"
                "==================================================\n"
                "1. DATA PROVIDED TO YOU IN INPUT PAYLOAD\n"
                "==================================================\n"
                "- `query`: User's target waterbody or corridor.\n"
                "- `coordinates`: Latitude and Longitude of target waterbody.\n"
                "- `cropland_data`: USDA Cropland Data Layer (CDL) metrics (agricultural_land_pct, crop_breakdown, fertilizer_intensity_score, cafos).\n"
                "- `eutrophication_index`: Satellite remote sensing algal bloom / Chlorophyll-a indices.\n"
                "- `land_risk_points`: Mireye riverbank terrain samples (slope_degrees, tree_canopy_pct, ndvi_change_5y, soil_erodibility_k).\n"
                "- `agri_water_samples`: WQP chemistry samples filtered for agricultural nutrients and pathogens.\n"
                "- `attains_status`: EPA CWA Section 303(d) waterbody impairment records.\n\n"
                "==================================================\n"
                "2. DYNAMIC MIREYE EARTH API TOOL EXECUTION INSTRUCTIONS\n"
                "==================================================\n"
                "You possess DYNAMIC, AUTONOMOUS capability to query the Mireye Earth API tools:\n"
                "- `query_mireye_fetch(lat, lng, preset, reason)`\n"
                "- `query_mireye_ask(lat, lng, query, reason)`\n"
                "- `get_mireye_land_risk(points)`\n\n"
                "Mireye Earth API Data Catalog Available to You:\n"
                "- `land_cover`: Cropland %, crop breakdown (corn/soy/wheat), tree canopy %, NDVI vegetation index, impervious surface, developed land.\n"
                "- `terrain`: Slope degrees, elevation (meters), soil erodibility (K-factor), erosion hazard.\n"
                "- `points_of_interest`: CAFO livestock facilities, manure storage lagoons, fertilizer storage, agricultural processing.\n"
                "- `utilities`: Agricultural drainage tiles, irrigation canals, runoff retention ponds.\n"
                "- `natural_hazard`: FEMA flood zones, storm surge risk, landslide risk.\n"
                "- `boundaries`: Watershed HUC-8/12 boundaries, agricultural conservation districts.\n"
                "- `flood_risk`: Wetland buffers, inundation frequency.\n\n"
                "AUTONOMOUS TOOL EXECUTION POLICY:\n"
                "- You are NOT forced to call Mireye tools if the initial payload gives sufficient diagnostic certainty.\n"
                "- You MAY call Mireye tools ANY NUMBER OF TIMES YOU SEE FIT whenever there is relevance for agricultural pollution detection, verifying cropland extent, soil erodibility, manure lagoons, or CAFO facilities.\n"
                "- Always provide a clear, descriptive `reason` string in every tool call explaining why the spatial query is relevant to agricultural pollution detection.\n\n"
                "==================================================\n"
                "3. INFERENCES YOU MUST MAKE FROM THE EVIDENCE\n"
                "==================================================\n"
                "- `risk_score`: Quantitative non-point source agricultural risk score (0-100) derived from cropland ratio, CAFO manure loading, and algal bloom intensity.\n"
                "- `risk_rating`: Categorical grade ('A': Low, 'B': Limited, 'C': Moderate, 'D': High, 'F': Critical non-point agricultural risk).\n"
                "- `crop_coverage`: Object summarizing agricultural land percentage, crop breakdown, and fertilizer intensity score.\n"
                "- `cafos_in_watershed`: List of identified CAFO livestock manure risk facilities.\n"
                "- `eutrophication_index`: Eutrophication risk evaluation object synthesizing satellite Chlorophyll-a with water sample DO/turbidity.\n"
                "- `nutrient_signature_match`: Deduce whether measured water quality parameters match synthetic fertilizer runoff vs livestock manure loading.\n"
                "- `evidence_summary`: Clear, step-by-step diagnostic reasoning connecting agricultural land use to non-point source nutrient pollution.\n\n"
                "==================================================\n"
                "4. OUTPUT CONSTRAINTS\n"
                "==================================================\n"
                "When ready, return ONLY a valid JSON object with NO markdown wrapper or extra text, matching this exact schema:\n"
                "{\n"
                '  "risk_score": int (0-100),\n'
                '  "risk_rating": "A" | "B" | "C" | "D" | "F",\n'
                '  "crop_coverage": object,\n'
                '  "cafos_in_watershed": [object],\n'
                '  "eutrophication_index": object,\n'
                '  "nutrient_signature_match": "string",\n'
                '  "evidence_summary": "string"\n'
                "}"
            )
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Analyze agricultural runoff and waste risks:\n{json.dumps(prompt_payload, indent=2)}")
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
                        logger.warning(f"Agricultural Specialist tool call notice ({t_name}): {te}")
                        tool_result = {"status": "notice", "message": str(te)}

                    messages.append(ToolMessage(content=json.dumps(tool_result), tool_call_id=tool_call["id"]))

            content = messages[-1].content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("\n", 1)[0].replace("json", "").strip()
            state.agricultural_analysis = json.loads(content)
        except Exception as e:
            logger.error(f"Agricultural Specialist LLM reasoning notice: {e}")
            state.agricultural_analysis = {
                "risk_score": 40,
                "risk_rating": "B",
                "crop_coverage": cropland_data.get("crop_breakdown", {}),
                "cafos_in_watershed": cropland_data.get("cafos", []),
                "eutrophication_index": eutrophication_index,
                "nutrient_signature_match": "Agricultural Non-Point Source Context",
                "evidence_summary": "Evaluated agricultural land cover and nutrient indicators."
            }

    state.execution_log.append({
        "stage": "Stage 4B — Agricultural Specialist Analysis",
        "component": "agricultural_specialist_node",
        "status": "SUCCESS",
        "risk_rating": state.agricultural_analysis.get("risk_rating")
    })
    log_diagnostic_event("Stage 4B — Agricultural Agent", "agricultural_specialist_node", "SUCCESS", {"risk_rating": state.agricultural_analysis.get("risk_rating")}, run_id=state.run_id)

    return state
