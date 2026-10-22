#!/usr/bin/env python3
"""
GitHub PR Action Card Formatter & Reporter.
Posts the structured evaluation results directly as a Pull Request comment.
"""
import argparse
import json
import os
import subprocess
import sys

def format_markdown(report: dict) -> str:
    severity = report.get("overall_contextual_severity", "Informational")
    badge_emoji = "🟢" if severity in {"Low", "Informational"} else "🟡" if severity == "Medium" else "🔴"

    md = []
    md.append(f"## {badge_emoji} DevSecOps Agentic Security Card: {severity} Risk")
    md.append(f"**Summary:** {report.get('summary', 'Evaluation complete.')}\n")

    threats = report.get("threats", [])
    if threats:
        md.append("### Identified STRIDE Threats & Context-Aware Adjustments")
        md.append("| Category | Threat | Raw Severity | Contextual Severity | Context Rationale |")
        md.append("| :--- | :--- | :--- | :--- | :--- |")
        for t in threats:
            md.append(f"| **{t['category']}** | {t['description']} | {t['raw_severity']} | **{t['contextual_severity']}** | {t['context_rationale']} |")
        md.append("")

        md.append("### Remediation Guidance")
        for idx, t in enumerate(threats, start=1):
            if t.get("suggested_fix"):
                md.append(f"<details><summary><b>Remediation {idx}: {t['category']}</b></summary>\n")
                md.append(f"```python\n{t['suggested_fix']}\n```\n</details>\n")
    else:
        md.append("✅ **No critical architectural or STRIDE threats identified in this diff.**\n")

    test_code = report.get("generated_verification_tests")
    if test_code:
        md.append("<details><summary><b>View Synthesized Verification Test Stubs (pytest)</b></summary>\n")
        md.append(f"```python\n{test_code}\n```\n</details>\n")

    md.append("---\n*Automated assessment powered by internal AppSec Agentic Tooling.*")
    return "\n".join(md)

def post_github_comment(pr_number: str, comment_body: str):
    try:
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
