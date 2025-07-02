output "app_runner_service_url" {
  description = "App Runner service URL"
  value       = "https://${aws_apprunner_service.missing_trees.service_url}"
}

output "app_runner_service_arn" {
  description = "App Runner service ARN"
  value       = aws_apprunner_service.missing_trees.service_arn
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.missing_trees.repository_url
}

output "ecr_repository_name" {
  description = "ECR repository name"
  value       = aws_ecr_repository.missing_trees.name
}