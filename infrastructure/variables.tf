variable "auto_deploy_enabled" {
  default     = true
  description = "Enable automatic deployments"
  type        = bool
}

variable "aws_region" {
  default     = "eu-west-1"
  description = "AWS region"
  type        = string
}

variable "cpu" {
  default     = "0.25 vCPU"
  description = "CPU allocation"
  type        = string
}

variable "ecr_repository_name" {
  default     = "missing_trees"
  description = "ECR repository name"
  type        = string
}

variable "environment_variables" {
  default = {
    FLASK_ENV  = "production"
    PYTHONPATH = "/app"
  }
  description = "Environment variables for the application"
  type        = map(string)
}

variable "health_check_path" {
  description = "Health check endpoint path"
  type        = string
  default     = "/health"
}

variable "image_tag" {
  default     = "latest"
  description = "Docker image tag"
  type        = string
}

variable "memory" {
  default     = "0.5 GB"
  description = "Memory allocation"
  type        = string
}

variable "service_name" {
  default     = "missing_trees"
  description = "App Runner service name"
  type        = string
}

variable "tags" {
  default = {
    Environment = "production"
    ManagedBy   = "terraform"
    Project     = "missing_trees"
  }
  description = "Tags to apply to resources"
  type        = map(string)
}

