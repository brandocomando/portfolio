#!/usr/bin/env python3
"""
Automated STRIDE Threat Modeling & Security Verification Test Generator.
Combines Git diff, Terraform infrastructure topology (reachability, IAM blast radius,
trust boundaries), and application route surface into a structured LLM DevSecOps evaluation.
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
        description="Specific architectural trust boundary crossed (e.g., Internet -> Public Cloud Run Ingress, Cloud Run SA -> Firestore, GitHub OIDC -> GCP IAM)"
    )
    affected_component: str = Field(
        description="Specific file, API route, or Terraform resource (e.g., POST /api/v1/chat/stream, google_project_iam_member.terraform_editor)"
    )
    description: str = Field(
        description="Concrete architectural or code-level threat identified in this change"
    )
    raw_severity: str = Field(
        description="Severity before infrastructure context adjustment (Critical, High, Medium, Low)"
    )
    contextual_severity: str = Field(
        description="Adjusted severity after evaluating Terraform network reachability, IAM blast radius, and auth middleware (Critical, High, Medium, Low)"
    )
    context_rationale: str = Field(
        description="Explicit explanation of why severity was downgraded, escalated, or maintained based on in-repo Terraform topology (ingress, IAM scope, subnet/service isolation)"
    )
    suggested_fix: str = Field(
        description="Actionable code or Terraform HCL remediation snippet"
    )


class SecurityReport(BaseModel):
    summary: str = Field(
        description="Executive summary of the pull request security posture across application code and Terraform infrastructure"
    )
    context_summary_narrative: str = Field(
        description='Concise 2-3 sentence Context Summary (e.g., "Workload exposed via Cloud Run INGRESS_TRAFFIC_ALL; runtime SA scoped to datastore.user and secretAccessor. Downranked secret leakage risk from High to Low due to Secret Manager secret_key_ref injection.")'
    )
    data_flow_diagram_ascii: str = Field(
        description="Compact ASCII Data Flow Diagram (DFD) illustrating the PR's data flow across trust boundaries"
    )
    overall_contextual_severity: str = Field(
        description="Highest contextual severity remaining across all identified threats (Critical, High, Medium, Low, or Informational)"
    )
    threats: list[ThreatItem]
    generated_verification_tests: str = Field(
        description="Complete, runnable pytest security verification suite testing authentication boundary rejection (401/403), BOLA/IDOR, header spoofing, or malformed payload rejection against the repo's routes/logic"
    )
    generated_adversarial_curl_probes: str = Field(
        description="Executable curl adversarial test probes targeting the modified endpoints or boundaries (e.g., missing X-Portfolio-Client header, forged Bearer JWT, oversized/malformed JSON payload)"
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
You are a Staff Application Security & Cloud DevSecOps Engineer reviewing a Pull Request.
Analyze the following Pull Request diff together with the extracted in-repo Terraform cloud topology and FastAPI application route surface.

MODIFIED FILES SUMMARY:
{json.dumps(materiality_context, indent=2)}

TERRAFORM INFRASTRUCTURE & APPLICATION TOPOLOGY:
{json.dumps(infra_context, indent=2)}

PULL REQUEST GIT DIFF:
```diff
{git_diff[:16000]}
```

EVALUATION RULES:
1. **Context Summary (`context_summary_narrative`)**:
   Write a concise 2-3 sentence architectural context summary explaining how the co-located Terraform definitions affect the risk of this PR (e.g., workload reachability, IAM role scoping, Secret Manager injection, OIDC conditions, and which findings were downranked or escalated as a result).

2. **ASCII Data Flow Diagram (`data_flow_diagram_ascii`)**:
   Produce a compact ASCII diagram showing the request path, trust boundaries, middleware gates, runtime service account identity, and backing datastores/secrets.

3. **STRIDE Threat Model (`threats`)**:
   - Analyze changes across STRIDE categories (`Spoofing`, `Tampering`, `Repudiation`, `Information Disclosure`, `Denial of Service`, `Elevation of Privilege`).
   - Populate `trust_boundary` and `affected_component` with actual resource/file/route names from the repository.
   - Adjust severity using the Terraform context:
     * Downgrade severity when infrastructure or middleware controls mitigate raw exposure (e.g., private/non-routable components, scoped runtime IAM roles, Secret Manager `secret_key_ref`, OIDC `assertion.repository` constraint, or `ClientVerificationMiddleware`).
     * Escalate or maintain severity when public ingress (`INGRESS_TRAFFIC_ALL` / `allUsers` / `0.0.0.0/0`) or broad IAM privileges (`roles/editor`, `roles/secretmanager.admin`, wildcard `*`) increase blast radius.
   - Provide actionable Python or Terraform HCL remediation snippets in `suggested_fix`.

4. **Generated Model-Based Test Suite (`generated_verification_tests` & `generated_adversarial_curl_probes`)**:
   - Generate runnable `pytest` verification tests asserting boundary rejection (HTTP 401/403, missing `X-Portfolio-Client` header rejection, malformed JWT rejection, or input validation).
   - Provide targeted `curl` test commands attempting an unauthenticated bypass or boundary breach against the application routes.
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
            print(f"Successfully evaluated PR using model: {candidate_model}")
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
