variable "project_id" {
  description = "The GCP Project ID"
  type        = string
}

variable "firebase_site_id" {
  description = "The Firebase Hosting Site ID (defaults to project ID if empty)"
  type        = string
  default     = ""
}

variable "custom_domain" {
  description = "Primary apex domain name (e.g. brandonfoster.dev)"
  type        = string
  default     = "brandonfoster.dev"
}

variable "enable_custom_domain_mapping" {
  description = "Whether to register the custom domain in Firebase Hosting"
  type        = bool
  default     = true
}

variable "enable_www_subdomain" {
  description = "Whether to configure the www subdomain (e.g. www.brandonfoster.dev)"
  type        = bool
  default     = true
}

variable "redirect_www_to_apex" {
  description = "Whether www subdomain should automatically 301 redirect to apex domain"
  type        = bool
  default     = true
}

variable "enable_cloud_dns" {
  description = "Whether to manage DNS in Google Cloud DNS (set to false if using Cloudflare, Namecheap, or Porkbun directly)"
  type        = bool
  default     = false
}

variable "firebase_hosting_ip_addresses" {
  description = "Firebase Hosting Anycast IP addresses for apex A records"
  type        = list(string)
  default     = ["199.36.158.100"]
}

variable "verification_txt_record" {
  description = "Optional manual Firebase TXT ownership verification token override (e.g. 'hosting-site-verification=abc...')"
  type        = string
  default     = ""
}

variable "auto_verify_dns" {
  description = "Whether to automatically pipe the TXT verification record from Firebase into Cloud DNS in one go using depends_on"
  type        = bool
  default     = true
}
