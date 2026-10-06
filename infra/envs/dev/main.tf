# ==============================================================================
# Development Environment Composition (Root Module)
# Cost-optimized: scaled down to 2 instances max, 256Mi memory
# ==============================================================================

# 1. APIs Enablement
module "apis" {
  source     = "../../modules/apis"
  project_id = var.project_id
}

# 2. Artifact Registry
module "artifact_registry" {
  source      = "../../modules/artifact_registry"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment

  depends_on = [module.apis]
}

# 3. Cloud Run Service (Dev Scale: max 2 instances, 256Mi for minimal footprint)
module "cloud_run" {
  source              = "../../modules/cloud_run"
  project_id          = var.project_id
  region              = var.region
  environment         = var.environment
  min_instances       = 0
  max_instances       = 2
  cpu_limit           = "1"
  memory_limit        = "256Mi"
  firebase_project_id = var.firebase_project_id != "" ? var.firebase_project_id : var.project_id

  # Contact-form SMTP forwarding (password injected from Secret Manager, never stored in Terraform)
  smtp_host               = var.smtp_host
  smtp_user               = var.smtp_user
  smtp_password_secret_id = var.smtp_password_secret_id

  depends_on = [module.apis]
}

# 4. Workload Identity Federation (WIF) for Keyless GitHub Actions OIDC
module "iam_wif" {
  source             = "../../modules/iam_wif"
  project_id         = var.project_id
  github_repository  = var.github_repository
  pool_id            = "github-pool-dev"
  provider_id        = "github-provider-dev"
  service_account_id = "sa-gha-dev"

  depends_on = [module.apis]
}

# 5. Firestore Database (Native Mode)
module "firestore" {
  source     = "../../modules/firestore"
  project_id = var.project_id

  depends_on = [module.apis]
}

# 6. Secret Manager for Gemini API Key (+ optional SMTP password)
module "secrets" {
  source             = "../../modules/secrets"
  project_id         = var.project_id
  environment        = var.environment
  cloud_run_sa_email = module.cloud_run.service_account_email

  smtp_password_secret_id = var.smtp_password_secret_id

  depends_on = [module.apis]
}
