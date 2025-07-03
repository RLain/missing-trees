# Variables
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

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "missing-trees-api"
}

variable "key_name" {
  description = "EC2 Key Pair name"
  type        = string
}