import re
import json
import asyncio
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from backend.app.schemas.chat import ChatRequest
from backend.app.core.security import UserIdentity, get_current_user_optional
from backend.app.core.rate_limiter import RateLimitStatus, rate_limit_gate
from backend.app.services.retrieval_service import retrieval_service
from backend.app.services.llm_client import llm_client
from backend.app.services.synthesizer import is_conversational_followup, is_generic_continuation, synthesize_conversational_response
from backend.app.services.intent import classify_intent, IntentType, is_query_about_brandon
from backend.app.services.firestore_service import firestore_service

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger("portfolio.api.chat")


def _last_turns(messages) -> tuple[str, str]:
    """Returns (last_user_content, last_assistant_content) from prior turns."""
    last_asst, last_user = "", ""
    for m in reversed(messages):
        if m.role == "assistant" and not last_asst:
            last_asst = m.content
        elif m.role == "user" and not last_user:
            last_user = m.content
        if last_asst and last_user:
            break
    return last_user, last_asst


def _offered_options(assistant_text: str) -> str:
    """Extracts the trailing follow-up question(s) the assistant offered (e.g. 'Would you like ... X, Y, or Z?')."""
    questions = re.findall(r"[^.!?\n]*\?", assistant_text)
    return questions[-1].strip() if questions else ""


def build_search_query(question: str, messages) -> str:
    """Builds a retrieval query that reflects what the user is actually asking about.

    - Topic-bearing replies ("terraform setup") search on the user's own words, anchored by the prior
      user question for context. The prior assistant answer is NOT included: its body is about the
      *previous* topic and would crowd the right documents out of the top-k.
    - Bare continuations ("yes", "tell me more") have no topic of their own, so they borrow the
      options the assistant just offered plus the prior user question.
    """
    if not is_conversational_followup(question, messages):
        return question
    last_user, last_asst = _last_turns(messages)
    if is_generic_continuation(question):
        return f"{last_user} {_offered_options(last_asst)}".strip() or question
    return f"{question} {question} {last_user}".strip()  # repeat to weight the user's chosen topic


@router.post("/stream", summary="Stream AI Response with RAG Context")
async def chat_stream(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    user: UserIdentity = Depends(get_current_user_optional),
    rate_status: RateLimitStatus = Depends(rate_limit_gate)
):
    """Streams conversational token-by-token answer grounded in Brandon's portfolio."""
    # Resolve contextual query for multi-turn continuations, options, and short followups
    is_followup = is_conversational_followup(request.question, request.messages)
    search_query = build_search_query(request.question, request.messages)

    # 1. Intent Classification
    intent_type, precomputed_answer = classify_intent(request.question)

    # A reply to the assistant's own question ("check", "help", "yes") is part of the conversation,
    # not a fresh ping/greeting. Safety intents (guardrail/personal/contact) are never overridden.
    if is_followup and intent_type in (IntentType.PING, IntentType.GREETING):
        intent_type, precomputed_answer = IntentType.PORTFOLIO_SEARCH, None

    if intent_type != IntentType.PORTFOLIO_SEARCH:
        # Non-search queries (greetings, pings, math, general off-topic, guardrails, personal)
        raw_sources = []
        formatted_sources = []
    else:
        # Genuine technical/portfolio query
        raw_sources = retrieval_service.retrieve(search_query, top_k=3)

        # System-1 Relevance Gate: If an initial query has zero keyword matches across the knowledge base
        # and negligible dense semantic similarity (<0.135), check if synthesizer recognizes it (e.g. platform architecture,
        # code authorship). If ungrounded, deflect in System-1 to protect LLM token budget and avoid hallucinations.
        has_bm25 = any(s.get("bm25_rank") is not None for s in raw_sources)
        if not is_followup and not has_bm25 and len(raw_sources) > 0:
            top_dense = retrieval_service.retriever._dense_search(search_query, top_n=1)[0][1]
            if top_dense < 0.135:
                candidate_synth = synthesize_conversational_response(
                    question=request.question,
                    raw_sources=[],
                    conversation_history=[m.model_dump() for m in request.messages],
                )
                if "maybe you should ask" not in candidate_synth and "not something I'm configured to answer" not in candidate_synth:
                    precomputed_answer = candidate_synth
                    raw_sources = []
                else:
                    intent_type = IntentType.OFF_TOPIC_GENERAL
                    if is_query_about_brandon(request.question):
                        precomputed_answer = (
                            "I don't know—maybe you should ask Brandon directly! That's outside the scope of Brandon Foster's professional engineering portfolio. "
                            "You can submit your question and email directly through the **[Contact Page](#contact)** and it will be forwarded straight to him.\n\n"
                            "Or feel free to ask about his work with Kubernetes, Terraform, Confluent Kafka, or AI infrastructure!"
                        )
                    else:
                        precomputed_answer = (
                            "That's not something I'm configured to answer! As Brandon Foster's portfolio assistant, I'm focused specifically on his platform engineering background, architectures, and projects. "
                            "For general questions or trivia, you might want to ask **ChatGPT** or **Claude**!\n\n"
                            "Feel free to ask about Brandon's work with Kubernetes, Terraform, Confluent Kafka, or AI infrastructure!"
                        )
                    raw_sources = []

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

        # If non-search intent has an authoritative precomputed answer, stream it directly
        if intent_type != IntentType.PORTFOLIO_SEARCH and precomputed_answer:
            tokens = re.findall(r"\S+|\n", precomputed_answer)
            for t in tokens:
                token_str = t + (" " if t != "\n" else "")
                full_answer_accumulator.append(token_str)
                yield f"event: token\ndata: {json.dumps({'token': token_str})}\n\n"
                await asyncio.sleep(0.015)
        else:
            # Stream tokens from LLM client / conversational synthesizer
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
