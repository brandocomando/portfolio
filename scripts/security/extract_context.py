#!/usr/bin/env python3
"""
Terraform Context Extractor.
Parses local Terraform definitions to discover ingress exposure, IAM boundaries, and tags.
"""
import argparse
import json
import os
import hcl2

def parse_tf_files(repo_root: str) -> dict:
    context = {
        "is_public_facing": False,
        "public_ingress_points": [],
        "iam_wildcard_detected": False,
        "iam_wildcard_statements": [],
        "data_classifications": []
    }

    for root, _, files in os.walk(repo_root):
        if ".terraform" in root:
            continue
        for file in files:
            if not file.endswith(".tf"):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data = hcl2.load(fh)
                    inspect_hcl_data(data, context, path)
            except Exception as e:
                print(f"Warning: Failed parsing {path}: {e}")

    return context

def inspect_hcl_data(data: dict, context: dict, file_path: str):
    resources = data.get("resource", [])
    for res_dict in resources:
        for res_type, instances in res_dict.items():
            for res_name, config in instances.items():
                # Check ALB / Ingress exposure
                if res_type in {"aws_lb", "aws_alb"}:
                    internal = config.get("internal", False)
                    if not internal:
                        context["is_public_facing"] = True
                        context["public_ingress_points"].append(f"{res_type}.{res_name} (in {file_path})")

                # Check Security Groups open to internet
                if res_type in {"aws_security_group", "aws_security_group_rule"}:
                    ingress_rules = config.get("ingress", [])
                    if isinstance(ingress_rules, dict):
                        ingress_rules = [ingress_rules]
                    for rule in ingress_rules:
                        cidr_blocks = rule.get("cidr_blocks", [])
                        if "0.0.0.0/0" in cidr_blocks:
                            context["is_public_facing"] = True
                            port = rule.get("from_port", "all")
                            context["public_ingress_points"].append(f"SG {res_name} allows 0.0.0.0/0 on port {port}")

                # Check IAM wildcard policies
                if res_type in {"aws_iam_policy", "aws_iam_role_policy"}:
                    policy_doc = config.get("policy", "")
                    if isinstance(policy_doc, str) and '"*"' in policy_doc:
                        context["iam_wildcard_detected"] = True
                        context["iam_wildcard_statements"].append(f"{res_type}.{res_name}")

                # Extract Data Classification Tags
                tags = config.get("tags", {})
                if isinstance(tags, dict):
                    for tag_key, tag_val in tags.items():
                        if tag_key.lower() in {"dataclassification", "tier", "compliance"}:
                            context["data_classifications"].append(f"{res_type}.{res_name}: {tag_val}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-file", default="/tmp/tf_context.json")
    args = parser.parse_args()

    context = parse_tf_files(args.repo_root)
    with open(args.output_file, "w", encoding="utf-8") as fh:
        json.dump(context, fh, indent=2)

    print(f"Extracted Context saved to {args.output_file}:")
    print(json.dumps(context, indent=2))

if __name__ == "__main__":
    main()
