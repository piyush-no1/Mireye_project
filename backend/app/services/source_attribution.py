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
        "REASONING PROTOCOL\n"
        "==================================================\n"
        "You MUST execute your investigation in the following strict sequence. Do not skip phases or jump to conclusions.\n\n"
        "PHASE 1 — IDENTIFY IMPAIRMENTS\n"
        "- Start ONLY from ATTAINS impairments flagged as 'is_primary_path': true.\n"
        "- Nearby/contextual assessment units (is_primary_path: false) are NOT evidence that the primary path is impaired. Use them for supporting context only.\n"
        "- If there are no meaningful primary-path impairments, do not invent sources.\n\n"
        "PHASE 2 — GENERATE CANDIDATE SOURCES\n"
        "- Generate candidate source categories (Point, Nonpoint, Infrastructure, Natural) relevant to the actual impairment and supplied evidence.\n"
        "- Do NOT output every theoretically possible source.\n\n"
        "PHASE 3 — POLLUTANT COMPATIBILITY\n"
        "- Could this source plausibly contribute to THIS specific impairment? If a candidate has no plausible pollutant pathway, discard it or mark it unsupported.\n\n"
        "PHASE 4 — SPATIAL / HYDROLOGICAL ANALYSIS\n"
        "- Determine hydrological connectivity (upstream, downstream, tributary_connected, within_watershed, adjacent, disconnected, unknown).\n"
        "- Hydrological connectivity is more important than geographic proximity. (e.g. a downstream facility is NOT a likely source).\n\n"
        "PHASE 5 — EVIDENCE MATRIX & COMPETING SOURCE COMPARISON\n"
        "- Internally evaluate every candidate using Direct Evidence, Supporting Evidence, Contradicting Evidence, and Competing Sources.\n"
        "- You must actively look for evidence AGAINST strong hypotheses (e.g. absent pollutants, disconnected watersheds).\n"
        "- If multiple sources are plausible, compare them. Do not force a single source when multiple contributors remain plausible.\n\n"
        "PHASE 6 — SOURCE-SPECIFIC INVESTIGATION & DYNAMIC MIREYE\n"
        "- Identify exact missing information needed to reduce uncertainty between competing source hypotheses.\n\n"
        "==================================================\n"
        "DYNAMIC MIREYE INVESTIGATION\n"
        "==================================================\n"
        "Mireye is STRICTLY an INFORMATION RETRIEVAL TOOL. It provides environmental facts.\n"
        "Do NOT ask Mireye to perform source attribution, causal reasoning, or hypothesis testing.\n"
        "You (GPT) must perform the causal interpretation and attribution based on the facts Mireye returns.\n\n"
        "- `query_mireye_fetch`: Use for structured environmental information (e.g. agricultural extent, residential density, developed land, impervious surface).\n"
        "- `query_mireye_ask`: Use for information requests requiring Mireye to gather or describe contextual environmental info (e.g. \"What agricultural land-use characteristics are present upstream?\").\n\n"
        "BAD query: \"Is the agricultural land upstream causing the nutrient impairment?\"\n"
        "GOOD query: \"What agricultural land-use characteristics are present upstream of this assessment unit?\"\n\n"
        "Limit: You may use Mireye up to 5 times. Zero calls are also valid if evidence is sufficient.\n\n"
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
        "{\n"
        '  "impairments": [\n'
        "    {\n"
        '      "impairment": "...",\n'
        '      "affected_uses": ["..."],\n'
        '      "sources": [\n'
        "        {\n"
        '          "source_type": "...",\n'
        '          "source_name": "...",\n'
        '          "source_id": null,\n'
        '          "latitude": null,\n'
        '          "longitude": null,\n'
        '          "geography_type": "point | watershed | assessment_unit | polygon | region | unknown",\n'
        '          "geography_id": null,\n'
        '          "relationship_to_primary_path": "upstream | downstream | adjacent | within_watershed | tributary_connected | disconnected | unknown",\n'
        '          "attribution": "DOCUMENTED | LIKELY | POSSIBLE | UNSUPPORTED",\n'
        '          "confidence": "HIGH | MEDIUM | LOW",\n'
        '          "supporting_evidence": ["..."],\n'
        '          "contradicting_evidence": ["..."],\n'
        '          "evidence_sources": ["ATTAINS", "ECHO", "WQP", "USGS", "NLDI", "Mireye"]\n'
        "        }\n"
        "      ]\n"
        "    }\n"
        "  ],\n"
        '  "major_source_findings": ["..."],\n'
        '  "source_data_gaps": ["..."],\n'
        '  "overall_source_reasoning": "..."\n'
        "}\n\n"
        "In `overall_source_reasoning`, you MUST explicitly state how many times you called the Mireye tool (e.g., 'Mireye was called 2 times.' or 'Mireye was not called.').\n"
        "For physical facilities, coordinates MUST come from trusted supplied data. Never invent coordinates.\n"
        "For diffuse sources, latitude/longitude must be null; use geography_type/geography_id where available.\n"
        "Respond with the raw JSON string only, so it can be parsed."
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
        # Wait, create_react_agent expects `{"messages": [("user", content)]}`
        inputs = {"messages": [("user", f"Analyze this environmental dataset for source attribution:\n{json.dumps(data_payload, indent=2)}")]}
        response = await agent.ainvoke(inputs)
        
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
                investigation_log.append({
                    "round": len(investigation_log) + 1,
                    "tool": msg.name,
                    "reason": "Agent requested additional environmental context.",
                    "arguments": tc.get("args", {}),
                    "result_status": "success" if not msg.content.startswith('{"error"') else "error",
                    "source": "Mireye",
                    "summary": f"Mireye call to {msg.name}"
                })
        
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
