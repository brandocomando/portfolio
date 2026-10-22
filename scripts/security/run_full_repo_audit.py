#!/usr/bin/env python3
"""
Full-Repository LangGraph Security Scanner & GitHub Issue Reporter.
Uses a stateful LangGraph ReAct agent (`StateGraph`) equipped with dynamic repository
discovery tools (`list_files`, `search_code`, `read_file`, `inspect_terraform`)
to autonomously explore the entire repository without hardcoded directory paths,
perform holistic STRIDE threat modeling, and create deduplicated GitHub Issues.
"""
import argparse
import json
import os
import subprocess
import sys
from typing import Any, TypedDict
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from langgraph.graph import StateGraph, END

from repo_tools import make_agent_tools, redact_secrets


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
        description="How surrounding Terraform/application controls discovered via tools mitigate or amplify this risk"
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


class RepoAuditGraphState(TypedDict):
    repo_root: str
    contents: list[Any]
    tool_trace: list[str]
    iterations: int
    max_iterations: int
    pending_tool_calls: list[dict[str, Any]]
    final_report: dict[str, Any]


def call_gemini_with_fallback(
    client: genai.Client,
    contents: Any,
    config: types.GenerateContentConfig,
) -> Any:
    primary = os.getenv("GEMINI_SECURITY_MODEL", "gemini-3.5-flash")
    candidates = list(dict.fromkeys([primary, "gemini-2.5-flash", "gemini-2.0-flash"]))
    last_err = None
    for model_name in candidates:
        try:
            return client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
        except Exception as err:
            print(f"Warning: Model '{model_name}' failed ({err}), trying next fallback...")
            last_err = err
    raise RuntimeError(f"All Gemini models failed. Last error: {last_err}")


def build_full_repo_audit_graph(client: genai.Client, repo_root: str):
    """Builds a LangGraph ReAct agent that autonomously explores the repository for full-scan auditing."""
    tool_bundle = make_agent_tools(repo_root)
    tool_functions = tool_bundle["functions"]
    tool_dispatch = tool_bundle["dispatch"]

    def explore_node(state: RepoAuditGraphState) -> dict[str, Any]:
        contents = list(state["contents"])
        if not contents:
            prompt = f"""
You are an autonomous Principal Cloud Security & DevSecOps Architect performing a Full-Repository Security Audit.
Instead of relying on hardcoded paths, use your repository exploration tools to dynamically discover and inspect the codebase:
- `list_files(subdir, glob_pattern)`: Discover all directories, Terraform modules, backend services, MLOps pipelines, and CI/CD workflows.
- `search_code(regex_query, file_glob)`: Search for IAM bindings, SDK calls, authentication middlewares, rate limiters, or secret handling.
- `read_file(file_path, start_line, end_line)`: Read key files to verify whether IAM permissions match actual code usage and whether security controls are properly enforced.
- `inspect_terraform(tf_path)`: Parse `.tf` files into structured HCL2 JSON.

Start by calling `list_files` or `inspect_terraform` and `search_code` to map the repository's architecture (up to {state['max_iterations']} steps) so you can perform a comprehensive, evidence-backed STRIDE audit.
"""
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))

        response = call_gemini_with_fallback(
            client=client,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=tool_functions,
                temperature=0.1,
            ),
        )
        candidate_content = response.candidates[0].content
        contents.append(candidate_content)

        calls = []
        if response.function_calls:
            for fc in response.function_calls:
                calls.append({"name": fc.name, "args": dict(fc.args) if fc.args else {}})

        return {
            "contents": contents,
            "pending_tool_calls": calls,
            "iterations": state["iterations"] + 1,
        }

    def tools_node(state: RepoAuditGraphState) -> dict[str, Any]:
        contents = list(state["contents"])
        trace = list(state["tool_trace"])
        response_parts = []

        for call in state.get("pending_tool_calls", []):
            fn_name = call["name"]
            fn_args = call["args"]
            trace_entry = f"{fn_name}({json.dumps(fn_args)})"
            print(f"[Full-Scan LangGraph Tool Call] {trace_entry}")
            trace.append(trace_entry)

            fn = tool_dispatch.get(fn_name)
            if fn is None:
                result_str = f"Error: Unknown tool '{fn_name}'."
            else:
                try:
                    result_str = fn(**fn_args)
                except Exception as e:
                    result_str = f"Error executing {fn_name}: {e}"

            response_parts.append(
                types.Part.from_function_response(
                    name=fn_name,
                    response={"result": result_str},
                )
            )

        contents.append(types.Content(role="tool", parts=response_parts))
        return {
            "contents": contents,
            "tool_trace": trace,
            "pending_tool_calls": [],
        }

    def synthesize_node(state: RepoAuditGraphState) -> dict[str, Any]:
        contents = list(state["contents"])
        synthesis_prompt = """
Based on your autonomous exploration of the repository:
1. Produce the structured `FullRepoAuditReport` JSON.
2. Calibrate `raw_severity` vs `contextual_severity` using the real compensating controls you verified in the codebase (e.g., OIDC `attribute_condition`, Secret Manager `secret_key_ref`, `ClientVerificationMiddleware`, Firebase JWT verification, and actual SDK usage vs IAM roles).
3. Assign each finding a deterministic `finding_id` (e.g., `SEC-IAM-WIF-BROAD-ROLES`, `SEC-TF-FIRESTORE-DELETE-PROT`) for GitHub Issue deduplication.
"""
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=synthesis_prompt)]))

        response = call_gemini_with_fallback(
            client=client,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FullRepoAuditReport,
                temperature=0.1,
            ),
        )
        parsed = json.loads(response.text)
        parsed["agent_tool_trace"] = state.get("tool_trace", [])
        return {"final_report": parsed}

    def should_continue(state: RepoAuditGraphState) -> str:
        if state.get("pending_tool_calls") and state["iterations"] < state["max_iterations"]:
            return "tools"
        return "synthesize"

    workflow = StateGraph(RepoAuditGraphState)
    workflow.add_node("explore", explore_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("synthesize", synthesize_node)

    workflow.set_entry_point("explore")
    workflow.add_conditional_edges(
        "explore",
        should_continue,
        {
            "tools": "tools",
            "synthesize": "synthesize",
        },
    )
    workflow.add_edge("tools", "explore")
    workflow.add_edge("synthesize", END)

    return workflow.compile()


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
*Generated by the Full-Repository LangGraph DevSecOps Audit workflow (`.github/workflows/appsec-full-scan.yml`).*
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
    parser.add_argument("--output-report", default="/tmp/full_security_audit.json")
    parser.add_argument("--min-severity", default="Medium", choices=["Low", "Medium", "High", "Critical"])
    parser.add_argument("--max-issues", type=int, default=5)
    parser.add_argument("--max-iterations", type=int, default=6)
    parser.add_argument("--create-issues", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    graph = build_full_repo_audit_graph(client, args.repo_root)

    initial_state: RepoAuditGraphState = {
        "repo_root": args.repo_root,
        "contents": [],
        "tool_trace": [],
        "iterations": 0,
        "max_iterations": args.max_iterations,
        "pending_tool_calls": [],
        "final_report": {},
    }

    final_state = graph.invoke(initial_state)
    parsed = json.loads(redact_secrets(json.dumps(final_state["final_report"])))

    with open(args.output_report, "w", encoding="utf-8") as fh:
        json.dump(parsed, fh, indent=2)

    print(
        f"Full repo audit saved to {args.output_report} "
        f"({len(parsed.get('findings', []))} findings, {len(parsed.get('agent_tool_trace', []))} tool calls)."
    )

    if args.create_issues and os.getenv("GH_TOKEN"):
        create_github_issues(
            parsed,
            min_severity=args.min_severity,
            max_issues=args.max_issues,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    main()
