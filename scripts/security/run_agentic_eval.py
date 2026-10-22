#!/usr/bin/env python3
"""
Agentic STRIDE Threat Modeling & Verification Test Generator.
Combines Git diff and Terraform infrastructure context into a structured LLM assessment.
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
    category: str = Field(description="STRIDE category: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, or Elevation of Privilege")
    description: str = Field(description="Concrete architectural threat identified in this change")
    raw_severity: str = Field(description="Severity before context (Critical, High, Medium, Low)")
    contextual_severity: str = Field(description="Adjusted severity incorporating Terraform exposure")
    context_rationale: str = Field(description="Why the severity was adjusted based on cloud reachability, IAM boundaries, or tags")
    suggested_fix: str = Field(description="Actionable remediation code snippet or guidance")

class SecurityReport(BaseModel):
    summary: str = Field(description="Executive summary of the change and security posture")
    overall_contextual_severity: str = Field(description="Highest contextual severity remaining")
    threats: list[ThreatItem]
    generated_verification_tests: str = Field(description="Complete, executable pytest verification stub testing boundaries/auth controls")

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
    parser.add_argument("--output-report", default="/tmp/security_report.json")
    parser.add_argument("--base-ref", default="origin/main")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)

    with open(args.context_file, "r", encoding="utf-8") as fh:
        infra_context = json.load(fh)

    git_diff = get_git_diff(args.base_ref)
    if not git_diff.strip():
        print("Empty git diff. Exiting.")
        sys.exit(0)

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an expert Application Security & DevSecOps Engineer.
Analyze the following pull request code diff and its corresponding verified Terraform cloud infrastructure context.

INFRASTRUCTURE TOPOLOGY & RUNTIME CONTEXT:
{json.dumps(infra_context, indent=2)}

CODE DIFF:
```diff
{git_diff[:12000]}
```

EVALUATION RULES:
1. Threat Model: Analyze code changes across STRIDE categories.
2. Context Awareness:
   - If an issue is flagged in code but the infrastructure context proves the component is isolated on an internal network (is_public_facing = false) with no 0.0.0.0/0 ingress, downgrade severity (e.g., Critical to Medium/Low).
   - If an IAM wildcard exists, escalate any S3/data operations as a potential Elevation of Privilege threat.
3. Model-Based Test Generation:
   - Generate runnable pytest code in generated_verification_tests testing boundary rejection (asserting HTTP 401/403 or rejecting unvalidated inputs).
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SecurityReport,
            temperature=0.1
        )
    )

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
