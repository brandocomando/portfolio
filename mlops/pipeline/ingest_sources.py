"""Bronze Layer Ingestion: Ingests heterogeneous data sources into immutable raw storage.

Sources:
1. Local YAML raw profile documents (Bio, Experience, Projects, Skills)
2. Live GitHub API metadata for brandocomando (repos, stargazers, topics)

Outputs:
Saved to mlops/data/bronze/ with cryptographic hashes and ingestion metadata.
"""

import os
import json
import hashlib
import datetime
import yaml
import requests
from pathlib import Path


BRONZE_DIR = Path(__file__).resolve().parent.parent / "data" / "bronze"
RAW_PROFILE_DIR = Path(__file__).resolve().parent.parent / "raw_profile"
GITHUB_USER = "brandocomando"


def compute_sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def ingest_yaml_file(file_path: Path) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()
    parsed = yaml.safe_load(raw_text)
    return {
        "source_type": "local_yaml",
        "file_name": file_path.name,
        "raw_hash": compute_sha256(raw_text),
        "ingested_at": datetime.datetime.utcnow().isoformat() + "Z",
        "payload": parsed
    }


def ingest_github_repos(username: str) -> dict:
    url = f"https://api.github.com/users/{username}/repos?per_page=100"
    headers = {"User-Agent": "portfolio-mlops-ingest/1.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            repos_data = resp.json()
            cleaned_repos = []
            for r in repos_data:
                cleaned_repos.append({
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "full_name": r.get("full_name"),
                    "html_url": r.get("html_url"),
                    "description": r.get("description"),
                    "language": r.get("language"),
                    "stars": r.get("stargazers_count", 0),
                    "forks": r.get("forks_count", 0),
                    "topics": r.get("topics", []),
                    "updated_at": r.get("updated_at")
                })
            return {
                "source_type": "github_rest_api",
                "status": "success",
                "username": username,
                "ingested_at": datetime.datetime.utcnow().isoformat() + "Z",
                "count": len(cleaned_repos),
                "payload": cleaned_repos
            }
        else:
            return {
                "source_type": "github_rest_api",
                "status": "rate_limited_or_error",
                "status_code": resp.status_code,
                "ingested_at": datetime.datetime.utcnow().isoformat() + "Z",
                "payload": []
            }
    except Exception as e:
        return {
            "source_type": "github_rest_api",
            "status": "network_exception",
            "error": str(e),
            "ingested_at": datetime.datetime.utcnow().isoformat() + "Z",
            "payload": []
        }


def run_bronze_ingestion():
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "stage": "bronze",
        "ingested_at": datetime.datetime.utcnow().isoformat() + "Z",
        "artifacts": {}
    }

    # Ingest local YAML sources
    for yaml_file in RAW_PROFILE_DIR.glob("*.yaml"):
        bronze_data = ingest_yaml_file(yaml_file)
        dest_file = BRONZE_DIR / f"{yaml_file.stem}_raw.json"
        with open(dest_file, "w", encoding="utf-8") as f:
            json.dump(bronze_data, f, indent=2)
        manifest["artifacts"][yaml_file.stem] = {
            "file": str(dest_file),
            "hash": bronze_data["raw_hash"]
        }
        print(f"✅ Ingested Bronze: {yaml_file.name} -> {dest_file.name}")

    # Ingest GitHub API data
    gh_data = ingest_github_repos(GITHUB_USER)
    gh_dest = BRONZE_DIR / "github_repos_raw.json"
    with open(gh_dest, "w", encoding="utf-8") as f:
        json.dump(gh_data, f, indent=2)
    manifest["artifacts"]["github_repos"] = {
        "file": str(gh_dest),
        "status": gh_data["status"],
        "count": len(gh_data.get("payload", []))
    }
    print(f"✅ Ingested Bronze: GitHub API ({GITHUB_USER}) -> {gh_dest.name} ({manifest['artifacts']['github_repos']['count']} repos)")

    # Save Bronze manifest
    with open(BRONZE_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


if __name__ == "__main__":
    run_bronze_ingestion()
