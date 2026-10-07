locals {
  site_id      = var.firebase_site_id != "" ? var.firebase_site_id : var.project_id
  clean_domain = lower(trimspace(var.custom_domain))
}

# 1. Firebase Hosting Custom Domain: Apex Domain (Triggers Google-managed SSL provisioning)
resource "google_firebase_hosting_custom_domain" "apex" {
  provider              = google-beta
  count                 = var.enable_custom_domain_mapping ? 1 : 0
  project               = var.project_id
  site_id               = local.site_id
  custom_domain         = local.clean_domain
  cert_preference       = "GROUPED"
  wait_dns_verification = false
}

# 2. Firebase Hosting Custom Domain: www Subdomain (301 Redirect to Apex)
resource "google_firebase_hosting_custom_domain" "www" {
  provider              = google-beta
  count                 = var.enable_custom_domain_mapping && var.enable_www_subdomain ? 1 : 0
  project               = var.project_id
  site_id               = local.site_id
  custom_domain         = "www.${local.clean_domain}"
  redirect_target       = var.redirect_www_to_apex ? local.clean_domain : null
  cert_preference       = "GROUPED"
  wait_dns_verification = false

  depends_on = [google_firebase_hosting_custom_domain.apex]
}

# 3. Optional: Google Cloud DNS Managed Zone (if DNS is delegated to GCP)
resource "google_dns_managed_zone" "primary" {
  count       = var.enable_cloud_dns ? 1 : 0
  project     = var.project_id
  name        = replace("${local.clean_domain}-zone", ".", "-")
  dns_name    = "${local.clean_domain}."
  description = "Managed Cloud DNS zone for ${local.clean_domain} portfolio"
}

# 4. Optional: Apex Domain A Record
resource "google_dns_record_set" "apex_a" {
  count        = var.enable_cloud_dns ? 1 : 0
  project      = var.project_id
  managed_zone = google_dns_managed_zone.primary[0].name
  name         = "${local.clean_domain}."
  type         = "A"
  ttl          = 300
  rrdatas      = var.firebase_hosting_ip_addresses
}

# 5. Optional: www Subdomain CNAME Record
resource "google_dns_record_set" "www_cname" {
  count        = var.enable_cloud_dns && var.enable_www_subdomain ? 1 : 0
  project      = var.project_id
  managed_zone = google_dns_managed_zone.primary[0].name
  name         = "www.${local.clean_domain}."
  type         = "CNAME"
  ttl          = 300
  rrdatas      = ["${local.clean_domain}."]
}

# 6. Optional: Apex Domain TXT Ownership Verification Record (Day 1 / 2nd Run)
resource "google_dns_record_set" "ownership_txt" {
  count        = var.enable_cloud_dns && var.verification_txt_record != "" ? 1 : 0
  project      = var.project_id
  managed_zone = google_dns_managed_zone.primary[0].name
  name         = "${local.clean_domain}."
  type         = "TXT"
  ttl          = 300
  rrdatas      = [startswith(var.verification_txt_record, "\"") ? var.verification_txt_record : format("\"%s\"", var.verification_txt_record)]
}
