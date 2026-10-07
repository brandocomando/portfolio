output "custom_domain" {
  description = "The registered apex custom domain"
  value       = local.clean_domain
}

output "www_domain" {
  description = "The registered www subdomain"
  value       = "www.${local.clean_domain}"
}

output "dns_records_for_registrar" {
  description = "DNS records to configure at your registrar (Cloudflare, Namecheap, Porkbun, etc.)"
  value = {
    apex_a_record = {
      type  = "A"
      name  = "@"
      value = var.firebase_hosting_ip_addresses
      ttl   = "300 or Auto"
    }
    www_cname_record = {
      type  = "CNAME"
      name  = "www"
      value = local.clean_domain
      ttl   = "300 or Auto"
    }
  }
}

output "cloud_dns_nameservers" {
  description = "Authoritative Google Cloud DNS nameservers (if enable_cloud_dns is true)"
  value       = var.enable_cloud_dns && length(google_dns_managed_zone.primary) > 0 ? google_dns_managed_zone.primary[0].name_servers : []
}

output "ssl_management" {
  description = "Details about SSL certificate issuance"
  value       = "Firebase Hosting automatically provisions and renews Google-managed SSL certificates once DNS records are verified."
}
