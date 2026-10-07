variable "project_id" {
  description = "The GCP project ID to deploy Cloud Run into"
  type        = string
}

variable "region" {
  description = "The GCP region for the Cloud Run service"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
  default     = "portfolio-backend"
}

variable "container_image" {
  description = "The container image URI to deploy"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "firebase_project_id" {
  description = "Firebase Project ID for authentication token verification"
  type        = string
  default     = ""
}

variable "gemini_secret_id" {
  description = "Secret Manager secret ID containing the Gemini API key"
  type        = string
  default     = "gemini-api-key"
}

variable "smtp_password_secret_id" {
  description = "Optional Secret Manager secret ID containing the SMTP password"
  type        = string
  default     = ""
}

variable "resend_api_key_secret_id" {
  description = "Optional Secret Manager secret ID containing the Resend API key"
  type        = string
  default     = ""
}

variable "lead_webhook_secret_id" {
  description = "Optional Secret Manager secret ID containing the notification webhook URL"
  type        = string
  default     = ""
}

variable "notification_email_secret_id" {
  description = "Optional Secret Manager secret ID containing the notification email recipient"
  type        = string
  default     = ""
}

variable "smtp_host" {
  description = "Optional SMTP Host (e.g. smtp.gmail.com)"
  type        = string
  default     = ""
}

variable "smtp_user" {
  description = "Optional SMTP User (e.g. your_email@gmail.com)"
  type        = string
  default     = ""
}

variable "environment" {
  description = "Deployment environment name (e.g. dev, prod)"
  type        = string
  default     = "prod"
}

variable "min_instances" {
  description = "Minimum number of container instances (0 enables Scale-to-Zero for FinOps)"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of container instances to prevent runaway spend"
  type        = number
  default     = 5
}

variable "cpu_limit" {
  description = "CPU allocated per container instance"
  type        = string
  default     = "1"
}

variable "memory_limit" {
  description = "Memory allocated per container instance"
  type        = string
  default     = "512Mi"
}

variable "allow_unauthenticated" {
  description = "Whether to allow unauthenticated public traffic to the service"
  type        = bool
  default     = true
}

variable "custom_domain" {
  description = "Custom domain for the portfolio (e.g. brandonfoster.dev)"
  type        = string
  default     = "brandonfoster.dev"
}

variable "cors_origins" {
  description = "Allowed origins for CORS (comma-separated or JSON list)"
  type        = string
  default     = ""
}

variable "client_verification_secret" {
  description = "Client verification secret shared with the frontend"
  type        = string
  default     = "portfolio-client-v1"
}
