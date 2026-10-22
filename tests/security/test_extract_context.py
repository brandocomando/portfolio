"""
Unit tests for Pillar 2: Terraform & Application Context Extractor (extract_context.py).
Tests both AWS and GCP (Cloud Run, IAM WIF, Secret Manager, Firestore) HCL2 parsing
as well as real end-to-end parsing with python-hcl2.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../scripts/security")))

from extract_context import parse_tf_files


def test_parse_aws_public_alb_open_sg_and_wildcard_iam(tmp_path):
    tf_content = '''
resource "aws_alb" "public_api" {
  name     = "public-api-alb"
  internal = false
  tags = {
    DataClassification = "Confidential"
  }
}

resource "aws_security_group" "web_sg" {
  name = "web-sg"
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_policy" "wildcard_policy" {
  name   = "wildcard-policy"
  policy = "{\\"Statement\\": [{\\"Effect\\": \\"Allow\\", \\"Action\\": \\"*\\", \\"Resource\\": \\"*\\"}]}"
}
'''
    tf_file = tmp_path / "aws_main.tf"
    tf_file.write_text(tf_content, encoding="utf-8")

    context = parse_tf_files(str(tmp_path))

    assert context["is_public_facing"] is True
    assert any("aws_alb.public_api" in p for p in context["public_ingress_points"])
    assert any("SG web_sg allows 0.0.0.0/0 on port 443" in p for p in context["public_ingress_points"])
    assert context["iam_wildcard_detected"] is True
    assert "aws_iam_policy.wildcard_policy" in context["iam_wildcard_statements"]
    assert any("DataClassification=Confidential" in c for c in context["data_classifications"])


def test_parse_gcp_cloud_run_iam_and_secrets(tmp_path):
    tf_content = '''
resource "google_cloud_run_v2_service" "backend" {
  name    = "portfolio-backend"
  ingress = "INGRESS_TRAFFIC_ALL"
  labels = {
    environment = "prod"
  }
  template {
    containers {
      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "gemini-api-key"
            version = "latest"
          }
        }
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "public_access" {
  name   = "portfolio-backend"
  role   = "roles/run.invoker"
  member = "allUsers"
}

resource "google_project_iam_member" "terraform_editor" {
  project = "my-proj"
  role    = "roles/editor"
  member  = "serviceAccount:ci@my-proj.iam.gserviceaccount.com"
}

resource "google_firestore_database" "database" {
  name                    = "(default)"
  type                    = "FIRESTORE_NATIVE"
  delete_protection_state = "DELETE_PROTECTION_DISABLED"
}
'''
    tf_file = tmp_path / "gcp_main.tf"
    tf_file.write_text(tf_content, encoding="utf-8")

    context = parse_tf_files(str(tmp_path))

    assert context["is_public_facing"] is True
    assert any("google_cloud_run_v2_service.backend" in p for p in context["public_ingress_points"])
    assert any("allUsers" in p for p in context["public_ingress_points"])
    assert context["iam_wildcard_detected"] is True
    assert any("roles/editor" in s for s in context["iam_wildcard_statements"])
    assert any("GEMINI_API_KEY" in s for s in context["secrets_inventory"])
    assert any("google_firestore_database.database" in d for d in context["datastores"])


def test_parse_internal_only_resources(tmp_path):
    tf_content = '''
resource "aws_lb" "internal_service" {
  name     = "internal-lb"
  internal = true
}

resource "aws_security_group" "internal_sg" {
  name = "internal-sg"
  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }
}
'''
    tf_file = tmp_path / "internal.tf"
    tf_file.write_text(tf_content, encoding="utf-8")

    context = parse_tf_files(str(tmp_path))

    assert context["is_public_facing"] is False
    assert context["public_ingress_points"] == []
    assert len(context["private_workloads"]) == 1
    assert context["iam_wildcard_detected"] is False
