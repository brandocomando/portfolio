"""Chat Request and Response Schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., pattern=r"^(user|assistant|system)$")
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(default_factory=list, description="Prior conversation turns for context")
    question: str = Field(..., min_length=2, max_length=1000, description="The visitor's question")


class RetrievalSource(BaseModel):
    id: str
    title: str
    category: str
    rrf_score: float
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[RetrievalSource] = Field(default_factory=list)
    remaining_quota: int
    tier: str
