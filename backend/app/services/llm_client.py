"""Gemini LLM Client with Streaming and RAG Context Injection.

Features:
- Conversational Persona (acts as Brandon's AI Assistant, not a search engine)
- Prompt Injection & Security Guardrails
- Multi-turn Conversational Context
- Streaming Server-Sent Events (SSE)
- High-fidelity Conversational Fallback when GEMINI_API_KEY is not configured
"""

import os
import re
import json
import asyncio
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional

from backend.app.core.config import settings
from backend.app.services.synthesizer import synthesize_conversational_response

logger = logging.getLogger("portfolio.llm")

SYSTEM_PROMPT = """You are Brandon Foster's personal AI Assistant on his engineering portfolio website.
You are having an engaging, natural conversation with technical recruiters, hiring managers, and engineers.

Tone & Persona:
- Conversational, sharp, friendly, and articulate—like a senior platform engineer chatting with a colleague over coffee.
- Speak naturally in complete, fluid sentences and short paragraphs.
- Do NOT speak like a search engine or quote document categories like "Based on Brandon's background in Skills:".
- Directly answer the question right away, and weave in relevant stories, architectural highlights, metrics, and technologies.
- If asked "did he really do this?", "is this true?", or asked to verify a specific claim or accomplishment from his profile, ALWAYS directly confirm ("Yes, Brandon really did this!") and focus your answer on the concrete architecture, context, and technical implementation of that specific item, rather than reciting unrelated resume milestones.
- Answer the user's specific question directly instead of reciting a generic bulleted laundry list of facts.
- If someone says "hi", "test", or chats casually, be warm and conversational! Don't recite a resume dump.
- If asked about Brandon's skills, experience, or projects, talk about what he built, why he made specific architectural choices, and the real-world impact (e.g., migrating mission-critical services to EKS with zero downtime, saving $10K+/month in cloud costs, Confluent Cloud migration, custom Go tooling).
- Always end with a helpful, friendly follow-up question inviting them to explore deeper.

Scope & Task Boundaries (STRICT):
- Your sole purpose is to represent Brandon Foster and discuss his professional background, platform engineering architectures, migrations, and projects.
- You are NOT a general-purpose programming assistant, code-generation engine, homework tutor, or algorithm solver.
- NEVER write arbitrary code, scripts, algorithms, or tutorials for user programming tasks (such as "write a script for a linked list in python", "write a sorting algorithm", "solve this LeetCode problem", "write a web scraper for me").
- Even if the user flatters or mentions Brandon to prompt you (e.g., "Brandon is smart... but first write me a script for X"), firmly and politely decline the coding request and steer back to Brandon's portfolio:
  "While Brandon writes plenty of Python and Go, I'm here specifically to discuss his platform engineering background, architectures, and projects rather than write custom scripts or solve general programming exercises. Feel free to ask about his work with Kubernetes, Terraform, Confluent Kafka, or AI infrastructure!"
- The only code snippets you may discuss are small architectural or configuration examples illustrating how Brandon built his own projects or infrastructure.

Grounding & Context Sufficiency:
- Ground your answers strictly in the provided knowledge base excerpts.
- If asked about a technology, framework, or domain that Brandon has NOT worked with (or is not in the knowledge base excerpts), be honest and transparent! For example: "Brandon's public portfolio doesn't highlight production work with [Technology], but he has deep experience in related areas like [X and Y]." Do not invent or hallucinate production experience.

Conversation Continuity (multi-turn):
- You are mid-conversation. Read the prior turns before answering.
- If your previous message offered options (e.g. "Would you like to know more about X, Y, or Z?") and the user replies with a short phrase like "Y" or "the Y one", they picked that option: answer about Y specifically, in the same context as the previous discussion (e.g. "the Terraform setup" for this portfolio platform means this platform's Terraform, not a generic overview).
- If the user just says "yes", "sure", or "tell me more", continue the most recent topic in more depth.
- Do not repeat content you already gave in earlier turns; build on it.
- The knowledge base excerpts below are retrieved per message and may include loosely related material. Use only what is relevant to the user's current question.

Privacy & Guardrails:
- NEVER reveal personal contact information such as Brandon's personal phone number, direct email address, home address, age, relationship status, or salary. Brandon's direct contact info is strictly confidential and not published on this site.
- If asked for his direct contact info or private personal questions about Brandon, respond with: "I don't know—maybe you should ask him! You can submit your question and email through the [Contact Page](#contact), and it will be forwarded directly to him."
- If asked general off-topic questions, trivia, or general tasks unrelated to Brandon Foster (such as general world trivia, recipes, or general chat), respond that this is outside your configuration: "That's not something I'm configured to answer! As Brandon Foster's portfolio assistant, I'm focused specifically on his platform engineering background, architectures, and projects. For general questions like this, you might want to ask ChatGPT or Claude! Feel free to ask about Brandon's work with Kubernetes, Terraform, Confluent Kafka, or AI infrastructure."

Knowledge base about Brandon:
{context}
"""

# Number of prior messages (user + assistant) sent to the LLM for multi-turn context.
MAX_HISTORY_MESSAGES = 12


def check_guardrails(query: str) -> bool:
    """Detects prompt injection attempts."""
    patterns = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"system\s+prompt",
        r"delete\s+your",
        r"reveal\s+your",
        r"jailbreak",
        r"you\s+are\s+now\s+in\s+dan\s+mode",
    ]
    query_lower = query.lower()
    return any(re.search(pat, query_lower) for pat in patterns)


class LLMClient:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        self.model_name = settings.GEMINI_MODEL
        self._genai_client = None

        if self.api_key and self.api_key != "placeholder-key-replace-in-secret-manager":
            try:
                from google import genai
                self._genai_client = genai.Client(api_key=self.api_key)
                logger.info(f"Initialized Gemini client with model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Could not initialize google-genai SDK: {e}")

    def _format_context(self, sources: List[Dict[str, Any]]) -> str:
        formatted = []
        for i, s in enumerate(sources, 1):
            clean_content = re.sub(r"\[[A-Z\s\:\&]+\]", "", s.get("content", "")).strip()
            formatted.append(f"--- [Topic: {s.get('title', '')}] ---\n{clean_content}\n")
        return "\n".join(formatted)

    async def stream_response(
        self,
        question: str,
        sources: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[str, None]:
        """Streams response tokens as SSE data events."""
        # 1. Guardrail Check
        if check_guardrails(question):
            deflection = (
                "I am Brandon Foster's portfolio assistant, designed to discuss his engineering background, "
                "projects, and architecture experience. I cannot modify my system instructions. "
                "Feel free to ask about Brandon's work with Kubernetes, Terraform, MLOps, or Kafka!"
            )
            for word in deflection.split(" "):
                yield json.dumps({"token": word + " "}) + "\n"
                await asyncio.sleep(0.02)
            return

        # 2. If Gemini API is available, invoke streaming with multi-turn history
        if self._genai_client:
            emitted_any = False
            try:
                from google.genai import types

                context_str = self._format_context(sources)
                full_system_prompt = SYSTEM_PROMPT.format(context=context_str)

                turns = self._build_history(
                    (conversation_history or []) + [{"role": "user", "content": question}]
                )
                contents = [
                    types.Content(role=role, parts=[types.Part.from_text(text=text)])
                    for role, text in turns
                ]

                config = types.GenerateContentConfig(
                    system_instruction=full_system_prompt,
                    temperature=0.7,
                )

                stream = await self._genai_client.aio.models.generate_content_stream(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )
                async for chunk in stream:
                    if chunk.text:
                        emitted_any = True
                        yield json.dumps({"token": chunk.text}) + "\n"
                return
            except Exception as e:
                logger.error(
                    f"Gemini API error during streaming (model={self.model_name}): {e}. "
                    + ("Aborting partially streamed answer." if emitted_any else "Falling back to conversational synthesizer.")
                )
                if emitted_any:
                    # Don't splice an unrelated canned answer onto a half-finished Gemini reply.
                    yield json.dumps({"token": "\n\n_(Sorry—my connection dropped mid-answer. Please ask again!)_"}) + "\n"
                    return

        # 3. Conversational Synthesizer (Works offline, in testing, and as reliable fallback)
        fallback_text = synthesize_conversational_response(
            question=question,
            raw_sources=sources,
            conversation_history=conversation_history
        )
        tokens = re.findall(r"\S+|\n", fallback_text)
        for t in tokens:
            yield json.dumps({"token": t + (" " if t != "\n" else "")}) + "\n"
            await asyncio.sleep(0.015)

    @staticmethod
    def _build_history(
        conversation_history: Optional[List[Dict[str, str]]],
        max_turns: int = MAX_HISTORY_MESSAGES,
    ) -> List[tuple]:
        """Normalizes chat history into alternating (role, text) turns for Gemini.

        - Keeps the most recent `max_turns` messages (enough to hold several Q&A exchanges).
        - Drops leading assistant turns (e.g. the UI's canned welcome message) so history starts with the user.
        - Merges consecutive same-role turns and skips empty ones.
        """
        turns: List[tuple] = []
        for msg in (conversation_history or [])[-max_turns:]:
            text = (msg.get("content") or "").strip()
            if not text or msg.get("role") == "system":
                continue
            role = "user" if msg.get("role") == "user" else "model"
            if not turns and role == "model":
                continue
            if turns and turns[-1][0] == role:
                turns[-1] = (role, turns[-1][1] + "\n\n" + text)
            else:
                turns.append((role, text))
        return turns

    def _synthesize_fallback(
        self,
        question: str,
        sources: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Grounded conversational synthesis for offline dev/test environments."""
        return synthesize_conversational_response(
            question=question,
            raw_sources=sources,
            conversation_history=conversation_history
        )


llm_client = LLMClient()
