#!/usr/bin/env python3
"""
Full-Repository Agentic Security Scanner & GitHub Issue Reporter.
Audits the entire repository's Terraform infrastructure (`infra/`), FastAPI application
code (`backend/`), and CI/CD workflows (`.github/workflows/`) to identify actionable
STRIDE architectural or security hardening findings and automatically creates
deduplicated GitHub Issues for Medium/High/Critical findings.
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


class RepoSecurityFinding(BaseModel):
    finding_id: str = Field(
        description="Deterministic, short slug ID for deduplication (e.g., 'SEC-TF-FIRESTORE-DELETE-PROTECTION', 'SEC-IAM-WIF-EDITOR-ROLE')"
    )
    title: str = Field(
        description="Concise, actionable GitHub Issue title (e.g., 'Enable delete_protection on production Firestore database')"
    )
    stride_category: str = Field(
        description="STRIDE category: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, or Elevation of Privilege"
    )
    affected_files: list[str] = Field(
        description="Exact repository file paths affected (e.g., ['infra/modules/firestore/main.tf'])"
    )
    trust_boundary: str = Field(
        description="Architectural trust boundary involved"
    )
    raw_severity: str = Field(
        description="Raw severity before architectural context (Critical, High, Medium, Low)"
    )
    contextual_severity: str = Field(
        description="Context-adjusted severity after accounting for compensating controls in the repo (Critical, High, Medium, Low)"
    )
    description: str = Field(
        description="Detailed explanation of the architectural or code vulnerability/hardening gap"
    )
    context_rationale: str = Field(
        description="How surrounding Terraform/application controls mitigate or amplify this risk"
    )
    remediation_patch: str = Field(
        description="Actionable code or Terraform HCL patch to resolve the finding"
    )
    verification_test: str = Field(
        description="Pytest test case, Terraform validation command, or curl probe to verify the fix"
    )


class FullRepoAuditReport(BaseModel):
    executive_summary: str = Field(
        description="Executive summary of the full repository security posture"
    )
    findings: list[RepoSecurityFinding]


def collect_repo_snapshots(repo_root: str) -> str:
    """Collects key Terraform and backend security files for full-repo analysis."""
    patterns = [
        "infra/**/*.tf",
        "backend/app/main.py",
        "backend/app/core/*.py",
        "backend/app/api/**/*.py",
        ".github/workflows/*.yml",
    ]
    snippets = []
    seen = set()

    for pattern in patterns:
        for path in sorted(glob.glob(os.path.join(repo_root, pattern), recursive=True)):
            rel_path = os.path.relpath(path, repo_root)
            if rel_path in seen or ".worktrees" in rel_path or ".terraform" in rel_path:
                continue
            seen.add(rel_path)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    content = fh.read()
                snippets.append(f"--- FILE: {rel_path} ---\n{content[:4000]}\n")
            except Exception:
                continue

    return "\n".join(snippets)[:45000]


def get_existing_open_issues() -> list[dict]:
    """Fetches open GitHub issues to prevent duplicate issue creation."""
    try:
        output = subprocess.check_output(
            ["gh", "issue", "list", "--state", "open", "--limit", "100", "--json", "number,title,body"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return json.loads(output)
    except Exception as e:
        print(f"Warning: Could not fetch existing GitHub issues: {e}")
        return []


def ensure_security_label():
    """Ensures the 'security' label exists in the repository."""
    try:
        subprocess.run(
            ["gh", "label", "create", "security", "--color", "d73a4a", "--description", "Automated DevSecOps Security Finding", "--force"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except Exception:
        pass


def format_issue_body(finding: dict) -> str:
    files_md = ", ".join(f"`{f}`" for f in finding.get("affected_files", []))
    return f"""<!-- appsec-finding-id: {finding['finding_id']} -->
## 🛡️ Automated DevSecOps Security Finding: `{finding['finding_id']}`

| Attribute | Value |
| :--- | :--- |
| **STRIDE Category** | **{finding['stride_category']}** |
| **Trust Boundary** | `{finding['trust_boundary']}` |
| **Affected Files** | {files_md} |
| **Raw Severity** | `{finding['raw_severity']}` |
| **Contextual Severity** | **`{finding['contextual_severity']}`** |

### 1. Architectural Vulnerability & Risk Description
{finding['description']}

### 2. Context-Aware Severity Rationale
> {finding['context_rationale']}

### 3. Recommended Remediation Patch
```hcl
{finding['remediation_patch']}
```

### 4. Verification Test / Probe
```python
{finding['verification_test']}
```

---
*Generated by the Full-Repository Agentic DevSecOps Audit workflow (`.github/workflows/appsec-full-scan.yml`).*
"""


def create_github_issues(
    report: dict,
    min_severity: str = "Medium",
    max_issues: int = 5,
    dry_run: bool = False,
) -> list[str]:
    severity_rank = {"Informational": 0, "Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    threshold = severity_rank.get(min_severity, 2)

    existing_issues = get_existing_open_issues()
    ensure_security_label()

    created_urls = []
    for finding in report.get("findings", []):
        sev = finding.get("contextual_severity", "Low")
        if severity_rank.get(sev, 0) < threshold:
            print(f"Skipping finding {finding.get('finding_id')} (Contextual Severity: {sev} < {min_severity})")
            continue

        fid = finding.get("finding_id", "")
        title = f"[Security][{sev}] {finding.get('title', fid)}"

        # Check deduplication by finding_id marker or title
        already_exists = any(
            (fid and fid in (iss.get("body") or ""))
            or finding.get("title", "").lower() in (iss.get("title") or "").lower()
            for iss in existing_issues
        )
        if already_exists:
            print(f"Skipping duplicate open issue for finding: {fid} ({title})")
            continue

        body = format_issue_body(finding)
        if dry_run:
            print(f"[DRY RUN] Would create issue: {title}")
            continue

        try:
            out = subprocess.check_output(
                ["gh", "issue", "create", "--title", title, "--body", body, "--label", "security"],
                text=True,
            ).strip()
            print(f"Created GitHub Issue: {out}")
            created_urls.append(out)
            if len(created_urls) >= max_issues:
                break
        except Exception as e:
            print(f"Warning: Failed creating GitHub issue for {fid}: {e}")

    return created_urls


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--context-file", required=True)
    parser.add_argument("--output-report", default="/tmp/full_security_audit.json")
    parser.add_argument("--min-severity", default="Medium", choices=["Low", "Medium", "High", "Critical"])
    parser.add_argument("--max-issues", type=int, default=5)
    parser.add_argument("--create-issues", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)

    with open(args.context_file, "r", encoding="utf-8") as fh:
        infra_context = json.load(fh)

    code_snapshots = collect_repo_snapshots(args.repo_root)
    client = genai.Client(api_key=api_key)

    prompt = f"""
You are a Principal Cloud Security & DevSecOps Architect performing a Full-Repository Security & Threat Modeling Audit across both Terraform Infrastructure (`infra/`) and Application Code (`backend/`, `.github/workflows/`).

EXTRACTED TERRAFORM & APPLICATION TOPOLOGY:
{json.dumps(infra_context, indent=2)}

REPOSITORY SOURCE & INFRASTRUCTURE SNAPSHOTS:
{code_snapshots}

AUDIT INSTRUCTIONS:
1. Perform a holistic STRIDE threat model and security audit across the entire repository (Terraform modules, IAM bindings, Workload Identity Federation, Firestore settings, Cloud Run scaling/ingress, FastAPI auth/rate-limiting middlewares, and CI/CD workflows).
2. Calibrate `raw_severity` vs `contextual_severity` using the real compensating controls present in the codebase (e.g., OIDC `attribute_condition`, Secret Manager `secret_key_ref`, `ClientVerificationMiddleware`, Firebase JWT verification).
3. Surface concrete, high-signal architectural findings (such as broad CI/CD service account roles like `roles/editor` / `roles/secretmanager.admin`, Firestore `DELETE_PROTECTION_DISABLED`, or endpoint/middleware hardening opportunities) with exact file paths, copy-pasteable remediation patches, and verification tests.
4. Assign each finding a stable, deterministic `finding_id` (e.g., `SEC-IAM-WIF-BROAD-ROLES`, `SEC-TF-FIRESTORE-DELETE-PROT`) so subsequent scans can deduplicate open GitHub Issues.
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
                    response_schema=FullRepoAuditReport,
                    temperature=0.1,
                ),
            )
            print(f"Successfully completed full-repo audit using model: {candidate_model}")
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
    print(f"Full repo audit saved to {args.output_report} ({len(parsed.get('findings', []))} findings).")

    if args.create_issues and os.getenv("GH_TOKEN"):
        create_github_issues(
            parsed,
            min_severity=args.min_severity,
            max_issues=args.max_issues,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    main()
