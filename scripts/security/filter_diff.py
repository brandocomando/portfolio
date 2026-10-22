#!/usr/bin/env python3
"""
Material-Change Detection Filter.
Inspects Git diff paths to determine if security-sensitive evaluation is needed.
"""
import argparse
import os
import subprocess
import sys

NON_MATERIAL_EXTENSIONS = {
    ".md", ".txt", ".png", ".jpg", ".jpeg", ".svg", ".gif",
    ".css", ".scss", ".sass", ".less"
}

NON_MATERIAL_PREFIXES = (
    "docs/",
    ".github/ISSUE_TEMPLATE/",
    ".vscode/",
    ".idea/"
)

MATERIAL_FILE_PATTERNS = (
    ".tf",
    ".tfvars",
    "Dockerfile",
    "docker-compose",
    "requirements.txt",
    "package.json",
    "go.mod",
    "Pipfile",
    "Cargo.toml"
)

MATERIAL_PATH_KEYWORDS = (
    "auth",
    "security",
    "routes",
    "api",
    "controller",
    "middleware",
    "policy",
    "iam"
)

def get_changed_files(base_ref: str = "origin/main") -> list[str]:
    try:
        cmd = ["git", "diff", "--name-only", f"{base_ref}...HEAD"]
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        return [line.strip() for line in output.splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        # Fallback to single commit diff or all uncommitted
        cmd = ["git", "diff", "--name-only", "HEAD~1"]
        output = subprocess.check_output(cmd, text=True)
        return [line.strip() for line in output.splitlines() if line.strip()]

def evaluate_materiality(files: list[str]) -> tuple[bool, str]:
    if not files:
        return False, "No files modified in pull request."

    material_reasons = []

    for f in files:
        # Check non-material overrides
        if any(f.startswith(prefix) for prefix in NON_MATERIAL_PREFIXES):
            continue
        _, ext = os.path.splitext(f)
        if ext.lower() in NON_MATERIAL_EXTENSIONS:
            continue

        # Check explicit material extensions/files
        if any(pattern in f for pattern in MATERIAL_FILE_PATTERNS):
            material_reasons.append(f"Infrastructure or dependency file modified: {f}")
            continue

        # Check path keywords
        if any(keyword in f.lower() for keyword in MATERIAL_PATH_KEYWORDS):
            material_reasons.append(f"Security-sensitive application path modified: {f}")
            continue

        # Default: executable application code (.py, .ts, .js, .go) is material
        if ext.lower() in {".py", ".ts", ".js", ".go", ".rs", ".java", ".rb", ".yaml", ".yml"}:
            material_reasons.append(f"Application logic modified: {f}")

    is_material = len(material_reasons) > 0
    summary = "; ".join(material_reasons) if is_material else "Only non-material files (docs/styling) modified."
    return is_material, summary

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--output-github-env", action="store_true")
    args = parser.parse_args()

    files = get_changed_files(args.base_ref)
    is_material, summary = evaluate_materiality(files)

    print(f"Material Change Result: {is_material}")
    print(f"Rationale: {summary}")

    if args.output_github_env:
        github_output = os.getenv("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a", encoding="utf-8") as fh:
                fh.write(f"IS_MATERIAL={'true' if is_material else 'false'}\n")
                fh.write(f"MATERIAL_SUMMARY={summary}\n")

if __name__ == "__main__":
    main()
