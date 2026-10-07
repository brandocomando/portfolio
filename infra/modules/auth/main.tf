# ==============================================================================
# Identity Platform & Firebase Web App Configuration Module
# ==============================================================================

# 1. Identity Platform Project Configuration
resource "google_identity_platform_config" "auth" {
  project = var.project_id

  authorized_domains = distinct(compact(concat([
    "localhost",
    "${var.project_id}.firebaseapp.com",
    "${var.project_id}.web.app"
  ], var.authorized_domains)))

  sign_in {
    allow_duplicate_emails = false

    email {
      enabled           = var.enable_email_sign_in
      password_required = false
    }

    anonymous {
      enabled = var.enable_anonymous_sign_in
    }
  }
}

# 2. Firebase Web Application Registration
resource "google_firebase_web_app" "web" {
  provider     = google-beta
  project      = var.project_id
  display_name = var.web_app_display_name

  deletion_policy = "DELETE"
}

# 3. Retrieve Web App Config (SDK initialization parameters)
data "google_firebase_web_app_config" "web" {
  provider   = google-beta
  project    = var.project_id
  web_app_id = google_firebase_web_app.web.app_id
}

# 4. Google Identity Provider (IdP) Config (Optional: active when OAuth client ID and secret are supplied)
resource "google_identity_platform_default_supported_idp_config" "google" {
  count         = var.google_oauth_client_id != "" && var.google_oauth_client_secret != "" ? 1 : 0
  project       = var.project_id
  idp_id        = "google.com"
  client_id     = var.google_oauth_client_id
  client_secret = var.google_oauth_client_secret
  enabled       = true

  depends_on = [google_identity_platform_config.auth]
}

# 5. GitHub Identity Provider (IdP) Config (Optional: active when GitHub OAuth credentials are supplied)
resource "google_identity_platform_default_supported_idp_config" "github" {
  count         = var.github_oauth_client_id != "" && var.github_oauth_client_secret != "" ? 1 : 0
  project       = var.project_id
  idp_id        = "github.com"
  client_id     = var.github_oauth_client_id
  client_secret = var.github_oauth_client_secret
  enabled       = true

  depends_on = [google_identity_platform_config.auth]
}
