output "repository_id" {
  description = "The repository ID created in Artifact Registry"
  value       = google_artifact_registry_repository.docker_repo.repository_id
}

output "repository_name" {
  description = "The fully qualified resource name of the repository"
  value       = google_artifact_registry_repository.docker_repo.name
}

output "repository_url" {
  description = "The container registry URL prefix for docker tag and docker push"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
}
