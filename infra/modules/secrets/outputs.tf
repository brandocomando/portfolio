output "secret_id" {
  description = "The secret ID created in Secret Manager"
  value       = google_secret_manager_secret.gemini_key.secret_id
}

output "secret_name" {
  description = "The fully qualified resource name of the secret"
  value       = google_secret_manager_secret.gemini_key.name
}

output "smtp_password_secret_id" {
  description = "The SMTP password secret ID (empty if not enabled)"
  value       = try(google_secret_manager_secret.smtp_password[0].secret_id, "")
}

output "notification_email_secret_id" {
  description = "The notification recipient email secret ID (empty if not enabled)"
  value       = try(google_secret_manager_secret.notification_email[0].secret_id, "")
}

