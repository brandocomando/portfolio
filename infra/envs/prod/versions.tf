terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.30"
    }
  }

  # Configured via -backend-config in bootstrap script and CI/CD:
  # backend "gcs" {
  #   bucket = "portfolio-terraform-state-<PROJECT_ID>"
  #   prefix = "terraform/state/prod"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
