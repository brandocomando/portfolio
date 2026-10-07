variable "project_id" {
  description = "Google Cloud Project ID for Production"
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
  default     = "prod"
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

variable "notification_email_secret_id" {
  description = "Secret Manager secret ID holding the notification email recipient (e.g. notification-email). Empty disables it."
  type        = string
  default     = ""
}

# --- Auth & Domain Configuration ---
variable "custom_domain" {
  description = "Custom domain for the portfolio (e.g. brandonfoster.dev)"
  type        = string
  default     = "brandonfoster.dev"
}

variable "google_oauth_client_id" {
  description = "Google OAuth 2.0 Web Client ID (optional)"
  type        = string
  default     = ""
}

variable "google_oauth_client_secret" {
  description = "Google OAuth 2.0 Web Client Secret (optional, sensitive)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "github_oauth_client_id" {
  description = "GitHub OAuth App Client ID (optional)"
  type        = string
  default     = ""
}

variable "github_oauth_client_secret" {
  description = "GitHub OAuth App Client Secret (optional, sensitive)"
  type        = string
  default     = ""
  sensitive   = true
}

