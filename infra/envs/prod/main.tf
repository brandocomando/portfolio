terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.30"
    }
  }

  # Remote backend configured via -backend-config in CI/CD:
  # backend "gcs" {
  #   bucket = "portfolio-terraform-state-<PROJECT_ID>"
  #   prefix = "terraform/state/prod"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. APIs Enablement
module "apis" {
  source     = "../../modules/apis"
  project_id = var.project_id
}

# 2. Artifact Registry
module "artifact_registry" {
  source     = "../../modules/artifact_registry"
  project_id = var.project_id
  region     = var.region

  depends_on = [module.apis]
}

# 3. Cloud Run Service
module "cloud_run" {
  source              = "../../modules/cloud_run"
  project_id          = var.project_id
  region              = var.region
  firebase_project_id = var.firebase_project_id != "" ? var.firebase_project_id : var.project_id

  depends_on = [module.apis]
}

# 4. Workload Identity Federation (WIF) for GitHub Actions
module "iam_wif" {
  source            = "../../modules/iam_wif"
  project_id        = var.project_id
  github_repository = var.github_repository

  depends_on = [module.apis]
}

# 5. Firestore Database (Native Mode)
module "firestore" {
  source     = "../../modules/firestore"
  project_id = var.project_id

  depends_on = [module.apis]
}

# 6. Secret Manager for Gemini API Key
module "secrets" {
  source             = "../../modules/secrets"
  project_id         = var.project_id
  cloud_run_sa_email = module.cloud_run.service_account_email

  depends_on = [module.apis]
}
