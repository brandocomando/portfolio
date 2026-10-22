"""
Unit tests for Material-Change Detection Filter (filter_diff.py).
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../scripts/security")))

from filter_diff import evaluate_materiality


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
