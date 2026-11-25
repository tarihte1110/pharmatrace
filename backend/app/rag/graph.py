"""LangGraph workflow definition."""
from langgraph.graph import END, START, StateGraph
from app.rag.nodes import RAGState, generate_node, guardrail_node, retrieve_node


def route_after_guardrail(state: RAGState) -> str:
    return "retrieve" if state.get("is_pharmaceutical") else END


builder = StateGraph(RAGState)
builder.add_node("guardrail", guardrail_node)
builder.add_node("retrieve", retrieve_node)
builder.add_node("generate", generate_node)

builder.add_edge(START, "guardrail")
builder.add_conditional_edges("guardrail", route_after_guardrail, {"retrieve": "retrieve", END: END})
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)

pharma_rag_graph = builder.compile()