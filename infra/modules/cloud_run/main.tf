# Service Account for Cloud Run Runtime
resource "google_service_account" "cloud_run_sa" {
  project      = var.project_id
  account_id   = "sa-portfolio-backend-${var.environment}"
  display_name = "Cloud Run Service Account for Portfolio Backend (${var.environment})"
}

# Grant Firestore User role to Cloud Run SA
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Cloud Run v2 Service
resource "google_cloud_run_v2_service" "backend" {
  name     = "${var.service_name}-${var.environment}"
  location = var.region
  project  = var.project_id
  ingress  = "INGRESS_TRAFFIC_ALL"

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    repository  = "portfolio"
  }

  template {
    service_account = google_service_account.cloud_run_sa.email

    scaling {
      min_instance_count = var.min_instances # FinOps Scale-to-Zero ($0 idle)
      max_instance_count = var.max_instances # Ceiling against runaway billing
    }

    containers {
      image = var.container_image

      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
        cpu_idle = true # CPU allocated only during request processing
      }

      ports {
        container_port = 8080
      }

      env {
        name  = "ENV"
        value = var.environment
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "FIREBASE_PROJECT_ID"
        value = var.firebase_project_id
      }

      env {
        name  = "CUSTOM_DOMAIN"
        value = var.custom_domain
      }

      dynamic "env" {
        for_each = var.cors_origins != "" ? [var.cors_origins] : []
        content {
          name  = "CORS_ORIGINS"
          value = env.value
        }
      }

      dynamic "env" {
        for_each = var.client_verification_secret != "" ? [var.client_verification_secret] : []
        content {
          name  = "CLIENT_VERIFICATION_SECRET"
          value = env.value
        }
      }

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = var.gemini_secret_id
            version = "latest"
          }
        }
      }

      dynamic "env" {
        for_each = var.smtp_host != "" ? [var.smtp_host] : []
        content {
          name  = "SMTP_HOST"
          value = env.value
        }
      }

      dynamic "env" {
        for_each = var.smtp_user != "" ? [var.smtp_user] : []
        content {
          name  = "SMTP_USER"
          value = env.value
        }
      }

      dynamic "env" {
        for_each = var.smtp_password_secret_id != "" ? [var.smtp_password_secret_id] : []
        content {
          name = "SMTP_PASSWORD"
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }

      dynamic "env" {
        for_each = var.resend_api_key_secret_id != "" ? [var.resend_api_key_secret_id] : []
        content {
          name = "RESEND_API_KEY"
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }

      dynamic "env" {
        for_each = var.lead_webhook_secret_id != "" ? [var.lead_webhook_secret_id] : []
        content {
          name = "LEAD_NOTIFICATION_WEBHOOK_URL"
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }

      dynamic "env" {
        for_each = var.notification_email_secret_id != "" ? [var.notification_email_secret_id] : []
        content {
          name = "NOTIFICATION_EMAIL_TO"
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }

      startup_probe {
        http_get {
          path = "/healthz"
          port = 8080
        }
        initial_delay_seconds = 2
        period_seconds        = 5
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/healthz"
          port = 8080
        }
        period_seconds    = 15
        failure_threshold = 3
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image # Allow CI/CD to push new image revisions without Terraform drift
    ]
  }
}

# Allow public invocations if enabled
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  count    = var.allow_unauthenticated ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
