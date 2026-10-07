variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "web_app_display_name" {
  description = "Display name for the Firebase Web App"
  type        = string
  default     = "Portfolio Web"
}

variable "authorized_domains" {
  description = "Additional domains to authorize for Firebase Auth (e.g. custom domain)"
  type        = list(string)
  default     = []
}

variable "enable_email_sign_in" {
  description = "Whether to enable email sign-in method in Identity Platform"
  type        = bool
  default     = true
}

variable "enable_anonymous_sign_in" {
  description = "Whether to enable anonymous sign-in in Identity Platform"
  type        = bool
  default     = true
}

variable "google_oauth_client_id" {
  description = "Google OAuth 2.0 Web Client ID (optional, enables google.com provider in Identity Platform)"
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
  description = "GitHub OAuth App Client ID (optional, enables github.com provider in Identity Platform)"
  type        = string
  default     = ""
}

variable "github_oauth_client_secret" {
  description = "GitHub OAuth App Client Secret (optional, sensitive)"
  type        = string
  default     = ""
  sensitive   = true
}
