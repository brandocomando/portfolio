variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "secret_id" {
  description = "Secret ID for Gemini API key"
  type        = string
  default     = "gemini-api-key"
}

variable "cloud_run_sa_email" {
  description = "Service account email of the Cloud Run backend"
  type        = string
}

resource "google_secret_manager_secret" "gemini_key" {
  project   = var.project_id
  secret_id = var.secret_id

  replication {
    auto {}
  }
}

# Grant Cloud Run SA access to read secret payload
resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.gemini_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.cloud_run_sa_email}"
}

output "secret_id" {
  value = google_secret_manager_secret.gemini_key.secret_id
}
