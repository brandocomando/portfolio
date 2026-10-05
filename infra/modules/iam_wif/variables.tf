variable "project_id" {
  description = "The GCP project ID to configure Workload Identity Federation in"
  type        = string
}

variable "github_repository" {
  description = "GitHub repository (owner/repo) permitted to authenticate via OIDC"
  type        = string
  default     = "brandocomando/portfolio"
}

variable "pool_id" {
  description = "Workload Identity Pool ID"
  type        = string
  default     = "github-pool"
}

variable "provider_id" {
  description = "Workload Identity Provider ID"
  type        = string
  default     = "github-provider"
}

variable "service_account_id" {
  description = "Service account ID to create for GitHub Actions CI/CD"
  type        = string
  default     = "sa-github-actions"
}
