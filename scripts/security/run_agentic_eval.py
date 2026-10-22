#!/usr/bin/env python3
"""
PR Diff-Scoped STRIDE Threat Modeling & Security Verification Test Generator.
Evaluates ONLY the code and infrastructure lines modified in the pull request diff,
using the repository's extracted Terraform and middleware topology strictly as
background context to calibrate severity (downgrading or escalating findings
introduced in the diff).
"""
import argparse
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
        description="Trust boundary crossed by the modified code in this PR"
    )
    affected_component: str = Field(
        description="Specific file, function, route, or resource modified in this PR diff"
    )
    description: str = Field(
        description="Concrete security threat introduced or modified by the changes in this PR diff"
    )
    raw_severity: str = Field(
        description="Severity before infrastructure context adjustment (Critical, High, Medium, Low)"
    )
    contextual_severity: str = Field(
        description="Adjusted severity after evaluating runtime/infrastructure context (Critical, High, Medium, Low)"
    )
    context_rationale: str = Field(
        description="Why the severity of this diff finding was adjusted based on runtime environment, execution context, or surrounding security controls"
    )
    suggested_fix: str = Field(
        description="Actionable remediation snippet for the modified file in this PR"
    )


class SecurityReport(BaseModel):
    summary: str = Field(
        description="Executive summary of the security impact of the changes introduced in this pull request"
    )
    context_summary_narrative: str = Field(
        description="2-3 sentence summary explaining the runtime context of the modified files in this PR and how surrounding infrastructure/middleware controls affect their risk"
    )
    data_flow_diagram_ascii: str = Field(
        description="Compact ASCII Data Flow Diagram (DFD) illustrating the data flow of the components modified in this PR"
    )
    overall_contextual_severity: str = Field(
        description="Highest contextual severity remaining across threats introduced in this PR (Critical, High, Medium, Low, or Informational)"
    )
    threats: list[ThreatItem]
    generated_verification_tests: str = Field(
        description="Runnable pytest verification test stubs specifically testing the code/functions/routes added or modified in this PR"
    )
    generated_adversarial_curl_probes: str = Field(
        description="Optional curl or CLI adversarial test probes if the PR modifies API routes or CLI scripts (leave empty string if not applicable)"
    )


def get_git_diff(base_ref: str = "origin/main") -> str:
    try:
        cmd = ["git", "diff", f"{base_ref}...HEAD"]
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        cmd = ["git", "diff", "HEAD~1"]
        return subprocess.check_output(cmd, text=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context-file", required=True)
    parser.add_argument("--materiality-file", default="/tmp/materiality_gate.json")
    parser.add_argument("--output-report", default="/tmp/security_report.json")
    parser.add_argument("--base-ref", default="origin/main")
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

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are a Staff Application Security & DevSecOps Engineer reviewing a Pull Request.

CRITICAL SCOPE RULE — DIFF-ONLY REVIEW:
- You MUST ONLY report threats, vulnerabilities, or risks that are directly introduced or modified inside the `PULL REQUEST GIT DIFF` below.
- Every `ThreatItem.affected_component` MUST be one of the files modified in this PR (`MODIFIED FILES IN THIS PR`).
- DO NOT report findings, IAM recommendations, or hardening advice for untouched repository files that appear only in `BACKGROUND INFRASTRUCTURE & APPLICATION CONTEXT`.
- The `BACKGROUND INFRASTRUCTURE & APPLICATION CONTEXT` is provided strictly so you understand the environment (e.g., whether a modified route is exposed via public ingress, protected by `ClientVerificationMiddleware`, or running as a scoped service account, or whether a modified CI script runs in an isolated GitHub Actions runner) and can accurately adjust `raw_severity` -> `contextual_severity`.
- If the PR only modifies CI/CD scripts, tests, or safe code with low risk, reflect that honestly (`Low` or `Informational` overall severity) and focus any threats strictly on the new/changed code itself (e.g., subprocess command handling, token handling, API response parsing, or file I/O in the modified files).

MODIFIED FILES IN THIS PR:
{json.dumps(materiality_context, indent=2)}

BACKGROUND INFRASTRUCTURE & APPLICATION CONTEXT (DO NOT AUDIT UNTOUCHED RESOURCES):
{json.dumps(infra_context, indent=2)}

PULL REQUEST GIT DIFF (AUDIT ONLY THIS DIFF):
```diff
{git_diff[:18000]}
```

EVALUATION RULES:
1. **Context Summary (`context_summary_narrative`)**:
   Write a concise 2-3 sentence summary of the execution context for the files modified in this PR and how surrounding controls (e.g. GitHub Actions runner permissions, Secret Manager / GitHub Secrets injection, or Cloud Run/FastAPI middleware if backend routes were touched) adjust the severity of the diff.
2. **ASCII Data Flow Diagram (`data_flow_diagram_ascii`)**:
   Produce a compact ASCII diagram showing the data flow of the components modified in this PR.
3. **STRIDE Threat Model (`threats`)**:
   - Identify STRIDE threats strictly within the modified files in the diff.
   - Show how runtime context adjusts `raw_severity` to `contextual_severity` in `context_rationale`.
   - Provide actionable remediation code snippets for the modified files in `suggested_fix`.
4. **Generated Model-Based Test Suite (`generated_verification_tests` & `generated_adversarial_curl_probes`)**:
   - Generate runnable `pytest` verification tests targeting the functions, routes, or modules modified in this PR.
   - If the PR modifies HTTP endpoints, include targeted `curl` boundary probes in `generated_adversarial_curl_probes` (or CLI invocation probes if the PR modifies CLI scripts).
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
