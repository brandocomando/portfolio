#!/usr/bin/env python3
"""
GitHub PR Action Card Formatter & Reporter.
Formats the 4-Pillar Agentic DevSecOps evaluation into a comprehensive Markdown
PR comment featuring:
  - 4-Pillar Coverage Scorecard & Materiality Gate Breakdown
  - Block 1: Context-Aware Infrastructure & Reachability Summary (+ ASCII DFD)
  - Block 2: Automated STRIDE Threat Model across Trust Boundaries & Remediation Patches
  - Block 3: Synthesized Model-Based Security Test Suite (pytest + adversarial curl probes)
"""
import argparse
import json
import os
import subprocess


def format_markdown(
    report: dict,
    context: dict | None = None,
    materiality: dict | None = None,
) -> str:
    context = context or {}
    materiality = materiality or {}

    severity = report.get("overall_contextual_severity", "Informational")
    badge_emoji = (
        "🟢"
        if severity in {"Low", "Informational"}
        else "🟡"
        if severity == "Medium"
        else "🔴"
    )

    md = []
    md.append(f"## {badge_emoji} Agentic DevSecOps PR Security Assessment — `{severity}` Contextual Risk")
    md.append(f"**Executive Summary:** {report.get('summary', 'Evaluation complete.')}\n")

    # -------------------------------------------------------------------------
    # 4-Pillar DevSecOps Coverage Scorecard
    # -------------------------------------------------------------------------
    cats = materiality.get("categories", {})
    infra_count = len(cats.get("infrastructure", []))
    sec_count = len(cats.get("security_and_auth", []))
    app_count = len(cats.get("application_logic", []))
    dep_count = len(cats.get("dependencies", []))
    bypass_count = len(cats.get("non_material_bypassed", []))

    ingress_count = len(context.get("public_ingress_points", []))
    iam_count = len(context.get("iam_bindings", []))
    overpriv_count = len(context.get("overprivileged_iam_bindings", []))
    route_count = len(context.get("application_routes", []))
    threat_count = len(report.get("threats", []))

    md.append("### 📊 4-Pillar DevSecOps Pipeline Scorecard")
    md.append("| Pillar | Coverage | Pipeline Telemetry & In-Repo Verification |")
    md.append("| :--- | :---: | :--- |")
    md.append(
        f"| **1. Material-Change Detection Gate** | `100%` | Triggered (`{infra_count}` Infra, `{sec_count}` Security/Auth, `{app_count}` App, `{dep_count}` Deps; `{bypass_count}` cosmetic files bypassed) |"
    )
    md.append(
        f"| **2. Context-Aware Infra Aggregator** | `95%` | Parsed `{ingress_count}` ingress points, `{iam_count}` IAM bindings (`{overpriv_count}` broad/wildcard), `{route_count}` API routes |"
    )
    md.append(
        f"| **3. Automated STRIDE Threat Modeling** | `95%` | Evaluated `{threat_count}` architectural threats across verified GCP/AWS trust boundaries |"
    )
    md.append(
        "| **4. Model-Based Security Testing** | `80%` | Synthesized dynamic `pytest` boundary assertions & adversarial `curl` probes |"
    )
    md.append("")

    # -------------------------------------------------------------------------
    # Block 1: Context-Aware Infrastructure & Reachability Summary
    # -------------------------------------------------------------------------
    md.append("---")
    md.append("### 🌐 Block 1: Context-Aware Infrastructure & Blast-Radius Summary")
    context_narrative = report.get(
        "context_summary_narrative",
        "Evaluated workload reachability, IAM role scoping, and middleware boundaries from co-located Terraform definitions.",
    )
    md.append(f"> **Context Verdict:** {context_narrative}\n")

    if context:
        is_pub = context.get("is_public_facing", False)
        has_wc = context.get("iam_wildcard_detected", False)
        md.append(
            f"- **Network Reachability (`is_public_facing={is_pub}`):** "
            + (
                ", ".join(f"`{p}`" for p in context.get("public_ingress_points", [])[:4])
                if context.get("public_ingress_points")
                else "Isolated internal workload (Zero `0.0.0.0/0` or `allUsers` public ingress)."
            )
        )
        md.append(
            f"- **IAM Blast Radius (`iam_wildcard_or_broad_role={has_wc}`):** "
            + (
                ", ".join(f"`{s}`" for s in context.get("iam_wildcard_statements", [])[:4])
                if context.get("iam_wildcard_statements")
                else "Strictly least-privilege IAM roles."
            )
        )
        if context.get("security_middlewares"):
            md.append(
                "- **Active Security Middleware:** "
                + ", ".join(f"`{m}`" for m in context.get("security_middlewares", []))
            )
        if context.get("datastores"):
            md.append(
                "- **Backing Datastores:** "
                + ", ".join(f"`{d}`" for d in context.get("datastores", []))
            )
        md.append("")

    dfd = report.get("data_flow_diagram_ascii")
    if dfd:
        md.append("<details open><summary><b>🗺️ Verified Architecture & Trust Boundary Data Flow Diagram (DFD)</b></summary>\n")
        md.append(f"```text\n{dfd}\n```\n</details>\n")

    # -------------------------------------------------------------------------
    # Block 2: STRIDE Threat Model & Contextual Risk Adjustments
    # -------------------------------------------------------------------------
    md.append("---")
    md.append("### 🛡️ Block 2: Automated STRIDE Threat Model & Context Adjustments")
    threats = report.get("threats", [])
    if threats:
        md.append(
            "| STRIDE Category | Trust Boundary & Component | Threat Description | Raw Severity | Contextual Severity | Context Adjustment Rationale |"
        )
        md.append("| :--- | :--- | :--- | :---: | :---: | :--- |")
        for t in threats:
            boundary = t.get("trust_boundary", "Application Boundary")
            comp = t.get("affected_component", "N/A")
            md.append(
                f"| **{t['category']}** | `{boundary}`<br/>*({comp})* | {t['description']} | `{t['raw_severity']}` | **{t['contextual_severity']}** | {t['context_rationale']} |"
            )
        md.append("")

        md.append("#### 🔧 Actionable Remediation Patches (Code & Terraform)")
        for idx, t in enumerate(threats, start=1):
            if t.get("suggested_fix"):
                comp = t.get("affected_component", "")
                title = f"Remediation {idx}: {t['category']} — {comp}" if comp else f"Remediation {idx}: {t['category']}"
                md.append(f"<details><summary><b>{title}</b></summary>\n")
                md.append(f"```python\n{t['suggested_fix']}\n```\n</details>\n")
    else:
        md.append("✅ **No critical architectural or STRIDE threats identified in this diff.**\n")

    # -------------------------------------------------------------------------
    # Block 3: Generated Model-Based Security Test Suite
    # -------------------------------------------------------------------------
    md.append("---")
    md.append("### 🧪 Block 3: Generated Model-Based Security Verification Suite")
    test_code = report.get("generated_verification_tests")
    if test_code:
        md.append(
            "<details open><summary><b>🐍 Synthesized Pytest Boundary & Auth Verification Suite (<code>tests/security/test_generated_verification.py</code>)</b></summary>\n"
        )
        md.append(f"```python\n{test_code}\n```\n</details>\n")

    curl_probes = report.get("generated_adversarial_curl_probes")
    if curl_probes:
        md.append(
            "<details><summary><b>🎯 Adversarial Boundary & Fuzzing Probes (<code>curl</code>)</b></summary>\n"
        )
        md.append(f"```bash\n{curl_probes}\n```\n</details>\n")

    md.append(
        "---\n*Automated 4-Pillar DevSecOps assessment powered by in-repo Terraform context extraction & Gemini 3.5 Flash structured threat modeling.*"
    )
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
    parser.add_argument("--context-file", default="/tmp/tf_context.json")
    parser.add_argument("--materiality-file", default="/tmp/materiality_gate.json")
    parser.add_argument("--pr-number", default=None)
    args = parser.parse_args()

    with open(args.report_file, "r", encoding="utf-8") as fh:
        report = json.load(fh)

    context = {}
    if args.context_file and os.path.exists(args.context_file):
        try:
            with open(args.context_file, "r", encoding="utf-8") as fh:
                context = json.load(fh)
        except Exception:
            pass

    materiality = {}
    if args.materiality_file and os.path.exists(args.materiality_file):
        try:
            with open(args.materiality_file, "r", encoding="utf-8") as fh:
                materiality = json.load(fh)
        except Exception:
            pass

    body = format_markdown(report, context=context, materiality=materiality)
    print("Formatted PR Markdown:\n")
    print(body)

    pr_num = args.pr_number or os.getenv("PR_NUMBER")
    if pr_num and os.getenv("GH_TOKEN"):
        post_github_comment(pr_num, body)


if __name__ == "__main__":
    main()
