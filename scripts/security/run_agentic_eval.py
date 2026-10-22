#!/usr/bin/env python3
"""
PR Diff-Scoped Agentic STRIDE Threat Modeling & Verification Test Generator.
Evaluates the security impact of the Pull Request diff by cross-referencing
the modified files against the rest of the repository:
  - If Terraform/IAM is modified in the PR -> Cross-references application code
    (`code_cloud_sdk_usage` & relevant source files) to verify whether the granted
    IAM permissions, network exposure, or resources are actually required by the code
    (least-privilege validation).
  - If Application Code is modified in the PR -> Cross-references Terraform
    (`public_ingress_points`, `iam_bindings`, `security_middlewares`) to determine
    whether the modified code is publicly reachable and what IAM blast radius it runs with.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
from pydantic import BaseModel, Field
from google import genai
from google.genai import types


class ThreatItem(BaseModel):
    category: str = Field(
        description="STRIDE category: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, or Elevation of Privilege"
    )
    trust_boundary: str = Field(
        description="Trust boundary crossed or impacted by the change in this PR"
    )
    affected_component: str = Field(
        description="Specific file, resource, or route modified in this PR diff"
    )
    description: str = Field(
        description="Concrete architectural or code-level threat introduced or modified by this PR diff"
    )
    raw_severity: str = Field(
        description="Severity before cross-referencing repository context (Critical, High, Medium, Low)"
    )
    contextual_severity: str = Field(
        description="Adjusted severity after cross-referencing how the rest of the repo's code and infrastructure interact with this change (Critical, High, Medium, Low)"
    )
    context_rationale: str = Field(
        description="How cross-referencing the repo's application code (SDK usage, middlewares) and Terraform topology (ingress, IAM bindings) justified downgrading, escalating, or flagging this change"
    )
    suggested_fix: str = Field(
        description="Actionable remediation snippet for the modified file in this PR"
    )


class SecurityReport(BaseModel):
    summary: str = Field(
        description="Executive summary of the security impact of the changes introduced in this pull request"
    )
    context_summary_narrative: str = Field(
        description="2-3 sentence summary explaining how the PR changes interact with existing repository code and infrastructure (e.g., whether an IAM/infra change matches actual SDK usage in code, or how existing ingress/IAM context affects modified application code)"
    )
    data_flow_diagram_ascii: str = Field(
        description="Compact ASCII Data Flow Diagram (DFD) illustrating the data flow and trust boundaries of the components modified in this PR"
    )
    overall_contextual_severity: str = Field(
        description="Highest contextual severity remaining across threats introduced in this PR (Critical, High, Medium, Low, or Informational)"
    )
    threats: list[ThreatItem]
    generated_verification_tests: str = Field(
        description="Runnable pytest verification test stubs specifically testing the code, routes, or infrastructure invariants modified in this PR"
    )
    generated_adversarial_curl_probes: str = Field(
        description="Optional curl or CLI adversarial test probes targeting the modified routes or scripts (leave empty string if not applicable)"
    )


def get_git_diff(base_ref: str = "origin/main") -> str:
    try:
        cmd = ["git", "diff", f"{base_ref}...HEAD"]
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        cmd = ["git", "diff", "HEAD~1"]
        return subprocess.check_output(cmd, text=True)


def gather_cross_reference_files(repo_root: str, materiality: dict) -> str:
    """
    Dynamically pulls relevant untouched repository files so the LLM can answer
    cross-cutting questions about the diff:
      - If `.tf` / IAM files are changed in the PR, pulls backend service code that
        interacts with cloud resources to check if the IAM permission is actually needed.
      - If backend/application files are changed in the PR, pulls the full content of
        the modified files plus core auth/middleware and Cloud Run IAM `.tf` files.
    """
    cats = materiality.get("categories", {})
    infra_changed = bool(cats.get("infrastructure"))
    code_changed = bool(cats.get("security_and_auth") or cats.get("application_logic"))

    target_globs = []
    if infra_changed:
        # Pull backend services & core config so the model can see what SDK calls the app actually makes
        target_globs.extend([
            "backend/app/services/*.py",
            "backend/app/core/config.py",
            "backend/app/core/security.py",
        ])
    if code_changed:
        # Pull Cloud Run / IAM / Auth Terraform definitions so the model sees runtime identity & ingress
        target_globs.extend([
            "infra/modules/cloud_run/main.tf",
            "infra/modules/secrets/main.tf",
            "backend/app/core/client_auth.py",
            "backend/app/core/security.py",
        ])

    snippets = []
    seen = set()
    for pattern in target_globs:
        for path in sorted(glob.glob(os.path.join(repo_root, pattern))):
            rel_path = os.path.relpath(path, repo_root)
            if rel_path in seen:
                continue
            seen.add(rel_path)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    content = fh.read()
                snippets.append(f"--- CROSS-REFERENCED REPO FILE: {rel_path} ---\n{content[:3000]}\n")
            except Exception:
                continue

    return "\n".join(snippets)[:15000]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context-file", required=True)
    parser.add_argument("--materiality-file", default="/tmp/materiality_gate.json")
    parser.add_argument("--output-report", default="/tmp/security_report.json")
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)

    with open(args.context_file, "r", encoding="utf-8") as fh:
        infra_context = json.load(fh)

    materiality_context = {}
    if args.materiality_file and os.path.exists(args.materiality_file):
        try:
            with open(args.materiality_file, "r", encoding="utf-8") as fh:
                materiality_context = json.load(fh)
        except Exception:
            pass

    git_diff = get_git_diff(args.base_ref)
    if not git_diff.strip():
        print("Empty git diff. Exiting.")
        sys.exit(0)

    cross_ref_code = gather_cross_reference_files(args.repo_root, materiality_context)

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are a Staff Application Security & DevSecOps Engineer reviewing a Pull Request.

================================================================================
HOW TO USE REPOSITORY CONTEXT TO EVALUATE THIS PR DIFF (BI-DIRECTIONAL ANALYSIS)
================================================================================
1. **Focus Findings on the PR Diff**:
   Every reported threat (`ThreatItem.affected_component`) must be anchored to a file, resource, or route modified in `PULL REQUEST GIT DIFF` (`MODIFIED FILES IN THIS PR`). Do not file unrelated backlog findings on untouched files.

2. **Use Full Repo Context to Validate the Change**:
   - **If this PR modifies Terraform / IAM / Infrastructure (`.tf`, workflows, Dockerfiles)**:
     Inspect `code_cloud_sdk_usage`, `code_env_and_secret_reads`, and `CROSS-REFERENCED REPOSITORY FILES` to verify whether the infrastructure or IAM change is actually needed by the application code!
     * *Example*: If a `.tf` change grants a service account `roles/datastore.owner`, `roles/storage.admin`, or `s3:*`, check `code_cloud_sdk_usage` to see what SDK methods `backend/` actually calls. If the code only performs Firestore reads/writes (`roles/datastore.user`) or doesn't use GCS/S3 at all, flag the new IAM change as an **Elevation of Privilege** violation of Least Privilege!
   - **If this PR modifies Application Code (`.py`, routes, middleware, dependencies)**:
     Inspect `public_ingress_points`, `iam_bindings`, `security_middlewares`, and `CROSS-REFERENCED REPOSITORY FILES` to evaluate the blast radius of the code change!
     * *Example*: If a new route or function has a flaw, check whether it is publicly reachable (`is_public_facing = true`), gated by `ClientVerificationMiddleware`, or running under a scoped vs. overprivileged service account, and adjust `raw_severity` -> `contextual_severity` accordingly.

================================================================================
MODIFIED FILES IN THIS PR
================================================================================
{json.dumps(materiality_context, indent=2)}

================================================================================
EXTRACTED REPOSITORY TOPOLOGY & CODE SDK USAGE MAP
================================================================================
{json.dumps(infra_context, indent=2)}

================================================================================
CROSS-REFERENCED REPOSITORY FILES (FOR LEAST-PRIVILEGE & BLAST-RADIUS VERIFICATION)
================================================================================
{cross_ref_code if cross_ref_code else "No additional cross-reference files needed."}

================================================================================
PULL REQUEST GIT DIFF (PRIMARY REVIEW TARGET)
================================================================================
```diff
{git_diff[:18000]}
```

================================================================================
OUTPUT REQUIREMENTS
================================================================================
1. **Context Summary (`context_summary_narrative`)**:
   Write a concise 2-3 sentence summary explaining how the PR's changes interact with the rest of the repository (e.g., whether modified permissions match actual code SDK usage, or how surrounding infrastructure/middleware controls affect the modified code's severity).
2. **ASCII Data Flow Diagram (`data_flow_diagram_ascii`)**:
   Produce a compact ASCII diagram showing the data flow and trust boundaries of the components modified in this PR.
3. **STRIDE Threat Model (`threats`)**:
   - Identify concrete STRIDE threats introduced or impacted by the PR diff.
   - Show how cross-referencing the repo's code and infrastructure calibrated `raw_severity` -> `contextual_severity` in `context_rationale`.
   - Provide actionable code or Terraform HCL remediation snippets in `suggested_fix`.
4. **Generated Model-Based Test Suite (`generated_verification_tests` & `generated_adversarial_curl_probes`)**:
   - Generate runnable `pytest` verification tests specifically exercising the code, routes, or security invariants modified in this PR.
   - Provide targeted `curl` or CLI adversarial probes if applicable.
"""

    model_name = os.getenv("GEMINI_SECURITY_MODEL", "gemini-3.5-flash")
    fallback_models = [model_name, "gemini-2.5-flash", "gemini-2.0-flash"]
    response = None
    last_err = None

    for candidate_model in dict.fromkeys(fallback_models):
        try:
            response = client.models.generate_content(
                model=candidate_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=SecurityReport,
                    temperature=0.1,
                ),
            )
            print(f"Successfully evaluated PR diff using model: {candidate_model}")
            break
        except Exception as err:
            print(f"Warning: Model '{candidate_model}' failed ({err}), trying next fallback...")
            last_err = err

    if response is None:
        print(f"Error: All Gemini model candidates failed. Last error: {last_err}", file=sys.stderr)
        sys.exit(1)

    report_data = response.text
    with open(args.output_report, "w", encoding="utf-8") as fh:
        fh.write(report_data)

    parsed = json.loads(report_data)
    test_code = parsed.get("generated_verification_tests", "")
    if test_code:
        os.makedirs("tests/security", exist_ok=True)
        with open("tests/security/test_generated_verification.py", "w", encoding="utf-8") as fh:
            fh.write(test_code)

    print(f"Report generated successfully at {args.output_report}")


if __name__ == "__main__":
    main()
