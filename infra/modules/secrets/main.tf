resource "google_secret_manager_secret" "gemini_key" {
  project   = var.project_id
  secret_id = var.secret_id

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    repository  = "portfolio"
  }

  replication {
    auto {}
  }
}

# Grant Cloud Run SA access to read secrets in Secret Manager
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${var.cloud_run_sa_email}"
}
