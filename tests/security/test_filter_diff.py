"""
Unit tests for Pillar 1: Material-Change Detection Filter (filter_diff.py)
and PR Action Card Formatter & Comment Minimizer (post_pr_comment.py).
"""
import json
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../scripts/security")))

from filter_diff import categorize_files, evaluate_materiality
from post_pr_comment import COMMENT_MARKER, format_markdown, hide_previous_pr_comments


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
        "summary": "Assessed Cloud Run and FastAPI routes.",
        "context_summary_narrative": "Workload exposed via INGRESS_TRAFFIC_ALL; runtime SA scoped to datastore.user. Downgraded secret exposure risk from High to Low due to Secret Manager injection.",
        "data_flow_diagram_ascii": "[Internet] --> [Cloud Run] --> [Firestore]",
        "overall_contextual_severity": "Medium",
        "threats": [
            {
                "category": "Elevation of Privilege",
                "trust_boundary": "GitHub Actions OIDC -> GCP Project IAM",
                "affected_component": "google_project_iam_member.terraform_editor",
                "description": "CI/CD SA has broad roles/editor permission.",
                "raw_severity": "High",
                "contextual_severity": "Medium",
                "context_rationale": "Mitigated by Workload Identity Federation repository attribute_condition.",
                "suggested_fix": "role = \"roles/run.admin\"",
            }
        ],
        "generated_verification_tests": "def test_unauthorized(): assert True",
        "generated_adversarial_curl_probes": "curl -i -X POST https://example.com/api/v1/chat/stream",
    }
    context = {
        "is_public_facing": True,
        "public_ingress_points": ["google_cloud_run_v2_service.backend"],
        "iam_wildcard_detected": True,
        "iam_wildcard_statements": ["google_project_iam_member.terraform_editor"],
        "iam_bindings": ["b1"],
        "overprivileged_iam_bindings": ["b1"],
        "application_routes": ["POST /stream"],
        "security_middlewares": ["ClientVerificationMiddleware"],
        "datastores": ["google_firestore_database.database"],
    }
    materiality = {
        "categories": {
            "infrastructure": ["infra/main.tf"],
            "security_and_auth": ["backend/app/core/security.py"],
            "application_logic": [],
            "dependencies": [],
            "non_material_bypassed": ["README.md"],
        }
    }

    md = format_markdown(report, context=context, materiality=materiality)
    assert COMMENT_MARKER in md
    assert "### 1. Context Summary" in md
    assert "### 2. STRIDE Threat Model" in md
    assert "### 3. Generated Model-Based Test Suite" in md
    assert "Downgraded secret exposure risk from High to Low" in md


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
