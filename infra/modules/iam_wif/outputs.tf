output "workload_identity_pool_name" {
  description = "The fully qualified resource name of the Workload Identity Pool"
  value       = google_iam_workload_identity_pool.github_pool.name
}

output "workload_identity_provider_name" {
  description = "The fully qualified resource name of the Workload Identity Provider for GitHub Actions"
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}

output "service_account_email" {
  description = "The service account email dedicated to GitHub Actions CI/CD"
  value       = google_service_account.github_actions_sa.email
}
