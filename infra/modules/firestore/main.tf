resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = var.database_name
  location_id = var.location_id
  type        = "FIRESTORE_NATIVE"

  delete_protection_state = "DELETE_PROTECTION_DISABLED"
  deletion_policy         = "DELETE"
}
