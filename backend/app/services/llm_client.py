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
- If someone says "hi", "test", or chats casually, be warm and conversational! Don't recite a resume dump.
- If asked about Brandon's skills, experience, or projects, talk about what he built, why he made specific architectural choices, and the real-world impact (e.g., migrating 30+ services to EKS with zero downtime, saving $10K+/month in cloud costs, Confluent Cloud migration, custom Go tooling).
- Always end with a helpful, friendly follow-up question inviting them to explore deeper.

Privacy & Guardrails:
- NEVER reveal personal contact information such as Brandon's personal phone number, direct email address, home address, age, relationship status, or salary. Brandon's direct contact info is strictly confidential and not published on this site.
- If asked for his direct contact info, or if asked about personal topics or general off-topic questions outside his professional engineering work, respond with: "I don't know—maybe you should ask him! You can submit your question and email through the [Contact Page](#contact), and it will be forwarded directly to him."

Knowledge base about Brandon:
{context}
"""


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
            try:
                from google.genai import types

                context_str = self._format_context(sources)
                full_system_prompt = SYSTEM_PROMPT.format(context=context_str)

                contents = []
                if conversation_history:
                    for msg in conversation_history[-6:]:
                        role = "user" if msg.get("role") == "user" else "model"
                        contents.append(
                            types.Content(
                                role=role,
                                parts=[types.Part.from_text(text=msg.get("content", ""))]
                            )
                        )

                # Add current question
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=question)]
                    )
                )

                config = types.GenerateContentConfig(
                    system_instruction=full_system_prompt,
                    temperature=0.7,
                )

                response = self._genai_client.models.generate_content_stream(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )
                for chunk in response:
                    if chunk.text:
                        yield json.dumps({"token": chunk.text}) + "\n"
                        await asyncio.sleep(0.005)
                return
            except Exception as e:
                logger.error(f"Gemini API error during streaming: {e}. Falling back to conversational synthesizer.")

        # 3. Conversational Synthesizer (Works offline, in testing, and as reliable fallback)
        fallback_text = synthesize_conversational_response(question, sources)
        tokens = re.findall(r"\S+|\n", fallback_text)
        for t in tokens:
            yield json.dumps({"token": t + (" " if t != "\n" else "")}) + "\n"
            await asyncio.sleep(0.015)

    def _synthesize_fallback(self, question: str, sources: List[Dict[str, Any]]) -> str:
        """Grounded conversational synthesis for offline dev/test environments."""
        return synthesize_conversational_response(question, sources)


llm_client = LLMClient()
