variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "service_name" {
  description = "App Runner service name"
  type        = string
  default     = "missing-trees-api"
}

variable "ecr_repository_name" {
  description = "ECR repository name"
  type        = string
  default     = "missing-trees"
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}

variable "cpu" {
  description = "CPU allocation"
  type        = string
  default     = "0.25 vCPU"
}

variable "memory" {
  description = "Memory allocation"
  type        = string
  default     = "0.5 GB"
}

variable "auto_deploy_enabled" {
  description = "Enable automatic deployments"
  type        = bool
  default     = true
}

variable "health_check_path" {
  description = "Health check endpoint path"
  type        = string
  default     = "/health"
}

variable "environment_variables" {
  description = "Environment variables for the application"
  type        = map(string)
  default = {
    FLASK_ENV   = "production"
    PYTHONPATH  = "/app"
  }
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default = {
    Environment = "production"
    Project     = "missing-trees"
    ManagedBy   = "terraform"
  }
}