variable "project_id" {
  description = "The GCP project ID to enable services in"
  type        = string
}

variable "gcp_services" {
  description = "List of Google Cloud API service names to enable"
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
    "cloudresourcemanager.googleapis.com",
    "identitytoolkit.googleapis.com",
    "firebase.googleapis.com"
  ]
}

variable "disable_services_on_destroy" {
  description = "Whether to disable services when the module is destroyed"
  type        = bool
  default     = false
}
