"""Silver Layer Transformation: Cleans, schema-validates, chunks, and enriches data.

Applies Pydantic v2 data contracts, merges GitHub live metrics, performs semantic
chunking, and executes DataOps quality assertions before Gold indexing.
"""

import json
import datetime
from pathlib import Path
from typing import List

from mlops.pipeline.schemas import (
    BioProfile,
    CareerMilestone,
    ProjectEntry,
    SkillCategory,
    KnowledgeChunk,
)

BRONZE_DIR = Path(__file__).resolve().parent.parent / "data" / "bronze"
SILVER_DIR = Path(__file__).resolve().parent.parent / "data" / "silver"


def estimate_tokens(text: str) -> int:
    """Approximate token count (rule of thumb: ~4 characters per token)."""
    return max(1, len(text) // 4)


def run_silver_transform():
    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Bronze payloads
    with open(BRONZE_DIR / "bio_raw.json", "r") as f:
        bio_raw = json.load(f)["payload"]
    with open(BRONZE_DIR / "experience_raw.json", "r") as f:
        exp_raw = json.load(f)["payload"]["milestones"]
    with open(BRONZE_DIR / "projects_raw.json", "r") as f:
        proj_raw = json.load(f)["payload"]["projects"]
    with open(BRONZE_DIR / "skills_raw.json", "r") as f:
        skills_raw = json.load(f)["payload"]["skill_categories"]

    # Load GitHub live repos for enrichment (if available)
    gh_repos_map = {}
    gh_file = BRONZE_DIR / "github_repos_raw.json"
    if gh_file.exists():
        with open(gh_file, "r") as f:
            gh_data = json.load(f)
            for repo in gh_data.get("payload", []):
                gh_repos_map[repo.get("name")] = repo

    # 2. Schema Validation via Pydantic
    bio = BioProfile.model_validate(bio_raw)
    milestones = [CareerMilestone.model_validate(m) for m in exp_raw]
    projects = [ProjectEntry.model_validate(p) for p in proj_raw]
    skill_categories = [SkillCategory.model_validate(s) for s in skills_raw]

    print(f"✅ Schema validation passed: Bio, {len(milestones)} milestones, {len(projects)} projects, {len(skill_categories)} skill groups")

    # 3. Semantic Chunk Generation
    chunks: List[KnowledgeChunk] = []

    # Bio Chunks
    bio_content = (
        f"Brandon Foster ({bio.handle}) is a {bio.title} based in {bio.location}.\n"
        f"Headline: {bio.headline}\n"
        f"Overview: {bio.summary}\n"
        f"Core Technical Domains: {', '.join(bio.domains)}.\n"
        f"Contact: {bio.email} | GitHub: {bio.github} | LinkedIn: {bio.linkedin or 'N/A'}"
    )
    chunks.append(KnowledgeChunk(
        id="chunk-bio-overview",
        title="Brandon Foster Professional Overview & Domains",
        category="bio",
        content=bio_content,
        tags=["bio", "overview", "platform_engineering", "mlops", "distributed_systems"],
        source_file="bio.yaml",
        token_estimate=estimate_tokens(bio_content),
        metadata={"handle": bio.handle, "location": bio.location}
    ))

    # Experience Chunks
    for m in milestones:
        impact_str = "\n".join([f"  • {item}" for item in m.impact_metrics])
        tech_str = ", ".join(m.technologies)
        content = (
            f"[CAREER EXPERIENCE] {m.title}\n"
            f"Role: {m.role} | Category: {m.category}\n"
            f"Summary: {m.summary.strip()}\n"
            f"Quantified Impact & Metrics:\n{impact_str}\n"
            f"Technologies Utilized: {tech_str}"
        )
        chunks.append(KnowledgeChunk(
            id=f"chunk-{m.id}",
            title=f"Experience: {m.title}",
            category=m.category,
            content=content,
            tags=[t.lower() for t in m.technologies] + [m.category, "experience"],
            source_file="experience.yaml",
            token_estimate=estimate_tokens(content),
            metadata={"role": m.role, "milestone_id": m.id}
        ))

    # Project Chunks (enriched with GitHub stars/links if available)
    for p in projects:
        gh_meta = gh_repos_map.get(p.repo.split("/")[-1], {})
        stars = gh_meta.get("stars", 0)
        highlights_str = "\n".join([f"  • {h}" for h in p.highlights])
        tech_str = ", ".join(p.technologies)
        content = (
            f"[TECHNICAL PROJECT] {p.name}\n"
            f"Repository: {p.url} (GitHub Stars: {stars})\n"
            f"Tagline: {p.tagline}\n"
            f"Overview: {p.summary.strip()}\n"
            f"Key Architectural Highlights:\n{highlights_str}\n"
            f"Tech Stack: {tech_str}"
        )
        chunks.append(KnowledgeChunk(
            id=f"chunk-{p.id}",
            title=f"Project: {p.name}",
            category=p.category,
            content=content,
            tags=[t.lower() for t in p.technologies] + [p.category, "project", p.name.lower()],
            source_file="projects.yaml",
            token_estimate=estimate_tokens(content),
            metadata={"repo": p.repo, "stars": stars, "project_id": p.id}
        ))

    # Skills Chunks
    for cat in skill_categories:
        skill_lines = []
        all_skill_tags = []
        for s in cat.skills:
            skill_lines.append(f"  • {s.name} ({s.proficiency}): {s.context}")
            all_skill_tags.append(s.name.lower())
        content = (
            f"[TECHNICAL SKILLS: {cat.name.upper()}]\n"
            f"Skills and Production Proof-Points:\n" + "\n".join(skill_lines)
        )
        chunks.append(KnowledgeChunk(
            id=f"chunk-skills-{cat.name.lower().replace(' ', '-').replace('&', 'and')}",
            title=f"Skills: {cat.name}",
            category="skills",
            content=content,
            tags=all_skill_tags + ["skills", cat.name.lower()],
            source_file="skills.yaml",
            token_estimate=estimate_tokens(content),
            metadata={"category_name": cat.name, "skills_count": len(cat.skills)}
        ))

    # 4. DataOps Quality Assertions
    assert len(chunks) >= 10, f"DataOps Assertion Failed: Expected at least 10 chunks, got {len(chunks)}"
    unique_ids = set()
    for c in chunks:
        assert c.id not in unique_ids, f"DataOps Assertion Failed: Duplicate chunk ID: {c.id}"
        unique_ids.add(c.id)
        assert len(c.content) > 30, f"DataOps Assertion Failed: Chunk {c.id} content too short"
        assert c.token_estimate > 5, f"DataOps Assertion Failed: Chunk {c.id} has invalid token estimate"

    # Verify key domains exist in chunk tags
    all_tags = set(t for c in chunks for t in c.tags)
    required_tags = {"kubernetes", "terraform", "go", "python"}
    for req in required_tags:
        assert any(req in t for t in all_tags), f"DataOps Assertion Failed: Required topic '{req}' missing from tags"

    print(f"✅ DataOps Quality Gates Passed: {len(chunks)} verified semantic chunks generated.")

    # 5. Save Silver Chunks
    serialized = [c.model_dump() for c in chunks]
    silver_output = SILVER_DIR / "chunks.json"
    with open(silver_output, "w", encoding="utf-8") as f:
        json.dump(serialized, f, indent=2)

    silver_manifest = {
        "stage": "silver",
        "processed_at": datetime.datetime.utcnow().isoformat() + "Z",
        "chunk_count": len(chunks),
        "total_estimated_tokens": sum(c.token_estimate for c in chunks),
        "categories": list(set(c.category for c in chunks)),
        "artifacts": {
            "chunks_file": str(silver_output)
        }
    }
    with open(SILVER_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(silver_manifest, f, indent=2)

    return chunks


if __name__ == "__main__":
    run_silver_transform()
