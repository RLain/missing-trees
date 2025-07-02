terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.0"
}

provider "aws" {
  region = var.aws_region
}

# ECR Repository
resource "aws_ecr_repository" "missing_trees" {
  name                 = var.ecr_repository_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = var.tags
}

# ECR Lifecycle Policy
resource "aws_ecr_lifecycle_policy" "missing_trees" {
  repository = aws_ecr_repository.missing_trees.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# IAM Role for App Runner
resource "aws_iam_role" "apprunner_instance_role" {
  name = "${var.service_name}-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "tasks.apprunner.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM Role for App Runner Access
resource "aws_iam_role" "apprunner_access_role" {
  name = "${var.service_name}-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Attach ECR access policy
resource "aws_iam_role_policy_attachment" "apprunner_access_role_policy" {
  role       = aws_iam_role.apprunner_access_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}



# Null resource to build and push Docker image
resource "null_resource" "docker_build_push" {
  triggers = {
    # Only hash files that exist
    dockerfile_hash = fileexists("${path.module}/../Dockerfile") ? filemd5("${path.module}/../Dockerfile") : "none"
    package_json_hash = fileexists("${path.module}/../package.json") ? filemd5("${path.module}/../package.json") : "none"
    # Fallback to timestamp if files don't exist
    timestamp = timestamp()
  }

  provisioner "local-exec" {
    working_dir = path.module
    command = <<-EOT
      # Navigate to project root (assuming infrastructure is a subdirectory)
      cd ..
      
      # Get ECR login
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.missing_trees.repository_url}
      
      # Build image
      docker build -t ${var.service_name} .
      
      # Tag for ECR
      docker tag ${var.service_name}:latest ${aws_ecr_repository.missing_trees.repository_url}:${var.image_tag}
      
      # Push to ECR
      docker push ${aws_ecr_repository.missing_trees.repository_url}:${var.image_tag}
    EOT
  }

  depends_on = [aws_ecr_repository.missing_trees]
}

# App Runner Service
resource "aws_apprunner_service" "missing_trees" {
  service_name = var.service_name

  source_configuration {
    auto_deployments_enabled = var.auto_deploy_enabled
    
    # Authentication configuration for private ECR
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_access_role.arn
    }
    
    image_repository {
      image_configuration {
        port = "8080"
        runtime_environment_variables = var.environment_variables
      }
      image_identifier      = "${aws_ecr_repository.missing_trees.repository_url}:${var.image_tag}"
      image_repository_type = "ECR"
    }
  }

  instance_configuration {
    cpu               = var.cpu
    memory            = var.memory
    instance_role_arn = aws_iam_role.apprunner_instance_role.arn
  }

  health_check_configuration {
    healthy_threshold   = 1
    interval            = 10
    path               = var.health_check_path
    protocol           = "HTTP"
    timeout            = 5
    unhealthy_threshold = 5
  }

  tags = var.tags

  depends_on = [aws_iam_role_policy_attachment.apprunner_access_role_policy, null_resource.docker_build_push]
}