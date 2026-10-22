#!/usr/bin/env python3
"""
Pillar 3 & Pillar 4: Automated STRIDE Threat Modeling & Model-Based Security Test Generator.
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
        description="2-3 sentence Block 1 Context Summary narrative explicitly citing workload reachability (public vs private ingress), IAM blast radius (scoped vs broad roles), and how findings were contextually adjusted"
    )
    data_flow_diagram_ascii: str = Field(
        description="Compact ASCII Data Flow Diagram (DFD) illustrating the PR's data flow across trust boundaries (e.g. [Untrusted Client] --HTTPS--> [Cloud Run + ClientVerificationMiddleware] --IAM SA--> [Firestore / Secret Manager])"
    )
    overall_contextual_severity: str = Field(
        description="Highest contextual severity remaining across all identified threats (Critical, High, Medium, Low, or Informational)"
    )
    threats: list[ThreatItem]
    generated_verification_tests: str = Field(
        description="Complete, runnable pytest security verification suite testing authentication boundary rejection (401/403), BOLA/IDOR, header spoofing, or malformed payload rejection against the repo's routes/logic"
    )
    generated_adversarial_curl_probes: str = Field(
        description="Executable curl / shell adversarial test probes targeting the modified endpoints or boundaries (e.g., missing X-Portfolio-Client header, forged Bearer JWT, oversized/malformed JSON payload)"
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
You are a Staff Principal DevSecOps & Cloud Security Architect performing an automated, context-aware PR inspection across a 4-Pillar Agentic DevSecOps Pipeline:
1. Material-Change Detection Gate
2. Context-Aware Infrastructure & Application Topology Aggregator
3. Automated STRIDE Threat Modeling across Trust Boundaries & Data Flow Diagrams (DFD)
4. Model-Based Adversarial Security Verification Test Generation

Analyze the following Pull Request diff together with the extracted in-repo Terraform cloud topology and FastAPI route surface.

================================================================================
PILLAR 1: MATERIAL-CHANGE DETECTION SUMMARY
================================================================================
{json.dumps(materiality_context, indent=2)}

================================================================================
PILLAR 2: VERIFIED TERRAFORM INFRASTRUCTURE & APPLICATION TOPOLOGY
================================================================================
{json.dumps(infra_context, indent=2)}

================================================================================
PULL REQUEST GIT DIFF
================================================================================
```diff
{git_diff[:16000]}
```

================================================================================
MANDATORY EVALUATION & OUTPUT RULES
================================================================================
1. **Context Summary Narrative (`context_summary_narrative`)**:
   Write a sharp, concrete architectural summary showing how the in-repo Terraform definitions informed your risk scoring. Explicitly reference the actual resources found in the topology (e.g., `google_cloud_run_v2_service.backend` with `INGRESS_TRAFFIC_ALL`, `ClientVerificationMiddleware`, `sa-portfolio-backend` scoped to `roles/datastore.user` and `roles/secretmanager.secretAccessor`, vs CI/CD WIF service account roles or internal-only components) and state which findings were downgraded or escalated due to reachability and IAM blast radius.

2. **ASCII Data Flow Diagram (`data_flow_diagram_ascii`)**:
   Produce a clear, compact ASCII diagram showing the request path, trust boundaries, middleware gates, runtime service account identity, and backing datastores/secrets.

3. **STRIDE Threat Modeling (`threats`)**:
   - Identify concrete architectural or code-level threats across STRIDE categories (`Spoofing`, `Tampering`, `Repudiation`, `Information Disclosure`, `Denial of Service`, `Elevation of Privilege`).
   - Always populate `trust_boundary` and `affected_component` with real names from the repo/diff.
   - **Context Adjustment Requirement**:
     * Demonstrate at least one **Context-Aware Downgrade** where a theoretical/raw finding is downgraded (e.g., `High` -> `Low` or `Critical` -> `Medium`) because Terraform or middleware context proves constrained blast radius, secret injection via Secret Manager (`secret_key_ref`), OIDC repository attribute condition (`assertion.repository == ...`), or non-routable internal execution.
     * Demonstrate **Context-Aware Escalation / Preservation** where public ingress (`INGRESS_TRAFFIC_ALL` / `allUsers`) or broad IAM roles (`roles/editor`, `roles/secretmanager.admin`, wildcard `*`, or `DELETE_PROTECTION_DISABLED` on Firestore) warrant heightened scrutiny.
   - Provide copy-pasteable Python or Terraform HCL remediation patches in `suggested_fix`.

4. **Model-Based Security Verification Suite (`generated_verification_tests` & `generated_adversarial_curl_probes`)**:
   - In `generated_verification_tests`, write realistic, self-contained `pytest` security tests (using `fastapi.testclient.TestClient` or unit harness) that dynamically verify boundary enforcement (e.g., rejecting requests missing `X-Portfolio-Client` verification header with HTTP 403, testing spoofed `X-Forwarded-For` / `Authorization: Bearer <malformed_jwt>` handling, or boundary validation).
   - In `generated_adversarial_curl_probes`, provide 2-3 realistic `curl` adversarial command snippets targeting the API routes to verify unauthenticated boundary rejection, header tampering, or rate-limit/payload abuse.
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
