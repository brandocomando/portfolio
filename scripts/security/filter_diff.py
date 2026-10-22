#!/usr/bin/env python3
"""
Pillar 1: Material-Change Detection Gate.
Deterministically inspects Git diff paths and categorizes PR modifications across
Infrastructure (.tf), IAM/Security Policies, API Routes/Middleware, Dependencies,
and Non-Material assets (docs/CSS) to gate downstream LLM Threat Modeling.
"""
import argparse
import json
import os
import subprocess

NON_MATERIAL_EXTENSIONS = {
    ".md", ".txt", ".png", ".jpg", ".jpeg", ".svg", ".gif",
    ".css", ".scss", ".sass", ".less", ".ico", ".woff", ".woff2"
}

NON_MATERIAL_PREFIXES = (
    "docs/",
    ".github/ISSUE_TEMPLATE/",
    ".vscode/",
    ".idea/"
)

INFRA_PATTERNS = (
    ".tf",
    ".tfvars",
    "Dockerfile",
    "docker-compose"
)

DEPENDENCY_PATTERNS = (
    "requirements.txt",
    "package.json",
    "package-lock.json",
    "go.mod",
    "Pipfile",
    "Cargo.toml",
    "pyproject.toml"
)

SECURITY_PATH_KEYWORDS = (
    "auth",
    "security",
    "routes",
    "api",
    "controller",
    "middleware",
    "policy",
    "iam",
    "rate_limit",
    "secret",
    "jwt",
    "cors"
)

CODE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".rb", ".yaml", ".yml", ".sh"
}


def get_changed_files(base_ref: str = "origin/main") -> list[str]:
    try:
        cmd = ["git", "diff", "--name-only", f"{base_ref}...HEAD"]
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        return [line.strip() for line in output.splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        cmd = ["git", "diff", "--name-only", "HEAD~1"]
        output = subprocess.check_output(cmd, text=True)
        return [line.strip() for line in output.splitlines() if line.strip()]


def categorize_files(files: list[str]) -> dict:
    """Categorizes modified files into security-relevant buckets for the PR scorecard."""
    categories = {
        "infrastructure": [],
        "security_and_auth": [],
        "dependencies": [],
        "application_logic": [],
        "non_material_bypassed": [],
    }
    material_reasons = []

    for f in files:
        if any(f.startswith(prefix) for prefix in NON_MATERIAL_PREFIXES):
            categories["non_material_bypassed"].append(f)
            continue
        _, ext = os.path.splitext(f)
        if ext.lower() in NON_MATERIAL_EXTENSIONS:
            categories["non_material_bypassed"].append(f)
            continue

        if any(pattern in f for pattern in INFRA_PATTERNS):
            categories["infrastructure"].append(f)
            material_reasons.append(f"Infrastructure definition modified: {f}")
            continue

        if any(pattern in f for pattern in DEPENDENCY_PATTERNS):
            categories["dependencies"].append(f)
            material_reasons.append(f"Dependency manifest modified: {f}")
            continue

        if any(keyword in f.lower() for keyword in SECURITY_PATH_KEYWORDS):
            categories["security_and_auth"].append(f)
            material_reasons.append(f"Security-sensitive application path modified: {f}")
            continue

        if ext.lower() in CODE_EXTENSIONS:
            categories["application_logic"].append(f)
            material_reasons.append(f"Application logic modified: {f}")
        else:
            categories["non_material_bypassed"].append(f)

    is_material = len(material_reasons) > 0
    summary = (
        "; ".join(material_reasons)
        if is_material
        else "Only non-material files (docs/styling) modified."
    )

    return {
        "is_material": is_material,
        "summary": summary,
        "total_files_changed": len(files),
        "categories": categories,
        "reasons": material_reasons,
    }


def evaluate_materiality(files: list[str]) -> tuple[bool, str]:
    if not files:
        return False, "No files modified in pull request."
    result = categorize_files(files)
    return result["is_material"], result["summary"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--output-github-env", action="store_true")
    parser.add_argument("--output-json", default="/tmp/materiality_gate.json")
    args = parser.parse_args()

    files = get_changed_files(args.base_ref)
    gate_report = categorize_files(files) if files else {
        "is_material": False,
        "summary": "No files modified in pull request.",
        "total_files_changed": 0,
        "categories": {
            "infrastructure": [],
            "security_and_auth": [],
            "dependencies": [],
            "application_logic": [],
            "non_material_bypassed": [],
        },
        "reasons": [],
    }

    is_material = gate_report["is_material"]
    summary = gate_report["summary"]

    print(f"Material Change Result: {is_material}")
    print(f"Rationale: {summary}")

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as fh:
            json.dump(gate_report, fh, indent=2)

    if args.output_github_env:
        github_output = os.getenv("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a", encoding="utf-8") as fh:
                fh.write(f"IS_MATERIAL={'true' if is_material else 'false'}\n")
                fh.write(f"MATERIAL_SUMMARY={summary}\n")


if __name__ == "__main__":
    main()
