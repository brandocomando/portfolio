#!/usr/bin/env bash
# ==============================================================================
# GCP Bootstrap Script for Brandon Foster Portfolio Platform
# Idempotently initializes GCP project, enables APIs, provisions Terraform remote
# state bucket, and prepares Workload Identity Federation for GitHub Actions.
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}       Brandon Foster Portfolio - GCP Bootstrap Script           ${NC}"
echo -e "${CYAN}================================================================${NC}"

# Check for gcloud CLI
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: 'gcloud' CLI is not installed or not in PATH.${NC}"
    echo -e "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Ensure user is logged in
CURRENT_USER=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || true)
if [ -z "$CURRENT_USER" ]; then
    echo -e "${YELLOW}No active gcloud login detected. Running 'gcloud auth login'...${NC}"
    gcloud auth login
fi

echo -e "Authenticated as: ${GREEN}${CURRENT_USER}${NC}"

# Prompt for Project ID if not set
if [ -z "${GCP_PROJECT_ID:-}" ]; then
    read -rp "Enter your Google Cloud Project ID: " GCP_PROJECT_ID
fi

REGION="${GCP_REGION:-us-central1}"
GITHUB_REPO="${GITHUB_REPOSITORY:-brandocomando/portfolio}"

echo -e "Target Project: ${GREEN}${GCP_PROJECT_ID}${NC}"
echo -e "Target Region:  ${GREEN}${REGION}${NC}"
echo -e "GitHub Repo:    ${GREEN}${GITHUB_REPO}${NC}"

gcloud config set project "${GCP_PROJECT_ID}" --quiet

# 1. Enable Core APIs required for bootstrap
echo -e "\n${CYAN}Step 1: Enabling essential Google Cloud APIs...${NC}"
gcloud services enable \
    serviceusage.googleapis.com \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com \
    storage.googleapis.com \
    secretmanager.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    firestore.googleapis.com \
    --quiet

echo -e "${GREEN}✓ APIs successfully enabled.${NC}"

# 2. Create Remote Terraform State Bucket
STATE_BUCKET="portfolio-terraform-state-${GCP_PROJECT_ID}"
echo -e "\n${CYAN}Step 2: Configuring Terraform Remote State Bucket (gs://${STATE_BUCKET})...${NC}"

if gcloud storage buckets describe "gs://${STATE_BUCKET}" &>/dev/null; then
    echo -e "${YELLOW}Bucket gs://${STATE_BUCKET} already exists.${NC}"
else
    gcloud storage buckets create "gs://${STATE_BUCKET}" \
        --location="${REGION}" \
        --uniform-bucket-level-access \
        --quiet
    gcloud storage buckets update "gs://${STATE_BUCKET}" --versioning
    echo -e "${GREEN}✓ Created remote state bucket with object versioning enabled.${NC}"
fi

# 3. Create Secret Manager placeholder for Gemini API Key if not present
echo -e "\n${CYAN}Step 3: Checking Gemini API Key secret in Secret Manager...${NC}"
if ! gcloud secrets describe gemini-api-key --quiet &>/dev/null; then
    gcloud secrets create gemini-api-key --replication-policy="automatic" --quiet
    read -rsp "Enter your Gemini API Key (or press Enter to set a dummy placeholder): " USER_GEMINI_KEY
    echo
    if [ -z "$USER_GEMINI_KEY" ]; then
        USER_GEMINI_KEY="placeholder-key-replace-in-secret-manager"
    fi
    echo -n "$USER_GEMINI_KEY" | gcloud secrets versions add gemini-api-key --data-file=- --quiet
    echo -e "${GREEN}✓ Created Secret Manager secret 'gemini-api-key'.${NC}"
else
    echo -e "${YELLOW}Secret 'gemini-api-key' already exists.${NC}"
fi

# 4. Generate local terraform.tfvars
echo -e "\n${CYAN}Step 4: Generating infra/envs/prod/terraform.tfvars...${NC}"
cat <<EOF > infra/envs/prod/terraform.tfvars
project_id          = "${GCP_PROJECT_ID}"
region              = "${REGION}"
github_repository   = "${GITHUB_REPO}"
firebase_project_id = "${GCP_PROJECT_ID}"
EOF
echo -e "${GREEN}✓ Created infra/envs/prod/terraform.tfvars${NC}"

# 5. Initialize Terraform with remote backend
echo -e "\n${CYAN}Step 5: Initializing Terraform with remote state backend...${NC}"
cd infra/envs/prod
terraform init -backend-config="bucket=${STATE_BUCKET}" -reconfigure

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}             GCP Bootstrap Completed Successfully!              ${NC}"
echo -e "${GREEN}================================================================${NC}"
echo -e "\nNext Steps:"
echo -e "1. Run Terraform apply locally or via CI/CD:"
echo -e "   ${CYAN}cd infra/envs/prod && terraform apply${NC}"
echo -e "2. Add these GitHub Repository Secrets to ${CYAN}https://github.com/${GITHUB_REPO}/settings/secrets/actions${NC}:"
echo -e "   • ${YELLOW}GCP_PROJECT_ID${NC}:       ${GCP_PROJECT_ID}"
echo -e "   • ${YELLOW}GCP_TF_STATE_BUCKET${NC}:  ${STATE_BUCKET}"
echo -e "   • ${YELLOW}GCP_WIF_PROVIDER${NC}:     (Output by terraform apply as workload_identity_provider)"
echo -e "   • ${YELLOW}GCP_WIF_SA_EMAIL${NC}:     (Output by terraform apply as github_actions_sa_email)"
echo
