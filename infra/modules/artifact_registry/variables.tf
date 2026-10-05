variable "project_id" {
  description = "The GCP project ID to create the Artifact Registry repository in"
  type        = string
}

variable "region" {
  description = "The GCP region for the Artifact Registry repository"
  type        = string
  default     = "us-central1"
}

variable "repository_id" {
  description = "Unique ID of the Artifact Registry repository"
  type        = string
  default     = "portfolio-backend"
}

variable "description" {
  description = "Description of the Artifact Registry repository"
  type        = string
  default     = "Docker repository for Portfolio FastAPI backend containers"
}

variable "environment" {
  description = "Deployment environment (e.g. dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "keep_versions_count" {
  description = "Number of recent tagged image versions to retain in cleanup policy"
  type        = number
  default     = 5
}
