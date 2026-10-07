variable "project_id" {
  description = "The GCP project ID to create secrets in"
  type        = string
}

variable "secret_id" {
  description = "The unique secret ID in Secret Manager"
  type        = string
  default     = "gemini-api-key"
}

variable "cloud_run_sa_email" {
  description = "The service account email of the Cloud Run runtime to grant secretAccessor role"
  type        = string
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "prod"
}

variable "smtp_password_secret_id" {
  description = "Optional Secret Manager secret ID for the SMTP password. Leave empty to skip creating it."
  type        = string
  default     = ""
}

variable "notification_email_secret_id" {
  description = "Optional Secret Manager secret ID for the notification recipient email. Leave empty to skip creating it."
  type        = string
  default     = ""
}

