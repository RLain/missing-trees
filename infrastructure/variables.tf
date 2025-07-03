# Variables
variable "allowed_ssh_cidr" {
  description = "CIDR blocks allowed to SSH into EC2"
  type        = list(string)
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "missing-trees-api"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "af-south-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "EC2 Key Pair name"
  type        = string
}

variable "repository_branch" {
  description = "The branch of the repository to check out"
  type        = string
  default     = "main"
}

variable "repository_url" {
  description = "The URL of the Git repository to clone"
  type        = string
}