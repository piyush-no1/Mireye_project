from langgraph.graph import StateGraph, END, START
from app.agent.state import AssessmentState
from app.agent.nodes.geocode_node import geocode_node
from app.agent.nodes.hydrology_node import hydrology_node
from app.agent.nodes.spatial_translation_node import spatial_translation_node
from app.agent.nodes.parallel_fetch_node import parallel_fetch_node
from app.agent.nodes.aggregate_node import aggregate_node
from app.agent.nodes.persist_node import persist_node, persist_assessment_node
from app.agent.nodes.source_attribution_node import source_attribution_node

def route_after_geocode(state: AssessmentState) -> str:
    if state.status == "needs_clarification":
        return "persist_node"
    return "hydrology_node"

def route_after_hydrology(state: AssessmentState) -> str:
    if state.status == "failed":
        return "persist_node"
    return "spatial_translation_node"

def route_after_spatial(state: AssessmentState) -> str:
    if state.status == "failed":
        return "persist_node"
    return "parallel_fetch_node"

def create_assessment_graph():
    builder = StateGraph(AssessmentState)

    builder.add_node("geocode_node", geocode_node)
    builder.add_node("hydrology_node", hydrology_node)
    builder.add_node("spatial_translation_node", spatial_translation_node)
    builder.add_node("parallel_fetch_node", parallel_fetch_node)
    builder.add_node("aggregate_node", aggregate_node)
    builder.add_node("persist_assessment_node", persist_assessment_node)
    builder.add_node("source_attribution_node", source_attribution_node)
    builder.add_node("persist_node", persist_node)

    builder.add_edge(START, "geocode_node")
    builder.add_conditional_edges("geocode_node", route_after_geocode)
    builder.add_conditional_edges("hydrology_node", route_after_hydrology)
    builder.add_conditional_edges("spatial_translation_node", route_after_spatial)
    builder.add_edge("parallel_fetch_node", "aggregate_node")
    builder.add_edge("aggregate_node", "persist_assessment_node")
    builder.add_edge("persist_assessment_node", "source_attribution_node")
    builder.add_edge("source_attribution_node", "persist_node")
    builder.add_edge("persist_node", END)

    return builder.compile()

assessment_graph = create_assessment_graph()
