"""
Unit tests for Terraform Context Extractor (extract_context.py).
"""
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../scripts/security")))

from extract_context import inspect_hcl_data, parse_tf_files


def test_inspect_hcl_data_public_alb_and_open_sg():
    data = {
        "resource": [
            {
                "aws_alb": {
                    "public_api": {
                        "name": "public-api-alb",
                        "internal": False,
                        "tags": {
                            "DataClassification": "Confidential",
                        },
                    }
                }
            },
            {
                "aws_security_group": {
                    "web_sg": {
                        "name": "web-sg",
                        "ingress": [
                            {
                                "from_port": 443,
                                "to_port": 443,
                                "protocol": "tcp",
                                "cidr_blocks": ["0.0.0.0/0"],
                            }
                        ],
                    }
                }
            },
            {
                "aws_iam_policy": {
                    "wildcard_policy": {
                        "name": "wildcard-policy",
                        "policy": '{"Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]}',
                    }
                }
            },
        ]
    }
    context = {
        "is_public_facing": False,
        "public_ingress_points": [],
        "iam_wildcard_detected": False,
        "iam_wildcard_statements": [],
        "data_classifications": [],
    }

    inspect_hcl_data(data, context, "infra/main.tf")

    assert context["is_public_facing"] is True
    assert "aws_alb.public_api (in infra/main.tf)" in context["public_ingress_points"]
    assert "SG web_sg allows 0.0.0.0/0 on port 443" in context["public_ingress_points"]
    assert context["iam_wildcard_detected"] is True
    assert "aws_iam_policy.wildcard_policy" in context["iam_wildcard_statements"]
    assert "aws_alb.public_api: Confidential" in context["data_classifications"]


def test_inspect_hcl_data_internal_only():
    data = {
        "resource": [
            {
                "aws_lb": {
                    "internal_service": {
                        "name": "internal-lb",
                        "internal": True,
                    }
                }
            },
            {
                "aws_security_group": {
                    "internal_sg": {
                        "name": "internal-sg",
                        "ingress": {
                            "from_port": 8080,
                            "to_port": 8080,
                            "protocol": "tcp",
                            "cidr_blocks": ["10.0.0.0/8"],
                        },
                    }
                }
            },
        ]
    }
    context = {
        "is_public_facing": False,
        "public_ingress_points": [],
        "iam_wildcard_detected": False,
        "iam_wildcard_statements": [],
        "data_classifications": [],
    }

    inspect_hcl_data(data, context, "infra/internal.tf")

    assert context["is_public_facing"] is False
    assert context["public_ingress_points"] == []
    assert context["iam_wildcard_detected"] is False
    assert context["iam_wildcard_statements"] == []


def test_parse_tf_files_walks_directory(tmp_path):
    tf_file = tmp_path / "main.tf"
    tf_file.write_text('resource "aws_alb" "app" {}\n', encoding="utf-8")

    mock_hcl = {
        "resource": [
            {
                "aws_alb": {
                    "app": {
                        "internal": False,
                    }
                }
            }
        ]
    }

    with patch("extract_context.hcl2.load", return_value=mock_hcl):
        context = parse_tf_files(str(tmp_path))

    assert context["is_public_facing"] is True
    assert len(context["public_ingress_points"]) == 1
