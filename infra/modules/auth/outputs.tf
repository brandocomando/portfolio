output "app_id" {
  description = "Firebase Web App ID"
  value       = google_firebase_web_app.web.app_id
}

output "api_key" {
  description = "Firebase Web API Key"
  value       = data.google_firebase_web_app_config.web.api_key
}

output "auth_domain" {
  description = "Firebase Auth Domain"
  value       = data.google_firebase_web_app_config.web.auth_domain
}

output "storage_bucket" {
  description = "Firebase Storage Bucket"
  value       = lookup(data.google_firebase_web_app_config.web, "storage_bucket", "")
}

output "messaging_sender_id" {
  description = "Firebase Messaging Sender ID"
  value       = lookup(data.google_firebase_web_app_config.web, "messaging_sender_id", "")
}

output "firebase_config" {
  description = "Full Firebase configuration map for frontend consumption"
  value = {
    apiKey            = data.google_firebase_web_app_config.web.api_key
    authDomain        = data.google_firebase_web_app_config.web.auth_domain
    projectId         = var.project_id
    storageBucket     = lookup(data.google_firebase_web_app_config.web, "storage_bucket", "")
    messagingSenderId = lookup(data.google_firebase_web_app_config.web, "messaging_sender_id", "")
    appId             = google_firebase_web_app.web.app_id
  }
}
