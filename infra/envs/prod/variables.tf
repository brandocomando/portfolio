variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Primary GCP Region"
  type        = string
  default     = "us-central1"
}

variable "github_repository" {
  description = "GitHub repository for Workload Identity Federation (owner/repo)"
  type        = string
  default     = "brandocomando/portfolio"
}

variable "firebase_project_id" {
  description = "Firebase Project ID (often same as GCP project ID)"
  type        = string
  default     = ""
}
