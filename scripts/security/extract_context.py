#!/usr/bin/env python3
"""
Terraform & Application Context Extractor.
Parses local Terraform definitions (.tf) AND inspects application source code
(`backend/`, `scripts/`, `.github/workflows/`) to build a bi-directional
Infra <-> Code Cross-Reference Map:
  1. Infrastructure Topology: Ingress exposure, IAM bindings, Service Accounts,
     Secret Manager containers, Datastores, and Auth providers.
  2. Code-Side Cloud SDK & Permission Usage: Which GCP/AWS services, SDK clients,
     secrets, and operations (read vs write/admin) are actually invoked in code.
  3. Bi-Directional Alignment: Allows the PR evaluator to verify:
     - When IAM/Terraform changes: Is the newly granted permission actually used by the code?
     - When Application Code changes: What is the runtime ingress and IAM blast radius of that code?
"""
import argparse
import json
import os
import re
from typing import Any
import hcl2


BROAD_GCP_ROLES = {
    "roles/owner",
    "roles/editor",
    "roles/resourcemanager.projectIamAdmin",
    "roles/iam.securityAdmin",
    "roles/secretmanager.admin",
}

# Maps code-level SDK imports/patterns to the cloud services and least-privilege IAM roles they require
CODE_SDK_SIGNATURES = [
    {
        "service": "GCP Firestore / Datastore",
        "patterns": [r"google\.cloud\s+import\s+firestore", r"firestore\.Client", r"firestore\.AsyncClient"],
        "write_patterns": [r"\.set\(", r"\.add\(", r"\.update\(", r"\.delete\("],
        "read_patterns": [r"\.get\(", r"\.stream\(", r"\.where\("],
        "expected_roles": ["roles/datastore.user", "roles/datastore.viewer"],
    },
    {
        "service": "GCP Secret Manager API",
        "patterns": [r"secretmanager", r"SecretManagerServiceClient"],
        "write_patterns": [r"create_secret", r"add_secret_version", r"destroy_secret_version"],
        "read_patterns": [r"access_secret_version"],
        "expected_roles": ["roles/secretmanager.secretAccessor"],
    },
    {
        "service": "Google Gemini / Vertex AI",
        "patterns": [r"from\s+google\s+import\s+genai", r"ChatGoogleGenerativeAI", r"genai\.Client"],
        "write_patterns": [],
        "read_patterns": [r"generate_content", r"ainvoke", r"astream"],
        "expected_roles": ["Secret Manager env injection (GEMINI_API_KEY) or roles/aiplatform.user"],
    },
    {
        "service": "Firebase Admin / Identity Platform Auth",
        "patterns": [r"verify_firebase_token", r"firebase_admin", r"google\.oauth2\s+import\s+id_token"],
        "write_patterns": [r"create_user", r"set_custom_user_claims"],
        "read_patterns": [r"verify_firebase_token", r"verify_id_token"],
        "expected_roles": ["Public cert verification (no IAM role required for token verification)"],
    },
    {
        "service": "GCP Cloud Storage (GCS)",
        "patterns": [r"google\.cloud\s+import\s+storage", r"storage\.Client"],
        "write_patterns": [r"upload_from_", r"blob\.delete"],
        "read_patterns": [r"download_as_", r"list_blobs"],
        "expected_roles": ["roles/storage.objectViewer", "roles/storage.objectUser"],
    },
    {
        "service": "AWS S3 / Boto3",
        "patterns": [r"boto3\.client\(\s*['\"]s3['\"]", r"boto3\.resource\(\s*['\"]s3['\"]"],
        "write_patterns": [r"put_object", r"upload_file", r"delete_object"],
        "read_patterns": [r"get_object", r"list_objects"],
        "expected_roles": ["s3:GetObject", "s3:PutObject"],
    },
]


def strip_hcl_quotes(val: Any) -> Any:
    """Recursively strips extra outer quotes added by python-hcl2 v8+."""
    if isinstance(val, str):
        if len(val) >= 2 and val.startswith('"') and val.endswith('"'):
            return val[1:-1]
        return val
    if isinstance(val, list):
        return [strip_hcl_quotes(item) for item in val]
    if isinstance(val, dict):
        return {
            strip_hcl_quotes(k): strip_hcl_quotes(v)
            for k, v in val.items()
            if k not in {"__is_block__", "__comments__"}
        }
    return val


def parse_tf_files(repo_root: str) -> dict:
    context = {
        "is_public_facing": False,
        "public_ingress_points": [],
        "private_workloads": [],
        "iam_wildcard_detected": False,
        "iam_wildcard_statements": [],
        "iam_bindings": [],
        "overprivileged_iam_bindings": [],
        "service_accounts": [],
        "secrets_inventory": [],
        "datastores": [],
        "auth_providers": [],
        "trust_boundaries": [],
        "data_classifications": [],
        "application_routes": [],
        "security_middlewares": [],
        "code_cloud_sdk_usage": [],
        "code_env_and_secret_reads": [],
    }

    for root, _, files in os.walk(repo_root):
        if any(
            ignored in root
            for ignored in (".terraform", ".venv", "node_modules", ".git", ".worktrees", "__pycache__")
        ):
            continue
        for file in sorted(files):
            if not file.endswith(".tf"):
                continue
            path = os.path.join(root, file)
            rel_path = os.path.relpath(path, repo_root)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    raw_data = hcl2.load(fh)
                    clean_data = strip_hcl_quotes(raw_data)
                    inspect_hcl_data(clean_data, context, rel_path)
            except Exception as e:
                print(f"Warning: Failed parsing {rel_path}: {e}")

    extract_fastapi_and_sdk_usage(repo_root, context)
    synthesize_trust_boundaries(context)
    return context


def inspect_hcl_data(data: dict, context: dict, file_path: str):
    data = strip_hcl_quotes(data)
    resources = data.get("resource", [])
    for res_dict in resources:
        for res_type, instances in res_dict.items():
            for res_name, config in instances.items():
                if not isinstance(config, dict):
                    continue
                res_id = f"{res_type}.{res_name}"

                # 1. AWS Ingress & Network Exposure
                if res_type in {"aws_lb", "aws_alb"}:
                    internal = config.get("internal", False)
                    if not internal:
                        context["is_public_facing"] = True
                        context["public_ingress_points"].append(f"{res_id} (in {file_path})")
                    else:
                        context["private_workloads"].append(f"{res_id} (internal ALB in {file_path})")

                if res_type in {"aws_security_group", "aws_security_group_rule"}:
                    ingress_rules = config.get("ingress", [])
                    if isinstance(ingress_rules, dict):
                        ingress_rules = [ingress_rules]
                    for rule in ingress_rules:
                        if not isinstance(rule, dict):
                            continue
                        cidr_blocks = rule.get("cidr_blocks", [])
                        if "0.0.0.0/0" in cidr_blocks:
                            context["is_public_facing"] = True
                            port = rule.get("from_port", "all")
                            context["public_ingress_points"].append(
                                f"SG {res_name} allows 0.0.0.0/0 on port {port}"
                            )

                # 2. GCP Cloud Run Ingress & Public Invoker Exposure
                if res_type == "google_cloud_run_v2_service":
                    ingress = config.get("ingress", "INGRESS_TRAFFIC_ALL")
                    if ingress in {"INGRESS_TRAFFIC_ALL", "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"}:
                        context["is_public_facing"] = True
                        context["public_ingress_points"].append(
                            f"{res_id} (ingress={ingress} in {file_path})"
                        )
                    else:
                        context["private_workloads"].append(
                            f"{res_id} (ingress={ingress} in {file_path})"
                        )

                    templates = config.get("template", [])
                    if isinstance(templates, dict):
                        templates = [templates]
                    for tpl in templates:
                        if not isinstance(tpl, dict):
                            continue
                        containers = tpl.get("containers", [])
                        if isinstance(containers, dict):
                            containers = [containers]
                        for container in containers:
                            if not isinstance(container, dict):
                                continue
                            envs = container.get("env", [])
                            if isinstance(envs, dict):
                                envs = [envs]
                            for env_entry in envs:
                                if isinstance(env_entry, dict) and "value_source" in env_entry:
                                    env_name = env_entry.get("name", "UNKNOWN")
                                    context["secrets_inventory"].append(
                                        f"Cloud Run env '{env_name}' injected via Secret Manager secret_key_ref ({file_path})"
                                    )

                if res_type in {
                    "google_cloud_run_v2_service_iam_member",
                    "google_cloud_run_service_iam_member",
                }:
                    member = str(config.get("member", ""))
                    role = str(config.get("role", ""))
                    if "allUsers" in member or "allAuthenticatedUsers" in member:
                        context["is_public_facing"] = True
                        context["public_ingress_points"].append(
                            f"{res_id} grants {role} to {member} ({file_path})"
                        )

                # 3. IAM Policies, Wildcards & Blast Radius (AWS & GCP)
                if res_type in {"aws_iam_policy", "aws_iam_role_policy"}:
                    policy_doc = str(config.get("policy", ""))
                    if any(w in policy_doc for w in ('"*"', "'*'", '\\"*\\"', ":*")):
                        context["iam_wildcard_detected"] = True
                        context["iam_wildcard_statements"].append(res_id)

                if res_type == "google_service_account":
                    sa_id = config.get("account_id", res_name)
                    display = config.get("display_name", "")
                    context["service_accounts"].append(
                        f"{res_id} (account_id={sa_id}, display='{display}', file={file_path})"
                    )

                if res_type in {
                    "google_project_iam_member",
                    "google_project_iam_binding",
                    "google_service_account_iam_member",
                }:
                    role = str(config.get("role", ""))
                    member = str(config.get("member", ""))
                    binding_desc = f"{res_id}: {member} -> {role} ({file_path})"
                    context["iam_bindings"].append(binding_desc)
                    if role in BROAD_GCP_ROLES or "*" in role:
                        context["iam_wildcard_detected"] = True
                        context["iam_wildcard_statements"].append(
                            f"{res_id} ({role} granted to {member})"
                        )
                        context["overprivileged_iam_bindings"].append(binding_desc)

                if res_type == "google_iam_workload_identity_pool_provider":
                    cond = config.get("attribute_condition", "NONE")
                    context["trust_boundaries"].append(
                        f"OIDC Workload Identity Federation Boundary ({res_id}): condition [{cond}] in {file_path}"
                    )

                # 4. Data Layer, Secrets & Identity Platform
                if res_type == "google_firestore_database":
                    db_type = config.get("type", "FIRESTORE_NATIVE")
                    del_prot = config.get("delete_protection_state", "UNKNOWN")
                    del_pol = config.get("deletion_policy", "UNKNOWN")
                    context["datastores"].append(
                        f"{res_id} (type={db_type}, delete_protection={del_prot}, deletion_policy={del_pol}, file={file_path})"
                    )

                if res_type == "aws_s3_bucket":
                    context["datastores"].append(f"{res_id} (AWS S3 Bucket in {file_path})")

                if res_type == "google_secret_manager_secret":
                    sec_id = config.get("secret_id", res_name)
                    context["secrets_inventory"].append(
                        f"Secret Manager Container: {res_id} (secret_id={sec_id}, file={file_path})"
                    )

                if res_type == "google_identity_platform_config":
                    domains = config.get("authorized_domains", [])
                    context["auth_providers"].append(
                        f"Firebase/GCP Identity Platform ({res_id}) authorized_domains={domains} ({file_path})"
                    )

                # 5. Resource Tags & Labels
                for tag_field in ("tags", "labels"):
                    tags = config.get(tag_field, {})
                    if isinstance(tags, dict):
                        for tag_key, tag_val in tags.items():
                            if str(tag_key).lower() in {
                                "dataclassification",
                                "tier",
                                "compliance",
                                "environment",
                                "managed_by",
                            }:
                                context["data_classifications"].append(
                                    f"{res_id}: {tag_key}={tag_val}"
                                )


def extract_fastapi_and_sdk_usage(repo_root: str, context: dict):
    """Scans application code to map routes, middleware, AND actual cloud SDK/permission usage."""
    scan_dirs = [
        os.path.join(repo_root, "backend"),
        os.path.join(repo_root, "mlops"),
    ]
    route_pattern = re.compile(
        r'@(?:\w+)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']'
    )
    depends_pattern = re.compile(r"Depends\(\s*([a-zA-Z0-9_]+)\s*\)")
    env_pattern = re.compile(r'(?:os\.getenv|os\.environ\.get)\(\s*["\']([A-Z0-9_]+)["\']')

    for base_dir in scan_dirs:
        if not os.path.isdir(base_dir):
            continue
        for root, _, files in os.walk(base_dir):
            if "__pycache__" in root:
                continue
            for file in sorted(files):
                if not file.endswith(".py"):
                    continue
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, repo_root)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        content = fh.read()
                except Exception:
                    continue

                # 1. Middleware registrations
                for mw_match in re.finditer(r"add_middleware\(\s*([A-Za-z0-9_]+)", content):
                    mw_name = mw_match.group(1)
                    context["security_middlewares"].append(f"{mw_name} (registered in {rel_path})")

                # 2. FastAPI Routes
                lines = content.splitlines()
                for idx, line in enumerate(lines):
                    m = route_pattern.search(line)
                    if m:
                        method = m.group(1).upper()
                        route_path = m.group(2)
                        window = "\n".join(lines[idx : min(idx + 12, len(lines))])
                        deps = depends_pattern.findall(window)
                        auth_dep = ", ".join(deps) if deps else "None (Public / Middleware-only)"
                        context["application_routes"].append(
                            f"{method} {route_path} [Auth/Deps: {auth_dep}] ({rel_path}:{idx + 1})"
                        )

                # 3. Cloud SDK & Data Operations Usage (for IAM least-privilege cross-referencing)
                for sig in CODE_SDK_SIGNATURES:
                    if any(re.search(pat, content) for pat in sig["patterns"]):
                        has_write = any(re.search(wp, content) for wp in sig["write_patterns"])
                        has_read = any(re.search(rp, content) for rp in sig["read_patterns"])
                        ops = []
                        if has_read:
                            ops.append("READ")
                        if has_write:
                            ops.append("WRITE/MUTATE")
                        op_str = "/".join(ops) if ops else "CLIENT_INIT"
                        expected = ", ".join(sig["expected_roles"])
                        context["code_cloud_sdk_usage"].append(
                            f"{sig['service']} used in {rel_path} [Operations: {op_str}] (Expected Least-Privilege Role: {expected})"
                        )

                # 4. Environment variable & secret consumption in code
                for env_var in sorted(set(env_pattern.findall(content))):
                    if any(k in env_var for k in ("KEY", "SECRET", "PASSWORD", "TOKEN", "PROJECT", "WEBHOOK")):
                        context["code_env_and_secret_reads"].append(f"{env_var} (read in {rel_path})")


def synthesize_trust_boundaries(context: dict):
    """Builds architectural trust boundary summaries combining Terraform and app surface."""
    if context["is_public_facing"]:
        context["trust_boundaries"].append(
            "Internet -> Public Cloud Run / ALB Ingress (Untrusted External Network Boundary)"
        )
    else:
        context["trust_boundaries"].append(
            "Internal Network Only -> Private Workload Boundary (Zero Public 0.0.0.0/0 Ingress)"
        )

    if context["security_middlewares"]:
        context["trust_boundaries"].append(
            "Edge/API Gateway Middleware Layer -> " + ", ".join(context["security_middlewares"])
        )

    if context["service_accounts"] or context["iam_bindings"]:
        context["trust_boundaries"].append(
            "Application Runtime Identity (Cloud Run SA) -> GCP Managed Services (Firestore / Secret Manager)"
        )


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
