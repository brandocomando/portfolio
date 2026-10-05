output "database_name" {
  description = "The name of the Firestore database"
  value       = google_firestore_database.database.name
}

output "database_id" {
  description = "The ID of the Firestore database"
  value       = google_firestore_database.database.id
}

output "location_id" {
  description = "The location ID where Firestore is provisioned"
  value       = google_firestore_database.database.location_id
}
