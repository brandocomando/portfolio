"""
Unit tests for Material-Change Detection Filter (filter_diff.py),
PR Action Card Formatter & Comment Minimizer (post_pr_comment.py),
and Full-Repo Audit Issue Deduplication (run_full_repo_audit.py).
"""
import json
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../scripts/security")))

from filter_diff import categorize_files, evaluate_materiality
from post_pr_comment import COMMENT_MARKER, format_markdown, hide_previous_pr_comments
from run_full_repo_audit import create_github_issues, format_issue_body


def test_empty_file_list():
    is_material, summary = evaluate_materiality([])
    assert is_material is False
    assert "No files modified" in summary


def test_non_material_docs_and_styles():
    files = [
        "README.md",
        "docs/architecture.txt",
        "assets/logo.png",
        "frontend/src/styles/main.css",
        ".vscode/settings.json",
    ]
    is_material, summary = evaluate_materiality(files)
    assert is_material is False
    assert "Only non-material files" in summary

    cat = categorize_files(files)
    assert len(cat["categories"]["non_material_bypassed"]) == 5


def test_material_infrastructure_and_dependencies():
    files = [
        "README.md",
        "infra/main.tf",
        "backend/package.json",
        "backend/Dockerfile",
    ]
    is_material, summary = evaluate_materiality(files)
    assert is_material is True
    assert "infra/main.tf" in summary
    assert "backend/package.json" in summary
    assert "backend/Dockerfile" in summary

    cat = categorize_files(files)
    assert "infra/main.tf" in cat["categories"]["infrastructure"]
    assert "backend/Dockerfile" in cat["categories"]["infrastructure"]
    assert "backend/package.json" in cat["categories"]["dependencies"]
    assert "README.md" in cat["categories"]["non_material_bypassed"]


def test_material_security_sensitive_paths():
    files = [
        "backend/app/auth/login.py",
        "backend/app/middleware/cors.ts",
    ]
    is_material, summary = evaluate_materiality(files)
    assert is_material is True
    assert "Security-sensitive application path modified" in summary


def test_material_application_code():
    files = [
        "backend/app/services/calculator.py",
    ]
    is_material, summary = evaluate_materiality(files)
    assert is_material is True
    assert "Application logic modified: backend/app/services/calculator.py" in summary


def test_format_markdown_three_blocks():
    report = {
        "summary": "Assessed modified security scripts.",
        "context_summary_narrative": "Scripts run inside isolated GitHub Actions runner; downgraded subprocess risk from Medium to Low.",
        "data_flow_diagram_ascii": "[GitHub PR] --> [GitHub Actions Runner] --> [PR Comment API]",
        "overall_contextual_severity": "Low",
        "threats": [
            {
                "category": "Tampering",
                "trust_boundary": "GitHub Runner -> Git CLI",
                "affected_component": "scripts/security/filter_diff.py",
                "description": "Base ref argument passed to git diff command.",
                "raw_severity": "Medium",
                "contextual_severity": "Low",
                "context_rationale": "Executed via subprocess list arguments without shell=True.",
                "suggested_fix": "cmd = ['git', 'diff', '--name-only', f'{base_ref}...HEAD']",
            }
        ],
        "generated_verification_tests": "def test_diff(): assert True",
        "generated_adversarial_curl_probes": "",
    }
    context = {
        "is_public_facing": True,
        "public_ingress_points": ["google_cloud_run_v2_service.backend"],
        "iam_wildcard_detected": True,
        "iam_wildcard_statements": ["google_project_iam_member.terraform_editor"],
        "security_middlewares": ["ClientVerificationMiddleware"],
    }

    md = format_markdown(report, context=context)
    assert COMMENT_MARKER in md
    assert "### 1. Context Summary" in md
    assert "### 2. STRIDE Threat Model" in md
    assert "### 3. Generated Model-Based Test Suite" in md
    assert "scripts/security/filter_diff.py" in md


def test_hide_previous_pr_comments(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "brandocomando/portfolio")
    mock_comments = json.dumps(
        [
            {"id": 1, "node_id": "IC_old_appsec", "body": f"{COMMENT_MARKER}\n## Security Card"},
            {"id": 2, "node_id": "IC_human_comment", "body": "Looks good to me!"},
        ]
    )

    with patch("post_pr_comment.subprocess.check_output", return_value=mock_comments), patch(
        "post_pr_comment.subprocess.check_call"
    ) as mock_call:
        hide_previous_pr_comments("34")
        assert mock_call.call_count == 1
        called_args = mock_call.call_args[0][0]
        assert "id=IC_old_appsec" in called_args


def test_create_github_issues_deduplicates_and_filters_severity():
    sample_report = {
        "executive_summary": "Full repo scan.",
        "findings": [
            {
                "finding_id": "SEC-IAM-EDITOR",
                "title": "Scope down roles/editor on CI service account",
                "stride_category": "Elevation of Privilege",
                "affected_files": ["infra/modules/iam_wif/main.tf"],
                "trust_boundary": "GitHub OIDC -> GCP IAM",
                "raw_severity": "High",
                "contextual_severity": "Medium",
                "description": "Broad role granted.",
                "context_rationale": "Mitigated by OIDC repo condition.",
                "remediation_patch": "role = 'roles/run.admin'",
                "verification_test": "assert True",
            },
            {
                "finding_id": "SEC-FIRESTORE-DEL",
                "title": "Enable delete protection on Firestore",
                "stride_category": "Tampering",
                "affected_files": ["infra/modules/firestore/main.tf"],
                "trust_boundary": "Terraform Control Plane -> Firestore",
                "raw_severity": "Medium",
                "contextual_severity": "Medium",
                "description": "Delete protection disabled.",
                "context_rationale": "State could allow accidental deletion.",
                "remediation_patch": "delete_protection_state = 'DELETE_PROTECTION_ENABLED'",
                "verification_test": "assert True",
            },
            {
                "finding_id": "SEC-LOW-INFO",
                "title": "Minor logging format note",
                "stride_category": "Repudiation",
                "affected_files": ["backend/app/main.py"],
                "trust_boundary": "App",
                "raw_severity": "Low",
                "contextual_severity": "Low",
                "description": "Low severity item.",
                "context_rationale": "N/A",
                "remediation_patch": "pass",
                "verification_test": "assert True",
            },
        ],
    }

    existing_open = [
        {
            "number": 10,
            "title": "[Security][Medium] Scope down roles/editor on CI service account",
            "body": "<!-- appsec-finding-id: SEC-IAM-EDITOR -->",
        }
    ]

    with patch("run_full_repo_audit.get_existing_open_issues", return_value=existing_open), patch(
        "run_full_repo_audit.ensure_security_label"
    ), patch(
        "run_full_repo_audit.subprocess.check_output",
        return_value="https://github.com/brandocomando/portfolio/issues/35\n",
    ) as mock_create:
        urls = create_github_issues(sample_report, min_severity="Medium", max_issues=5)
        assert urls == ["https://github.com/brandocomando/portfolio/issues/35"]
        assert mock_create.call_count == 1
        body_Check = format_issue_body(sample_report["findings"][1])
        assert "SEC-FIRESTORE-DEL" in body_Check
