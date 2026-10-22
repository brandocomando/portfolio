#!/usr/bin/env python3
"""
GitHub PR Action Card Formatter & Reporter.
Formats the DevSecOps security evaluation into a clean, professional Markdown
PR review card containing three core sections:
  1. Context Summary (Autonomous LangGraph repo investigation & severity adjustments)
  2. STRIDE Threat Model (Architectural threats, context adjustments, and CodeRabbit-style
     "🤖 Prompt for AI Agents" + Suggested Patch blocks)
  3. Generated Model-Based Test Suite (Runnable pytest verification tests + curl probes)

Automatically hides (minimizes as OUTDATED) any previous DevSecOps security assessment
comments on the PR before posting the latest assessment.
"""
import argparse
import json
import os
import subprocess

COMMENT_MARKER = "<!-- appsec-agentic-pr-comment -->"
LEGACY_HEADER_SIGNATURES = (
    COMMENT_MARKER,
    "Agentic DevSecOps PR Security Assessment",
    "DevSecOps Agentic Security Card:",
    "DevSecOps Security Assessment",
)


def format_markdown(report: dict) -> str:
    severity = report.get("overall_contextual_severity", "Informational")
    badge_emoji = (
        "🟢"
        if severity in {"Low", "Informational"}
        else "🟡"
        if severity == "Medium"
        else "🔴"
    )

    md = [COMMENT_MARKER]
    md.append(f"## {badge_emoji} DevSecOps Security Assessment — `{severity}` Contextual Risk")
    md.append(f"**Summary:** {report.get('summary', 'Evaluation complete.')}\n")

    # -------------------------------------------------------------------------
    # 1. Context Summary
    # -------------------------------------------------------------------------
    md.append("### 1. Context Summary")
    context_narrative = report.get(
        "context_summary_narrative",
        "Evaluated workload reachability, IAM role scoping, and middleware boundaries via autonomous repository inspection.",
    )
    md.append(f"> {context_narrative}\n")

    dfd = report.get("data_flow_diagram_ascii")
    if dfd:
        md.append("<details><summary><b>Architecture & Trust Boundary Data Flow Diagram (DFD)</b></summary>\n")
        md.append(f"```text\n{dfd}\n```\n</details>\n")

    tool_trace = report.get("agent_tool_trace", [])
    if tool_trace:
        md.append(f"<details><summary><b>Autonomous LangGraph Repo Investigation ({len(tool_trace)} tool calls)</b></summary>\n")
        for idx, tc in enumerate(tool_trace, start=1):
            md.append(f"{idx}. `{tc}`")
        md.append("\n</details>\n")

    # -------------------------------------------------------------------------
    # 2. STRIDE Threat Model
    # -------------------------------------------------------------------------
    md.append("### 2. STRIDE Threat Model")
    threats = report.get("threats", [])
    if threats:
        md.append(
            "| Category | Component & Boundary | Threat Description | Raw Severity | Contextual Severity | Context Rationale |"
        )
        md.append("| :--- | :--- | :--- | :---: | :---: | :--- |")
        for t in threats:
            boundary = t.get("trust_boundary", "Application Boundary")
            comp = t.get("affected_component", "N/A")
            md.append(
                f"| **{t['category']}** | `{comp}`<br/>*({boundary})* | {t['description']} | `{t['raw_severity']}` | **{t['contextual_severity']}** | {t['context_rationale']} |"
            )
        md.append("")

        md.append("#### Remediation & AI Agent Prompts")
        for idx, t in enumerate(threats, start=1):
            comp = t.get("affected_component", "")
            title = f"Remediation {idx}: {t['category']} ({comp})" if comp else f"Remediation {idx}: {t['category']}"
            ai_prompt = t.get("ai_agent_prompt") or (
                f"In @{comp}, verify the following {t['category']} finding: {t['description']}. "
                f"Confirm whether the issue is applicable in context ({t['context_rationale']}), "
                f"apply the remediation, and run pytest to verify."
            )
            md.append(f"<details><summary><b>🤖 {title}</b></summary>\n")
            md.append("##### 📋 Prompt for AI Agents *(Copy & paste into your coding agent)*")
            md.append(f"```text\n{ai_prompt}\n```\n")
            if t.get("suggested_fix"):
                md.append("##### 🔧 Suggested Code / Configuration Patch")
                md.append(f"```python\n{t['suggested_fix']}\n```")
            md.append("</details>\n")
    else:
        md.append("✅ **No critical architectural or STRIDE threats identified in this diff.**\n")

    return "\n".join(md)


def hide_previous_pr_comments(pr_number: str):
    """Finds and minimizes (hides as OUTDATED) previous AppSec assessment comments on the PR."""
    repo = os.getenv("GITHUB_REPOSITORY")
    if not repo:
        try:
            repo = subprocess.check_output(
                ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except Exception:
            return

    if not repo:
        return

    try:
        output = subprocess.check_output(
            ["gh", "api", f"repos/{repo}/issues/{pr_number}/comments", "--paginate"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        comments = json.loads(output)
    except Exception as e:
        print(f"Warning: Could not list existing PR comments to minimize: {e}")
        return

    minimized_count = 0
    mutation = (
        "mutation($id: ID!) { "
        "minimizeComment(input: {subjectId: $id, classifier: OUTDATED}) { "
        "minimizedComment { isMinimized } "
        "} }"
    )

    for comment in comments:
        body = comment.get("body") or ""
        node_id = comment.get("node_id")
        if not node_id:
            continue
        if any(sig in body for sig in LEGACY_HEADER_SIGNATURES):
            try:
                subprocess.check_call(
                    ["gh", "api", "graphql", "-f", f"query={mutation}", "-f", f"id={node_id}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                minimized_count += 1
            except Exception as e:
                print(f"Warning: Failed to minimize comment {node_id}: {e}")

    if minimized_count > 0:
        print(f"Minimized (hidden as OUTDATED) {minimized_count} previous security comment(s) on PR #{pr_number}.")


def post_github_comment(pr_number: str, comment_body: str):
    try:
        hide_previous_pr_comments(str(pr_number))
        cmd = ["gh", "pr", "comment", str(pr_number), "--body", comment_body]
        subprocess.check_call(cmd)
        print(f"Successfully posted comment to PR #{pr_number}")
    except Exception as e:
        print(f"Warning: Failed to post comment via gh CLI: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-file", required=True)
    parser.add_argument("--pr-number", default=None)
    args = parser.parse_args()

    with open(args.report_file, "r", encoding="utf-8") as fh:
        report = json.load(fh)

    body = format_markdown(report)
    print("Formatted PR Markdown:\n")
    print(body)

    pr_num = args.pr_number or os.getenv("PR_NUMBER")
    if pr_num and os.getenv("GH_TOKEN"):
        post_github_comment(pr_num, body)


if __name__ == "__main__":
    main()
