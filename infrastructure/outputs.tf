# Outputs

output "elastic_ip" {
  value = aws_eip.app_eip.public_ip
  description = "Static IP for missing tree app"
}

output "instance_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_instance.missing_tree_app.public_dns
}

output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.missing_tree_app.public_ip
}

output "missing_tree_api_url" {
  description = "Missing Tree API URL"
  value       = "http://${aws_instance.missing_tree_app.public_ip}:5000"
}