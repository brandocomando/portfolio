"""
Unit tests for Pillar 1: Material-Change Detection Filter (filter_diff.py)
and PR Action Card Formatter (post_pr_comment.py).
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../scripts/security")))

from filter_diff import categorize_files, evaluate_materiality
from post_pr_comment import format_markdown


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
    assert "4-Pillar DevSecOps Pipeline Scorecard" in md
    assert "Block 1: Context-Aware Infrastructure & Blast-Radius Summary" in md
    assert "Block 2: Automated STRIDE Threat Model & Context Adjustments" in md
    assert "Block 3: Generated Model-Based Security Verification Suite" in md
    assert "Downgraded secret exposure risk from High to Low" in md
