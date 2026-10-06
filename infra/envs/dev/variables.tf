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

# --- Contact-form email forwarding (optional) ---
variable "smtp_host" {
  description = "SMTP host for contact-form forwarding (e.g. smtp.gmail.com). Empty disables SMTP."
  type        = string
  default     = ""
}

variable "smtp_user" {
  description = "SMTP username (e.g. you@gmail.com)"
  type        = string
  default     = ""
}

variable "smtp_password_secret_id" {
  description = "Secret Manager secret ID holding the SMTP password (e.g. smtp-password). Empty disables it."
  type        = string
  default     = ""
}
