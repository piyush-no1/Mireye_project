import asyncio
from typing import Dict, Any, List
from app.agent.state import AssessmentState
from app.tools.mireye_dynamic_tool import query_mireye_natural_language
from app.core.logging import logger, log_diagnostic_event

async def targeted_fetch_node(state: AssessmentState) -> AssessmentState:
    """
    Targeted Fetch Node:
    Takes the `data_needed_to_confirm` natural-language queries from `hypothesis_generation`
    and executes them generically against Mireye Earth API without keyword-matching or field translations.
    """
    stage_name = "Stage 5b — Targeted Evidence Fetch"
    if state.status in ("failed", "needs_clarification"):
        return state

    hypotheses_data = state.hypothesis_output or {}
    hypotheses_list = hypotheses_data.get("hypotheses", [])

    # Extract all data_needed_to_confirm queries generically into a flat list
    queries_to_fetch: List[str] = []
    for hyp in hypotheses_list:
        for query_str in hyp.get("data_needed_to_confirm", []):
            cleaned_q = str(query_str).strip()
            if cleaned_q and cleaned_q not in queries_to_fetch:
                queries_to_fetch.append(cleaned_q)

    # Determine coordinates and bounding box context
    lat = None
    lng = None
    if state.resolved_location:
        lat = state.resolved_location.get("lat")
        lng = state.resolved_location.get("lng")
    elif state.start_location:
        lat = state.start_location.get("lat")
        lng = state.start_location.get("lng")
    elif state.land_risk_points and len(state.land_risk_points) > 0:
        lat = state.land_risk_points[0].get("lat")
        lng = state.land_risk_points[0].get("lng")

    bbox = state.hydrology.get("bbox") if state.hydrology else None

    # Generic execution loop over all requested query strings
    targeted_results: Dict[str, Any] = {}
    investigation_log_entries: List[Dict[str, Any]] = []

    async def _fetch_single_query(query_str: str, round_idx: int):
        try:
            logger.info(f"Targeted Fetch executing query [{round_idx}]: '{query_str}'")
            res = await query_mireye_natural_language(
                query_str=query_str,
                lat=lat,
                lng=lng,
                bbox=bbox
            )
            targeted_results[query_str] = res
            investigation_log_entries.append({
                "round": round_idx,
                "tool": "mireye_dynamic_ask",
                "reason": f"Targeted evidence query: {query_str}",
                "arguments": {"query": query_str, "lat": lat, "lng": lng},
                "result_status": "success",
                "source": "Mireye",
                "summary": str(res.get("findings") or res.get("answer") or res)
            })
        except Exception as e:
            logger.warning(f"Targeted fetch query '{query_str}' failed: {e}")
            targeted_results[query_str] = {"error": str(e), "source": "ERROR_FALLBACK"}
            investigation_log_entries.append({
                "round": round_idx,
                "tool": "mireye_dynamic_ask",
                "reason": f"Targeted evidence query: {query_str}",
                "arguments": {"query": query_str},
                "result_status": "error",
                "source": "Mireye",
                "summary": f"Failed to retrieve data: {e}"
            })

    if queries_to_fetch:
        tasks = [
            _fetch_single_query(q_str, idx + 1)
            for idx, q_str in enumerate(queries_to_fetch)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
    else:
        logger.info("No additional targeted queries requested by hypothesis generation.")

    state.targeted_evidence = targeted_results
    state.source_investigation_log = investigation_log_entries

    state.execution_log.append({
        "stage": stage_name,
        "component": "targeted_fetch_node",
        "status": "SUCCESS",
        "queries_executed": len(queries_to_fetch),
        "results_count": len(targeted_results)
    })

    log_diagnostic_event(
        stage=stage_name,
        component="targeted_fetch_node",
        status="SUCCESS",
        details={
            "queries": queries_to_fetch,
            "targeted_evidence": targeted_results
        },
        run_id=state.run_id
    )

    return state
