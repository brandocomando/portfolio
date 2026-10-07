output "cloud_run_url" {
  description = "Public URL of the FastAPI backend on Cloud Run"
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

output "custom_domain" {
  description = "The registered apex custom domain"
  value       = module.custom_domain.custom_domain
}

output "www_domain" {
  description = "The registered www subdomain (redirected to apex)"
  value       = module.custom_domain.www_domain
}

output "dns_records_for_registrar" {
  description = "DNS records to configure at registrar (Cloudflare, Namecheap, Porkbun, etc.)"
  value       = module.custom_domain.dns_records_for_registrar
}

output "cloud_dns_nameservers" {
  description = "Nameservers if Google Cloud DNS is enabled"
  value       = module.custom_domain.cloud_dns_nameservers
}

output "firebase_required_dns_updates" {
  description = "Dynamic DNS records computed by Firebase, including secret TXT verification token"
  value       = module.custom_domain.required_dns_updates
}

output "firebase_web_app_id" {
  description = "Firebase Web App ID"
  value       = module.auth.app_id
}

output "firebase_web_api_key" {
  description = "Firebase Web Client API Key"
  value       = module.auth.api_key
  sensitive   = false
}

output "firebase_config" {
  description = "Firebase SDK initialization parameters for the frontend"
  value       = module.auth.firebase_config
  sensitive   = false
}
