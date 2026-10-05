output "cloud_run_url" {
  description = "Public URL of the Development FastAPI backend on Cloud Run"
  value       = module.cloud_run.service_url
}

output "artifact_registry_repo" {
  description = "Docker repository URI for backend images"
  value       = module.artifact_registry.repository_url
}

output "workload_identity_provider" {
  description = "WIF Provider resource name for GitHub Actions OIDC"
  value       = module.iam_wif.workload_identity_provider_name
}

output "github_actions_sa_email" {
  description = "Service account email for GitHub Actions"
  value       = module.iam_wif.service_account_email
}
