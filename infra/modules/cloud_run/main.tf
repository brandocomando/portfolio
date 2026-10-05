variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "portfolio-backend"
}

variable "container_image" {
  description = "Container image URI"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello" # Default placeholder until first build
}

variable "firebase_project_id" {
  description = "Firebase Project ID for auth validation"
  type        = string
  default     = ""
}

variable "gemini_secret_id" {
  description = "Secret Manager secret ID for Gemini API key"
  type        = string
  default     = "gemini-api-key"
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  project      = var.project_id
  account_id   = "sa-portfolio-backend"
  display_name = "Cloud Run Service Account for Portfolio Backend"
}

# Grant Firestore User role to Cloud Run SA
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Cloud Run v2 Service
resource "google_cloud_run_v2_service" "backend" {
  name     = var.service_name
  location = var.region
  project  = var.project_id
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.cloud_run_sa.email

    scaling {
      min_instance_count = 0 # FinOps Scale-to-Zero ($0 idle)
      max_instance_count = 5 # Ceiling against runaway billing
    }

    containers {
      image = var.container_image

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true # CPU allocated only during request processing
      }

      ports {
        container_port = 8080
      }

      env {
        name  = "ENV"
        value = "production"
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
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = var.gemini_secret_id
            version = "latest"
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

# Allow public invocations
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "service_name" {
  value = google_cloud_run_v2_service.backend.name
}

output "service_url" {
  value = google_cloud_run_v2_service.backend.uri
}

output "service_account_email" {
  value = google_service_account.cloud_run_sa.email
}
