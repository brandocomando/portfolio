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

# Optional SMTP password secret (contact-form email forwarding).
# Terraform only creates the secret container; add the value out-of-band so it never lands in state:
#   printf '%s' "$SMTP_PASSWORD" | gcloud secrets versions add <secret_id> --data-file=-
resource "google_secret_manager_secret" "smtp_password" {
  count     = var.smtp_password_secret_id != "" ? 1 : 0
  project   = var.project_id
  secret_id = var.smtp_password_secret_id

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    repository  = "portfolio"
  }

  replication {
    auto {}
  }
}

# Optional notification email secret (contact-form destination).
# Terraform only creates the secret container; add the value out-of-band so it never lands in state:
#   printf '%s' "$NOTIFICATION_EMAIL_TO" | gcloud secrets versions add <secret_id> --data-file=-
resource "google_secret_manager_secret" "notification_email" {
  count     = var.notification_email_secret_id != "" ? 1 : 0
  project   = var.project_id
  secret_id = var.notification_email_secret_id

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    repository  = "portfolio"
  }

  replication {
    auto {}
  }
}

