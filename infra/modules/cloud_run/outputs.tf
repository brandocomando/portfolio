output "service_name" {
  description = "The name of the Cloud Run service"
  value       = google_cloud_run_v2_service.backend.name
}

output "service_id" {
  description = "The unique resource ID of the Cloud Run service"
  value       = google_cloud_run_v2_service.backend.id
}

output "service_url" {
  description = "The publicly accessible HTTPS URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.backend.uri
}

output "service_account_email" {
  description = "The email address of the Cloud Run dedicated runtime service account"
  value       = google_service_account.cloud_run_sa.email
}
