variable "project_id" {
  description = "The GCP project ID to create the Firestore database in"
  type        = string
}

variable "location_id" {
  description = "Firestore database location (e.g. nam5 for multi-region US free tier)"
  type        = string
  default     = "nam5"
}

variable "database_name" {
  description = "The database name (default database must be '(default)')"
  type        = string
  default     = "(default)"
}
