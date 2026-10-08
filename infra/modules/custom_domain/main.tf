locals {
  site_id      = var.firebase_site_id != "" ? var.firebase_site_id : var.project_id
  clean_domain = lower(trimspace(var.custom_domain))

  # Dynamically extract TXT verification record from Firebase required_dns_updates
  dynamic_txt_records = flatten([
    for u in concat(
      try(google_firebase_hosting_custom_domain.apex[0].required_dns_updates, []),
      try(google_firebase_hosting_custom_domain.www[0].required_dns_updates, [])
    ) : [
      for d in u.desired : [
        for r in d.records : format("\"%s\"", replace(r.rdata, "\"", "")) if r.type == "TXT"
      ]
    ]
  ])

  # Selected TXT records: manual override if set, otherwise dynamically extracted
  resolved_txt_records = var.verification_txt_record != "" ? [
    startswith(var.verification_txt_record, "\"") ? var.verification_txt_record : format("\"%s\"", var.verification_txt_record)
  ] : local.dynamic_txt_records
}

# 1. Firebase Hosting Custom Domain: www Subdomain (Standardized Primary Domain)
resource "google_firebase_hosting_custom_domain" "www" {
  provider              = google-beta
  count                 = var.enable_custom_domain_mapping && var.enable_www_subdomain ? 1 : 0
  project               = var.project_id
  site_id               = local.site_id
  custom_domain         = "www.${local.clean_domain}"
  redirect_target       = var.redirect_www_to_apex ? local.clean_domain : null
  cert_preference       = "GROUPED"
  wait_dns_verification = false
}

# 2. Firebase Hosting Custom Domain: Apex Domain (Auto 301 Redirect to www)
resource "google_firebase_hosting_custom_domain" "apex" {
  provider              = google-beta
  count                 = var.enable_custom_domain_mapping ? 1 : 0
  project               = var.project_id
  site_id               = local.site_id
  custom_domain         = local.clean_domain
  redirect_target       = var.redirect_apex_to_www ? "www.${local.clean_domain}" : null
  cert_preference       = "GROUPED"
  wait_dns_verification = false

  depends_on = [google_firebase_hosting_custom_domain.www]
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

# 6. Apex Domain TXT Ownership Verification Record (Automatic via depends_on or manual override)
resource "google_dns_record_set" "ownership_txt" {
  count        = var.enable_cloud_dns && (var.auto_verify_dns || var.verification_txt_record != "") ? 1 : 0
  project      = var.project_id
  managed_zone = google_dns_managed_zone.primary[0].name
  name         = "${local.clean_domain}."
  type         = "TXT"
  ttl          = 300
  rrdatas      = length(local.resolved_txt_records) > 0 ? local.resolved_txt_records : ["\"hosting-verification=pending\""]

  depends_on = [google_firebase_hosting_custom_domain.apex]
}
