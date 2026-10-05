variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "location_id" {
  description = "Firestore database location (e.g. nam5 or us-central1)"
  type        = string
  default     = "nam5" # Multi-region US free tier location
}

resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.location_id
  type        = "FIRESTORE_NATIVE"

  delete_protection_state = "DELETE_PROTECTION_DISABLED"
  deletion_policy         = "DELETE"
}

output "database_name" {
  value = google_firestore_database.database.name
}
