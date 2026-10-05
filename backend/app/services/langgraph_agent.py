"""LangGraph Stateful Agent Graph for Advanced Cross-Domain Reasoning.

Implements a StateGraph with:
1. GuardrailNode (Input sanitization & prompt injection prevention)
2. HybridRetrievalNode (In-memory BM25 + Dense vector search)
3. ReasoningNode (Context sufficiency & query evaluation)
4. SynthesisNode (Grounded response generation with source citations)
"""

import re
import json
import logging
from typing import TypedDict, List, Dict, Any, Optional

from langgraph.graph import StateGraph, END
from backend.app.services.retrieval_service import retrieval_service
from backend.app.services.llm_client import llm_client, check_guardrails

logger = logging.getLogger("portfolio.langgraph")


class AgentState(TypedDict):
    question: str
    is_safe: bool
    deflection_message: Optional[str]
    retrieved_docs: List[Dict[str, Any]]
    sources: List[Dict[str, Any]]
    reasoning_notes: str
    final_answer: str


def guardrail_node(state: AgentState) -> Dict[str, Any]:
    """Node 1: Evaluates security guardrails against adversarial prompts."""
    q = state["question"]
    if check_guardrails(q):
        logger.warning(f"LangGraph Guardrail triggered for query: {q[:50]}")
        return {
            "is_safe": False,
            "deflection_message": (
                "I am Brandon Foster's portfolio assistant. I cannot modify my system instructions. "
                "Feel free to ask about Brandon's work with Kubernetes, Terraform, MLOps, or Kafka!"
            ),
            "final_answer": (
                "I am Brandon Foster's portfolio assistant. I cannot modify my system instructions. "
                "Feel free to ask about Brandon's work with Kubernetes, Terraform, MLOps, or Kafka!"
            ),
            "sources": []
        }
    return {"is_safe": True, "deflection_message": None}


def retrieval_node(state: AgentState) -> Dict[str, Any]:
    """Node 2: Interrogates the in-memory Hybrid Retrieval Engine."""
    raw_hits = retrieval_service.retrieve(state["question"], top_k=3)
    formatted_sources = [
        {
            "id": h["id"],
            "title": h["title"],
            "category": h["category"],
            "rrf_score": h["rrf_score"],
            "excerpt": h["content"][:160] + "..."
        }
        for h in raw_hits
    ]
    return {
        "retrieved_docs": raw_hits,
        "sources": formatted_sources
    }


def reasoning_node(state: AgentState) -> Dict[str, Any]:
    """Node 3: Analyzes context sufficiency and extracts key entity relationships."""
    docs = state.get("retrieved_docs", [])
    if not docs:
        notes = "No matching knowledge base documents found."
    else:
        categories = list(set(d.get("category", "") for d in docs))
        notes = f"Retrieved {len(docs)} high-confidence documents across domains: {', '.join(categories)}."

    return {"reasoning_notes": notes}


def synthesis_node(state: AgentState) -> Dict[str, Any]:
    """Node 4: Synthesizes final response grounded in retrieved documentation."""
    docs = state.get("retrieved_docs", [])
    answer = llm_client._synthesize_fallback(state["question"], docs)
    return {"final_answer": answer}


def route_guardrail(state: AgentState) -> str:
    """Conditional router based on guardrail check."""
    return "end" if not state.get("is_safe", True) else "retrieve"


# Compile the StateGraph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("guardrail", guardrail_node)
workflow.add_node("retrieve", retrieval_node)
workflow.add_node("reasoning", reasoning_node)
workflow.add_node("synthesize", synthesis_node)

# Set Entry Point
workflow.set_entry_point("guardrail")

# Add Conditional Edges
workflow.add_conditional_edges(
    "guardrail",
    route_guardrail,
    {
        "end": END,
        "retrieve": "retrieve"
    }
)

workflow.add_edge("retrieve", "reasoning")
workflow.add_edge("reasoning", "synthesize")
workflow.add_edge("synthesize", END)

# Compiled Graph
langgraph_agent = workflow.compile()


async def run_langgraph_agent(question: str) -> Dict[str, Any]:
    """Executes the stateful LangGraph agent for a user question."""
    initial_state: AgentState = {
        "question": question,
        "is_safe": True,
        "deflection_message": None,
        "retrieved_docs": [],
        "sources": [],
        "reasoning_notes": "",
        "final_answer": ""
    }

    result = await langgraph_agent.ainvoke(initial_state)
    return {
        "answer": result.get("final_answer", ""),
        "sources": result.get("sources", []),
        "reasoning": result.get("reasoning_notes", ""),
        "is_safe": result.get("is_safe", True)
    }
