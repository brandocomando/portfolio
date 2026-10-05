"""Chat Streaming API Endpoint via Server-Sent Events (SSE)."""

import json
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from backend.app.schemas.chat import ChatRequest
from backend.app.core.security import UserIdentity, get_current_user_optional
from backend.app.core.rate_limiter import RateLimitStatus, rate_limit_gate
from backend.app.services.retrieval_service import retrieval_service
from backend.app.services.llm_client import llm_client
from backend.app.services.intent import classify_intent, IntentType
from backend.app.services.firestore_service import firestore_service

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger("portfolio.api.chat")


@router.post("/stream", summary="Stream AI Response with RAG Context")
async def chat_stream(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    user: UserIdentity = Depends(get_current_user_optional),
    rate_status: RateLimitStatus = Depends(rate_limit_gate)
):
    """Streams conversational token-by-token answer grounded in Brandon's portfolio."""
    # 1. Intent Classification
    intent_type, _ = classify_intent(request.question)

    if intent_type != IntentType.PORTFOLIO_SEARCH:
        # Non-search queries (greetings, pings, math, general off-topic, guardrails)
        raw_sources = []
        formatted_sources = []
    else:
        # Genuine technical/portfolio query
        raw_sources = retrieval_service.retrieve(request.question, top_k=3)
        formatted_sources = [
            {
                "id": s["id"],
                "title": s["title"].replace("Experience: ", "").replace("Project: ", "").replace("Skills: ", ""),
                "category": s["category"],
                "rrf_score": s["rrf_score"],
            }
            for s in raw_sources
        ]

    # 2. SSE Generator
    async def event_generator() -> AsyncGenerator[str, None]:
        # Initial event: Send retrieved sources and quota status
        yield f"event: sources\ndata: {json.dumps({'sources': formatted_sources, 'tier': rate_status.tier, 'remaining': rate_status.remaining})}\n\n"

        full_answer_accumulator = []

        # Stream tokens
        async for chunk_json in llm_client.stream_response(
            question=request.question,
            sources=raw_sources,
            conversation_history=[m.model_dump() for m in request.messages]
        ):
            try:
                data = json.loads(chunk_json)
                token = data.get("token", "")
                full_answer_accumulator.append(token)
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
            except Exception:
                yield f"event: token\ndata: {chunk_json}\n\n"

        # Final event: Done
        yield f"event: done\ndata: {json.dumps({'status': 'completed', 'remaining': rate_status.remaining})}\n\n"

        # Record lead interaction in background
        complete_answer = "".join(full_answer_accumulator)
        background_tasks.add_task(
            firestore_service.record_lead_interaction,
            user=user,
            question=request.question,
            answer_preview=complete_answer
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/graph", summary="Execute LangGraph Stateful Multi-Agent Reasoning")
async def chat_langgraph(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    user: UserIdentity = Depends(get_current_user_optional),
    rate_status: RateLimitStatus = Depends(rate_limit_gate)
):
    """Executes stateful LangGraph agent graph with explicit guardrail, retrieval, and reasoning nodes."""
    from backend.app.services.langgraph_agent import run_langgraph_agent

    result = await run_langgraph_agent(request.question)

    # Record lead interaction in background
    background_tasks.add_task(
        firestore_service.record_lead_interaction,
        user=user,
        question=request.question,
        answer_preview=result["answer"]
    )

    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "reasoning": result["reasoning"],
        "engine": "langgraph-state-machine",
        "remaining_quota": rate_status.remaining,
        "tier": rate_status.tier
    }
