variable "project_id" {
  description = "Google Cloud Project ID for Development"
  type        = string
}

variable "region" {
  description = "Primary GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment identifier"
  type        = string
  default     = "dev"
}

variable "github_repository" {
  description = "GitHub repository for Workload Identity Federation (owner/repo)"
  type        = string
  default     = "brandocomando/portfolio"
}

variable "firebase_project_id" {
  description = "Firebase Project ID"
  type        = string
  default     = ""
}
