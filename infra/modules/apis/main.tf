variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_services" {
  description = "List of GCP APIs to enable"
  type        = list(string)
  default = [
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "firestore.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "cloudresourcemanager.googleapis.com"
  ]
}

resource "google_project_service" "enabled_services" {
  for_each = toset(var.gcp_services)

  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

output "enabled_services" {
  value = [for s in google_project_service.enabled_services : s.service]
}
