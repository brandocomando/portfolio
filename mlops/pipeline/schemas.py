"""Pydantic v2 Data Contracts for Data Platform & Knowledge Base.

Enforces strict schemas across Bronze, Silver, and Gold Medallion layers.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator


class BioProfile(BaseModel):
    name: str = Field(..., min_length=2, description="Full professional name")
    handle: str = Field(..., min_length=2, description="GitHub/online handle")
    title: str = Field(..., min_length=5, description="Primary professional title")
    location: str = Field(..., description="Geographic location")
    headline: str = Field(..., min_length=10, description="Short elevator pitch")
    email: Optional[str] = Field(None, description="Contact email")
    github: str = Field(..., description="GitHub profile URL")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    summary: str = Field(..., min_length=50, description="Comprehensive bio summary")
    domains: List[str] = Field(..., min_length=1, description="Primary technical domains")


class CareerMilestone(BaseModel):
    id: str = Field(..., pattern=r"^exp-[a-z0-9-]+$", description="Unique milestone ID")
    category: str = Field(..., description="Domain category (e.g. distributed_systems, platform_engineering)")
    title: str = Field(..., min_length=5, description="Project/Initiative title")
    role: str = Field(..., min_length=3, description="Role held during the milestone")
    summary: str = Field(..., min_length=30, description="Detailed description of the initiative")
    impact_metrics: List[str] = Field(..., min_length=1, description="Quantified achievements and metrics")
    technologies: List[str] = Field(..., min_length=1, description="Key technologies utilized")


class ProjectEntry(BaseModel):
    id: str = Field(..., pattern=r"^proj-[a-z0-9-]+$", description="Unique project ID")
    name: str = Field(..., min_length=2, description="Project name")
    repo: str = Field(..., description="GitHub repo path (owner/repo)")
    url: str = Field(..., description="Full repository or live demo URL")
    category: str = Field(..., description="Technical domain category")
    tagline: str = Field(..., min_length=10, description="One-line punchy description")
    summary: str = Field(..., min_length=30, description="Detailed architectural overview")
    highlights: List[str] = Field(default_factory=list, description="Key technical highlights")
    technologies: List[str] = Field(..., min_length=1, description="Tech stack list")


class SkillItem(BaseModel):
    name: str = Field(..., min_length=1)
    proficiency: str = Field(..., pattern=r"^(Expert|Proficient|Familiar)$")
    context: str = Field(..., min_length=10, description="Specific proof-point or practical usage context")


class SkillCategory(BaseModel):
    name: str = Field(..., min_length=3)
    skills: List[SkillItem] = Field(..., min_length=1)


class PersonalProfile(BaseModel):
    location: str = Field(..., description="Geographic location")
    work_preferences: Dict[str, Any] = Field(..., description="Work preference details")
    years_of_experience: str = Field(..., description="DevOps experience years")
    experience_summary: str = Field(..., description="Experience summary statement")
    employers: Dict[str, Any] = Field(..., description="Current and past employers")
    education: Dict[str, Any] = Field(..., description="School and degree")
    hobbies: List[str] = Field(default_factory=list, description="Personal hobbies")
    fun_facts: Dict[str, Any] = Field(..., description="Fun personal facts and preferences")
    socials: Dict[str, str] = Field(..., description="Social profile URLs")



class KnowledgeChunk(BaseModel):
    """Silver-layer semantic chunk ready for vectorization and keyword indexing."""
    id: str = Field(..., description="Unique chunk identifier")
    title: str = Field(..., min_length=3, description="Title of the chunk topic")
    category: str = Field(..., description="Classification category")
    content: str = Field(..., min_length=20, description="Textual body used for retrieval")
    tags: List[str] = Field(default_factory=list, description="Extracted keywords and technology tags")
    source_file: str = Field(..., description="Origin source file")
    token_estimate: int = Field(default=0, description="Estimated token count")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary structured metadata")


class GoldIndexManifest(BaseModel):
    """Metadata manifest describing a published Gold layer retrieval index."""
    build_timestamp: str = Field(..., description="ISO 8601 build timestamp")
    git_sha: str = Field(..., description="Git commit SHA of the source data")
    chunk_count: int = Field(..., ge=1, description="Total number of indexed chunks")
    embedding_model: str = Field(..., description="Embedding model name or algorithm")
    embedding_dim: int = Field(..., ge=1, description="Embedding vector dimensionality")
    vocabulary_size: int = Field(..., ge=1, description="BM25 unique token vocabulary size")
    checksum_sha256: str = Field(..., description="SHA-256 checksum of the serialized index bundle")
