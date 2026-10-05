resource "google_project_service" "enabled_services" {
  for_each = toset(var.gcp_services)

  project            = var.project_id
  service            = each.key
  disable_on_destroy = var.disable_services_on_destroy
}
