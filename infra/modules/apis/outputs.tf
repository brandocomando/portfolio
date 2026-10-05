output "enabled_services" {
  description = "List of Google Cloud API service names enabled by this module"
  value       = [for s in google_project_service.enabled_services : s.service]
}
